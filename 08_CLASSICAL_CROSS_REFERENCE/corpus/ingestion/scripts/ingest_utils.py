"""
ingest_utils.py — Shared utilities for M8 classical text ingestion pipeline.
Functions: chunk_text, clean_html, embed_batch, db_upsert_text,
           db_bulk_insert_chunks, gcs_upload_jsonl.
LLM stack: Vertex AI text-embedding-004 (768-dim). No Anthropic/Claude API.
"""

import os
import re
import json
import logging
import textwrap
import unicodedata
from typing import Any

import psycopg2
import psycopg2.extras
from bs4 import BeautifulSoup
from google.cloud import aiplatform, storage
from vertexai.language_models import TextEmbeddingModel

logger = logging.getLogger(__name__)

# ─── DB connection ─────────────────────────────────────────────────────────────

def get_db_conn() -> psycopg2.extensions.connection:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(url)


# ─── Text cleaning ─────────────────────────────────────────────────────────────

def clean_html(raw: str) -> str:
    """Strip HTML tags, normalize whitespace, remove boilerplate artifacts."""
    soup = BeautifulSoup(raw, "html.parser")
    # Remove script/style elements
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Remove null bytes and non-printable chars
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


# ─── Chunking ──────────────────────────────────────────────────────────────────

def _approximate_tokens(text: str) -> int:
    """Approximate token count: ~4 chars per token (GPT-style)."""
    return len(text) // 4


def chunk_text(
    text: str,
    max_tokens: int = 500,
    overlap: int = 80,
) -> list[dict[str, Any]]:
    """
    Split text into overlapping chunks preserving verse/paragraph boundaries.
    Returns list of dicts: {chunk_index, content, approx_tokens}.
    Tries to split on double-newlines (verse/paragraph boundaries) first,
    then word boundaries if a paragraph is too large.
    """
    paragraphs = re.split(r"\n\s*\n", text)
    chunks: list[dict[str, Any]] = []
    current_words: list[str] = []
    current_tokens = 0
    chunk_idx = 0

    def flush(words: list[str]) -> None:
        nonlocal chunk_idx
        content = " ".join(words).strip()
        if content:
            chunks.append({
                "chunk_index": chunk_idx,
                "content": content,
                "approx_tokens": _approximate_tokens(content),
            })
            chunk_idx += 1

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_tokens = _approximate_tokens(para)
        if para_tokens > max_tokens:
            # Split large paragraph on word boundaries
            words = para.split()
            for word in words:
                word_tokens = _approximate_tokens(word) + 1
                if current_tokens + word_tokens > max_tokens and current_words:
                    flush(current_words)
                    # Overlap: keep last `overlap`-token words
                    overlap_words: list[str] = []
                    overlap_count = 0
                    for w in reversed(current_words):
                        wt = _approximate_tokens(w) + 1
                        if overlap_count + wt > overlap:
                            break
                        overlap_words.insert(0, w)
                        overlap_count += wt
                    current_words = overlap_words
                    current_tokens = overlap_count
                current_words.append(word)
                current_tokens += word_tokens
        else:
            if current_tokens + para_tokens > max_tokens and current_words:
                flush(current_words)
                overlap_words = []
                overlap_count = 0
                for w in reversed(current_words):
                    wt = _approximate_tokens(w) + 1
                    if overlap_count + wt > overlap:
                        break
                    overlap_words.insert(0, w)
                    overlap_count += wt
                current_words = overlap_words
                current_tokens = overlap_count
            current_words.extend(para.split())
            current_tokens += para_tokens

    if current_words:
        flush(current_words)

    return chunks


# ─── Embeddings ────────────────────────────────────────────────────────────────

def embed_batch(
    chunks: list[dict[str, Any]],
    project: str | None = None,
    location: str = "us-central1",
    max_tokens_per_request: int = 8000,
    max_chunks_per_batch: int = 15,
) -> list[dict[str, Any]]:
    """
    Embed a list of chunk dicts using Vertex AI text-embedding-004 (768-dim).
    Dynamically sizes batches to stay under max_tokens_per_request (default 8k approx,
    ≈14-16k actual tokens — safely below the 20k Vertex AI limit; real token counts
    run ~1.5-1.8x the len//4 approximation for classical Sanskrit/English text).
    Hard cap of max_chunks_per_batch (default 15) as an additional safety net.
    Adds 'embedding' key to each chunk. Uses Application Default Credentials.
    """
    gcp_project = project or os.environ.get("GCP_PROJECT")
    if not gcp_project:
        raise RuntimeError("GCP_PROJECT not set")

    aiplatform.init(project=gcp_project, location=location)
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    i = 0
    batch_num = 0
    while i < len(chunks):
        # Build a batch that stays under the token budget AND chunk cap
        batch: list[dict[str, Any]] = []
        batch_tokens = 0
        j = i
        while j < len(chunks) and len(batch) < max_chunks_per_batch:
            chunk_tokens = _approximate_tokens(chunks[j]["content"])
            if batch and batch_tokens + chunk_tokens > max_tokens_per_request:
                break
            batch.append(chunks[j])
            batch_tokens += chunk_tokens
            j += 1
        if not batch:
            # Single oversized chunk — truncate and embed alone
            chunk = chunks[i]
            text = chunk["content"]
            # Truncate to ~8000 approx tokens worth of chars (~32000 chars)
            text = text[: max_tokens_per_request * 4]
            batch = [chunk]
            batch[0] = dict(chunk)
            batch[0]["content"] = text
            j = i + 1

        texts = [c["content"] for c in batch]
        try:
            embeddings = model.get_embeddings(texts)
            for chunk, emb in zip(batch, embeddings):
                chunk["embedding"] = emb.values  # list[float] len=768
            logger.debug("Embedded batch %d (%d chunks, ~%d tokens)", batch_num, len(batch), batch_tokens)
        except Exception as e:
            logger.error("Embedding batch %d failed (%d chunks): %s", batch_num, len(batch), e)
            for chunk in batch:
                chunk["embedding"] = None

        i = j
        batch_num += 1

    return chunks


