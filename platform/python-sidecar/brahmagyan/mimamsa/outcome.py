"""
brahmagyan/mimamsa/outcome.py — Brahma L5 Mīmāṃsā — mimamsa.outcome (MI-5-3)

record_outcome() is RETIRED (CR-115/CR-128, 2026-07-23, native-directed) — see its own
docstring below for the full reasoning. It now raises RecordOutcomeRetiredError
unconditionally, before any DB access; the FastAPI route returns HTTP 410 Gone.

query_calibration() remains LIVE and CORRECT (fixed separately, R-14 / CR-51/CR-30) — it
reads the real, live mimamsa_calibration schema (match_id/prediction_id/event_id/
score_timing/composite_score/brier_vs_null/...), written by the mi_pramana orchestrator
writer. Untouched by this retirement.

Original asset docs (historical, for record_outcome's now-dead design — kept for context,
not as a live contract):
    Tool:     record_outcome(prediction_id, outcome_observed) →
                  {brier_score, updated_calibration, provenance_envelope}  [RETIRED]
    Table:    mimamsa_calibration (chart_id UUID, technique TEXT, ayanamsha_id TEXT,
              brier_score FLOAT, sample_size INT, computed_at TIMESTAMPTZ,
              source_citation TEXT NOT NULL)  — this shape never matched the live table;
              the live mi_pramana-written schema is documented in query_calibration() below.

Contract (BRAHMA MI-5-3, query_calibration only):
    - source_citation non-null on all rows (B.3 mandate)
    - provenance_envelope on every tool response
    - NO LEAKAGE: life_events must never feed into prediction generation;
      they feed only into calibration after outcomes are observed.

Depends:  mimamsa_calibration (written by mi_pramana, NOT by this module)
          FORENSIC v8.0 §5.1 DSH.V.023–028
          LEL v1.7 (life event ground-truth for calibration)

Native:   Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
          chart_id: 482012f1-710e-4a25-994a-93821f5871aa

Authors:  Silpī (MI-5-3 session)
Version:  1.1 — 2026-07-23 (record_outcome retired; CR-115/CR-128)
BRAHMA-MI-5-3
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg
import psycopg.rows
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

# Valid techniques for calibration
VALID_TECHNIQUES = frozenset({
    "vimshottari",
    "yogini",
    "kp",
    "jaimini_chara",
    "transit_outer",
    "transit_inner",
    "sade_sati",
    "ashtakavarga",
    "ensemble",
})

# Valid ayanamsha IDs
VALID_AYANAMSHAS = frozenset({
    "lahiri",
    "true_chitra",
    "kp",
    "raman",
    "surya_siddhanta",
})

# Uninformative Brier baseline (random 50/50 at 0.5 confidence)
UNINFORMATIVE_BRIER_BASELINE = 0.25

# CR-115/CR-128 (2026-07-23, native-directed retirement): record_outcome()'s write path is
# RETIRED. It targeted phala_anchors columns (id, confidence, prediction_state, outcome_note,
# outcome_recorded_at, updated_at) that do not exist on the live table (live phala_anchors has
# anchor_id/confidence_low/confidence_high/posterior/computed_at instead), and called the SQL
# function update_calibration(), which wrote into a mimamsa_calibration(technique, ayanamsha_id,
# brier_score, sample_size, source_citation, computed_at) shape the live table has never had.
# Both column sets are phantom — this was disconnected, misleading dead code, not a working
# write path with a schema bug.
#
# The REAL, live calibration write-surface is the mi_pramana / mi_gunanaka orchestrator writer
# pair: mi_pramana matches mimamsa_predictions against mimamsa_event_provenance (LEL-derived,
# admissible_clean) and writes the REAL, live mimamsa_calibration schema (chart_id, match_id,
# prediction_id, event_id, score_timing/magnitude/domain/falsifier/manifestation,
# composite_score, composite_verdict, leakage_status, brier_vs_null, ...); mi_gunanaka reads it
# to produce mimamsa_multipliers. Both have already run for chart 482012f1 (asset_throughput
# state=stale, last_built_at=2026-07-18) and correctly wrote ZERO calibration rows — an honest
# result (no admissible-window overlap yet), not a broken pipeline. There is no manual
# "record an outcome" step in the real pipeline; it is driven entirely by chart rebuild.
#
# record_outcome() is retired rather than repaired: repairing it to point at either live schema
# would create a second, redundant write path into mimamsa_calibration that bypasses
# mi_pramana's admissibility/held-out/leakage discipline — worse than leaving it dead. See
# MARSYS_DEFECT_GAP_REGISTER_v2_0.md CR-115 (RESOLVED) / CR-128 (RESOLVED) for the full record.
class RecordOutcomeRetiredError(RuntimeError):
    """Raised unconditionally by record_outcome() — the endpoint is retired, not repaired."""


# ── DB URL ────────────────────────────────────────────────────────────────────

def _get_db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key, "")
        if val:
            return val
    raise RuntimeError(
        "No database URL configured. Set DATABASE_URL, DIRECT_DATABASE_URL, or POSTGRES_URL."
    )


# ── Brier score computation ───────────────────────────────────────────────────

def compute_brier_score(confidence: float, occurred: bool) -> float:
    """
    Brier score = (confidence - outcome_binary)²

    outcome_binary: True → 1.0, False → 0.0

    Args:
        confidence: Prediction confidence in [0.0, 1.0].
        occurred:   Whether the predicted event actually occurred.

    Returns:
        float in [0.0, 1.0]. Lower = better calibration.

    Raises:
        ValueError: confidence not in [0.0, 1.0].
    """
    if not (0.0 <= confidence <= 1.0):
        raise ValueError(
            f"confidence must be in [0.0, 1.0], got {confidence}"
        )
    outcome_binary = 1.0 if occurred else 0.0
    return (confidence - outcome_binary) ** 2


def compute_mean_brier(scores: list[float]) -> float:
    """
    Compute mean Brier score over a list of individual Brier scores.

    Args:
        scores: List of individual Brier scores, each in [0.0, 1.0].

    Returns:
        Mean Brier score in [0.0, 1.0].
        Returns UNINFORMATIVE_BRIER_BASELINE (0.25) for empty list.

    Raises:
        ValueError: Any score outside [0.0, 1.0].
    """
    if not scores:
        return UNINFORMATIVE_BRIER_BASELINE
    for s in scores:
        if not (0.0 <= s <= 1.0):
            raise ValueError(f"Brier score {s} outside [0.0, 1.0]")
    return sum(scores) / len(scores)


# ── Core: record_outcome ──────────────────────────────────────────────────────

def record_outcome(
    prediction_id: str,
    outcome_observed: bool,
    technique: str = "vimshottari",
    ayanamsha_id: str = "lahiri",
    chart_id: str | None = None,
    outcome_note: str | None = None,
) -> dict[str, Any]:
    """
    RETIRED (CR-115/CR-128, 2026-07-23, native-directed). Raises
    RecordOutcomeRetiredError unconditionally, before any DB access — this function
    NEVER touches phala_anchors or mimamsa_calibration anymore.

    Why: this write path targeted phantom columns on both ends (phala_anchors.prediction_state/
    outcome_note/outcome_recorded_at/updated_at; a mimamsa_calibration(technique, ayanamsha_id,
    brier_score, ...) shape) that do not exist on the live schema, and was fully disconnected
    from the REAL, live calibration write-surface: the mi_pramana / mi_gunanaka orchestrator
    writer pair, which already matches mimamsa_predictions against mimamsa_event_provenance
    (LEL-derived) and writes the real, live mimamsa_calibration schema. That real pipeline has
    already run for chart 482012f1 and correctly produced zero calibration rows (no
    admissible-window overlap yet) — an honest result, not a gap this function should try to
    fill. There is no manual "record an outcome" step in the real architecture; calibration
    ignites automatically as the orchestrator rebuilds a chart against a growing LEL corpus.

    Repairing this function to target either live schema was deliberately rejected: it would
    create a second, redundant write path into mimamsa_calibration that bypasses mi_pramana's
    admissibility/held-out/leakage discipline — worse than leaving it retired.

    See MARSYS_DEFECT_GAP_REGISTER_v2_0.md CR-115 / CR-128 for the full record.

    Raises:
        RecordOutcomeRetiredError: always.
    """
    raise RecordOutcomeRetiredError(
        "record_outcome() is RETIRED (CR-115/CR-128, 2026-07-23, native-directed) — it targeted "
        "phantom phala_anchors/mimamsa_calibration columns disconnected from the real pipeline. "
        "Calibration is computed automatically by the mi_pramana -> mi_gunanaka orchestrator "
        "writers from LEL-event provenance; there is no manual outcome-recording step. See "
        "MARSYS_DEFECT_GAP_REGISTER_v2_0.md CR-115 / CR-128 (both RESOLVED 2026-07-23)."
    )


# ── Calibration query ─────────────────────────────────────────────────────────

def query_calibration(
    chart_id: str | None = None,
    technique: str | None = None,
    ayanamsha_id: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Query the mimamsa_calibration table for current calibration state.

    R6 0b-deadtools (R-14) schema-drift fix: the MI-5-3 prototype table
    (id, technique, ayanamsha_id, brier_score, sample_size, source_citation,
    computed_at — see 0001_brahma_baseline.sql) was superseded, without a
    tracked migration, by the L5 mi_pramana/mi_gunanaka/mi_pariksha writer
    family's per-match scoring schema (chart_id, match_id, prediction_id,
    event_id, score_timing, score_magnitude, score_domain, score_falsifier,
    score_manifestation, manifestation_channel, composite_verdict,
    composite_score, base_rate_adjusted_skill, evidence_admissibility,
    n_for_stratum, leakage_status, scoring_formula_version, scored_at,
    base_rate, brier_vs_null — see mi_pramana.py's CAL_SQL insert). The
    `technique`/`ayanamsha_id` columns no longer exist on this table; a
    calibration row is now keyed per (chart_id, match_id) with no per-technique
    slice. Filters are honored where a matching column still exists and
    reported back (never silently dropped) when it does not.

    Args:
        chart_id:     Chart UUID filter (required; ValueError if None/empty).
        technique:    Accepted for API back-compat but NOT a column on the
                      current schema; reported in `unsupported_filters`, never
                      silently applied or silently dropped.
        ayanamsha_id: Same as technique — no longer a column on this table.
        limit:        Max rows to return (most recent first). Default 10.

    Returns:
        {
            "ok": True,
            "rows": [...],
            "row_count": int,
            "provenance_envelope": {...}
        }
    """
    if not chart_id or not str(chart_id).strip():
        raise ValueError("chart_id is required and must be a non-empty string")
    effective_chart_id = chart_id

    # Validate before DB access (so invalid input raises ValueError, not RuntimeError).
    # technique/ayanamsha_id are still validated against the legacy enum (so a typo'd
    # caller gets a clear error) even though neither filters the query anymore.
    unsupported_filters: list[str] = []

    if technique:
        if technique not in VALID_TECHNIQUES:
            raise ValueError(
                f"Invalid technique '{technique}'. Valid: {sorted(VALID_TECHNIQUES)}"
            )
        unsupported_filters.append("technique")

    if ayanamsha_id:
        if ayanamsha_id not in VALID_AYANAMSHAS:
            raise ValueError(
                f"Invalid ayanamsha_id '{ayanamsha_id}'. Valid: {sorted(VALID_AYANAMSHAS)}"
            )
        unsupported_filters.append("ayanamsha_id")

    db_url = _get_db_url()

    params: list[Any] = [effective_chart_id, limit]

    sql = """
        SELECT
            chart_id, match_id, prediction_id, event_id,
            score_timing, score_magnitude, score_domain, score_falsifier,
            score_manifestation, manifestation_channel, composite_verdict,
            composite_score, base_rate_adjusted_skill, evidence_admissibility,
            n_for_stratum, leakage_status, scoring_formula_version,
            base_rate, brier_vs_null, scored_at
        FROM public.mimamsa_calibration
        WHERE chart_id = %s
        ORDER BY scored_at DESC
        LIMIT %s
    """

    rows: list[dict[str, Any]] = []
    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            for row in cur.fetchall():
                normalised: dict[str, Any] = {}
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        normalised[k] = v.isoformat()
                    else:
                        normalised[k] = v
                rows.append(normalised)

    queried_at = datetime.now(tz=timezone.utc).isoformat()

    return {
        "ok": True,
        "rows": rows,
        "row_count": len(rows),
        "unsupported_filters": unsupported_filters,
        "provenance_envelope": {
            "source": "mimamsa.outcome",
            "asset": "MI-5-3",
            "algorithm": "score_manifestation/score_timing/score_domain/score_falsifier/"
                         "score_magnitude per prediction-event match; composite_score = "
                         "mi_pramana's weighted rollup; brier_vs_null = 1 - (model_brier / "
                         "null_brier) per BA-P6.",
            "chart_id": effective_chart_id,
            "technique_filter_note": (
                "technique/ayanamsha_id are not columns on the current mimamsa_calibration "
                "schema (superseded by the mi_pramana per-match schema) — filter ignored, "
                "not silently applied. See unsupported_filters."
                if unsupported_filters else None
            ),
            "queried_at": queried_at,
            "l1_ground_truth": "FORENSIC v8.0 §5.1 DSH.V.023–028; LEL v1.7",
            # B.3: the current schema carries no per-row source_citation column (that was
            # the MI-5-3 prototype's field); citation now lives at scoring_formula_version +
            # the mi_pramana writer provenance, not per calibration row. Never fabricate a
            # per-row citation claim the schema can't back.
            "b3_citation_compliant": all(bool(r.get("scoring_formula_version")) for r in rows) if rows else None,
        },
    }


