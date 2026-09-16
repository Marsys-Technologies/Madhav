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
3. Creates and commits a durable `build_runs` + `build_run_assets` lifecycle
   before any ga_dashas pre-clean delete, then calls _run_data_writer which drives _drive_substeps (per-substep SAVEPOINT +
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
  - Create and commit a real running build_run plus building build_run_asset
    before the first destructive write; complete or fail both terminal records
    after _run_data_writer returns
  - _run_data_writer's existing build_run_assets updates then target that real row
  - Downstream stale cascade runs automatically

USAGE
=====
  cd platform/python-sidecar
  DATABASE_URL=... python run_heavy_writer_standalone.py ga_dashas
  DATABASE_URL=... python run_heavy_writer_standalone.py ga_sensitive
"""
from __future__ import annotations

import json
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


def _create_standalone_run_lifecycle(conn, cur, run_id: str, asset_id: str) -> None:
    """Commit the durable fence before a standalone writer can replace output."""
    plan = json.dumps({
        "entrypoint": "run_heavy_writer_standalone",
        "asset_ids": [asset_id],
        "watchdog_safe_asset_throughput": True,
    }, sort_keys=True)
    cur.execute(
        """INSERT INTO build_runs
             (id, chart_id, scope, scope_target, action, plan, state, triggered_by,
              started_at, current_asset_id)
           VALUES (%s, %s, 'asset', %s, 'rebuild', %s::jsonb, 'running',
                   'run_heavy_writer_standalone', NOW(), %s)""",
        (run_id, CHART_ID, asset_id, plan, asset_id),
    )
    cur.execute(
        """INSERT INTO build_run_assets (run_id, asset_id, position, state, started_at)
           VALUES (%s, %s, 0, 'building', NOW())""",
        (run_id, asset_id),
    )
    conn.commit()


def _complete_standalone_run_lifecycle(conn, cur, run_id: str, asset_id: str) -> None:
    """Terminalize the standalone lifecycle only after writer success."""
    cur.execute(
        """UPDATE build_run_assets SET state = 'complete', ended_at = NOW(), error = NULL
           WHERE run_id = %s AND asset_id = %s AND state IN ('queued', 'building', 'complete')""",
        (run_id, asset_id),
    )
    cur.execute(
        """UPDATE build_runs SET state = 'completed', ended_at = NOW(), last_error = NULL
           WHERE id = %s AND state IN ('planned', 'running', 'paused')""",
        (run_id,),
    )
    conn.commit()


def _fail_standalone_run_lifecycle(conn, cur, run_id: str, asset_id: str, error: str) -> None:
    """Fail the durable fence without overwriting a more specific writer error."""
    cur.execute(
        """UPDATE build_run_assets
           SET state = 'error', ended_at = NOW(), error = COALESCE(NULLIF(error, ''), %s)
           WHERE run_id = %s AND asset_id = %s""",
        (error[:2000], run_id, asset_id),
    )
    cur.execute(
        """UPDATE build_runs
           SET state = 'failed', ended_at = NOW(), last_error = COALESCE(NULLIF(last_error, ''), %s)
           WHERE id = %s AND state IN ('planned', 'running', 'paused')""",
        (error[:2000], run_id),
    )
    conn.commit()


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

    # The ID is durable: its build_runs/build_run_assets lifecycle is committed
    # before ga_dashas can delete any old rows, so readers can fence the partial
    # replacement without putting asset_throughput into watchdog-visible building.
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

    lifecycle_created = False
    try:
        _create_standalone_run_lifecycle(conn, cur, run_id, asset_id)
        lifecycle_created = True
        logger.info("Standalone lifecycle running: asset=%s chart=%s run_id=%s", asset_id, CHART_ID, run_id)

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
            _complete_standalone_run_lifecycle(conn, cur, run_id, asset_id)
            logger.info("SUCCESS: %s is now state='lit'", asset_id)
        else:
            logger.error("FAILURE: _run_data_writer returned False for %s — check logs above", asset_id)
            _fail_standalone_run_lifecycle(
                conn, cur, run_id, asset_id,
                "_run_data_writer returned False; preserving any writer error recorded on build_run_assets",
            )
            sys.exit(1)

    except Exception as exc:
        logger.exception("Unexpected error during standalone run for %s", asset_id)
        try:
            conn.rollback()
        except Exception:
            pass
        if lifecycle_created:
            try:
                _fail_standalone_run_lifecycle(conn, cur, run_id, asset_id, f"{type(exc).__name__}: {exc}")
            except Exception:
                logger.exception("Could not record standalone lifecycle failure for %s", asset_id)
        sys.exit(1)
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    main()
