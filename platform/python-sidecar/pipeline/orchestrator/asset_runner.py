"""
pipeline.orchestrator.asset_runner
====================================

Per-asset execution: state transitions, savepoint isolation, error recovery,
downstream stale marking.
"""
from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path

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


def deps_unsatisfied(
    cur,
    chart_id,
    asset_id: str,
    declared_deps: list[str] | None = None,
) -> list[str]:
    """Return the list of this asset's declared deps that are NOT satisfied for the
    target scope, as 'dep(state)' strings. Empty list = all deps ready.

    A data dep is satisfied iff its asset_throughput.state == 'lit' at the correct
    scope (global deps -> chart_id IS NULL row; per-chart deps -> this chart's row).
    A service dep (asset_kind/type='service') has no data rows and is never 'lit';
    it is satisfied unless explicitly in 'error'.
    """
    if declared_deps is None:
        cur.execute(
            "SELECT COALESCE(depends_on, '{}') AS deps FROM asset_registry WHERE asset_id = %s",
            (asset_id,),
        )
        row = cur.fetchone()
        # Legacy/unit callers may omit frozen deps. Production F0 runs always
        # supply the digest-verified manifest list from runner.py.
        deps = list(row.get("deps") or []) if isinstance(row, dict) else []
    else:
        deps = list(declared_deps)
    if not deps:
        return []
    cur.execute(
        """
        SELECT dep.asset_id, t.state, f.freshness_state
        FROM unnest(%s::text[]) AS dep(asset_id)
        LEFT JOIN LATERAL (
            SELECT state FROM asset_throughput at
            WHERE at.asset_id = dep.asset_id
              AND (at.chart_id IS NOT DISTINCT FROM %s OR at.chart_id IS NULL)
            ORDER BY (at.chart_id IS NOT DISTINCT FROM %s) DESC, at.last_built_at DESC NULLS LAST
            LIMIT 1
        ) t ON true
        LEFT JOIN LATERAL (
            SELECT freshness_state FROM asset_freshness af
            WHERE af.asset_id = dep.asset_id
              AND (af.chart_id IS NOT DISTINCT FROM %s OR af.chart_id IS NULL)
            ORDER BY (af.chart_id IS NOT DISTINCT FROM %s) DESC, af.observed_at DESC
            LIMIT 1
        ) f ON true
        """,
        (deps, chart_id, chart_id, chart_id, chart_id),
    )
    bad: list[str] = []
    for d in cur.fetchall():
        state = d["state"]
        freshness = d["freshness_state"]
        if state not in ("lit", "service_ok"):
            bad.append(f"{d['asset_id']}({state or 'absent'})")
        elif freshness != "fresh":
            bad.append(f"{d['asset_id']}(receipt:{freshness or 'absent'})")
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

_UPSTREAM_HASH_VERSION = "nirmana-upstream-v1"
_WRITER_HASH_VERSION = b"nirmana-writer-source-v1\\0"
_REPO_ROOT = Path(__file__).resolve().parents[4]
_SIDECAR_ROOT = Path(__file__).resolve().parents[2]


