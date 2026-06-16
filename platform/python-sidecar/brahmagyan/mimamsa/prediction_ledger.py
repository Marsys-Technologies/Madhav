"""
brahmagyan/mimamsa/prediction_ledger.py — Brahma L5 Mīmāṃsā — mimamsa.prediction_ledger (MI-5-2)

Asset:    mimamsa.prediction_ledger
Tools:
    log_prediction(chart_id, prediction, horizon, confidence, falsifier) → prediction_id
        Logs a prediction BEFORE outcome is observed. source_citation is derived from
        the phala.anchors layer; falsifier is required and non-null.

    record_outcome(prediction_id, outcome_observed) → brier_score
        Writes outcome_observed and computes brier_score = (outcome::int - confidence)^2.
        This is the ONLY sanctioned path for writing outcome_observed.

Table:    mimamsa_predictions
    (prediction_id UUID, chart_id UUID, predicted_at TIMESTAMPTZ,
     horizon_date DATE, domain TEXT, prediction_text TEXT NOT NULL,
     confidence FLOAT CHECK(0<c<1), falsifier TEXT NOT NULL,
     outcome_observed BOOLEAN, brier_score FLOAT,
     source_citation TEXT NOT NULL)

Contract (BRAHMA MI-5-2):
    - source_citation non-null on ALL rows (B.3 derivation-ledger mandate)
    - falsifier non-null on ALL rows (Learning Layer discipline rule #4)
    - confidence in OPEN interval (0, 1)
    - outcome_observed NULL until record_outcome() is called — NO LEAKAGE rule
    - brier_score = (outcome_observed::int - confidence)^2
    - provenance_envelope on every tool response
    - Migration: brahma_mimamsa_prediction_ledger.sql (IF NOT EXISTS)
    - NO LEAKAGE: life_events must never feed into prediction generation;
      LEL intake feeds calibration ONLY

source_citation format: "Brahma L4 phala.anchors / [anchor_id]"

Native:   Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
          chart_id: 482012f1-710e-4a25-994a-93821f5871aa

Layer:    L5 Mīmāṃsā (depends on L4 phala.anchors)
Depends:  brahma_mimamsa_prediction_ledger.sql
          FORENSIC v8.0 (indirect — via phala.anchors citations)
          phala.anchors PH-4-1 (source_citation references anchor_id)

Authors:  Silpī (MI-5-2 session)
Version:  1.0 — 2026-06-04
BRAHMA-MI-5-2
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

import psycopg
import psycopg.rows
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)

# Valid domain values — extensible; used for soft validation only
VALID_DOMAINS = frozenset({
    "career",
    "spiritual",
    "relational",
    "financial",
    "health",
    "residential",
    "creative",
    "authority",
    "transition",
    "general",
})

SOURCE_CITATION_PREFIX = "Brahma L4 phala.anchors"


# ── DB URL ────────────────────────────────────────────────────────────────────

def _get_db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key, "")
        if val:
            return val
    raise RuntimeError(
        "No database URL configured. Set DATABASE_URL, DIRECT_DATABASE_URL, or POSTGRES_URL."
    )


# ── Brier score ───────────────────────────────────────────────────────────────

def compute_brier_score(confidence: float, outcome_observed: bool) -> float:
    """
    brier_score = (outcome_observed::int - confidence)^2

    Args:
        confidence:       Calibrated probability in (0, 1).
        outcome_observed: True if the predicted event occurred; False otherwise.

    Returns:
        float in [0.0, 1.0]. Lower is better. Perfect = 0.0.

    Raises:
        ValueError: confidence not in (0, 1).
    """
    if not (0.0 < confidence < 1.0):
        raise ValueError(
            f"confidence must be in open interval (0, 1), got {confidence}"
        )
    outcome_int = 1 if outcome_observed else 0
    return float((outcome_int - confidence) ** 2)


# ── Core engine — log_prediction ──────────────────────────────────────────────

def log_prediction(
    chart_id: str,
    prediction_text: str,
    horizon_date: str,
    confidence: float,
    falsifier: str,
    domain: str = "general",
    source_citation: Optional[str] = None,
    anchor_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Log a prediction BEFORE outcome is observed.

    This is the primary write path for MI-5-2. The caller supplies:
        - prediction_text (the claim being made)
        - horizon_date (the date by which the claim will be observable)
        - confidence (calibrated probability in (0, 1))
        - falsifier (explicit falsifier per Learning Layer rule #4)

    source_citation is auto-derived as "Brahma L4 phala.anchors / [anchor_id]"
    if anchor_id is given; otherwise caller must supply source_citation directly.

    NO LEAKAGE: life_events (LEL) must never call this function during prediction
    generation — only during calibration (post-hoc verification) sessions.

    Args:
        chart_id:         Chart UUID.
        prediction_text:  The prediction claim (non-empty).
        horizon_date:     ISO date string — the date by which the claim is observable.
        confidence:       Calibrated probability in OPEN interval (0, 1).
        falsifier:        Explicit falsifier (non-empty, required).
        domain:           Domain label (e.g. "career", "spiritual"). Default "general".
        source_citation:  L4 citation. If None, derived from anchor_id.
        anchor_id:        Optional phala.anchors anchor_id for auto-citation.

    Returns:
        {
            "ok": True,
            "prediction_id": str (UUID),
            "chart_id": str,
            "confidence": float,
            "horizon_date": str,
            "domain": str,
            "source_citation": str,
            "provenance_envelope": {...}
        }

    Raises:
        ValueError:   Invalid inputs (confidence, falsifier, source_citation).
        RuntimeError: DATABASE_URL not configured.
    """
    # Validate confidence — open interval (0, 1)
    if not (0.0 < confidence < 1.0):
        raise ValueError(
            f"confidence must be in open interval (0, 1), got {confidence}. "
            "Zero and one are not valid calibrated probabilities."
        )

    # Validate falsifier
    if not falsifier or not falsifier.strip():
        raise ValueError(
            "falsifier is required and must be non-empty "
            "(Learning Layer discipline rule #4)."
        )

    # Validate prediction_text
    if not prediction_text or not prediction_text.strip():
        raise ValueError("prediction_text is required and must be non-empty.")

    # Parse horizon_date
    try:
        horizon = date.fromisoformat(horizon_date)
    except ValueError as exc:
        raise ValueError(
            f"horizon_date must be an ISO date string (YYYY-MM-DD): {exc}"
        ) from exc

    # Derive source_citation
    if source_citation is None:
        if anchor_id:
            source_citation = f"{SOURCE_CITATION_PREFIX} / {anchor_id}"
        else:
            raise ValueError(
                "source_citation is required (B.3 mandate). "
                "Provide either source_citation or anchor_id."
            )

    if not source_citation.strip():
        raise ValueError(
            "source_citation must be non-empty (B.3 derivation-ledger mandate)."
        )

    prediction_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc)

    sql = """
        INSERT INTO public.mimamsa_predictions
            (prediction_id, chart_id, predicted_at, horizon_date, domain,
             prediction_text, confidence, falsifier, source_citation)
        VALUES
            (%s::UUID, %s::UUID, %s, %s, %s, %s, %s, %s, %s)
        RETURNING prediction_id, predicted_at
    """
    params = [
        prediction_id,
        chart_id,
        now,
        horizon,
        domain,
        prediction_text.strip(),
        confidence,
        falsifier.strip(),
        source_citation.strip(),
    ]

    db_url = _get_db_url()
    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            returned_id = str(row["prediction_id"]) if row else prediction_id
        conn.commit()

    logger.info(
        "log_prediction chart_id=%s prediction_id=%s domain=%s horizon=%s confidence=%.4f",
        chart_id, returned_id, domain, horizon, confidence,
    )

    return {
        "ok": True,
        "prediction_id": returned_id,
        "chart_id": chart_id,
        "confidence": confidence,
        "horizon_date": horizon.isoformat(),
        "domain": domain,
        "source_citation": source_citation.strip(),
        "provenance_envelope": _build_log_provenance(
            chart_id=chart_id,
            prediction_id=returned_id,
            confidence=confidence,
            horizon_date=horizon.isoformat(),
            domain=domain,
            source_citation=source_citation.strip(),
            logged_at=now.isoformat(),
        ),
    }


