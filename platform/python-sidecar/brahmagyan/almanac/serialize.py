"""
brahmagyan.almanac.serialize — AlmanacDay → JSON-serializable dict.

All datetime fields are serialized as ISO 8601 strings (UTC-aware, with Z suffix).
Provenance envelope (computation_version, ephemeris_version, source) is always
included so callers can trace which engine version produced the result.
"""
from datetime import datetime
from typing import Optional


def _iso(dt: Optional[datetime]) -> Optional[str]:
    """Convert a UTC-aware datetime to ISO 8601 string, or None."""
    if dt is None:
        return None
    return dt.isoformat()


def _timing_to_dict(t) -> dict:
    """Serialize a panchang_engine.Timing to a plain dict."""
    return {
        "label": t.label,
        "start_utc": _iso(t.start_utc),
        "end_utc": _iso(t.end_utc),
    }


def almanac_day_to_dict(day) -> dict:
    """
    Convert an AlmanacDay dataclass to a JSON-serializable dict.

    Canonical structure matches the brahmagyan.almanac contract (L0 §C 0.8):
      - Five angas (tithi, vara, nakshatra, yoga, karana) with end_utc
      - Day-quality windows (choghadiya, hora, rahu_kalam, gulika_kalam, yamagandam)
      - Special yogas list
      - Provenance envelope
    """
    # Inline special_yogas — already dicts from the engine
    return {
        "date": day.date.isoformat(),
        "location": {
            "lat": day.location.lat,
            "lon": day.location.lon,
            "tz_name": day.location.tz_name,
            "label": day.location.label,
            "cache_key": day.location.cache_key,
        },
        "tz_offset_minutes": day.tz_offset_minutes,
        "sunrise_utc": _iso(day.sunrise_utc),
        "sunset_utc": _iso(day.sunset_utc),
        "moonrise_utc": _iso(day.moonrise_utc),
        "moonset_utc": _iso(day.moonset_utc),
        # Five angas
        "tithi": day.tithi,
        "vara": day.vara,
        "nakshatra": day.nakshatra,
        "yoga": day.yoga,
        "karana": day.karana,
        # Day-quality windows
        "choghadiya": day.choghadiya,
        "hora": day.hora,
        "rahu_kalam": day.rahu_kalam,
        "gulika_kalam": day.gulika_kalam,
        "yamagandam": day.yamagandam,
        "special_yogas": day.special_yogas,
        # Provenance
        "computation_version": day.computation_version,
        "ephemeris_version": day.ephemeris_version,
        "source": day.source,
    }
