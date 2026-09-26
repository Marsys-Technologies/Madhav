"""Nirmāṇa engine packet A1 — "Record how long and how fast".

Before this packet: asset_throughput.rows_per_second existed (migration 169, 2026-06-06)
but was NULL for 100% of all 268 rows across every layer — no code path anywhere in the
engine ever computed it, and there was no duration column at all to compute it from. The
frozen WriterResult (pipeline.orchestrator.writers.WriterResult) already carries
`duration_seconds` per completed writer/sub-step; the engine received it and discarded it
in `_drive_substeps`. See `00_ARCHITECTURE/briefs/nirmana/engine/measurements/
A1_before_20260926T120730Z.json` for the full before-state.

Gate review A1_review_20260926T124832Z.md (ACCEPT_WITH_CORRECTIONS) found the packet's
central coverage claim false: A1's original design summed each sub-step's own
WriterResult.duration_seconds (a value the WRITER self-reports), which defaults to 0.0
and is a lottery decided by whether each writer happens to populate it (measured: bg
30/32, mi 14/14, ka 2/23, ga 1/19, bo 0/24, ph 0/8 — roughly 201/268 asset_throughput
rows stayed NULL through the very path meant to fix them). C1 (this file's tests C/D
below) fixes this at the root: the ENGINE now times its own call into
`writer.run_substep(ctx, step)` with `time.monotonic()`, so coverage is universal and
earned (§N.8) regardless of whether any writer ever sets duration_seconds. The review
also found a build-fatal deploy-ordering hazard (C2, tests marked "degraded path"
below) and two documentation-only defects in migration 1094's COMMENT ON blocks (C3,
not tested here — SQL comments have no executable behavior to assert against).

This file tests, without a live DB (FakeConn/FakeCursor, same pattern as
test_asset_runner_zero_rows.py):

  A. `_compute_duration_and_rate` (asset_runner.py) — the pure guard: missing/zero/
     negative/non-finite duration -> (None, None), never 0, never a ZeroDivisionError;
     a genuine positive duration -> a real (duration, rate) pair, including the
     rate=0.0-is-honest case (0 rows written over a real positive duration).
  B. `_drive_substeps` sums each executed sub-step's own ENGINE-MEASURED wall-clock
     time (tested directly in test_orchestrator_substeps.py; not duplicated here).
  C. `_run_data_writer`'s SUCCESS completion write persists a real, non-zero
     duration_seconds + rows_per_second — and that value is the ENGINE's own
     measurement, never the writer's self-report (a writer that self-reports a false
     duration_seconds=4.0 while actually running near-instantly must NOT get 4.0
     persisted). This is C1's whole point.
  D. The much more common case today (most writers never set duration_seconds, so
     WriterResult defaults it to 0.0) must STILL get a real, positive, engine-measured
     duration and rate — this is the fix for the ~201/268 rows that stayed NULL under
     A1's original writer-self-report design. Fails without the C1 fix.
  E. `_run_data_writer`'s FAILURE path (mark_asset_error, reached before the
     completion write) never touches duration_seconds/rows_per_second at all —
     the columns must read NULL by omission, never a fabricated value.
  F. The legacy L1 telemetry helper (ga_writers/_telemetry.py) has the same guard
     and, with no duration_seconds argument (the case for all 8 of today's callers
     — untouched by this packet, an out-of-scope writer-edit stop condition per
     §8(2); see the A1 report's honest-limits section), still writes NULL/NULL
     exactly as before this change.
  G. C2 — graceful degradation when asset_throughput.duration_seconds does not yet
     exist (migration 1094 unapplied): the completion write must still succeed
     (build completes normally) and simply omit duration_seconds/rows_per_second
     from the UPDATE, never raise. The presence probe is cached once per process,
     never re-run per write.
"""
from __future__ import annotations

import math
import sys
import pathlib
import time

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar  # noqa: E402
from pipeline.orchestrator.writers import WriterBase, WriterResult  # noqa: E402


