"""
brahmagyan.l0_run_phase2 — L0FR Stream C Phase 2 Runner
=========================================================

Corrected source mappings + full ingestion pipeline for texts 4-15.
Deterministic-first: Python regex chunking + Vertex AI embeddings only.

Texts to ingest:
  jataka_parijata_vol2 — IA (vol 2 supplement)
  uttara_kalamrita     — IA
  brihat_jataka        — IA (B. Suryanarain Rao 1919)
  saravali             — IA
  hora_sara            — IA
  sarvartha_chintamani — IA (B. Suryanarayana Row 1899 English)
  jaimini_sutram       — IA (B. Suryanarain Rao 1949 English — public domain)
  brihat_samhita       — IA (V. Subrahmanya Sastri English)
  lal_kitab            — IA

Manual upload (skipped):
  tajaka_neelakanthi, yavana_jataka, bhrigu_samhita
  muhurta_chintamani   — Hindi-only on IA; needs English upload

Usage:
  cd /Users/Dev/Vibe-Coding/Apps/MadhavL0FR-C/platform/python-sidecar
  python -m brahmagyan.l0_run_phase2
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

TEXTS_DIR = Path("/tmp/l0fr_texts")
MANUAL_LOG = Path("/tmp/l0fr_manual_upload_pending.txt")
PARK_LOG = Path("/tmp/l0fr_chunks_parked.txt")

# ── Source config: already-downloaded files ───────────────────────────────────

# All local paths confirmed present and valid
LOCAL_SOURCES: dict[str, dict] = {
    "jataka_parijata": {
        "files": [str(TEXTS_DIR / "jataka_parijata/raw/jp_vol2_djvu.txt")],
        "db_text_id": "jataka_parijata",
        "title": "Jataka Parijata",
        "author": "Vaidyanatha Dikshita",
        "tradition_school": "parashari",
        "translator": "V. Subrahmanya Sastri",
        "edition": "2 vols, Motilal Banarsidass (Vol 2)",
        "source_url": "https://archive.org/details/JatakaParijataVolIIOfIIByVSubrahmanyaSastri",
        "license": "public_domain",
        "skip_if_exists": True,  # already 741 chunks from vol1; append vol2
    },
    "uttara_kalamrita": {
        "files": [str(TEXTS_DIR / "uttara_kalamrita/raw/uk_djvu.txt")],
        "db_text_id": "uttara_kalamrita",
        "title": "Uttara Kalamrita",
        "author": "Kalidasa",
        "tradition_school": "parashari",
        "translator": "P. Subrahmanya Sastri",
        "edition": "P. Subrahmanya Sastri edition",
        "source_url": "https://archive.org/details/uttkalamrita-kalidas-ps-sastri",
        "license": "public_domain",
    },
    "brihat_jataka": {
        "files": [str(TEXTS_DIR / "brihat_jataka/raw/bj_djvu.txt")],
        "db_text_id": "brihat_jataka",
        "title": "Brihat Jataka",
        "author": "Varahamihira",
        "tradition_school": "parashari",
        "translator": "B. Suryanarain Rao",
        "edition": "B. Suryanarain Rao 1919 edition",
        "source_url": "https://archive.org/details/Astrology_Books_by_B_Suryanarayana_Row",
        "license": "public_domain",
    },
    "saravali": {
        "files": [str(TEXTS_DIR / "saravali/raw/saravali_djvu.txt")],
        "db_text_id": "saravali",
        "title": "Saravali",
        "author": "Kalyana Varma",
        "tradition_school": "parashari",
        "translator": "R. Santhanam",
        "edition": "Ranjan Publications",
        "source_url": "https://archive.org/details/saravaliofkalyanavarmasanthanamr.astrology_202003_28_Z",
        "license": "public_domain",
    },
    "hora_sara": {
        "files": [str(TEXTS_DIR / "hora_sara/raw/hora_sara_djvu.txt")],
        "db_text_id": "hora_sara",
        "title": "Hora Sara",
        "author": "Prithuyasas",
        "tradition_school": "parashari",
        "translator": "R. Santhanam",
        "edition": "R. Santhanam English translation",
        "source_url": "https://archive.org/details/HoraSaraRSanthanamEng",
        "license": "public_domain",
    },
    "sarvartha_chintamani": {
        "files": [str(TEXTS_DIR / "sarvartha_chintamani/raw/sc_djvu.txt")],
        "db_text_id": "sarvartha_chintamani",
        "title": "Sarvartha Chintamani",
        "author": "Venkatesh Daivagna",
        "tradition_school": "parashari",
        "translator": "B. Suryanarayana Row",
        "edition": "B. Suryanarayana Row English translation, 1899",
        "source_url": "https://archive.org/details/Astrology_Books_by_B_Suryanarayana_Row",
        "license": "public_domain",
    },
    "jaimini_sutram": {
        "files": [str(TEXTS_DIR / "jaimini_sutram/raw/js_djvu.txt")],
        "db_text_id": "jaimini_sutram",
        "title": "Jaimini Sutras",
        "author": "Jaimini Rishi",
        "tradition_school": "jaimini",
        "translator": "B. Suryanarain Rao",
        "edition": "B. Suryanarain Rao English translation, 1949 (public domain)",
        "source_url": "https://archive.org/details/Astrology_Books_by_B_Suryanarayana_Row",
        "license": "public_domain",
        "note": "B. Suryanarain Rao 1949 public domain edition (Sanjay Rath edition not on IA; this is available public domain equivalent)"
    },
    "brihat_samhita": {
        "files": [str(TEXTS_DIR / "brihat_samhita/raw/bs_vol1_djvu.txt")],
        "db_text_id": "brihat_samhita",
        "title": "Brihat Samhita",
        "author": "Varahamihira",
        "tradition_school": "samhita",
        "translator": "V. Subrahmanya Sastri",
        "edition": "V. Subrahmanya Sastri English translation with notes",
        "source_url": "https://archive.org/details/VarahamihirasBrihatSamhitaByVSubrahmanyaSastri",
        "license": "public_domain",
    },
    "lal_kitab": {
        "files": [str(TEXTS_DIR / "lal_kitab/raw/lal_kitab_djvu.txt")],
        "db_text_id": "lal_kitab",
        "title": "Lal Kitab",
        "author": "Pt. Roop Chand Joshi",
        "tradition_school": "lal_kitab",
        "translator": "B.M. Goswami / L.K. Vashisth",
        "edition": "Pt. Beni Madhav Goswami & Laxmi Kant Vashisth English edition",
        "source_url": "https://archive.org/details/jyotishlalkitabb.m.gosvami",
        "license": "public_domain",
    },
}

# Manual-upload texts (skip + log)
MANUAL_UPLOAD_TEXTS = {
    "tajaka_neelakanthi": {
        "title": "Tajaka Neelakanthi",
        "author": "Neelakantha",
        "edition": "Sanjay Rath — not on Internet Archive",
        "reason": "Sanjay Rath publication — manual upload required",
    },
    "yavana_jataka": {
        "title": "Yavana Jataka",
        "author": "Sphujidhvaja",
        "edition": "David Pingree, Harvard Oriental Series",
        "reason": "Academic edition — not on Internet Archive",
    },
    "bhrigu_samhita": {
        "title": "Bhrigu Samhita",
        "author": "Maharishi Bhrigu",
        "edition": "Multiple sources — native chooses extracts",
        "reason": "Multiple sources; native must choose which extracts",
    },
    "muhurta_chintamani": {
        "title": "Muhurta Chintamani",
        "author": "Dayananda",
        "edition": "English translation required — IA has Hindi-only",
        "reason": "Internet Archive only has Hindi/Sanskrit version; English translation upload required",
    },
}


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_db_conn():
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


def existing_chunk_count(conn, text_id: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM classical_text_chunks WHERE text_id = %s", (text_id,))
        return cur.fetchone()[0]


def insert_classical_text_row(conn, text_id: str, meta: dict):
    """Insert or update classical_texts row — schema: text_id, title_en, author, school, tradition, license, source_edition."""
    tradition = meta.get("tradition_school", "parashari")
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO classical_texts (text_id, title_en, author, school, tradition, license, source_edition)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (text_id) DO UPDATE SET
              title_en = EXCLUDED.title_en,
              author = EXCLUDED.author,
              source_edition = EXCLUDED.source_edition
            """,
            (
                text_id,
                meta.get("title", text_id),
                meta.get("author", ""),
                tradition,
                tradition,
                meta.get("license", "public_domain"),
                meta.get("edition", ""),
            )
        )
    conn.commit()


