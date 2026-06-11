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
from .writers import discover_all, get_writer, ContextSpec, WriterBase

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


def _writer_source_paths(asset_id: str) -> list[str]:
    """
    Locate the source file(s) whose git history represents a writer — wherever
    the writer lives (Orchestrator Convergence Phase 3: GA writers live in
    ga_writers/, not pipeline/orchestrator/writers/, so the old hard-coded path
    is wrong for them). Resolution order, generic + registry-driven:

      1. the registered class's `source_paths` (repo-relative) if declared
         (GA adapters set this to their ga_writers/ module);
      2. else the registered class's own module file (inspect.getfile);
      3. else fall back to the legacy convention.
    """
    import inspect

    cls = get_writer(asset_id)
    if cls is not None:
        declared = getattr(cls, "source_paths", None)
        if declared:
            return list(declared)
        try:
            abs = inspect.getfile(cls)
            idx = abs.find("platform/python-sidecar/")
            return [abs[idx:] if idx >= 0 else abs]
        except Exception:
            pass
    return [f"platform/python-sidecar/pipeline/orchestrator/writers/{asset_id.replace('.', '/')}.py"]


def get_writer_git_hash(asset_id: str) -> str:
    paths = _writer_source_paths(asset_id)
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", *paths],
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


# ── Sub-step driver (Orchestrator Convergence Phase 2) ────────────────────────

def _drive_substeps(
    conn: psycopg.Connection,
    cur,
    run_id: str,
    chart_id: str,
    asset_id: str,
    writer: WriterBase,
    ctx: ContextSpec,
    completed_keys: set[str] | None = None,
) -> tuple[int, int]:
    """
    Drive a writer's sub-steps, each as its own SAVEPOINT + heartbeat + commit.

    - `plan_substeps(ctx)` yields the chunk grain: ONE default sub-step for a
      light writer (whole asset), N for a heavy writer (e.g. ga_dashas → 35
      system×ayanamsha chunks).
    - Each sub-step runs inside `SAVEPOINT writer_exec`; on failure the sub-step
      is rolled back to the savepoint and the exception re-raised (the caller
      marks the asset errored) — prior committed sub-steps stay durable.
    - After each successful sub-step: refresh `asset_throughput.last_built_at`
      (the reaper heartbeat — see watchdog/route.ts) + cumulative `rows_written`,
      commit, and emit an `asset.substep` event (granular SSE).
    - `completed_keys` (optional) lets a resumed run SKIP already-finished chunks;
      omitted on a fresh run, where writer idempotency (replace-not-accrete,
      scoped to `step.key`) makes an accidental re-run safe anyway.

    The writer MUST NOT commit/rollback/close — this driver owns the transaction
    lifecycle (one commit per sub-step). Returns (rows_inserted, rows_updated).
    """
    completed_keys = completed_keys or set()
    substeps = writer.plan_substeps(ctx)
    total = len(substeps)
    rows_inserted = 0
    rows_updated = 0

    for idx, step in enumerate(substeps):
        if step.key in completed_keys:
            emit_event({
                "type": "asset.substep",
                "chart_id": chart_id,
                "asset_id": asset_id,
                "substep_key": step.key,
                "substep_label": step.label,
                "index": idx + 1,
                "total": total,
                "skipped": True,
            })
            continue

        cur.execute("SAVEPOINT writer_exec")
        try:
            result = writer.run_substep(ctx, step)
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT writer_exec")
            raise
        cur.execute("RELEASE SAVEPOINT writer_exec")

        rows_inserted += int(result.rows_inserted or 0)
        rows_updated += int(result.rows_updated or 0)

        # Heartbeat: keep the asset visibly alive for BOTH reapers and feed live
        # cockpit progress. Cumulative rows_written is finalized below in run_asset.
        cur.execute(
            """UPDATE asset_throughput
               SET last_built_at = NOW(), rows_written = %s
               WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s""",
            (rows_inserted + rows_updated, chart_id, asset_id),
        )
        conn.commit()

        emit_event({
            "type": "asset.substep",
            "chart_id": chart_id,
            "asset_id": asset_id,
            "substep_key": step.key,
            "substep_label": step.label,
            "index": idx + 1,
            "total": total,
            "rows_written": rows_inserted + rows_updated,
        })

    return rows_inserted, rows_updated


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

    # Execute the writer as a sequence of sub-steps, each its own savepoint +
    # last_built_at heartbeat + commit (see _drive_substeps). A light writer
    # yields a single default sub-step (behaviour identical to the old single
    # SAVEPOINT path); a heavy writer yields its natural chunks so a 40-min asset
    # stays under both reapers and resumes per-chunk. Writer must NOT
    # commit/rollback/close — this driver owns the transaction lifecycle.
    writer = writer_cls()
    ctx = ContextSpec(
        asset_id=asset_id,
        build_id=run_id,
        db_conn=conn,
        config={'chart_id': chart_id},
    )
    try:
        rows_inserted, rows_updated = _drive_substeps(
            conn, cur, run_id, chart_id, asset_id, writer, ctx,
        )
    except Exception as exc:
        # The failed sub-step was already rolled back to its savepoint inside
        # _drive_substeps; prior committed sub-steps stay durable. Mark errored.
        err = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[:2000]}"
        logger.warning("[orchestrator] writer %s failed: %s", asset_id, err[:200])
        mark_asset_error(conn, cur, run_id, chart_id, asset_id, err)
        return

    rows_written = int((rows_inserted + rows_updated) or 0)
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
