"""
gochara_v3.resolution_hierarchy — Multi-resolution window hierarchy (W3.3,
PARIṢKĀRA MR-11(b), ADJUDICATOR ruling PK-R-8).

Resolution tiers (coarsest to finest):
  era       One find_threshold_crossings interval (any duration) — the
            CONTEXT container within which peaks are anchored. Per PK-R-1,
            an era-tier row is CONTEXT, never a timing claim on its own.
  month     A peak-anchored calendar month, clipped to its era window.
  day       The single calendar date of a peak-anchored window's
            day-refined true peak.
  muhurta   Lazily computed on demand (Tier-C Moon-based; NOT built here).

PK-R-8 (native ADJUDICATOR ruling, binding) REPLACED the original W3.3
tiling design (fixed 30-day/1-day step subdivision with a midpoint-sampled
"peak") with PEAK-ANCHORING:
  R8.1  No tiling anywhere — month/day windows exist ONLY as children of a
        genuine local-maximum scan, never a fixed-step subdivision.
  R8.2  The peak scan REUSES the coarse series find_threshold_crossings
        already computes for era detection (via `return_series=True`) — no
        second ephemeris sweep.
  R8.3  Admission: a candidate peak is admitted iff its λ >= the ERA
        WINDOW'S OWN P90 (never lambda_thresh — that would make admission
        externally gate-dependent instead of a property of this window's
        own λ distribution). A flat/constant series admits nothing.
  R8.4  Retention: rank (λ DESC, jd ASC), greedy-retain enforcing
        MIN_PEAK_SEPARATION_DAYS, capped at MAX_PEAKS_PER_ERA_WINDOW.
        MR-44 AMENDMENT (2026-08-11, register MASTER_REMEDIATION_
        REGISTER_v2_0.md): when one decade slice genuinely produces
        MULTIPLE era windows (find_threshold_crossings returning >=2
        intervals — a real, observed production condition), retention now
        runs ONCE, POOLED, across ALL of that call's era windows —
        MIN_PEAK_SEPARATION_DAYS is enforced GLOBALLY, never per-interval
        only. Rationale: two peaks admitted from two DIFFERENT era windows
        could each trivially clear their own interval's within-interval
        separation check (nothing else in that interval to collide with)
        yet independently day-refine (R8.5) to the IDENTICAL calendar
        date — a duplicate row on uq_kala_gochara_windows_v2_natural_key
        (chart_id, event_class, window_start, peak_date, milestone_id,
        generation). MAX_PEAKS_PER_ERA_WINDOW stays a PER-ERA-WINDOW cap
        (register MR-44's ruled interpretation of PK-R-8 R8.4: "cap at
        MAX_PEAKS_PER_ERA_WINDOW per era window as before") — only the
        SEPARATION check widens to global scope. See
        retain_candidates_pooled.
  R8.5  Day refinement: each retained candidate is re-sampled at 1-day
        resolution over a ±7-day window around it; the TRUE argmax (not
        the coarse candidate) is what peak_date is stamped with, on BOTH
        the month and day rows.
  R8.6  Exactly one month row (the calendar month containing the true
        peak, clipped to the era window) + one day row (a single date)
        PER RETAINED PEAK. Zero retained peaks -> zero month/day rows, no
        fallback fabrication.

I2: zero imports from gochara_grammar/*, gochara_intensity/*, ka_gochara_sweep/*.
"""
from __future__ import annotations

import datetime as _dt
import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .interval_solver import find_threshold_crossings, _eval_single
from .threshold import ThresholdConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolution tier constants
# ---------------------------------------------------------------------------

# Ordered coarsest-to-finest. Index position defines tier ordering.
RESOLUTION_TIERS: tuple[str, ...] = ("era", "month", "day", "muhurta")

# Orbital periods in days for slow bodies historically associated with
# era-scale activation (documentation only — no longer used to CLASSIFY a
# window's tier; every find_threshold_crossings interval is an "era" window
# under PK-R-8, regardless of its own duration. Retained as a reference for
# readers reasoning about WHY era-scale windows tend to be multi-year).
ERA_BODIES: dict[str, float] = {
    "Saturn": 28.45 * 365.25,   # 10,392 days ≈ 28.45 years
    "Jupiter": 11.86 * 365.25,  # 4,332 days ≈ 11.86 years
    "Rahu": 18.61 * 365.25,     # 6,793 days ≈ 18.61 years
    "Ketu": 18.61 * 365.25,     # 6,793 days ≈ 18.61 years (same period as Rahu)
}

# R8.2: the coarse-scan stride REUSED from find_threshold_crossings — this
# constant is passed as `coarse_step_days` to find_threshold_crossings AND
# is the stride the reused series was sampled at, so peak-anchoring never
# assumes a different grid than the one actually computed.
PEAK_SCAN_STRIDE_DAYS: float = 7.0

# R8.3: admission percentile. A candidate peak must reach at least this
# percentile of ITS OWN era window's coarse λ distribution — never a
# reference to lambda_thresh (which is a calibration-tier, external,
# possibly-0.0-structural-prior value; PK-R-8 requires admission to be a
# property of the window's own data, independent of that external gate).
ADMISSION_PERCENTILE: float = 90.0

# R8.4: greedy-retention parameters.
MIN_PEAK_SEPARATION_DAYS: float = 90.0
MAX_PEAKS_PER_ERA_WINDOW: int = 3

# R8.5: day-refinement window around each retained coarse candidate.
DAY_REFINEMENT_HALF_WINDOW_DAYS: float = 7.0
DAY_REFINEMENT_STEP_DAYS: float = 1.0

