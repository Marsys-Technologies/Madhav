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
    asset_id = 'ga_heavy'
    has_substeps = True
    def plan_substeps(self, ctx):
        return [SubStep(key=f'sys{i}', label=f'system {i}') for i in range(3)]
    def run_substep(self, ctx, step):
        return WriterResult(asset_id=self.asset_id, rows_inserted=10)


def test_driver_runs_each_substep_with_heartbeat(monkeypatch):
    events: list[dict] = []
    monkeypatch.setattr(asset_runner, 'emit_event', lambda e, cur=None: events.append(e))

    conn, cur = FakeConn(), FakeCursor()
    ins, upd = asset_runner._drive_substeps(
        conn, cur, 'run-1', 'chart-C', 'ga_heavy', _Heavy3(), _ctx(conn),
    )

    assert (ins, upd) == (30, 0)
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


def test_driver_resume_skips_completed(monkeypatch):
    events: list[dict] = []
    monkeypatch.setattr(asset_runner, 'emit_event', lambda e, cur=None: events.append(e))

    runs = {'n': 0}

    class Heavy3Counting(_Heavy3):
        def run_substep(self, ctx, step):
            runs['n'] += 1
            return WriterResult(asset_id=self.asset_id, rows_inserted=10)

    conn, cur = FakeConn(), FakeCursor()
    ins, upd = asset_runner._drive_substeps(
        conn, cur, 'run-1', 'chart-C', 'ga_heavy', Heavy3Counting(), _ctx(conn),
        completed_keys={'sys0', 'sys1'},
    )

    # only sys2 actually executed; sys0/sys1 skipped
    assert runs['n'] == 1
    assert (ins, upd) == (10, 0)
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
