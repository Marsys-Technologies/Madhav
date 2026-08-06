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

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra import stage4_field as S4, stage5_null as S5  # noqa: E402
from services.ka_kshetra import stage8_spec as S8  # noqa: E402
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

    # MERGE-TRAIN NOTE (2026-07-30): `stage4_field.load_promise_prior` prefers Lane
    # A's real `stage2_promise.promise_prior` when it's importable, falling back to
    # a direct `kala_field_routes` read (§3.3) only when it isn't. This fixture's
    # `FakeConn` was built against that FALLBACK shape (see fake_db.py's own
    # `kala_field_routes` handler) — it does not simulate Lane A's real data model
    # (`bodha_cgm_nodes`/`bodha_cgm_edges`/etc). Now that Lane A is merged and
    # genuinely importable, the writer correctly prefers it in production, which
    # would make these WRITER-orchestration tests silently become integration tests
    # of Lane A's promise-graph implementation too. Force the fallback path here —
    # deliberately, not by accident — so this suite keeps testing what it says it
    # tests: the writer's own contract, against the simple fixture it was built for.
    monkeypatch.setitem(sys.modules, 'services.ka_kshetra.stage2_promise', None)
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
        # Lane A (bo_pratijna) has not promised or conditionally-promised anything
        # for this chart yet. Zero substeps and a log line — not a crash, and not
        # a fabricated class list.
        tables = F.build_tables()
        tables['bodha_pratijna'] = []
        conn = FakeConn(tables)
        assert W.KaKshetraWriter().plan_substeps(FakeCtx(conn, F.CHART_ID)) == []

    def test_denied_pratijna_rows_do_not_count_as_event_classes(self):
        # A chart can have bo_pratijna rows that are all `denied` — real Bodha
        # output, but nothing this writer should build a field for. Regression
        # guard for the defect this test file's sibling test used to mask: the
        # writer must discover classes from bo_pratijna's promised/conditional
        # rows, never from the `kala_field_routes` cache table (nothing in the
        # live call graph ever writes to it — see stage2_promise.promise_prior,
        # which computes routes in-memory and never persists them).
        tables = F.build_tables()
        tables['bodha_pratijna'] = [
            {'chart_id': F.CHART_ID, 'event_class_id': 'never_promised', 'status': 'denied'},
        ]
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

    @staticmethod
    def _names_in(stmt: str) -> set[str]:
        """Identifiers in `stmt`, tokenized on WORD BOUNDARIES.

        Substring matching is wrong in both directions here and it bit this
        assertion for real: `kala_timeline` is a strict prefix of the W2 table
        `kala_timeline_spec`, so a plain `legacy in stmt` flagged a write to a
        brand-new table as a legacy regression. The mirror-image failure is the
        dangerous one — a legacy table whose name is a prefix of nothing would
        pass a check that was only ever accidentally strict.
        """
        return set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', stmt))

    def test_zero_writes_to_any_legacy_table(self):
        # §1 rail 2 (strangler-fig) and §10's gate row "legacy writers UNTOUCHED
        # and still serving". W2 writes ZERO rows to any legacy table.
        writer, conn = _run_full_build(F.build_tables())
        for stmt in conn.executed:
            head = ' '.join(stmt.split())[:40].upper()
            if head.startswith(('INSERT', 'UPDATE', 'DELETE')):
                hit = self._names_in(stmt) & set(self.LEGACY_TABLES)
                assert not hit, f'W2 wrote to legacy table(s) {sorted(hit)}:\n{stmt[:200]}'

    def test_the_prefix_trap_this_guard_fell_into_stays_closed(self):
        # A regression test for the GUARD itself: the two names differ, and the
        # matcher must say so.
        assert 'kala_timeline' not in self._names_in(
            'INSERT INTO kala_timeline_spec (chart_id) VALUES (%s)')
        assert 'kala_timeline' in self._names_in(
            'INSERT INTO kala_timeline (chart_id) VALUES (%s)')

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


# ── stages 6 / 6.5 / 8: the publication wiring ──────────────────────────────