# ── Fakes (mirrors test_asset_runner_zero_rows.py) ────────────────────────────

class FakeCursor:
    def __init__(self):
        self.executed: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return []

    def fetchone(self):
        return None

    def sqls(self) -> list[str]:
        return [s for s, _ in self.executed]

    def params_for(self, keyword: str) -> list[tuple]:
        return [p for s, p in self.executed if keyword in s]


class FakeConn:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def _run_with_writer(
    monkeypatch, writer_cls, chart_id, duration_columns_present: bool = True,
) -> tuple[FakeCursor, list[str]]:
    """Run _run_data_writer with the given writer class injected via get_writer stub.
    Returns (cursor, errors) — errors collects whatever mark_asset_error was called with,
    so a failure path's error message is inspectable without a real DB.

    `duration_columns_present` (C2, default True): sets the module-level, once-per-
    process cache `ar._DURATION_COLUMNS_PRESENT` directly rather than relying on
    FakeCursor.fetchone() (which always returns None) to simulate "column absent" —
    this lets most tests assume the common case (migration 1094 applied) while the
    dedicated degraded-path test below passes False to prove the other branch."""
    errors: list[str] = []
    monkeypatch.setattr(ar, 'emit_event', lambda e, cur=None: None)
    monkeypatch.setattr(ar, 'discover_all', lambda: None)
    monkeypatch.setattr(ar, 'get_writer', lambda aid: writer_cls)
    monkeypatch.setattr(ar, 'fetch_birth_params', lambda conn, cid: {'chart_id': cid})
    monkeypatch.setattr(ar, 'compute_upstream_hash', lambda cur, aid, cid: 'hash-upstream')
    monkeypatch.setattr(ar, 'get_writer_source_hash', lambda aid: 'hash-writer')
    monkeypatch.setattr(ar, 'compute_downstream_closure', lambda cur, aid: [])
    monkeypatch.setattr(ar, '_DURATION_COLUMNS_PRESENT', duration_columns_present)
    monkeypatch.setattr(
        ar, 'mark_asset_error',
        lambda conn, cur, run_id, chart_id, asset_id, error: errors.append(error),
    )

    conn = FakeConn()
    cur = FakeCursor()
    ar._run_data_writer(conn, cur, 'run-1', chart_id, writer_cls.asset_id)
    return cur, errors


def _duration_and_rate_written(cur: FakeCursor) -> tuple[object, object]:
    """Extract (duration_seconds, rows_per_second) from the completion UPDATE's params.
    params tuple order: (final_state, rows_written, upstream_hash, writer_hash,
    duration_seconds, rows_per_second, chart_id, asset_id) — see asset_runner.py's
    `UPDATE asset_throughput ... duration_seconds = %s, rows_per_second = %s` site."""
    rows = cur.params_for('duration_seconds = %s, rows_per_second = %s')
    assert rows, "expected exactly one completion UPDATE naming duration_seconds/rows_per_second"
    p = rows[-1]
    return p[4], p[5]


# ── A. Pure guard ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("rows_written,duration_seconds", [
    (10, None),
    (10, 0.0),
    (10, -1.0),
    (10, float("nan")),
    (10, float("inf")),
])
def test_guard_yields_null_null_never_zero_never_raises(rows_written, duration_seconds):
    """The one guard every success-completion write site must call. A missing, zero,
    negative, or non-finite duration must yield (None, None) — never (0, 0), never a
    ZeroDivisionError."""
    duration, rate = ar._compute_duration_and_rate(rows_written, duration_seconds)
    assert (duration, rate) == (None, None)


def test_guard_real_positive_duration_yields_real_rate():
    duration, rate = ar._compute_duration_and_rate(100, 4.0)
    assert duration == 4.0
    assert rate == pytest.approx(25.0)


