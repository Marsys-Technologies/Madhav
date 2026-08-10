"""
dispatch_sampurti_p_g1_ka_kshetra_rebuild.py — SAMPŪRTI Wave 1 P-G1 proof rebuild.

Dispatches a ka_kshetra rebuild for chart 482012f1 (Abhisek Mohanty, canonical) to
verify the G1 CLOCKLESS FIELD fix (PR #1139 — stages 0–3 wired into
_optional_stage_plugins in dependency order: stage0→stage2→stage3→stage1).

PRECONDITIONS (verify before running):
  1. cloud-sql-proxy is running on 127.0.0.1:5433 (DATABASE_URL in .env.local).
  2. PR #1139 wiring fix is checked out (sampurti/integration or sampurti-gate-fix worktree).
  3. Wave 0 content fixes (L0e/G8/G10) are deployed in production (confirmed 2026-08-10).
  4. L0 substrate fully built (bg_* assets live in production).

P-G1 ACCEPTANCE CRITERIA (checked by the runner script after build):
  a. kala_field_clocks > 0 rows for chart 482012f1 with Law-1 states.
  b. kala_field_windows populated (from ka_windows computed via ka_kshetra output).
  c. kala_ahead_get returns non-empty windows for chart 482012f1.

Prints run_id to stdout. The invoker then runs:
  cd platform/python-sidecar && python3 -m pipeline.orchestrator.main --run-id <run_id>
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-wave1-p-g1-ka-kshetra-proof"
TARGET_ASSETS = ["ka_kshetra"]

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

    # Pre-flight: asset must exist and have a writer.
    cur.execute(
        "SELECT asset_id, scope, has_writer FROM asset_registry WHERE asset_id = ANY(%s)",
        (TARGET_ASSETS,),
    )
    rows = cur.fetchall()
    found = {r["asset_id"] for r in rows}
    missing = set(TARGET_ASSETS) - found
    if missing:
        raise RuntimeError(f"asset_registry missing rows for: {sorted(missing)}")
    no_writer = [r["asset_id"] for r in rows if not r["has_writer"]]
    if no_writer:
        raise RuntimeError(f"asset_registry rows with has_writer=false: {sorted(no_writer)}")

    # Reset to dormant so orchestrator treats this as a genuine rebuild.
    for asset_id in TARGET_ASSETS:
        cur.execute(
            """INSERT INTO asset_throughput (chart_id, asset_id, state)
               VALUES (%s, %s, 'dormant')
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'dormant', last_error = NULL""",
            (CHART_ID, asset_id),
        )

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset', %s, 'rebuild', %s, 'planned', %s)""",
        (run_id, CHART_ID, TARGET_ASSETS[0], json.dumps(TARGET_ASSETS), TRIGGERED_BY),
    )
    for position, asset_id in enumerate(TARGET_ASSETS):
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, %s, 'queued')""",
            (run_id, asset_id, position),
        )
    conn.commit()
    conn.close()
    print(
        f"[dispatch] created SAMPURTI P-G1 ka_kshetra rebuild run {run_id} for chart 482012f1",
        file=sys.stderr,
    )
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