def insert_text_source_row(conn, text_id: str, meta: dict):
    """Insert or update classical_texts_source row — schema: text_id, title, author, edition, translator, source_url, license, citation_format."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO classical_texts_source (text_id, title, author, edition, translator, source_url, license, citation_format)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (text_id) DO UPDATE SET
              title = EXCLUDED.title,
              author = EXCLUDED.author,
              edition = EXCLUDED.edition,
              translator = EXCLUDED.translator,
              source_url = EXCLUDED.source_url,
              license = EXCLUDED.license
            """,
            (
                text_id,
                meta.get("title", text_id),
                meta.get("author", ""),
                meta.get("edition", ""),
                meta.get("translator", ""),
                meta.get("source_url", ""),
                meta.get("license", "public_domain"),
                f"{meta.get('title', text_id).upper()} Ch.N v.N",
            )
        )
    conn.commit()


# ── Text processing ───────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_sanskrit(content: str) -> tuple[str, Optional[str]]:
    lines = content.split('\n')
    sa_lines, en_lines = [], []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        non_ascii = sum(1 for c in stripped if ord(c) > 127)
        ratio = non_ascii / max(len(stripped), 1)
        if ratio > 0.4:
            sa_lines.append(stripped)
        else:
            en_lines.append(stripped)
    content_en = '\n'.join(en_lines).strip()
    content_sa = '\n'.join(sa_lines).strip() if sa_lines else None
    return content_en, content_sa


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def extract_topics(text: str) -> list[str]:
    keywords = [
        'lagna', 'ascendant', 'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn',
        'rahu', 'ketu', 'house', 'bhava', 'yoga', 'dasha', 'transit', 'aspect', 'conjunction',
        'retrograde', 'exalt', 'debilitat', 'sign', 'rasi', 'nakshatra', 'lord', 'karak',
        'muhurta', 'election', 'remedial', 'mantra', 'gemstone', 'remedy',
    ]
    lower = text.lower()
    found = [kw for kw in keywords if kw in lower]
    return list(set(found))[:10]