def _canonical_timestamp(value: object) -> str | None:
    """Return a timezone-stable timestamp representation for a provenance digest."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    return str(value)


def canonical_upstream_hash(
    asset_id: str,
    chart_id: str | None,
    upstreams: list[dict[str, object]],
) -> str:
    """Hash the exact, sorted upstream build receipts used by one asset execution."""
    payload = {
        "version": _UPSTREAM_HASH_VERSION,
        "asset_id": asset_id,
        "chart_id": chart_id,
        "upstreams": [
            {"asset_id": str(row["asset_id"]), "last_built_at": _canonical_timestamp(row.get("last_built_at"))}
            for row in sorted(upstreams, key=lambda row: str(row["asset_id"]))
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_upstream_receipts(cur, declared_deps: list[str], chart_id: str | None) -> list[dict[str, object]]:
    """Load exact, scoped successful receipts without consulting mutable DAG metadata."""
    if not declared_deps:
        return []
    cur.execute(
        """
        SELECT dep.asset_id, p.receipt_version, p.code_digest, p.config_digest,
               p.upstream_digest, p.partition_digest, p.output_digest,
               p.receipt_state, p.observed_at
        FROM unnest(%s::text[]) AS dep(asset_id)
        LEFT JOIN LATERAL (
            SELECT receipt_version, code_digest, config_digest, upstream_digest,
                   partition_digest, output_digest, receipt_state, observed_at
              FROM asset_provenance_receipts apr
             WHERE apr.asset_id = dep.asset_id
               AND (apr.chart_id IS NOT DISTINCT FROM %s OR apr.chart_id IS NULL)
             ORDER BY (apr.chart_id IS NOT DISTINCT FROM %s) DESC, apr.observed_at DESC
             LIMIT 1
        ) p ON true
        ORDER BY dep.asset_id
        """,
        (declared_deps, chart_id, chart_id),
    )
    return [dict(row) for row in cur.fetchall()]


def compute_upstream_hash(
    cur,
    asset_id: str,
    chart_id: str | None,
    declared_deps: list[str] | None = None,
) -> str | None:
    """Return a reproducible digest of this execution's actual scoped upstream receipts."""
    if declared_deps is not None:
        from .provenance import canonical_digest
        receipts = load_upstream_receipts(cur, declared_deps, chart_id)
        if len(receipts) != len(declared_deps) or any(
            row.get("receipt_state") != "proven" or not row.get("output_digest")
            for row in receipts
        ):
            return None
        return canonical_digest({
            "version": "nirmana-upstream-receipts-v2",
            "asset_id": asset_id,
            "chart_id": chart_id,
            "receipts": receipts,
        })
    cur.execute(
        """
        SELECT ar.asset_id, t.last_built_at
        FROM asset_registry ar
        LEFT JOIN LATERAL (
            SELECT at.last_built_at
            FROM asset_throughput at
            WHERE at.asset_id = ar.asset_id
              AND (CASE WHEN ar.scope = 'global' THEN at.chart_id IS NULL
                        ELSE at.chart_id = %s END)
            ORDER BY at.last_built_at DESC NULLS LAST
            LIMIT 1
        ) t ON true
        WHERE ar.asset_id = ANY(
            SELECT unnest(depends_on) FROM asset_registry WHERE asset_id = %s
        )
        ORDER BY ar.asset_id
        """,
        (chart_id, asset_id),
    )
    return canonical_upstream_hash(asset_id, chart_id, cur.fetchall())


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

    `_writer_source_files` extends these roots through local Python imports, so
    delegated implementation files are part of the provenance receipt too.
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


def _local_module_path(module: str) -> Path | None:
    """Resolve an in-repo sidecar module without importing or executing it."""
    if not module:
        return None
    relative = Path(*module.split("."))
    module_file = _SIDECAR_ROOT / relative.with_suffix(".py")
    package_init = _SIDECAR_ROOT / relative / "__init__.py"
    if module_file.is_file():
        return module_file
    if package_init.is_file():
        return package_init
    return None


def _module_name_for_path(path: Path) -> str | None:
    try:
        relative = path.resolve().relative_to(_SIDECAR_ROOT)
    except ValueError:
        return None
    if relative.suffix != ".py":
        return None
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) or None


def _local_import_files(path: Path) -> list[Path]:
    """Statically resolve direct local Python imports from one implementation file."""
    module_name = _module_name_for_path(path)
    if module_name is None:
        return []
    package = module_name if path.name == "__init__.py" else module_name.rpartition(".")[0]
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                package_parts = package.split(".") if package else []
                base_parts = package_parts[:len(package_parts) - node.level + 1]
                if not base_parts:
                    continue
                base = ".".join(base_parts)
                target = f"{base}.{node.module}" if node.module else base
            else:
                target = node.module or ""
            if target:
                imports.add(target)
                imports.update(f"{target}.{alias.name}" for alias in node.names)

    return [resolved for module in sorted(imports) if (resolved := _local_module_path(module)) is not None]


