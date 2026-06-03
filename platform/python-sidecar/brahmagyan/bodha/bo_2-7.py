"""
bo_2-7.py — BO-2-7: bodha.embeddings — signal vector embeddings in pgvector.

Layer:  L2 Bodha (Chart Intelligence)
Asset:  bodha.embeddings
Unit:   BO-2-7
Table:  bodha_signal_embeddings (signal_id, embedding vector(768), model_name, source_citation)
Model:  text-multilingual-embedding-002 (Vertex AI, 768-dim) — same model as rag/embed.py (C4 spike)
Index:  HNSW on embedding column (vector_cosine_ops, m=16, ef_construction=64)
Feed:   corpus.search vector-search path

Embed text = "{domain} | {valence} | {claim_text[:400]}" per signal row in msr_signals.
One embedding row per signal_id. Idempotent: existing embeddings are skipped unless
--force is passed.

Acceptance gates:
  - embedding present for >= 5 signals
  - cosine self-search: embed(signal_description) top-1 returns the same signal_id
  - HNSW index present on bodha_signal_embeddings

Dependencies:
  - bodha.signals (msr_signals table populated)
  - bodha.graph   (cgm tables populated)
  - GCP Application Default Credentials or SERVICE_ACCOUNT_JSON env var
  - DATABASE_URL  (psycopg3 connection string)
  - GCP_PROJECT   (Vertex AI project)
  - VERTEX_AI_LOCATION (defaults to asia-south1)

Usage:
  python bo_2-7.py [--force] [--limit N] [--self-test]
    --force       re-embed signals that already have embeddings
    --limit N     only embed the first N signals (for smoke tests)
    --self-test   run acceptance gates and exit 0 on pass / 1 on fail
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any

import numpy as np
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────────

EMBED_MODEL = "text-multilingual-embedding-002"
EMBED_DIM = 768
BATCH_SIZE = 10          # conservative; Vertex AI limit is 20k tokens/request
TARGET_TABLE = "bodha_signal_embeddings"
SOURCE_TABLE = "msr_signals"
SELF_TEST_MIN_SIGNALS = 5

# ── Environment ──────────────────────────────────────────────────────────────────


def _load_env() -> None:
    load_dotenv(override=False)


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "[STOP] DATABASE_URL not set. "
            "Set DATABASE_URL=postgresql://... (psycopg3 format) before running."
        )
    return url


# ── Vertex AI helpers ─────────────────────────────────────────────────────────────


def _init_vertexai() -> None:
    import vertexai  # type: ignore[import]

    project = os.environ.get("GCP_PROJECT", "")
    location = os.environ.get("VERTEX_AI_LOCATION", "asia-south1")
    vertexai.init(project=project, location=location)
    logger.info("Vertex AI initialised: project=%r location=%r", project, location)


def _embed_batch(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    Embed a batch of texts via Vertex AI text-multilingual-embedding-002.
    Returns list of 768-dim float vectors. Any API error propagates to caller.
    """
    from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel  # type: ignore[import]

    model = TextEmbeddingModel.from_pretrained(EMBED_MODEL)
    inputs = [TextEmbeddingInput(t, task_type) for t in texts]
    result = model.get_embeddings(inputs)
    return [list(e.values) for e in result]


# ── Signal text composition ───────────────────────────────────────────────────────


def _signal_text(row: dict[str, Any]) -> str:
    """
    Compose the embedding text for one signal.
    Format: "{domain} | {valence} | {claim_text[:400]}"
    domain and valence are the primary classification axes; claim_text is the
    top assertion. Truncated to 400 chars to stay well within token limits.
    """
    domain = (row.get("domain") or "unknown_domain").strip()
    valence = (row.get("valence") or "neutral").strip()
    claim = (row.get("claim_text") or "").strip()[:400]
    return f"{domain} | {valence} | {claim}"


# ── DB helpers ────────────────────────────────────────────────────────────────────


