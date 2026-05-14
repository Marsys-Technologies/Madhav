#!/usr/bin/env python3
"""
ingest_prashna_marga.py — Ingest Prashna Marga (Narayanan Namboodiri, B.V. Raman trans.)
Tier 3. Source: archive.org PrasnaMargaBVR (2 vols).
Target: ≥300 chunks, ≥95% embedded.
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
logger = logging.getLogger("ingest_prashna_marga")

TEXT_KEY = "prashna_marga"
TEXT_METADATA = {
    "text_key": TEXT_KEY, "title": "Prashna Marga", "author": "Narayanan Namboodiri",
    "tradition": "parashari", "school": "parashari", "tier": 3,
    "language_original": "sanskrit", "translation_author": "B.V. Raman",
    "source_url": "https://archive.org/details/PrasnaMargaBVR",
    "procurement_date": str(date.today()),
}
GCS_PATH = "L8/classical_texts/tier3/prashna_marga_chunks.jsonl"
CHUNK_THRESHOLD = 300
ARCHIVE_DOWNLOAD_BASE = "https://archive.org/download/"
HEADERS = {"User-Agent": "Mozilla/5.0 (MARSYS-JIS M8 academic ingestion; contact: mail.abhisek.mohanty@gmail.com)"}
REQUEST_DELAY = 0.5

# Verified 2026-05-14: PrasnaMargaBVR has 2 djvu.txt volumes (~625KB + ~562KB)
SOURCE_URLS = [
    f"{ARCHIVE_DOWNLOAD_BASE}PrasnaMargaBVR/Prasna Marga 1_djvu.txt",
    f"{ARCHIVE_DOWNLOAD_BASE}PrasnaMargaBVR/Prasna Marga 2_djvu.txt",
]

FALLBACK_IDENTIFIERS = ["prashna-marga-bv-raman", "PrashnaMarga", "prashna_marga"]


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


def run(dry_run: bool = False) -> int:
    logger.info("=== Prashna Marga Ingestion START (dry_run=%s) ===", dry_run)

    text_files: list[tuple[str, str]] = []
    for url in SOURCE_URLS:
        text = fetch_url(url)
        if text and len(text) > 500:
            text_files.append((url, text))
        time.sleep(REQUEST_DELAY)

    if not text_files:
        # Try fallback identifiers
        import json as _json
        for ident in FALLBACK_IDENTIFIERS:
            meta = fetch_url(f"https://archive.org/metadata/{ident}")
            if not meta:
                continue
            try:
                files = _json.loads(meta).get("files", [])
                djvu = [f for f in files if f.get("name", "").endswith("_djvu.txt")]
                for f in djvu[:3]:
                    url = f"{ARCHIVE_DOWNLOAD_BASE}{ident}/{f['name']}"
                    text = fetch_url(url)
                    if text and len(text) > 500:
                        text_files.append((url, text))
                    time.sleep(REQUEST_DELAY)
                if text_files:
                    break
            except Exception:
                pass

    if not text_files:
        logger.warning("Prashna Marga not found — PROCUREMENT_GAP")
        print(json.dumps({"status": "PROCUREMENT_GAP", "text_key": TEXT_KEY}))
        return 1

    total_chars = sum(len(t) for _, t in text_files)
    logger.info("Fetched %d files (~%d chars)", len(text_files), total_chars)

    if dry_run:
        print(json.dumps({"status": "dry_run_complete", "text_key": TEXT_KEY, "files": len(text_files), "chars": total_chars}))
        return 0

    text_id = db_upsert_text(TEXT_METADATA)

    all_chunks: list[dict[str, Any]] = []
    global_idx = 0
    for i, (url, text) in enumerate(text_files):
        for c in chunk_text(text, max_tokens=500, overlap=80):
            all_chunks.append({"text_id": text_id, "chunk_index": global_idx, "chapter": f"Vol. {i+1}", "verse_range": None, "content": c["content"], "language": "en"})
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
    summary = {"text_key": TEXT_KEY, "text_id": text_id, "files_fetched": len(text_files), "chunks_inserted": inserted, "chunk_count_in_db": chunk_count, "embeddings_ok": embedded_count, "embedding_pct": round(embedding_pct, 1), "gcs_uri": gcs_uri, "ac_pass": chunk_count >= CHUNK_THRESHOLD and embedding_pct >= 95}
    print(json.dumps(summary))
    logger.info("=== Prashna Marga Ingestion COMPLETE ===")
    if chunk_count < CHUNK_THRESHOLD:
        logger.warning("chunk_count %d < %d threshold", chunk_count, CHUNK_THRESHOLD)
        return 1
    if embedding_pct < 95:
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))
