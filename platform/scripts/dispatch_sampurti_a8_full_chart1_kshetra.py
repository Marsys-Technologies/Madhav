"""
dispatch_sampurti_a8_full_chart1_kshetra.py — SAMPŪRTI A8 Full: ka_kshetra 27-class.

A8 rationale (PURNA_KSHETRA_PLAN_v1_1.md §3 P-C, 2026-08-14, SM-R-11):
  Run AFTER A8 CANARY GREEN (dispatch_sampurti_a8_canary_chart1_kshetra.py).
  - All F-wave PRs merged and deployed: F1+F2+F5 (#1284), F3 (#1285), F4 (#1283).
  - F1: dhara_compute_null C/E decomposition — zero evaluator calls in replicate loop.
  - F2: stage5dhara:{ec} split into :1 (null, commits) + :2 (windows, resume-safe).
  - F5: interior decade knots d·H/10 added to DHARA sweep.
  - F4: main.py no-args guard (exit 2 instead of argparse error).
  - _RESUME_VERSION == 6: forces fresh delete-and-replan for all 27 classes.
  - CANARY GREEN: CAREER class completed within 12 min (F1+F2 confirmed effective).

PRECONDITIONS (enforced by script):
  1. ka_kshetra state NOT 'lit' (mark stale if needed).
  2. No active (planned/running) build_runs for chart_id.
  3. A8 CANARY GREEN confirmed (CAREER:1 + CAREER:2 both complete within 12 min).
  4. cloud-sql-proxy running on 127.0.0.1:5433; DATABASE_URL set via gcloud secrets.

FM-07: run_id output to stderr immediately on creation.
FM-18: all params have argparse guards; script is headless-safe.

After running:
  gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1
  → record execution name to ledger (FM-07).
  → Rate gate: >90 min total (27 classes × ~3 min/class = ~81 min expected)
    → clean stop + diagnose if exceeded.
  → FM-21 HARD trigger: past T+35 min with zero substep progress → recovery.
  → On completion: verify kala_field_null (27 rows) + kala_field_windows written.
  → Post ██ MARKER-POSTED: FIELD-INTEGRATED ██ to unblock Δ3.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-a8-full-chart1-kshetra"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dispatch SAMPŪRTI A8 Full ka_kshetra 27-class build for chart 482012f1"
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
    parser.add_argument(
        "--canary-verified",
        action="store_true",
        default=False,
        help="Confirm A8 CANARY GREEN gate was observed before dispatching full run",
    )
    args = parser.parse_args()
    chart_id = args.chart_id

    if not args.canary_verified and not args.dry_run:
        print(
            "[a8-full] ABORT: --canary-verified flag not set.\n"
            "  Run dispatch_sampurti_a8_canary_chart1_kshetra.py first.\n"
            "  Only pass --canary-verified after observing CANARY GREEN "
            "(CAREER:1 + CAREER:2 both complete within 12 min).",
            file=sys.stderr,
        )
        sys.exit(4)

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
            f"[a8-full] ka_kshetra is already `lit` for chart {chart_id} — "
            "mark stale first if forcing a rebuild.",
            file=sys.stderr,
        )
        sys.exit(2)
    current_state = row["state"] if row else "NOT_FOUND"
    print(f"[a8-full] ka_kshetra state={current_state!r} — proceeding", file=sys.stderr)

    # Precondition 2: No active build_runs.
    cur.execute(
        "SELECT id, state FROM build_runs WHERE chart_id = %s AND state IN ('planned', 'running')",
        (chart_id,),
    )
    active = cur.fetchall()
    if active:
        print(
            f"[a8-full] ABORT: {len(active)} active build_run(s) already exist: "
            + ", ".join(f"{r['id'][:8]}…={r['state']}" for r in active),
            file=sys.stderr,
        )
        sys.exit(3)

    run_id = str(uuid.uuid4())
    print(f"[a8-full] run_id={run_id}", file=sys.stderr)
    print(f"[a8-full] dry_run={args.dry_run}", file=sys.stderr)
    print(f"[a8-full] canary_verified={args.canary_verified}", file=sys.stderr)

    if args.dry_run:
        print(f"[a8-full] DRY RUN — no DB changes. Would create run_id={run_id}", file=sys.stderr)
        conn.close()
        print(run_id, flush=True)
        _print_gcloud_command(run_id)
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
    print(f"[a8-full] created A8 Full ka_kshetra run {run_id}", file=sys.stderr)
    # FM-07: run_id to stdout for capture by conductor.
    print(run_id, flush=True)
    _print_gcloud_command(run_id)


def _print_gcloud_command(run_id: str) -> None:
    print(
        f"\n[a8-full] EXECUTE FULL BUILD (copy-paste to conductor terminal):\n"
        f"  gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1\n"
        f"  → record execution name + run_id={run_id} to ledger (FM-07)\n"
        f"\n[a8-full] MONITORING PROTOCOL:\n"
        f"  T+3    : verify GUC smoke-log (lock_timeout=300s, idle_in_txn=1800000ms)\n"
        f"  T+3–10 : first 2–3 classes (CAREER, EDUCATION, FAMILY) completing\n"
        f"  T+81   : expected completion (27 classes × ~3 min = ~81 min total)\n"
        f"  T+90   : rate gate → clean stop + cProfile ONE substep if exceeded\n"
        f"  T+35   : FM-21 HARD: zero substep progress → recovery sequence\n"
        f"\n[a8-full] ON SUCCESS:\n"
        f"  1. Verify kala_field_null 27 rows + kala_field_windows written\n"
        f"  2. Post ██ MARKER-POSTED: FIELD-INTEGRATED ██ to CAMPAIGN_COORDINATION.md\n"
        f"     to unblock Δ3 PARĪKṢAKA dispatch",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
