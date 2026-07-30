"""
tests/l3/ka_kshetra/test_stage4_field.py — ṢAḌ-DARŚANA W2 Lane C, §5.2–§5.4.

Stage 4 field assembly: envelope indexing, the field evaluator, breakpoint
assembly, the provenance RECONCILIATION INVARIANT, and the honest-skip path for
a class with no classical baseline.

These are DB-free: the evaluator is constructed from explicit inputs so the
numerics can be pinned without a Postgres round-trip, which is also what lets the
stage-5 null re-run the same evaluator 256 times cheaply.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra import hazard, integrator as I, stage4_field as S4  # noqa: E402
from services.ka_kshetra.contracts import ClockApplicability, PromisePrior, Route  # noqa: E402


# ── envelopes ────────────────────────────────────────────────────────────────

def _prim(kind, subject, knots, polarity='supportive', object_ref=None, class_label=None):
    return S4.Primitive(
        primitive_kind=kind, subject=subject, object_ref=object_ref,
        polarity=polarity, class_label=class_label,
        knots=tuple((float(t), float(v)) for t, v in knots),
        source_pk=None,
    )


class TestEnvelope:
    def test_piecewise_linear_between_knots(self):
        p = _prim('contact_moon_ref', 'Ju', [(0, 0.0), (10, 1.0), (20, 0.0)])
        assert p.value_at(0.0) == pytest.approx(0.0)
        assert p.value_at(5.0) == pytest.approx(0.5)
        assert p.value_at(10.0) == pytest.approx(1.0)
        assert p.value_at(15.0) == pytest.approx(0.5)

    def test_zero_outside_the_declared_span(self):
        # §3.2 envelope contract: "Outside [t_start, t_end] the value is 0."
        # An extrapolated envelope would silently extend a transit's influence
        # past the orb the classical rule actually grants it.
        p = _prim('contact_moon_ref', 'Ju', [(10, 0.0), (20, 1.0), (30, 0.0)])
        assert p.value_at(9.999) == 0.0
        assert p.value_at(30.001) == 0.0

    def test_coincident_knots_make_a_step_explicit(self):
        p = _prim('moorti_at_ingress', 'Ju', [(10, 0.0), (10, 1.0), (20, 1.0), (20, 0.0)],
                  class_label='svarna')
        assert p.value_at(9.9) == 0.0
        assert p.value_at(15.0) == pytest.approx(1.0)
        assert p.value_at(20.0) == pytest.approx(0.0)

    def test_single_knot_envelope_is_rejected(self):
        # The frozen contract requires ≥2 knots. A one-knot envelope has no
        # defined value anywhere and would silently read 0 for the whole horizon.
        with pytest.raises(ValueError):
            _prim('contact_moon_ref', 'Ju', [(5, 1.0)]).value_at(5.0)


class TestEnvelopeIndex:
    def _index(self):
        return S4.EnvelopeIndex([
            _prim('contact_moon_ref', 'Ju', [(0, 0.0), (10, 0.8), (20, 0.0)]),
            _prim('contact_moon_ref', 'Sa', [(5, 0.0), (10, 0.4), (15, 0.0)]),
            _prim('contact_lagna_ref', 'Ju', [(0, 0.0), (10, 0.6), (20, 0.0)]),
            _prim('vedha', 'Sa', [(8, 0.0), (12, 1.0), (16, 0.0)],
                  polarity='obstructive', object_ref='10'),
        ], horizon_days=100.0)

    def test_covariates_take_the_max_over_same_kind_primitives(self):
        # §5.1 C-5 row 1: "max envelope over active Moon-referenced contacts".
        x = self._index().covariates_at(10.0)
        assert x['contact_moon_ref'] == pytest.approx(0.8)

    def test_dual_reference_agreement_is_derived_not_stored(self):
        x = self._index().covariates_at(10.0)
        assert hazard.derive_dual_reference_agreement(x) == pytest.approx(0.6)

    def test_obstructive_primitives_are_routed_to_the_suppression_channel(self):
        idx = self._index()
        assert 'vedha' not in idx.covariates_at(12.0)
        assert idx.obstructions_at(12.0)['vedha:Sa->10'] == pytest.approx(1.0)

    def test_inactive_obstructors_are_absent_not_zero_valued(self):
        # An entry with u = 0 contributes ln(1) = 0, so including it would be
        # harmless arithmetically — but it would emit a provenance edge claiming
        # an obstruction that was not active. Honest absence beats a null row.
        assert self._index().obstructions_at(50.0) == {}

    def test_knots_are_exposed_as_breakpoints(self):
        bps = self._index().breakpoints()
        for t in (0.0, 5.0, 8.0, 10.0, 12.0, 15.0, 16.0, 20.0):
            assert t in bps

    def test_circular_shift_translates_and_wraps_within_the_horizon(self):
        # §5.5: the replicate rebuild translates every primitive's knots by −δ
        # and wraps into [0, H). This is what makes the null a genuine
        # permutation of the SAME transit stream rather than a different stream.
        idx = self._index()
        shifted = idx.circular_shift(30.0)
        assert shifted.covariates_at(10.0 - 30.0 + 100.0)['contact_moon_ref'] == pytest.approx(0.8)
        assert shifted.horizon_days == idx.horizon_days

    def test_circular_shift_preserves_total_activity(self):
        # A shift may not create or destroy signal — otherwise the null would be
        # comparing against a *weaker* sky and every p-value would be optimistic.
        idx = self._index()
        # `.get(..., 0.0)` because an inactive covariate is ABSENT from the dict,
        # not present-with-zero — see EnvelopeIndex.covariates_at's docstring.
        grid = [i * 0.5 for i in range(200)]
        base = sum(idx.covariates_at(t).get('contact_moon_ref', 0.0) for t in grid)
        assert base > 0.0
        for delta in (7.0, 33.5, 91.0):
            shifted = idx.circular_shift(delta)
            got = sum(shifted.covariates_at(t).get('contact_moon_ref', 0.0) for t in grid)
            assert got == pytest.approx(base, rel=1e-9)

    def test_zero_shift_is_the_identity(self):
        idx = self._index()
        z = idx.circular_shift(0.0)
        for t in (0.0, 3.0, 10.0, 17.5, 99.0):
            assert z.covariates_at(t) == idx.covariates_at(t)


# ── the field evaluator ──────────────────────────────────────────────────────

def _evaluator(**over):
    clocks = [ClockApplicability('vimshottari', 'applicable', 'fruition', 1, True, 0.9)]
    routes = (Route('e', 1, ('graha:Ju', 'bhava:10', 'event_class:e'), 0.6, True, ()),)
    kwargs = dict(
        event_class='e',
        lifetime_count=2.0,
        promise=PromisePrior(p=0.4, routes=routes, n_routes=1, fact_ids=('fact:p',)),
        clocks=clocks,
        ladder={'vimshottari': [
            S4.LadderPeriod(system_id='vimshottari', level='MD', lord='Ju',
                            t_start=0.0, t_end=6000.0),
            S4.LadderPeriod(system_id='vimshottari', level='MD', lord='Sa',
                            t_start=6000.0, t_end=12000.0),
        ]},
        envelopes=S4.EnvelopeIndex([
            _prim('contact_moon_ref', 'Ju', [(1000, 0.0), (1100, 1.0), (1200, 0.0)]),
        ], horizon_days=12000.0),
        weights={'w_s:vimshottari': 1.0, 'beta:x1': 0.4, 'rho:vedha': 0.4,
                 'd:MD': 1.0, 'd:AD': 0.7, 'd:PD': 0.5, 'd:SD': 0.3, 'd:PrD': 0.15},
        horizon_days=12000.0,
        baseline_source=('brahma_class_priors', 'k', 'fact:baseline:e'),
    )
    kwargs.update(over)
    return S4.FieldEvaluator(**kwargs)


class TestFieldEvaluator:
    def test_ln_lambda_is_finite_and_lambda_positive_everywhere(self):
        ev = _evaluator()
        for t in (0.0, 1.0, 1050.0, 5999.0, 6000.0, 11999.0):
            v = ev.ln_lambda(t)
            assert math.isfinite(v)
            assert math.exp(v) > 0.0

    def test_lord_stack_switches_at_the_ladder_boundary(self):
        ev = _evaluator()
        assert ev.lord_stacks_at(1.0)['vimshottari'] == [('MD', 'Ju')]
        assert ev.lord_stacks_at(6001.0)['vimshottari'] == [('MD', 'Sa')]

    def test_a_supportive_running_lord_lifts_the_field_above_an_unrouted_one(self):
        ev = _evaluator()
        # Ju is on the route to e (gain 0.6); Sa is not on any route (g = 0).
        assert ev.ln_lambda(1.0) > ev.ln_lambda(6001.0)

    def test_covariate_activity_lifts_the_field(self):
        ev = _evaluator()
        assert ev.ln_lambda(1100.0) > ev.ln_lambda(500.0)

    def test_breakpoints_include_ladder_boundaries_envelope_knots_and_the_span(self):
        ev = _evaluator()
        bps = ev.breakpoints()
        for t in (0.0, 1000.0, 1100.0, 1200.0, 6000.0, 12000.0):
            assert t in bps
        assert bps == sorted(set(bps))

    def test_extra_breakpoints_from_lane_a_kinematics_are_merged(self):
        ev = _evaluator(extra_breakpoints=[2500.5, 2500.5, -3.0, 99999.0])
        bps = ev.breakpoints()
        assert 2500.5 in bps
        assert all(0.0 <= t <= 12000.0 for t in bps)   # out-of-horizon knots dropped

    def test_terms_at_reproduce_ln_lambda(self):
        ev = _evaluator()
        for t in (0.0, 1100.0, 6001.0):
            assert ev.terms_at(t).ln_lambda == pytest.approx(ev.ln_lambda(t), abs=1e-12)

    def test_evaluator_is_deterministic(self):
        a, b = _evaluator(), _evaluator()
        assert [a.ln_lambda(t) for t in range(0, 12000, 500)] == \
               [b.ln_lambda(t) for t in range(0, 12000, 500)]


class TestSegmentsFromEvaluator:
    def test_segments_span_the_whole_horizon_contiguously(self):
        ev = _evaluator()
        segs = ev.build_segments()
        assert segs[0].t_start == pytest.approx(0.0)
        assert segs[-1].t_end == pytest.approx(12000.0)
        for a, b in zip(segs, segs[1:]):
            assert a.t_end == b.t_start

    def test_stored_segments_reproduce_the_evaluator_at_the_breakpoints(self):
        ev = _evaluator()
        segs = ev.build_segments()
        for s in segs:
            assert s.alpha == pytest.approx(ev.ln_lambda(s.t_start), abs=1e-11)

    def test_total_integral_is_positive_and_finite(self):
        ev = _evaluator()
        segs = ev.build_segments()
        total = I.integrate(segs, 0.0, 12000.0)
        assert 0.0 < total < math.inf


# ── §5.4 the reconciliation invariant ────────────────────────────────────────

class TestProvenanceReconciliation:
    def test_a_faithful_edge_set_reconciles(self):
        ev = _evaluator()
        terms = ev.terms_at(1100.0)
        S4.assert_provenance_reconciles(terms.edges, math.exp(terms.ln_lambda),
                                        target_id='w1')

    def test_a_dropped_edge_fails_the_invariant_loudly(self):
        # THE DETECTOR (§N.8). This is the code path that makes the "provenance
        # is earned" claim able to read FALSE — without it, the invariant would
        # be a signal with no detector.
        ev = _evaluator()
        terms = ev.terms_at(1100.0)
        pruned = tuple(e for e in terms.edges if e.term_role != 'promise')
        with pytest.raises(S4.ProvenanceReconciliationError) as exc:
            S4.assert_provenance_reconciles(pruned, math.exp(terms.ln_lambda),
                                            target_id='w1')
        assert 'provenance_reconciliation_failed' in str(exc.value)

    def test_a_tampered_edge_value_fails_the_invariant(self):
        ev = _evaluator()
        terms = ev.terms_at(1100.0)
        import dataclasses
        tampered = tuple(
            dataclasses.replace(e, log_contribution=e.log_contribution + 1e-6)
            if e.term_role == 'clock' else e
            for e in terms.edges
        )
        with pytest.raises(S4.ProvenanceReconciliationError):
            S4.assert_provenance_reconciles(tampered, math.exp(terms.ln_lambda),
                                            target_id='w1')

    def test_identity_edges_do_not_disturb_the_sum(self):
        ev = _evaluator()
        terms = ev.terms_at(1100.0)
        edges = list(terms.edges) + [
            hazard.identity_edge('route', 'route:rank1', 'l3_row',
                                 source_table='kala_field_routes', source_pk='7'),
            hazard.identity_edge('gate', 'gate:legacy_sweep_xref:agree', 'l3_row',
                                 source_table='kala_gochara_windows', source_pk='991'),
        ]
        S4.assert_provenance_reconciles(edges, math.exp(terms.ln_lambda), target_id='w1')

    def test_tolerance_is_1e_9_in_log_space(self):
        assert S4.RECONCILIATION_TOLERANCE == 1e-9


# ── snapshot identity ────────────────────────────────────────────────────────

class TestSnapshotIdentity:
    def _pins(self, **over):
        base = dict(
            chart_id='482012f1-710e-4a25-994a-93821f5871aa',
            corpus_pin='corpus-2026-07-30',
            weights_version='v0_classical',
            x_schema_version='x12_v0',
            cohort_version='bgc_abc123',
            config_pin={'horizon_days': 36525.0, 'p_floor': 0.05},
        )
        base.update(over)
        return S4.FieldPins(**base)

    def test_pin_id_is_deterministic_and_prefixed(self):
        assert self._pins().field_snapshot_id == self._pins().field_snapshot_id
        assert self._pins().field_snapshot_id.startswith('kfs_')
        assert len(self._pins().field_snapshot_id) == 4 + 32

    def test_every_pin_component_changes_the_id(self):
        ref = self._pins().field_snapshot_id
        for k, v in [('chart_id', 'x'), ('corpus_pin', 'y'), ('weights_version', 'v1'),
                     ('x_schema_version', 'x13_v0'), ('cohort_version', 'bgc_z'),
                     ('config_pin', {'horizon_days': 1.0})]:
            assert self._pins(**{k: v}).field_snapshot_id != ref

    def test_config_pin_key_order_does_not_change_the_id(self):
        # canonical_json sorts keys — otherwise a dict-literal reordering in a
        # future refactor would silently invalidate every stored snapshot.
        a = self._pins(config_pin={'a': 1, 'b': 2}).field_snapshot_id
        b = self._pins(config_pin={'b': 2, 'a': 1}).field_snapshot_id
        assert a == b

    def test_absent_cohort_version_is_an_honest_none_not_an_empty_string(self):
        p = self._pins(cohort_version=None)
        assert p.field_snapshot_id != self._pins(cohort_version='').field_snapshot_id

    def test_float_serialization_is_round_trip_exact(self):
        # §7.4: floats are serialized with repr at 17 significant digits so the
        # hash is stable across platforms.
        assert S4.canonical_json({'x': 0.1 + 0.2}) == S4.canonical_json({'x': 0.30000000000000004})
        assert S4.canonical_json({'x': 0.3}) != S4.canonical_json({'x': 0.1 + 0.2})


class TestContentHash:
    def test_content_hash_is_order_independent_over_rows(self):
        rows_a = [('kala_field', ('e', 0), {'alpha': -9.0}), ('kala_field', ('e', 1), {'alpha': -8.0})]
        rows_b = list(reversed(rows_a))
        assert S4.field_content_hash('pins', rows_a) == S4.field_content_hash('pins', rows_b)

    def test_content_hash_moves_when_any_row_value_moves(self):
        rows = [('kala_field', ('e', 0), {'alpha': -9.0})]
        moved = [('kala_field', ('e', 0), {'alpha': -9.000000001})]
        assert S4.field_content_hash('pins', rows) != S4.field_content_hash('pins', moved)

    def test_content_hash_moves_when_the_pin_identity_moves(self):
        rows = [('kala_field', ('e', 0), {'alpha': -9.0})]
        assert S4.field_content_hash('pinsA', rows) != S4.field_content_hash('pinsB', rows)

    def test_empty_row_set_still_hashes(self):
        assert S4.field_content_hash('pins', []).startswith('kfh_')


# ── honest skip: no classical baseline ───────────────────────────────────────

class TestHonestSkip:
    def test_a_class_with_no_prior_is_skipped_with_a_reason(self):
        # §5.1 C-1: "A class with no prior row is not_computed and is SKIPPED
        # ENTIRELY (no field rows written for it) — never given a made-up
        # baseline." The reason is recorded so a reader sees WHY the class is
        # absent rather than concluding the chart has no hazard for it.
        with pytest.raises(S4.ClassSkipped) as exc:
            S4.require_baseline(None, 'career_change')
        assert exc.value.reason == 'no_class_prior_row'
        assert exc.value.event_class == 'career_change'

    def test_a_non_positive_prior_is_also_a_skip_not_a_floor(self):
        with pytest.raises(S4.ClassSkipped) as exc:
            S4.require_baseline(0.0, 'career_change')
        assert exc.value.reason == 'class_prior_not_positive'

    def test_a_usable_prior_passes_through_unchanged(self):
        assert S4.require_baseline(2.5, 'career_change') == 2.5