class TestStage6Salience:
    def test_the_plan_reaches_stages_6_65_and_8_before_the_snapshot(self):
        conn = FakeConn(F.build_tables())
        steps = W.KaKshetraWriter().plan_substeps(FakeCtx(conn, F.CHART_ID))
        keys = [s.key for s in steps]
        kinds = [k.split(':', 1)[0] for k in keys]
        # §2's pipeline order. The snapshot is last because the content hash is
        # a digest OF every stage-0..8 row, so anything hashed must commit first.
        assert kinds.index('stage5finalize') < kinds.index('stage6')
        assert kinds.index('stage6') < kinds.index('stage65')
        assert kinds.index('stage65') < kinds.index('stage8')
        assert kinds[-1] == 'snapshot'
        assert [k for k in keys if k.startswith('stage8:')] == [
            f'stage8:{v}' for v in W.TIMELINE_VIEWS]

    def test_one_salience_row_per_committed_window(self):
        writer, conn = _run_full_build(F.build_tables())
        windows = {w['window_id'] for w in conn.tables['kala_field_windows']}
        salience = {r['window_id'] for r in conn.tables['kala_field_salience']}
        assert windows and salience == windows

    def test_a_not_computed_factor_is_null_and_absent_from_the_basis(self):
        # §6.1: "never imputed". The fixture cohort is far below the 10,000-row
        # minimum, so Informativeness is genuinely not computable; it must be
        # NULL and must drop OUT of salience_basis rather than score 0.
        writer, conn = _run_full_build(F.build_tables())
        row = conn.tables['kala_field_salience'][0]
        assert row['factor_informativeness'] is None
        assert 'I' not in row['salience_basis']
        # Actionability likewise: §11's tri-plane is not built at W2.
        assert row['factor_actionability'] is None
        assert 'A' not in row['salience_basis']
        # ...but the factors that ARE computable are present and in the scalar.
        assert row['factor_consequence'] is not None and 'Q' in row['salience_basis']
        assert row['factor_reliability'] is not None and 'B' in row['salience_basis']
        assert 0.0 <= row['salience'] <= 1.0

    def test_the_reason_a_factor_is_null_is_recorded_not_swallowed(self):
        # §N.8: a NULL that nothing explains is indistinguishable from a NULL
        # nobody looked for.
        writer, conn = _run_full_build(F.build_tables())
        assert any(n.startswith('rarity:') for n in writer._coverage_notes)

    def test_the_submodular_run_summary_is_denormalized_onto_every_row(self):
        writer, conn = _run_full_build(F.build_tables())
        rows = conn.tables['kala_field_salience']
        assert len({r['coverage_fraction'] for r in rows}) == 1
        selected = [r for r in rows if r['selected']]
        assert all(r['selection_rank'] is not None for r in selected)
        assert all(r['selection_rank'] is None for r in rows if not r['selected'])
        assert len(selected) <= W.SUBMODULAR_ROW_BUDGET