def _writer_source_files(paths: list[str]) -> list[tuple[str, bytes]]:
    """Load declared source plus its local implementation closure deterministically."""
    files: list[Path] = []
    for raw_path in paths:
        source_path = Path(raw_path)
        resolved = source_path if source_path.is_absolute() else _REPO_ROOT / source_path
        if resolved.is_file():
            files.append(resolved)
        elif resolved.is_dir():
            files.extend(path for path in resolved.rglob("*.py") if path.is_file() and "tests" not in path.parts)
        else:
            raise RuntimeError(f"writer source path is unavailable: {raw_path}")

    seen: set[Path] = set()
    pending = sorted(files, key=lambda item: item.as_posix())
    resolved_files: list[Path] = []
    while pending:
        path = pending.pop(0)
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        resolved_files.append(resolved)
        pending.extend(_local_import_files(resolved))

    out: list[tuple[str, bytes]] = []
    for resolved in sorted(resolved_files, key=lambda item: item.as_posix()):
        try:
            rel = resolved.relative_to(_REPO_ROOT).as_posix()
        except ValueError:
            rel = resolved.as_posix()
        out.append((rel, resolved.read_bytes()))
    if not out:
        raise RuntimeError("writer has no declared source files")
    return out


def get_writer_source_hash(asset_id: str) -> str:
    """Return a content hash of the concrete writer source used by an execution."""
    digest = hashlib.sha256(_WRITER_HASH_VERSION)
    for path, content in _writer_source_files(_writer_source_paths(asset_id)):
        encoded_path = path.encode("utf-8")
        digest.update(len(encoded_path).to_bytes(8, "big"))
        digest.update(encoded_path)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def get_probe_source_hash() -> str:
    """Hash the generic probe implementation used when no asset writer exists."""
    from pipeline.orchestrator import service_probes
    digest = hashlib.sha256(b"nirmana-probe-source-v1\0")
    for path in sorted((Path(__file__).resolve(), Path(service_probes.__file__).resolve())):
        content = path.read_bytes()
        digest.update(path.name.encode("utf-8"))
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _persist_probe_receipt(
    cur,
    *,
    run_id: str,
    chart_id: str | None,
    asset_id: str,
    declared_deps: list[str] | None,
    natural_key_partition: str | None,
    has_cowriters: bool | None,
    probe_config: dict[str, object],
    result_message: str,
) -> None:
    """Persist a GREEN probe as evidence in the caller's success transaction."""
    from .provenance import canonical_digest, capture_and_persist_receipt
    deps = declared_deps or []
    upstream_receipts = load_upstream_receipts(cur, deps, chart_id)
    upstream_digest = compute_upstream_hash(cur, asset_id, chart_id, declared_deps)
    try:
        code_digest = get_writer_source_hash(asset_id)
    except Exception:
        code_digest = get_probe_source_hash()
    capture_and_persist_receipt(
        cur,
        asset_id=asset_id,
        chart_id=chart_id,
        build_id=run_id,
        code_digest=code_digest,
        config=probe_config,
        upstream_digest=upstream_digest,
        upstream_receipts=upstream_receipts,
        output_digest=canonical_digest({
            "version": "nirmana-probe-output-v1",
            "asset_id": asset_id,
            "chart_id": chart_id,
            "run_id": run_id,
            "status": "GREEN",
            "message": result_message,
        }),
        partition_declaration=natural_key_partition,
        has_cowriters=has_cowriters,
    )


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
    declared_deps: list[str] | None = None,
    natural_key_partition: str | None = None,
    has_cowriters: bool | None = None,
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
        try:
            _persist_probe_receipt(
                cur,
                run_id=run_id,
                chart_id=chart_id,
                asset_id=asset_id,
                declared_deps=declared_deps,
                natural_key_partition=natural_key_partition,
                has_cowriters=has_cowriters,
                probe_config={"health_probe": health_probe},
                result_message=message,
            )
        except Exception as exc:
            conn.rollback()
            mark_asset_error(conn, cur, run_id, chart_id, asset_id, f"provenance receipt: {exc}")
            return
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
    defer_commits: bool = False,
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
      commit, and emit an `asset.substep` event (granular SSE). When
      `defer_commits` is true, every sub-step remains in the caller's transaction
      so post-write integrity and provenance can gate the complete output.
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
        if not defer_commits:
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