def test_guard_zero_rows_with_real_duration_is_an_honest_zero_rate_not_null():
    """0 rows written over a genuinely-measured positive duration is a real,
    correctly-computed rate of 0.0 (the writer ran and wrote nothing) — this is
    different from an unknown/invalid duration, which must stay NULL."""
    duration, rate = ar._compute_duration_and_rate(0, 3.0)
    assert duration == 3.0
    assert rate == 0.0
    assert rate is not None


# ── C/D. _run_data_writer success completion write ──────────────────────────────

class _TimedWriter(WriterBase):
    """Self-reports a FALSE duration_seconds=4.0 while actually running near-
    instantly. C1: the engine must never use a writer's self-report as the
    persisted duration — its own time.monotonic() measurement around the call
    is the sole authority, and the writer's self-report (still a valid field on
    the frozen WriterResult contract) is never even consulted for this value."""
    asset_id = '_test_a1_timed'

    def run(self, ctx):
        return WriterResult(asset_id=self.asset_id, rows_inserted=8, rows_updated=2,
                             duration_seconds=4.0)


class _UntimedWriter(WriterBase):
    """Never sets duration_seconds — WriterResult defaults it to 0.0. This was the
    common case under A1's original design (most of the 129 writers; measured
    coverage: bg 30/32, mi 14/14, ka 2/23, ga 1/19, bo 0/24, ph 0/8). Sleeps a
    small, real, measurable amount of wall-clock time inside run() so the test
    can prove the ENGINE's own timing (C1) picks this up regardless of what the
    writer self-reports."""
    asset_id = '_test_a1_untimed'

    def run(self, ctx):
        time.sleep(0.02)
        return WriterResult(asset_id=self.asset_id, rows_inserted=5, rows_updated=0)


def test_completed_build_records_engine_measured_duration_not_writer_self_report(monkeypatch):
    """C1 (gate review F-1): the engine times its OWN call into the writer with
    time.monotonic() — a writer's self-report must never be persisted verbatim.
    Fails under A1's original (pre-correction) behaviour, which would have
    recorded exactly the writer's false claim of 4.0, not the real near-instant
    elapsed time."""
    cur, errors = _run_with_writer(monkeypatch, _TimedWriter, 'chart-abc')
    assert errors == []
    duration, rate = _duration_and_rate_written(cur)
    assert duration is not None
    # Real wall time for this trivial call is near-instant — nowhere near the
    # writer's false 4.0s claim, which the engine never reads for this purpose.
    assert duration < 1.0
    assert duration != 4.0
    assert rate == pytest.approx(10 / duration)  # rows_written=10 (8 inserted + 2 updated)


def test_untimed_writer_still_gets_a_real_engine_measured_duration(monkeypatch):
    """C1's whole point, and the exact proof the gate review demanded: a writer
    that never sets duration_seconds must still get a real, positive engine-
    measured duration and rate. Fails without the C1 fix: pre-fix, _drive_substeps
    summed only `result.duration_seconds` (default 0.0 here, regardless of the
    real ~20ms this writer actually took), so the completion write would have
    recorded NULL/NULL despite the engine having spent real, measurable wall-
    clock time invoking the writer."""
    cur, errors = _run_with_writer(monkeypatch, _UntimedWriter, 'chart-abc')
    assert errors == []
    duration, rate = _duration_and_rate_written(cur)
    assert duration is not None and duration > 0.0
    assert rate is not None and rate == pytest.approx(5 / duration)  # rows_written=5


# ── E. Failure path never touches duration/rate ──────────────────────────────────

class _BoomWriter(WriterBase):
    asset_id = '_test_a1_boom'

    def run(self, ctx):
        raise RuntimeError('writer exploded')


