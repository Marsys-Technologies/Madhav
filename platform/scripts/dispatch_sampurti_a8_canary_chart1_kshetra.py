"""
dispatch_sampurti_a8_canary_chart1_kshetra.py — SAMPŪRTI A8 CANARY: 1-class timing gate.

F3 (SM-R-11) CANARY GATE — validates F1+F2+F5 performance before A8 full dispatch.

Rationale:
  F1 (dhara_compute_null C/E decomposition) + F2 (split substeps) target:
    stage5dhara:CAREER:1 (null)    < 5 min   (was 90+ min before F1)
    stage5dhara:CAREER:2 (windows) < 5 min
    Total CAREER class              < 12 min  (well inside 15-min reaper window)
  If CAREER passes within these gates → proceed to A8 full dispatch.
  If CAREER exceeds 15 min → stop; diagnose before full run.

What this script does:
  1. Checks preconditions: no active build_run; ka_kshetra NOT lit.
  2. Creates a build_run tagged 'sampurti-a8-canary' with ka_kshetra scope.
  3. Prints the gcloud command with --update-env-vars SAMPURTI_CANARY_CLASSES=CAREER
     that invokes the writer with only the CAREER event class discovered.

CANARY GATE PROTOCOL (conductor follow-up):
  T+0  : Execute: gcloud run jobs execute brahma-build-pipeline-job
           --region=asia-south1
           --update-env-vars SAMPURTI_CANARY_CLASSES=CAREER,RUN_ID=<run_id>
  T+3  : Check GUC smoke-log (lock_timeout=300s, idle_in_txn=1800000ms).
  T+5  : stage5dhara:CAREER:1 (null) should be COMPLETE in build_substep_progress.
  T+10 : stage5dhara:CAREER:2 (windows) should be COMPLETE.
  T+12 : If both chunks COMPLETE → CANARY GREEN → proceed to A8 full dispatch.
  T+15 : FM-21 HARD trigger: zero progress past 15 min → stop and diagnose.

After CANARY GREEN → run dispatch_sampurti_a8_full_chart1_kshetra.py.

PRECONDITIONS (enforced by script):
  1. ka_kshetra state NOT 'lit'.
  2. No active (planned/running) build_runs for chart_id.
  3. cloud-sql-proxy running on 127.0.0.1:5433; DATABASE_URL set via gcloud secrets.

FM-07: run_id output to stderr immediately on creation.
FM-18: all params have argparse guards; script is headless-safe.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
CANARY_CLASS = "CAREER"
TRIGGERED_BY = "sampurti-a8-canary-chart1-kshetra"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dispatch SAMPŪRTI A8 CANARY 1-class timing gate for chart 482012f1"
    )
    parser.add_argument(
        "--chart-id",
        default=CHART_ID,
        help="Chart UUID (default: 482012f1 native chart)",
    )
    parser.add_argument(
        "--canary-class",
        default=CANARY_CLASS,
        help=f"Event class to canary (default: {CANARY_CLASS!r})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate preconditions and print run_id without committing to DB",
    )
    args = parser.parse_args()
    chart_id = args.chart_id
    canary_class = args.canary_class

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
            f"[a8-canary] ka_kshetra is already `lit` for chart {chart_id} — "
            "mark stale first if forcing a rebuild.",
            file=sys.stderr,
        )
        sys.exit(2)
    current_state = row["state"] if row else "NOT_FOUND"
    print(f"[a8-canary] ka_kshetra state={current_state!r} — proceeding", file=sys.stderr)

    # Precondition 2: No active build_runs.
    cur.execute(
        "SELECT id, state FROM build_runs WHERE chart_id = %s AND state IN ('planned', 'running')",
        (chart_id,),
    )
    active = cur.fetchall()
    if active:
        print(
            f"[a8-canary] ABORT: {len(active)} active build_run(s) already exist: "
            + ", ".join(f"{r['id'][:8]}…={r['state']}" for r in active),
            file=sys.stderr,
        )
        sys.exit(3)

    run_id = str(uuid.uuid4())
    print(f"[a8-canary] run_id={run_id}", file=sys.stderr)
    print(f"[a8-canary] canary_class={canary_class!r}", file=sys.stderr)
    print(f"[a8-canary] dry_run={args.dry_run}", file=sys.stderr)

    if args.dry_run:
        print(f"[a8-canary] DRY RUN — no DB changes. Would create run_id={run_id}", file=sys.stderr)
        conn.close()
        print(run_id, flush=True)
        _print_gcloud_command(run_id, canary_class)
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
    print(f"[a8-canary] created A8 CANARY run {run_id}", file=sys.stderr)
    # FM-07: run_id to stdout for capture by conductor.
    print(run_id, flush=True)
    _print_gcloud_command(run_id, canary_class)


def _print_gcloud_command(run_id: str, canary_class: str) -> None:
    print(
        f"\n[a8-canary] EXECUTE CANARY (copy-paste to conductor terminal):\n"
        f"  gcloud run jobs execute brahma-build-pipeline-job \\\n"
        f"    --region=asia-south1 \\\n"
        f"    --update-env-vars SAMPURTI_CANARY_CLASSES={canary_class},RUN_ID={run_id}\n"
        f"\n[a8-canary] CANARY GATE PROTOCOL:\n"
        f"  T+5  : stage5dhara:{canary_class}:1 (null) COMPLETE in build_substep_progress\n"
        f"  T+10 : stage5dhara:{canary_class}:2 (windows) COMPLETE\n"
        f"  T+12 : CANARY GREEN → run dispatch_sampurti_a8_full_chart1_kshetra.py\n"
        f"  T+15 : FM-21 HARD: zero progress → stop, diagnose, do NOT dispatch full run",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