# R8.13: named zero-peaks reasons — never a bare/undifferentiated string.
# Each has a distinct, testable cause (see build_peak_anchored_windows).
ZERO_PEAKS_ERA_WINDOW_TOO_SHORT = "era_window_too_short"
ZERO_PEAKS_FLAT_LAMBDA_CURVE = "flat_lambda_curve"
ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90 = "no_candidate_above_p90"
# MR-44: an era window admitted >=1 candidate (cleared its own P90) but
# retained ZERO after the POOLED cross-interval retention pass — every
# admitted candidate either fell within MIN_PEAK_SEPARATION_DAYS of a
# higher-lambda peak retained from a SIBLING era window in the same
# build_resolution_hierarchy call, or the per-era MAX_PEAKS_PER_ERA_WINDOW
# cap was exhausted by that window's own higher-ranked candidates first.
# Distinct from ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90 (that reason means
# admission itself found nothing; this one means admission succeeded but
# the candidate lost the pooled retention competition) — §N.8: a real,
# distinguishable detector, not a proxy folded into an existing reason.
ZERO_PEAKS_LOST_TO_POOLED_RETENTION = "lost_to_pooled_retention"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class WindowResolutionRecord:
    """A window at a specific resolution tier with hierarchy linkage.

    Fields
    ------
    window_id           Unique identifier for this window (UUID string).
    parent_window_id    window_id of the containing coarser-tier window
                        (era for month rows, month for day rows). None for
                        era-tier rows (no coarser parent exists).
    resolution_tier     One of RESOLUTION_TIERS ("era", "month", "day", "muhurta").
    enter_jd            JD where this window starts.
    exit_jd             JD where this window ends.
    peak_jd             JD of λ_v3 maximum within [enter_jd, exit_jd]. For
                        month/day rows (PK-R-8 R8.5) this is the DAY-REFINED
                        true argmax, never the coarse scan candidate.
    peak_lambda         λ_v3 value at peak_jd.
    term_breakdown      W1.5 per-mechanism λ_v3 decomposition at peak_jd.
                        Populated ONLY for era-tier windows sourced directly
                        from find_threshold_crossings's IntervalBoundary
                        (which already computes this at its own peak_jd —
                        see interval_solver.py). None for month/day-tier
                        windows: the day-refinement scan (R8.5) uses
                        `_eval_single` (a bare scalar λ, no full
                        IntensityResult) — an honest None here, never a
                        fabricated decomposition (§N.7 item 6).
    lambda_v3_ci_low    80% credible-interval lower bound at peak_jd, era-tier
                        only (same honest-None rule as term_breakdown).
    lambda_v3_ci_high   80% credible-interval upper bound at peak_jd, era-tier
                        only (same honest-None rule as term_breakdown).
    ci_source           'structural_prior' | 'fitted_posterior' disclosure tag,
                        era-tier only (same honest-None rule as term_breakdown).
    """
    window_id: str
    parent_window_id: Optional[str]
    resolution_tier: str
    enter_jd: float
    exit_jd: float
    peak_jd: float
    peak_lambda: float
    term_breakdown: Optional[dict] = None
    lambda_v3_ci_low: Optional[float] = None
    lambda_v3_ci_high: Optional[float] = None
    ci_source: Optional[str] = None


@dataclass
class PeakCandidate:
    """One local-maximum candidate from the coarse-series scan (R8.2)."""
    jd: float
    lam: float


@dataclass
class EraWindowAccounting:
    """Peak-accounting for ONE era window's peak-anchoring pass (R8.13)."""
    peaks_scanned: int
    peaks_admitted: int
    peaks_retained: int
    zero_peaks_reason: Optional[str]


@dataclass
class HierarchyResult:
    """Full multi-resolution hierarchy for one (event_class, JD range) call.

    Fields
    ------
    era_windows          Windows at the "era" tier (one per detected
                         find_threshold_crossings interval).
    month_windows        Peak-anchored "month" tier windows.
    day_windows          Peak-anchored "day" tier windows.
    resolution_facet     Machine-readable counts by tier for serving/census.
                         Keys: "era", "month", "day". Values: int counts.
    era_window_count     Same as len(era_windows) — carried explicitly for
                         WriterResult.notes accounting (R8.13).
    peaks_scanned        Total local-maximum candidates found across ALL
                         era windows in this call (R8.13).
    peaks_admitted       Total candidates whose λ >= their era window's own
                         P90 (R8.13).
    peaks_retained       Total candidates surviving greedy retention —
                         equals len(month_windows) == len(day_windows)
                         (R8.6/R8.13).
    zero_peaks_reason    Populated ONLY when peaks_retained == 0 across the
                         whole call AND at least one era window was scanned;
                         the reason from the (first, or only) era window
                         that retained zero peaks. None when peaks were
                         retained, or when there were no era windows at all
                         to explain (a genuinely different, unrelated case
                         from "scanned and found nothing"). AGGREGATE ONLY —
                         see `era_window_accounting` for the per-era-window
                         reason MR-45 fixed the reachability of (a specific
                         era window can lose the pooled retention
                         competition even while the pool AS A WHOLE retains
                         something from a SIBLING era window, in which case
                         this aggregate field stays None/absent because
                         `total_retained` across the whole call is nonzero
                         — that per-era loss is still real and is reported
                         via `era_window_accounting`, never silently
                         dropped).
    era_window_accounting  MR-45 fix: one `EraWindowAccounting` per era
                         window, INDEX-ALIGNED with `era_windows`
                         (`era_window_accounting[i]` describes
                         `era_windows[i]`'s own scan/admission/retention
                         outcome). Unlike `zero_peaks_reason` (an aggregate
                         gated on the WHOLE call retaining zero peaks), each
                         entry's own `zero_peaks_reason` is populated
                         whenever THAT era window itself retained zero
                         peaks — including `ZERO_PEAKS_LOST_TO_POOLED_
                         RETENTION` for an era window whose admitted
                         candidate(s) lost the cross-interval pooled
                         retention competition (MR-44's `retain_candidates_
                         pooled`) to a higher-λ peak from a SIBLING era
                         window, even when that sibling's retention means
                         the call's own `total_retained` (and therefore
                         `zero_peaks_reason` above) is nonzero. This is the
                         register's MR-45 fix for the finding that
                         `ZERO_PEAKS_LOST_TO_POOLED_RETENTION` was
                         unreachable dead code: `retain_candidates_pooled`
                         always retains >=1 candidate globally whenever ANY
                         era window admitted one, so the aggregate
                         `total_retained == 0` gate could never fire in the
                         exact case this reason exists to name (one era's
                         own candidate globally rejected while the pool as
                         a whole still retains something else). Empty list
                         for calls with zero era windows.
    """
    era_windows: list[WindowResolutionRecord]
    month_windows: list[WindowResolutionRecord]
    day_windows: list[WindowResolutionRecord]
    resolution_facet: dict[str, int]
    era_window_count: int = 0
    peaks_scanned: int = 0
    peaks_admitted: int = 0
    peaks_retained: int = 0
    zero_peaks_reason: Optional[str] = None
    era_window_accounting: list["EraWindowAccounting"] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pure helper: tier ordering (kept for any caller reasoning about coarseness)
