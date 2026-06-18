"""
routers/prashna.py
FastAPI router: POST /api/compute/prashna/cast

Explicit-invoke Prashna path:
  1. Validate question (deterministic rules)
  2. Cast question-moment chart + run ga_prashna judgment
  3. Return structured judgment
Namespace-isolated — never touches the native's natal chart_facts stream.
"""
from __future__ import annotations
import os
import uuid
import logging
from typing import Any, Optional
import psycopg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class PrashnaRequest(BaseModel):
    question_text: str = Field(..., min_length=10, max_length=1000)
    question_class: str
    prashna_lagna_method: str = "tajik_moment_lagna"
    question_instant: str  # ISO-8601 (e.g. "2026-06-18T22:00:00+05:30")
    question_lat: float = Field(..., ge=-90.0, le=90.0)
    question_lon: float = Field(..., ge=-180.0, le=180.0)
    querent_natal_chart_id: Optional[str] = None
    kp_number: Optional[int] = Field(None, ge=1, le=249)
    querent_direction: Optional[str] = None
    active_nostril: Optional[str] = None


class PrashnaResponse(BaseModel):
    chart_id: str
    valid: bool
    validation_reason: str
    rows_inserted: int
    primary_judgment: Optional[dict[str, Any]]


@router.post("/cast", response_model=PrashnaResponse)
async def cast_prashna(req: PrashnaRequest):
    """Cast a Prashna (horary) chart and return the judgment."""
    from ga_writers.ga_prashna_cast import validate_prashna_question, cast_prashna_chart

    # Step 1: Validate question
    validation = validate_prashna_question(req.question_text)
    if not validation["valid"]:
        return PrashnaResponse(
            chart_id="",
            valid=False,
            validation_reason=validation["reason"],
            rows_inserted=0,
            primary_judgment=None,
        )

    # Step 2: Cast + compute — same DB pattern as routers/panchang.py
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL not configured")

    build_id = str(uuid.uuid4())
    try:
        with psycopg.connect(db_url) as conn:
            result = cast_prashna_chart(
                conn=conn,
                build_id=build_id,
                question_text=req.question_text,
                question_class=req.question_class,
                prashna_lagna_method=req.prashna_lagna_method,
                question_instant=req.question_instant,
                question_lat=req.question_lat,
                question_lon=req.question_lon,
                querent_natal_chart_id=req.querent_natal_chart_id,
                kp_number=req.kp_number,
                querent_direction=req.querent_direction,
                active_nostril=req.active_nostril,
            )
            conn.commit()
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[prashna router] cast failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    return PrashnaResponse(
        chart_id=result["chart_id"],
        valid=True,
        validation_reason="",
        rows_inserted=result["rows_inserted"],
        primary_judgment=result.get("primary_judgment"),
    )
