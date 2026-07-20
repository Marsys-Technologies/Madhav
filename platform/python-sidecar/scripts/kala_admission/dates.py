"""
dates.py -- date-math primitives for the D-3 ADMIT kernel-admission harness.

Direct Python port of
platform/scripts/audit/t0_retrodiction/lib/dates.ts (same function names,
same semantics -- UTC-midnight dates, signed day differences). No network,
no astrology -- pure calendar math.
"""
from __future__ import annotations

from datetime import date, timedelta


def parse_date(iso: str) -> date:
    """Parses a 'YYYY-MM-DD' string into a date object."""
    y, m, d = (int(x) for x in iso[:10].split("-"))
    return date(y, m, d)


def to_iso_date(d: date) -> str:
    return d.isoformat()


def add_days(d: date, days: int) -> date:
    return d + timedelta(days=days)


def days_between(a: date, b: date) -> int:
    """Signed day difference b - a."""
    return (b - a).days


def is_within_days(center: date, candidate: date, window_days: int) -> bool:
    return abs(days_between(center, candidate)) <= window_days


def clamp_date(d: date, dmin: date, dmax: date) -> date:
    if d < dmin:
        return dmin
    if d > dmax:
        return dmax
    return d
