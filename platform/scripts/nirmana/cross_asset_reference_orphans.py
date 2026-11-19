#!/usr/bin/env python3
"""cross_asset_reference_orphans.py -- read-only orphan detector for the seven references whose ON DELETE CASCADE
foreign keys migration 1260 drops (SS N-99/N-105). No DB object: it runs cross_asset_reference_orphans.sql in a
READ ONLY transaction. REPORTED, NEVER BUILD-BLOCKING: orphans never change the exit code.

Use as the W7 / S-L3 pre/post check:  DATABASE_URL=... python3 platform/scripts/nirmana/cross_asset_reference_orphans.py [--json]

Exit: 0 report produced (orphans or not), 2 invocation/environment error (no DATABASE_URL, the SQL did not return exactly
      seven summary rows), 3 INCONCLUSIVE with --require-nonvacuous (a reference has zero referencing child rows, so its
      zero orphan count proves nothing).
Limit stated so it cannot overclaim: it sees a child row that EXISTS and points at nothing. A child row that was DELETED
leaves no trace here (that is the before/after row-count check of the rebuild plan).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SQL_PATH = Path(__file__).with_name("cross_asset_reference_orphans.sql")
EXPECTED_REFERENCES = 7


def split_statements(text: str) -> list[str]:
    """The SQL file holds exactly two statements; comments are stripped line-wise (no semicolons occur in them)."""
    body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("--"))
    stmts = [s.strip() for s in body.split(";") if s.strip()]
    if len(stmts) != 2:
        raise RuntimeError(f"expected exactly two statements in {SQL_PATH.name}, found {len(stmts)}")
    return stmts


def run(conn) -> dict:
    summary_sql, by_chart_sql = split_statements(SQL_PATH.read_text())
    conn.read_only = True
    with conn.cursor() as cur:
        cur.execute(summary_sql)
        cols = [d[0] for d in cur.description]
        summary = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.execute(by_chart_sql)
        cols2 = [d[0] for d in cur.description]
        by_chart = [{k: (str(v) if k == "chart_id" else v) for k, v in zip(cols2, r)} for r in cur.fetchall()]
    conn.rollback()
    if len(summary) != EXPECTED_REFERENCES:
        raise RuntimeError(f"summary returned {len(summary)} rows, expected {EXPECTED_REFERENCES}")
    return {"summary": summary, "by_chart": by_chart,
            "orphan_rows_total": sum(int(r["orphan_rows"]) for r in summary),
            "vacuous_references": [r["reference_name"] for r in summary if int(r["child_rows_with_reference"]) == 0]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--require-nonvacuous", action="store_true")
    args = ap.parse_args(argv)
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL not set", file=sys.stderr)
        return 2
    try:
        import psycopg
        with psycopg.connect(dsn) as conn:
            result = run(conn)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        for r in result["summary"]:
            print(f"{r['reference_name']:42s} refs={r['child_rows_with_reference']:<8} orphans={r['orphan_rows']:<8} charts={r['orphan_chart_count']}")
        print(f"orphan rows total: {result['orphan_rows_total']} (reported, never build-blocking)")
        if result["vacuous_references"]:
            print("VACUOUS (zero referencing child rows; a zero orphan count proves nothing): " + ", ".join(result["vacuous_references"]))
    if args.require_nonvacuous and result["vacuous_references"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
