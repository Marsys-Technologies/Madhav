"""
brahmagyan.l0_text_embedder — L0FR Stream C: Vertex AI Embedder
===============================================================

Deterministic transformation: same text → same 768-dim vector.
Model: text-multilingual-embedding-002 (Vertex AI)
Cost: ~$0.63 per 10,000 chunks (one-time, deterministic).
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ── Vertex AI embedding ───────────────────────────────────────────────────────

EMBEDDING_MODEL = "text-multilingual-embedding-002"
VERTEX_LOCATION = "asia-south1"
VERTEX_PROJECT = "madhav-astrology"
BATCH_SIZE = 250  # Vertex AI batch limit
RATE_LIMIT_DELAY = 0.1  # seconds between batches


def _get_vertex_client():
    """Initialize Vertex AI client."""
    try:
        from vertexai.language_models import TextEmbeddingModel  # type: ignore
        return TextEmbeddingModel
    except ImportError:
        pass

    try:
        import vertexai  # type: ignore
        vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)
        from vertexai.language_models import TextEmbeddingModel
        return TextEmbeddingModel
    except Exception as exc:
        logger.error("[l0_embedder] Vertex AI not available: %s", exc)
        return None


def embed_texts(texts: list[str]) -> list[Optional[list[float]]]:
    """
    Embed a list of text strings using Vertex AI.
    Returns list of 768-dim vectors (or None on failure).
    Deterministic: same text → same vector.
    """
    if not texts:
        return []

    # Try google-cloud-aiplatform SDK approach
    try:
        import vertexai  # type: ignore
        vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)
        from vertexai.language_models import TextEmbeddingModel
        model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)

        all_embeddings: list[Optional[list[float]]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            # Filter empty strings
            safe_batch = [t[:8192] if t else " " for t in batch]
            try:
                embeddings = model.get_embeddings(safe_batch)
                for emb in embeddings:
                    all_embeddings.append(emb.values)
                logger.debug(
                    "[l0_embedder] Embedded batch %d/%d (%d texts)",
                    i // BATCH_SIZE + 1, (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE, len(batch)
                )
            except Exception as exc:
                logger.warning("[l0_embedder] Batch %d failed: %s", i // BATCH_SIZE, exc)
                all_embeddings.extend([None] * len(batch))

            if i + BATCH_SIZE < len(texts):
                time.sleep(RATE_LIMIT_DELAY)

        return all_embeddings

    except Exception as exc:
        logger.error("[l0_embedder] Vertex AI embedding failed: %s", exc)

    # Fallback: try REST API
    return _embed_via_rest(texts)


def _embed_via_rest(texts: list[str]) -> list[Optional[list[float]]]:
    """Fallback: embed via Vertex AI REST API."""
    import json
    import subprocess

    all_embeddings: list[Optional[list[float]]] = []

    try:
        # Get access token
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            logger.error("[l0_embedder] Could not get access token: %s", result.stderr)
            return [None] * len(texts)
        token = result.stdout.strip()
    except Exception as exc:
        logger.error("[l0_embedder] gcloud auth failed: %s", exc)
        return [None] * len(texts)

    import urllib.request
    endpoint = (
        f"https://{VERTEX_LOCATION}-aiplatform.googleapis.com/v1/projects/"
        f"{VERTEX_PROJECT}/locations/{VERTEX_LOCATION}/publishers/google/"
        f"models/{EMBEDDING_MODEL}:predict"
    )

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        instances = [{"content": t[:8192] if t else " "} for t in batch]
        payload = json.dumps({"instances": instances}).encode("utf-8")

        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                preds = data.get("predictions", [])
                for pred in preds:
                    all_embeddings.append(pred.get("embeddings", {}).get("values"))
                logger.debug(
                    "[l0_embedder] REST batch %d/%d embedded %d texts",
                    i // BATCH_SIZE + 1, (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE, len(batch)
                )
        except Exception as exc:
            logger.warning("[l0_embedder] REST batch %d failed: %s", i // BATCH_SIZE, exc)
            all_embeddings.extend([None] * len(batch))

        if i + BATCH_SIZE < len(texts):
            time.sleep(RATE_LIMIT_DELAY)

    return all_embeddings


# ── DB updater ────────────────────────────────────────────────────────────────

def embed_and_store(conn, text_id: Optional[str] = None, batch_size: int = 100) -> dict:
    """
    Fetch unembedded chunks from DB, embed them, store back.
    If text_id given, only embed that text's chunks.

    Returns {embedded: int, failed: int, skipped: int}.
    """
    results = {"embedded": 0, "failed": 0, "skipped": 0}

    with conn.cursor() as cur:
        if text_id:
            cur.execute(
                "SELECT chunk_id, content_en, content_sa FROM classical_text_chunks "
                "WHERE embedding IS NULL AND text_id = %s ORDER BY chunk_id",
                (text_id,)
            )
        else:
            cur.execute(
                "SELECT chunk_id, content_en, content_sa FROM classical_text_chunks "
                "WHERE embedding IS NULL ORDER BY chunk_id"
            )
        rows = cur.fetchall()

    if not rows:
        logger.info("[l0_embedder] No unembedded chunks for text_id=%s", text_id)
        return results

    logger.info("[l0_embedder] Embedding %d chunks (text_id=%s)", len(rows), text_id)

    for offset in range(0, len(rows), batch_size):
        batch = rows[offset:offset + batch_size]
        chunk_ids = [r[0] for r in batch]
        texts = [
            f"{r[1] or ''} {r[2] or ''}".strip()
            for r in batch
        ]
        texts = [t if t else " " for t in texts]

        vectors = embed_texts(texts)

        with conn.cursor() as cur:
            for chunk_id, vector in zip(chunk_ids, vectors):
                if vector is None:
                    results["failed"] += 1
                    continue
                try:
                    # Convert to pgvector format
                    vec_str = "[" + ",".join(str(x) for x in vector) + "]"
                    cur.execute(
                        "UPDATE classical_text_chunks SET embedding = %s::vector WHERE chunk_id = %s",
                        (vec_str, chunk_id)
                    )
                    results["embedded"] += 1
                except Exception as exc:
                    logger.warning(
                        "[l0_embedder] Failed to store embedding for %s: %s",
                        chunk_id, exc
                    )
                    results["failed"] += 1

        conn.commit()
        logger.info(
            "[l0_embedder] Progress: %d/%d (embedded=%d, failed=%d)",
            min(offset + batch_size, len(rows)), len(rows),
            results["embedded"], results["failed"]
        )

    return results


def check_embedding_coverage(conn, text_id: Optional[str] = None) -> dict:
    """Check what fraction of chunks have embeddings."""
    with conn.cursor() as cur:
        if text_id:
            cur.execute(
                "SELECT COUNT(*), COUNT(embedding) FROM classical_text_chunks WHERE text_id = %s",
                (text_id,)
            )
        else:
            cur.execute(
                "SELECT COUNT(*), COUNT(embedding) FROM classical_text_chunks"
            )
        total, embedded = cur.fetchone()

    return {
        "total": total,
        "embedded": embedded,
        "missing": total - embedded,
        "coverage_pct": round(embedded / max(total, 1) * 100, 1),
        "text_id": text_id or "all",
    }
