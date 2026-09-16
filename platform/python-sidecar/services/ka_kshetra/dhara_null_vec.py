"""Compatibility and arithmetic helpers for the DHARA null engine.

SM-R-11 superseded the historical per-replicate segment implementation with
the C(t)/E(t) decomposition in :mod:`services.ka_kshetra.dhara_null`. The
public ``dhara_compute_null_vec`` name remains as a compatibility entry point
and delegates exactly to that accepted implementation. The NumPy cumulative
and sliding-window helpers remain independently tested utilities.
"""
from __future__ import annotations

import math

import numpy as np

from services.ka_kshetra.contracts import NullResult
from services.ka_kshetra.stage4_field import FieldEvaluator

# ── public constants ──────────────────────────────────────────────────────────

#: SM-R-8 MANDATE (restored): R=1024. OPT-N3 R=256 is VOIDED.
#: The vectorized implementation eliminates the per-replicate Python loop
#: overhead that made 1024 replicates infeasible with the serial engine.
DEFAULT_REPLICATES: int = 1024

#: Same exceedance threshold as dhara_null.py and stage5_null.py.
DEFAULT_ALPHA: float = 0.05


# ── vectorized sliding-window maximum ────────────────────────────────────────

def _vec_sliding_window_max(cum: np.ndarray, bucket_days: int) -> float:
    """M(L) = max over all t on the 1-day grid of Λ(t, t+L).

    Vectorized: Λ(t, t+L) = cum[t+L] − cum[t] computed as a numpy slice
    subtraction. This is exact and matches the serial sliding_window_max
    in stage5_null.py output value for value.

    Parameters
    ----------
    cum : np.ndarray, shape (N+1,)
        Cumulative integral at each grid point, as returned by
        _cumulative_on_grid_numpy.
    bucket_days : int
        Duration bucket L in days.

    Returns
    -------
    float
        Max windowed cumulative integral over width L.
    """
    n = len(cum) - 1
    if bucket_days >= n:
        # Bucket longer than horizon: return total integral (honest maximum).
        return float(cum[-1] - cum[0])
    # Vectorized slice subtraction: all windows of width bucket_days at once.
    windows = cum[bucket_days:] - cum[:n - bucket_days + 1]
    return float(np.max(windows))


def _cumulative_on_grid_numpy(
    segments,
    horizon_days: float,
    grid_step: float = 1.0,
) -> np.ndarray:
    """Λ(0, t) at every grid point, returned as a numpy float64 array.

    Semantics identical to stage5_null.cumulative_on_grid but returns
    np.ndarray instead of list[float], enabling numpy vectorized diff and
    sliding-window operations without a list→array conversion step.

    O(N_grid + N_seg) pointer-advance, same algorithm as cumulative_on_grid.
    """
    from services.ka_kshetra import integrator

    n = int(round(horizon_days / grid_step))
    cum = np.zeros(n + 1, dtype=np.float64)
    if not segments:
        return cum
    running = 0.0
    n_segs = len(segments)
    j = 0  # pointer: first segment that might overlap [a, b)
    for k in range(n):
        a = k * grid_step
        b = a + grid_step
        # Advance j past segments that end at or before a.
        while j < n_segs and segments[j].t_end <= a:
            j += 1
        # Sum contributions from all segments overlapping [a, b).
        i = j
        while i < n_segs and segments[i].t_start < b:
            u = max(a, segments[i].t_start)
            v = min(b, segments[i].t_end)
            if v > u:
                running += integrator.segment_integral(segments[i], u, v)
            i += 1
        cum[k + 1] = running
    return cum


# ── main entry point ──────────────────────────────────────────────────────────

def dhara_compute_null_vec(
    evaluator: FieldEvaluator,
    R: int = DEFAULT_REPLICATES,
    alpha: float = DEFAULT_ALPHA,
    coarse_mode: bool = True,
) -> NullResult:
    """Compatibility entry point for the accepted C/E-vectorized engine.

    SM-R-11 superseded this module's per-replicate segment construction with
    :func:`dhara_compute_null`, which precomputes C(t) and E(t) once and performs
    only NumPy shifts in the replicate loop. Delegation keeps callers of the
    historical ``R``-named API byte-for-byte aligned with the active writer
    path, including R-1 shifts, 1/R resolution and the fixed-clock/shifted-sky
    null hypothesis.
    """
    from services.ka_kshetra.dhara_null import dhara_compute_null

    return dhara_compute_null(
        evaluator,
        replicates=R,
        alpha=alpha,
        coarse_mode=coarse_mode,
    )


__all__ = [
    'DEFAULT_REPLICATES',
    'DEFAULT_ALPHA',
    'dhara_compute_null_vec',
]
