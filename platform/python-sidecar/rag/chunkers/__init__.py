"""
chunkers — MARSYS-JIS RAG Pipeline chunker package.
Phase B.2. Per M2A_EXEC_PLAN_v1_0.md §PLAN B.2 + chunker_spec_v1_0.md §2.
Shared utilities: token counting (cl100k_base), truncation, Cloud SQL write (psycopg),
MSR reference normalization, staleness register loader.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import tiktoken
from dotenv import load_dotenv

from rag.models import Chunk

logger = logging.getLogger(__name__)

# ── Token counting (cl100k_base per chunker_spec §2.5) ────────────────────────

_ENC = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Token count via cl100k_base — approximation per chunker_spec §2.5."""
    return len(_ENC.encode(text))


def truncate_to_tokens(content: str, max_tokens: int) -> tuple[str, bool]:
    """Hard-truncate content to max_tokens. Returns (truncated, was_truncated)."""
    tokens = _ENC.encode(content)
    if len(tokens) <= max_tokens:
        return content, False
    return _ENC.decode(tokens[:max_tokens]), True


# ── MSR reference normalization ───────────────────────────────────────────────

_MSR_BARE_RE = re.compile(r"\bMSR\.(\d{3}[a-z]?)\b")


def normalize_msr_refs(text: str) -> str:
    """
    Convert bare MSR.NNN → SIG.MSR.NNN so that P1's entity-reference check
    recognizes them. CDLM cells and UCN sections use the bare MSR. prefix;
    this normalization makes them consistent with the P1 validator pattern.
    """
    return _MSR_BARE_RE.sub(r"SIG.MSR.\1", text)


# ── Cloud SQL (psycopg) helpers ───────────────────────────────────────────────

def _db_url() -> str:
    load_dotenv(Path(__file__).parents[4] / ".env.rag", override=False)
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "[STOP] DATABASE_URL not set. "
            "Add it to .env.rag at the project root."
        )
    return url


def _chunk_to_row(c: Chunk) -> dict[str, Any]:
    meta = {
        **c.metadata,
        "citation_valid": c.citation_valid,
        "external_computation_pending": c.external_computation_pending,
    }
    return {
        "chunk_id": c.chunk_id,
        "doc_type": c.doc_type,
        "layer": c.layer,
        "source_file": c.source_file,
        "source_version": c.source_version,
        "content": c.content,
        "token_count": c.token_count,
        "is_stale": c.is_stale,
        "stale_reason": c.stale_reason,
        "stale_since": c.stale_since,
        "metadata": meta,
    }


def write_chunks_to_db(chunks: list[Chunk], chart_id: str) -> int:
    """
    Upsert chunks to rag_chunks via psycopg (Cloud SQL Auth Proxy).
    chart_id is required: the build's chart UUID (per-chart corpus rows).
    ON CONFLICT (chunk_id) DO UPDATE — idempotent. Batches 100 rows per call.
    Returns total chunks written.
    """
    if not chunks:
        return 0
    import psycopg

    db_url = _db_url()
    rows = [_chunk_to_row(c) for c in chunks]
    written = 0
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            for i in range(0, len(rows), 100):
                batch = rows[i : i + 100]
                for row in batch:
                    cur.execute(
                        """
                        INSERT INTO rag_chunks
                          (chunk_id, doc_type, layer, source_file, source_version,
                           content, token_count, is_stale, stale_reason, stale_since,
                           metadata, chart_id)
                        VALUES
                          (%(chunk_id)s, %(doc_type)s, %(layer)s, %(source_file)s,
                           %(source_version)s, %(content)s, %(token_count)s,
                           %(is_stale)s, %(stale_reason)s, %(stale_since)s,
                           %(metadata)s, %(chart_id)s)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                          content       = EXCLUDED.content,
                          token_count   = EXCLUDED.token_count,
                          is_stale      = EXCLUDED.is_stale,
                          stale_reason  = EXCLUDED.stale_reason,
                          stale_since   = EXCLUDED.stale_since,
                          metadata      = EXCLUDED.metadata,
                          chart_id      = EXCLUDED.chart_id
                        """,
                        {**row, "metadata": json.dumps(row["metadata"]), "chart_id": chart_id},
                    )
                conn.commit()
                written += len(batch)
    return written


def count_db_chunks(doc_type: str) -> int:
    """Return exact row count from rag_chunks for a given doc_type via psycopg."""
    import psycopg

    with psycopg.connect(_db_url()) as conn:
        row = conn.execute(
            "SELECT count(*) FROM rag_chunks WHERE doc_type = %s", (doc_type,)
        ).fetchone()
    return int(row[0]) if row else 0


# ── Staleness register ────────────────────────────────────────────────────────

def load_staleness_register(repo_root: str) -> dict[str, tuple[bool, str, str]]:
    """
    Parse 00_ARCHITECTURE/STALENESS_REGISTER.md.
    Returns {path_or_filename: (is_stale, stale_reason, detected_at)}.
    Both full relative path and basename keys are stored for flexible lookup.
    Used by doc-type 5 (domain_report) chunker to propagate is_stale flag.
    """
    path = Path(repo_root) / "00_ARCHITECTURE" / "STALENESS_REGISTER.md"
    if not path.exists():
        logger.warning("STALENESS_REGISTER.md not found at %s", path)
        return {}

    result: dict[str, tuple[bool, str, str]] = {}
    in_table = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if "| file_path |" in line:
            in_table = True
            continue
        if not in_table or not line.startswith("|"):
            if in_table and line.startswith("##"):
                in_table = False
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 7 or "---" in parts[1]:
            continue
        fp = parts[1].strip("`")
        if not fp.endswith(".md"):
            continue
        is_stale = "true" in parts[4].lower()
        stale_reason = parts[5].replace("—", "").strip() if len(parts) > 5 else ""
        detected_at = parts[6].strip() if len(parts) > 6 else ""
        result[fp] = (is_stale, stale_reason, detected_at)
        result[Path(fp).name] = (is_stale, stale_reason, detected_at)
    return result