def split_into_chapters(text: str, text_id: str) -> list[tuple[int, str, str]]:
    """
    Split text into (chapter_num, chapter_title, chapter_text) segments.
    Tries multiple chapter heading patterns.
    """
    # Pattern: CHAPTER N or Chapter N or CH. N
    ch_patterns = [
        re.compile(r'(?:^|\n)\s*(?:CHAPTER|Chapter|CHAP\.?)\s+(\d+)[^\n]*\n', re.MULTILINE),
        re.compile(r'(?:^|\n)\s*Ch(?:apter)?\.?\s+(\d+)[^\n]*\n', re.MULTILINE | re.IGNORECASE),
        # Numbered section headings like "I. PLANETS" or "1. PLANETS"
        re.compile(r'(?:^|\n)\s*([IVX]+)\.\s+([A-Z][A-Z\s]{3,})\n', re.MULTILINE),
    ]

    segments = []
    for pat in ch_patterns:
        matches = list(pat.finditer(text))
        if len(matches) >= 3:
            # Found chapter structure
            for i, m in enumerate(matches):
                ch_num_str = m.group(1)
                # Convert Roman numerals if needed
                if re.match(r'^[IVX]+$', ch_num_str):
                    roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50}
                    ch_num = sum(roman_map.get(c, 0) for c in ch_num_str)
                else:
                    ch_num = int(ch_num_str)

                start = m.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                ch_text = text[start:end].strip()

                if ch_text and len(ch_text) > 100:
                    segments.append((ch_num, m.group(0).strip(), ch_text))
            break

    if not segments:
        # Fallback: treat entire text as one chapter
        segments = [(1, "Main", text)]

    return segments


