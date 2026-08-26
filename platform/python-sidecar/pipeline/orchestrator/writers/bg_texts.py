"""
bg_texts writer — classical text corpus PDF→chunk→embed pipeline.

Implements CLAUDECODE_BRIEF_BG_TEXTS_v1_0.md §4 (Doc 6 of 15).
Clear-and-rebuild from GCS PDFs. ZERO LLM — embeddings only via Vertex AI.

Embedding model (pinned): text-multilingual-embedding-002 (768-dim)
Endpoint: projects/madhav-astrology/locations/asia-south1/publishers/google/models/text-multilingual-embedding-002@default
SDK: google-genai 2.7.0 (replaces deprecated vertexai.language_models.TextEmbeddingModel)

BRAHMA-BG-0-3 | L0 Brahmagyan Build — bg_texts asset (Doc 6 of 15)
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_texts import TEXTS

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
EMBED_MODEL = "text-multilingual-embedding-002"
EMBED_BATCH_SIZE = 20        # conservative; Vertex AI accepts up to 250 inputs
CHUNK_MAX_CHARS = 1_500      # ~300 words; well within model 2048-token limit
MIN_CHUNK_CHARS = 50         # discard near-empty chunks (headers, page artifacts)
SMALLINT_MAX = 32_767        # PostgreSQL SMALLINT ceiling

# Immutable accepted corpus distribution from migration 610. Additive mode may
# create an absent text, but an already-present canonical text must match this
# reviewed row count exactly; otherwise skipping it would turn partial data into
# a false-success build.
ACCEPTED_CHUNK_COUNTS_BY_TEXT: dict[str, int] = {
    "bhrigu_nandi_nadi": 608,
    "bphs": 1459,
    "bphs_jaimini": 264,
    "brihat_jataka": 607,
    "brihat_samhita": 1171,
    "hora_sara": 460,
    "jataka_parijata": 704,
    "muhurta_chintamani": 274,
    "nadi_navamsa_patel": 1850,
    "phaladeepika": 564,
    "saravali": 471,
    "sarvartha_chintamani": 342,
    "tajaka_neelakanthi": 290,
    "uttara_kalamrita": 289,
    "yavana_jataka": 1298,
}

GCP_PROJECT = os.environ.get("GCP_PROJECT", "madhav-astrology")
VERTEX_LOCATION = os.environ.get("VERTEX_AI_LOCATION", "asia-south1")

# sarvartha_chintamani: image-only PDF → use the reviewed GCS snapshot of the
# Archive.org DjVu OCR extract. Never fetch mutable upstream content at build time.
_SARVARTHA_DJVU_GCS_PATH = (
    "gs://madhav-marsys-sources/L8/classical_texts/source/"
    "sarvartha_chintamani_djvu.txt"
)

# nadi_navamsa_patel: use pre-extracted DjVu .txt from GCS (cleaner than PDF OCR)
_PATEL_DJVU_GCS_PATH = (
    "gs://madhav-marsys-sources/L8/classical_texts/source/nadi_navamsa_patel_djvu.txt"
)

_SOURCE_MANIFEST_PATH = (
    Path(__file__).resolve().parents[3]
    / "brahmagyan"
    / "bg_texts_source_manifest_v1.json"
)
_SOURCE_MANIFEST_SHA256 = (
    "bfcf536e16fb219d5f6faf1f01b6bd6a3a89830a96c997afb71d46eff32d1c36"
)


def _load_source_manifest(path: Path = _SOURCE_MANIFEST_PATH) -> dict[str, Any]:
    """Load the governed manifest only when its exact bytes are reviewed."""
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != _SOURCE_MANIFEST_SHA256:
        raise ValueError(
            "bg_texts source manifest SHA-256 mismatch: "
            f"expected {_SOURCE_MANIFEST_SHA256}, observed {actual}"
        )
    return json.loads(raw)


SOURCE_MANIFEST: dict[str, Any] = _load_source_manifest()
_SOURCE_OBJECTS = {item["gcs_path"]: item for item in SOURCE_MANIFEST["objects"]}

# bhrigu_nandi_nadi: regex to strip chart-diagram label fragments
# e.g. "Sat.", "Ven.", "Dh.", "Dt.", "Ma.", "Mo." appearing as isolated tokens
_BNN_CHART_LABELS_RE = re.compile(
    r"\b(Sat|Ven|Mar|Dh|Dt|Mo|Su|Ju|Me|Ra|Ke)\.\s*"
)

# ── google-genai embedding client ─────────────────────────────────────────────

# L-3: double-checked locking for thread-safe singleton init. The outer
# `if _genai_client is not None` fast-path avoids lock contention once the
# client is initialised; the inner check inside the lock prevents a second
# initialisation when two threads race through the outer check simultaneously.
_genai_client_lock = threading.Lock()
_genai_client: Any = None


def _get_genai_client() -> Any:
    global _genai_client
    if _genai_client is not None:
        return _genai_client
    with _genai_client_lock:
        if _genai_client is None:
            from google import genai  # type: ignore[import]
            _genai_client = genai.Client(
                vertexai=True,
                project=GCP_PROJECT,
                location=VERTEX_LOCATION,
            )
            logger.info(
                "[bg_texts] genai client init: project=%s location=%s model=%s",
                GCP_PROJECT, VERTEX_LOCATION, EMBED_MODEL,
            )
        return _genai_client


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns list of 768-dim float vectors."""
    client = _get_genai_client()
    resp = client.models.embed_content(model=EMBED_MODEL, contents=texts)
    return [list(e.values) for e in resp.embeddings]


