"""
dispatch_sampurti_a6prime_chart1_kshetra.py — SAMPŪRTI A6′: ka_kshetra DHARA rebuild.

A6′ rationale (RESTART EDITION, 2026-08-14, SM-R-4):
  - Prior A6 (crfzx) was dispatched then cancelled at T+12min per SM-R-4 investigation.
  - S7-LOCK hardening (lock_timeout=300s + GUC smoke-log) now deployed.
  - Job resized to 4vCPU/8Gi (SM-R-4 desk directive).
  - ka_kshetra is `incomplete` with 74/534 substeps (SAMPLED-generation, fingerprint
    5d1c656a…). On dispatch, DHARA _RESUME_VERSION 3→4 forces a full 534-substep
    replan. THIS IS EXPECTED AND PRE-AUTHORIZED — not a park trigger.
  - DHARA analytic engine is active (ENGINE_VERSION='analytic', PR #1268 merged).

PRECONDITIONS (enforced by script):
  1. ka_kshetra state IN ('incomplete', 'stale', 'error') — not 'lit' (already done).
  2. No active (planned/running) build_runs for chart_id.
  3. cloud-sql-proxy running on 127.0.0.1:5433; DATABASE_URL set via gcloud secrets.

FM-18: all params have argparse guards; script is headless-safe.

Usage:
    DATABASE_URL=<psql_url> python dispatch_sampurti_a6prime_chart1_kshetra.py
    DATABASE_URL=<psql_url> python dispatch_sampurti_a6prime_chart1_kshetra.py --chart-id <uuid>
    DATABASE_URL=<psql_url> python dispatch_sampurti_a6prime_chart1_kshetra.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-a6prime-chart1-kshetra-dhara"

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
        description="Dispatch SAMPŪRTI A6′ ka_kshetra DHARA rebuild for chart 482012f1"
    )
    parser.add_argument(
        "--chart-id",
        default=CHART_ID,
        help="Chart UUID (default: 482012f1 native chart)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate preconditions and print run_id without committing to DB",
    )
    args = parser.parse_args()
    chart_id = args.chart_id

    import psycopg
    import psycopg.rows

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set. Set via gcloud secrets, never .env.local.", file=sys.stderr)
        sys.exit(1)

    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # Precondition 1: ka_kshetra must NOT be lit (already done).
    cur.execute(
        "SELECT state FROM asset_throughput WHERE chart_id = %s AND asset_id = 'ka_kshetra'",
        (chart_id,),
    )
    row = cur.fetchone()
    if row and row["state"] == "lit":
        print(
            f"[a6prime-dispatch] ka_kshetra is already `lit` for chart {chart_id} — "
            "no rebuild needed. If forcing a rebuild, mark stale first.",
            file=sys.stderr,
        )
        sys.exit(2)
    current_state = row["state"] if row else "NOT_FOUND"
    print(f"[a6prime-dispatch] ka_kshetra state={current_state!r} — proceeding", file=sys.stderr)

    # Precondition 2: No active build_runs.
    cur.execute(
        "SELECT id, state FROM build_runs WHERE chart_id = %s AND state IN ('planned', 'running')",
        (chart_id,),
    )
    active = cur.fetchall()
    if active:
        print(
            f"[a6prime-dispatch] ABORT: {len(active)} active build_run(s) already exist: "
            + ", ".join(f"{r['id'][:8]}…={r['state']}" for r in active),
            file=sys.stderr,
        )
        sys.exit(3)

    run_id = str(uuid.uuid4())
    print(f"[a6prime-dispatch] run_id={run_id}", file=sys.stderr)
    print(f"[a6prime-dispatch] dry_run={args.dry_run}", file=sys.stderr)

    if args.dry_run:
        print(f"[a6prime-dispatch] DRY RUN — no DB changes. Would create run_id={run_id}", file=sys.stderr)
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
    print(f"[a6prime-dispatch] created A6′ ka_kshetra run {run_id}", file=sys.stderr)
    # Print run_id to stdout for capture by conductor.
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
