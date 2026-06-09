"""
pipeline.orchestrator.asset_runner
====================================

Per-asset execution: state transitions, savepoint isolation, error recovery,
downstream stale marking.
"""
from __future__ import annotations

import hashlib
import logging
import subprocess
import traceback

import psycopg

from .events import emit_event
from .writers import discover_all, get_writer, ContextSpec

logger = logging.getLogger(__name__)


# ── Downstream closure ────────────────────────────────────────────────────────

def compute_downstream_closure(cur, asset_id: str) -> list[str]:
    """All assets that transitively depend on asset_id (text[] depends_on)."""
    cur.execute(
        """
        WITH RECURSIVE downstream AS (
            SELECT asset_id FROM asset_registry
            WHERE %s = ANY(depends_on)
            UNION
            SELECT ar.asset_id FROM asset_registry ar
            INNER JOIN downstream d ON d.asset_id = ANY(ar.depends_on)
        )
        SELECT asset_id FROM downstream WHERE asset_id != %s
        """,
        (asset_id, asset_id),
    )
    return [r["asset_id"] for r in cur.fetchall()]


# ── Hash helpers ──────────────────────────────────────────────────────────────

def compute_upstream_hash(cur, asset_id: str, chart_id: str) -> str:
    cur.execute(
        """
        SELECT ar.asset_id, t.last_built_at
        FROM asset_registry ar
        LEFT JOIN asset_throughput t
          ON t.asset_id = ar.asset_id AND t.chart_id IS NOT DISTINCT FROM %s
        WHERE ar.asset_id = ANY(
            SELECT unnest(depends_on) FROM asset_registry WHERE asset_id = %s
        )
        ORDER BY ar.asset_id
        """,
        (chart_id, asset_id),
    )
    payload = "|".join(f"{r['asset_id']}:{r['last_built_at']}" for r in cur.fetchall())
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def get_writer_git_hash(asset_id: str) -> str:
    path = f"platform/python-sidecar/pipeline/orchestrator/writers/{asset_id.replace('.', '/')}.py"
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", path],
            capture_output=True, text=True, timeout=2,
        )
        return result.stdout.strip()[:16] if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


# ── Error helper ──────────────────────────────────────────────────────────────

def mark_asset_error(
    conn: psycopg.Connection,
    cur,
    run_id: str,
    chart_id: str,
    asset_id: str,
    error: str,
) -> None:
    cur.execute(
        """UPDATE asset_throughput
           SET state = 'error', last_error = %s, last_built_at = NOW()
           WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s""",
        (error, chart_id, asset_id),
    )
    cur.execute(
        """UPDATE build_run_assets SET state = 'error', ended_at = NOW(), error = %s
           WHERE run_id = %s AND asset_id = %s""",
        (error[:2000], run_id, asset_id),
    )
    conn.commit()
    emit_event({
        "type": "asset.state_change",
        "chart_id": chart_id,
        "asset_id": asset_id,
        "from_state": "building",
        "to_state": "error",
        "error": error[:500],
    })


# ── Service asset health-probe runner ─────────────────────────────────────────

def _run_service_health_probe(
    conn: psycopg.Connection,
    cur,
    run_id: str,
    chart_id: str,
    asset_id: str,
    health_probe: dict | None,
) -> None:
    """
    Execute the health probe for a service asset (storage_type='service').
    Reports GREEN/degraded/down to asset_throughput and build_run_assets.
    A service "build" produces no rows — integrity (FORENSIC-consistent smoke) is the gate.
    """
    from pipeline.orchestrator.service_probes import run_health_probe

    try:
        result = run_health_probe(asset_id, health_probe)
        status = result.get("status", "unknown")  # "GREEN" | "degraded" | "down"
        message = result.get("message", "")
    except Exception as exc:
        status = "down"
        message = f"{type(exc).__name__}: {exc}"

    if status == "GREEN":
        cur.execute(
            """UPDATE asset_throughput
               SET state = 'lit', last_built_at = NOW(), rows_written = 0, last_error = NULL
               WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s""",
            (chart_id, asset_id),
        )
        cur.execute(
            """UPDATE build_run_assets SET state = 'complete', ended_at = NOW()
               WHERE run_id = %s AND asset_id = %s""",
            (run_id, asset_id),
        )
        conn.commit()
        emit_event({
            "type": "asset.state_change",
            "chart_id": chart_id,
            "asset_id": asset_id,
            "from_state": "building",
            "to_state": "lit",
            "service_health": "GREEN",
        })
        logger.info("[orchestrator] service %s health probe GREEN", asset_id)
    else:
        error_msg = f"service health: {status} — {message}"
        mark_asset_error(conn, cur, run_id, chart_id, asset_id, error_msg)
        logger.warning("[orchestrator] service %s health probe %s: %s", asset_id, status, message)


# ── Main per-asset execution ──────────────────────────────────────────────────

