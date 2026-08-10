"""
gochara_v3.resolution_hierarchy — Multi-resolution window hierarchy (W3.3).

Defines the resolution tiers and parent-window assignment logic for λ_v3 windows.

Resolution tiers (coarsest to finest):
  era       Saturn (28.45y), Jupiter (11.86y), Rahu/Ketu (18.61y) orbital periods.
            These are computed from ephemeris; typical duration 3–30 years.
  month     28–31 day windows (synodic month approximation).
  day       Individual calendar days.
  muhurta   Lazily computed on demand (Tier-C Moon-based; NOT built here).

I2: zero imports from gochara_grammar/*, gochara_intensity/*, ka_gochara_sweep/*.

Dataclasses:
  Resolution: enum-like frozen dataclass with TIER ordering (era < month < day < muhurta)
  WindowResolutionRecord: a window with its tier, span JDs, and optional parent_id
  HierarchyResult: full hierarchy for one event-class episode
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

from .interval_solver import find_threshold_crossings, _eval_single
from .threshold import ThresholdConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolution tier constants
# ---------------------------------------------------------------------------

# Ordered coarsest-to-finest. Index position defines tier ordering.
RESOLUTION_TIERS: tuple[str, ...] = ("era", "month", "day", "muhurta")

# Orbital periods in days for slow bodies that define "era"-level windows.
ERA_BODIES: dict[str, float] = {
    "Saturn": 28.45 * 365.25,   # 10,392 days ≈ 28.45 years
    "Jupiter": 11.86 * 365.25,  # 4,332 days ≈ 11.86 years
    "Rahu": 18.61 * 365.25,     # 6,793 days ≈ 18.61 years
    "Ketu": 18.61 * 365.25,     # 6,793 days ≈ 18.61 years (same period as Rahu)
}

# A window whose duration exceeds this is classified as "era"; else "month".
ERA_MIN_DAYS: float = 365.0  # one year

# Step size used when sub-dividing era windows into month-level windows.
MONTH_STEP_DAYS: float = 30.0

# Step size used when sub-dividing month windows into day-level windows.
DAY_STEP_DAYS: float = 1.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class WindowResolutionRecord:
    """A window at a specific resolution tier with hierarchy linkage.

    Fields
    ------
    window_id           Unique identifier for this window (UUID string).
    parent_window_id    window_id of the widest containing window at a coarser
                        tier. None if no containing coarser window exists.
    resolution_tier     One of RESOLUTION_TIERS ("era", "month", "day", "muhurta").
    enter_jd            JD where this window's λ_v3 crosses the threshold upward.
    exit_jd             JD where this window's λ_v3 crosses the threshold downward.
    peak_jd             JD of λ_v3 maximum within [enter_jd, exit_jd].
    peak_lambda         λ_v3 value at peak_jd.
    """
    window_id: str
    parent_window_id: Optional[str]
    resolution_tier: str
    enter_jd: float
    exit_jd: float
    peak_jd: float
    peak_lambda: float


@dataclass
class HierarchyResult:
    """Full multi-resolution hierarchy for one event-class episode.

    Fields
    ------
    era_windows         Windows classified at the "era" tier.
    month_windows       Windows classified at the "month" tier.
    day_windows         Windows classified at the "day" tier.
    resolution_facet    Machine-readable counts by tier for serving/census.
                        Keys: "era", "month", "day". Values: int counts.
    """
    era_windows: list[WindowResolutionRecord]
    month_windows: list[WindowResolutionRecord]
    day_windows: list[WindowResolutionRecord]
    resolution_facet: dict[str, int]


# ---------------------------------------------------------------------------
# Pure helper: tier ordering
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
# Pure function: assign parent_window_ids
# ---------------------------------------------------------------------------

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
    # Build an annotated list to avoid mutating input
    result: list[WindowResolutionRecord] = []

    for w in windows:
        best_parent_id: Optional[str] = None
        best_span: float = -1.0

        for candidate in windows:
            if candidate.window_id == w.window_id:
                continue

            # candidate must be at a strictly coarser tier
            if not _is_coarser(candidate.resolution_tier, w.resolution_tier):
                continue

            # candidate must contain w geometrically
            if candidate.enter_jd > w.enter_jd:
                continue
            if candidate.exit_jd < w.exit_jd:
                continue

            # pick the widest containing coarser window as the parent
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
        ))

    return result


# ---------------------------------------------------------------------------
# Era window builder
# ---------------------------------------------------------------------------

def build_era_windows(
    swe,
    context,
    start_jd: float,
    end_jd: float,
    threshold_config: ThresholdConfig,
) -> list[WindowResolutionRecord]:
    """Build era-level (or month-level) windows from threshold crossings.

    Uses find_threshold_crossings from interval_solver to locate intervals
    where λ_v3 is above the activation threshold. Each interval is classified
    as "era" if its duration > ERA_MIN_DAYS (365 days), else "month".

    I4: empty/sparse inputs → honest empty output. No fabrication.

    Parameters
    ----------
    swe                 Swiss Ephemeris handle.
    context             ClassContext (pre-fetched, immutable).
    start_jd            Search range start (Julian Day).
    end_jd              Search range end (Julian Day).
    threshold_config    ThresholdConfig from W1.4 (carries lambda_thresh).

    Returns
    -------
    list[WindowResolutionRecord] — windows at "era" or "month" tier, parent_id=None
    (parent assignment is done separately by assign_parent_window_ids).
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
        duration = interval.exit_jd - interval.enter_jd
        tier = "era" if duration >= ERA_MIN_DAYS else "month"

        records.append(WindowResolutionRecord(
            window_id=str(uuid.uuid4()),
            parent_window_id=None,
            resolution_tier=tier,
            enter_jd=interval.enter_jd,
            exit_jd=interval.exit_jd,
            peak_jd=interval.peak_jd,
            peak_lambda=interval.peak_lambda,
        ))

    return records


