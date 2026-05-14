#!/usr/bin/env python3
"""
ingest_kp_texts.py — Ingest KP Reader Vols 1-4 (K.S. Krishnamurti) into M8 corpus.
Tier 3. Source: archive.org kp-readers (verified 2026-05-14).
Target: ≥500 chunks combined, ≥95% embedded.
Uses the 4 KP Reader djvu.txt files (Vols 1-4 specifically).
"""

import argparse, json, logging, sys, time
from datetime import date
from pathlib import Path
from typing import Any
import requests

sys.path.insert(0, str(Path(__file__).parent))
from ingest_utils import (
    chunk_text, embed_batch,
    db_upsert_text, db_bulk_insert_chunks, db_update_embeddings, db_update_chunk_count,
    gcs_upload_jsonl,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s — %(message)s", stream=sys.stderr)
logger = logging.getLogger("ingest_kp_texts")

TEXT_KEY = "kp_texts"
TEXT_METADATA = {
    "text_key": TEXT_KEY, "title": "Krishnamurti Padhdhati (KP) Readers Vols 1-4",
    "author": "K.S. Krishnamurti", "tradition": "kp", "school": "kp", "tier": 3,
    "language_original": "english", "translation_author": "K.S. Krishnamurti (original)",
    "source_url": "https://archive.org/details/kp-readers",
    "procurement_date": str(date.today()),
}
GCS_PATH = "L8/classical_texts/tier3/kp_vols_chunks.jsonl"
CHUNK_THRESHOLD = 500
ARCHIVE_DOWNLOAD_BASE = "https://archive.org/download/"
HEADERS = {"User-Agent": "Mozilla/5.0 (MARSYS-JIS M8 academic ingestion; contact: mail.abhisek.mohanty@gmail.com)"}
REQUEST_DELAY = 0.5

# Verified 2026-05-14: kp-readers has KP Vol 1-4 djvu.txt files
KP_VOL_URLS = [
    f"{ARCHIVE_DOWNLOAD_BASE}kp-readers/J_KP reader_1_casting the horoscope_djvu.txt",
    f"{ARCHIVE_DOWNLOAD_BASE}kp-readers/J_KP reader_2_fundamental Principles of Astrology_djvu.txt",
    f"{ARCHIVE_DOWNLOAD_BASE}kp-readers/J_KP reader_3_Predictive Stellar Astrology_djvu.txt",
    f"{ARCHIVE_DOWNLOAD_BASE}kp-readers/J_KP reader_4_Marriage-married-Life-Children_djvu.txt",
]

FALLBACK_IDENTIFIERS = ["KPReadersVol1", "kp-readers-vol1", "KrishnamurtiPadhdhati"]


def fetch_url(url: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code in (403, 404):
                return None
        except requests.RequestException as e:
            logger.warning("Request error %s (attempt %d): %s", url, attempt + 1, e)
        time.sleep(REQUEST_DELAY * (attempt + 1))
    return None


def run(dry_run: bool = False) -> int:
    logger.info("=== KP Texts Ingestion START (dry_run=%s) ===", dry_run)

    text_files: list[tuple[str, str]] = []
    for vol_num, url in enumerate(KP_VOL_URLS, 1):
        logger.info("Fetching KP Vol %d: %s", vol_num, url.split("/")[-1][:40])
        text = fetch_url(url)
        if text and len(text) > 500:
            text_files.append((url, text))
            logger.info("Vol %d: %d chars", vol_num, len(text))
        else:
            logger.warning("Vol %d: not available or too small", vol_num)
        time.sleep(REQUEST_DELAY)

    if not text_files:
        # Fallback: try other identifiers
        import json as _json
        for ident in FALLBACK_IDENTIFIERS:
            meta = fetch_url(f"https://archive.org/metadata/{ident}")
            if not meta:
                continue
            try:
                files = _json.loads(meta).get("files", [])
                djvu = [f for f in files if f.get("name", "").endswith("_djvu.txt")]
                for f in djvu[:4]:
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
        logger.warning("KP texts not found — PROCUREMENT_GAP")
        print(json.dumps({"status": "PROCUREMENT_GAP", "text_key": TEXT_KEY}))
        return 1

    total_chars = sum(len(t) for _, t in text_files)
    logger.info("Fetched %d volumes (~%d chars)", len(text_files), total_chars)

    if dry_run:
        print(json.dumps({"status": "dry_run_complete", "text_key": TEXT_KEY, "vols": len(text_files), "chars": total_chars}))
        return 0

    text_id = db_upsert_text(TEXT_METADATA)

    all_chunks: list[dict[str, Any]] = []
    global_idx = 0
    for i, (url, text) in enumerate(text_files):
        for c in chunk_text(text, max_tokens=500, overlap=80):
            all_chunks.append({"text_id": text_id, "chunk_index": global_idx, "chapter": f"KP Vol. {i+1}", "verse_range": None, "content": c["content"], "language": "en"})
            global_idx += 1

    logger.info("Built %d chunks from %d volumes", len(all_chunks), len(text_files))
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
    summary = {"text_key": TEXT_KEY, "text_id": text_id, "vols_fetched": len(text_files), "chunks_inserted": inserted, "chunk_count_in_db": chunk_count, "embeddings_ok": embedded_count, "embedding_pct": round(embedding_pct, 1), "gcs_uri": gcs_uri, "ac_pass": chunk_count >= CHUNK_THRESHOLD and embedding_pct >= 95}
    print(json.dumps(summary))
    logger.info("=== KP Texts Ingestion COMPLETE ===")
    if chunk_count < CHUNK_THRESHOLD:
        logger.warning("chunk_count %d < %d", chunk_count, CHUNK_THRESHOLD)
        return 1
    if embedding_pct < 95:
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.exit(run(dry_run=args.dry_run))
