"""I-10: the stage-5 dhara-windows work is split into many small substeps.

ka_kshetra's 2026-09-11 build died with a lost database connection inside the ONE
long `stage5dhara:{ec}:2` substep. Writers must not manage connections
(`ctx.db_conn` belongs to the orchestrator, CLAUDE.md §N.2), so the fix lives
inside the frozen contract: `plan_substeps` emits `WINDOW_PARTS` small substeps per
class (`stage5dhara:{ec}:2:{p}`), each owning a disjoint `t_start` partition of the
class's windows. A connection loss then costs one small substep and the
orchestrator's existing per-substep savepoint/commit + the writer's own resume
ledger carry the rest.

These tests are DB-free (in-memory fake). Behaviour that is only SQL-text verified,
not executed against Postgres: the class-level COUNT(DISTINCT window_id)
detector (the fake emulates its documented meaning); the upsert ON CONFLICT clauses
are pre-existing SQL, unchanged.
"""
from __future__ import annotations

import copy
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from pipeline.orchestrator import asset_runner  # noqa: E402
from pipeline.orchestrator.writers import SubStep  # noqa: E402
from services.ka_kshetra import integrator  # noqa: E402
from services.ka_kshetra import stage4_field as S4  # noqa: E402
from services.ka_kshetra import writer as W  # noqa: E402
from services.ka_kshetra.integrator import Window  # noqa: E402
from tests.l3.ka_kshetra import fixtures as F  # noqa: E402
from tests.l3.ka_kshetra.fake_db import FakeConn, FakeCtx  # noqa: E402
from tests.l3.ka_kshetra.test_planning_safety import _TransactionalFakeConn  # noqa: E402
# Re-exported autouse fixture: shrinks horizon/replicates, isolates stages 0-3.
from tests.l3.ka_kshetra.test_writer import _small_build  # noqa: E402,F401

EC = F.EVENT_CLASS
H = 400.0  # the _small_build horizon

#: t_start values chosen to straddle every partition edge (edges every H/20 = 20 d):
#: exactly on an edge, one ulp-ish below, one above, plus the extremes.
STARTS = [0.0, 0.5, 19.999999, 20.0, 20.000001, 39.999, 40.0, 100.0, 199.999999,
          200.0, 200.000001, 359.9999, 360.0, 380.0, 398.0]


def _synthetic_windows(starts):
    return [Window(t_start=s, t_end=s + 1.0, t_peak=s + 0.5, lambda_peak=1.0,
                   expected_count=0.25, duration_days=1.0) for s in starts]


@pytest.fixture
def synthetic(monkeypatch):
    """Replace window detection with a fixed multi-window list. The §5.4 provenance
    reconciliation is exercised elsewhere (test_writer.py); here lambda_peak is a
    placeholder, so the reconciliation assertion is stubbed to isolate PARTITIONING."""
    state = {'starts': list(STARTS)}
    monkeypatch.setattr(
        integrator, 'find_windows',
        lambda segments, q: _synthetic_windows(sorted(state['starts'])))
    monkeypatch.setattr(S4, 'assert_provenance_reconciles', lambda *a, **k: None)
    return state


def _ctx(conn):
    return FakeCtx(conn, F.CHART_ID)


def _run(writer, ctx, steps):
    for s in steps:
        writer.run_substep(ctx, s)


def _snapshot_tables(conn):
    keep = ('kala_field_windows', 'kala_field_provenance', 'kala_field_null',
            'kala_field', 'kala_field_snapshots')
    out = {}
    for t in keep:
        rows = conn.tables.get(t, [])
        out[t] = sorted((tuple(sorted((k, repr(v)) for k, v in r.items())) for r in rows))
    return out


def _single_pass_steps(steps):
    """Collapse the parts back into the pre-I-10 single substep per class."""
    out, seen = [], set()
    for s in steps:
        parts = s.key.split(':')
        if parts[0] == 'stage5dhara' and len(parts) == 4:
            legacy = ':'.join(parts[:3])
            if legacy not in seen:
                seen.add(legacy)
                out.append(SubStep(key=legacy, label='legacy single-pass windows'))
            continue
        out.append(s)
    return out


# ── plan shape + determinism ─────────────────────────────────────────────────

