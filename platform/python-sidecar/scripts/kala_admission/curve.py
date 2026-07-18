"""
curve.py -- v1-baseline curve construction, ported from
platform/scripts/audit/t0_retrodiction/lib/curve.ts (same DEPTH_WEIGHT,
same dasha-lord-confluence formula, same percentile/local-max helpers).

WHAT CURVE THIS IS, AND WHY (same rationale as the TS original): the
Vimsottari dasha-period table has exactly the right natural granularity for
a +/-45-day retrodiction test -- MD spans years, AD ~MD/9, PD ~AD/9. At
each date, sum a depth-weighted contribution for every active nested dasha
level (MD/AD/PD) whose running lord is one of a mechanism's significator
grahas, weighting deeper levels more heavily. This is the T-0 INTERIM proxy
(`peak_basis: 'dasha_lord_confluence_v1'`), not a re-derivation of a shipped
transit kernel.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

MS_PER_DAY = 1

# Deeper (more localized) dasha levels weight more heavily.
DEPTH_WEIGHT: dict[int, float] = {1: 1, 2: 2, 3: 4, 4: 8}


@dataclass(frozen=True)
class DashaPeriod:
    level: int
    lord: str
    start: date
    end: date


@dataclass(frozen=True)
class CurvePoint:
    date: date
    intensity: float


def period_at(periods: list[DashaPeriod], level: int, d: date) -> Optional[DashaPeriod]:
    for p in periods:
        if p.level == level and p.start <= d < p.end:
            return p
    return None


def intensity_at(periods: list[DashaPeriod], significators: dict[str, float], d: date) -> float:
    total = 0.0
    for level in (1, 2, 3, 4):
        p = period_at(periods, level, d)
        if p is None:
            continue
        w = significators.get(p.lord)
        if w:
            total += DEPTH_WEIGHT[level] * w
    return total


def build_curve(
    periods: list[DashaPeriod],
    significators: dict[str, float],
    range_start: date,
    range_end: date,
    step_days: int,
) -> list[CurvePoint]:
    out: list[CurvePoint] = []
    d = range_start
    while d <= range_end:
        out.append(CurvePoint(date=d, intensity=intensity_at(periods, significators, d)))
        d = d + timedelta(days=step_days)
    return out


def percentile_threshold(curve: list[CurvePoint], p: float) -> float:
    """Value at the given percentile (0..1), nearest-rank -- same formula as curve.ts."""
    if not curve:
        return 0.0
    import math

    sorted_vals = sorted(c.intensity for c in curve)
    idx = min(len(sorted_vals) - 1, max(0, math.ceil(p * len(sorted_vals)) - 1))
    return sorted_vals[idx]


def top_decile_threshold(curve: list[CurvePoint]) -> float:
    return percentile_threshold(curve, 0.9)


def top_tercile_threshold(curve: list[CurvePoint]) -> float:
    return percentile_threshold(curve, 2.0 / 3.0)


def local_max(curve: list[CurvePoint], center: date, window_days: int) -> Optional[CurvePoint]:
    lo = center - timedelta(days=window_days)
    hi = center + timedelta(days=window_days)
    best: Optional[CurvePoint] = None
    for pt in curve:
        if pt.date < lo or pt.date > hi:
            continue
        if best is None or pt.intensity > best.intensity:
            best = pt
    return best


def fraction_at_or_above(curve: list[CurvePoint], threshold: float) -> float:
    if not curve:
        return 0.0
    n = sum(1 for c in curve if c.intensity >= threshold)
    return n / len(curve)


def variance(curve: list[CurvePoint]) -> float:
    if not curve:
        return 0.0
    mean = sum(c.intensity for c in curve) / len(curve)
    return sum((c.intensity - mean) ** 2 for c in curve) / len(curve)