def _mark_probe_green(
    conn,
    cur,
    run_id: str,
    chart_id: str | None,
    asset_id: str,
    message: str,
    registry_row: dict,
    declared_deps: list[str] | None = None,
    natural_key_partition: str | None = None,
    has_cowriters: bool | None = None,
) -> None:
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
    try:
        _persist_probe_receipt(
            cur,
            run_id=run_id,
            chart_id=chart_id,
            asset_id=asset_id,
            declared_deps=declared_deps,
            natural_key_partition=natural_key_partition,
            has_cowriters=has_cowriters,
            probe_config={
                "health_probe": registry_row.get("health_probe"),
                "integrity_check_sql": registry_row.get("integrity_check_sql"),
                "rebuild_on_probe_fail": bool(registry_row.get("rebuild_on_probe_fail")),
            },
            result_message=message,
        )
    except Exception as exc:
        conn.rollback()
        mark_asset_error(conn, cur, run_id, chart_id, asset_id, f"provenance receipt: {exc}")
        return
    conn.commit()
    emit_event({"type": "asset.probe", "chart_id": chart_id, "asset_id": asset_id,
                "status": "green", "action": "skipped", "message": message[:500]})
    emit_event({"type": "asset.state_change", "chart_id": chart_id, "asset_id": asset_id,
                "from_state": "building", "to_state": "lit"})


def _skip_no_delta(conn, cur, run_id: str, chart_id: str | None, asset_id: str) -> bool:
    """O-wave WP-2 (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.2, "delta-skip"):
    the pre-execution gate found every input digest unchanged since the last
    complete receipt. Record the skip WITHOUT invoking the writer.

    asset_throughput returns to 'lit': run_asset's own unconditional
    'building' flip (before any writer-selection logic runs) is the only
    thing that moved it off 'lit' this run -- a receipt only exists after a
    prior success, so 'lit' is the correct restored state, not a guess.
    build_run_assets records disposition='skip_no_delta' (plan §3.2's own
    acceptance wording) and output_changed=False, so staleness.py's
    delta-directional propagation (O-wave WP-1) also reads "no delta" and
    does not walk downstream for nothing.
    """
    cur.execute(
        """UPDATE asset_throughput
           SET state = 'lit', last_built_at = NOW(), last_error = NULL
           WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s""",
        (chart_id, asset_id),
    )
    _guard_state_write(cur, run_id, chart_id, asset_id, 'lit')
    cur.execute(
        """UPDATE build_run_assets
           SET state = 'complete', disposition = 'skip_no_delta',
               output_changed = FALSE, ended_at = NOW()
           WHERE run_id = %s AND asset_id = %s""",
        (run_id, asset_id),
    )
    conn.commit()
    emit_event({
        "type": "asset.skip_no_delta", "chart_id": chart_id, "asset_id": asset_id, "run_id": run_id,
    }, cur=cur)
    logger.info(
        "[orchestrator] asset %s skip_no_delta (O-wave WP-2 delta-skip gate) — zero writer invocation",
        asset_id,
    )
    return True


