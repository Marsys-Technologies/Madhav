#!/usr/bin/env python3
"""
query_event_register.py — read the durable orchestrator event register.

SAMĀPTI lane B-EVENTREG (brief v2.0 §9.6 / register item SD-EVENTREG-1).

This is the audit surface SATYA_DIPA_REPORT_v1_0.md §1 went looking for and did not
find. Before this lane, `asset.noop_completion` / `asset.noop_completion_rejected` went
only to stdout (Cloud Logging, ~30d, and a `--freshness=9999d` probe returned ZERO) or
to a fire-and-forget Pub/Sub topic with a 600-second per-connection window. There was no
queryable history, which is why SATYA-DĪPA's Phase A had to abandon its primary forensic
method. `orchestrator_event_register` (see the migration) is that history; this script
is the convenience reader for it.

Everything here is plain SQL against `orchestrator_noop_events` /
`orchestrator_event_register` — nothing this script does is unavailable from psql. It
exists so the next audit does not have to re-derive the query.

Usage:
    python scripts/query_event_register.py                          # last 50 no-op events
    python scripts/query_event_register.py --limit 200
    python scripts/query_event_register.py --asset ka_gochara_sweep
    python scripts/query_event_register.py --chart 482012f1-710e-4a25-994a-93821f5871aa
    python scripts/query_event_register.py --run <run_id>
    python scripts/query_event_register.py --type asset.noop_completion_rejected
    python scripts/query_event_register.py --since 2026-01-01
    python scripts/query_event_register.py --all-types                # not just no-op classes
    python scripts/query_event_register.py --summary                  # counts by asset/verdict
    python scripts/query_event_register.py --json                     # machine-readable

Connection: DATABASE_URL / DIRECT_DATABASE_URL / POSTGRES_URL, via
pipeline.orchestrator.db.connect() — the same helper the orchestrator itself uses.

Read-only. This script issues SELECTs and never writes.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.db import connect  # noqa: E402


NOOP_TYPES = ("asset.noop_completion", "asset.noop_completion_rejected")

VERDICT = {
    "asset.noop_completion": "promoted_to_lit",
    "asset.noop_completion_rejected": "held_incomplete",
}


def build_query(args) -> tuple[str, list]:
    where: list[str] = []
    params: list = []

    if args.type:
        where.append("event_type = %s")
        params.append(args.type)
    elif not args.all_types:
        where.append("event_type = ANY(%s)")
        params.append(list(NOOP_TYPES))

    if args.asset:
        where.append("asset_id = %s")
        params.append(args.asset)
    if args.chart:
        where.append("chart_id = %s")
        params.append(args.chart)
    if args.run:
        where.append("run_id = %s")
        params.append(args.run)
    if args.since:
        where.append("occurred_at >= %s::timestamptz")
        params.append(args.since)

    clause = ("WHERE " + " AND ".join(where)) if where else ""

    if args.summary:
        sql = f"""
            SELECT asset_id,
                   COALESCE(chart_id, '(global)') AS chart_id,
                   event_type,
                   count(*)            AS events,
                   min(occurred_at)    AS first_seen,
                   max(occurred_at)    AS last_seen,
                   max(rows_present)   AS max_rows_present,
                   max(substeps_remaining) AS max_substeps_remaining
            FROM orchestrator_event_register
            {clause}
            GROUP BY asset_id, COALESCE(chart_id, '(global)'), event_type
            ORDER BY last_seen DESC
        """
        return sql, params

    sql = f"""
        SELECT id, occurred_at, event_type, chart_id, asset_id, run_id,
               rows_present, substeps_remaining, emitted_by, payload
        FROM orchestrator_event_register
        {clause}
        ORDER BY occurred_at DESC, id DESC
        LIMIT %s
    """
    return sql, params + [args.limit]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--limit", type=int, default=50, help="max rows (default 50)")
    p.add_argument("--asset", help="filter by asset_id, e.g. ka_gochara_sweep")
    p.add_argument("--chart", help="filter by chart_id")
    p.add_argument("--run", help="filter by run_id")
    p.add_argument("--type", help="filter by exact event_type")
    p.add_argument("--since", help="only events at/after this timestamp (any tz-aware literal)")
    p.add_argument("--all-types", action="store_true",
                   help="do not restrict to the two no-op classes")
    p.add_argument("--summary", action="store_true",
                   help="aggregate counts per asset/chart/event_type instead of listing rows")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = p.parse_args()

    sql, params = build_query(args)

    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT to_regclass('public.orchestrator_event_register') AS t"
            )
            row = cur.fetchone()
            if not row or not row.get("t"):
                print(
                    "orchestrator_event_register does not exist in this database. "
                    "Apply the orchestrator_event_register migration "
                    "(platform/supabase/migrations/) first.",
                    file=sys.stderr,
                )
                return 2
            cur.execute(sql, params)
            rows = cur.fetchall()
    finally:
        conn.close()

    if args.json:
        print(json.dumps(rows, default=str, indent=2))
        return 0

    if not rows:
        print("no matching events in orchestrator_event_register.")
        print("An empty register is an honest answer: it means no no-op completion has "
              "been recorded since the register was created. It is NOT the same as the "
              "pre-SD-EVENTREG-1 state, where the question could not be asked at all.")
        return 0

    if args.summary:
        print(f"{'asset_id':<28} {'chart_id':<38} {'verdict':<17} {'n':>5}  last_seen")
        print("-" * 110)
        for r in rows:
            print(f"{str(r['asset_id']):<28} {str(r['chart_id']):<38} "
                  f"{VERDICT.get(r['event_type'], r['event_type']):<17} "
                  f"{r['events']:>5}  {r['last_seen']}")
        print(f"\n{len(rows)} group(s).")
        return 0

    print(f"{'occurred_at':<34} {'verdict':<17} {'asset_id':<26} "
          f"{'rows':>9} {'left':>5}  chart_id / run_id")
    print("-" * 134)
    for r in rows:
        print(f"{str(r['occurred_at']):<34} "
              f"{VERDICT.get(r['event_type'], r['event_type']):<17} "
              f"{str(r['asset_id']):<26} "
              f"{('' if r['rows_present'] is None else r['rows_present']):>9} "
              f"{('' if r['substeps_remaining'] is None else r['substeps_remaining']):>5}  "
              f"{r['chart_id']} / {r['run_id']}")
    print(f"\n{len(rows)} event(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
