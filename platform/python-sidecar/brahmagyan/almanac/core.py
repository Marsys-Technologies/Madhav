"""
brahmagyan.almanac.core — Core almanac.query() implementation.

This is the primary callable for the brahmagyan.almanac asset (BG-0-8).

Usage
-----
    from brahmagyan.almanac import query, AlmanacLocation, AlmanacDateRange

    location = AlmanacLocation(lat=20.3, lon=85.8, tz_name="Asia/Kolkata",
                               label="Bhubaneswar")
    date_range = AlmanacDateRange(date_from=date(1984, 2, 5),
                                   date_to=date(1984, 2, 5))
    results = query(date_range, location)
    day = results[0]
    # day.tithi.name == "Shukla Tritiya"
    # day.vara.name  == "Ravivara"
    # etc.

Architecture
------------
1. Normalize lat/lon to 0.1° (AlmanacLocation constructor).
2. For each date in [date_from, date_to]:
   a. Resolve UTC offset for that specific date via resolve_tz_offset_minutes()
      — handles DST, half-hour zones, non-integer offsets.
   b. Check in-process LRU cache (keyed by date + location.cache_key).
   c. On miss: call panchang_engine.compute_panchang() → Panchang.
   d. Convert Panchang to AlmanacDay (adds provenance, normalizes dicts).
   e. Store in cache (tagged source="cache" for future hits).
3. Return list[AlmanacDay].

The function is safe to call with large date ranges (up to 366 days per call,
as enforced by AlmanacDateRange). For ranges > 31 days the computation may take
several seconds; callers should consider asynchronous patterns for production
use.

Error handling
--------------
- OutOfRangeError from the engine (polar latitudes): propagated as-is.
- ValidationError: propagated as-is.
- zoneinfo.ZoneInfoNotFoundError: raised as ValueError with a clear message.
- Per-date errors do NOT abort the entire range; the error is captured in a
  special "error" AlmanacDay substitute dict with the exception message, and
  computation continues for the remaining dates.
"""
from datetime import date, timedelta
from typing import Optional

from panchang_engine import compute_panchang
from panchang_engine.types import Panchang, Anga, Timing
from panchang_engine.exceptions import PanchangEngineError, OutOfRangeError, ValidationError
from panchang_engine.shastra_tables import NAKSHATRA_NAMES

from .types import AlmanacDay, AlmanacLocation, AlmanacDateRange
from .tz_utils import resolve_tz_offset_minutes, normalize_location
from .cache import cache_get, cache_put


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def query(date_range: AlmanacDateRange, location: AlmanacLocation) -> list:
    """
    Compute (or retrieve from cache) the full almanac for each date in the
    requested range at the given location.

    Args:
        date_range : AlmanacDateRange — inclusive [date_from, date_to]
        location   : AlmanacLocation — normalized lat/lon + IANA tz_name

    Returns:
        list[AlmanacDay] — one entry per date in the range (inclusive),
        in chronological order.

    Raises:
        ValueError  : if tz_name is unknown or date_range is invalid
        ValidationError : if lat/lon are out of range
    """
    results = []
    current = date_range.date_from

    while current <= date_range.date_to:
        # Resolve UTC offset for THIS specific date (handles DST)
        tz_offset = resolve_tz_offset_minutes(current, location.tz_name)

        # Check cache
        cached = cache_get(current, location.cache_key)
        if cached is not None:
            # Return a copy tagged source="cache"
            results.append(_tag_source(cached, "cache"))
            current += timedelta(days=1)
            continue

        # Compute
        try:
            panchang = compute_panchang(current, location.lat, location.lon, tz_offset)
        except (ValidationError, OutOfRangeError, PanchangEngineError) as exc:
            # Per-date errors: capture and continue
            results.append(_make_error_day(current, location, tz_offset, str(exc)))
            current += timedelta(days=1)
            continue

        # Convert to AlmanacDay
        day = _panchang_to_almanac_day(panchang, location, tz_offset)

        # Store in cache (tagged source="engine")
        cache_put(current, location.cache_key, day)

        results.append(day)
        current += timedelta(days=1)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _timing_dict(t: Optional[Timing]) -> Optional[dict]:
    if t is None:
        return None
    return {
        "label": t.label,
        "start_utc": t.start_utc.isoformat(),
        "end_utc": t.end_utc.isoformat(),
    }


def _anga_dict(a: Anga, extra: Optional[dict] = None) -> dict:
    d = {
        "id": a.id,
        "name": a.name,
        "end_utc": a.end_utc.isoformat(),
    }
    if extra:
        d.update(extra)
    return d


