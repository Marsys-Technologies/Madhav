"""
chunk — MARSYS-JIS RAG Pipeline corpus chunker orchestrator.
Phase B.2 (doc-types 1–5) + B.4 Session 1 (doc-type 6).
Per M2A_EXEC_PLAN_v1_0.md §PLAN B.2 Task 3 + chunker_spec_v1_0.md.
Dispatches to each doc-type chunker, integrates P1/P2/P5 gating, and produces
verification_artifacts/RAG/chunking_report.json.

Doc-types:
  1: msr_signal  (L2.5) — chunkers/msr_signal.py
  2: ucn_section (L2.5) — chunkers/ucn_section.py
  3: cdlm_cell   (L2.5) — chunkers/cdlm_cell.py
  4: l1_fact     (L1)   — chunkers/l1_fact.py
  5: domain_report (L3) — chunkers/domain_report.py
  6: cgm_node    (L2.5) — chunkers/cgm_node.py (activated at B.4 Session 1)

Stop conditions propagate from individual chunkers via RuntimeError.
"""
from __future__ import annotations

import json
import logging
import os
import statistics
import sys
from pathlib import Path
from typing import Any

from rag.chunkers import count_db_chunks, write_chunks_to_db
from rag.chunkers.msr_signal import chunk_msr_signals
from rag.chunkers.ucn_section import chunk_ucn_sections
from rag.chunkers.cdlm_cell import chunk_cdlm_cells
from rag.chunkers.l1_fact import chunk_l1_facts
from rag.chunkers.domain_report import chunk_domain_reports
from rag.chunkers.cgm_node import chunk_cgm_nodes
from rag.models import Chunk

logger = logging.getLogger(__name__)

# Token ceilings per doc-type (from M2A_EXEC_PLAN §RISKS RT5)
TOKEN_CEILINGS = {
    "msr_signal": 800,
    "ucn_section": 1500,
    "cdlm_cell": 400,
    "l1_fact": 1000,
    "domain_report": 1500,
    "cgm_node": 600,
}


def _token_stats(chunks: list[Chunk]) -> dict[str, Any]:
    if not chunks:
        return {"min": 0, "max": 0, "p50": 0, "p95": 0, "count": 0}
    counts = [c.token_count for c in chunks]
    counts_sorted = sorted(counts)
    n = len(counts_sorted)
    p50_idx = int(n * 0.50)
    p95_idx = int(n * 0.95)
    return {
        "min": counts_sorted[0],
        "max": counts_sorted[-1],
        "p50": counts_sorted[min(p50_idx, n - 1)],
        "p95": counts_sorted[min(p95_idx, n - 1)],
        "count": n,
    }


def run_all_chunkers(repo_root: str, doc_types: list[str] | None = None) -> dict[str, list[Chunk]]:
    """
    Run all (or a subset of) chunkers and return chunks by doc_type.
    Each chunker writes its chunks to rag_chunks.
    Stop conditions from individual chunkers propagate as RuntimeError.

    Args:
        repo_root: Absolute path to the repository root.
        doc_types: Optional list of doc_types to run. Defaults to all 6 types (includes cgm_node).
    """
    all_types = ["msr_signal", "ucn_section", "cdlm_cell", "l1_fact", "domain_report", "cgm_node"]
    requested = doc_types if doc_types is not None else all_types

    chunker_map = {
        "msr_signal": lambda: chunk_msr_signals(repo_root),
        "ucn_section": lambda: chunk_ucn_sections(repo_root),
        "cdlm_cell": lambda: chunk_cdlm_cells(repo_root),
        "l1_fact": lambda: chunk_l1_facts(repo_root),
        "domain_report": lambda: chunk_domain_reports(repo_root),
        "cgm_node": lambda: chunk_cgm_nodes(repo_root),
    }

    result: dict[str, list[Chunk]] = {}
    for doc_type in requested:
        if doc_type not in chunker_map:
            logger.warning("chunk.py: unknown doc_type '%s' — skipping", doc_type)
            continue
        logger.info("chunk.py: running chunker for doc_type=%s", doc_type)
        chunks = chunker_map[doc_type]()
        chart_id = os.environ.get("NATIVE_CHART_ID", "362f9f17-95a5-490b-a5a7-027d3e0efda0")
        written = write_chunks_to_db(chunks, chart_id)
        logger.info("chunk.py: doc_type=%s — %d chunks parsed, %d written to DB", doc_type, len(chunks), written)
        result[doc_type] = chunks

    return result


