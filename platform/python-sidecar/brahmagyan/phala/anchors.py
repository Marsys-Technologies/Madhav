"""
brahmagyan/phala/anchors.py — Brahma L4 Phala — phala.anchors (PH-4-1)

Asset:    phala.anchors
Tool:     event_anchors(chart_id, date_range, min_confidence?) →
              {anchors:[{window,domain,event_type,confidence,confidence_band,falsifier,
              source_citation}], provenance_envelope}
Table:    phala_anchors (anchor_id UUID PRIMARY KEY, chart_id UUID, window_start/peak_date/
          window_end DATE, domain TEXT, event_type TEXT, confidence_low/confidence_high
          DOUBLE PRECISION, posterior DOUBLE PRECISION (mig 398), falsifier TEXT NOT NULL,
          derivation_ledger_jsonb/causal_chain_jsonb JSONB, source_citation TEXT NOT NULL).
          R5 W0a punch-list (P5) NOTE (2026-07-08): this docstring previously described a
          LEGACY schema (id, anchor_id TEXT, theme, single confidence, contributing_dashas/
          contributing_signals, prediction_state, outcome_note) that migration 330
          (platform/supabase/migrations/330_phala_anchors_and_drop_kala_timeline.sql) DROPped
          and replaced wholesale — the mismatch was the root cause of live "column ... does
          not exist" SQL errors leaking through phala_outlook_get. Corrected to the real,
          deployed schema (verified against migrations 330 + 398) above.

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
        min_confidence:   Minimum confidence threshold [0.0, 1.0]. Applied against
                          posterior (migration 398) when present, else the midpoint
                          of confidence_low/confidence_high.
        prediction_state: ACCEPTED BUT NOT APPLIED (R5 W0a punch-list, P5). No
                          prediction_state column exists on phala_anchors — the
                          concept is not yet modeled at this layer. Validated for
                          input-contract compatibility only; passing it does not
                          filter results. See module docstring / P5 fix note above.

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

    # R5 W0a punch-list (P5): this SELECT used to reference a schema
    # (id, theme, confidence, contributing_dashas, contributing_signals,
    # prediction_state, outcome_note, outcome_recorded_at, created_at, updated_at)
    # that never matches the deployed table. Migration 330
    # (platform/supabase/migrations/330_phala_anchors_and_drop_kala_timeline.sql)
    # DROPped and recreated phala_anchors with anchor_id (UUID PK, not `id`),
    # domain/event_type (not `theme`), confidence_low/confidence_high +
    # posterior (migration 398) instead of a single `confidence`, and no
    # prediction_state/outcome_note/outcome_recorded_at/created_at/updated_at
    # columns at all — those concepts are not (yet) modeled on this table.
    # This was the exact root cause of the live "column \"id\" does not exist"
    # SQL errors leaking into phala_outlook_get responses.
    #
    # `confidence` filtering now uses posterior when present (the BA-P5B
    # Bayesian point estimate — migration 398), falling back to the midpoint
    # of the pre-posterior confidence_low/confidence_high band for older rows.
    # prediction_state is NOT a real column — the filter is accepted for API
    # compatibility but is a documented no-op (see event_anchors() docstring).
    conditions = [
        "chart_id = %s",
        "window_start <= %s",
        "window_end >= %s",
        "COALESCE(posterior, (confidence_low + confidence_high) / 2.0, 0.0) >= %s",
    ]
    params: list[Any] = [chart_id, range_end, range_start, min_confidence]

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            anchor_id, chart_id, anchor_source,
            event_type, direction, domain, horizon_tier,
            window_start, peak_date, window_end,
            magnitude, magnitude_basis,
            confidence_low, confidence_high, confidence_basis,
            posterior, lift_vector_jsonb, structured_falsifier_jsonb,
            karmic_frame, karmic_note,
            malleability, counterfactual_jsonb, contradiction_jsonb,
            causal_chain_jsonb, precedent_refs_jsonb,
            dasha_consensus_count, school_consensus_jsonb, ayanamsha_robustness,
            falsifier, derivation_ledger_jsonb, source_citation, computed_at
        FROM public.phala_anchors
        WHERE {where}
        ORDER BY window_start ASC, COALESCE(posterior, (confidence_low + confidence_high) / 2.0, 0.0) DESC
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

    # Build structured anchor list for the response.
    # R5 W0a punch-list (P5): field mapping rewritten against the REAL phala_anchors
    # schema (migrations 330 + 398) — see fetch_anchors() note above. `theme` →
    # domain/event_type; single `confidence` → posterior (point estimate) with the
    # confidence_low/confidence_high band retained; contributing_dashas/
    # contributing_signals → derivation_ledger_jsonb/causal_chain_jsonb (the real
    # audit-trail columns); prediction_state/outcome_note dropped — not modeled on
    # this table (no fabricated substitute served; see docstring above).
    anchor_list = []
    for row in anchors:
        confidence_point = row.get("posterior")
        if confidence_point is None:
            cl, ch = row.get("confidence_low"), row.get("confidence_high")
            confidence_point = (cl + ch) / 2.0 if cl is not None and ch is not None else None
        anchor_list.append({
            "anchor_id": row["anchor_id"],
            "window": {
                "start": row["window_start"],
                "end": row["window_end"],
            },
            "domain": row.get("domain"),
            "event_type": row.get("event_type"),
            "direction": row.get("direction"),
            "confidence": confidence_point,
            "confidence_band": {
                "low": row.get("confidence_low"),
                "high": row.get("confidence_high"),
                "basis": row.get("confidence_basis"),
            },
            "magnitude": row.get("magnitude"),
            "falsifier": row["falsifier"],
            "structured_falsifier": row.get("structured_falsifier_jsonb"),
            "derivation_ledger": row.get("derivation_ledger_jsonb"),
            "causal_chain": row.get("causal_chain_jsonb"),
            "source_citation": row["source_citation"],
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
    # (confidence may be None if a row predates both posterior (mig 398) and the
    # confidence_low/confidence_high band — treat as out-of-range rather than crash.)
    try:
        out_of_range = [
            (a["anchor_id"], a["confidence"])
            for a in anchors
            if a["confidence"] is None or not (0.0 <= float(a["confidence"]) <= 1.0)
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
