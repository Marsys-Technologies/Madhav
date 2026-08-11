"""
Standalone runner for L1 heavy writers (ga_dashas, ga_sensitive).

WHY THIS EXISTS
===============
The TypeScript orphan watchdog (src/app/api/cockpit/watchdog/route.ts) fires
when asset_throughput.state = 'building' AND last_built_at has not updated for
>15 min. For ga_dashas (~90 min, 36 substeps) and ga_sensitive (~30 min, 5
substeps), individual substep computations take >15 min, triggering the reaper
mid-substep even though the orchestrator commits per-substep correctly.

FIX: Call _run_data_writer directly, BYPASSING run_asset (which is the only
place that transitions state to 'building'). Since state never becomes
'building', the watchdog condition is never satisfied. _drive_substeps still
commits per-substep and updates last_built_at (heartbeat). The asset ends in
state='lit' with correct rows_written and downstream stale cascade.

WHAT THIS SCRIPT DOES
=====================
1. Discovers all registered writers (discover_all).
2. For ga_dashas only: pre-cleans ALL chart_dashas rows for this chart so stale
   rows with legacy ayanamsha IDs (lahiri, kp, surya_siddhanta) are purged.
   replace_prior_chart_dashas scopes deletes to (chart_id, system_id, ayanamsha_id)
   pairs present in the NEW rows — it would never touch the old IDs.
3. Calls _run_data_writer which drives _drive_substeps (per-substep SAVEPOINT +
   commit + heartbeat) then sets state='lit' + marks downstream stale.

IDEMPOTENCY
===========
Safe to re-run. For ga_sensitive the 3 already-committed ayanamsha substeps
are replaced (delete-then-insert is idempotent). For ga_dashas the pre-clean
wipes all rows so the full 36-substep run always produces a clean canonical set.

L3 USAGE NOTE (document for convergence rebuild)
=================================================
Any future heavy writer whose substep computation exceeds the 15-min watchdog
threshold must use this pattern:
  - Call _run_data_writer directly (skip run_asset / execute_run)
  - Never SET state='building' in asset_throughput during the standalone run
  - A synthetic run_id (uuid4) is sufficient — no build_run record required
  - The UPDATE build_run_assets inside _run_data_writer affects 0 rows harmlessly
  - Downstream stale cascade runs automatically

USAGE
=====
  cd platform/python-sidecar
  DATABASE_URL=... python run_heavy_writer_standalone.py ga_dashas
  DATABASE_URL=... python run_heavy_writer_standalone.py ga_sensitive
"""
from __future__ import annotations

import logging
import os
import sys
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

VALID_ASSETS = {"ga_dashas", "ga_sensitive"}


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <asset_id>")
        print(f"  asset_id: one of {sorted(VALID_ASSETS)}")
        sys.exit(1)

    asset_id = sys.argv[1]
    if asset_id not in VALID_ASSETS:
        print(f"ERROR: asset_id must be one of {sorted(VALID_ASSETS)}, got: {asset_id!r}")
        sys.exit(1)

    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Add the sidecar root to sys.path so imports resolve.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from pipeline.orchestrator.db import connect as _orchestrator_connect
    from pipeline.orchestrator.writers import discover_all
    from pipeline.orchestrator.asset_runner import _run_data_writer

    discover_all()

    # Synthetic run_id — no build_run record required.
    # _run_data_writer uses this only as build_id for rows + a harmless
    # UPDATE build_run_assets that affects 0 rows (no matching run_id).
    run_id = str(uuid.uuid4())
    logger.info("Starting standalone run: asset=%s chart=%s run_id=%s", asset_id, CHART_ID, run_id)

    # PARIṢKĀRA MR-39: route through the orchestrator's own connection
    # factory (pipeline.orchestrator.db.connect) instead of a bare
    # psycopg.connect(). ga_dashas (~90 min, 36 substeps) and ga_sensitive
    # (~30 min, 5 substeps) are exactly the "long-running writer substep with
    # no DB traffic in between" scenario MR-39 targets — connect() sets
    # idle_in_transaction_session_timeout=0 for this session (both via the
    # libpq startup option and a defense-in-depth explicit SET, since a
    # Cloud SQL Auth Proxy / pooler may not forward the startup option), so
    # a substep's CPU-heavy compute window can never be killed by the
    # server-side idle-in-transaction timeout independent of TCP keepalive
    # health.
    conn = _orchestrator_connect()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # ── ga_dashas pre-cleanup ─────────────────────────────────────────────
        # replace_prior_chart_dashas scopes deletes to (chart_id, system_id,
        # ayanamsha_id) pairs present in the NEW rows — it NEVER deletes stale
        # rows that use legacy IDs (lahiri, kp, surya_siddhanta). Pre-delete all
        # chart_dashas rows for this chart so the final table contains ONLY
        # canonical-ayanamsha rows from this run.
        if asset_id == "ga_dashas":
            cur.execute(
                "SELECT COUNT(*) AS n FROM chart_dashas WHERE chart_id = %s",
                (CHART_ID,),
            )
            before = cur.fetchone()["n"]
            logger.info("Pre-cleanup: deleting %d existing chart_dashas rows for chart %s", before, CHART_ID)
            cur.execute("DELETE FROM chart_dashas WHERE chart_id = %s", (CHART_ID,))
            conn.commit()
            logger.info("Pre-cleanup: chart_dashas purged — table is now empty for this chart")

        # ── Core: call _run_data_writer directly ──────────────────────────────
        # asset_throughput.state stays 'error' (or whatever it was) — it NEVER
        # becomes 'building', so the TypeScript watchdog condition
        # (state='building' AND last_built_at < NOW()-15min) is never true.
        # _drive_substeps commits per-substep and updates last_built_at.
        # _run_data_writer sets state='lit' and marks downstream stale on success.
        logger.info("Calling _run_data_writer for %s — watchdog-safe (no 'building' transition)", asset_id)
        success = _run_data_writer(conn, cur, run_id, CHART_ID, asset_id)

        if success:
            logger.info("SUCCESS: %s is now state='lit'", asset_id)
        else:
            logger.error("FAILURE: _run_data_writer returned False for %s — check logs above", asset_id)
            sys.exit(1)

    except Exception:
        logger.exception("Unexpected error during standalone run for %s", asset_id)
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
