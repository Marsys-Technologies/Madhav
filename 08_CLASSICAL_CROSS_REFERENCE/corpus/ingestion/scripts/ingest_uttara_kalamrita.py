#!/usr/bin/env python3
"""
ingest_uttara_kalamrita.py — Ingest Uttara Kalamrita (Kalidasa) into M8 corpus.
Tier 2 text. Primary source: archive.org.
Target: ≥200 chunks, ≥95% embedded.

Exit codes: 0 success, 1 partial/gap
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
logger = logging.getLogger("ingest_uttara_kalamrita")

TEXT_KEY = "uttara_kalamrita"
TEXT_METADATA = {
    "text_key": TEXT_KEY,
    "title": "Uttara Kalamrita",
    "author": "Kalidasa",
    "tradition": "parashari",
    "school": "parashari",
    "tier": 2,
    "language_original": "sanskrit",
    "translation_author": "P.S. Sastri",
    "source_url": "https://archive.org/search?query=uttara+kalamrita+kalidasa",
    "procurement_date": str(date.today()),
}
GCS_PATH = "L8/classical_texts/tier2/uttara_kalamrita_chunks.jsonl"
CHUNK_THRESHOLD = 200

ARCHIVE_METADATA_BASE = "https://archive.org/metadata/"
ARCHIVE_DOWNLOAD_BASE = "https://archive.org/download/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (MARSYS-JIS M8 academic ingestion; contact: mail.abhisek.mohanty@gmail.com)"
}
REQUEST_DELAY = 0.5

KNOWN_IDENTIFIERS = [
    "uttkalamrita-kalidas-ps-sastri",   # 373KB P.S. Sastri (verified 2026-05-14)
    "uttara-kalamrita-kalidas",          # 260KB (verified 2026-05-14)
    "in.ernet.dli.2015.313087",
    "UttaraKalamrita",
    "uttara-kalamrita",
    "UttaraKalamritaKalidasa",
    "in.ernet.dli.2015.149827",
]


def fetch_url(url: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code in (403, 404):
                return None
            else:
                logger.warning("HTTP %d at %s (attempt %d)", resp.status_code, url, attempt + 1)
        except requests.RequestException as e:
            logger.warning("Request error %s (attempt %d): %s", url, attempt + 1, e)
        time.sleep(REQUEST_DELAY * (attempt + 1))
    return None


def find_best_identifier() -> tuple[str, list[str]] | None:
    for ident in KNOWN_IDENTIFIERS:
        meta_text = fetch_url(f"{ARCHIVE_METADATA_BASE}{ident}")
        if not meta_text:
            time.sleep(REQUEST_DELAY)
            continue
        try:
            meta = json.loads(meta_text)
        except Exception:
            continue
        files = meta.get("files", [])
        djvu = [f for f in files if f.get("name", "").endswith("_djvu.txt")]
        txt = [f for f in files if f.get("name", "").endswith(".txt") and "_djvu" not in f.get("name", "")]
        html = [f for f in files if f.get("name", "").lower().endswith((".htm", ".html"))]
        chosen = djvu or txt or html
        if chosen:
            urls = [f"{ARCHIVE_DOWNLOAD_BASE}{ident}/{f['name']}" for f in chosen[:5]]
            logger.info("Found identifier %s with %d text files", ident, len(urls))
            return ident, urls
        time.sleep(REQUEST_DELAY)

    # Search fallback
    search = fetch_url("https://archive.org/advancedsearch.php?q=uttara+kalamrita+kalidasa&output=json&rows=5")
    if search:
        try:
            docs = json.loads(search).get("response", {}).get("docs", [])
            for doc in docs:
                ident = doc.get("identifier", "")
                if not ident:
                    continue
                meta_text = fetch_url(f"{ARCHIVE_METADATA_BASE}{ident}")
                if not meta_text:
                    continue
                try:
                    meta = json.loads(meta_text)
                except Exception:
                    continue
                files = meta.get("files", [])
                djvu = [f for f in files if f.get("name", "").endswith("_djvu.txt")]
                chosen = djvu or [f for f in files if f.get("name", "").endswith(".txt")]
                if chosen:
                    urls = [f"{ARCHIVE_DOWNLOAD_BASE}{ident}/{f['name']}" for f in chosen[:5]]
                    return ident, urls
                time.sleep(REQUEST_DELAY)
        except Exception:
            pass
    return None


def run(dry_run: bool = False) -> int:
    logger.info("=== Uttara Kalamrita Ingestion START (dry_run=%s) ===", dry_run)

    result = find_best_identifier()
    if not result:
        logger.warning("Uttara Kalamrita not found — PROCUREMENT_GAP")
        print(json.dumps({"status": "PROCUREMENT_GAP", "text_key": TEXT_KEY}))
        return 1

    ident, urls = result
    text_files: list[tuple[str, str]] = []
    for url in urls:
        text = fetch_url(url)
        if text and len(text) > 500:
            if url.lower().endswith((".htm", ".html")):
                text = clean_html(text)
            text_files.append((url, text))
        time.sleep(REQUEST_DELAY)

    if not text_files:
        print(json.dumps({"status": "PROCUREMENT_GAP", "text_key": TEXT_KEY, "identifier": ident}))
        return 1

    total_chars = sum(len(t) for _, t in text_files)
    logger.info("Fetched %d files (~%d chars) from %s", len(text_files), total_chars, ident)

    if dry_run:
        print(json.dumps({"status": "dry_run_complete", "text_key": TEXT_KEY, "files": len(text_files), "chars": total_chars}))
        return 0

    text_id = db_upsert_text(TEXT_METADATA)

    all_chunks: list[dict[str, Any]] = []
    global_idx = 0
    for i, (url, text) in enumerate(text_files):
        for c in chunk_text(text, max_tokens=500, overlap=80):
            all_chunks.append({
                "text_id": text_id,
                "chunk_index": global_idx,
                "chapter": f"File {i + 1}",
                "verse_range": None,
                "content": c["content"],
                "language": "en",
            })
            global_idx += 1

    logger.info("Built %d chunks", len(all_chunks))

    try:
        all_chunks = embed_batch(all_chunks)
        embedded_count = sum(1 for c in all_chunks if c.get("embedding") is not None)
    except Exception as e:
        logger.error("Embedding failed: %s", e)
        embedded_count = 0

    inserted = db_bulk_insert_chunks(all_chunks)
    db_update_embeddings(all_chunks)
    chunk_count = db_update_chunk_count(text_id)

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
    logger.info("=== Uttara Kalamrita Ingestion COMPLETE ===")

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
