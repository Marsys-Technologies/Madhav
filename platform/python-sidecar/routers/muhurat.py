"""HTTP adapter for the Panchang Muhurat Finder.

This route serves the active Panchang UI contract at ``POST
/api/compute/muhurat``.  The deterministic scoring implementation lives in
``muhurat.finder``; this module only validates transport input, hydrates the
optional native overlay, calls the direct engine, and serializes windows.
"""
from __future__ import annotations

import logging
import os
from datetime import date as DateType, datetime, time as TimeType
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import psycopg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from muhurat.finder import EVENTS_MVP, find_muhurat, is_supported_event
from panchang_engine.exceptions import OutOfRangeError, PanchangEngineError, ValidationError
from panchang_engine.types import MuhuratWindow, NatalChart

logger = logging.getLogger(__name__)
router = APIRouter()


class MuhuratRequest(BaseModel):
    event: str
    date_from: DateType
    date_to: DateType
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tz_offset_minutes: int = Field(330, ge=-720, le=840)
    chart_id: Optional[str] = None
    top_n: int = Field(10, ge=1, le=90)


def _window_to_dict(window: MuhuratWindow) -> dict:
    return {
        "event": window.event,
        "start_utc": window.start_utc.isoformat() if window.start_utc else None,
        "end_utc": window.end_utc.isoformat() if window.end_utc else None,
        "star_rating": window.star_rating,
        "score": round(window.score, 2),
        "breakdown": window.breakdown,
    }


def _fetch_native_chart(chart_id: str) -> NatalChart:
    """Compute the natal scorer inputs at the recorded birth instant."""
    from panchang_engine import panchanga_instant

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")

    try:
        with psycopg.connect(db_url) as conn:
            row = conn.execute(
                """
                SELECT birth_date, birth_time, birth_lat, birth_lng, timezone_id
                FROM charts
                WHERE id = %s
                """,
                (chart_id,),
            ).fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Chart lookup unavailable") from exc

    if row is None:
        raise HTTPException(status_code=404, detail=f"Chart {chart_id!r} not found")

    birth_date, birth_time, birth_lat, birth_lng, timezone_id = row
    if birth_date is None or birth_time is None:
        raise HTTPException(status_code=422, detail="Chart lacks birth date or time")
    if birth_lat is None or birth_lng is None:
        raise HTTPException(status_code=422, detail="Chart lacks birth coordinates")
    if not timezone_id:
        raise HTTPException(status_code=422, detail="Chart lacks birth timezone")

    try:
        parsed_time = (
            birth_time
            if isinstance(birth_time, TimeType)
            else TimeType.fromisoformat(str(birth_time))
        )
        birth_instant = datetime.combine(birth_date, parsed_time)
        utc_offset = birth_instant.replace(tzinfo=ZoneInfo(str(timezone_id))).utcoffset()
    except (TypeError, ValueError, ZoneInfoNotFoundError) as exc:
        raise HTTPException(status_code=422, detail="Chart birth time or timezone is invalid") from exc

    if utc_offset is None:
        raise HTTPException(status_code=422, detail="Chart birth timezone has no UTC offset")
    tz_offset_minutes = int(utc_offset.total_seconds() // 60)

    try:
        instant = panchanga_instant(
            birth_instant,
            float(birth_lat),
            float(birth_lng),
            tz_offset_minutes,
        )
    except (ValueError, ValidationError, OutOfRangeError, PanchangEngineError) as exc:
        raise HTTPException(status_code=422, detail=f"Birth chart compute error: {exc}") from exc

    moon = next(
        (planet for planet in instant.planets if getattr(planet, "name", "").lower() == "moon"),
        None,
    )
    if moon is None or instant.lagna is None:
        raise HTTPException(status_code=500, detail="Birth chart Moon or lagna unavailable")

    return NatalChart(
        birth_nakshatra_id=int(instant.nakshatra.id),
        birth_lagna_sign_id=int(instant.lagna.ascendant_sign_id),
        moon_sign_id=int(moon.sign_id),
        active_dasha_lord=None,
    )


@router.post("/muhurat")
async def compute_muhurat_endpoint(req: MuhuratRequest):
    if not is_supported_event(req.event):
        raise HTTPException(
            status_code=422,
            detail=f"Event '{req.event}' not supported. Supported events: {EVENTS_MVP}",
        )
    if req.date_from > req.date_to:
        raise HTTPException(status_code=422, detail="date_to must be >= date_from")
    if (req.date_to - req.date_from).days > 89:
        raise HTTPException(
            status_code=422,
            detail="Date range exceeds 90-day limit; split the request",
        )

    native_chart = _fetch_native_chart(req.chart_id) if req.chart_id else None
    try:
        windows = find_muhurat(
            req.event,
            req.date_from,
            req.date_to,
            lat=req.lat,
            lon=req.lon,
            tz_offset_minutes=req.tz_offset_minutes,
            native_chart=native_chart,
            top_n=req.top_n,
        )
    except (ValueError, ValidationError, OutOfRangeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PanchangEngineError as exc:
        raise HTTPException(status_code=500, detail=f"Engine error: {exc}") from exc

    logger.info(
        "muhurat path=engine-direct event=%s dates=%s..%s lat=%.4f lon=%.4f",
        req.event,
        req.date_from,
        req.date_to,
        req.lat,
        req.lon,
    )
    return {
        "ok": True,
        "windows": [_window_to_dict(window) for window in windows],
        "count": len(windows),
        "event": req.event,
        "supported_events": EVENTS_MVP,
    }
