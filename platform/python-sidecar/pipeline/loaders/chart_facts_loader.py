# DEPRECATED 2026-05-10 — VARGA-ETL-FULL-S1-CPA
# This loader implemented Pipeline B (ON CONFLICT upsert against live
# chart_facts) which raced with Pipeline A (chart_facts_writer.py
# staging-then-swap DELETE-then-INSERT). Whichever pipeline ran last won;
# the other pipeline's rows were lost. The canonical resolution is to run
# only ingest_chart_facts.py + chart_facts_writer.py against the unified
# CHART_FACTS_EXTRACTION_v1_0.yaml v1.1 (see 00_ARCHITECTURE/
# CHART_FACTS_PIPELINE_AUDIT_v1_0.md). This file is frozen — do not invoke
# for new ingests; do not extend its category enum.
"""
pipeline.loaders.chart_facts_loader — FROZEN/DEPRECATED 2026-05-10
KARN-W2-R2-CHART-FACTS-ETL — Direct-upsert loader for chart_facts rows
produced by chart_facts_extractor.

Accepts the 19 new category values added by this brief:
  shadbala, bhava_bala, ishta_kashta, strength_extra,
  ashtakavarga_bav, ashtakavarga_sav, ashtakavarga_pinda,
  kakshya_zone, avastha, upagraha, sensitive_point, mrityu_bhaga,
  arudha_occupancy, aspect, chalit_shift, chandra_placement,
  deity_assignment, varshphal, longevity_indicator

Does NOT replace the full chart_facts table (that is the forensic_extractor's
staging-swap job). Instead performs ON CONFLICT (fact_id) DO UPDATE upserts
against the live chart_facts table to ADD new rows without disturbing the
existing 589 baseline rows.

Usage:
    cd platform/python-sidecar
    DATABASE_URL=... python -m pipeline.loaders.chart_facts_loader \\
        --source ../../01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md \\
        --upsert

    python -m pipeline.loaders.chart_facts_loader --dry-run \\
        --source ../../01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BUILD_ID = f"karn-w2-r2-chart-facts-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
IMAGE_URI = "asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:v1.0.9"

VALID_CATEGORIES = frozenset({
    # pre-existing categories (pass-through)
    "birth_metadata", "planet", "house", "cusp", "arudha", "special_lagna",
    "saham", "navatara", "panchang", "dasha_vimshottari", "dasha_yogini",
    "dasha_chara", "yoga", "kp_cusp", "kp_planet", "kp_significator",
    "strength", "mercury_convergence",
    # new categories from this brief (W2-R2)
    "shadbala", "bhava_bala", "ishta_kashta", "strength_extra",
    "ashtakavarga_bav", "ashtakavarga_sav", "ashtakavarga_pinda",
    "kakshya_zone", "avastha", "upagraha", "sensitive_point", "mrityu_bhaga",
    "arudha_occupancy", "aspect", "chalit_shift", "chandra_placement",
    "deity_assignment", "varshphal", "longevity_indicator",
})

NEW_CATEGORIES = frozenset({
    "shadbala", "bhava_bala", "ishta_kashta", "strength_extra",
    "ashtakavarga_bav", "ashtakavarga_sav", "ashtakavarga_pinda",
    "kakshya_zone", "avastha", "upagraha", "sensitive_point", "mrityu_bhaga",
    "arudha_occupancy", "aspect", "chalit_shift", "chandra_placement",
    "deity_assignment", "varshphal", "longevity_indicator",
})

_UPSERT_SQL = """
INSERT INTO chart_facts
  (fact_id, category, divisional_chart, value_text, value_number, value_json,
   source_section, build_id, provenance, is_stale)
VALUES
  (%(fact_id)s, %(category)s, %(divisional_chart)s, %(value_text)s,
   %(value_number)s, %(value_json)s::jsonb,
   %(source_section)s, %(build_id)s, %(provenance)s::jsonb, FALSE)
ON CONFLICT (fact_id) DO UPDATE SET
  category         = EXCLUDED.category,
  divisional_chart = EXCLUDED.divisional_chart,
  value_text       = EXCLUDED.value_text,
  value_number     = EXCLUDED.value_number,
  value_json       = EXCLUDED.value_json,
  source_section   = EXCLUDED.source_section,
  build_id         = EXCLUDED.build_id,
  provenance       = EXCLUDED.provenance,
  is_stale         = FALSE
"""

_BUILD_MANIFEST_SQL = """
INSERT INTO build_manifests
  (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
   embedding_model, embedding_dim, chunk_count, embedding_count, status, manifest_uri)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (build_id) DO NOTHING