class TestPlanShape:
    def test_dhara_windows_are_emitted_as_ordered_parts(self):
        conn = FakeConn(F.build_tables())
        steps = W.KaKshetraWriter().plan_substeps(_ctx(conn))
        keys = [s.key for s in steps]
        dh = [k for k in keys if k.startswith('stage5dhara:')]
        assert dh[0] == f'stage5dhara:{EC}:1'
        assert dh[1:] == [f'stage5dhara:{EC}:2:{p}' for p in range(W.WINDOW_PARTS)]
        assert f'stage5dhara:{EC}:2' not in keys, 'the old single windows substep is gone'
        assert keys.index(f'stage5dhara:{EC}:2:{W.WINDOW_PARTS - 1}') < keys.index('stage6')
        assert keys.index(f'stage5dhara:{EC}:1') < keys.index(f'stage5dhara:{EC}:2:0')
        assert len(set(keys)) == len(keys)

    def test_plan_is_deterministic(self):
        a = [(s.key, s.label) for s in
             W.KaKshetraWriter().plan_substeps(_ctx(FakeConn(F.build_tables())))]
        b = [(s.key, s.label) for s in
             W.KaKshetraWriter().plan_substeps(_ctx(FakeConn(F.build_tables())))]
        assert a == b

    def test_more_than_one_part_so_a_crash_costs_a_fraction(self):
        assert W.WINDOW_PARTS >= 10


# ── partition: disjoint + complete ───────────────────────────────────────────

class TestPartition:
    def test_edges_are_shared_exactly_between_neighbours(self):
        n = W.WINDOW_PARTS
        bounds = [W._window_part_bounds(p, n) for p in range(n)]
        assert bounds[0][0] is None and bounds[-1][1] is None
        for p in range(n - 1):
            assert bounds[p][1] == bounds[p + 1][0]          # bitwise equal, no gap/overlap
            assert bounds[p][1] is not None
        interior = [b[1] for b in bounds[:-1]]
        assert interior == sorted(interior) and len(set(interior)) == len(interior)

    def test_edges_align_with_stage4_decade_boundaries(self):
        # every DECADES-th... decade boundary d*H/DECADES is also a part edge
        n = W.WINDOW_PARTS
        edges = {W._window_part_bounds(p, n)[1] for p in range(n - 1)}
        for d in range(1, W.DECADES):
            assert d * W.HORIZON_DAYS / W.DECADES in edges

    @pytest.mark.parametrize('t', [-1e9, -1.0, -0.0, 0.0, 1e-12, 19.999999999, 20.0,
                                   20.0000000001, 199.99999999999997, 200.0, 399.9999999,
                                   400.0, 400.0000001, 1e9])
    def test_every_boundary_case_lands_in_exactly_one_part(self, t):
        n = W.WINDOW_PARTS
        hits = [p for p in range(n) if W._in_window_part(t, *W._window_part_bounds(p, n))]
        assert len(hits) == 1

    def test_random_starts_partition_exactly(self):
        rnd = random.Random(20261001)
        n = W.WINDOW_PARTS
        for _ in range(2000):
            t = rnd.uniform(-50.0, 450.0)
            hits = [p for p in range(n)
                    if W._in_window_part(t, *W._window_part_bounds(p, n))]
            assert len(hits) == 1

    def test_edge_start_belongs_to_the_part_it_opens(self):
        n = W.WINDOW_PARTS
        for p in range(1, n):
            lo, _ = W._window_part_bounds(p, n)
            assert W._in_window_part(lo, *W._window_part_bounds(p, n))
            assert not W._in_window_part(lo, *W._window_part_bounds(p - 1, n))


# ── union of parts == the single-pass result ────────────────────────────────

