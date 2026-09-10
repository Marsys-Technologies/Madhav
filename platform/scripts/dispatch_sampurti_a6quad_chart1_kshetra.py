#!/usr/bin/env python3
"""
SAMPURTI A6⁴ dispatch: ka_kshetra DHARA field build — OPT-N3 code.

OPT-N3 changes deployed:
  - DEFAULT_REPLICATES 1024→256 (~8min/class instead of ~34min)
  - SET LOCAL idle_in_transaction_session_timeout=0 in _run_stage5dhara
  - FakeConn SET handler for tests

Preconditions (enforced):
  1. ka_kshetra state != 'lit'
  2. No active build_runs (state in planned/running)
  3. advisory_locks = 0

Usage:
    python platform/scripts/dispatch_sampurti_a6quad_chart1_kshetra.py [--dry-run]

SAMPURTI-CONDUCTOR R40 — A6⁴ dispatch
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-a6quad-chart1-kshetra-dhara"

# Auto-load .env.local if present
_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch SAMPŪRTI A6⁴ ka_kshetra DHARA rebuild")
    parser.add_argument("--chart-id", default=CHART_ID)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    chart_id = args.chart_id

    import psycopg
    import psycopg.rows

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set.", file=sys.stderr)
        sys.exit(1)

    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # 1. Check ka_kshetra is not already lit
    cur.execute(
        "SELECT state FROM asset_throughput WHERE chart_id=%s AND asset_id='ka_kshetra'",
        (chart_id,),
    )
    row = cur.fetchone()
    if row and row["state"] == "lit":
        print("[a6quad-dispatch] ka_kshetra already lit — no rebuild needed.", file=sys.stderr)
        sys.exit(2)
    current_state = row["state"] if row else "NOT_FOUND"
    print(f"[a6quad-dispatch] ka_kshetra state={current_state!r} — proceeding", file=sys.stderr)

    # 2. Check no active build_runs
    cur.execute(
        "SELECT id, state FROM build_runs WHERE chart_id=%s AND state IN ('planned','running')",
        (chart_id,),
    )
    active = cur.fetchall()
    if active:
        print(
            f"[a6quad-dispatch] ABORT: {len(active)} active build_run(s): {[r['id'] for r in active]}",
            file=sys.stderr,
        )
        sys.exit(3)

    # 3. Check advisory locks = 0
    cur.execute("SELECT count(*) AS n FROM pg_locks WHERE locktype='advisory'")
    lock_count = cur.fetchone()["n"]
    if lock_count > 0:
        print(f"[a6quad-dispatch] ABORT: {lock_count} advisory lock(s) still held", file=sys.stderr)
        sys.exit(4)

    run_id = str(uuid.uuid4())
    print(f"[a6quad-dispatch] run_id={run_id}", file=sys.stderr)
    print(f"[a6quad-dispatch] triggered_by={TRIGGERED_BY}", file=sys.stderr)
    print(f"[a6quad-dispatch] dry_run={args.dry_run}", file=sys.stderr)

    if args.dry_run:
        print("[a6quad-dispatch] DRY RUN — no DB changes.", file=sys.stderr)
        conn.close()
        print(run_id, flush=True)
        return

    cur.execute(
        """INSERT INTO build_runs
               (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
        (run_id, chart_id, json.dumps(["ka_kshetra"]), TRIGGERED_BY),
    )
    conn.commit()
    conn.close()
    print(f"[a6quad-dispatch] created A6⁴ ka_kshetra run {run_id}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
