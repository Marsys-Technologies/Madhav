"""
routers/panchang.py — FastAPI router for /api/compute/panchanga endpoints.

Engine-direct path: calls panchang_engine.compute_panchang() on demand.
No SQL cache this session — 4C-2 will add panchang_daily cache below
the endpoint without changing this router.

Phase: 4C-3 (initial); 4C-5 (NativeContext hydration + chart_id wiring)
"""
import os
from datetime import date as DateType, time as TimeType
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import psycopg

from panchang_engine import compute_panchang, panchang_range
from panchang_engine.serialize import panchang_to_dict
from panchang_engine.exceptions import PanchangEngineError, OutOfRangeError, ValidationError
from panchang_engine.shastra_tables import NAKSHATRA_NAMES, SIGN_NAMES

router = APIRouter()


# ── NativeContext ──────────────────────────────────────────────────────────────

class NativeContext(BaseModel):
    """
    Minimal native overlay computed from birth chart for Tara Bala / Chandra Bala.
    Attached to the /api/compute/panchanga response when chart_id is provided.
    """
    chart_id: str
    native_name: str                  # chart name for UI display (e.g. "Abhisek")
    birth_nakshatra_id: int           # 1..27 (Moon nakshatra at birth, sidereal)
    birth_nakshatra_name: str         # e.g. "Purva Bhadrapada"
    moon_sign_id: int                 # 1..12 (1 = Aries … 12 = Pisces)
    moon_sign_name: str               # Sanskrit sign name, e.g. "Kumbha"
    active_dasha_lord: Optional[str] = None  # for future dasha-aware muhurat in 4C-6


# ── Chart fetcher ──────────────────────────────────────────────────────────────

def _fetch_native_context(chart_id: str) -> NativeContext:
    """
    Fetch chart from DB, compute birth nakshatra + Moon sign via panchang_engine,
    and return NativeContext.

    Uses DATABASE_URL (same pattern as dasha_chain router).
    Raises HTTPException 503 if DB is unreachable, 404 if chart not found.

    Security: caller must already have confirmed chart access (auth is enforced
    at the Next.js proxy layer; the sidecar trusts the proxy's chart_id).
    """
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")

    try:
        with psycopg.connect(db_url) as conn:
            row = conn.execute(
                """
                SELECT name, birth_date, birth_time, birth_lat, birth_lng
                FROM charts
                WHERE id = %s
                """,
                (chart_id,),
            ).fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DB error: {exc}")

    if row is None:
        raise HTTPException(status_code=404, detail=f"Chart {chart_id!r} not found")

    chart_name, birth_date, birth_time, birth_lat, birth_lng = row

    # birth_lat / birth_lng can be None if the chart was created without coordinates;
    # fall back to Bhubaneswar (project canonical default per §8 / D1 decisions).
    lat = float(birth_lat) if birth_lat is not None else 20.27
    lon = float(birth_lng) if birth_lng is not None else 85.84

    # birth_time may come as a `datetime.time` or string depending on driver
    if isinstance(birth_time, TimeType):
        birth_hour = birth_time.hour
        birth_min  = birth_time.minute
    else:
        # parse HH:MM or HH:MM:SS string
        parts = str(birth_time).split(":")
        birth_hour = int(parts[0])
        birth_min  = int(parts[1]) if len(parts) > 1 else 0

    # Compute panchang at birth moment using IST (+330 min) by default.
    # (Charts may carry a different TZ in future; for this release, IST is canonical.)
    try:
        birth_panchang = compute_panchang(birth_date, lat, lon, tz_offset_minutes=330)
    except (ValidationError, OutOfRangeError, PanchangEngineError) as exc:
        raise HTTPException(status_code=422, detail=f"Birth chart compute error: {exc}")

    # Extract Moon's nakshatra and sign from the birth-moment planet positions.
    # birth_panchang.planets is list[PlanetState]; find Moon by name.
    moon = next(
        (ps for ps in birth_panchang.planets if getattr(ps, "name", "").lower() == "moon"),
        None
    )

    if moon is None:
        raise HTTPException(status_code=500, detail="Moon position not found in birth panchang")

    nak_id   = int(moon.nakshatra_id)      # 1..27
    nak_name = NAKSHATRA_NAMES[nak_id - 1]  # 0-indexed list
    sign_id  = int(moon.sign_id)           # 1..12
    sign_name = SIGN_NAMES[sign_id - 1]    # 0-indexed list

    return NativeContext(
        chart_id=chart_id,
        native_name=chart_name or "",
        birth_nakshatra_id=nak_id,
        birth_nakshatra_name=nak_name,
        moon_sign_id=sign_id,
        moon_sign_name=sign_name,
        active_dasha_lord=None,  # populated in 4C-6
    )


# ── Request / Response models ──────────────────────────────────────────────────

class PanchangaRequest(BaseModel):
    date: DateType
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tz_offset_minutes: int = Field(..., ge=-720, le=840)
    chart_id: Optional[str] = None  # personalise overlay; hydrated this session (4C-5)
    fields: Optional[list[str]] = None  # field projection for token-budget control


class PanchangaRangeRequest(BaseModel):
    date_from: DateType
    date_to: DateType
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tz_offset_minutes: int = Field(..., ge=-720, le=840)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/panchanga")
async def compute_panchanga_endpoint(req: PanchangaRequest):
    """
    Returns full Panchang for a single (date, lat, lon, tz). Engine-direct;
    no cache layer this session. 4C-2 will add panchang_daily cache below.

    When chart_id is provided, also returns native_context (NativeContext) with
    birth nakshatra + moon sign for Tara Bala / Chandra Bala overlay.

    Response:
        {ok: true, panchang: {...}, native_context: NativeContext|null, cache_hit: false}
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

    # Native context — hydrated when chart_id is present
    native_context: Optional[NativeContext] = None
    if req.chart_id:
        native_context = _fetch_native_context(req.chart_id)

    return {
        "ok": True,
        "panchang": payload,
        "native_context": native_context.model_dump() if native_context else None,
        "cache_hit": False,
    }


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
