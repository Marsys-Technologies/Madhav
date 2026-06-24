"""
pipeline.orchestrator.runner
============================

Core execution loop: load a build_run, acquire lock, walk per-asset plan.
"""
from __future__ import annotations

import logging
import os
import signal
import sys
from typing import Optional

import psycopg

from .db import connect
from .events import emit_event
from .locks import acquire_chart_lock, release_chart_lock

logger = logging.getLogger(__name__)

# Concurrency cap: keep worst-case orchestrator connections well under Cloud SQL
# max_connections=50 (budget: 50 − ~12 app/agent headroom − 5 margin = 33 available).
# Default 10 leaves ample room; override via env var for larger deployments.
_MAX_CONCURRENT_RUNS = int(os.environ.get("ORCHESTRATOR_MAX_CONCURRENT_RUNS", "10"))


# ── Run-level helpers ─────────────────────────────────────────────────────────

def load_run(cur, run_id: str) -> Optional[dict]:
    cur.execute(
        """SELECT id, chart_id, scope, scope_target, action, plan, state
           FROM build_runs WHERE id = %s""",
        (run_id,),
    )
    return cur.fetchone()


def mark_run_state(
    conn: psycopg.Connection,
    cur,
    run_id: str,
    state: str,
    started_at: bool = False,
    ended_at: bool = False,
) -> None:
    parts = ["state = %s"]
    values: list = [state]
    if started_at:
        parts.append("started_at = COALESCE(started_at, NOW())")
    if ended_at:
        parts.append("ended_at = NOW()")
    sql = f"UPDATE build_runs SET {', '.join(parts)} WHERE id = %s"
    values.append(run_id)
    cur.execute(sql, values)
    conn.commit()


def check_signals(cur, run_id: str) -> Optional[str]:
    cur.execute(
        "SELECT pause_requested_at, stop_requested_at FROM build_runs WHERE id = %s",
        (run_id,),
    )
    row = cur.fetchone()
    if not row:
        return "stop"
    if row["stop_requested_at"]:
        return "stop"
    if row["pause_requested_at"]:
        return "pause"
    return None


def is_asset_complete(cur, chart_id, asset_id: str) -> bool:
    cur.execute(
        """SELECT state FROM asset_throughput
           WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s""",
        (chart_id, asset_id),
    )
    row = cur.fetchone()
    return row is not None and row["state"] == "lit"


# ── Main entry ────────────────────────────────────────────────────────────────

def execute_run(run_id: str) -> None:
    """
    Load build_run by run_id, acquire chart advisory lock, walk the asset plan.

    Exit codes:
      0  — completed or stopped/paused cleanly
      2  — run not found
      3  — chart locked by another run (defer)
    """
    from .asset_runner import run_asset  # imported here to break circular deps
    from .writers import discover_all    # D1: ensure all writer modules are imported
    discover_all()

    # SIGTERM → SystemExit so finally blocks run and the connection is cleaned up.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()

    # Concurrency cap: defer if too many runs are already active.
    cur.execute("SELECT count(*) AS active FROM build_runs WHERE state = 'running'")
    active_count = cur.fetchone()["active"]
    if active_count >= _MAX_CONCURRENT_RUNS:
        logger.warning(
            "[orchestrator] max concurrent runs (%d) reached (%d active) — deferring run %s",
            _MAX_CONCURRENT_RUNS, active_count, run_id,
        )
        conn.close()
        sys.exit(3)

    run = load_run(cur, run_id)
    if run is None:
        logger.error("[orchestrator] build_run %s not found", run_id)
        conn.close()
        sys.exit(2)

    chart_id: str = run["chart_id"]
    plan: list[str] = run["plan"]

    # Preload asset scopes so global assets (scope='global') are always dispatched with
    # chart_id=None — they are singletons independent of any chart.  Passing a non-None
    # chart_id to run_asset() for a global asset creates a spurious chart-scoped
    # asset_throughput row that shadows the correct global row in the stats query.
    cur.execute(
        "SELECT asset_id, scope FROM asset_registry WHERE asset_id = ANY(%s)",
        (plan,),
    )
    _asset_scopes: dict[str, str] = {r["asset_id"]: r["scope"] for r in cur.fetchall()}

    if not acquire_chart_lock(cur, chart_id):
        logger.warning("[orchestrator] chart %s locked by another run — deferring", chart_id)
        conn.close()
        sys.exit(3)
    # Lock acquired; commit the advisory lock transaction so it survives later commits
    conn.commit()

    try:
        mark_run_state(conn, cur, run_id, "running", started_at=True)
        emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": "running"})

        for position, asset_id in enumerate(plan):
            sig = check_signals(cur, run_id)
            if sig == "stop":
                mark_run_state(conn, cur, run_id, "stopped", ended_at=True)
                emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": "stopped"})
                return
            if sig == "pause":
                mark_run_state(conn, cur, run_id, "paused")
                emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": "paused"})
                return

            # Global assets are chart-independent singletons; run with chart_id=None
            # so run_asset() targets the `WHERE chart_id IS NULL` partial index.
            effective_chart_id = None if _asset_scopes.get(asset_id) == "global" else chart_id

            if is_asset_complete(cur, effective_chart_id, asset_id):
                logger.info("[orchestrator] skip %s (already lit)", asset_id)
                continue

            run_asset(conn, cur, run_id, effective_chart_id, asset_id, position)

        mark_run_state(conn, cur, run_id, "completed", ended_at=True)
        emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": "completed"})

    except Exception as exc:
        logger.error("[orchestrator] unexpected error: %s", exc, exc_info=True)
        try:
            mark_run_state(conn, cur, run_id, "failed", ended_at=True)
            emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": "failed"})
        except Exception:
            pass
        raise

    finally:
        # Guard B: roll back any open transaction BEFORE releasing the advisory
        # lock, so a killed/interrupted build never leaves a txn open on the
        # connection. Advisory locks are session-level and survive ROLLBACK, so
        # the unlock below is still effective after the rollback.
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            release_chart_lock(cur, chart_id)
            conn.commit()
        except Exception:
            pass
        conn.close()
