"""
checks.py -- retrodiction scoring checks, ported and GENERALIZED from
platform/scripts/audit/t0_retrodiction/lib/checks.ts.

T-0's `scoreEvent`/`runBlindBattery` built one fixed curve (the v1
dasha-lord-confluence proxy) per event. This module's `score_event_curve` /
`run_blind_battery_curve` take a CANDIDATE CURVE (already built by
currents.py from a configurable combination of v1 + PERMISSION gate + TRIGGER
signed term) instead of building it inline -- this is what makes the D-3
ADMIT admission loop possible: the same peak-proximity/percentile-threshold
math T-0 already verified is reused unchanged, only the curve fed into it
varies per candidate configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Optional

from .curve import CurvePoint, local_max, percentile_threshold
from .dates import days_between

PROXIMITY_DAYS = 45  # DR-11 (DIS.024)
WINDOW_YEARS = 5
STEP_DAYS = 5

CurveBuilder = Callable[[date, date], list[CurvePoint]]


def _window_for(event_date: date, bounds_start: date, bounds_end: date) -> tuple[date, date]:
    half = timedelta(days=int(WINDOW_YEARS / 2 * 365))
    start = max(event_date - half, bounds_start)
    end = min(event_date + half, bounds_end)
    return start, end


@dataclass
class SingleEventScore:
    event_id: str
    event_date: str
    window_start: str
    window_end: str
    threshold_percentile: float
    threshold_value: float
    peak_date: Optional[str]
    peak_intensity: Optional[float]
    peak_lag_days: Optional[int]
    within_proximity: bool
    at_or_above_threshold: bool
    passed: bool


def score_event_curve(
    build_curve: CurveBuilder,
    event_id: str,
    event_date: date,
    bounds_start: date,
    bounds_end: date,
    percentile: float,
    proximity_days: int = PROXIMITY_DAYS,
) -> SingleEventScore:
    start, end = _window_for(event_date, bounds_start, bounds_end)
    curve = build_curve(start, end)
    threshold = percentile_threshold(curve, percentile)
    peak = local_max(curve, event_date, proximity_days)
    within_proximity = peak is not None
    at_or_above = peak is not None and peak.intensity > 0 and peak.intensity >= threshold
    return SingleEventScore(
        event_id=event_id,
        event_date=event_date.isoformat(),
        window_start=start.isoformat(),
        window_end=end.isoformat(),
        threshold_percentile=percentile,
        threshold_value=threshold,
        peak_date=peak.date.isoformat() if peak else None,
        peak_intensity=peak.intensity if peak else None,
        peak_lag_days=days_between(event_date, peak.date) if peak else None,
        within_proximity=within_proximity,
        at_or_above_threshold=at_or_above,
        passed=within_proximity and at_or_above,
    )


@dataclass
class BlindBatteryResult:
    scored_count: int
    hit_count: int
    hit_rate: float
    per_event: list[SingleEventScore]


def run_blind_battery_curve(
    build_curve_for_event: Callable[[str], CurveBuilder],
    events: list[tuple[str, date]],  # (event_id, date) -- significators resolved inside build_curve_for_event
    bounds_start: date,
    bounds_end: date,
    percentile: float = 2.0 / 3.0,
) -> BlindBatteryResult:
    per_event: list[SingleEventScore] = []
    for event_id, d in events:
        cb = build_curve_for_event(event_id)
        per_event.append(score_event_curve(cb, event_id, d, bounds_start, bounds_end, percentile))
    hits = [s for s in per_event if s.passed]
    return BlindBatteryResult(
        scored_count=len(per_event),
        hit_count=len(hits),
        hit_rate=(len(hits) / len(per_event)) if per_event else 0.0,
        per_event=per_event,
    )
