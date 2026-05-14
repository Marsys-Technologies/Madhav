#!/usr/bin/env python3
"""
ingest_bphs.py — Ingest Brihat Parashara Hora Shastra (BPHS) into the M8 corpus.
Text: R. Santhanam translation (Ranjan Publications), sourced from archive.org / sacred-texts.com.
Tier 1 — mandatory text. If unavailable at all sources, sets BLOCKED_PROCUREMENT.

Usage:
  python ingest_bphs.py [--dry-run] [--limit-chapters N]

Exit codes:
  0 — success (or dry-run complete)
  1 — non-fatal partial failure (some chapters missing)
  2 — BLOCKED: BPHS unavailable at all sources

AC.M8B.1: script complete, idempotent, exits 0
AC.M8B.2: ≥800 chunks loaded; embeddings ≥95%
AC.M8B.5: uploaded to gs://madhav-marsys-sources/L8/classical_texts/tier1/bphs_chunks.jsonl
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent))
from ingest_utils import (
    clean_html, chunk_text, embed_batch,
    db_upsert_text, db_bulk_insert_chunks, db_update_embeddings, db_update_chunk_count,
    gcs_upload_jsonl,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("ingest_bphs")

TEXT_KEY = "bphs"
TEXT_METADATA = {
    "text_key": TEXT_KEY,
    "title": "Brihat Parashara Hora Shastra",
    "author": "Maharishi Parashara",
    "tradition": "parashari",
    "school": "parashari",
    "tier": 1,
    "language_original": "sanskrit",
    "translation_author": "R. Santhanam",
    "source_url": "https://archive.org/download/BrihatParasaraHoraSastra/",
    "procurement_date": str(date.today()),
}
GCS_PATH = "L8/classical_texts/tier1/bphs_chunks.jsonl"

# archive.org — primary source (verified 2026-05-14)
# BPHSEnglish has R. Santhanam 2-volume djvu.txt (OCR text of the authoritative English translation)
ARCHIVE_IDENTIFIERS = [
    "BPHSEnglish",                      # R. Santhanam 2-vol (verified available)
    "brihat-parashara-hora-shastra",     # alternate (djvu.txt available)
    "brihat-parashara-hora-sastra",      # alternate (djvu.txt available)
    "BrihatParasharHoraShastra",         # further fallback
]
ARCHIVE_METADATA_BASE = "https://archive.org/metadata/"
ARCHIVE_DOWNLOAD_BASE = "https://archive.org/download/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (MARSYS-JIS M8 academic ingestion; contact: mail.abhisek.mohanty@gmail.com)"
}
REQUEST_DELAY = 0.5  # seconds between requests (polite crawling)


def fetch_url(url: str, retries: int = 3) -> str | None:
    """Fetch a URL with retries. Returns text content or None on failure."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code in (403, 404):
                logger.warning("HTTP %d at %s", resp.status_code, url)
                return None
            else:
                logger.warning("HTTP %d at %s (attempt %d)", resp.status_code, url, attempt + 1)
        except requests.RequestException as e:
            logger.warning("Request error at %s (attempt %d): %s", url, attempt + 1, e)
        time.sleep(REQUEST_DELAY * (attempt + 1))
    return None


def fetch_bphs_text_files() -> list[tuple[str, str]]:
    """
    Try each archive.org identifier in order; return list of (url, text_content).
    Prefers _djvu.txt files (best OCR quality). Returns on first successful identifier.
    """
    for ident in ARCHIVE_IDENTIFIERS:
        logger.info("Trying archive.org identifier: %s", ident)
        meta_url = f"{ARCHIVE_METADATA_BASE}{ident}"
        meta_text = fetch_url(meta_url)
        if not meta_text:
            continue
        try:
            meta = json.loads(meta_text)
        except Exception:
            continue

        files = meta.get("files", [])
        # Prefer _djvu.txt files for quality OCR text
        djvu_files = [f for f in files if f.get("name", "").endswith("_djvu.txt")]
        txt_files = [f for f in files if f.get("name", "").endswith(".txt") and not f.get("name", "").endswith("_djvu.txt")]
        chosen = djvu_files or txt_files

        if not chosen:
            logger.warning("No text files in identifier %s", ident)
            continue

        results = []
        for f in chosen:
            name = f["name"]
            url = f"{ARCHIVE_DOWNLOAD_BASE}{ident}/{name}"
            logger.info("Fetching text file: %s", url)
            text = fetch_url(url)
            if text and len(text) > 1000:
                results.append((url, text))
            time.sleep(REQUEST_DELAY)

        if results:
            logger.info("Retrieved %d text files from identifier %s", len(results), ident)
            return results

    return []


