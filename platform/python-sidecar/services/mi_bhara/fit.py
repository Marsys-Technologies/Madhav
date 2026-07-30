"""
fit.py — THE WEIGHT-FITTING HARNESS (§7.2): optimiser, blocked forward-chaining CV, shrinkage
to the classical priors, and the per-release trust region.

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.2. Registry items 21 (per-tradition per-chart
calibration weights) and E1's D3 fit.

── THE OBJECTIVE ──────────────────────────────────────────────────────────────────────────
Maximise the inhomogeneous-Poisson log-likelihood `ℓ(θ) = Σ_e ℓ_e(θ)` over
`θ = (w_s, β_j, ρ_m)`, box-constrained to `w ∈ [0,1]`, `β ∈ [−2,2]`, `ρ ∈ [0,0.95]`.
`scipy.optimize.minimize(method='L-BFGS-B')`, started at the classical priors `θ⁰`, with
fixed tolerances and NO RNG anywhere: same inputs ⇒ same parameters, byte for byte. That
determinism is not a nicety — the field hash pins a weights version, and a fit that wandered
would make the hash unreproducible.

── WHY THE SPLIT IS FORWARD-CHAINING AND NEVER RANDOM ─────────────────────────────────────
A random train/test split leaks the future into the past for a temporal model: the fitted
weights would be tuned on events the "held-out" ones are correlated with through the very
clocks being fitted, and the reported out-of-sample likelihood would be optimistic in a way
nothing downstream could detect. So (§7.2 steps 1–4):

  1. sort the chart's LEL events by date;
  2. FINAL HOLDOUT — the most recent 20% are removed entirely, scored ONCE per release, never
     used for fitting or model selection;
  3. on the remaining 80%, `k = 5` EXPANDING-ORIGIN folds: fold `j` fits on events before
     `c_j` and evaluates on `[c_j, c_{j+1})`, with `Λ` taken over `[0, c_{j+1}]` — the
     observation window actually available at that origin, not the full horizon;
  4. the POOLED out-of-sample log-likelihood is the fit's reported quality; the SHIPPED vector
     is refit on the full 80% and then shrunk.

Fold 1 has no fitting events at all. That is not a bug to paper over — it is the honest state
of the earliest origin, and the shrinkage formula answers it exactly: `n_eff = 0 ⇒ φ̂ = φ⁰`.

── SHRINKAGE (hierarchical / empirical-Bayes, conservative) ───────────────────────────────
    φ̂_shrunk = ( n_eff / (n_eff + τ) )·φ̂_MLE  +  ( τ / (n_eff + τ) )·φ⁰ ,   τ = 20 events

`n_eff` is the number of OUT-OF-SAMPLE events in the stratum the parameter governs. Three
consequences the design calls out and this module makes literal:
  • `n_eff = 0 ⇒ φ̂ = φ⁰` EXACTLY. **This is the LEL-absent scenario falling out of the
    formula rather than being special-cased** — there is no `if chart_has_no_lel` branch
    anywhere in this package, and there must never be one.
  • `n_eff = 20` ⇒ half-way; `n_eff = 57` (the native's current LEL) ⇒ 74% data, 26% prior.
  • TRUST REGION, per release: `|φ̂_shrunk − φ_prev| ≤ 0.5·|φ_prev| + 0.25`. A single release
    can never move a weight arbitrarily far, and a clipped parameter is RECORDED
    (`clipped = TRUE`), not silently accepted.

── PROSPECTIVE vs BACKFILL ────────────────────────────────────────────────────────────────
Prospective resolutions (predictions filed BEFORE their outcome, from the item-20 ledger) are
ALWAYS out-of-sample. They are scored and reported SEPARATELY from retrodiction and are never
summed with it (Elevation §7). This module carries the split through as a field on the result;
`living_lel.py` owns the ledger side.

Pure functions. No DB, no clock, no RNG.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Mapping, Sequence

import numpy as np
from scipy import optimize

from services.mi_bhara.basis import (
    FieldBasis,
    ParameterVector,
    bounds_for,
    clip_to_bounds,
)
from services.mi_bhara.likelihood import (
    LogLikelihood,
    loglik_for_theta,
    negative_loglik_objective,
)

#: §7.2. The shrinkage half-life, in events.
TAU_SHRINKAGE = 20.0
#: §7.2 step 2 — the fraction removed as the FINAL holdout.
FINAL_HOLDOUT_FRACTION = 0.20
#: §7.2 step 3 — expanding-origin folds on the remaining 80%.
CV_FOLDS = 5
#: §7.2's fixed optimiser tolerances. No RNG, no adaptive restarts.
LBFGSB_FTOL = 1e-9
LBFGSB_MAXITER = 500


@dataclass(frozen=True)
class ScoredEvent:
    """One LEL event as the fitter sees it.

    `t` is days since birth (the field's own time axis). `is_prospective` marks an event that
    resolved a prediction filed BEFORE it happened — the gold-standard currency, tallied
    separately and never summed with backfill.
    """

    t: float
    event_class: str
    is_prospective: bool = False
    event_id: str = ""


@dataclass(frozen=True)
class ShrinkageOutcome:
    weight_id: str
    prior_value: float
    mle_value: float
    shrunk_value: float
    n_eff: int
    clipped: bool


@dataclass(frozen=True)
class FoldResult:
    fold_index: int
    cut_start: float
    cut_end: float
    n_train: int
    n_eval: int
    #: out-of-sample ℓ on this fold's evaluation slice, under the fold's own fitted θ
    oos_loglik: float


@dataclass(frozen=True)
class FitResult:
    event_class: str
    theta_mle: ParameterVector
    theta_shipped: ParameterVector
    prior: ParameterVector
    n_train: int
    n_holdout: int
    n_prospective: int
    n_backfill: int
    fit_loglik: float
    pooled_oos_loglik: float
    holdout_loglik: float | None
    folds: tuple[FoldResult, ...] = ()
    shrinkage: tuple[ShrinkageOutcome, ...] = ()
    any_clipped: bool = False
    converged: bool = True
    notes: tuple[str, ...] = dc_field(default_factory=tuple)


# ── shrinkage + trust region ───────────────────────────────────────────────────────────

def shrink(mle: float, prior: float, n_eff: int, tau: float = TAU_SHRINKAGE) -> float:
    """`φ̂_shrunk = (n_eff/(n_eff+τ))·φ̂_MLE + (τ/(n_eff+τ))·φ⁰`.

    `n_eff = 0` returns `prior` EXACTLY — bit-identical, not merely close. That exactness is
    what makes the LEL-absent scenario a property of the formula rather than of a branch.
    """
    if n_eff < 0:
        raise ValueError(f"n_eff must be non-negative; got {n_eff}")
    if tau <= 0:
        raise ValueError(f"tau must be positive; got {tau}")
    if n_eff == 0:
        return float(prior)
    lam = n_eff / (n_eff + tau)
    return lam * float(mle) + (1.0 - lam) * float(prior)


def apply_trust_region(candidate: float, previous: float) -> tuple[float, bool]:
    """`|φ̂ − φ_prev| ≤ 0.5·|φ_prev| + 0.25` (§7.2). Returns `(value, clipped)`.

    The `+ 0.25` floor is what lets a parameter whose previous value is 0 move at all — a
    purely multiplicative region would freeze a zeroed weight forever.
    """
    allowance = 0.5 * abs(float(previous)) + 0.25
    lo, hi = float(previous) - allowance, float(previous) + allowance
    if candidate < lo:
        return lo, True
    if candidate > hi:
        return hi, True
    return float(candidate), False


def shrink_vector(
    *,
    basis: FieldBasis,
    mle: ParameterVector,
    prior: ParameterVector,
    n_eff_by_weight_id: Mapping[str, int],
    previous: ParameterVector | None = None,
    tau: float = TAU_SHRINKAGE,
) -> tuple[ParameterVector, tuple[ShrinkageOutcome, ...]]:
    """Shrink every parameter toward its prior, then apply the per-release trust region.

    `n_eff_by_weight_id` is keyed by the SAME `weight_id` strings `basis.weight_ids` emits,
    so a stratum count can never be applied to the wrong parameter. A missing key means zero
    out-of-sample events in that stratum, which is a legitimate state and resolves to the
    prior — not an error and not a silent 1.
    """
    basis.assert_conformable(mle)
    basis.assert_conformable(prior)
    ids = basis.weight_ids
    mle_flat = mle.as_flat()
    prior_flat = prior.as_flat()
    prev_flat = previous.as_flat() if previous is not None else prior_flat

    values: list[float] = []
    outcomes: list[ShrinkageOutcome] = []
    for wid, m, p0, prev in zip(ids, mle_flat, prior_flat, prev_flat):
        n_eff = int(n_eff_by_weight_id.get(wid, 0))
        shrunk = shrink(m, p0, n_eff, tau=tau)
        bounded, clipped = apply_trust_region(shrunk, prev)
        values.append(bounded)
        outcomes.append(
            ShrinkageOutcome(
                weight_id=wid,
                prior_value=float(p0),
                mle_value=float(m),
                shrunk_value=float(bounded),
                n_eff=n_eff,
                clipped=clipped,
            )
        )

    n_w, n_b, n_r = basis.dimensions
    shrunk_vec = clip_to_bounds(ParameterVector.from_flat(values, n_w, n_b, n_r))
    return shrunk_vec, tuple(outcomes)


# ── the optimiser ──────────────────────────────────────────────────────────────────────

def maximise_loglik(
    basis: FieldBasis,
    event_times: Sequence[float],
    observation_start: float,
    observation_end: float,
    start: ParameterVector,
) -> tuple[ParameterVector, float, bool]:
    """One L-BFGS-B run. Returns `(θ̂, ℓ(θ̂), converged)`.

    With ZERO training events the log-likelihood is `−Λ(0,T;θ)`, whose maximiser is whatever θ
    minimises total hazard — a meaningless direction with no data behind it. So the zero-event
    case short-circuits to the starting point (the prior) rather than optimising noise. This
    is the same honesty the shrinkage formula enforces one level up; doing it here too means
    `theta_mle` is never a fabricated number even before shrinkage sees it.
    """
    if len(event_times) == 0:
        ll = loglik_for_theta(basis, start, [], observation_start, observation_end)
        return start, ll.total, True

    n_w, n_b, n_r = basis.dimensions
    if n_w + n_b + n_r == 0:
        ll = loglik_for_theta(basis, start, event_times, observation_start, observation_end)
        return start, ll.total, True

    objective = negative_loglik_objective(
        basis, event_times, observation_start, observation_end
    )
    res = optimize.minimize(
        objective,
        x0=np.asarray(start.as_flat(), dtype=float),
        method="L-BFGS-B",
        bounds=bounds_for(basis),
        options={"ftol": LBFGSB_FTOL, "maxiter": LBFGSB_MAXITER},
    )
    theta = clip_to_bounds(ParameterVector.from_flat(list(res.x), n_w, n_b, n_r))
    ll = loglik_for_theta(basis, theta, event_times, observation_start, observation_end)
    return theta, ll.total, bool(res.success)


# ── the CV split ───────────────────────────────────────────────────────────────────────

def split_final_holdout(
    events: Sequence[ScoredEvent], fraction: float = FINAL_HOLDOUT_FRACTION
) -> tuple[list[ScoredEvent], list[ScoredEvent]]:
    """§7.2 step 2 — the most recent `fraction` of events become the FINAL holdout.

    Returns `(train, holdout)`, both date-sorted. With fewer than 5 events the holdout would
    be a single point (or empty) and any score on it would be noise, so the whole set stays in
    training and the holdout score is reported as `None` — an honest "not measurable", never
    a number computed from one observation.
    """
    ordered = sorted(events, key=lambda e: (e.t, e.event_id))
    n = len(ordered)
    if n < 5:
        return list(ordered), []
    n_hold = max(1, int(round(n * fraction)))
    return list(ordered[: n - n_hold]), list(ordered[n - n_hold :])


def expanding_origin_cuts(
    events: Sequence[ScoredEvent], folds: int = CV_FOLDS, horizon_end: float | None = None
) -> list[float]:
    """The `k+1` cut dates `c_1 … c_{k+1}` bounding §7.2 step 3's expanding-origin folds.

    `c_j` is the time of the `⌊j·n/k⌋`-th training event (quintile boundaries by COUNT, which
    is what "quintile cut-dates" means for a point process); `c_{k+1}` closes the last fold at
    the end of the observed training window.
    """
    ordered = sorted(events, key=lambda e: (e.t, e.event_id))
    n = len(ordered)
    if n == 0:
        return []
    end = horizon_end if horizon_end is not None else ordered[-1].t
    cuts: list[float] = []
    for j in range(1, folds + 1):
        idx = min(n - 1, max(0, int(j * n / folds) - 1))
        cuts.append(ordered[idx].t)
    cuts = sorted(set(cuts))
    if end > cuts[-1]:
        cuts.append(end)
    return cuts


# ── the whole harness ──────────────────────────────────────────────────────────────────

def fit_event_class(
    *,
    basis: FieldBasis,
    events: Sequence[ScoredEvent],
    prior: ParameterVector,
    horizon_end: float,
    previous: ParameterVector | None = None,
    tau: float = TAU_SHRINKAGE,
    folds: int = CV_FOLDS,
) -> FitResult:
    """The full §7.2 harness for one event class.

    Order of operations is the design's, not a rearrangement: final holdout FIRST (so nothing
    downstream can see it), then expanding-origin CV for the reported quality, then the
    shipped refit on the full training set, then shrinkage, then the trust region.
    """
    notes: list[str] = []
    class_events = [e for e in events if e.event_class == basis.event_class]
    train, holdout = split_final_holdout(class_events)
    if class_events and not holdout:
        notes.append(
            "final_holdout_not_taken: fewer than 5 events — a holdout score on 1 point is "
            "noise, so it is reported as null rather than as a number"
        )

    train_times = [e.t for e in train]

    # ── expanding-origin CV ──
    fold_results: list[FoldResult] = []
    pooled_oos = 0.0
    cuts = expanding_origin_cuts(train, folds=folds, horizon_end=horizon_end)
    for j in range(len(cuts) - 1):
        c_j, c_next = cuts[j], cuts[j + 1]
        fit_times = [t for t in train_times if t < c_j]
        eval_times = [t for t in train_times if c_j <= t < c_next]
        theta_j, _, _ = maximise_loglik(basis, fit_times, 0.0, c_j if fit_times else c_next, prior)
        # §7.2 step 3: Λ over [0, c_{j+1}] — the observation window available at this origin.
        ll_j = loglik_for_theta(basis, theta_j, eval_times, 0.0, c_next)
        pooled_oos += ll_j.total
        fold_results.append(
            FoldResult(
                fold_index=j + 1,
                cut_start=c_j,
                cut_end=c_next,
                n_train=len(fit_times),
                n_eval=len(eval_times),
                oos_loglik=ll_j.total,
            )
        )

    # ── shipped refit on the full training set ──
    theta_mle, fit_ll, converged = maximise_loglik(
        basis, train_times, 0.0, horizon_end, prior
    )
    if not converged:
        notes.append("optimizer_did_not_converge: L-BFGS-B reported success=False")

    # n_eff = OUT-OF-SAMPLE events in the stratum the parameter governs (§7.2). β and ρ are
    # per-event-class; w_s is pooled across classes, but this function fits one class at a
    # time, so the caller supplies the pooled count for w_s via `n_eff_by_weight_id`. Here the
    # per-class default is the CV-evaluated count, which is exactly "out-of-sample".
    n_oos = sum(f.n_eval for f in fold_results)
    n_eff_map = {wid: n_oos for wid in basis.weight_ids}

    theta_shipped, shrinkage = shrink_vector(
        basis=basis,
        mle=theta_mle,
        prior=prior,
        n_eff_by_weight_id=n_eff_map,
        previous=previous,
        tau=tau,
    )

    holdout_ll: float | None = None
    if holdout:
        holdout_ll = loglik_for_theta(
            basis, theta_shipped, [e.t for e in holdout], 0.0, horizon_end
        ).total

    return FitResult(
        event_class=basis.event_class,
        theta_mle=theta_mle,
        theta_shipped=theta_shipped,
        prior=prior,
        n_train=len(train),
        n_holdout=len(holdout),
        n_prospective=sum(1 for e in class_events if e.is_prospective),
        n_backfill=sum(1 for e in class_events if not e.is_prospective),
        fit_loglik=fit_ll,
        pooled_oos_loglik=pooled_oos,
        holdout_loglik=holdout_ll,
        folds=tuple(fold_results),
        shrinkage=shrinkage,
        any_clipped=any(o.clipped for o in shrinkage),
        converged=converged,
        notes=tuple(notes),
    )


def loglik_of(
    basis: FieldBasis,
    theta: ParameterVector,
    events: Sequence[ScoredEvent],
    horizon_end: float,
) -> LogLikelihood:
    """Convenience: `ℓ` of a θ against a class's events over `[0, horizon_end]`."""
    times = [e.t for e in events if e.event_class == basis.event_class]
    return loglik_for_theta(basis, theta, times, 0.0, horizon_end)
