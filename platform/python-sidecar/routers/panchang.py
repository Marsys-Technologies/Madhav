"""
routers/panchang.py — FastAPI router for /api/compute/panchanga endpoints.

Engine-direct path: calls panchang_engine.compute_panchang() on demand.
No SQL cache this session — 4C-2 will add panchang_daily cache below
the endpoint without changing this router.

Phase: 4C-3
"""
from datetime import date as DateType
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from panchang_engine import compute_panchang, panchang_range
from panchang_engine.serialize import panchang_to_dict
from panchang_engine.exceptions import PanchangEngineError, OutOfRangeError, ValidationError

router = APIRouter()


class PanchangaRequest(BaseModel):
    date: DateType
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tz_offset_minutes: int = Field(..., ge=-720, le=840)
    chart_id: Optional[str] = None  # for future personalise overlay (4C-5); ignored this session
    fields: Optional[list[str]] = None  # field projection for token-budget control


class PanchangaRangeRequest(BaseModel):
    date_from: DateType
    date_to: DateType
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tz_offset_minutes: int = Field(..., ge=-720, le=840)


@router.post("/panchanga")
async def compute_panchanga_endpoint(req: PanchangaRequest):
    """
    Returns full Panchang for a single (date, lat, lon, tz). Engine-direct;
    no cache layer this session. 4C-2 will add panchang_daily cache below.

    Response:
        {ok: true, panchang: {...}, cache_hit: false}
    """
    try:
        panchang = compute_panchang(req.date, req.lat, req.lon, req.tz_offset_minutes)
    except (ValidationError, OutOfRangeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except PanchangEngineError as exc:
        raise HTTPException(status_code=500, detail=f"Engine error: {exc}")

    payload = panchang_to_dict(panchang)

    # Field projection — clip server-side; query_panchanga.ts also clips client-side
    if req.fields:
        payload = {k: v for k, v in payload.items() if k in req.fields}

    return {"ok": True, "panchang": payload, "cache_hit": False}


@router.post("/panchanga/range")
async def compute_panchanga_range_endpoint(req: PanchangaRangeRequest):
    """
    Range variant for calendar feed / week views. Same engine-direct logic.
    date_from and date_to are both inclusive.

    Response:
        {ok: true, panchangs: [...], count: N}
    """
    # Sanity-check: cap at 31 days to prevent runaway sidecar calls
    delta = (req.date_to - req.date_from).days
    if delta < 0:
        raise HTTPException(status_code=422, detail="date_to must be >= date_from")
    if delta > 30:
        raise HTTPException(status_code=422, detail="Range exceeds 31-day limit; split the request")

    try:
        panchangs = panchang_range(
            req.date_from, req.date_to, req.lat, req.lon, req.tz_offset_minutes
        )
    except (ValidationError, OutOfRangeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except PanchangEngineError as exc:
        raise HTTPException(status_code=500, detail=f"Engine error: {exc}")

    return {
        "ok": True,
        "panchangs": [panchang_to_dict(p) for p in panchangs],
        "count": len(panchangs),
    }
