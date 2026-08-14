"""
services/ka_kshetra/layer1.py — DHARA Engine Layer 1: per-class projection.

Implements DHARA_ENGINE_SPEC_v1_0.md §2 (P-B L-ENGINE, P1).

Layer 1 takes a pre-computed Layer 0 and an event class, and produces the
ln_lambda value at each knot WITHOUT calling terms_at() or hazard.evaluate().
This eliminates the 60K+ redundant evaluations that today's DHARA sweep calls.

The projection replicates the §5.1 hazard formula from Layer 0's arrays:

    ln λ_e(t_k) = ln λ⁰_e + ln P̃_e   (baseline + promise — constant)
                + Σ_s w_s · A_s · r_{s,e}(t_k)  (clock term — from lord_stacks)
                + Σ_j β_j · x_j(t_k)             (modifier term — from covariates)
                + Σ_m ln(1 − ρ_m · u_m(t_k))     (suppression — SM-R-7 filtered)

SM-R-7 suppression filter (OPTION B, per-class):
  suppressed_keys = {key for r in routes for key in r.suppressed_by}
  filtered_obs    = {k: v for k, v in layer0.obstructions.items()
                    if k in suppressed_keys}
  A class with no suppressed routes gets filtered_obs = {} → S_e(t) = 1.0.

The .npz contract (TermMatrixRow schema) is UNCHANGED. This module does not
interact with it — it produces the raw ln_lambda values the existing DHARA sweep
and dhara_term_matrix.py already know how to consume.

PURITY: no DB, no IO, no RNG.

Authority: DHARA_ENGINE_SPEC_v1_0.md §2. SM-R-7 suppression semantics: B
(per-class filtered, OPTION B). PURNA_GROUNDING_REPORT G1-G3.
"""
from __future__ import annotations

import bisect
import math
from typing import TYPE_CHECKING, Sequence

import numpy as np

from services.ka_kshetra.contracts import Route
from services.ka_kshetra.hazard import (
    DEFAULT_DEPTH_WEIGHTS,
    RHO_MAX,
    baseline_rate,
    clock_log_factor,
    predictive_systems,
    promise_tilde,
    relevance,
    suppression_log_term,
)
from services.ka_kshetra.layer0 import Layer0

if TYPE_CHECKING:
    from services.ka_kshetra.stage4_field import FieldEvaluator


def project_layer1(
    layer0: Layer0,
    event_class: str,
    routes: Sequence[Route],
    evaluator: 'FieldEvaluator',
    knot_index: int,
) -> float:
    """Project Layer 0 to a per-class ln_lambda at one knot index.

    DHARA_ENGINE_SPEC_v1_0.md §2.2:
      Zero I/O; pure arithmetic on pre-computed Layer 0 arrays.

    Args:
        layer0:      Pre-computed chart-level Layer 0 instance.
        event_class: The event class being projected.
        routes:      Sequence[Route] for this class (from kala_field_routes).
        evaluator:   FieldEvaluator for this class (supplies lifetime_count,
                     promise, clocks, weights, horizon_days).
        knot_index:  Index into layer0.knots to evaluate at.

    Returns:
        ln_lambda at layer0.knots[knot_index] for event_class.

    SM-R-7 suppression filter:
        suppressed_keys = {key for r in routes for key in r.suppressed_by}
        filtered_obs    = keys in layer0.obstructions ∩ suppressed_keys
        A class with no suppressed routes gets S_e(t_k) = 1.0 (filtered_obs
        empty → suppression_log_term returns 0.0 → exp(0) = 1.0).
    """
    k = knot_index

    # ── Baseline + promise (constant terms) ──────────────────────────────────
    lam0 = baseline_rate(evaluator.lifetime_count)
    p_tilde = promise_tilde(evaluator.promise.p)
    ln_base = math.log(lam0) + math.log(p_tilde)

    # ── Clock term: Σ_s w_s * A_s * r_{s,e}(t_k) ────────────────────────────
    #
    # For each applicable predictive clock system, build the lord stack at this
    # knot from layer0.lord_stacks and compute relevance against routes.
    weights = evaluator.weights
    depth_weights = {
        level: float(weights.get(f'd:{level}', default))
        for level, default in DEFAULT_DEPTH_WEIGHTS.items()
    }

    clock_log = 0.0
    for clock in sorted(predictive_systems(evaluator.clocks), key=lambda c: c.system_id):
        w_s = float(weights.get(f'w_s:{clock.system_id}', 0.0))
        if w_s == 0.0:
            continue

        # Build lord_stack for this system at knot k from Layer 0.
        # lord_stacks keys are (system_id, level); stack is ordered MD→AD→PD…
        # by the level's LEVEL_ORDER rank (same order FieldEvaluator builds).
        lord_stack: list[tuple[str, str]] = []
        from services.ka_kshetra.stage4_field import LEVEL_ORDER
        for level in LEVEL_ORDER:
            key = (clock.system_id, level)
            if key in layer0.lord_stacks:
                lord = layer0.lord_stacks[key][k]
                if lord:  # '' means no lord at this knot
                    lord_stack.append((level, lord))

        r = relevance(lord_stack, routes, depth_weights)
        clock_log += clock_log_factor(float(clock.quality or 0.0), r, w_s)

    # ── Modifier term: Σ_j β_j * x_j(t_k) ────────────────────────────────────
    #
    # Read directly from the pre-computed covariates matrix (row j, column k).
    modifier_log = 0.0
    from services.ka_kshetra.hazard import COVARIATE_KEYS, COVARIATE_WEIGHT_IDS
    for j, cov_key in enumerate(COVARIATE_KEYS):
        beta_id = COVARIATE_WEIGHT_IDS[cov_key]
        beta = weights.get(beta_id)
        if beta is None:
            continue
        modifier_log += float(beta) * float(layer0.covariates[j, k])

    # ── Suppression term: SM-R-7 per-class filter (OPTION B) ─────────────────
    #
    # suppressed_keys = union of all route.suppressed_by sets for this class.
    # Only obstructions referenced by some route can suppress this class.
    suppressed_keys: set[str] = {
        key for r in routes for key in r.suppressed_by
    }

    suppression_log = 0.0
    if suppressed_keys:
        # Build the filtered obstruction dict at knot k.
        filtered_obs: dict[str, float] = {}
        for vighna_key, u_arr in layer0.obstructions.items():
            if vighna_key in suppressed_keys:
                u_val = float(u_arr[k])
                if u_val > 0.0:
                    filtered_obs[vighna_key] = u_val

        if filtered_obs:
            default_rho = float(weights.get('rho:default', 0.25))
            suppression_log = suppression_log_term(filtered_obs, weights, default_rho)
    # If suppressed_keys is empty: suppression_log = 0.0 → S_e(t) = 1.0. (SM-R-7)

    return ln_base + clock_log + modifier_log + suppression_log


__all__ = [
    'project_layer1',
]
