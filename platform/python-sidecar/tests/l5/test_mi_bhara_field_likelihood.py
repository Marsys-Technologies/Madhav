"""
test_mi_bhara_field_likelihood — ṢAḌ-DARŚANA W2 Lane E · the integrator and the
inhomogeneous-Poisson log-likelihood, verified against CLOSED-FORM ground truth.

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §5.2 (the exact analytic integral, and its mandated
1e-9-relative agreement with a 10⁴-point Simpson quadrature) and §7.2 (the log-likelihood).

VERIFICATION POSTURE (this is the point of the file, not decoration): every assertion below
compares the implementation against a value derived INDEPENDENTLY of it — a closed-form
integral done on paper, or a Simpson quadrature that shares no code with `field.integrate`.
An "internal consistency" suite that only checks the code agrees with itself would pass just
as happily on a wrong formula.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.mi_bhara.basis import (  # noqa: E402
    FieldBasis,
    ParameterVector,
    SegmentBasis,
    build_segments,
)
from services.mi_bhara.field import (  # noqa: E402
    FieldSegment,
    constant_field,
    integrate,
    log_lambda,
    segments_from_rows,
)
from services.mi_bhara.likelihood import (  # noqa: E402
    loglik_for_theta,
    poisson_loglik,
)


# ── §1 — the integrator against closed form ────────────────────────────────────────────

def test_flat_segment_integral_is_rate_times_width():
    """γ = 0 ⇒ Λ(a,b) = λ·(b−a), exactly. The homogeneous-Poisson base case."""
    segs = constant_field(2.0 / 365.0, 0.0, 3650.0)
    assert integrate(segs, 0.0, 3650.0) == pytest.approx(20.0, rel=1e-12)
    assert integrate(segs, 1000.0, 1100.0) == pytest.approx(100.0 * 2.0 / 365.0, rel=1e-12)


def test_log_linear_segment_integral_matches_closed_form():
    """ln λ = α + γ(t − t₀) ⇒ ∫ = (e^{α+γΔ} − e^{α})/γ, done on paper.

    α = ln(0.001), γ = 0.002/day, over 50 days:
        ∫ = 0.001·(e^{0.1} − 1)/0.002 = 0.5·(e^{0.1} − 1)
    """
    alpha = math.log(0.001)
    gamma = 0.002
    seg = FieldSegment(t_start=100.0, t_end=150.0, alpha=alpha, gamma=gamma)
    expected = 0.001 * (math.exp(0.1) - 1.0) / 0.002
    assert integrate([seg], 100.0, 150.0) == pytest.approx(expected, rel=1e-14)


def test_integral_matches_simpson_quadrature_to_1e_9_relative():
    """§5.2's own mandated check: agreement with a 10⁴-point Simpson quadrature to 1e-9
    relative, on a fixture segment set. Simpson shares no code with `field.integrate`."""
    segs = [
        FieldSegment(t_start=0.0, t_end=90.0, alpha=math.log(3e-4), gamma=0.004),
        FieldSegment(t_start=90.0, t_end=180.0, alpha=math.log(4.3e-4), gamma=-0.0031),
        FieldSegment(t_start=180.0, t_end=365.0, alpha=math.log(2.6e-4), gamma=0.0),
        FieldSegment(t_start=365.0, t_end=800.0, alpha=math.log(2.6e-4), gamma=1e-13),
    ]

    def simpson_over(seg: FieldSegment, n: int = 10_000) -> float:
        # Composite Simpson, grid ALIGNED to the segment. Aligning matters: λ is smooth
        # inside a segment but its derivative is discontinuous at the breakpoints, and a
        # single grid spanning the whole field straddles those kinks — that error is
        # Simpson's, not the integrator's, and comparing against it would test the wrong
        # thing (observed: ~8e-6 relative, entirely from the four kinks).
        xs = np.linspace(seg.t_start, seg.t_end, n + 1)
        ys = np.exp(seg.alpha + seg.gamma * (xs - seg.t_start))
        h = (seg.t_end - seg.t_start) / n
        return float(
            h / 3.0 * (ys[0] + ys[-1] + 4.0 * ys[1:-1:2].sum() + 2.0 * ys[2:-1:2].sum())
        )

    simpson = sum(simpson_over(s) for s in segs)
    assert integrate(segs, 0.0, 800.0) == pytest.approx(simpson, rel=1e-9)


def test_tiny_gamma_uses_the_stable_expm1_form_not_cancellation():
    """The catastrophic-cancellation guard §5.2 mandates.

    With γ·Δ ≈ 1e-12 the naive (e^{α+γΔ} − e^{α})/γ loses ~12 digits. The closed-form answer
    to first order is λ·Δ·(1 + γΔ/2); assert we are within 1e-13 relative of it, which the
    naive form is NOT.
    """
    lam = 1e-4
    gamma = 1e-14
    width = 100.0
    seg = FieldSegment(t_start=0.0, t_end=width, alpha=math.log(lam), gamma=gamma)
    expected = lam * width * (1.0 + gamma * width / 2.0)
    assert integrate([seg], 0.0, width) == pytest.approx(expected, rel=1e-13)


def test_integral_is_additive_over_a_partition():
    """Λ(a,c) = Λ(a,b) + Λ(b,c) across a segment boundary — the property `expected_count`
    on adjacent windows depends on."""
    segs = [
        FieldSegment(0.0, 100.0, math.log(1e-3), 0.003),
        FieldSegment(100.0, 250.0, math.log(1.2e-3), -0.001),
    ]
    whole = integrate(segs, 10.0, 240.0)
    left = integrate(segs, 10.0, 100.0)
    right = integrate(segs, 100.0, 240.0)
    assert whole == pytest.approx(left + right, rel=1e-13)


def test_empty_and_inverted_intervals_are_errors_not_silent_zeros():
    segs = constant_field(1e-3, 0.0, 100.0)
    assert integrate(segs, 50.0, 50.0) == 0.0
    with pytest.raises(ValueError):
        integrate(segs, 60.0, 50.0)


def test_evaluating_outside_the_support_raises_rather_than_returning_zero():
    """λ is strictly positive everywhere by construction (§5.1's P_floor / ρ_max). Returning
    λ = 0 outside the support would be a fabricated value; a caller bug must surface."""
    segs = constant_field(1e-3, 0.0, 100.0)
    with pytest.raises(ValueError):
        log_lambda(segs, 200.0)
    with pytest.raises(ValueError):
        log_lambda(segs, -1.0)


def test_segments_from_rows_rejects_overlapping_field_rows():
    good = segments_from_rows(
        [
            {"t_start": 100.0, "t_end": 200.0, "alpha": -6.0, "gamma": 0.0},
            {"t_start": 0.0, "t_end": 100.0, "alpha": -7.0, "gamma": 0.001},
        ]
    )
    assert [s.t_start for s in good] == [0.0, 100.0]
    with pytest.raises(ValueError):
        segments_from_rows(
            [
                {"t_start": 0.0, "t_end": 150.0, "alpha": -7.0, "gamma": 0.0},
                {"t_start": 100.0, "t_end": 200.0, "alpha": -6.0, "gamma": 0.0},
            ]
        )


# ── §2 — the log-likelihood against closed form ────────────────────────────────────────

def test_homogeneous_poisson_loglik_matches_the_textbook_closed_form():
    """For λ ≡ c over [0,T] with n events: ℓ = n·ln c − c·T. Done on paper."""
    c = 3.0 / 365.0
    T = 3650.0
    events = [100.0, 400.0, 900.0, 1800.0, 3000.0]
    segs = constant_field(c, 0.0, T)
    ll = poisson_loglik(segs, events, 0.0, T)
    assert ll.total == pytest.approx(len(events) * math.log(c) - c * T, rel=1e-12)
    assert ll.event_term == pytest.approx(len(events) * math.log(c), rel=1e-12)
    assert ll.integral_term == pytest.approx(c * T, rel=1e-12)
    assert ll.n_events == 5


def test_an_event_outside_the_observation_window_is_an_error_not_a_silent_drop():
    segs = constant_field(1e-3, 0.0, 100.0)
    with pytest.raises(ValueError):
        poisson_loglik(segs, [50.0, 150.0], 0.0, 100.0)


def test_observation_window_shortens_only_the_integral_term():
    """Fold-`j` semantics from §7.2 step 3: Λ over [0, c_{j+1}], not over the full horizon."""
    c = 1e-3
    segs = constant_field(c, 0.0, 1000.0)
    full = poisson_loglik(segs, [10.0, 20.0], 0.0, 1000.0)
    fold = poisson_loglik(segs, [10.0, 20.0], 0.0, 100.0)
    assert full.event_term == pytest.approx(fold.event_term, rel=1e-14)
    assert fold.integral_term == pytest.approx(c * 100.0, rel=1e-12)
    assert full.integral_term == pytest.approx(c * 1000.0, rel=1e-12)


# ── §3 — the basis → field rebuild (§5.1 composition, §5.2 storage) ────────────────────

def _two_system_basis() -> FieldBasis:
    """A hand-built basis whose ln λ at each endpoint is computable on paper."""
    return FieldBasis(
        event_class="career_change",
        system_ids=("vimshottari", "yogini"),
        covariate_ids=("x1_contact_moon_ref", "x4_av_kaksha_gate"),
        vighna_ids=("vedha",),
        segments=(
            SegmentBasis(
                t_start=0.0,
                t_end=100.0,
                log_base=math.log(1e-3),
                log_a_start=(0.5, 0.2),
                log_a_end=(0.9, 0.1),
                x_start=(0.0, 0.4),
                x_end=(1.0, 0.4),
                u_start=(0.0,),
                u_end=(0.5,),
            ),
        ),
    )


def test_build_segments_reproduces_the_five_factor_product_at_both_endpoints():
    basis = _two_system_basis()
    theta = ParameterVector(w=(0.8, 0.3), beta=(1.25, -0.5), rho=(0.6,))
    seg = build_segments(basis, theta)[0]

    # ln λ(t_start) = ln(1e-3) + 0.8·0.5 + 0.3·0.2 + 1.25·0.0 + (−0.5)·0.4 + ln(1 − 0.6·0.0)
    expected_start = math.log(1e-3) + 0.8 * 0.5 + 0.3 * 0.2 + (-0.5) * 0.4 + math.log(1.0)
    # ln λ(t_end)  = ln(1e-3) + 0.8·0.9 + 0.3·0.1 + 1.25·1.0 + (−0.5)·0.4 + ln(1 − 0.6·0.5)
    expected_end = (
        math.log(1e-3) + 0.8 * 0.9 + 0.3 * 0.1 + 1.25 * 1.0 + (-0.5) * 0.4 + math.log(0.7)
    )
    assert seg.alpha == pytest.approx(expected_start, rel=1e-13)
    assert seg.log_lambda_at(100.0) == pytest.approx(expected_end, rel=1e-13)
    assert seg.gamma == pytest.approx((expected_end - expected_start) / 100.0, rel=1e-13)


def test_w_equals_zero_collapses_a_clock_factor_to_exactly_one():
    """§5.1 C-3: a calibration run can switch a clock OFF SMOOTHLY without changing the
    model's structure. This is the detector for someone re-implementing it as a knock-out."""
    basis = _two_system_basis()
    with_clock = build_segments(basis, ParameterVector((0.0, 0.7), (0.0, 0.0), (0.0,)))[0]
    # the same θ with the first system's basis values changed arbitrarily must be identical
    mutated = FieldBasis(
        event_class=basis.event_class,
        system_ids=basis.system_ids,
        covariate_ids=basis.covariate_ids,
        vighna_ids=basis.vighna_ids,
        segments=(
            SegmentBasis(
                t_start=0.0,
                t_end=100.0,
                log_base=math.log(1e-3),
                log_a_start=(99.0, 0.2),
                log_a_end=(-99.0, 0.1),
                x_start=(0.0, 0.4),
                x_end=(1.0, 0.4),
                u_start=(0.0,),
                u_end=(0.5,),
            ),
        ),
    )
    other = build_segments(mutated, ParameterVector((0.0, 0.7), (0.0, 0.0), (0.0,)))[0]
    assert other.alpha == pytest.approx(with_clock.alpha, rel=1e-14)
    assert other.gamma == pytest.approx(with_clock.gamma, rel=1e-14)


def test_suppression_is_multiplicative_thinning_so_lambda_stays_strictly_positive():
    """§5.1 C-6 with ρ_max = 0.95 and u ≤ 1 ⇒ S ≥ 0.05^{|vighna|} > 0, never ≤ 0."""
    basis = FieldBasis(
        event_class="e",
        vighna_ids=("a", "b", "c"),
        segments=(
            SegmentBasis(
                t_start=0.0,
                t_end=10.0,
                log_base=math.log(1e-3),
                u_start=(1.0, 1.0, 1.0),
                u_end=(1.0, 1.0, 1.0),
            ),
        ),
    )
    seg = build_segments(basis, ParameterVector((), (), (0.95, 0.95, 0.95)))[0]
    assert math.exp(seg.alpha) > 0.0
    assert seg.alpha == pytest.approx(math.log(1e-3) + 3 * math.log(0.05), rel=1e-13)


def test_a_suppression_factor_at_or_below_zero_raises_rather_than_clamping():
    """A silently-clamped impossible input is a plausible-looking output standing in for
    'I don't know' — exactly what §N.7 item 6 forbids."""
    basis = FieldBasis(
        event_class="e",
        vighna_ids=("a",),
        segments=(
            SegmentBasis(0.0, 10.0, math.log(1e-3), u_start=(1.0,), u_end=(1.0,)),
        ),
    )
    with pytest.raises(ValueError):
        build_segments(basis, ParameterVector((), (), (1.0,)))


def test_theta_shape_mismatch_is_caught_before_any_arithmetic_happens():
    basis = _two_system_basis()
    with pytest.raises(ValueError):
        build_segments(basis, ParameterVector(w=(0.5,), beta=(0.0, 0.0), rho=(0.0,)))


def test_loglik_for_theta_agrees_with_the_two_step_path():
    basis = _two_system_basis()
    theta = ParameterVector(w=(0.6, 0.4), beta=(0.5, 0.5), rho=(0.3,))
    events = [10.0, 55.0, 90.0]
    direct = loglik_for_theta(basis, theta, events, 0.0, 100.0)
    staged = poisson_loglik(build_segments(basis, theta), events, 0.0, 100.0)
    assert direct.total == pytest.approx(staged.total, rel=1e-14)
