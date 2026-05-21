"""
chunkers.msr_signal — Doc-type 1: MSR Signal chunker.
Phase B.2. Per M2A_EXEC_PLAN_v1_0.md §PLAN B.2 Task 1.1 + chunker_spec_v1_0.md §1 Doc-Type 1.
Spec ref: chunker_spec_v1_0.md §1 Doc-Type 1.
Boundary: ^SIG\\.MSR\\.\\d{3}[a-z]?:$ — one chunk per signal. Target: 573 chunks (v5.0).
"""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from rag.chunkers import count_tokens, normalize_msr_refs, truncate_to_tokens, write_chunks_to_db
from rag.models import Chunk
from rag.validators import p1_layer_separation as p1
from rag.validators import p2_citation as p2
from rag.validators import p5_signal_id_resolution as p5

logger = logging.getLogger(__name__)

MAX_TOKENS = 800
SOURCE_FILE = "025_HOLISTIC_SYNTHESIS/MSR_v5_0.md"
SOURCE_VERSION = "5.0"
LAYER = "L2.5"

_BOUNDARY = re.compile(r"^(SIG\.MSR\.\d{3}[a-z]?):\s*$", re.MULTILINE)


def _parse_signals(msr_path: Path) -> list[tuple[str, str, dict[str, Any]]]:
    """
    Parse MSR_v5_0.md into (signal_id, raw_yaml_body, parsed_dict) tuples.
    signal_id = 'SIG.MSR.001'; raw_yaml_body = indented YAML text for that signal.
    """
    text = msr_path.read_text(encoding="utf-8")
    blocks = _BOUNDARY.split(text)
    # blocks[0] = preamble; alternating pairs: signal_id, body
    results: list[tuple[str, str, dict[str, Any]]] = []
    for sig_id, body in zip(blocks[1::2], blocks[2::2]):
        sig_id = sig_id.strip()
        # Collect YAML lines until next signal boundary
        lines = body.lstrip("\n").split("\n")
        yaml_lines: list[str] = []
        for line in lines:
            if re.match(r"^SIG\.MSR\.\d{3}[a-z]?:\s*$", line):
                break
            yaml_lines.append(line)
        yaml_text = "\n".join(yaml_lines)
        try:
            data = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError:
            data = {}
        if not isinstance(data, dict):
            data = {}
        results.append((sig_id, yaml_text, data))
    return results


def chunk_msr_signals(repo_root: str) -> list[Chunk]:
    """
    Parse MSR_v5_0.md and produce one Chunk per signal.
    Applies P1 (layer separation), P2 (citation), P5 (signal ID resolution) gating.
    Stop condition: raises RuntimeError if chunk count ≠ 514.
    """
    msr_path = Path(repo_root) / SOURCE_FILE
    if not msr_path.exists():
        raise FileNotFoundError(f"MSR_v5_0.md not found at {msr_path}")

    signals = _parse_signals(msr_path)
    chunks: list[Chunk] = []
    p1_violations = 0
    p5_blocks = 0

    for sig_id, raw_body, data in signals:
        # Content = full YAML block with normalized MSR refs for P1 entity matching
        content_raw = f"{sig_id}:\n{raw_body.rstrip()}"
        content = normalize_msr_refs(content_raw)

        token_count = count_tokens(content)
        truncated = False
        if token_count > MAX_TOKENS:
            content, truncated = truncate_to_tokens(content, MAX_TOKENS)
            token_count = count_tokens(content)

        metadata: dict[str, Any] = {
            "signal_id": sig_id,
            "signal_name": data.get("signal_name", ""),
            "signal_type": data.get("signal_type", ""),
            "domains_affected": data.get("domains_affected", []),
            "confidence": float(data.get("confidence", 0.0)),
            "valence": data.get("valence", ""),
            "temporal_activation": data.get("temporal_activation", ""),
            "tags": data.get("tags", []),
            "provenance": str(data.get("provenance", "")),
            "v6_ids_consumed": data.get("v6_ids_consumed", []),
        }
        if truncated:
            metadata["truncation_note"] = f"Hard truncated at {MAX_TOKENS} tokens"

        chunk_dict: dict[str, Any] = {
            "doc_type": "msr_signal",
            "layer": LAYER,
            "content": content,
            "metadata": metadata,
        }

        # P1 gate — block if L2.5 content has no entity reference IDs
        p1_res = p1.validate(chunk_dict)
        if not p1_res["valid"]:
            p1_violations += 1
            logger.warning("P1 violation for %s: %s", sig_id, p1_res["reason"])
            continue

        # P2 — sets citation_valid flag (non-blocking; writes with False if missing/bad)
        p2_res = p2.validate(chunk_dict)
        citation_valid = p2_res.get("citation_valid", True)

        # P5 gate — hard BLOCK if signal_id not in MSR registry
        p5_res = p5.validate(chunk_dict)
        if not p5_res["valid"]:
            p5_blocks += 1
            logger.error("P5 BLOCK for %s: %s", sig_id, p5_res["reason"])
            continue

        chunk = Chunk(
            chunk_id="",
            doc_type="msr_signal",
            layer=LAYER,
            source_file=SOURCE_FILE,
            source_version=SOURCE_VERSION,
            content=content,
            token_count=token_count,
            is_stale=False,
            citation_valid=citation_valid,
            metadata=metadata,
        )
        chunks.append(chunk)

    if p1_violations:
        logger.warning("%d MSR signals failed P1 (blocked from write)", p1_violations)
    if p5_blocks:
        logger.error("%d MSR signals blocked by P5 (unresolvable signal_id)", p5_blocks)

    total_parsed = len(signals)
    if len(chunks) != 573:
        raise RuntimeError(
            f"STOP: MSR chunk count {len(chunks)} ≠ 573 "
            f"(parsed={total_parsed}, p1_violations={p1_violations}, p5_blocks={p5_blocks}). "
            "Check MSR_v5_0.md parse or validator gating."
        )

    logger.info("msr_signal: %d chunks parsed from %d signals", len(chunks), total_parsed)
    return chunks


def run(repo_root: str) -> int:
    """Parse MSR signals, write to rag_chunks via Cloud SQL (psycopg), return written count."""
    chunks = chunk_msr_signals(repo_root)
    written = write_chunks_to_db(chunks)
    logger.info("msr_signal: wrote %d / %d chunks to rag_chunks", written, len(chunks))
    return written


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parents[5])
    count = run(root)
    print(f"msr_signal: {count} chunks written")
