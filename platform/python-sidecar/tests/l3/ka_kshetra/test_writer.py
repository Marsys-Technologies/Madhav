"""
tests/l3/ka_kshetra/test_writer.py — ṢAḌ-DARŚANA W2 Lane C: the `ka_kshetra`
HEAVY writer end to end against an in-memory connection.

These tests pin the WIRING, not the numerics (those are exhaustively pinned by
test_hazard.py / test_integrator.py / test_stage4_field.py / test_stage5_null.py):

  • FROZEN orchestrator contract conformance — no commit/rollback/close, no
    asset_throughput write, plan_substeps + run_substep;
  • idempotency done ONCE in plan_substeps (the ka_gochara_sweep D-5 RED-C lesson);
  • the weights version pinned ONCE (§7.5 sub-rule 5);
  • the §5.4 reconciliation invariant actually firing at write time;
  • ZERO rows written to any legacy table (§1 rail 2 — the wave's headline
    non-regression);
  • determinism: two identical builds produce the same content hash.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra import stage4_field as S4, stage5_null as S5  # noqa: E402
from services.ka_kshetra import writer as W  # noqa: E402
from tests.l3.ka_kshetra.fake_db import FakeConn, FakeCtx  # noqa: E402
from tests.l3.ka_kshetra import fixtures as F  # noqa: E402


@pytest.fixture(autouse=True)
def _small_build(monkeypatch):
    """Shrink the horizon and the replicate count so the wiring tests are fast.

    The SHAPE is unchanged: ten stage-4 decade slices, N stage-5 replicate
    blocks, a finalize per class, a terminal snapshot. Only the magnitudes move.
    """
    monkeypatch.setattr(W, 'HORIZON_DAYS', 400.0)
    monkeypatch.setattr(S5, 'DEFAULT_REPLICATES', 8)
    monkeypatch.setattr(S5, 'DEFAULT_BLOCK_SIZE', 4)
    yield


def _run_full_build(tables) -> tuple[W.KaKshetraWriter, FakeConn]:
    conn = FakeConn(tables)
    ctx = FakeCtx(conn, F.CHART_ID)
    writer = W.KaKshetraWriter()
    for step in writer.plan_substeps(ctx):
        writer.run_substep(ctx, step)
    return writer, conn


# ── plan shape + ordering ────────────────────────────────────────────────────

class TestPlan:
    def test_plan_is_stage_ordered(self):
        conn = FakeConn(F.build_tables())
        steps = W.KaKshetraWriter().plan_substeps(FakeCtx(conn, F.CHART_ID))
        kinds = [s.key.split(':', 1)[0] for s in steps]
        # asset_runner._run_substeps iterates plan_substeps(ctx) IN ORDER, so
        # emitting the stages in dependency order is what makes stage 5 able to
        # read stage 4's committed rows. Each substep ALSO checks its upstream
        # independently (see TestUpstreamGuard) so the ordering is belt, not braces.
        assert kinds.index('stage4') < kinds.index('stage5')
        assert kinds.index('stage5') < kinds.index('stage5finalize')
        assert kinds[-1] == 'snapshot'

    def test_ten_decade_slices_per_event_class(self):
        conn = FakeConn(F.build_tables())
        steps = W.KaKshetraWriter().plan_substeps(FakeCtx(conn, F.CHART_ID))
        s4 = [s for s in steps if s.key.startswith('stage4:')]
        assert len(s4) == W.DECADES
        assert {s.key.rsplit(':', 1)[1] for s in s4} == {str(d) for d in range(W.DECADES)}

    def test_replicate_blocks_cover_every_replicate_exactly_once(self):
        conn = FakeConn(F.build_tables())
        steps = W.KaKshetraWriter().plan_substeps(FakeCtx(conn, F.CHART_ID))
        blocks = [s for s in steps if s.key.startswith('stage5:')]
        assert len(blocks) == S5.DEFAULT_REPLICATES // S5.DEFAULT_BLOCK_SIZE

    def test_no_event_classes_is_an_honest_empty_plan(self):
        # Lane A has not produced a promise graph for this chart. Zero substeps
        # and a log line — not a crash, and not a fabricated class list.
        tables = F.build_tables()
        tables['kala_field_routes'] = []
        conn = FakeConn(tables)
        assert W.KaKshetraWriter().plan_substeps(FakeCtx(conn, F.CHART_ID)) == []

    def test_idempotency_delete_happens_exactly_once_in_plan_substeps(self):
        # THE ka_gochara_sweep D-5 RED-C LESSON. A per-substep delete can fire
        # after sibling substeps have committed rows in the SAME build and
        # silently wipe them.
        writer, conn = _run_full_build(F.build_tables())
        assert conn.deletes.count('kala_field') == 1
        assert conn.deletes.count('kala_field_windows') == 1
        assert conn.deletes.count('kala_field_provenance') == 1

    def test_delete_never_touches_a_legacy_table(self):
        writer, conn = _run_full_build(F.build_tables())
        assert 'kala_gochara_windows' not in conn.deletes
        assert 'gochara_resonance_map' not in conn.deletes

    def test_weights_version_is_resolved_exactly_once(self):
        # §7.5 sub-rule 5: a long build straddling an mi_bhara release must not
        # produce segments under two weights versions in one snapshot.
        writer, conn = _run_full_build(F.build_tables())
        n = sum(1 for s in conn.executed if 'FROM kala_field_weight_versions' in s)
        assert n == 1


# ── the FROZEN orchestrator contract ─────────────────────────────────────────

class TestFrozenContract:
    def test_writer_never_commits_rolls_back_or_closes(self):
        # FakeConn raises on all three, so a violation fails here at the call site.
        _run_full_build(F.build_tables())

    def test_writer_never_writes_asset_throughput(self):
        writer, conn = _run_full_build(F.build_tables())
        assert not any('asset_throughput' in s for s in conn.executed)

    def test_writer_declares_substeps(self):
        assert W.KaKshetraWriter.has_substeps is True
        assert W.KaKshetraWriter.asset_id == 'ka_kshetra'

    def test_registered_under_its_asset_id(self):
        import pipeline.orchestrator.writers.ka_kshetra  # noqa: F401
        from pipeline.orchestrator.writers import WRITER_REGISTRY
        assert WRITER_REGISTRY['ka_kshetra'] is W.KaKshetraWriter

    def test_dry_run_writes_nothing(self):
        conn = FakeConn(F.build_tables())
        ctx = FakeCtx(conn, F.CHART_ID, dry_run=True)
        writer = W.KaKshetraWriter()
        for step in writer.plan_substeps(ctx):
            writer.run_substep(ctx, step)
        assert conn.inserts == {}
        assert conn.deletes == []


# ── what the build produces ──────────────────────────────────────────────────

class TestBuildOutput:
    def test_segments_windows_provenance_and_null_rows_are_written(self):
        writer, conn = _run_full_build(F.build_tables())
        assert conn.tables['kala_field'], 'the field must have segments'
        assert conn.tables['kala_field_null'], 'the null must be persisted'
        assert conn.tables['kala_field_snapshots'], 'the snapshot row must exist'

    def test_every_null_row_covers_one_duration_bucket(self):
        writer, conn = _run_full_build(F.build_tables())
        buckets = {r['bucket_days'] for r in conn.tables['kala_field_null']}
        assert buckets == set(S5.DURATION_BUCKETS)

    def test_segment_indices_are_unique_and_ascending_in_time(self):
        writer, conn = _run_full_build(F.build_tables())
        rows = sorted(conn.tables['kala_field'], key=lambda r: r['t_start'])
        idx = [r['segment_index'] for r in rows]
        assert len(set(idx)) == len(idx)
        assert idx == sorted(idx)

    def test_every_row_carries_the_same_snapshot_and_weights_version(self):
        writer, conn = _run_full_build(F.build_tables())
        assert {r['field_snapshot_id'] for r in conn.tables['kala_field']} == \
               {writer._snapshot_id}
        assert {r['weights_version'] for r in conn.tables['kala_field']} == {'v0_classical'}

    def test_provenance_rows_carry_the_window_id_as_authority_basis(self):
        writer, conn = _run_full_build(F.build_tables())
        if not conn.tables['kala_field_windows']:
            pytest.skip('fixture produced no window above its own null threshold')
        wids = {r['window_id'] for r in conn.tables['kala_field_windows']}
        prov = conn.tables['kala_field_provenance']
        assert prov
        assert {r['authority_basis'] for r in prov} <= wids
        assert {r['target_id'] for r in prov} <= wids

    def test_gate_edges_reference_the_legacy_row_without_copying_its_values(self):
        writer, conn = _run_full_build(F.build_tables())
        gates = [r for r in conn.tables['kala_field_provenance']
                 if r['term_role'] == 'gate']
        if not gates:
            pytest.skip('fixture produced no window, hence no gate edges')
        for g in gates:
            assert g['source_table'] == 'kala_gochara_windows'
            # §N.5: the legacy value is INHERITED BY REFERENCE, never restated.
            # An identity edge carries exactly 1.0, so it cannot smuggle a
            # legacy magnitude into the field's arithmetic either.
            assert g['term_value'] == 1.0
            assert g['log_contribution'] == 0.0

    def test_snapshot_records_the_content_hash_and_the_tables_it_covered(self):
        writer, conn = _run_full_build(F.build_tables())
        snap = conn.tables['kala_field_snapshots'][0]
        assert snap['field_content_hash'].startswith('kfh_')
        assert 'kala_field' in snap['hashed_tables']


# ── the legacy non-regression rail ───────────────────────────────────────────

class TestLegacyUntouched:
    LEGACY_TABLES = (
        'kala_gochara_windows', 'gochara_resonance_map', 'kala_convergence',
        'kala_darshana', 'kala_jivana_parva', 'kala_timeline', 'kala_obstruction',
    )

    def test_zero_writes_to_any_legacy_table(self):
        # §1 rail 2 (strangler-fig) and §10's gate row "legacy writers UNTOUCHED
        # and still serving". W2 writes ZERO rows to any legacy table.
        writer, conn = _run_full_build(F.build_tables())
        for stmt in conn.executed:
            head = ' '.join(stmt.split())[:40].upper()
            if head.startswith(('INSERT', 'UPDATE', 'DELETE')):
                for legacy in self.LEGACY_TABLES:
                    assert legacy not in stmt, (
                        f'W2 wrote to legacy table {legacy}:\n{stmt[:200]}')

    def test_the_legacy_sweep_is_read_and_only_read(self):
        writer, conn = _run_full_build(F.build_tables())
        touches = [s for s in conn.executed if 'kala_gochara_windows' in s]
        assert touches, 'the legacy cross-check corpus must actually be consulted'
        assert all(' '.join(s.split()).upper().startswith('SELECT') for s in touches)


# ── the §5.4 reconciliation invariant, at write time ────────────────────────

class TestReconciliationAtWriteTime:
    def test_a_broken_edge_set_halts_the_substep(self, monkeypatch):
        # THE DETECTOR (§N.8). Drop a factor from the provenance decomposition and
        # the write must HALT with provenance_reconciliation_failed — the
        # orchestrator then rolls its savepoint back and the window never reaches
        # a reader.
        import services.ka_kshetra.hazard as H
        real_evaluate = H.evaluate

        def lossy(**kw):
            # `promise` specifically, because it is the one factor guaranteed to
            # be present AND non-unit at every instant: dropping a role that
            # happens to be inactive at this fixture's peak (e.g. `suppression`,
            # whose vedha fires at t≈260 while the peak sits at t≈101) would
            # leave the sum unchanged and make this test pass vacuously.
            terms = real_evaluate(**kw)
            pruned = tuple(e for e in terms.edges if e.term_role != 'promise')
            return type(terms)(
                ln_lambda=terms.ln_lambda, baseline=terms.baseline,
                promise_term=terms.promise_term, clock_term=terms.clock_term,
                modifier_term=terms.modifier_term,
                suppression_term=terms.suppression_term,
                signed_obstruction=terms.signed_obstruction, edges=pruned)

        conn = FakeConn(F.build_tables())
        ctx = FakeCtx(conn, F.CHART_ID)
        writer = W.KaKshetraWriter()
        steps = writer.plan_substeps(ctx)
        for step in steps:
            if step.key.startswith('stage5finalize'):
                monkeypatch.setattr(H, 'evaluate', lossy)
                with pytest.raises(S4.ProvenanceReconciliationError):
                    writer.run_substep(ctx, step)
                return
            writer.run_substep(ctx, step)
        pytest.skip('fixture produced no window to reconcile')


# ── upstream-completeness guard (§8.1) ──────────────────────────────────────

class TestUpstreamGuard:
    def test_stage5_refuses_to_run_on_an_absent_field(self):
        conn = FakeConn(F.build_tables())
        ctx = FakeCtx(conn, F.CHART_ID)
        writer = W.KaKshetraWriter()
        steps = writer.plan_substeps(ctx)
        block = next(s for s in steps if s.key.startswith('stage5:'))
        with pytest.raises(S4.UpstreamStageIncomplete):
            writer.run_substep(ctx, block)     # no stage-4 substep has run

    def test_finalize_refuses_a_partial_replicate_set(self):
        conn = FakeConn(F.build_tables())
        ctx = FakeCtx(conn, F.CHART_ID)
        writer = W.KaKshetraWriter()
        steps = writer.plan_substeps(ctx)
        for s in steps:
            if s.key.startswith('stage4:'):
                writer.run_substep(ctx, s)
        fin = next(s for s in steps if s.key.startswith('stage5finalize'))
        with pytest.raises(S4.UpstreamStageIncomplete):
            writer.run_substep(ctx, fin)       # no replicate block has run


# ── honest skip ─────────────────────────────────────────────────────────────

class TestHonestSkip:
    def test_temporal_shape_is_READ_from_the_ontology_not_derived(self):
        # §N.7 item 3: no wrapper-local rule may shadow an authoritative value.
        # The fixture class is 'interval' in brahma_event_ontology; a
        # duration-derived shape would call this 199-day window 'interval' too,
        # so the test flips the ontology to prove the value is genuinely READ.
        tables = F.build_tables()
        tables['brahma_event_ontology'][0]['temporal_shape'] = 'chain'
        _, conn = _run_full_build(tables)
        shapes = {r['temporal_shape'] for r in conn.tables['kala_field_windows']}
        assert shapes == {'chain'}

    def test_a_class_with_no_ontology_row_is_skipped_with_a_reason(self):
        tables = F.build_tables()
        tables['brahma_event_ontology'] = []
        _, conn = _run_full_build(tables)
        assert conn.tables['kala_field'] == []
        assert 'no_event_ontology_row' in conn.tables['kala_field_snapshots'][0]['skipped_classes']

    def test_a_class_with_no_classical_prior_writes_no_rows_and_records_why(self):
        # §5.1 C-1. The build SUCCEEDS with an honest empty for that class —
        # it does not fabricate a baseline, and it does not silently vanish.
        writer, conn = _run_full_build(F.build_tables(with_lifetime_prior=False))
        assert conn.tables['kala_field'] == []
        snap = conn.tables['kala_field_snapshots'][0]
        assert 'no_class_prior_row' in snap['skipped_classes']
        assert F.EVENT_CLASS in snap['skipped_classes']


# ── determinism ─────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_two_identical_builds_produce_the_same_content_hash(self):
        _, a = _run_full_build(F.build_tables())
        _, b = _run_full_build(F.build_tables())
        ha = a.tables['kala_field_snapshots'][0]['field_content_hash']
        hb = b.tables['kala_field_snapshots'][0]['field_content_hash']
        assert ha == hb

    def test_a_rebuild_over_existing_rows_replaces_rather_than_accretes(self):
        tables = F.build_tables()
        _, conn = _run_full_build(tables)
        first = len(conn.tables['kala_field'])
        writer = W.KaKshetraWriter()
        ctx = FakeCtx(conn, F.CHART_ID)
        for step in writer.plan_substeps(ctx):
            writer.run_substep(ctx, step)
        assert len(conn.tables['kala_field']) == first

    def test_a_changed_weights_version_changes_the_snapshot_identity(self):
        tables = F.build_tables()
        w1, _ = _run_full_build(tables)
        tables2 = F.build_tables()
        tables2['kala_field_weight_versions'][0]['version_id'] = 'v1_fitted'
        for row in tables2['kala_field_weights']:
            row['version_id'] = 'v1_fitted'
        w2, _ = _run_full_build(tables2)
        assert w1._snapshot_id != w2._snapshot_id
