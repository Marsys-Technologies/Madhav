"""
routers/muhurat.py — FastAPI router for /api/compute/muhurat endpoint.

Phase 4C-6-S1: Muhurat Finder backend live.
Endpoint: POST /api/compute/muhurat

Accepts event + date range + location + optional chart_id.
Returns top_n MuhuratWindow objects with breakdown, star rating, and score.

WRAPUP-S4 Packet C: cache-first hot path for Bhubaneswar (native) requests.
When DATABASE_URL is set and lat/lon is within 10 km of Bhubaneswar, the
endpoint reads from panchanga_daily SQL cache (single SELECT) instead of
calling find_muhurat() which invokes compute_panchang() 90× synchronously.
On any cache miss or failure, falls back to engine-direct transparently.
"""
import logging
import os
from datetime import date as DateType
from typing import Optional

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field
except ImportError:  # test environments without fastapi/pydantic installed
    HTTPException = Exception

    class _PassthroughDecorator:
        def __getattr__(self, name):
            def _deco(*a, **kw):
                def _inner(fn): return fn
                return _inner
            return _deco

    class APIRouter(_PassthroughDecorator):  # type: ignore[no-redef]
        def include_router(self, *a, **kw): pass

    class BaseModel:  # type: ignore[no-redef]
        def __init_subclass__(cls, **kw): pass
        def __init__(self, **kw): self.__dict__.update(kw)

    def Field(*a, **kw): return None  # type: ignore[no-redef]

from panchang_engine.muhurat import (
    find_muhurat,
    find_muhurat_from_cache,
    is_supported_event,
    EVENTS_MVP,
)
from panchang_engine.panchang_daily_reader import is_bhubaneswar
from panchang_engine.types import NatalChart, MuhuratWindow
from panchang_engine.exceptions import PanchangEngineError, OutOfRangeError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class MuhuratRequest(BaseModel):
    event: str
    date_from: DateType
    date_to: DateType
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tz_offset_minutes: int = Field(330, ge=-720, le=840)
    chart_id: Optional[str] = None   # Native overlay via NatalChart from DB
    top_n: int = Field(10, ge=1, le=90)   # cap at 90 to prevent abuse


def _window_to_dict(w: MuhuratWindow) -> dict:
    """Serialize a MuhuratWindow to JSON-safe dict."""
    return {
        "event":        w.event,
        "start_utc":    w.start_utc.isoformat() if w.start_utc else None,
        "end_utc":      w.end_utc.isoformat() if w.end_utc else None,
        "star_rating":  w.star_rating,
        "score":        round(w.score, 2),
        "breakdown":    w.breakdown,
    }


# ---------------------------------------------------------------------------
# Native chart helper (re-uses the pattern from panchang.py)
# ---------------------------------------------------------------------------