# ── Core engine — record_outcome ──────────────────────────────────────────────

def record_outcome(
    prediction_id: str,
    outcome_observed: bool,
) -> dict[str, Any]:
    """
    Record the outcome for a logged prediction. Computes Brier score.

    This is the ONLY sanctioned path for writing outcome_observed.
    Calls the DB function mimamsa_record_outcome(prediction_id, outcome).

    NO LEAKAGE: life_events must never call this function during prediction
    generation. Only valid post-hoc during calibration sessions.

    Args:
        prediction_id:    UUID of the prediction row.
        outcome_observed: True if the predicted event occurred; False otherwise.

    Returns:
        {
            "ok": True,
            "prediction_id": str,
            "outcome_observed": bool,
            "brier_score": float,
            "provenance_envelope": {...}
        }

    Raises:
        ValueError:   prediction_id not found.
        RuntimeError: DATABASE_URL not configured.
    """
    db_url = _get_db_url()
    sql = "SELECT mimamsa_record_outcome(%s::UUID, %s) AS brier_score"

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(sql, [prediction_id, outcome_observed])
                row = cur.fetchone()
                brier_score = float(row["brier_score"]) if row else None
            except Exception as exc:
                raise ValueError(
                    f"Failed to record outcome for prediction_id={prediction_id}: {exc}"
                ) from exc
        conn.commit()

    if brier_score is None:
        raise ValueError(
            f"prediction_id {prediction_id} not found or outcome already recorded."
        )

    now = datetime.now(tz=timezone.utc)
    logger.info(
        "record_outcome prediction_id=%s outcome=%s brier_score=%.6f",
        prediction_id, outcome_observed, brier_score,
    )

    return {
        "ok": True,
        "prediction_id": prediction_id,
        "outcome_observed": outcome_observed,
        "brier_score": brier_score,
        "provenance_envelope": _build_outcome_provenance(
            prediction_id=prediction_id,
            outcome_observed=outcome_observed,
            brier_score=brier_score,
            recorded_at=now.isoformat(),
        ),
    }


