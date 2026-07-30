"""
tests/l3/ka_kshetra/test_integrator.py — ṢAḌ-DARŚANA W2 Lane C, §5.2.

THE SEGMENT REPRESENTATION AND EXACT ANALYTIC INTEGRATION.

The headline test here is `TestAnalyticVsNumerical`: the closed-form integral
must agree with a 10⁴-point composite Simpson quadrature to 1e-9 relative on a
fixture segment set — the design's own mandated cross-check (§5.2). Everything
else in this file protects one of the properties that makes that closed form
usable downstream:

  • the log-linear form is EXACTLY integrable, so the stage-9 Poisson likelihood
    and the served `expected_count` are the same arithmetic (§7.2 — "if the
    fitter used a different integral, the published skill score would be
    measuring a model the product does not serve");
  • the integral is ADDITIVE over sub-intervals, so `kala_field.integral_days`
    can be denormalized per segment and summed;
  • ln λ is MONOTONE per segment, so a window's peak is ALWAYS a breakpoint and
    needs no interior optimizer — the property §5.2 says "must not be 'improved'
    into one", because the closed form is what makes the field hash-replayable.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra import integrator as I  # noqa: E402


# ── helpers ───────────────────────────────────────────────────────────────────

def _simpson(f, a: float, b: float, n: int = 10_000) -> float:
    """Composite Simpson on n sub-intervals (n even). Independent of the code
    under test: it evaluates the SEGMENT's own exp(alpha + gamma·(t−t0)) form
    numerically, so an error in the closed form cannot hide in a shared helper."""
    if n % 2:
        n += 1
    h = (b - a) / n
    total = f(a) + f(b)
    for i in range(1, n):
        total += (4.0 if i % 2 else 2.0) * f(a + i * h)
    return total * h / 3.0


def _seg(idx, t0, t1, alpha, gamma):
    return I.Segment(index=idx, t_start=t0, t_end=t1, alpha=alpha, gamma=gamma)


# ── the mandated analytic-vs-numerical cross-check ───────────────────────────

class TestAnalyticVsNumerical:
    #: A deliberately nasty fixture set. It spans nine orders of magnitude in
    #: |gamma| — from the exp() branch, through the expm1() branch, down to the
    #: exact gamma == 0 case — because the two catastrophic-cancellation failure
    #: modes live at opposite ends of that range.
    FIXTURES = [
        # (t_start, t_end, alpha, gamma)
        (0.0,     30.0,  math.log(1e-4),   0.0),          # flat
        (30.0,    45.0,  math.log(1e-4),   +0.20),        # steep rise, |γΔ| = 3
        (45.0,    60.0,  math.log(2e-3),   -0.20),        # steep fall
        (60.0,   160.0,  math.log(5e-5),   +1e-3),        # mild
        (160.0,  260.0,  math.log(5e-5),   -1e-3),
        (260.0,  270.0,  math.log(3e-4),   +1e-6),        # expm1 branch, |γΔ| = 1e-5
        (270.0,  280.0,  math.log(3e-4),   -1e-9),        # deep expm1 branch
        (280.0,  290.0,  math.log(3e-4),   +1e-13),       # below eps: the |γ| ≤ ε path
        (290.0, 1290.0,  math.log(1e-6),   +2e-3),        # long segment, |γΔ| = 2
        (1290.0, 1300.0, math.log(9.9e-1), -0.5),         # large λ, large |γ|
    ]

    def _segments(self):
        return [_seg(i, *f) for i, f in enumerate(self.FIXTURES)]

    def test_each_segment_matches_simpson_to_1e_9_relative(self):
        for seg in self._segments():
            analytic = I.segment_integral(seg, seg.t_start, seg.t_end)
            numeric = _simpson(
                lambda t, s=seg: math.exp(s.alpha + s.gamma * (t - s.t_start)),
                seg.t_start, seg.t_end, n=10_000,
            )
            assert analytic == pytest.approx(numeric, rel=1e-9), (
                f'segment {seg.index} (gamma={seg.gamma}) analytic={analytic!r} '
                f'numeric={numeric!r}'
            )

    def test_whole_field_integral_matches_simpson_to_1e_9_relative(self):
        segs = self._segments()
        a, b = segs[0].t_start, segs[-1].t_end
        analytic = I.integrate(segs, a, b)
        # Piecewise numeric: Simpson is only accurate within a smooth piece, so
        # the reference sums per-segment quadratures. That is a REFERENCE
        # construction, not a reuse of the code under test.
        numeric = sum(
            _simpson(lambda t, s=s: math.exp(s.alpha + s.gamma * (t - s.t_start)),
                     s.t_start, s.t_end, n=10_000)
            for s in segs
        )
        assert analytic == pytest.approx(numeric, rel=1e-9)

    def test_expm1_branch_beats_the_naive_difference_form(self):
        # THE REASON the expm1 form is mandatory. For tiny |γΔ| the naive
        # (e^{α+γΔ} − e^{α})/γ loses almost every significant digit to
        # cancellation. This test asserts the implementation is on the right side
        # of that: it must match the exact analytic limit better than the naive
        # form does.
        seg = _seg(0, 0.0, 10.0, math.log(3e-4), 1e-13)
        exact = _simpson(lambda t: math.exp(seg.alpha + seg.gamma * t), 0.0, 10.0, 20_000)
        naive_num = math.exp(seg.alpha + seg.gamma * 10.0) - math.exp(seg.alpha)
        naive = naive_num / seg.gamma
        ours = I.segment_integral(seg, 0.0, 10.0)
        assert abs(ours - exact) <= abs(naive - exact)
        assert ours == pytest.approx(exact, rel=1e-12)

    def test_gamma_exactly_zero_is_the_rectangle(self):
        seg = _seg(0, 5.0, 12.0, math.log(2e-4), 0.0)
        assert I.segment_integral(seg, 5.0, 12.0) == pytest.approx(2e-4 * 7.0, rel=1e-15)


class TestIntegralAlgebra:
    def test_additivity_over_a_split_point(self):
        seg = _seg(0, 0.0, 100.0, math.log(1e-4), 3e-3)
        whole = I.segment_integral(seg, 0.0, 100.0)
        halves = I.segment_integral(seg, 0.0, 37.5) + I.segment_integral(seg, 37.5, 100.0)
        assert whole == pytest.approx(halves, rel=1e-14)

    def test_empty_and_reversed_intervals_are_zero(self):
        seg = _seg(0, 0.0, 10.0, 0.0, 0.1)
        assert I.segment_integral(seg, 4.0, 4.0) == 0.0
        assert I.integrate([seg], 7.0, 3.0) == 0.0

    def test_integrate_clips_to_the_requested_window(self):
        segs = [_seg(0, 0.0, 10.0, math.log(1e-3), 0.0),
                _seg(1, 10.0, 20.0, math.log(2e-3), 0.0)]
        assert I.integrate(segs, 5.0, 15.0) == pytest.approx(1e-3 * 5 + 2e-3 * 5, rel=1e-14)

    def test_integral_is_strictly_positive_for_any_finite_field(self):
        # λ > 0 everywhere (hazard.py guarantees it), so Λ > 0 over any interval
        # of positive length. A zero or negative expected_count would be a
        # dimensional impossibility, not a small number.
        for gamma in (-2.0, -1e-9, 0.0, 1e-9, 2.0):
            seg = _seg(0, 0.0, 1.0, math.log(1e-9), gamma)
            assert I.segment_integral(seg, 0.0, 1.0) > 0.0


# ── segment construction + adaptive refinement ───────────────────────────────

class TestBuildSegments:
    def test_stored_segment_reproduces_the_true_field_at_both_endpoints(self):
        # alpha_i = ln λ(t_i⁺) and gamma_i is chosen so the segment lands exactly
        # on ln λ(t_{i+1}⁻). That is a DEFINITION of the stored field, so it must
        # hold to machine precision, not approximately.
        def ln_lambda(t):
            return math.log(1e-4) + 0.5 * math.sin(t / 40.0)

        segs = I.build_segments([0.0, 50.0, 130.0, 400.0], ln_lambda)
        for s in segs:
            assert s.alpha == pytest.approx(ln_lambda(s.t_start), abs=1e-12)
            end = s.alpha + s.gamma * (s.t_end - s.t_start)
            assert end == pytest.approx(ln_lambda(s.t_end), abs=1e-12)

    def test_refinement_splits_a_curved_segment_and_drives_residual_under_tau(self):
        def ln_lambda(t):
            return math.log(1e-4) + 1.5 * math.sin(t / 30.0)

        coarse = I.build_segments([0.0, 300.0], ln_lambda, tau=1e9)   # refinement off
        fine = I.build_segments([0.0, 300.0], ln_lambda, tau=0.02)
        assert len(coarse) == 1
        assert len(fine) > 1
        for s in fine:
            if s.refinement_exhausted:
                continue
            tm = 0.5 * (s.t_start + s.t_end)
            residual = abs(ln_lambda(tm) - (s.alpha + s.gamma * (tm - s.t_start)))
            assert residual <= I.DEFAULT_TAU + 1e-12

    def test_refinement_respects_max_depth_and_flags_exhaustion_visibly(self):
        # A pathological field that cannot be linearized at depth 6. The segment
        # is STILL STORED, with refinement_exhausted=True and its residual
        # recorded — visible, never silent (LAW ZERO).
        def ln_lambda(t):
            return math.log(1e-4) + 40.0 * math.sin(t * 7.0)

        segs = I.build_segments([0.0, 100.0], ln_lambda, tau=0.02, max_depth=2)
        assert any(s.refinement_exhausted for s in segs)
        for s in segs:
            assert s.refinement_depth <= 2
            if s.refinement_exhausted:
                assert s.refinement_residual is not None
                assert s.refinement_residual > 0.02

    def test_max_depth_six_bounds_sub_segments_at_sixty_four_per_original(self):
        def ln_lambda(t):
            return math.log(1e-4) + 40.0 * math.sin(t * 7.0)

        segs = I.build_segments([0.0, 100.0], ln_lambda)   # DEFAULT_MAX_DEPTH = 6
        assert I.DEFAULT_MAX_DEPTH == 6
        assert len(segs) <= 2 ** I.DEFAULT_MAX_DEPTH

    def test_segments_are_contiguous_ordered_and_index_ascending(self):
        segs = I.build_segments([0.0, 10.0, 25.0, 90.0], lambda t: math.log(1e-4) + 0.001 * t)
        assert [s.index for s in segs] == list(range(len(segs)))
        for a, b in zip(segs, segs[1:]):
            assert a.t_end == b.t_start
            assert a.t_start < a.t_end

    def test_duplicate_and_unsorted_breakpoints_are_normalized(self):
        segs = I.build_segments([50.0, 0.0, 50.0, 25.0], lambda t: math.log(1e-4))
        assert [(s.t_start, s.t_end) for s in segs] == [(0.0, 25.0), (25.0, 50.0)]

    def test_fewer_than_two_distinct_breakpoints_is_an_honest_empty(self):
        assert I.build_segments([7.0, 7.0], lambda t: 0.0) == []
        assert I.build_segments([], lambda t: 0.0) == []


# ── windows: closed-form crossings, peak always at a breakpoint ──────────────

class TestWindows:
    def _flat_hump(self):
        """A field that is 1e-4 outside [100,200] and rises to 1e-3 at t=150."""
        lo, hi = math.log(1e-4), math.log(1e-3)
        return [
            _seg(0, 0.0, 100.0, lo, 0.0),
            _seg(1, 100.0, 150.0, lo, (hi - lo) / 50.0),
            _seg(2, 150.0, 200.0, hi, (lo - hi) / 50.0),
            _seg(3, 200.0, 300.0, lo, 0.0),
        ]

    def test_window_endpoints_are_the_exact_closed_form_crossings(self):
        segs = self._flat_hump()
        q = 5e-4
        wins = I.find_windows(segs, q)
        assert len(wins) == 1
        w = wins[0]
        # λ(t_start) == q exactly (to machine precision) — the endpoint is a
        # solved root of a LINEAR equation in the exponent, never a grid scan.
        assert I.lambda_at(segs, w.t_start) == pytest.approx(q, rel=1e-12)
        assert I.lambda_at(segs, w.t_end - 1e-9) >= q * (1 - 1e-6)
        assert 100.0 < w.t_start < 150.0 < w.t_end < 200.0

    def test_peak_is_always_a_breakpoint(self):
        # §5.2: "Because ln λ is monotone on each segment, THE PEAK OF A WINDOW
        # IS ALWAYS A BREAKPOINT ... No interior optimizer is needed, and this
        # must not be 'improved' into one."
        segs = self._flat_hump()
        w = I.find_windows(segs, 5e-4)[0]
        breakpoints = {s.t_start for s in segs} | {s.t_end for s in segs} | {w.t_start, w.t_end}
        assert w.t_peak in breakpoints
        assert w.t_peak == pytest.approx(150.0)

    def test_expected_count_is_the_integral_over_the_window(self):
        segs = self._flat_hump()
        w = I.find_windows(segs, 5e-4)[0]
        assert w.expected_count == pytest.approx(I.integrate(segs, w.t_start, w.t_end), rel=1e-14)
        assert w.duration_days == pytest.approx(w.t_end - w.t_start)

    def test_threshold_above_the_field_yields_an_honest_empty(self):
        assert I.find_windows(self._flat_hump(), 1.0) == []

    def test_threshold_below_the_field_yields_one_window_spanning_everything(self):
        segs = self._flat_hump()
        wins = I.find_windows(segs, 1e-9)
        assert len(wins) == 1
        assert wins[0].t_start == pytest.approx(0.0)
        assert wins[0].t_end == pytest.approx(300.0)

    def test_two_separated_humps_yield_two_windows(self):
        lo, hi = math.log(1e-4), math.log(1e-3)
        segs = [
            _seg(0, 0.0, 10.0, hi, 0.0),
            _seg(1, 10.0, 20.0, lo, 0.0),
            _seg(2, 20.0, 30.0, hi, 0.0),
        ]
        wins = I.find_windows(segs, 5e-4)
        assert len(wins) == 2
        assert wins[0].t_end == pytest.approx(10.0)
        assert wins[1].t_start == pytest.approx(20.0)

    def test_adjacent_above_threshold_segments_merge_into_one_maximal_window(self):
        # "MAXIMAL interval" is the definition — three consecutive above-q
        # segments are ONE window, not three.
        hi = math.log(1e-3)
        segs = [_seg(i, 10.0 * i, 10.0 * (i + 1), hi, 0.0) for i in range(3)]
        wins = I.find_windows(segs, 5e-4)
        assert len(wins) == 1
        assert (wins[0].t_start, wins[0].t_end) == pytest.approx((0.0, 30.0))

    def test_windows_are_deterministic_across_repeated_calls(self):
        segs = self._flat_hump()
        a = I.find_windows(segs, 5e-4)
        b = I.find_windows(segs, 5e-4)
        assert [(w.t_start, w.t_end, w.t_peak, w.expected_count) for w in a] == \
               [(w.t_start, w.t_end, w.t_peak, w.expected_count) for w in b]


class TestLambdaAt:
    def test_lambda_at_uses_the_containing_segment(self):
        segs = [_seg(0, 0.0, 10.0, math.log(1e-4), 0.0),
                _seg(1, 10.0, 20.0, math.log(5e-4), 0.0)]
        assert I.lambda_at(segs, 5.0) == pytest.approx(1e-4)
        assert I.lambda_at(segs, 15.0) == pytest.approx(5e-4)

    def test_lambda_at_a_shared_breakpoint_takes_the_right_hand_limit(self):
        # alpha_i is DEFINED as ln λ(t_i⁺) (§5.2), so at a boundary the later
        # segment wins. A step function's two coincident knots make the step
        # explicit, and this rule is what makes it readable.
        segs = [_seg(0, 0.0, 10.0, math.log(1e-4), 0.0),
                _seg(1, 10.0, 20.0, math.log(5e-4), 0.0)]
        assert I.lambda_at(segs, 10.0) == pytest.approx(5e-4)

    def test_lambda_outside_the_field_is_zero_not_extrapolated(self):
        segs = [_seg(0, 0.0, 10.0, math.log(1e-4), 0.5)]
        assert I.lambda_at(segs, -1.0) == 0.0
        assert I.lambda_at(segs, 11.0) == 0.0


class TestWindowId:
    def test_window_id_is_stable_and_prefixed(self):
        a = I.window_id('482012f1-710e-4a25-994a-93821f5871aa', 'career_change',
                        1000.0, 1100.0, 'v0_classical', 'x12_v0')
        b = I.window_id('482012f1-710e-4a25-994a-93821f5871aa', 'career_change',
                        1000.0, 1100.0, 'v0_classical', 'x12_v0')
        assert a == b
        assert a.startswith('kfw_')
        assert len(a) == 4 + 24

    def test_window_id_changes_with_every_input(self):
        base = dict(chart_id='c', event_class='e', t_start=1.0, t_end=2.0,
                    weights_version='v0', x_schema_version='x12_v0')
        ref = I.window_id(**base)
        for k, v in [('chart_id', 'd'), ('event_class', 'f'), ('t_start', 1.5),
                     ('t_end', 2.5), ('weights_version', 'v1'),
                     ('x_schema_version', 'x13_v0')]:
            assert I.window_id(**{**base, k: v}) != ref

    def test_window_id_rounds_times_to_six_decimals(self):
        # §5.2 rounds t to 6 dp inside the hash so a float-representation wobble
        # far below day-grade precision cannot mint a new authority id for the
        # same window.
        a = I.window_id('c', 'e', 1.0000000001, 2.0, 'v0', 'x12_v0')
        b = I.window_id('c', 'e', 1.0, 2.0, 'v0', 'x12_v0')
        assert a == b