def _run_data_writer(
    conn,
    cur,
    run_id: str,
    chart_id: str | None,
    asset_id: str,
    declared_deps: list[str] | None = None,
    natural_key_partition: str | None = None,
    has_cowriters: bool | None = None,
    force: bool = False,
) -> bool:
    """
    Run a data asset's registered writer to completion (sub-step driven). Marks
    'lit' + downstream stale on success (returns True); marks 'error' and returns
    False on failure. Reused by both the normal data path and the regenerate path.

    force=True (O-wave WP-2, plan §3.2) bypasses the pre-execution delta-skip
    gate below unconditionally -- e.g. a campaign route that needs one
    accepted execution regardless of whether inputs already match the last
    complete receipt.
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
    # Capture provenance before a writer can mutate its own output. An unavailable
    # source or receipt is a failed execution, never a successful run with an
    # "unknown" provenance marker that would mask later invalidation.
    try:
        upstream_receipts = load_upstream_receipts(cur, declared_deps or [], chart_id)
        upstream_hash = (
            compute_upstream_hash(cur, asset_id, chart_id)
            if declared_deps is None
            else compute_upstream_hash(cur, asset_id, chart_id, declared_deps)
        )
        writer_hash = get_writer_source_hash(asset_id)
    except Exception as exc:
        mark_asset_error(conn, cur, run_id, chart_id, asset_id, f"provenance: {exc}")
        return False

    # O-wave WP-2 (plan §3.2, "delta-skip"): pre-execution gate. Only for the
    # same real-data-writer path WP-1's receipt capture already covers
    # (declared_deps is not None; has_cowriters is not None -- both always
    # supplied by the sole production caller, _schedule_parallel -- legacy
    # unit-fixture direct calls that omit either skip this exactly like they
    # already skip receipt capture). Never gates a probe/service asset.
    if declared_deps is not None and has_cowriters is not None and not force:
        try:
            from .provenance import previous_receipt_matches_inputs
            if previous_receipt_matches_inputs(
                cur, asset_id=asset_id, chart_id=chart_id, code_digest=writer_hash,
                config=ctx.config, upstream_digest=upstream_hash,
                partition_declaration=natural_key_partition, has_cowriters=has_cowriters,
            ):
                return _skip_no_delta(conn, cur, run_id, chart_id, asset_id)
        except Exception as exc:
            # A failed delta-skip DECISION must never become a failed BUILD.
            # Fail open into the normal execute path -- a wasted execution is
            # recoverable; skipping on an error we couldn't fully evaluate is
            # not (plan §3.2 point 4).
            logger.warning(
                "[orchestrator] delta-skip gate check failed for %s (executing "
                "normally): %s", asset_id, exc,
            )

    cur.execute(
        "SELECT integrity_check_sql FROM asset_registry WHERE asset_id = %s",
        (asset_id,),
    )
    integrity_row = cur.fetchone() or {}
    has_integrity_check = bool(integrity_row.get("integrity_check_sql"))
    # Light writers are one transaction and can be rolled back atomically when
    # their detector fails. Heavy writers intentionally keep their established
    # per-substep commits: those commits make heartbeats visible to the watchdog
    # and preserve resumable work. Their detector still gates final success and
    # provenance, while an error state prevents partial output being accepted.
    defer_writer_commits = has_integrity_check and not writer.has_substeps
    try:
        rows_inserted, rows_updated = _drive_substeps(
            conn, cur, run_id, chart_id, asset_id, writer, ctx,
            defer_commits=defer_writer_commits,
        )
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[:2000]}"
        logger.warning("[orchestrator] writer %s failed: %s", asset_id, err[:200])
        # Never let mark_asset_error's own commit capture an open writer
        # transaction. For heavy writers, earlier substep commits remain the
        # documented resumable output; only the failing substep is rolled back.
        conn.rollback()
        mark_asset_error(conn, cur, run_id, chart_id, asset_id, err)
        return False

    # A writer completing is not proof that its output is correct. When the
    # registry declares integrity SQL, run it before final success/provenance.
    # Light-writer output remains in this transaction and rolls back atomically;
    # heavy-writer substeps remain durable/resumable but cannot be accepted while
    # the detector is red. This applies even when rebuild_on_probe_fail=false:
    # that flag controls the preflight skip/regenerate policy, not whether a
    # freshly written result must satisfy its detector.
    if has_integrity_check:
        ok, message = _probe_asset(conn, cur, asset_id, integrity_row, False)
        if not ok:
            conn.rollback()
            mark_asset_error(
                conn, cur, run_id, chart_id, asset_id,
                f"post-write integrity check failed: {message}",
            )
            return False

    rows_written = int((rows_inserted + rows_updated) or 0)

    # When a chart-scoped data writer produces 0 rows, record 'dormant' rather than
    # 'lit'. 'lit' would cause the plan resolver's action='build' filter to exclude
    # the asset (filter picks only dormant/error/missing), leaving the Build button
    # stuck with an empty plan. 'dormant' correctly signals "ran but produced nothing
    # — safe to retry". Global assets (chart_id is None) are service singletons and
    # always get 'lit' regardless of rows_written.
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
        """UPDATE build_run_assets
           SET state = 'complete', disposition = 'build', ended_at = NOW()
           WHERE run_id = %s AND asset_id = %s""",
        (run_id, asset_id),
    )
    # declared_deps is supplied by the orchestrator's sole production caller
    # (_schedule_parallel, via run_asset) for every asset in every real run;
    # None only occurs from direct helper calls in legacy unit fixtures.
    if declared_deps is not None:
        try:
            from .output_digest import compute_output_digest
            from .provenance import (
                WHOLE_ASSET_PARTITION,
                capture_and_persist_receipt,
                previous_output_digest,
            )
            output_digest, output_digest_spec_sha256 = compute_output_digest(cur, asset_id=asset_id)
            # O-wave WP-1 (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.1): read the
            # prior receipt's output_digest BEFORE capture_and_persist_receipt
            # overwrites it below -- this is the only point where "did this
            # write's output actually change" can still be answered.
            partition_key = natural_key_partition or WHOLE_ASSET_PARTITION
            prior_output_digest = previous_output_digest(
                cur, asset_id=asset_id, chart_id=chart_id, partition_key=partition_key,
            )
            capture_and_persist_receipt(
                cur,
                asset_id=asset_id,
                chart_id=chart_id,
                build_id=run_id,
                code_digest=writer_hash,
                config=ctx.config,
                upstream_digest=upstream_hash,
                upstream_receipts=upstream_receipts,
                output_digest=output_digest,
                output_digest_spec_sha256=output_digest_spec_sha256,
                partition_declaration=natural_key_partition,
                has_cowriters=has_cowriters,
            )
            # Record the delta decision durably so staleness.py's propagation
            # (a fresh connection in the orchestrator's on_complete callback,
            # with no access to this transaction's local state) can read it
            # back. No prior receipt at all counts as changed -- fail-open,
            # never fake-fresh (plan §3.1 point 4 / CLAUDE.md §N.8).
            output_changed = prior_output_digest is None or prior_output_digest != output_digest
            cur.execute(
                "UPDATE build_run_assets SET output_changed = %s WHERE run_id = %s AND asset_id = %s",
                (output_changed, run_id, asset_id),
            )
        except Exception as exc:
            conn.rollback()
            mark_asset_error(conn, cur, run_id, chart_id, asset_id, f"provenance receipt: {exc}")
            return False
    conn.commit()

    emit_event({"type": "asset.state_change", "chart_id": chart_id, "asset_id": asset_id,
                "from_state": "building", "to_state": final_state})
    emit_event({"type": "asset.progress", "chart_id": chart_id, "asset_id": asset_id,
                "rows_written": rows_written})

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
    declared_deps: list[str] | None = None,
    natural_key_partition: str | None = None,
    has_cowriters: bool | None = None,
    force: bool = False,
) -> None:
    """
    Execute one asset writer inside a savepoint.

    force=True (O-wave WP-2, plan §3.2) bypasses _run_data_writer's
    pre-execution delta-skip gate unconditionally.

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
        unmet = (
            deps_unsatisfied(cur, chart_id, asset_id)
            if declared_deps is None
            else deps_unsatisfied(cur, chart_id, asset_id, declared_deps)
        )
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
            _mark_probe_green(
                conn, cur, run_id, chart_id, asset_id, msg, registry_row, declared_deps,
                natural_key_partition, has_cowriters,
            )
            return
        emit_event({"type": "asset.probe", "chart_id": chart_id, "asset_id": asset_id,
                    "status": "failed", "action": "regenerating", "message": msg[:500]})
        if get_writer(asset_id) is None:
            mark_asset_error(conn, cur, run_id, chart_id, asset_id,
                             f"probe failed ({msg}); no writer to regenerate")
            return
        if not _run_data_writer(
            conn, cur, run_id, chart_id, asset_id, declared_deps,
            natural_key_partition, has_cowriters,
            # The probe just failed -- independent evidence that regeneration
            # is needed regardless of what the input digests say. Always
            # bypass the delta-skip gate here; skipping now would silently
            # re-accept the very state the probe just rejected.
            force=True,
        ):
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
            _run_data_writer(
                conn, cur, run_id, chart_id, asset_id, declared_deps,
                natural_key_partition, has_cowriters, force,
            )
            return
        # Legacy health-probe path (bg_* assets with health_probe JSONB spec).
        _run_service_health_probe(
            conn, cur, run_id, chart_id, asset_id,
            registry_row.get("health_probe"), declared_deps,
            natural_key_partition, has_cowriters,
        )
        return

    # Data asset: run its registered writer to completion (sub-step driven).
    _run_data_writer(
        conn, cur, run_id, chart_id, asset_id, declared_deps,
        natural_key_partition, has_cowriters, force,
    )
