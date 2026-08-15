"""
dispatch_ekv_e03_gochara_canary_482012f1.py — EKV E-03 GOCHARA CANARY DISPATCH.

Creates a build_run for `ka_gochara` (chart 482012f1) and prints the gcloud execute
command for E-03 Stream operator.

This is the CANARY step. The actual canary validation (F-52: nodal terms in MARRIAGE
window) is performed MANUALLY after the build completes — see EKV_E03_GOCHARA_REBUILD_RUNBOOK.md
Step 2. `ka_gochara` does not support a class-filter env var, so the "canary" here means
dispatching a limited rebuild and then asserting the F-52 criterion before proceeding to the
full dispatch.

WHAT THIS SCRIPT DOES:
  1. Checks preconditions: no active/planned build_run for this chart; `ka_gochara` NOT lit
     (or force-rebuild if --force flag given).
  2. Creates a build_run tagged 'ekv-e03-gochara-canary-482012f1'.
  3. Prints the gcloud run jobs execute command to stdout for copy-paste by E-03 operator.

PRECONDITIONS (enforced):
  1. cloud-sql-proxy running on 127.0.0.1:5433; DATABASE_URL set via gcloud secrets.
  2. B-01/02/03/04 lanes merged to main and deployed.
  3. `ka_gochara` state is NOT 'lit', OR --force flag is given.
  4. No active (planned/running) build_runs for this chart_id.

After CANARY BUILD COMPLETES → run F-52 verification (see runbook Step 2).
If F-52 PASSES → run dispatch_ekv_e03_gochara_full_482012f1.py.

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
ASSET_ID = "ka_gochara"
TRIGGERED_BY = "ekv-e03-gochara-canary-482012f1"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dispatch EKV E-03 gochara canary build for chart 482012f1"
    )
    parser.add_argument(
        "--chart-id",
        default=CHART_ID,
        help="Chart UUID (default: 482012f1 native chart)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow dispatch even if ka_gochara is already 'lit' (marks dormant first)",
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
        print(
            "ERROR: DATABASE_URL not set. Obtain via: "
            "gcloud secrets versions access latest --secret=DATABASE_URL --project=<project>",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # Precondition 1: ka_gochara must NOT be lit (unless --force).
    cur.execute(
        "SELECT state FROM asset_throughput WHERE chart_id = %s AND asset_id = %s",
        (chart_id, ASSET_ID),
    )
    row = cur.fetchone()
    current_state = row["state"] if row else "NOT_FOUND"
    if current_state == "lit" and not args.force:
        print(
            f"[ekv-e03-canary] {ASSET_ID} is already 'lit' for chart {chart_id}. "
            "Pass --force to mark dormant and force a canary rebuild.",
            file=sys.stderr,
        )
        sys.exit(2)
    print(
        f"[ekv-e03-canary] {ASSET_ID} state={current_state!r} — proceeding",
        file=sys.stderr,
    )

    # Precondition 2: No active build_runs.
    cur.execute(
        "SELECT id, state FROM build_runs WHERE chart_id = %s AND state IN ('planned', 'running')",
        (chart_id,),
    )
    active = cur.fetchall()
    if active:
        print(
            f"[ekv-e03-canary] ABORT: {len(active)} active build_run(s) exist: "
            + ", ".join(f"{r['id'][:8]}...={r['state']}" for r in active),
            file=sys.stderr,
        )
        sys.exit(3)

    run_id = str(uuid.uuid4())
    print(f"[ekv-e03-canary] run_id={run_id}", file=sys.stderr)
    print(f"[ekv-e03-canary] dry_run={args.dry_run}", file=sys.stderr)

    if args.dry_run:
        print(
            f"[ekv-e03-canary] DRY RUN — no DB changes. Would create run_id={run_id}",
            file=sys.stderr,
        )
        conn.close()
        print(run_id, flush=True)
        _print_gcloud_command(run_id)
        return

    # If --force and currently lit, mark dormant so orchestrator treats as genuine rebuild.
    if current_state == "lit" and args.force:
        cur.execute(
            """INSERT INTO asset_throughput (chart_id, asset_id, state)
               VALUES (%s, %s, 'dormant')
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'dormant', last_error = NULL""",
            (chart_id, ASSET_ID),
        )
        print(
            f"[ekv-e03-canary] --force: marked {ASSET_ID} dormant for chart {chart_id}",
            file=sys.stderr,
        )

    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset', %s, 'rebuild', %s, 'planned', %s)""",
        (run_id, chart_id, ASSET_ID, json.dumps([ASSET_ID]), TRIGGERED_BY),
    )
    cur.execute(
        """INSERT INTO build_run_assets (run_id, asset_id, position, state)
           VALUES (%s, %s, 0, 'queued')""",
        (run_id, ASSET_ID),
    )
    conn.commit()
    conn.close()
    print(
        f"[ekv-e03-canary] created EKV E-03 gochara CANARY run {run_id} for chart 482012f1",
        file=sys.stderr,
    )
    # FM-07: run_id to stdout for capture by conductor.
    print(run_id, flush=True)
    _print_gcloud_command(run_id)


def _print_gcloud_command(run_id: str) -> None:
    print(
        f"\n[ekv-e03-canary] EXECUTE CANARY (copy-paste to operator terminal):\n"
        f"  gcloud run jobs execute brahma-build-pipeline-job \\\n"
        f"    --region=asia-south1 \\\n"
        f"    --update-env-vars RUN_ID={run_id}\n"
        f"\n[ekv-e03-canary] CANARY GATE PROTOCOL (see EKV_E03_GOCHARA_REBUILD_RUNBOOK.md):\n"
        f"  T+0   : Execute the gcloud command above\n"
        f"  T+5   : Check build_substep_progress for ka_gochara substep rows\n"
        f"  T+35  : STALL GATE — if ZERO new substep rows since T+0 → stop + diagnose\n"
        f"  DONE  : Run F-52 verification (see runbook Step 2)\n"
        f"  F-52 PASS : Run dispatch_ekv_e03_gochara_full_482012f1.py\n"
        f"  F-52 FAIL : STOP — diagnose before full dispatch",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
