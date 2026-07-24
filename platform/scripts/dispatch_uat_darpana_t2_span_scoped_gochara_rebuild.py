"""
dispatch_uat_darpana_t2_span_scoped_gochara_rebuild.py — Stage 4 T-2 dispatch.

UAT_BATTERY_v1_0.md (stamped 2026-07-24) requires live gochara/transit serving
across: the named LEL specimen years (2010-11 windfall, 2013 marriage — already
tier-0 priority in ka_gochara_sweep's dispatch-order sort key), the remaining
scoring-span years through 2027 (tier-1, S3-01/S3-02/S3-04/S3-05/S3-08/SN-01
all bear on 2026-2027), and the forward-span years covering Ketu MD onset and
the Venus MD window 2033-2036 (SN-02/SN-03; tier-3).

HONEST SCOPE NOTE (recorded here, not silently assumed): `ka_gochara_sweep`'s
`plan_substeps` (services/ka_gochara_sweep/writer.py `_substep_sort_key`)
already prioritizes exactly the tiers this dispatch needs (specimen years,
then scoring-span, then forward-span) — but it does not expose an arbitrary
"only these calendar years" filter; a full run still plans one substep per
(event_class x year) across the whole birth->birth+100y grid, just processed
in this priority order. The native's own optimization ruling's "~10-14 years,
~2.5-3.5h" estimate assumes a narrower selective-year capability that does not
exist in the current writer. Adding one would be a real writer-logic change
requiring review, not a bounded data-only dispatch — correctly out of this
script's scope. This dispatch therefore runs the EXISTING prioritized sweep
and is monitored/stopped once the battery's actually-needed years show live
served data, rather than run to full completion. 165 substeps / 3227 rows
already banked in build_substep_progress from prior attempts resume cleanly.

Follows the established dispatch-script precedent in this directory. Abhisek's
chart (482012f1) ONLY.

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage:
  cd <repo-root>/platform
  python3 scripts/dispatch_uat_darpana_t2_span_scoped_gochara_rebuild.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "uat-darpana-stage4-t2-span-scoped-gochara-rebuild"
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
    # build_substep_progress (the real resumption ledger) is untouched here —
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
    print(f"[dispatch] created UAT-DARPANA T-2 span-scoped gochara rebuild build_run {run_id}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
