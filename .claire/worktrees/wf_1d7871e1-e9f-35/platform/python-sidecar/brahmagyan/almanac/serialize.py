"""brahmagyan.almanac.serialize — AlmanacDay → JSON-serializable dict."""
from datetime import datetime, date
from typing import Optional


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.isoformat()


def _anga_to_dict(anga) -> dict:
    """Convert a panchang_engine.Anga to a plain dict."""
    return {
        "id": anga.id,
        "name": anga.name,
        "end_utc": _iso(anga.end_utc),
    }


def _timing_to_dict(t) -> dict:
    return {
        "label": t.label,
        "start_utc": _iso(t.start_utc),
        "end_utc": _iso(t.end_utc),
    }


def almanac_day_to_dict(day) -> dict:
    """
    Convert an AlmanacDay dataclass to a JSON-serializable dict.
    All datetime fields are converted to ISO 8601 strings (UTC).
    """
    return {
        "date": day.date.isoformat(),
        "location": {
            "lat": day.location.lat,
            "lon": day.location.lon,
            "tz_name": day.location.tz_name,
            "label": day.location.label,
        },
        "tz_offset_minutes": day.tz_offset_minutes,
        "sunrise_utc": _iso(day.sunrise_utc),
        "sunset_utc": _iso(day.sunset_utc),
        "moonrise_utc": _iso(day.moonrise_utc),
        "moonset_utc": _iso(day.moonset_utc),
        "tithi": day.tithi,
        "vara": day.vara,
        "nakshatra": day.nakshatra,
        "yoga": day.yoga,
        "karana": day.karana,
        "choghadiya": day.choghadiya,
        "hora": day.hora,
        "rahu_kalam": day.rahu_kalam,
        "gulika_kalam": day.gulika_kalam,
        "yamagandam": day.yamagandam,
        "special_yogas": day.special_yogas,
        "computation_version": day.computation_version,
        "ephemeris_version": day.ephemeris_version,
        "source": day.source,
    }