# ---------------------------------------------------------------------------
# Month window builder
# ---------------------------------------------------------------------------

def build_month_windows(
    swe,
    context,
    era_windows: list[WindowResolutionRecord],
    threshold_config: ThresholdConfig,
) -> list[WindowResolutionRecord]:
    """Build month-level windows by sub-dividing era windows at ~30-day steps.

    For each era window, evaluates λ_v3 at 30-day coarse steps within the
    [enter_jd, exit_jd] span. Each step becomes a month-level window record.
    Peak λ_v3 within the step is determined by evaluating at the step midpoint.

    I4: if era_windows is empty, returns [] honestly.

    Parameters
    ----------
    swe                 Swiss Ephemeris handle.
    context             ClassContext (pre-fetched, immutable).
    era_windows         Era-tier windows to subdivide.
    threshold_config    ThresholdConfig (for peak evaluation context).

    Returns
    -------
    list[WindowResolutionRecord] at "month" tier, parent_id=None.
    """
    if not era_windows:
        return []

    records: list[WindowResolutionRecord] = []

    for era_win in era_windows:
        jd = era_win.enter_jd
        while jd < era_win.exit_jd:
            step_enter = jd
            step_exit = min(jd + MONTH_STEP_DAYS, era_win.exit_jd)

            if step_exit <= step_enter:
                break

            # Peak at the midpoint of this 30-day sub-window
            mid_jd = 0.5 * (step_enter + step_exit)
            try:
                peak_lambda = _eval_single(swe, context, mid_jd)
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "[resolution_hierarchy] build_month_windows: _eval_single "
                    "failed at jd=%.4f: %s — using 0.0", mid_jd, exc,
                )
                peak_lambda = 0.0

            records.append(WindowResolutionRecord(
                window_id=str(uuid.uuid4()),
                parent_window_id=None,
                resolution_tier="month",
                enter_jd=step_enter,
                exit_jd=step_exit,
                peak_jd=mid_jd,
                peak_lambda=peak_lambda,
            ))

            jd += MONTH_STEP_DAYS

    return records


# ---------------------------------------------------------------------------
# Day window builder
# ---------------------------------------------------------------------------

