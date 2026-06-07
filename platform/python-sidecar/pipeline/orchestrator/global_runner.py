"""
pipeline.orchestrator.global_runner
=====================================

L0FR: --global-build mode.
Acquires pg_advisory_lock(hashtext('global')), walks all asset_registry rows
where scope='global', runs their writers, releases lock.

This is the orchestration entry point for the L0 Foundation Rebuild.
It does NOT use build_runs — it runs inline and logs to a global_build_runs
pseudo-record (or logs to Smriti if that table doesn't exist).
"""
from __future__ import annotations

import logging
import sys
from typing import Optional

from .db import connect
from .events import emit_event

logger = logging.getLogger(__name__)

GLOBAL_LOCK_KEY = "global"


def acquire_global_lock(cur) -> bool:
    """Acquire exclusive advisory lock for global build. Non-blocking."""
    cur.execute(
        "SELECT pg_try_advisory_lock(hashtext(%s)) AS got",
        (GLOBAL_LOCK_KEY,),
    )
    row = cur.fetchone()
    return bool(row["got"])


def release_global_lock(cur) -> None:
    cur.execute("SELECT pg_advisory_unlock(hashtext(%s))", (GLOBAL_LOCK_KEY,))


def load_global_assets(cur) -> list[dict]:
    """Return all active global-scope assets ordered by sort_order."""
    cur.execute(
        """SELECT asset_id, layer, sanskrit_name, english_name,
                  target_table, target_floor, count_sql, depends_on
           FROM asset_registry
           WHERE scope = 'global' AND is_active = true
           ORDER BY layer, sort_order""",
    )
    return cur.fetchall()


def run_global_asset(conn, cur, asset: dict) -> bool:
    """
    Attempt to run the writer for a global-scope asset.
    Returns True if completed, False if skipped/failed.

    Global assets use chart_id=NULL in asset_throughput.
    The writer is resolved by asset_id convention:
      brahmagyan.X  →  brahmagyan.writers.X_writer
    If no writer module found, logs and continues (non-fatal).
    """
    asset_id: str = asset["asset_id"]
    logger.info("[global_runner] building asset: %s", asset_id)

    # Check if already lit (idempotency) — global assets have no chart_id
    cur.execute(
        """SELECT state FROM asset_throughput
           WHERE asset_id = %s AND chart_id IS NULL""",
        (asset_id,),
    )
    row = cur.fetchone()
    if row and row["state"] == "lit":
        logger.info("[global_runner] %s already lit — skip", asset_id)
        return True

    # Try to load and run the writer
    layer, _, name = asset_id.partition(".")
    writer_module = f"{layer}.writers.{name}_writer"

    try:
        import importlib
        mod = importlib.import_module(writer_module)
        writer_fn = getattr(mod, "run", None) or getattr(mod, "write", None)
        if writer_fn is None:
            logger.warning("[global_runner] no run/write fn in %s — skip", writer_module)
            _mark_asset_state(conn, cur, asset_id, "skipped", "no_writer_fn")
            return False
        writer_fn(conn=conn, cur=cur, asset=asset)
        _mark_asset_state(conn, cur, asset_id, "lit", None)
        emit_event({
            "type": "asset.lit",
            "asset_id": asset_id,
            "chart_id": None,
            "scope": "global",
        })
        return True
    except ModuleNotFoundError:
        logger.warning("[global_runner] writer module not found: %s — skip", writer_module)
        _mark_asset_state(conn, cur, asset_id, "skipped", "no_writer_module")
        return False
    except Exception as exc:
        logger.error("[global_runner] asset %s failed: %s", asset_id, exc, exc_info=True)
        _mark_asset_state(conn, cur, asset_id, "failed", str(exc)[:500])
        return False


def _mark_asset_state(conn, cur, asset_id: str, state: str, note: Optional[str]) -> None:
    # asset_throughput PK is just asset_id; global assets have chart_id=NULL
    cur.execute(
        """INSERT INTO asset_throughput (asset_id, chart_id, state, last_error, last_built_at)
           VALUES (%s, NULL, %s, %s, NOW())
           ON CONFLICT (asset_id) DO UPDATE
             SET state = EXCLUDED.state,
                 last_error = EXCLUDED.last_error,
                 last_built_at = NOW()
        """,
        (asset_id, state, note),
    )
    conn.commit()


def execute_global_build(run_id: Optional[str] = None) -> None:
    """
    Entry point for --global-build mode.
    Acquires global advisory lock, walks all global assets, releases lock.

    Exit codes:
      0  all assets processed (some may be skipped/failed — check throughput)
      3  global lock held by another process
      1  unexpected fatal error
    """
    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()

    if not acquire_global_lock(cur):
        logger.warning("[global_runner] global lock held by another process — deferring")
        conn.close()
        sys.exit(3)
    conn.commit()  # commit the advisory lock so it persists

    try:
        emit_event({"type": "global_build.started", "run_id": run_id})
        assets = load_global_assets(cur)
        logger.info("[global_runner] found %d global assets to process", len(assets))

        results = {"lit": 0, "skipped": 0, "failed": 0}
        for asset in assets:
            ok = run_global_asset(conn, cur, asset)
            if ok:
                results["lit"] += 1
            # failed/skipped tracked internally by run_global_asset

        logger.info("[global_runner] global build complete: %s", results)
        emit_event({"type": "global_build.completed", "run_id": run_id, "results": results})

    except Exception as exc:
        logger.error("[global_runner] global build fatal: %s", exc, exc_info=True)
        emit_event({"type": "global_build.failed", "run_id": run_id, "error": str(exc)})
        raise

    finally:
        try:
            release_global_lock(cur)
            conn.commit()
        except Exception:
            pass
        conn.close()
