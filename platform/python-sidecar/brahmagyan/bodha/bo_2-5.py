"""
brahmagyan/bodha/bo_2-5.py — Brahma L2 Bodha — bodha.lenses (BO-2-5)

Asset:    bodha.lenses
Tool:     query_signals(chart_id, lens=concordance|contradiction|salience|negative_space, ...)
Tables:   NONE (computed views over bodha_signals + bodha_graph via stored functions)
Contract: BRAHMA_L1_L5_REGISTRY_SEED §C acceptance gate:
          - concordance lens: groups signals by school agreement/disagreement
          - contradiction lens: surfaces signal pairs with contradicting valence
          - negative_space: computes what is NOT signalled (absent expected signals)
          - salience: ranks signals by confidence x reinforcement_count x domain_weight
          - native chart test: >= 1 contradiction-hub (BO-2-5 gate)
Native:   Abhisek Mohanty, 1984-02-05, 10:43 IST Bhubaneswar
          chart_id: 482012f1-710e-4a25-994a-93821f5871aa
          Expected contradiction-hub: career domain (Saturn-Ketu vs. Jupiter)

Layer:    L2 Bodha (depends on BO-2-1 bodha_signals + BO-2-2 bodha_graph)
Depends:  brahma_bo_2-5.sql (stored functions — no new tables)
          bodha_signals table (brahma_bodha_bo21.sql)
          bodha_graph table (brahma_bodha_bo22.sql)

Authors:  Silpī (BO-2-5 session)
Version:  1.0 — 2026-06-03
"""
from __future__ import annotations

import json
import logging
import os
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

VALID_LENSES = frozenset({
    "concordance",
    "contradiction",
    "negative_space",
    "salience",
})

VALID_DOMAINS = frozenset({
    "career", "wealth", "relationships", "health", "spirit",
    "mind", "travel", "parents", "dasha", "nadi_bnn",
    "yogini_tajaka", "house_domain",
})

VALID_VALENCES = frozenset({"benefic", "malefic", "context-dependent", "mixed"})


# ── DB URL ────────────────────────────────────────────────────────────────────

def _get_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not configured")
    return url


# ── Lens query functions ──────────────────────────────────────────────────────

