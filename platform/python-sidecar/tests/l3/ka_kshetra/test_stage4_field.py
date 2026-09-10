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
import os
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
    routes = (Route(event_class='e', route_rank=1, path_node_ids=('graha:Ju', 'bhava:10', 'event_class:e'),
                     path_edge_ids=(), route_gain=0.6, is_primary=True),)
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


# ── F-149: bounded-memory content hashing ────────────────────────────────────

def _pre_f149_field_content_hash(pin_identity, rows):
    """A verbatim transcription of the PRE-F-149 implementation.

    It exists so the streaming rewrite's central claim — "the digest did not
    change, only the memory profile did" — is asserted against the old algorithm
    rather than merely stated in a docstring. If someone later alters the
    canonical form on purpose, this reference must be updated in the same commit
    and the divergence becomes visible in review, which is exactly what a
    stored-hash-compatibility change should look like.
    """
    import hashlib as _hashlib
    entries = sorted(
        (table, S4.canonical_json(list(key)), S4.canonical_json(dict(payload)))
        for table, key, payload in rows
    )
    digest = _hashlib.sha256()
    digest.update(pin_identity.encode('utf-8'))
    for table, key_json, payload_json in entries:
        digest.update(b'\x1e')
        digest.update(table.encode('utf-8'))
        digest.update(b'\x1f')
        digest.update(key_json.encode('utf-8'))
        digest.update(b'\x1f')
        digest.update(payload_json.encode('utf-8'))
    return 'kfh_' + digest.hexdigest()[:32]


def _synthetic_hash_rows(n, *, tables=('kala_field', 'kala_field_provenance'),
                         seed=1234):
    """Rows shaped like the real hashed tables: mixed str/int/float/None/bool
    payloads, unsorted arrival order, keys that sort DIFFERENTLY as text than as
    numbers (`segment_index` 2 vs 10) so a would-be "just ORDER BY in SQL"
    shortcut cannot pass this by accident.
    """
    import random
    rnd = random.Random(seed)
    classes = ['marriage', 'career_change', 'health_crisis', 'relocation', 'ādhi']
    out = []
    for i in range(n):
        table = tables[i % len(tables)]
        if table == 'kala_field':
            key = (classes[i % len(classes)], i)
            payload = {
                'event_class': key[0], 'segment_index': key[1],
                't_start': float(i) * 1.5, 't_end': float(i) * 1.5 + 1.5,
                'alpha': rnd.uniform(-12.0, -2.0), 'gamma': rnd.uniform(-1.0, 1.0),
                'integral_days': rnd.uniform(0.0, 40.0),
                'refinement_depth': i % 4, 'refinement_exhausted': bool(i % 3),
            }
        else:
            key = ('window', f'w_{i:09d}', f'term_{i % 17}')
            payload = {
                'target_kind': key[0], 'target_id': key[1], 'term_key': key[2],
                'term_value': rnd.uniform(0.1, 3.0),
                'log_contribution': rnd.uniform(-2.0, 2.0),
                'weight_id': f'w{i % 23}', 'weight_value': rnd.uniform(0.0, 1.0),
                'source_kind': 'table', 'source_table': 'kala_gochara_windows',
                'source_pk': i, 'source_fact_id': None if i % 5 else f'f_{i}',
                'authority_basis': 'classical',
            }
        out.append((table, key, payload))
    rnd.shuffle(out)
    return out


