"""
services/ka_kshetra/layer0.py — DHARA Engine Layer 0: chart-level raw matrix.

Implements DHARA_ENGINE_SPEC_v1_0.md §1 (P-B L-ENGINE, P1).

Layer 0 computes ONCE per chart the quantities that are 100% chart-level with
zero class-dependence in their raw form (PURNA_GROUNDING_REPORT G1/G2/G3):
  - The knot set K (clock + envelope knots, sorted, deduplicated) plus 9
    interior decade seam knots (t = d*H/10 for d=1..9).
  - Lord stacks: for each (system_id, level) pair, the lord ID at each knot.
  - Raw covariates: 12 x_j values at each knot.
  - Raw obstruction envelopes: u_m(t) at each knot for every vighna instance.

Today's writer._class_context() rebuilds all three once per event class (27×
rebuild of identical structures). Layer 0 computes them ONCE per chart.

Thread-from-sweep optimization (§1.4): with Layer 0 pre-computed, the per-class
sweep indexes into layer0 arrays directly (O(1) per knot) instead of calling
the O(N_primitives) EnvelopeIndex methods at each of 60K+ knots per class.

PURITY: no DB, no IO, no RNG. Same constraint as hazard.py and dhara_sweep.py.

Authority: DHARA_ENGINE_SPEC_v1_0.md §1, PURNA_GROUNDING_REPORT G1-G3.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from services.ka_kshetra.hazard import (
    COVARIATE_KEYS,
    derive_dual_reference_agreement,
)

if TYPE_CHECKING:
    from services.ka_kshetra.stage4_field import FieldEvaluator


# ── Layer0 dataclass ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Layer0:
    """Chart-level raw data, computed ONCE per chart, shared across all classes.

    DHARA_ENGINE_SPEC_v1_0.md §1.2 binding contract:

    knots       : shape (N_k,), float64, days from epoch, sorted, unique.
    lord_stacks : key (system_id, level) → str ndarray shape (N_k,).
                  Each element is the lord ID active at the corresponding knot,
                  or '' when no period covers that knot.
    covariates  : shape (12, N_k), row j = covariate j=0..11 (COVARIATE_KEYS).
                  Index j=2 (dual_reference_agreement = min(x1,x2)) is derived
                  from x1 and x2 here, matching hazard.evaluate()'s own treatment.
    obstructions: key vighna_key → float64 ndarray shape (N_k,).
                  Every vighna instance present in the chart is stored here,
                  even if not referenced by any class's routes. SM-R-7's
                  per-class filter is applied in Layer 1, NOT here.

    This dataclass is frozen (immutable). Compute it once; share the reference.
    """
    knots: np.ndarray                           # float64, shape (N_k,)
    lord_stacks: dict[tuple[str, str], np.ndarray]   # str dtype, shape (N_k,) each
    covariates: np.ndarray                      # float64, shape (12, N_k)
    obstructions: dict[str, np.ndarray]         # float64, shape (N_k,) each

    def __hash__(self):
        # Frozen dataclass with numpy arrays — numpy arrays are not hashable.
        # Provide an id-based hash so Layer0 objects can be used as dict keys
        # if needed, while preserving the immutability contract.
        return id(self)

    def __eq__(self, other):
        return self is other


# ── Decade-seam knot set assembly ─────────────────────────────────────────────

def assemble_knot_set_with_decade_seams(evaluator: 'FieldEvaluator') -> np.ndarray:
    """Build K = sort(K_c UNION K_e UNION K_decade), clipped to [0, H].

    Extends the original dhara_sweep.assemble_knot_set with 9 interior decade
    seam knots t = d * H / 10 for d = 1..9 (DHARA_ENGINE_SPEC §1.2, decade-seam
    fix, originally W1 in §1.1 ground truth report).

    The decade seams eliminate the artifact at decade boundaries in the DHARA
    sweep's stored segments: without them, a lord change that coincides with a
    decade boundary is processed only by the adjacent knots from the dasha ladder,
    which may be coarser than the decade edge. Adding them is O(9) and zero-cost.

    K_c: all t_start and t_end from every LadderPeriod + horizon ends.
    K_e: evaluator.envelopes.breakpoints() — envelope primitive knot times.
    K_d: {d * H / 10 for d in range(1, 10)} — 9 interior decade seams.
    K  : sorted, deduped union, float64.

    Returns a float64 numpy array of monotonically increasing knot times.
    """
    H = evaluator.horizon_days

    pts: set[float] = {0.0, H}

    # K_c: clock knots from the dasha ladder.
    for periods in evaluator.ladder.values():
        for p in periods:
            if math.isfinite(p.t_start):
                pts.add(p.t_start)
            if math.isfinite(p.t_end):
                pts.add(p.t_end)

    # K_e: envelope primitive knot times.
    for t in evaluator.envelopes.breakpoints():
        if math.isfinite(t):
            pts.add(t)

    # K_d: 9 interior decade seam knots.
    for d in range(1, 10):
        seam = d * H / 10.0
        if math.isfinite(seam):
            pts.add(seam)

    merged = [t for t in pts if 0.0 <= t <= H]
    return np.unique(np.array(merged, dtype=np.float64))


# ── Layer 0 computation ───────────────────────────────────────────────────────

def compute_layer0(evaluator: 'FieldEvaluator', event_horizon_days: float) -> Layer0:
    """Compute the chart-level Layer 0 matrix.

    DHARA_ENGINE_SPEC_v1_0.md §1.3 — computation order:
      1. Build K = K_c ∪ K_e ∪ K_decade (with decade seam fix).
      2. For each (system_id, level): evaluate lord at each knot via the
         evaluator's pre-built binary-search arrays (O(log N) per knot).
      3. For each of the 12 covariates: evaluate x_j(t) at each knot.
         x3 (dual_reference_agreement) is derived here from x1 and x2,
         matching hazard.evaluate()'s own treatment (single definition rule).
      4. For each vighna in the chart: evaluate u_m(t) at each knot.

    The evaluator must have horizon_days == event_horizon_days for a consistent
    knot set (the horizon end is always included in K).

    Args:
        evaluator: FieldEvaluator for any event class (chart-level data is the
                   same regardless of class — that is the whole point of Layer 0).
        event_horizon_days: the build horizon (should equal evaluator.horizon_days).

    Returns:
        A frozen Layer0 instance holding all chart-level arrays.
    """
    import bisect

    # ── Step 1: build knot set ────────────────────────────────────────────────
    K = assemble_knot_set_with_decade_seams(evaluator)
    N_k = len(K)

    # ── Step 2: lord stacks — (system_id, level) → lord array ────────────────
    #
    # We use the same binary-search structure FieldEvaluator._ladder_bsearch
    # pre-built for lord_stacks_at(), but sweep once over all knots instead
    # of calling lord_stacks_at() N_k times (O(N_k * N_levels * log N) total
    # vs. N_k separate calls each doing the same work).
    #
    # Result: lord_stacks[(system_id, level)] = str ndarray, '' when no lord.
    lord_stacks: dict[tuple[str, str], np.ndarray] = {}

    for sid, levels_data in evaluator._ladder_bsearch.items():
        for level, lvl_t_starts, lvl_t_ends, lvl_lords in levels_data:
            key = (sid, level)
            arr = np.empty(N_k, dtype=object)
            arr[:] = ''
            for k_idx, t_val in enumerate(K):
                t = float(t_val)
                idx = bisect.bisect_right(lvl_t_starts, t) - 1
                if idx >= 0 and lvl_t_ends[idx] > t:
                    arr[k_idx] = lvl_lords[idx]
            lord_stacks[key] = arr

    # ── Step 3: covariates — shape (12, N_k) ─────────────────────────────────
    #
    # Row j = COVARIATE_KEYS[j] value at each knot.
    # x3 (dual_reference_agreement = min(x1,x2)) is derived after x1 and x2
    # are filled, matching hazard.evaluate()'s single-definition discipline.
    covariates = np.zeros((12, N_k), dtype=np.float64)
    envelopes = evaluator.envelopes

    for k_idx, t_val in enumerate(K):
        t = float(t_val)
        cov_dict = envelopes.covariates_at(t)
        for j, key in enumerate(COVARIATE_KEYS):
            if key == 'dual_reference_agreement':
                # Derived from x1, x2 already set — same rule as hazard.evaluate.
                covariates[j, k_idx] = derive_dual_reference_agreement(cov_dict)
            else:
                covariates[j, k_idx] = cov_dict.get(key, 0.0)

    # ── Step 4: obstructions — vighna_key → u_m(t) array ────────────────────
    #
    # Store ALL chart-level vighna instances. Per-class SM-R-7 filtering is
    # Layer 1's responsibility (DHARA_ENGINE_SPEC §2.2 / SM-R-7 OPTION B).
    # A class that references no vighna keys gets filtered_obs = {} in Layer 1
    # and S_e(t) = 1.0.
    obstructions: dict[str, np.ndarray] = {}

    # Collect all vighna keys present in the chart.
    all_vighna_keys = sorted(
        p.vighna_key() for p in envelopes.obstructive
    )
    # Use the obstruction_sources index for O(1) per-primitive lookup.
    obs_sources = envelopes.obstruction_sources()

    for vighna_key in all_vighna_keys:
        if vighna_key not in obs_sources:
            continue
        prim = obs_sources[vighna_key]
        arr = np.zeros(N_k, dtype=np.float64)
        for k_idx, t_val in enumerate(K):
            t = float(t_val)
            v = prim.value_at(t)
            if v > 0.0:
                arr[k_idx] = v
        obstructions[vighna_key] = arr

    return Layer0(
        knots=K,
        lord_stacks=lord_stacks,
        covariates=covariates,
        obstructions=obstructions,
    )


__all__ = [
    'Layer0',
    'assemble_knot_set_with_decade_seams',
    'compute_layer0',
]
