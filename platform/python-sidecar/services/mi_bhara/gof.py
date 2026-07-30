"""
gof.py — THE TIME-RESCALING GOODNESS-OF-FIT TEST (§7.3).

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.3.

── THE THEOREM, AND WHY IT IS THE RIGHT TEST ──────────────────────────────────────────────
By the time-rescaling theorem, if `t_1 < … < t_n` is a realization of a point process with
intensity `λ`, then

    τ_k = Λ(t_{k−1}, t_k)     (with t_0 = the observation start)   are i.i.d. Exponential(1)
    z_k = 1 − exp(−τ_k)                                            are i.i.d. Uniform(0,1)

That converts "is this inhomogeneous intensity right?" — which has no direct test — into "are
these n numbers i.i.d. U(0,1)?", which has two standard ones. It is a genuinely falsifiable
check on the model as a whole: get the shape of `λ` wrong anywhere and the `z_k` bunch.

── TWO TESTS, BOTH REQUIRED ───────────────────────────────────────────────────────────────
1. **Kolmogorov–Smirnov**, one-sample, `{z_k}` vs `U(0,1)`. `D_n = sup_z |F_n(z) − z|`, exact
   p-value via `scipy.stats.kstest`. Catches the marginal being wrong (too many events where
   the model says few, or vice versa).
2. **Ljung–Box** on `{z_k}` at lags 1..5. Catches DEPENDENCE in the rescaled times — a missing
   clustering or refractory term — which KS is blind to: a perfectly uniform but strongly
   autocorrelated `{z_k}` passes KS and is still a wrong model.

    gof_state = 'pass'         iff  KS p ≥ 0.05  AND  Ljung–Box p ≥ 0.05  AND  n ≥ 8
              = 'fail'         iff  n ≥ 8  AND  (either p < 0.05)   → `failing_statistic` named
              = 'underpowered' iff  n < 8

`n < 8` is **never** reported as a pass (CLAUDE.md §N.8: a PASS needs a detector with the power
to fail; with 5 points a KS test has essentially none).

── WHY LJUNG–BOX IS IMPLEMENTED HERE RATHER THAN IMPORTED ─────────────────────────────────
The design names `statsmodels.stats.diagnostic.acorr_ljungbox`. `statsmodels` is NOT in
`platform/python-sidecar/requirements.txt`, and pulling a large new runtime dependency into
the sidecar for one closed-form statistic is a worse trade than writing the statistic. The
formula is fully specified and hand-verifiable:

    ρ̂_k = Σ_{t=k+1}^{n} r_t r_{t−k} / Σ_{t=1}^{n} r_t²        with r = z − z̄
    Q_h  = n(n+2) · Σ_{k=1}^{h} ρ̂_k² / (n − k)
    p    = P(χ²_h > Q_h)

This is exactly `acorr_ljungbox`'s statistic (the biased/`n`-denominator autocorrelation, which
is the standard convention for this test). `tests/l5/test_mi_bhara_gof.py` verifies it against
a hand-computed worked example — an alternating series whose `Q_5` is exactly 31.25 by pencil —
rather than against another implementation, so the check is independent of any library.

`scipy` IS a pinned dependency (`scipy>=1.13.0`), so `kstest` and `chi2` are used directly.

Pure functions. No DB, no clock, no RNG.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy import stats

#: §7.3. Below this the test has no power and is reported `underpowered`, never `pass`.
MIN_EVENTS_FOR_POWER = 8
GOF_ALPHA = 0.05
LJUNG_BOX_MAX_LAGS = 5

GOF_PASS = "pass"
GOF_FAIL = "fail"
GOF_UNDERPOWERED = "underpowered"


@dataclass(frozen=True)
class LjungBox:
    statistic: float
    p_value: float
    lags: int


@dataclass(frozen=True)
class GoodnessOfFit:
    event_class: str | None
    n: int
    rescaled_tau: tuple[float, ...]
    rescaled_z: tuple[float, ...]
    ks_statistic: float | None
    ks_p: float | None
    ljung_box_stat: float | None
    ljung_box_p: float | None
    ljung_box_lags: int
    gof_state: str
    failing_statistic: str | None
    #: ±1.36/√n — the 95% KS band, emitted as DATA for the plot (§7.3), never as prose
    ks_band_95: float | None


def rescale_times(
    integrate_fn,
    event_times: Sequence[float],
    observation_start: float,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """`τ_k = Λ(t_{k−1}, t_k)` and `z_k = 1 − exp(−τ_k)`, with `t_0 = observation_start`.

    `integrate_fn(a, b) -> float` is injected rather than imported so this stays a pure
    function of the field it is handed: the caller passes a closure over `field.integrate` and
    the SAME segments the likelihood used. Passing a different integral here would silently
    test a different model than the one that was fitted.

    Event times must be strictly ascending — the theorem is about successive inter-event
    intervals, so an unsorted or duplicated input is a caller bug, not something to sort away.
    """
    taus: list[float] = []
    prev = observation_start
    for t in event_times:
        if t < prev:
            raise ValueError(
                f"event times must be ascending and start at/after the observation start; "
                f"got t={t} after {prev}"
            )
        taus.append(integrate_fn(prev, t))
        prev = t
    zs = [1.0 - math.exp(-tau) for tau in taus]
    return tuple(taus), tuple(zs)


def ljung_box(z: Sequence[float], max_lags: int = LJUNG_BOX_MAX_LAGS) -> LjungBox:
    """Ljung–Box Q on `{z_k}`, lags 1..h. See the module docstring for the exact formula.

    `h` is capped at `n − 1` (a lag-`k` autocorrelation needs `n > k` pairs).

    DEGENERACY, and why the test is a RELATIVE spread rather than `denom == 0`: a constant
    series has no defined autocorrelation, and the honest report is "this test could not be
    run" (`lags = 0`), never a `p = 1.0` pass. But `sum((z − z̄)²)` for twelve copies of 0.4
    is not exactly zero in IEEE-754 — it is ~1e-33 of pure rounding noise, whose lag
    autocorrelations are ±1 and which produced a spurious `Q = 52.5, p = 4e-10` before this
    guard existed. So degeneracy is measured as "the values are identical to within double
    precision", scaled to the data, which is the property actually meant.
    """
    arr = np.asarray(z, dtype=float)
    n = arr.size
    h = min(max_lags, n - 1)
    if n < 2 or h < 1:
        return LjungBox(statistic=0.0, p_value=1.0, lags=0)

    spread = float(arr.max() - arr.min())
    scale = max(1.0, float(np.abs(arr).max()))
    if spread <= 1e-12 * scale:
        return LjungBox(statistic=0.0, p_value=1.0, lags=0)

    resid = arr - arr.mean()
    denom = float(np.dot(resid, resid))
    if denom <= 0.0:
        return LjungBox(statistic=0.0, p_value=1.0, lags=0)

    q = 0.0
    for k in range(1, h + 1):
        rho_k = float(np.dot(resid[k:], resid[:-k])) / denom
        q += (rho_k * rho_k) / (n - k)
    q *= n * (n + 2)
    p = float(stats.chi2.sf(q, h))
    return LjungBox(statistic=float(q), p_value=p, lags=h)


def kolmogorov_smirnov(z: Sequence[float]) -> tuple[float, float]:
    """One-sample KS of `{z_k}` against `U(0,1)`: `(D_n, exact p)`."""
    result = stats.kstest(np.asarray(z, dtype=float), "uniform")
    return float(result.statistic), float(result.pvalue)


def gof_state_for(
    n: int, ks_p: float | None, lb_p: float | None
) -> tuple[str, str | None]:
    """The §7.3 three-state predicate plus its `failing_statistic`, in one place.

    Returns `(state, failing_statistic)`. `failing_statistic` is non-`None` exactly when the
    state is `fail`, and names WHICH test failed — a `fail` that will not say what failed is
    not a finding, it is a mood.
    """
    if n < MIN_EVENTS_FOR_POWER:
        return GOF_UNDERPOWERED, None
    if ks_p is None or lb_p is None:
        # n ≥ 8 but a statistic could not be computed. Not a pass; not a fail on an
        # uncomputed statistic either — the honest answer is that the test lacked its input.
        return GOF_UNDERPOWERED, None
    ks_bad = ks_p < GOF_ALPHA
    lb_bad = lb_p < GOF_ALPHA
    if not ks_bad and not lb_bad:
        return GOF_PASS, None
    if ks_bad and lb_bad:
        return GOF_FAIL, "ks+ljung_box"
    return GOF_FAIL, ("ks" if ks_bad else "ljung_box")


def compute_gof(
    *,
    event_class: str | None,
    integrate_fn,
    event_times: Sequence[float],
    observation_start: float,
    max_lags: int = LJUNG_BOX_MAX_LAGS,
) -> GoodnessOfFit:
    """The whole §7.3 GOF for one event class (or the pooled chart-level set).

    An empty or tiny event set is a legal input and returns `underpowered` with whatever
    statistics could be computed — the number is published in every state, exactly as the
    skill score is.
    """
    taus, zs = rescale_times(integrate_fn, event_times, observation_start)
    n = len(zs)

    if n == 0:
        return GoodnessOfFit(
            event_class=event_class,
            n=0,
            rescaled_tau=(),
            rescaled_z=(),
            ks_statistic=None,
            ks_p=None,
            ljung_box_stat=None,
            ljung_box_p=None,
            ljung_box_lags=0,
            gof_state=GOF_UNDERPOWERED,
            failing_statistic=None,
            ks_band_95=None,
        )

    ks_stat, ks_p = kolmogorov_smirnov(zs)
    lb = ljung_box(zs, max_lags=max_lags)
    # A Ljung–Box that could not be run (lags = 0) contributes no evidence; treating its
    # placeholder p = 1.0 as a pass would be a green light from a test that never executed.
    lb_p_effective: float | None = lb.p_value if lb.lags > 0 else None
    state, failing = gof_state_for(n, ks_p, lb_p_effective)

    return GoodnessOfFit(
        event_class=event_class,
        n=n,
        rescaled_tau=taus,
        rescaled_z=zs,
        ks_statistic=ks_stat,
        ks_p=ks_p,
        ljung_box_stat=lb.statistic if lb.lags > 0 else None,
        ljung_box_p=lb_p_effective,
        ljung_box_lags=lb.lags,
        gof_state=state,
        failing_statistic=failing,
        ks_band_95=1.36 / math.sqrt(n),
    )