# ---------------------------------------------------------------------------

def _tier_index(tier: str) -> int:
    """Return the numeric index of a tier (lower = coarser).

    Raises ValueError if tier is not in RESOLUTION_TIERS.
    """
    try:
        return RESOLUTION_TIERS.index(tier)
    except ValueError as exc:
        raise ValueError(
            f"[resolution_hierarchy] unknown tier '{tier}'; "
            f"valid tiers: {RESOLUTION_TIERS}"
        ) from exc


def _is_coarser(tier_a: str, tier_b: str) -> bool:
    """Return True iff tier_a is strictly coarser than tier_b."""
    return _tier_index(tier_a) < _tier_index(tier_b)


# ---------------------------------------------------------------------------
# Pure function: assign parent_window_ids by geometric containment
# ---------------------------------------------------------------------------
#
# PK-R-8 note: build_resolution_hierarchy (below) no longer CALLS this —
# under peak-anchoring, parent linkage is set directly at construction time
# (a month window's parent IS the era window it was anchored within; a day
# window's parent IS its month window), which is more precise than a
# geometric "widest containing window" search now that windows are anchored
# rather than tiled. Retained as a standalone, independently-useful, and
# independently-tested pure utility — R8.1 named only the tilers (build_
# month_windows/build_day_windows/MONTH_STEP_DAYS/DAY_STEP_DAYS) for removal.

def assign_parent_window_ids(
    windows: list[WindowResolutionRecord],
) -> list[WindowResolutionRecord]:
    """Assign each window's parent_window_id to the widest containing coarser window.

    Given a flat list of windows at mixed tiers, for each window W:
      - Find all windows whose resolution_tier is strictly coarser than W's tier.
      - Among those that geometrically contain W ([enter_jd..exit_jd] ⊇ W's span),
        pick the widest one (largest exit_jd - enter_jd) as the parent.
      - If no coarser window contains W, parent_window_id remains None.

    This is a pure function — no DB access.

    Parameters
    ----------
    windows     Flat list of WindowResolutionRecord at any mix of tiers.

    Returns
    -------
    New list of WindowResolutionRecord with parent_window_id filled in.
    """
    result: list[WindowResolutionRecord] = []

    for w in windows:
        best_parent_id: Optional[str] = None
        best_span: float = -1.0

        for candidate in windows:
            if candidate.window_id == w.window_id:
                continue
            if not _is_coarser(candidate.resolution_tier, w.resolution_tier):
                continue
            if candidate.enter_jd > w.enter_jd:
                continue
            if candidate.exit_jd < w.exit_jd:
                continue
            candidate_span = candidate.exit_jd - candidate.enter_jd
            if candidate_span > best_span:
                best_span = candidate_span
                best_parent_id = candidate.window_id

        result.append(WindowResolutionRecord(
            window_id=w.window_id,
            parent_window_id=best_parent_id,
            resolution_tier=w.resolution_tier,
            enter_jd=w.enter_jd,
            exit_jd=w.exit_jd,
            peak_jd=w.peak_jd,
            peak_lambda=w.peak_lambda,
            term_breakdown=w.term_breakdown,
            lambda_v3_ci_low=w.lambda_v3_ci_low,
            lambda_v3_ci_high=w.lambda_v3_ci_high,
            ci_source=w.ci_source,
        ))

    return result


# ---------------------------------------------------------------------------
# R8.2 — local-maximum scan on a REUSED coarse series
# ---------------------------------------------------------------------------

def find_local_maxima(jds: np.ndarray, lambdas: np.ndarray) -> list[PeakCandidate]:
    """Find local-maximum candidates in a coarse (jd, lambda) series.

    A candidate is an interior index i with s[i] > s[i-1] AND s[i] >= s[i+1]
    (a strict rise followed by a non-increase — this admits the flat top of
    a plateau exactly once, at its FIRST point, rather than once per equal
    sample). An endpoint (index 0 or n-1) is a candidate only if it STRICTLY
    exceeds its single neighbour.

    Pure function — no swe/context access, no evaluate_lambda_vector calls.
    Operates entirely on the series already computed by the caller (R8.2:
    this is the "reuse", not a re-sweep).

    Returns
    -------
    list[PeakCandidate], in series order (ascending jd). Empty for series
    with fewer than 2 points, or a perfectly flat series (no strict rises
    anywhere — see admit_candidates for the EXPLICIT flat-curve check that
    does not merely rely on this emergent behaviour).
    """
    n = len(lambdas)
    if n < 2:
        return []

    candidates: list[PeakCandidate] = []
    for i in range(n):
        if i == 0:
            if lambdas[0] > lambdas[1]:
                candidates.append(PeakCandidate(float(jds[0]), float(lambdas[0])))
        elif i == n - 1:
            if lambdas[i] > lambdas[i - 1]:
                candidates.append(PeakCandidate(float(jds[i]), float(lambdas[i])))
        else:
            if lambdas[i] > lambdas[i - 1] and lambdas[i] >= lambdas[i + 1]:
                candidates.append(PeakCandidate(float(jds[i]), float(lambdas[i])))
    return candidates