def test_real_mark_asset_error_sql_never_names_duration_or_rate(monkeypatch):
    """Direct unit test of the real (unmocked) mark_asset_error — the SQL text itself
    must never name duration_seconds/rows_per_second. Complements
    test_failed_build_never_writes_duration_or_rate, which proves the control-flow
    path never reaches the completion-write site; this proves the failure-path
    function itself was not edited to add these columns."""
    monkeypatch.setattr(ar, 'emit_event', lambda e, cur=None: None)
    conn, cur = FakeConn(), FakeCursor()
    ar.mark_asset_error(conn, cur, 'run-1', 'chart-abc', '_test_a1_direct_error', 'boom')
    assert not any('duration_seconds' in s for s in cur.sqls())
    assert not any('rows_per_second' in s for s in cur.sqls())
    assert any("state = 'error'" in s for s in cur.sqls())


def test_failed_build_never_writes_duration_or_rate(monkeypatch):
    """This is the one that matters (packet's own words): a genuinely-failed build
    must record NO rate — a real NULL — never a zero. mark_asset_error's UPDATE
    (asset_runner.py:584-591) sets state='error'/last_error/last_built_at only; it
    must never be extended to touch duration_seconds/rows_per_second, and the
    completion-write site that DOES set them must never be reached on this path."""
    cur, errors = _run_with_writer(monkeypatch, _BoomWriter, 'chart-abc')
    assert len(errors) == 1
    assert 'writer exploded' in errors[0]
    # The success-completion UPDATE (the only site that ever sets these two columns)
    # must never have run on this path.
    assert not any('duration_seconds' in s for s in cur.sqls())
    assert not any('rows_per_second' in s for s in cur.sqls())


# ── F. Legacy L1 telemetry helper (ga_writers/_telemetry.py) ─────────────────────

def test_legacy_telemetry_guard_matches_orchestrator_guard():
    from ga_writers import _telemetry

    assert _telemetry._compute_duration_and_rate(10, None) == (None, None)
    assert _telemetry._compute_duration_and_rate(10, 0.0) == (None, None)
    assert _telemetry._compute_duration_and_rate(10, -5.0) == (None, None)
    assert _telemetry._compute_duration_and_rate(10, float('nan')) == (None, None)
    d, r = _telemetry._compute_duration_and_rate(10, 2.0)
    assert d == 2.0 and r == 5.0


def test_legacy_telemetry_no_duration_arg_writes_null_exactly_as_before(monkeypatch):
    """None of today's 8 ga_writers/*.py call sites (ga_dashas, ga_panchanga,
    ga_positions, ga_sade_sati, ga_sensitive, ga_strength, ga_structural, ga_tajaka —
    ga_vargas_writer.py defines its own unrelated local _update_asset_throughput
    no-op and is correctly excluded) pass duration_seconds (out of this packet's
    scope to edit them — an editing-a-writer stop condition per §8(2); see
    honest-limits). Confirms the extended helper is backward compatible: an
    unmodified call site still writes NULL/NULL, unchanged from before this
    packet."""
    from ga_writers import _telemetry

    captured: list[tuple[str, list]] = []

    class _FakeConnCtx:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class _FakeTelemetryConn:
        def transaction(self):
            return _FakeConnCtx()

        def execute(self, sql, params):
            captured.append((sql, params))

    _telemetry.update_asset_throughput(
        _FakeTelemetryConn(), 'ga_test', 'chart-abc', 'build-1', 42, state='lit',
    )
    assert len(captured) == 1
    _, params = captured[0]
    # params: [chart_id, asset_id, state, rows_written, build_id, duration_clean, rate]
    assert params[-2:] == [None, None]


def test_legacy_telemetry_with_duration_computes_real_rate(monkeypatch):
    from ga_writers import _telemetry

    captured: list[tuple[str, list]] = []

    class _FakeConnCtx:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class _FakeTelemetryConn:
        def transaction(self):
            return _FakeConnCtx()

        def execute(self, sql, params):
            captured.append((sql, params))

    _telemetry.update_asset_throughput(
        _FakeTelemetryConn(), 'ga_test', 'chart-abc', 'build-1', 40, state='lit',
        duration_seconds=8.0,
    )
    _, params = captured[0]
    assert params[-2:] == [8.0, 5.0]


