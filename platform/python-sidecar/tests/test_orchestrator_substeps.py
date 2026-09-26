"""Orchestrator Convergence Phase 2 — frozen WriterBase sub-step contract + driver.

Two halves:

A. Frozen contract (pure, no DB): the ONE generalization baked into WriterBase —
   declarable sub-steps. A light writer implements run() and never sees sub-steps;
   a heavy writer overrides plan_substeps + run_substep and gets a working run()
   for free; an unimplemented writer raises NotImplementedError.

B. Sub-step driver (_drive_substeps, FakeConn/FakeCursor — no real DB): plan →
   run-each (one SAVEPOINT + last_built_at heartbeat + commit + asset.substep SSE
   per sub-step) → resume-skips-completed → a failed sub-step rolls back to its
   savepoint and re-raises (prior committed sub-steps stay durable).
"""

import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.writers import (  # noqa: E402
    WriterBase, WriterResult, ContextSpec, SubStep,
)
from pipeline.orchestrator import asset_runner  # noqa: E402


# ── Fakes ─────────────────────────────────────────────────────────────────────

class FakeCursor:
    def __init__(self):
        self.executed: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def sqls(self) -> list[str]:
        return [s for s, _ in self.executed]


class FakeConn:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


def _ctx(conn):
    return ContextSpec(asset_id='ga_test', build_id='run-1', db_conn=conn,
                       config={'chart_id': 'chart-C'})


# ── A. Frozen contract ─────────────────────────────────────────────────────────

def test_substep_label_defaults_to_key():
    assert SubStep(key='vimshottari:lahiri').label == 'vimshottari:lahiri'
    assert SubStep(key='k', label='Pretty').label == 'Pretty'


def test_plan_substeps_default_is_single_whole_asset():
    class Light(WriterBase):
        asset_id = 'ga_light'
        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=7)

    steps = Light().plan_substeps(_ctx(FakeConn()))
    assert len(steps) == 1
    assert steps[0].key == 'ga_light'


def test_run_substep_default_delegates_to_run():
    """A light writer's run_substep (default) routes to its run()."""
    calls = {'run': 0}

    class Light(WriterBase):
        asset_id = 'ga_light'
        def run(self, ctx):
            calls['run'] += 1
            return WriterResult(asset_id=self.asset_id, rows_inserted=3)

    w = Light()
    r = w.run_substep(_ctx(FakeConn()), SubStep(key='ga_light'))
    assert r.rows_inserted == 3
    assert calls['run'] == 1


def test_heavy_writer_run_drives_its_substeps():
    """A heavy writer (plan_substeps + run_substep, no run) gets a working run()."""
    class Heavy(WriterBase):
        asset_id = 'ga_heavy'
        has_substeps = True
        def plan_substeps(self, ctx):
            return [SubStep(key=f'sys{i}') for i in range(3)]
        def run_substep(self, ctx, step):
            return WriterResult(asset_id=self.asset_id, rows_inserted=10, rows_updated=1)

    agg = Heavy().run(_ctx(FakeConn()))
    assert agg.rows_inserted == 30
    assert agg.rows_updated == 3


def test_unimplemented_writer_raises():
    """Neither run() nor run_substep() overridden → NotImplementedError, no recursion."""
    class Broken(WriterBase):
        asset_id = 'ga_broken'

    with pytest.raises(NotImplementedError):
        Broken().run(_ctx(FakeConn()))
    # Orchestrator calls run_substep (default) → run() (default) → raises, not loops.
    with pytest.raises(NotImplementedError):
        Broken().run_substep(_ctx(FakeConn()), SubStep(key='ga_broken'))


# ── B. Sub-step driver ──────────────────────────────────────────────────────────

class _Heavy3(WriterBase):
    """Self-reports duration_seconds=999.0 — an obviously-irrelevant value, to
    prove C1's engine-side timing never consults it (see the test below, which
    controls time.monotonic() to a known sequence and asserts the persisted
    duration is the CONTROLLED clock's 7.5, not 3 x 999.0)."""
    asset_id = 'ga_heavy'
    has_substeps = True
    def plan_substeps(self, ctx):
        return [SubStep(key=f'sys{i}', label=f'system {i}') for i in range(3)]
    def run_substep(self, ctx, step):
        return WriterResult(asset_id=self.asset_id, rows_inserted=10, duration_seconds=999.0)


def _fake_monotonic(monkeypatch, *ticks: float):
    """Monkeypatch asset_runner.time.monotonic() to return `ticks` in sequence —
    deterministic, no real sleep required. `_drive_substeps` calls it exactly
    twice (start, end) per EXECUTED sub-step and zero times per skipped one."""
    it = iter(ticks)
    monkeypatch.setattr(asset_runner.time, 'monotonic', lambda: next(it))