class TestStage65Insights:
    def test_every_row_is_non_lel_derived(self):
        # THE CIRCULARITY GUARD CARVE-OUT (§6.4 / §8.3 CG-1). Stage 6.5 writes
        # the seven non-LEL types only; `biographical_echo` belongs to Lane E.
        writer, conn = _run_full_build(F.build_tables())
        rows = conn.tables['kala_insights']
        assert rows, 'the fixture field must fire at least one insight predicate'
        assert all(r['lel_derived'] is False for r in rows)
        assert all(r['insight_type'] != 'biographical_echo' for r in rows)
        assert all(r['field_snapshot_id'] == writer._snapshot_id for r in rows)

    def test_a_lane_E_biographical_row_survives_a_field_rebuild(self):
        # THE SHARED-TABLE HAZARD. `kala_insights` is written by two authors; a
        # blanket per-chart delete on a field rebuild would silently destroy
        # Lane E's LEL-derived rows, which are outside this writer's authorship
        # AND outside the field hash by design.
        tables = F.build_tables()
        _, conn = _run_full_build(tables)
        conn.tables['kala_insights'].append({
            'chart_id': F.CHART_ID, 'insight_id': 'kin_laneE_biographical',
            'insight_type': 'biographical_echo', 'lel_derived': True,
            'field_snapshot_id': None, 'insight_score': 0.5,
        })
        # Force the FRESH/REPLAN branch. Without this the second build resumes
        # off the completed ledger, takes no delete path at all, and the
        # assertion below would pass while proving nothing — which is exactly
        # what a mutation run caught this test doing.
        conn.tables['build_substep_progress'] = []
        writer = W.KaKshetraWriter()
        ctx = FakeCtx(conn, F.CHART_ID)
        steps = writer.plan_substeps(ctx)
        assert 'kala_insights' in conn.deletes, 'the delete path must actually run'
        for step in steps:
            writer.run_substep(ctx, step)
        ids = {r['insight_id'] for r in conn.tables['kala_insights']}
        assert 'kin_laneE_biographical' in ids

    def test_a_lel_derived_row_never_enters_the_content_hash(self):
        # The other half of the carve-out: the insight is SERVED and the field
        # does not move (§6.4's "what lets both things be true at once").
        tables = F.build_tables()
        writer, conn = _run_full_build(tables)
        before = conn.tables['kala_field_snapshots'][0]['field_content_hash']
        conn.tables['kala_insights'].append({
            'chart_id': F.CHART_ID, 'insight_id': 'kin_laneE_biographical',
            'insight_type': 'biographical_echo', 'lel_derived': True,
            'field_snapshot_id': None, 'insight_score': 0.5,
        })
        after = writer._compute_content_hash(conn)
        assert after == before

    def test_statement_params_are_data_and_never_composed_prose(self):
        # §6.4 / B.10: `statement_key` + `statement_params`, never a sentence.
        writer, conn = _run_full_build(F.build_tables())
        for r in conn.tables['kala_insights']:
            assert r['statement_key'].startswith('insight_')
            assert isinstance(json.loads(r['statement_params']), dict)

    def test_insights_without_a_salience_layer_halt_rather_than_score_a_default(self):
        tables = F.build_tables()
        conn = FakeConn(tables)
        ctx = FakeCtx(conn, F.CHART_ID)
        writer = W.KaKshetraWriter()
        steps = writer.plan_substeps(ctx)
        for step in steps:
            if step.key == 'stage65':
                # Wipe the salience layer stage 6 just wrote: every insight_score
                # is cohort_surprise x CARRIER_SALIENCE x reliability, so scoring
                # without it would substitute a default for a computed value.
                conn.tables['kala_field_salience'] = []
                with pytest.raises(S4.UpstreamStageIncomplete):
                    writer.run_substep(ctx, step)
                return
            writer.run_substep(ctx, step)
        pytest.fail('the plan never reached stage65')


