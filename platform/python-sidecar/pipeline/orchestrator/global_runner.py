"""
pipeline.orchestrator.global_runner — L0FR global-build mode
=============================================================

L0FR Stream A step 8-9:
  Acquire pg_advisory_lock(hashtext('global')), walk asset_registry rows
  where scope='global', run their writers, release lock.

Used for L0 brahmagyan foundation data builds that are chart-independent
(no chart_id, runs against shared global assets).

Writer dispatch:
  Asset writers are resolved by asset_id via the brahmagyan writer registry.
  Writers that don't exist yet are skipped with a DEFERRED log entry.
  This makes the global_runner forward-compatible: as Stream B/C/D writers land,
  they auto-dispatch without changes here.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from .db import connect
from .writers import discover_all, get_writer, ContextSpec

logger = logging.getLogger(__name__)

# Advisory lock key — must match across all callers
_GLOBAL_BUILD_LOCK = 0x676c6f62  # hashtext('global') approximate; use pg function


def execute_global_build(run_id: Optional[str] = None) -> None:
    """
    Execute a global (chart-independent) build for all scope='global' assets.

    Args:
        run_id: Optional UUID for logging; auto-generated if not provided.
    """
    if not run_id:
        run_id = str(uuid.uuid4())

    logger.info("[global_build] starting run_id=%s", run_id)

    with connect() as conn:
        # Acquire advisory lock so only one global build runs at a time
        lock_key = _acquire_global_lock(conn)
        if lock_key is None:
            logger.warning("[global_build] could not acquire global advisory lock — another global build is running; exiting")
            return

        try:
            # Walk asset_registry rows where scope='global' and is_active=true
            rows = conn.execute(
                """
                SELECT asset_id, layer, target_table, count_sql, depends_on, sort_order
                FROM asset_registry
                WHERE scope = 'global' AND is_active = true
                ORDER BY layer, sort_order
                """,
            ).fetchall()

            logger.info("[global_build] found %d global assets to build", len(rows))
            discover_all()  # D2: ensure all writer modules are imported before dispatch

            results = []
            for row in rows:
                asset_id = row["asset_id"]
                result = _run_asset_writer(conn, run_id, asset_id, row)
                results.append((asset_id, result))

            # Summary
            passed = [a for a, r in results if r == "ok"]
            skipped = [a for a, r in results if r == "deferred"]
            failed = [a for a, r in results if r == "failed"]

            logger.info(
                "[global_build] COMPLETE run_id=%s: %d ok, %d deferred, %d failed",
                run_id, len(passed), len(skipped), len(failed),
            )
            if failed:
                logger.warning("[global_build] FAILED assets: %s", failed)
            if skipped:
                logger.info("[global_build] DEFERRED assets (writer not yet implemented): %s", skipped)

        finally:
            _release_global_lock(conn, lock_key)

    logger.info("[global_build] run_id=%s done", run_id)


def _acquire_global_lock(conn) -> Optional[int]:
    """Try to acquire an advisory lock for global builds. Returns lock key or None."""
    # Use hashtext('global') as the lock key
    row = conn.execute("SELECT hashtext('global') AS lock_key").fetchone()
    lock_key = row["lock_key"]
    result = conn.execute(
        "SELECT pg_try_advisory_lock(%s) AS acquired", [lock_key]
    ).fetchone()
    if result["acquired"]:
        logger.info("[global_build] acquired advisory lock key=%s", lock_key)
        return lock_key
    return None


def _release_global_lock(conn, lock_key: int) -> None:
    """Release the advisory lock."""
    conn.execute("SELECT pg_advisory_unlock(%s)", [lock_key])
    logger.info("[global_build] released advisory lock key=%s", lock_key)


def _run_asset_writer(conn, run_id: str, asset_id: str, row: dict) -> str:
    """
    Dispatch to the writer registered for asset_id via the WriterBase registry.
    Returns 'ok', 'deferred', or 'failed'.
    """
    writer_cls = get_writer(asset_id)
    if writer_cls is None:
        logger.info("[global_build] DEFERRED: no writer for asset_id=%s (will run when writer lands)", asset_id)
        return "deferred"

    logger.info("[global_build] running writer for asset_id=%s", asset_id)
    try:
        ctx = ContextSpec(
            asset_id=asset_id,
            build_id=run_id,
            db_conn=conn,
            config={},
        )
        result = writer_cls().run(ctx)
        logger.info("[global_build] OK: asset_id=%s rows_inserted=%d", asset_id, result.rows_inserted)
        return "ok"
    except Exception as exc:
        logger.error("[global_build] FAILED: asset_id=%s error=%s", asset_id, exc, exc_info=True)
        return "failed"
