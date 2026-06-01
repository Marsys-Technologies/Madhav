"""
chunkers.rm_element — Doc-type: rm_element (Resonance Map element chunker).
Phase 11C_c. Per CLAUDECODE_BRIEF_RETRIEVAL_11C_c §3.4.
Boundary: ### RM.NN — ... heading + YAML code block.
One chunk per RM element (RM.01–RM.32, ~28 active).
"""
from __future__ import annotations

import os
import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from rag.chunkers import count_tokens, truncate_to_tokens
from rag.models import Chunk

logger = logging.getLogger(__name__)

MAX_TOKENS = 500
MIN_BODY_TOKENS = 20
SOURCE_FILE = "025_HOLISTIC_SYNTHESIS/RM_v2_0.md"
LAYER = "L2.5"

# Matches: ### RM.01 — ..., ### RM.21A — ..., ### RM.21B — ...
_HEADING_RE = re.compile(r"^###\s+(RM\.\d+[A-Z]?)\s*[—–-]\s*(.+)$")


def _read_frontmatter_version(text: str) -> str:
    """Return version string from YAML frontmatter; falls back to '2.1'."""
    if not text.startswith("---"):
        return "2.1"
    end = text.find("---", 3)
    if end == -1:
        return "2.1"
    try:
        fm = yaml.safe_load(text[3:end]) or {}
        return str(fm.get("version", "2.1"))
    except yaml.YAMLError:
        return "2.1"


def _parse_rm_element_blocks(
    text: str,
) -> list[tuple[str, str, str, dict[str, Any]]]:
    """
    Parse RM_v2_0.md and return (section_id, heading_label, raw_yaml, parsed_data)
    for each element block.

    - section_id: "RM.01", "RM.21A", etc.
    - heading_label: text after the "RM.NN — " prefix
    - raw_yaml: raw YAML text inside the ``` fence (without the fences)
    - parsed_data: yaml.safe_load result or {}
    """
    lines = text.splitlines()
    results: list[tuple[str, str, str, dict[str, Any]]] = []

    current_section: str | None = None
    current_label: str = ""
    in_yaml: bool = False
    yaml_lines: list[str] = []
    heading_consumed: bool = False

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            if in_yaml and yaml_lines:
                logger.warning("Unclosed YAML block before heading %s — discarding", line.strip())
                in_yaml = False
                yaml_lines = []
            current_section = m.group(1)
            current_label = m.group(2).strip()
            heading_consumed = False
            continue

        if re.match(r"^```yaml\s*$", line):
            if not in_yaml:
                in_yaml = True
                yaml_lines = []
            continue

        if re.match(r"^```\s*$", line) and in_yaml:
            in_yaml = False
            raw_yaml = "\n".join(yaml_lines)
            try:
                data = yaml.safe_load(raw_yaml) or {}
            except yaml.YAMLError:
                data = {}
            if not isinstance(data, dict):
                data = {}

            if current_section and not heading_consumed:
                results.append((current_section, current_label, raw_yaml, data))
                heading_consumed = True
            yaml_lines = []
            continue

        if in_yaml:
            yaml_lines.append(line)

    return results


def chunk_rm_elements(repo_root: str) -> list[Chunk]:
    """
    Parse RM_v2_0.md and emit one Chunk per resonance-map element (RM.01–RM.32).

    Each Chunk:
      chunk_id    = semantic element ID, e.g. "RM.01", "RM.21A"
      doc_type    = "rm_element"
      layer       = "L2.5"
      source_file = "025_HOLISTIC_SYNTHESIS/RM_v2_0.md"
      source_version = read from frontmatter
      content     = heading + full YAML block
      token_count = count_tokens(content)
      metadata    = {element_id, element_label, domains_primary, msr_anchors}

    Stop condition: raises RuntimeError if fewer than 20 chunks produced.
    """
    rm_path = Path(repo_root) / SOURCE_FILE
    if not rm_path.exists():
        raise FileNotFoundError(f"RM_v2_0.md not found at {rm_path}")

    text = rm_path.read_text(encoding="utf-8")
    source_version = _read_frontmatter_version(text)
    blocks = _parse_rm_element_blocks(text)
    logger.info("rm_element: parsed %d element blocks from %s", len(blocks), SOURCE_FILE)

    chunks: list[Chunk] = []
    for section_id, heading_label, raw_yaml, data in blocks:
        content = f"### {section_id} — {heading_label}\n\n```yaml\n{raw_yaml.rstrip()}\n```"
        token_count = count_tokens(content)

        if token_count < MIN_BODY_TOKENS:
            logger.debug("rm_element: skipping %s (%d tokens — below min)", section_id, token_count)
            continue

        if token_count > MAX_TOKENS:
            content, _ = truncate_to_tokens(content, MAX_TOKENS)
            token_count = count_tokens(content)

        domains_primary = data.get("domains_primary") or []
        if isinstance(domains_primary, str):
            domains_primary = [domains_primary]

        msr_anchors = data.get("msr_anchors") or []
        if isinstance(msr_anchors, str):
            msr_anchors = [msr_anchors]

        metadata: dict[str, Any] = {
            "element_id": section_id,
            "element_label": heading_label,
            "domains_primary": [str(d) for d in domains_primary],
            "msr_anchors": [str(a) for a in msr_anchors],
        }

        chunks.append(
            Chunk(
                chunk_id=section_id,
                doc_type="rm_element",
                layer=LAYER,
                source_file=SOURCE_FILE,
                source_version=source_version,
                content=content,
                token_count=token_count,
                is_stale=False,
                citation_valid=True,
                metadata=metadata,
            )
        )

    if len(chunks) < 20:
        raise RuntimeError(
            f"STOP: rm_element chunk count {len(chunks)} < 20 "
            f"(parsed={len(blocks)}). Check RM_v2_0.md parse."
        )

    logger.info("rm_element: %d chunks produced from %d blocks", len(chunks), len(blocks))
    return chunks


def run(repo_root: str) -> int:
    """Parse RM elements, write to rag_chunks via Cloud SQL (psycopg), return written count."""
    from rag.chunkers import write_chunks_to_db

    chunks = chunk_rm_elements(repo_root)
    chart_id = os.environ.get("NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0")
    written = write_chunks_to_db(chunks, chart_id)
    logger.info("rm_element: wrote %d / %d chunks to rag_chunks", written, len(chunks))
    return written


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parents[5])
    count = run(root)
    print(f"rm_element: {count} chunks written")