class TestStage8TimelineSpec:
    def test_one_spec_row_per_view(self):
        writer, conn = _run_full_build(F.build_tables())
        rows = conn.tables['kala_timeline_spec']
        assert {r['generated_for'] for r in rows} == set(W.TIMELINE_VIEWS)
        assert all(r['spec_version'] == 'kala_timeline_spec/1' for r in rows)

    def test_every_interval_id_is_a_real_window_id(self):
        # Item 44's SINGLE TEMPORAL AUTHORITY rail: the spec CITES field windows
        # and never mints its own ids.
        writer, conn = _run_full_build(F.build_tables())
        windows = {w['window_id'] for w in conn.tables['kala_field_windows']}
        spec = json.loads(conn.tables['kala_timeline_spec'][0]['spec'])
        assert spec['intervals'], 'the fixture field must render at least one interval'
        assert {i['id'] for i in spec['intervals']} <= windows

    def test_the_earned_signal_check_holds_on_every_row(self):
        # Migration 496's CHECK: (n_intervals + n_points + n_bands = 0) ==
        # (empty_reason IS NOT NULL). An empty spec is served WITH a reason.
        writer, conn = _run_full_build(F.build_tables())
        for r in conn.tables['kala_timeline_spec']:
            total = r['n_intervals'] + r['n_points'] + r['n_bands']
            assert (total == 0) == (r['empty_reason'] is not None)

    def test_now_marker_is_pinned_and_not_wall_clock(self):
        # §7.4 hash-replay ("build twice, assert bit-identical") vs §2 ("stages
        # 0-8 are pure functions of the pins"). A wall-clock marker would break
        # both every midnight, which is why the spec joined the hash only once
        # this was true.
        writer, conn = _run_full_build(F.build_tables())
        spec = json.loads(conn.tables['kala_timeline_spec'][0]['spec'])
        assert spec['now_marker'] == spec['t_zero'][:10]

    def test_point_ids_are_natural_key_derived_not_identity_derived(self):
        # BIGINT identities are reassigned on every rebuild; hashing one into the
        # spec would move the content hash on a rebuild that changed nothing.
        a_writer, a = _run_full_build(F.build_tables())
        b_writer, b = _run_full_build(F.build_tables())
        pa = json.loads(a.tables['kala_timeline_spec'][0]['spec'])['points']
        pb = json.loads(b.tables['kala_timeline_spec'][0]['spec'])['points']
        assert pa and [p['id'] for p in pa] == [p['id'] for p in pb]
        assert all(p['id'].startswith('kfb_') for p in pa)

    def test_zero_surviving_tracks_writes_an_honest_empty_row_instead_of_crashing(self):
        # Real production defect (Gate-Chain MORNING REPORT #6, chart 482012f1): every
        # event class stage4 discovers can be skipped `no_class_prior_row` (no
        # brahma_class_priors overlap — see TestHonestSkip's sibling test), which leaves
        # zero `kala_field_windows`. When zero `kala_field_boundaries` also survive to
        # stage8 (no clock rows either), `_timeline_tracks_and_windows` +
        # `_timeline_points` hand `build_timeline_spec` zero tracks. Before the fix this
        # raised an unhandled ValueError and took the whole writer down; now it must
        # write an honest-empty `kala_timeline_spec` row per view, same as any other
        # LAW ZERO empty case.
        tables = F.build_tables(with_lifetime_prior=False)
        tables['kala_field_boundaries'] = []
        writer, conn = _run_full_build(tables)

        assert conn.tables['kala_field'] == [], 'no class survived stage4'
        rows = conn.tables['kala_timeline_spec']
        assert {r['generated_for'] for r in rows} == set(W.TIMELINE_VIEWS)
        for r in rows:
            spec = json.loads(r['spec'])
            assert spec['tracks'] == spec['intervals'] == spec['points'] == spec['bands'] == []
            assert r['n_tracks'] == r['n_intervals'] == r['n_points'] == r['n_bands'] == 0
            assert r['empty_reason'] == S8.EMPTY_NO_RENDERABLE_ROWS


class TestHashCoverage:
    def test_the_snapshot_declares_the_new_tables_it_covered(self):
        # The hash's row-set CHANGED when stages 6/6.5/8 landed. That is only
        # safe because every snapshot row states what its own hash covered — a
        # hash-replay comparison across differing `hashed_tables` is comparing
        # two different measurements.
        writer, conn = _run_full_build(F.build_tables())
        covered = conn.tables['kala_field_snapshots'][0]['hashed_tables']
        for table in ('kala_field_salience', 'kala_insights', 'kala_timeline_spec'):
            assert table in covered

    def test_the_hash_moves_when_a_stage_6_row_moves(self):
        # THE DETECTOR (§N.8): if perturbing a newly-hashed table left the hash
        # unchanged, "these tables are covered" would be an unearned claim.
        writer, conn = _run_full_build(F.build_tables())
        before = writer._compute_content_hash(conn)
        conn.tables['kala_field_salience'][0]['salience'] = 0.123456
        assert writer._compute_content_hash(conn) != before

    def test_the_hash_moves_when_a_stage_8_spec_moves(self):
        writer, conn = _run_full_build(F.build_tables())
        before = writer._compute_content_hash(conn)
        conn.tables['kala_timeline_spec'][0]['n_intervals'] = 99
        assert writer._compute_content_hash(conn) != before