def query_concordance_lens(
    chart_id: str,
    min_conf: float = 0.0,
    domain: Optional[str] = None,
    valence: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Concordance lens: groups signals by domain + valence.

    Returns rows: domain, valence, signal_count, avg_confidence, avg_salience,
    agreement_score, signal_ids[], signal_names[].
    Sorted by domain then agreement_score DESC.
    """
    sql = """
        SELECT domain, valence, signal_count, avg_confidence, avg_salience,
               agreement_score, signal_ids, signal_names
        FROM bodha_concordance_lens(%s, %s)
        WHERE (%s IS NULL OR domain = %s)
          AND (%s IS NULL OR valence = %s)
    """
    params = [chart_id, min_conf, domain, domain, valence, valence]
    return _run_query(sql, params)


def query_contradiction_lens(
    chart_id: str,
    min_conf: float = 0.3,
    domain: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Contradiction lens: surfaces signal pairs with opposing valence in same domain.

    Returns rows: domain, signal_id_a, signal_name_a, valence_a, confidence_a,
    signal_id_b, signal_name_b, valence_b, confidence_b,
    tension_score, graph_edge_id, has_graph_edge.
    Sorted by tension_score DESC.

    Acceptance gate: native chart must have >= 1 row (BO-2-5).
    """
    effective_min_conf = max(min_conf, 0.3)
    sql = """
        SELECT domain, signal_id_a, signal_name_a, valence_a, confidence_a,
               signal_id_b, signal_name_b, valence_b, confidence_b,
               tension_score, graph_edge_id, has_graph_edge
        FROM bodha_contradiction_lens(%s, %s)
        WHERE (%s IS NULL OR domain = %s)
    """
    params = [chart_id, effective_min_conf, domain, domain]
    return _run_query(sql, params)


def query_negative_space(chart_id: str) -> list[dict[str, Any]]:
    """
    Negative space lens: computes what is NOT signalled.

    Returns rows: check_type (domain_absent|domain_weak|graha_absent),
    label, signal_count, max_confidence, interpretation_hint.
    """
    sql = """
        SELECT check_type, label, signal_count, max_confidence, interpretation_hint
        FROM bodha_negative_space(%s)
    """
    return _run_query(sql, [chart_id])


def query_salience_lens(
    chart_id: str,
    min_conf: float = 0.0,
    min_salience: float = 0.0,
    domain: Optional[str] = None,
    valence: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Salience lens: ranks signals by composite_salience.

    composite_salience = confidence x base_salience x (1 + reinforcement_count/10) x domain_weight

    Returns rows: rank, signal_id, signal_name, domain, valence, confidence,
    base_salience, reinforcement_count, domain_weight, composite_salience,
    claim_text, source_citation, grounding_status.
    """
    sql = """
        SELECT rank, signal_id, signal_name, domain, valence, confidence,
               base_salience, reinforcement_count, domain_weight, composite_salience,
               claim_text, source_citation, grounding_status
        FROM bodha_salience_lens(%s, %s, %s, %s)
        WHERE (%s IS NULL OR domain = %s)
          AND (%s IS NULL OR valence = %s)
    """
    params = [chart_id, min_conf, min_salience, limit, domain, domain, valence, valence]
    return _run_query(sql, params)


# ── Core dispatch — query_signals with lens ───────────────────────────────────

def query_signals_with_lens(
    chart_id: str,
    lens: Optional[str] = None,
    domain: Optional[str] = None,
    valence: Optional[str] = None,
    confidence_min: float = 0.0,
    grounding_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Unified query_signals with optional lens parameter.

    lens=None → plain BO-2-1 signal list (ordered by salience DESC, confidence DESC).
    lens=concordance → group by domain+valence agreement.
    lens=contradiction → surface opposing-valence signal pairs.
    lens=negative_space → absent domains/grahas.
    lens=salience → composite ranked list.

    Args:
        chart_id:         Chart UUID.
        lens:             Lens name (None|concordance|contradiction|negative_space|salience).
        domain:           Optional domain filter.
        valence:          Optional valence filter.
        confidence_min:   Minimum confidence threshold.
        grounding_status: Optional grounding status filter (plain mode only).
        limit:            Maximum rows (default 100).
        offset:           Pagination offset (plain mode only).

    Returns:
        dict with keys: ok, chart_id, lens, filters_applied, total_returned, rows.

    Raises:
        ValueError: for invalid lens/domain/valence values.
        RuntimeError: if DATABASE_URL is not set.
    """
    # Validate
    if lens and lens not in VALID_LENSES:
        raise ValueError(f"Unknown lens '{lens}'. Valid: {sorted(VALID_LENSES)}")
    if domain and domain not in VALID_DOMAINS:
        raise ValueError(f"Unknown domain '{domain}'. Valid: {sorted(VALID_DOMAINS)}")
    if valence and valence not in VALID_VALENCES:
        raise ValueError(f"Unknown valence '{valence}'. Valid: {sorted(VALID_VALENCES)}")
    if not (0.0 <= confidence_min <= 1.0):
        raise ValueError(f"confidence_min must be in [0.0, 1.0], got {confidence_min}")
    limit = min(limit, 500)

    # Dispatch
    if lens == "concordance":
        rows = query_concordance_lens(chart_id, confidence_min, domain, valence)
    elif lens == "contradiction":
        rows = query_contradiction_lens(chart_id, confidence_min, domain)
    elif lens == "negative_space":
        rows = query_negative_space(chart_id)
    elif lens == "salience":
        rows = query_salience_lens(chart_id, confidence_min, 0.0, domain, valence, limit)
    else:
        # Plain BO-2-1 style
        rows = _plain_signal_query(
            chart_id, domain, valence, confidence_min, grounding_status, limit, offset
        )

    return {
        "ok": True,
        "chart_id": chart_id,
        "lens": lens,
        "filters_applied": {
            "domain": domain,
            "valence": valence,
            "confidence_min": confidence_min,
            "grounding_status": grounding_status,
            "limit": limit,
            "offset": offset,
        },
        "total_returned": len(rows),
        "rows": rows,
    }


# ── Plain signal query (fallback, no lens) ────────────────────────────────────

def _plain_signal_query(
    chart_id: str,
    domain: Optional[str],
    valence: Optional[str],
    confidence_min: float,
    grounding_status: Optional[str],
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    conditions = ["chart_id = %s"]
    params: list[Any] = [chart_id]

    if domain:
        conditions.append("domain = %s")
        params.append(domain)
    if valence:
        conditions.append("valence = %s")
        params.append(valence)
    if confidence_min > 0.0:
        conditions.append("confidence >= %s")
        params.append(confidence_min)
    if grounding_status:
        conditions.append("grounding_status = %s")
        params.append(grounding_status)

    where = " AND ".join(conditions)
    sql = f"""
        SELECT signal_id, chart_id, domain, signal_type, valence,
               temporal_activation, graha, house, nakshatra,
               confidence, salience, strength_score,
               signal_name, claim_text, classical_source,
               supporting_rules, entities_involved, domains_affected, falsifier,
               is_forward_looking,
               source_l1_fact_ids, source_l0_rule_id, source_citation,
               grounding_status, derivation_ledger, msr_version
        FROM public.bodha_signals
        WHERE {where}
        ORDER BY salience DESC, confidence DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    return _run_query(sql, params)


# ── DB helper ─────────────────────────────────────────────────────────────────

def _run_query(sql: str, params: list[Any]) -> list[dict[str, Any]]:
    """Execute a SELECT query and return rows as list[dict]."""
    db_url = _get_db_url()
    rows: list[dict[str, Any]] = []

    with psycopg.connect(db_url, row_factory=psycopg.rows.dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            for row in cur.fetchall():
                # Normalise psycopg JSONB/array types to Python natives
                normalised: dict[str, Any] = {}
                for k, v in row.items():
                    if isinstance(v, (list, dict)):
                        normalised[k] = v
                    elif isinstance(v, str):
                        # Attempt JSON parse for JSONB columns
                        if v.startswith(("{", "[")):
                            try:
                                normalised[k] = json.loads(v)
                            except json.JSONDecodeError:
                                normalised[k] = v
                        else:
                            normalised[k] = v
                    else:
                        normalised[k] = v
                rows.append(normalised)

    return rows


# ── Acceptance gate ───────────────────────────────────────────────────────────

def run_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    Run the BO-2-5 acceptance gate against the database.

    Gate criteria:
      AC1 — contradiction_lens returns >= 1 pair (native chart has >= 1 contradiction-hub)
      AC2 — salience_lens returns >= 5 rows (signals present and lens computes)
      AC3 — negative_space executes without error (may return 0 rows if coverage complete)
      AC4 — concordance_lens returns >= 1 group
      AC5 — query_signals_with_lens(lens=None) returns >= 1 row (plain mode works)

    Returns dict: passed (bool), checks (list).
    """
    checks: list[dict[str, Any]] = []

    # AC1: Contradiction hub
    try:
        contradictions = query_contradiction_lens(chart_id, min_conf=0.3)
        checks.append({
            "id": "AC1",
            "desc": "contradiction_lens returns >= 1 pair (native chart has >= 1 contradiction-hub)",
            "passed": len(contradictions) >= 1,
            "value": len(contradictions),
        })
    except Exception as exc:
        checks.append({"id": "AC1", "desc": "contradiction_lens", "passed": False, "error": str(exc)})

    # AC2: Salience lens returns >= 5 rows
    try:
        salience_rows = query_salience_lens(chart_id, limit=10)
        checks.append({
            "id": "AC2",
            "desc": "salience_lens returns >= 5 rows",
            "passed": len(salience_rows) >= 5,
            "value": len(salience_rows),
        })
    except Exception as exc:
        checks.append({"id": "AC2", "desc": "salience_lens", "passed": False, "error": str(exc)})

    # AC3: Negative space executes
    try:
        ns_rows = query_negative_space(chart_id)
        checks.append({
            "id": "AC3",
            "desc": "negative_space executes without error",
            "passed": True,
            "value": len(ns_rows),
        })
    except Exception as exc:
        checks.append({"id": "AC3", "desc": "negative_space", "passed": False, "error": str(exc)})

    # AC4: Concordance lens returns >= 1 group
    try:
        concordance_rows = query_concordance_lens(chart_id)
        checks.append({
            "id": "AC4",
            "desc": "concordance_lens returns >= 1 group",
            "passed": len(concordance_rows) >= 1,
            "value": len(concordance_rows),
        })
    except Exception as exc:
        checks.append({"id": "AC4", "desc": "concordance_lens", "passed": False, "error": str(exc)})

    # AC5: Plain mode works
    try:
        plain_result = query_signals_with_lens(chart_id, lens=None, limit=5)
        checks.append({
            "id": "AC5",
            "desc": "plain query_signals_with_lens(lens=None) returns >= 1 row",
            "passed": plain_result["total_returned"] >= 1,
            "value": plain_result["total_returned"],
        })
    except Exception as exc:
        checks.append({"id": "AC5", "desc": "plain mode", "passed": False, "error": str(exc)})

    passed = all(c["passed"] for c in checks)
    if passed:
        logger.info("BO-2-5 acceptance gate PASSED for chart_id=%s", chart_id)
    else:
        failed = [c["id"] for c in checks if not c["passed"]]
        logger.error("BO-2-5 acceptance gate FAILED for chart_id=%s — %s", chart_id, failed)

    return {"chart_id": chart_id, "gate_passed": passed, "checks": checks}


# ── FastAPI request/response models ───────────────────────────────────────────

class QuerySignalsWithLensRequest(BaseModel):
    chart_id: str = Field(..., description="Chart UUID")
    lens: Optional[str] = Field(
        None,
        description=(
            "Lens to apply: concordance | contradiction | negative_space | salience | null (plain list)"
        ),
    )
    domain: Optional[str] = Field(None, description="Filter by domain (concordance/contradiction/salience)")
    valence: Optional[str] = Field(None, description="Filter by valence (concordance/salience)")
    confidence_min: float = Field(0.0, ge=0.0, le=1.0, description="Minimum confidence")
    grounding_status: Optional[str] = Field(None, description="Filter by grounding_status (plain mode only)")
    limit: int = Field(100, ge=1, le=500, description="Maximum rows")
    offset: int = Field(0, ge=0, description="Pagination offset (plain mode only)")


# ── FastAPI endpoints ─────────────────────────────────────────────────────────

@router.post("/query_signals_lens")
def api_query_signals_lens(req: QuerySignalsWithLensRequest) -> dict[str, Any]:
    """
    BO-2-5 query_signals with lens support.

    lens=concordance   → groups signals by domain+valence agreement.
    lens=contradiction → surfaces opposing-valence signal pairs (same domain).
    lens=negative_space→ computes absent domains/grahas.
    lens=salience      → composite ranked list (confidence x salience x reinforcement x domain_weight).
    lens=null          → plain BO-2-1 signal list.
    """
    try:
        return query_signals_with_lens(
            chart_id=req.chart_id,
            lens=req.lens,
            domain=req.domain,
            valence=req.valence,
            confidence_min=req.confidence_min,
            grounding_status=req.grounding_status,
            limit=req.limit,
            offset=req.offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/acceptance_gate_bo25/{chart_id}")
def api_acceptance_gate(chart_id: str) -> dict[str, Any]:
    """
    BO-2-5 acceptance gate.

    Runs AC1-AC5: contradiction-hub present, salience >= 5 rows,
    negative_space executes, concordance >= 1 group, plain mode works.
    """
    try:
        return run_acceptance_gate(chart_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