# ── Fetch predictions ─────────────────────────────────────────────────────────

def fetch_predictions(
    chart_id: str,
    domain: Optional[str] = None,
    open_only: bool = False,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Retrieve logged predictions for a chart.

    Args:
        chart_id:   Chart UUID.
        domain:     Optional domain filter.
        open_only:  If True, return only predictions with outcome_observed IS NULL.
        limit:      Maximum number of rows to return. Default 50.

    Returns:
        list[dict] — rows from mimamsa_predictions, ordered by horizon_date ASC.

    Raises:
        RuntimeError: DATABASE_URL not configured.
    """
    conditions = ["chart_id = %s"]
    params: list[Any] = [chart_id]

    if domain:
        conditions.append("domain = %s")
        params.append(domain)

    if open_only:
        conditions.append("outcome_observed IS NULL")

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            prediction_id, chart_id, predicted_at, horizon_date, domain,
            prediction_text, confidence, falsifier, source_citation,
            outcome_observed, brier_score, outcome_recorded_at,
            created_at, updated_at
        FROM public.mimamsa_predictions
        WHERE {where}
        ORDER BY horizon_date ASC, predicted_at DESC
        LIMIT %s
    """
    params.append(limit)

    db_url = _get_db_url()
    rows: list[dict[str, Any]] = []

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            for row in cur.fetchall():
                normalised: dict[str, Any] = {}
                for k, v in row.items():
                    if isinstance(v, (date, datetime)):
                        normalised[k] = v.isoformat()
                    elif isinstance(v, uuid.UUID):
                        normalised[k] = str(v)
                    else:
                        normalised[k] = v
                rows.append(normalised)

    return rows


def list_predictions(
    chart_id: str,
    domain: Optional[str] = None,
    open_only: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    """
    List logged predictions for a chart with provenance envelope.

    Returns:
        {
            "ok": True,
            "chart_id": str,
            "predictions": list[dict],
            "count": int,
            "open_count": int,
            "provenance_envelope": {...}
        }
    """
    rows = fetch_predictions(chart_id, domain=domain, open_only=open_only, limit=limit)
    open_count = sum(1 for r in rows if r.get("outcome_observed") is None)
    now = datetime.now(tz=timezone.utc)

    return {
        "ok": True,
        "chart_id": chart_id,
        "predictions": rows,
        "count": len(rows),
        "open_count": open_count,
        "provenance_envelope": {
            "source": "mimamsa.prediction_ledger",
            "asset": "MI-5-2",
            "chart_id": chart_id,
            "queried_at": now.isoformat(),
            "filters": {
                "domain": domain,
                "open_only": open_only,
                "limit": limit,
            },
            "b3_citation_compliant": all(bool(r.get("source_citation")) for r in rows),
            "all_falsifiers_present": all(bool(r.get("falsifier")) for r in rows),
            "no_leakage_note": (
                "LEL life_events feed calibration only; "
                "they must never feed prediction generation."
            ),
        },
    }


# ── Provenance envelope builders ──────────────────────────────────────────────

def _build_log_provenance(
    chart_id: str,
    prediction_id: str,
    confidence: float,
    horizon_date: str,
    domain: str,
    source_citation: str,
    logged_at: str,
) -> dict[str, Any]:
    return {
        "source": "mimamsa.prediction_ledger",
        "asset": "MI-5-2",
        "tool": "log_prediction",
        "chart_id": chart_id,
        "prediction_id": prediction_id,
        "confidence": confidence,
        "horizon_date": horizon_date,
        "domain": domain,
        "source_citation": source_citation,
        "logged_at": logged_at,
        "l4_ground_truth": "phala.anchors PH-4-1",
        "b3_citation_compliant": bool(source_citation),
        "no_leakage_discipline": (
            "Prediction logged BEFORE outcome is observed. "
            "LEL life_events must not feed prediction generation."
        ),
    }


def _build_outcome_provenance(
    prediction_id: str,
    outcome_observed: bool,
    brier_score: float,
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "source": "mimamsa.prediction_ledger",
        "asset": "MI-5-2",
        "tool": "record_outcome",
        "prediction_id": prediction_id,
        "outcome_observed": outcome_observed,
        "brier_score": brier_score,
        "brier_formula": "brier_score = (outcome::int - confidence)^2",
        "recorded_at": recorded_at,
        "no_leakage_note": (
            "Outcome recorded post-hoc via the ONLY sanctioned path. "
            "LEL life_events feed calibration only."
        ),
    }


# ── FastAPI request/response models ───────────────────────────────────────────

class LogPredictionRequest(BaseModel):
    chart_id: str = Field(..., description="Chart UUID")
    prediction_text: str = Field(..., min_length=1, description="The prediction claim")
    horizon_date: str = Field(..., description="ISO date (YYYY-MM-DD) — observable by this date")
    confidence: float = Field(
        ...,
        gt=0.0,
        lt=1.0,
        description="Calibrated probability in OPEN interval (0, 1)"
    )
    falsifier: str = Field(
        ...,
        min_length=1,
        description='Explicit falsifier per Learning Layer rule #4. '
                    'Format: "If [event] does not occur by [date], this prediction is false."'
    )
    domain: str = Field(
        default="general",
        description="Domain label: career|spiritual|relational|financial|health|residential|creative|authority|transition|general"
    )
    source_citation: Optional[str] = Field(
        None,
        description='L4 citation: "Brahma L4 phala.anchors / [anchor_id]". '
                    'If omitted, anchor_id is required.'
    )
    anchor_id: Optional[str] = Field(
        None,
        description="phala.anchors anchor_id for auto-citation (e.g. PH-4-1.2026H1.CAREER)"
    )

    @field_validator("confidence")
    @classmethod
    def confidence_open_interval(cls, v: float) -> float:
        if not (0.0 < v < 1.0):
            raise ValueError(
                f"confidence must be in open interval (0, 1), got {v}. "
                "Zero and one are not valid calibrated probabilities."
            )
        return v

    @field_validator("falsifier")
    @classmethod
    def falsifier_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("falsifier must be non-empty (Learning Layer rule #4).")
        return v.strip()


class RecordOutcomeRequest(BaseModel):
    prediction_id: str = Field(..., description="UUID of the prediction to close")
    outcome_observed: bool = Field(
        ...,
        description="True if the predicted event occurred; False if it was falsified."
    )


class ListPredictionsRequest(BaseModel):
    chart_id: str = Field(..., description="Chart UUID")
    domain: Optional[str] = Field(None, description="Optional domain filter")
    open_only: bool = Field(
        default=False,
        description="If True, return only predictions with no recorded outcome"
    )
    limit: int = Field(default=50, ge=1, le=500, description="Maximum rows to return")


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

@router.post("/mimamsa/log_prediction")
def api_log_prediction(req: LogPredictionRequest) -> dict[str, Any]:
    """
    MI-5-2 log_prediction tool.

    Logs a prediction BEFORE outcome is observed.
    Returns a prediction_id handle for record_outcome().

    Required: prediction_text, horizon_date, confidence (0<c<1), falsifier.
    source_citation is auto-derived from anchor_id if not provided directly.

    NO LEAKAGE: life_events (LEL) must never feed into this call.
    """
    try:
        return log_prediction(
            chart_id=req.chart_id,
            prediction_text=req.prediction_text,
            horizon_date=req.horizon_date,
            confidence=req.confidence,
            falsifier=req.falsifier,
            domain=req.domain,
            source_citation=req.source_citation,
            anchor_id=req.anchor_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/mimamsa/record_outcome")
def api_record_outcome(req: RecordOutcomeRequest) -> dict[str, Any]:
    """
    MI-5-2 record_outcome tool.

    ONLY sanctioned path to write outcome_observed.
    Computes brier_score = (outcome::int - confidence)^2.

    NO LEAKAGE: LEL life_events feed calibration only.
    """
    try:
        return record_outcome(
            prediction_id=req.prediction_id,
            outcome_observed=req.outcome_observed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/mimamsa/list_predictions")
def api_list_predictions(req: ListPredictionsRequest) -> dict[str, Any]:
    """
    MI-5-2 list predictions for a chart.

    Returns predictions with provenance envelope, B.3 compliance flag,
    falsifier completeness check, and open/closed counts.
    """
    try:
        return list_predictions(
            chart_id=req.chart_id,
            domain=req.domain,
            open_only=req.open_only,
            limit=req.limit,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