# ── G. C2 — graceful degradation when the column does not exist yet ──────────────

def test_degraded_write_when_duration_columns_absent_build_still_completes(monkeypatch):
    """C2 (gate review F-2): migration 1094 may not yet be applied when this code
    deploys -- the exact §N.4 hazard (a migration silently no-op'ing while the
    deploy reports success) must never be build-fatal. When duration_seconds/
    rows_per_second are absent from asset_throughput, the completion write must
    degrade gracefully: the build still completes (the completion UPDATE still
    runs and still sets state/rows_written/hashes), and it simply never names
    duration_seconds/rows_per_second at all. Fails if the completion write ever
    unconditionally names those columns: this test's cursor never has a matching
    'duration_seconds'/'rows_per_second' column to probe against, so an
    unconditional UPDATE would (in a real DB) raise
    `column "duration_seconds" does not exist`."""
    cur, errors = _run_with_writer(
        monkeypatch, _TimedWriter, 'chart-abc', duration_columns_present=False,
    )
    assert errors == []
    # The one completion UPDATE (identified by a column unique to that site, so
    # it can't be confused with the heartbeat or build_run_assets UPDATEs).
    completion_updates = [s for s in cur.sqls() if 'built_against_writer_hash' in s]
    assert len(completion_updates) == 1, "expected exactly one completion UPDATE"
    assert 'duration_seconds' not in completion_updates[0]
    assert 'rows_per_second' not in completion_updates[0]
    # The build still completed successfully -- state/rows_written/hashes are
    # still recorded, just without the two duration columns.
    assert 'SET state = %s' in completion_updates[0]
    assert 'rows_written = %s' in completion_updates[0]


def test_duration_columns_present_probes_information_schema_once_and_caches(monkeypatch):
    """C2: the presence probe must be cached once per process, never re-run per
    write. Simulates the column being present (a truthy fetchone) and asserts a
    second call does not issue a second information_schema query."""
    monkeypatch.setattr(ar, '_DURATION_COLUMNS_PRESENT', None)

    class _ProbeCursor:
        def __init__(self):
            self.executed: list[str] = []

        def execute(self, sql, params=None):
            self.executed.append(sql)

        def fetchone(self):
            return {'?column?': 1}  # simulates a matching information_schema row

    cur = _ProbeCursor()
    assert ar._duration_columns_present(cur) is True
    assert ar._duration_columns_present(cur) is True
    info_schema_calls = [s for s in cur.executed if 'information_schema' in s]
    assert len(info_schema_calls) == 1, "must probe information_schema at most once per process"


def test_duration_columns_absent_detected_and_cached(monkeypatch):
    """The absent-column branch of the same cache: fetchone() returning None (no
    matching information_schema row) must cache False, not crash or re-probe."""
    monkeypatch.setattr(ar, '_DURATION_COLUMNS_PRESENT', None)

    class _ProbeCursor:
        def __init__(self):
            self.executed: list[str] = []

        def execute(self, sql, params=None):
            self.executed.append(sql)

        def fetchone(self):
            return None

    cur = _ProbeCursor()
    assert ar._duration_columns_present(cur) is False
    assert ar._duration_columns_present(cur) is False
    info_schema_calls = [s for s in cur.executed if 'information_schema' in s]
    assert len(info_schema_calls) == 1


