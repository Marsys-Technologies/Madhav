"""
brahmagyan/mimamsa/answer_quality.py — Brahma L5 Mīmāṃsā — mimamsa.answer_quality (MI-5-6)

Asset:    mimamsa.answer_quality
Tool:     answer_quality_eval(question, actual_response) →
              {b11_compliance, layer_coverage, grounding_score, provenance_envelope}
Table:    mimamsa_qa_eval (eval_id UUID, question TEXT NOT NULL,
          expected_domains TEXT[], actual_response TEXT,
          b11_compliance BOOLEAN, layer_coverage FLOAT CHECK(0<=c<=1),
          grounding_score FLOAT CHECK(0<=s<=1),
          evaluated_at TIMESTAMPTZ, source_citation TEXT NOT NULL)

Golden Q&A eval — distinct from prediction calibration (phala.anchors).
Covers all 6 Brahma layers (L0–L5): 10 pairs seeded, 2 per layer minimum.

Source citation on all rows: "Brahma QA golden set v1.0"

Layers evaluated:
    L0 Brahmagyan  — instrument meta-layer identity
    L1 Gaṇita      — astronomical facts (FORENSIC v8.0)
    L2 Bodha       — holistic synthesis signals (MSR, UCN, CGM, CDLM, RM)
    L3 Kāla        — temporal / dasha engines
    L4 Phala       — calibrated predictions / anchors
    L5 Mīmāṃsā     — answer quality (this layer)

B.11 compliance:
    Every response must route through holistic_bundle (MSR+UCN+CDLM+CGM+RM)
    before producing a domain-specific answer. A response lacking this routing
    is a procedural violation. Detected by presence of holistic_bundle-related
    signal terms in the actual_response.

NO LEAKAGE constraint:
    life_events feed calibration only — never prediction generation.
    This module enforces the constraint via the _leakage_check() guard.

Contract (BRAHMA MI-5-6):
    - source_citation non-null on all rows
    - provenance_envelope on every tool response
    - 10 golden pairs seeded (ON CONFLICT DO NOTHING — idempotent)
    - b11_compliance checks for holistic_bundle usage in response
    - layer_coverage and grounding_score are float in [0.0, 1.0]
    - Tests: range assertions (not exact floats), tool smoke

Migration: brahma_mimamsa_answer_quality.sql (IF NOT EXISTS)

Native:   Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
          chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0

Authors:  Silpī (MI-5-6 session)
Version:  1.0 — 2026-06-04
BRAHMA-MI-5-6
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import psycopg
import psycopg.rows
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = os.environ.get(
    "NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0"
)

SOURCE_CITATION = "Brahma QA golden set v1.0"

# 6 Brahma layers (L0–L5)
BRAHMA_LAYERS = [
    "L0",   # Brahmagyan — meta / instrument identity
    "L1",   # Gaṇita — astronomical facts
    "L2",   # Bodha — holistic synthesis signals
    "L3",   # Kāla — temporal / dasha engines
    "L4",   # Phala — calibrated predictions
    "L5",   # Mīmāṃsā — answer quality (this layer)
]

TOTAL_LAYERS = len(BRAHMA_LAYERS)  # 6

# Terms that indicate B.11-compliant holistic_bundle routing.
# A B.11-compliant response cites at least one of these.
B11_HOLISTIC_TERMS = [
    "holistic_bundle",
    "MSR",
    "UCN",
    "CDLM",
    "CGM",
    "RM",
    "Whole-Chart-Read",
    "holistic synthesis",
    "holistic bundle",
    "SIG.",         # MSR signal reference pattern
    "CVG.",         # Convergence reference pattern
    "signal_state",
    "multi_school",
]

# Layer presence indicators in responses
LAYER_INDICATORS: dict[str, list[str]] = {
    "L0": [
        "Brahma", "instrument", "layer", "brahmagyan", "meta", "B.11",
        "Whole-Chart-Read", "architecture", "six layer",
    ],
    "L1": [
        "FORENSIC", "lagna", "ascendant", "chart", "graha", "planet",
        "nakshatra", "rashi", "house", "degree", "longitude",
        "ephemeris", "ganita", "Gaṇita", "positions",
    ],
    "L2": [
        "MSR", "UCN", "CDLM", "CGM", "RM", "signal", "SIG.", "CVG.",
        "holistic", "bodha", "Bodha", "synthesis",
        "convergence", "pattern", "divergence",
    ],
    "L3": [
        "dasha", "Dasha", "Mahadasha", "Antardasha", "transit",
        "kala", "Kāla", "timeline", "temporal", "Sade Sati",
        "DSH.V", "vimshottari", "Vimshottari",
    ],
    "L4": [
        "prediction", "anchor", "falsifier", "phala", "Phala",
        "confidence", "calibrat", "window", "2026", "2027",
        "forecast", "anchor_id",
    ],
    "L5": [
        "mimamsa", "Mīmāṃsā", "quality", "eval", "grounding",
        "layer_coverage", "b11_compliance", "acharya-grade",
        "answer quality", "evaluation",
    ],
}

# Life-event leakage guard: terms that must not feed prediction generation
_LEAKAGE_SENTINEL_TERMS = [
    "life_events",
    "lel_events",
    "LEL",
    "life event log",
    "event log",
]


# ── DB URL ────────────────────────────────────────────────────────────────────

def _get_db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        val = os.environ.get(key, "")
        if val:
            return val
    raise RuntimeError(
        "No database URL configured. Set DATABASE_URL, DIRECT_DATABASE_URL, or POSTGRES_URL."
    )


# ── Core evaluation logic ─────────────────────────────────────────────────────

def _check_b11_compliance(actual_response: str) -> bool:
    """
    Determine whether a response demonstrates B.11 Whole-Chart-Read compliance.

    B.11: Every query must route through L2.5 Holistic Synthesis first
    (MSR + UCN + CDLM + CGM + RM), surface cross-domain signals via the
    Cross-Domain Linkage Matrix, then produce its domain-specific answer.

    Detection: presence of at least one holistic_bundle-related term.

    Args:
        actual_response: The response text to check.

    Returns:
        True if the response contains holistic_bundle routing evidence.
    """
    lower = actual_response.lower()
    for term in B11_HOLISTIC_TERMS:
        if term.lower() in lower:
            return True
    return False


def _compute_layer_coverage(actual_response: str) -> float:
    """
    Compute the fraction of 6 Brahma layers (L0–L5) present in the response.

    Each layer is detected by presence of at least one of its indicator terms.
    Result is clamped to [0.0, 1.0].

    Args:
        actual_response: The response text to check.

    Returns:
        Float in [0.0, 1.0] — fraction of 6 layers covered.
    """
    if not actual_response.strip():
        return 0.0

    layers_present = 0
    for layer, indicators in LAYER_INDICATORS.items():
        lower = actual_response.lower()
        for indicator in indicators:
            if indicator.lower() in lower:
                layers_present += 1
                break  # Count each layer at most once

    coverage = layers_present / TOTAL_LAYERS
    return max(0.0, min(1.0, coverage))


def _compute_grounding_score(
    actual_response: str,
    expected_domains: list[str],
) -> float:
    """
    Compute the fraction of expected_domains present in actual_response.

    Domain matching is case-insensitive substring match. Each domain that
    appears (in any part) in the actual_response counts as covered.
    Result is clamped to [0.0, 1.0].

    Args:
        actual_response: The response text to check.
        expected_domains: List of domain strings to look for.

    Returns:
        Float in [0.0, 1.0] — fraction of expected_domains found.
        Returns 0.0 if expected_domains is empty.
    """
    if not expected_domains:
        return 0.0
    if not actual_response.strip():
        return 0.0

    lower_response = actual_response.lower()
    matched = 0
    for domain in expected_domains:
        # Strip layer prefix for matching (e.g. "L2.bodha.signals" → check both
        # "L2.bodha.signals" and "signals")
        domain_lower = domain.lower()
        # Try full domain string first
        if domain_lower in lower_response:
            matched += 1
            continue
        # Try just the final segment (e.g. "signals" from "L2.bodha.signals")
        parts = domain.split(".")
        if len(parts) > 1:
            leaf = parts[-1].lower()
            if len(leaf) >= 3 and leaf in lower_response:  # avoid false positives on short terms
                matched += 1

    score = matched / len(expected_domains)
    return max(0.0, min(1.0, score))


def _leakage_check(response_context: str) -> bool:
    """
    Guard: life_events must never feed into prediction generation.

    Returns True if a leakage violation is detected (life-event terms used
    in a prediction-generation context).

    NOTE: This is a heuristic check — true leakage prevention is enforced
    at the architecture level (L1 facts / calibration separation).
    This check detects obvious violations in generated text.

    Args:
        response_context: Text to check for leakage patterns.

    Returns:
        True if leakage violation detected, False if clean.
    """
    # A violation requires BOTH a leakage sentinel AND a prediction-generation term
    prediction_terms = [
        "predict", "forecast", "anchor", "generate prediction",
        "will occur", "will happen",
    ]
    lower = response_context.lower()
    has_leakage_sentinel = any(t.lower() in lower for t in _LEAKAGE_SENTINEL_TERMS)
    has_prediction_term = any(t.lower() in lower for t in prediction_terms)
    return has_leakage_sentinel and has_prediction_term


# ── Main tool entry-point ─────────────────────────────────────────────────────

def answer_quality_eval(
    question: str,
    actual_response: str,
    expected_domains: Optional[list[str]] = None,
    eval_id: Optional[str] = None,
    persist: bool = False,
) -> dict[str, Any]:
    """
    Main tool entry-point: answer_quality_eval(question, actual_response)

    Evaluates the quality of an actual_response against the Brahma L5 Mīmāṃsā
    quality standards. Distinct from prediction calibration (phala.anchors).

    Evaluation dimensions:
        b11_compliance:  response routes through holistic_bundle before answering.
        layer_coverage:  fraction of 6 layers (L0–L5) touched.
        grounding_score: fraction of expected_domains present in response.

    If `persist=True`, persists the evaluation result to mimamsa_qa_eval (DB required).
    If `persist=False` (default), returns the result without a DB write.

    If `eval_id` is provided and `persist=True`, the result is written back
    to that specific golden pair row (updating actual_response + scores).

    Args:
        question:         The question being evaluated.
        actual_response:  The response text to evaluate.
        expected_domains: Optional list of domain strings the response should cover.
                          If None, grounding_score is computed as 0.0 (no domains to check).
        eval_id:          Optional UUID of an existing mimamsa_qa_eval row to update.
        persist:          If True, persist result to DB. Default False.

    Returns:
        {
            "ok": True,
            "question": str,
            "b11_compliance": bool,
            "layer_coverage": float,   # [0.0, 1.0]
            "grounding_score": float,  # [0.0, 1.0]
            "leakage_detected": bool,
            "provenance_envelope": {
                "source": "mimamsa.answer_quality",
                "asset": "MI-5-6",
                "source_citation": "Brahma QA golden set v1.0",
                "b11_compliance": bool,
                "layer_coverage": float,
                "grounding_score": float,
                "layers_evaluated": 6,
                "b11_holistic_terms_checked": list[str],
                "leakage_detected": bool,
                "evaluated_at": str (ISO),
                "l1_ground_truth": "FORENSIC v8.0",
                "no_leakage_constraint": "life_events feed calibration only",
                "persisted": bool,
                "eval_id": str | None,
            }
        }

    Raises:
        ValueError: If question or actual_response is empty.
        RuntimeError: If persist=True and DATABASE_URL not configured.
    """
    if not question.strip():
        raise ValueError("question must not be empty")
    if not actual_response.strip():
        raise ValueError("actual_response must not be empty")

    effective_domains = expected_domains or []

    # Core evaluations
    b11_compliance = _check_b11_compliance(actual_response)
    layer_coverage = _compute_layer_coverage(actual_response)
    grounding_score = _compute_grounding_score(actual_response, effective_domains)
    leakage_detected = _leakage_check(actual_response)

    evaluated_at = datetime.now(tz=timezone.utc).isoformat()

    # Persist if requested
    persisted_eval_id: Optional[str] = eval_id
    if persist:
        persisted_eval_id = _persist_eval(
            question=question,
            actual_response=actual_response,
            expected_domains=effective_domains,
            b11_compliance=b11_compliance,
            layer_coverage=layer_coverage,
            grounding_score=grounding_score,
            evaluated_at=evaluated_at,
            eval_id=eval_id,
        )

    provenance_envelope = {
        "source": "mimamsa.answer_quality",
        "asset": "MI-5-6",
        "source_citation": SOURCE_CITATION,
        "b11_compliance": b11_compliance,
        "layer_coverage": layer_coverage,
        "grounding_score": grounding_score,
        "layers_evaluated": TOTAL_LAYERS,
        "b11_holistic_terms_checked": B11_HOLISTIC_TERMS,
        "leakage_detected": leakage_detected,
        "evaluated_at": evaluated_at,
        "l1_ground_truth": "FORENSIC v8.0; MSR v5.0; LEL v1.7 (calibration only)",
        "no_leakage_constraint": "life_events feed calibration only — never prediction generation",
        "persisted": persist and persisted_eval_id is not None,
        "eval_id": persisted_eval_id,
    }

    return {
        "ok": True,
        "question": question,
        "b11_compliance": b11_compliance,
        "layer_coverage": layer_coverage,
        "grounding_score": grounding_score,
        "leakage_detected": leakage_detected,
        "provenance_envelope": provenance_envelope,
    }


def _persist_eval(
    question: str,
    actual_response: str,
    expected_domains: list[str],
    b11_compliance: bool,
    layer_coverage: float,
    grounding_score: float,
    evaluated_at: str,
    eval_id: Optional[str] = None,
) -> str:
    """
    Persist an evaluation result to mimamsa_qa_eval.

    If eval_id is provided and the row exists, updates actual_response + scores.
    Otherwise inserts a new row.

    Returns:
        eval_id (UUID string) of the persisted row.

    Raises:
        RuntimeError: DATABASE_URL not configured.
    """
    db_url = _get_db_url()

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            if eval_id:
                # Update existing golden pair
                cur.execute(
                    """
                    UPDATE public.mimamsa_qa_eval
                    SET actual_response = %s,
                        b11_compliance  = %s,
                        layer_coverage  = %s,
                        grounding_score = %s,
                        evaluated_at    = %s,
                        updated_at      = NOW()
                    WHERE eval_id = %s::UUID
                    RETURNING eval_id::TEXT
                    """,
                    [
                        actual_response,
                        b11_compliance,
                        layer_coverage,
                        grounding_score,
                        evaluated_at,
                        eval_id,
                    ],
                )
                row = cur.fetchone()
                result_id = row["eval_id"] if row else eval_id
            else:
                # Insert new evaluation
                cur.execute(
                    """
                    INSERT INTO public.mimamsa_qa_eval
                        (question, expected_domains, actual_response,
                         b11_compliance, layer_coverage, grounding_score,
                         evaluated_at, source_citation)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING eval_id::TEXT
                    """,
                    [
                        question,
                        expected_domains,
                        actual_response,
                        b11_compliance,
                        layer_coverage,
                        grounding_score,
                        evaluated_at,
                        SOURCE_CITATION,
                    ],
                )
                row = cur.fetchone()
                result_id = row["eval_id"] if row else None
        conn.commit()

    logger.info(
        "mimamsa_qa_eval persisted eval_id=%s b11=%s layer_coverage=%.3f grounding=%.3f",
        result_id, b11_compliance, layer_coverage, grounding_score,
    )
    return result_id


# ── Golden pair management ────────────────────────────────────────────────────

def seed_golden_pairs() -> dict[str, Any]:
    """
    Trigger the golden pair seed function in the DB.

    Calls seed_mimamsa_golden_pairs() — inserts 10 golden Q&A pairs (idempotent).

    Returns:
        {"ok": True, "rows_inserted": int, "source_citation": str}

    Raises:
        RuntimeError: DATABASE_URL not configured.
    """
    db_url = _get_db_url()
    sql = "SELECT seed_mimamsa_golden_pairs() AS rows_inserted"

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchone()
            rows_inserted = result["rows_inserted"] if result else 0
        conn.commit()

    logger.info("seed_mimamsa_golden_pairs rows_inserted=%d", rows_inserted)
    return {
        "ok": True,
        "rows_inserted": rows_inserted,
        "source_citation": SOURCE_CITATION,
    }


def list_golden_pairs(
    b11_compliant_only: bool = False,
    evaluated_only: bool = False,
) -> dict[str, Any]:
    """
    List all golden Q&A pairs from mimamsa_qa_eval.

    Args:
        b11_compliant_only: If True, return only pairs where b11_compliance=TRUE.
        evaluated_only:     If True, return only pairs that have been evaluated
                            (actual_response is not NULL).

    Returns:
        {
            "ok": True,
            "pairs": list[dict],
            "count": int,
            "source_citation": str,
            "provenance_envelope": {...}
        }

    Raises:
        RuntimeError: DATABASE_URL not configured.
    """
    conditions = []
    params: list[Any] = []

    if b11_compliant_only:
        conditions.append("b11_compliance = TRUE")
    if evaluated_only:
        conditions.append("actual_response IS NOT NULL")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""
        SELECT
            eval_id::TEXT, question, expected_domains, actual_response,
            b11_compliance, layer_coverage, grounding_score,
            evaluated_at, source_citation, created_at
        FROM public.mimamsa_qa_eval
        {where}
        ORDER BY created_at ASC
    """

    db_url = _get_db_url()
    pairs: list[dict[str, Any]] = []

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            for row in cur.fetchall():
                normalised: dict[str, Any] = {}
                for k, v in row.items():
                    if isinstance(v, datetime):
                        normalised[k] = v.isoformat()
                    else:
                        normalised[k] = v
                pairs.append(normalised)

    queried_at = datetime.now(tz=timezone.utc).isoformat()

    return {
        "ok": True,
        "pairs": pairs,
        "count": len(pairs),
        "source_citation": SOURCE_CITATION,
        "provenance_envelope": {
            "source": "mimamsa.answer_quality",
            "asset": "MI-5-6",
            "source_citation": SOURCE_CITATION,
            "filters": {
                "b11_compliant_only": b11_compliant_only,
                "evaluated_only": evaluated_only,
            },
            "queried_at": queried_at,
        },
    }


