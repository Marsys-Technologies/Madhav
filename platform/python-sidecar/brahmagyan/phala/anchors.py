"""
brahmagyan/phala/anchors.py — Brahma L4 Phala — phala.anchors (PH-4-1)

Asset:    phala.anchors
Tool:     event_anchors(chart_id, date_range, min_confidence?) →
              {anchors:[{window,theme,confidence,falsifier,provenance}], provenance_envelope}
Table:    phala_anchors (chart_id UUID, anchor_id TEXT, window_start DATE, window_end DATE,
          theme TEXT, confidence FLOAT CHECK(0<=confidence<=1), falsifier TEXT NOT NULL,
          contributing_dashas JSONB, contributing_signals JSONB, source_citation TEXT NOT NULL)

Algorithm:
    For each 6-month window in the requested date range:
        score = dasha_quality × signal_strength × convergence_score
    Each anchor carries an explicit falsifier:
        "If [event] does not occur by [date], this prediction is false"

Contract (BRAHMA PH-4-1):
    - source_citation non-null on all rows (B.3 mandate)
    - falsifier non-null on all rows (Learning Layer discipline rule #4)
    - provenance_envelope on every tool response
    - Migration: brahma_phala_anchors.sql (IF NOT EXISTS)
    - Native chart test: >= 3 anchors for 2026-2030 period

Native:   Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
          chart_id: 482012f1-710e-4a25-994a-93821f5871aa

Layer:    L4 Phala (depends on phala_anchors table seeded via migration)
Depends:  brahma_phala_anchors.sql
          FORENSIC v8.0 §5.1 DSH.V.023–028 (dasha ground-truth)
          MSR v5.0 SIG.* (signal ensemble)

Authors:  Silpī (PH-4-1 session)
Version:  1.0 — 2026-06-04
BRAHMA-PH-4-1
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timezone
from typing import Any, Optional

import psycopg
import psycopg.rows
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "482012f1-710e-4a25-994a-93821f5871aa"
)

# Valid prediction states
VALID_PREDICTION_STATES = frozenset({
    "open", "confirmed", "falsified", "expired"
})

# Valid theme families (extensible — used only for validation)
VALID_THEMES = frozenset({
    "career_consolidation",
    "spiritual_practice_intensification",
    "life_transition_preparatory",
    "regime_discontinuity_mercury_to_ketu",
    "relational_creative_activation",
    "wealth_karmic_resolution",
    "public_authority_emergence",
    "soul_level_atmakaraka_activation",
    "decisive_action_initiative",
})


# ── DB URL ────────────────────────────────────────────────────────────────────

def _get_db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key, "")
        if val:
            return val
    raise RuntimeError(
        "No database URL configured. Set DATABASE_URL, DIRECT_DATABASE_URL, or POSTGRES_URL."
    )


# ── Core engine ───────────────────────────────────────────────────────────────

def compute_window_score(
    dasha_quality: float,
    signal_strength: float,
    convergence_score: float,
) -> float:
    """
    score = CLAMP(dasha_quality × signal_strength × convergence_score, 0.0, 1.0)

    All three components must be in [0.0, 1.0].
    High confidence ≥ 0.65; Medium 0.45–0.64; Low < 0.45.

    This mirrors the SQL compute_window_score() function in brahma_phala_anchors.sql.
    """
    raw = dasha_quality * signal_strength * convergence_score
    return float(max(0.0, min(1.0, raw)))


def fetch_anchors(
    chart_id: str,
    range_start: date,
    range_end: date,
    min_confidence: float = 0.0,
    prediction_state: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve phala_anchors rows whose window overlaps [range_start, range_end].

    Overlap condition: window_start <= range_end AND window_end >= range_start.

    Args:
        chart_id:         Chart UUID.
        range_start:      Query window start (inclusive).
        range_end:        Query window end (inclusive).
        min_confidence:   Minimum confidence threshold [0.0, 1.0].
        prediction_state: Optional filter: 'open'|'confirmed'|'falsified'|'expired'.

    Returns:
        list[dict] — rows from phala_anchors, normalised.

    Raises:
        RuntimeError: DATABASE_URL not configured.
        ValueError:   Invalid prediction_state.
    """
    if not (0.0 <= min_confidence <= 1.0):
        raise ValueError(
            f"min_confidence must be in [0.0, 1.0], got {min_confidence}"
        )
    if prediction_state and prediction_state not in VALID_PREDICTION_STATES:
        raise ValueError(
            f"Invalid prediction_state '{prediction_state}'. "
            f"Valid: {sorted(VALID_PREDICTION_STATES)}"
        )

    conditions = [
        "chart_id = %s",
        "window_start <= %s",
        "window_end >= %s",
        "confidence >= %s",
    ]
    params: list[Any] = [chart_id, range_end, range_start, min_confidence]

    if prediction_state:
        conditions.append("prediction_state = %s")
        params.append(prediction_state)

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            id, chart_id, anchor_id,
            window_start, window_end,
            theme, confidence, falsifier,
            contributing_dashas, contributing_signals,
            source_citation,
            prediction_state, outcome_note, outcome_recorded_at,
            created_at, updated_at
        FROM public.phala_anchors
        WHERE {where}
        ORDER BY window_start ASC, confidence DESC
    """

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
                    elif isinstance(v, (list, dict)):
                        normalised[k] = v
                    elif isinstance(v, str) and v.startswith(("{", "[")):
                        try:
                            normalised[k] = json.loads(v)
                        except json.JSONDecodeError:
                            normalised[k] = v
                    else:
                        normalised[k] = v
                rows.append(normalised)

    return rows


def event_anchors(
    chart_id: str,
    date_range: dict[str, str],
    min_confidence: Optional[float] = None,
    prediction_state: Optional[str] = None,
) -> dict[str, Any]:
    """
    Main tool entry-point: event_anchors(chart_id, date_range, min_confidence?)

    Returns calibrated probabilistic event anchors for the requested window.
    Each anchor carries:
        - window (start/end dates)
        - theme
        - confidence (float in [0.0, 1.0])
        - falsifier (explicit, non-null)
        - contributing_dashas (JSONB array)
        - contributing_signals (JSONB array)
        - source_citation (non-null)

    Plus a provenance_envelope at the response root.

    Algorithm:
        For each 6-month window in 2026-2030 that overlaps the requested range,
        score = dasha_quality × signal_strength × convergence_score (pre-seeded).
        Rows are pre-computed and stored; this function is a retrieval engine.

    Args:
        chart_id:         Chart UUID.
        date_range:       Dict with 'start' and 'end' keys (ISO date strings).
        min_confidence:   Minimum confidence [0.0, 1.0]. Default 0.0.
        prediction_state: Optional filter for prediction lifecycle state.

    Returns:
        {
            "ok": True,
            "chart_id": str,
            "query_window": {"start": str, "end": str},
            "anchors": [...],
            "anchor_count": int,
            "provenance_envelope": {
                "source": "phala.anchors",
                "asset": "PH-4-1",
                "algorithm": "dasha_quality × signal_strength × convergence_score",
                "min_confidence_applied": float,
                "chart_id": str,
                "queried_at": str (ISO),
                "l1_ground_truth": "FORENSIC v8.0 §5.1 DSH.V.023–028",
                "b3_citation_compliant": bool,
                "all_falsifiers_present": bool,
            }
        }

    Raises:
        ValueError:   Invalid date_range format or min_confidence out of range.
        RuntimeError: DATABASE_URL not configured.
    """
    # Parse date range
    try:
        range_start = date.fromisoformat(date_range["start"])
        range_end = date.fromisoformat(date_range["end"])
    except (KeyError, ValueError) as exc:
        raise ValueError(
            f"date_range must have 'start' and 'end' ISO date strings: {exc}"
        ) from exc

    if range_start > range_end:
        raise ValueError(
            f"date_range start ({range_start}) must not be after end ({range_end})"
        )

    effective_min_conf = min_confidence if min_confidence is not None else 0.0
    if not (0.0 <= effective_min_conf <= 1.0):
        raise ValueError(
            f"min_confidence must be in [0.0, 1.0], got {effective_min_conf}"
        )

    # Fetch from DB
    anchors = fetch_anchors(
        chart_id=chart_id,
        range_start=range_start,
        range_end=range_end,
        min_confidence=effective_min_conf,
        prediction_state=prediction_state,
    )

    # Build structured anchor list for the response
    anchor_list = []
    for row in anchors:
        anchor_list.append({
            "anchor_id": row["anchor_id"],
            "window": {
                "start": row["window_start"],
                "end": row["window_end"],
            },
            "theme": row["theme"],
            "confidence": row["confidence"],
            "falsifier": row["falsifier"],
            "contributing_dashas": row["contributing_dashas"],
            "contributing_signals": row["contributing_signals"],
            "source_citation": row["source_citation"],
            "prediction_state": row["prediction_state"],
            "outcome_note": row["outcome_note"],
        })

    # Provenance checks
    b3_compliant = all(
        bool(r.get("source_citation")) for r in anchors
    )
    all_falsifiers_present = all(
        bool(r.get("falsifier")) for r in anchors
    )

    queried_at = datetime.now(tz=timezone.utc).isoformat()

    return {
        "ok": True,
        "chart_id": chart_id,
        "query_window": {
            "start": range_start.isoformat(),
            "end": range_end.isoformat(),
        },
        "anchors": anchor_list,
        "anchor_count": len(anchor_list),
        "provenance_envelope": {
            "source": "phala.anchors",
            "asset": "PH-4-1",
            "algorithm": "dasha_quality × signal_strength × convergence_score",
            "min_confidence_applied": effective_min_conf,
            "chart_id": chart_id,
            "queried_at": queried_at,
            "l1_ground_truth": "FORENSIC v8.0 §5.1 DSH.V.023–028; CHART_FACTS_EXTRACTION_v1_0.yaml",
            "b3_citation_compliant": b3_compliant,
            "all_falsifiers_present": all_falsifiers_present,
        },
    }


def seed_native_anchors(chart_id: str) -> dict[str, Any]:
    """
    Trigger the native anchor seed function in the DB for a given chart_id.

    Calls the SQL function seed_native_phala_anchors(chart_id::UUID)
    which inserts 9 pre-calibrated anchors for 2026-2030. Idempotent.

    Returns:
        {"ok": True, "rows_inserted": int, "chart_id": str}

    Raises:
        RuntimeError: DATABASE_URL not configured.
    """
    db_url = _get_db_url()
    sql = "SELECT seed_native_phala_anchors(%s::UUID) AS rows_inserted"

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [chart_id])
            result = cur.fetchone()
            rows_inserted = result["rows_inserted"] if result else 0
        conn.commit()

    logger.info(
        "seed_native_phala_anchors chart_id=%s rows_inserted=%d",
        chart_id, rows_inserted,
    )
    return {
        "ok": True,
        "rows_inserted": rows_inserted,
        "chart_id": chart_id,
    }


# ── Acceptance gate ───────────────────────────────────────────────────────────

def run_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    PH-4-1 acceptance gate.

    Gate criteria:
      AC1 — event_anchors returns >= 3 anchors for the 2026-2030 period.
      AC2 — all anchor.falsifier values are non-empty strings (Learning Layer rule #4).
      AC3 — all anchor.source_citation values are non-empty strings (B.3 mandate).
      AC4 — all anchor.confidence values are in [0.0, 1.0].
      AC5 — seed idempotency: calling seed twice does not increase count.

    Returns:
        {"chart_id": str, "gate_passed": bool, "checks": list[dict]}
    """
    checks: list[dict[str, Any]] = []

    # AC1: >= 3 anchors for 2026-2030
    try:
        result = event_anchors(
            chart_id=chart_id,
            date_range={"start": "2026-01-01", "end": "2030-12-31"},
        )
        anchors = result["anchors"]
        checks.append({
            "id": "AC1",
            "desc": "event_anchors returns >= 3 anchors for 2026-2030",
            "passed": len(anchors) >= 3,
            "value": len(anchors),
        })
    except Exception as exc:
        checks.append({
            "id": "AC1",
            "desc": "event_anchors 2026-2030 >= 3",
            "passed": False,
            "error": str(exc),
        })
        anchors = []

    # AC2: All falsifiers non-empty
    try:
        missing_falsifiers = [
            a["anchor_id"] for a in anchors if not a.get("falsifier")
        ]
        checks.append({
            "id": "AC2",
            "desc": "All anchors have non-empty falsifier (Learning Layer rule #4)",
            "passed": len(missing_falsifiers) == 0,
            "value": f"{len(anchors) - len(missing_falsifiers)}/{len(anchors)} have falsifiers",
            "missing": missing_falsifiers,
        })
    except Exception as exc:
        checks.append({"id": "AC2", "desc": "falsifier completeness", "passed": False, "error": str(exc)})

    # AC3: All source_citations non-empty
    try:
        missing_citations = [
            a["anchor_id"] for a in anchors if not a.get("source_citation")
        ]
        checks.append({
            "id": "AC3",
            "desc": "All anchors have non-empty source_citation (B.3 mandate)",
            "passed": len(missing_citations) == 0,
            "value": f"{len(anchors) - len(missing_citations)}/{len(anchors)} have citations",
            "missing": missing_citations,
        })
    except Exception as exc:
        checks.append({"id": "AC3", "desc": "citation completeness", "passed": False, "error": str(exc)})

    # AC4: All confidence values in [0.0, 1.0]
    try:
        out_of_range = [
            (a["anchor_id"], a["confidence"])
            for a in anchors
            if not (0.0 <= float(a["confidence"]) <= 1.0)
        ]
        checks.append({
            "id": "AC4",
            "desc": "All confidence values in [0.0, 1.0]",
            "passed": len(out_of_range) == 0,
            "value": f"{len(anchors) - len(out_of_range)}/{len(anchors)} in range",
            "out_of_range": out_of_range,
        })
    except Exception as exc:
        checks.append({"id": "AC4", "desc": "confidence range", "passed": False, "error": str(exc)})

    # AC5: Seed idempotency
    try:
        seed_result_1 = seed_native_anchors(chart_id)
        seed_result_2 = seed_native_anchors(chart_id)
        # Second call should insert 0 (ON CONFLICT DO NOTHING)
        idempotent = seed_result_2["rows_inserted"] == 0
        checks.append({
            "id": "AC5",
            "desc": "seed_native_anchors is idempotent (2nd call inserts 0 rows)",
            "passed": idempotent,
            "value": {
                "first_call_inserted": seed_result_1["rows_inserted"],
                "second_call_inserted": seed_result_2["rows_inserted"],
            },
        })
    except Exception as exc:
        checks.append({"id": "AC5", "desc": "seed idempotency", "passed": False, "error": str(exc)})

    gate_passed = all(c["passed"] for c in checks)
    if gate_passed:
        logger.info("PH-4-1 acceptance gate PASSED for chart_id=%s", chart_id)
    else:
        failed = [c["id"] for c in checks if not c["passed"]]
        logger.error("PH-4-1 acceptance gate FAILED for chart_id=%s — %s", chart_id, failed)

    return {"chart_id": chart_id, "gate_passed": gate_passed, "checks": checks}


