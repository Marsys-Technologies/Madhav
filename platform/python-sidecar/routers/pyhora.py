"""
routers/pyhora.py — /api/pyhora endpoint for per-chart natal computation.

Accepts birth_data dict → returns full natal computation via PyJHora:
  - graha_sthana (natal planet positions)
  - bhava_lagna (house cusps / ascendant)
  - special_lagnas (upagrahas + sensitive points)
  - vimshottari_dasha (mahadasha chain)

Stream G deliverable: BRAHMA-G-1 (POST /api/pyhora/compute)
"""
import logging
import os
from typing import Any

from panchang_engine.swiss_backend import OutOfCorpusRangeError, ensure_swiss_backend
from panchang_engine.swiss_state import serialized_swiss_state

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class BirthData(BaseModel):
    """Birth data for chart computation."""
    datetime_iso: str = Field(
        ...,
        description="Birth datetime in local wall-clock ISO format (e.g. '1984-02-05T10:43:00')"
    )
    latitude_deg: float = Field(..., description="Geographic latitude in decimal degrees (N positive)")
    longitude_deg: float = Field(..., description="Geographic longitude in decimal degrees (E positive)")
    tz_offset_hours: float = Field(..., description="Timezone offset in hours (e.g. 5.5 for IST)")
    place_name: str = Field(default="", description="Place name (informational)")
    subject_label: str = Field(default="", description="Subject label (informational)")
    ayanamsha_id: str = Field(default="lahiri", description="Ayanamsha: lahiri|raman|kp|true_citra")


class PyHoraResponse(BaseModel):
    """Full natal computation response from PyJHora."""
    status: str
    engine: str
    ayanamsha_used: str
    graha_sthana: list[dict[str, Any]]
    bhava_lagna: dict[str, Any]
    special_lagnas: dict[str, Any]
    vimshottari_dasha: dict[str, Any]
    panchanga: dict[str, Any]
    provenance: dict[str, Any]


def _birth_jd(datetime_iso: str) -> float:
    """Julian day (0h) of the ISO birth datetime's calendar date; ValueError if unparseable."""
    from datetime import datetime

    return datetime.fromisoformat(datetime_iso).toordinal() + 1721424.5


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/compute", response_model=None)
@serialized_swiss_state
async def compute_natal(birth_data: BirthData) -> dict[str, Any]:
    """
    Compute full natal chart via PyJHora.

    Returns graha_sthana, bhava_lagna, special_lagnas, vimshottari_dasha.
    This is the BRAHMA L1 Gaṇita endpoint — pure PyJHora computation.

    Ephemeris: Swiss .se1 files at SE_EPHE_PATH, verified fail-closed (500 if
    the file backend is not serving; never a silent Moshier fallback).
    """
    try:
        from pyjhora_adapter.compute import compute_chart
        from pyjhora_adapter.version import ENGINE_VERSION

        # After the PyJHora import (which resets the swisseph path).  The birth day is
        # passed so a chart outside the corpus window (1800-2400) is a disclosed 422
        # (out_of_corpus_range), never a silent Moshier chart.
        ensure_swiss_backend(_birth_jd(birth_data.datetime_iso))

        inputs = {
            "datetime_iso": birth_data.datetime_iso,
            "latitude_deg": birth_data.latitude_deg,
            "longitude_deg": birth_data.longitude_deg,
            "tz_offset_hours": birth_data.tz_offset_hours,
            "place_name": birth_data.place_name,
            "subject_label": birth_data.subject_label,
        }

        chart = compute_chart(
            inputs=inputs,
            ayanamsha_id=birth_data.ayanamsha_id,
        )

        # Shape graha_sthana for the response
        graha_sthana = _shape_graha_sthana(chart.get("grahas", []))
        bhava_lagna = chart.get("ascendant", chart.get("lagna", {}))
        special_lagnas = chart.get("sensitive_points", {})
        vimshottari = chart.get("dashas", {})
        panchanga = chart.get("panchanga", {})
        provenance = chart.get("provenance", {})

        return {
            "status": "ok",
            "engine": f"PyJHora/{ENGINE_VERSION}",
            "ayanamsha_used": birth_data.ayanamsha_id,
            "graha_sthana": graha_sthana,
            "bhava_lagna": bhava_lagna,
            "special_lagnas": special_lagnas,
            "vimshottari_dasha": vimshottari,
            "panchanga": panchanga,
            "provenance": provenance,
        }

    except OutOfCorpusRangeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ImportError as exc:
        logger.error("[pyhora] PyJHora import failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"PyJHora not available: {exc}"
        )
    except Exception as exc:
        logger.error("[pyhora] Computation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Computation error: {str(exc)[:500]}"
        )