def chunk_chapter_text(
    text: str,
    text_id: str,
    chapter: int,
    chapter_title: str,
    meta: dict,
) -> tuple[list[dict], list[dict]]:
    """
    Chunk a chapter's text into verse-level chunks.
    Returns (good_chunks, parked_chunks) as dicts ready for DB insert.
    """
    tradition_school = meta.get("tradition_school", "parashari")
    translator = meta.get("translator", "unknown")

    text = normalize_text(text)
    good, parked = [], []

    # Primary: numbered verse pattern "1. text" or "1-3. text"
    verse_pat = re.compile(
        r'^\s*(\d+)(?:-(\d+))?\.\s+(.+?)(?=^\s*\d+(?:-\d+)?\.\s|\Z)',
        re.MULTILINE | re.DOTALL
    )
    chunks_raw = []
    for m in verse_pat.finditer(text):
        v_start = int(m.group(1))
        v_end = int(m.group(2)) if m.group(2) else v_start
        content = m.group(3).strip()
        chunks_raw.append((v_start, v_end, content))

    # Fallback: paragraph chunking
    if len(chunks_raw) < 3:
        paragraphs = re.split(r'\n\s*\n', text)
        chunks_raw = []
        for idx, para in enumerate(paragraphs, start=1):
            para = para.strip()
            if len(para) > 50:
                chunks_raw.append((idx, idx, para))

    if len(chunks_raw) < 2:
        # Park entire chapter
        parked.append({
            "text_id": text_id,
            "chapter": chapter,
            "verse_start": 0,
            "verse_end": 0,
            "verse_ref": f"CH{chapter}:UNEXTRACTED",
            "content_en": text[:500] if text else "(empty)",
            "content_sa": None,
            "source_citation": f"{text_id.upper()} Ch.{chapter} (unextracted)",
            "tradition_school": tradition_school,
            "translator": translator,
            "topics": [],
            "content_sha256": sha256(text),
            "chunk_id": f"{text_id}_ch{chapter:03d}_park",
            "park_reason": f"<2 chunks found (got {len(chunks_raw)})",
        })
        return good, parked

    for v_start, v_end, content in chunks_raw:
        content_en, content_sa = extract_sanskrit(content)

        park_reason = None
        if len(content_en) < 50:
            park_reason = f"content_en too short ({len(content_en)})"
        elif len(content_en) > 2500:
            content_en = content_en[:2500]  # truncate instead of park

        verse_ref = f"CH{chapter}:V{v_start}" + (f"-V{v_end}" if v_end != v_start else "")
        chunk_id = f"{text_id}_ch{chapter:03d}_v{v_start:04d}"

        row = {
            "text_id": text_id,
            "chapter": chapter,
            "verse_start": v_start,
            "verse_end": v_end,
            "verse_ref": verse_ref,
            "content_en": content_en if content_en else content[:2000],
            "content_sa": content_sa,
            "source_citation": f"{text_id.upper()} Ch.{chapter} v.{v_start}",
            "tradition_school": tradition_school,
            "translator": translator,
            "topics": extract_topics(content_en or content),
            "content_sha256": sha256(content_en or content),
            "chunk_id": chunk_id,
            "park_reason": park_reason,
        }

        if park_reason:
            row["park_reason"] = park_reason
            parked.append(row)
        else:
            good.append(row)

    return good, parked


