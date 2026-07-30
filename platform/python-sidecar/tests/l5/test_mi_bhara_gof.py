"""
test_mi_bhara_gof — ṢAḌ-DARŚANA W2 Lane E · the TIME-RESCALING goodness-of-fit test, verified
against CONSTRUCTED examples whose true answers are known by pencil.

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.3.

── THE THREE GROUND TRUTHS THIS FILE ESTABLISHES ──────────────────────────────────────────

1. **Time rescaling itself.** For `λ ≡ c`, `τ_k = c·(t_k − t_{k−1})`. Choose the gaps so that
   `τ_k = −ln(1 − z_k)` for a target `{z_k}` and the rescaled values come back EXACTLY equal
   to that target. This verifies `Λ`, the `t_0 = observation_start` convention, and the
   `z = 1 − e^{−τ}` transform in one shot, against arithmetic done independently.

2. **The KS statistic.** For the maximally-uniform sample `z_k = (k − ½)/n`, the empirical CDF
   sits at `k/n` on `[z_k, z_{k+1})`, so
       `D_n = sup_z |F_n(z) − z| = max_k max(|k/n − z_k|, |(k−1)/n − z_k|) = 1/(2n)`
   — exactly. With `n = 20` that is `0.025`. Derived on paper; `scipy.stats.kstest` must agree.

3. **The Ljung–Box statistic.** Hand-computed in full for the alternating series
   `z = [0,1,0,1,0,1,0,1]` (`n = 8`):
       `z̄ = ½`, `r = ±½`, `Σr² = 2`
       `ρ̂_1 = 7·(−¼)/2 = −0.875`   `ρ̂_2 = 6·(¼)/2 = 0.75`   `ρ̂_3 = −0.625`
       `ρ̂_4 = 0.5`                 `ρ̂_5 = −0.375`
       `Q_5 = 8·10·[0.765625/7 + 0.5625/6 + 0.390625/5 + 0.25/4 + 0.140625/3]`
            `= 80 · 0.390625 = 31.25`   EXACTLY.
   This is why Ljung–Box is implemented rather than imported: the check is against pencil
   arithmetic, not against a second library that could share a wrong convention.

── AND THE FAILURE DIRECTIONS ─────────────────────────────────────────────────────────────
A test that can only pass is not a test (§N.8). §4 exercises both real failure modes: a
clustered event set that KS rejects, and a uniform-but-autocorrelated set that KS ACCEPTS and
Ljung–Box rejects — which is precisely why the design requires both statistics.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.mi_bhara.field import constant_field, integrate  # noqa: E402
from services.mi_bhara.gof import (  # noqa: E402
    GOF_FAIL,
    GOF_PASS,
    GOF_UNDERPOWERED,
    MIN_EVENTS_FOR_POWER,
    compute_gof,
    gof_state_for,
    kolmogorov_smirnov,
    ljung_box,
    rescale_times,
)

RATE = 1.0 / 365.0


def _times_producing(zs, rate: float = RATE, start: float = 0.0) -> list[float]:
    """Event times whose rescaled values under `λ ≡ rate` are exactly `zs`.

    τ_k = −ln(1 − z_k), and for a flat field τ_k = rate·gap_k ⇒ gap_k = τ_k / rate.
    """
    t = start
    out = []
    for z in zs:
        t += (-math.log(1.0 - z)) / rate
        out.append(t)
    return out


def _flat_integrator(rate: float = RATE, horizon: float = 5.0e5):
    segs = constant_field(rate, 0.0, horizon)
    return lambda a, b: integrate(segs, a, b)


# ── §1 — time rescaling reproduces a constructed target exactly ────────────────────────

def test_rescaling_recovers_the_constructed_z_values_exactly():
    target = [0.05, 0.31, 0.62, 0.77, 0.91]
    times = _times_producing(target)
    taus, zs = rescale_times(_flat_integrator(), times, observation_start=0.0)
    assert list(zs) == pytest.approx(target, rel=1e-12)
    assert list(taus) == pytest.approx([-math.log(1.0 - z) for z in target], rel=1e-12)


def test_t_zero_is_the_observation_start_not_the_first_event():
    """§7.3: `τ_k = Λ(t_{k−1}, t_k)` with `t_0 = 0`. The FIRST inter-event interval is
    measured from the observation start, so an event long after the start carries a large τ.
    Getting this wrong silently drops one observation's worth of evidence."""
    times = _times_producing([0.5, 0.5])
    taus, _ = rescale_times(_flat_integrator(), times, observation_start=0.0)
    assert len(taus) == 2
    assert taus[0] == pytest.approx(-math.log(0.5), rel=1e-12)


