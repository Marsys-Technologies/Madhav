"""
pipeline.orchestrator.asset_runner
====================================

Per-asset execution: state transitions, savepoint isolation, error recovery,
downstream stale marking.
"""
from __future__ import annotations

import hashlib
import logging
import os
import subprocess
import threading
import traceback

import psycopg

from .birth_params import fetch_birth_params
from .events import emit_event
from .writers import discover_all, get_writer, ContextSpec, WriterBase

logger = logging.getLogger(__name__)

# Serializes compute_downstream_closure + stale-mark UPDATE across worker threads.
# Under wave-parallel execution each worker owns a separate DB connection; without
# this lock two workers completing simultaneously can issue overlapping UPDATEs on
# the same downstream rows, causing row-lock contention or a deadlock (PostgreSQL
# locks rows in array scan order, which is not consistent across concurrent txns).
# The lock is held only during the short SELECT + UPDATE pair, never during the
# writer compute phase, so it adds negligible latency.
_stale_mark_lock = threading.Lock()

# Writer-entry dependency assertion (defense-in-depth layer 5).
#   enforce (default) — block the asset if any declared dep is not satisfied.
#   warn              — log loudly + emit event, but run anyway.
#   off               — skip the check entirely.
# The wave-parallel scheduler guarantees deps are lit before dispatch, so this is
# a backstop that catches scheduler bugs, out-of-order dispatch, or a never-built
# upstream — failing LOUD instead of silently building on missing data.
_DEP_ASSERT_MODE = os.environ.get("ORCHESTRATOR_DEP_ASSERT", "enforce").lower()


