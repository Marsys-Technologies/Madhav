"""
chunkers.timeline_chunker — Doc-type l5_timeline: Lifetime Timeline chunker.
Wave 5 M2-D234-BUNDLE. Source: LIFETIME_TIMELINE_v1_0.md.
Boundary: H2 (^## §N ); split at H3 if > 1500 tokens.
Doc-type: l5_timeline.
Layer: L5.
Note: Timeline mixes L1 dasha dates with L2.5 interpretive text.
      Bridge-marker prepended for P1 awareness (L5 is exempt from P1 constraint,
      but marker documents the mixed-layer nature for audit traceability).
Stop condition: STOP if source file produces 0 chunks.
"""
from __future__ import annotations

import os
import logging
import re
import sys
from pathlib import Path
from typing import Any

from rag.chunkers import count_tokens, truncate_to_tokens, write_chunks_to_db
from rag.models import Chunk

logger = logging.getLogger(__name__)

SOURCE_FILE = "05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md"
CANONICAL_ID = "LIFETIME_TIMELINE_v1_0"
DOC_TYPE = "l5_timeline"
LAYER = "L5"
SOURCE_VERSION = "1.0"
MAX_TOKENS = 1500
MIN_BODY_TOKENS = 30

# Bridge marker: documents L1 dasha date + L2.5 interpretive text co-presence.
# L5 is exempt from P1 entity-ref constraint, but marker aids audit trail.
_BRIDGE_LINE = "# [L1 dasha timeline] → [L2.5 activation pattern embedded]\n"

_H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)
_H3_RE = re.compile(r"^### (.+)$", re.MULTILINE)
_FRONTMATTER_RE = re.compile(r"^---\n.*?^---\n", re.DOTALL | re.MULTILINE)

# Headings to skip (document metadata headers)
_SKIP_HEADING_PATTERNS = [
    re.compile(r"abhisek mohanty jyotish intelligence system", re.IGNORECASE),
]

# Dasha date pattern — signals L1/L2.5 mixed content
_DASHA_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _strip_frontmatter(text: str) -> str:
    m = _FRONTMATTER_RE.match(text)
    return text[m.end():] if m else text


def _is_metadata_heading(heading: str) -> bool:
    for pat in _SKIP_HEADING_PATTERNS:
        if pat.search(heading):
            return True
    return False


def _split_at_h3(body: str) -> list[str]:
    """Split H2 section body at H3 boundaries."""
    parts: list[str] = []
    matches = list(_H3_RE.finditer(body))
    if not matches:
        return [body.strip()]
    preamble = body[: matches[0].start()].strip()
    if preamble and count_tokens(preamble) >= MIN_BODY_TOKENS:
        parts.append(preamble)
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        chunk_text = body[m.start() : end].strip()
        if count_tokens(chunk_text) >= MIN_BODY_TOKENS:
            parts.append(chunk_text)
    return parts if parts else [body.strip()]


def _has_dasha_dates(text: str) -> bool:
    return bool(_DASHA_DATE_RE.search(text))


def _build_chunk(content: str, idx: int, heading: str) -> Chunk:
    chunk_id = f"timeline_{idx:03d}"
    token_count = count_tokens(content)
    truncated = False
    if token_count > MAX_TOKENS:
        content, truncated = truncate_to_tokens(content, MAX_TOKENS)
        token_count = count_tokens(content)

    metadata: dict[str, Any] = {
        "canonical_id": CANONICAL_ID,
        "heading": heading,
        "chunk_index": idx,
    }
    if truncated:
        metadata["truncation_note"] = f"Hard truncated at {MAX_TOKENS} tokens"

    return Chunk(
        chunk_id=chunk_id,
        doc_type=DOC_TYPE,
        layer=LAYER,
        source_file=SOURCE_FILE,
        source_version=SOURCE_VERSION,
        content=content,
        token_count=token_count,
        is_stale=False,
        citation_valid=True,
        metadata=metadata,
    )


def chunk_timeline_sections(repo_root: str) -> list[Chunk]:
    """
    Parse LIFETIME_TIMELINE_v1_0.md and return chunks.
    Stop condition: raises RuntimeError if 0 chunks produced.
    """
    path = Path(repo_root) / SOURCE_FILE
    if not path.exists():
        raise FileNotFoundError(f"Timeline source not found: {path}")

    text = _strip_frontmatter(path.read_text(encoding="utf-8"))

    # Split at H2 boundaries
    sections: list[tuple[str, str]] = []
    matches = list(_H2_RE.finditer(text))
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        if _is_metadata_heading(heading):
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((heading, body))

    if not sections:
        raise RuntimeError("STOP: LIFETIME_TIMELINE_v1_0.md produced 0 content H2 sections")

    chunks: list[Chunk] = []
    idx = 0
    for heading, body in sections:
        # Prepend bridge marker when chunk contains dasha date data
        bridge = _BRIDGE_LINE if _has_dasha_dates(body) else ""
        full_section = f"{bridge}## {heading}\n\n{body}"

        if count_tokens(full_section) <= MAX_TOKENS:
            if count_tokens(body) >= MIN_BODY_TOKENS:
                chunks.append(_build_chunk(full_section, idx, heading))
                idx += 1
        else:
            sub_parts = _split_at_h3(body)
            for sub in sub_parts:
                bridge_sub = _BRIDGE_LINE if _has_dasha_dates(sub) else ""
                sub_content = (
                    f"{bridge_sub}## {heading}\n\n{sub}"
                    if not sub.startswith("###")
                    else f"{bridge_sub}{sub}"
                )
                if count_tokens(sub_content) >= MIN_BODY_TOKENS:
                    chunks.append(_build_chunk(sub_content, idx, heading))
                    idx += 1

    if not chunks:
        raise RuntimeError("STOP: timeline_chunker produced 0 chunks — check H2 structure")

    logger.info("timeline_chunker: %d chunks produced for doc_type='%s'", len(chunks), DOC_TYPE)
    return chunks


def run(repo_root: str) -> int:
    """Parse LIFETIME_TIMELINE, write to rag_chunks, return written count."""
    chunks = chunk_timeline_sections(repo_root)
    chart_id = os.environ.get("NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0")
    written = write_chunks_to_db(chunks, chart_id)
    logger.info("timeline_chunker: wrote %d / %d chunks to rag_chunks", written, len(chunks))
    return written


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parents[4])
    count = run(root)
    print(f"timeline_chunker: {count} chunks written")