class TestContentHashIsBoundedMemory:
    """F-149. `_compute_content_hash` used to materialize every stage-0–8 row for
    the chart into one list and hand it to `sorted()`, which made a second full
    copy — on the native chart's ~10.5M rows that OOM'd, which is the confirmed
    root cause of the F-141 `ka_kshetra` incident (a rebuild was deterministically
    impossible, not merely slow).

    Two properties have to hold together, and neither is sufficient alone:
      • the digest is UNCHANGED, so every stored `kfh_` value stays comparable
        and the F-77 hash-replay control is not silently re-baselined; and
      • peak memory is a function of the spill chunk, not of the row count.
    """

    ROWS = _synthetic_hash_rows(4_000)

    def test_digest_is_byte_identical_to_the_pre_f149_implementation(self):
        assert (S4.field_content_hash('pins', self.ROWS)
                == _pre_f149_field_content_hash('pins', self.ROWS))

    @pytest.mark.parametrize('chunk', [1, 2, 3, 7, 999, 4_000, 10_000_000])
    def test_digest_does_not_depend_on_the_spill_chunk_size(self, chunk):
        # The failure this guards against is an "accidental batch-size artifact":
        # a hash that depends on how many rows happened to fit in one fetch is
        # not a content hash, it is a hash of the runtime's mood.
        assert (S4.field_content_hash('pins', self.ROWS, chunk_entries=chunk)
                == _pre_f149_field_content_hash('pins', self.ROWS))

    def test_digest_does_not_depend_on_arrival_order_at_any_chunk_size(self):
        shuffled = list(reversed(self.ROWS))
        assert (S4.field_content_hash('pins', shuffled, chunk_entries=13)
                == S4.field_content_hash('pins', self.ROWS, chunk_entries=997))

    def test_a_one_shot_iterator_is_accepted(self):
        # The writer now passes a generator over server-side cursors; a `rows`
        # parameter that quietly required a re-iterable sequence would fail only
        # in production, on the exact build this fix exists to make possible.
        gen = (r for r in self.ROWS)
        assert (S4.field_content_hash('pins', gen, chunk_entries=100)
                == _pre_f149_field_content_hash('pins', self.ROWS))

    def test_a_moved_value_still_moves_the_digest_across_the_spill_path(self):
        moved = list(self.ROWS)
        table, key, payload = moved[0]
        moved[0] = (table, key, dict(payload, **{'alpha': -99.5}) if 'alpha' in payload
                    else dict(payload, **{'term_value': -99.5}))
        assert (S4.field_content_hash('pins', moved, chunk_entries=7)
                != S4.field_content_hash('pins', self.ROWS, chunk_entries=7))

    def test_peak_memory_is_bounded_by_the_chunk_not_the_row_count(self):
        """The §N.8 detector for this fix.

        Without it, "streaming" is a claim with nothing behind it: the digest
        tests above would all still pass over an implementation that buffered
        everything.

        WHAT IS AND IS NOT CLAIMED. An external merge sort's peak is
        O(chunk) + O(run_count × per-run I/O buffer), i.e. O(chunk + N/chunk) —
        NOT O(1), and this test would be dishonest if it asserted otherwise. What
        it asserts is the property that matters: with the chunk pinned in the
        regime the code actually ships in (chunk >> N/chunk), quadrupling the row
        count barely moves peak memory, while the pre-F-149 reference tracks it
        linearly. Measured on this fixture: 5.6MB -> 7.6MB streaming versus
        25MB -> 100MB materialized. The bounds below are loose because
        tracemalloc measures a live interpreter, not a model — but the two
        populations are an order of magnitude apart, so a regression that
        reintroduces full materialization cannot sneak between them.
        """
        import tracemalloc

        def peak(fn, n):
            rows = _synthetic_hash_rows(n)
            src = (r for r in rows)          # do not count the fixture itself
            tracemalloc.start()
            tracemalloc.reset_peak()
            try:
                fn(src)
            finally:
                _, pk = tracemalloc.get_traced_memory()
                tracemalloc.stop()
            del rows
            return pk

        small, large = 50_000, 200_000
        chunk = 10_000
        stream_s = peak(lambda it: S4.field_content_hash('p', it, chunk_entries=chunk), small)
        stream_l = peak(lambda it: S4.field_content_hash('p', it, chunk_entries=chunk), large)
        ref_s = peak(lambda it: _pre_f149_field_content_hash('p', it), small)
        ref_l = peak(lambda it: _pre_f149_field_content_hash('p', it), large)

        stream_growth = stream_l / max(stream_s, 1)
        ref_growth = ref_l / max(ref_s, 1)
        assert stream_growth < 1.8, (
            f'streaming peak grew {stream_growth:.2f}x for a 4x row count '
            f'({stream_s} -> {stream_l} bytes) — it is not actually streaming'
        )
        assert ref_growth > 3.0, (
            f'the pre-F-149 reference only grew {ref_growth:.2f}x for 4x rows '
            f'({ref_s} -> {ref_l} bytes) — this control no longer reproduces the '
            'defect, so the comparison above proves nothing'
        )
        assert stream_l * 5 < ref_l, (
            f'streaming peak {stream_l} is not decisively below the materialized '
            f'peak {ref_l} at {large} rows'
        )

    def test_a_truncated_spill_run_refuses_to_emit_a_hash(self):
        # An honest halt beats a digest computed over a partial dataset — the
        # latter is exactly the "confident-looking wrong answer" class this
        # campaign exists to remove.
        fh = S4._spill_run([('t', '["a"]', '{"x":1}')], None)
        fh.seek(0)
        data = fh.read()
        fh.seek(0)
        fh.truncate()
        fh.write(data[:-3])
        fh.seek(0)
        with pytest.raises(RuntimeError, match='truncated'):
            list(S4._read_run(fh))