def build_day_windows(
    swe,
    context,
    month_windows: list[WindowResolutionRecord],
    threshold_config: ThresholdConfig,
) -> list[WindowResolutionRecord]:
    """Build day-level windows by sub-dividing month windows at 1-day steps.

    For each month window, evaluates λ_v3 at the midpoint of each calendar-day
    sub-window within [enter_jd, exit_jd].

    I4: if month_windows is empty, returns [] honestly.

    Parameters
    ----------
    swe                 Swiss Ephemeris handle.
    context             ClassContext (pre-fetched, immutable).
    month_windows       Month-tier windows to subdivide.
    threshold_config    ThresholdConfig (for peak evaluation context).

    Returns
    -------
    list[WindowResolutionRecord] at "day" tier, parent_id=None.
    """
    if not month_windows:
        return []

    records: list[WindowResolutionRecord] = []

    for month_win in month_windows:
        jd = month_win.enter_jd
        while jd < month_win.exit_jd:
            step_enter = jd
            step_exit = min(jd + DAY_STEP_DAYS, month_win.exit_jd)

            if step_exit <= step_enter:
                break

            mid_jd = 0.5 * (step_enter + step_exit)
            try:
                peak_lambda = _eval_single(swe, context, mid_jd)
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "[resolution_hierarchy] build_day_windows: _eval_single "
                    "failed at jd=%.4f: %s — using 0.0", mid_jd, exc,
                )
                peak_lambda = 0.0

            records.append(WindowResolutionRecord(
                window_id=str(uuid.uuid4()),
                parent_window_id=None,
                resolution_tier="day",
                enter_jd=step_enter,
                exit_jd=step_exit,
                peak_jd=mid_jd,
                peak_lambda=peak_lambda,
            ))

            jd += DAY_STEP_DAYS

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
    """Build the full multi-resolution hierarchy for a given search range.

    Calls all three tier builders in order (era → month → day), then runs
    assign_parent_window_ids on the combined flat list to wire up the tree.

    I4: empty/sparse inputs → honest empty HierarchyResult with 0 counts.
    No windows are fabricated.

    Parameters
    ----------
    swe                 Swiss Ephemeris handle.
    context             ClassContext (pre-fetched, immutable).
    start_jd            Search range start (Julian Day).
    end_jd              Search range end (Julian Day).
    threshold_config    ThresholdConfig from W1.4.

    Returns
    -------
    HierarchyResult with era/month/day window lists and resolution_facet.
    """
    # 1. Era tier (calls interval_solver, classifies by duration)
    raw_era = build_era_windows(swe, context, start_jd, end_jd, threshold_config)

    # Separate records by their tier classification from build_era_windows.
    # build_era_windows may return "month"-tier windows (short intervals); keep them.
    true_era_windows = [w for w in raw_era if w.resolution_tier == "era"]
    # month windows that came out of build_era_windows (short intervals < ERA_MIN_DAYS)
    auto_month_windows = [w for w in raw_era if w.resolution_tier == "month"]

    # 2. Month tier: sub-divide true era windows
    subdivided_month_windows = build_month_windows(
        swe, context, true_era_windows, threshold_config,
    )
    all_month_windows = auto_month_windows + subdivided_month_windows

    # 3. Day tier: sub-divide all month windows
    all_day_windows = build_day_windows(
        swe, context, all_month_windows, threshold_config,
    )

    # 4. Assign parent_window_ids across the entire flat pool
    all_windows = true_era_windows + all_month_windows + all_day_windows
    all_windows_with_parents = assign_parent_window_ids(all_windows)

    # Partition back into tiers
    era_out = [w for w in all_windows_with_parents if w.resolution_tier == "era"]
    month_out = [w for w in all_windows_with_parents if w.resolution_tier == "month"]
    day_out = [w for w in all_windows_with_parents if w.resolution_tier == "day"]

    resolution_facet: dict[str, int] = {
        "era": len(era_out),
        "month": len(month_out),
        "day": len(day_out),
    }

    logger.info(
        "[resolution_hierarchy] build_resolution_hierarchy: "
        "era=%d month=%d day=%d — start=%.4f end=%.4f",
        len(era_out), len(month_out), len(day_out), start_jd, end_jd,
    )

    return HierarchyResult(
        era_windows=era_out,
        month_windows=month_out,
        day_windows=day_out,
        resolution_facet=resolution_facet,
    )


__all__ = [
    "RESOLUTION_TIERS",
    "ERA_BODIES",
    "ERA_MIN_DAYS",
    "WindowResolutionRecord",
    "HierarchyResult",
    "assign_parent_window_ids",
    "build_era_windows",
    "build_month_windows",
    "build_day_windows",
    "build_resolution_hierarchy",
]
