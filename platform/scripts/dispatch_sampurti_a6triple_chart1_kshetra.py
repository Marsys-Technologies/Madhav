"""
dispatch_sampurti_a6triple_chart1_kshetra.py — SAMPŪRTI A6‴: ka_kshetra DHARA rebuild.

A6‴ rationale (2026-08-14, R40):
  - A6″ (s27bp) failed at stage5dhara OOM: deploy.yml hardcoded --memory=4Gi --cpu=2,
    overwriting SM-R-4's manual resize to 4vCPU/8Gi when OPT-N1 was deployed.
  - dhara_compute_null with 1024 replicates × 343,973 kala_field segments/class
    exceeded 4Gi container memory limit.
  - Fix: deploy.yml updated to --memory=8Gi --cpu=4; job manually resized to 4vCPU/8Gi.
  - Stage4 data (60 substeps, 2,063,838 kala_field rows) is intact from A6″.
  - OPT-N1 (_RESUME_VERSION=5, fingerprint 0ddbfce7...) will resume from 60/318 substeps
    (all stage4 done, stage5dhara pending for 6 non-skipped classes).

PRECONDITIONS (enforced by script):
  1. ka_kshetra state IN ('incomplete', 'stale', 'error') — not 'lit' (already done).
  2. No active (planned/running) build_runs for chart_id.
  3. DATABASE_URL set (via .env.local or environment).

FM-18: all params have argparse guards; script is headless-safe.

Usage:
    python dispatch_sampurti_a6triple_chart1_kshetra.py
    python dispatch_sampurti_a6triple_chart1_kshetra.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-a6triple-chart1-kshetra-dhara"

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
        description="Dispatch SAMPŪRTI A6‴ ka_kshetra DHARA rebuild for chart 482012f1"
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
        print("[a6triple-dispatch] ka_kshetra is already `lit` — no rebuild needed.", file=sys.stderr)
        sys.exit(2)
    current_state = row["state"] if row else "NOT_FOUND"
    print(f"[a6triple-dispatch] ka_kshetra state={current_state!r} — proceeding", file=sys.stderr)

    cur.execute(
        "SELECT id, state FROM build_runs WHERE chart_id = %s AND state IN ('planned', 'running')",
        (chart_id,),
    )
    active = cur.fetchall()
    if active:
        print(
            f"[a6triple-dispatch] ABORT: {len(active)} active build_run(s) exist: {[r['id'] for r in active]}",
            file=sys.stderr,
        )
        sys.exit(3)

    # Verify advisory lock is clear
    cur2 = conn.cursor()
    cur2.execute("SELECT count(*) AS n FROM pg_locks WHERE locktype='advisory'")
    lock_count = cur2.fetchone()['n']
    if lock_count > 0:
        print(f"[a6triple-dispatch] ABORT: {lock_count} advisory lock(s) still held", file=sys.stderr)
        sys.exit(4)

    run_id = str(uuid.uuid4())
    print(f"[a6triple-dispatch] run_id={run_id}", file=sys.stderr)
    print(f"[a6triple-dispatch] triggered_by={TRIGGERED_BY}", file=sys.stderr)
    print(f"[a6triple-dispatch] dry_run={args.dry_run}", file=sys.stderr)

    if args.dry_run:
        print("[a6triple-dispatch] DRY RUN — no DB changes.", file=sys.stderr)
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
    print(f"[a6triple-dispatch] created A6\u2034 ka_kshetra run {run_id}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
