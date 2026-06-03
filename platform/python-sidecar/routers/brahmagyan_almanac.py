"""
routers/brahmagyan_almanac.py — FastAPI router for the brahmagyan.almanac tool.

Tool: almanac.query(date_range, location)
Path: POST /api/brahmagyan/almanac/query
MCP tool name: brahmagyan_almanac_query

Contract reference: L0_CONTRACT_REGISTRY_SEED_v1_0.md §C 0.8
Asset ID: BG-0-8 (brahmagyan.almanac)
Commit tag: [BRAHMA-BG-0-8]

Endpoints
---------
POST /api/brahmagyan/almanac/query
    Compute almanac for a date range + location. Returns list of AlmanacDay dicts.
    Supports 1–366 day ranges.

GET /api/brahmagyan/almanac/cache_stats
    Return in-process cache statistics (hit rate, size, etc.)

GET /api/brahmagyan/almanac/health
    Return a minimal health check (pings the engine with today's date).
"""
import os
from datetime import date as DateType
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from brahmagyan.almanac import (
    query as almanac_query,
    AlmanacDateRange,
    get_cache_stats,
    clear_cache,
)
from brahmagyan.almanac.core import make_location
from brahmagyan.almanac.serialize import almanac_day_to_dict
from panchang_engine.exceptions import PanchangEngineError, OutOfRangeError, ValidationError

router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class LocationRequest(BaseModel):
    """
    Location descriptor for almanac queries.
    lat/lon will be normalized to 0.1° internally (cache resolution).
    """
    lat: float = Field(..., ge=-90, le=90,
                       description="Latitude in decimal degrees (+N)")
    lon: float = Field(..., ge=-180, le=180,
                       description="Longitude in decimal degrees (+E)")
    tz_name: str = Field(...,
                         description="IANA timezone name, e.g. 'Asia/Kolkata'")
    label: str = Field("",
                       description="Optional human-readable location label")


class AlmanacQueryRequest(BaseModel):
    """
    Request body for almanac.query(date_range, location).

    date_from / date_to: inclusive date range (max 366 days).
    location: lat, lon, tz_name (IANA), optional label.
    """
    date_from: DateType = Field(..., description="Start date (inclusive), ISO 8601")
    date_to: DateType = Field(..., description="End date (inclusive), ISO 8601")
    location: LocationRequest


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/query")
async def almanac_query_endpoint(req: AlmanacQueryRequest):
    """
    brahmagyan.almanac tool endpoint.

    Computes (or retrieves from in-process LRU cache) the full panchanga +
    day-quality windows for each date in [date_from, date_to] at the given
    location.

    Provenance envelope is always included in each AlmanacDay:
      - computation_version: panchang_engine version string
      - ephemeris_version: swisseph version string
      - source: "engine" (computed) or "cache" (LRU hit)

    Response shape:
        {
            "ok": true,
            "days": [AlmanacDay, ...],     # one per date in range
            "count": N,
            "location": { lat, lon, tz_name, label, cache_key },
            "date_range": { date_from, date_to },
        }

    Errors:
        422: invalid date range or lat/lon out of range
        500: engine error
    """
    # Build AlmanacDateRange (validates date_from <= date_to, max 366 days)
    try:
        date_range = AlmanacDateRange(
            date_from=req.date_from,
            date_to=req.date_to,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Build AlmanacLocation (normalizes lat/lon to 0.1°)
    try:
        location = make_location(
            lat=req.location.lat,
            lon=req.location.lon,
            tz_name=req.location.tz_name,
            label=req.location.label,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Run the query
    try:
        days = almanac_query(date_range, location)
    except (ValidationError, OutOfRangeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except PanchangEngineError as exc:
        raise HTTPException(status_code=500, detail=f"Engine error: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Serialize — AlmanacDay dataclasses → dicts; error sentinels are already dicts
    serialized = []
    for day in days:
        if isinstance(day, dict):
            # Error sentinel (computation failed for that date)
            serialized.append(day)
        else:
            serialized.append(almanac_day_to_dict(day))

    return {
        "ok": True,
        "days": serialized,
        "count": len(serialized),
        "location": {
            "lat": location.lat,
            "lon": location.lon,
            "tz_name": location.tz_name,
            "label": location.label,
            "cache_key": location.cache_key,
        },
        "date_range": {
            "date_from": date_range.date_from.isoformat(),
            "date_to": date_range.date_to.isoformat(),
        },
    }


@router.get("/cache_stats")
async def cache_stats_endpoint():
    """Return in-process LRU cache statistics."""
    return {"ok": True, "cache": get_cache_stats()}


@router.get("/health")
async def almanac_health_endpoint():
    """
    Lightweight health check: compute today's almanac for Bhubaneswar
    and verify the engine returns a valid tithi name.
    """
    import datetime
    today = datetime.date.today()
    try:
        location = make_location(lat=20.27, lon=85.84,
                                 tz_name="Asia/Kolkata", label="Bhubaneswar")
        date_range = AlmanacDateRange(date_from=today, date_to=today)
        days = almanac_query(date_range, location)
        if not days:
            raise HTTPException(status_code=500, detail="Engine returned no results")
        day = days[0]
        if isinstance(day, dict) and "error" in day:
            raise HTTPException(status_code=500, detail=f"Engine error: {day['error']}")
        tithi_name = day.tithi["name"] if hasattr(day, "tithi") else day.get("tithi", {}).get("name")
    except (PanchangEngineError, ValidationError, OutOfRangeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=f"Almanac health check failed: {exc}")
    return {
        "ok": True,
        "date": today.isoformat(),
        "tithi": tithi_name,
        "location": "Bhubaneswar (20.3°N 85.8°E, Asia/Kolkata)",
    }