def run_asset(
    conn: psycopg.Connection,
    cur,
    run_id: str,
    chart_id: str,
    asset_id: str,
    position: int,
) -> None:
    """
    Execute one asset writer inside a savepoint.

    Robustness properties:
    - Savepoint isolation: writer crash rolls back only its writes, not run state.
    - Per-asset error recovery: asset goes to 'error' but run continues.
    - Downstream stale marking: transitive downstream assets flipped to 'stale'.
    """
    logger.info("[orchestrator] starting asset %s (pos=%d)", asset_id, position)

    # Ensure asset_throughput row exists for this (chart_id, asset_id).
    # Global assets (chart_id IS NULL) use a separate partial unique index (migration 184).
    if chart_id is not None:
        cur.execute(
            """INSERT INTO asset_throughput (asset_id, chart_id, state)
               VALUES (%s, %s, 'building')
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'building', last_error = NULL""",
            (asset_id, chart_id),
        )
    else:
        cur.execute(
            """INSERT INTO asset_throughput (asset_id, chart_id, state)
               VALUES (%s, NULL, 'building')
               ON CONFLICT (asset_id) WHERE chart_id IS NULL
               DO UPDATE SET state = 'building', last_error = NULL""",
            (asset_id,),
        )

    cur.execute(
        """INSERT INTO build_run_assets (run_id, asset_id, position, state, started_at)
           VALUES (%s, %s, %s, 'building', NOW())
           ON CONFLICT (run_id, asset_id)
           DO UPDATE SET state = 'building', started_at = NOW()""",
        (run_id, asset_id, position),
    )

    cur.execute(
        "UPDATE build_runs SET current_asset_id = %s WHERE id = %s",
        (asset_id, run_id),
    )
    conn.commit()

    emit_event({
        "type": "asset.state_change",
        "chart_id": chart_id,
        "asset_id": asset_id,
        "from_state": None,
        "to_state": "building",
    })

    # Check whether this asset is a service (asset_type='service' per migration 202)
    cur.execute(
        "SELECT asset_type, health_probe FROM asset_registry WHERE asset_id = %s",
        (asset_id,),
    )
    registry_row = cur.fetchone()
    is_service = registry_row and registry_row.get("asset_type") == "service"

    if is_service:
        # Service "build" = run health probe. No row writer involved.
        _run_service_health_probe(conn, cur, run_id, chart_id, asset_id,
                                  registry_row.get("health_probe"))
        return

    # Resolve writer (discover_all is idempotent; self-heals if runner.py skipped it)
    discover_all()
    writer_cls = get_writer(asset_id)
    if writer_cls is None:
        mark_asset_error(conn, cur, run_id, chart_id, asset_id, f"no writer registered for {asset_id}")
        return

    # Execute writer inside savepoint — crash rolls back only its writes
    # Writer must NOT commit/rollback; caller owns the transaction.
    cur.execute("SAVEPOINT writer_exec")
    try:
        ctx = ContextSpec(
            asset_id=asset_id,
            build_id=run_id,
            db_conn=conn,
            config={'chart_id': chart_id},
        )
        result = writer_cls().run(ctx)
        rows_written = result.rows_inserted + result.rows_updated
    except Exception as exc:
        cur.execute("ROLLBACK TO SAVEPOINT writer_exec")
        err = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[:2000]}"
        logger.warning("[orchestrator] writer %s failed: %s", asset_id, err[:200])
        mark_asset_error(conn, cur, run_id, chart_id, asset_id, err)
        return
    cur.execute("RELEASE SAVEPOINT writer_exec")

    rows_written = int(rows_written or 0)
    upstream_hash = compute_upstream_hash(cur, asset_id, chart_id)
    writer_hash = get_writer_git_hash(asset_id)

    cur.execute(
        """UPDATE asset_throughput
           SET state = 'lit',
               last_built_at = NOW(),
               rows_written = %s,
               built_against_upstream_hash = %s,
               built_against_writer_hash = %s,
               last_error = NULL
           WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s""",
        (rows_written, upstream_hash, writer_hash, chart_id, asset_id),
    )

    cur.execute(
        """UPDATE build_run_assets SET state = 'complete', ended_at = NOW()
           WHERE run_id = %s AND asset_id = %s""",
        (run_id, asset_id),
    )
    conn.commit()

    emit_event({
        "type": "asset.state_change",
        "chart_id": chart_id,
        "asset_id": asset_id,
        "from_state": "building",
        "to_state": "lit",
    })
    emit_event({
        "type": "asset.progress",
        "chart_id": chart_id,
        "asset_id": asset_id,
        "rows_written": rows_written,
    })

    # Mark transitive downstream stale
    downstream = compute_downstream_closure(cur, asset_id)
    if downstream:
        cur.execute(
            """UPDATE asset_throughput SET state = 'stale'
               WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = ANY(%s)
               AND state IN ('lit', 'mature')""",
            (chart_id, downstream),
        )
        conn.commit()
        for d in downstream:
            emit_event({
                "type": "asset.state_change",
                "chart_id": chart_id,
                "asset_id": d,
                "from_state": "lit",
                "to_state": "stale",
            })

    logger.info("[orchestrator] asset %s complete — %d rows", asset_id, rows_written)