# ─── DB operations ─────────────────────────────────────────────────────────────

def db_upsert_text(metadata: dict[str, Any]) -> str:
    """
    Upsert a row into classical_texts. Returns the UUID of the upserted row.
    metadata keys: text_key, title, author, tradition, school, tier,
                   language_original, translation_author, source_url, procurement_date.
    """
    sql = """
    INSERT INTO classical_texts
      (text_key, title, author, tradition, school, tier, language_original,
       translation_author, source_url, procurement_date)
    VALUES (%(text_key)s, %(title)s, %(author)s, %(tradition)s, %(school)s,
            %(tier)s, %(language_original)s, %(translation_author)s,
            %(source_url)s, %(procurement_date)s)
    ON CONFLICT (text_key) DO UPDATE SET
      title = EXCLUDED.title,
      author = EXCLUDED.author,
      tradition = EXCLUDED.tradition,
      school = EXCLUDED.school,
      tier = EXCLUDED.tier,
      language_original = EXCLUDED.language_original,
      translation_author = EXCLUDED.translation_author,
      source_url = EXCLUDED.source_url,
      procurement_date = EXCLUDED.procurement_date
    RETURNING id
    """
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, metadata)
            row_id = cur.fetchone()[0]
        conn.commit()
    return str(row_id)


def db_bulk_insert_chunks(
    rows: list[dict[str, Any]],
    batch_size: int = 200,
) -> int:
    """
    Bulk insert classical_chunks rows. Each row: text_id, chunk_index, chapter,
    verse_range, content, embedding (list[float] or None), language.
    Uses ON CONFLICT DO NOTHING (idempotent by text_id + chunk_index).
    Returns number of rows inserted.
    """
    if not rows:
        return 0

    sql = """
    INSERT INTO classical_chunks
      (text_id, chunk_index, chapter, verse_range, content, embedding, language)
    VALUES %s
    ON CONFLICT (text_id, chunk_index) DO NOTHING
    """
    inserted = 0
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            for i in range(0, len(rows), batch_size):
                batch = rows[i : i + batch_size]
                values = []
                for r in batch:
                    emb = r.get("embedding")
                    emb_str = f"[{','.join(str(v) for v in emb)}]" if emb else None
                    values.append((
                        r["text_id"],
                        r["chunk_index"],
                        r.get("chapter"),
                        r.get("verse_range"),
                        r["content"],
                        emb_str,
                        r.get("language", "en"),
                    ))
                psycopg2.extras.execute_values(cur, sql, values)
                inserted += cur.rowcount
        conn.commit()
    return inserted


def db_update_embeddings(
    rows: list[dict[str, Any]],
    batch_size: int = 200,
) -> int:
    """
    Update embeddings for existing classical_chunks rows matched by (text_id, chunk_index).
    Skips rows where embedding is None. Returns count of rows updated.
    """
    rows_with_emb = [r for r in rows if r.get("embedding") is not None]
    if not rows_with_emb:
        return 0
    updated = 0
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            for i in range(0, len(rows_with_emb), batch_size):
                batch = rows_with_emb[i : i + batch_size]
                for r in batch:
                    emb_str = f"[{','.join(str(v) for v in r['embedding'])}]"
                    cur.execute(
                        "UPDATE classical_chunks SET embedding = %s WHERE text_id = %s AND chunk_index = %s",
                        (emb_str, r["text_id"], r["chunk_index"]),
                    )
                    updated += cur.rowcount
        conn.commit()
    return updated


def db_update_chunk_count(text_id: str) -> int:
    """Update classical_texts.chunk_count to match actual count in classical_chunks."""
    sql = """
    UPDATE classical_texts t
    SET chunk_count = (
      SELECT count(*) FROM classical_chunks c WHERE c.text_id = t.id
    )
    WHERE t.id = %s
    RETURNING chunk_count
    """
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (text_id,))
            row = cur.fetchone()
        conn.commit()
    return row[0] if row else 0


# ─── GCS upload ────────────────────────────────────────────────────────────────

def gcs_upload_jsonl(
    chunks: list[dict[str, Any]],
    gcs_path: str,
    bucket_name: str = "madhav-marsys-sources",
) -> str:
    """
    Serialize chunks to JSONL and upload to GCS.
    gcs_path: relative path within the bucket (e.g. 'L8/classical_texts/tier1/bphs_chunks.jsonl').
    Returns gs:// URI of uploaded object.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)

    lines = []
    for c in chunks:
        # Exclude embedding from JSONL (too large; embeddings live in DB)
        record = {k: v for k, v in c.items() if k != "embedding"}
        lines.append(json.dumps(record, ensure_ascii=False))

    jsonl_content = "\n".join(lines)
    blob.upload_from_string(jsonl_content, content_type="application/jsonl")

    uri = f"gs://{bucket_name}/{gcs_path}"
    logger.info("Uploaded %d chunks to %s", len(chunks), uri)
    return uri
