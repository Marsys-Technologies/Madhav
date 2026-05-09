"""
pipeline.ingest_chart_facts — Phase 14C Stream F one-shot runner.

Reads CHART_FACTS_EXTRACTION_v1_0.yaml from GCS, validates against
CHART_FACTS_SCHEMA_v1_0.json, writes to chart_facts_staging, validates,
and swaps to live.

As of v1.1 YAML (VARGA-ETL-FULL-S1-CPA, 2026-05-10), this is the SOLE ETL
path for chart_facts. The markdown extractor (chart_facts_extractor.py +
chart_facts_loader.py) is deprecated and frozen — running it concurrently
with this pipeline causes a dual-pipeline race condition where the
DELETE-then-INSERT swap wipes the upsert's rows (or vice versa). All
formerly-extractor categories have been migrated into the YAML.
See 00_ARCHITECTURE/CHART_FACTS_PIPELINE_AUDIT_v1_0.md.

Row-count sanity gates: see chart_facts_writer.py
EXPECTED_COUNT_MIN/MAX (currently 500–820, accommodating ~666 facts in v1.1).

Usage:
  cd platform/python-sidecar
  DATABASE_URL=... python -m pipeline.ingest_chart_facts [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

import psycopg

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(levelname)s %(name)s %(message)s",
)
log = logging.getLogger(__name__)

BUILD_ID = "build-14c-chart-facts-20260429"
IMAGE_URI = "asia-south1-docker.pkg.dev/madhav-astrology/marsys-pipeline/pipeline:v1.0.9"


def _ensure_build_manifest(build_id: str) -> None:
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL env var not set")
    with psycopg.connect(db_url) as conn:
        existing = conn.execute(
            "SELECT 1 FROM build_manifests WHERE build_id = %s", (build_id,)
        ).fetchone()
        if existing:
            log.info("build_manifest already exists for build_id=%s", build_id)
            return
        conn.execute(
            """
            INSERT INTO build_manifests
              (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
               embedding_model, embedding_dim, chunk_count, embedding_count, status, manifest_uri)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                build_id,
                "manual:phase-14c-stream-f-chart-facts",
                "n/a",
                IMAGE_URI,
                "n/a",
                0,
                0,
                0,
                "live",
                f"gs://madhav-marsys-build-artifacts/{build_id}/manifest.json",
            ),
        )
        conn.commit()
    log.info("build_manifest registered for build_id=%s", build_id)


def _load_from_local_yaml(yaml_path: str, schema_path: str) -> list[dict]:
    """Local-filesystem fallback for environments without GCS access."""
    import yaml
    import json
    import jsonschema

    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    with open(schema_path) as f:
        schema = json.load(f)

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        msgs = [f"{list(e.path)}: {e.message}" for e in errors[:5]]
        raise RuntimeError(f"YAML schema validation failed ({len(errors)} errors): {msgs}")

    facts = data["facts"]
    rows = []
    for fact in facts:
        value_json = fact.get("value_json")
        rows.append({
            "fact_id": fact["fact_id"],
            "category": fact["category"],
            "divisional_chart": fact.get("divisional_chart", "D1"),
            "value_text": fact.get("value_text"),
            "value_number": fact.get("value_number"),
            "value_json": json.dumps(value_json) if value_json is not None else None,
            "source_section": fact["source_section"],
            "provenance": json.dumps({
                "source_uri": yaml_path,
                "source_version": "CHART_FACTS_EXTRACTION_v1_0",
                "extraction_method": fact.get("extraction_method", "manual"),
            }),
        })
    log.info("Loaded %d facts from local YAML", len(rows))
    return rows


def run(dry_run: bool = False, local_yaml: str | None = None, local_schema: str | None = None) -> None:
    log.info("=== CHART FACTS ===")

    if local_yaml and local_schema:
        rows = _load_from_local_yaml(local_yaml, local_schema)
    else:
        from pipeline.writers.chart_facts_writer import load_from_gcs
        rows = load_from_gcs()
    log.info("chart_facts: %d rows loaded", len(rows))

    if dry_run:
        log.info("dry-run — skipping DB writes")
        return

    _ensure_build_manifest(BUILD_ID)

    from pipeline.writers.chart_facts_writer import ChartFactsWriter
    writer = ChartFactsWriter()

    write_result = writer.write_to_staging(rows, BUILD_ID)
    log.info("staging: %d rows written, errors=%s", write_result.chunk_count, write_result.errors[:3])

    val = writer.validate_staging(BUILD_ID)
    log.info("validate: valid=%s count=%d issues=%s", val.valid, val.chunk_count, val.issues)

    if not val.valid:
        log.error("validation FAILED: %s", val.issues)
        sys.exit(1)

    swap = writer.swap_to_live(BUILD_ID)
    log.info("swap: %s", swap.message)
    if not swap.success:
        log.error("swap FAILED")
        sys.exit(1)

    log.info("ingest_chart_facts COMPLETE — build_id=%s", BUILD_ID)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--local-yaml", help="Path to CHART_FACTS_EXTRACTION_v1_0.yaml (local fallback)")
    parser.add_argument("--local-schema", help="Path to CHART_FACTS_SCHEMA_v1_0.json (local fallback)")
    args = parser.parse_args()
    run(dry_run=args.dry_run, local_yaml=args.local_yaml, local_schema=args.local_schema)