def test_driver_runs_each_substep_with_heartbeat(monkeypatch):
    """C1: _drive_substeps must time the ENGINE's own call into
    writer.run_substep() with time.monotonic(), summing each executed sub-
    step's real elapsed wall time — NOT the writer's self-reported
    WriterResult.duration_seconds (_Heavy3 sets that to an irrelevant 999.0
    precisely to prove it has no effect). Fails without the C1 fix: a driver
    that instead summed the writer's self-report would compute 3 x 999.0 =
    2997.0, not this test's controlled-clock 7.5."""
    events: list[dict] = []
    monkeypatch.setattr(asset_runner, 'emit_event', lambda e, cur=None: events.append(e))
    _fake_monotonic(monkeypatch, 0.0, 2.5, 2.5, 5.0, 5.0, 7.5)

    conn, cur = FakeConn(), FakeCursor()
    ins, upd, dur = asset_runner._drive_substeps(
        conn, cur, 'run-1', 'chart-C', 'ga_heavy', _Heavy3(), _ctx(conn),
    )

    assert (ins, upd) == (30, 0)
    assert dur == pytest.approx(7.5)  # engine-measured: 3 sub-steps x 2.5s each (controlled clock)
    sqls = cur.sqls()
    # one SAVEPOINT + RELEASE per sub-step (3 each)
    assert sqls.count('SAVEPOINT writer_exec') == 3
    assert sqls.count('RELEASE SAVEPOINT writer_exec') == 3
    # one heartbeat UPDATE per sub-step, and one commit per sub-step
    assert sum('UPDATE asset_throughput' in s and 'last_built_at = NOW()' in s for s in sqls) == 3
    assert conn.commits == 3
    # granular SSE: 3 asset.substep events, indices 1..3, cumulative rows advancing
    subs = [e for e in events if e['type'] == 'asset.substep']
    assert [e['index'] for e in subs] == [1, 2, 3]
    assert [e['total'] for e in subs] == [3, 3, 3]
    assert [e['rows_written'] for e in subs] == [10, 20, 30]
    assert subs[1]['substep_label'] == 'system 1'


def test_integrity_gated_driver_defers_every_substep_commit(monkeypatch):
    """A final detector failure must be able to roll back every substep."""
    monkeypatch.setattr(asset_runner, 'emit_event', lambda e, cur=None: None)
    _fake_monotonic(monkeypatch, 0.0, 2.5, 2.5, 5.0, 5.0, 7.5)

    conn, cur = FakeConn(), FakeCursor()
    ins, upd, dur = asset_runner._drive_substeps(
        conn, cur, 'run-1', 'chart-C', 'ga_heavy', _Heavy3(), _ctx(conn),
        defer_commits=True,
    )

    assert (ins, upd) == (30, 0)
    assert dur == pytest.approx(7.5)  # engine-measured (controlled clock), not writer self-report
    assert conn.commits == 0


def test_driver_resume_skips_completed(monkeypatch):
    events: list[dict] = []
    monkeypatch.setattr(asset_runner, 'emit_event', lambda e, cur=None: events.append(e))
    _fake_monotonic(monkeypatch, 10.0, 11.25)  # only sys2 executes -> one start/end pair

    runs = {'n': 0}

    class Heavy3Counting(_Heavy3):
        def run_substep(self, ctx, step):
            runs['n'] += 1
            # Irrelevant self-report (C1 never reads it) -- distinct from _Heavy3's
            # 999.0 only to prove per-class self-reports are equally ignored.
            return WriterResult(asset_id=self.asset_id, rows_inserted=10, duration_seconds=1234.0)

    conn, cur = FakeConn(), FakeCursor()
    ins, upd, dur = asset_runner._drive_substeps(
        conn, cur, 'run-1', 'chart-C', 'ga_heavy', Heavy3Counting(), _ctx(conn),
        completed_keys={'sys0', 'sys1'},
    )

    # only sys2 actually executed; sys0/sys1 skipped
    assert runs['n'] == 1
    assert (ins, upd) == (10, 0)
    # a skipped sub-step contributes 0 to duration and is never timed -- it did
    # no work this run, so only sys2's own engine-measured 1.25s counts (the
    # controlled clock), not the writer's self-reported 1234.0.
    assert dur == pytest.approx(1.25)
    assert cur.sqls().count('SAVEPOINT writer_exec') == 1
    assert conn.commits == 1
    skipped = [e for e in events if e['type'] == 'asset.substep' and e.get('skipped')]
    assert {e['substep_key'] for e in skipped} == {'sys0', 'sys1'}


def test_driver_failure_rolls_back_substep_and_reraises(monkeypatch):
    events: list[dict] = []
    monkeypatch.setattr(asset_runner, 'emit_event', lambda e, cur=None: events.append(e))

    class Heavy3Boom(_Heavy3):
        def run_substep(self, ctx, step):
            if step.key == 'sys1':
                raise ValueError('boom on chunk 2')
            return WriterResult(asset_id=self.asset_id, rows_inserted=10)

    conn, cur = FakeConn(), FakeCursor()
    with pytest.raises(ValueError, match='boom'):
        asset_runner._drive_substeps(
            conn, cur, 'run-1', 'chart-C', 'ga_heavy', Heavy3Boom(), _ctx(conn),
        )

    sqls = cur.sqls()
    # the failed sub-step rolled back to its savepoint (not released)
    assert sqls.count('ROLLBACK TO SAVEPOINT writer_exec') == 1
    # chunk 0 committed durably before the failure; chunk 2 never ran
    assert conn.commits == 1
    assert sqls.count('RELEASE SAVEPOINT writer_exec') == 1  # only sys0 released
    assert not any(e.get('substep_key') == 'sys2' for e in events)
