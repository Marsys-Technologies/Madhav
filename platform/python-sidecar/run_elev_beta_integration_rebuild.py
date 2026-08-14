"""Elevation Campaign β integration phase — chart-scoped standalone rebuild for lane β.G's
gemstone-verdict writer (`bo_upaya`, EL-51).

Runs one registered L2 writer for one chart via the FROZEN orchestrator's single-asset
`_run_data_writer` (per-substep SAVEPOINT + commit + heartbeat + downstream stale cascade),
importing the LOCAL worktree code (the fully-merged elev/beta head) so β.G's
`_compute_gemstone_maraka_verdict()` (BPHS Ch.44-cited) takes effect WITHOUT a container image
deploy. Chart-scoped delete-then-insert (§N.3) — never a full-DB rebuild. No orchestrator
contract change.

Deliberately mirrors `run_elev_beta_d_rebuild.py`'s exact pattern (same watchdog-safe direct-writer
call, same canonical-chart + dead-phantom guards) rather than the multi-asset `execute_run` path —
the latter enforces a same-run dependency-freshness gate that blocked on `ga_strength` (state=stale)
for an asset (`bo_upaya`) whose actual dependency is `chart_facts.ayurdaya`, already live and
correct; the direct single-writer call is the narrower-scoped, already-proven-safe mechanism for
exactly this "rebuild one writer without needing its whole upstream freshly re-lit" situation, and
is what the binding native `ka_gochara_sweep` protection ruling calls for (enumerate the exact
asset/chart list, no wider cascade).

Stream-Conductor authored (integration phase, 2026-07-25).

USAGE
  cd platform/python-sidecar
  DATABASE_URL=... python run_elev_beta_integration_rebuild.py <asset_id> <chart_id>

  asset_id ∈ {bo_upaya}
"""
from __future__ import annotations

import logging
import os
import sys
import uuid

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

VALID_ASSETS = {"bo_upaya"}
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

    from pipeline.orchestrator.db import connect as _orchestrator_connect
    from pipeline.orchestrator.writers import discover_all
    from pipeline.orchestrator.asset_runner import _run_data_writer

    discover_all()

    run_id = str(uuid.uuid4())
    logger.info("β integration rebuild: asset=%s chart=%s run_id=%s", asset_id, chart_id, run_id)

    # PARIṢKĀRA MR-39: route through pipeline.orchestrator.db.connect() (not
    # a bare psycopg.connect()) so this build session gets
    # idle_in_transaction_session_timeout=0 — the writer substep driven via
    # _run_data_writer below can legitimately hold this transaction open for
    # minutes of pure CPU work with no DB traffic.
    conn = _orchestrator_connect()
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
        logger.exception("Unexpected error during β integration rebuild %s / %s", asset_id, chart_id)
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