def deps_unsatisfied(cur, chart_id, asset_id: str) -> list[str]:
    """Return the list of this asset's declared deps that are NOT satisfied for the
    target scope, as 'dep(state)' strings. Empty list = all deps ready.

    A data dep is satisfied iff its asset_throughput.state == 'lit' at the correct
    scope (global deps -> chart_id IS NULL row; per-chart deps -> this chart's row).
    A service dep (asset_kind/type='service') has no data rows and is never 'lit';
    it is satisfied unless explicitly in 'error'.
    """
    cur.execute(
        "SELECT COALESCE(depends_on, '{}') AS deps FROM asset_registry WHERE asset_id = %s",
        (asset_id,),
    )
    row = cur.fetchone()
    # Defensive: a real dict_row has 'deps'; if the cursor can't resolve it (no row,
    # or a context that doesn't answer this query), treat as "no deps to verify" — the
    # assertion is a backstop, it must never crash the writer path.
    deps = list(row.get("deps") or []) if isinstance(row, dict) else []
    if not deps:
        return []
    cur.execute(
        """
        SELECT r.asset_id,
               COALESCE(r.asset_kind, r.asset_type) AS kind,
               t.state
        FROM asset_registry r
        LEFT JOIN LATERAL (
            SELECT state FROM asset_throughput at
            WHERE at.asset_id = r.asset_id
              AND (CASE WHEN r.scope = 'global' THEN at.chart_id IS NULL
                        ELSE at.chart_id = %s END)
            LIMIT 1
        ) t ON true
        WHERE r.asset_id = ANY(%s)
        """,
        (chart_id, deps),
    )
    bad: list[str] = []
    for d in cur.fetchall():
        state = d["state"]
        if d["kind"] == "service":
            if state == "error":
                bad.append(f"{d['asset_id']}(service:error)")
        elif state != "lit":
            bad.append(f"{d['asset_id']}({state or 'absent'})")
    return bad


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
        # Write service health telemetry to asset_registry (mig 242 columns).
        # health_probe result → 'healthy'; last_invoked_at = NOW().
        cur.execute(
            """UPDATE asset_registry
               SET service_health = 'healthy',
                   last_invoked_at = NOW(),
                   last_selftest_at = NOW()
               WHERE asset_id = %s""",
            (asset_id,),
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
        # Write degraded/unhealthy to asset_registry (mig 242 columns).
        health_col_value = "degraded" if status == "degraded" else "unhealthy"
        try:
            cur.execute(
                """UPDATE asset_registry
                   SET service_health = %s,
                       last_invoked_at = NOW()
                   WHERE asset_id = %s""",
                (health_col_value, asset_id),
            )
            conn.commit()
        except Exception as hc_exc:
            logger.debug("[orchestrator] service_health update skipped (col missing?): %s", hc_exc)
            try:
                conn.rollback()
            except Exception:
                pass
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


# ── Probe / verify-then-conditionally-regenerate (Phase 4 — the one new primitive) ─

def _probe_asset(conn, cur, asset_id: str, registry_row: dict, is_service: bool) -> tuple[bool, str]:
    """
    Run an asset's health/integrity check. Returns (green, message).

    - service asset (asset_type='service') → its health_probe.
    - data asset with integrity_check_sql → runs the SQL; convention: it returns a
      single row whose first column is truthy (boolean true / non-zero) when healthy.

    Generic + metadata-driven: works for BOTH L0 service probes AND L0 data-asset
    integrity checks, with no layer-specific branch (investigation §2.C).
    """
    if is_service:
        from pipeline.orchestrator.service_probes import run_health_probe
        try:
            r = run_health_probe(asset_id, registry_row.get("health_probe"))
        except Exception as exc:
            return False, f"{type(exc).__name__}: {exc}"
        return r.get("status") == "GREEN", r.get("message", "")

    integrity_sql = registry_row.get("integrity_check_sql")
    if integrity_sql:
        try:
            cur.execute(integrity_sql)
            row = cur.fetchone()
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                pass
            return False, f"integrity_check_sql error: {exc}"
        if not row:
            return False, "integrity_check_sql returned no rows"
        val = next(iter(row.values())) if isinstance(row, dict) else row[0]
        return bool(val), f"integrity_check_sql → {val}"

    return False, "no check defined"


def _mark_probe_green(conn, cur, run_id: str, chart_id: str, asset_id: str, message: str) -> None:
    """Skip-if-green: mark the asset lit WITHOUT running its writer (no rows)."""
    cur.execute(
        """UPDATE asset_throughput
           SET state = 'lit', last_built_at = NOW(),
               rows_written = COALESCE(rows_written, 0), last_error = NULL
           WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s""",
        (chart_id, asset_id),
    )
    cur.execute(
        """UPDATE build_run_assets SET state = 'complete', ended_at = NOW()
           WHERE run_id = %s AND asset_id = %s""",
        (run_id, asset_id),
    )
    conn.commit()
    emit_event({"type": "asset.probe", "chart_id": chart_id, "asset_id": asset_id,
                "status": "green", "action": "skipped", "message": message[:500]})
    emit_event({"type": "asset.state_change", "chart_id": chart_id, "asset_id": asset_id,
                "from_state": "building", "to_state": "lit"})


def _run_data_writer(conn, cur, run_id: str, chart_id: str, asset_id: str) -> bool:
    """
    Run a data asset's registered writer to completion (sub-step driven). Marks
    'lit' + downstream stale on success (returns True); marks 'error' and returns
    False on failure. Reused by both the normal data path and the regenerate path.
    """
    discover_all()
    writer_cls = get_writer(asset_id)
    if writer_cls is None:
        mark_asset_error(conn, cur, run_id, chart_id, asset_id, f"no writer registered for {asset_id}")
        return False

    writer = writer_cls()
    if chart_id is None:
        # Global-scope asset: no chart_id → no birth_params needed (writer must not use them).
        birth_params = {}
    else:
        try:
            birth_params = fetch_birth_params(conn, chart_id)
        except Exception as exc:
            mark_asset_error(conn, cur, run_id, chart_id, asset_id, f"birth_params: {exc}")
            return False

    ctx = ContextSpec(
        asset_id=asset_id, build_id=run_id, db_conn=conn,
        config={'chart_id': chart_id, 'birth_params': birth_params},
    )
    try:
        rows_inserted, rows_updated = _drive_substeps(conn, cur, run_id, chart_id, asset_id, writer, ctx)
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[:2000]}"
        logger.warning("[orchestrator] writer %s failed: %s", asset_id, err[:200])
        mark_asset_error(conn, cur, run_id, chart_id, asset_id, err)
        return False

    rows_written = int((rows_inserted + rows_updated) or 0)

    # When a chart-scoped data writer produces 0 rows, record 'dormant' rather than
    # 'lit'. 'lit' would cause the plan resolver's action='build' filter to exclude
    # the asset (filter picks only dormant/error/missing), leaving the Build button
    # stuck with an empty plan. 'dormant' correctly signals "ran but produced nothing
    # — safe to retry". Global assets (chart_id is None) are service singletons and
    # always get 'lit' regardless of rows_written.
    final_state = 'lit'
    if rows_written == 0 and chart_id is not None:
        # Check whether the asset declares target_floor=0 (meaning 0 rows = complete
        # by design, e.g. ga_prashna with no prashna charts). Only write 'dormant'
        # when target_floor is None or > 0 (i.e. rows were expected but not produced).
        cur.execute(
            "SELECT target_floor FROM asset_registry WHERE asset_id = %s",
            (asset_id,),
        )
        _tf_row = cur.fetchone()
        _target_floor = _tf_row["target_floor"] if _tf_row else None
        if _target_floor != 0:
            final_state = 'dormant'

    upstream_hash = compute_upstream_hash(cur, asset_id, chart_id)
    writer_hash = get_writer_git_hash(asset_id)

    cur.execute(
        """UPDATE asset_throughput
           SET state = %s, last_built_at = NOW(), rows_written = %s,
               built_against_upstream_hash = %s, built_against_writer_hash = %s,
               last_error = NULL
           WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s""",
        (final_state, rows_written, upstream_hash, writer_hash, chart_id, asset_id),
    )
    cur.execute(
        """UPDATE build_run_assets SET state = 'complete', ended_at = NOW()
           WHERE run_id = %s AND asset_id = %s""",
        (run_id, asset_id),
    )
    conn.commit()

    emit_event({"type": "asset.state_change", "chart_id": chart_id, "asset_id": asset_id,
                "from_state": "building", "to_state": final_state})
    emit_event({"type": "asset.progress", "chart_id": chart_id, "asset_id": asset_id,
                "rows_written": rows_written})

    with _stale_mark_lock:
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
            emit_event({"type": "asset.state_change", "chart_id": chart_id, "asset_id": d,
                        "from_state": "lit", "to_state": "stale"})

    logger.info("[orchestrator] asset %s complete — %d rows", asset_id, rows_written)
    return True


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

    # ── Writer-entry dependency assertion (defense-in-depth) ───────────────────
    # Verify every declared dependency is actually committed-complete BEFORE running
    # the writer. This is the last line catching a scheduler bug, out-of-order
    # dispatch, or a never-built upstream — so the writer never silently builds on
    # missing/incomplete data (many writers swallow missing-table reads).
    if _DEP_ASSERT_MODE != "off":
        unmet = deps_unsatisfied(cur, chart_id, asset_id)
        if unmet:
            detail = ", ".join(sorted(unmet))
            if _DEP_ASSERT_MODE == "warn":
                logger.warning(
                    "[orchestrator] DEP-ASSERT(warn) %s: unmet deps [%s] — running anyway",
                    asset_id, detail,
                )
                emit_event({"type": "asset.dep_assert", "chart_id": chart_id,
                            "asset_id": asset_id, "mode": "warn", "unmet": detail[:500]})
            else:  # enforce
                msg = (
                    "DEP-ASSERT: declared dependency(ies) not lit before run: %s — "
                    "refused to build on incomplete/missing upstream data" % detail
                )
                logger.error("[orchestrator] %s %s", asset_id, msg)
                mark_asset_error(conn, cur, run_id, chart_id, asset_id, msg)
                conn.commit()
                emit_event({"type": "asset.state_change", "chart_id": chart_id,
                            "asset_id": asset_id, "from_state": "queued",
                            "to_state": "error", "error": msg[:500]})
                return

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

    # Asset metadata: probe/integrity-check + rebuild policy (Phase 4).
    cur.execute(
        """SELECT asset_kind, asset_type, health_probe, rebuild_on_probe_fail, integrity_check_sql
           FROM asset_registry WHERE asset_id = %s""",
        (asset_id,),
    )
    registry_row = cur.fetchone() or {}
    # asset_kind is canonical since migration 242; asset_type retained for legacy bg_* rows
    is_service = (registry_row.get("asset_kind") == "service"
                  or registry_row.get("asset_type") == "service")
    has_check = is_service or bool(registry_row.get("integrity_check_sql"))
    rebuild_policy = bool(registry_row.get("rebuild_on_probe_fail"))

    # ── Generic verify-then-conditionally-regenerate (the only new primitive) ──
    # Metadata-driven, no `if layer == ...`: any asset (any layer) with a
    # probe/integrity check AND rebuild_on_probe_fail=true participates. GREEN →
    # skip (no writer run); FAIL → regenerate ONLY this asset via its registered
    # writer → re-probe → lit / error. Works for L0 service probes AND L0 data
    # integrity checks alike (investigation §2.C).
    if has_check and rebuild_policy:
        ok, msg = _probe_asset(conn, cur, asset_id, registry_row, is_service)
        if ok:
            _mark_probe_green(conn, cur, run_id, chart_id, asset_id, msg)
            return
        emit_event({"type": "asset.probe", "chart_id": chart_id, "asset_id": asset_id,
                    "status": "failed", "action": "regenerating", "message": msg[:500]})
        if get_writer(asset_id) is None:
            mark_asset_error(conn, cur, run_id, chart_id, asset_id,
                             f"probe failed ({msg}); no writer to regenerate")
            return
        if not _run_data_writer(conn, cur, run_id, chart_id, asset_id):
            return  # writer failed; already marked error
        ok2, msg2 = _probe_asset(conn, cur, asset_id, registry_row, is_service)
        if ok2:
            emit_event({"type": "asset.probe", "chart_id": chart_id, "asset_id": asset_id,
                        "status": "green", "action": "regenerated"})
        else:
            mark_asset_error(conn, cur, run_id, chart_id, asset_id,
                             f"regenerate-then-probe still failing: {msg2}")
        return

    if is_service:
        # Service assets with a registered WriterBase writer (e.g. ka_graha_sancara,
        # ka_muhurta_seva) use the writer's run() for their self-test — they are
        # "service writers", not legacy health-probe-spec services. Route through
        # _run_data_writer which now safely handles chart_id=None (global-scope backstop).
        discover_all()
        if get_writer(asset_id) is not None:
            _run_data_writer(conn, cur, run_id, chart_id, asset_id)
            return
        # Legacy health-probe path (bg_* assets with health_probe JSONB spec).
        _run_service_health_probe(conn, cur, run_id, chart_id, asset_id,
                                  registry_row.get("health_probe"))
        return

    # Data asset: run its registered writer to completion (sub-step driven).
    _run_data_writer(conn, cur, run_id, chart_id, asset_id)