def _fetch_signals(limit: int | None = None) -> list[dict[str, Any]]:
    """
    Fetch signal rows from msr_signals.
    Columns: signal_id, domain, valence, claim_text, source_citation (if present).
    source_citation may not exist on older schema — handled gracefully.
    """
    import psycopg  # type: ignore[import]

    # Check whether source_citation column exists
    with psycopg.connect(_db_url()) as conn:
        col_check = conn.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'msr_signals' AND column_name = 'source_citation'
            """
        ).fetchone()
        has_source_citation = col_check is not None

        citation_col = ", source_citation" if has_source_citation else ", NULL::text AS source_citation"

        sql = f"""
            SELECT signal_id, domain, valence, claim_text {citation_col}
            FROM msr_signals
            WHERE native_id = 'abhisek'
            ORDER BY signal_id
        """
        if limit:
            sql += f" LIMIT {int(limit)}"

        rows = conn.execute(sql).fetchall()

    result = [
        {
            "signal_id": r[0],
            "domain": r[1],
            "valence": r[2],
            "claim_text": r[3],
            "source_citation": r[4],
        }
        for r in rows
    ]
    logger.info("Fetched %d signals from %s.", len(result), SOURCE_TABLE)
    return result


def _fetch_already_embedded() -> set[str]:
    """Return set of signal_ids already present in bodha_signal_embeddings."""
    import psycopg  # type: ignore[import]

    with psycopg.connect(_db_url()) as conn:
        rows = conn.execute(f"SELECT signal_id FROM {TARGET_TABLE}").fetchall()
    ids = {r[0] for r in rows}
    logger.info("Already embedded: %d signal IDs in %s.", len(ids), TARGET_TABLE)
    return ids


def _upsert_embeddings(rows: list[dict[str, Any]]) -> None:
    """
    Upsert embedding rows into bodha_signal_embeddings.
    Each row: {signal_id, embedding (list[float]), source_citation}.
    ON CONFLICT (signal_id) DO UPDATE — idempotent.
    """
    import psycopg  # type: ignore[import]
    from pgvector.psycopg import register_vector  # type: ignore[import]

    with psycopg.connect(_db_url(), autocommit=True) as conn:
        register_vector(conn)
        for row in rows:
            vec = np.array(row["embedding"], dtype=np.float32)
            conn.execute(
                f"""
                INSERT INTO {TARGET_TABLE} (signal_id, embedding, model_name, source_citation)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (signal_id) DO UPDATE
                  SET embedding       = EXCLUDED.embedding,
                      model_name      = EXCLUDED.model_name,
                      source_citation = EXCLUDED.source_citation,
                      embedded_at     = NOW()
                """,
                (row["signal_id"], vec, EMBED_MODEL, row.get("source_citation")),
            )


# ── HNSW index ────────────────────────────────────────────────────────────────────


def _ensure_hnsw_index() -> bool:
    """Create HNSW index on bodha_signal_embeddings if absent. Returns True if present."""
    import psycopg  # type: ignore[import]
    from pgvector.psycopg import register_vector  # type: ignore[import]

    with psycopg.connect(_db_url(), autocommit=True) as conn:
        register_vector(conn)
        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_bodha_signal_embeddings_hnsw
            ON {TARGET_TABLE}
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
            """
        )
        row = conn.execute(
            f"""
            SELECT indexname FROM pg_indexes
            WHERE tablename = '{TARGET_TABLE}' AND indexname LIKE '%hnsw%'
            """
        ).fetchone()
    exists = row is not None
    logger.info("HNSW index present on %s: %s", TARGET_TABLE, exists)
    return exists


# ── Cosine self-search ────────────────────────────────────────────────────────────


def _cosine_self_search(signal_id: str, query_vec: list[float]) -> str | None:
    """
    Run cosine similarity search for query_vec against bodha_signal_embeddings.
    Returns the top-1 signal_id.
    """
    import psycopg  # type: ignore[import]
    from pgvector.psycopg import register_vector  # type: ignore[import]

    vec = np.array(query_vec, dtype=np.float32)
    with psycopg.connect(_db_url()) as conn:
        register_vector(conn)
        row = conn.execute(
            f"""
            SELECT signal_id
            FROM {TARGET_TABLE}
            ORDER BY embedding <=> %s
            LIMIT 1
            """,
            (vec,),
        ).fetchone()
    return row[0] if row else None


