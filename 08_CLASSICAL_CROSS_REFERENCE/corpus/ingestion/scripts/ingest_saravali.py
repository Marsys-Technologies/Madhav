#!/usr/bin/env python3
"""
ingest_saravali.py — Ingest Saravali (Kalyana Varma) into the M8 classical corpus.
Tier 2 text. Primary source: archive.org.
Target: ≥400 chunks, ≥95% embedded.

Usage:
  python ingest_saravali.py [--dry-run]

Exit codes:
  0 — success (≥400 chunks, ≥95% embedded)
  1 — partial success or procurement gap
"""

import argparse
import json
import logging
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

import requests

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
logger = logging.getLogger("ingest_saravali")

TEXT_KEY = "saravali"
TEXT_METADATA = {
    "text_key": TEXT_KEY,
    "title": "Saravali",
    "author": "Kalyana Varma",
    "tradition": "parashari",
    "school": "parashari",
    "tier": 2,
    "language_original": "sanskrit",
    "translation_author": "R. Santhanam",
    "source_url": "https://archive.org/search?query=saravali+kalyana+varma",
    "procurement_date": str(date.today()),
}
GCS_PATH = "L8/classical_texts/tier2/saravali_chunks.jsonl"
CHUNK_THRESHOLD = 400

ARCHIVE_METADATA_BASE = "https://archive.org/metadata/"
ARCHIVE_DOWNLOAD_BASE = "https://archive.org/download/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (MARSYS-JIS M8 academic ingestion; contact: mail.abhisek.mohanty@gmail.com)"
}
REQUEST_DELAY = 0.5

# Known identifiers — ordered by expected quality/size
KNOWN_IDENTIFIERS = [
    "saravaliofkalyanavarmasanthanamr.astrology_202003_28_Z",  # 978KB R. Santhanam (verified 2026-05-14)
    "KalyanaVarmasSaravali_201707",                            # 623KB (verified 2026-05-14)
    "in.ernet.dli.2015.404963",
    "Saravali",
    "saravali",
    "SaravaliKalyanaVarma",
    "in.ernet.dli.2015.282607",
]


def fetch_url(url: str, retries: int = 3) -> str | None:
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
            logger.warning("Request error %s (attempt %d): %s", url, attempt + 1, e)
        time.sleep(REQUEST_DELAY * (attempt + 1))
    return None


def get_identifier_urls(ident: str) -> list[str]:
    """Return list of text file URLs for a given archive.org identifier."""
    meta_text = fetch_url(f"{ARCHIVE_METADATA_BASE}{ident}")
    if not meta_text:
        return []
    try:
        meta = json.loads(meta_text)
    except Exception:
        return []
    files = meta.get("files", [])
    djvu = [f for f in files if f.get("name", "").endswith("_djvu.txt")]
    txt = [f for f in files if f.get("name", "").endswith(".txt") and "_djvu" not in f.get("name", "")]
    html = [f for f in files if f.get("name", "").lower().endswith((".htm", ".html"))]
    chosen = djvu or txt or html
    return [f"{ARCHIVE_DOWNLOAD_BASE}{ident}/{f['name']}" for f in chosen[:5]]


def find_all_sources() -> list[tuple[str, list[str]]]:
    """Return list of (identifier, urls) for all available Saravali sources."""
    sources: list[tuple[str, list[str]]] = []
    for ident in KNOWN_IDENTIFIERS:
        urls = get_identifier_urls(ident)
        if urls:
            logger.info("Source found: %s (%d files)", ident, len(urls))
            sources.append((ident, urls))
        time.sleep(REQUEST_DELAY)
        if len(sources) >= 2:
            break  # Two sources is enough for volume coverage

    if not sources:
        # Search fallback
        search = fetch_url("https://archive.org/advancedsearch.php?q=saravali+kalyana+varma&output=json&rows=5")
        if search:
            try:
                docs = json.loads(search).get("response", {}).get("docs", [])
                for doc in docs:
                    ident = doc.get("identifier", "")
                    urls = get_identifier_urls(ident) if ident else []
                    if urls:
                        sources.append((ident, urls))
                        time.sleep(REQUEST_DELAY)
                        if len(sources) >= 2:
                            break
            except Exception:
                pass
    return sources


def fetch_texts(urls: list[str]) -> list[tuple[str, str]]:
    results = []
    for url in urls:
        text = fetch_url(url)
        if text and len(text) > 500:
            if url.lower().endswith((".htm", ".html")):
                text = clean_html(text)
            results.append((url, text))
        time.sleep(REQUEST_DELAY)
    return results


def run(dry_run: bool = False) -> int:
    logger.info("=== Saravali Ingestion START (dry_run=%s) ===", dry_run)

    sources = find_all_sources()
    if not sources:
        logger.warning("Saravali not found — PROCUREMENT_GAP")
        print(json.dumps({"status": "PROCUREMENT_GAP", "text_key": TEXT_KEY}))
        return 1

    text_files: list[tuple[str, str]] = []
    for ident, urls in sources:
        text_files.extend(fetch_texts(urls))

    if not text_files:
        logger.warning("No text content retrieved")
        print(json.dumps({"status": "PROCUREMENT_GAP", "text_key": TEXT_KEY}))
        return 1

    ident = sources[0][0]
    total_chars = sum(len(t) for _, t in text_files)
    logger.info("Fetched %d files (~%d chars) from %d sources", len(text_files), total_chars, len(sources))

    if dry_run:
        print(json.dumps({"status": "dry_run_complete", "text_key": TEXT_KEY, "files": len(text_files), "chars": total_chars, "sources": len(sources)}))
        return 0

    text_id = db_upsert_text(TEXT_METADATA)
    logger.info("text_id: %s", text_id)

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

    try:
        all_chunks = embed_batch(all_chunks)
        embedded_count = sum(1 for c in all_chunks if c.get("embedding") is not None)
    except Exception as e:
        logger.error("Embedding failed: %s", e)
        embedded_count = 0

    inserted = db_bulk_insert_chunks(all_chunks)
    db_update_embeddings(all_chunks)
    chunk_count = db_update_chunk_count(text_id)
    logger.info("Inserted %d new rows; chunk_count=%d", inserted, chunk_count)

    try:
        gcs_uri = gcs_upload_jsonl(all_chunks, GCS_PATH)
    except Exception as e:
        logger.warning("GCS upload failed: %s", e)
        gcs_uri = None

    embedding_pct = (embedded_count / len(all_chunks) * 100) if all_chunks else 0
    summary = {
        "text_key": TEXT_KEY,
        "text_id": text_id,
        "identifier": ident,
        "files_fetched": len(text_files),
        "chunks_inserted": inserted,
        "chunk_count_in_db": chunk_count,
        "embeddings_ok": embedded_count,
        "embedding_pct": round(embedding_pct, 1),
        "gcs_uri": gcs_uri,
        "ac_pass": chunk_count >= CHUNK_THRESHOLD and embedding_pct >= 95,
    }
    print(json.dumps(summary))
    logger.info("=== Saravali Ingestion COMPLETE ===")

    if chunk_count < CHUNK_THRESHOLD:
        logger.warning("chunk_count %d < %d threshold", chunk_count, CHUNK_THRESHOLD)
        return 1
    if embedding_pct < 95:
        logger.warning("embedding_pct %.1f%% < 95%%", embedding_pct)
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))
