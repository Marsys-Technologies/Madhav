"""Elevation Campaign β.D — chart-scoped standalone rebuild for the writer fixes.

Runs one registered L1 writer for one chart via the FROZEN orchestrator contract
(`_run_data_writer` → per-substep SAVEPOINT + commit + heartbeat + downstream
stale cascade), importing the LOCAL worktree code so the EL-30/40/47 fixes take
effect WITHOUT a container image deploy. Chart-scoped delete-then-insert (§N.3) —
never a full-DB rebuild. No orchestrator contract change.

Same watchdog-safe pattern as run_heavy_writer_standalone.py (never sets
state='building'), generalised to (asset_id, chart_id).

USAGE
  cd platform/python-sidecar
  DATABASE_URL=... python run_elev_beta_d_rebuild.py <asset_id> <chart_id>

  asset_id ∈ {ga_sensitive, ga_structural, ga_vargas}
"""
from __future__ import annotations

import logging
import os
import sys
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

VALID_ASSETS = {"ga_sensitive", "ga_structural", "ga_vargas"}
CANONICAL_CHARTS = {
    "482012f1-710e-4a25-994a-93821f5871aa",
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a",
}
DEAD_PHANTOM = "362f9f17"


def main() -> None:
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <asset_id> <chart_id>")
        print(f"  asset_id ∈ {sorted(VALID_ASSETS)}")
        sys.exit(1)

    asset_id = sys.argv[1]
    chart_id = sys.argv[2]

    if asset_id not in VALID_ASSETS:
        print(f"ERROR: asset_id must be one of {sorted(VALID_ASSETS)}, got {asset_id!r}")
        sys.exit(1)
    if chart_id.startswith(DEAD_PHANTOM):
        print("ERROR: refusing to write the dead phantom chart_id 362f9f17-…")
        sys.exit(1)
    if chart_id not in CANONICAL_CHARTS:
        print(f"ERROR: chart_id {chart_id} is not a canonical campaign chart; refusing.")
        sys.exit(1)

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    import psycopg
    from pipeline.orchestrator.writers import discover_all
    from pipeline.orchestrator.asset_runner import _run_data_writer

    discover_all()

    run_id = str(uuid.uuid4())
    logger.info("β.D rebuild: asset=%s chart=%s run_id=%s", asset_id, chart_id, run_id)

    conn = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    conn.autocommit = False
    cur = conn.cursor()
    try:
        success = _run_data_writer(conn, cur, run_id, chart_id, asset_id)
        if success:
            logger.info("SUCCESS: %s (chart %s) is now state='lit'", asset_id, chart_id)
        else:
            logger.error("FAILURE: _run_data_writer returned False for %s / %s", asset_id, chart_id)
            sys.exit(1)
    except Exception:
        logger.exception("Unexpected error during β.D rebuild %s / %s", asset_id, chart_id)
        try:
            conn.rollback()
        except Exception:
            pass
        sys.exit(1)
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    main()
