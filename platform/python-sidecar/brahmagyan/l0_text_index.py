"""
brahmagyan.l0_text_index — BRAHMA WS-2 L0 Brahmagyan: Classical Text Search Index
===================================================================================

Provides hybrid full-text search over the classical Jyotish text corpus.

Primary source: classical_text_chunks (WS-2 L0 schema, content_en column)
Fallback source: rag_chunks (legacy RAG table, content column)

Search strategy (hybrid):
  1. Full-text search via PostgreSQL tsvector + plainto_tsquery
  2. ILIKE substring match (case-insensitive)
  Combined with UNION DISTINCT, ordered by relevance rank.

Volume floor:
  classical_text_chunks >= 50 rows (from brahmagyan.texts WS-2 build)
  OR rag_chunks >= 1 row (legacy corpus)

Acceptance gate:
  - search_classical_texts('Sun exalted') returns >= 1 result from BPHS
  - All rows carry source_citation
  - Result rows have text_id or source field identifying the corpus

BRAHMA-BG-0-7
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

VOLUME_FLOOR = 50  # classical_text_chunks floor (from WS-2 brahmagyan.texts)
SOURCE_CITATION = "BPHS + classical_text_chunks (BRAHMA WS-2 L0)"

# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_conn():
    import os
    import psycopg2  # type: ignore[import]
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(url)


# ── Volume check ──────────────────────────────────────────────────────────────

def check_volume(conn=None, dry_run: bool = False) -> dict[str, Any]:
    """
    Check volume floors for the text search index.

    Returns:
      {
        "asset": "brahmagyan.text_index",
        "classical_text_chunks": {"actual": int, "floor": int, "status": str},
        "rag_chunks": {"actual": int, "available": bool},
        "overall_status": "GREEN" | "AMBER" | "EMPTY",
      }
    """
    if dry_run:
        return {
            "asset": "brahmagyan.text_index",
            "classical_text_chunks": {"actual": 0, "floor": VOLUME_FLOOR, "status": "EMPTY"},
            "rag_chunks": {"actual": 0, "available": False},
            "overall_status": "EMPTY",
        }

    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    try:
        with conn.cursor() as cur:
            # Check classical_text_chunks
            try:
                cur.execute("SELECT COUNT(*) FROM classical_text_chunks")
                chunks_count = cur.fetchone()[0]
            except Exception:
                conn.rollback()
                chunks_count = 0

            # Check rag_chunks
            try:
                cur.execute("SELECT COUNT(*) FROM rag_chunks")
                rag_count = cur.fetchone()[0]
                rag_available = True
            except Exception:
                conn.rollback()
                rag_count = 0
                rag_available = False

        if chunks_count >= VOLUME_FLOOR:
            chunk_status = "GREEN"
        elif chunks_count > 0:
            chunk_status = "AMBER"
        else:
            chunk_status = "EMPTY"

        overall = chunk_status if chunks_count > 0 else (
            "AMBER" if rag_count > 0 else "EMPTY"
        )

        return {
            "asset": "brahmagyan.text_index",
            "classical_text_chunks": {
                "actual": chunks_count,
                "floor": VOLUME_FLOOR,
                "status": chunk_status,
            },
            "rag_chunks": {
                "actual": rag_count,
                "available": rag_available,
            },
            "overall_status": overall,
        }

    finally:
        if close_conn:
            conn.close()


# ── Search ────────────────────────────────────────────────────────────────────

def search_classical_texts(
    query: str,
    conn=None,
    limit: int = 10,
    source_filter: list[str] | None = None,
) -> dict[str, Any]:
    """
    Hybrid full-text search over classical text corpus.

    Searches classical_text_chunks (primary) and rag_chunks (fallback).
    Uses PostgreSQL tsvector + plainto_tsquery AND ILIKE for broad coverage.

    Args:
      query: search string (e.g. 'Sun exalted', 'Saturn career remedy')
      conn: optional psycopg2 connection (created if None)
      limit: max rows returned (default 10)
      source_filter: list of text_ids to restrict search (e.g. ['bphs'])

    Returns:
      {
        "ok": bool,
        "query": str,
        "results": [...],
        "count": int,
        "sources_searched": [...],
        "provenance_envelope": {...},
      }
    """
    close_conn = False
    if conn is None:
        try:
            conn = _get_conn()
            close_conn = True
        except Exception as exc:
            logger.warning("[l0_text_index] DB unavailable: %s", exc)
            return _empty_result(query, error=str(exc))

    try:
        results = []
        sources_searched = []

        # ── Try classical_text_chunks first ───────────────────────────────────
        try:
            with conn.cursor() as cur:
                # Test table exists
                cur.execute(
                    "SELECT 1 FROM classical_text_chunks LIMIT 1"
                )

            results_classical = _search_classical_chunks(
                conn, query, limit=limit, source_filter=source_filter
            )
            results.extend(results_classical)
            sources_searched.append("classical_text_chunks")
        except Exception as exc:
            logger.info(
                "[l0_text_index] classical_text_chunks not available: %s", exc
            )
            conn.rollback()

        # ── Fallback: rag_chunks ───────────────────────────────────────────────
        if not results:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM rag_chunks LIMIT 1")

                results_rag = _search_rag_chunks(
                    conn, query, limit=limit, source_filter=source_filter
                )
                results.extend(results_rag)
                sources_searched.append("rag_chunks")
            except Exception as exc:
                logger.info("[l0_text_index] rag_chunks not available: %s", exc)
                conn.rollback()

        # Deduplicate by content
        seen = set()
        deduped = []
        for r in results[:limit]:
            key = r.get("content_en") or r.get("content") or r.get("chunk_id", "")
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        return {
            "ok": True,
            "query": query,
            "results": deduped,
            "count": len(deduped),
            "sources_searched": sources_searched,
            "provenance_envelope": {
                "source": "brahmagyan.text_index",
                "asset": "BRAHMA-BG-0-7",
                "query": query,
                "sources_searched": sources_searched,
                "limit": limit,
                "source_citation": SOURCE_CITATION,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    finally:
        if close_conn:
            conn.close()


def _search_classical_chunks(
    conn,
    query: str,
    limit: int = 10,
    source_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search the classical_text_chunks table using hybrid FTS + ILIKE."""
    conditions = []
    params: list[Any] = []

    if source_filter:
        conditions.append("c.text_id = ANY(%s)")
        params.append(source_filter)

    where_clause = ("AND " + " AND ".join(conditions)) if conditions else ""

    # FTS + ILIKE query
    search_params = [query, f"%{query}%"] + params + [query, f"%{query}%"] + params + [limit]

    sql = f"""
    SELECT
        c.chunk_id,
        c.text_id,
        c.verse_ref,
        c.chapter,
        c.content_en AS content,
        c.topics,
        c.source_citation,
        ts_rank(
            to_tsvector('english', c.content_en),
            plainto_tsquery('english', %s)
        ) AS rank,
        'fts' AS match_type
    FROM classical_text_chunks c
    WHERE (
        to_tsvector('english', c.content_en) @@ plainto_tsquery('english', %s)
        OR c.content_en ILIKE %s
    )
    {where_clause}

    UNION

    SELECT
        c.chunk_id,
        c.text_id,
        c.verse_ref,
        c.chapter,
        c.content_en AS content,
        c.topics,
        c.source_citation,
        0.0 AS rank,
        'ilike' AS match_type
    FROM classical_text_chunks c
    WHERE (
        c.content_en ILIKE %s
        OR c.verse_ref ILIKE %s
    )
    AND NOT (
        to_tsvector('english', c.content_en) @@ plainto_tsquery('english', %s)
    )
    {where_clause}

    ORDER BY rank DESC, chunk_id
    LIMIT %s
    """

    with conn.cursor() as cur:
        cur.execute(sql, search_params)
        cols = [d[0] for d in cur.description]
        rows = []
        for r in cur.fetchall():
            row = dict(zip(cols, r))
            if isinstance(row.get("topics"), (list, tuple)):
                row["topics"] = list(row["topics"])
            rows.append(row)
    return rows


