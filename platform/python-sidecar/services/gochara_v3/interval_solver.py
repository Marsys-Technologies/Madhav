"""
gochara_v3.interval_solver — Root-solved interval and chain production (W3.2).

Replaces the v1 daily-chunk-continuity machinery with:
  1. INTERVALS: Bisection root-solver finds exact JD where lambda_v3 crosses
     the activation threshold. Peak = numerical argmax over the active interval.
  2. CHAINS: One IntensityResult per milestone in `milestone_template`, each
     evaluated at that milestone's own JD (episode anchor + typical_offset_days).

I2: This module is in gochara_v3/ — it does NOT modify gochara_grammar/*,
gochara_intensity/*, or ka_gochara_sweep/*.

I4: Honest gaps — if a class has no `milestone_template`, chain output returns
an honest empty result (never fabricated milestones).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from .engine import evaluate_lambda_vector
from .threshold import ThresholdConfig, is_above_threshold

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Generation-scoping constant
# ---------------------------------------------------------------------------

# era_slice_key for all v3-Utkarsha rows (migration 556 column).
ERA_SLICE_KEY_V3: str = "g3_utkarsha"

# Default bisection tolerance in days: root-solve enter/exit to within 0.1 days.
_BISECT_TOL_DAYS: float = 0.1

# Dense sampling count within an active interval for peak detection.
_PEAK_SAMPLE_COUNT: int = 50


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class IntervalBoundary:
    """A detected interval where lambda_v3 is above threshold.

    Fields
    ------
    enter_jd        Exact JD where lambda_v3 crosses threshold upward (bisected).
    exit_jd         Exact JD where lambda_v3 crosses threshold downward (bisected).
    peak_jd         JD of lambda_v3 maximum within [enter_jd, exit_jd].
    peak_lambda     lambda_v3 value at peak_jd.
    era_slice_key   Generation-scoping key (always ERA_SLICE_KEY_V3 for v3 rows).
    term_breakdown  PARIṢKĀRA MR-14 fix: the full W1.5 per-mechanism λ_v3
                    decomposition ({promise, permission, activity,
                    quality_gates, lambda_v3, activity_terms, formula}) at
                    peak_jd -- the single most representative instant for
                    this window (mirrors peak_basis='gochara_lambda_v3').
                    `evaluate_lambda_vector`/`_evaluate_single_from_context`
                    (gochara_v3.engine) already computes this correctly on
                    every IntensityResult; prior to this fix, this module
                    discarded it by only ever reading `.raw_lambda` via
                    `_eval_single` during the coarse sweep/bisection/peak
                    search. None ONLY on an honest evaluation failure at
                    peak_jd (I4) -- never silently dropped when the peak
                    evaluation succeeds.
    lambda_v3_ci_low   80% credible-interval lower bound at peak_jd (structural
                       prior band; see IntensityResult docstring). None on I4
                       degrade, matching term_breakdown.
    lambda_v3_ci_high  80% credible-interval upper bound at peak_jd. None on
                       I4 degrade.
    ci_source          'structural_prior' | 'fitted_posterior' disclosure tag
                       from the peak IntensityResult. None on I4 degrade.
    """
    enter_jd: float
    exit_jd: float
    peak_jd: float
    peak_lambda: float
    era_slice_key: str
    term_breakdown: Optional[dict] = None
    lambda_v3_ci_low: Optional[float] = None
    lambda_v3_ci_high: Optional[float] = None
    ci_source: Optional[str] = None


@dataclass
class MilestoneScore:
    """One milestone in a chain-shaped event class.

    Fields
    ------
    milestone_id                Identifier from the milestone_template entry.
    milestone_jd                episode_anchor_jd + typical_offset_days.
    lambda_v3                   raw_lambda from the engine at milestone_jd.
    is_above_threshold          Whether lambda_v3 meets the activation threshold.
    is_irreversibility_milestone Flag from the milestone_template entry.
    intensity_result            Full IntensityResult from the engine (or None if
                                evaluation failed — I4 honest gap).
    """
    milestone_id: str
    milestone_jd: float
    lambda_v3: float
    is_above_threshold: bool
    is_irreversibility_milestone: bool
    intensity_result: Any  # IntensityResult | None


# ---------------------------------------------------------------------------
# Internal helper: evaluate lambda_v3 at a single JD
# ---------------------------------------------------------------------------

def _eval_single(swe, context, jd: float) -> float:
    """Evaluate lambda_v3 at a single JD.

    Calls evaluate_lambda_vector with a one-element array and returns the
    raw_lambda of the result. Returns 0.0 on any exception (honest degrade).

    Note: evaluate_lambda_vector is imported at module level so tests can
    patch services.gochara_v3.interval_solver.evaluate_lambda_vector.
    """
    try:
        results = evaluate_lambda_vector(
            swe, context, np.array([float(jd)]), v1_parity_mode=False,
        )
        if results:
            return float(results[0].raw_lambda)
        return 0.0
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "[gochara_v3.interval_solver] _eval_single failed at jd=%.4f: %s", jd, exc,
        )
        return 0.0


def _eval_single_full(swe, context, jd: float):
    """Evaluate lambda_v3 at a single JD and return the full IntensityResult.

    Returns None on any exception (I4: honest gap).
    """
    try:
        results = evaluate_lambda_vector(
            swe, context, np.array([float(jd)]), v1_parity_mode=False,
        )
        if results:
            return results[0]
        return None
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "[gochara_v3.interval_solver] _eval_single_full failed at jd=%.4f: %s", jd, exc,
        )
        return None


# ---------------------------------------------------------------------------
# Bisection root-solver
# ---------------------------------------------------------------------------

def _bisect_crossing(
    swe,
    context,
    jd_low: float,
    jd_high: float,
    threshold_config: ThresholdConfig,
    *,
    tol_days: float = _BISECT_TOL_DAYS,
    target_above: bool,
) -> float:
    """Bisect [jd_low, jd_high] to find where lambda_v3 crosses the threshold.

    target_above=True  → find JD where lambda transitions BELOW→ABOVE threshold
                         (jd_low has lambda below, jd_high has lambda above).
    target_above=False → find JD where lambda transitions ABOVE→BELOW threshold
                         (jd_low has lambda above, jd_high has lambda below).

    Returns the bisected crossing JD (midpoint of the final converged interval).
    """
    lo, hi = jd_low, jd_high
    max_iters = 100  # safety cap; converges in log2((hi-lo)/tol) iterations
    for _ in range(max_iters):
        if (hi - lo) < tol_days:
            break
        mid = 0.5 * (lo + hi)
        mid_lambda = _eval_single(swe, context, mid)
        mid_above = is_above_threshold(mid_lambda, threshold_config)
        if mid_above == target_above:
            # mid is on the same side as the target-side → crossing is between [lo, mid]
            hi = mid
        else:
            # mid is on the opposite side → crossing is between [mid, hi]
            lo = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# Public API: find_threshold_crossings
# ---------------------------------------------------------------------------

def find_threshold_crossings(
    swe,
    context,
    start_jd: float,
    end_jd: float,
    threshold_config: ThresholdConfig,
    *,
    coarse_step_days: float = 7.0,
    bisect_tol_days: float = _BISECT_TOL_DAYS,
    return_series: bool = False,
):
    """Find all intervals where lambda_v3 is above the activation threshold.

    Algorithm
    ---------
    1. Evaluate lambda_v3 at coarse weekly (or `coarse_step_days`) intervals
       across [start_jd, end_jd].
    2. Identify consecutive pairs where the threshold is crossed (sign change
       in is_above_threshold).
    3. For each upward crossing (below→above): bisect to find enter_jd.
       For each downward crossing (above→below): bisect to find exit_jd.
    4. Within each [enter_jd, exit_jd] interval, sample densely to find
       peak_jd and peak_lambda.
    5. Return a list of IntervalBoundary (empty if lambda never exceeds the
       threshold across the full range).

    Parameters
    ----------
    swe               Swiss Ephemeris handle.
    context           ClassContext (pre-fetched, immutable).
    start_jd          Start of search range (Julian Day).
    end_jd            End of search range (Julian Day).
    threshold_config  ThresholdConfig from W1.4 (carries lambda_thresh).
    coarse_step_days  Coarse grid spacing in days (default 7 = weekly).
    bisect_tol_days   Bisection convergence tolerance in days (default 0.1).
    return_series     PARIṢKĀRA MR-11(b)/PK-R-8 (R8.2): when True, ALSO
                      return the (jd_series, lambdas) coarse-sweep arrays
                      this function already computes in step 1 below, as
                      `(intervals, jd_series, lambdas)`. Default False
                      preserves the original `list[IntervalBoundary]`-only
                      return for every pre-existing caller (test_w32/mr14/
                      mr23 and others call this positionally/without this
                      kwarg and must see byte-identical behavior). This flag
                      exists so `resolution_hierarchy.build_resolution_
                      hierarchy` can REUSE this exact coarse sweep for its
                      peak-anchoring scan (R8.2) instead of re-sweeping —
                      the series is computed once, here, regardless of which
                      return shape the caller asked for.

    Returns
    -------
    If return_series is False (default): list[IntervalBoundary] — one entry
    per detected above-threshold interval, sorted by enter_jd. Empty list
    when lambda is always below the threshold.
    If return_series is True: (intervals, jd_series, lambdas) — the same
    list plus the raw numpy coarse-sweep arrays (both empty arrays if the
    range/step produced no samples).
    """
    if end_jd <= start_jd:
        logger.debug(
            "[gochara_v3.interval_solver] find_threshold_crossings: "
            "end_jd (%.4f) <= start_jd (%.4f) — returning []", end_jd, start_jd,
        )
        if return_series:
            return [], np.array([]), np.array([])
        return []

    # 1. Coarse sweep
    jd_series = np.arange(start_jd, end_jd, coarse_step_days)
    if len(jd_series) == 0:
        if return_series:
            return [], jd_series, np.array([])
        return []

    # Evaluate lambda at all coarse points
    lambdas = np.array([_eval_single(swe, context, jd) for jd in jd_series])
    above_flags = np.array(
        [is_above_threshold(lam, threshold_config) for lam in lambdas],
        dtype=bool,
    )

    # 2. Detect sign-change intervals
    intervals: list[IntervalBoundary] = []
    i = 0
    n = len(above_flags)

    while i < n:
        if not above_flags[i]:
            i += 1
            continue

        # Found a segment that starts above threshold at index i.
        # If i > 0, bisect [i-1, i] to get precise enter_jd.
        if i > 0:
            enter_jd = _bisect_crossing(
                swe, context,
                jd_low=float(jd_series[i - 1]),
                jd_high=float(jd_series[i]),
                threshold_config=threshold_config,
                tol_days=bisect_tol_days,
                target_above=True,
            )
        else:
            # Series starts above threshold — enter_jd is at the series start
            enter_jd = float(jd_series[0])

        # Find where the segment ends
        j = i
        while j < n and above_flags[j]:
            j += 1

        # j is now the first index below threshold (or past the end).
        if j < n:
            # Bisect [j-1, j] to get precise exit_jd.
            exit_jd = _bisect_crossing(
                swe, context,
                jd_low=float(jd_series[j - 1]),
                jd_high=float(jd_series[j]),
                threshold_config=threshold_config,
                tol_days=bisect_tol_days,
                target_above=False,
            )
        else:
            # Series ends above threshold — exit_jd is at the series end
            exit_jd = float(jd_series[-1])

        # 3. Find peak within [enter_jd, exit_jd] via dense sampling
        peak_jd, peak_lambda = _find_peak(
            swe, context, enter_jd, exit_jd,
            sample_count=_PEAK_SAMPLE_COUNT,
        )

        # PARIṢKĀRA MR-14 fix: capture the full W1.5 per-mechanism decomposition
        # at peak_jd -- one extra evaluate_lambda_vector call per DETECTED
        # interval (not per coarse/bisection/dense-sampling point), using
        # _eval_single_full so the IntensityResult's term_breakdown/CI fields
        # survive instead of being discarded (the prior defect: every call
        # site in this function used _eval_single, which returns only a bare
        # float). Honest None on evaluation failure (I4) -- never fabricated.
        peak_result = _eval_single_full(swe, context, peak_jd)
        if peak_result is not None:
            term_breakdown = peak_result.term_breakdown
            lambda_v3_ci_low = peak_result.lambda_v3_ci_low
            lambda_v3_ci_high = peak_result.lambda_v3_ci_high
            ci_source = peak_result.ci_source
        else:
            term_breakdown = None
            lambda_v3_ci_low = None
            lambda_v3_ci_high = None
            ci_source = None

        intervals.append(IntervalBoundary(
            enter_jd=enter_jd,
            exit_jd=exit_jd,
            peak_jd=peak_jd,
            peak_lambda=peak_lambda,
            era_slice_key=ERA_SLICE_KEY_V3,
            term_breakdown=term_breakdown,
            lambda_v3_ci_low=lambda_v3_ci_low,
            lambda_v3_ci_high=lambda_v3_ci_high,
            ci_source=ci_source,
        ))

        i = j  # continue scanning after this segment

    if return_series:
        return intervals, jd_series, lambdas
    return intervals


def _find_peak(
    swe,
    context,
    enter_jd: float,
    exit_jd: float,
    *,
    sample_count: int = _PEAK_SAMPLE_COUNT,
) -> tuple[float, float]:
    """Find the peak lambda_v3 within [enter_jd, exit_jd] via dense sampling.

    Returns (peak_jd, peak_lambda).
    """
    if exit_jd <= enter_jd:
        # Degenerate interval: evaluate at the single point
        lam = _eval_single(swe, context, enter_jd)
        return enter_jd, lam

    dense_jds = np.linspace(enter_jd, exit_jd, max(2, sample_count))
    dense_lambdas = np.array([_eval_single(swe, context, jd) for jd in dense_jds])

    peak_idx = int(np.argmax(dense_lambdas))
    return float(dense_jds[peak_idx]), float(dense_lambdas[peak_idx])


# ---------------------------------------------------------------------------
# Public API: score_chain_milestones
# ---------------------------------------------------------------------------

def score_chain_milestones(
    swe,
    context,
    episode_anchor_jd: float,
    milestone_template: list[dict],
    threshold_config: ThresholdConfig,
) -> list[MilestoneScore]:
    """Score each milestone in a chain-shaped event class at its own JD.

    Each milestone is evaluated at:
        milestone_jd = episode_anchor_jd + milestone['typical_offset_days']

    This is genuine per-milestone evaluation — not a copy of the episode-level
    score. If a milestone has a different temporal phase (e.g. an irreversibility
    point months after the onset), it is evaluated at THAT phase's JD.

    I4 contract: if milestone_template is empty, returns [] honestly.
    No milestones are fabricated when the template has no entries.

    Parameters
    ----------
    swe                  Swiss Ephemeris handle.
    context              ClassContext (pre-fetched, immutable).
    episode_anchor_jd    JD of the episode's reference anchor (e.g. onset).
    milestone_template   List of dicts, each with:
                           milestone_id: str
                           typical_offset_days: float (offset from anchor)
                           is_irreversibility_milestone: bool
    threshold_config     ThresholdConfig (lambda_thresh for gating).

    Returns
    -------
    list[MilestoneScore] — one per milestone in template, in template order.
    Empty list when milestone_template is empty (I4: honest null).
    """
    if not milestone_template:
        # I4: honest empty result — never fabricate milestones
        return []

    scores: list[MilestoneScore] = []

    for entry in milestone_template:
        milestone_id = str(entry.get("milestone_id", "unknown"))
        typical_offset_days = float(entry.get("typical_offset_days", 0.0))
        is_irrev = bool(entry.get("is_irreversibility_milestone", False))

        milestone_jd = episode_anchor_jd + typical_offset_days

        # Evaluate at this milestone's own JD (genuine per-milestone evaluation)
        intensity_result = _eval_single_full(swe, context, milestone_jd)

        if intensity_result is not None:
            lam = float(intensity_result.raw_lambda)
        else:
            # Honest gap: evaluation failed — lambda is unknown, treat as 0.0
            lam = 0.0

        above = is_above_threshold(lam, threshold_config)

        scores.append(MilestoneScore(
            milestone_id=milestone_id,
            milestone_jd=milestone_jd,
            lambda_v3=lam,
            is_above_threshold=above,
            is_irreversibility_milestone=is_irrev,
            intensity_result=intensity_result,
        ))

    return scores


__all__ = [
    "ERA_SLICE_KEY_V3",
    "IntervalBoundary",
    "MilestoneScore",
    "find_threshold_crossings",
    "score_chain_milestones",
]
