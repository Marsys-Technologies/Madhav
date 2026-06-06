"""
pipeline.orchestrator.runner
============================

Core execution loop: load a build_run, acquire lock, walk per-asset plan.
"""
from __future__ import annotations

import logging
import sys
from typing import Optional

import psycopg

from .db import connect
from .events import emit_event
from .locks import acquire_chart_lock, release_chart_lock

logger = logging.getLogger(__name__)


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


def is_asset_complete(cur, chart_id: str, asset_id: str) -> bool:
    cur.execute(
        """SELECT state FROM asset_throughput
           WHERE chart_id = %s AND asset_id = %s""",
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

    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()

    run = load_run(cur, run_id)
    if run is None:
        logger.error("[orchestrator] build_run %s not found", run_id)
        conn.close()
        sys.exit(2)

    chart_id: str = run["chart_id"]
    plan: list[str] = run["plan"]

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
            signal = check_signals(cur, run_id)
            if signal == "stop":
                mark_run_state(conn, cur, run_id, "stopped", ended_at=True)
                emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": "stopped"})
                return
            if signal == "pause":
                mark_run_state(conn, cur, run_id, "paused")
                emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": "paused"})
                return

            if is_asset_complete(cur, chart_id, asset_id):
                logger.info("[orchestrator] skip %s (already lit)", asset_id)
                continue

            run_asset(conn, cur, run_id, chart_id, asset_id, position)

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
        try:
            release_chart_lock(cur, chart_id)
            conn.commit()
        except Exception:
            pass
        conn.close()
