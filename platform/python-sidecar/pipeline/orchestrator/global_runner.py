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
    Dispatch to the appropriate writer for the given asset.
    Returns 'ok', 'deferred', or 'failed'.
    """
    logger.info("[global_build] running writer for asset_id=%s", asset_id)

    # Writer registry — maps asset_id to a callable
    # Writers are imported lazily so missing modules degrade gracefully
    writer_registry = _build_writer_registry()

    if asset_id not in writer_registry:
        logger.info("[global_build] DEFERRED: no writer for asset_id=%s (will run when stream lands)", asset_id)
        return "deferred"

    writer_fn = writer_registry[asset_id]
    try:
        writer_fn(conn=conn, run_id=run_id, asset_row=row)
        logger.info("[global_build] OK: asset_id=%s", asset_id)
        return "ok"
    except Exception as exc:
        logger.error("[global_build] FAILED: asset_id=%s error=%s", asset_id, exc, exc_info=True)
        return "failed"


def _build_writer_registry() -> dict:
    """
    Build the writer registry by importing available writer modules.
    Each module is imported with try/except so missing modules are silent.
    """
    registry: dict = {}

    # brahmagyan.sarani — reference library (Stream A seeds minimal ontology)
    try:
        from pipeline.orchestrator.writers.brahmagyan_sarani import write_sarani
        registry["brahmagyan.sarani"] = write_sarani
    except ImportError:
        pass

    # brahmagyan.samanvaya — concordance / brahma_ontology (seeded by Stream A)
    try:
        from pipeline.orchestrator.writers.brahmagyan_samanvaya import write_samanvaya
        registry["brahmagyan.samanvaya"] = write_samanvaya
    except ImportError:
        pass

    # brahmagyan.kalapancanga — ephemeris (Stream B)
    try:
        from pipeline.orchestrator.writers.brahmagyan_kalapancanga import write_kalapancanga
        registry["brahmagyan.kalapancanga"] = write_kalapancanga
    except ImportError:
        pass

    # brahmagyan.shastra — classical text chunks (Stream C)
    try:
        from pipeline.orchestrator.writers.brahmagyan_shastra import write_shastra
        registry["brahmagyan.shastra"] = write_shastra
    except ImportError:
        pass

    # brahmagyan.text_index — vector embeddings (Stream C)
    try:
        from pipeline.orchestrator.writers.brahmagyan_text_index import write_text_index
        registry["brahmagyan.text_index"] = write_text_index
    except ImportError:
        pass

    # brahmagyan.sutravali — rules corpus (Stream D)
    try:
        from pipeline.orchestrator.writers.brahmagyan_sutravali import write_sutravali
        registry["brahmagyan.sutravali"] = write_sutravali
    except ImportError:
        pass

    # brahmagyan.upaya_kosha — remedy corpus (Stream F)
    try:
        from pipeline.orchestrator.writers.brahmagyan_upaya_kosha import write_upaya_kosha
        registry["brahmagyan.upaya_kosha"] = write_upaya_kosha
    except ImportError:
        pass

    return registry
