"""
chunkers.lel_chunker — Doc-types lel_period_summary + lel_chronic_pattern.
KARN-W3-R1-CHUNKER-COMPLETION. Per M2_B2_CHUNKER_COMPLETION brief §3.3.

Parses LIFE_EVENT_LOG_v1_2.md:
  §4 → 6 lel_chronic_pattern chunks  (PATTERN.STAMMER.01 … PATTERN.COMPUTER_APTITUDE.01)
  §5 → 5 lel_period_summary chunks   (PERIOD.2007 … PERIOD.2022_2024)

Stop condition: raises RuntimeError if produced counts ≠ {period: 5, chronic: 6}.
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
from rag.validators import p1_layer_separation as p1

logger = logging.getLogger(__name__)

SOURCE_FILE = "01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md"
SOURCE_VERSION = "1.2"
LAYER = "L1"
MAX_TOKENS = 800
NATIVE_ID = "abhisek"

# Bridge marker: tells P1 validator to bypass L1 trigger-word check.
# LEL §4/§5 YAML blocks embed interpretive fields (likely_astrological_basis,
# retrodictive_note) alongside L1 observations — acknowledged here.
_BRIDGE_LINE = "# [L1 fact] → [L2.5 interp embedded]\n"

_YAML_BLOCK_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
_NEXT_H2_RE = re.compile(r"^## ", re.MULTILINE)


def _extract_section(text: str, anchor: str) -> str:
    """Extract text from anchor (inclusive) to the next H2 header."""
    start_re = re.compile(r"^" + re.escape(anchor) + r"(?=\s|—|–|-|$)", re.MULTILINE)
    m = start_re.search(text)
    if not m:
        return ""
    next_h = _NEXT_H2_RE.search(text, m.end())
    return text[m.start() : next_h.start() if next_h else len(text)]


def _parse_yaml_blocks(section_text: str) -> list[tuple[str, str]]:
    """
    Parse fenced YAML blocks in section_text.
    Returns [(block_id, full_fenced_block)] where block_id is the first YAML key
    (e.g. 'PATTERN.STAMMER.01', 'PERIOD.2007').
    """
    blocks: list[tuple[str, str]] = []
    for m in _YAML_BLOCK_RE.finditer(section_text):
        yaml_body = m.group(1)
        full_fence = m.group(0)
        first_line = yaml_body.split("\n")[0].rstrip(":").strip()
        if first_line:
            blocks.append((first_line, full_fence))
    return blocks


def _build_lel_chunk(block_id: str, doc_type: str, section: str, fenced_content: str) -> Chunk:
    """Construct a Chunk from a LEL YAML block. Prepends bridge marker for P1 compliance."""
    full_content = _BRIDGE_LINE + fenced_content
    token_count = count_tokens(full_content)
    truncated = False
    if token_count > MAX_TOKENS:
        full_content, truncated = truncate_to_tokens(full_content, MAX_TOKENS)
        token_count = count_tokens(full_content)

    doc_type_short = "period" if doc_type == "lel_period_summary" else "chronic"
    chunk_id = f"lel_{doc_type_short}_{block_id.lower().replace('.', '_')}"

    metadata: dict[str, Any] = {
        "block_id": block_id,
        "native_id": NATIVE_ID,
        "lel_version": SOURCE_VERSION,
        "section": section,
    }
    if truncated:
        metadata["truncation_note"] = f"Hard truncated at {MAX_TOKENS} tokens"

    return Chunk(
        chunk_id=chunk_id,
        doc_type=doc_type,
        layer=LAYER,
        source_file=SOURCE_FILE,
        source_version=SOURCE_VERSION,
        content=full_content,
        token_count=token_count,
        is_stale=False,
        citation_valid=True,
        metadata=metadata,
    )


def chunk_lel_sections(repo_root: str) -> list[Chunk]:
    """
    Parse LEL §4 (chronic patterns) and §5 (period summaries).
    Returns exactly 11 chunks: 6 lel_chronic_pattern + 5 lel_period_summary.
    Stop condition: raises RuntimeError if counts != {period: 5, chronic: 6}.
    """
    lel_path = Path(repo_root) / SOURCE_FILE
    if not lel_path.exists():
        raise FileNotFoundError(f"LEL not found at {lel_path}")

    text = lel_path.read_text(encoding="utf-8")

    sec4 = _extract_section(text, "## §4")
    if not sec4:
        raise RuntimeError("STOP: §4 section not found in LEL — boundary detection failure")
    chronic_blocks = _parse_yaml_blocks(sec4)
    if not chronic_blocks:
        raise RuntimeError("STOP: §4 produced 0 YAML blocks — parser failure")

    sec5 = _extract_section(text, "## §5")
    if not sec5:
        raise RuntimeError("STOP: §5 section not found in LEL — boundary detection failure")
    period_blocks = _parse_yaml_blocks(sec5)
    if not period_blocks:
        raise RuntimeError("STOP: §5 produced 0 YAML blocks — parser failure")

    chunks: list[Chunk] = []
    p1_violations = 0

    for block_id, fenced in chronic_blocks:
        candidate = _build_lel_chunk(block_id, "lel_chronic_pattern", "4", fenced)
        chunk_dict = {"layer": LAYER, "doc_type": "lel_chronic_pattern", "content": candidate.content, "metadata": candidate.metadata}
        p1_res = p1.validate(chunk_dict)
        if not p1_res["valid"]:
            p1_violations += 1
            logger.warning("P1 violation lel_chronic '%s': %s", block_id, p1_res["reason"])
        else:
            chunks.append(candidate)

    for block_id, fenced in period_blocks:
        candidate = _build_lel_chunk(block_id, "lel_period_summary", "5", fenced)
        chunk_dict = {"layer": LAYER, "doc_type": "lel_period_summary", "content": candidate.content, "metadata": candidate.metadata}
        p1_res = p1.validate(chunk_dict)
        if not p1_res["valid"]:
            p1_violations += 1
            logger.warning("P1 violation lel_period '%s': %s", block_id, p1_res["reason"])
        else:
            chunks.append(candidate)

    period_count = sum(1 for c in chunks if c.doc_type == "lel_period_summary")
    chronic_count = sum(1 for c in chunks if c.doc_type == "lel_chronic_pattern")

    if period_count != 5 or chronic_count != 6:
        raise RuntimeError(
            f"STOP: LEL chunk counts wrong — "
            f"lel_period_summary={period_count} (expected 5), "
            f"lel_chronic_pattern={chronic_count} (expected 6). "
            f"P1 violations: {p1_violations}"
        )

    logger.info(
        "lel_chunker: %d chunks produced (%d period + %d chronic, %d P1 violations)",
        len(chunks), period_count, chronic_count, p1_violations,
    )
    return chunks


def run(repo_root: str) -> int:
    """Parse LEL sections, write to rag_chunks via Cloud SQL, return written count."""
    chunks = chunk_lel_sections(repo_root)
    chart_id = os.environ.get("NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0")
    written = write_chunks_to_db(chunks, chart_id)
    logger.info("lel_chunker: wrote %d / %d chunks to rag_chunks", written, len(chunks))
    return written


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parents[4])
    count = run(root)
    print(f"lel_chunker: {count} chunks written")
