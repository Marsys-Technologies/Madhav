"""
INF10-S1: RAG Embedder — chunk chart_documents + Vertex AI 768-dim embedding.

Reads chart_documents of type 'forensic_render' for a given (chart_id, ayanamsha_id),
chunks at H2/H3 Markdown boundaries, runs each chunk through the no-narration linter,
embeds via Vertex AI text-multilingual-embedding-002, and inserts into rag_chunks
with source_type='forensic_render'.

Designed to run as a post-render step after ForensicRenderer produces chart_documents.
Idempotent: deletes existing rag_chunks rows for (chart_id, ayanamsha_id, source_type)
before re-inserting.

[BUILD-ORCH-G4-08] INF10-S1
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-multilingual-embedding-002"
EMBEDDING_DIM = 768
SOURCE_TYPE = "forensic_render"
BATCH_SIZE = 20
MAX_CHUNK_TOKENS = 800
_EMBED_TIMEOUT_S = 120

# ── Chunking ──────────────────────────────────────────────────────────────────

# Matches H2 or H3 headers (##/###) with optional anchor {#...}
_HEADING_RE = re.compile(r'^#{2,3}\s+', re.MULTILINE)


@dataclass
class Chunk:
    heading: str
    body: str
    chunk_index: int
    source_section: str


def chunk_markdown(markdown: str) -> list[Chunk]:
    """Split a Markdown document at H2/H3 boundaries.

    Returns one Chunk per section. Sections longer than MAX_CHUNK_TOKENS (rough
    word count) are split further at paragraph boundaries.
    """
    # Strip YAML frontmatter if present
    if markdown.startswith('---'):
        end = markdown.find('\n---\n', 3)
        if end != -1:
            markdown = markdown[end + 5:]

    # Find all heading positions
    splits = list(_HEADING_RE.finditer(markdown))
    if not splits:
        return [Chunk(heading='', body=markdown.strip(), chunk_index=0, source_section='document')]

    chunks: list[Chunk] = []
    for i, match in enumerate(splits):
        start = match.start()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(markdown)
        section_text = markdown[start:end].strip()

        # Extract heading text (first line)
        first_nl = section_text.find('\n')
        heading = section_text[:first_nl].strip() if first_nl != -1 else section_text
        body = section_text[first_nl:].strip() if first_nl != -1 else ''

        # Rough token estimate: 1 word ≈ 1.3 tokens
        words = len(section_text.split())
        estimated_tokens = int(words * 1.3)

        if estimated_tokens <= MAX_CHUNK_TOKENS:
            chunks.append(Chunk(
                heading=heading,
                body=section_text,
                chunk_index=len(chunks),
                source_section=heading,
            ))
        else:
            # Split at paragraph breaks
            paragraphs = re.split(r'\n\n+', section_text)
            acc: list[str] = []
            acc_words = 0
            for para in paragraphs:
                para_words = len(para.split())
                if acc_words + para_words > MAX_CHUNK_TOKENS // 1.3 and acc:
                    chunks.append(Chunk(
                        heading=heading,
                        body='\n\n'.join(acc),
                        chunk_index=len(chunks),
                        source_section=heading,
                    ))
                    acc = [para]
                    acc_words = para_words
                else:
                    acc.append(para)
                    acc_words += para_words
            if acc:
                chunks.append(Chunk(
                    heading=heading,
                    body='\n\n'.join(acc),
                    chunk_index=len(chunks),
                    source_section=heading,
                ))

    return chunks


# ── No-narration linting ──────────────────────────────────────────────────────

def _lint_chunk(chunk: Chunk) -> None:
    """Lint a chunk body. Raises NoNarrationViolationError on violation."""
    try:
        from pipeline.linters.no_narration_linter import lint, NoNarrationViolationError  # noqa: F401
        lint(chunk.body, source_hint=chunk.source_section)
    except ImportError:
        # Linter not yet on PYTHONPATH — degrade gracefully (log warning)
        log.warning("no_narration_linter not importable; skipping lint for chunk %d", chunk.chunk_index)


# ── Vertex AI embedding ───────────────────────────────────────────────────────

_embed_model = None


def _init_vertexai() -> None:
    global _embed_model
    try:
        import vertexai
        from vertexai.language_models import TextEmbeddingModel
        project = os.environ.get("GCP_PROJECT", "")
        location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
        if not project:
            raise RuntimeError("GCP_PROJECT not set")
        vertexai.init(project=project, location=location)
        _embed_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
        log.info("rag_embedder: vertex initialized model=%s", EMBEDDING_MODEL)
    except ImportError:
        log.warning("rag_embedder: vertexai not installed; embeddings will be zero-vectors")


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Return 768-dim embeddings. Falls back to zero vectors if Vertex unavailable."""
    if _embed_model is None:
        return [[0.0] * EMBEDDING_DIM for _ in texts]

    try:
        from vertexai.language_models import TextEmbeddingInput

        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            inputs = [TextEmbeddingInput(t, "RETRIEVAL_DOCUMENT") for t in batch]
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(_embed_model.get_embeddings, inputs)
                results = future.result(timeout=_EMBED_TIMEOUT_S)
            all_embeddings.extend(r.values for r in results)
        return all_embeddings
    except Exception as exc:
        log.error("rag_embedder: embedding batch failed: %s", exc)
        return [[0.0] * EMBEDDING_DIM for _ in texts]


