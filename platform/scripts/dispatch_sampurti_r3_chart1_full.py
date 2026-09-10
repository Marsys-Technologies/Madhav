"""
dispatch_sampurti_r3_chart1_full.py — SAMPŪRTI R3 full-DAG rebuild, chart 1 (native Abhisek).

Dispatches a full-DAG build for chart 482012f1 (Abhisek Mohanty, canonical).
Targets all stale/error bo_*/ka_*/mi_*/ph_* assets minus the 5 gochara exclusions
and ka_gochara_sweep.

PRECONDITIONS (verify before running):
  1. A1 pin (PR #1254) merged to sampurti/integration and deployed.
     The production sidecar must carry _gochara_corpus_pin() in writer.py so
     the new field snapshot includes the gochara corpus digest.
  2. β YANTRA-CORPUS-READY marker posted on campaign-coordination.
     β's B5 corpus rebuild (L-9 lease) must have completed so ka_gochara_resonance
     carries the post-B1-B4 resonance rows that A1 will fingerprint into the snapshot.
  3. cloud-sql-proxy is running on 127.0.0.1:5433 (DATABASE_URL in .env.local).
     (Note: PARIṢKĀRA uses :5434; ensure the SAMPŪRTI proxy is on :5433.)

GOCHARA EXCLUSIONS (never touched by SAMPŪRTI):
  ka_gochara, ka_gochara_v3_century_materialize, ka_gochara_resonance,
  ka_vedha_gochara, ka_kota_chakra, ka_gochara_sweep
"""
from __future__ import annotations

import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-r3-chart1-full-dag"

GOCHARA_EXCLUSIONS = {
    "ka_gochara",
    "ka_gochara_v3_century_materialize",
    "ka_gochara_resonance",
    "ka_vedha_gochara",
    "ka_kota_chakra",
    "ka_gochara_sweep",
}

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

    # Enforce precondition: ka_gochara_resonance must be lit (β B5 complete).
    cur.execute(
        "SELECT state FROM asset_throughput WHERE chart_id = %s AND asset_id = 'ka_gochara_resonance'",
        (CHART_ID,),
    )
    row = cur.fetchone()
    if not row or row["state"] != "lit":
        raise RuntimeError(
            f"ka_gochara_resonance is not `lit` for chart1 (state={row and row['state']!r}). "
            "Wait for β YANTRA-CORPUS-READY before dispatching R3."
        )

    # Query all non-lit assets with writers, excluding gochara.
    cur.execute(
        """SELECT at.asset_id, at.state
             FROM asset_throughput at
             JOIN asset_registry ar ON ar.asset_id = at.asset_id AND ar.has_writer = TRUE
            WHERE at.chart_id = %s
              AND at.asset_id != ALL(%s)
              AND at.state != 'lit'
            ORDER BY at.asset_id""",
        (CHART_ID, list(GOCHARA_EXCLUSIONS)),
    )
    targets = cur.fetchall()
    if not targets:
        print("[dispatch] No stale/error assets found — nothing to do.", file=sys.stderr)
        conn.close()
        return

    target_ids = [r["asset_id"] for r in targets]
    print(
        f"[dispatch] R3 chart1 full plan: {len(target_ids)} assets to build",
        file=sys.stderr,
    )
    for r in targets:
        print(f"  {r['asset_id']} ({r['state']})", file=sys.stderr)

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
        (run_id, CHART_ID, json.dumps(target_ids), TRIGGERED_BY),
    )
    for position, asset_id in enumerate(target_ids):
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, %s, 'queued')""",
            (run_id, asset_id, position),
        )
    conn.commit()
    conn.close()
    print(
        f"[dispatch] created SAMPŪRTI R3 chart1 full run {run_id}",
        file=sys.stderr,
    )
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