class TestUnionEqualsSinglePass:
    def _build(self, tables, steps_fn):
        conn = FakeConn(tables)
        ctx = _ctx(conn)
        writer = W.KaKshetraWriter()
        _run(writer, ctx, steps_fn(writer.plan_substeps(ctx)))
        return writer, conn

    def test_parts_write_exactly_the_single_pass_rows(self, synthetic):
        _, parted = self._build(F.build_tables(), lambda s: s)
        _, single = self._build(F.build_tables(), _single_pass_steps)
        assert len(parted.tables['kala_field_windows']) == len(STARTS)
        assert _snapshot_tables(parted) == _snapshot_tables(single)
        # content hash (the snapshot row) is part of the comparison above
        assert parted.tables['kala_field_snapshots'] == single.tables['kala_field_snapshots']

    def test_each_part_writes_only_windows_in_its_own_range(self, synthetic):
        conn = FakeConn(F.build_tables())
        ctx = _ctx(conn)
        writer = W.KaKshetraWriter()
        n = W.WINDOW_PARTS
        for step in writer.plan_substeps(ctx):
            before = {r['window_id'] for r in conn.tables.get('kala_field_windows', [])}
            writer.run_substep(ctx, step)
            after = {r['window_id']: r for r in conn.tables.get('kala_field_windows', [])}
            new = [after[w] for w in set(after) - before]
            parts = step.key.split(':')
            if parts[0] == 'stage5dhara' and len(parts) == 4:
                lo, hi = W._window_part_bounds(int(parts[3]), n)
                assert all(W._in_window_part(r['t_start'], lo, hi) for r in new)
                expected = [s for s in STARTS if W._in_window_part(s, lo, hi)]
                assert sorted(r['t_start'] for r in new) == sorted(expected)
            elif step.key.startswith('stage6'):
                break

    def test_adrishta_residual_is_class_wide_not_per_part(self, synthetic, monkeypatch):
        # adrishta_residual reads the totals of ALL windows; a part-local value would
        # make the union differ from the single pass. The real function can clamp to a
        # constant on small fixtures, so use a total-sensitive stand-in to make the
        # class-wide input observable.
        monkeypatch.setattr(W.S5, 'adrishta_residual',
                            lambda totals, rate, horizon: float(sum(totals)))
        _, parted = self._build(F.build_tables(), lambda s: s)
        _, single = self._build(F.build_tables(), _single_pass_steps)
        a = {r['adrishta_residual'] for r in parted.tables['kala_field_windows']}
        b = {r['adrishta_residual'] for r in single.tables['kala_field_windows']}
        assert a == b and a == {0.25 * len(STARTS)}


# ── idempotent per part (natural-key upsert, no computational delete) ───────

class TestPerPartIdempotency:
    def _prepared(self, synthetic):
        conn = FakeConn(F.build_tables())
        ctx = _ctx(conn)
        writer = W.KaKshetraWriter()
        steps = writer.plan_substeps(ctx)
        for s in steps:
            if s.key.startswith('stage5dhara') and s.key.endswith(':2:0'):
                break
            writer.run_substep(ctx, s)
        return writer, ctx, conn, steps

    def test_rerunning_a_part_does_not_duplicate_or_touch_other_parts(self, synthetic):
        writer, ctx, conn, steps = self._prepared(synthetic)
        part = {s.key: s for s in steps}
        n = W.WINDOW_PARTS
        # run parts 0 and 1, then re-run part 0
        writer.run_substep(ctx, part[f'stage5dhara:{EC}:2:0'])
        writer.run_substep(ctx, part[f'stage5dhara:{EC}:2:1'])
        snap = _snapshot_tables(conn)
        writer.run_substep(ctx, part[f'stage5dhara:{EC}:2:0'])
        assert _snapshot_tables(conn) == snap
        ids = [r['window_id'] for r in conn.tables['kala_field_windows']]
        assert len(ids) == len(set(ids))
        lo0, hi0 = W._window_part_bounds(0, n)
        lo1, hi1 = W._window_part_bounds(1, n)
        want = [s for s in STARTS if W._in_window_part(s, lo0, hi0)
                or W._in_window_part(s, lo1, hi1)]
        assert sorted(r['t_start'] for r in conn.tables['kala_field_windows']) == sorted(want)

    def test_a_part_never_deletes_anything(self, synthetic):
        """D-5 RED-C doctrine: replacement happens once, in prepare:replace. A part
        rewrites only its own slice by natural-key upsert and leaves every other row,
        including rows it did not write, exactly as they were."""
        writer, ctx, conn, steps = self._prepared(synthetic)
        part = {s.key: s for s in steps}
        snap = writer._snapshot_id
        foreign = {'chart_id': F.CHART_ID, 'window_id': 'foreign_row', 'event_class': EC,
                   't_start': 3.0, 'field_snapshot_id': snap}
        conn.tables['kala_field_windows'].append(foreign)
        deletes_before = list(conn.deletes)
        writer.run_substep(ctx, part[f'stage5dhara:{EC}:2:0'])
        assert conn.deletes == deletes_before
        assert foreign in conn.tables['kala_field_windows']

    def test_provenance_of_a_rerun_part_is_not_duplicated(self, synthetic):
        writer, ctx, conn, steps = self._prepared(synthetic)
        part = {s.key: s for s in steps}
        writer.run_substep(ctx, part[f'stage5dhara:{EC}:2:0'])
        n = len(conn.tables['kala_field_provenance'])
        assert n > 0
        writer.run_substep(ctx, part[f'stage5dhara:{EC}:2:0'])
        assert len(conn.tables['kala_field_provenance']) == n
        keys = [(r['target_id'], r['term_key']) for r in conn.tables['kala_field_provenance']]
        assert len(keys) == len(set(keys))

    def test_dry_run_part_writes_nothing(self, synthetic):
        conn = FakeConn(F.build_tables())
        ctx = FakeCtx(conn, F.CHART_ID, dry_run=True)
        writer = W.KaKshetraWriter()
        steps = writer.plan_substeps(ctx)
        before = copy.deepcopy(conn.tables)
        for s in steps:
            if s.key.startswith('stage5dhara:') and s.key.endswith(':2:3'):
                res = writer.run_substep(ctx, s)
                assert res.rows_inserted == 0
        assert conn.tables == before