# ---------------------------------------------------------------------------
# R8.3 — admission: P90 of the era window's OWN coarse series, never
# lambda_thresh
# ---------------------------------------------------------------------------

def admit_candidates(
    candidates: list[PeakCandidate],
    series_lambdas: np.ndarray,
    *,
    percentile: float = ADMISSION_PERCENTILE,
) -> list[PeakCandidate]:
    """Admit candidates whose λ meets the era window's OWN P90.

    NO reference to lambda_thresh/ThresholdConfig anywhere in this function
    — admission is a property of THIS era window's own λ distribution only
    (R8.3, binding). A flat/constant series (max == min) admits ZERO
    candidates EXPLICITLY (not merely because find_local_maxima happens to
    find none on a flat series — this is a second, independent guarantee).
    """
    if len(series_lambdas) == 0 or not candidates:
        return []

    lo = float(np.min(series_lambdas))
    hi = float(np.max(series_lambdas))
    if hi <= lo:
        # Explicit flat/constant-curve guard (R8.3) — never admit from a
        # series with zero variance, regardless of what find_local_maxima
        # returned for it.
        return []

    p90 = float(np.percentile(series_lambdas, percentile))
    return [c for c in candidates if c.lam >= p90]


# ---------------------------------------------------------------------------
# R8.4 — retention: rank, greedy-retain with separation, cap
# ---------------------------------------------------------------------------

def retain_candidates(
    admitted: list[PeakCandidate],
    *,
    max_peaks: int = MAX_PEAKS_PER_ERA_WINDOW,
    min_separation_days: float = MIN_PEAK_SEPARATION_DAYS,
) -> list[PeakCandidate]:
    """Rank (λ DESC, jd ASC) and greedily retain, skipping any candidate
    within min_separation_days of an already-retained one, capped at
    max_peaks. Deterministic on ties (jd ASC is the tiebreaker).

    Returns the retained set sorted by jd ASCENDING (stable emission order).
    """
    ranked = sorted(admitted, key=lambda c: (-c.lam, c.jd))
    retained: list[PeakCandidate] = []
    for c in ranked:
        if len(retained) >= max_peaks:
            break
        if all(abs(c.jd - r.jd) >= min_separation_days for r in retained):
            retained.append(c)
    return sorted(retained, key=lambda c: c.jd)


# ---------------------------------------------------------------------------
# MR-44 fix — R8.4 amendment: retention POOLED across all era windows in one
# build_resolution_hierarchy call, so MIN_PEAK_SEPARATION_DAYS is enforced
# GLOBALLY (not just within each interval's own candidate set).
# ---------------------------------------------------------------------------

def retain_candidates_pooled(
    admitted_by_era: list[list[PeakCandidate]],
    *,
    max_peaks_per_era: int = MAX_PEAKS_PER_ERA_WINDOW,
    min_separation_days: float = MIN_PEAK_SEPARATION_DAYS,
) -> list[list[PeakCandidate]]:
    """Pool admitted candidates from MULTIPLE era windows into ONE
    retention pass (MR-44 fix; register `MASTER_REMEDIATION_REGISTER_v2_0.md`
    MR-44, PK-R-8 R8.4 amendment).

    THE BUG THIS CLOSES: `retain_candidates` (above) enforces
    MIN_PEAK_SEPARATION_DAYS only within the ONE candidate set it is
    handed. When `find_threshold_crossings` genuinely returns >=2 intervals
    for a single decade slice (a real, observed production condition — not
    a threshold artifact) and each interval's `build_peak_anchored_windows`
    call retains independently, two peaks from two DIFFERENT era windows
    can each trivially pass their own within-interval separation check
    (there was nothing else in their own interval to collide with) yet
    land, after independent day-refinement (R8.5), on the IDENTICAL
    calendar day — producing a duplicate row on the writer's natural key
    (chart_id, event_class, window_start, peak_date, milestone_id,
    generation). Observed live: chart 482012f1, event_class=career_setback,
    decade g3_2014_2024, two intervals' peaks both refined to 2017-03-01.

    THE FIX: rank ALL candidates from ALL era windows TOGETHER using the
    exact same tie-break `retain_candidates` uses (λ DESC, jd ASC), then
    greedily retain enforcing MIN_PEAK_SEPARATION_DAYS across the WHOLE
    pooled set — while still capping each INDIVIDUAL era window's own
    retained count at `max_peaks_per_era` (register MR-44's ruled
    interpretation of PK-R-8 R8.4: option (a), "cap at
    MAX_PEAKS_PER_ERA_WINDOW per era window as before" — the cap is
    per-window; only the separation check widens to global scope).

    Parameters
    ----------
    admitted_by_era     One list of P90-admitted PeakCandidates per era
                        window, in era-window order (index-aligned with the
                        caller's own era_windows list — index i's retained
                        subset is returned at result[i]).

    Returns
    -------
    A list, index-aligned with `admitted_by_era`, of each era window's own
    RETAINED subset (sorted jd ASCENDING within each era window, mirroring
    `retain_candidates`' own stable emission order). An era window whose
    candidates all lost the pooled competition gets an empty list — never
    a fallback fabrication.
    """
    tagged: list[tuple[int, PeakCandidate]] = [
        (era_idx, c)
        for era_idx, candidates in enumerate(admitted_by_era)
        for c in candidates
    ]

    ranked = sorted(tagged, key=lambda t: (-t[1].lam, t[1].jd))

    retained: list[tuple[int, PeakCandidate]] = []
    per_era_count: dict[int, int] = {}
    for era_idx, c in ranked:
        if per_era_count.get(era_idx, 0) >= max_peaks_per_era:
            continue
        if all(abs(c.jd - r.jd) >= min_separation_days for _, r in retained):
            retained.append((era_idx, c))
            per_era_count[era_idx] = per_era_count.get(era_idx, 0) + 1

    result: list[list[PeakCandidate]] = [[] for _ in admitted_by_era]
    for era_idx, c in retained:
        result[era_idx].append(c)
    for bucket in result:
        bucket.sort(key=lambda c: c.jd)
    return result


