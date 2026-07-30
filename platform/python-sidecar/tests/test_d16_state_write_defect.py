"""Pre-D-2 fix — D-1.6 asset_throughput state-write defect (run 71b260c7).

Deterministic reproduction + regression tests for the incident documented in
00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/REPORT_D-1.6.md:

  ka_sangam's cross-attempt substep-resumption ledger (build_substep_progress,
  migration 436) found ALL 61 substeps already committed under a matching
  same-day fingerprint, so plan_substeps() returned an EMPTY substep list.
  _drive_substeps therefore reported rows_written=0, and _run_data_writer's
  zero-rows heuristic marked the asset 'dormant' — even though all 2,488
  kala_convergence rows were present and correct. Every downstream DEP-ASSERT
  then saw ka_sangam(dormant) and cascaded 24 BLOCKED errors.

Fixes under test (pipeline/orchestrator/asset_runner.py):
  1. No-op-completion reclassification: before accepting 'dormant', probe the
     asset's actual data via its chart-scoped count_sql; rows present → 'lit'.
  2. _guard_state_write: a state UPDATE matching 0 rows is logged loudly and
     recovered via upsert instead of being silently lost.
  3. DEP-ASSERT anomaly diagnostics: blocking on a dep whose data is
     demonstrably present logs/annotates expected-vs-actual state + row count.

All tests use fakes — no live DB. Writers are NOT @register-decorated (would
pollute the global registry and break test_has_writer_completeness).
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar
from pipeline.orchestrator.writers import SubStep, WriterBase, WriterResult


# ── Fakes ─────────────────────────────────────────────────────────────────────

COUNT_SQL = "SELECT count(*) FROM kala_convergence WHERE chart_id = $1"


class FakeCursor:
    """Scriptable cursor: answers registry/count queries; records everything."""

    def __init__(self, rows_present: int | None = None, count_sql: str | None = COUNT_SQL,
                 target_floor=None, rowcount: int = 1, has_substeps: bool | None = None):
        self.executed: list[tuple[str, object]] = []
        self._rows_present = rows_present
        self._count_sql = count_sql
        self._target_floor = target_floor
        self._has_substeps = has_substeps
        self.rowcount = rowcount
        self._next_fetch = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        s = " ".join(sql.split())
        self._next_fetch = None
        if "SELECT count_sql FROM asset_registry" in s:
            self._next_fetch = {"count_sql": self._count_sql}
        elif "SELECT target_floor FROM asset_registry" in s:
            self._next_fetch = {"target_floor": self._target_floor}
        elif "SELECT has_substeps FROM asset_registry" in s:
            self._next_fetch = {"has_substeps": self._has_substeps}
        elif self._count_sql and s.startswith(self._count_sql.replace("$1", "%s").split(" WHERE")[0]):
            self._next_fetch = {"count": self._rows_present}

    def fetchone(self):
        return self._next_fetch

    def fetchall(self):
        return []

    def params_for(self, keyword: str) -> list[tuple]:
        return [p for s, p in self.executed if keyword in s]

    def sqls_containing(self, keyword: str) -> list[str]:
        return [s for s, _ in self.executed if keyword in s]


class FakeConn:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


class _ResumeSkipAllWriter(WriterBase):
    """Mimics ka_sangam when the resumption ledger says every substep is already
    committed: plan_substeps returns an EMPTY list, so zero rows are reported."""
    asset_id = "_test_resume_skip_all"

    def plan_substeps(self, ctx):
        return []

    def run(self, ctx):  # pragma: no cover — never reached with empty plan
        return WriterResult(asset_id=self.asset_id, rows_inserted=0, rows_updated=0)


class _ZeroRowWriter(WriterBase):
    asset_id = "_test_zero_rows_d16"

    def run(self, ctx):
        return WriterResult(asset_id=self.asset_id, rows_inserted=0, rows_updated=0)


class _PartialPlanWriter(WriterBase):
    """SATYA-DIPA: mimics a genuinely-incomplete resumable writer — a substep
    still remains (plan_substeps() reports non-empty) even though this round's
    chunk nets zero rows and earlier-committed chunks left data present. Unlike
    _ResumeSkipAllWriter (D-1.6's true shape: plan_substeps() reports EMPTY,
    meaning nothing is left), this writer's own bookkeeping says work remains —
    the no-op-completion rescue must not paper over that."""
    asset_id = "_test_partial_plan_satyadipa"

    def plan_substeps(self, ctx):
        return [SubStep(key="year:79", label="year 79")]

    def run_substep(self, ctx, step):
        return WriterResult(asset_id=self.asset_id, rows_inserted=0, rows_updated=0)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _patch_common(monkeypatch, writer_cls, events: list | None = None):
    monkeypatch.setattr(ar, "emit_event",
                        (lambda e, cur=None: events.append(e)) if events is not None
                        else (lambda e, cur=None: None))
    monkeypatch.setattr(ar, "discover_all", lambda: None)
    monkeypatch.setattr(ar, "get_writer", lambda aid: writer_cls)
    monkeypatch.setattr(ar, "fetch_birth_params", lambda conn, cid: {"chart_id": cid})
    monkeypatch.setattr(ar, "compute_upstream_hash", lambda cur, aid, cid: "hash-upstream")
    monkeypatch.setattr(ar, "get_writer_git_hash", lambda aid: "hash-writer")
    monkeypatch.setattr(ar, "compute_downstream_closure", lambda cur, aid: [])


def _final_state(cur: FakeCursor):
    params_list = cur.params_for("SET state = %s")
    return params_list[-1][0] if params_list else None


def _final_rows_written(cur: FakeCursor):
    params_list = cur.params_for("SET state = %s")
    return params_list[-1][1] if params_list else None


# ── 1. Deterministic D-1.6 reproduction: no-op completion → 'lit', not 'dormant'

def test_d16_repro_resume_skip_all_with_data_present_marks_lit(monkeypatch):
    """THE incident shape: writer plans zero substeps (resume ledger complete),
    reports 0 rows, but 2,488 data rows exist → must be 'lit', not 'dormant'."""
    events: list = []
    _patch_common(monkeypatch, _ResumeSkipAllWriter, events)
    conn, cur = FakeConn(), FakeCursor(rows_present=2488)
    ar._run_data_writer(conn, cur, "run-71b260c7", "chart-482012f1", _ResumeSkipAllWriter.asset_id)
    assert _final_state(cur) == "lit", (
        "D-1.6 regression: 0-rows-this-run with data present must be 'lit', got %r"
        % _final_state(cur)
    )
    # rows_written should reflect the present data, not 0 (cockpit truth)
    assert _final_rows_written(cur) == 2488
    # and the reclassification must be loud (event emitted)
    assert any(e.get("type") == "asset.noop_completion" for e in events)


def test_satyadipa_d16_preserved_through_completeness_check(monkeypatch):
    """D-1.6 preserved THROUGH the new substep-completeness check (not merely by
    bypassing it): has_substeps=True (so the new check IS exercised) AND
    plan_substeps() still reports empty (truly nothing left) -> must stay 'lit',
    downstream deps must stay unblocked. A fix that trades false-unblocking for
    false-blocking is not a fix (SATYA_DIPA_BRIEF_v1_0.md, prime directive)."""
    events: list = []
    _patch_common(monkeypatch, _ResumeSkipAllWriter, events)
    conn, cur = FakeConn(), FakeCursor(rows_present=2488, has_substeps=True)
    ar._run_data_writer(conn, cur, "run-71b260c7", "chart-482012f1", _ResumeSkipAllWriter.asset_id)
    assert _final_state(cur) == "lit", (
        "D-1.6 regression THROUGH the completeness check: the writer's own "
        "plan_substeps() confirms nothing remains -> must still promote to 'lit', "
        "got %r" % _final_state(cur)
    )
    assert _final_rows_written(cur) == 2488
    assert any(e.get("type") == "asset.noop_completion" for e in events)


def test_satyadipa_partial_substep_plan_with_rows_present_not_lit(monkeypatch):
    """THE SATYA-DIPA fix: has_substeps=True AND the writer's own plan_substeps()
    reports a substep still remaining, even though this round nets 0 rows and
    data from earlier committed substeps IS present -> must NOT be reclassified
    to 'lit' (would falsely unblock downstream on an incomplete build). Must not
    be 'dormant' either (data is not absent) -> new 'incomplete' state."""
    events: list = []
    _patch_common(monkeypatch, _PartialPlanWriter, events)
    conn, cur = FakeConn(), FakeCursor(rows_present=1267, has_substeps=True)
    ar._run_data_writer(conn, cur, "run-partial", "chart-1c826d5a", _PartialPlanWriter.asset_id)
    final = _final_state(cur)
    assert final not in ("lit", "service_ok"), (
        "SATYA-DIPA regression: a genuinely partial substep plan with rows present "
        "must not satisfy downstream dependency gating, got %r" % final
    )
    assert final == "incomplete", final
    assert any(e.get("type") == "asset.noop_completion_rejected" for e in events)
    rejected = [e for e in events if e.get("type") == "asset.noop_completion_rejected"][0]
    assert rejected["rows_present"] == 1267
    assert rejected["substeps_remaining"] == 1


def test_satyadipa_light_writer_no_substep_plan_behaves_as_before(monkeypatch):
    """has_substeps unset/False (light writer, no real substep plan) -> the new
    completeness check does not apply at all; old no-op-completion behavior
    holds unchanged (SATYA_DIPA_BRIEF_v1_0.md §4.1: "An asset with no substep
    plan defined behaves as before")."""
    events: list = []
    _patch_common(monkeypatch, _ZeroRowWriter, events)
    conn, cur = FakeConn(), FakeCursor(rows_present=45, has_substeps=False)
    ar._run_data_writer(conn, cur, "run-1", "chart-abc", _ZeroRowWriter.asset_id)
    assert _final_state(cur) == "lit"
    assert any(e.get("type") == "asset.noop_completion" for e in events)


def test_d16_zero_rows_and_no_data_stays_dormant(monkeypatch):
    """A genuine dormant (0 rows this run AND no data present) is unchanged."""
    _patch_common(monkeypatch, _ZeroRowWriter)
    conn, cur = FakeConn(), FakeCursor(rows_present=0)
    ar._run_data_writer(conn, cur, "run-1", "chart-abc", _ZeroRowWriter.asset_id)
    assert _final_state(cur) == "dormant"


def test_d16_zero_rows_probe_unavailable_stays_dormant(monkeypatch):
    """No count_sql defined → probe abstains → prior behavior ('dormant') holds."""
    _patch_common(monkeypatch, _ZeroRowWriter)
    conn, cur = FakeConn(), FakeCursor(rows_present=None, count_sql=None)
    ar._run_data_writer(conn, cur, "run-1", "chart-abc", _ZeroRowWriter.asset_id)
    assert _final_state(cur) == "dormant"


# ── 2. Safety net: state UPDATE matching 0 rows is recovered, not lost ─────────

def test_guard_state_write_recovers_zero_rowcount(monkeypatch):
    events: list = []
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: events.append(e))
    cur = FakeCursor(rowcount=0)
    ar._guard_state_write(cur, "run-1", "chart-abc", "ka_sangam", "lit")
    inserts = cur.sqls_containing("INSERT INTO asset_throughput")
    assert inserts, "0-rowcount state write must trigger a recovery upsert"
    assert any(e.get("type") == "asset.state_write_anomaly" for e in events)