# ── resume through the REAL orchestrator driver ─────────────────────────────

class _Boom(RuntimeError):
    pass


def _driver(conn, writer, ctx):
    return asset_runner._drive_substeps(
        conn, conn.cursor(), 'run-1', F.CHART_ID, W.ASSET_ID, writer, ctx)


class TestResume:
    @pytest.fixture(autouse=True)
    def _quiet(self, monkeypatch):
        monkeypatch.setattr(asset_runner, 'emit_event', lambda *a, **k: None)

    def _clean_reference(self, synthetic):
        conn = _TransactionalFakeConn(F.build_tables())
        ctx = _ctx(conn)
        _driver(conn, W.KaKshetraWriter(), ctx)
        return _snapshot_tables(conn)

    @pytest.mark.parametrize('k', [0, 1, 7, W.WINDOW_PARTS - 1])
    def test_crash_at_part_k_then_resume_equals_clean_build(self, synthetic, monkeypatch, k):
        reference = self._clean_reference(synthetic)

        conn = _TransactionalFakeConn(F.build_tables())
        ctx = _ctx(conn)
        w1 = W.KaKshetraWriter()
        orig = w1.run_substep

        def crashing(c, step):
            if step.key == f'stage5dhara:{EC}:2:{k}':
                # connection lost mid-part, after the part started its writes
                orig(c, step)
                raise _Boom('the connection is lost')
            return orig(c, step)

        monkeypatch.setattr(w1, 'run_substep', crashing)
        with pytest.raises(_Boom):
            _driver(conn, w1, ctx)

        done = {r['substep_key'] for r in conn.tables['build_substep_progress']}
        for p in range(k):
            assert f'stage5dhara:{EC}:2:{p}' in done
        for p in range(k, W.WINDOW_PARTS):
            assert f'stage5dhara:{EC}:2:{p}' not in done
        # the crashed part's own writes were rolled back by the savepoint
        n = W.WINDOW_PARTS
        got = sorted(r['t_start'] for r in conn.tables['kala_field_windows'])
        lo, hi = W._window_part_bounds(k, n)
        assert all(W._in_window_part(t, None, lo) for t in got) or k == 0
        assert not any(W._in_window_part(t, lo, hi) for t in got)

        # resume with a FRESH writer (new process): plan starts exactly at part k
        w2 = W.KaKshetraWriter()
        ran: list[str] = []
        orig2 = w2.run_substep
        monkeypatch.setattr(w2, 'run_substep', lambda c, s: (ran.append(s.key), orig2(c, s))[1])
        _driver(conn, w2, ctx)
        assert ran[0] == f'stage5dhara:{EC}:2:{k}'
        assert 'prepare:replace' not in ran
        assert not any(r.startswith('stage4:') for r in ran)
        assert f'stage5dhara:{EC}:1' not in ran
        assert [r for r in ran if r.startswith(f'stage5dhara:{EC}:2:')] == [
            f'stage5dhara:{EC}:2:{p}' for p in range(k, W.WINDOW_PARTS)]
        assert _snapshot_tables(conn) == reference

    def test_a_completed_run_replans_to_nothing(self, synthetic):
        conn = _TransactionalFakeConn(F.build_tables())
        ctx = _ctx(conn)
        _driver(conn, W.KaKshetraWriter(), ctx)
        assert W.KaKshetraWriter().plan_substeps(ctx) == []


