"""
brahmagyan.l0_text_ingest_phase2 — L0FR Stream C: Phase 2 Text Ingestion
=========================================================================

Phase 2: Ingest texts 4-15 per L0FR_SOURCE_DATA_v1_0.md.
Deterministic-first: download djvu.txt → regex chunk → embed → DB insert.

Auto-downloadable texts (9 sources):
  jataka_parijata vol2  — Internet Archive
  4. uttara_kalamrita   — Internet Archive
  5. brihat_jataka      — Internet Archive
  6. saravali           — Internet Archive
  7. hora_sara          — Internet Archive
  9. sarvartha_chintamani — Internet Archive
  11. brihat_samhita    — Internet Archive (2 vols)
  14. muhurta_chintamani — Internet Archive
  15. lal_kitab         — Internet Archive

Manual-upload-required (SKIP — log to /tmp/l0fr_manual_upload_pending.txt):
  8. jaimini_sutram — Sanjay Rath publication
  10. tajaka_neelakanthi — Sanjay Rath publication
  12. yavana_jataka — academic edition
  13. bhrigu_samhita — multiple sources

Usage:
  python -m brahmagyan.l0_text_ingest_phase2 [--dry-run] [--skip-embed] [--text-id TEXT_ID]

Environment:
  DATABASE_URL: PostgreSQL connection string
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brahmagyan.l0_text_chunker import (
    TEXT_META,
    Chunk,
    chunk_text,
    insert_chunks,
    insert_classical_text,
    insert_text_source,
    chunk_jp_slokas,
    _split_into_chapters,
    _normalize_text,
    _extract_sanskrit,
    _extract_topics,
    _sha256,
    _split_jp_adhyayas,
    _write_park_log,
)
from brahmagyan.l0_text_embedder import embed_and_store, check_embedding_coverage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

TEXTS_DIR = Path("/tmp/l0fr_texts")
MANUAL_UPLOAD_LOG = Path("/tmp/l0fr_manual_upload_pending.txt")
PARK_LOG = Path("/tmp/l0fr_chunks_parked.txt")

# ── Phase 2 text metadata ─────────────────────────────────────────────────────

PHASE2_TEXT_META = {
    "jataka_parijata": {
        "title": "Jataka Parijata",
        "author": "Vaidyanatha Dikshita",
        "tradition_school": "parashari",
        "translator": "V. Subrahmanya Sastri",
        "edition": "2 vols, Motilal Banarsidass (Vol 1 + 2)",
        "source_url": "https://archive.org/details/JatakaParijataVolIOfIIByVSubrahmanyaSastri",
        "license": "public_domain",
    },
    "uttara_kalamrita": {
        "title": "Uttara Kalamrita",
        "author": "Kalidasa",
        "tradition_school": "parashari",
        "translator": "P. Subrahmanya Sastri",
        "edition": "P. Subrahmanya Sastri edition",
        "source_url": "https://archive.org/details/uttkalamrita-kalidas-ps-sastri",
        "license": "public_domain",
    },
    "brihat_jataka": {
        "title": "Brihat Jataka",
        "author": "Varahamihira",
        "tradition_school": "parashari",
        "translator": "B. Suryanarain Rao",
        "edition": "B. Suryanarain Rao 1919 edition",
        "source_url": "https://archive.org/details/Astrology_Books_by_B_Suryanarayana_Row",
        "license": "public_domain",
    },
    "saravali": {
        "title": "Saravali",
        "author": "Kalyana Varma",
        "tradition_school": "parashari",
        "translator": "R. Santhanam",
        "edition": "Ranjan Publications",
        "source_url": "https://archive.org/details/saravaliofkalyanavarmasanthanamr.astrology_202003_28_Z",
        "license": "public_domain",
    },
    "hora_sara": {
        "title": "Hora Sara",
        "author": "Prithuyasas",
        "tradition_school": "parashari",
        "translator": "R. Santhanam",
        "edition": "R. Santhanam English translation",
        "source_url": "https://archive.org/details/HoraSaraRSanthanamEng",
        "license": "public_domain",
    },
    "sarvartha_chintamani": {
        "title": "Sarvartha Chintamani",
        "author": "Venkatesh Daivagna",
        "tradition_school": "parashari",
        "translator": "Mahidhar Sharma",
        "edition": "Mahidhar Sharma edition",
        "source_url": "https://archive.org/details/sarvartha-chintamani-mahidhar-sharma",
        "license": "public_domain",
    },
    "brihat_samhita": {
        "title": "Brihat Samhita",
        "author": "Varahamihira",
        "tradition_school": "samhita",
        "translator": "M. Ramakrishna Bhat",
        "edition": "Motilal Banarsidass, 2 vols (1981)",
        "source_url": "https://archive.org/details/aqbw_brihat-samhita-part-1-by-varahamihira-translated-by-m-ramakrishna-bhat-sans",
        "license": "public_domain",
    },
    "muhurta_chintamani": {
        "title": "Muhurta Chintamani",
        "author": "Dayananda",
        "tradition_school": "muhurta",
        "translator": "Unknown",
        "edition": "Internet Archive edition",
        "source_url": "https://archive.org/details/muhurta-chintamani",
        "license": "public_domain",
    },
    "lal_kitab": {
        "title": "Lal Kitab",
        "author": "Pt. Roop Chand Joshi",
        "tradition_school": "lal_kitab",
        "translator": "B.M. Gosvami",
        "edition": "B.M. Gosvami edition",
        "source_url": "https://archive.org/details/jyotishlalkitabb.m.gosvami",
        "license": "public_domain",
    },
}

# Manual upload required texts
MANUAL_UPLOAD_TEXTS = {
    "jaimini_sutram": {
        "title": "Jaimini Sutram",
        "author": "Jaimini Rishi",
        "edition": "Sanjay Rath, Sagittarius Publications",
        "reason": "Sanjay Rath publications not on Internet Archive",
    },
    "tajaka_neelakanthi": {
        "title": "Tajaka Neelakanthi",
        "author": "Neelakantha",
        "edition": "Sanjay Rath",
        "reason": "Sanjay Rath publications not on Internet Archive",
    },
    "yavana_jataka": {
        "title": "Yavana Jataka",
        "author": "Sphujidhvaja",
        "edition": "David Pingree, Harvard Oriental Series",
        "reason": "Academic edition — not available on Internet Archive",
    },
    "bhrigu_samhita": {
        "title": "Bhrigu Samhita",
        "author": "Maharishi Bhrigu",
        "edition": "Multiple sources — native chooses extracts",
        "reason": "Multiple sources; native must choose which extracts to include",
    },
}

# ── Correct Internet Archive source config ────────────────────────────────────
# ia_id: Internet Archive identifier
# files: [(URL-encoded remote filename, local filename)]
# Note: Use %20 for spaces in filenames

PHASE2_SOURCES = {
    "jataka_parijata": {
        # Vol 2 supplement (vol 1 already ingested as phase 1)
        "ia_id_vol2": "JatakaParijataVolIIOfIIByVSubrahmanyaSastri",
        "files_vol2": [
            (
                "Jataka%20Parijata%20Vol%20II%20of%20II%20by%20V%20Subrahmanya%20Sastri_djvu.txt",
                "jp_vol2_djvu.txt",
            )
        ],
        "text_id_db": "jataka_parijata",
        "chunker": "jp_sloka",
    },
    "uttara_kalamrita": {
        "ia_id": "uttkalamrita-kalidas-ps-sastri",
        "files": [("Uttkalamrita-kalidas-ps-sastri_djvu.txt", "uk_djvu.txt")],
        "chunker": "numbered",
    },
    "brihat_jataka": {
        "ia_id": "Astrology_Books_by_B_Suryanarayana_Row",
        "files": [
            (
                "Brihat%20Jataka%20English%20Translation-%20B%20Suryanarain%20Row%201919%20LR_djvu.txt",
                "bj_djvu.txt",
            )
        ],
        "chunker": "numbered",
    },
    "saravali": {
        "ia_id": "saravaliofkalyanavarmasanthanamr.astrology_202003_28_Z",
        "files": [
            (
                "Saravali%20of%20Kalyana%20Varma%20Santhanam%20R.%20%28Astrology%29_djvu.txt",
                "saravali_djvu.txt",
            )
        ],
        "chunker": "numbered",
    },
    "hora_sara": {
        "ia_id": "HoraSaraRSanthanamEng",
        "files": [("Hora%20Sara%20RSanthanam%20Eng_djvu.txt", "hora_sara_djvu.txt")],
        "chunker": "numbered",
    },
    "sarvartha_chintamani": {
        "ia_id": "sarvartha-chintamani-mahidhar-sharma",
        "files": [
            (
                "Sarvartha%20Chintamani%20-%20Mahidhar%20Sharma_djvu.txt",
                "sc_djvu.txt",
            )
        ],
        "chunker": "numbered",
    },
    "brihat_samhita": {
        "ia_id": "aqbw_brihat-samhita-part-1-by-varahamihira-translated-by-m-ramakrishna-bhat-sans",
        "files": [
            (
                "Brihat%20Samhita%20Part%201%20By%20Varahamihira%20Translated%20By%20M%20Ramakrishna%20Bhat%20Sanskrit%20And%20English%20Astrology%20Illustrated%20Delhi%201986%20-%20Motilal%20Banarsidass_djvu.txt",
                "bs_vol1_djvu.txt",
            )
        ],
        "ia_id_vol2": "brihat-samhita-of-varaha-mihir-mr.-bhat-part-2-of-2-1981",
        "files_vol2": [
            (
                "brihat%20samhita%20OF%20VARAHA%20MIHIR_mr.%20bhat_part-2-of-2_1981_djvu.txt",
                "bs_vol2_djvu.txt",
            )
        ],
        "chunker": "numbered",
    },
    "muhurta_chintamani": {
        "ia_id": "muhurta-chintamani",
        "files": [("Muhurta%20Chintamani_djvu.txt", "mc_djvu.txt")],
        "chunker": "numbered",
    },
    "lal_kitab": {
        "ia_id": "jyotishlalkitabb.m.gosvami",
        "files": [("Jyotish_Lal%20Kitab_B.M.%20Gosvami_djvu.txt", "lal_kitab_djvu.txt")],
        "chunker": "numbered",
    },
}


def _log_manual_upload(text_id: str, info: dict) -> None:
    """Log manual-upload-required text to pending log."""
    MANUAL_UPLOAD_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(MANUAL_UPLOAD_LOG, "a") as f:
        f.write(
            f"MANUAL_UPLOAD_REQUIRED: {text_id}\n"
            f"  Title: {info['title']}\n"
            f"  Edition: {info['edition']}\n"
            f"  Author: {info['author']}\n"
            f"  Reason: {info['reason']}\n\n"
        )


def _download_file(text_dir: Path, ia_id: str, remote_fn: str, local_fn: str) -> str | None:
    """
    Download a file from Internet Archive.
    Deletes the cached HTML error page if present, then re-downloads.
    Returns local path if successful, None otherwise.
    """
    local_path = text_dir / local_fn

    # If file exists but is HTML error page (< 200KB and contains DOCTYPE), delete and retry
    if local_path.exists():
        size = local_path.stat().st_size
        if size > 10_000:
            # Quick check: not an HTML error page if > 200KB or starts with text
            with open(local_path, 'rb') as fh:
                header = fh.read(20)
            if not header.startswith(b'<!DOCTYPE') and not header.startswith(b'<html'):
                logger.info("[ingest2] Already downloaded (valid): %s", local_path)
                return str(local_path)
        logger.info("[ingest2] Removing invalid cached file: %s (%d bytes)", local_fn, size)
        local_path.unlink()

    url = f"https://archive.org/download/{ia_id}/{remote_fn}"
    logger.info("[ingest2] Downloading: %s -> %s", url, local_fn)
    result = subprocess.run(
        ["curl", "-s", "-L", "--max-time", "120", "-o", str(local_path), url],
        timeout=150,
        capture_output=True,
    )

    if result.returncode == 0 and local_path.exists():
        size = local_path.stat().st_size
        if size > 10_000:
            # Verify not HTML error page
            with open(local_path, 'rb') as fh:
                header = fh.read(20)
            if header.startswith(b'<!DOCTYPE') or header.startswith(b'<html'):
                logger.warning("[ingest2] Downloaded HTML error page for %s", local_fn)
                local_path.unlink()
                return None
            logger.info("[ingest2] Downloaded: %s (%d bytes)", local_fn, size)
            return str(local_path)
        else:
            logger.warning("[ingest2] File too small (%d bytes): %s", size, local_fn)
            local_path.unlink()
            return None

    logger.warning("[ingest2] Download failed for %s (rc=%d)", url, result.returncode)
    return None


def _download_phase2_sources(text_id: str, config: dict) -> list[str]:
    """Download source files. Returns list of valid local paths."""
    text_dir = TEXTS_DIR / text_id / "raw"
    text_dir.mkdir(parents=True, exist_ok=True)
    local_paths = []

    # Main files
    for remote_fn, local_fn in config.get("files", []):
        p = _download_file(text_dir, config["ia_id"], remote_fn, local_fn)
        if p:
            local_paths.append(p)

    # Vol2 files
    if config.get("ia_id_vol2"):
        vol2_dir = TEXTS_DIR / text_id / "raw"
        for remote_fn, local_fn in config.get("files_vol2", []):
            p = _download_file(vol2_dir, config["ia_id_vol2"], remote_fn, local_fn)
            if p:
                local_paths.append(p)

    return local_paths


def _chunk_with_strategy(
    text_id: str,
    local_paths: list[str],
    config: dict,
) -> tuple[list[Chunk], int, int]:
    """
    Chunk text files using the appropriate strategy.
    Returns (good_chunks, good_count, parked_count).
    """
    chunker_type = config.get("chunker", "numbered")
    all_good: list[Chunk] = []
    all_parked: list[Chunk] = []

    for src_path in local_paths:
        path = Path(src_path)
        if not path.exists():
            logger.warning("[ingest2] File not found: %s", src_path)
            continue

        raw_text = path.read_text(encoding="utf-8", errors="replace")
        raw_text = _normalize_text(raw_text)
        char_count = len(raw_text)
        logger.info("[ingest2] Processing %s from %s (%d chars)", text_id, path.name, char_count)

        if char_count < 1000:
            logger.warning("[ingest2] File too small (%d chars): %s", char_count, path.name)
            continue

        # Split into chapters
        if chunker_type == "jp_sloka":
            segments = _split_jp_adhyayas(raw_text)
        else:
            segments = _split_into_chapters(raw_text, text_id)

        logger.info("[ingest2] %s: found %d chapters in %s", text_id, len(segments), path.name)

        for ch_num, ch_title, ch_text in segments:
            if chunker_type == "jp_sloka":
                good, parked = chunk_jp_slokas(ch_text, text_id, ch_num, ch_title)
            else:
                good, parked = chunk_text(ch_text, text_id, ch_num, ch_title)
            all_good.extend(good)
            all_parked.extend(parked)

    if all_parked:
        _write_park_log(all_parked, str(PARK_LOG))

    logger.info("[ingest2] %s TOTAL: %d good, %d parked", text_id, len(all_good), len(all_parked))
    return all_good, len(all_good), len(all_parked)


def _get_db_conn():
    import psycopg2  # type: ignore
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        for env_path in [
            Path(__file__).parent.parent.parent / ".env.local",
            Path("/Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env.local"),
        ]:
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith("DATABASE_URL="):
                        db_url = line.split("=", 1)[1].strip()
                        break
            if db_url:
                break
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(db_url)


def run_phase2(
    dry_run: bool = False,
    skip_embed: bool = False,
    only_text_id: str | None = None,
) -> dict:
    """
    Phase 2: Ingest texts 4-15.
    Returns summary dict.
    """
    logger.info("[ingest2] === L0FR Stream C Phase 2 START ===")

    # Log manual-upload-required texts
    for tid, info in MANUAL_UPLOAD_TEXTS.items():
        logger.info("[ingest2] SKIP (manual upload required): %s", tid)
        _log_manual_upload(tid, info)

    summary = {
        "texts_attempted": [],
        "texts_succeeded": [],
        "texts_failed_download": [],
        "texts_manual_upload": list(MANUAL_UPLOAD_TEXTS.keys()),
        "chunk_counts": {},
        "parked_counts": {},
        "total_new_chunks": 0,
        "errors": [],
    }

    conn = None if dry_run else _get_db_conn()

    try:
        # Update TEXT_META with Phase 2 entries
        TEXT_META.update(PHASE2_TEXT_META)

        texts_to_process = {
            k: v for k, v in PHASE2_SOURCES.items()
            if only_text_id is None or k == only_text_id
        }

        for text_id, config in texts_to_process.items():
            logger.info("[ingest2] === Processing: %s ===", text_id)
            summary["texts_attempted"].append(text_id)

            # Determine DB text_id
            db_text_id = config.get("text_id_db", text_id)

            # Download source files
            if not dry_run:
                local_paths = _download_phase2_sources(text_id, config)
            else:
                # Dry run: use existing cached files if present
                text_dir = TEXTS_DIR / text_id / "raw"
                local_paths = []
                for local_fn in [lf for _, lf in config.get("files", [])]:
                    p = text_dir / local_fn
                    if p.exists() and p.stat().st_size > 10_000:
                        # Check not HTML
                        with open(p, 'rb') as fh:
                            hdr = fh.read(20)
                        if not hdr.startswith(b'<!DOCTYPE') and not hdr.startswith(b'<html'):
                            local_paths.append(str(p))
                for local_fn in [lf for _, lf in config.get("files_vol2", [])]:
                    p = text_dir / local_fn
                    if p.exists() and p.stat().st_size > 10_000:
                        with open(p, 'rb') as fh:
                            hdr = fh.read(20)
                        if not hdr.startswith(b'<!DOCTYPE') and not hdr.startswith(b'<html'):
                            local_paths.append(str(p))

            if not local_paths:
                logger.warning("[ingest2] No valid source files for %s", text_id)
                summary["texts_failed_download"].append(text_id)
                summary["errors"].append(f"{text_id}: download failed")
                continue

            # Chunk
            good_chunks, good_count, park_count = _chunk_with_strategy(
                db_text_id, local_paths, config
            )
            summary["chunk_counts"][text_id] = good_count
            summary["parked_counts"][text_id] = park_count

            if good_count == 0:
                logger.warning("[ingest2] Zero good chunks for %s — skipping", text_id)
                summary["texts_failed_download"].append(text_id)
                continue

            summary["texts_succeeded"].append(text_id)
            summary["total_new_chunks"] += good_count

            if not dry_run and conn:
                # Update TEXT_META for DB operations
                TEXT_META[db_text_id] = PHASE2_TEXT_META.get(db_text_id, PHASE2_TEXT_META.get(text_id, {}))
                insert_classical_text(conn, db_text_id)
                insert_text_source(conn, db_text_id)
                inserted = insert_chunks(conn, good_chunks)
                logger.info("[ingest2] %s: inserted %d chunks into DB", text_id, inserted)

        # Embed all newly inserted chunks
        if not dry_run and not skip_embed and conn:
            logger.info("[ingest2] === Embedding Phase 2 chunks ===")
            embedded_text_ids = set()
            for text_id in summary["texts_succeeded"]:
                db_text_id = PHASE2_SOURCES[text_id].get("text_id_db", text_id)
                embedded_text_ids.add(db_text_id)

            for db_text_id in embedded_text_ids:
                t0 = time.time()
                result = embed_and_store(conn, text_id=db_text_id)
                elapsed = time.time() - t0
                logger.info(
                    "[ingest2] %s embedding: embedded=%d failed=%d (%.1fs)",
                    db_text_id, result["embedded"], result["failed"], elapsed
                )

        # Final DB stats
        if not dry_run and conn:
            with conn.cursor() as cur:
                cur.execute("SELECT text_id, COUNT(*) FROM classical_text_chunks GROUP BY text_id ORDER BY text_id")
                db_counts = {r[0]: r[1] for r in cur.fetchall()}
            summary["db_total_by_text"] = db_counts
            summary["db_total_all"] = sum(db_counts.values())

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM classical_text_chunks WHERE embedding IS NOT NULL"
                )
                summary["embedded_count"] = cur.fetchone()[0]

    finally:
        if conn:
            conn.close()

    logger.info("[ingest2] === Phase 2 COMPLETE ===")
    logger.info("[ingest2] Succeeded: %s", summary["texts_succeeded"])
    logger.info("[ingest2] Failed: %s", summary["texts_failed_download"])
    logger.info("[ingest2] New chunks: %d", summary["total_new_chunks"])
    return summary


def main():
    parser = argparse.ArgumentParser(description="L0FR Stream C Phase 2 Text Ingestion")
    parser.add_argument("--dry-run", action="store_true", help="Skip DB writes and embedding")
    parser.add_argument("--skip-embed", action="store_true", help="Skip embedding step")
    parser.add_argument("--text-id", type=str, help="Process only this text_id")
    args = parser.parse_args()

    result = run_phase2(
        dry_run=args.dry_run,
        skip_embed=args.skip_embed,
        only_text_id=args.text_id,
    )
    import json
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
