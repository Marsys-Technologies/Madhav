"""
chunkers.cgm_node — Doc-type 6: CGM Node chunker.
Phase B.2. Per M2A_EXEC_PLAN_v1_0.md §PLAN B.2 Task 2.3 + chunker_spec_v1_0.md §1 Doc-Type 6.
Spec ref: chunker_spec_v1_0.md §1 Doc-Type 6.
Boundary: node_id: key (YAML block per CGM_v9_0 format).
Max tokens: 600. Required metadata: node_id, node_type, node_label, domains, karaka_system.
NOTE: CGM_v9_0.md does not exist until B.3.5 Task 5. This chunker is implemented but cannot
be run until then. A FileNotFoundError guard enforces this. B.3.5 Task 5.5 triggers the run.
"""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from rag.chunkers import count_tokens, truncate_to_tokens, write_chunks_to_db
from rag.models import Chunk
from rag.validators import p1_layer_separation as p1

logger = logging.getLogger(__name__)

MAX_TOKENS = 600
SOURCE_FILE = "025_HOLISTIC_SYNTHESIS/CGM_v9_0.md"
SOURCE_VERSION = "9.1"
LAYER = "L2.5"

# CGM_v9_0 node blocks begin with a line matching `node_id: <ID>`
_NODE_BOUNDARY_RE = re.compile(r"^node_id:\s*(\S+)\s*$", re.MULTILINE)
# KRK-type node detection
_KRK_TYPE_RE = re.compile(r"node_type:\s*KRK", re.IGNORECASE)


def _parse_nodes(text: str) -> list[tuple[str, str]]:
    """
    Parse CGM_v9_0.md YAML node blocks.
    Each block starts at a `node_id:` line and runs until the next `node_id:` or EOF.
    Returns list of (node_id, raw_block_text).
    """
    matches = list(_NODE_BOUNDARY_RE.finditer(text))
    if not matches:
        return []

    nodes: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        node_id = m.group(1).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        nodes.append((node_id, block))
    return nodes


def _parse_node_properties(block: str) -> dict[str, Any]:
    """Parse a single YAML node block into a dict. Returns {} on parse error."""
    try:
        data = yaml.safe_load(block) or {}
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def chunk_cgm_nodes(cgm_path_or_root: str) -> list[Chunk]:
    """
    Parse CGM_v9_0.md and produce one Chunk per node block.
    - KRK-type nodes must carry `karaka_system` metadata field (7-karaka|8-karaka|both).
    - P1 gating applied to all candidate chunks.
    - Stop condition: raises RuntimeError if CGM node chunk count ≠ node count in file.
    - FileNotFoundError guard: raises if CGM_v9_0.md does not exist (pre-B.3.5 sessions).

    Args:
        cgm_path_or_root: Either the repo root (str path) or the direct path to CGM_v9_0.md.
    """
    # Resolve path: if cgm_path_or_root ends in CGM_v9_0.md use directly, else build from root
    candidate = Path(cgm_path_or_root)
    if candidate.is_file():
        cgm_path = candidate
    else:
        cgm_path = candidate / SOURCE_FILE

    # FileNotFoundError guard — CGM_v9_0.md produced by B.3.5 Task 5, not before
    if not cgm_path.exists():
        raise FileNotFoundError(
            "CGM_v9_0 not yet produced — run B.3.5 first. "
            f"Expected at: {cgm_path}"
        )

    repo_root = str(cgm_path.parents[2]) if cgm_path.is_file() else cgm_path_or_root

    text = cgm_path.read_text(encoding="utf-8")
    raw_nodes = _parse_nodes(text)

    if not raw_nodes:
        raise RuntimeError(
            "STOP: CGM_v9_0.md has no parseable node blocks (no `node_id:` entries found). "
            "Check CGM_v9_0 format."
        )

    node_count = len(raw_nodes)
    chunks: list[Chunk] = []
    p1_violations = 0

    for node_id, block in raw_nodes:
        props = _parse_node_properties(block)

        token_count = count_tokens(block)
        was_truncated = False
        content = block
        if token_count > MAX_TOKENS:
            # Truncate at longest complete property boundary (line-level)
            lines = block.split("\n")
            truncated_lines: list[str] = []
            running_tokens = 0
            for line in lines:
                line_tokens = count_tokens(line + "\n")
                if running_tokens + line_tokens > MAX_TOKENS:
                    break
                truncated_lines.append(line)
                running_tokens += line_tokens
            content = "\n".join(truncated_lines)
            was_truncated = True
            token_count = count_tokens(content)

        node_type = str(props.get("node_type", ""))
        node_label = str(props.get("node_label", props.get("label", node_id)))
        domains = props.get("domains", [])
        if not isinstance(domains, list):
            domains = [str(domains)] if domains else []

        # karaka_system required for KRK-type nodes
        karaka_system = props.get("karaka_system", "")
        is_krk = _KRK_TYPE_RE.search(block) is not None
        if is_krk and not karaka_system:
            logger.warning("CGM node '%s' is KRK type but missing karaka_system — defaulting to 'UNKNOWN'", node_id)
            karaka_system = "UNKNOWN"

        l1_source = props.get("l1_source", props.get("l1_basis", ""))

        meta: dict[str, Any] = {
            "node_id": node_id,
            "node_type": node_type,
            "node_label": node_label,
            "domains": domains,
            "l1_source": str(l1_source) if l1_source else "",
        }
        if karaka_system:
            meta["karaka_system"] = karaka_system
        if was_truncated:
            meta["truncation_note"] = f"Truncated at {MAX_TOKENS} tokens (property-boundary)"

        chunk_dict = {"layer": LAYER, "doc_type": "cgm_node", "content": content, "metadata": meta}
        p1_res = p1.validate(chunk_dict)
        if not p1_res["valid"]:
            p1_violations += 1
            logger.warning("P1 violation CGM node '%s': %s", node_id, p1_res["reason"])
            continue

        chunks.append(Chunk(
            chunk_id="",
            doc_type="cgm_node",
            layer=LAYER,
            source_file=SOURCE_FILE,
            source_version=SOURCE_VERSION,
            content=content,
            token_count=token_count,
            is_stale=False,
            citation_valid=True,
            metadata=meta,
        ))

    if p1_violations:
        logger.warning("cgm_node: %d P1 violations (chunks blocked)", p1_violations)

    if len(chunks) != node_count:
        raise RuntimeError(
            f"STOP: CGM node chunk count {len(chunks)} ≠ node count {node_count} "
            f"(p1_violations={p1_violations}). "
            "Check CGM_v9_0 node blocks or P1 gating."
        )

    logger.info("cgm_node: %d chunks produced from CGM_v9_0 (%d nodes)", len(chunks), node_count)
    return chunks


def run(repo_root: str) -> int:
    """Parse CGM nodes, write to rag_chunks via Cloud SQL (psycopg), return written count."""
    chunks = chunk_cgm_nodes(repo_root)
    written = write_chunks_to_db(chunks)
    logger.info("cgm_node: wrote %d / %d chunks to rag_chunks", written, len(chunks))
    return written


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parents[5])
    count = run(root)
    print(f"cgm_node: {count} chunks written")