# ── GCS download ──────────────────────────────────────────────────────────────

def _source_object(gcs_path: str) -> dict[str, Any]:
    """Return one reviewed immutable source object or reject the build."""
    source = _SOURCE_OBJECTS.get(gcs_path)
    if source is None:
        raise ValueError(f"bg_texts source path is not pinned: {gcs_path}")
    return source


def _verify_source_bytes(data: bytes, source: dict[str, Any]) -> None:
    """Fail closed when downloaded bytes differ from the reviewed manifest."""
    actual = base64.b64encode(hashlib.md5(data).digest()).decode("ascii")
    if actual != source["md5_base64"]:
        raise ValueError(
            f"bg_texts source MD5 mismatch for {source['gcs_path']}: "
            f"expected {source['md5_base64']}, observed {actual}"
        )


def _download_gcs(gcs_path: str) -> bytes | None:
    """Download the exact reviewed GCS generation and verify its content hash."""
    source = _source_object(gcs_path)
    generation = int(source["generation"])
    try:
        from google.cloud import storage  # type: ignore[import]
        parts = gcs_path.removeprefix("gs://").split("/", 1)
        bucket_name, blob_path = parts[0], parts[1]
        client = storage.Client(project=GCP_PROJECT)
        blob = client.bucket(bucket_name).blob(blob_path, generation=generation)
        if not blob.exists():
            return None
        data = blob.download_as_bytes(if_generation_match=generation)
    except Exception as exc:
        logger.error("[bg_texts] GCS download failed %s: %s", gcs_path, exc)
        return None
    _verify_source_bytes(data, source)
    return data


# ── PDF text extraction ───────────────────────────────────────────────────────

def _extract_pages(pdf_bytes: bytes) -> list[str]:
    """
    Extract text per page via PyMuPDF. Handles Unicode/Devanagari text layers.
    Returns list[str] — one entry per page (may be empty for image-only pages).
    """
    import fitz  # PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = [page.get_text().strip() for page in doc]
    doc.close()
    return pages


def _is_image_only(pages: list[str], sample_n: int = 10) -> bool:
    """True if the PDF has no usable text layer (image-only scan)."""
    return sum(len(p) for p in pages[:sample_n]) < 100