def test_guard_state_write_noop_on_normal_rowcount(monkeypatch):
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)
    cur = FakeCursor(rowcount=1)
    ar._guard_state_write(cur, "run-1", "chart-abc", "ka_sangam", "lit")
    assert not cur.sqls_containing("INSERT INTO asset_throughput")


def test_guard_state_write_tolerates_missing_rowcount(monkeypatch):
    """Cursors without a rowcount attribute (fakes, exotic drivers) are a no-op."""
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)
    cur = FakeCursor(rowcount=1)
    del cur.rowcount
    ar._guard_state_write(cur, "run-1", "chart-abc", "ka_sangam", "lit")
    assert not cur.sqls_containing("INSERT INTO asset_throughput")


def test_mark_asset_error_zero_rowcount_recovers(monkeypatch):
    """mark_asset_error on a missing throughput row must not silently lose 'error'."""
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)
    conn, cur = FakeConn(), FakeCursor(rowcount=0)
    ar.mark_asset_error(conn, cur, "run-1", "chart-abc", "ka_sangam", "boom")
    assert cur.sqls_containing("INSERT INTO asset_throughput")


# ── 3. Safety net: DEP-ASSERT anomaly diagnostics ─────────────────────────────

def test_dep_assert_block_names_data_present_anomaly(monkeypatch):
    """Blocking on a dep whose data IS present must carry actionable diagnostics
    (expected vs actual state + observed row count) in the error and event stream."""
    events: list = []
    captured: dict = {}

    def fake_mark_error(conn, cur, run_id, chart_id, asset_id, msg):
        captured["msg"] = msg

    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: events.append(e))
    monkeypatch.setattr(ar, "deps_unsatisfied", lambda cur, cid, aid: ["ka_sangam(dormant)"])
    monkeypatch.setattr(ar, "mark_asset_error", fake_mark_error)
    monkeypatch.setattr(ar, "_data_rows_present", lambda conn, cur, aid, cid: 2488)

    conn, cur = FakeConn(), FakeCursor()
    ar.run_asset(conn, cur, "run-71b260c7", "chart-482012f1", "ka_kalasutra", 2)

    assert "ANOMALY" in captured.get("msg", ""), captured
    assert "2488" in captured["msg"]
    assert "dormant" in captured["msg"]
    anomaly_events = [e for e in events if e.get("type") == "asset.dep_assert_anomaly"]
    assert anomaly_events and anomaly_events[0]["dep_id"] == "ka_sangam"
    assert anomaly_events[0]["actual_state"] == "dormant"
    assert anomaly_events[0]["rows_present"] == 2488


