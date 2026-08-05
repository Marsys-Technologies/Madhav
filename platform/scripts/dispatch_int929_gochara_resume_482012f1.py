"""
dispatch_int929_gochara_resume_482012f1.py -- int-929 relay-resume session.

Resumes `ka_gochara_sweep` for chart 482012f1-710e-4a25-994a-93821f5871aa
(Abhisek Mohanty), one of the two canonical operator charts. This is a
routine continuation dispatch: the prior run (executions -zjwvn/-gbnsd,
2026-08-02 14:23-20:23 UTC) completed its 6h container budget successfully
(Cloud Run status: Completed/True) with 117/606 ka_gochara_sweep substeps
committed (verified via build_substep_progress, filtered to asset_id =
'ka_gochara_sweep' -- an unfiltered count also picks up 61 unrelated
week-old ka_sangam rows for this chart_id). 489 substeps remain. No new
dispatch had been queued since the prior run finished (~13h idle), which is
the reason for this resume -- not a failure or eviction.

Follows the established dispatch-script precedent in this directory (same
asset_throughput-dormant-reset + build_runs/build_run_assets insert shape as
dispatch_elev_beta_t_gochara_resume.py / dispatch_uat_darpana_t2_span_scoped_
gochara_rebuild.py / dispatch_shaddarshana_c2_gochara_resume_1c826d5a.py).
build_substep_progress (the real resumption ledger) is untouched here --
already-completed (event_class, year) substeps resume from there per the
writer's own idempotent replan path.

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_int929_gochara_resume_482012f1.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "int-929-gochara-relay-resume-482012f1"
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
    print(f"[dispatch] created int-929 gochara-resume build_run {run_id} (chart 482012f1)", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