def _devanagari_ratio(pages: list[str], sample_n: int = 20) -> float:
    """Fraction of chars in U+0900–U+097F (Devanagari block) across a sample."""
    sample = " ".join(pages[:sample_n])
    if not sample:
        return 0.0
    deva = sum(1 for c in sample if "ऀ" <= c <= "ॿ")
    return deva / len(sample)


# ── sarvartha DjVu OCR ────────────────────────────────────────────────────────

def _fetch_sarvartha_djvu() -> str | None:
    """
    Download the pinned sarvartha_chintamani DjVu OCR snapshot from GCS.
    Returns cleaned text, or None on failure.
    """
    try:
        raw_bytes = _download_gcs(_SARVARTHA_DJVU_GCS_PATH)
        if not raw_bytes:
            return None
        raw = raw_bytes.decode("utf-8", errors="replace")
        # DjVu format: form-feeds (\x0c) separate pages; strip noise lines
        cleaned = raw.replace("\x0c", "\n\n")
        lines = []
        for ln in cleaned.split("\n"):
            s = ln.strip()
            # Drop lines that are mostly OCR box chars or too short
            if len(s) >= 4 and not all(c in "■□▪▫●○◆◇▸▹►▻" for c in s):
                lines.append(s)
        return "\n".join(lines)
    except Exception as exc:
        logger.warning("[bg_texts] sarvartha DjVu fetch failed: %s", exc)
        return None


def _fetch_patel_djvu_from_gcs() -> str | None:
    """
    Download the nadi_navamsa_patel DjVu OCR text from GCS.
    Applies verse-fragment filtering: lines where >30% chars are non-ASCII
    are excluded (they are garbled Devanagari verse-lines from inline Sanskrit).
    Returns cleaned text, or None on failure.
    """
    raw_bytes = _download_gcs(_PATEL_DJVU_GCS_PATH)
    if not raw_bytes:
        logger.warning("[bg_texts] nadi_navamsa_patel DjVu .txt absent in GCS")
        return None

    raw = raw_bytes.decode("utf-8", errors="replace")
    # DjVu format: form-feeds (\x0c) separate pages
    cleaned = raw.replace("\x0c", "\n\n")

    filtered_lines: list[str] = []
    verse_fragment_count = 0
    for ln in cleaned.split("\n"):
        s = ln.strip()
        if not s:
            filtered_lines.append("")
            continue
        # Verse-fragment filter: exclude lines where >30% chars are non-ASCII
        non_ascii = sum(1 for c in s if ord(c) > 127)
        if len(s) > 0 and non_ascii / len(s) > 0.30:
            verse_fragment_count += 1
            continue  # exclude — garbled Sanskrit verse, don't embed
        filtered_lines.append(s)

    result = "\n".join(filtered_lines)
    logger.info(
        "[bg_texts] nadi_navamsa_patel DjVu: %d chars after filtering; "
        "verse_fragments_excluded=%d",
        len(result), verse_fragment_count,
    )
    return result if len(result) >= 5_000 else None


# ── Chunking ──────────────────────────────────────────────────────────────────