@router.get("/smoke")
@serialized_swiss_state
async def smoke_test() -> dict[str, Any]:
    """
    Smoke test: compute native chart (1984-02-05 10:43 IST Bhubaneswar).
    Verifies Sun in Capricorn ~21°48' and Moon in Purva Bhadrapada.

    Returns pass/fail with actual vs expected values.
    """
    ephe_path = os.environ.get("SE_EPHE_PATH", "")
    try:
        from pyjhora_adapter.compute import compute_chart
        from pyjhora_adapter.version import ENGINE_VERSION

        # After the PyJHora import (which resets the swisseph path).
        ensure_swiss_backend()

        inputs = {
            "datetime_iso": "1984-02-05T10:43:00",
            "latitude_deg": 20.2735,
            "longitude_deg": 85.8334,
            "tz_offset_hours": 5.5,
            "place_name": "Bhubaneswar",
            "subject_label": "native",
        }

        chart = compute_chart(inputs=inputs, ayanamsha_id="lahiri")
        grahas = chart.get("grahas", [])

        sun = next((g for g in grahas if g.get("name") == "Sun"), None)
        moon = next((g for g in grahas if g.get("name") == "Moon"), None)

        sun_sign = sun.get("sign", "") if sun else "MISSING"
        sun_lon = sun.get("longitude_deg", sun.get("sidereal_longitude", 0)) if sun else 0
        moon_nak = moon.get("nakshatra", "") if moon else "MISSING"

        # Acceptance: Sun in Capricorn, lon ~291.8° (21°48' in Capricorn = 270+21.8=291.8)
        sun_pass = sun_sign == "Capricorn" and abs(sun_lon - 291.8) < 1.0
        # Moon in Purva Bhadrapada
        moon_pass = "Purva Bhadrapada" in moon_nak if moon else False

        return {
            "status": "pass" if (sun_pass and moon_pass) else "fail",
            "engine": f"PyJHora/{ENGINE_VERSION}",
            "ephe_path": ephe_path,
            "sun_sign": sun_sign,
            "sun_longitude_deg": round(float(sun_lon), 4) if sun else None,
            "sun_expected": "Capricorn ~291.8° (21°48')",
            "sun_pass": sun_pass,
            "moon_nakshatra": moon_nak,
            "moon_expected": "Purva Bhadrapada",
            "moon_pass": moon_pass,
        }

    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc)[:500],
            "ephe_path": ephe_path,
        }


def _shape_graha_sthana(grahas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize graha output to graha_sthana schema."""
    out = []
    for g in grahas:
        lon = g.get("longitude_deg", g.get("sidereal_longitude", g.get("lon", 0)))
        out.append({
            "name": g.get("name", ""),
            "sign": g.get("sign", ""),
            "sign_id": g.get("sign_id", 0),
            "nakshatra": g.get("nakshatra", ""),
            "nakshatra_id": g.get("nakshatra_id", 0),
            "pada": g.get("nakshatra_pada", g.get("pada", 0)),
            "house": g.get("house", 0),
            "longitude_deg": round(float(lon), 6) if lon else 0.0,
            "degree_in_sign": g.get("degree_in_sign", round(float(lon) % 30, 4) if lon else 0.0),
            "is_retrograde": bool(g.get("is_retrograde", g.get("retrograde", False))),
            "speed_dps": g.get("speed_dps", g.get("speed", 0.0)),
            "ayanamsha_id": g.get("ayanamsha_id", "lahiri"),
        })
    return out