# ---------------------------------------------------------------------------
# R8.5 — day refinement: 1-day-resolution argmax over [c-7d, c+7d]
# ---------------------------------------------------------------------------

def refine_peak_to_day(
    swe,
    context,
    candidate_jd: float,
    *,
    half_window_days: float = DAY_REFINEMENT_HALF_WINDOW_DAYS,
    step_days: float = DAY_REFINEMENT_STEP_DAYS,
) -> tuple[float, float]:
    """Re-sample at `step_days` resolution over [candidate_jd - half_window_days,
    candidate_jd + half_window_days] and return (peak_jd_true, peak_lambda_true)
    — the TRUE argmax over that fine grid, never the coarse candidate itself
    (R8.5, the fix this ruling calls "most important": the coarse P90-scan
    stride is 7 days — a true peak can fall anywhere inside that stride, and
    serving the coarse candidate's own jd as `peak_date` would silently
    misrepresent which calendar day the window's timing claim actually
    anchors to).
    """
    start = candidate_jd - half_window_days
    end = candidate_jd + half_window_days
    n_steps = int(round((end - start) / step_days)) + 1

    best_jd = candidate_jd
    try:
        best_lam = _eval_single(swe, context, candidate_jd)
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "[resolution_hierarchy] refine_peak_to_day: _eval_single failed "
            "at candidate_jd=%.4f: %s — using 0.0", candidate_jd, exc,
        )
        best_lam = 0.0

    jd = start
    for _ in range(n_steps):
        try:
            lam = _eval_single(swe, context, jd)
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "[resolution_hierarchy] refine_peak_to_day: _eval_single "
                "failed at jd=%.4f: %s — skipping this sample", jd, exc,
            )
            jd += step_days
            continue
        if lam > best_lam:
            best_lam = lam
            best_jd = jd
        jd += step_days

    return best_jd, best_lam


# ---------------------------------------------------------------------------
# JD <-> calendar-date helpers (local to this module — resolution_hierarchy
# must not import from the writer, which imports IT)
# ---------------------------------------------------------------------------

_EPOCH_JD = 2440588.0  # JD for Unix epoch 1970-01-01 (matches the writer's
                       # own _jd_to_date convention, kept independently here
                       # to avoid a backwards dependency on the writer module).


def _jd_to_pydate(jd: float) -> _dt.date:
    days_since_epoch = int(jd - _EPOCH_JD)
    return _dt.date(1970, 1, 1) + _dt.timedelta(days=days_since_epoch)


def _pydate_to_jd(d: _dt.date) -> float:
    days_since_epoch = (d - _dt.date(1970, 1, 1)).days
    return _EPOCH_JD + days_since_epoch


def _calendar_month_bounds_jd(peak_jd: float) -> tuple[float, float]:
    """Return (month_start_jd, month_end_jd) for the calendar month
    containing peak_jd — the FULL month, clipping to the era window is the
    caller's job (R8.6)."""
    d = _jd_to_pydate(peak_jd)
    month_start = d.replace(day=1)
    if d.month == 12:
        next_month_start = d.replace(year=d.year + 1, month=1, day=1)
    else:
        next_month_start = d.replace(month=d.month + 1, day=1)
    month_end = next_month_start - _dt.timedelta(days=1)
    return _pydate_to_jd(month_start), _pydate_to_jd(month_end)


# ---------------------------------------------------------------------------
# R8.1/R8.2-R8.6 — build_peak_anchored_windows: replaces the tilers
# ---------------------------------------------------------------------------

def _scan_and_admit(
    coarse_series: tuple[np.ndarray, np.ndarray],
) -> tuple[list[PeakCandidate], int, int, Optional[str]]:
    """R8.2/R8.3: local-maximum scan + P90 admission for ONE era window's
    sliced series.

    Factored out of `build_peak_anchored_windows` (MR-44) so that
    `build_resolution_hierarchy`'s pooled-retention path (which needs each
    era window's admitted candidates BEFORE any retention decision is made)
    and `build_peak_anchored_windows`'s own single-interval path share
    IDENTICAL scan+admission logic — no drift between the two call sites.

    Returns
    -------
    (admitted, peaks_scanned, peaks_admitted, zero_reason) — `zero_reason`
    is populated (and `admitted` is `[]`) for the three ADMISSION-stage zero
    causes (era window too short to scan, flat curve, no candidate clears
    P90); it is `None` when >=1 candidate was admitted. Retention-caused
    zero (MR-44: an admitted candidate that loses the POOLED cross-interval
    retention competition) is a separate, later-diagnosed case the caller
    alone can determine, since only the caller sees the pooled outcome.
    """
    jds, lambdas = coarse_series

    if len(jds) < 3:
        # R8.13: can't run interior-point local-max detection with <3 points.
        return [], 0, 0, ZERO_PEAKS_ERA_WINDOW_TOO_SHORT

    candidates = find_local_maxima(jds, lambdas)
    peaks_scanned = len(candidates)

    admitted = admit_candidates(candidates, lambdas)
    peaks_admitted = len(admitted)

    if peaks_admitted == 0:
        lo, hi = float(np.min(lambdas)), float(np.max(lambdas))
        reason = ZERO_PEAKS_FLAT_LAMBDA_CURVE if hi <= lo else ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90
        return [], peaks_scanned, 0, reason

    return admitted, peaks_scanned, peaks_admitted, None