def _chunk_text(text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    """
    Split text into semantic chunks ≤ max_chars, preferring paragraph breaks.
    Returns list of strings, each ≥ MIN_CHUNK_CHARS.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = (current + "\n\n" + para).strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) > max_chars:
                # Hard-split oversized paragraphs at line boundaries
                cur = ""
                for ln in para.split("\n"):
                    ln = ln.strip()
                    if not ln:
                        continue
                    if len(cur) + len(ln) + 1 <= max_chars:
                        cur = (cur + "\n" + ln).strip() if cur else ln
                    else:
                        if cur:
                            chunks.append(cur)
                        # If a single line still exceeds max, hard-split at chars
                        while len(ln) > max_chars:
                            chunks.append(ln[:max_chars])
                            ln = ln[max_chars:]
                        cur = ln
                if cur:
                    chunks.append(cur)
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) >= MIN_CHUNK_CHARS]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sha256(text_id: str, content: str) -> str:
    return hashlib.sha256(f"{text_id}::{content}".encode()).hexdigest()


def _chunk_id(text_id: str, page: int, idx: int) -> str:
    return f"{text_id}_pg{page:04d}_c{idx:02d}"


def _verse_ref(page: int, idx: int) -> str:
    return f"PG{page}:C{idx}"


def _source_citation(text: dict, page: int) -> str:
    """
    Build source_citation with [HIGH|MEDIUM|LOW] prefix + page location.
    Strips any existing tier prefix to avoid double-prefix.
    """
    tier = text.get("provenance_tier", "MEDIUM")
    base = text.get("source_citation", text.get("title_en", text["text_id"]))
    base = re.sub(r"^\[(HIGH|MEDIUM|LOW|MARGINAL)\]\s*", "", base)
    return f"[{tier}] {base} | PG{page}"


def _vec_str(vec: list[float]) -> str:
    """Format 768-dim float list as pgvector literal: '[0.123,...]'"""
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"


def _upsert_text_metadata(conn: Any, text: dict[str, Any]) -> None:
    """Converge the canonical registry metadata without refreshing chunk provenance."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO classical_texts
              (text_id, title_en, title_sa, author, school, tradition, tier,
               license, license_cleared, total_chapters, total_verses,
               source_edition, ingested_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (text_id) DO UPDATE SET
              title_en        = EXCLUDED.title_en,
              title_sa        = EXCLUDED.title_sa,
              author          = EXCLUDED.author,
              school          = EXCLUDED.school,
              tradition       = EXCLUDED.tradition,
              tier            = EXCLUDED.tier,
              license         = EXCLUDED.license,
              license_cleared = EXCLUDED.license_cleared,
              total_chapters  = EXCLUDED.total_chapters,
              total_verses    = EXCLUDED.total_verses,
              source_edition  = EXCLUDED.source_edition
            """,
            (
                text["text_id"], text["title_en"], text.get("title_sa"),
                text.get("author"), text["school"], text["tradition"],
                text["tier"], text["license"], text.get("license_cleared", True),
                text.get("total_chapters"), text.get("total_verses"),
                text.get("source_edition"), datetime.now(timezone.utc),
            ),
        )


def _validate_rebuild_mode(raw_mode: object) -> str:
    """Permit only non-destructive text maintenance until staged swap exists."""
    if raw_mode == "full":
        raise ValueError(
            "bg_texts full rebuild is quarantined until per-text staged verification "
            "and atomic selective replacement exist"
        )
    if raw_mode not in {"additive", "metadata_only"}:
        raise ValueError(f"bg_texts unsupported rebuild_mode: {raw_mode!r}")
    return str(raw_mode)


# ── Main writer ───────────────────────────────────────────────────────────────

@register("bg_texts")
class TextsWriter(WriterBase):
    asset_id = "bg_texts"

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"dry_run=True; would ingest {len(TEXTS)} texts from GCS PDFs",
            )

        # ── Step 0: Non-destructive mode + registry cleanup ──────────────────
        # additive (default): insert only texts with no chunks.
        # metadata_only: converge the 15 canonical registry rows and stop.
        # full: quarantined because delete-first can destroy healthy chunks when
        # a later source/extraction step is conditional. A staged per-text swap
        # is required before that mode may return.
        rebuild_mode = _validate_rebuild_mode(
            ctx.config.get("rebuild_mode", "additive")
        )
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM classical_text_chunks")
            pre_count = cur.fetchone()["n"]
            logger.info(
                "[bg_texts] %s mode: %d existing chunks preserved",
                rebuild_mode,
                pre_count,
            )

            cur.execute("DELETE FROM classical_texts WHERE text_id = 'lal_kitab'")
            if cur.rowcount:
                logger.info("[bg_texts] removed lal_kitab from classical_texts (DROPPED corpus text)")

        # ── Step 1: Upsert classical_texts registry rows ──────────────────────
        for text in TEXTS:
            _upsert_text_metadata(conn, text)
        logger.info("[bg_texts] upserted %d classical_texts registry rows", len(TEXTS))

        if rebuild_mode == "metadata_only":
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                duration_seconds=time.time() - t0,
                notes=(
                    f"metadata_only: converged {len(TEXTS)} canonical text rows; "
                    f"preserved {pre_count} existing chunks"
                ),
            )

        # ── Steps 2–6: Per-text PDF→extract→chunk→embed→insert ───────────────
        total_chunks = 0
        conditional: list[str] = []
        per_text_counts: dict[str, int] = {}

        # Pre-build exact per-text counts so a partially surviving text cannot
        # be mistaken for a complete text merely because one row exists.
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT text_id, count(*) AS row_count
                FROM classical_text_chunks
                GROUP BY text_id
                """
            )
            existing_counts = {
                row["text_id"]: int(row["row_count"]) for row in cur.fetchall()
            }
        canonical_ids = {text["text_id"] for text in TEXTS}
        unknown_ids = sorted(set(existing_counts) - canonical_ids)
        if unknown_ids:
            raise RuntimeError(
                "bg_texts found non-canonical chunk owners and refuses destructive cleanup: "
                + ", ".join(unknown_ids)
            )
        logger.info(
            "[bg_texts] additive mode: %d text_ids already have chunks → will skip them",
            len(existing_counts),
        )

        for text in TEXTS:
            text_id = text["text_id"]
            is_hindi = text.get("language_available", "en") == "sa+hi"
            gcs_paths = [text["gcs_path"]]
            if text.get("gcs_path_vol2"):
                gcs_paths.append(text["gcs_path_vol2"])

            # ── 2a-pre. Additive skip: skip texts already present in DB ───────
            existing_n = existing_counts.get(text_id, 0)
            if rebuild_mode == "additive" and existing_n:
                expected_n = ACCEPTED_CHUNK_COUNTS_BY_TEXT.get(text_id)
                if expected_n is None or existing_n != expected_n:
                    raise RuntimeError(
                        "bg_texts partial canonical text cannot be skipped safely: "
                        f"{text_id} has {existing_n} chunks; accepted count is {expected_n}"
                    )
                logger.info(
                    "[bg_texts] additive: skipping %s (%d chunks already present)",
                    text_id, existing_n,
                )
                per_text_counts[text_id] = existing_n
                continue

            # ── 2a. Download PDF(s) from GCS ─────────────────────────────────
            vol_pages: list[tuple[int, list[str]]] = []  # (vol_num, page_texts)
            skip_text = False

            for vol_idx, gcs_path in enumerate(gcs_paths, start=1):
                pdf_bytes = _download_gcs(gcs_path)
                if pdf_bytes is None:
                    logger.warning(
                        "[bg_texts] %s vol%d: GCS object absent (%s) — AWAITING_MANUAL_UPLOAD",
                        text_id, vol_idx, gcs_path,
                    )
                    conditional.append(f"AWAITING_MANUAL_UPLOAD:{text_id}")
                    skip_text = True
                    break
                pages = _extract_pages(pdf_bytes)
                vol_pages.append((vol_idx, pages))

            if skip_text:
                per_text_counts[text_id] = 0
                continue

            # ── 2b. Merge volumes with page offset ────────────────────────────
            # Page numbers are globally unique across volumes to avoid chunk_id collision.
            merged: list[tuple[int, int, str]] = []  # (global_page, vol_num, text)
            offset = 0
            for vol_num, pages in vol_pages:
                for pg_idx, page_text in enumerate(pages, start=1):
                    merged.append((offset + pg_idx, vol_num, page_text))
                offset += len(pages)

            # ── 2c. Special handling: sarvartha_chintamani (image-only) ───────
            if text_id == "sarvartha_chintamani":
                sample_pages = [pt for _, _, pt in merged[:10]]
                if _is_image_only(sample_pages):
                    logger.info(
                        "[bg_texts] sarvartha_chintamani: image-only PDF — fetching DjVu OCR"
                    )
                    djvu_text = _fetch_sarvartha_djvu()
                    if not djvu_text or len(djvu_text) < 5_000:
                        logger.warning(
                            "[bg_texts] sarvartha DjVu OCR unavailable/too short — AWAITING_OCR"
                        )
                        conditional.append("AWAITING_OCR:sarvartha_chintamani")
                        per_text_counts[text_id] = 0
                        continue
                    # Replace merged with DjVu virtual pages (split at triple newlines)
                    segments = [s.strip() for s in djvu_text.split("\n\n\n") if s.strip()]
                    merged = [(i + 1, 1, seg) for i, seg in enumerate(segments)]
                    logger.info(
                        "[bg_texts] sarvartha DjVu OCR: %d segments, %d chars",
                        len(merged), len(djvu_text),
                    )

            # ── 2c2. nadi_navamsa_patel: use DjVu .txt (verse-fragment filtered) ──
            if text_id == "nadi_navamsa_patel":
                logger.info(
                    "[bg_texts] nadi_navamsa_patel: fetching DjVu .txt from GCS "
                    "(preferred over PDF OCR; verse-fragment filter applied)"
                )
                djvu_text = _fetch_patel_djvu_from_gcs()
                if not djvu_text or len(djvu_text) < 5_000:
                    logger.warning(
                        "[bg_texts] nadi_navamsa_patel DjVu .txt unavailable/too short — "
                        "falling back to PDF extraction"
                    )
                    # Fall through — use the PDF pages already in `merged`
                else:
                    # Replace merged with DjVu virtual pages
                    segments = [s.strip() for s in djvu_text.split("\n\n\n") if s.strip()]
                    if not segments:
                        segments = [s.strip() for s in djvu_text.split("\n\n") if s.strip()]
                    merged = [(i + 1, 1, seg) for i, seg in enumerate(segments)]
                    logger.info(
                        "[bg_texts] nadi_navamsa_patel DjVu: %d segments replacing PDF pages",
                        len(merged),
                    )

            # ── 2d. Hindi OCR quality gate (muhurta + tajaka) ─────────────────
            if is_hindi:
                sample_texts = [pt for _, _, pt in merged[:20]]
                ratio = _devanagari_ratio(sample_texts)
                logger.info(
                    "[bg_texts] %s Hindi OCR gate: Devanagari ratio = %.3f", text_id, ratio
                )
                if ratio < 0.05:
                    logger.warning(
                        "[bg_texts] %s Devanagari ratio %.3f < 0.05 — AWAITING_NATIVE_DECISION",
                        text_id, ratio,
                    )
                    conditional.append(f"AWAITING_NATIVE_DECISION:{text_id}")
                    per_text_counts[text_id] = 0
                    continue

            # ── 3. Build chunk records ─────────────────────────────────────────
            chunk_records: list[dict] = []
            for global_page, vol_num, page_text in merged:
                if len(page_text) < MIN_CHUNK_CHARS:
                    continue
                # Strip bhrigu_nandi_nadi chart-diagram label fragments before chunking
                if text_id == "bhrigu_nandi_nadi":
                    page_text = _BNN_CHART_LABELS_RE.sub(" ", page_text)
                sub_chunks = _chunk_text(page_text)
                for c_idx, sub_text in enumerate(sub_chunks, start=1):
                    # For Devanagari texts: content_en = Devanagari text (NOT NULL constraint);
                    # content_sa also set so downstream can distinguish.
                    if is_hindi:
                        content_en = sub_text
                        content_sa = sub_text
                    else:
                        content_en = sub_text
                        content_sa = None

                    chunk_records.append({
                        "text_id":          text_id,
                        "chunk_id":         _chunk_id(text_id, global_page, c_idx),
                        "verse_ref":        _verse_ref(global_page, c_idx),
                        "chapter":          min(global_page, SMALLINT_MAX),
                        "verse_start":      min(c_idx, SMALLINT_MAX),
                        "verse_end":        min(c_idx, SMALLINT_MAX),
                        "content_en":       content_en,
                        "content_sa":       content_sa,
                        "source_citation":  _source_citation(text, global_page),
                        "content_sha256":   _sha256(text_id, sub_text),
                        "translator":       text.get("source_edition", ""),
                        "tradition_school": f"{text.get('tradition','')}:{text.get('school','')}",
                        "source_volume":    vol_num,
                    })

            if not chunk_records:
                logger.warning("[bg_texts] %s: no chunks extracted — skipping", text_id)
                conditional.append(f"NO_CHUNKS:{text_id}")
                per_text_counts[text_id] = 0
                continue

            logger.info(
                "[bg_texts] %s: %d chunks built, embedding in batches of %d...",
                text_id, len(chunk_records), EMBED_BATCH_SIZE,
            )

            # ── 4. Batch embed ─────────────────────────────────────────────────
            embed_texts = [r["content_en"] for r in chunk_records]
            embeddings: list[list[float]] = []
            for i in range(0, len(embed_texts), EMBED_BATCH_SIZE):
                batch = embed_texts[i : i + EMBED_BATCH_SIZE]
                vecs = _embed_batch(batch)  # raises on API error — HALT is correct
                embeddings.extend(vecs)
                if (i // EMBED_BATCH_SIZE) % 10 == 0:
                    logger.info(
                        "[bg_texts] %s: embedded %d/%d chunks",
                        text_id, min(i + EMBED_BATCH_SIZE, len(embed_texts)), len(embed_texts),
                    )

            # ── 5. Insert ──────────────────────────────────────────────────────
            inserted = 0
            with conn.cursor() as cur:
                for record, emb in zip(chunk_records, embeddings):
                    cur.execute(
                        """
                        INSERT INTO classical_text_chunks
                          (text_id, chunk_id, verse_ref, chapter, verse_start, verse_end,
                           content_sa, content_en, source_citation, content_sha256,
                           translator, tradition_school, embedding, ingested_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector,%s)
                        ON CONFLICT (chunk_id) DO NOTHING
                        """,
                        (
                            record["text_id"], record["chunk_id"], record["verse_ref"],
                            record["chapter"], record["verse_start"], record["verse_end"],
                            record["content_sa"], record["content_en"],
                            record["source_citation"], record["content_sha256"],
                            record["translator"], record["tradition_school"],
                            _vec_str(emb),
                            datetime.now(timezone.utc),
                        ),
                    )
                    inserted += cur.rowcount

                # ── 6. Update classical_texts.ingested_at ─────────────────────
                cur.execute(
                    "UPDATE classical_texts SET ingested_at = %s WHERE text_id = %s",
                    (datetime.now(timezone.utc), text_id),
                )

            total_chunks += inserted
            per_text_counts[text_id] = inserted
            logger.info("[bg_texts] %s: %d chunks inserted", text_id, inserted)

        # ── Summary ───────────────────────────────────────────────────────────
        duration = time.time() - t0
        if conditional:
            raise RuntimeError(
                "bg_texts required inputs or quality gates were unavailable: "
                + ", ".join(conditional)
            )
        notes_parts = [f"{tid}:{n}" for tid, n in per_text_counts.items()]

        logger.info(
            "[bg_texts] COMPLETE: total_chunks=%d texts=%d duration=%.1fs conditional=%s",
            total_chunks, len(per_text_counts), duration, conditional,
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_chunks,
            duration_seconds=duration,
            notes="; ".join(notes_parts),
        )
