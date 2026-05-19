"""
Sidecar /transit_search — live-compute aspect + conjunction event search (§4.D).

For ingress and station queries, the TypeScript query_transit_event tool reads
Postgres tables directly (ephemeris_daily + retrogrades). This endpoint is
only invoked for aspect and conjunction live-compute cases.

Window cap: ±10 years from start_date (latency guard per approved decision §4.D §3.4).
Lahiri sidereal throughout (approved decision §4.D §3.1).
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Literal, Optional
import swisseph as swe

from pipeline.transit_search import (
    find_aspect_events,
    find_conjunction_events,
    TransitEvent,
)

router = APIRouter()


class TransitSearchRequest(BaseModel):
    event_type: Literal["aspect", "conjunction"]
    start_date: str                     # ISO YYYY-MM-DD
    end_date: str                       # ISO YYYY-MM-DD; max 10 years from start_date
    # For aspect queries:
    transit_planet: Optional[str] = None
    target_longitude_deg: Optional[float] = None
    target_planet_natal_longitude_deg: Optional[float] = None
    aspect_degrees: list[int] = Field(default_factory=lambda: [0, 60, 90, 120, 180])
    # For conjunction queries:
    planet_a: Optional[str] = None
    planet_b: Optional[str] = None
    # Common:
    orb_deg: float = 1.0               # clamped to [0.0, 3.0] server-side


class TransitEventResponse(BaseModel):
    event_type: str
    event_jd: float
    event_datetime_ist: str
    transit_planet: str
    secondary_planet: Optional[str]
    exact_longitude_deg: float
    orb_at_event_deg: float
    sign: str
    nakshatra: str
    extra: dict


@router.post("/transit_search", response_model=list[TransitEventResponse])
async def transit_search(req: TransitSearchRequest):
    from datetime import datetime as _dt

    try:
        start_dt = _dt.fromisoformat(req.start_date)
        end_dt = _dt.fromisoformat(req.end_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid date: {exc}")

    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    if (end_dt - start_dt).days > 365 * 10:
        raise HTTPException(status_code=400, detail="Window exceeds ±10-year cap")

    start_jd = swe.julday(start_dt.year, start_dt.month, start_dt.day, 0.0)
    end_jd = swe.julday(end_dt.year, end_dt.month, end_dt.day, 0.0)
    orb = max(0.0, min(3.0, req.orb_deg))

    if req.event_type == "aspect":
        if not req.transit_planet:
            raise HTTPException(status_code=400, detail="transit_planet required for aspect")
        target_lon = req.target_planet_natal_longitude_deg or req.target_longitude_deg
        if target_lon is None:
            raise HTTPException(status_code=400, detail="target_longitude_deg or target_planet_natal_longitude_deg required")
        events: list[TransitEvent] = find_aspect_events(
            swe,
            req.transit_planet,
            target_lon,
            req.aspect_degrees,
            orb,
            start_jd,
            end_jd,
        )
    else:  # conjunction
        if not req.planet_a or not req.planet_b:
            raise HTTPException(status_code=400, detail="planet_a and planet_b required for conjunction")
        events = find_conjunction_events(
            swe,
            req.planet_a,
            req.planet_b,
            orb,
            start_jd,
            end_jd,
        )

    return [
        TransitEventResponse(
            event_type=e.event_type,
            event_jd=e.event_jd,
            event_datetime_ist=e.event_datetime_ist,
            transit_planet=e.transit_planet,
            secondary_planet=e.secondary_planet,
            exact_longitude_deg=e.exact_longitude_deg,
            orb_at_event_deg=e.orb_at_event_deg,
            sign=e.sign,
            nakshatra=e.nakshatra,
            extra=e.extra,
        )
        for e in events
    ]
