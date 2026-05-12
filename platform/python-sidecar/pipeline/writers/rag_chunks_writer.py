"""
pipeline.writers.rag_chunks_writer — RAGChunksWriter: writes L1/L2.5/L3 chunks to
rag_chunks_staging + rag_embeddings_staging. Does not touch live tables directly.
Phase 14B.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import numpy as np
import psycopg

_KEEPALIVE_KWARGS = {
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 10,
    "keepalives_count": 3,
}

from pipeline.writers.base import IBuildWriter, SwapResult, ValidationResult, WriteResult

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-multilingual-embedding-002"
EMBEDDING_DIM = 768


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return url


class RAGChunksWriter(IBuildWriter):
    """
    Writes Chunk objects + embedding vectors to rag_chunks_staging / rag_embeddings_staging.
    Staging tables are cleared at the start of each build_id run to ensure idempotency.
    """

    def __init__(self) -> None:
        self._db_url = _db_url()

    def write_to_staging(self, rows: list[Any], build_id: str) -> WriteResult:
        """
        Write chunk+embedding pairs to rag_chunks_staging / rag_embeddings_staging.
        rows is list[tuple[chunk, list[float]]] — (chunk, embedding) pairs.
        Each 100-row batch commits independently. On OperationalError, the connection
        is reopened with TCP keepalives and the failed batch is retried up to 3 times.
        """
        from pgvector.psycopg import register_vector

        errors: list[str] = []
        written = 0
        backoffs = [5, 15, 45, 90, 180]

        def _open_conn() -> psycopg.Connection:
            last: Exception | None = None
            for d in [0, 5, 15, 45, 90, 180]:
                if d:
                    logger.warning("db_open_retry delay=%ds prior_error=%s", d, last)
                    time.sleep(d)
                try:
                    c = psycopg.connect(self._db_url, **_KEEPALIVE_KWARGS)
                    register_vector(c)
                    return c
                except (psycopg.OperationalError, psycopg.InterfaceError) as exc:
                    last = exc
            raise RuntimeError(f"DB connect failed after retries: {last}")

        def _write_one_batch(c: psycopg.Connection, b: list[Any]) -> None:
            with c.cursor() as cur:
                for chunk, emb in b:
                    meta = {
                        **chunk.metadata,
                        "citation_valid": chunk.citation_valid,
                        "external_computation_pending": chunk.external_computation_pending,
                        "build_id": build_id,
                    }
                    cur.execute(
                        """
                        INSERT INTO rag_chunks_staging
                          (chunk_id, doc_type, layer, source_file, source_version,
                           content, token_count, is_stale, stale_reason, stale_since, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                          content       = EXCLUDED.content,
                          token_count   = EXCLUDED.token_count,
                          is_stale      = EXCLUDED.is_stale,
                          metadata      = EXCLUDED.metadata
                        """,
                        (
                            chunk.chunk_id,
                            chunk.doc_type,
                            chunk.layer,
                            chunk.source_file,
                            chunk.source_version,
                            chunk.content,
                            chunk.token_count,
                            chunk.is_stale,
                            chunk.stale_reason,
                            chunk.stale_since,
                            json.dumps(meta),
                        ),
                    )
                    vec = np.array(emb, dtype=np.float32)
                    cur.execute(
                        """
                        INSERT INTO rag_embeddings_staging
                          (chunk_id, model, embedding)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (chunk_id, model) DO UPDATE SET
                          embedding = EXCLUDED.embedding
                        """,
                        (chunk.chunk_id, EMBEDDING_MODEL, vec),
                    )
            c.commit()

        conn = _open_conn()
        try:
            for i in range(0, len(rows), 100):
                batch = rows[i : i + 100]
                last_exc: Exception | None = None
                ok = False
                for attempt, delay in enumerate([0] + backoffs):
                    if delay:
                        logger.warning(
                            "db_retry batch=%d attempt=%d delay=%ds prior_error=%s",
                            i, attempt, delay, last_exc,
                        )
                        time.sleep(delay)
                        try:
                            conn.close()
                        except Exception:
                            pass
                        try:
                            conn = _open_conn()
                        except (psycopg.OperationalError, psycopg.InterfaceError) as exc:
                            last_exc = exc
                            continue
                    try:
                        _write_one_batch(conn, batch)
                        ok = True
                        break
                    except (psycopg.OperationalError, psycopg.InterfaceError) as exc:
                        last_exc = exc
                if not ok:
                    errors.append(str(last_exc))
                    raise RuntimeError(
                        f"[STOP] DB write failed at batch {i} after {len(backoffs) + 1} attempts: {last_exc}"
                    ) from last_exc
                written += len(batch)
                logger.info("Wrote staging batch %d–%d (%d total)", i, i + len(batch) - 1, written)
        finally:
            try:
                conn.close()
            except Exception:
                pass

        return WriteResult(chunk_count=written, embedding_count=written, errors=errors)

    def write_chunks(
        self,
        chunks: list[Any],
        embeddings: list[list[float]],
        build_id: str,
    ) -> WriteResult:
        """Convenience wrapper for main.py: zips chunks+embeddings into pairs and calls write_to_staging."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunks ({len(chunks)}) and embeddings ({len(embeddings)}) count mismatch"
            )
        return self.write_to_staging(list(zip(chunks, embeddings)), build_id)

    def validate_staging(self, build_id: str) -> ValidationResult:
        issues: list[str] = []

        with psycopg.connect(self._db_url, **_KEEPALIVE_KWARGS) as conn:
            row = conn.execute("SELECT COUNT(*) FROM rag_chunks_staging").fetchone()
            chunk_count = int(row[0]) if row else 0

            row = conn.execute("SELECT COUNT(*) FROM rag_embeddings_staging").fetchone()
            emb_count = int(row[0]) if row else 0

            # Every chunk must have a corresponding embedding
            row = conn.execute(
                """
                SELECT COUNT(*) FROM rag_chunks_staging rc
                LEFT JOIN rag_embeddings_staging re ON rc.chunk_id = re.chunk_id
                WHERE re.chunk_id IS NULL
                """
            ).fetchone()
            missing_embeddings = int(row[0]) if row else 0

            # Verify all embeddings are 768-dim
            row = conn.execute(
                "SELECT vector_dims(embedding) FROM rag_embeddings_staging LIMIT 1"
            ).fetchone()
            actual_dim = int(row[0]) if row else 0

        if chunk_count == 0:
            issues.append("rag_chunks_staging is empty")
        if missing_embeddings > 0:
            issues.append(f"{missing_embeddings} chunks have no embedding in staging")
        if actual_dim != EMBEDDING_DIM:
            issues.append(f"embedding dim={actual_dim}, expected {EMBEDDING_DIM}")

        valid = len(issues) == 0
        logger.info(
            "Staging validation: valid=%s chunks=%d embeddings=%d issues=%s",
            valid, chunk_count, emb_count, issues,
        )
        return ValidationResult(
            valid=valid,
            chunk_count=chunk_count,
            embedding_count=emb_count,
            issues=issues,
        )

    def swap_to_live(self, build_id: str) -> SwapResult:
        # Safety gate: abort if staging has fewer than 50% of live rows
        with psycopg.connect(self._db_url, **_KEEPALIVE_KWARGS) as conn:
            live_count = int((conn.execute("SELECT COUNT(*) FROM rag_chunks").fetchone() or [0])[0])
            staging_count = int((conn.execute("SELECT COUNT(*) FROM rag_chunks_staging").fetchone() or [0])[0])

        if live_count > 0 and staging_count < (0.5 * live_count):
            msg = (
                f"ABORT: staging has {staging_count} rows but live has {live_count} — "
                "below 50% safety threshold. Swap aborted; live tables untouched."
            )
            logger.error(msg)
            return SwapResult(success=False, promoted_chunk_count=0, message=msg)

        with psycopg.connect(self._db_url, autocommit=False, **_KEEPALIVE_KWARGS) as conn:
            from pgvector.psycopg import register_vector
            register_vector(conn)
            with conn.transaction():
                # Clear FK-dependent tables in dependency order before touching rag_chunks
                conn.execute("DELETE FROM rag_graph_edges")
                conn.execute("DELETE FROM rag_graph_nodes")
                conn.execute("DELETE FROM rag_embeddings")
                conn.execute("DELETE FROM rag_chunks")
                conn.execute("INSERT INTO rag_chunks SELECT * FROM rag_chunks_staging")
                conn.execute("INSERT INTO rag_embeddings SELECT * FROM rag_embeddings_staging")
                conn.execute("TRUNCATE rag_chunks_staging, rag_embeddings_staging")
                conn.execute(
                    "UPDATE build_manifests SET status='live', promoted_at=NOW() WHERE build_id=%s",
                    (build_id,),
                )
                conn.execute(
                    "UPDATE build_manifests SET status='rolled_back' WHERE status='live' AND build_id != %s",
                    (build_id,),
                )

        # Best-effort HNSW reindex post-swap
        try:
            with psycopg.connect(self._db_url, autocommit=True, **_KEEPALIVE_KWARGS) as conn:
                conn.execute(
                    "REINDEX INDEX CONCURRENTLY idx_rag_embeddings_hnsw"
                )
            logger.info("HNSW reindex completed")
        except Exception as exc:
            logger.warning("HNSW reindex skipped (best-effort): %s", exc)

        logger.info("Swap complete: %d chunks promoted to live", staging_count)
        return SwapResult(
            success=True,
            promoted_chunk_count=staging_count,
            message=f"Promoted {staging_count} chunks to live",
        )