def _emit_retained_peaks(
    swe,
    context,
    era_window: WindowResolutionRecord,
    retained: list[PeakCandidate],
) -> tuple[list[WindowResolutionRecord], list[WindowResolutionRecord]]:
    """R8.5/R8.6: day-refine each RETAINED candidate and emit exactly one
    month row + one day row per peak, parented to `era_window`.

    Factored out of `build_peak_anchored_windows` (MR-44) so that
    `build_resolution_hierarchy` can call it directly with a POOLED
    (cross-interval) retained set instead of a per-interval one, without
    duplicating the day-refinement/row-construction logic. `retained` is
    assumed to already reflect whatever retention policy the caller applied
    (single-interval `retain_candidates` or pooled `retain_candidates_
    pooled`) — this function makes no retention decisions of its own.
    """
    month_windows: list[WindowResolutionRecord] = []
    day_windows: list[WindowResolutionRecord] = []

    for cand in retained:
        peak_jd_true, peak_lambda_true = refine_peak_to_day(swe, context, cand.jd)

        month_start_jd, month_end_jd = _calendar_month_bounds_jd(peak_jd_true)
        # R8.6: clip the calendar month to the era window's own span.
        month_start_jd = max(month_start_jd, era_window.enter_jd)
        month_end_jd = min(month_end_jd, era_window.exit_jd)

        month_id = str(uuid.uuid4())
        month_windows.append(WindowResolutionRecord(
            window_id=month_id,
            parent_window_id=era_window.window_id,
            resolution_tier="month",
            enter_jd=month_start_jd,
            exit_jd=month_end_jd,
            peak_jd=peak_jd_true,  # R8.5: day-refined TRUE argmax, never the coarse candidate
            peak_lambda=peak_lambda_true,
        ))
        day_windows.append(WindowResolutionRecord(
            window_id=str(uuid.uuid4()),
            parent_window_id=month_id,
            resolution_tier="day",
            enter_jd=peak_jd_true,   # R8.6: window_start == window_end == that date
            exit_jd=peak_jd_true,
            peak_jd=peak_jd_true,
            peak_lambda=peak_lambda_true,
        ))

    return month_windows, day_windows


def build_peak_anchored_windows(
    swe,
    context,
    era_window: WindowResolutionRecord,
    coarse_series: tuple[np.ndarray, np.ndarray],
    *,
    max_peaks: int = MAX_PEAKS_PER_ERA_WINDOW,
    min_separation_days: float = MIN_PEAK_SEPARATION_DAYS,
) -> tuple[list[WindowResolutionRecord], list[WindowResolutionRecord], EraWindowAccounting]:
    """Build peak-anchored month + day children for ONE era window (PK-R-8).

    No fixed-step subdivision anywhere (R8.1) — every candidate comes from
    a genuine local-maximum scan (R8.2) of `coarse_series`, the SLICE of the
    already-computed find_threshold_crossings coarse series covering
    [era_window.enter_jd, era_window.exit_jd] (reused, not re-swept).

    NOTE (MR-44): this function's own `retain_candidates` call is scoped to
    THIS era window's candidates only — it is the right behaviour for a
    caller anchoring exactly ONE era window in isolation (as this function's
    own direct callers/tests do). `build_resolution_hierarchy` (the
    multi-interval top-level entry) does NOT call this function for its
    retention step — it pools ALL era windows' admitted candidates via
    `retain_candidates_pooled` first (closing the MR-44 cross-interval
    duplicate-peak defect), then calls `_emit_retained_peaks` directly with
    each era window's POOLED-retained subset. See `build_resolution_
    hierarchy` and `retain_candidates_pooled` for the full rationale.

    Parameters
    ----------
    swe, context        Needed ONLY for the day-refinement re-sample (R8.5) —
                        the coarse scan itself makes zero evaluate_lambda_
                        vector calls (it reuses `coarse_series`).
    era_window          The era-tier WindowResolutionRecord this call anchors
                        peaks within (used for parent_window_id + clipping).
    coarse_series       (jds, lambdas) — the reused coarse-sweep slice for
                        this era window's own JD span.
    max_peaks, min_separation_days
                        R8.4 retention parameters (module defaults; kept as
                        parameters for testability).

    Returns
    -------
    (month_windows, day_windows, accounting) — exactly one month row and one
    day row per RETAINED peak (R8.6); zero peaks retained -> both lists
    empty, no fallback fabrication.
    """
    admitted, peaks_scanned, peaks_admitted, zero_reason = _scan_and_admit(coarse_series)
    if zero_reason is not None:
        return [], [], EraWindowAccounting(peaks_scanned, peaks_admitted, 0, zero_reason)

    retained = retain_candidates(admitted, max_peaks=max_peaks, min_separation_days=min_separation_days)
    peaks_retained = len(retained)

    month_windows, day_windows = _emit_retained_peaks(swe, context, era_window, retained)

    return month_windows, day_windows, EraWindowAccounting(
        peaks_scanned, peaks_admitted, peaks_retained, None,
    )


# ---------------------------------------------------------------------------
# Era-window builder (unchanged detection machinery; simplified tiering)
# ---------------------------------------------------------------------------