class TestContentHashAtRealisticScale:
    """R-6 requires this fix to be 'tested against a realistically-sized dataset'.

    HONEST SCOPE. The default-on test below runs 300,000 entries, not the native
    chart's ~10.5M. It is a scaled-down proxy, and the scaling is justified by
    what the algorithm's cost actually depends on: the external merge sort's
    memory is O(chunk) and its correctness rests on the k-way merge of R sorted
    runs, so the properties under test are exercised by driving R above 1 by a
    healthy margin — here 300k/25k = 12 runs, versus 42 runs at the real 10.5M
    with the shipped 250k default. Nothing in the code path changes shape between
    12 runs and 42.

    The FULL-SCALE run is available and was executed by hand before this landed;
    it is opt-in rather than default because it needs ~5 minutes and several GB
    of scratch disk, which is not a per-PR CI cost. Set
    KA_KSHETRA_HASH_SCALE_TEST_ROWS=10500000 to reproduce it.
    """

    SCALE_ROWS = int(os.environ.get('KA_KSHETRA_HASH_SCALE_TEST_ROWS', '300000'))

    def test_scale_run_matches_the_reference_and_is_chunk_invariant(self):
        n = self.SCALE_ROWS
        chunk = max(n // 12, 1_000)

        def gen():
            # Generated lazily and in blocks so the FIXTURE never becomes the
            # memory hog the code under test is being cleared of.
            block = 25_000
            done = 0
            while done < n:
                take = min(block, n - done)
                yield from _synthetic_hash_rows(take, seed=done)
                done += take

        streamed = S4.field_content_hash('scale', gen(), chunk_entries=chunk)
        # A second pass at a very different chunk size must land on the same
        # digest — the whole point of a merge that reproduces the total order.
        streamed_again = S4.field_content_hash('scale', gen(),
                                               chunk_entries=max(chunk // 7, 500))
        assert streamed == streamed_again
        assert streamed.startswith('kfh_')

        if n <= 300_000:
            # Only cross-check against the memory-hungry reference at proxy
            # scale; running it at 10.5M is the very thing that OOMs.
            assert streamed == _pre_f149_field_content_hash('scale', gen())


# ── F-149: streaming row access ──────────────────────────────────────────────

class _BatchCursor:
    """A cursor that serves rows in batches and RECORDS the batch sizes asked
    for, so 'it streams' is checked rather than assumed."""

    def __init__(self, rows, tuples=False):
        self._rows = list(rows)
        self._i = 0
        self.requested: list[int] = []
        self.closed = False
        self.itersize = None
        self.description = [(k,) for k in (rows[0].keys() if rows else ())] if tuples else None
        self._tuples = tuples

    def fetchmany(self, size):
        self.requested.append(size)
        batch = self._rows[self._i:self._i + size]
        self._i += len(batch)
        if self._tuples:
            return [tuple(r.values()) for r in batch]
        return batch

    def fetchall(self):
        rest = self._rows[self._i:]
        self._i = len(self._rows)
        return rest

    def close(self):
        self.closed = True


class _NoFetchmanyCursor:
    def __init__(self, rows):
        self._rows = list(rows)
        self.description = None

    def fetchall(self):
        return self._rows


class TestIterRows:
    ROWS = [{'a': i, 'b': f'v{i}'} for i in range(250)]

    def test_streams_in_bounded_batches_and_yields_every_row(self):
        cur = _BatchCursor(self.ROWS)
        got = list(S4.iter_rows(cur, batch_size=40))
        assert got == self.ROWS
        assert cur.requested and set(cur.requested) == {40}
        assert len(cur.requested) == 8      # 6 full + 1 partial + 1 empty sentinel

    def test_normalizes_tuple_rows_the_same_way_the_eager_path_does(self):
        cur = _BatchCursor(self.ROWS, tuples=True)
        assert list(S4.iter_rows(cur, batch_size=64)) == self.ROWS

    def test_falls_back_to_fetchall_for_a_cursor_without_fetchmany(self):
        # The in-memory test fake is exactly this shape; a hard requirement on
        # fetchmany would have broken every DB-free test in this lane.
        assert list(S4.iter_rows(_NoFetchmanyCursor(self.ROWS))) == self.ROWS

    def test_empty_result_yields_nothing_and_stops(self):
        cur = _BatchCursor([])
        assert list(S4.iter_rows(cur, batch_size=10)) == []


class _CursorConn:
    """Records whether a SERVER-SIDE cursor was requested, and refuses the
    FROZEN-contract-violating calls outright."""

    def __init__(self, *, supports_named=True):
        self.supports_named = supports_named
        self.names: list[str] = []
        self.cursors: list[_BatchCursor] = []

    def cursor(self, name=None):
        if name is not None:
            if not self.supports_named:
                raise TypeError('cursor() got an unexpected keyword argument')
            self.names.append(name)
        cur = _BatchCursor([{'a': 1}])
        self.cursors.append(cur)
        return cur

    def commit(self):
        raise AssertionError('FROZEN CONTRACT VIOLATION: commit() on ctx.db_conn')

    def close(self):
        raise AssertionError('FROZEN CONTRACT VIOLATION: close() on ctx.db_conn')


class TestStreamingCursor:
    def test_prefers_a_named_server_side_cursor_and_sets_itersize(self):
        conn = _CursorConn()
        with S4.streaming_cursor(conn, 'kfh_kala_field', itersize=1234) as cur:
            assert cur.itersize == 1234
        assert len(conn.names) == 1
        assert conn.names[0].startswith('kfh_kala_field_')

    def test_names_are_unique_per_call(self):
        # A named cursor's name must be unique within its transaction, and this
        # is opened once per hashed table inside ONE orchestrator transaction.
        conn = _CursorConn()
        for _ in range(5):
            with S4.streaming_cursor(conn, 'kfh'):
                pass
        assert len(set(conn.names)) == 5

    def test_degrades_to_a_plain_cursor_when_the_driver_has_no_named_cursors(self):
        conn = _CursorConn(supports_named=False)
        with S4.streaming_cursor(conn) as cur:
            assert cur is not None
        assert conn.names == []

    def test_closes_its_own_cursor_and_never_the_connection(self):
        conn = _CursorConn()
        with S4.streaming_cursor(conn) as cur:
            pass
        assert cur.closed is True          # the cursor, which the writer owns
        # `conn.commit()` / `conn.close()` raise; reaching here means neither ran.

    def test_closes_the_cursor_even_when_the_body_raises(self):
        conn = _CursorConn()
        with pytest.raises(ValueError):
            with S4.streaming_cursor(conn) as cur:
                raise ValueError('boom')
        assert cur.closed is True


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


# ── N_e selection determinism (§5.1 C-1's RESERVED COORDINATE) ───────────────

class _RecordingCursor:
    """Records the SQL + params, and replays a caller-supplied row table through
    a deliberately literal interpretation of the WHERE clause.

    It is not a SQL engine: it understands exactly the four predicates the
    reserved coordinate is made of, plus the ORDER BY. That is the point — a
    predicate the production SQL does NOT issue simply never filters here, so a
    missing predicate shows up as the wrong row being returned rather than as a
    silently-passing test.
    """

    def __init__(self, rows: list[dict], log: list[tuple[str, tuple]]):
        self._all = rows
        self._log = log
        self._rows: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql: str, params: tuple = ()) -> None:
        s = ' '.join(sql.split())
        self._log.append((s, params))
        rows = [r for r in self._all
                if r['fact_kind'] == 'lifetime_count_per_100y'
                and r['signal_type_class'] == params[0]]
        if "source_subsystem = '*'" in s:
            rows = [r for r in rows if r['source_subsystem'] == '*']
        if "signal_tradition = '*'" in s:
            rows = [r for r in rows if r['signal_tradition'] == '*']
        # Mirror Postgres's ORDER BY exactly as written, so a non-total ordering
        # here produces the same tie the database would produce.
        if 'ORDER BY prior_version DESC, source_subsystem, signal_tradition' in s:
            rows = sorted(rows, key=lambda r: (
                tuple(-ord(c) for c in r['prior_version']),
                r['source_subsystem'], r['signal_tradition']))
        elif 'ORDER BY prior_version DESC' in s:
            # A non-total ordering: Postgres is free to return ties in ANY order.
            # The adversarial replay returns them in INSERT order, which is the
            # order a real heap scan most often produces.
            rows = sorted(rows, key=lambda r: tuple(-ord(c) for c in r['prior_version']))
        self._rows = rows[:1] if 'LIMIT 1' in s else rows

    def fetchall(self) -> list[dict]:
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _RecordingConn:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.log: list[tuple[str, tuple]] = []

    def cursor(self) -> _RecordingCursor:
        return _RecordingCursor(self.rows, self.log)


def _prior_row(*, subsystem: str, tradition: str, value: float,
               prior_version: str = 'ne_v01') -> dict:
    return {'prior_version': prior_version,
            'signal_type_class': 'marriage',
            'fact_kind': 'lifetime_count_per_100y',
            'source_subsystem': subsystem,
            'signal_tradition': tradition,
            'class_prior': value}


class TestClassLifetimeCountSelection:
    """§5.1 C-1 + §N.7 item 2: N_e is read from ONE reserved coordinate, and the
    selection that reduces the table to one row must be TOTAL.

    This stopped being latent the moment `bg_class_lifetime_counts` seeded six
    real classes at `ne_v01` (migration 522 / `brahmagyan/l0_class_lifetime_
    counts.py`): every one of those rows sits at ('*','*'), so any row a sibling
    lane later writes at a NARROWER coordinate becomes a live candidate for the
    same `LIMIT 1`.
    """

    def test_the_reserved_coordinate_is_pinned_in_the_sql(self):
        conn = _RecordingConn([_prior_row(subsystem='*', tradition='*', value=1.1)])
        S4.load_class_lifetime_count(conn, 'marriage')
        sql, _ = conn.log[0]
        assert "source_subsystem = '*'" in sql
        assert "signal_tradition = '*'" in sql

    def test_a_narrower_coordinate_never_wins_the_limit_1(self):
        # Two rows, SAME class and SAME prior_version, differing only in the two
        # coordinate columns. Only the ('*','*') row is the reserved coordinate;
        # the other is some other lane's subsystem-specific prior and must not
        # be able to become this class's chart-independent baseline.
        conn = _RecordingConn([
            _prior_row(subsystem='jaimini', tradition='parashari', value=9.9),
            _prior_row(subsystem='*', tradition='*', value=1.1),
        ])
        value, source = S4.load_class_lifetime_count(conn, 'marriage')
        assert value == 1.1
        assert source is not None and source[0] == 'brahma_class_priors'

    def test_selection_is_order_independent(self):
        # The same two rows in the opposite physical order must give the same
        # answer. A non-total ORDER BY would let the heap-scan order decide N_e,
        # which would make λ⁰ — and therefore the whole field hash — depend on
        # something no version pin covers.
        seen = set()
        for rows in (
            [_prior_row(subsystem='*', tradition='*', value=1.1),
             _prior_row(subsystem='jaimini', tradition='*', value=9.9)],
            [_prior_row(subsystem='jaimini', tradition='*', value=9.9),
             _prior_row(subsystem='*', tradition='*', value=1.1)],
        ):
            value, _ = S4.load_class_lifetime_count(_RecordingConn(rows), 'marriage')
            seen.add(value)
        assert seen == {1.1}

    def test_the_order_by_is_total(self):
        conn = _RecordingConn([_prior_row(subsystem='*', tradition='*', value=1.1)])
        S4.load_class_lifetime_count(conn, 'marriage')
        sql, _ = conn.log[0]
        assert 'ORDER BY prior_version DESC, source_subsystem, signal_tradition' in sql

    def test_the_newest_prior_version_still_wins(self):
        conn = _RecordingConn([
            _prior_row(subsystem='*', tradition='*', value=1.1, prior_version='ne_v01'),
            _prior_row(subsystem='*', tradition='*', value=2.2, prior_version='ne_v02'),
        ])
        value, source = S4.load_class_lifetime_count(conn, 'marriage')
        assert value == 2.2
        assert source[1].startswith('ne_v02|')

    def test_no_row_at_the_reserved_coordinate_is_an_honest_none(self):
        # A class seeded ONLY at a narrower coordinate has no chart-independent
        # baseline. §5.1 C-1 skips it; it never inherits the narrower row.
        conn = _RecordingConn([_prior_row(subsystem='jaimini', tradition='parashari',
                                          value=9.9)])
        value, source = S4.load_class_lifetime_count(conn, 'marriage')
        assert value is None and source is None


class TestLoadLegacyCrosscheck:
    """PG-31 (UTK post-close audit): load_legacy_crosscheck must be
    generation-aware so that it reads only the authoritative generation's rows
    from kala_gochara_windows when v1 and 3.0 rows coexist.

    The fix: a correlated COALESCE sub-select against kala_gochara_authority —
    the same seam contract the MCP serving layer uses
    (register_gochara_windows.ts AUTHORITATIVE_GENERATION_FILTER).  When the
    authority table has no row for this chart, 'v1' is the default (migration
    527: an ABSENT row means v1 authoritative by definition).
    """

    def test_sql_filters_by_authoritative_generation(self):
        # The SQL emitted must reference kala_gochara_authority and
        # authoritative_generation so the filter is generation-aware, not
        # generation-blind.  A missing predicate would cause one xref edge PER
        # GENERATION per window — double-counted, self-referential provenance.
        conn = _RecordingConn([])
        S4.load_legacy_crosscheck(conn, 'chart-abc', 'career_advancement')
        sql, params = conn.log[0]
        assert 'kala_gochara_authority' in sql, (
            'load_legacy_crosscheck must join kala_gochara_authority to resolve '
            'the authoritative generation; generation-blind reads produce '
            'double-counted provenance edges when v1+3.0 rows coexist')
        assert 'authoritative_generation' in sql
        assert 'COALESCE' in sql, (
            "default to 'v1' via COALESCE so charts without an authority row "
            'remain functional (migration 527: absent row → v1 authoritative)')

    def test_default_generation_fallback_is_v1(self):
        # The COALESCE fallback must be the string literal 'v1' — the same
        # default the serving layer and migration 527 specify.
        conn = _RecordingConn([])
        S4.load_legacy_crosscheck(conn, 'chart-abc', 'career_advancement')
        sql, _ = conn.log[0]
        assert "'v1'" in sql, (
            "COALESCE fallback must be literal 'v1' to match the authority "
            "table's documented default (migration 527 COMMENT ON TABLE)")

    def test_generation_predicate_is_not_hardcoded(self):
        # Must NOT hardcode generation='v1' — that would never flip to 3.0 even
        # after the authority table is seeded, defeating the whole fix.
        conn = _RecordingConn([])
        S4.load_legacy_crosscheck(conn, 'chart-abc', 'career_advancement')
        sql, _ = conn.log[0]
        assert "generation = 'v1'" not in sql, (
            "generation must not be hardcoded: use COALESCE against "
            "kala_gochara_authority so the predicate flips automatically when "
            "the authority row is updated to '3.0'")

    def test_params_are_chart_id_and_event_class_only(self):
        # The correlated sub-select uses kala_gochara_windows.chart_id as a
        # column reference, NOT a bound parameter — so params must still be
        # exactly (chart_id, event_class), same as before the fix.
        conn = _RecordingConn([])
        S4.load_legacy_crosscheck(conn, 'chart-abc', 'career_advancement')
        _, params = conn.log[0]
        assert params == ('chart-abc', 'career_advancement'), (
            'Bound params must be exactly (chart_id, event_class); '
            'the authority sub-select uses a correlated column reference, '
            'not a third bound parameter')


class TestSpillDirEnv:
    """F-185: `KA_KSHETRA_HASH_SPILL_DIR` used to be read with
    `os.environ.get(...) or None` — no validation, no logging, so a
    misconfigured or silently-tmpfs spill directory was invisible until an
    OOM. `_resolve_spill_dir_env` / `_detect_filesystem_kind` are the fix's
    detectors; these tests are the §N.8 "can it actually fail" proof for each
    branch, plus the deliberate accept-not-reject behaviour for tmpfs (no
    Cloud Run volume mount exists in this repo's infra, so the interim
    disposition is memory headroom, not a hard tmpfs failure — see
    deploy.yml)."""

    def test_unset_returns_none_and_logs_info(self, monkeypatch, caplog):
        monkeypatch.delenv('KA_KSHETRA_HASH_SPILL_DIR', raising=False)
        with caplog.at_level('INFO', logger='services.ka_kshetra.stage4_field'):
            result = S4._resolve_spill_dir_env('KA_KSHETRA_HASH_SPILL_DIR')
        assert result is None
        assert any('not set' in r.message for r in caplog.records)

    def test_empty_string_treated_as_unset(self, monkeypatch):
        monkeypatch.setenv('KA_KSHETRA_HASH_SPILL_DIR', '')
        assert S4._resolve_spill_dir_env('KA_KSHETRA_HASH_SPILL_DIR') is None

    def test_a_real_writable_directory_is_accepted_and_logged(self, tmp_path, monkeypatch, caplog):
        monkeypatch.setenv('KA_KSHETRA_HASH_SPILL_DIR', str(tmp_path))
        monkeypatch.setattr(S4, '_detect_filesystem_kind', lambda path: 'ext4')
        with caplog.at_level('INFO', logger='services.ka_kshetra.stage4_field'):
            result = S4._resolve_spill_dir_env('KA_KSHETRA_HASH_SPILL_DIR')
        assert result == str(tmp_path)
        assert any('ext4' in r.message for r in caplog.records)

    def test_nonexistent_directory_raises(self, tmp_path, monkeypatch):
        missing = tmp_path / 'does-not-exist'
        monkeypatch.setenv('KA_KSHETRA_HASH_SPILL_DIR', str(missing))
        with pytest.raises(RuntimeError, match='does not exist'):
            S4._resolve_spill_dir_env('KA_KSHETRA_HASH_SPILL_DIR')

    def test_read_only_directory_raises(self, tmp_path, monkeypatch):
        if os.geteuid() == 0:
            pytest.skip('root bypasses the write-permission check this test exercises')
        ro_dir = tmp_path / 'read-only'
        ro_dir.mkdir()
        ro_dir.chmod(0o555)
        try:
            monkeypatch.setenv('KA_KSHETRA_HASH_SPILL_DIR', str(ro_dir))
            with pytest.raises(RuntimeError, match='not writable'):
                S4._resolve_spill_dir_env('KA_KSHETRA_HASH_SPILL_DIR')
        finally:
            ro_dir.chmod(0o755)

    def test_insufficient_free_space_raises(self, tmp_path, monkeypatch):
        monkeypatch.setenv('KA_KSHETRA_HASH_SPILL_DIR', str(tmp_path))
        fake_usage = type('Usage', (), {'free': S4.REQUIRED_SPILL_FREE_BYTES - 1})()
        monkeypatch.setattr(S4.shutil, 'disk_usage', lambda path: fake_usage)
        with pytest.raises(RuntimeError, match='free'):
            S4._resolve_spill_dir_env('KA_KSHETRA_HASH_SPILL_DIR')

    def test_tmpfs_is_accepted_not_rejected_but_warns_loudly(self, tmp_path, monkeypatch, caplog):
        # This is the load-bearing case: F-185's directive (no volume mount
        # exists to provision in this fix) is "accept tmpfs, raise memory
        # instead of a hard fail" — but the acceptance must be OBSERVABLE, not
        # silent. Today's pre-fix code neither raised nor logged anything.
        monkeypatch.setenv('KA_KSHETRA_HASH_SPILL_DIR', str(tmp_path))
        monkeypatch.setattr(S4, '_detect_filesystem_kind', lambda path: 'tmpfs')
        with caplog.at_level('WARNING', logger='services.ka_kshetra.stage4_field'):
            result = S4._resolve_spill_dir_env('KA_KSHETRA_HASH_SPILL_DIR')
        assert result == str(tmp_path)
        assert any(
            r.levelname == 'WARNING' and 'tmpfs' in r.message for r in caplog.records
        ), 'a tmpfs spill dir must be logged at WARNING, not silently accepted'

    def test_undetectable_filesystem_warns_does_not_raise(self, tmp_path, monkeypatch, caplog):
        # §N.8: a check that cannot determine the answer on this platform must
        # say so (WARNING), never report a silent pass at INFO or below.
        monkeypatch.setenv('KA_KSHETRA_HASH_SPILL_DIR', str(tmp_path))
        monkeypatch.setattr(S4, '_detect_filesystem_kind', lambda path: None)
        with caplog.at_level('WARNING', logger='services.ka_kshetra.stage4_field'):
            result = S4._resolve_spill_dir_env('KA_KSHETRA_HASH_SPILL_DIR')
        assert result == str(tmp_path)
        assert any(r.levelname == 'WARNING' for r in caplog.records)

    def test_detect_filesystem_kind_returns_none_without_proc_mounts(self, tmp_path, monkeypatch):
        monkeypatch.setattr(S4.os.path, 'exists', lambda p: False)
        assert S4._detect_filesystem_kind(str(tmp_path)) is None

    def test_detect_filesystem_kind_matches_longest_mount_prefix(self, tmp_path, monkeypatch):
        fake_proc_mounts = (
            'overlay / overlay rw,relatime 0 0\n'
            f'tmpfs {tmp_path} tmpfs rw,relatime 0 0\n'
        )
        real_exists = S4.os.path.exists
        monkeypatch.setattr(
            S4.os.path, 'exists',
            lambda p: True if p == '/proc/mounts' else real_exists(p))
        # `open` is a builtin, not a module attribute of S4 — patch it via
        # builtins so the function under test (which calls bare `open(...)`)
        # observes the fake mount table.
        monkeypatch.setattr('builtins.open', lambda *a, **kw: __import__('io').StringIO(fake_proc_mounts))
        assert S4._detect_filesystem_kind(str(tmp_path)) == 'tmpfs'