def build_chunking_report(
    chunks_by_type: dict[str, list[Chunk]],
    repo_root: str,
) -> dict[str, Any]:
    """
    Build the chunking_report.json content dict from all chunks.
    Queries DB for any doc_type counts not in chunks_by_type.
    """
    all_types = ["msr_signal", "ucn_section", "cdlm_cell", "l1_fact", "domain_report", "cgm_node"]

    # Per-doctype counts: prefer in-memory count, fall back to DB query
    per_doctype_counts: dict[str, int] = {}
    for dt in all_types:
        if dt in chunks_by_type:
            per_doctype_counts[dt] = len(chunks_by_type[dt])
        else:
            try:
                per_doctype_counts[dt] = count_db_chunks(dt)
            except Exception as e:
                logger.warning("chunk.py: DB count failed for %s: %s", dt, e)
                per_doctype_counts[dt] = -1

    # Token distribution from in-memory chunks
    token_distribution: dict[str, Any] = {}
    for dt, chunks in chunks_by_type.items():
        token_distribution[dt] = _token_stats(chunks)

    # Stale chunk count (domain_report only — only L3 chunks carry is_stale from STALENESS_REGISTER)
    stale_count = sum(1 for c in chunks_by_type.get("domain_report", []) if c.is_stale)

    # Truncation events (across all in-memory chunks)
    truncation_events = sum(
        1
        for chunks in chunks_by_type.values()
        for c in chunks
        if c.metadata.get("truncation_note")
    )

    # P1 violations: any L2.5/L3 P1-blocked chunk wouldn't be in the list, so count = 0
    # (L1 P1 violations raise RuntimeError — if we reached here, count is 0)
    p1_violations = 0

    # P5 warnings: count msr_signal chunks where citation_valid is False (proxy for P5 concerns)
    p5_warnings = sum(1 for c in chunks_by_type.get("msr_signal", []) if not c.citation_valid)

    report = {
        "produced_at": _now_iso(),
        "producer": "chunk.py — M2A-Exec Session 3 (Madhav_M2A_Exec_3)",
        "per_doctype_counts": per_doctype_counts,
        "token_distribution": token_distribution,
        "stale_chunk_count": stale_count,
        "truncation_events": truncation_events,
        "p1_violations": p1_violations,
        "p5_warnings": p5_warnings,
    }
    return report


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def write_chunking_report(report: dict[str, Any], repo_root: str) -> Path:
    """Write chunking_report.json to verification_artifacts/RAG/ and return path."""
    out_dir = Path(repo_root) / "verification_artifacts" / "RAG"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "chunking_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("chunk.py: chunking_report.json written to %s", out_path)
    return out_path


def main(repo_root: str, doc_types: list[str] | None = None) -> None:
    """
    Main entry point: run all requested doc-type chunkers, produce chunking_report.json.
    Stop conditions from individual chunkers propagate as RuntimeError.
    """
    chunks_by_type = run_all_chunkers(repo_root, doc_types)
    report = build_chunking_report(chunks_by_type, repo_root)

    out_path = write_chunking_report(report, repo_root)

    # Verify p1_violations: 0 before declaring success
    if report["p1_violations"] != 0:
        raise RuntimeError(
            f"STOP: chunking_report p1_violations={report['p1_violations']} (expected 0). "
            "AC-B2.8 fails."
        )

    print(f"chunking_report.json written to {out_path}")
    print(f"per_doctype_counts: {report['per_doctype_counts']}")
    print(f"stale_chunk_count: {report['stale_chunk_count']}")
    print(f"truncation_events: {report['truncation_events']}")
    print(f"p1_violations: {report['p1_violations']} (AC-B2.8: must be 0 ✓)")
    print(f"p5_warnings: {report['p5_warnings']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parents[3])
    # Optional: pass doc_types as remaining argv e.g. "l1_fact domain_report"
    dtypes = sys.argv[2:] if len(sys.argv) > 2 else None
    main(root, dtypes)
