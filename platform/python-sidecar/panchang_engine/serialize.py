"""
serialize.py — JSON serialization for panchang_engine Panchang dataclass.

panchang_to_dict(p: Panchang) -> dict

Output shape matches PANCHANG_DAILY_v1_0.md §2 (the JSONB column shapes),
ensuring that 4C-2's cache writes/reads are byte-identical to engine-direct
compute output.

Field mapping rules:
  - datetime → ISO 8601 string with Z for UTC
  - Anga → {"id": int, "name": str, "end_utc": "...Z"}
  - Timing → {"label": str, "start_utc": "...Z", "end_utc": "...Z"}
  - PlanetState → flat dict with all fields
  - special_yogas → list[dict] — the detect_all_special_yogas output shape

Phase: 4C-3
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Panchang, Anga, Timing, PlanetState


def _dt_to_iso(dt: datetime | None) -> str | None:
    """
    Convert a UTC datetime to an ISO 8601 string ending in 'Z'.
    Returns None if dt is None (moonrise/moonset can be None on some days).
    """
    if dt is None:
        return None
    # Ensure we treat the datetime as UTC
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _anga_to_dict(anga: "Anga") -> dict:
    """Serialize an Anga (tithi, nakshatra, yoga, karana, vara) to dict."""
    return {
        "id": anga.id,
        "name": anga.name,
        "end_utc": _dt_to_iso(anga.end_utc),
    }


def _timing_to_dict(timing: "Timing") -> dict:
    """Serialize a Timing (inauspicious/auspicious window) to dict."""
    return {
        "label": timing.label,
        "start_utc": _dt_to_iso(timing.start_utc),
        "end_utc": _dt_to_iso(timing.end_utc),
    }


def _planet_state_to_dict(ps: "PlanetState") -> dict:
    """Serialize a PlanetState to a flat dict matching the PANCHANG_DAILY planets JSONB shape."""
    return {
        "name": ps.name,
        "longitude_sidereal": ps.longitude_sidereal,
        "sign_id": ps.sign_id,
        "sign_name": ps.sign_name,
        "nakshatra_id": ps.nakshatra_id,
        "nakshatra_name": ps.nakshatra_name,
        "nakshatra_pada": ps.nakshatra_pada,
        "retrograde": ps.retrograde,
        "combust": ps.combust,
    }


def _serialize_choghadiya(choghadiya: dict) -> dict:
    """
    Serialize the choghadiya dict.
    choghadiya = {"day": [Timing...], "night": [Timing...]}
    Each list element may be a Timing dataclass or already a dict (defensive).
    """
    result = {}
    for period_key in ("day", "night"):
        entries = choghadiya.get(period_key, [])
        serialized = []
        for entry in entries:
            if hasattr(entry, "label"):
                serialized.append(_timing_to_dict(entry))
            else:
                # Already a dict — pass through with datetime coercion
                serialized.append({
                    k: (_dt_to_iso(v) if isinstance(v, datetime) else v)
                    for k, v in entry.items()
                })
        result[period_key] = serialized
    return result


def _serialize_special_yoga(yoga_dict: dict) -> dict:
    """
    Serialize one special yoga entry.
    Input shape from detect_all_special_yogas:
        {"yoga": str, "start_utc": datetime, "end_utc": datetime,
         "strength": str, "stars": int}  (stars may be absent in some entries)
    Output shape per PANCHANG_DAILY_v1_0.md §2:
        {"yoga": str, "start_utc": "...Z", "end_utc": "...Z", "strength": str, "stars": int}
    """
    out: dict = {}
    for k, v in yoga_dict.items():
        if isinstance(v, datetime):
            out[k] = _dt_to_iso(v)
        else:
            out[k] = v
    return out


def panchang_to_dict(p: "Panchang") -> dict:
    """
    Serialize a Panchang dataclass to a JSON-serializable dict.
    Output matches PANCHANG_DAILY_v1_0.md §2 JSONB column shapes.

    All datetimes become ISO 8601 strings ending in Z (UTC).
    All nested dataclasses (Anga, Timing, PlanetState) are serialized recursively.
    The dict is JSON-serializable — no datetime / dataclass leaks.
    """
    # Planets: list[PlanetState] → keyed by planet name (lowercase) for JSONB shape
    # PANCHANG_DAILY §5 shows: {sun: {...}, moon: {...}, ...}
    planets_dict = {}
    for ps in p.planets:
        key = ps.name.lower()
        planets_dict[key] = _planet_state_to_dict(ps)

    # Inauspicious: list[Timing] → list of dicts
    inauspicious = [_timing_to_dict(t) for t in p.inauspicious]

    # Auspicious: list[Timing] → list of dicts
    auspicious = [_timing_to_dict(t) for t in p.auspicious]

    # Hora: list[Timing] → list of dicts
    hora = [_timing_to_dict(t) for t in p.hora]

    # Special yogas: list[dict] → serialize datetime values inside each dict
    special_yogas = [_serialize_special_yoga(y) for y in p.special_yogas]

    return {
        # Identity
        "date": p.date.isoformat(),
        "lat": p.lat,
        "lon": p.lon,
        "tz_offset_minutes": p.tz_offset_minutes,
        # Sun / Moon timings
        "sunrise_utc": _dt_to_iso(p.sunrise_utc),
        "sunset_utc": _dt_to_iso(p.sunset_utc),
        "moonrise_utc": _dt_to_iso(p.moonrise_utc),
        "moonset_utc": _dt_to_iso(p.moonset_utc),
        # 5 angas
        "tithi": _anga_to_dict(p.tithi),
        "nakshatra": _anga_to_dict(p.nakshatra),
        "yoga": _anga_to_dict(p.yoga),
        "karana_first": _anga_to_dict(p.karana_first),
        "karana_second": _anga_to_dict(p.karana_second),
        "vara": _anga_to_dict(p.vara),
        "paksha": p.paksha,
        # Timings
        "inauspicious": inauspicious,
        "auspicious": auspicious,
        "choghadiya": _serialize_choghadiya(p.choghadiya),
        "hora": hora,
        # Special yogas
        "special_yogas": special_yogas,
        # Planetary positions at sunrise
        "planets": planets_dict,
        # Audit
        "computation_version": p.computation_version,
        "ephemeris_version": p.ephemeris_version,
    }
