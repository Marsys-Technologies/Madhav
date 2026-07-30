"""
l0_embed_runner.py — Robust embedding runner for L0FR Stream C Phase 1.
Reconnects per batch to handle Cloud SQL Auth Proxy timeouts.
Idempotent: only embeds chunks with embedding IS NULL.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

DB_URL = os.environ["DATABASE_URL"]
VERTEX_LOCATION = "asia-south1"
VERTEX_PROJECT = "madhav-astrology"
EMBEDDING_MODEL = "text-multilingual-embedding-002"
BATCH_SIZE = 50  # Vertex AI text-multilingual-embedding-002: 20k token limit per batch; ~400 chars/chunk avg → 50 chunks ≈ 20k tokens
RATE_LIMIT_DELAY = 0.2
TEXTS = ["bphs", "phaladeepika", "jataka_parijata"]


def get_conn():
    import psycopg2
    return psycopg2.connect(DB_URL)


def _get_token() -> str:
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        raise RuntimeError(f"gcloud auth failed: {result.stderr}")
    return result.stdout.strip()


def embed_texts_rest(texts: list[str], max_retries: int = 3) -> list[list[float] | None]:
    """Embed via Vertex AI REST — no long-lived connection needed. Retries on failure."""
    endpoint = (
        f"https://{VERTEX_LOCATION}-aiplatform.googleapis.com/v1/projects/"
        f"{VERTEX_PROJECT}/locations/{VERTEX_LOCATION}/publishers/google/"
        f"models/{EMBEDDING_MODEL}:predict"
    )
    instances = [{"content": (t[:8192] if t else " ")} for t in texts]
    payload = json.dumps({"instances": instances}).encode("utf-8")

    for attempt in range(max_retries):
        # Refresh token on every attempt (handles token expiry)
        try:
            token = _get_token()
        except Exception as exc:
            logger.warning("Token refresh failed (attempt %d): %s", attempt + 1, exc)
            time.sleep(2 ** attempt)
            continue

        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                preds = data.get("predictions", [])
                result = []
                for pred in preds:
                    val = pred.get("embeddings", {}).get("values")
                    result.append(val)
                return result
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:300]
            logger.warning("REST embedding HTTP %d (attempt %d): %s", exc.code, attempt + 1, body)
            if exc.code == 400 and "token count" in body:
                # Token limit exceeded — split the batch in half and recurse
                if len(texts) > 1:
                    mid = len(texts) // 2
                    left = embed_texts_rest(texts[:mid], max_retries=max_retries)
                    right = embed_texts_rest(texts[mid:], max_retries=max_retries)
                    return left + right
                # Single chunk too large — truncate to 2000 chars and retry
                truncated = [t[:2000] for t in texts]
                payload = json.dumps({"instances": [{"content": t} for t in truncated]}).encode("utf-8")
                continue
            if exc.code == 400:
                # Other bad request — don't retry
                return [None] * len(texts)
            time.sleep(2 ** attempt)
        except Exception as exc:
            logger.warning("REST embedding failed (attempt %d): %s", attempt + 1, exc)
            time.sleep(2 ** attempt)

    logger.warning("REST embedding exhausted %d retries", max_retries)
    return [None] * len(texts)


def embed_all():
    """Embed all unembedded chunks for all 3 Phase 1 texts. Reconnects per batch."""
    totals = {"embedded": 0, "failed": 0}

    for text_id in TEXTS:
        logger.info("=== Fetching unembedded chunks for %s ===", text_id)

        # Fetch all chunk_ids that need embedding (fresh connection)
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT chunk_id, content_en, content_sa "
                    "FROM classical_text_chunks "
                    "WHERE text_id = %s AND embedding IS NULL "
                    "ORDER BY chapter, verse_start",
                    (text_id,)
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            logger.info("%s: no unembedded chunks, skipping", text_id)
            continue

        logger.info("%s: %d chunks to embed", text_id, len(rows))
        embedded_count = 0
        failed_count = 0

        for offset in range(0, len(rows), BATCH_SIZE):
            batch = rows[offset:offset + BATCH_SIZE]
            chunk_ids = [r[0] for r in batch]
            texts = [
                f"{r[1] or ''} {r[2] or ''}".strip() or " "
                for r in batch
            ]

            vectors = embed_texts_rest(texts)

            # New connection per batch — avoids stale connection issues
            conn = get_conn()
            try:
                with conn.cursor() as cur:
                    for chunk_id, vector in zip(chunk_ids, vectors):
                        if vector is None:
                            failed_count += 1
                            continue
                        vec_str = "[" + ",".join(str(x) for x in vector) + "]"
                        cur.execute(
                            "UPDATE classical_text_chunks "
                            "SET embedding = %s::vector "
                            "WHERE chunk_id = %s",
                            (vec_str, chunk_id)
                        )
                        embedded_count += 1
                conn.commit()
            except Exception as exc:
                logger.warning("DB write failed for batch at offset %d: %s", offset, exc)
                conn.rollback()
                failed_count += len(batch)
            finally:
                conn.close()

            pct = round((offset + len(batch)) / len(rows) * 100, 1)
            logger.info(
                "%s: %d/%d chunks (%.1f%%) — embedded=%d failed=%d",
                text_id, offset + len(batch), len(rows), pct,
                embedded_count, failed_count
            )
            time.sleep(RATE_LIMIT_DELAY)

        totals["embedded"] += embedded_count
        totals["failed"] += failed_count
        logger.info(
            "%s DONE: embedded=%d, failed=%d",
            text_id, embedded_count, failed_count
        )

    # Final coverage check
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT text_id, COUNT(*), COUNT(embedding), COUNT(*)-COUNT(embedding) "
                "FROM classical_text_chunks "
                "WHERE text_id = ANY(%s) "
                "GROUP BY text_id ORDER BY text_id",
                (TEXTS,)
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    logger.info("=== FINAL COVERAGE ===")
    grand_total = 0
    grand_embedded = 0
    for row in rows:
        logger.info(
            "%s: total=%d, embedded=%d, missing=%d",
            row[0], row[1], row[2], row[3]
        )
        grand_total += row[1]
        grand_embedded += row[2]

    logger.info(
        "GRAND TOTAL: %d/%d embedded (%.1f%%)",
        grand_embedded, grand_total,
        round(grand_embedded / max(grand_total, 1) * 100, 1)
    )
    return {
        "embedded": totals["embedded"],
        "failed": totals["failed"],
        "grand_total": grand_total,
        "grand_embedded": grand_embedded,
        "coverage_pct": round(grand_embedded / max(grand_total, 1) * 100, 1),
    }


if __name__ == "__main__":
    result = embed_all()
    print("RESULT:", result)
    sys.exit(0 if result["failed"] == 0 else 1)