# ── Main embed pipeline ───────────────────────────────────────────────────────────


def embed_signals(force: bool = False, limit: int | None = None) -> dict[str, Any]:
    """
    BO-2-7 main embedding pipeline.

    1. Fetch signal rows from msr_signals.
    2. Skip already-embedded (unless --force).
    3. Compose embedding text: domain | valence | claim_text[:400].
    4. Batch-embed with Vertex AI text-multilingual-embedding-002.
    5. Upsert into bodha_signal_embeddings.
    6. Ensure HNSW index.

    Returns a result dict with counts and status.
    """
    _init_vertexai()

    all_signals = _fetch_signals(limit=limit)
    if not all_signals:
        raise RuntimeError(
            f"[STOP] {SOURCE_TABLE} is empty — bodha.signals (BO-2-1/BO-2-2) must run first."
        )

    already_embedded = set() if force else _fetch_already_embedded()
    to_embed = [s for s in all_signals if s["signal_id"] not in already_embedded]
    logger.info(
        "Signals to embed: %d (total: %d, already done: %d, force=%s)",
        len(to_embed), len(all_signals), len(already_embedded), force,
    )

    newly_embedded = 0
    for batch_start in range(0, len(to_embed), BATCH_SIZE):
        batch = to_embed[batch_start: batch_start + BATCH_SIZE]
        texts = [_signal_text(s) for s in batch]

        try:
            embeddings = _embed_batch(texts, task_type="RETRIEVAL_DOCUMENT")
        except Exception as exc:
            logger.error(
                "Vertex AI error at batch starting %d: %s", batch_start, exc
            )
            raise RuntimeError(
                f"[STOP] Vertex AI error at batch starting {batch_start}: {exc}"
            ) from exc

        rows = [
            {
                "signal_id": s["signal_id"],
                "embedding": emb,
                "source_citation": s.get("source_citation"),
            }
            for s, emb in zip(batch, embeddings)
        ]
        _upsert_embeddings(rows)
        newly_embedded += len(batch)
        logger.info(
            "Embedded batch %d–%d (%d total so far).",
            batch_start, batch_start + len(batch) - 1, newly_embedded,
        )

    hnsw_ok = _ensure_hnsw_index()
    if not hnsw_ok:
        raise RuntimeError(f"[STOP] HNSW index creation failed on {TARGET_TABLE}.")

    total_embedded = len(already_embedded) + newly_embedded
    return {
        "total_signals": len(all_signals),
        "already_embedded_at_start": len(already_embedded),
        "newly_embedded": newly_embedded,
        "total_embedded": total_embedded,
        "hnsw_index_present": hnsw_ok,
        "embedding_model": EMBED_MODEL,
        "embed_dim": EMBED_DIM,
        "table": TARGET_TABLE,
    }


# ── Acceptance gates (self-test) ───────────────────────────────────────────────────


def run_self_test() -> dict[str, Any]:
    """
    Run acceptance gates for BO-2-7:
      AC1: >= SELF_TEST_MIN_SIGNALS embeddings present
      AC2: cosine self-search top-1 returns the same signal_id
      AC3: HNSW index present

    Returns a dict with pass/fail per gate. Raises on hard failures.
    """
    import psycopg  # type: ignore[import]
    from pgvector.psycopg import register_vector  # type: ignore[import]

    # AC1: count check
    with psycopg.connect(_db_url()) as conn:
        row = conn.execute(f"SELECT COUNT(*) FROM {TARGET_TABLE}").fetchone()
    count = int(row[0]) if row else 0
    ac1_pass = count >= SELF_TEST_MIN_SIGNALS

    # AC2: cosine self-search on the first signal
    ac2_pass = False
    ac2_detail: str = "no signals"
    if count > 0:
        with psycopg.connect(_db_url()) as conn:
            register_vector(conn)
            probe_row = conn.execute(
                f"SELECT signal_id, embedding FROM {TARGET_TABLE} LIMIT 1"
            ).fetchone()

        if probe_row:
            probe_id = probe_row[0]
            probe_vec = list(probe_row[1])
            top1 = _cosine_self_search(probe_id, probe_vec)
            ac2_pass = top1 == probe_id
            ac2_detail = f"probe={probe_id!r} top1={top1!r}"

    # AC3: HNSW index
    import psycopg  # type: ignore[import]
    with psycopg.connect(_db_url()) as conn:
        idx_row = conn.execute(
            f"""
            SELECT indexname FROM pg_indexes
            WHERE tablename = '{TARGET_TABLE}' AND indexname LIKE '%hnsw%'
            """
        ).fetchone()
    ac3_pass = idx_row is not None

    result = {
        "ac1_min_embeddings": {"pass": ac1_pass, "count": count, "required": SELF_TEST_MIN_SIGNALS},
        "ac2_cosine_self_search": {"pass": ac2_pass, "detail": ac2_detail},
        "ac3_hnsw_index": {"pass": ac3_pass},
        "overall_pass": ac1_pass and ac2_pass and ac3_pass,
    }
    return result


