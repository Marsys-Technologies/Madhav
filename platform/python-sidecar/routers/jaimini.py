"""
jaimini.py — FastAPI router for Jaimini Chara Dasha endpoints.

Exposes two GET endpoints:
  GET /jaimini_drishti/chara_dasha?date=YYYY-MM-DD
      → Returns the active Chara Dasha period (maha dasha + antar dasha) for the given date.
  GET /jaimini_drishti/chara_dasha/full
      → Returns all 12 rashi periods with start/end dates and optional sub-periods.

Session: TR-P7-S2
"""
from __future__ import annotations

from datetime import date as DateType
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

# Import the Chara Dasha engine.
# Use a try/except so the router degrades gracefully if the engine has
# an import error in environments without swisseph (test environments use mocks).
try:
    from panchang_engine.jaimini_chara import (
        build_full_chara_dasha,
        get_active_dasha,
        NATIVE_FALLBACK_LONGITUDES,
        NATIVE_LAGNA_RASHI_INDEX,
    )
    _ENGINE_AVAILABLE = True
except ImportError:
    _ENGINE_AVAILABLE = False

router = APIRouter()

# ── Native birth constants ─────────────────────────────────────────────────────

# Native Abhisek Mohanty: 1984-02-05
_NATIVE_BIRTH_DATE = DateType(1984, 2, 5)


# ── Legacy stub endpoint (preserved for backwards compat) ─────────────────────

class Params(BaseModel):
    params: dict = {}


@router.post("")
def compute(req: Params):
    """Legacy POST stub — retained for backwards compatibility. Use GET /chara_dasha instead."""
    return {
        "status": "deprecated",
        "message": "Use GET /jaimini_drishti/chara_dasha or GET /jaimini_drishti/chara_dasha/full",
    }


# ── Chara Dasha endpoints ──────────────────────────────────────────────────────

@router.get("/chara_dasha")
def get_active_chara_dasha(
    date: Optional[str] = Query(
        default=None,
        description="ISO date (YYYY-MM-DD) to query active dasha for. Defaults to today.",
    ),
    birth_date: Optional[str] = Query(
        default=None,
        description="Birth date override (ISO YYYY-MM-DD). Defaults to native birth date 1984-02-05.",
    ),
) -> Dict[str, Any]:
    """
    Return the active Jaimini Chara Dasha period for a given date.

    Query params:
      date       — target date (default: today)
      birth_date — birth date (default: native 1984-02-05)

    Response shape:
      {
        ok: true,
        query_date: "YYYY-MM-DD",
        active_rashi_dasha: {rashi, sign_lord, start_date, end_date},
        active_antar_dasha: {rashi, sign_lord, start_date, end_date},
        algorithm: "jaimini_chara_dasha",
      }
    """
    if not _ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="jaimini_chara engine not available")

    # Resolve query date
    if date is not None:
        try:
            query_date = DateType.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {date!r}. Use YYYY-MM-DD.")
    else:
        query_date = DateType.today()

    # Resolve birth date
    if birth_date is not None:
        try:
            bd = DateType.fromisoformat(birth_date)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid birth_date format: {birth_date!r}. Use YYYY-MM-DD.")
    else:
        bd = _NATIVE_BIRTH_DATE

    # Build full periods and find active one
    full_periods = build_full_chara_dasha(
        birth_date=bd,
        planet_longitudes=None,   # use native fallback
        lagna_longitude=None,     # use native fallback
    )
    active = get_active_dasha(full_periods, query_date)

    return {
        "ok": True,
        "query_date": query_date.isoformat(),
        "birth_date": bd.isoformat(),
        "active_rashi_dasha": active["active_rashi_dasha"],
        "active_antar_dasha": active["active_antar_dasha"],
        "algorithm": "jaimini_chara_dasha",
        "source": "native_fallback_longitudes",
    }


@router.get("/chara_dasha/full")
def get_full_chara_dasha(
    birth_date: Optional[str] = Query(
        default=None,
        description="Birth date override (ISO YYYY-MM-DD). Defaults to native birth date 1984-02-05.",
    ),
    include_sub_periods: bool = Query(
        default=False,
        description="If true, include antar_dasha (sub-period) breakdown for each rashi period.",
    ),
) -> Dict[str, Any]:
    """
    Return all 12 rashi Chara Dasha periods with start/end dates.

    Query params:
      birth_date          — birth date (default: native 1984-02-05)
      include_sub_periods — if true, include antar dasha entries per period

    Response shape:
      {
        ok: true,
        birth_date: "YYYY-MM-DD",
        total_years: 120,
        periods: [
          {
            rashi: "Taurus",
            sign_lord: "Venus",
            years: <int>,
            start_date: "YYYY-MM-DD",
            end_date: "YYYY-MM-DD",
            antar_dasha: [...] (only if include_sub_periods=true)
          },
          ...  (12 entries)
        ],
        algorithm: "jaimini_chara_dasha",
      }
    """
    if not _ENGINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="jaimini_chara engine not available")

    # Resolve birth date
    if birth_date is not None:
        try:
            bd = DateType.fromisoformat(birth_date)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid birth_date format: {birth_date!r}. Use YYYY-MM-DD.")
    else:
        bd = _NATIVE_BIRTH_DATE

    full_periods = build_full_chara_dasha(
        birth_date=bd,
        planet_longitudes=None,
        lagna_longitude=None,
    )

    # Optionally strip antar_dasha from response to reduce payload
    if not include_sub_periods:
        periods_out: List[Dict[str, Any]] = [
            {
                "rashi": p["rashi"],
                "sign_lord": p["sign_lord"],
                "years": p["years"],
                "start_date": p["start_date"],
                "end_date": p["end_date"],
            }
            for p in full_periods
        ]
    else:
        periods_out = full_periods

    total_years = sum(p["years"] for p in full_periods)

    return {
        "ok": True,
        "birth_date": bd.isoformat(),
        "total_years": total_years,
        "period_count": len(periods_out),
        "periods": periods_out,
        "algorithm": "jaimini_chara_dasha",
        "source": "native_fallback_longitudes",
    }
