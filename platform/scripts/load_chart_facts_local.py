#!/usr/bin/env python3
"""
Standalone loader: read CHART_FACTS_EXTRACTION_v1_0.yaml from local path
and load into chart_facts (live table) via truncate+insert.

Usage:
  DATABASE_URL=... python3 load_chart_facts_local.py --source <yaml_path> [--truncate]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import yaml
import psycopg


YAML_SOURCE_VERSION = "CHART_FACTS_EXTRACTION_v1_0"
YAML_URI_LOG = "local:01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml"
BUILD_ID = "dar-p4-s14-2026-05-25"

INSERT_SQL = """
INSERT INTO chart_facts
  (fact_id, category, divisional_chart, value_text, value_number, value_json,
   source_section, build_id, provenance, is_stale)
VALUES
  (%(fact_id)s, %(category)s, %(divisional_chart)s, %(value_text)s, %(value_number)s,
   %(value_json)s::jsonb, %(source_section)s, %(build_id)s, %(provenance)s::jsonb, FALSE)
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


def load_yaml(path: str) -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    facts = data["facts"]
    print(f"Loaded {len(facts)} facts from {path} (schema_version={data.get('schema_version','?')})")
    return facts


def rows_from_facts(facts: list[dict]) -> list[dict]:
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
            "build_id": BUILD_ID,
            "provenance": json.dumps({
                "source_uri": YAML_URI_LOG,
                "source_version": YAML_SOURCE_VERSION,
                "extraction_method": fact.get("extraction_method", "manual"),
            }),
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description="Load chart_facts from local YAML")
    parser.add_argument("--source", required=True, help="Path to CHART_FACTS_EXTRACTION_v1_0.yaml")
    parser.add_argument("--truncate", action="store_true", help="Truncate chart_facts before insert")
    parser.add_argument(
        "--db-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="Postgres URL. Defaults to $DATABASE_URL. Required (empty default fails).",
    )
    args = parser.parse_args()

    if not args.db_url:
        sys.stderr.write(
            "ERROR: --db-url is empty and $DATABASE_URL is not set.\n"
            "Provide --db-url postgresql://user:pass@host:port/db or export DATABASE_URL.\n"
        )
        sys.exit(1)

    facts = load_yaml(args.source)
    rows = rows_from_facts(facts)

    with psycopg.connect(args.db_url, autocommit=False) as conn:
        with conn.transaction():
            # Ensure build_manifests row exists (FK requirement)
            conn.execute("""
                INSERT INTO build_manifests
                  (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
                   embedding_model, embedding_dim, chunk_count, embedding_count,
                   status, manifest_uri, notes)
                VALUES
                  (%(build_id)s, 'DAR-P4-S14-claude-code', 'dar-local-v1.2',
                   'local', 'none', 0, %(chunk_count)s, 0, 'staging',
                   'local:CHART_FACTS_EXTRACTION_v1_0.yaml',
                   'DAR-P4-S14: load enhanced chart_facts v1.2 (783 facts, 14 new categories)')
                ON CONFLICT (build_id) DO NOTHING
            """, {"build_id": BUILD_ID, "chunk_count": len(rows)})
            print(f"Ensured build_manifests row for build_id={BUILD_ID}")

            if args.truncate:
                conn.execute("TRUNCATE chart_facts")
                print("Truncated chart_facts.")

            written = 0
            errors = []
            for row in rows:
                try:
                    conn.execute(INSERT_SQL, row)
                    written += 1
                except Exception as exc:
                    errors.append(f"{row['fact_id']}: {exc}")

            print(f"Written: {written} rows, Errors: {len(errors)}")
            if errors:
                print("ERRORS:")
                for e in errors[:20]:
                    print(f"  {e}")

        # Update build_manifests to live
        conn.execute(
            "UPDATE build_manifests SET status='live', promoted_at=NOW() WHERE build_id=%s",
            (BUILD_ID,)
        )
        conn.commit()

        # Verify
        count = conn.execute("SELECT COUNT(*) FROM chart_facts").fetchone()[0]
        print(f"Total chart_facts rows after load: {count}")

        # Category breakdown
        rows_cat = conn.execute(
            "SELECT category, COUNT(*) FROM chart_facts GROUP BY category ORDER BY category"
        ).fetchall()
        print("\nCategory breakdown:")
        for cat, cnt in rows_cat:
            print(f"  {cat}: {cnt}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
