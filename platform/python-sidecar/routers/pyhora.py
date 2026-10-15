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
from pydantic import BaseModel, Field, field_validator

from services.ayanamsha_ids import PRIMARY_AYANAMSHA_ID, normalize_ayanamsha_id

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class BirthData(BaseModel):
    """Birth data for chart computation."""
    datetime_iso: str = Field(
        ...,
        description="Birth datetime in local wall-clock ISO format (e.g. '2000-01-01T12:00:00')"
    )
    latitude_deg: float = Field(..., description="Geographic latitude in decimal degrees (N positive)")
    longitude_deg: float = Field(..., description="Geographic longitude in decimal degrees (E positive)")
    tz_offset_hours: float = Field(..., description="Timezone offset in hours (e.g. 5.5 for IST)")
    place_name: str = Field(default="", description="Place name (informational)")
    subject_label: str = Field(default="", description="Subject label (informational)")
    ayanamsha_id: str = Field(
        default=PRIMARY_AYANAMSHA_ID,
        description=(
            "Stored ayanamsha id (lahiri_chitrapaksha | true_chitra | krishnamurti | raman | "
            "surya_siddhanta_classical); default lahiri_chitrapaksha (primary). Legacy short spellings "
            "(lahiri, kp, true_citra, surya_siddhanta) are mapped to the stored id at this boundary; "
            "anything else is a 422. ayanamsha_used echoes the stored id."
        ),
    )

    @field_validator("ayanamsha_id", mode="before")
    @classmethod
    def _normalise_ayanamsha(cls, v):
        return normalize_ayanamsha_id(v)  # ValueError -> pydantic 422


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


# SS N-384 (PR-S6): the smoke test runs on a SYNTHETIC subject, never on a real person's birth
# details. 2000-01-01 12:00 at the Greenwich meridian (UTC) is J2000 -- an astronomical epoch,
# not anyone's birth.
SMOKE_SYNTHETIC_INPUTS: dict[str, Any] = {
    "datetime_iso": "2000-01-01T12:00:00",
    "latitude_deg": 51.4769,
    "longitude_deg": 0.0,
    "tz_offset_hours": 0.0,
    "place_name": "Greenwich (synthetic)",
    "subject_label": "SMOKE-TEST synthetic subject",
}

SMOKE_NOTE = (
    "synthetic smoke-test subject (fictional person, J2000 epoch, Greenwich): proves the "
    "PyJHora engine computes a self-consistent chart; it is not any real person's chart"
)

_SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


@router.get("/smoke")
@serialized_swiss_state
async def smoke_test() -> dict[str, Any]:
    """
    Smoke test: compute a SYNTHETIC chart (fictional subject, 2000-01-01 12:00 UTC, Greenwich).

    Proves PyJHora works by internal consistency: the Sun's reported sign name must agree with
    its sidereal longitude (longitude // 30), and the Moon must carry a nakshatra. It compares
    against no real person's chart.

    Returns pass/fail with the actual values and the synthetic inputs used.
    """
    ephe_path = os.environ.get("SE_EPHE_PATH", "")
    try:
        from pyjhora_adapter.compute import compute_chart
        from pyjhora_adapter.version import ENGINE_VERSION

        # After the PyJHora import (which resets the swisseph path).
        ensure_swiss_backend()

        inputs = dict(SMOKE_SYNTHETIC_INPUTS)

        chart = compute_chart(inputs=inputs, ayanamsha_id=PRIMARY_AYANAMSHA_ID)
        grahas = chart.get("grahas", [])

        sun = next((g for g in grahas if g.get("name") == "Sun"), None)
        moon = next((g for g in grahas if g.get("name") == "Moon"), None)

        sun_sign = sun.get("sign", "") if sun else "MISSING"
        sun_lon = sun.get("longitude_deg", sun.get("sidereal_longitude")) if sun else None
        moon_nak = moon.get("nakshatra", "") if moon else "MISSING"

        # Sun: the sign label must be the sign its own longitude falls in.
        sun_pass = False
        if sun_lon is not None:
            lon = float(sun_lon)
            sun_pass = 0.0 <= lon < 360.0 and _SIGN_NAMES[int(lon // 30)] == sun_sign
        # Moon: a non-empty nakshatra must be reported.
        moon_pass = bool(moon) and bool(moon_nak) and moon_nak != "MISSING"

        return {
            "status": "pass" if (sun_pass and moon_pass) else "fail",
            "synthetic": True,
            "note": SMOKE_NOTE,
            "inputs": inputs,
            "engine": f"PyJHora/{ENGINE_VERSION}",
            "ephe_path": ephe_path,
            "sun_sign": sun_sign,
            "sun_longitude_deg": round(float(sun_lon), 4) if sun_lon is not None else None,
            "sun_expected": "sign name consistent with the sidereal longitude",
            "sun_pass": sun_pass,
            "moon_nakshatra": moon_nak,
            "moon_expected": "a non-empty nakshatra",
            "moon_pass": moon_pass,
        }

    except Exception as exc:
        return {
            "status": "error",
            "synthetic": True,
            "note": SMOKE_NOTE,
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
            "ayanamsha_id": g.get("ayanamsha_id", PRIMARY_AYANAMSHA_ID),
        })
    return out
