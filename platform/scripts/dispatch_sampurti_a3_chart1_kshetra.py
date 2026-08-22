"""
dispatch_sampurti_a3_chart1_kshetra.py — SAMPŪRTI A3: ka_kshetra rebuild post-β.

A3 rationale:
  - ka_kshetra was built in A2 at ~04:50 IST, before β completed (05:15 IST, YANTRA-CORPUS-READY).
  - A1 code (gochara corpus pin via _gochara_corpus_pin()) was deployed before A2, but the
    ka_gochara_resonance data β updated wasn't finalized until 05:15 IST.
  - A2' rebuilt ka_gochara (now fresh post-β corpus, 83 rows).
  - A3 force-rebuilds ka_kshetra so the new config_pin includes the post-β gochara corpus
    digest → new snapshot_id → fresh post-β field data for Measurement #5.

PRECONDITIONS:
  1. A1 code deployed (gate packet PR #1255 merged dbdbb30ac).
  2. ka_gochara lit with post-β corpus (A2' complete, run cbd6ea44).
  3. ka_kshetra marked stale before dispatch (done by conductor).
  4. cloud-sql-proxy running on 127.0.0.1:5433.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TRIGGERED_BY = "sampurti-a3-chart1-kshetra-postbeta"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch SAMPŪRTI A3 ka_kshetra rebuild")
    parser.add_argument("--chart-id", default=CHART_ID, help="Chart UUID (default: chart1)")
    args = parser.parse_args()

    chart_id = args.chart_id

    import psycopg
    import psycopg.rows

    database_url = os.environ["DATABASE_URL"]
    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # Precondition: ka_gochara must be lit (post-β A2' complete).
    cur.execute(
        "SELECT state FROM asset_throughput WHERE chart_id = %s AND asset_id = 'ka_gochara'",
        (chart_id,),
    )
    row = cur.fetchone()
    if not row or row["state"] != "lit":
        raise RuntimeError(
            f"ka_gochara is not `lit` (state={row and row['state']!r}). "
            "A2' must complete before dispatching A3."
        )

    # Precondition: ka_kshetra must be stale (not lit — conductor forced stale before dispatch).
    cur.execute(
        "SELECT state FROM asset_throughput WHERE chart_id = %s AND asset_id = 'ka_kshetra'",
        (chart_id,),
    )
    row = cur.fetchone()
    if not row or row["state"] not in ("stale", "error"):
        raise RuntimeError(
            f"ka_kshetra is `{row and row['state']}` — expected stale/error. "
            "Mark it stale before running A3 dispatch."
        )

    print(f"[a3-dispatch] ka_kshetra state={row['state']!r} — proceeding", file=sys.stderr)

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
        (run_id, chart_id, json.dumps(["ka_kshetra"]), TRIGGERED_BY),
    )
    cur.execute(
        """INSERT INTO build_run_assets (run_id, asset_id, position, state)
           VALUES (%s, 'ka_kshetra', 0, 'queued')""",
        (run_id,),
    )
    conn.commit()
    conn.close()
    print(f"[a3-dispatch] created SAMPŪRTI A3 ka_kshetra run {run_id}", file=sys.stderr)
    print(run_id, flush=True)


if __name__ == "__main__":
    main()