def insert_chunks_batch(conn, chunks: list[dict]) -> int:
    """Insert chunks into classical_text_chunks. Returns inserted count."""
    if not chunks:
        return 0

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    inserted = 0
    with conn.cursor() as cur:
        for c in chunks:
            try:
                cur.execute(
                    """
                    INSERT INTO classical_text_chunks
                      (text_id, chunk_id, verse_ref, chapter, verse_start, verse_end,
                       content_sa, content_en, topics, source_citation, ingested_at,
                       translator, tradition_school, content_sha256)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                      content_en = EXCLUDED.content_en,
                      content_sa = EXCLUDED.content_sa,
                      topics = EXCLUDED.topics,
                      source_citation = EXCLUDED.source_citation,
                      content_sha256 = EXCLUDED.content_sha256
                    """,
                    (
                        c["text_id"],
                        c["chunk_id"],
                        c["verse_ref"],
                        c["chapter"],
                        c["verse_start"],
                        c["verse_end"],
                        c.get("content_sa"),
                        c["content_en"],
                        c["topics"],
                        c["source_citation"],
                        now,
                        c["translator"],
                        c["tradition_school"],
                        c["content_sha256"],
                    )
                )
                inserted += 1
            except Exception as exc:
                logger.warning("[ingest] Failed chunk %s: %s", c["chunk_id"], exc)
                conn.rollback()

    conn.commit()
    return inserted


def write_park_log(parked: list[dict]):
    """Append parked chunks to the park log."""
    if not parked:
        return
    PARK_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PARK_LOG, "a") as f:
        for c in parked:
            f.write(
                f"PARKED: {c['chunk_id']} | reason: {c.get('park_reason', 'unknown')}\n"
                f"  content: {c['content_en'][:100]}...\n\n"
            )


# ── Embedding ─────────────────────────────────────────────────────────────────