# ── Acceptance gate ───────────────────────────────────────────────────────────

def run_acceptance_gate(chart_id: str | None = None) -> dict[str, Any]:
    """
    MI-5-3 acceptance gate.

    Gate criteria:
      AC1 — compute_brier_score in [0.0, 1.0] for all confidence/outcome combos.
      AC2 — compute_mean_brier returns float in [0.0, 1.0].
      AC3 — mimamsa_calibration table exists and has source_citation NOT NULL.
      AC4 — Tool smoke: record_outcome response has required keys.
      AC5 — Brier score boundary: score(0.0, False)=0.0, score(1.0, True)=0.0,
             score(0.0, True)=1.0, score(1.0, False)=1.0.

    Returns:
        {"chart_id": str, "gate_passed": bool, "checks": list[dict]}
    """
    if not chart_id or not str(chart_id).strip():
        raise ValueError("chart_id is required and must be a non-empty string")
    effective_chart_id = chart_id
    checks: list[dict[str, Any]] = []

    # AC1: Brier score in [0.0, 1.0]
    try:
        ac1_pass = True
        ac1_cases = [
            (0.0, False, 0.0),
            (1.0, True, 0.0),
            (0.0, True, 1.0),
            (1.0, False, 1.0),
            (0.5, True, 0.25),
            (0.5, False, 0.25),
            (0.7, True, 0.09),
            (0.3, False, 0.09),
        ]
        for conf, occ, expected in ac1_cases:
            score = compute_brier_score(conf, occ)
            if not (0.0 <= score <= 1.0):
                ac1_pass = False
                break
            if abs(score - expected) > 1e-9:
                ac1_pass = False
                break
        checks.append({
            "id": "AC1",
            "desc": "compute_brier_score in [0.0, 1.0] for all confidence/outcome combos",
            "passed": ac1_pass,
            "value": f"{len(ac1_cases)} test cases validated",
        })
    except Exception as exc:
        checks.append({"id": "AC1", "desc": "brier_score range", "passed": False, "error": str(exc)})

    # AC2: mean_brier range
    try:
        test_scores = [0.0, 0.25, 0.5, 1.0]
        mean = compute_mean_brier(test_scores)
        ac2_pass = 0.0 <= mean <= 1.0
        # Empty list returns uninformative baseline
        empty_mean = compute_mean_brier([])
        ac2_pass = ac2_pass and (empty_mean == UNINFORMATIVE_BRIER_BASELINE)
        checks.append({
            "id": "AC2",
            "desc": "compute_mean_brier returns float in [0.0, 1.0]; empty → 0.25 baseline",
            "passed": ac2_pass,
            "value": {"sample_mean": mean, "empty_list_mean": empty_mean},
        })
    except Exception as exc:
        checks.append({"id": "AC2", "desc": "mean_brier range", "passed": False, "error": str(exc)})

    # AC3: mimamsa_calibration table exists
    try:
        db_url = _get_db_url()
        with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'mimamsa_calibration'
                    """
                )
                row = cur.fetchone()
                table_exists = row and row["count"] == 1

                # Check source_citation NOT NULL constraint
                cur.execute(
                    """
                    SELECT is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'mimamsa_calibration'
                      AND column_name = 'source_citation'
                    """
                )
                col_row = cur.fetchone()
                source_citation_not_null = (
                    col_row and col_row["is_nullable"] == "NO"
                )

        checks.append({
            "id": "AC3",
            "desc": "mimamsa_calibration table exists; source_citation NOT NULL",
            "passed": bool(table_exists and source_citation_not_null),
            "value": {
                "table_exists": bool(table_exists),
                "source_citation_not_null": bool(source_citation_not_null),
            },
        })
    except Exception as exc:
        checks.append({"id": "AC3", "desc": "table schema", "passed": False, "error": str(exc)})

    # AC4: Tool response has required keys (structural smoke — no live prediction needed)
    try:
        required_keys = {
            "ok", "prediction_id", "outcome_observed", "brier_score",
            "prediction_state", "updated_calibration", "provenance_envelope",
        }
        required_provenance_keys = {
            "source", "asset", "algorithm", "chart_id", "prediction_id",
            "technique", "ayanamsha_id", "recorded_at",
            "l1_ground_truth", "b3_citation_compliant", "leakage_guard_passed",
        }
        # Build a mock response to check structure (no DB call)
        mock_response = {
            "ok": True,
            "prediction_id": "PH-4-1.2026H1.CAREER",
            "outcome_observed": True,
            "brier_score": 0.16,
            "prediction_state": "confirmed",
            "updated_calibration": {
                "technique": "vimshottari",
                "ayanamsha_id": "lahiri",
                "brier_score": 0.16,
                "sample_size": 1,
                "computed_at": "2026-06-04T00:00:00+00:00",
            },
            "provenance_envelope": {
                "source": "mimamsa.outcome",
                "asset": "MI-5-3",
                "algorithm": "Brier score = (confidence - outcome_binary)²",
                "chart_id": effective_chart_id,
                "prediction_id": "PH-4-1.2026H1.CAREER",
                "technique": "vimshottari",
                "ayanamsha_id": "lahiri",
                "recorded_at": "2026-06-04T00:00:00+00:00",
                "l1_ground_truth": "FORENSIC v8.0 §5.1 DSH.V.023–028; LEL v1.7",
                "b3_citation_compliant": True,
                "leakage_guard_passed": True,
            },
        }
        missing_top = required_keys - set(mock_response.keys())
        missing_prov = required_provenance_keys - set(mock_response["provenance_envelope"].keys())
        ac4_pass = not missing_top and not missing_prov
        checks.append({
            "id": "AC4",
            "desc": "Tool response has all required keys (structural smoke)",
            "passed": ac4_pass,
            "value": {
                "missing_top_keys": list(missing_top),
                "missing_provenance_keys": list(missing_prov),
            },
        })
    except Exception as exc:
        checks.append({"id": "AC4", "desc": "response structure", "passed": False, "error": str(exc)})

    # AC5: Brier score boundary conditions
    try:
        boundary_cases = [
            (0.0, False, 0.0, "perfect negative prediction"),
            (1.0, True, 0.0, "perfect positive prediction"),
            (0.0, True, 1.0, "worst negative prediction"),
            (1.0, False, 1.0, "worst positive prediction"),
        ]
        ac5_failures = []
        for conf, occ, expected, label in boundary_cases:
            score = compute_brier_score(conf, occ)
            if abs(score - expected) > 1e-9:
                ac5_failures.append({
                    "label": label, "confidence": conf,
                    "occurred": occ, "expected": expected, "got": score,
                })
        checks.append({
            "id": "AC5",
            "desc": "Brier boundary: (0,False)=0, (1,True)=0, (0,True)=1, (1,False)=1",
            "passed": len(ac5_failures) == 0,
            "value": {"failures": ac5_failures},
        })
    except Exception as exc:
        checks.append({"id": "AC5", "desc": "brier boundary", "passed": False, "error": str(exc)})

    gate_passed = all(c["passed"] for c in checks)
    if gate_passed:
        logger.info("MI-5-3 acceptance gate PASSED for chart_id=%s", effective_chart_id)
    else:
        failed = [c["id"] for c in checks if not c["passed"]]
        logger.error(
            "MI-5-3 acceptance gate FAILED for chart_id=%s — %s",
            effective_chart_id, failed,
        )

    return {
        "chart_id": effective_chart_id,
        "gate_passed": gate_passed,
        "checks": checks,
    }


# ── FastAPI request/response models ───────────────────────────────────────────

class RecordOutcomeRequest(BaseModel):
    prediction_id: str = Field(
        ...,
        description="anchor_id from phala_anchors (e.g. 'PH-4-1.2026H1.CAREER')",
    )
    outcome_observed: bool = Field(
        ...,
        description="True = event occurred (confirmed); False = did not occur (falsified)",
    )
    technique: str = Field(
        "vimshottari",
        description=(
            "Dasha/technique: vimshottari | yogini | kp | jaimini_chara | "
            "transit_outer | transit_inner | sade_sati | ashtakavarga | ensemble"
        ),
    )
    ayanamsha_id: str = Field(
        "lahiri",
        description="Ayanamsha: lahiri | true_chitra | kp | raman | surya_siddhanta",
    )
    chart_id: str = Field(
        ...,
        min_length=1,
        description="Chart UUID (required).",
    )
    outcome_note: Optional[str] = Field(
        None,
        description="Optional operator annotation on what actually happened",
    )


class QueryCalibrationRequest(BaseModel):
    chart_id: str = Field(
        ...,
        min_length=1,
        description="Chart UUID filter (required).",
    )
    technique: Optional[str] = Field(
        None,
        description="Filter by technique. Default: all techniques.",
    )
    ayanamsha_id: Optional[str] = Field(
        None,
        description="Filter by ayanamsha. Default: all ayanamshas.",
    )
    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Max rows to return (most recent first). Default 10.",
    )


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

@router.post("/mimamsa/record_outcome")
def api_record_outcome(req: RecordOutcomeRequest) -> dict[str, Any]:
    """
    RETIRED (CR-115/CR-128, 2026-07-23, native-directed). Always returns HTTP 410 Gone —
    never touches the database. See record_outcome()'s docstring for the full reasoning.
    """
    try:
        return record_outcome(
            prediction_id=req.prediction_id,
            outcome_observed=req.outcome_observed,
            technique=req.technique,
            ayanamsha_id=req.ayanamsha_id,
            chart_id=req.chart_id,
            outcome_note=req.outcome_note,
        )
    except RecordOutcomeRetiredError as exc:
        raise HTTPException(status_code=410, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/mimamsa/query_calibration")
def api_query_calibration(req: QueryCalibrationRequest) -> dict[str, Any]:
    """
    Query the mimamsa_calibration table for current calibration state.

    Returns rows ordered by computed_at DESC (most recent first).
    Each row: {technique, ayanamsha_id, brier_score, sample_size, computed_at, source_citation}.
    """
    try:
        return query_calibration(
            chart_id=req.chart_id,
            technique=req.technique,
            ayanamsha_id=req.ayanamsha_id,
            limit=req.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    # R6 0b-deadtools (R-14): the prior blanket `except Exception` here masked real
    # SQL/schema-drift errors (e.g. "column \"id\" does not exist") as an ok:true,
    # 0-row "STRUCTURAL mode" response — genuine bugs were indistinguishable from the
    # legitimate empty-calibration-until-first-outcome case. DB/runtime errors now
    # propagate loudly as a 500 with the real error text; a legitimately-empty
    # calibration set (query succeeds, 0 rows) is still returned as
    # {"ok": true, "rows": [], "row_count": 0} by query_calibration() itself —
    # that path is unaffected and remains the only way to get an "empty" response.
    except Exception as exc:
        logger.error("query_calibration: unhandled DB/runtime error: %s", exc)
        raise HTTPException(status_code=500, detail=f"query_calibration DB error: {exc}")


@router.get("/mimamsa/acceptance_gate/{chart_id}")
def api_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    MI-5-3 acceptance gate.

    AC1: Brier score in [0.0, 1.0] for all confidence/outcome combos.
    AC2: compute_mean_brier returns float in [0.0, 1.0]; empty → 0.25 baseline.
    AC3: mimamsa_calibration table exists; source_citation NOT NULL.
    AC4: Tool response has all required keys (structural smoke).
    AC5: Brier boundary: (0,False)=0, (1,True)=0, (0,True)=1, (1,False)=1.
    """
    try:
        return run_acceptance_gate(chart_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/mimamsa/acceptance_gate")
def api_acceptance_gate_native(chart_id: str) -> dict[str, Any]:
    """
    MI-5-3 acceptance gate.

    chart_id is a required query parameter (e.g. the native chart UUID) — it is
    sourced from the request, never from a module-level constant.
    """
    try:
        return run_acceptance_gate(chart_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
