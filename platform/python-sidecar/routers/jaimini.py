"""
jaimini.py — FastAPI router for Jaimini Chara Dasha endpoints.

Exposes two GET endpoints:
  GET /jaimini_drishti/chara_dasha?date=YYYY-MM-DD&chart_id=...
      → Returns the active Chara Dasha period (maha dasha + antar dasha) for the given date.
  GET /jaimini_drishti/chara_dasha/full?chart_id=...
      → Returns all 12 rashi periods with start/end dates and optional sub-periods.

M-8 fix (MARSYS_DEFECT_GAP_REGISTER_v2_0.md): this router used to default
`planet_longitudes=None` / `lagna_longitude=None` into the engine, which
silently substituted NATIVE_FALLBACK_LONGITUDES — a table that was wrong
even for the native (Sun 322.61 Aquarius vs. FORENSIC truth Capricorn; Lagna
51.28 Taurus vs. FORENSIC truth Aries) — for EVERY chart_id. Per
canonical-or-floor doctrine, longitudes are now always resolved from
chart_facts (the real chart) or the request hard-fails with 422
[EXTERNAL_COMPUTATION_REQUIRED]. There is no fallback table left to serve.

Session: TR-P7-S2. M-8 fix session: r6/0f-fallbackkill.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
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
    )
    _ENGINE_AVAILABLE = True
except ImportError:
    _ENGINE_AVAILABLE = False

router = APIRouter()

# The canonical native chart_id (CLAUDE.md §B) — used ONLY as the default
# VALUE OF THE `chart_id` QUERY PARAM, never as a computation fallback. Every
# call still resolves its longitudes from chart_facts for whichever chart_id
# is actually supplied; a non-native chart_id gets its own real data.
_NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
_NATIVE_BIRTH_DATE = DateType(1984, 2, 5)

_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
_REQUIRED_SUBJECTS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna",
]


def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[jaimini_router] DATABASE_URL not set")


@contextmanager
def _conn():
    import psycopg
    with psycopg.connect(_db_url()) as conn:
        yield conn


def _fetch_chart_longitudes(chart_id: str, ayanamsha_id: str) -> Dict[str, float]:
    """
    Resolve this chart's REAL sidereal longitudes (7 classical grahas + Lagna)
    from chart_facts. M-8 fix: replaces NATIVE_FALLBACK_LONGITUDES — there is
    no substitute value for a missing fact; a gap here is a 422, not a number.
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fact_subject, fact_key, fact_value_text, fact_value_num
                      FROM chart_facts
                     WHERE chart_id = %s
                       AND ayanamsha_id = %s
                       AND fact_category IN ('graha_sign_attributes', 'graha_position')
                       AND fact_key IN ('sign', 'degree_in_sign')
                       AND fact_subject = ANY(%s)
                    """,
                    (chart_id, ayanamsha_id, _REQUIRED_SUBJECTS),
                )
                rows = cur.fetchall()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "[EXTERNAL_COMPUTATION_REQUIRED] could not query chart_facts for "
                f"chart_id={chart_id!r} ayanamsha_id={ayanamsha_id!r}: {exc}. "
                "Refusing to substitute fallback longitudes (M-8 fix)."
            ),
        )

    sign_by_subject: Dict[str, str] = {}
    deg_by_subject: Dict[str, float] = {}
    for subj, key, val_text, val_num in rows:
        if key == "sign" and val_text:
            sign_by_subject[subj] = val_text
        elif key == "degree_in_sign" and val_num is not None:
            deg_by_subject[subj] = float(val_num)

    longitudes: Dict[str, float] = {}
    missing: List[str] = []
    for subj in _REQUIRED_SUBJECTS:
        sign = sign_by_subject.get(subj)
        deg = deg_by_subject.get(subj)
        if sign is None or deg is None or sign not in _SIGN_NAMES:
            missing.append(subj)
            continue
        longitudes[subj] = _SIGN_NAMES.index(sign) * 30.0 + deg

    if missing:
        raise HTTPException(
            status_code=422,
            detail=(
                f"[EXTERNAL_COMPUTATION_REQUIRED] chart_facts missing sign/degree_in_sign "
                f"for {missing} (chart_id={chart_id!r}, ayanamsha_id={ayanamsha_id!r}). "
                "Cannot compute Jaimini Chara Dasha without this chart's real "
                "longitudes — refusing to serve another chart's values (M-8 fix)."
            ),
        )
    return longitudes


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
    chart_id: str = Query(
        default=_NATIVE_CHART_ID,
        description="Chart to compute for. Longitudes are ALWAYS resolved from "
        "this chart's own chart_facts (M-8 fix) — never a fallback table.",
    ),
    ayanamsha_id: str = Query(
        default="lahiri",
        description="Ayanamsha used to resolve chart_facts (lahiri|raman|kp|true_citra).",
    ),
) -> Dict[str, Any]:
    """
    Return the active Jaimini Chara Dasha period for a given date.

    Query params:
      date          — target date (default: today)
      birth_date    — birth date (default: native 1984-02-05)
      chart_id      — chart to resolve longitudes for (default: native chart_id)
      ayanamsha_id  — ayanamsha for chart_facts lookup (default: lahiri)

    M-8 fix: longitudes are resolved from chart_facts for `chart_id`; there is
    no fallback table. If chart_facts is missing the needed facts, this
    returns 422 [EXTERNAL_COMPUTATION_REQUIRED] rather than a fabricated number.

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

    # M-8 fix: no fallback — resolve real longitudes or hard-fail (422/503).
    longitudes = _fetch_chart_longitudes(chart_id, ayanamsha_id)

    # Build full periods and find active one
    full_periods = build_full_chara_dasha(
        birth_date=bd,
        planet_longitudes=longitudes,
        lagna_longitude=longitudes["Lagna"],
    )
    active = get_active_dasha(full_periods, query_date)

    return {
        "ok": True,
        "query_date": query_date.isoformat(),
        "birth_date": bd.isoformat(),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "active_rashi_dasha": active["active_rashi_dasha"],
        "active_antar_dasha": active["active_antar_dasha"],
        "algorithm": "jaimini_chara_dasha",
        "source": "chart_facts",
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
    chart_id: str = Query(
        default=_NATIVE_CHART_ID,
        description="Chart to compute for. Longitudes are ALWAYS resolved from "
        "this chart's own chart_facts (M-8 fix) — never a fallback table.",
    ),
    ayanamsha_id: str = Query(
        default="lahiri",
        description="Ayanamsha used to resolve chart_facts (lahiri|raman|kp|true_citra).",
    ),
) -> Dict[str, Any]:
    """
    Return all 12 rashi Chara Dasha periods with start/end dates.

    Query params:
      birth_date          — birth date (default: native 1984-02-05)
      include_sub_periods — if true, include antar dasha entries per period
      chart_id            — chart to resolve longitudes for (default: native chart_id)
      ayanamsha_id        — ayanamsha for chart_facts lookup (default: lahiri)

    M-8 fix: longitudes are resolved from chart_facts for `chart_id`; there is
    no fallback table. If chart_facts is missing the needed facts, this
    returns 422 [EXTERNAL_COMPUTATION_REQUIRED] rather than a fabricated number.
    total_years is now the ACTUAL chart-dependent cycle sum, not a hardcoded 120.

    Response shape:
      {
        ok: true,
        birth_date: "YYYY-MM-DD",
        total_years: <int, chart-dependent>,
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

    # M-8 fix: no fallback — resolve real longitudes or hard-fail (422/503).
    longitudes = _fetch_chart_longitudes(chart_id, ayanamsha_id)

    full_periods = build_full_chara_dasha(
        birth_date=bd,
        planet_longitudes=longitudes,
        lagna_longitude=longitudes["Lagna"],
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
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "total_years": total_years,
        "period_count": len(periods_out),
        "periods": periods_out,
        "algorithm": "jaimini_chara_dasha",
        "source": "chart_facts",
    }
