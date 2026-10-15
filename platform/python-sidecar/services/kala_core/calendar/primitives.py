"""Exact-instant pañcāṅga primitives; location is never defaulted."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CalendarLocation:
    lat: float
    lon: float
    tz_offset_minutes: int

    @classmethod
    def require(cls, value: "CalendarLocation | dict | None") -> "CalendarLocation":
        if value is None:
            raise ValueError("calendar location is required; no default location exists")
        if isinstance(value, cls):
            return value
        if not isinstance(value, dict):
            raise ValueError("calendar location must be CalendarLocation or a mapping")
        missing = [key for key in ("lat", "lon", "tz_offset_minutes") if key not in value]
        if missing:
            raise ValueError(f"calendar location is missing required keys: {missing}")
        location = cls(**{key: value[key] for key in ("lat", "lon", "tz_offset_minutes")})
        if not -90 <= location.lat <= 90:
            raise ValueError(f"calendar location lat out of range: {location.lat}")
        if not -180 <= location.lon <= 180:
            raise ValueError(f"calendar location lon out of range: {location.lon}")
        return location


@dataclass(frozen=True)
class PanchangaPrimitives:
    """The five exact-instant angas, with provenance retained for a consumer."""
    instant: datetime
    location: CalendarLocation
    tithi_id: int
    vara_id: int
    nakshatra_id: int
    yoga_id: int
    karana_id: int
    tithi_end_utc: datetime
    nakshatra_end_utc: datetime
    yoga_end_utc: datetime
    karana_end_utc: datetime


def panchanga_at(instant: datetime, location: CalendarLocation | dict | None) -> PanchangaPrimitives:
    """Compute primitives at ``instant``; callers must explicitly provide location."""
    if not isinstance(instant, datetime):
        raise ValueError("calendar instant must be a datetime")
    resolved = CalendarLocation.require(location)
    from panchang_engine import panchanga_instant

    value = panchanga_instant(instant, resolved.lat, resolved.lon, resolved.tz_offset_minutes)
    return PanchangaPrimitives(
        instant=instant,
        location=resolved,
        tithi_id=value.tithi.id,
        vara_id=value.vara.id,
        nakshatra_id=value.nakshatra.id,
        yoga_id=value.yoga.id,
        karana_id=value.karana.id,
        tithi_end_utc=value.tithi.end_utc,
        nakshatra_end_utc=value.nakshatra.end_utc,
        yoga_end_utc=value.yoga.end_utc,
        karana_end_utc=value.karana.end_utc,
    )
