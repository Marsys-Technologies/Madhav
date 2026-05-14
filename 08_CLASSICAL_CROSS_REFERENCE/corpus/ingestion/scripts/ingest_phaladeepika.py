#!/usr/bin/env python3
"""
ingest_phaladeepika.py — Ingest Phaladeepika (Mantreswara, Sitaram Jha translation)
into the M8 classical corpus.
Sources: archive.org (primary), alternate scans (fallback).
Tier 1 — high priority but non-blocking (unlike BPHS).

Usage:
  python ingest_phaladeepika.py [--dry-run] [--limit-chapters N]

Exit codes:
  0 — success (≥300 chunks, ≥95% embedded)
  1 — partial success (fewer chunks or embedding issues)
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
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

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
logger = logging.getLogger("ingest_phaladeepika")

TEXT_KEY = "phaladeepika"
TEXT_METADATA = {
    "text_key": TEXT_KEY,
    "title": "Phaladeepika",
    "author": "Mantreswara",
    "tradition": "parashari",
    "school": "parashari",
    "tier": 1,
    "language_original": "sanskrit",
    "translation_author": "Sitaram Jha",
    "source_url": "https://archive.org/search?query=phaladeepika+jyotish",
    "procurement_date": str(date.today()),
}
GCS_PATH = "L8/classical_texts/tier1/phaladeepika_chunks.jsonl"

ARCHIVE_SEARCH_URL = "https://archive.org/search?query=phaladeepika+jyotish&output=json"
ARCHIVE_METADATA_BASE = "https://archive.org/metadata/"
ARCHIVE_DOWNLOAD_BASE = "https://archive.org/download/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (MARSYS-JIS M8 academic ingestion; contact: mail.abhisek.mohanty@gmail.com)"
}
REQUEST_DELAY = 0.5


def fetch_url(url: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code in (403, 404):
                logger.warning("HTTP %d at %s", resp.status_code, url)
                return None
        except requests.RequestException as e:
            logger.warning("Request error %s (attempt %d): %s", url, attempt + 1, e)
        time.sleep(REQUEST_DELAY * (attempt + 1))
    return None


def find_archive_text_files(identifier: str) -> list[str]:
    """Return list of HTML/text file URLs for an archive.org item."""
    meta_url = f"{ARCHIVE_METADATA_BASE}{identifier}"
    meta_json = fetch_url(meta_url)
    if not meta_json:
        return []
    try:
        meta = json.loads(meta_json)
        files = meta.get("files", [])
        text_files = []
        for f in files:
            name = f.get("name", "")
            if name.lower().endswith((".htm", ".html", ".txt")):
                text_files.append(f"{ARCHIVE_DOWNLOAD_BASE}{identifier}/{name}")
        return text_files
    except Exception:
        return []


def fetch_archive_text(identifier: str) -> list[tuple[str, str]]:
    """
    Fetch text content from archive.org item.
    Returns list of (source_url, text_content) tuples.
    """
    files = find_archive_text_files(identifier)
    if not files:
        # Try to get main text page directly
        direct_url = f"{ARCHIVE_DOWNLOAD_BASE}{identifier}"
        html = fetch_url(direct_url)
        if html:
            text = clean_html(html)
            if len(text) > 500:
                return [(direct_url, text)]
        return []

    results = []
    for url in files[:20]:  # cap at 20 files
        html = fetch_url(url)
        if html:
            text = clean_html(html)
            if len(text) > 200:
                results.append((url, text))
        time.sleep(REQUEST_DELAY)
    return results


def search_archive_for_phaladeepika() -> str | None:
    """Search archive.org for Phaladeepika; return best identifier."""
    # Try known identifiers first — larger djvu.txt sources preferred for chunk count
    known_identifiers = [
        "in.ernet.dli.2015.406048",          # 1.37MB djvu.txt (verified 2026-05-14)
        "in.ernet.dli.2015.92117",            # 680KB "Mantreswaras Phaladeepika" (verified)
        "dli.ernet.507316",                   # 669KB Phaladeepika 1950 (verified)
        "phaladeepika-sitaram-jha",
        "Phaladeepika",
        "phaladeepika",
        "PhaladeepikaMantreswara",
    ]
    for identifier in known_identifiers:
        meta_url = f"{ARCHIVE_METADATA_BASE}{identifier}"
        resp_text = fetch_url(meta_url)
        if resp_text and '"identifier"' in resp_text:
            logger.info("Found archive.org identifier: %s", identifier)
            return identifier
        time.sleep(REQUEST_DELAY)

    # Fallback: search API
    search_url = "https://archive.org/advancedsearch.php?q=phaladeepika+jyotish&output=json&rows=5"
    search_text = fetch_url(search_url)
    if search_text:
        try:
            results = json.loads(search_text)
            docs = results.get("response", {}).get("docs", [])
            if docs:
                return docs[0].get("identifier")
        except Exception:
            pass
    return None


def run(dry_run: bool = False, limit_chapters: int | None = None) -> int:
    logger.info("=== Phaladeepika Ingestion START (dry_run=%s) ===", dry_run)

    identifier = search_archive_for_phaladeepika()
    if not identifier:
        logger.warning("Phaladeepika not found on archive.org — recording procurement gap")
        print(json.dumps({
            "status": "PROCUREMENT_GAP",
            "text_key": TEXT_KEY,
            "message": "Phaladeepika unavailable on archive.org after search",
        }))
        return 1

    logger.info("Fetching Phaladeepika from archive.org identifier: %s", identifier)
    text_files = fetch_archive_text(identifier)

    if not text_files:
        logger.warning("No text content retrieved for identifier: %s", identifier)
        print(json.dumps({
            "status": "PROCUREMENT_GAP",
            "text_key": TEXT_KEY,
            "message": f"No text content found at {identifier}",
        }))
        return 1

    if dry_run:
        total_chars = sum(len(t) for _, t in text_files)
        logger.info("DRY RUN complete: %d files, ~%d chars", len(text_files), total_chars)
        print(json.dumps({
            "status": "dry_run_complete",
            "text_key": TEXT_KEY,
            "files_fetched": len(text_files),
            "total_chars": total_chars,
        }))
        return 0

    # Upsert text metadata
    text_id = db_upsert_text(TEXT_METADATA)
    logger.info("text_id: %s", text_id)

    # Build chunks from all text files
    all_chunks: list[dict[str, Any]] = []
    global_idx = 0
    for i, (url, text) in enumerate(text_files):
        raw_chunks = chunk_text(text, max_tokens=500, overlap=80)
        for c in raw_chunks:
            all_chunks.append({
                "text_id": text_id,
                "chunk_index": global_idx,
                "chapter": f"File {i + 1}",
                "verse_range": None,
                "content": c["content"],
                "language": "en",
            })
            global_idx += 1

    logger.info("Built %d chunks from %d files", len(all_chunks), len(text_files))

    # Embed
    try:
        all_chunks = embed_batch(all_chunks)
        embedded_count = sum(1 for c in all_chunks if c.get("embedding") is not None)
    except Exception as e:
        logger.error("Embedding failed: %s", e)
        embedded_count = 0

    # DB insert + embedding update
    inserted = db_bulk_insert_chunks(all_chunks)
    db_update_embeddings(all_chunks)
    chunk_count = db_update_chunk_count(text_id)
    logger.info("Inserted %d new rows; chunk_count=%d", inserted, chunk_count)

    # GCS upload
    try:
        gcs_uri = gcs_upload_jsonl(all_chunks, GCS_PATH)
    except Exception as e:
        logger.warning("GCS upload failed: %s", e)
        gcs_uri = None

    embedding_pct = (embedded_count / len(all_chunks) * 100) if all_chunks else 0
    summary = {
        "text_key": TEXT_KEY,
        "text_id": text_id,
        "files_fetched": len(text_files),
        "chunks_inserted": inserted,
        "chunk_count_in_db": chunk_count,
        "embeddings_ok": embedded_count,
        "embedding_pct": round(embedding_pct, 1),
        "gcs_uri": gcs_uri,
        "ac_m8b4_pass": chunk_count >= 300 and embedding_pct >= 95,
    }
    print(json.dumps(summary))
    logger.info("=== Phaladeepika Ingestion COMPLETE ===")

    if chunk_count < 300:
        logger.warning("AC.M8B.4: chunk_count %d < 300 threshold", chunk_count)
        return 1
    if embedding_pct < 95:
        logger.warning("AC.M8B.4: embedding_pct %.1f%% < 95%%", embedding_pct)
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Phaladeepika into M8 classical corpus")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit-chapters", type=int, default=None)
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run, limit_chapters=args.limit_chapters))