"""


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return url


def _ensure_build_manifest(conn: Any, build_id: str, row_count: int) -> None:
    try:
        conn.execute(
            _BUILD_MANIFEST_SQL,
            (
                build_id,
                "karn-w2-r2-chart-facts-etl",
                "n/a",
                IMAGE_URI,
                "n/a",
                0,
                row_count,
                0,
                "live",
                f"gs://madhav-marsys-build-artifacts/{build_id}/manifest.json",
            ),
        )
    except Exception as exc:
        logger.warning("build_manifests upsert skipped (may already exist): %s", exc)


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    """Return list of validation error strings. Empty = all valid."""
    errors: list[str] = []
    seen_ids: set[str] = set()
    for i, row in enumerate(rows):
        fid = row.get("fact_id", "")
        cat = row.get("category", "")
        if not fid:
            errors.append(f"row {i}: missing fact_id")
        elif fid in seen_ids:
            errors.append(f"row {i}: duplicate fact_id {fid!r}")
        else:
            seen_ids.add(fid)
        if cat not in VALID_CATEGORIES:
            errors.append(f"row {i} ({fid}): unknown category {cat!r}")
        if not row.get("source_section"):
            errors.append(f"row {i} ({fid}): missing source_section")
    return errors


def _to_db_row(row: dict[str, Any], build_id: str, source_path: str) -> dict[str, Any]:
    value_json = row.get("value_json")
    return {
        "fact_id": row["fact_id"],
        "category": row["category"],
        "divisional_chart": row.get("divisional_chart", "D1"),
        "value_text": row.get("value_text"),
        "value_number": row.get("value_number"),
        "value_json": json.dumps(value_json) if value_json is not None else None,
        "source_section": row["source_section"],
        "build_id": build_id,
        "provenance": json.dumps({
            "source_uri": str(source_path),
            "source_version": "FORENSIC_ASTROLOGICAL_DATA_v8_0",
            "extraction_method": "karn_w2_r2_md_parser",
            "brief": "CLAUDECODE_BRIEF_M2_A2_CHART_FACTS_ETL",
        }),
    }


def upsert(rows: list[dict[str, Any]], build_id: str, source_path: str) -> dict[str, Any]:
    """Upsert rows into live chart_facts table. Returns summary dict."""
    import psycopg

    errors = validate_rows(rows)
    if errors:
        for e in errors[:10]:
            logger.error("Validation error: %s", e)
        raise ValueError(f"Row validation failed with {len(errors)} errors")

    db_rows = [_to_db_row(r, build_id, source_path) for r in rows]

    written = 0
    row_errors: list[str] = []

    with psycopg.connect(_db_url()) as conn:
        _ensure_build_manifest(conn, build_id, len(rows))
        for db_row in db_rows:
            try:
                conn.execute(_UPSERT_SQL, db_row)
                written += 1
            except Exception as exc:
                row_errors.append(f"{db_row['fact_id']}: {exc}")
                logger.error("Upsert failed for %s: %s", db_row["fact_id"], exc)
        conn.commit()

    logger.info("chart_facts_loader: wrote %d / %d rows (%d errors)", written, len(rows), len(row_errors))
    return {"written": written, "total": len(rows), "errors": row_errors}


def run(source: str | Path, dry_run: bool = False) -> dict[str, Any]:
    """Full pipeline: extract → validate → upsert (unless dry_run)."""
    from pipeline.extractors.chart_facts_extractor import load_and_extract

    source_path = Path(source)
    rows = load_and_extract(source_path)

    errors = validate_rows(rows)
    if errors:
        logger.error("Validation errors before upsert:")
        for e in errors[:20]:
            logger.error("  %s", e)
        raise ValueError(f"{len(errors)} validation errors in extracted rows")

    # Category breakdown for logging
    from collections import Counter
    cat_counts = Counter(r["category"] for r in rows)
    logger.info("Extracted %d rows across %d categories:", len(rows), len(cat_counts))
    for cat, cnt in sorted(cat_counts.items()):
        logger.info("  %-30s %d", cat, cnt)

    if dry_run:
        logger.info("dry_run=True — skipping DB write")
        return {"written": 0, "total": len(rows), "categories": dict(cat_counts), "dry_run": True}

    result = upsert(rows, BUILD_ID, str(source_path))
    result["categories"] = dict(cat_counts)
    result["build_id"] = BUILD_ID
    return result


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    parser = argparse.ArgumentParser(description="KARN-W2-R2 chart_facts loader — upserts new categories from FORENSIC markdown")
    parser.add_argument("--source", required=True, help="Path to FORENSIC_ASTROLOGICAL_DATA_v8_0.md")
    parser.add_argument("--upsert", action="store_true", help="Actually write to DB (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no DB write")
    args = parser.parse_args()

    do_dry = args.dry_run or not args.upsert
    result = run(source=args.source, dry_run=do_dry)

    print(f"\n=== chart_facts_loader result ===")
    print(f"Total rows extracted: {result['total']}")
    print(f"Rows written to DB:   {result.get('written', 0)}")
    if result.get("dry_run"):
        print("(dry-run mode — no DB write)")
    if result.get("errors"):
        print(f"Errors: {result['errors'][:5]}")
    print("\nPer-category breakdown:")
    for cat, cnt in sorted(result.get("categories", {}).items()):
        marker = "NEW" if cat in NEW_CATEGORIES else "   "
        print(f"  {marker} {cat:<35} {cnt}")


if __name__ == "__main__":
    main()
