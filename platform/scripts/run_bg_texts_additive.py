"""
run_bg_texts_additive.py — one-shot additive ingest of the 2 Nadi texts.

Phase 2 of CLAUDECODE_BRIEF_NADI_CORPUS_EXPANSION_v1_0 (v2.0):
  Runs bg_texts in 'additive' mode: existing 13 texts' 8,193 chunks stay
  untouched; only bhrigu_nandi_nadi + nadi_navamsa_patel are chunked + embedded.

Usage:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
  python -m scripts.run_bg_texts_additive

Requires: DATABASE_URL env var (or .env.local), GCP credentials for Vertex AI.
"""
from __future__ import annotations

import logging
import os
import sys
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Load .env.local if present
_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        logger.error("DATABASE_URL not set — aborting")
        sys.exit(1)

    import psycopg2  # type: ignore[import]
    import psycopg2.extras

    conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = False

    try:
        from pipeline.orchestrator.writers import discover_all, get_writer, ContextSpec

        discover_all()
        WriterClass = get_writer("bg_texts")
        if WriterClass is None:
            logger.error("bg_texts writer not found in registry — aborting")
            sys.exit(1)

        build_id = str(uuid.uuid4())
        ctx = ContextSpec(
            asset_id="bg_texts",
            build_id=build_id,
            db_conn=conn,
            config={"rebuild_mode": "additive"},
            dry_run=False,
        )

        logger.info("=== bg_texts ADDITIVE ingest starting (build_id=%s) ===", build_id)
        writer = WriterClass()
        result = writer.run(ctx)
        conn.commit()

        logger.info("=== bg_texts ADDITIVE ingest COMPLETE ===")
        logger.info("rows_inserted (delta): %d", result.rows_inserted)
        logger.info("duration: %.1fs", result.duration_seconds)
        logger.info("notes: %s", result.notes)

        # ── Post-run integrity report ─────────────────────────────────────────
        with conn.cursor() as cur:
            cur.execute(
                "SELECT text_id, COUNT(*) as n FROM classical_text_chunks "
                "GROUP BY text_id ORDER BY text_id"
            )
            rows = cur.fetchall()

        logger.info("=== Per-text chunk breakdown (all 15 texts) ===")
        total = 0
        nadi_texts = {}
        existing_texts = {}
        for row in rows:
            logger.info("  %-30s  %d", row["text_id"], row["n"])
            total += row["n"]
            if row["text_id"] in ("bhrigu_nandi_nadi", "nadi_navamsa_patel"):
                nadi_texts[row["text_id"]] = row["n"]
            else:
                existing_texts[row["text_id"]] = row["n"]

        logger.info("=== Summary ===")
        logger.info("Total chunks: %d (was 8,193 before additive ingest)", total)
        logger.info("Nadi additions: %s", nadi_texts)
        logger.info("Existing 13-text total: %d (should equal 8,193)", sum(existing_texts.values()))

        # ── Integrity assertions ──────────────────────────────────────────────
        existing_total = sum(existing_texts.values())
        if existing_total != 8193:
            logger.error(
                "INTEGRITY VIOLATION: existing 13-text chunk count = %d (expected 8,193). "
                "Something ran destructively. HALT.",
                existing_total,
            )
            sys.exit(2)
        else:
            logger.info("INTEGRITY OK: 13 existing texts' 8,193 chunks are UNCHANGED ✓")

        if not nadi_texts.get("bhrigu_nandi_nadi"):
            logger.warning("WARN: bhrigu_nandi_nadi has 0 chunks — check GCS download + embedding")
        if not nadi_texts.get("nadi_navamsa_patel"):
            logger.warning("WARN: nadi_navamsa_patel has 0 chunks — check DjVu .txt download + verse-fragment filter")

        # ── Nadi tradition_school tag check ───────────────────────────────────
        with conn.cursor() as cur:
            cur.execute(
                "SELECT text_id, COUNT(*) as n, "
                "COUNT(*) FILTER (WHERE tradition_school LIKE '%nadi%') as nadi_tagged "
                "FROM classical_text_chunks "
                "WHERE text_id IN ('bhrigu_nandi_nadi','nadi_navamsa_patel') "
                "GROUP BY text_id"
            )
            tag_rows = cur.fetchall()
        for r in tag_rows:
            pct = (r["nadi_tagged"] / r["n"] * 100) if r["n"] else 0
            logger.info(
                "tradition_school nadi-tag: %s  %d/%d chunks (%.1f%%)",
                r["text_id"], r["nadi_tagged"], r["n"], pct,
            )
            if r["nadi_tagged"] < r["n"]:
                logger.error(
                    "INTEGRITY VIOLATION: %s has %d chunks NOT tagged nadi. HALT.",
                    r["text_id"], r["n"] - r["nadi_tagged"],
                )
                sys.exit(2)

        # ── Patel 3-chunk sample ──────────────────────────────────────────────
        with conn.cursor() as cur:
            cur.execute(
                "SELECT chunk_id, content_en, tradition_school FROM classical_text_chunks "
                "WHERE text_id = 'nadi_navamsa_patel' ORDER BY chunk_id LIMIT 3"
            )
            patel_sample = cur.fetchall()
        logger.info("=== Patel DjVu sample (3 chunks) ===")
        for s in patel_sample:
            logger.info(
                "  [%s] school=%s\n    %s",
                s["chunk_id"], s["tradition_school"],
                (s["content_en"] or "")[:200].replace("\n", " "),
            )

        logger.info("=== GATE REACHED — review results above, then authorize cascade ===")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
