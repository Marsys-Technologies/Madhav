"""
dispatch_elev_beta_t_gochara_resume.py — Elevation Campaign v2.1, Stream beta, Lane T
(timing residuals / gochara env / CR-131 sweep completion).

Resumes `ka_gochara_sweep` for chart 482012f1 (Abhisek). CURRENT_STATE A-3/CR-131's last
known figure ("165/300") is stale by this lane's own live re-check: as of dispatch time
this session, `build_substep_progress` already holds 174/303 substeps (career_advancement
86, major_gain 44, marriage 44 -- 3 event classes x 101 years = 303, matching the T-2
correct-span replan size from PRE_DARPANA_READINESS_v2_0.md W-1/T-2, not the old 300).
The most recent dispatch (build_run 8fd6bcf7, triggered_by
"uat-darpana-stage4-t2-span-scoped-gochara-rebuild") hit the Cloud Run job's 21600s (6h)
wall-clock ceiling and self-reported state='error' with an honest
"BLOCKED: upstream dependency(ies) timeout" -- ka_gochara_resonance (the sole real
dependency) is itself long since 'lit' (80 rows, built 2026-07-20), so this is the
outer run's own timeout being surfaced generically, not a genuine blocked dependency.

Measured completion rate this session (median substep-to-substep delta across the last
~175 completions, excluding the two run-restart gaps): ~4.1-4.65 min/substep -- i.e. the
"~600x faster post-memoization" resume estimate in circulation is FALSE; the real speedup
over the pre-T-2-fix baseline is closer to ~6x (matching the charter's own framing). At
this rate, 303-174=129 remaining substeps project to ~8.9h -- more than one 6h Cloud Run
dispatch, so this lane resumes+monitors+parks with an ETA rather than claiming completion.

Follows the established dispatch-script precedent in this directory (same
asset_throughput-dormant-reset + build_runs/build_run_assets insert shape as
dispatch_uat_darpana_t2_span_scoped_gochara_rebuild.py); build_substep_progress (the real
resumption ledger) is untouched here -- already-completed (event_class, year) substeps
resume from there per the writer's own idempotent replan path.

Abhisek's chart (482012f1) ONLY.

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_elev_beta_t_gochara_resume.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "elev-v2-1-beta-T-gochara-timing-resume"
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
    print(f"[dispatch] created elev-v2.1 beta:T gochara-resume build_run {run_id}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
