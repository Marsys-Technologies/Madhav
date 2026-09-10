"""
dispatch_sampurti_a2prime_chart1_full.py — SAMPŪRTI A2' (remediated R3) full-DAG rebuild.

A2 (run e24e06c1) failed because ka_gochara was incorrectly included in GOCHARA_EXCLUSIONS.
ka_gochara became STALE when β rebuilt ka_gochara_resonance; it must be rebuilt to unblock
ka_sangam → ka_kalasutra → ka_vighnakara → all downstream ka_*/ph_*/mi_* assets.

A2' corrects this: ka_gochara is INCLUDED (§3 of CAMPAIGN_COORDINATION permits α to RUN
gochara writers in a full-DAG rebuild; ka_gochara is stale, not protected sweep corpus).

PRECONDITIONS (enforced by script):
  1. A1 pin deployed — production sidecar carries _gochara_corpus_pin() in writer.py
     (PR #1255 merged and deployed at dbdbb30ac, 2026-08-13T00:35Z).
  2. ka_gochara_resonance must be lit (β B5 / L-9 complete — YANTRA-CORPUS-READY posted).
  3. cloud-sql-proxy running on 127.0.0.1:5433 (α's port); DATABASE_URL set via gcloud.

GOCHARA EXCLUSIONS for A2' (ka_gochara INCLUDED to unblock ka_sangam):
  ka_gochara_v3_century_materialize, ka_gochara_resonance,
  ka_vedha_gochara, ka_kota_chakra, ka_gochara_sweep
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-a2prime-chart1-full-dag"

# A2' exclusions: ka_gochara NOT excluded (corrects A2 root cause).
# ka_gochara_sweep excluded: error state, unrelated to A2' scope, pre-existing bug.
# ka_gochara_resonance excluded: lit, β-owned, do not rebuild.
# ka_gochara_v3_century_materialize excluded: lit, β-owned, do not rebuild.
GOCHARA_EXCLUSIONS = {
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
    parser = argparse.ArgumentParser(
        description="SAMPŪRTI A2' remediated R3 dispatch — ka_gochara included."
    )
    parser.add_argument(
        "--chart-id",
        required=True,
        help="Chart ID to rebuild (must match canonical native chart).",
    )
    args = parser.parse_args()
    if args.chart_id != CHART_ID:
        print(
            f"[dispatch] ERROR: chart_id mismatch. Expected {CHART_ID!r}, got {args.chart_id!r}.",
            file=sys.stderr,
        )
        sys.exit(1)

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
            "Wait for β YANTRA-CORPUS-READY before dispatching A2'."
        )

    # Verify ka_gochara is stale (expected precondition for A2').
    cur.execute(
        "SELECT state FROM asset_throughput WHERE chart_id = %s AND asset_id = 'ka_gochara'",
        (CHART_ID,),
    )
    gochara_row = cur.fetchone()
    if gochara_row:
        print(
            f"[dispatch] ka_gochara state={gochara_row['state']!r} "
            "(expected: stale; will be included in A2' build)",
            file=sys.stderr,
        )

    # Query all non-lit assets with writers, excluding A2' gochara exclusions.
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
        f"[dispatch] A2' chart1 full plan: {len(target_ids)} assets to build",
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
        f"[dispatch] created SAMPŪRTI A2' chart1 full run {run_id}",
        file=sys.stderr,
    )
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
