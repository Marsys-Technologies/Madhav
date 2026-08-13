"""
dispatch_sampurti_a5_chart1_kshetra.py — SAMPŪRTI A5: ka_kshetra fresh rebuild with DHARA engine.

A5 rationale:
  - A4 (exec mv7c5) ran under DHARA analytic engine (ENGINE_VERSION='analytic' live since #1268).
  - A4 deadlocked at 16:05:49Z (21:35 IST 2026-08-13): OperationalError connection lost mid-
    stage5 null replicates. ka_kshetra state='error', rows_written=2,664,555.
  - Advisory locks cleared by recovery session. All DB sessions terminated.
  - A5 restarts from substep 0 (RESUME_VERSION=4 on writer; error->dormant = fresh start).
  - DHARA engine remains live in production (no code changes since #1268 merge).

PRECONDITIONS (verified by conductor before dispatch):
  1. ENGINE_VERSION='analytic' in production (PR #1268 merged + deployed).
  2. Advisory lock count = 0 (all sessions terminated post-deadlock recovery).
  3. No RUNNING Cloud Run execution for brahma-build-pipeline-job.
  4. cloud-sql-proxy running on 127.0.0.1:5433.
  5. No active UTKARSHA lease in CAMPAIGN_COORDINATION.md (L-3 expired 10:00 IST, DEAD).

Usage:
  cd <repo-root>/platform
  DATABASE_URL=... python3 scripts/dispatch_sampurti_a5_chart1_kshetra.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-a5-chart1-kshetra-dhara"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    import psycopg
    import psycopg.rows

    database_url = os.environ["DATABASE_URL"]
    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # Verify advisory locks are clear.
    cur.execute("SELECT count(*) AS cnt FROM pg_locks WHERE locktype='advisory'")
    row = cur.fetchone()
    if row and row["cnt"] > 0:
        raise RuntimeError(
            f"Advisory locks still held (count={row['cnt']}). "
            "Clear all sessions before dispatching."
        )

    # Verify no build_run is currently active.
    cur.execute(
        "SELECT count(*) AS cnt FROM build_runs WHERE state IN ('planned','running')"
    )
    row = cur.fetchone()
    if row and row["cnt"] > 0:
        raise RuntimeError(
            f"Active build_runs found (count={row['cnt']}). "
            "Wait for completion or stop them first."
        )

    # Reset ka_kshetra to dormant so orchestrator treats this as a fresh build.
    cur.execute(
        """INSERT INTO asset_throughput (chart_id, asset_id, state)
           VALUES (%s, 'ka_kshetra', 'dormant')
           ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
           DO UPDATE SET state = 'dormant', last_error = NULL""",
        (CHART_ID,),
    )

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
        (run_id, CHART_ID, json.dumps(["ka_kshetra"]), TRIGGERED_BY),
    )
    cur.execute(
        """INSERT INTO build_run_assets (run_id, asset_id, position, state)
           VALUES (%s, 'ka_kshetra', 0, 'queued')""",
        (run_id,),
    )
    conn.commit()
    conn.close()
    print(f"[a5-dispatch] created SAMPŪRTI A5 ka_kshetra run {run_id}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