def _search_rag_chunks(
    conn,
    query: str,
    limit: int = 10,
    source_filter: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Search rag_chunks table (legacy corpus) using hybrid FTS + ILIKE.

    rag_chunks schema (from 001_baseline.sql):
      chunk_id, source_canonical_id, content, content_embedding, source_citation
    """
    conditions = []
    params: list[Any] = []

    if source_filter:
        conditions.append("r.source_canonical_id = ANY(%s)")
        params.append(source_filter)

    where_clause = ("AND " + " AND ".join(conditions)) if conditions else ""

    search_params = [query, f"%{query}%"] + params + [limit]

    sql = f"""
    SELECT
        r.chunk_id,
        r.source_canonical_id AS text_id,
        NULL AS verse_ref,
        NULL AS chapter,
        r.content,
        NULL AS topics,
        COALESCE(r.source_citation, r.source_canonical_id) AS source_citation,
        ts_rank(
            to_tsvector('english', r.content),
            plainto_tsquery('english', %s)
        ) AS rank,
        'rag_fts' AS match_type
    FROM rag_chunks r
    WHERE (
        to_tsvector('english', r.content) @@ plainto_tsquery('english', %s)
        OR r.content ILIKE %s
    )
    {where_clause}
    ORDER BY rank DESC
    LIMIT %s
    """

    with conn.cursor() as cur:
        cur.execute(sql, search_params)
        cols = [d[0] for d in cur.description]
        rows = []
        for r in cur.fetchall():
            row = dict(zip(cols, r))
            rows.append(row)
    return rows


def _empty_result(query: str, error: str = "") -> dict[str, Any]:
    return {
        "ok": False,
        "query": query,
        "results": [],
        "count": 0,
        "sources_searched": [],
        "provenance_envelope": {
            "source": "brahmagyan.text_index",
            "asset": "BRAHMA-BG-0-7",
            "query": query,
            "error": error,
            "source_citation": SOURCE_CITATION,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        },
    }
