"""
likelihood.py — the inhomogeneous-Poisson process log-likelihood.

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.2.

    ℓ_e(θ) = Σ_{k=1}^{n_e} ln λ_e(t_k; θ)  −  Λ_e(0, T; θ)
    ℓ(θ)   = Σ_e ℓ_e(θ)

`Λ` is EXACTLY `field.integrate` — the same code path that serves `expected_count` on a window
and `τ_k` in the goodness-of-fit test. §7.2 calls this out as load-bearing and it is: a fitter
with a private integral would publish a skill score for a model the product does not serve.

── THE OBSERVATION WINDOW IS AN ARGUMENT, NOT A CONSTANT ──────────────────────────────────
`Λ` must be taken over the interval actually OBSERVED, not over the chart's full 100-year
horizon. In the forward-chaining CV of §7.2 step 3, fold `j` integrates over `[0, c_{j+1}]` —
"the observation window actually available at that origin". Integrating over the full horizon
in a fold would charge the model for hazard in a stretch where no event could yet have been
recorded, which systematically penalises exactly the folds with the least data. So
`observation_end` is a required argument here and every caller passes its own.

── THE LOG TERM IS COMPUTED IN LOG SPACE ──────────────────────────────────────────────────
`ln λ(t_k)` is read straight off the stored `(α, γ)` — never as `log(exp(...))`. For a rare
class over a century, `λ` runs around 1e-4/day; the round trip is lossy where it matters most.

Pure functions. No DB, no clock, no RNG.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from services.mi_bhara.basis import FieldBasis, ParameterVector, build_segments
from services.mi_bhara.field import FieldSegment, integrate, log_lambda


@dataclass(frozen=True)
class LogLikelihood:
    """`ℓ`, split into its two terms so a caller can report them separately.

    Kept apart deliberately: the skill score's bootstrap resamples the per-event terms while
    holding the integral term fixed (it is not indexed by event), and a summed-only return
    would make that impossible without recomputation.
    """

    total: float
    event_term: float
    integral_term: float
    n_events: int
    #: `ln λ(t_k)` per event, in the order given — the bootstrap's unit of resampling.
    per_event_log_intensity: tuple[float, ...] = ()


def poisson_loglik(
    segments: Sequence[FieldSegment],
    event_times: Sequence[float],
    observation_start: float,
    observation_end: float,
) -> LogLikelihood:
    """`ℓ = Σ_k ln λ(t_k) − Λ(observation_start, observation_end)`.

    Events outside the observation window are a caller error, not something to filter away
    quietly: silently dropping them would make the likelihood of two different event sets
    identical and the resulting skill score meaningless.
    """
    if observation_end < observation_start:
        raise ValueError(
            f"observation window is inverted: [{observation_start}, {observation_end}]"
        )
    per_event: list[float] = []
    for t in event_times:
        if not (observation_start <= t <= observation_end):
            raise ValueError(
                f"event at t={t} lies outside the observation window "
                f"[{observation_start}, {observation_end}] — filter before calling, so the "
                f"drop is visible and counted"
            )
        per_event.append(log_lambda(segments, t))
    event_term = sum(per_event)
    integral_term = integrate(segments, observation_start, observation_end)
    return LogLikelihood(
        total=event_term - integral_term,
        event_term=event_term,
        integral_term=integral_term,
        n_events=len(per_event),
        per_event_log_intensity=tuple(per_event),
    )


def loglik_for_theta(
    basis: FieldBasis,
    theta: ParameterVector,
    event_times: Sequence[float],
    observation_start: float,
    observation_end: float,
) -> LogLikelihood:
    """`ℓ_e(θ)` — rebuild the stored field at θ, then evaluate. The optimiser's objective."""
    segments = build_segments(basis, theta)
    return poisson_loglik(segments, event_times, observation_start, observation_end)


def negative_loglik_objective(
    basis: FieldBasis,
    event_times: Sequence[float],
    observation_start: float,
    observation_end: float,
):
    """A `scipy.optimize.minimize`-shaped closure over the flat θ vector.

    A θ that drives a suppression factor non-positive is not silently clamped — `basis.py`
    raises, and the objective converts that to `+inf`, which L-BFGS-B handles by backing off.
    The box constraints make it unreachable in practice; this is the belt for the braces.
    """
    n_w, n_b, n_r = basis.dimensions

    def objective(flat) -> float:
        theta = ParameterVector.from_flat(list(flat), n_w, n_b, n_r)
        try:
            ll = loglik_for_theta(
                basis, theta, event_times, observation_start, observation_end
            )
        except ValueError:
            return float("inf")
        if ll.total != ll.total or ll.total == float("inf"):  # NaN or +inf
            return float("inf")
        return -ll.total

    return objective
