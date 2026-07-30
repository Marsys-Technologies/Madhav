"""
routers/sutravali.py — FastAPI router for /api/brahma/sutravali endpoints.

SQL-only (ZERO LLM). Exposes 4 query + 2 resource-backing endpoints
over the sutravali_rules table populated by brahmagyan/l0_sutravali_extractor.py.

Routes:
  POST /api/brahma/sutravali/query_rules
  GET  /api/brahma/sutravali/query_rules_for_planet
  GET  /api/brahma/sutravali/read_rule/{rule_id}
  GET  /api/brahma/sutravali/list_rules_by_text/{text_id}
  GET  /api/brahma/sutravali/by_planet/{planet}      (MCP resource backing)
  GET  /api/brahma/sutravali/by_house/{house_num}    (MCP resource backing)

Table schema (actual columns):
  rule_id, text_id, verse_ref, antecedent_jsonb, predicate_jsonb,
  prediction_jsonb, confidence, extracted_by, extraction_pass_log, created_at

Stream D — L0FR Sutravali Pattern Extraction
"""
import os
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import psycopg

router = APIRouter()

DB_URL = os.environ.get("DATABASE_URL", "")


def get_conn():
    return psycopg.connect(DB_URL)


# ── Request models ─────────────────────────────────────────────────────────────

class QueryRulesRequest(BaseModel):
    antecedent_pattern: Optional[str] = Field(
        None, description="JSON text substring to search in antecedent_jsonb"
    )
    planet: Optional[str] = None
    house: Optional[int] = None  # integer 1-12; converted to ordinal (e.g. 7 -> "7th")
    sign: Optional[str] = None
    limit: int = Field(50, ge=1, le=500)


_ORDINALS = {1:"1st",2:"2nd",3:"3rd",4:"4th",5:"5th",6:"6th",
             7:"7th",8:"8th",9:"9th",10:"10th",11:"11th",12:"12th"}

def _house_str(n: int) -> str:
    """Convert integer house number to ordinal string used in antecedent_jsonb."""
    return _ORDINALS.get(n, f"{n}th")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _row_to_rule(row) -> dict:
    """
    Maps a DB row tuple to a dict.
    SELECT order: rule_id, text_id, verse_ref,
                  antecedent_jsonb, predicate_jsonb, prediction_jsonb,
                  confidence, extracted_by
    """
    return {
        "rule_id": str(row[0]),
        "text_id": row[1],
        "verse_ref": row[2],
        "antecedent": row[3] if isinstance(row[3], dict) else (json.loads(row[3]) if row[3] else None),
        "predicate": row[4] if isinstance(row[4], dict) else (json.loads(row[4]) if row[4] else None),
        "prediction": row[5] if isinstance(row[5], dict) else (json.loads(row[5]) if row[5] else None),
        "confidence": float(row[6]) if row[6] is not None else None,
        "extracted_by": row[7],
    }

_SELECT = """
    SELECT r.rule_id, r.text_id, r.verse_ref,
           r.antecedent_jsonb, r.predicate_jsonb, r.prediction_jsonb,
           r.confidence, r.extracted_by
    FROM sutravali_rules r
"""


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/sutravali/query_rules", response_model=list[dict])
def query_rules(req: QueryRulesRequest):
    """
    Flexible query over sutravali_rules.antecedent_jsonb.
    Supports antecedent_pattern (substring), planet, house, sign filters.
    """
    conditions = []
    params: list = []

    if req.antecedent_pattern:
        conditions.append("r.antecedent_jsonb::text ILIKE %s")
        params.append(f"%{req.antecedent_pattern}%")

    if req.planet:
        conditions.append("r.antecedent_jsonb->>'planet' ILIKE %s")
        params.append(req.planet)

    if req.house is not None:
        conditions.append("r.antecedent_jsonb->>'house' = %s")
        params.append(_house_str(req.house))

    if req.sign:
        conditions.append("r.antecedent_jsonb->>'sign_canon' ILIKE %s")
        params.append(req.sign)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(req.limit)

    sql = f"{_SELECT} {where} ORDER BY r.confidence DESC NULLS LAST LIMIT %s"

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        return [_row_to_rule(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sutravali/query_rules_for_planet", response_model=list[dict])
def query_rules_for_planet(
    planet: str = Query(..., description="Planet name or canonical (e.g. Saturn, SAT)"),
    house: Optional[int] = Query(None, ge=1, le=12),
    limit: int = Query(50, ge=1, le=500),
):
    """
    Query rules for a specific planet, optionally filtered by house placement.
    """
    params: list = [planet, planet]
    house_clause = ""
    if house is not None:
        house_clause = "AND r.antecedent_jsonb->>'house' = %s"
        params.append(_house_str(house))
    params.append(limit)

    sql = f"""
        {_SELECT}
        WHERE r.antecedent_jsonb->>'planet' ILIKE %s
        {house_clause}
        ORDER BY r.confidence DESC NULLS LAST
        LIMIT %s
    """

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        return [_row_to_rule(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sutravali/read_rule/{rule_id}", response_model=dict)
def read_rule(rule_id: str):
    """
    Fetch a single sutravali rule by its UUID rule_id.
    """
    sql = f"{_SELECT} WHERE r.rule_id::text = %s"
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [rule_id])
                row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id!r} not found")
        return _row_to_rule(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sutravali/list_rules_by_text/{text_id}", response_model=list[dict])
def list_rules_by_text(
    text_id: str,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    List all sutravali rules sourced from a given text_id.
    """
    sql = f"""
        {_SELECT}
        WHERE r.text_id = %s
        ORDER BY r.verse_ref NULLS LAST, r.confidence DESC NULLS LAST
        LIMIT %s OFFSET %s
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [text_id, limit, offset])
                rows = cur.fetchall()
        return [_row_to_rule(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Resource dump endpoints (for MCP resources) ───────────────────────────────

@router.get("/sutravali/by_planet/{planet}", response_model=list[dict])
def sutravali_by_planet(planet: str, limit: int = Query(500, ge=1, le=2000)):
    """
    MCP resource backing: all rules for a given planet canonical name.
    Used by marsys://resource/sutravali/all-by-planet/<planet>
    """
    sql = f"""
        {_SELECT}
        WHERE r.antecedent_jsonb->>'planet' ILIKE %s
        ORDER BY r.confidence DESC NULLS LAST
        LIMIT %s
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [planet, limit])
                rows = cur.fetchall()
        return [_row_to_rule(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sutravali/by_house/{house_num}", response_model=list[dict])
def sutravali_by_house(house_num: int, limit: int = Query(500, ge=1, le=2000)):
    """
    MCP resource backing: all rules for a given house number (1-12).
    Used by marsys://resource/sutravali/all-by-house/<n>
    """
    if house_num < 1 or house_num > 12:
        raise HTTPException(status_code=400, detail="house_num must be 1-12")
    sql = f"""
        {_SELECT}
        WHERE r.antecedent_jsonb->>'house' = %s
        ORDER BY r.confidence DESC NULLS LAST
        LIMIT %s
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, [_house_str(house_num), limit])
                rows = cur.fetchall()
        return [_row_to_rule(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
