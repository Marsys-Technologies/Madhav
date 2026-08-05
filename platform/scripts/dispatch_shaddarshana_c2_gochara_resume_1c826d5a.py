"""
dispatch_shaddarshana_c2_gochara_resume_1c826d5a.py -- SAMĀPTI conductor lane
C2-GOCHARA-RUN, dispatch 1 of ~3 (per GOCHARA_PARITY_DIAGNOSIS_v1_0.md §5,
branch samapti/gochara-parity, commit d5907e64).

Resumes `ka_gochara_sweep` for chart 1c826d5a-41cb-4450-b4dc-59d440e5f75a
(Abhinandan Mohanty), one of the two canonical operator charts. Root cause
(GOCH-1, diagnosed 2026-07-30): the asset is NOT stalling or defective -- it
is evicted by its own writer_timeout_seconds=21600 (6h) budget at exactly
the point 6h of compute buys, against a ~22h full-plan cost (303 substeps
x ~255-280s each). This chart has received exactly ONE productive dispatch
(78/303 substeps committed) and was correctly PARKED-HONEST on 2026-07-28
pending this diagnosis. The diagnosis's own §5 completion plan says C2 may
now proceed: ~3 resumed dispatches needed (225 remaining substeps), one at
a time, waiting for each to finish before the next, with a progress
assertion (>=40 substeps gained) gating continuation.

This script performs ONE dispatch only (per the plan's own "one at a time"
discipline) and does not loop. build_substep_progress (the resumption
ledger) is left untouched -- already-completed (event_class, year)
substeps resume from there per the writer's own idempotent replan path.
No row in kala_gochara_windows or build_substep_progress is touched here;
only asset_throughput (reset dormant) + build_runs + build_run_assets are
written, per the established dispatch-script precedent in this directory
(dispatch_elev_beta_t_gochara_resume.py, dispatch_uat_darpana_t2_span_scoped_
gochara_rebuild.py).

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_shaddarshana_c2_gochara_resume_1c826d5a.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
TRIGGERED_BY = "shad-darshana-c2-gochara-parity-resume-1c826d5a"
TARGET_ASSETS = ["ka_gochara_sweep"]

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

    cur.execute(
        "SELECT asset_id, scope FROM asset_registry WHERE asset_id = ANY(%s)",
        (TARGET_ASSETS,),
    )
    rows = cur.fetchall()
    found = {r["asset_id"] for r in rows}
    missing = set(TARGET_ASSETS) - found
    if missing:
        raise RuntimeError(f"asset_registry missing rows for: {sorted(missing)}")

    # Reset to dormant so the orchestrator treats this as a genuine (resumable)
    # rebuild attempt rather than skipping a chart already in 'error' state.
    # build_substep_progress (the real resumption ledger) is untouched here --
    # already-completed (event_class, year) substeps resume from there.
    cur.execute(
        """INSERT INTO asset_throughput (chart_id, asset_id, state)
           VALUES (%s, %s, 'dormant')
           ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
           DO UPDATE SET state = 'dormant', last_error = NULL""",
        (CHART_ID, "ka_gochara_sweep"),
    )

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'rebuild', %s, 'planned', %s)""",
        (run_id, CHART_ID, json.dumps(TARGET_ASSETS), TRIGGERED_BY),
    )
    cur.execute(
        """INSERT INTO build_run_assets (run_id, asset_id, position, state)
           VALUES (%s, %s, 0, 'queued')""",
        (run_id, "ka_gochara_sweep"),
    )
    conn.commit()
    conn.close()
    print(f"[dispatch] created shad-darshana C2 gochara-resume build_run {run_id}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