def test_duration_columns_absent_logs_warning_once(monkeypatch, caplog):
    """R-2 (gate review A1_rereview_20260926T132725Z.md N-2): the absence branch must
    be observable, not merely honest. Without this, an operator reading a NULL
    duration_seconds cannot tell "this build wasn't timed" (an ordinary skip) from
    "migration 1094 never applied here, so nothing will EVER be timed" (a silent,
    permanent, fleet-wide measurement outage — the §N.4 no-op-migration hazard one
    layer up). Asserts the warning fires exactly once, matching the probe's own
    once-per-process cardinality (a second call must not re-log), and names both the
    missing column and the migration so an operator knows what to do."""
    monkeypatch.setattr(ar, '_DURATION_COLUMNS_PRESENT', None)
    monkeypatch.setattr(ar, 'emit_event', lambda e, cur=None: None)

    class _ProbeCursor:
        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return None

    cur = _ProbeCursor()
    with caplog.at_level('WARNING', logger='pipeline.orchestrator.asset_runner'):
        assert ar._duration_columns_present(cur) is False
        assert ar._duration_columns_present(cur) is False  # cached — must not re-log

    warnings = [r for r in caplog.records if r.levelname == 'WARNING']
    assert len(warnings) == 1, "must warn exactly once per process, not once per probe call"
    assert 'duration_seconds' in warnings[0].message
    assert '1094' in warnings[0].message


def test_duration_columns_present_logs_no_warning(monkeypatch, caplog):
    """The mirror case: when the column IS present, nothing about a measurement
    outage should be logged at all — a healthy environment must stay silent."""
    monkeypatch.setattr(ar, '_DURATION_COLUMNS_PRESENT', None)
    monkeypatch.setattr(ar, 'emit_event', lambda e, cur=None: None)

    class _ProbeCursor:
        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return {'?column?': 1}

    cur = _ProbeCursor()
    with caplog.at_level('WARNING', logger='pipeline.orchestrator.asset_runner'):
        assert ar._duration_columns_present(cur) is True

    warnings = [r for r in caplog.records if r.levelname == 'WARNING']
    assert warnings == []


def test_duration_columns_absent_emits_event(monkeypatch):
    """R-2's "ideally + emit_event" half: the absence branch also emits an event
    (for whatever sink is listening — stdout/Pub/Sub, per events.py), exactly once,
    with a message that identifies the missing column and the migration. Present
    branch must emit nothing (mirrors the no-warning assertion above)."""
    monkeypatch.setattr(ar, '_DURATION_COLUMNS_PRESENT', None)
    emitted: list[dict] = []
    monkeypatch.setattr(ar, 'emit_event', lambda e, cur=None: emitted.append(e))

    class _AbsentProbeCursor:
        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return None

    cur = _AbsentProbeCursor()
    assert ar._duration_columns_present(cur) is False
    assert ar._duration_columns_present(cur) is False  # cached — must not re-emit
    assert len(emitted) == 1
    assert emitted[0]['type'] == 'asset.duration_columns_absent'
    assert 'duration_seconds' in emitted[0]['message']
    assert '1094' in emitted[0]['message']

    monkeypatch.setattr(ar, '_DURATION_COLUMNS_PRESENT', None)
    emitted.clear()

    class _PresentProbeCursor:
        def execute(self, sql, params=None):
            pass

        def fetchone(self):
            return {'?column?': 1}

    cur = _PresentProbeCursor()
    assert ar._duration_columns_present(cur) is True
    assert emitted == []


def test_duration_columns_probe_is_schema_qualified(monkeypatch):
    """R-7 (gate review N-6): the presence probe must filter table_schema, so a
    same-named table in another schema of a multi-schema deployment can never
    produce a false positive here (which would make the completion UPDATE name a
    column that doesn't exist in THIS asset_throughput, raise, and reintroduce the
    exact build-fatal hazard C2/the cache exists to prevent)."""
    monkeypatch.setattr(ar, '_DURATION_COLUMNS_PRESENT', None)
    monkeypatch.setattr(ar, 'emit_event', lambda e, cur=None: None)

    class _ProbeCursor:
        def __init__(self):
            self.executed: list[tuple[str, object]] = []

        def execute(self, sql, params=None):
            self.executed.append((sql, params))

        def fetchone(self):
            return None

    cur = _ProbeCursor()
    ar._duration_columns_present(cur)
    sql, _ = cur.executed[0]
    assert 'table_schema' in sql, "probe must filter table_schema, not just table_name"