# ── compatibility with a ledger recorded by the OLD (single :2) plan ────────

class TestOldPlanCompat:
    def _old_plan_ledger(self, synthetic, *, windows_done: bool):
        """Run a build with the legacy single-pass windows substep, stopping either
        right after it (windows_done) or right before it, and keep the DB + ledger."""
        conn = _TransactionalFakeConn(F.build_tables())
        ctx = _ctx(conn)
        w = W.KaKshetraWriter()
        for s in _single_pass_steps(w.plan_substeps(ctx)):
            if s.key == f'stage5dhara:{EC}:2' and not windows_done:
                break
            if s.key.startswith('stage6'):
                break
            asset_runner_step(conn, w, ctx, s)
        return conn, ctx

    def test_half_finished_old_run_with_windows_done_skips_all_parts(self, synthetic):
        conn, ctx = self._old_plan_ledger(synthetic, windows_done=True)
        done = {r['substep_key'] for r in conn.tables['build_substep_progress']}
        assert f'stage5dhara:{EC}:2' in done            # old-plan receipt
        remaining = [s.key for s in W.KaKshetraWriter().plan_substeps(ctx)]
        assert not any(k.startswith(f'stage5dhara:{EC}:') for k in remaining)
        assert 'prepare:replace' not in remaining       # ledger fingerprint still matches
        assert remaining[0] == 'stage6'

    def test_half_finished_old_run_with_windows_pending_runs_all_parts(self, synthetic):
        conn, ctx = self._old_plan_ledger(synthetic, windows_done=False)
        remaining = [s.key for s in W.KaKshetraWriter().plan_substeps(ctx)]
        assert remaining[:W.WINDOW_PARTS] == [f'stage5dhara:{EC}:2:{p}'
                                              for p in range(W.WINDOW_PARTS)]
        assert 'prepare:replace' not in remaining
        assert f'stage5dhara:{EC}:1' not in remaining

    def test_old_run_finished_by_new_code_equals_clean_build(self, synthetic, monkeypatch):
        monkeypatch.setattr(asset_runner, 'emit_event', lambda *a, **k: None)
        ref_conn = _TransactionalFakeConn(F.build_tables())
        _driver(ref_conn, W.KaKshetraWriter(), _ctx(ref_conn))
        conn, ctx = self._old_plan_ledger(synthetic, windows_done=False)
        _driver(conn, W.KaKshetraWriter(), ctx)
        assert _snapshot_tables(conn) == _snapshot_tables(ref_conn)

    def test_resume_fingerprint_is_independent_of_the_partition(self):
        conn = FakeConn(F.build_tables())
        w = W.KaKshetraWriter()
        w.plan_substeps(_ctx(conn))
        fp = w._fingerprint()
        assert W._RESUME_VERSION == 10, 'plan shape change is ledger-compatible: no bump'
        assert fp == w._fingerprint()      # stable across calls, no partition input

    def test_legacy_key_still_dispatches_the_whole_class(self, synthetic):
        """run_substep given the OLD key (a stale caller) writes the entire class."""
        conn = FakeConn(F.build_tables())
        ctx = _ctx(conn)
        w = W.KaKshetraWriter()
        steps = _single_pass_steps(w.plan_substeps(ctx))
        _run(w, ctx, [s for s in steps if not s.key.startswith('stage6')
                      and s.key not in ('stage65', 'snapshot')
                      and not s.key.startswith('stage8')])
        assert len(conn.tables['kala_field_windows']) == len(STARTS)


def asset_runner_step(conn, writer, ctx, step):
    """Run one substep exactly as _drive_substeps does (savepoint, run, release, commit)."""
    cur = conn.cursor()
    cur.execute('SAVEPOINT writer_exec')
    writer.run_substep(ctx, step)
    cur.execute('RELEASE SAVEPOINT writer_exec')
    conn.commit()


# ── dispatch ─────────────────────────────────────────────────────────────────

