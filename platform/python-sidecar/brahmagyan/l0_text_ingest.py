"""
brahmagyan.l0_text_ingest — L0FR Stream C: Text Ingestion Runner
================================================================

Phase 1: BPHS, Phaladeepika, Jataka Parijata
Deterministic-first: download djvu.txt → regex chunk → embed → DB insert.

Usage:
  python -m brahmagyan.l0_text_ingest --phase 1 [--dry-run] [--skip-embed]

Environment:
  DATABASE_URL: PostgreSQL connection string
  GOOGLE_APPLICATION_CREDENTIALS or gcloud auth
"""
from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from brahmagyan.l0_text_chunker import (
    TEXT_META,
    Chunk,
    chunk_text,
    insert_chunks,
    insert_classical_text,
    insert_text_source,
    process_text_file,
)
from brahmagyan.l0_text_embedder import embed_and_store, check_embedding_coverage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── Source configuration ──────────────────────────────────────────────────────

TEXTS_DIR = Path("/tmp/l0fr_texts")
MANUAL_UPLOAD_LOG = Path("/tmp/l0fr_manual_upload_pending.txt")
PARK_LOG = Path("/tmp/l0fr_chunks_parked.txt")

# Phase 1 texts: BPHS, Phaladeepika, Jataka Parijata
PHASE_1_SOURCES = {
    "bphs": {
        "ia_id": "BPHSEnglish",
        "files": [
            ("BPHS%20-%201%20RSanthanam_djvu.txt", "bphs_vol1_djvu.txt"),
            ("BPHS%20-%202%20RSanthanam_djvu.txt", "bphs_vol2_djvu.txt"),
        ],
        "type": "djvu_txt",
    },
    "phaladeepika": {
        "ia_id": "Phaladeepika2ndEd.1950ByVSubrahmanyaSastri",
        "files": [
            ("Phaladeepika%202nd%20Ed.%201950%20by%20V%20Subrahmanya%20Sastri_djvu.txt",
             "phaladeepika_djvu.txt"),
        ],
        "type": "djvu_txt",
    },
    "jataka_parijata": {
        "ia_id": "JatakaParijataVolIOfIIByVSubrahmanyaSastri",
        "files": [
            ("Jataka%20Parijata%20Vol%20I%20of%20II%20by%20V%20Subrahmanya%20Sastri_djvu.txt",
             "jp_vol1_djvu.txt"),
        ],
        "type": "djvu_txt",
        "ia_id_vol2": "JatakaParijataVolIIOfIIByVSubrahmanyaSastri",
        "files_vol2": [
            ("Jataka%20Parijata%20Vol%20II%20of%20II%20by%20V%20Subrahmanya%20Sastri_djvu.txt",
             "jp_vol2_djvu.txt"),
        ],
    },
}


def _download_if_missing(text_id: str, config: dict) -> list[str]:
    """Download source files from Internet Archive if not present. Returns local paths."""
    text_dir = TEXTS_DIR / text_id / "raw"
    text_dir.mkdir(parents=True, exist_ok=True)
    local_paths = []

    def dl_one(ia_id: str, remote_filename: str, local_filename: str) -> str | None:
        local_path = text_dir / local_filename
        if local_path.exists() and local_path.stat().st_size > 1000:
            logger.info("[ingest] Already downloaded: %s", local_path)
            return str(local_path)
        url = f"https://archive.org/download/{ia_id}/{remote_filename}"
        logger.info("[ingest] Downloading %s...", url)
        result = subprocess.run(
            ["curl", "-s", "-L", "-o", str(local_path), url],
            timeout=120
        )
        if result.returncode == 0 and local_path.stat().st_size > 1000:
            logger.info("[ingest] Downloaded: %s (%d bytes)", local_filename, local_path.stat().st_size)
            return str(local_path)
        else:
            logger.warning("[ingest] Download failed for %s", url)
            return None

    # Main files
    for remote_fn, local_fn in config.get("files", []):
        p = dl_one(config["ia_id"], remote_fn, local_fn)
        if p:
            local_paths.append(p)

    # Vol2 files (Jataka Parijata)
    if config.get("ia_id_vol2"):
        for remote_fn, local_fn in config.get("files_vol2", []):
            p = dl_one(config["ia_id_vol2"], remote_fn, local_fn)
            if p:
                local_paths.append(p)

    return local_paths


