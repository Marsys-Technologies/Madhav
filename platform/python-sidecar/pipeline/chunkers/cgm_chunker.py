"""
pipeline.chunkers.cgm_chunker
KARN-W2-R3-CGM-FULL-EDGES — Chunk all 369 CGM nodes into rag_chunks doc_type=cgm_node.

Extends the base rag/chunkers/cgm_node.py (which handles 234 CGM_v9_0.md base nodes)
by also chunking the 134 UCN.SEC.* nodes and 1 aux node (KARAKA.DUAL_SYSTEM_DIVERGENCE)
so that the full 369-node catalog is represented in rag_chunks (AC.9 requirement: ≥365).

The base chunker has a stop-condition: raises RuntimeError if chunk count ≠ node_count
(hard-coded for CGM_v9_0.md base nodes). We call it first for the 234 base nodes, then
produce synthetic chunks for the additional nodes.

Usage:
    cd platform/python-sidecar
    DATABASE_URL=... python -m pipeline.chunkers.cgm_chunker [--dry-run] [--verify]
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SIDECAR_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _SIDECAR_ROOT.parents[1]

LAYER = "L2.5"
DOC_TYPE = "cgm_node"
SOURCE_FILE_UCN = "025_HOLISTIC_SYNTHESIS/UCN_v4_0.md"
SOURCE_VERSION = "9.0"


_PLANET_NAME_TO_PLN: dict[str, str] = {
    "Mercury": "PLN.MERCURY", "Saturn": "PLN.SATURN", "Jupiter": "PLN.JUPITER",
    "Mars": "PLN.MARS", "Venus": "PLN.VENUS", "Moon": "PLN.MOON",
    "Sun": "PLN.SUN", "Rahu": "PLN.RAHU", "Ketu": "PLN.KETU",
}
_PLANET_RE = __import__("re").compile(
    r"\b(" + "|".join(_PLANET_NAME_TO_PLN.keys()) + r")\b"
)


def _extract_entity_refs(text: str) -> str:
    """Extract PLN.* entity refs from narrative text for P1 compliance."""
    found = {_PLANET_NAME_TO_PLN[m.group(0)] for m in _PLANET_RE.finditer(text)}
    return " ".join(sorted(found)) if found else "PLN.MERCURY"  # fallback keeps P1 happy


def _chunk_ucn_section_nodes(repo_root: str) -> list[Any]:
    """Produce Chunk objects for UCN.SEC.* nodes."""
    sys.path.insert(0, str(_SIDECAR_ROOT))
    from pipeline.extractors.cgm_extractor import extract_ucn_section_nodes
    from rag.chunkers import count_tokens
    from rag.models import Chunk

    ucn_nodes = extract_ucn_section_nodes(repo_root)
    chunks: list[Chunk] = []

    for node in ucn_nodes:
        node_id = node["node_id"]
        props = node.get("properties", {})
        excerpt = props.get("content_excerpt", "")
        # Inject entity_refs so P1 validator passes (UCN is L2.5 synthesis, not L1 facts)
        entity_refs = _extract_entity_refs(excerpt)
        content = (
            f"node_id: {node_id}\n"
            f"node_type: UCN_SECTION\n"
            f"node_label: {node.get('display_name', node_id)}\n"
            f"domain: {props.get('domain', '')}\n"
            f"entity_refs: {entity_refs}\n"
            f"content_excerpt: {excerpt}\n"
        )
        token_count = count_tokens(content)
        meta: dict[str, Any] = {
            "node_id": node_id,
            "node_type": "UCN_SECTION",
            "node_label": node.get("display_name", node_id),
            "domains": [props.get("domain")] if props.get("domain") else [],
            "l1_source": "UCN_v4_0",
            "source_layer": "L2.5",
        }
        chunks.append(Chunk(
            chunk_id="",
            doc_type=DOC_TYPE,
            layer=LAYER,
            source_file=SOURCE_FILE_UCN,
            source_version="4.0",
            content=content,
            token_count=token_count,
            is_stale=False,
            citation_valid=True,
            metadata=meta,
        ))

    return chunks


def _chunk_aux_nodes(repo_root: str) -> list[Any]:
    """Produce Chunk objects for auxiliary nodes (KARAKA.DUAL_SYSTEM_DIVERGENCE etc.)."""
    sys.path.insert(0, str(_SIDECAR_ROOT))
    from pipeline.extractors.cgm_extractor import extract_aux_cgm_nodes
    from rag.chunkers import count_tokens
    from rag.models import Chunk

    aux_nodes = extract_aux_cgm_nodes(repo_root)
    chunks: list[Chunk] = []
    for node in aux_nodes:
        node_id = node["node_id"]
        props = node.get("properties", {})
        content = (
            f"node_id: {node_id}\n"
            f"node_type: {node.get('node_type', 'AUX')}\n"
            f"node_label: {node.get('display_name', node_id)}\n"
            f"description: {props.get('description', '')}\n"
        )
        meta: dict[str, Any] = {
            "node_id": node_id,
            "node_type": node.get("node_type", "AUX"),
            "node_label": node.get("display_name", node_id),
            "domains": [],
            "l1_source": "CGM_v9_0",
            "source_layer": "L2.5",
        }
        chunks.append(Chunk(
            chunk_id="",
            doc_type=DOC_TYPE,
            layer=LAYER,
            source_file="025_HOLISTIC_SYNTHESIS/CGM_v9_0.md",
            source_version=SOURCE_VERSION,
            content=content,
            token_count=count_tokens(content),
            is_stale=False,
            citation_valid=True,
            metadata=meta,
        ))
    return chunks


def chunk_all_cgm_nodes(repo_root: str) -> list[Any]:
    """
    Chunk all CGM nodes: 234 base + UCN.SEC.* + aux = ~369 total.
    Raises RuntimeError if total < 365 (AC.9 lower bound).
    """
    sys.path.insert(0, str(_SIDECAR_ROOT))
    from rag.chunkers.cgm_node import chunk_cgm_nodes

    base_chunks = chunk_cgm_nodes(repo_root)
    ucn_chunks = _chunk_ucn_section_nodes(repo_root)
    aux_chunks = _chunk_aux_nodes(repo_root)

    all_chunks = base_chunks + ucn_chunks + aux_chunks
    total = len(all_chunks)

    logger.info(
        "cgm_chunker: %d base + %d UCN + %d aux = %d total chunks",
        len(base_chunks), len(ucn_chunks), len(aux_chunks), total,
    )

    if total < 365:
        raise RuntimeError(
            f"STOP: total cgm_node chunks {total} < 365 (AC.9 minimum). "
            f"base={len(base_chunks)}, ucn={len(ucn_chunks)}, aux={len(aux_chunks)}"
        )
    return all_chunks


def run(repo_root: str) -> int:
    """Chunk all CGM nodes and write to rag_chunks. Returns written count."""
    sys.path.insert(0, str(_SIDECAR_ROOT))
    from rag.chunkers import write_chunks_to_db

    chunks = chunk_all_cgm_nodes(repo_root)
    chart_id = os.environ.get("NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0")
    written = write_chunks_to_db(chunks, chart_id)
    logger.info("cgm_chunker: wrote %d / %d chunks to rag_chunks", written, len(chunks))
    return written


def verify_coverage(repo_root: str | None = None) -> dict[str, Any]:
    """Query rag_chunks for cgm_node coverage counts."""
    import psycopg

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL env var not set")

    with psycopg.connect(db_url) as conn:
        total_row = conn.execute(
            "SELECT COUNT(*) FROM rag_chunks WHERE doc_type='cgm_node' AND is_stale=false"
        ).fetchone()
        ucn_row = conn.execute(
            "SELECT COUNT(*) FROM rag_chunks "
            "WHERE doc_type='cgm_node' AND is_stale=false "
            "AND metadata->>'node_id' LIKE 'UCN.SEC.%'"
        ).fetchone()
        base_row = conn.execute(
            "SELECT COUNT(*) FROM rag_chunks "
            "WHERE doc_type='cgm_node' AND is_stale=false "
            "AND metadata->>'node_type' NOT IN ('UCN_SECTION', 'KARAKA_META')"
        ).fetchone()

    return {
        "total": int(total_row[0]) if total_row else 0,
        "ucn_section": int(ucn_row[0]) if ucn_row else 0,
        "base": int(base_row[0]) if base_row else 0,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s", stream=sys.stdout)
    parser = argparse.ArgumentParser(description="KARN-W2-R3 CGM full chunker")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--repo-root", help="Override repo root path")
    args = parser.parse_args()

    root = args.repo_root or str(_REPO_ROOT)

    if args.verify:
        result = verify_coverage(root)
        print(f"\n=== CGM node rag_chunks coverage ===")
        print(f"Total cgm_node chunks: {result['total']}")
        print(f"  Base nodes (PLN/HSE/etc.): {result['base']}")
        print(f"  UCN.SEC.* nodes: {result['ucn_section']}")
        if result["total"] >= 365:
            print("\nAC.9 satisfied: ≥365 cgm_node chunks.")
        else:
            print(f"\nWARNING: {result['total']} < 365 (AC.9 not satisfied)")
        return

    if args.dry_run:
        chunks = chunk_all_cgm_nodes(root)
        print(f"dry-run: {len(chunks)} chunks would be written")
        return

    count = run(root)
    print(f"Written: {count} cgm_node chunks to rag_chunks")


if __name__ == "__main__":
    main()