def test_unsorted_event_times_raise_rather_than_being_silently_sorted():
    with pytest.raises(ValueError):
        rescale_times(_flat_integrator(), [100.0, 50.0], observation_start=0.0)


# ── §2 — the KS statistic against its closed form ──────────────────────────────────────

def test_ks_statistic_for_the_maximally_uniform_sample_is_exactly_one_over_2n():
    for n in (8, 20, 57):
        zs = [(k + 0.5) / n for k in range(n)]
        d, p = kolmogorov_smirnov(zs)
        assert d == pytest.approx(1.0 / (2 * n), rel=1e-12), f"n={n}"
        assert p > 0.99, "the most-uniform possible sample cannot be rejected"


def test_ks_statistic_for_a_fully_clustered_sample_approaches_one():
    zs = [1e-9 * (k + 1) for k in range(20)]
    d, p = kolmogorov_smirnov(zs)
    assert d == pytest.approx(1.0, abs=1e-6)
    assert p < 1e-12


# ── §3 — the Ljung–Box statistic against pencil arithmetic ─────────────────────────────

def test_ljung_box_matches_the_hand_computed_worked_example_exactly():
    """z = [0,1,0,1,0,1,0,1] ⇒ Q_5 = 31.25 exactly. Full derivation in the module docstring."""
    z = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    lb = ljung_box(z, max_lags=5)
    assert lb.lags == 5
    assert lb.statistic == pytest.approx(31.25, abs=1e-12)
    assert lb.p_value == pytest.approx(float(stats.chi2.sf(31.25, 5)), rel=1e-12)
    assert lb.p_value < 0.05, "a perfectly alternating series is not independent"


def test_ljung_box_autocorrelations_match_the_hand_computed_rhos():
    """Re-derive ρ̂_1..ρ̂_5 independently from the same series and confirm the Q they imply."""
    z = np.array([0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0])
    r = z - z.mean()
    denom = float(np.dot(r, r))
    rhos = [float(np.dot(r[k:], r[:-k])) / denom for k in range(1, 6)]
    assert rhos == pytest.approx([-0.875, 0.75, -0.625, 0.5, -0.375], abs=1e-12)
    n = 8
    q = n * (n + 2) * sum(rho * rho / (n - k) for k, rho in enumerate(rhos, start=1))
    assert q == pytest.approx(31.25, abs=1e-12)


def test_ljung_box_caps_lags_at_n_minus_one():
    """A lag-k autocorrelation needs n > k pairs; asking for 5 lags on 4 points must not
    invent them."""
    lb = ljung_box([0.1, 0.5, 0.9, 0.3], max_lags=5)
    assert lb.lags == 3


def test_a_degenerate_constant_series_reports_zero_lags_rather_than_a_nan_pass():
    """Zero variance ⇒ no defined autocorrelation. `lags = 0` says the test could not run;
    it must NOT be laundered into a p = 1.0 pass (§N.8)."""
    lb = ljung_box([0.4] * 12, max_lags=5)
    assert lb.lags == 0
    gof = compute_gof(
        event_class="e",
        integrate_fn=lambda a, b: -math.log(0.6),  # every τ identical ⇒ every z identical
        event_times=[float(i) for i in range(1, 13)],
        observation_start=0.0,
    )
    assert gof.ljung_box_lags == 0
    assert gof.ljung_box_p is None, "an un-run test contributes no p-value"
    assert gof.gof_state != GOF_PASS


# ── §4 — the three states, and BOTH real failure directions ────────────────────────────

