"""
dispatch_gatechain_field_build_482012f1.py — Track T2 gate-chain pre-staging.

STAGED, NOT EXECUTED. This script is written ahead of SESSION-A-SWEEP's
`SWEEPS-COMPLETE` ledger signal so the field-build step of the gate chain
(`SHAD_DARSHANA_STATE.md` NEXT-ACTION: "S4-05 re-test on real data → field
build both charts → hash-replay → weights v0 → first skill score published →
GOF → one integration→main PR → deploy → PARĪKṢAKA both charts → Gates
W2/W3 evaluation") is a RUN, not a DISCOVERY, the moment sweeps finish. Per
this campaign's own standing directive this session operated under
(`SHAD_DARSHANA_STATE.md`, SESSION-B-BUILD native directive, recorded
verbatim): "the sweeps hold the build locks on both canonical charts — NO
per-chart production materialization on 482012f1/1c826d5a until A writes
SWEEPS-COMPLETE." This script therefore does NOT dispatch anything by being
present in the tree — it is inert until someone runs it, and the person who
runs it is responsible for having confirmed SWEEPS-COMPLETE first (see the
precondition checklist in this directory's sibling doc,
`gate_chain_prestage/README_v1_0.md`).

WHAT IT BUILDS: `ka_kshetra` (W2 stages 0–8, the temporal field) then
`mi_bhara` (stage 9 — weight fit, skill score, GOF, weights-version write),
in that dependency order, for chart 482012f1 (Abhisek Mohanty, native,
primary canonical chart) ONLY. `mi_bhara.depends_on = ['ka_kshetra']` and
NOTHING ELSE (the weights-version acyclicity rule, brief §2.5 item 4) — this
script's TARGET_ASSETS order respects that directly; it does not attempt to
topo-sort a larger closure because there is none to sort here.

PRECONDITIONS THIS SCRIPT DOES NOT VERIFY FOR YOU (verify manually / via the
sibling checklist before running):
  1. SESSION-A-SWEEP's ledger shows SWEEPS-COMPLETE for 482012f1 (606/606
     ka_gochara_sweep substeps) and `ka_gochara_resonance` has been re-run
     against the completed sweep.
  2. Every L0 (`bg_*`) upstream `ka_kshetra` reads is already built in
     production — per `SHAD_DARSHANA_STATE.md`'s Night-5 report, this was
     true as of 2026-08-02 ("L0 substrate fully built in production for the
     first time"); RE-CONFIRM this has not regressed before relying on it.
  3. `platform/supabase/migrations/491_kala_field_weights_seed.sql` (the
     `v0_classical` weights seed — the acyclicity keystone) is applied in
     production. Confirmed present in this campaign's own migration set
     (Night 2's W2 lanes, shipped to production per the Night-4 morning
     report) — RE-CONFIRM via `_migrations_applied`, do not assume.

Follows the established `dispatch_*.py` precedent in this directory (see
`dispatch_sarva_siddhi_cr66_cr73_rebuild.py` for the closest sibling: a
brief local Cloud SQL Auth Proxy session for the multi-row INSERT, then a
separate `gcloud run jobs execute brahma-build-pipeline-job` dispatch).

Prints ONLY the run_id (UUID) to stdout on success, for shell capture.

Usage (AFTER confirming the preconditions above, NOT before):
  cd <repo-root>/platform
  python3 scripts/dispatch_gatechain_field_build_482012f1.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "shad-darshana-t2-gatechain-field-build-482012f1"

# Order matters and is NOT re-derived by this script: ka_kshetra first (the field, stages
# 0-8), mi_bhara second (stage 9 — reads the field ka_kshetra just wrote). This is the
# acyclicity-safe pair per brief §2.5 item 4 — mi_bhara.depends_on = ['ka_kshetra'] and
# NOTHING ELSE; ka_kshetra never lists mi_bhara.
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

    # Precondition guard #1 (cheap, always run): both target assets must actually be
    # registered. This does NOT check the sweep-complete / L0-built preconditions above —
    # those need real judgment calls this script deliberately does not automate.
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

    # Reset to dormant so the orchestrator treats this as a genuine build attempt rather
    # than skipping a chart already in 'error'/'lit' state from a prior partial attempt.
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
        f"[dispatch] created T2 gate-chain field-build build_run {run_id} for 482012f1 "
        f"with assets: {TARGET_ASSETS}",
        file=sys.stderr,
    )
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