def test_dep_assert_block_without_data_has_no_anomaly(monkeypatch):
    """A legitimate block (dep truly absent) must not claim an anomaly."""
    captured: dict = {}
    monkeypatch.setattr(ar, "emit_event", lambda e, cur=None: None)
    monkeypatch.setattr(ar, "deps_unsatisfied", lambda cur, cid, aid: ["ka_sangam(absent)"])
    monkeypatch.setattr(ar, "mark_asset_error",
                        lambda conn, cur, run_id, chart_id, asset_id, msg: captured.update(msg=msg))
    monkeypatch.setattr(ar, "_data_rows_present", lambda conn, cur, aid, cid: 0)

    conn, cur = FakeConn(), FakeCursor()
    ar.run_asset(conn, cur, "run-1", "chart-abc", "ka_kalasutra", 2)
    assert "ANOMALY" not in captured.get("msg", "")


# ── 4. _data_rows_present unit behavior ────────────────────────────────────────

def test_data_rows_present_reads_count_sql():
    cur = FakeCursor(rows_present=42)
    assert ar._data_rows_present(FakeConn(), cur, "ka_sangam", "chart-abc") == 42
    # probe must be savepoint-isolated
    assert cur.sqls_containing("SAVEPOINT presence_probe")


def test_data_rows_present_none_for_global_asset():
    cur = FakeCursor(rows_present=42)
    assert ar._data_rows_present(FakeConn(), cur, "bg_thing", None) is None


def test_data_rows_present_never_raises_on_broken_sql():
    class ExplodingCursor(FakeCursor):
        def execute(self, sql, params=None):
            super().execute(sql, params)
            if sql.startswith("SELECT count(*)"):
                raise RuntimeError("relation does not exist")

    cur = ExplodingCursor(rows_present=1)
    assert ar._data_rows_present(FakeConn(), cur, "ka_sangam", "chart-abc") is None
    # and it must have rolled back to the savepoint, not left the txn aborted
    assert cur.sqls_containing("ROLLBACK TO SAVEPOINT presence_probe")