class TestDispatch:
    def _writer(self):
        w = W.KaKshetraWriter()
        w._chart_id = F.CHART_ID
        return w

    def test_part_key_routes_with_part_index(self, monkeypatch):
        w = self._writer()
        seen = {}
        monkeypatch.setattr(
            w, '_run_stage5dhara_windows',
            lambda conn, ec, step, part=None: seen.update(ec=ec, part=part) or 'ok')
        assert w.run_substep(SimpleNamespace(db_conn=object()),
                             SubStep(key='stage5dhara:career_change:2:13')) == 'ok'
        assert seen == {'ec': 'career_change', 'part': 13}

    def test_legacy_key_routes_with_no_part(self, monkeypatch):
        w = self._writer()
        seen = {}
        monkeypatch.setattr(
            w, '_run_stage5dhara_windows',
            lambda conn, ec, step, part=None: seen.update(ec=ec, part=part) or 'ok')
        w.run_substep(SimpleNamespace(db_conn=object()),
                      SubStep(key='stage5dhara:career_change:2'))
        assert seen == {'ec': 'career_change', 'part': None}


# ── class-level completeness detector (§N.8) ────────────────────────────────

class TestCompletenessDetector:
    def test_last_part_fails_loudly_if_an_earlier_part_never_ran(self, synthetic):
        conn = FakeConn(F.build_tables())
        ctx = _ctx(conn)
        w = W.KaKshetraWriter()
        steps = w.plan_substeps(ctx)
        skipped = f'stage5dhara:{EC}:2:5'   # part 5 = [100, 120): holds t_start 100.0
        assert any(W._in_window_part(s, *W._window_part_bounds(5, W.WINDOW_PARTS))
                   for s in STARTS), 'fixture must put a window in the skipped part'
        with pytest.raises(S4.UpstreamStageIncomplete, match='window'):
            for s in steps:
                if s.key == skipped:
                    continue
                w.run_substep(ctx, s)

    def test_a_class_with_no_windows_passes(self, synthetic):
        synthetic['starts'] = []
        conn = FakeConn(F.build_tables())
        ctx = _ctx(conn)
        w = W.KaKshetraWriter()
        for s in w.plan_substeps(ctx):
            if s.key.startswith('stage6'):
                break
            w.run_substep(ctx, s)
        assert conn.tables.get('kala_field_windows', []) == []

    def test_skipped_class_parts_are_honest_no_ops(self):
        tables = F.build_tables()
        tables['brahma_event_ontology'] = []
        conn = FakeConn(tables)
        ctx = _ctx(conn)
        w = W.KaKshetraWriter()
        for s in w.plan_substeps(ctx):
            if s.key.startswith('stage6'):
                break
            w.run_substep(ctx, s)
        assert conn.tables.get('kala_field_windows', []) == []


# ── per-class derivation sharing ─────────────────────────────────────────────

class TestClassStateSharing:
    """The parts of ONE class share one load; another class (or snapshot) never
    inherits it."""

    class _NoDb:
        def cursor(self, *a, **k):
            raise AssertionError('DB touched')

    def _writer(self):
        w = W.KaKshetraWriter()
        w._chart_id = F.CHART_ID
        w._snapshot_id = 'snap-1'
        return w

    def test_same_class_and_snapshot_reuses_without_touching_the_db(self):
        w = self._writer()
        st = SimpleNamespace(event_class='A', snapshot_id='snap-1')
        w._dhara_windows_state = st
        assert w._dhara_windows_for_class(self._NoDb(), 'A', object()) is st

    def test_a_different_class_never_reuses_the_cached_state(self):
        w = self._writer()
        w._dhara_windows_state = SimpleNamespace(event_class='A', snapshot_id='snap-1')
        with pytest.raises(AssertionError, match='DB touched'):
            w._dhara_windows_for_class(self._NoDb(), 'B', object())

    def test_a_different_snapshot_never_reuses_the_cached_state(self):
        w = self._writer()
        w._dhara_windows_state = SimpleNamespace(event_class='A', snapshot_id='snap-0')
        with pytest.raises(AssertionError, match='DB touched'):
            w._dhara_windows_for_class(self._NoDb(), 'A', object())

    def test_plan_substeps_resets_the_cache(self):
        w = self._writer()
        w._dhara_windows_state = SimpleNamespace(event_class='A', snapshot_id='x')
        w.plan_substeps(_ctx(FakeConn(F.build_tables())))
        assert w._dhara_windows_state is None