def _choghadiya_dict(chog: dict) -> dict:
    return {
        "day": [_timing_dict(t) for t in chog.get("day", [])],
        "night": [_timing_dict(t) for t in chog.get("night", [])],
    }


def _panchang_to_almanac_day(p: Panchang, location: AlmanacLocation,
                              tz_offset: int) -> AlmanacDay:
    """Convert a panchang_engine.Panchang to a brahmagyan.almanac.AlmanacDay."""

    # Tithi — add paksha field
    tithi_dict = _anga_dict(p.tithi, extra={"paksha": p.paksha})

    # Vara
    vara_dict = _anga_dict(p.vara)

    # Nakshatra — add pada
    moon = next((ps for ps in p.planets if ps.name == "Moon"), None)
    pada = moon.nakshatra_pada if moon is not None else None
    nak_dict = _anga_dict(p.nakshatra, extra={"pada": pada})

    # Yoga
    yoga_dict = _anga_dict(p.yoga)

    # Karana — first karana at sunrise
    karana_dict = _anga_dict(p.karana_first)

    # Choghadiya
    chog_dict = _choghadiya_dict(p.choghadiya)

    # Hora — 24 planetary hours
    hora_list = [_timing_dict(t) for t in p.hora]

    # Inauspicious windows — extract by label
    inauspicious_by_label = {t.label: t for t in p.inauspicious}
    rahu_kalam_dict = _timing_dict(inauspicious_by_label.get("rahu_kalam"))
    gulika_kalam_dict = _timing_dict(inauspicious_by_label.get("gulika_kalam"))
    yamagandam_dict = _timing_dict(inauspicious_by_label.get("yamagandam"))

    # Special yogas — already list[dict] from engine
    special_yogas = _serialize_special_yogas(p.special_yogas)

    return AlmanacDay(
        date=p.date,
        location=location,
        tz_offset_minutes=tz_offset,
        sunrise_utc=p.sunrise_utc,
        sunset_utc=p.sunset_utc,
        moonrise_utc=p.moonrise_utc,
        moonset_utc=p.moonset_utc,
        tithi=tithi_dict,
        vara=vara_dict,
        nakshatra=nak_dict,
        yoga=yoga_dict,
        karana=karana_dict,
        choghadiya=chog_dict,
        hora=hora_list,
        rahu_kalam=rahu_kalam_dict,
        gulika_kalam=gulika_kalam_dict,
        yamagandam=yamagandam_dict,
        special_yogas=special_yogas,
        computation_version=p.computation_version,
        ephemeris_version=p.ephemeris_version,
        source="engine",
    )


def _serialize_special_yogas(yogas) -> list:
    """
    Normalize special_yogas output from the engine.
    The engine returns a list of dicts with datetime objects embedded.
    We normalize any datetime values to ISO strings.
    """
    from datetime import datetime

    result = []
    for yoga in yogas:
        if isinstance(yoga, dict):
            cleaned = {}
            for k, v in yoga.items():
                if isinstance(v, datetime):
                    cleaned[k] = v.isoformat()
                else:
                    cleaned[k] = v
            result.append(cleaned)
        else:
            # Unexpected type; skip
            pass
    return result


def _tag_source(day: AlmanacDay, source: str) -> AlmanacDay:
    """Return a copy of AlmanacDay with a different source tag."""
    # AlmanacDay is frozen; use object.__setattr__ trick via dataclasses.replace
    from dataclasses import replace
    return replace(day, source=source)


def _make_error_day(d: date, location: AlmanacLocation,
                    tz_offset: int, error_msg: str) -> dict:
    """
    Return a minimal error sentinel dict (not a full AlmanacDay) when
    a single-date computation fails. This lets the range call continue.
    """
    return {
        "date": d.isoformat(),
        "error": error_msg,
        "location": location.cache_key,
        "tz_offset_minutes": tz_offset,
        "source": "error",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Convenience constructors (for clean caller ergonomics)
# ─────────────────────────────────────────────────────────────────────────────

def make_location(lat: float, lon: float, tz_name: str, label: str = "") -> AlmanacLocation:
    """
    Construct an AlmanacLocation with normalized coordinates.

    Args:
        lat     : decimal degrees (+N); will be rounded to 0.1°
        lon     : decimal degrees (+E); will be rounded to 0.1°
        tz_name : IANA timezone string (e.g. "Asia/Kolkata")
        label   : optional human-readable label

    Returns:
        AlmanacLocation with lat/lon rounded to 0.1°
    """
    lat_n, lon_n = normalize_location(lat, lon)
    return AlmanacLocation(lat=lat_n, lon=lon_n, tz_name=tz_name, label=label)
