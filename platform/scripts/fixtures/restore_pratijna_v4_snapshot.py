#!/usr/bin/env python3
"""
restore_pratijna_v4_snapshot.py — restores the committed
`pratijna_v4_snapshot` fixture (schema.sql + gzipped per-table CSVs) into a
target Postgres database. Used by both:
  - CI (`.github/workflows/ci.yml`'s `pratijna-v4-fixture-property-tests`
    job), against the job's ephemeral `postgres:16` service container;
  - a developer's own local ephemeral Postgres, for reproducing a CI
    failure or validating a fixture refresh before committing it (see
    `export_pratijna_v4_snapshot.py`'s module docstring, step 4).

Idempotent in the sense that matters here: always targets a throwaway
database (never production — this script takes no `DBURL`-style production
credential at all, only a plain local/CI Postgres URL), and always starts
from `CREATE EXTENSION IF NOT EXISTS` + fresh `CREATE TABLE` (schema.sql
has no `IF NOT EXISTS` guards, matching a real pg_dump — re-running against
a database that already has these 5 tables will fail loudly on the second
`CREATE TABLE`, which is the correct behavior for a throwaway CI database
that should be provisioned fresh every run, not silently re-used).
"""
from __future__ import annotations

import gzip
import subprocess
import sys
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parents[3] / (
    "platform/python-sidecar/tests/fixtures/pratijna_v4_snapshot"
)
DATA_DIR = FIXTURE_DIR / "data"

TABLES_IN_FK_ORDER = [
    "charts",
    "reference_planets",
    "chart_facts",
    "chart_divisionals",
    "chart_fact_identity",
]


def run(args: list[str], **kw) -> subprocess.CompletedProcess:
    r = subprocess.run(args, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise SystemExit(f"command failed: {' '.join(args)}\n{r.stderr}")
    return r


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <postgres-url>")
    url = sys.argv[1]

    for ext in ("pgcrypto", "uuid-ossp"):
        run(["psql", url, "-v", "ON_ERROR_STOP=1", "-c", f'CREATE EXTENSION IF NOT EXISTS "{ext}";'])
    print("extensions ready")

    run(["psql", url, "-v", "ON_ERROR_STOP=1", "-f", str(FIXTURE_DIR / "schema.sql")])
    print("schema restored")

    for table in TABLES_IN_FK_ORDER:
        gz_path = DATA_DIR / f"{table}.csv.gz"
        with gzip.open(gz_path, "rt") as f:
            csv_text = f.read()
        r = subprocess.run(
            ["psql", url, "-v", "ON_ERROR_STOP=1", "-c", f"\\copy {table} FROM STDIN WITH CSV HEADER"],
            input=csv_text, capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise SystemExit(f"COPY failed for {table}:\n{r.stderr}")
        print(f"loaded {table}")

    print("fixture restored successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