# ── FastAPI request/response models ───────────────────────────────────────────

class DateRange(BaseModel):
    start: str = Field(..., description="ISO date string (YYYY-MM-DD)")
    end: str = Field(..., description="ISO date string (YYYY-MM-DD)")


class EventAnchorsRequest(BaseModel):
    chart_id: str = Field(..., description="Chart UUID")
    date_range: DateRange = Field(..., description="Query window — must overlap anchors")
    min_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Minimum confidence [0.0, 1.0]. Default 0.0."
    )
    prediction_state: Optional[str] = Field(
        None,
        description="Filter by state: open|confirmed|falsified|expired. Default: all states."
    )


class SeedAnchorsRequest(BaseModel):
    chart_id: str = Field(..., description="Chart UUID to seed native anchors for")


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

@router.post("/phala/event_anchors")
def api_event_anchors(req: EventAnchorsRequest) -> dict[str, Any]:
    """
    PH-4-1 event_anchors tool.

    Returns calibrated probabilistic event anchors for the requested date window.
    Each anchor: {window, theme, confidence [0-1], falsifier, contributing_dashas,
    contributing_signals, source_citation} + provenance_envelope at response root.

    Algorithm: dasha_quality × signal_strength × convergence_score, pre-seeded
    from FORENSIC v8.0 §5.1 + MSR v5.0. B.3 citations and falsifiers are mandatory.
    """
    try:
        return event_anchors(
            chart_id=req.chart_id,
            date_range={"start": req.date_range.start, "end": req.date_range.end},
            min_confidence=req.min_confidence,
            prediction_state=req.prediction_state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/phala/seed_anchors")
def api_seed_anchors(req: SeedAnchorsRequest) -> dict[str, Any]:
    """
    Seed pre-calibrated phala anchors for a chart.

    Calls seed_native_phala_anchors(chart_id) in the DB (idempotent).
    Inserts 9 anchors for 2026-2030 for the native's chart.
    """
    try:
        return seed_native_anchors(req.chart_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/phala/acceptance_gate/{chart_id}")
def api_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    PH-4-1 acceptance gate.

    AC1: >= 3 anchors for 2026-2030.
    AC2: All falsifiers non-empty (Learning Layer rule #4).
    AC3: All source_citations non-empty (B.3 mandate).
    AC4: All confidence values in [0.0, 1.0].
    AC5: seed_native_anchors is idempotent.
    """
    try:
        return run_acceptance_gate(chart_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
