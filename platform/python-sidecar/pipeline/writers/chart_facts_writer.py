"""
pipeline.writers.chart_facts_writer — Write chart facts to chart_facts_staging.
Phase 14C Stream F.

Reads CHART_FACTS_EXTRACTION_v1_0.yaml from GCS, validates against schema,
and upserts to chart_facts_staging using the staging-then-swap pattern.

Source: gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml
Schema: gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json
"""
from __future__ import annotations

import io
import json
import logging
import os
from typing import Any

import jsonschema
import psycopg
import yaml
from google.cloud import storage as gcs

from pipeline.writers.base import IBuildWriter, SwapResult, ValidationResult, WriteResult

log = logging.getLogger(__name__)

# ── C-07 stub dispatch constants ───────────────────────────────────────────────
ASSET_ID = "A3_chart_facts"
ASSET_LABEL = "Chart Facts (L1 Structured)"


def write(
    build_id: str,
    chart_id: str,
    ayanamsha_id: str,
    chart_output: dict,
    conn,
    extra: "Optional[dict]" = None,
) -> int:
    """
    Stub writer for A3 Chart Facts (build_chart dispatch registry).
    Returns rows_written = 0 (stub — no data written).
    Real implementation wires ChartFactsWriter below; stub until Stream F.
    """
    log.info(
        "[STUB] %s: chart=%s ayanamsha=%s build=%s",
        ASSET_LABEL, chart_id, ayanamsha_id, build_id,
    )
    return 0


TABLE_STAGING = "chart_facts_staging"
TABLE_LIVE = "chart_facts"
YAML_URI = "gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
SCHEMA_URI = "gs://madhav-marsys-sources/L1/facts/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json"

EXPECTED_COUNT_MIN = 500
EXPECTED_COUNT_MAX = 700

_INSERT_SQL = f"""
INSERT INTO {TABLE_STAGING}
  (fact_id, category, divisional_chart, value_text, value_number, value_json,
   source_section, build_id, provenance, is_stale)
VALUES
  (%(fact_id)s, %(category)s, %(divisional_chart)s, %(value_text)s, %(value_number)s,
   %(value_json)s::jsonb, %(source_section)s, %(build_id)s, %(provenance)s::jsonb, FALSE)
ON CONFLICT (fact_id) DO UPDATE SET
  category        = EXCLUDED.category,
  divisional_chart = EXCLUDED.divisional_chart,
  value_text      = EXCLUDED.value_text,
  value_number    = EXCLUDED.value_number,
  value_json      = EXCLUDED.value_json,
  source_section  = EXCLUDED.source_section,
  build_id        = EXCLUDED.build_id,
  provenance      = EXCLUDED.provenance,
  is_stale        = FALSE
"""


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL env var not set")
    return url


def _fetch_gcs_text(uri: str) -> str:
    bucket_name, blob_path = uri.replace("gs://", "").split("/", 1)
    client = gcs.Client()
    return client.bucket(bucket_name).blob(blob_path).download_as_text()


def load_from_gcs() -> list[dict[str, Any]]:
    """Fetch CHART_FACTS_EXTRACTION_v1_0.yaml from GCS, validate, return row dicts."""
    yaml_text = _fetch_gcs_text(YAML_URI)
    schema_text = _fetch_gcs_text(SCHEMA_URI)
    data = yaml.safe_load(yaml_text)
    schema = json.loads(schema_text)

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        msgs = [f"{list(e.path)}: {e.message}" for e in errors[:5]]
        raise RuntimeError(f"YAML schema validation failed ({len(errors)} errors): {msgs}")

    facts = data["facts"]
    count = len(facts)
    if count < EXPECTED_COUNT_MIN or count > EXPECTED_COUNT_MAX:
        raise RuntimeError(
            f"chart_facts sanity gate: {count} facts (expected {EXPECTED_COUNT_MIN}–{EXPECTED_COUNT_MAX})"
        )

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
                "source_uri": YAML_URI,
                "source_version": "CHART_FACTS_EXTRACTION_v1_0",
                "extraction_method": fact.get("extraction_method", "manual"),
            }),
        })

    log.info("chart_facts_writer: loaded %d facts from GCS", count)
    return rows


class ChartFactsWriter(IBuildWriter):
    """Write chart fact rows from CHART_FACTS_EXTRACTION_v1_0.yaml into chart_facts_staging."""

    def write_to_staging(self, rows: list[Any], build_id: str) -> WriteResult:
        if not rows:
            return WriteResult(chunk_count=0, errors=["No rows provided"])

        errors: list[str] = []
        written = 0

        with psycopg.connect(_db_url()) as conn:
            for row in rows:
                params = {**row, "build_id": build_id}
                try:
                    conn.execute(_INSERT_SQL, params)
                    written += 1
                except Exception as exc:
                    errors.append(f"{row['fact_id']}: {exc}")
            conn.commit()

        log.info("chart_facts_staging written: %d rows, %d errors", written, len(errors))
        return WriteResult(chunk_count=written, errors=errors)

    def validate_staging(self, build_id: str) -> ValidationResult:
        with psycopg.connect(_db_url()) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM chart_facts_staging WHERE build_id = %s", (build_id,)
            ).fetchone()
            count = int(row[0]) if row else 0

        valid = EXPECTED_COUNT_MIN <= count <= EXPECTED_COUNT_MAX
        issues = [] if valid else [
            f"chart_facts_staging count {count} outside {EXPECTED_COUNT_MIN}–{EXPECTED_COUNT_MAX} for build_id={build_id}"
        ]
        log.info("chart_facts validate_staging: build_id=%s count=%d valid=%s", build_id, count, valid)
        return ValidationResult(valid=valid, chunk_count=count, issues=issues)

    def swap_to_live(self, build_id: str) -> SwapResult:
        with psycopg.connect(_db_url()) as conn:
            live_count = int(
                (conn.execute("SELECT COUNT(*) FROM chart_facts").fetchone() or [0])[0]
            )
            staging_count = int(
                (conn.execute(
                    "SELECT COUNT(*) FROM chart_facts_staging WHERE build_id = %s", (build_id,)
                ).fetchone() or [0])[0]
            )

        if live_count > 0 and staging_count < (0.5 * live_count):
            msg = (
                f"ABORT: staging={staging_count}, live={live_count} — "
                "below 50% safety threshold."
            )
            log.error(msg)
            return SwapResult(success=False, promoted_chunk_count=0, message=msg)

        with psycopg.connect(_db_url(), autocommit=False) as conn:
            with conn.transaction():
                conn.execute("DELETE FROM chart_facts")
                conn.execute(
                    """
                    INSERT INTO chart_facts
                      (fact_id, category, divisional_chart, value_text, value_number, value_json,
                       source_section, build_id, provenance, is_stale)
                    SELECT fact_id, category, divisional_chart, value_text, value_number, value_json,
                           source_section, build_id, provenance, is_stale
                    FROM chart_facts_staging
                    WHERE build_id = %s
                    """,
                    (build_id,),
                )
                conn.execute("TRUNCATE chart_facts_staging")
                try:
                    conn.execute(
                        "UPDATE build_manifests SET status='live', promoted_at=NOW() WHERE build_id=%s",
                        (build_id,),
                    )
                except Exception as exc:
                    log.warning("build_manifests update skipped: %s", exc)

        log.info("chart_facts swap_to_live: promoted %d rows for build_id=%s", staging_count, build_id)
        return SwapResult(
            success=True,
            promoted_chunk_count=staging_count,
            message=f"chart_facts live: {staging_count} rows (build_id={build_id})",
        )