def _get_db_conn():
    """Get PostgreSQL connection."""
    import psycopg2  # type: ignore
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        # Try .env.local
        env_path = Path(__file__).parent.parent.parent / ".env.local"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip()
                    break
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(db_url)


def run_phase1(dry_run: bool = False, skip_embed: bool = False) -> dict:
    """
    Phase 1: Ingest BPHS, Phaladeepika, Jataka Parijata.
    Returns summary dict.
    """
    logger.info("[ingest] === L0FR Stream C Phase 1 START ===")
    logger.info("[ingest] Texts: BPHS, Phaladeepika, Jataka Parijata")
    logger.info("[ingest] dry_run=%s skip_embed=%s", dry_run, skip_embed)

    summary = {
        "chunks_bphs": 0,
        "chunks_phaladeepika": 0,
        "chunks_jp": 0,
        "parked_total": 0,
        "embedded": False,
    }

    conn = None if dry_run else _get_db_conn()

    try:
        for text_id, config in PHASE_1_SOURCES.items():
            logger.info("[ingest] --- Processing %s ---", text_id)

            # Step 1: Download source files
            local_paths = _download_if_missing(text_id, config)
            if not local_paths:
                logger.warning("[ingest] No source files for %s - SKIP", text_id)
                continue

            # Step 2: Chunk
            good_chunks, good_count, park_count = process_text_file(
                text_id, local_paths, str(PARK_LOG)
            )
            logger.info(
                "[ingest] %s: %d good chunks, %d parked",
                text_id, good_count, park_count
            )

            summary[f"chunks_{text_id.split('_')[0]}"] = good_count
            summary["parked_total"] += park_count

            if not dry_run and good_chunks and conn:
                # Step 3a: Insert classical_texts row (parent of FK in classical_text_chunks)
                insert_classical_text(conn, text_id)

                # Step 3b: Insert text source metadata
                insert_text_source(conn, text_id)

                # Step 4: Insert chunks
                inserted = insert_chunks(conn, good_chunks)
                logger.info("[ingest] %s: inserted %d chunks", text_id, inserted)

        # Step 5: Embed
        if not dry_run and not skip_embed and conn:
            logger.info("[ingest] --- Embedding all Phase 1 chunks ---")
            for text_id in PHASE_1_SOURCES.keys():
                t0 = time.time()
                embed_result = embed_and_store(conn, text_id=text_id)
                elapsed = time.time() - t0
                logger.info(
                    "[ingest] %s embedding: embedded=%d failed=%d (%.1fs)",
                    text_id, embed_result["embedded"], embed_result["failed"], elapsed
                )

            # Coverage check
            cov = check_embedding_coverage(conn)
            summary["embedding_coverage"] = cov
            summary["embedded"] = cov.get("missing", 1) == 0

        # Final DB counts
        if not dry_run and conn:
            import psycopg2.extras
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT text_id, COUNT(*) FROM classical_text_chunks "
                    "WHERE text_id = ANY(%s) GROUP BY text_id",
                    (list(PHASE_1_SOURCES.keys()),)
                )
                counts = {r[0]: r[1] for r in cur.fetchall()}

            summary["chunks_bphs"] = counts.get("bphs", 0)
            summary["chunks_phaladeepika"] = counts.get("phaladeepika", 0)
            summary["chunks_jp"] = counts.get("jataka_parijata", 0)
            summary["chunks_total"] = sum(counts.values())

            # Embedding check
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM classical_text_chunks "
                    "WHERE text_id = ANY(%s) AND embedding IS NULL",
                    (list(PHASE_1_SOURCES.keys()),)
                )
                missing_embed = cur.fetchone()[0]
            summary["missing_embeddings"] = missing_embed

    finally:
        if conn:
            conn.close()

    logger.info("[ingest] === Phase 1 COMPLETE ===")
    logger.info("[ingest] Summary: %s", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description="L0FR Stream C Text Ingestion")
    parser.add_argument("--phase", type=int, default=1, help="Ingestion phase (1=BPHS+PD+JP)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to DB")
    parser.add_argument("--skip-embed", action="store_true", help="Skip embedding step")
    args = parser.parse_args()

    if args.phase == 1:
        result = run_phase1(dry_run=args.dry_run, skip_embed=args.skip_embed)
        print("RESULT:", result)
        return 0
    else:
        print(f"Phase {args.phase} not implemented yet")
        return 1


if __name__ == "__main__":
    sys.exit(main())