def build_era_windows(
    swe,
    context,
    start_jd: float,
    end_jd: float,
    threshold_config: ThresholdConfig,
) -> list[WindowResolutionRecord]:
    """Build era-tier windows from find_threshold_crossings' detected
    intervals.

    PK-R-8: EVERY detected interval is now an "era" window, regardless of
    its own duration — the pre-PK-R-8 duration-based era/month split
    (ERA_MIN_DAYS) is retired: month-tier windows now come ONLY from
    peak-anchoring (build_peak_anchored_windows), never from a short
    interval being auto-reclassified as "month". A short era window simply
    produces fewer (possibly zero) peak-anchored children — see
    build_resolution_hierarchy.

    I4: empty/sparse inputs → honest empty output. No fabrication.
    """
    if end_jd <= start_jd:
        logger.debug(
            "[resolution_hierarchy] build_era_windows: end_jd (%.4f) <= start_jd (%.4f) "
            "— returning []", end_jd, start_jd,
        )
        return []

    intervals = find_threshold_crossings(
        swe, context, start_jd, end_jd, threshold_config,
    )

    records: list[WindowResolutionRecord] = []
    for interval in intervals:
        records.append(WindowResolutionRecord(
            window_id=str(uuid.uuid4()),
            parent_window_id=None,
            resolution_tier="era",
            enter_jd=interval.enter_jd,
            exit_jd=interval.exit_jd,
            peak_jd=interval.peak_jd,
            peak_lambda=interval.peak_lambda,
            term_breakdown=interval.term_breakdown,
            lambda_v3_ci_low=interval.lambda_v3_ci_low,
            lambda_v3_ci_high=interval.lambda_v3_ci_high,
            ci_source=interval.ci_source,
        ))

    return records


# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------

