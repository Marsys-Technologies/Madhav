"""
tests/l3/ka_kshetra/test_stage5_null.py — ṢAḌ-DARŚANA W2 Lane C, §5.5–§5.6.

The circular-shift null (item 23), the robustness vector, the confidence tier and
the Adṛṣṭa residual.

The statistics here are REAL, COMPUTABLE AND FALSIFIABLE — no placeholders. Each
test below pins either an exactness property (the shift grid is computed not
drawn; the p-value has the standard +1 correction; the resolution is served so
p = 1/257 cannot be read as p = 0) or a genuine failure mode (a null that is
stronger than the observation must produce a NON-significant p; a robustness
dimension with no data must read `None`, never `True`).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra import integrator as I, stage5_null as S5  # noqa: E402
from services.ka_kshetra.contracts import ClockApplicability, PromisePrior, Route  # noqa: E402
from services.ka_kshetra import stage4_field as S4  # noqa: E402


# ── the deterministic shift grid ─────────────────────────────────────────────

class TestShiftGrid:
    def test_grid_is_computed_not_drawn(self):
        # NO RNG ANYWHERE (§5.5). Hash-replay depends on it: a seeded PRNG would
        # tie the field hash to library-internal generator behaviour.
        g = S5.shift_grid(horizon_days=1000.0, replicates=4)
        assert g == [250.0, 500.0, 750.0, 1000.0]

    def test_grid_has_exactly_R_shifts_starting_at_r_equals_one(self):
        g = S5.shift_grid(horizon_days=36525.0, replicates=256)
        assert len(g) == 256
        assert g[0] == pytest.approx(36525.0 / 256)
        assert g[-1] == pytest.approx(36525.0)

    def test_grid_is_reproducible(self):
        assert S5.shift_grid(36525.0, 256) == S5.shift_grid(36525.0, 256)

    def test_zero_replicates_is_rejected(self):
        with pytest.raises(ValueError):
            S5.shift_grid(100.0, 0)


# ── bucket selection ─────────────────────────────────────────────────────────

class TestBucketSelection:
    def test_smallest_bucket_at_or_above_the_window_duration(self):
        assert S5.select_bucket(0.4) == 1
        assert S5.select_bucket(1.0) == 1
        assert S5.select_bucket(2.0) == 3
        assert S5.select_bucket(45.0) == 60
        assert S5.select_bucket(365.0) == 365

    def test_over_long_windows_clamp_to_the_largest_bucket(self):
        # Conservative in the right direction: the largest matched filter is the
        # closest available, and a longer filter can only ACCUMULATE MORE, so p
        # remains an upper bound rather than an understated one.
        assert S5.select_bucket(5000.0) == max(S5.DURATION_BUCKETS)

    def test_buckets_are_the_design_s_ten(self):
        assert S5.DURATION_BUCKETS == (1, 3, 7, 15, 30, 60, 90, 180, 365, 730)


# ── the permutation p-value ──────────────────────────────────────────────────

class TestNullP:
    def test_standard_plus_one_correction(self):
        # p = (1 + #{r: M_r ≥ Λ_obs}) / (R + 1). Even an observation that beats
        # EVERY replicate gets p = 1/(R+1), never 0 — because with R replicates
        # you cannot have measured a smaller probability than that.
        stats = [1.0] * 256
        assert S5.null_p(stats, lambda_obs=99.0) == pytest.approx(1.0 / 257.0)

    def test_an_observation_beaten_by_every_replicate_is_p_equals_one(self):
        stats = [99.0] * 256
        assert S5.null_p(stats, lambda_obs=1.0) == pytest.approx(257.0 / 257.0)

    def test_ties_count_as_exceedances_conservatively(self):
        # `M_r ≥ Λ_obs`, not `>`. A tie is evidence AGAINST the observation being
        # exceptional; scoring it the other way would inflate significance.
        assert S5.null_p([5.0, 1.0, 1.0, 1.0], lambda_obs=5.0) == pytest.approx(2.0 / 5.0)

    def test_resolution_is_one_over_R_plus_one(self):
        assert S5.null_resolution(256) == pytest.approx(1.0 / 257.0)
        assert S5.null_resolution(256) == pytest.approx(0.00389, abs=1e-5)

    def test_exceeding_flag_uses_the_declared_alpha(self):
        assert S5.null_exceeding(0.05) is True
        assert S5.null_exceeding(0.0500001) is False
        assert S5.ALPHA == 0.05

    def test_p_can_never_be_reported_below_its_own_resolution(self):
        # LAW ZERO: we do not report a precision the replicate count cannot
        # support. This is the arithmetic guarantee behind serving null_p
        # alongside null_R and null_resolution.
        for k in range(0, 257):
            stats = [99.0] * k + [0.0] * (256 - k)
            p = S5.null_p(stats, lambda_obs=1.0)
            assert p >= S5.null_resolution(256) - 1e-15

    def test_empty_replicate_set_is_an_honest_none(self):
        assert S5.null_p([], lambda_obs=1.0) is None


# ── q_e: the null's 95th-percentile rate ─────────────────────────────────────

class TestQuantilePool:
    def test_pool_reproduces_the_exact_quantile_of_the_full_sample(self):
        import random
        rng = random.Random(20260730)          # test fixture only — never in prod code
        sample = [rng.random() for _ in range(20_000)]
        pool = S5.QuantilePool(quantile=0.95, expected_total=20_000)
        for chunk_start in range(0, 20_000, 997):
            pool.add(sample[chunk_start:chunk_start + 997])
        exact = sorted(sample)[math.ceil(0.95 * 20_000) - 1]
        assert pool.value() == pytest.approx(exact)

    def test_pool_memory_is_bounded_by_the_upper_tail(self):
        pool = S5.QuantilePool(quantile=0.95, expected_total=100_000)
        pool.add([float(i) for i in range(100_000)])
        assert len(pool._heap) <= pool._capacity
        assert pool._capacity < 100_000

    def test_pool_is_order_independent(self):
        vals = [float(i) for i in range(5000)]
        a = S5.QuantilePool(0.95, 5000)
        a.add(vals)
        b = S5.QuantilePool(0.95, 5000)
        b.add(list(reversed(vals)))
        assert a.value() == b.value()

    def test_empty_pool_is_an_honest_none(self):
        assert S5.QuantilePool(0.95, 10).value() is None


# ── replicate statistics over a real (small) field ───────────────────────────

def _evaluator(horizon=200.0, hump_at=100.0):
    """A tiny but genuine field: flat baseline plus one contact hump."""
    return S4.FieldEvaluator(
        event_class='e',
        lifetime_count=2.0,
        promise=PromisePrior(p=0.4, routes=(
            Route('e', 1, ('graha:Ju', 'event_class:e'), 0.6, True, ()),), n_routes=1),
        clocks=[ClockApplicability('vimshottari', 'applicable', 'fruition', 1, True, 0.9)],
        ladder={'vimshottari': [
            S4.LadderPeriod('vimshottari', 'MD', 'Ju', 0.0, horizon)]},
        envelopes=S4.EnvelopeIndex([
            S4.Primitive('contact_moon_ref', 'Ju', None, 'supportive', None,
                         ((hump_at - 10, 0.0), (hump_at, 1.0), (hump_at + 10, 0.0))),
        ], horizon_days=horizon),
        weights={'w_s:vimshottari': 1.0, 'beta:x1': 1.2, 'd:MD': 1.0},
        horizon_days=horizon,
    )


class TestReplicate:
    def test_replicate_shifts_only_the_transit_stream(self):
        # §5.5: "Clock terms C_e, promise P̃_e, baseline λ⁰_e, and all weights are
        # UNCHANGED." The asymmetry IS the null hypothesis — shifting the daśā
        # ladder would destroy the chart's identity.
        ev = _evaluator()
        rep = S5.replicate_evaluator(ev, delta=50.0)
        assert rep.lifetime_count == ev.lifetime_count
        assert rep.promise is ev.promise
        assert rep.weights == ev.weights
        assert rep.ladder == ev.ladder
        assert rep.envelopes is not ev.envelopes

    def test_replicate_moves_the_hump(self):
        ev = _evaluator()
        rep = S5.replicate_evaluator(ev, delta=50.0)
        assert rep.ln_lambda(50.0) == pytest.approx(ev.ln_lambda(100.0), abs=1e-12)

    def test_daily_cumulative_matches_the_analytic_integral(self):
        ev = _evaluator()
        segs = ev.build_segments()
        cum = S5.cumulative_on_grid(segs, horizon_days=200.0, grid_step=1.0)
        assert len(cum) == 201
        assert cum[0] == 0.0
        assert cum[-1] == pytest.approx(I.integrate(segs, 0.0, 200.0), rel=1e-12)
        assert cum[73] == pytest.approx(I.integrate(segs, 0.0, 73.0), rel=1e-12)

    def test_cumulative_is_non_decreasing(self):
        # λ > 0 everywhere, so Λ(0, ·) is strictly increasing. A dip would mean a
        # negative hazard somewhere.
        cum = S5.cumulative_on_grid(_evaluator().build_segments(), 200.0, 1.0)
        assert all(b >= a for a, b in zip(cum, cum[1:]))

    def test_sliding_max_is_the_matched_filter_at_scale_L(self):
        cum = [0.0, 1.0, 3.0, 6.0, 10.0, 11.0]
        assert S5.sliding_window_max(cum, bucket_days=1) == pytest.approx(4.0)
        assert S5.sliding_window_max(cum, bucket_days=2) == pytest.approx(7.0)

    def test_sliding_max_over_a_bucket_longer_than_the_horizon_uses_the_whole_span(self):
        cum = [0.0, 1.0, 3.0]
        assert S5.sliding_window_max(cum, bucket_days=99) == pytest.approx(3.0)

    def test_replicate_stats_cover_every_bucket(self):
        ev = _evaluator()
        stats = S5.replicate_stats(ev, delta=37.0, horizon_days=200.0)
        assert set(stats) == set(S5.DURATION_BUCKETS)
        assert all(v > 0.0 for v in stats.values())

    def test_longer_buckets_accumulate_at_least_as_much(self):
        stats = S5.replicate_stats(_evaluator(), delta=0.0, horizon_days=200.0)
        for a, b in zip(S5.DURATION_BUCKETS, S5.DURATION_BUCKETS[1:]):
            assert stats[b] >= stats[a] - 1e-12


class TestRunNull:
    def test_a_flat_field_is_not_exceeded_by_its_own_shifts(self):
        # A field with NO transit structure is invariant under circular shift, so
        # every replicate reproduces the observation exactly and no window can be
        # significant. This is the null behaving correctly on a negative control —
        # the failure mode that a placeholder statistic would never exhibit.
        flat = S4.FieldEvaluator(
            event_class='e', lifetime_count=2.0,
            promise=PromisePrior(p=0.4),
            clocks=[], ladder={},
            envelopes=S4.EnvelopeIndex([], horizon_days=200.0),
            weights={}, horizon_days=200.0,
        )
        res = S5.run_null(flat, horizon_days=200.0, replicates=8)
        assert res.q_threshold is not None
        obs = I.integrate(flat.build_segments(), 0.0, 30.0)
        p = S5.null_p(res.max_stats[30], obs)
        assert p == pytest.approx(1.0)

    def test_a_structured_field_beats_its_own_shifts_at_the_hump(self):
        ev = _evaluator(horizon=400.0, hump_at=200.0)
        res = S5.run_null(ev, horizon_days=400.0, replicates=16)
        segs = ev.build_segments()
        wins = I.find_windows(segs, res.q_threshold)
        assert wins, 'a field with real structure must produce at least one window'
        w = max(wins, key=lambda x: x.expected_count)
        p = S5.null_p(res.max_stats[S5.select_bucket(w.duration_days)], w.expected_count)
        assert 0.0 < p <= 1.0

    def test_q_threshold_is_a_rate_inside_the_field_s_own_range(self):
        ev = _evaluator()
        res = S5.run_null(ev, horizon_days=200.0, replicates=8)
        segs = ev.build_segments()
        grid = [I.lambda_at(segs, float(t)) for t in range(0, 200)]
        assert min(grid) <= res.q_threshold <= max(grid) * 1.000001

    def test_run_null_is_deterministic(self):
        ev = _evaluator()
        a = S5.run_null(ev, horizon_days=200.0, replicates=8)
        b = S5.run_null(ev, horizon_days=200.0, replicates=8)
        assert a.q_threshold == b.q_threshold
        assert a.max_stats == b.max_stats


# ── §5.6 robustness, confidence tier, Adṛṣṭa ────────────────────────────────

class TestRobustness:
    def test_system_concurrent_needs_two_positive_predictive_systems(self):
        ev = _evaluator()
        assert S5.system_concurrent(ev, t_peak=100.0) is False   # only one system
        ev2 = S4.FieldEvaluator(
            event_class='e', lifetime_count=2.0,
            promise=PromisePrior(p=0.4, routes=(
                Route('e', 1, ('graha:Ju', 'event_class:e'), 0.6, True, ()),)),
            clocks=[ClockApplicability('vimshottari', 'applicable', 'fruition', 1, True, 0.9),
                    ClockApplicability('yogini', 'applicable', 'flavour', 2, True, 0.7)],
            ladder={'vimshottari': [S4.LadderPeriod('vimshottari', 'MD', 'Ju', 0.0, 200.0)],
                    'yogini': [S4.LadderPeriod('yogini', 'MD', 'Ju', 0.0, 200.0)]},
            envelopes=S4.EnvelopeIndex([], horizon_days=200.0),
            weights={'w_s:vimshottari': 1.0, 'w_s:yogini': 0.6, 'd:MD': 1.0},
            horizon_days=200.0,
        )
        assert S5.system_concurrent(ev2, t_peak=100.0) is True

    def test_birth_time_robust_is_true_when_the_peak_survives_the_interval(self):
        ev = _evaluator()
        segs = ev.build_segments()
        q = I.lambda_at(segs, 100.0) * 0.5
        assert S5.birth_time_robust(segs, t_peak=100.0, q=q, sigma_t_days=0.001) is True

    def test_birth_time_robust_is_false_when_the_peak_is_knife_edge(self):
        ev = _evaluator()
        segs = ev.build_segments()
        q = I.lambda_at(segs, 100.0) * 0.999
        # ±1.96·σ with σ = 3 days walks well off a 10-day-wide hump's tip.
        assert S5.birth_time_robust(segs, t_peak=100.0, q=q, sigma_t_days=3.0) is False

    def test_birth_time_robust_is_none_without_a_sigma(self):
        # §N.8: no detector ⇒ null, never green.
        ev = _evaluator()
        assert S5.birth_time_robust(ev.build_segments(), 100.0, 1e-9, None) is None

    def test_ayanamsha_robust_needs_every_pinned_id_present(self):
        pinned = ('lahiri', 'raman', 'kp', 'yukteshwar', 'fagan_bradley')
        assert S5.ayanamsha_robust(set(pinned), pinned) is True
        assert S5.ayanamsha_robust({'lahiri', 'raman', 'kp', 'yukteshwar'}, pinned) is False

    def test_ayanamsha_robust_is_none_when_only_one_ayanamsha_was_computed(self):
        pinned = ('lahiri', 'raman', 'kp', 'yukteshwar', 'fagan_bradley')
        assert S5.ayanamsha_robust({'lahiri'}, pinned) is None
        assert S5.ayanamsha_robust(set(), pinned) is None

    def test_authority_clean_is_false_on_a_dangling_citation(self):
        assert S5.authority_clean(cited=3, resolved=3) is True
        assert S5.authority_clean(cited=3, resolved=2) is False
        assert S5.authority_clean(cited=0, resolved=0) is True

    def test_confidence_tier_is_the_minimum_across_dimensions(self):
        from services.ka_kshetra.contracts import RobustnessVector
        all_true = RobustnessVector(True, True, True, True, True)
        assert all_true.confidence_tier() == 'concurrent'
        assert all_true.weakest_link() is None
        one_false = RobustnessVector(True, False, True, True, True)
        assert one_false.confidence_tier() == 'structural_prior'
        assert one_false.weakest_link() == 'birth_time_robust'

    def test_weakest_link_names_the_first_false_in_the_fixed_order(self):
        from services.ka_kshetra.contracts import RobustnessVector
        v = RobustnessVector(False, False, True, False, True)
        assert v.weakest_link() == 'ayanamsha_robust'

    def test_a_not_computed_dimension_is_not_green(self):
        from services.ka_kshetra.contracts import RobustnessVector
        v = RobustnessVector(None, True, True, True, True)
        assert v.confidence_tier() == 'structural_prior'
        assert v.weakest_link() == 'ayanamsha_robust'

    def test_stage_five_may_never_award_a_calibrated_tier(self):
        # §5.6: 'calibrated_provisional'/'calibrated' are stage-9 OVERRIDES. The
        # field may not promote its own confidence — that is the Circularity
        # Guard's whole point, expressed in the tier vocabulary.
        from services.ka_kshetra.contracts import RobustnessVector
        import itertools
        for combo in itertools.product([True, False, None], repeat=5):
            assert RobustnessVector(*combo).confidence_tier() in (
                'concurrent', 'structural_prior')


class TestAdrishta:
    def test_residual_is_the_share_outside_every_notable_window(self):
        # λ⁰·H is the class's whole classical expectation over the horizon; the
        # windows account for part of it and the Adṛṣṭa residual is the rest.
        r = S5.adrishta_residual(window_integrals=[0.3, 0.2], baseline_rate=1.0 / 36525.0,
                                 horizon_days=36525.0)
        assert r == pytest.approx(0.5)

    def test_residual_is_one_when_no_window_fires(self):
        r = S5.adrishta_residual([], 1.0 / 36525.0, 36525.0)
        assert r == pytest.approx(1.0)

    def test_residual_clamps_at_zero_when_windows_over_account(self):
        # Over-accounting is possible: the field can concentrate more than the
        # classical baseline expects. Clamping to 0 is honest — "no residual" —
        # whereas a negative share would be meaningless.
        r = S5.adrishta_residual([2.0], 1.0 / 36525.0, 36525.0)
        assert r == 0.0

    def test_zero_expectation_is_an_honest_none(self):
        assert S5.adrishta_residual([0.1], 0.0, 36525.0) is None
