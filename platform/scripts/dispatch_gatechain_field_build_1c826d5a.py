"""
dispatch_gatechain_field_build_1c826d5a.py — Track T2 gate-chain pre-staging.

STAGED, NOT EXECUTED. Sibling of `dispatch_gatechain_field_build_482012f1.py`
in this directory — same rationale, same preconditions, same TARGET_ASSETS
order, targeting the SECOND canonical chart (Abhinandan Mohanty) instead.
Read that file's module docstring for the full rationale; this docstring
only states what differs.

WHAT IT BUILDS: `ka_kshetra` then `mi_bhara`, in that order, for chart
1c826d5a-41cb-4450-b4dc-59d440e5f75a (Abhinandan Mohanty, secondary
canonical chart) ONLY. Deliberately a SEPARATE file rather than a
CLI-parameterized single script — the two canonical chart ids are
operationally distinct enough (native vs. secondary; different LEL history,
different paddhati profile per ADJUDICATION rulings) that a single script
with a chart-id argument risks a copy-paste/flag-order mistake dispatching
the wrong chart. This mirrors the established precedent of this campaign's
own per-chart dispatch pairs (e.g. `dispatch_int929_gochara_resume_
{482012f1,1c826d5a}.py`, SESSION-A-SWEEP's own operational scripts — not
committed, not touched by this lane, cited here only as the naming
precedent this pair follows).

PRECONDITIONS THIS SCRIPT DOES NOT VERIFY FOR YOU (verify manually / via the
sibling checklist before running):
  1. SESSION-A-SWEEP's ledger shows SWEEPS-COMPLETE for 1c826d5a (606/606
     ka_gochara_sweep substeps) and `ka_gochara_resonance` has been re-run
     against the completed sweep.
  2. Every L0 (`bg_*`) upstream `ka_kshetra` reads is already built in
     production (global, chart-independent — shared with 482012f1's build;
     do not re-trigger an L0 build here, it is not chart-scoped).
  3. `platform/supabase/migrations/491_kala_field_weights_seed.sql` (the
     `v0_classical` weights seed) is applied in production.
  4. `1c826d5a`'s gochara forward-horizon-coverage ticket (noted at this
     campaign's own Phase-0 preflight: 1,267 rows to horizon 2027-07-03 vs.
     482012f1's 8,345 rows to horizon 2084-12-30, despite a MORE RECENT
     compute timestamp) is resolved by the real sweep completing — confirm
     the completed sweep actually extended this chart's horizon to parity,
     not just its substep COUNT, before treating SWEEPS-COMPLETE as
     sufficient for this chart specifically.

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage (AFTER confirming the preconditions above, NOT before):
  cd <repo-root>/platform
  python3 scripts/dispatch_gatechain_field_build_1c826d5a.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
TRIGGERED_BY = "shad-darshana-t2-gatechain-field-build-1c826d5a"

# Same order, same acyclicity rationale as the 482012f1 sibling script.
TARGET_ASSETS = ["ka_kshetra", "mi_bhara"]

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
           VALUES (%s, %s, 'asset_set', %s, 'rebuild', %s, 'planned', %s)""",
        (run_id, CHART_ID, ",".join(TARGET_ASSETS), json.dumps(TARGET_ASSETS), TRIGGERED_BY),
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
        f"[dispatch] created T2 gate-chain field-build build_run {run_id} for 1c826d5a "
        f"with assets: {TARGET_ASSETS}",
        file=sys.stderr,
    )
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