def build_resolution_hierarchy(
    swe,
    context,
    start_jd: float,
    end_jd: float,
    threshold_config: ThresholdConfig,
) -> HierarchyResult:
    """Build the full era⊃month⊃day peak-anchored hierarchy (PK-R-8) for a
    given search range.

    1. find_threshold_crossings(..., return_series=True) — ONE ephemeris
       sweep, producing both the detected intervals (era windows) AND the
       coarse (jd, lambda) series (R8.2's reuse source).
    2. Each detected interval becomes exactly one era-tier
       WindowResolutionRecord.
    3. For each era window, slice the reused series to its own JD span and
       run the R8.2/R8.3 scan+admission (_scan_and_admit) on that slice —
       no re-sweep, no tiling.
    4. MR-44 FIX: retain ONCE across ALL era windows in this call, POOLED
       (`retain_candidates_pooled`) — MIN_PEAK_SEPARATION_DAYS is enforced
       GLOBALLY across the whole decade, not just within each interval's
       own candidate set (R8.4 amendment; see module docstring + `retain_
       candidates_pooled`'s own docstring for the full defect this closes).
       MAX_PEAKS_PER_ERA_WINDOW remains a PER-ERA-WINDOW cap.
    5. For each era window, day-refine (R8.5) + emit (R8.6) its own POOLED-
       retained subset via `_emit_retained_peaks`.
    6. Aggregate peak accounting across all era windows for the caller's
       WriterResult.notes (R8.13).

    I4: empty/sparse inputs → honest empty HierarchyResult with 0 counts.
    No windows are fabricated.
    """
    if end_jd <= start_jd:
        logger.debug(
            "[resolution_hierarchy] build_resolution_hierarchy: end_jd (%.4f) <= "
            "start_jd (%.4f) — returning empty.", end_jd, start_jd,
        )
        return HierarchyResult(
            era_windows=[], month_windows=[], day_windows=[],
            resolution_facet={"era": 0, "month": 0, "day": 0},
        )

    intervals, series_jds, series_lambdas = find_threshold_crossings(
        swe, context, start_jd, end_jd, threshold_config,
        coarse_step_days=PEAK_SCAN_STRIDE_DAYS,
        return_series=True,
    )

    era_windows: list[WindowResolutionRecord] = []
    # Index-aligned with era_windows: each era window's own admitted
    # candidates + pre-retention scan/admission accounting (MR-44 — the
    # scan+admission stage stays per-era-window; only retention pools).
    admitted_by_era: list[list[PeakCandidate]] = []
    scan_meta: list[tuple[int, int, Optional[str]]] = []  # (scanned, admitted, zero_reason)

    for interval in intervals:
        era_record = WindowResolutionRecord(
            window_id=str(uuid.uuid4()),
            parent_window_id=None,
            resolution_tier="era",
            enter_jd=interval.enter_jd,
            exit_jd=interval.exit_jd,
            peak_jd=interval.peak_jd,
            peak_lambda=interval.peak_lambda,
            term_breakdown=interval.term_breakdown,
            lambda_v3_ci_low=interval.lambda_v3_ci_low,
            lambda_v3_ci_high=interval.lambda_v3_ci_high,
            ci_source=interval.ci_source,
        )
        era_windows.append(era_record)

        # R8.2: slice the ALREADY-COMPUTED coarse series to this era
        # window's own span — zero additional evaluate_lambda_vector calls.
        if len(series_jds) > 0:
            mask = (series_jds >= interval.enter_jd) & (series_jds <= interval.exit_jd)
            sliced_jds = series_jds[mask]
            sliced_lambdas = series_lambdas[mask]
        else:
            sliced_jds = np.array([])
            sliced_lambdas = np.array([])

        admitted, peaks_scanned, peaks_admitted, zero_reason = _scan_and_admit(
            (sliced_jds, sliced_lambdas),
        )
        admitted_by_era.append(admitted)
        scan_meta.append((peaks_scanned, peaks_admitted, zero_reason))

    # MR-44 fix: ONE pooled retention pass across ALL era windows in this
    # call — MIN_PEAK_SEPARATION_DAYS enforced globally; MAX_PEAKS_PER_ERA_
    # WINDOW still capped per era window. For a single-era-window call this
    # is exactly equivalent to calling retain_candidates on that one
    # window's admitted set (no behavioural change from before MR-44 in the
    # common single-interval case).
    retained_by_era = retain_candidates_pooled(admitted_by_era)

    all_month: list[WindowResolutionRecord] = []
    all_day: list[WindowResolutionRecord] = []

    total_scanned = 0
    total_admitted = 0
    total_retained = 0
    # MR-45: per-era-window accounting, INDEX-ALIGNED with era_windows —
    # each era window's OWN outcome, computed independent of whatever the
    # POOL as a whole retained. This is what makes ZERO_PEAKS_LOST_TO_
    # POOLED_RETENTION reachable: the pre-MR-45 code only ever surfaced a
    # zero_peaks_reason gated on total_retained==0 (the whole-call
    # aggregate), which `retain_candidates_pooled` guarantees is nonzero
    # whenever ANY era window admitted a candidate anywhere in the pool —
    # so a SPECIFIC era window losing the pooled competition while a
    # SIBLING era window's peak survives could never reach that aggregate
    # gate. era_window_accounting reports it directly, per window, always.
    era_window_accounting: list[EraWindowAccounting] = []

    for era_idx, era_record in enumerate(era_windows):
        peaks_scanned, peaks_admitted, pre_retention_reason = scan_meta[era_idx]
        retained = retained_by_era[era_idx]

        total_scanned += peaks_scanned
        total_admitted += peaks_admitted
        total_retained += len(retained)

        if retained:
            month_rows, day_rows = _emit_retained_peaks(swe, context, era_record, retained)
            all_month.extend(month_rows)
            all_day.extend(day_rows)
            era_window_accounting.append(
                EraWindowAccounting(peaks_scanned, peaks_admitted, len(retained), None)
            )
        elif pre_retention_reason is not None:
            era_window_accounting.append(
                EraWindowAccounting(peaks_scanned, peaks_admitted, 0, pre_retention_reason)
            )
        elif peaks_admitted > 0:
            # MR-44: this era window HAD admittable candidates but none
            # survived the POOLED cross-interval retention pass -- an
            # honest, distinct reason from "no candidate above P90" (see
            # ZERO_PEAKS_LOST_TO_POOLED_RETENTION's own docstring note).
            # MR-45: this is THIS era window's OWN accounting entry,
            # reported regardless of whether a sibling era window's peak
            # survived pooled retention (the fix for the dead-code finding).
            era_window_accounting.append(
                EraWindowAccounting(peaks_scanned, peaks_admitted, 0, ZERO_PEAKS_LOST_TO_POOLED_RETENTION)
            )
        else:
            # Defensive: _scan_and_admit's own contract guarantees a
            # pre_retention_reason whenever peaks_admitted == 0, so this
            # branch is not expected to execute. An honest None rather than
            # a fabricated reason if it ever does (§N.7 item 6).
            era_window_accounting.append(
                EraWindowAccounting(peaks_scanned, peaks_admitted, 0, None)
            )

    resolution_facet: dict[str, int] = {
        "era": len(era_windows),
        "month": len(all_month),
        "day": len(all_day),
    }

    overall_zero_reason: Optional[str] = None
    if total_retained == 0:
        zero_reasons = [
            acc.zero_peaks_reason for acc in era_window_accounting
            if acc.zero_peaks_reason is not None
        ]
        if zero_reasons:
            # One era window's reason (the first) stands in for the
            # aggregate — R8.13's WriterResult.notes reports this alongside
            # era_windows so a reader with multiple era windows can see the
            # count and reconcile. Per-era-window reasons (including any
            # ZERO_PEAKS_LOST_TO_POOLED_RETENTION entries) are ALWAYS
            # available in full via era_window_accounting regardless of
            # this aggregate gate — see that field's own docstring.
            overall_zero_reason = zero_reasons[0]

    logger.info(
        "[resolution_hierarchy] build_resolution_hierarchy: "
        "era=%d month=%d day=%d peaks_scanned=%d peaks_admitted=%d "
        "peaks_retained=%d — start=%.4f end=%.4f",
        len(era_windows), len(all_month), len(all_day),
        total_scanned, total_admitted, total_retained, start_jd, end_jd,
    )

    return HierarchyResult(
        era_windows=era_windows,
        month_windows=all_month,
        day_windows=all_day,
        resolution_facet=resolution_facet,
        era_window_count=len(era_windows),
        peaks_scanned=total_scanned,
        peaks_admitted=total_admitted,
        peaks_retained=total_retained,
        zero_peaks_reason=overall_zero_reason,
        era_window_accounting=era_window_accounting,
    )


__all__ = [
    "RESOLUTION_TIERS",
    "ERA_BODIES",
    "PEAK_SCAN_STRIDE_DAYS",
    "ADMISSION_PERCENTILE",
    "MIN_PEAK_SEPARATION_DAYS",
    "MAX_PEAKS_PER_ERA_WINDOW",
    "DAY_REFINEMENT_HALF_WINDOW_DAYS",
    "DAY_REFINEMENT_STEP_DAYS",
    "ZERO_PEAKS_ERA_WINDOW_TOO_SHORT",
    "ZERO_PEAKS_FLAT_LAMBDA_CURVE",
    "ZERO_PEAKS_NO_CANDIDATE_ABOVE_P90",
    "ZERO_PEAKS_LOST_TO_POOLED_RETENTION",
    "WindowResolutionRecord",
    "PeakCandidate",
    "EraWindowAccounting",
    "HierarchyResult",
    "assign_parent_window_ids",
    "find_local_maxima",
    "admit_candidates",
    "retain_candidates",
    "retain_candidates_pooled",
    "refine_peak_to_day",
    "build_peak_anchored_windows",
    "build_era_windows",
    "build_resolution_hierarchy",
]
