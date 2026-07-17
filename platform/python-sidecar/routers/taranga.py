"""
routers/taranga — Kāla Taraṅga service HTTP endpoints (L3 D-3 Lane T-2).

Mounted at /api/compute/taranga (see main.py). Exposes the uniform contract
from `services.taranga_service`:

  POST /api/compute/taranga/activation      -> single time-point intensity
  POST /api/compute/taranga/curve           -> time-series of intensities
  POST /api/compute/taranga/record_evidence -> explicit opt-in evidence write-through

CR-87: `chart_id` is a required body field on every request — never
defaulted, never a query-string fallback to a native chart.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.taranga_service import (
    ChartRef,
    activation as _activation,
    curve as _curve,
    record_evidence as _record_evidence,
)

router = APIRouter()


class ActivationRequest(BaseModel):
    chart_id: str = Field(..., min_length=1, description="REQUIRED — CR-87, never defaulted")
    ayanamsha_id: str = "lahiri_chitrapaksha"
    target: str = Field(..., min_length=1, description="Domain name (wealth/career/marriage/health/general) or a bodha_mechanisms mechanism_id")
    t: datetime


class CurveRequest(BaseModel):
    chart_id: str = Field(..., min_length=1, description="REQUIRED — CR-87, never defaulted")
    ayanamsha_id: str = "lahiri_chitrapaksha"
    target: str = Field(..., min_length=1)
    t_start: datetime
    t_end: datetime
    resolution: Literal["daily", "weekly", "monthly"] = "daily"


class RecordEvidenceRequest(BaseModel):
    chart_id: str = Field(..., min_length=1, description="REQUIRED — CR-87, never defaulted")
    ayanamsha_id: str = "lahiri_chitrapaksha"
    target: str = Field(..., min_length=1)
    t: datetime
    cited_by: str = Field(..., min_length=1, description="What consumed this evidence (reading id / L5 job id) — REQUIRED opt-in")


@router.post("/activation")
def post_activation(req: ActivationRequest) -> dict[str, Any]:
    try:
        chart = ChartRef(chart_id=req.chart_id, ayanamsha_id=req.ayanamsha_id)
        return _activation(chart, req.target, req.t)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/curve")
def post_curve(req: CurveRequest) -> dict[str, Any]:
    try:
        chart = ChartRef(chart_id=req.chart_id, ayanamsha_id=req.ayanamsha_id)
        return _curve(chart, req.target, req.t_start, req.t_end, resolution=req.resolution)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/record_evidence")
def post_record_evidence(req: RecordEvidenceRequest) -> dict[str, Any]:
    try:
        chart = ChartRef(chart_id=req.chart_id, ayanamsha_id=req.ayanamsha_id)
        return _record_evidence(chart, req.target, req.t, cited_by=req.cited_by)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))
