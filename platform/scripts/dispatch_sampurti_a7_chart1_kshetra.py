"""
dispatch_sampurti_a7_chart1_kshetra.py — SAMPŪRTI A7 Pūrṇa Build: ka_kshetra 27-class tiered.

A7 rationale (PURNA_KSHETRA_PLAN_v1_1.md §3 P-C, 2026-08-14, SM-R-10):
  - All P-B lanes merged: L-ENGINE (#1277), L-NULL (#1278), L-TIER (#1279), FM-23 (#1271),
    P3-b serving suppression (#1281 or similar).
  - Migration 571 deployed: ka_kshetra_tier_basis (27-row tier-basis, PRATINIDHI-ratified).
  - _RESUME_VERSION 5→6 (L-NULL PR #1278): forces a full fresh 27-class replan.
    THIS IS EXPECTED AND PRE-AUTHORIZED — not a park trigger.
  - ENGINE_VERSION='analytic' (the only live path).
  - Tier-aware writer: 6 calibrated classes (full C-1 guard), 19 shape_only (synthetic
    SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT=1.0, baseline_is_synthetic=TRUE), 2 not_applicable
    (ClassSkipped). P3-b serving suppression deployed: expected_count=None when synthetic.

PRECONDITIONS (enforced by script):
  1. ka_kshetra state NOT 'lit' (already done).
  2. No active (planned/running) build_runs for chart_id.
  3. cloud-sql-proxy running on 127.0.0.1:5433; DATABASE_URL set via gcloud secrets.

FM-18: all params have argparse guards; script is headless-safe.
FM-07: run_id + pid output to stderr immediately on creation; capture to ledger.

Usage:
    DATABASE_URL=<psql_url> python dispatch_sampurti_a7_chart1_kshetra.py
    DATABASE_URL=<psql_url> python dispatch_sampurti_a7_chart1_kshetra.py --chart-id <uuid>
    DATABASE_URL=<psql_url> python dispatch_sampurti_a7_chart1_kshetra.py --dry-run

After running, immediately:
  gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1
  → record execution name to ledger (FM-07).
  → T+3min: verify GUC smoke-log line (idle_in_txn=1800000ms, lock_timeout=300s, SET LOCAL).
  → Rate gate: >90min total → clean stop + cProfile ONE substep + diagnosis.
  → FM-21 HARD trigger: past T+35min with zero substep progress → recovery sequence.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-a7-chart1-kshetra-purna"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dispatch SAMPŪRTI A7 Pūrṇa ka_kshetra 27-class tiered build for chart 482012f1"
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

    # Precondition 1: ka_kshetra must NOT be lit.
    cur.execute(
        "SELECT state FROM asset_throughput WHERE chart_id = %s AND asset_id = 'ka_kshetra'",
        (chart_id,),
    )
    row = cur.fetchone()
    if row and row["state"] == "lit":
        print(
            f"[a7-dispatch] ka_kshetra is already `lit` for chart {chart_id} — "
            "no rebuild needed. If forcing a rebuild, mark stale first.",
            file=sys.stderr,
        )
        sys.exit(2)
    current_state = row["state"] if row else "NOT_FOUND"
    print(f"[a7-dispatch] ka_kshetra state={current_state!r} — proceeding", file=sys.stderr)

    # Precondition 2: No active build_runs.
    cur.execute(
        "SELECT id, state FROM build_runs WHERE chart_id = %s AND state IN ('planned', 'running')",
        (chart_id,),
    )
    active = cur.fetchall()
    if active:
        print(
            f"[a7-dispatch] ABORT: {len(active)} active build_run(s) already exist: "
            + ", ".join(f"{r['id'][:8]}…={r['state']}" for r in active),
            file=sys.stderr,
        )
        sys.exit(3)

    run_id = str(uuid.uuid4())
    print(f"[a7-dispatch] run_id={run_id}", file=sys.stderr)
    print(f"[a7-dispatch] dry_run={args.dry_run}", file=sys.stderr)

    if args.dry_run:
        print(f"[a7-dispatch] DRY RUN — no DB changes. Would create run_id={run_id}", file=sys.stderr)
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
    print(f"[a7-dispatch] created A7 Pūrṇa ka_kshetra run {run_id}", file=sys.stderr)
    # FM-07: run_id to stdout for capture by conductor.
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
