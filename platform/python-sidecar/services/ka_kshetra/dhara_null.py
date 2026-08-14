"""
services/ka_kshetra/dhara_null.py — DHARA vectorized 1024-replicate null distribution.

DHARA NULL DESIGN (§6, DHARA_DESIGN_v1_0.md)
─────────────────────────────────────────────
This module implements the DHARA variant of the circular-shift null distribution
(`stage5_null.py`). Key differences from the 256-replicate engine:

1. R=1024 replicates (native ruling n3).

2. F-01 CORRECTION — shift grid uses range(1, R), not range(1, R+1):
   When r=R, delta = R*(H/R) = H, and circular_shift's `delta % H = 0` returns
   an unshifted index IDENTICAL to the real field. This double-counts the
   observation in the p-value formula and inflates the minimum achievable p from
   1/(R+1) to 2/(R+1). The correct grid uses range(1, R), yielding R-1=1023
   independent replicates with p-value resolution 1/1024 (observation + 1023
   shifts = 1024 denominator). This corrects a pre-existing bug in stage5_null.py's
   256-replicate engine (range(1, 257) has the same defect).

3. coarse_mode=True (default): uses MD/AD/PD ladder boundaries only (~819 knots),
   the same L1g optimization as stage5_null.py, keeping each replicate affordable.
   Set coarse_mode=False to merge the full K_c (all levels) into the knot set.

4. The envelope knot set K_e is shifted per-replicate using np.mod for O(|K_e|)
   cost; then merged with K_c via np.unique(np.concatenate(...)) for O(|K_r| log |K_r|).

── NULL HYPOTHESIS (inherited from stage5_null.py) ──────────────────────────
The TRANSIT STREAM is circularly shifted. The NATAL STRUCTURE and the DAŚĀ
LADDER are held FIXED. That asymmetry IS the null hypothesis:
  "the sky's timing carries no information about this chart's events
   beyond what the clocks already say."

── DETERMINISM ───────────────────────────────────────────────────────────────
No RNG anywhere. The shift grid δ_r = r*(H/R) for r = 1…R-1 is COMPUTED, not
drawn. Hash-replay must hold (§7.4 field design), and a computed grid has no seed
that could flatter a result.

── p-VALUE AND RESOLUTION ────────────────────────────────────────────────────
    null_p          = (1 + #{r : M_r(L*) >= Lambda_obs}) / (R + 1)
    null_resolution = 1 / R = 1/1024

The 1/R resolution follows from the F-01-corrected grid: R-1 independent shifts
+ 1 observation = R denominator entries, giving minimum achievable p = 1/R.
(Note: stage5_null.py uses R+1 denominator with its R=256 full grid; here the
denominator is R because the grid has R-1 shifts, not R.)

Authority: DHARA_DESIGN_v1_0.md §6.1–§6.6.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from services.ka_kshetra.contracts import NullResult
from services.ka_kshetra.stage4_field import EnvelopeIndex, FieldEvaluator
from services.ka_kshetra.stage5_null import (
    DURATION_BUCKETS,
    QuantilePool,
    Q_QUANTILE,
    sliding_window_max,
)

# ── public constants ──────────────────────────────────────────────────────────

#: SM-R-8 MANDATE (restored): R=1024. OPT-N3 R=256 is VOIDED.
#: The serial dhara_compute_null is retained for backward-compatibility and as
#: the reference implementation for equivalence testing. Under
#: ENGINE_VERSION='analytic', writer.py routes to dhara_compute_null_vec
#: (dhara_null_vec.py) which eliminates the per-replicate Python loop and runs
#: within idle_in_transaction_session_timeout=900000ms (FM-24).
#: The F-01-corrected shift grid uses range(1, R), giving R-1=1023
#: independent shifts. p-value resolution = 1/R = 1/1024.
DEFAULT_REPLICATES: int = 1024

#: Same exceedance threshold as stage5_null.py.
DEFAULT_ALPHA: float = 0.05


# NullResult is defined in contracts.py (P0.b, 2026-08-14) — single canonical
# frozen type shared across writer.py and all consumers.  Imported above.


# ── main entry point ──────────────────────────────────────────────────────────

def dhara_compute_null(
    evaluator: FieldEvaluator,
    replicates: int = DEFAULT_REPLICATES,
    alpha: float = DEFAULT_ALPHA,
    coarse_mode: bool = True,
) -> NullResult:
    """Compute the DHARA null distribution via circular-shift replicates.

    F1 (SM-R-11): C/E DECOMPOSITION — ZERO evaluator calls in the replicate loop.
    ─────────────────────────────────────────────────────────────────────────────
    The identity ln λ_r(t) = C(t) + E((t−δ_r) mod H) is exploited:

    C(t): clock/lord/promise contribution only — precomputed ONCE on a 1-day
          midpoint grid using a clock-only evaluator built with EnvelopeIndex([],H).
          EnvelopeIndex with empty primitives returns {} from covariates_at and
          obstructions_at, so hazard.evaluate produces only clock/promise terms.
    E(t): envelope contribution = ev.ln_lambda(t) − C(t) — precomputed ONCE.

    Total precomputation: 2·n evaluator calls (n = int(H) = 36,525 for a
    100-year horizon, ~4–8 s).  Previous approach: 819 calls PER replicate
    × 1,023 replicates = 838,937 calls → 90+ min/class (RC-1, SM-R-11 RCA).

    Each replicate r performs a vectorized circular shift of E_fine by
    δ_r = r·H/R using modular index arithmetic and linear interpolation
    (O(n) NumPy ops, zero evaluator calls), then:
        lam   = exp(C_fine + E_shifted)          # per-day approximate integral
        cum   = [0] + cumsum(lam)                # cumulative hazard on 1-day grid
        stats = sliding_window_max(cum, bucket)  # per-bucket max

    Parameters
    ----------
    evaluator : FieldEvaluator
        The real (unshifted) field evaluator for this (chart, event_class).
    replicates : int
        R value. Default 1024. Shift grid uses range(1, R) → R-1=1023
        independent shifts (F-01 correction).
    alpha : float
        Exceedance threshold (default 0.05). Stored in NullResult; the null
        distribution itself is threshold-agnostic.
    coarse_mode : bool
        Accepted for API compatibility; not used. The 1-day grid is used for
        all modes and is coarser than any clock-knot ladder subset.
    """
    if replicates < 2:
        raise ValueError(f'replicates must be >= 2, got {replicates!r}')
    if not (0.0 < alpha < 1.0):
        raise ValueError(f'alpha must be in (0, 1), got {alpha!r}')

    H = evaluator.horizon_days
    if not (H > 0):
        raise ValueError(f'evaluator.horizon_days must be > 0, got {H!r}')

    n = int(round(H))  # 1-day grid size: 36,525 for a 100-year horizon
    # Midpoint grid: avoids evaluating exactly on dasa-boundary discontinuities.
    t_grid = np.arange(n, dtype=np.float64) + 0.5  # 0.5, 1.5, …, H-0.5

    # ── F1: precompute C and E grids ONCE (2·n evaluator calls total) ─────────
    # Clock-only evaluator: EnvelopeIndex([], H) → covariates_at → {} and
    # obstructions_at → {} → C(t) = clock/promise/lord terms only.
    clock_ev = FieldEvaluator(
        event_class=evaluator.event_class,
        lifetime_count=evaluator.lifetime_count,
        promise=evaluator.promise,
        clocks=evaluator.clocks,
        ladder=evaluator.ladder,
        envelopes=EnvelopeIndex([], H),
        weights=evaluator.weights,
        horizon_days=H,
        baseline_source=evaluator.baseline_source,
        extra_breakpoints=evaluator.extra_breakpoints,
    )
    C_fine = np.fromiter(
        (clock_ev.ln_lambda(t) for t in t_grid), dtype=np.float64, count=n
    )
    full_fine = np.fromiter(
        (evaluator.ln_lambda(t) for t in t_grid), dtype=np.float64, count=n
    )
    E_fine = full_fine - C_fine  # envelope-only contribution, shape (n,)

    # ── accumulators ─────────────────────────────────────────────────────────
    shift_step = H / replicates
    # F-01: range(1, replicates) — R-1=1023 independent shifts.
    # Max delta = (R-1)·(H/R) = H·(1−1/R) < H, so the last shift never
    # wraps to H (which would yield the identity, double-counting the observation).
    n_shifts = replicates - 1

    pool = QuantilePool(quantile=Q_QUANTILE, expected_total=n_shifts * n)
    all_stats: dict[int, dict[int, float]] = {int(b): {} for b in DURATION_BUCKETS}

    for r in range(1, replicates):  # F-01: range(1, R)
        delta = r * shift_step

        # ── vectorized circular shift of E — zero evaluator calls ─────────────
        # E_shifted[k] ≈ E_fine at source time (t_grid[k] − delta) mod H.
        # t_grid[k] = k + 0.5, so source midpoint index = (k + 0.5 − delta) mod H.
        src_idx = (t_grid - delta) % H   # fractional index in [0, H) = [0, n)
        i_low = np.floor(src_idx).astype(np.intp) % n
        i_high = (i_low + 1) % n
        frac = src_idx - np.floor(src_idx)
        E_shifted = E_fine[i_low] * (1.0 - frac) + E_fine[i_high] * frac

        # ── cumulative hazard on 1-day grid ───────────────────────────────────
        lam = np.exp(C_fine + E_shifted)   # per-day approximate integral, O(n)
        cum = np.empty(n + 1, dtype=np.float64)
        cum[0] = 0.0
        cum[1:] = np.cumsum(lam)

        # ── sliding-window max for each duration bucket ───────────────────────
        replicate_idx = r - 1  # 0-indexed
        for b in DURATION_BUCKETS:
            all_stats[int(b)][replicate_idx] = sliding_window_max(cum, int(b))

        # ── pool lambda values for q_e quantile ──────────────────────────────
        pool.add(lam)  # lam ≡ np.diff(cum); avoids recomputing the differences

    # ── finalize ──────────────────────────────────────────────────────────────
    ordered_stats: dict[int, list[float]] = {
        int(b): [all_stats[int(b)][i] for i in range(n_shifts)]
        for b in DURATION_BUCKETS
    }
    return NullResult(
        replicates=replicates,
        shift_count=n_shifts,
        horizon_days=H,
        shift_grid_step=shift_step,
        q_threshold=pool.value(),
        max_stats=ordered_stats,
        alpha=alpha,
    )


__all__ = [
    'DEFAULT_REPLICATES',
    'DEFAULT_ALPHA',
    'NullResult',
    'dhara_compute_null',
]