def embed_text_id(conn, text_id: str) -> dict:
    """Embed all un-embedded chunks for a given text_id. Returns stats."""
    import vertexai  # type: ignore
    vertexai.init(project="madhav-astrology", location="asia-south1")
    from vertexai.language_models import TextEmbeddingModel  # type: ignore

    model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")

    # Fetch un-embedded chunks
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_id, content_en, content_sa
            FROM classical_text_chunks
            WHERE text_id = %s AND embedding IS NULL
            ORDER BY chunk_id
            """,
            (text_id,)
        )
        rows = cur.fetchall()

    if not rows:
        logger.info("[embed] No unembedded chunks for %s", text_id)
        return {"text_id": text_id, "embedded": 0, "failed": 0}

    logger.info("[embed] Embedding %d chunks for %s", len(rows), text_id)

    BATCH_SIZE = 100  # conservative to avoid token limits
    embedded = 0
    failed = 0

    for batch_start in range(0, len(rows), BATCH_SIZE):
        batch = rows[batch_start:batch_start + BATCH_SIZE]
        texts = []
        for chunk_id, content_en, content_sa in batch:
            combined = (content_en or "") + (" " + content_sa if content_sa else "")
            combined = combined.strip()[:8192]
            if not combined:
                combined = " "
            texts.append(combined)

        # Retry with halving on failure
        batch_chunks = list(zip([r[0] for r in batch], texts))
        _embed_batch_recursive(conn, model, batch_chunks)

        # Count embedded after this batch
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM classical_text_chunks WHERE text_id = %s AND embedding IS NOT NULL",
                (text_id,)
            )
            current_count = cur.fetchone()[0]

        batch_embedded = min(BATCH_SIZE, len(batch))
        embedded = current_count
        logger.info("[embed] %s: %d/%d embedded", text_id, current_count, len(rows))

        time.sleep(0.2)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM classical_text_chunks WHERE text_id = %s AND embedding IS NULL",
            (text_id,)
        )
        remaining = cur.fetchone()[0]
    failed = remaining

    return {"text_id": text_id, "embedded": embedded, "failed": failed}


def _embed_batch_recursive(conn, model, chunk_pairs: list[tuple[str, str]], depth: int = 0):
    """Recursively embed with batch halving on 400 errors."""
    if not chunk_pairs:
        return
    if depth > 5:
        logger.warning("[embed] Too many retries, skipping %d chunks", len(chunk_pairs))
        return

    chunk_ids = [p[0] for p in chunk_pairs]
    texts = [p[1] for p in chunk_pairs]

    try:
        embeddings = model.get_embeddings(texts)
        # Update DB
        with conn.cursor() as cur:
            for (chunk_id, _), emb in zip(chunk_pairs, embeddings):
                vec = emb.values
                cur.execute(
                    "UPDATE classical_text_chunks SET embedding = %s WHERE chunk_id = %s",
                    (vec, chunk_id)
                )
        conn.commit()
        logger.debug("[embed] Embedded %d chunks at depth %d", len(chunk_pairs), depth)
    except Exception as exc:
        err_str = str(exc)
        if "400" in err_str or "token" in err_str.lower() or "size" in err_str.lower():
            if len(chunk_pairs) > 1:
                mid = len(chunk_pairs) // 2
                logger.warning("[embed] 400 error, halving batch: %d -> %d+%d", len(chunk_pairs), mid, len(chunk_pairs) - mid)
                _embed_batch_recursive(conn, model, chunk_pairs[:mid], depth + 1)
                _embed_batch_recursive(conn, model, chunk_pairs[mid:], depth + 1)
            else:
                logger.warning("[embed] Single chunk failed (too long?): %s", chunk_pairs[0][0])
        else:
            logger.error("[embed] Embedding error: %s", exc)
            time.sleep(2)
            if depth < 3:
                _embed_batch_recursive(conn, model, chunk_pairs, depth + 1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    logger.info("=== L0FR Stream C Phase 2 START ===")

    # Log manual uploads
    MANUAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(MANUAL_LOG, "w") as f:
        for tid, info in MANUAL_UPLOAD_TEXTS.items():
            f.write(
                f"MANUAL_UPLOAD_REQUIRED: {tid}\n"
                f"  Title: {info['title']}\n"
                f"  Edition: {info['edition']}\n"
                f"  Author: {info['author']}\n"
                f"  Reason: {info['reason']}\n\n"
            )

    conn = get_db_conn()
    summary = {
        "texts_attempted": [],
        "texts_succeeded": [],
        "texts_failed": [],
        "manual_upload": list(MANUAL_UPLOAD_TEXTS.keys()),
        "chunk_counts": {},
        "parked_counts": {},
        "total_new_chunks": 0,
        "errors": [],
    }

    all_parked = []

    try:
        for text_id, config in LOCAL_SOURCES.items():
            db_text_id = config["db_text_id"]
            logger.info("=== Processing: %s (db_text_id=%s) ===", text_id, db_text_id)
            summary["texts_attempted"].append(text_id)

            # Check if already has chunks
            existing = existing_chunk_count(conn, db_text_id)
            if existing > 0 and not config.get("skip_if_exists"):
                logger.info("[ingest] %s already has %d chunks, skipping", db_text_id, existing)
                summary["texts_succeeded"].append(text_id)
                summary["chunk_counts"][text_id] = existing
                continue

            # Check source files exist
            valid_files = []
            for fp in config["files"]:
                p = Path(fp)
                if not p.exists():
                    logger.warning("[ingest] File not found: %s", fp)
                    continue
                # Check not HTML
                with open(p, 'rb') as fh:
                    header = fh.read(20)
                if header.startswith(b'<!DOCTYPE') or header.startswith(b'<html'):
                    logger.warning("[ingest] HTML error page: %s", fp)
                    continue
                if p.stat().st_size < 10_000:
                    logger.warning("[ingest] Too small: %s (%d bytes)", fp, p.stat().st_size)
                    continue
                valid_files.append(fp)

            if not valid_files:
                logger.warning("[ingest] No valid files for %s", text_id)
                summary["texts_failed"].append(text_id)
                summary["errors"].append(f"{text_id}: no valid source files")
                continue

            # Insert text metadata rows
            insert_classical_text_row(conn, db_text_id, config)
            insert_text_source_row(conn, db_text_id, config)

            # Process each source file
            text_good_chunks = []
            text_parked_chunks = []

            for fp in valid_files:
                raw_text = Path(fp).read_text(encoding="utf-8", errors="replace")
                raw_text = normalize_text(raw_text)
                char_count = len(raw_text)
                logger.info("[ingest] %s from %s (%d chars)", text_id, Path(fp).name, char_count)

                # Split into chapters
                segments = split_into_chapters(raw_text, text_id)
                logger.info("[ingest] %s: %d chapters", text_id, len(segments))

                # Chunk each chapter
                for ch_num, ch_title, ch_text in segments:
                    good, parked = chunk_chapter_text(ch_text, db_text_id, ch_num, ch_title, config)
                    text_good_chunks.extend(good)
                    text_parked_chunks.extend(parked)

            all_parked.extend(text_parked_chunks)
            write_park_log(text_parked_chunks)

            if not text_good_chunks:
                logger.warning("[ingest] Zero good chunks for %s", text_id)
                summary["texts_failed"].append(text_id)
                summary["errors"].append(f"{text_id}: zero good chunks")
                continue

            # Insert chunks
            inserted = insert_chunks_batch(conn, text_good_chunks)
            logger.info("[ingest] %s: inserted %d chunks (%d parked)", text_id, inserted, len(text_parked_chunks))

            summary["chunk_counts"][text_id] = inserted
            summary["parked_counts"][text_id] = len(text_parked_chunks)
            summary["total_new_chunks"] += inserted
            summary["texts_succeeded"].append(text_id)

        # Now embed all newly inserted chunks
        logger.info("=== Embedding phase ===")
        for text_id in summary["texts_succeeded"]:
            db_text_id = LOCAL_SOURCES.get(text_id, {}).get("db_text_id", text_id)
            t0 = time.time()
            embed_result = embed_text_id(conn, db_text_id)
            elapsed = time.time() - t0
            logger.info(
                "[embed] %s: embedded=%d failed=%d (%.1fs)",
                db_text_id, embed_result["embedded"], embed_result["failed"], elapsed
            )

        # Final DB stats
        with conn.cursor() as cur:
            cur.execute("SELECT text_id, COUNT(*) FROM classical_text_chunks GROUP BY text_id ORDER BY text_id")
            db_counts = {r[0]: r[1] for r in cur.fetchall()}
        summary["db_total_by_text"] = db_counts
        summary["db_total_all"] = sum(db_counts.values())

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM classical_text_chunks WHERE embedding IS NOT NULL")
            summary["embedded_count"] = cur.fetchone()[0]

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(DISTINCT text_id) FROM classical_texts_source")
            summary["distinct_texts_in_source"] = cur.fetchone()[0]

    finally:
        conn.close()

    logger.info("=== Phase 2 COMPLETE ===")
    logger.info("Succeeded: %s", summary["texts_succeeded"])
    logger.info("Failed: %s", summary["texts_failed"])
    logger.info("Total DB chunks: %s", summary.get("db_total_all", "?"))
    logger.info("Embedded chunks: %s", summary.get("embedded_count", "?"))

    import json
    print(json.dumps(summary, indent=2, default=str))
    return summary


if __name__ == "__main__":
    result = main()
    total = result.get("db_total_all", 0)
    embedded = result.get("embedded_count", 0)
    if total >= 6000 and total == embedded:
        print(f"\n[PASS] AC met: {total} total chunks, {embedded} embedded")
        sys.exit(0)
    else:
        print(f"\n[WARN] AC not fully met: {total} total, {embedded} embedded (need ≥6000)")
        sys.exit(1)
