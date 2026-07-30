"""
skill.py — THE TEMPORAL SKILL SCORE (§7.3).

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §7.3.

── THE SCORE ──────────────────────────────────────────────────────────────────────────────
Per chart, per event class — a log-likelihood-ratio skill score against the chart's OWN
circular-shifted null (§5.5), in NATS PER EVENT:

    SS_e = (1 / n_e) · [ ℓ_e(model) − mean_{r=1..R} ℓ_e(null^{(r)}) ]

      ℓ_e(model)      = Σ_k ln λ_e(t_k)        − Λ_e(0,T)        the FITTED, OUT-OF-SAMPLE λ
      ℓ_e(null^{(r)}) = Σ_k ln λ^{(r)}_e(t_k)  − Λ^{(r)}_e(0,T)  the §5.5 replicate

    chart level: SS = Σ_e n_e·SS_e / Σ_e n_e   (event-weighted)

`exp(SS_e)` is the per-event likelihood ratio. **`SS_e = 0` is exactly the null hypothesis
"this field carries no temporal information."** The comparison is against the chart's own sky,
circularly shifted — not against a generic Poisson baseline — so a high score cannot be earned
by a class simply being common: the null has the same baseline, the same promise, the same
clocks and the same marginal rate, and differs ONLY in when the transits fall.

── WHY THE SCORE DECOMPOSES INTO PER-EVENT TERMS ──────────────────────────────────────────
Write `C = Λ_model(0,T) − mean_r Λ_null^{(r)}(0,T)` — a constant with no event index. Then

    SS_e = mean_k [ ln λ_model(t_k) − mean_r ln λ_null^{(r)}(t_k) ]  −  C / n_e
         = mean_k(d_k) − C / n_e

The `d_k` are the per-event log-likelihood advantages. That decomposition is what makes the
percentile bootstrap well-defined: resampling events means resampling the `d_k`, while `C`
(an integral over the whole observation window, not over events) is held fixed. Bootstrapping
the whole `ℓ` instead would resample the integral term too, which is not a per-event quantity
and would understate the interval.

── DETERMINISM ────────────────────────────────────────────────────────────────────────────
`B = 2000` resamples, seed = `int(sha256(f'{chart_id}|{weights_version}|{e}')[:8], 16)`. Fixed
by the design so a rerun reproduces the interval exactly; the seed is stored on the row
(`kala_field_skill.bootstrap_seed`) so reproduction is inspection, not re-derivation.

── THE HONESTY RULE (§N.8's detector for "this instrument has skill") ─────────────────────
    skill_state = 'established'     iff  SS_lo > 0  and  n_e ≥ 8
                = 'not_established' iff  SS_lo ≤ 0  and  n_e ≥ 8
                = 'underpowered'    iff  n_e < 8

**The number is published in all three states.** `not_established` is a legitimate, shippable
result. The code path that makes this signal correctly read false is the ordinary one: a field
with no temporal information produces `d_k ≈ 0`, the bootstrap interval straddles zero, and
the state is `not_established`. That is a real detector, not a flag.

Pure functions. No DB, no clock; the only randomness is the seeded bootstrap.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence

import numpy as np

#: §7.3. Below this, a score is `underpowered` — never `established`, never `not_established`.
MIN_EVENTS_FOR_POWER = 8
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_CONFIDENCE = 0.95

SKILL_ESTABLISHED = "established"
SKILL_NOT_ESTABLISHED = "not_established"
SKILL_UNDERPOWERED = "underpowered"

#: §7.3's regression gate (E7.5): "regressed" = below the best released value by more than
#: this many nats/event, absent a classified reason. Stated so ordinary refit churn does not
#: trip the gate; versioned with the harness.
SKILL_REGRESSION_TOLERANCE_NATS = 0.05


def bootstrap_seed(chart_id: str, weights_version: str, event_class: str) -> int:
    """The §7.3 deterministic seed. `event_class` is `''` for the chart-level aggregate."""
    digest = hashlib.sha256(f"{chart_id}|{weights_version}|{event_class}".encode()).hexdigest()
    return int(digest[:8], 16)


@dataclass(frozen=True)
class SkillScore:
    event_class: str | None
    n_events: int
    skill_score: float
    skill_lo: float
    skill_hi: float
    skill_state: str
    null_replicates: int
    bootstrap_resamples: int
    bootstrap_seed: int
    #: the per-event advantages `d_k`, retained so a caller can audit or re-bootstrap
    per_event_advantage: tuple[float, ...] = ()
    #: `C = Λ_model − mean_r Λ_null^{(r)}`, the event-independent term
    integral_advantage: float = 0.0


def skill_state_for(n_events: int, skill_lo: float) -> str:
    """The §7.3 three-state predicate, in one place so no caller re-derives it."""
    if n_events < MIN_EVENTS_FOR_POWER:
        return SKILL_UNDERPOWERED
    return SKILL_ESTABLISHED if skill_lo > 0.0 else SKILL_NOT_ESTABLISHED


def compute_skill(
    *,
    chart_id: str,
    weights_version: str,
    event_class: str | None,
    model_log_intensity: Sequence[float],
    null_log_intensity_per_replicate: Sequence[Sequence[float]],
    model_integral: float,
    null_integrals: Sequence[float],
    resamples: int = BOOTSTRAP_RESAMPLES,
    confidence: float = BOOTSTRAP_CONFIDENCE,
) -> SkillScore:
    """`SS_e` with its percentile-bootstrap interval and its honest state.

    Args:
      model_log_intensity: `ln λ_model(t_k)` for each scored event, in event order.
      null_log_intensity_per_replicate: `R` sequences of `ln λ^{(r)}(t_k)`, same events, same
        order. `R` is `kala_field_null.replicates` (256 at W2).
      model_integral: `Λ_model(0, T)` over the observation window actually scored.
      null_integrals: `Λ^{(r)}(0, T)` per replicate, same window.

    An empty event set is a legal, honest input: it yields `SS = 0.0` with
    `skill_state = 'underpowered'` and a degenerate `[0, 0]` interval. That is the LEL-absent
    chart, and it is a real answer ("we cannot measure skill here"), not an error.
    """
    n = len(model_log_intensity)
    replicates = len(null_log_intensity_per_replicate)

    if replicates != len(null_integrals):
        raise ValueError(
            f"{replicates} replicate intensity vectors but {len(null_integrals)} replicate "
            f"integrals — the two must come from the same §5.5 replicate set"
        )
    for r, vec in enumerate(null_log_intensity_per_replicate):
        if len(vec) != n:
            raise ValueError(
                f"replicate {r} scores {len(vec)} events but the model scores {n} — the null "
                f"must be evaluated at exactly the same event times (§5.5 shifts the sky, not "
                f"the events)"
            )

    seed = bootstrap_seed(chart_id, weights_version, event_class or "")

    if n == 0 or replicates == 0:
        # Honest degenerate case. Reported, never hidden; `underpowered` is the truthful state.
        return SkillScore(
            event_class=event_class,
            n_events=n,
            skill_score=0.0,
            skill_lo=0.0,
            skill_hi=0.0,
            skill_state=SKILL_UNDERPOWERED,
            null_replicates=replicates,
            bootstrap_resamples=0,
            bootstrap_seed=seed,
            per_event_advantage=(),
            integral_advantage=0.0,
        )

    model_arr = np.asarray(model_log_intensity, dtype=float)
    null_arr = np.asarray(
        [np.asarray(v, dtype=float) for v in null_log_intensity_per_replicate], dtype=float
    )
    # d_k = ln λ_model(t_k) − mean_r ln λ^{(r)}(t_k)
    d = model_arr - null_arr.mean(axis=0)
    # C = Λ_model − mean_r Λ^{(r)}
    integral_advantage = float(model_integral) - float(np.mean(np.asarray(null_integrals, float)))

    point = float(d.mean() - integral_advantage / n)

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(resamples, n))
    boot = d[idx].mean(axis=1) - integral_advantage / n
    alpha = (1.0 - confidence) / 2.0
    lo = float(np.quantile(boot, alpha))
    hi = float(np.quantile(boot, 1.0 - alpha))

    return SkillScore(
        event_class=event_class,
        n_events=n,
        skill_score=point,
        skill_lo=lo,
        skill_hi=hi,
        skill_state=skill_state_for(n, lo),
        null_replicates=replicates,
        bootstrap_resamples=resamples,
        bootstrap_seed=seed,
        per_event_advantage=tuple(float(v) for v in d),
        integral_advantage=integral_advantage,
    )


def aggregate_chart_skill(
    per_class: Sequence[SkillScore],
    *,
    chart_id: str,
    weights_version: str,
    resamples: int = BOOTSTRAP_RESAMPLES,
    confidence: float = BOOTSTRAP_CONFIDENCE,
) -> SkillScore:
    """The chart-level row: `SS = Σ_e n_e·SS_e / Σ_e n_e` (§7.3, event-weighted).

    The interval is bootstrapped over the POOLED per-event advantages rather than combined
    from the per-class intervals — pooling is the same estimator applied to the same events,
    whereas averaging intervals has no defensible coverage.
    """
    scored = [s for s in per_class if s.n_events > 0]
    total_n = sum(s.n_events for s in scored)
    seed = bootstrap_seed(chart_id, weights_version, "")

    if total_n == 0:
        return SkillScore(
            event_class=None,
            n_events=0,
            skill_score=0.0,
            skill_lo=0.0,
            skill_hi=0.0,
            skill_state=SKILL_UNDERPOWERED,
            null_replicates=max((s.null_replicates for s in per_class), default=0),
            bootstrap_resamples=0,
            bootstrap_seed=seed,
        )

    point = sum(s.n_events * s.skill_score for s in scored) / total_n

    # Pooled bootstrap: resample the union of per-event advantages, then re-apply each class's
    # own integral offset in proportion. Equivalent to resampling events chart-wide.
    pooled_d = np.concatenate([np.asarray(s.per_event_advantage, dtype=float) for s in scored])
    pooled_offset = sum(s.integral_advantage for s in scored) / total_n

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, total_n, size=(resamples, total_n))
    boot = pooled_d[idx].mean(axis=1) - pooled_offset
    alpha = (1.0 - confidence) / 2.0
    lo = float(np.quantile(boot, alpha))
    hi = float(np.quantile(boot, 1.0 - alpha))

    return SkillScore(
        event_class=None,
        n_events=total_n,
        skill_score=float(point),
        skill_lo=lo,
        skill_hi=hi,
        skill_state=skill_state_for(total_n, lo),
        null_replicates=max(s.null_replicates for s in scored),
        bootstrap_resamples=resamples,
        bootstrap_seed=seed,
        per_event_advantage=tuple(float(v) for v in pooled_d),
        integral_advantage=pooled_offset * total_n,
    )


def has_regressed(new_score: float, best_released: float | None) -> bool:
    """§7.3's regression gate (E7.5).

    `None` best_released means this is the first published score for the chart — it BECOMES
    the baseline and cannot itself be a regression.
    """
    if best_released is None:
        return False
    return new_score < best_released - SKILL_REGRESSION_TOLERANCE_NATS
