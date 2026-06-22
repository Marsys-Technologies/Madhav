"""
rebuild_ga_sensitive_ga_strength.py — Part A of PROGRESSBAR_RECONCILE v1.0

Re-runs ga_sensitive + ga_strength through the orchestrator for the native chart
(482012f1-710e-4a25-994a-93821f5871aa) to write fresh 'lit' throughput records
with correct rows_written. See CLAUDECODE_BRIEF_PROGRESSBAR_RECONCILE_v1_0.md §1.

Root cause: ga_sensitive never received a throughput record; ga_strength has a
stale partial-run record (rows_written=1,330 vs actual 2,184).

Usage (Cloud SQL proxy must be running on port 5433):
  cd <repo-root>/platform
  python -m scripts.rebuild_ga_sensitive_ga_strength

Verify after:
  SELECT asset_id, state, rows_written, last_built_at
  FROM asset_throughput
  WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
    AND asset_id IN ('ga_sensitive', 'ga_strength');
  -- Expected: both 'lit', rows_written ~8055 and ~2184
"""
from __future__ import annotations

import json
import logging
import os
import sys
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
ASSETS = ["ga_sensitive", "ga_strength"]
TRIGGERED_BY = "rebuild-script-progressbar-reconcile"

# Load .env.local if present
_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# Ensure python-sidecar is importable
_sidecar = os.path.join(os.path.dirname(__file__), "..", "python-sidecar")
if _sidecar not in sys.path:
    sys.path.insert(0, _sidecar)


def main() -> None:
    import psycopg
    import psycopg.rows

    from pipeline.orchestrator.db import db_url
    from pipeline.orchestrator.runner import execute_run
    from pipeline.orchestrator.writers import discover_all
    discover_all()

    conn = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    # 1. Show current throughput state before doing anything
    cur.execute(
        """SELECT asset_id, state, rows_written, last_built_at
           FROM asset_throughput
           WHERE chart_id = %s AND asset_id = ANY(%s)""",
        (CHART_ID, ASSETS),
    )
    existing = {r["asset_id"]: r for r in cur.fetchall()}
    for a in ASSETS:
        if a in existing:
            r = existing[a]
            logger.info("[pre] %s: state=%s rows_written=%s last_built_at=%s",
                        a, r["state"], r["rows_written"], r["last_built_at"])
        else:
            logger.info("[pre] %s: no throughput record", a)

    # 2. Reset both assets to 'dormant' so the runner doesn't skip them
    #    (runner skips assets whose throughput.state='lit'; resetting to dormant forces re-execution)
    cur.execute(
        """INSERT INTO asset_throughput (chart_id, asset_id, state)
           VALUES (%s, %s, 'dormant'), (%s, %s, 'dormant')
           ON CONFLICT (chart_id, asset_id)
           WHERE chart_id IS NOT NULL
           DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
        (CHART_ID, "ga_sensitive", CHART_ID, "ga_strength"),
    )
    conn.commit()
    logger.info("[reset] ga_sensitive and ga_strength throughput → dormant")

    # 3. Create a single build_run with both assets in plan (sequential execution)
    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'global', NULL, 'build', %s, 'planned', %s)""",
        (run_id, CHART_ID, json.dumps(ASSETS), TRIGGERED_BY),
    )
    for position, asset_id in enumerate(ASSETS):
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, %s, 'queued')""",
            (run_id, asset_id, position),
        )
    conn.commit()
    logger.info("[run] created build_run %s with plan=%s", run_id, ASSETS)
    conn.close()

    # 4. Execute the run — orchestrator walks the plan, writes throughput records
    logger.info("[run] invoking execute_run(%s)…", run_id)
    execute_run(run_id)
    logger.info("[run] execute_run complete — verifying throughput…")

    # 5. Verify
    conn2 = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    cur2 = conn2.cursor()
    cur2.execute(
        """SELECT asset_id, state, rows_written, last_built_at
           FROM asset_throughput
           WHERE chart_id = %s AND asset_id = ANY(%s)""",
        (CHART_ID, ASSETS),
    )
    for r in cur2.fetchall():
        logger.info("[post] %s: state=%s rows_written=%s last_built_at=%s",
                    r["asset_id"], r["state"], r["rows_written"], r["last_built_at"])
    conn2.close()


if __name__ == "__main__":
    main()
