"""
chunkers.cdlm_cell — Doc-type 3: CDLM Cell chunker.
Phase B.2. Per M2A_EXEC_PLAN_v1_0.md §PLAN B.2 Task 1.3 + chunker_spec_v1_0.md §1 Doc-Type 3.
Spec ref: chunker_spec_v1_0.md §1 Doc-Type 3.
Boundary: ^CDLM.D[1-9].D[1-9]:$ — one chunk per cell. Target: 81 chunks.
"""
from __future__ import annotations

import os
import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from rag.chunkers import count_tokens, normalize_msr_refs, truncate_to_tokens, write_chunks_to_db
from rag.models import Chunk
from rag.validators import p1_layer_separation as p1

logger = logging.getLogger(__name__)

MAX_TOKENS = 400
SOURCE_FILE = "025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md"
SOURCE_VERSION = "1.1"
LAYER = "L2.5"

_BOUNDARY = re.compile(r"^(CDLM\.D[1-9]\.D[1-9]):\s*$", re.MULTILINE)

DOMAIN_MAP: dict[str, str] = {
    "D1": "career",
    "D2": "wealth",
    "D3": "relationships",
    "D4": "health",
    "D5": "children",
    "D6": "spirit",
    "D7": "parents",
    "D8": "mind",
    "D9": "travel",
}


def _cell_id(cell_key: str) -> str:
    """Convert 'CDLM.D1.D2' → 'CDLM.career.wealth'."""
    parts = cell_key.split(".")  # ['CDLM', 'D1', 'D2']
    if len(parts) != 3:
        return cell_key
    row = DOMAIN_MAP.get(parts[1], parts[1])
    col = DOMAIN_MAP.get(parts[2], parts[2])
    return f"CDLM.{row}.{col}"


def _parse_cells(cdlm_path: Path) -> list[tuple[str, str, dict[str, Any]]]:
    """
    Parse CDLM_v1_1.md into (cell_key, raw_yaml_body, parsed_dict) tuples.
    cell_key = 'CDLM.D1.D2'; raw_yaml_body = indented YAML text for that cell.
    """
    text = cdlm_path.read_text(encoding="utf-8")
    blocks = _BOUNDARY.split(text)
    # blocks[0] = preamble; alternating pairs: cell_key, body
    results: list[tuple[str, str, dict[str, Any]]] = []
    for cell_key, body in zip(blocks[1::2], blocks[2::2]):
        cell_key = cell_key.strip()
        lines = body.lstrip("\n").split("\n")
        yaml_lines: list[str] = []
        for line in lines:
            if re.match(r"^CDLM\.D[1-9]\.D[1-9]:\s*$", line):
                break
            yaml_lines.append(line)
        yaml_text = "\n".join(yaml_lines)
        try:
            data = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError:
            data = {}
        if not isinstance(data, dict):
            data = {}
        results.append((cell_key, yaml_text, data))
    return results


def _normalize_anchors(anchors: Any) -> list[str]:
    """Normalize msr_anchors list: convert MSR.NNN → SIG.MSR.NNN entries."""
    if not isinstance(anchors, list):
        return []
    normalized = []
    for item in anchors:
        s = str(item)
        s = re.sub(r"\bMSR\.(\d{3}[a-z]?)\b", r"SIG.MSR.\1", s)
        normalized.append(s)
    return normalized


def chunk_cdlm_cells(repo_root: str) -> list[Chunk]:
    """
    Parse CDLM_v1_1.md and produce one Chunk per grid cell.
    Applies P1 gating. Normalizes MSR.NNN → SIG.MSR.NNN in content and anchors.
    Stop condition: raises RuntimeError if chunk count < 81.
    """
    cdlm_path = Path(repo_root) / SOURCE_FILE
    if not cdlm_path.exists():
        raise FileNotFoundError(f"CDLM_v1_1.md not found at {cdlm_path}")

    cells = _parse_cells(cdlm_path)
    chunks: list[Chunk] = []
    p1_violations = 0

    for cell_key, raw_body, data in cells:
        content_raw = f"{cell_key}:\n{raw_body.rstrip()}"
        content = normalize_msr_refs(content_raw)

        token_count = count_tokens(content)
        truncated = False
        requires_split = False
        if token_count > MAX_TOKENS:
            requires_split = True
            content, truncated = truncate_to_tokens(content, MAX_TOKENS)
            token_count = count_tokens(content)

        row_d = cell_key.split(".")[1] if len(cell_key.split(".")) == 3 else ""
        col_d = cell_key.split(".")[2] if len(cell_key.split(".")) == 3 else ""
        row_domain = DOMAIN_MAP.get(row_d, data.get("row_domain", ""))
        col_domain = DOMAIN_MAP.get(col_d, data.get("col_domain", ""))

        msr_anchors = _normalize_anchors(data.get("msr_anchors", []))

        metadata: dict[str, Any] = {
            "row_domain": row_domain,
            "col_domain": col_domain,
            "cell_id": _cell_id(cell_key),
            "cdlm_version": SOURCE_VERSION,
            "cell_valence": data.get("valence", ""),
            "linkage_type": data.get("linkage_type", ""),
            "strength": float(data.get("strength", 0.0)) if data.get("strength") is not None else 0.0,
            "direction": data.get("direction", ""),
            "msr_anchors": msr_anchors,
            "key_finding": data.get("key_finding", ""),
        }
        if truncated:
            metadata["truncation_note"] = f"Hard truncated at {MAX_TOKENS} tokens"
        if requires_split:
            metadata["requires_split"] = True

        chunk_dict: dict[str, Any] = {
            "doc_type": "cdlm_cell",
            "layer": LAYER,
            "content": content,
            "metadata": metadata,
        }

        p1_res = p1.validate(chunk_dict)
        if not p1_res["valid"]:
            p1_violations += 1
            logger.warning("P1 violation CDLM '%s': %s", cell_key, p1_res["reason"])
            continue

        chunk = Chunk(
            chunk_id="",
            doc_type="cdlm_cell",
            layer=LAYER,
            source_file=SOURCE_FILE,
            source_version=SOURCE_VERSION,
            content=content,
            token_count=token_count,
            is_stale=False,
            citation_valid=True,
            metadata=metadata,
        )
        chunks.append(chunk)

    if p1_violations:
        logger.warning("%d CDLM cells failed P1 (blocked from write)", p1_violations)

    if len(chunks) < 81:
        raise RuntimeError(
            f"STOP: CDLM chunk count {len(chunks)} < 81 "
            f"(parsed={len(cells)}, p1_violations={p1_violations}). "
            "Check CDLM_v1_1.md parse or P1 gating."
        )

    logger.info("cdlm_cell: %d chunks produced from %d cells", len(chunks), len(cells))
    return chunks


def run(repo_root: str) -> int:
    """Parse CDLM cells, write to rag_chunks via Cloud SQL (psycopg), return written count."""
    chunks = chunk_cdlm_cells(repo_root)
    chart_id = os.environ.get("NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0")
    written = write_chunks_to_db(chunks, chart_id)
    logger.info("cdlm_cell: wrote %d / %d chunks to rag_chunks", written, len(chunks))
    return written


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parents[5])
    count = run(root)
    print(f"cdlm_cell: {count} chunks written")
