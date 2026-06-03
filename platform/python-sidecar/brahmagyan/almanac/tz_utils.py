"""
brahmagyan.almanac.tz_utils — IANA timezone / DST / half-hour-zone utilities.

Resolves the UTC offset in minutes for a given (date, IANA tz_name) pair.
Handles:
  - Standard zones (UTC+05:30 = India Standard Time = 330 min)
  - DST transitions within a date range (each date gets its own offset)
  - Half-hour zones (IST +05:30, NST −03:30, ACST +09:30, etc.)
  - Non-integer offsets (NPT +05:45, ACWST +08:45, etc.)
  - UTC itself (offset = 0)

The resolved offset is used as `tz_offset_minutes` in compute_panchang().
Sunrise is computed as the moment the Sun appears above the horizon in local
civil time, so the correct civil offset for the specific date is critical.

Strategy
--------
We use `zoneinfo` (Python 3.9+) with `backports.zoneinfo` as fallback.
For each (date, tz_name) pair we sample the UTC offset at local noon on that
date using `datetime.utcoffset()`, which returns a timedelta. We convert that
to minutes and return it.

This correctly handles:
- DST: IST never changes, but US/Eastern flips by 60 minutes seasonally.
- Half-hour zones: IST = +330 exactly, NST = −210 exactly.
- Sub-30-minute zones: NPT = +345 (UTC+05:45), Chatham = varies.

Fallback
--------
If the IANA name is unrecognised or zoneinfo is unavailable, we fall back to
a hard-coded table of common offsets (covers the 30 most common). If the name
is not in the table either, we raise ValueError with a clear message.
"""
from datetime import date, datetime, timezone, timedelta
from typing import Optional

# ── zoneinfo import (Python 3.9+ stdlib; backport for 3.8) ──────────────────
try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    _HAS_ZONEINFO = True
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo, ZoneInfoNotFoundError  # type: ignore
        _HAS_ZONEINFO = True
    except ImportError:
        _HAS_ZONEINFO = False
        ZoneInfo = None
        ZoneInfoNotFoundError = Exception


# ── Hard-coded fallback table (used when zoneinfo is unavailable) ────────────
# Offset in minutes (positive = east of UTC). Covers 30 most common TZs.
_FALLBACK_TABLE: dict[str, int] = {
    "UTC":                    0,
    "GMT":                    0,
    "Asia/Kolkata":         330,   # IST +05:30
    "Asia/Calcutta":        330,   # alias
    "Asia/Colombo":         330,   # Sri Lanka +05:30
    "Asia/Kathmandu":       345,   # NPT +05:45
    "Asia/Karachi":         300,   # PKT +05:00
    "Asia/Dhaka":           360,   # BST +06:00
    "Asia/Yangon":          390,   # MMT +06:30
    "Asia/Bangkok":         420,   # ICT +07:00
    "Asia/Jakarta":         420,   # WIB +07:00
    "Asia/Singapore":       480,   # SGT +08:00
    "Asia/Shanghai":        480,   # CST +08:00
    "Asia/Tokyo":           540,   # JST +09:00
    "Asia/Seoul":           540,   # KST +09:00
    "Australia/Darwin":     570,   # ACST +09:30
    "Australia/Adelaide":   570,   # ACST (no DST here for fallback)
    "Australia/Sydney":     600,   # AEST +10:00
    "Pacific/Auckland":     720,   # NZST +12:00
    "Europe/London":          0,   # GMT (approx; no DST in fallback)
    "Europe/Paris":          60,   # CET +01:00
    "Europe/Berlin":         60,
    "Europe/Moscow":        180,   # MSK +03:00
    "America/New_York":    -300,   # EST −05:00 (no DST in fallback)
    "America/Chicago":     -360,   # CST −06:00
    "America/Denver":      -420,   # MST −07:00
    "America/Los_Angeles": -480,   # PST −08:00
    "America/Toronto":     -300,   # EST
    "America/Vancouver":   -480,   # PST
    "America/Sao_Paulo":  -180,   # BRT −03:00
    "Pacific/Honolulu":   -600,   # HST −10:00
}


def resolve_tz_offset_minutes(d: date, tz_name: str) -> int:
    """
    Return the UTC offset in *minutes* for the given (date, IANA tz_name).

    The offset is sampled at local noon on `d` (which is well within daylight
    for almost all inhabited zones). This correctly handles:
      - Half-hour zones (IST = 330 min exactly)
      - Non-integer zones (NPT = 345 min exactly)
      - DST transitions (each date gives the right offset for that day)

    Args:
        d       : the local calendar date
        tz_name : IANA timezone identifier, e.g. "Asia/Kolkata"

    Returns:
        UTC offset in minutes (int; may be negative)

    Raises:
        ValueError : if tz_name is unknown and not in the fallback table
    """
    if _HAS_ZONEINFO and ZoneInfo is not None:
        try:
            tz = ZoneInfo(tz_name)
            # Sample at local noon to avoid edge cases near midnight DST flips
            local_noon = datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=tz)
            delta = local_noon.utcoffset()
            if delta is None:
                raise ValueError(f"utcoffset() returned None for {tz_name!r} on {d}")
            total_seconds = int(delta.total_seconds())
            minutes = total_seconds // 60
            return minutes
        except ZoneInfoNotFoundError:
            pass  # fall through to table lookup

    # Fallback table
    if tz_name in _FALLBACK_TABLE:
        return _FALLBACK_TABLE[tz_name]

    raise ValueError(
        f"Unknown IANA timezone {tz_name!r}. "
        "Install 'tzdata' (pip install tzdata) or add the zone to "
        "brahmagyan.almanac.tz_utils._FALLBACK_TABLE."
    )


def normalize_location(lat: float, lon: float) -> tuple[float, float]:
    """
    Round lat/lon to 0.1° for cache-key normalization.
    0.1° ≈ 11 km at the equator — adequate for panchang purposes.

    Returns:
        (lat_rounded, lon_rounded) as floats rounded to 1 decimal place.
    """
    return round(lat, 1), round(lon, 1)