def _fetch_native_chart(chart_id: str) -> NatalChart:
    """
    Fetch minimal NatalChart from DB for Tara Bala / Chandra Bala overlay.
    Uses DATABASE_URL (same psycopg pattern as panchang.py / dasha_chain.py).
    Raises HTTPException 503/404 on failure.
    """
    import psycopg
    from panchang_engine import compute_panchang
    from panchang_engine.exceptions import PanchangEngineError, ValidationError

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")

    try:
        with psycopg.connect(db_url) as conn:
            row = conn.execute(
                """
                SELECT birth_date, birth_lat, birth_lng
                FROM charts
                WHERE id = %s
                """,
                (chart_id,),
            ).fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DB error: {exc}")

    if row is None:
        raise HTTPException(status_code=404, detail=f"Chart {chart_id!r} not found")

    birth_date, birth_lat, birth_lng = row
    lat = float(birth_lat) if birth_lat is not None else 20.27
    lon = float(birth_lng) if birth_lng is not None else 85.84

    try:
        birth_panchang = compute_panchang(birth_date, lat, lon, tz_offset=330)
    except (ValidationError, PanchangEngineError) as exc:
        raise HTTPException(status_code=422, detail=f"Birth chart compute error: {exc}")

    moon = next(
        (p for p in birth_panchang.planets if getattr(p, "name", "").lower() == "moon"),
        None,
    )
    if moon is None:
        raise HTTPException(status_code=500, detail="Moon position not found in birth panchang")

    return NatalChart(
        birth_nakshatra_id=int(moon.nakshatra_id),
        birth_lagna_sign_id=1,   # Lagna not needed for Tara Bala; default Aries
        moon_sign_id=int(moon.sign_id),
        active_dasha_lord=None,  # populated in a future session
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/muhurat")
async def compute_muhurat_endpoint(req: MuhuratRequest):
    """
    Find top auspicious muhurat windows for a given event in a date range.

    Request:
        event: str — one of the 6 MVP events (vivah, griha_pravesh, vyapara,
                      yatra, property_purchase, mantra_initiation)
        date_from: date — start of search window (inclusive)
        date_to:   date — end of search window (inclusive); max 90 days
        lat, lon:  float — location coordinates
        tz_offset_minutes: int — UTC offset in minutes (default 330 = IST)
        chart_id:  str | null — optional; provides Tara Bala native overlay
        top_n:     int — number of top windows to return (default 10)

    Response:
        {ok: true, windows: [MuhuratWindow...], count: int,
         event: str, supported_events: [...]}
    """
    # Validate event
    if not is_supported_event(req.event):
        raise HTTPException(
            status_code=422,
            detail=f"Event '{req.event}' not supported. Supported events: {EVENTS_MVP}",
        )

    # Validate date range
    if req.date_from > req.date_to:
        raise HTTPException(
            status_code=422,
            detail="date_to must be >= date_from",
        )

    delta = (req.date_to - req.date_from).days
    if delta > 89:
        raise HTTPException(
            status_code=422,
            detail="Date range exceeds 90-day limit; split the request",
        )

    # Native chart overlay (optional)
    native_chart: Optional[NatalChart] = None
    if req.chart_id:
        native_chart = _fetch_native_chart(req.chart_id)

    # ---------------------------------------------------------------------------
    # Cache-first hot path (Bhubaneswar / native use case)
    # ---------------------------------------------------------------------------
    # For requests from within 10 km of Bhubaneswar when DATABASE_URL is set,
    # read from panchanga_daily SQL cache (single SELECT) instead of calling
    # find_muhurat() which computes Swiss Ephemeris 90× synchronously.
    # Any cache miss or failure silently falls through to engine-direct.
    # ---------------------------------------------------------------------------
    db_url = os.environ.get("DATABASE_URL", "")
    windows = None
    cache_used = False

    if db_url and is_bhubaneswar(req.lat, req.lon):
        try:
            windows = find_muhurat_from_cache(
                req.event,
                req.date_from,
                req.date_to,
                lat=req.lat,
                lon=req.lon,
                db_url=db_url,
                native_chart=native_chart,
                top_n=req.top_n,
            )
            if windows is not None:
                cache_used = True
        except Exception:  # noqa: BLE001
            windows = None  # fall through to engine-direct

    # ---------------------------------------------------------------------------
    # Engine-direct fallback (non-Bhubaneswar, DB unavailable, or cache miss)
    # ---------------------------------------------------------------------------
    if windows is None:
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
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except (ValidationError, OutOfRangeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except PanchangEngineError as exc:
            raise HTTPException(status_code=500, detail=f"Engine error: {exc}")

    logger.info(
        "muhurat path: %s | event=%s dates=%s–%s lat=%.4f lon=%.4f",
        "cache" if cache_used else "engine-direct",
        req.event, req.date_from, req.date_to, req.lat, req.lon,
    )

    return {
        "ok":               True,
        "windows":          [_window_to_dict(w) for w in windows],
        "count":            len(windows),
        "event":            req.event,
        "supported_events": EVENTS_MVP,
    }
