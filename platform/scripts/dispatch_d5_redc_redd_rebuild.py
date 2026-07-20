"""
dispatch_d5_redc_redd_rebuild.py — D-5 post-gate_run_2 REBUILD after RED-C
(PR #650, 86a82ca5) and RED-D (PR #651, d2d9555e) both merged+deployed.

TARGET_ASSETS = ["ka_gochara_sweep"] only, per BIND_D-5 §6's minimal-cascade
ruling (STATE_D-5.md `rebuild.scope`): RED-C's fix lives entirely in
ka_gochara_sweep's own writer/sweep/shape_output modules; RED-D's fix lives
in gochara_grammar/gochara_intensity, which ka_gochara_sweep CONSUMES but
which are not themselves WriterBase assets with their own asset_registry
row -- ka_gochara_sweep is the sole served-data asset whose rows change.
ka_gochara_resonance (G-1, state='lit', 80 rows) is untouched by either fix
and is NOT rebuilt (asset_registry.depends_on confirms ka_gochara_sweep's
only dependency). writer.py's own _RESUME_VERSION bump (4->5, RED-C v4)
already forces a full delete-and-replan on next dispatch regardless of
asset_throughput.state, so this script's job is purely to create the
build_run/build_run_assets rows and hand off to the Cloud Run job -- same
precedent pattern as dispatch_d3_perfcache_rebuild.py.

Abhisek's chart (482012f1) ONLY; Abhinandan is never rebuilt (CR-87 guard).

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_d5_redc_redd_rebuild.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "d5-redc-redd-post-merge-rebuild"
TARGET_ASSETS = ["ka_gochara_sweep"]


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

    for asset_id in TARGET_ASSETS:
        cur.execute(
            """INSERT INTO asset_throughput (chart_id, asset_id, state)
               VALUES (%s, %s, 'dormant')
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
            (CHART_ID, asset_id),
        )

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'rebuild', %s, 'planned', %s)""",
        (run_id, CHART_ID, json.dumps(TARGET_ASSETS), TRIGGERED_BY),
    )
    for position, asset_id in enumerate(TARGET_ASSETS):
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, %s, 'queued')""",
            (run_id, asset_id, position),
        )
    conn.commit()
    conn.close()
    print(f"[dispatch] created D-5 RED-C/RED-D rebuild build_run {run_id} "
          f"with {len(TARGET_ASSETS)} assets: {TARGET_ASSETS}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
