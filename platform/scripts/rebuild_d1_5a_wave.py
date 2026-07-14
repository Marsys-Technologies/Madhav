"""
rebuild_d1_5a_wave.py — D-1.5a scope-limited rebuild

Re-runs ga_structural, ga_vichara, bo_laksana for Abhisek's chart (482012f1) only,
per the native-ratified Abhisek-only / scope-limited rebuild policy (CLAUDECODE_BRIEF.md
R-5). These are the three writers Lane A-alpha and Lane A-gamma modified in wave D-1.5a.
Abhinandan (1c826d5a) is not rebuilt — read-only reference for the CR-87 guard only.

Usage (Cloud SQL Auth Proxy must be running on port 5433):
  cd <repo-root>/platform
  python -m scripts.rebuild_d1_5a_wave
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
ASSETS = ["ga_structural", "ga_vichara", "bo_laksana"]
TRIGGERED_BY = "rebuild-script-d1-5a-wave"

_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = (10, 30)

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


def _execute_run_with_bounded_retry(run_id: str, chart_id: str, assets: list[str]) -> None:
    import psycopg
    from pipeline.orchestrator.db import db_url
    from pipeline.orchestrator.runner import execute_run

    current_run_id = run_id
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            execute_run(current_run_id)
            return
        except (psycopg.OperationalError, OSError) as exc:
            if attempt >= _MAX_ATTEMPTS:
                logger.error("[run] execute_run(%s) failed after %d/%d attempts: %s: %s",
                             current_run_id, attempt, _MAX_ATTEMPTS, type(exc).__name__, exc)
                raise
            backoff = _RETRY_BACKOFF_SECONDS[min(attempt - 1, len(_RETRY_BACKOFF_SECONDS) - 1)]
            logger.warning("[run] attempt %d/%d hit connection error (%s: %s) — retrying in %ds",
                           attempt, _MAX_ATTEMPTS, type(exc).__name__, exc, backoff)
            time.sleep(backoff)

            conn = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
            conn.autocommit = False
            cur = conn.cursor()
            current_run_id = str(uuid.uuid4())
            cur.execute(
                """INSERT INTO build_runs
                     (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
                   VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
                (current_run_id, chart_id, json.dumps(assets), f"{TRIGGERED_BY}-retry{attempt}"),
            )
            for position, asset_id in enumerate(assets):
                cur.execute(
                    """INSERT INTO build_run_assets (run_id, asset_id, position, state)
                       VALUES (%s, %s, %s, 'queued')""",
                    (current_run_id, asset_id, position),
                )
            conn.commit()
            conn.close()


def main() -> None:
    import psycopg
    import psycopg.rows

    from pipeline.orchestrator.db import db_url
    from pipeline.orchestrator.writers import discover_all
    discover_all()

    conn = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()

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

    cur.execute(
        """INSERT INTO asset_throughput (chart_id, asset_id, state)
           VALUES (%s, %s, 'dormant'), (%s, %s, 'dormant'), (%s, %s, 'dormant')
           ON CONFLICT (chart_id, asset_id)
           WHERE chart_id IS NOT NULL
           DO UPDATE SET state = 'dormant', rows_written = 0, last_error = NULL""",
        (CHART_ID, ASSETS[0], CHART_ID, ASSETS[1], CHART_ID, ASSETS[2]),
    )
    conn.commit()
    logger.info("[reset] %s -> dormant", ASSETS)

    run_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by)
           VALUES (%s, %s, 'asset_set', NULL, 'build', %s, 'planned', %s)""",
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

    logger.info("[run] invoking execute_run(%s) with bounded retry…", run_id)
    _execute_run_with_bounded_retry(run_id, CHART_ID, ASSETS)
    logger.info("[run] execute_run complete — verifying throughput…")

    conn2 = psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
    cur2 = conn2.cursor()
    cur2.execute(
        """SELECT asset_id, state, rows_written, last_built_at, last_error
           FROM asset_throughput
           WHERE chart_id = %s AND asset_id = ANY(%s)""",
        (CHART_ID, ASSETS),
    )
    for r in cur2.fetchall():
        logger.info("[post] %s: state=%s rows_written=%s last_built_at=%s last_error=%s",
                    r["asset_id"], r["state"], r["rows_written"], r["last_built_at"], r["last_error"])
    conn2.close()


if __name__ == "__main__":
    main()
