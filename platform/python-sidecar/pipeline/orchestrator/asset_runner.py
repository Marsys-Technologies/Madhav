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


# ── Data-presence probe (D-1.6 state-write defect fix) ───────────────────────

def _data_rows_present(conn, cur, asset_id: str, chart_id) -> int | None:
    """Count the data rows that actually exist for (asset_id, chart_id) using the
    asset's chart-scoped `count_sql` from asset_registry (§N.4 "Cockpit truth").

    Used to distinguish "writer ran and produced nothing because NO data exists"
    (a real dormant) from "writer reported 0 rows this run but the asset's data IS
    present" (e.g. a resumable writer like ka_sangam whose cross-attempt ledger
    said every substep was already committed, so it planned zero substeps — the
    D-1.6 incident, run 71b260c7).

    Returns the row count, or None when the probe cannot answer (no count_sql,
    global asset, or SQL failure). NEVER raises, and savepoint-isolates the count
    query so a broken count_sql cannot abort the caller's ambient transaction.
    """
    if chart_id is None:
        return None
    try:
        cur.execute(
            "SELECT count_sql FROM asset_registry WHERE asset_id = %s",
            (asset_id,),
        )
        row = cur.fetchone()
        count_sql = (row or {}).get("count_sql") if isinstance(row, dict) else None
        if not count_sql or "$1" not in count_sql:
            return None
        cur.execute("SAVEPOINT presence_probe")
        try:
            cur.execute(count_sql.replace("$1", "%s"), (chart_id,))
            r = cur.fetchone()
            cur.execute("RELEASE SAVEPOINT presence_probe")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT presence_probe")
            raise
        if r is None:
            return None
        val = next(iter(r.values())) if isinstance(r, dict) else r[0]
        return int(val or 0)
    except Exception as exc:
        logger.warning(
            "[orchestrator] presence probe failed for %s (chart %s): %s",
            asset_id, chart_id, exc,
        )
        return None


def _upsert_throughput_state(cur, chart_id, asset_id: str, state: str, error: str | None) -> None:
    """Recovery INSERT for a state UPDATE that matched 0 rows — the throughput row
    is missing (it should have been created by run_asset's 'building' upsert).
    Mirrors run_asset's partial-unique-index upsert forms (migration 184)."""
    if chart_id is not None:
        cur.execute(
            """INSERT INTO asset_throughput (asset_id, chart_id, state, last_error, last_built_at)
               VALUES (%s, %s, %s, %s, NOW())
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state=EXCLUDED.state, last_error=EXCLUDED.last_error, last_built_at=NOW()""",
            (asset_id, chart_id, state, error),
        )
    else:
        cur.execute(
            """INSERT INTO asset_throughput (asset_id, chart_id, state, last_error, last_built_at)
               VALUES (%s, NULL, %s, %s, NOW())
               ON CONFLICT (asset_id) WHERE chart_id IS NULL
               DO UPDATE SET state=EXCLUDED.state, last_error=EXCLUDED.last_error, last_built_at=NOW()""",
            (asset_id, state, error),
        )