def build_chunks_from_texts(
    text_files: list[tuple[str, str]],
    text_id: str,
) -> list[dict[str, Any]]:
    """Chunk all text files; assign text_id, file metadata."""
    all_chunks: list[dict[str, Any]] = []
    global_idx = 0
    for file_num, (url, text) in enumerate(text_files):
        # Clean plain text (not HTML)
        import unicodedata, re
        text = unicodedata.normalize("NFKD", text)
        text = re.sub(r"\s+", " ", text).strip()
        vol_label = f"Vol. {file_num + 1}" if len(text_files) > 1 else "Single Volume"
        raw_chunks = chunk_text(text, max_tokens=500, overlap=80)
        for c in raw_chunks:
            all_chunks.append({
                "text_id": text_id,
                "chunk_index": global_idx,
                "chapter": vol_label,
                "verse_range": None,
                "content": c["content"],
                "language": "en",
            })
            global_idx += 1
    return all_chunks


def run(dry_run: bool = False, limit_chapters: int | None = None) -> int:
    """Main ingestion flow. Returns exit code."""
    logger.info("=== BPHS Ingestion START (dry_run=%s) ===", dry_run)

    # ── Step 1: Fetch BPHS text files from archive.org ────────────────────────
    text_files = fetch_bphs_text_files()

    if not text_files:
        logger.error("BPHS unavailable at all archive.org identifiers — BLOCKED_PROCUREMENT")
        print(json.dumps({
            "status": "BLOCKED_PROCUREMENT",
            "text_key": TEXT_KEY,
            "message": "BPHS unavailable at all sources after retries",
        }))
        return 2

    total_chars = sum(len(t) for _, t in text_files)
    logger.info("Fetched %d text files (~%d chars)", len(text_files), total_chars)

    if dry_run:
        logger.info("DRY RUN complete")
        print(json.dumps({
            "status": "dry_run_complete",
            "text_key": TEXT_KEY,
            "files_fetched": len(text_files),
            "total_chars": total_chars,
        }))
        return 0

    # ── Step 2: Upsert text metadata ───────────────────────────────────────────
    logger.info("Upserting classical_texts row for %s", TEXT_KEY)
    text_id = db_upsert_text(TEXT_METADATA)
    logger.info("text_id: %s", text_id)

    # ── Step 3: Chunk ──────────────────────────────────────────────────────────
    chunks = build_chunks_from_texts(text_files, text_id)
    logger.info("Built %d chunks from %d text files", len(chunks), len(text_files))

    # ── Step 4: Embed ──────────────────────────────────────────────────────────
    logger.info("Embedding %d chunks via Vertex AI text-embedding-004", len(chunks))
    try:
        chunks = embed_batch(chunks)
        embedded_count = sum(1 for c in chunks if c.get("embedding") is not None)
        logger.info("Embedded %d / %d chunks", embedded_count, len(chunks))
    except Exception as e:
        logger.error("Embedding failed: %s — proceeding without embeddings", e)
        embedded_count = 0

    # ── Step 5: DB bulk insert + embedding update ──────────────────────────────
    logger.info("Inserting %d chunks into classical_chunks", len(chunks))
    inserted = db_bulk_insert_chunks(chunks)
    emb_updated = db_update_embeddings(chunks)
    logger.info("Embedding rows updated: %d", emb_updated)
    chunk_count = db_update_chunk_count(text_id)
    logger.info("Inserted %d new rows; chunk_count updated to %d", inserted, chunk_count)

    # ── Step 6: GCS upload ─────────────────────────────────────────────────────
    logger.info("Uploading JSONL to GCS: %s", GCS_PATH)
    try:
        gcs_uri = gcs_upload_jsonl(chunks, GCS_PATH)
        logger.info("Uploaded to %s", gcs_uri)
    except Exception as e:
        logger.warning("GCS upload failed (non-fatal): %s", e)
        gcs_uri = None

    # ── Step 7: Summary ────────────────────────────────────────────────────────
    embedding_pct = (embedded_count / len(chunks) * 100) if chunks else 0
    summary = {
        "text_key": TEXT_KEY,
        "text_id": text_id,
        "files_fetched": len(text_files),
        "chunks_inserted": inserted,
        "chunk_count_in_db": chunk_count,
        "embeddings_ok": embedded_count,
        "embedding_pct": round(embedding_pct, 1),
        "gcs_uri": gcs_uri,
        "ac_m8b2_pass": chunk_count >= 800 and embedding_pct >= 95,
    }
    print(json.dumps(summary))
    logger.info("=== BPHS Ingestion COMPLETE ===")

    if chunk_count < 800:
        logger.warning("AC.M8B.2: chunk_count %d < 800 threshold", chunk_count)
        return 1
    if embedding_pct < 95:
        logger.warning("AC.M8B.2: embedding_pct %.1f%% < 95%% threshold", embedding_pct)
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest BPHS into M8 classical corpus")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but do not write to DB/GCS")
    parser.add_argument("--limit-chapters", type=int, default=None, help="Limit to first N chapters")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run, limit_chapters=args.limit_chapters))
