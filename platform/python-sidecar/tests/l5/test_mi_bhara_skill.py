"""
test_mi_bhara_skill — ṢAḌ-DARŚANA W2 Lane E · the TEMPORAL SKILL SCORE, verified against a
CONSTRUCTED SYNTHETIC EXAMPLE whose true answer is known in closed form.

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.3.

── THE CONSTRUCTED EXAMPLE (§1 below) ─────────────────────────────────────────────────────
Take the model and the null both HOMOGENEOUS, `λ_model ≡ A` and `λ_null ≡ B`, over `[0, T]`,
with `n` events at arbitrary times. Then

    ℓ_model = n·ln A − A·T
    ℓ_null  = n·ln B − B·T
    SS      = (1/n)(ℓ_model − ℓ_null) = ln(A/B) − (A − B)·T / n

With `A = 2/365`, `B = 1/365`, `T = 3650`, `n = 20`:

    SS = ln 2 − (1/365)·3650 / 20 = 0.6931471805599453 − 0.5 = 0.1931471805599453

That number is arrived at with a pencil, not with this code. The test drives it through the
FULL production stack — `field.constant_field` → `likelihood.poisson_loglik` →
`skill.compute_skill` — so it verifies the composition, not an isolated formula.

Two sanity properties of the constructed case, both asserted:
  • A model that IS the null scores exactly 0 — which is the null hypothesis "this field
    carries no temporal information", so the estimator is correctly centred.
  • A model twice as concentrated where the events actually are scores POSITIVE; a model
    that is systematically wrong scores NEGATIVE. The score has a real failure direction.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.mi_bhara.field import constant_field, integrate, log_lambda  # noqa: E402
from services.mi_bhara.skill import (  # noqa: E402
    MIN_EVENTS_FOR_POWER,
    SKILL_ESTABLISHED,
    SKILL_NOT_ESTABLISHED,
    SKILL_UNDERPOWERED,
    aggregate_chart_skill,
    bootstrap_seed,
    compute_skill,
    has_regressed,
    skill_state_for,
)

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
WV = "v0_classical"

T_HORIZON = 3650.0
N_EVENTS = 20
EVENT_TIMES = [T_HORIZON * (k + 0.5) / N_EVENTS for k in range(N_EVENTS)]


def _score_through_the_real_stack(rate_model: float, rate_null: float, replicates: int = 4):
    """Drive the production path end-to-end for two homogeneous fields."""
    model = constant_field(rate_model, 0.0, T_HORIZON)
    null = constant_field(rate_null, 0.0, T_HORIZON)
    model_log_intensity = [log_lambda(model, t) for t in EVENT_TIMES]
    null_vec = [log_lambda(null, t) for t in EVENT_TIMES]
    return compute_skill(
        chart_id=CHART,
        weights_version=WV,
        event_class="career_change",
        model_log_intensity=model_log_intensity,
        # every replicate identical here — the constructed case has a single known null
        null_log_intensity_per_replicate=[null_vec] * replicates,
        model_integral=integrate(model, 0.0, T_HORIZON),
        null_integrals=[integrate(null, 0.0, T_HORIZON)] * replicates,
    )


# ── §1 — THE GROUND-TRUTH VERIFICATION ─────────────────────────────────────────────────

def test_skill_score_matches_the_hand_computed_closed_form():
    """SS = ln(A/B) − (A − B)·T/n, computed on paper as 0.1931471805599453."""
    A, B = 2.0 / 365.0, 1.0 / 365.0
    hand_computed = math.log(2.0) - (A - B) * T_HORIZON / N_EVENTS
    assert hand_computed == pytest.approx(0.1931471805599453, abs=1e-15)

    result = _score_through_the_real_stack(A, B)
    assert result.skill_score == pytest.approx(hand_computed, rel=1e-12)
    assert result.n_events == N_EVENTS


def test_a_model_identical_to_the_null_scores_exactly_zero():
    """SS = 0 IS the null hypothesis (§7.3). The estimator must be centred there."""
    rate = 1.7 / 365.0
    result = _score_through_the_real_stack(rate, rate)
    assert result.skill_score == pytest.approx(0.0, abs=1e-14)
    assert result.skill_lo == pytest.approx(0.0, abs=1e-14)
    assert result.skill_hi == pytest.approx(0.0, abs=1e-14)
    # zero advantage with n ≥ 8 must read `not_established`, never `established`
    assert result.skill_state == SKILL_NOT_ESTABLISHED


def test_a_systematically_worse_model_scores_negative():
    """The failure direction is real: a model half as likely as the null loses nats."""
    A, B = 0.5 / 365.0, 1.0 / 365.0
    hand_computed = math.log(0.5) - (A - B) * T_HORIZON / N_EVENTS
    result = _score_through_the_real_stack(A, B)
    assert result.skill_score < 0.0
    assert result.skill_score == pytest.approx(hand_computed, rel=1e-12)


def test_an_inhomogeneous_model_that_concentrates_hazard_on_the_events_beats_the_flat_null():
    """The case the instrument actually claims: same total expected count, different timing.

    Model: λ = 2·c on the first half of the horizon, 0 elsewhere is not expressible (λ > 0 by
    construction), so use 1.8c / 0.2c — mean rate exactly c, matching the null's total mass.
    All 20 events fall in the first half. The model must win, and its total integral must
    equal the null's, so the advantage is PURELY timing.
    """
    from services.mi_bhara.field import FieldSegment

    c = 1.0 / 365.0
    half = T_HORIZON / 2.0
    model = [
        FieldSegment(0.0, half, math.log(1.8 * c), 0.0),
        FieldSegment(half, T_HORIZON, math.log(0.2 * c), 0.0),
    ]
    null = constant_field(c, 0.0, T_HORIZON)
    assert integrate(model, 0.0, T_HORIZON) == pytest.approx(
        integrate(null, 0.0, T_HORIZON), rel=1e-12
    )

    early_events = [half * (k + 0.5) / N_EVENTS for k in range(N_EVENTS)]
    result = compute_skill(
        chart_id=CHART,
        weights_version=WV,
        event_class="career_change",
        model_log_intensity=[log_lambda(model, t) for t in early_events],
        null_log_intensity_per_replicate=[[log_lambda(null, t) for t in early_events]] * 3,
        model_integral=integrate(model, 0.0, T_HORIZON),
        null_integrals=[integrate(null, 0.0, T_HORIZON)] * 3,
    )
    # with equal integrals the score collapses to the mean per-event log ratio = ln 1.8
    assert result.skill_score == pytest.approx(math.log(1.8), rel=1e-12)
    assert result.skill_state == SKILL_ESTABLISHED


# ── §2 — the bootstrap interval ────────────────────────────────────────────────────────

def test_bootstrap_interval_collapses_when_every_event_advantage_is_identical():
    """With all d_k equal there is no resampling variability, so lo == hi == the point.
    A non-degenerate interval here would mean the bootstrap is resampling the wrong thing."""
    result = _score_through_the_real_stack(2.0 / 365.0, 1.0 / 365.0)
    assert result.skill_lo == pytest.approx(result.skill_score, abs=1e-12)
    assert result.skill_hi == pytest.approx(result.skill_score, abs=1e-12)


def test_bootstrap_is_deterministic_across_runs_and_seeded_per_the_spec():
    """§7.3: seed = int(sha256(f'{chart_id}|{weights_version}|{e}')[:8], 16). A rerun must
    reproduce the interval exactly, or the published number is not reproducible."""
    import hashlib

    expected = int(
        hashlib.sha256(f"{CHART}|{WV}|career_change".encode()).hexdigest()[:8], 16
    )
    assert bootstrap_seed(CHART, WV, "career_change") == expected

    a = _score_through_the_real_stack(2.0 / 365.0, 1.0 / 365.0)
    b = _score_through_the_real_stack(2.0 / 365.0, 1.0 / 365.0)
    assert (a.skill_lo, a.skill_hi, a.bootstrap_seed) == (b.skill_lo, b.skill_hi, b.bootstrap_seed)


def test_bootstrap_interval_widens_with_heterogeneous_advantages_and_brackets_the_point():
    from services.mi_bhara.field import FieldSegment

    c = 1.0 / 365.0
    model = [
        FieldSegment(0.0, 1825.0, math.log(3.0 * c), 0.0),
        FieldSegment(1825.0, T_HORIZON, math.log(0.4 * c), 0.0),
    ]
    null = constant_field(c, 0.0, T_HORIZON)
    times = [200.0, 500.0, 900.0, 1400.0, 1700.0, 2200.0, 2900.0, 3400.0, 3600.0]
    result = compute_skill(
        chart_id=CHART,
        weights_version=WV,
        event_class="career_change",
        model_log_intensity=[log_lambda(model, t) for t in times],
        null_log_intensity_per_replicate=[[log_lambda(null, t) for t in times]] * 2,
        model_integral=integrate(model, 0.0, T_HORIZON),
        null_integrals=[integrate(null, 0.0, T_HORIZON)] * 2,
    )
    assert result.skill_lo < result.skill_score < result.skill_hi
    assert result.bootstrap_resamples == 2000


# ── §3 — the three honest states (§N.8: a PASS needs the power to fail) ────────────────

def test_three_state_predicate_is_exactly_the_spec():
    assert skill_state_for(7, 5.0) == SKILL_UNDERPOWERED, "n < 8 is never established"
    assert skill_state_for(8, 0.01) == SKILL_ESTABLISHED
    assert skill_state_for(8, 0.0) == SKILL_NOT_ESTABLISHED, "lo == 0 is not > 0"
    assert skill_state_for(8, -0.5) == SKILL_NOT_ESTABLISHED
    assert MIN_EVENTS_FOR_POWER == 8


def test_seven_events_are_underpowered_however_large_the_advantage():
    """A large, genuine advantage on 7 events is STILL `underpowered`. The state is about
    POWER, not about the point estimate — otherwise it would be a signal with no detector.

    Constructed with equal integrals (so the whole advantage is timing, as in §1's fourth
    case) to make the point estimate unambiguously large and positive: `ln 1.8` per event.
    """
    from services.mi_bhara.field import FieldSegment

    c = 1.0 / 365.0
    half = T_HORIZON / 2.0
    model = [
        FieldSegment(0.0, half, math.log(1.8 * c), 0.0),
        FieldSegment(half, T_HORIZON, math.log(0.2 * c), 0.0),
    ]
    null = constant_field(c, 0.0, T_HORIZON)
    times = [half * (k + 0.5) / 7 for k in range(7)]
    result = compute_skill(
        chart_id=CHART,
        weights_version=WV,
        event_class="career_change",
        model_log_intensity=[log_lambda(model, t) for t in times],
        null_log_intensity_per_replicate=[[log_lambda(null, t) for t in times]],
        model_integral=integrate(model, 0.0, T_HORIZON),
        null_integrals=[integrate(null, 0.0, T_HORIZON)],
    )
    assert result.n_events == 7
    assert result.skill_score == pytest.approx(math.log(1.8), rel=1e-12)
    assert result.skill_lo > 0.0, "the interval genuinely clears zero — and it STILL is not established"
    assert result.skill_state == SKILL_UNDERPOWERED


def test_the_integral_penalty_is_real_a_uniformly_hotter_model_is_punished():
    """A model that simply raises λ everywhere buys per-event log-intensity and pays for it
    in Λ. §1's closed form covers this, but the sign matters enough to name it: inflating the
    hazard is NOT a way to score well, which is what makes the score honest rather than
    game-able."""
    A, B = 50.0 / 365.0, 1.0 / 365.0
    result = _score_through_the_real_stack(A, B)
    hand_computed = math.log(A / B) - (A - B) * T_HORIZON / N_EVENTS
    assert result.skill_score == pytest.approx(hand_computed, rel=1e-12)
    assert result.skill_score < 0.0, "50x the hazard for the same 20 events must LOSE"


def test_zero_events_is_an_honest_underpowered_zero_not_an_error():
    """The LEL-absent chart. This is a real answer — 'we cannot measure skill here' — and it
    is published, not suppressed (§7.6's LEL-absent scenario)."""
    result = compute_skill(
        chart_id=CHART,
        weights_version=WV,
        event_class="career_change",
        model_log_intensity=[],
        null_log_intensity_per_replicate=[],
        model_integral=0.0,
        null_integrals=[],
    )
    assert result.n_events == 0
    assert result.skill_score == 0.0
    assert result.skill_state == SKILL_UNDERPOWERED
    assert result.bootstrap_resamples == 0


def test_replicate_shape_mismatch_is_rejected():
    """§5.5 shifts the SKY, not the events — every replicate must score the same event set."""
    with pytest.raises(ValueError):
        compute_skill(
            chart_id=CHART,
            weights_version=WV,
            event_class="e",
            model_log_intensity=[-6.0, -6.1, -6.2],
            null_log_intensity_per_replicate=[[-6.0, -6.1]],
            model_integral=1.0,
            null_integrals=[1.0],
        )
    with pytest.raises(ValueError):
        compute_skill(
            chart_id=CHART,
            weights_version=WV,
            event_class="e",
            model_log_intensity=[-6.0],
            null_log_intensity_per_replicate=[[-6.0], [-6.0]],
            model_integral=1.0,
            null_integrals=[1.0],
        )


# ── §4 — the chart-level aggregate and the regression gate ─────────────────────────────

def test_chart_level_aggregate_is_event_weighted():
    """SS = Σ_e n_e·SS_e / Σ_e n_e (§7.3) — a class with more events pulls harder."""
    a = _score_through_the_real_stack(2.0 / 365.0, 1.0 / 365.0)  # n = 20
    b = compute_skill(
        chart_id=CHART,
        weights_version=WV,
        event_class="health_crisis",
        model_log_intensity=[math.log(1e-3)] * 8,
        null_log_intensity_per_replicate=[[math.log(1e-3)] * 8],
        model_integral=1.0,
        null_integrals=[1.0],
    )
    agg = aggregate_chart_skill([a, b], chart_id=CHART, weights_version=WV)
    expected = (a.n_events * a.skill_score + b.n_events * b.skill_score) / (
        a.n_events + b.n_events
    )
    assert agg.n_events == 28
    assert agg.event_class is None
    assert agg.skill_score == pytest.approx(expected, rel=1e-12)


def test_chart_level_aggregate_over_no_scored_classes_is_an_honest_underpowered_zero():
    agg = aggregate_chart_skill([], chart_id=CHART, weights_version=WV)
    assert agg.n_events == 0
    assert agg.skill_state == SKILL_UNDERPOWERED


def test_regression_gate_uses_the_005_nat_tolerance_and_no_baseline_cannot_regress():
    assert has_regressed(0.10, None) is False, "the first published score BECOMES the baseline"
    assert has_regressed(0.10, 0.10) is False
    assert has_regressed(0.06, 0.10) is False, "0.04 below is inside the churn tolerance"
    assert has_regressed(0.049, 0.10) is True
    assert has_regressed(-0.20, 0.10) is True