def _guard_state_write(cur, run_id: str, chart_id, asset_id: str, intended_state: str,
                       error: str | None = None) -> None:
    """SAFETY NET (D-1.6): a state UPDATE on asset_throughput that matched 0 rows
    means the intended state transition was silently LOST — exactly the failure
    mode that cost wall-clock time in the D-1.6 incident because nothing surfaced
    it. Log loudly with actionable diagnostics and re-insert the row so the state
    is never dropped. Call immediately after a state UPDATE on asset_throughput."""
    rc = getattr(cur, "rowcount", None)
    if rc != 0:
        return
    logger.error(
        "[orchestrator] STATE-WRITE ANOMALY: asset_throughput UPDATE matched 0 rows "
        "— intended state '%s' for asset=%s chart=%s run=%s would have been silently "
        "lost (row missing; expected a 'building' row from run_asset). Re-inserting.",
        intended_state, asset_id, chart_id, run_id,
    )
    try:
        _upsert_throughput_state(cur, chart_id, asset_id, intended_state, error)
        emit_event({
            "type": "asset.state_write_anomaly",
            "chart_id": chart_id,
            "asset_id": asset_id,
            "run_id": run_id,
            "intended_state": intended_state,
            "recovered": True,
        })
    except Exception as exc:
        logger.error(
            "[orchestrator] STATE-WRITE ANOMALY recovery insert also failed for %s: %s",
            asset_id, exc,
        )


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
    _guard_state_write(cur, run_id, chart_id, asset_id, "error", error)
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
    upstream_hash = compute_upstream_hash(cur, asset_id, chart_id)
    writer_hash = get_writer_git_hash(asset_id)

    # Determine whether 0 rows is correct completion for this asset.
    # target_floor=0 in asset_registry is the explicit declaration that a writer
    # may correctly produce 0 rows (e.g. ga_prashna on natal charts — the writer
    # ran, evaluated, found no prashna question, and returned nothing by design).
    # Such assets must be 'lit' so the plan resolver stops re-queuing them.
    # For assets with target_floor > 0, 0 rows means a silent failure → 'dormant'
    # keeps them in the plan so the next build retries them.
    # Global assets (chart_id IS NULL) are service singletons — always 'lit'.
    cur.execute(
        "SELECT target_floor FROM asset_registry WHERE asset_id = %s",
        (asset_id,),
    )
    reg_row = cur.fetchone()
    target_floor = reg_row["target_floor"] if reg_row else None

    zero_rows_is_complete = (chart_id is None) or (target_floor == 0)
    final_state = 'lit' if (rows_written > 0 or zero_rows_is_complete) else 'dormant'

    # ── No-op-completion reclassification (D-1.6 root-cause fix) ──────────────
    # 'dormant' means "ran and produced nothing → data absent → retry next build".
    # But a writer with cross-attempt substep resumption (ka_sangam, migration 436)
    # can legitimately report 0 rows THIS RUN because every substep was already
    # committed by a prior same-fingerprint build — its data is fully present and
    # correct. Marking that 'dormant' poisons every downstream DEP-ASSERT (the
    # D-1.6 incident: run 71b260c7, ka_sangam(dormant) → 24 BLOCKED). Before
    # accepting 'dormant', probe the asset's actual data via its chart-scoped
    # count_sql: if rows exist, this was a no-op completion → 'lit', loudly.
    if final_state == 'dormant':
        present = _data_rows_present(conn, cur, asset_id, chart_id)
        if present is not None and present > 0:
            # SATYA-DIPA (asset_runner.py:596-630, authorized freeze exception —
            # see ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md): rows being present is
            # necessary but not sufficient. A genuinely partial substep plan can
            # also leave rows present (from whatever substeps DID commit) while
            # substeps remain — the same "unearned lit" shape as D-1.6 itself.
            # For writers with a real substep plan (has_substeps=true), require
            # the writer's OWN plan_substeps(ctx) to confirm nothing remains
            # before promoting. has_substeps=false/NULL (light writers, no real
            # plan) skip this check entirely — behaves exactly as before.
            cur.execute(
                "SELECT has_substeps FROM asset_registry WHERE asset_id = %s",
                (asset_id,),
            )
            hs_row = cur.fetchone()
            has_substeps = bool((hs_row or {}).get("has_substeps")) if isinstance(hs_row, dict) else False

            plan_complete = True
            remaining_count = 0
            if has_substeps:
                cur.execute("SAVEPOINT noop_completeness_probe")
                try:
                    remaining = writer.plan_substeps(ctx)
                    remaining_count = len(remaining)
                    plan_complete = remaining_count == 0
                    cur.execute("RELEASE SAVEPOINT noop_completeness_probe")
                except Exception as exc:
                    cur.execute("ROLLBACK TO SAVEPOINT noop_completeness_probe")
                    logger.warning(
                        "[orchestrator] substep-completeness re-probe failed for %s "
                        "(chart %s): %s — conservatively treating plan as incomplete",
                        asset_id, chart_id, exc,
                    )
                    plan_complete = False

            if plan_complete:
                logger.warning(
                    "[orchestrator] NO-OP COMPLETION: asset %s (chart %s, run %s) reported "
                    "0 rows this run but %d data rows are present (resumable-writer skip or "
                    "equivalent), and its substep plan confirms nothing remains. Marking "
                    "'lit', not 'dormant' — downstream deps stay unblocked.",
                    asset_id, chart_id, run_id, present,
                )
                # cur= persists this to orchestrator_event_register, in THIS
                # transaction — so the register row commits iff the 'lit' promotion
                # below commits (SAMĀPTI §9.6 / SD-EVENTREG-1; see events.py).
                emit_event({
                    "type": "asset.noop_completion",
                    "chart_id": chart_id,
                    "asset_id": asset_id,
                    "run_id": run_id,
                    "rows_present": present,
                }, cur=cur)
                final_state = 'lit'
                rows_written = present
            else:
                logger.warning(
                    "[orchestrator] NO-OP COMPLETION REJECTED: asset %s (chart %s, run %s) "
                    "reported 0 rows this run; %d data rows are present but the writer's own "
                    "substep plan reports %d substep(s) still remaining. Marking 'incomplete', "
                    "NOT 'lit' — downstream deps stay blocked until the plan actually finishes.",
                    asset_id, chart_id, run_id, present, remaining_count,
                )
                # cur= persists this to orchestrator_event_register, in THIS
                # transaction — so the register row commits iff the 'incomplete' hold
                # below commits (SAMĀPTI §9.6 / SD-EVENTREG-1; see events.py).
                emit_event({
                    "type": "asset.noop_completion_rejected",
                    "chart_id": chart_id,
                    "asset_id": asset_id,
                    "run_id": run_id,
                    "rows_present": present,
                    "substeps_remaining": remaining_count,
                }, cur=cur)
                final_state = 'incomplete'
                rows_written = present

    if target_floor and rows_written < target_floor:
        logger.warning(
            "asset %s: rows_written=%d below target_floor=%d; marking %s",
            asset_id, rows_written, target_floor, final_state
        )

    cur.execute(
        """UPDATE asset_throughput
           SET state = %s, last_built_at = NOW(), rows_written = %s,
               built_against_upstream_hash = %s, built_against_writer_hash = %s,
               last_error = NULL
           WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s""",
        (final_state, rows_written, upstream_hash, writer_hash, chart_id, asset_id),
    )
    _guard_state_write(cur, run_id, chart_id, asset_id, final_state)
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
                # SAFETY NET (D-1.6): before blocking, check each unmet dep for the
                # "state says not-lit but the data is demonstrably present" anomaly.
                # In the D-1.6 incident this block fired 24 times on ka_sangam(dormant)
                # while kala_convergence held all 2,488 correct rows — and nothing in
                # the error said so, which is what made recovery slow. The block still
                # happens (state is the contract), but the diagnostics now name the
                # exact asset, run, expected-vs-actual state, and observed row count.
                anomalies: list[str] = []
                for item in unmet:
                    dep_id = item.split("(", 1)[0]
                    dep_state = item[len(dep_id) + 1:-1] if "(" in item else "?"
                    present = _data_rows_present(conn, cur, dep_id, chart_id)
                    if present is not None and present > 0:
                        anomaly = (
                            f"{dep_id}: expected state 'lit', actual '{dep_state}', "
                            f"but {present} data rows ARE present (run={run_id})"
                        )
                        anomalies.append(anomaly)
                        logger.error(
                            "[orchestrator] DEP-ASSERT ANOMALY for %s → dep %s — "
                            "state/data mismatch: %s. Likely a no-op completion "
                            "misclassified (see asset.noop_completion) or a lost "
                            "state write; verify the dep's data, correct "
                            "asset_throughput.state, and resume.",
                            asset_id, dep_id, anomaly,
                        )
                        emit_event({
                            "type": "asset.dep_assert_anomaly",
                            "chart_id": chart_id,
                            "asset_id": asset_id,
                            "dep_id": dep_id,
                            "run_id": run_id,
                            "expected_state": "lit",
                            "actual_state": dep_state,
                            "rows_present": present,
                        })
                msg = (
                    "DEP-ASSERT: declared dependency(ies) not lit before run: %s — "
                    "refused to build on incomplete/missing upstream data" % detail
                )
                if anomalies:
                    msg += " | ANOMALY (data present despite state): " + "; ".join(anomalies)
                logger.error("[orchestrator] %s %s", asset_id, msg)
                mark_asset_error(conn, cur, run_id, chart_id, asset_id, msg)
                conn.commit()
                emit_event({"type": "asset.state_change", "chart_id": chart_id,
                            "asset_id": asset_id, "from_state": "queued",
                            "to_state": "error", "error": msg[:500]})
                return

    # Ensure asset_throughput row exists for this (chart_id, asset_id).
    # Global assets (chart_id IS NULL) use a separate partial unique index (migration 184).
    #
    # WATCHDOG HEARTBEAT FIX (R6 0h): last_built_at MUST be stamped NOW() on this initial
    # 'building' transition, not left untouched. Every OTHER state-writing site in this
    # module (mark_asset_error, _run_service_health_probe, _mark_probe_green,
    # _drive_substeps' per-sub-step heartbeat, _run_data_writer's completion UPDATE) already
    # refreshes last_built_at; this was the one gap. Without it, a single-substep
    # (non-heartbeating) writer's 'building' row keeps whatever last_built_at value survived
    # from that asset's PREVIOUS build attempt — which can be arbitrarily stale. The Cloud
    # Scheduler watchdog (platform/src/app/api/cockpit/watchdog/route.ts, clause 2) reaps any
    # 'building' row whose last_built_at is >15 min old, so a stale timestamp lets it fire
    # almost immediately instead of after 15 real minutes of THIS build. Stamping NOW() here
    # anchors the 15-minute grace window to the actual start of this run, matching the
    # watchdog comment's documented intent (single-substep writers complete well under 15
    # min "kept alive" implicitly by never going stale in the first place). This does not
    # touch WriterBase/run(ctx)/plan_substeps/run_substep or ctx.db_conn semantics — it is the
    # orchestrator's own pre-existing asset_throughput UPDATE, unchanged in shape, one column
    # added to its SET clause.
    if chart_id is not None:
        cur.execute(
            """INSERT INTO asset_throughput (asset_id, chart_id, state, last_built_at)
               VALUES (%s, %s, 'building', NOW())
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'building', last_error = NULL, last_built_at = NOW()""",
            (asset_id, chart_id),
        )
    else:
        cur.execute(
            """INSERT INTO asset_throughput (asset_id, chart_id, state, last_built_at)
               VALUES (%s, NULL, 'building', NOW())
               ON CONFLICT (asset_id) WHERE chart_id IS NULL
               DO UPDATE SET state = 'building', last_error = NULL, last_built_at = NOW()""",
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
