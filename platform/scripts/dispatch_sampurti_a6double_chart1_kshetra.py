"""
dispatch_sampurti_a6double_chart1_kshetra.py — SAMPŪRTI A6″: ka_kshetra DHARA rebuild.

A6″ rationale (2026-08-14, SM-R-6, R40):
  - A6′ (vcc6h) ran 9h on stage-5 because dhara_null.py was imported by NOTHING in
    production — only dhara_sweep was wired (SM-R-6 root cause, F-13).
  - OPT-N1 (PR #1272) wires dhara_compute_null into the stage-5 analytic path.
  - _RESUME_VERSION 4→5 (FM-17) forces a full replan — vcc6h checkpoint abandoned.
  - New stage-5 plan: one stage5dhara:{ec} substep per class (1024-replicate vectorized
    null in-process, F-01 corrected) vs old 8 blocks + finalize (~9h → ~30-60min).
  - Advisory locks: 0 (vcc6h sessions drained via idle_in_txn_timeout at 22:49Z).
  - Deploy to Cloud Run completed at 23:59Z with OPT-N1 code.

PRECONDITIONS (enforced by script):
  1. ka_kshetra state IN ('incomplete', 'stale', 'error') — not 'lit' (already done).
  2. No active (planned/running) build_runs for chart_id.
  3. cloud-sql-proxy running on 127.0.0.1:5433; DATABASE_URL set.

FM-18: all params have argparse guards; script is headless-safe.

Usage:
    DATABASE_URL=<psql_url> python dispatch_sampurti_a6double_chart1_kshetra.py
    DATABASE_URL=<psql_url> python dispatch_sampurti_a6double_chart1_kshetra.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-a6double-chart1-kshetra-dhara"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dispatch SAMPŪRTI A6″ ka_kshetra DHARA rebuild for chart 482012f1"
    )
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

    cur.execute(
        "SELECT state FROM asset_throughput WHERE chart_id = %s AND asset_id = 'ka_kshetra'",
        (chart_id,),
    )
    row = cur.fetchone()
    if row and row["state"] == "lit":
        print(f"[a6double-dispatch] ka_kshetra is already `lit` — no rebuild needed.", file=sys.stderr)
        sys.exit(2)
    current_state = row["state"] if row else "NOT_FOUND"
    print(f"[a6double-dispatch] ka_kshetra state={current_state!r} — proceeding", file=sys.stderr)

    cur.execute(
        "SELECT id, state FROM build_runs WHERE chart_id = %s AND state IN ('planned', 'running')",
        (chart_id,),
    )
    active = cur.fetchall()
    if active:
        print(
            f"[a6double-dispatch] ABORT: {len(active)} active build_run(s) exist",
            file=sys.stderr,
        )
        sys.exit(3)

    run_id = str(uuid.uuid4())
    print(f"[a6double-dispatch] run_id={run_id}", file=sys.stderr)
    print(f"[a6double-dispatch] dry_run={args.dry_run}", file=sys.stderr)

    if args.dry_run:
        print(f"[a6double-dispatch] DRY RUN — no DB changes.", file=sys.stderr)
        conn.close()
        print(run_id, flush=True)
        return

    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
        (run_id, chart_id, json.dumps(["ka_kshetra"]), TRIGGERED_BY),
    )
    cur.execute(
        """INSERT INTO build_run_assets (run_id, asset_id, position, state)
           VALUES (%s, 'ka_kshetra', 0, 'queued')""",
        (run_id,),
    )
    conn.commit()
    conn.close()
    print(f"[a6double-dispatch] created A6″ ka_kshetra run {run_id}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
