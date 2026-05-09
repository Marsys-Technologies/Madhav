"""
pipeline.chunkers.forensic_chunker
KARN-W2-R2-CHART-FACTS-ETL — Pipeline wrapper around rag.chunkers.l1_fact.

Provides a rerunnable, pipeline-style interface to re-chunk FORENSIC
sections into rag_chunks doc_type=l1_fact. The underlying chunker
(rag/chunkers/l1_fact.py) already handles all H2/H3 sections including
§6–§24. This wrapper adds:
  - A --sections filter to re-chunk only specific sections
  - Logging of per-section chunk counts for AC.11 verification
  - Can be invoked as: python -m pipeline.chunkers.forensic_chunker --verify

Usage:
    cd platform/python-sidecar
    DATABASE_URL=... python -m pipeline.chunkers.forensic_chunker [--dry-run] [--verify]
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

import psycopg

logger = logging.getLogger(__name__)

_SIDECAR_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _SIDECAR_ROOT.parents[1]
_FORENSIC_PATH = _REPO_ROOT / "01_FACTS_LAYER" / "FORENSIC_ASTROLOGICAL_DATA_v8_0.md"

# Target sections for AC.11: must have ≥1 chunk each post-run.
# VARGA-ETL-FULL-S1-CPA D11 (2026-05-10): added §3 + every §3.1–§3.15 sub-section
# so the verify-coverage report explicitly confirms each divisional chart section
# (D2 Hora through D60 Shashtyamsha + the §3.15 CSI ledger) produces ≥1 chunk.
# l1_fact.py MIN_BODY_TOKENS lowered to 12 (was 20) so §3.1 D2 Hora (only 2 table
# rows, ~30–50 tokens) is no longer at risk of being below the threshold.
TARGET_SECTIONS = [
    "§3", "§3.1", "§3.2", "§3.3", "§3.4", "§3.5", "§3.6", "§3.7",
    "§3.8", "§3.9", "§3.10", "§3.11", "§3.12", "§3.13", "§3.14", "§3.15",
    "§6", "§7", "§8", "§9", "§11", "§13",
    "§16", "§17", "§18", "§20", "§22", "§24",
]


def verify_coverage(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Check rag_chunks DB for l1_fact coverage of TARGET_SECTIONS.

    Returns:
        dict with keys: covered, missing, total_l1_chunks, per_section_counts
    """
    root = Path(repo_root) if repo_root else _REPO_ROOT
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL env var not set")

    with psycopg.connect(db_url) as conn:
        rows = conn.execute(
            """
            SELECT metadata->>'section_id', COUNT(*)
            FROM rag_chunks
            WHERE doc_type = 'l1_fact' AND is_stale = false
            GROUP BY metadata->>'section_id'
            """
        ).fetchall()

    per_section: dict[str, int] = {}
    total = 0
    for sid, cnt in rows:
        per_section[sid or "(no_id)"] = cnt
        total += cnt

    covered: list[str] = []
    missing: list[str] = []
    for target in TARGET_SECTIONS:
        found = any(sid.startswith(target) for sid in per_section)
        if found:
            covered.append(target)
        else:
            missing.append(target)

    return {
        "covered": covered,
        "missing": missing,
        "total_l1_chunks": total,
        "per_section_counts": per_section,
    }


def run_chunker(repo_root: str | Path | None = None, dry_run: bool = False) -> int:
    """Run the l1_fact chunker and return written count."""
    sys.path.insert(0, str(_SIDECAR_ROOT))
    from rag.chunkers.l1_fact import chunk_l1_facts, run as l1_run

    root = str(Path(repo_root) if repo_root else _REPO_ROOT)

    if dry_run:
        chunks = chunk_l1_facts(root)
        logger.info("forensic_chunker dry-run: %d chunks would be written", len(chunks))
        return len(chunks)

    written = l1_run(root)
    logger.info("forensic_chunker: %d chunks written to rag_chunks", written)
    return written


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    parser = argparse.ArgumentParser(
        description="KARN-W2-R2 FORENSIC chunker — re-chunk L1 sections into rag_chunks"
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse only, do not write to DB")
    parser.add_argument("--verify", action="store_true", help="Check coverage without re-running chunker")
    parser.add_argument("--repo-root", help="Override repo root path")
    args = parser.parse_args()

    root = args.repo_root or str(_REPO_ROOT)

    if args.verify:
        result = verify_coverage(root)
        print(f"\n=== FORENSIC l1_fact chunk coverage ===")
        print(f"Total l1_fact chunks: {result['total_l1_chunks']}")
        print(f"\nTarget sections covered ({len(result['covered'])}/{len(TARGET_SECTIONS)}):")
        for s in result["covered"]:
            print(f"  ✅ {s}")
        if result["missing"]:
            print(f"\nMISSING ({len(result['missing'])}):")
            for s in result["missing"]:
                print(f"  ❌ {s}")
        else:
            print("\nAll target sections covered — AC.11 satisfied.")
        print("\nPer-section breakdown:")
        for sid, cnt in sorted(result["per_section_counts"].items()):
            print(f"  {sid:<20} {cnt}")
        return

    count = run_chunker(repo_root=root, dry_run=args.dry_run)
    if args.dry_run:
        print(f"dry-run: {count} chunks would be written")
    else:
        print(f"Written: {count} l1_fact chunks to rag_chunks")


if __name__ == "__main__":
    main()
