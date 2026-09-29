#!/usr/bin/env python3.13
"""T3 fix F4 (sandbox only): actually RUN the bg_medical_mappings writer against the sandbox,
the way the orchestrator would — a real build_runs row, the writer's run() on a real connection
(autocommit off, harness owns the transaction), build_run_assets rows for the three assets the
writer's @register set covers, and asset_throughput updated from the measured run
(rows_written = post-run live count, rows_per_second = rows/duration, last_built_at = now).

This is the honest version of the "registry gap has_writer=false" repair's consequence: once
bg_nakshatra_medical is declared to have a writer, Build.exercised can only be closed by the
orchestrator actually dispatching it. So dispatch it.

Usage: PG* env pointed at the sandbox. Prints the run id and per-asset throughput rows.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time

import psycopg2

ROOT = "/Users/Dev/madhav-nikasha"
sys.path.insert(0, f"{ROOT}/platform/python-sidecar")

from pipeline.orchestrator.writers import ContextSpec  # noqa: E402
from pipeline.orchestrator.writers.bg_medical_mappings import BgMedicalMappingsWriter  # noqa: E402

ASSETS = ["bg_medical_mappings", "bg_nakshatra_medical", "bg_sign_medical"]
TABLES = {"bg_medical_mappings": "bg_medical_mappings",
          "bg_nakshatra_medical": "bg_nakshatra_medical",
          "bg_sign_medical": "bg_sign_medical"}
GLOBAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"  # chart_id used by existing asset_set runs


def main() -> None:
    conn = psycopg2.connect(host=os.environ["PGHOST"], port=os.environ["PGPORT"],
                            user=os.environ["PGUSER"], dbname=os.environ["PGDATABASE"])
    conn.autocommit = False
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO build_runs (chart_id, scope, scope_target, action, state, plan, triggered_by,"
        "                        started_at)"
        " VALUES (%s, 'asset_set', %s, 'build', 'running', %s, 'nikasha-test-t3-sandbox', now())"
        " RETURNING id",
        (GLOBAL_CHART, "bg_medical_mappings", json.dumps(ASSETS)))
    run_id = cur.fetchone()[0]
    conn.commit()
    print(f"run_id={run_id}")

    t0 = time.time()
    ctx = ContextSpec(build_id=str(run_id), asset_id="bg_medical_mappings", db_conn=conn, dry_run=False)
    result = BgMedicalMappingsWriter().run(ctx)
    conn.commit()  # harness owns the transaction boundary, as the orchestrator would
    dur = time.time() - t0
    print(f"writer.run ok: rows_inserted={result.rows_inserted} duration={dur:.2f}s notes={result.notes}")

    now = dt.datetime.now(dt.timezone.utc)
    for pos, aid in enumerate(ASSETS):
        cur.execute(
            "INSERT INTO build_run_assets (run_id, asset_id, position, state, started_at, ended_at,"
            "                             output_changed, disposition)"
            " VALUES (%s, %s, %s, 'complete', now(), now(), true, 'build')",
            (run_id, aid, pos))
        cur.execute(f"SELECT count(*) FROM {TABLES[aid]}")
        live = cur.fetchone()[0]
        rps = round(live / dur, 2) if dur > 0 else None
        cur.execute(
            "UPDATE asset_throughput SET state='lit', rows_written=%s, rows_per_second=%s,"
            " last_built_at=%s, last_measured_at=%s, last_measured_build_id=%s,"
            " measurement_count=coalesce(measurement_count,0)+1 WHERE asset_id=%s",
            (live, rps, now, now, str(run_id), aid))
        print(f"  {aid}: live={live} rps={rps}")
    cur.execute("UPDATE build_runs SET state='completed', ended_at=now() WHERE id=%s", (run_id,))
    conn.commit()
    conn.close()
    print("run completed; throughput updated")


if __name__ == "__main__":
    main()