# ── Vector search helper (for MCP tool / corpus.search path) ──────────────────────


def vector_search_signals(
    query_text: str,
    limit: int = 5,
    domain_filter: str | None = None,
    valence_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Embed query_text and return the top-`limit` most similar signals from
    bodha_signal_embeddings, joined back to msr_signals for full context.

    Optional filters:
      domain_filter  — restrict to msr_signals.domain = domain_filter
      valence_filter — restrict to msr_signals.valence = valence_filter

    Returns list of dicts:
      { signal_id, domain, valence, claim_text, source_citation, similarity }
    """
    import psycopg  # type: ignore[import]
    from pgvector.psycopg import register_vector  # type: ignore[import]

    _init_vertexai()
    vecs = _embed_batch([query_text], task_type="RETRIEVAL_QUERY")
    query_vec = np.array(vecs[0], dtype=np.float32)

    filter_clauses: list[str] = []
    params: list[Any] = [query_vec, query_vec]

    if domain_filter:
        filter_clauses.append("ms.domain = %s")
        params.append(domain_filter)
    if valence_filter:
        filter_clauses.append("ms.valence = %s")
        params.append(valence_filter)

    where_clause = ""
    if filter_clauses:
        where_clause = "AND " + " AND ".join(filter_clauses)

    # Check whether source_citation column exists
    with psycopg.connect(_db_url()) as conn:
        col_check = conn.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'msr_signals' AND column_name = 'source_citation'
            """
        ).fetchone()
        has_source_citation = col_check is not None
        citation_sel = "ms.source_citation" if has_source_citation else "NULL::text AS source_citation"

        register_vector(conn)
        rows = conn.execute(
            f"""
            SELECT
                bse.signal_id,
                ms.domain,
                ms.valence,
                ms.claim_text,
                {citation_sel},
                (1 - (bse.embedding <=> %s))::float AS similarity
            FROM {TARGET_TABLE} bse
            JOIN msr_signals ms ON bse.signal_id = ms.signal_id
            WHERE 1=1 {where_clause}
            ORDER BY bse.embedding <=> %s
            LIMIT %s
            """,
            (*params, limit),
        ).fetchall()

    return [
        {
            "signal_id": r[0],
            "domain": r[1],
            "valence": r[2],
            "claim_text": r[3],
            "source_citation": r[4],
            "similarity": round(float(r[5]), 6),
        }
        for r in rows
    ]


# ── CLI ───────────────────────────────────────────────────────────────────────────


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="BO-2-7: embed msr_signals into bodha_signal_embeddings (pgvector)"
    )
    parser.add_argument("--force", action="store_true", help="Re-embed signals that already have embeddings")
    parser.add_argument("--limit", type=int, default=None, help="Only embed the first N signals")
    parser.add_argument("--self-test", action="store_true", help="Run acceptance gates; exit 0=pass 1=fail")
    args = parser.parse_args()

    _load_env()

    if args.self_test:
        result = run_self_test()
        logger.info("Self-test result: %s", result)
        print(result)
        sys.exit(0 if result["overall_pass"] else 1)

    result = embed_signals(force=args.force, limit=args.limit)
    logger.info("BO-2-7 embed_signals complete: %s", result)
    print(result)


if __name__ == "__main__":
    main()