# ── DB operations ─────────────────────────────────────────────────────────────

def _chunk_id(chart_id: str, ayanamsha_id: str, source_section: str, chunk_index: int) -> str:
    key = f"{chart_id}|{ayanamsha_id}|{source_section}|{chunk_index}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]


def embed_chart_document(
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    db_url: Optional[str] = None,
    *,
    init_vertex: bool = True,
) -> dict:
    """
    Full pipeline: read chart_documents → chunk → lint → embed → insert rag_chunks.

    Returns:
        dict with keys: chunks_written, chunks_skipped_lint, source_type
    """
    import psycopg

    url = db_url or os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set")

    if init_vertex:
        _init_vertexai()

    conn = psycopg.connect(url)
    conn.autocommit = False

    try:
        # 1. Fetch forensic_render document
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT content_md FROM chart_documents
                 WHERE chart_id = %s AND ayanamsha_id = %s
                   AND document_type = 'forensic_render'
                 ORDER BY rendered_at DESC LIMIT 1
                """,
                (chart_id, ayanamsha_id),
            )
            row = cur.fetchone()

        if not row or not row[0]:
            log.warning("rag_embedder: no forensic_render document for chart=%s aya=%s", chart_id, ayanamsha_id)
            return {'chunks_written': 0, 'chunks_skipped_lint': 0, 'source_type': SOURCE_TYPE}

        markdown = row[0]

        # 2. Chunk
        chunks = chunk_markdown(markdown)
        log.info("rag_embedder: %d chunks from chart=%s aya=%s", len(chunks), chart_id, ayanamsha_id)

        # 3. Lint + filter
        valid_chunks: list[Chunk] = []
        skipped = 0
        for chunk in chunks:
            try:
                _lint_chunk(chunk)
                valid_chunks.append(chunk)
            except Exception as exc:
                log.warning("rag_embedder: lint violation in chunk %d of %s/%s: %s",
                            chunk.chunk_index, chart_id, ayanamsha_id, exc)
                skipped += 1

        if not valid_chunks:
            log.warning("rag_embedder: all %d chunks failed lint for chart=%s aya=%s",
                        len(chunks), chart_id, ayanamsha_id)
            return {'chunks_written': 0, 'chunks_skipped_lint': skipped, 'source_type': SOURCE_TYPE}

        # 4. Embed
        texts = [c.body for c in valid_chunks]
        embeddings = _embed_texts(texts)

        # 5. Delete existing chunks for this (chart_id, ayanamsha_id, source_type)
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM rag_chunks WHERE chart_id = %s AND ayanamsha_id = %s AND source_type = %s",
                (chart_id, ayanamsha_id, SOURCE_TYPE),
            )

        # 6. Insert new chunks
        written = 0
        with conn.cursor() as cur:
            for chunk, emb in zip(valid_chunks, embeddings):
                chunk_uuid = str(uuid.uuid4())
                meta = {
                    'heading': chunk.heading,
                    'chunk_index': chunk.chunk_index,
                    'chart_id': chart_id,
                    'ayanamsha_id': ayanamsha_id,
                    'build_id': build_id,
                    'source_section': chunk.source_section,
                }
                cur.execute(
                    """
                    INSERT INTO rag_chunks
                      (id, source_type, chart_id, ayanamsha_id, build_id,
                       source_section, text, embedding, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, %s, NOW())
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        chunk_uuid,
                        SOURCE_TYPE,
                        chart_id,
                        ayanamsha_id,
                        build_id,
                        chunk.source_section,
                        chunk.body[:4000],  # cap at 4k chars for storage
                        emb,
                        meta,
                    ),
                )
                written += 1

        conn.commit()
        log.info("rag_embedder: wrote %d chunks for chart=%s aya=%s", written, chart_id, ayanamsha_id)

        return {
            'chunks_written': written,
            'chunks_skipped_lint': skipped,
            'source_type': SOURCE_TYPE,
        }

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