# ── Acceptance gate ───────────────────────────────────────────────────────────

def run_acceptance_gate() -> dict[str, Any]:
    """
    MI-5-6 acceptance gate.

    Gate criteria:
      AC1 — 10 golden pairs seeded (source_citation = 'Brahma QA golden set v1.0').
      AC2 — All seeded pairs have non-empty source_citation (B.3 mandate).
      AC3 — All seeded pairs have b11_compliance = TRUE (B.11 mandate).
      AC4 — answer_quality_eval tool smoke: returns b11_compliance, layer_coverage,
             grounding_score all present and in range.
      AC5 — Seed is idempotent (second call inserts 0 rows).
      AC6 — layer_coverage and grounding_score are in [0.0, 1.0].

    Returns:
        {"gate_passed": bool, "checks": list[dict]}
    """
    checks: list[dict[str, Any]] = []

    # AC1: 10 golden pairs seeded
    try:
        result = list_golden_pairs()
        pairs = result["pairs"]
        golden = [p for p in pairs if p.get("source_citation") == SOURCE_CITATION]
        checks.append({
            "id": "AC1",
            "desc": "10 golden pairs seeded (source_citation = 'Brahma QA golden set v1.0')",
            "passed": len(golden) >= 10,
            "value": len(golden),
        })
    except Exception as exc:
        checks.append({
            "id": "AC1",
            "desc": "golden pairs count >= 10",
            "passed": False,
            "error": str(exc),
        })
        golden = []

    # AC2: All source_citations non-empty
    try:
        missing_citations = [p["eval_id"] for p in golden if not p.get("source_citation")]
        checks.append({
            "id": "AC2",
            "desc": "All golden pairs have non-empty source_citation (B.3 mandate)",
            "passed": len(missing_citations) == 0,
            "value": f"{len(golden) - len(missing_citations)}/{len(golden)} have citations",
            "missing": missing_citations,
        })
    except Exception as exc:
        checks.append({"id": "AC2", "desc": "source_citation completeness", "passed": False, "error": str(exc)})

    # AC3: All b11_compliance = TRUE
    try:
        non_b11 = [p["eval_id"] for p in golden if p.get("b11_compliance") is not True]
        checks.append({
            "id": "AC3",
            "desc": "All golden pairs have b11_compliance = TRUE (B.11 mandate)",
            "passed": len(non_b11) == 0,
            "value": f"{len(golden) - len(non_b11)}/{len(golden)} b11_compliant",
            "non_compliant": non_b11,
        })
    except Exception as exc:
        checks.append({"id": "AC3", "desc": "b11_compliance completeness", "passed": False, "error": str(exc)})

    # AC4: Tool smoke — answer_quality_eval returns all required fields in range
    try:
        smoke_question = "What is the dominant career signal for this native?"
        smoke_response = (
            "The dominant career signal is Mercury (SIG.09) with 8-system convergence. "
            "Routing through holistic_bundle first: MSR SIG.14 (Sun 10H career-density), "
            "UCN and CDLM confirm the pattern. FORENSIC v8.0 DSH.V.023 Mercury MD "
            "is active. Layer L1 chart positions, L2 Bodha signals, L3 Kāla dasha, "
            "L4 Phala predictions for 2026 career_consolidation, L5 Mīmāṃsā quality."
        )
        eval_result = answer_quality_eval(
            question=smoke_question,
            actual_response=smoke_response,
            expected_domains=["career", "L2.bodha.signals", "L1.ganita.positions"],
        )
        b11_ok = isinstance(eval_result.get("b11_compliance"), bool)
        lc_ok = isinstance(eval_result.get("layer_coverage"), float) and \
                0.0 <= eval_result["layer_coverage"] <= 1.0
        gs_ok = isinstance(eval_result.get("grounding_score"), float) and \
                0.0 <= eval_result["grounding_score"] <= 1.0
        prov_ok = "provenance_envelope" in eval_result
        checks.append({
            "id": "AC4",
            "desc": "answer_quality_eval tool smoke: returns b11_compliance, layer_coverage, grounding_score in range",
            "passed": b11_ok and lc_ok and gs_ok and prov_ok,
            "value": {
                "b11_compliance": eval_result.get("b11_compliance"),
                "layer_coverage": eval_result.get("layer_coverage"),
                "grounding_score": eval_result.get("grounding_score"),
                "has_provenance_envelope": prov_ok,
            },
        })
    except Exception as exc:
        checks.append({"id": "AC4", "desc": "tool smoke", "passed": False, "error": str(exc)})

    # AC5: Seed idempotency
    try:
        seed_result_1 = seed_golden_pairs()
        seed_result_2 = seed_golden_pairs()
        idempotent = seed_result_2["rows_inserted"] == 0
        checks.append({
            "id": "AC5",
            "desc": "seed_golden_pairs is idempotent (2nd call inserts 0 rows)",
            "passed": idempotent,
            "value": {
                "first_call_inserted": seed_result_1["rows_inserted"],
                "second_call_inserted": seed_result_2["rows_inserted"],
            },
        })
    except Exception as exc:
        checks.append({"id": "AC5", "desc": "seed idempotency", "passed": False, "error": str(exc)})

    # AC6: layer_coverage and grounding_score in [0.0, 1.0] for smoke response
    try:
        test_cases = [
            ("", False, 0.0, 0.0),   # Empty response → 0.0 coverage
            ("MSR SIG.09 holistic_bundle FORENSIC DSH.V.023 dasha Phala Mīmāṃsā L5", True, None, None),
        ]
        all_in_range = True
        for resp, _expected_b11, _expected_lc, _expected_gs in test_cases:
            if not resp:
                lc = _compute_layer_coverage(resp)
                gs = _compute_grounding_score(resp, [])
            else:
                lc = _compute_layer_coverage(resp)
                gs = _compute_grounding_score(resp, ["MSR", "FORENSIC"])
            if not (0.0 <= lc <= 1.0) or not (0.0 <= gs <= 1.0):
                all_in_range = False
                break
        checks.append({
            "id": "AC6",
            "desc": "layer_coverage and grounding_score always in [0.0, 1.0]",
            "passed": all_in_range,
        })
    except Exception as exc:
        checks.append({"id": "AC6", "desc": "range assertions", "passed": False, "error": str(exc)})

    gate_passed = all(c["passed"] for c in checks)
    if gate_passed:
        logger.info("MI-5-6 acceptance gate PASSED")
    else:
        failed = [c["id"] for c in checks if not c["passed"]]
        logger.error("MI-5-6 acceptance gate FAILED — %s", failed)

    return {"gate_passed": gate_passed, "checks": checks}