def test_state_predicate_is_exactly_the_spec():
    assert MIN_EVENTS_FOR_POWER == 8
    assert gof_state_for(7, 0.9, 0.9) == (GOF_UNDERPOWERED, None), "n < 8 is never a pass"
    assert gof_state_for(8, 0.9, 0.9) == (GOF_PASS, None)
    assert gof_state_for(8, 0.01, 0.9) == (GOF_FAIL, "ks")
    assert gof_state_for(8, 0.9, 0.01) == (GOF_FAIL, "ljung_box")
    assert gof_state_for(8, 0.01, 0.01) == (GOF_FAIL, "ks+ljung_box")
    assert gof_state_for(20, None, 0.5) == (GOF_UNDERPOWERED, None), "uncomputed ≠ pass"


def test_a_correct_model_passes_on_a_deterministic_iid_uniform_sample():
    """The PASS direction, on a seeded i.i.d. U(0,1) draw — which is what {z_k} is when the
    intensity is right. Seed fixed so the assertion is deterministic, not a coin flip."""
    rng = np.random.default_rng(20260730)
    zs = [float(v) for v in rng.uniform(0.0, 1.0, size=200)]
    times = _times_producing(zs)
    gof = compute_gof(
        event_class="career_change",
        integrate_fn=_flat_integrator(),
        event_times=times,
        observation_start=0.0,
    )
    assert gof.n == 200
    assert gof.ks_p > 0.05 and gof.ljung_box_p > 0.05
    assert gof.gof_state == GOF_PASS
    assert gof.failing_statistic is None
    assert gof.ks_band_95 == pytest.approx(1.36 / math.sqrt(200), rel=1e-12)
    assert len(gof.rescaled_z) == 200


def test_failure_direction_one_a_clustered_event_set_is_rejected_by_ks():
    """The model says events are spread over a century; they all happen in one year. KS
    rejects. This is the marginal being wrong."""
    zs = [0.001 * (k + 1) for k in range(40)]
    times = _times_producing(zs)
    gof = compute_gof(
        event_class="career_change",
        integrate_fn=_flat_integrator(),
        event_times=times,
        observation_start=0.0,
    )
    assert gof.gof_state == GOF_FAIL
    assert gof.failing_statistic in ("ks", "ks+ljung_box")
    assert gof.ks_p < 0.05


def test_failure_direction_two_uniform_but_autocorrelated_passes_ks_and_fails_ljung_box():
    """THE REASON BOTH STATISTICS ARE REQUIRED (§7.3). `{z_k}` here is a perfect uniform grid
    — KS cannot reject it — but ordered so that consecutive values alternate low/high, i.e.
    the rescaled times are strongly dependent. That dependence means a missing
    clustering/refractory term in the intensity, and only Ljung–Box sees it.
    """
    n = 40
    grid = [(k + 0.5) / n for k in range(n)]
    lows, highs = grid[: n // 2], grid[n // 2 :]
    zs = [v for pair in zip(lows, highs) for v in pair]  # low, high, low, high, ...
    assert sorted(zs) == pytest.approx(grid, rel=1e-12), "same multiset — only the ORDER differs"

    times = _times_producing(zs)
    gof = compute_gof(
        event_class="career_change",
        integrate_fn=_flat_integrator(),
        event_times=times,
        observation_start=0.0,
    )
    assert gof.ks_p > 0.05, "KS is blind to ordering — it sees the maximally uniform sample"
    assert gof.ljung_box_p < 0.05
    assert gof.gof_state == GOF_FAIL
    assert gof.failing_statistic == "ljung_box"


def test_seven_events_are_underpowered_even_when_both_statistics_look_clean():
    zs = [(k + 0.5) / 7 for k in range(7)]
    gof = compute_gof(
        event_class="career_change",
        integrate_fn=_flat_integrator(),
        event_times=_times_producing(zs),
        observation_start=0.0,
    )
    assert gof.n == 7
    assert gof.ks_p > 0.5
    assert gof.gof_state == GOF_UNDERPOWERED
    assert gof.failing_statistic is None


def test_zero_events_is_an_honest_underpowered_row_not_a_missing_one():
    gof = compute_gof(
        event_class="career_change",
        integrate_fn=_flat_integrator(),
        event_times=[],
        observation_start=0.0,
    )
    assert gof.n == 0
    assert gof.gof_state == GOF_UNDERPOWERED
    assert gof.rescaled_z == ()
    assert gof.ks_p is None and gof.ljung_box_p is None
