"""
rebuild_d1_5a_bo_laksana.py — D-1.5a targeted rebuild for the missing-dependency fix

Rebuilds bo_laksana for Abhisek's chart (482012f1) ONLY. Migration 437 added
ga_vichara as a declared dependency (was missing, deferred since migration 367);
bo_laksana's last build (22:05:07 UTC) predates ga_vichara's own corrected data
(23:10:50 UTC) and must be re-run now that both the dependency edge exists and
ga_vichara is fresh, per the D-1.5a wave gate's hotfix verification.

Usage (Cloud SQL Auth Proxy must be running on port 5433):
  cd <repo-root>/platform
  python -m scripts.rebuild_d1_5a_bo_laksana
"""
from __future__ import annotations

import json
import logging
import os
import sys
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
ASSETS = ["bo_laksana"]
TRIGGERED_BY = "rebuild-script-d1-5a-bo-laksana-dep-fix"

_env_file = os.path.join(os.path.dirname(__file__), "..", ".env.local")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_sidecar = os.path.join(os.path.dirname(__file__), "..", "python-sidecar")
if _sidecar not in sys.path:
    sys.path.insert(0, _sidecar)


def main() -> None:
    import psycopg
    import psycopg.rows

    from pipeline.orchestrator.db import db_url
    from pipeline.orchestrator.writers import discover_all
    from pipeline.orchestrator.runner import execute_run
    discover_all()

    conn = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute(
        """SELECT asset_id, state, rows_written, last_built_at
           FROM asset_throughput WHERE chart_id = %s AND asset_id = ANY(%s)""",
        (CHART_ID, ASSETS),
    )
    for r in cur.fetchall():
        logger.info("[pre] %s: state=%s rows_written=%s last_built_at=%s",
                    r["asset_id"], r["state"], r["rows_written"], r["last_built_at"])

    cur.execute(
        """INSERT INTO asset_throughput (chart_id, asset_id, state)
           VALUES (%s, %s, 'dormant')
           ON CONFLICT (chart_id, asset_id)
           WHERE chart_id IS NOT NULL
           DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
        (CHART_ID, "bo_laksana"),
    )
    conn.commit()
    logger.info("[reset] bo_laksana -> dormant")

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
        (run_id, CHART_ID, json.dumps(ASSETS), TRIGGERED_BY),
    )
    cur.execute(
        """INSERT INTO build_run_assets (run_id, asset_id, position, state)
           VALUES (%s, %s, 0, 'queued')""",
        (run_id, "bo_laksana"),
    )
    conn.commit()
    logger.info("[run] created build_run %s", run_id)
    conn.close()

    logger.info("[run] invoking execute_run(%s)…", run_id)
    execute_run(run_id)
    logger.info("[run] execute_run complete — verifying throughput…")

    conn2 = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    cur2 = conn2.cursor()
    cur2.execute(
        """SELECT asset_id, state, rows_written, last_built_at, last_error
           FROM asset_throughput WHERE chart_id = %s AND asset_id = ANY(%s)""",
        (CHART_ID, ASSETS),
    )
    for r in cur2.fetchall():
        logger.info("[post] %s: state=%s rows_written=%s last_built_at=%s last_error=%s",
                    r["asset_id"], r["state"], r["rows_written"], r["last_built_at"], r["last_error"])
    conn2.close()


if __name__ == "__main__":
    main()