# ── FastAPI request/response models ───────────────────────────────────────────

class AnswerQualityRequest(BaseModel):
    question: str = Field(..., description="The question being evaluated")
    actual_response: str = Field(..., description="The response text to evaluate")
    expected_domains: Optional[list[str]] = Field(
        None,
        description="Optional list of domain strings the response should cover"
    )
    eval_id: Optional[str] = Field(
        None,
        description="Optional UUID of an existing mimamsa_qa_eval row to update"
    )
    persist: bool = Field(
        False,
        description="If True, persist evaluation result to DB"
    )


class ListGoldenPairsRequest(BaseModel):
    b11_compliant_only: bool = Field(False, description="Return only B.11-compliant pairs")
    evaluated_only: bool = Field(False, description="Return only pairs with actual_response")


class SeedRequest(BaseModel):
    pass  # No parameters needed for seeding


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

@router.post("/mimamsa/answer_quality_eval")
def api_answer_quality_eval(req: AnswerQualityRequest) -> dict[str, Any]:
    """
    MI-5-6 answer_quality_eval tool.

    Evaluates the quality of an actual_response against Brahma L5 Mīmāṃsā standards.
    Returns b11_compliance, layer_coverage [0,1], grounding_score [0,1],
    and a provenance_envelope on every response.

    B.11 compliance: response must route through holistic_bundle first.
    NO LEAKAGE: life_events feed calibration only, never prediction generation.
    """
    try:
        return answer_quality_eval(
            question=req.question,
            actual_response=req.actual_response,
            expected_domains=req.expected_domains,
            eval_id=req.eval_id,
            persist=req.persist,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/mimamsa/seed_golden_pairs")
def api_seed_golden_pairs() -> dict[str, Any]:
    """
    Seed the 10 golden Q&A pairs for mimamsa.answer_quality eval.

    Idempotent — ON CONFLICT DO NOTHING.
    Source citation: "Brahma QA golden set v1.0"
    Covers all 6 Brahma layers (L0–L5).
    """
    try:
        return seed_golden_pairs()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/mimamsa/list_golden_pairs")
def api_list_golden_pairs(req: ListGoldenPairsRequest) -> dict[str, Any]:
    """
    List golden Q&A pairs from mimamsa_qa_eval.

    Optional filters: b11_compliant_only, evaluated_only.
    """
    try:
        return list_golden_pairs(
            b11_compliant_only=req.b11_compliant_only,
            evaluated_only=req.evaluated_only,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/mimamsa/acceptance_gate")
def api_acceptance_gate() -> dict[str, Any]:
    """
    MI-5-6 acceptance gate.

    AC1: 10 golden pairs seeded.
    AC2: All pairs have non-empty source_citation (B.3 mandate).
    AC3: All pairs have b11_compliance = TRUE (B.11 mandate).
    AC4: Tool smoke — answer_quality_eval returns all fields in range.
    AC5: seed_golden_pairs is idempotent.
    AC6: layer_coverage and grounding_score always in [0.0, 1.0].
    """
    try:
        return run_acceptance_gate()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
