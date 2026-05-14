#!/usr/bin/env python3
"""
ingest_chandra_kala_nadi.py — Ingest Chandra Kala Nadi (R. Santhanam translation).
Nadi/BNN tier. Source: archive.org.
Target: ≥300 chunks, ≥90% embedded.
"""

import argparse, json, logging, sys, time
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s", stream=sys.stderr)
logger = logging.getLogger("ingest_chandra_kala_nadi")

TEXT_KEY = "chandra_kala_nadi"
TEXT_METADATA = {
    "text_key": TEXT_KEY, "title": "Chandra Kala Nadi", "author": "Chandra Nadi",
    "tradition": "nadi", "school": "nadi", "tier": 4,
    "language_original": "tamil", "translation_author": "R. Santhanam",
    "source_url": "https://archive.org/search?query=chandra+kala+nadi+santhanam",
    "procurement_date": str(date.today()),
}
GCS_PATH = "L8/classical_texts/nadi_bnn/chandra_kala_nadi_chunks.jsonl"
CHUNK_THRESHOLD = 300
EMBED_THRESHOLD = 90.0
ARCHIVE_DOWNLOAD_BASE = "https://archive.org/download/"
ARCHIVE_METADATA_BASE = "https://archive.org/metadata/"
HEADERS = {"User-Agent": "Mozilla/5.0 (MARSYS-JIS M8 academic ingestion; contact: mail.abhisek.mohanty@gmail.com)"}
REQUEST_DELAY = 0.5

KNOWN_IDENTIFIERS = [
    "in.ernet.dli.2015.489053",              # verified: Chandra Kala Nadi (Deva Keralam) djvu.txt
    "j-90370-r-santhanam-deva-keralam-chandra-kala-nadi-2004-vol-3",  # verified: Part 3 djvu.txt
    "ChandraKalaNadiRSanthanam",
    "chandra-kala-nadi",
    "ChandraKalaNadi",
    "chandra_kala_nadi",
]


def fetch_url(url: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code in (403, 404):
                return None
        except requests.RequestException as e:
            logger.warning("Request error %s (attempt %d): %s", url, attempt + 1, e)
        time.sleep(REQUEST_DELAY * (attempt + 1))
    return None


def find_text_files() -> list[tuple[str, str]]:
    for ident in KNOWN_IDENTIFIERS:
        meta_text = fetch_url(f"{ARCHIVE_METADATA_BASE}{ident}")
        if not meta_text:
            time.sleep(REQUEST_DELAY)
            continue
        try:
            files = json.loads(meta_text).get("files", [])
        except Exception:
            continue
        djvu = [f for f in files if f.get("name", "").endswith("_djvu.txt")]
        txt = [f for f in files if f.get("name", "").endswith(".txt") and "_djvu" not in f.get("name", "")]
        pdf = [f for f in files if f.get("name", "").endswith(".pdf")]
        chosen = djvu or txt or pdf
        if chosen:
            results = []
            for f in chosen[:5]:
                url = f"{ARCHIVE_DOWNLOAD_BASE}{ident}/{f['name']}"
                text = fetch_url(url)
                if text and len(text) > 500:
                    results.append((url, text))
                time.sleep(REQUEST_DELAY)
            if results:
                logger.info("Found %d files from identifier: %s", len(results), ident)
                return results
        time.sleep(REQUEST_DELAY)
    return []


def run(dry_run: bool = False) -> int:
    logger.info("=== Chandra Kala Nadi Ingestion START (dry_run=%s) ===", dry_run)

    text_files = find_text_files()
    if not text_files:
        logger.warning("Chandra Kala Nadi not found on archive.org — PROCUREMENT_GAP")
        print(json.dumps({"status": "PROCUREMENT_GAP", "text_key": TEXT_KEY,
                          "note": "Text not found at known archive.org identifiers. "
                                  "Search for 'Chandra Kala Nadi Santhanam' or "
                                  "'chandrakalanadi' on archive.org."}))
        return 1

    total_chars = sum(len(t) for _, t in text_files)
    logger.info("Fetched %d files (~%d chars)", len(text_files), total_chars)

    if dry_run:
        print(json.dumps({"status": "dry_run_complete", "text_key": TEXT_KEY,
                          "files": len(text_files), "chars": total_chars}))
        return 0

    text_id = db_upsert_text(TEXT_METADATA)

    all_chunks: list[dict[str, Any]] = []
    global_idx = 0
    for i, (url, text) in enumerate(text_files):
        for c in chunk_text(text, max_tokens=500, overlap=80):
            all_chunks.append({
                "text_id": text_id, "chunk_index": global_idx,
                "chapter": f"File {i+1}", "verse_range": None,
                "content": c["content"], "language": "en"
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

    gcs_uri = None
    try:
        gcs_uri = gcs_upload_jsonl(all_chunks, GCS_PATH)
    except Exception as e:
        logger.warning("GCS upload failed: %s", e)

    embedding_pct = (embedded_count / len(all_chunks) * 100) if all_chunks else 0
    ac_pass = chunk_count >= CHUNK_THRESHOLD and embedding_pct >= EMBED_THRESHOLD
    summary = {
        "text_key": TEXT_KEY, "text_id": text_id,
        "files_fetched": len(text_files), "chunks_inserted": inserted,
        "chunk_count_in_db": chunk_count, "embeddings_ok": embedded_count,
        "embedding_pct": round(embedding_pct, 1), "gcs_uri": gcs_uri, "ac_pass": ac_pass
    }
    print(json.dumps(summary))
    logger.info("=== Chandra Kala Nadi Ingestion COMPLETE ===")
    if chunk_count < CHUNK_THRESHOLD:
        logger.warning("chunk_count %d < threshold %d", chunk_count, CHUNK_THRESHOLD)
        return 1
    if embedding_pct < EMBED_THRESHOLD:
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))
