"""
pipeline.orchestrator.runner
============================

Core execution loop: load a build_run, acquire lock, walk per-asset plan.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import signal
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait as _futures_wait
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

import psycopg

from .db import connect
from .events import emit_event
from .locks import (
    acquire_chart_lock,
    acquire_global_assets_lock,
    release_chart_lock,
    release_global_assets_lock,
)

logger = logging.getLogger(__name__)


class _DaemonThreadPoolExecutor(ThreadPoolExecutor):
    """ThreadPoolExecutor variant whose worker threads are daemon threads.

    Non-daemon TPE threads prevent process exit when a timed-out future is still
    running. Daemon threads are killed automatically when the main thread exits,
    which is the correct behaviour for a timed-out/hung asset writer.
    """

    def _adjust_thread_count(self) -> None:  # type: ignore[override]
        import threading, weakref
        from concurrent.futures.thread import _threads_queues, _worker
        if self._idle_semaphore.acquire(timeout=0):  # type: ignore[attr-defined]
            return
        def weakref_cb(_, q=self._work_queue):  # type: ignore[attr-defined]
            q.put(None)
        num_threads = len(self._threads)  # type: ignore[attr-defined]
        if num_threads < self._max_workers:  # type: ignore[attr-defined]
            thread_name = '%s_%d' % (self._thread_name_prefix or self, num_threads)  # type: ignore[attr-defined]
            executor_ref = weakref.ref(self, weakref_cb)
            if sys.version_info >= (3, 14):
                # CPython 3.14 replaced (work_queue, initializer, initargs) with
                # a worker context object. Keep the daemon behaviour while
                # matching the stdlib executor's exact calling convention.
                worker_args = (
                    executor_ref,
                    self._create_worker_context(),  # type: ignore[attr-defined]
                    self._work_queue,  # type: ignore[attr-defined]
                )
            else:
                worker_args = (
                    executor_ref,
                    self._work_queue,  # type: ignore[attr-defined]
                    self._initializer,  # type: ignore[attr-defined]
                    self._initargs,  # type: ignore[attr-defined]
                )
            t = threading.Thread(
                name=thread_name, target=_worker, args=worker_args,
                daemon=True,  # KEY: daemon so hung writers don't block process exit
            )
            t.start()
            self._threads.add(t)  # type: ignore[attr-defined]
            _threads_queues[t] = self._work_queue  # type: ignore[attr-defined]


import sys as _sys
import warnings as _warnings
if _sys.version_info >= (3, 15):
    _warnings.warn(
        "_DaemonThreadPoolExecutor uses CPython private internals and has only "
        "been audited through Python 3.14; re-audit before production use.",
        stacklevel=1,
    )


# ── Connection budget (Cloud SQL max_connections=50; ~33 available to orchestrator) ──
# A single run holds 1 MAIN connection (advisory lock + run-state) plus up to
# WORKER_LIMIT worker connections (one per concurrently-executing asset). Worst case
# per run = 1 + WORKER_LIMIT. The product MUST stay under the available budget:
#     _MAX_CONCURRENT_RUNS × (1 + _WORKER_LIMIT) ≤ ~33
# Defaults: 6 × (1 + 4) = 30. Override either via env for different deployments.
_MAX_CONCURRENT_RUNS = int(os.environ.get("ORCHESTRATOR_MAX_CONCURRENT_RUNS", "6"))

# Wave-parallel scheduler width: how many independent DAG assets run at once within
# ONE run. 1 = serial (dependency-ordered) — a safe fallback. The DAG's peak width
# is ~8 (L1); 4 captures most of the achievable speedup since the long pole is one
# asset (ga_dashas/ka_sangam). Each worker uses its own DB connection.
_WORKER_LIMIT = max(1, int(os.environ.get("ORCHESTRATOR_WORKER_LIMIT", "4")))

_POLL_INTERVAL: float = 5.0  # seconds between signal checks

# ── Per-writer timeout (H-3) ──────────────────────────────────────────────────
# A hung writer (e.g. blocked on a DB lock) will block a worker thread
# indefinitely without this guard. Timed-out assets are marked 'error' so the
# DAG can continue and the operator can see the failure. The daemon thread
# itself cannot be cancelled — it will die when the process exits — but the
# orchestrator no longer waits on it.
_WRITER_TIMEOUT_SECONDS = int(os.environ.get("WRITER_TIMEOUT_SECONDS", "600"))  # 10 min default

# ── Graceful SIGTERM drain (M-7) ──────────────────────────────────────────────
# Cloud Run sends SIGTERM and then waits up to 10 seconds before SIGKILL. Rather
# than calling sys.exit(0) immediately (which kills daemon threads without any
# cleanup), set a flag and let the polling loop drain in-flight sub-steps.
_shutdown = False


def _handle_sigterm(signum, frame):
    global _shutdown
    logger.warning("[orchestrator] SIGTERM received — draining in-flight writers")
    _shutdown = True


# ── Asset-outcome vocabulary (SAMĀPTI B-N8-SWEEPFIX, F-01) ────────────────────
# The EXHAUSTIVE allowlist of per-asset states that mean "this asset's work in this
# run finished successfully". Everything not listed is a failure.
#
# Why an allowlist. `build_run_assets.state` is written by `asset_runner.py` as the
# unconditional literal 'complete' for every terminal outcome — including the
# 'incomplete' state SATYA-DĪPA introduced (migration 474) to mean "this build did
# NOT finish". The run-level verdict therefore could not see 'incomplete' at all:
# the scheduler's success rule was a DENYLIST (`if result == 'error': failed`), so
# every non-'error' string — 'incomplete' included — scored as success and the run
# reported `build_runs.state = 'completed'`. That is the exact "green over-report"
# the guard comment at the bottom of execute_run says must not happen.
#
# The three-part fix in THIS file (the `build_run_assets` write itself lives in
# `asset_runner.py`, outside this lane's scope — see the module note below):
#   1. worker() cross-checks `asset_throughput` — the state the writer path
#      actually computed — and returns THAT when it is not a success state;
#   2. execute_dag uses this allowlist instead of the `!= 'error'` denylist
#      (which is also what execute_dag's own docstring has always claimed);
#   3. _reconcile_failed_assets_from_db will not promote an asset out of the
#      failed set on `build_run_assets.state = 'complete'` alone.
#
# A state added to `asset_throughput` in future is a FAILURE here until someone
# deliberately adds it — the safe default direction for a build-success signal.
_SUCCESS_OUTCOMES: frozenset[str] = frozenset({
    "complete",    # build_run_assets: terminal success for this run
    "lit",         # asset_throughput: writer produced a complete slice
    "mature",      # asset_throughput: lit and past its maturity gate
    "dormant",     # asset_throughput: DECLARED outcome — ran, legitimately 0 rows
    "service_ok",  # asset_throughput: service asset's health probe returned GREEN
})


# ── Writer-gap guard ──────────────────────────────────────────────────────────
# Mode: enforce (default) — fail the run; warn — log only; off — skip.
# A "writer gap" is an asset_id registered via @register() in the Python codebase
# that has has_writer=false in asset_registry. The plan resolver query
# (WHERE has_writer=true) silently excludes it from every build plan, so it can
# never be built. Gaps are a data-loss risk — L5 was entirely absent this way.
_WRITER_GAP_MODE = os.environ.get("ORCHESTRATOR_WRITER_GAP_CHECK", "enforce").lower()

# Sub-registrations that share a writer with their parent and intentionally have
# no independent asset_registry row (they are not standalone plan-level assets).
_WRITER_SUBASSET_IDS: frozenset[str] = frozenset({
    "bg_nakshatra_medical",  # sub-table inside bg_medical_mappings writer
    "bg_transit_engine",     # sub-table inside bg_transit_rules writer
})


def _check_writer_registry_gaps(cur) -> list[str]:
    """
    Return asset_ids registered via @register() in Python but with has_writer=false
    (or missing entirely) from asset_registry.

    These assets are invisible to the plan resolver (WHERE has_writer=true) and can
    never appear in any build plan. Caller decides whether to warn or abort the run.
    """
    from .writers import WRITER_REGISTRY
    candidate_ids = sorted(set(WRITER_REGISTRY.keys()) - _WRITER_SUBASSET_IDS)
    if not candidate_ids:
        return []

    # Single query: get all asset_registry rows that exist for our candidates.
    cur.execute(
        "SELECT asset_id, has_writer FROM asset_registry WHERE asset_id = ANY(%s)",
        (candidate_ids,),
    )
    db_rows = {r["asset_id"]: r["has_writer"] for r in cur.fetchall()}

    gaps: list[str] = []
    for aid in candidate_ids:
        if aid not in db_rows:
            gaps.append(aid)          # registered in Python, no DB row at all
        elif not db_rows[aid]:
            gaps.append(aid)          # DB row exists but has_writer=false
    return gaps


# ── Run-level helpers ─────────────────────────────────────────────────────────

def load_run(cur, run_id: str) -> Optional[dict]:
    cur.execute(
        """SELECT id, chart_id, scope, scope_target, action, plan, state,
                  plan_manifest, plan_manifest_digest
           FROM build_runs WHERE id = %s""",
        (run_id,),
    )
    return cur.fetchone()


@dataclass(frozen=True)
class FrozenRunManifest:
    """The exact DAG accepted by the dispatch API for one build_run."""

    plan: list[str]
    asset_scopes: dict[str, str]
    asset_deps: dict[str, list[str]]
    asset_partitions: dict[str, str | None]
    asset_has_cowriters: dict[str, bool]
    expected_code_digests: dict[str, str]


def _canonical_manifest_digest(manifest: object) -> str:
    """Match route.ts: recursively key-sort objects and preserve array order."""
    encoded = json.dumps(manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_frozen_run_manifest(run: dict[str, Any]) -> FrozenRunManifest:
    """
    Verify the dispatch-time manifest before any writer can run.

    `asset_registry` is mutable configuration. Its current values must not be
    allowed to re-order, add dependencies to, or change the scope of an accepted
    run; all scheduling inputs are therefore restored from this digest-protected
    manifest instead of reloaded from the registry.
    """
    manifest = run.get("plan_manifest")
    digest = run.get("plan_manifest_digest")
    if not isinstance(manifest, dict) or not isinstance(digest, str):
        raise ValueError("missing frozen run manifest or digest")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("invalid frozen run manifest digest")
    actual_digest = _canonical_manifest_digest(manifest)
    if actual_digest != digest:
        raise ValueError("frozen run manifest digest mismatch")

    required = ("version", "chart_id", "scope", "scope_target", "action", "waves", "assets")
    if any(key not in manifest for key in required):
        raise ValueError("frozen run manifest is incomplete")
    if manifest["version"] != "nirmana-run-manifest/v1":
        raise ValueError("unsupported frozen run manifest version")
    # psycopg decodes UUID columns to ``uuid.UUID`` while JSONB retains the
    # dispatch-time string.  Parse both representations before comparison so a
    # valid non-canonical spelling cannot falsely terminalize an accepted run.
    manifest_chart_id = manifest["chart_id"]
    run_chart_id = run.get("chart_id")
    try:
        manifest_chart_uuid = UUID(manifest_chart_id) if isinstance(manifest_chart_id, str) else None
        run_chart_uuid = run_chart_id if isinstance(run_chart_id, UUID) else UUID(str(run_chart_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("frozen run manifest chart_id does not match build_run") from None
    if manifest_chart_uuid is None or manifest_chart_uuid != run_chart_uuid:
        raise ValueError("frozen run manifest chart_id does not match build_run")
    for field in ("scope", "scope_target", "action"):
        if manifest[field] != run.get(field):
            raise ValueError(f"frozen run manifest {field} does not match build_run")

    plan = run.get("plan")
    waves = manifest["waves"]
    assets = manifest["assets"]
    if not isinstance(plan, list) or not all(isinstance(asset_id, str) for asset_id in plan):
        raise ValueError("build_run plan is invalid")
    if not isinstance(waves, list) or not all(isinstance(wave, list) for wave in waves):
        raise ValueError("frozen run manifest waves are invalid")
    flattened = [asset_id for wave in waves for asset_id in wave]
    if flattened != plan or len(set(plan)) != len(plan):
        raise ValueError("frozen run manifest waves do not exactly match build_run plan")
    if not isinstance(assets, list) or len(assets) != len(plan):
        raise ValueError("frozen run manifest assets do not exactly match build_run plan")

    asset_scopes: dict[str, str] = {}
    asset_deps: dict[str, list[str]] = {}
    asset_partitions: dict[str, str | None] = {}
    asset_has_cowriters: dict[str, bool] = {}
    expected_code_digests: dict[str, str] = {}
    for expected_id, asset in zip(plan, assets):
        if not isinstance(asset, dict) or asset.get("asset_id") != expected_id:
            raise ValueError("frozen run manifest asset order does not match build_run plan")
        scope = asset.get("scope")
        deps = asset.get("depends_on")
        partition = asset.get("natural_key_partition")
        has_cowriters = asset.get("has_cowriters")
        expected_code_digest = asset.get("expected_code_digest")
        if (
            not isinstance(scope, str)
            or not isinstance(deps, list)
            or not all(isinstance(dep, str) for dep in deps)
            or (partition is not None and not isinstance(partition, str))
            or not isinstance(has_cowriters, bool)
            or not isinstance(expected_code_digest, str)
            or len(expected_code_digest) != 64
            or any(c not in "0123456789abcdef" for c in expected_code_digest)
        ):
            raise ValueError(f"frozen run manifest asset {expected_id} is invalid")
        if len(set(deps)) != len(deps):
            raise ValueError(f"frozen run manifest asset {expected_id} has duplicate dependencies")
        asset_scopes[expected_id] = scope
        asset_deps[expected_id] = list(deps)
        asset_partitions[expected_id] = partition
        asset_has_cowriters[expected_id] = has_cowriters
        expected_code_digests[expected_id] = expected_code_digest

    return FrozenRunManifest(
        plan=list(plan), asset_scopes=asset_scopes, asset_deps=asset_deps,
        asset_partitions=asset_partitions, asset_has_cowriters=asset_has_cowriters,
        expected_code_digests=expected_code_digests,
    )


def _terminalize_preflight_failure(cur, *, run_id: str, message: str) -> None:
    """Fail an unclaimed run and abort its queued assets in one statement."""
    cur.execute(
        """WITH failed_run AS (
               UPDATE build_runs
                  SET state='failed', ended_at=NOW(), last_error=%s
                WHERE id=%s AND state IN ('planned', 'running', 'paused')
            RETURNING id
           )
           UPDATE build_run_assets
              SET state='aborted', ended_at=NOW(), error=%s
            WHERE run_id IN (SELECT id FROM failed_run)
              AND state='queued'""",
        (message, run_id, message),
    )


def _verify_registry_still_matches_manifest(cur, frozen: FrozenRunManifest) -> dict[str, str]:
    """Detect every asset in the frozen plan whose registry row diverged after dispatch.

    Returns ``{asset_id: reason}`` for EVERY divergent asset in `frozen.plan`, not just
    the first one found (A3 Decision 4 — the query below already computes the full
    per-asset comparison row in ONE round trip; the old code discarded every mismatch
    but the first by raising immediately, which is exactly the data the caller needs
    to narrow an abort to only the genuinely-affected asset(s) instead of the whole
    run). An empty dict means the registry still matches the frozen manifest for
    every planned asset. This function never raises for a mismatch — the caller
    (execute_run) decides what a divergence means; see _terminalize_diverged_assets.
    """
    cur.execute(
        """SELECT ar.asset_id, ar.scope, COALESCE(ar.depends_on, '{}') AS depends_on,
                  ar.natural_key_partition,
                  EXISTS (
                    SELECT 1 FROM asset_registry peer
                     WHERE peer.target_table = ar.target_table
                       AND ar.target_table IS NOT NULL
                       AND peer.asset_id <> ar.asset_id
                       AND peer.is_active = true AND peer.has_writer = true
                  ) AS has_cowriters
           FROM asset_registry ar WHERE ar.asset_id = ANY(%s)""",
        (frozen.plan,),
    )
    rows = {row["asset_id"]: row for row in cur.fetchall()}
    diverged: dict[str, str] = {}
    for asset_id in frozen.plan:
        row = rows.get(asset_id)
        if row is None:
            diverged[asset_id] = f"frozen run manifest asset {asset_id} is no longer registered"
            continue
        if (
            row["scope"] != frozen.asset_scopes[asset_id]
            # Sort both sides: the frozen manifest's depends_on is stored sorted
            # (matching the server's registryContractFingerprintInput, which also
            # sorts), but asset_registry.depends_on is stored in authored order —
            # dependency order was never a real invariant, so compare unordered.
            or sorted(row["depends_on"] or []) != sorted(frozen.asset_deps[asset_id])
            or row.get("natural_key_partition") != frozen.asset_partitions[asset_id]
            or bool(row.get("has_cowriters")) != frozen.asset_has_cowriters[asset_id]
        ):
            diverged[asset_id] = f"asset_registry changed after dispatch for frozen asset {asset_id}"
    return diverged


def _verify_sidecar_code_matches_manifest(frozen: FrozenRunManifest) -> None:
    """Reject web/job image skew before any asset state or output is mutated."""
    from .asset_runner import get_probe_source_hash, get_writer_source_hash
    from .writers import get_writer

    probe_digest: str | None = None
    for asset_id in frozen.plan:
        if get_writer(asset_id) is not None:
            actual = get_writer_source_hash(asset_id)
        else:
            if probe_digest is None:
                probe_digest = get_probe_source_hash()
            actual = probe_digest
        if actual != frozen.expected_code_digests[asset_id]:
            raise ValueError(
                f"sidecar code digest does not match dispatch manifest for asset {asset_id}"
            )


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


def claim_runnable_run(conn: psycopg.Connection, cur, run_id: str) -> bool:
    """Claim planned work or reclaim a lock-proven orphaned running attempt."""
    cur.execute(
        """UPDATE build_runs
              SET state='running', started_at=COALESCE(started_at, NOW())
            WHERE id=%s AND state IN ('planned', 'running')
        RETURNING id""",
        (run_id,),
    )
    claimed = cur.fetchone() is not None
    conn.commit()
    return claimed


def count_other_running_runs(cur, run_id: str) -> int:
    """Apply the fleet cap without making a crashed run block its own retry."""
    cur.execute(
        "SELECT count(*) AS active FROM build_runs WHERE state='running' AND id<>%s",
        (run_id,),
    )
    return int(cur.fetchone()["active"])


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

def _mark_asset_error_terminal(
    conn, cur, run_id: str, chart_id, asset_id: str, message: str,
    *, disposition: Optional[str] = None, blocked_by: Optional[str] = None,
) -> None:
    """
    Shared terminal-error write: asset_throughput + build_run_assets + the
    asset.state_change event, for an asset that fails THIS run without its writer
    having run at all. Three callers share this exact shape today: a dependent
    blocked by a failed/diverged upstream (_mark_asset_blocked), an asset whose own
    writer exceeded its writer_timeout_seconds budget (_mark_asset_timeout — Packet
    B1 Decision 2: a ROOT cause, never routed through _mark_asset_blocked), and an
    asset whose own asset_registry row genuinely diverged from the frozen manifest
    between freeze and check time (_terminalize_diverged_assets, A3). Not used for a
    writer's own runtime failure — that path belongs to asset_runner, not this one.

    `disposition`/`blocked_by` (Packet B1 Decision 1) are ONLY ever passed by
    _mark_asset_blocked, for a genuine dependency/deadlock cascade. Every other
    caller omits them, so build_run_assets.disposition stays NULL for a root-cause
    failure (a writer timeout, a registry divergence, a genuine writer crash) —
    exactly the same "this run did not succeed, and nothing downstream caused it"
    signal a plain writer failure already gets today.
    """
    if chart_id is not None:
        cur.execute(
            """INSERT INTO asset_throughput (asset_id, chart_id, state, last_error, last_built_at)
               VALUES (%s, %s, 'error', %s, NOW())
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state='error', last_error=EXCLUDED.last_error, last_built_at=NOW()""",
            (asset_id, chart_id, message),
        )
    else:
        cur.execute(
            """INSERT INTO asset_throughput (asset_id, chart_id, state, last_error, last_built_at)
               VALUES (%s, NULL, 'error', %s, NOW())
               ON CONFLICT (asset_id) WHERE chart_id IS NULL
               DO UPDATE SET state='error', last_error=EXCLUDED.last_error, last_built_at=NOW()""",
            (asset_id, message),
        )
    cur.execute(
        """UPDATE build_run_assets
           SET state='error', error=%s, ended_at=NOW(), disposition=%s, blocked_by_asset_id=%s
           WHERE run_id=%s AND asset_id=%s""",
        (message[:2000], disposition, blocked_by, run_id, asset_id),
    )
    conn.commit()
    emit_event({
        "type": "asset.state_change", "chart_id": chart_id, "asset_id": asset_id,
        "from_state": "queued", "to_state": "error", "error": message[:500],
    })


def _mark_asset_blocked(conn, cur, run_id: str, chart_id, asset_id: str, blocking_deps: list[str]) -> None:
    """
    Mark an asset BLOCKED because an upstream it depends on errored/was blocked.

    Recorded as state='error' (the loud, surfaced state — red in the tracker, counted in
    the run's error tally) with a 'BLOCKED:' message, rather than silently running the
    writer on incomplete upstream data and marking it 'complete'. The asset is NOT executed.

    Packet B1 Decision 1: ALSO records disposition='blocked_dependency' (the
    already-provisioned, previously-dormant CHECK constraint value) plus the
    immediate blocking asset id(s) in the new blocked_by_asset_id column, so a
    consumer can count "one cause, N blocked" instead of N failures. This function
    is called ONLY for a genuine dependency cascade or deadlock (execute_dag's two
    on_block call sites) — NEVER for a writer's own timeout, which is a root cause
    wearing cascade-victim clothes and is handled by the separate _mark_asset_timeout
    below (Decision 2).
    """
    joined = ", ".join(sorted(blocking_deps))
    msg = (
        "BLOCKED: upstream dependency(ies) %s did not complete in this run; "
        "skipped to avoid building on incomplete data" % joined
    )
    _mark_asset_error_terminal(
        conn, cur, run_id, chart_id, asset_id, msg,
        disposition="blocked_dependency", blocked_by=joined[:2000],
    )
    logger.warning("[orchestrator] BLOCKED %s — upstream not complete: %s", asset_id, blocking_deps)


def _mark_asset_timeout(conn, cur, run_id: str, chart_id, asset_id: str, budget_seconds: int) -> None:
    """
    Mark an asset's OWN writer as the root cause because it exceeded its
    writer_timeout_seconds budget (execute_dag's H-3/JL-023 watchdog).

    Packet B1 Decision 2: this is NOT a dependency block — `asset_id` itself is the
    failure, not a dependent of one. Before this fix, execute_dag funneled a timeout
    through _mark_asset_blocked() with a synthetic, non-asset-id dependency name
    ('timeout:600s'), which both fabricated a fake blocking dependency and
    misclassified a genuine root cause as a cascade victim — the exact defect this
    packet exists to fix, found sitting in the engine's own code
    (B1_before_20260926T173931Z.json §2). disposition is left NULL (the same
    default a plain writer crash gets — see asset_runner.py's mark_asset_error),
    and blocked_by_asset_id is left NULL: nothing blocked this asset, it blocked
    itself by running too long.
    """
    msg = (
        "TIMEOUT: writer exceeded its writer_timeout_seconds budget (%ds) — "
        "this asset is the failure, not a blocked dependent" % budget_seconds
    )
    _mark_asset_error_terminal(conn, cur, run_id, chart_id, asset_id, msg)
    logger.warning(
        "[orchestrator] TIMEOUT %s — exceeded writer_timeout_seconds=%ds", asset_id, budget_seconds,
    )


def _terminalize_diverged_assets(
    conn, cur, run_id: str, chart_id, asset_scopes: dict[str, str], diverged: dict[str, str],
) -> None:
    """
    A3 Decision 1: fail ONLY the asset(s) whose asset_registry row genuinely
    diverged from the frozen manifest between freeze and check time — never the
    whole run, and never by silently re-freezing onto the live (possibly only
    transiently mutated) registry row. Each diverged asset gets the SAME
    'frozen manifest validation failed: …' error-string prefix the old whole-run
    abort used, so any existing monitoring keyed on that prefix keeps matching —
    now attributed to the one asset that actually diverged, instead of stamped
    onto every queued row in the run regardless of whether it was affected.

    Transitive dependents of a diverged asset are NOT marked here: the caller
    seeds this asset's id into execute_dag's `failed` set (via _schedule_parallel's
    seed_failed), and the ordinary on_block/_mark_asset_blocked cascade already
    used for an upstream writer failure blocks them exactly the same way — one
    cause, N blocked, not a second bespoke blocking mechanism.

    F-3 (rereview 20260926T152022Z) — DELIBERATE state-class divergence from the
    watchdog's own convention: this goes through the shared
    _mark_asset_error_terminal helper, which writes state='error' via
    _mark_asset_blocked's "loud, surfaced state" convention — NOT state='aborted',
    which is what platform/src/app/api/cockpit/watchdog/route.ts:138 uses for a
    "queued row that never got a chance" (and which AssetNode.tsx:53 renders as
    "cancelled"). A registry-diverged asset never got a chance to run either, by
    that same description — but it is reported as a genuine FAILURE (it was
    checked and found incompatible), not a cancellation, which is the stronger
    and more accurate signal for an operator to act on. Consequence: any
    monitoring that filters strictly on state='aborted' will NOT see this family
    of failure. The 'frozen manifest validation failed: …' error-TEXT prefix
    (above) is preserved specifically so text-based monitoring keeps matching
    regardless of this state-class choice.
    """
    for asset_id, reason in diverged.items():
        eff_chart_id = None if asset_scopes.get(asset_id) == "global" else chart_id
        message = f"frozen manifest validation failed: {reason}"
        _mark_asset_error_terminal(conn, cur, run_id, eff_chart_id, asset_id, message)
        logger.error("[orchestrator] REGISTRY DIVERGED %s: %s", asset_id, reason)


def execute_dag(
    plan: list[str],
    deps_of: dict[str, list[str]],
    run_fn,
    worker_limit: int,
    seed_completed: Optional[set] = None,
    seed_failed: Optional[set] = None,
    on_block=None,
    on_timeout=None,          # Packet B1 Decision 2: called(asset, budget_seconds) for a
                               # writer's OWN timeout — a root cause, distinct from on_block
    should_stop=None,
    on_complete=None,         # called(asset_id) when asset lands in completed; errors are swallowed
    timeouts_of=None,         # optional {asset_id: seconds}; per-writer watchdog budget (JL-023)
) -> tuple[set[str], Optional[str]]:
    """
    Pure (DB-free) wave-parallel DAG executor — the scheduling core, separated so it
    is unit-testable without a database or the writer machinery.

      run_fn(asset) -> 'lit' | <anything else = failure>   (called on a worker thread)
      should_stop() -> None | 'stop' | 'pause'              (checked each round)
      on_block(asset, blocking_deps)                        (side effect on a genuine
                                                               dependency cascade/deadlock)
      on_timeout(asset, budget_seconds)                      (side effect when `asset` ITSELF
                                                               exceeds its writer_timeout_seconds
                                                               — Packet B1 Decision 2: never
                                                               routed through on_block, which
                                                               would fabricate a fake dependency
                                                               named 'timeout:Ns' and misreport
                                                               a root cause as a cascade victim)

    Invariant: an asset is dispatched ONLY when every dep is in `completed` and none
    is in `failed`; a failed dep blocks it (transitively). Two assets run at once only
    if neither depends on the other. Returns (failed_set, terminal|None).

    `seed_failed` (A3): assets already known to have failed BEFORE any writer ran —
    e.g. a registry-divergence preflight failure (_terminalize_diverged_assets) — are
    seeded straight into `failed` and excluded from `pending`, so they are never
    dispatched (their terminal row was already written by the caller) while their
    transitive dependents are still blocked by the ordinary on_block cascade below,
    exactly as if a writer had failed them.
    """
    completed: set = set(seed_completed or set())
    failed: set = set(seed_failed or set())
    pending: list[str] = [a for a in plan if a not in failed]
    in_flight: dict = {}          # future → asset_id
    deadlines: dict = {}          # future → wall-clock deadline (seconds since epoch)
    terminal: Optional[str] = None
    _block = on_block or (lambda a, b: None)
    _timeout_cb = on_timeout or (lambda a, budget: None)
    _stop = should_stop or (lambda: None)
    _on_complete = on_complete or (lambda a: None)
    # JL-023: per-writer watchdog budget from asset_registry.writer_timeout_seconds;
    # fall back to the global env default when an asset has no explicit budget.
    _budgets = timeouts_of or {}
    _timeout_for = lambda a: int(_budgets.get(a) or _WRITER_TIMEOUT_SECONDS)
    wl = max(1, worker_limit)

    pool = _DaemonThreadPoolExecutor(max_workers=wl, thread_name_prefix="asset")
    try:
        while pending or in_flight:
            # H-3 / M-7: check both DB stop/pause signals and the SIGTERM drain flag
            sig = _stop()
            if sig in ("stop", "pause") or _shutdown:
                terminal = "stopped" if (sig == "stop" or _shutdown) else "paused"
                break

            progressed = False
            for a in list(pending):
                blocking = [d for d in deps_of.get(a, []) if d in failed]
                if blocking:
                    _block(a, blocking)
                    failed.add(a)
                    pending.remove(a)
                    progressed = True
                    continue
                if all(d in completed for d in deps_of.get(a, [])) and len(in_flight) < wl:
                    _fut = pool.submit(run_fn, a)
                    in_flight[_fut] = a
                    # H-3: record the per-asset deadline when we dispatch
                    # JL-023: per-writer budget (falls back to global default)
                    deadlines[_fut] = time.monotonic() + _timeout_for(a)
                    pending.remove(a)
                    progressed = True

            if not in_flight:
                if pending and not progressed:
                    # Deadlock: remaining deps are neither completed nor failed and can
                    # never become ready (missing upstream). Block loudly, don't hang.
                    for a in list(pending):
                        miss = [d for d in deps_of.get(a, []) if d not in completed]
                        _block(a, miss)
                        failed.add(a)
                        pending.remove(a)
                    break
                continue

            done, _ = _futures_wait(list(in_flight), return_when=FIRST_COMPLETED, timeout=_POLL_INTERVAL)

            # H-3: check for timed-out in-flight futures BEFORE processing done set
            now = time.monotonic()
            for fut in list(in_flight):
                if fut not in done and deadlines.get(fut, float("inf")) < now:
                    a = in_flight.pop(fut)
                    deadlines.pop(fut, None)
                    _budget = _timeout_for(a)
                    logger.warning(
                        "[execute_dag] TIMEOUT: asset_id=%s exceeded writer_timeout_seconds=%d — "
                        "marking error; daemon thread will die on process exit",
                        a, _budget,
                    )
                    # Packet B1 Decision 2: a timeout is `a`'s OWN root-cause failure, not a
                    # dependency block on `a` — must never go through _block()/on_block, which
                    # would fabricate a fake dependency named 'timeout:Ns' and misclassify this
                    # root cause as a cascade victim. `a` still joins `failed`, so its OWN
                    # dependents are correctly cascade-blocked via the ordinary on_block path
                    # on a later round — only `a` itself is reported as the cause.
                    _timeout_cb(a, _budget)
                    failed.add(a)

            for fut in done:
                if fut not in in_flight:
                    # Already evicted by the timeout check above
                    deadlines.pop(fut, None)
                    continue
                a = in_flight.pop(fut)
                deadlines.pop(fut, None)
                # F-01: ALLOWLIST, not a denylist. Success is one of the enumerated
                # terminal success states; anything else — 'incomplete', 'error',
                # 'building', a state added later, an unexpected string — is failure.
                _outcome = fut.result()
                if _outcome not in _SUCCESS_OUTCOMES:
                    if _outcome != "error":
                        logger.error(
                            "[execute_dag] asset %s returned non-success outcome %r — "
                            "counting as FAILED (not a recognised success state)", a, _outcome,
                        )
                    failed.add(a)
                else:
                    completed.add(a)
                    try:
                        _on_complete(a)
                    except Exception as _oce:
                        logger.warning("[execute_dag] on_complete(%s) raised: %s", a, _oce)

        # On stop/pause/SIGTERM drain, let dispatched workers finish their current
        # savepoint commit (Cloud Run gives 10 s after SIGTERM before SIGKILL).
        for fut in list(in_flight):
            a = in_flight.pop(fut)
            deadlines.pop(fut, None)
            try:
                # F-01: same allowlist as the main loop above.
                if fut.result() not in _SUCCESS_OUTCOMES:
                    failed.add(a)
                else:
                    completed.add(a)
                    try:
                        _on_complete(a)
                    except Exception as _oce:
                        logger.warning("[execute_dag] on_complete(%s) raised: %s", a, _oce)
            except Exception:
                failed.add(a)

    finally:
        # Shut down the pool without waiting for timed-out futures still running
        # (they can't be interrupted, but we must not block the scheduler on them).
        pool.shutdown(wait=False, cancel_futures=True)
    return failed, terminal


def _schedule_parallel(
    conn,
    cur,
    run_id: str,
    chart_id,
    plan: list[str],
    action: str,
    asset_scopes: dict[str, str],
    asset_deps: dict[str, list[str]],
    asset_partitions: dict[str, str | None],
    asset_has_cowriters: dict[str, bool],
    force: bool = False,
    seed_failed: Optional[set[str]] = None,
) -> tuple[set[str], Optional[str]]:
    """
    Wave-parallel DAG executor. Replaces the serial plan walk while preserving the
    SAME completeness/consistency guarantee: an asset runs ONLY when every dependency
    it declares is committed-complete ('lit'); if any dependency failed/blocked, the
    asset is blocked (transitively) and never runs.

    Returns (failed_assets, terminal) where terminal is None | 'stopped' | 'paused'.

    Correctness model (provably equivalent to the serial gate, parallelism only
    changes WHICH independent ready assets run at the same time):
      * completed — assets confirmed 'lit' (this run, plus out-of-plan deps already
        lit from a prior build, seeded up front).
      * failed    — assets that errored or were blocked; their downstream never
        becomes ready (transitive blocking).
      * ready(a)  ⇔ every dep of a is in `completed` and none is in `failed`.
      * Two assets run concurrently ONLY if neither (transitively) depends on the
        other — guaranteed because dispatch requires all deps already in `completed`.

    Each in-flight asset runs on its OWN connection (psycopg connections are not
    shared across threads; run_asset commits per sub-step). The MAIN connection is
    used only by this scheduler thread (signals, blocked-marking) and holds the
    chart advisory lock for the whole run.
    """
    from .asset_runner import run_asset  # break circular import

    plan_set = set(plan)
    pos_of = {a: i for i, a in enumerate(plan)}
    deps_of = {a: list(asset_deps.get(a, [])) for a in plan}

    def eff(a: str):
        # Global assets are chart-independent singletons (chart_id IS NULL row).
        return None if asset_scopes.get(a) == "global" else chart_id

    completed: set[str] = set()
    pending: list[str] = list(plan)

    # Seed `completed` with out-of-plan dependencies already satisfied in the DB
    # (e.g. an earlier build already produced them). This makes ready(a) a single
    # "all deps in completed" test regardless of whether a dep is in this plan.
    out_deps = {d for a in plan for d in deps_of[a] if d not in plan_set}
    for d in out_deps:
        cur.execute(
            "SELECT 1 FROM asset_throughput WHERE asset_id = %s "
            "AND (chart_id = %s OR chart_id IS NULL) AND state IN ('lit','service_ok') LIMIT 1",
            (d, chart_id),
        )
        if cur.fetchone():
            completed.add(d)
    conn.commit()  # release the read snapshot so later check_signals sees fresh data

    # Skip-if-complete (non-rebuild): plan assets already lit need no work.
    if action != "rebuild":
        for a in list(pending):
            if is_asset_complete(cur, eff(a), a):
                completed.add(a)
                pending.remove(a)
                logger.info("[orchestrator] skip %s (already lit)", a)
        conn.commit()

    # Preload full active registry for downstream staleness propagation.
    # asset_deps only covers plan assets; propagation needs all assets.
    cur.execute(
        "SELECT asset_id, COALESCE(depends_on, '{}') AS depends_on "
        "FROM asset_registry WHERE is_active = true"
    )
    full_registry = [
        {'asset_id': row['asset_id'], 'depends_on': list(row['depends_on'])}
        for row in cur.fetchall()
    ]
    conn.commit()  # release snapshot so subsequent reads are fresh

    # JL-023: per-writer watchdog budgets from asset_registry. Guarded so a schema
    # predating migration 417 (or a unit fixture without the column) degrades to the
    # global WRITER_TIMEOUT_SECONDS default rather than crashing the run.
    timeouts_of: dict[str, int] = {}
    try:
        cur.execute(
            "SELECT asset_id, writer_timeout_seconds FROM asset_registry "
            "WHERE writer_timeout_seconds IS NOT NULL"
        )
        timeouts_of = {r["asset_id"]: int(r["writer_timeout_seconds"]) for r in cur.fetchall()}
        conn.commit()
    except Exception as _te:
        conn.rollback()
        logger.warning("[orchestrator] writer_timeout_seconds unavailable (%s); "
                       "using global WRITER_TIMEOUT_SECONDS=%d", _te, _WRITER_TIMEOUT_SECONDS)

    def worker(asset_id: str) -> str:
        """Run one asset on a DEDICATED connection. Returns its final state string."""
        wconn = connect()
        wconn.autocommit = False
        try:
            wcur = wconn.cursor()
            run_asset(
                wconn, wcur, run_id, eff(asset_id), asset_id, pos_of[asset_id],
                declared_deps=deps_of[asset_id],
                natural_key_partition=asset_partitions[asset_id],
                has_cowriters=asset_has_cowriters[asset_id],
                force=force,
            )
            wcur.execute(
                "SELECT state FROM build_run_assets WHERE run_id = %s AND asset_id = %s",
                (run_id, asset_id),
            )
            r = wcur.fetchone()
            run_state = r["state"] if r else "error"

            # F-01: `build_run_assets.state` is written as the unconditional literal
            # 'complete' for every terminal outcome, so on its own it cannot report a
            # failed build. `asset_throughput.state` is what the writer path actually
            # COMPUTED (including 'incomplete' — the no-op-completion rejection state).
            # Where the two disagree, the computed one wins: a signal with a detector
            # behind it beats a literal (CLAUDE.md §N.8).
            wcur.execute(
                "SELECT state FROM asset_throughput "
                "WHERE asset_id = %s AND chart_id IS NOT DISTINCT FROM %s",
                (asset_id, eff(asset_id)),
            )
            tr = wcur.fetchone()
            throughput_state = tr["state"] if tr else None
            if throughput_state is not None and throughput_state not in _SUCCESS_OUTCOMES:
                if run_state in _SUCCESS_OUTCOMES:
                    logger.error(
                        "[orchestrator] STATE DIVERGENCE: asset %s (chart %s, run %s) — "
                        "build_run_assets.state=%r but asset_throughput.state=%r. "
                        "Reporting the computed state; this asset FAILS the run.",
                        asset_id, eff(asset_id), run_id, run_state, throughput_state,
                    )
                return throughput_state
            return run_state
        except Exception as exc:
            logger.error("[orchestrator] worker crashed for %s: %s", asset_id, exc, exc_info=True)
            # When the connection is dead (e.g. server-side timeout killed it while the
            # writer was doing CPU-heavy work), mark_asset_error() inside the writer path
            # can't run — the asset stays 'building' in asset_throughput forever. Recover
            # by opening a FRESH connection to write the error state.
            _crash_msg = f"worker_crash: {type(exc).__name__}: {exc}"[:2000]
            try:
                from .asset_runner import mark_asset_error as _mark_err
                _use_orig = not getattr(wconn, "closed", False)
                _cconn = wconn if _use_orig else connect()
                _cconn.autocommit = False
                _ccur = _cconn.cursor()
                _mark_err(_cconn, _ccur, run_id, eff(asset_id), asset_id, _crash_msg)
                if not _use_orig:
                    _cconn.close()
            except Exception as _ce:
                logger.error(
                    "[orchestrator] crash-cleanup also failed for %s: %s", asset_id, _ce
                )
            return "error"
        finally:
            try:
                wconn.close()
            except Exception:
                pass

    def should_stop():
        # Refresh the main connection's snapshot so a stop/pause committed by the API
        # server is visible (the serial runner got this for free via per-asset commits).
        conn.rollback()
        return check_signals(cur, run_id)

    def on_block(a, blocking):
        _mark_asset_blocked(conn, cur, run_id, eff(a), a, blocking)

    def on_timeout(a, budget_seconds):
        # Packet B1 Decision 2: `a`'s own writer timeout is a root cause, not a
        # dependency block — routed to the dedicated terminal writer, never on_block.
        _mark_asset_timeout(conn, cur, run_id, eff(a), a, budget_seconds)

    from .staleness import propagate_downstream_staleness

    def on_complete(asset_id: str) -> None:
        # Fresh connection: must not use main conn (it holds the advisory lock).
        # Pass the run's chart_id — not eff(asset_id). eff() returns None for global
        # assets, but WHERE chart_id = NULL is always false in SQL. The staleness
        # UPDATE targets chart-specific rows in asset_throughput using the run's real
        # chart_id; the global asset's own throughput row (chart_id IS NULL) is never
        # a downstream target of itself, so the NULL-chart path is never needed here.
        _sconn = None
        try:
            _sconn = connect()
            _sconn.autocommit = False
            _scur = _sconn.cursor()
            propagate_downstream_staleness(
                conn=_sconn,
                cur=_scur,
                chart_id=chart_id,   # run's chart_id, not eff(asset_id)
                completed_asset_id=asset_id,
                plan_set=plan_set,
                registry=full_registry,
                emit_fn=emit_event,
                run_id=run_id,
            )
        except Exception as _pse:
            logger.error("[staleness] on_complete(%s) failed: %s", asset_id, _pse)
        finally:
            if _sconn is not None:
                try:
                    _sconn.close()
                except Exception:
                    pass

    return execute_dag(
        plan=pending,
        deps_of=deps_of,
        run_fn=worker,
        worker_limit=_WORKER_LIMIT,
        seed_completed=completed,
        seed_failed=seed_failed,
        on_block=on_block,
        on_timeout=on_timeout,
        should_stop=should_stop,
        on_complete=on_complete,
        timeouts_of=timeouts_of,
    )


def _throughput_states(cur, chart_id, plan: list[str]) -> dict[str, str]:
    """{asset_id: asset_throughput.state} for the plan, chart-scoped rows preferred.

    Global assets carry a `chart_id IS NULL` row; per-chart assets carry one keyed to
    the run's chart. Both are admitted and the chart-scoped row wins where both exist
    (the same convention `is_asset_complete` uses).
    """
    if not plan:
        return {}
    cur.execute(
        "SELECT asset_id, state, chart_id FROM asset_throughput "
        "WHERE asset_id = ANY(%s) AND (chart_id = %s OR chart_id IS NULL) "
        "ORDER BY (chart_id IS NULL)",
        (list(plan), chart_id),
    )
    out: dict[str, str] = {}
    for r in cur.fetchall():
        out.setdefault(r["asset_id"], r["state"])
    return out


def _reconcile_failed_assets_from_db(cur, run_id: str, plan: list[str], failed_assets: set[str],
                                     chart_id=None) -> set[str]:
    """RR-fix (D-3 carried-forward from D-2 close report): the run-rollup race.

    `_schedule_parallel` tracks `failed_assets` IN-PROCESS (an in-memory Python set
    built up as worker futures resolve). That set is a cache, not the source of
    truth — a worker can write 'error' (or, via a retried/late commit, 'complete')
    to `build_run_assets`/`asset_throughput` in a way the in-process bookkeeping
    misses or mis-tracks (e.g. a future read racing a worker's own crash-cleanup
    write in `worker()`'s except-block, or a `build_run_assets` row that never
    reached a terminal state at all). Before computing `final_state`, re-query
    `build_run_assets` for this run_id and let DB reality override the cache in
    BOTH directions:
      - DB shows 'error'/'aborted', or never reached a terminal state at all
        ('queued'/'building' still, or the row is simply missing) → treat as
        failed even if the in-process set missed it.
      - DB shows 'complete' for an asset the in-process set believed failed →
        trust the DB and drop it from the failed set (a false failure would
        report a run 'failed' when every child asset actually landed clean).

    F-01 (SAMĀPTI B-N8-SWEEPFIX): `build_run_assets.state` is written as the
    unconditional literal 'complete' for every terminal outcome, so it CANNOT by
    itself distinguish a finished build from one the writer path classified
    'incomplete'. This function therefore cross-checks `asset_throughput.state` —
    the state actually computed — and:
      - treats a non-success computed state as failed even when build_run_assets
        says 'complete';
      - refuses to drop an asset from the failed set on 'complete' alone; the
        computed state must ALSO be a success state.
    Without the second rule the fix in worker()/execute_dag would be undone right
    here: the incomplete asset would be put back into the clean column at rollup.
    """
    cur.execute(
        "SELECT asset_id, state FROM build_run_assets WHERE run_id = %s",
        (run_id,),
    )
    db_state = {r["asset_id"]: r["state"] for r in cur.fetchall()}
    throughput = _throughput_states(cur, chart_id, plan)

    reconciled = set(failed_assets)
    for asset_id in plan:
        state = db_state.get(asset_id)
        computed = throughput.get(asset_id)
        # F-01: the computed state is authoritative over the literal, in the
        # failing direction, regardless of what build_run_assets claims.
        if computed is not None and computed not in _SUCCESS_OUTCOMES:
            if asset_id not in reconciled:
                logger.error(
                    "[orchestrator] F-01: run %s asset %s — build_run_assets.state=%r "
                    "but asset_throughput.state=%r (not a success state). The run is "
                    "NOT clean; reconciling to failed.",
                    run_id, asset_id, state, computed,
                )
            reconciled.add(asset_id)
            continue
        if state in ("error", "aborted"):
            if asset_id not in reconciled:
                logger.error(
                    "[orchestrator] RR-fix: run %s asset %s missed by in-process "
                    "tracking but build_run_assets shows %r — reconciling to failed",
                    run_id, asset_id, state,
                )
            reconciled.add(asset_id)
        elif state in ("building", "queued", None):
            logger.error(
                "[orchestrator] RR-fix: run %s asset %s in non-terminal DB state "
                "%r at final rollup — treating as failed (never confirmed complete)",
                run_id, asset_id, state,
            )
            reconciled.add(asset_id)
        elif state == "complete" and asset_id in reconciled:
            # F-01: 'complete' is a literal, not a measurement. Only release the
            # asset when the COMPUTED state corroborates it. When no
            # asset_throughput row exists at all there is nothing corroborating a
            # successful build, so the in-process failure stands.
            if computed is not None and computed in _SUCCESS_OUTCOMES:
                logger.warning(
                    "[orchestrator] RR-fix: run %s asset %s was in the in-process "
                    "failed set but build_run_assets shows 'complete' and "
                    "asset_throughput shows %r — trusting DB, removing from failed set",
                    run_id, asset_id, computed,
                )
                reconciled.discard(asset_id)
            else:
                logger.error(
                    "[orchestrator] F-01: run %s asset %s shows build_run_assets="
                    "'complete' but asset_throughput=%r — the literal is NOT "
                    "corroborated by a computed success state; keeping it failed.",
                    run_id, asset_id, computed,
                )

    if reconciled != failed_assets:
        emit_event({
            "type": "run.rollup_reconciled",
            "run_id": run_id,
            "in_process_failed": sorted(failed_assets),
            "db_reconciled_failed": sorted(reconciled),
        })
    return reconciled


def execute_run(run_id: str) -> None:
    """
    Load build_run by run_id, acquire chart advisory lock, run the asset plan via
    the wave-parallel scheduler (dependency-gated; width = ORCHESTRATOR_WORKER_LIMIT).

    Exit codes:
      0  — completed or stopped/paused cleanly
      2  — run not found
      3  — chart locked by another run (defer)
    """
    from .writers import discover_all    # D1: ensure all writer modules are imported
    discover_all()

    # O-wave WP-2 (plan §3.2, "delta-skip"): NIRMANA_FORCE_EXECUTE bypasses the
    # pre-execution delta-skip gate for every asset in THIS run. Read per-run
    # (a Cloud Run Job invocation handles exactly one --run-id and exits), not
    # cached at module import, so it stays testable and matches the plan's own
    # "per dispatch" framing. The campaign dispatcher sets this env var on the
    # job execution override when its route demands one accepted execution
    # regardless of whether inputs already match the last complete receipt.
    force = os.environ.get("NIRMANA_FORCE_EXECUTE", "").strip().lower() in ("1", "true", "yes")

    # M-7: SIGTERM sets _shutdown flag for graceful drain instead of sys.exit(0).
    # Cloud Run gives 10 s after SIGTERM before SIGKILL; daemon workers finish
    # their current savepoint commit before the process exits.
    signal.signal(signal.SIGTERM, _handle_sigterm)

    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()

    run = load_run(cur, run_id)
    if run is None:
        logger.error("[orchestrator] build_run %s not found", run_id)
        conn.close()
        sys.exit(2)

    chart_id: str = run["chart_id"]
    action: str = run["action"]
    try:
        frozen = validate_frozen_run_manifest(run)
        _verify_sidecar_code_matches_manifest(frozen)
    except ValueError as exc:
        # A legacy, tampered, or registry-mutated run is unsafe to execute. Mark
        # it terminal rather than falling back to mutable planning inputs.
        message = f"frozen manifest validation failed: {exc}"
        logger.error("[orchestrator] run %s %s", run_id, message)
        _terminalize_preflight_failure(cur, run_id=run_id, message=message[:2000])
        conn.commit()
        conn.close()
        sys.exit(1)

    plan = frozen.plan
    _asset_scopes = frozen.asset_scopes
    _asset_deps = frozen.asset_deps

    # ── Writer-gap pre-flight ─────────────────────────────────────────────────
    # Check for @register()'d writers that lack has_writer=true in asset_registry.
    # They are silently excluded from every build plan by the plan resolver query
    # (WHERE has_writer=true). Discovering this mid-run would leave L2+/L5 empty.
    #
    # A3/C-1: this MUST run before registry-divergence detection below, not after.
    # In "enforce" mode (the default) a gap is a HARD FAIL — sys.exit(1), no
    # retry, nothing about this run_id ever runs again. A hard-fail exit sitting
    # AFTER a divergence was detected but BEFORE it was written would let a real
    # divergence be found and then discarded with nothing recorded anywhere — the
    # exact silent-failure shape this campaign exists to eliminate (confirmed by
    # probe: with a gap present and mode="enforce", the old ordering raised
    # SystemExit(1) with zero build_run_assets/asset_throughput writes). Running
    # this check first means nothing has been detected yet when it can hard-fail,
    # so nothing can be lost. The concurrency-cap/chart-lock/global-assets-lock
    # checks further below are different in kind — they are genuine DEFERS (no
    # build_runs mutation; the row stays 'planned' and a later retry of this same
    # run_id re-detects everything fresh) — so leaving those between detection
    # and claim is correct, not a hole.
    if _WRITER_GAP_MODE != "off":
        _gaps = _check_writer_registry_gaps(cur)
        if _gaps:
            msg = (
                "[orchestrator] WRITER GAP: %d writer(s) registered in Python but "
                "missing has_writer=true in asset_registry — they will NEVER appear "
                "in any build plan. Apply the missing migration. Affected: %s"
            )
            if _WRITER_GAP_MODE == "enforce":
                logger.error(msg, len(_gaps), _gaps)
                emit_event({
                    "type": "run.writer_gap",
                    "run_id": run_id,
                    "gaps": _gaps,
                    "mode": "enforce",
                })
                mark_run_state(conn, cur, run_id, "failed")
                conn.commit()
                conn.close()
                sys.exit(1)
            else:
                logger.warning(msg, len(_gaps), _gaps)

    # A3: registry divergence no longer raises — it returns the full set of
    # genuinely-affected assets (possibly empty) so only THOSE assets (plus their
    # transitive dependents) fail, instead of the manifest-structural/code-digest
    # checks above, which remain fail-closed/whole-run (out of this packet's
    # scope — see Family B in the before-measurement).
    diverged = _verify_registry_still_matches_manifest(cur, frozen) or {}
    if diverged:
        logger.error(
            "[orchestrator] run %s asset_registry diverged for %d/%d planned asset(s): %s",
            run_id, len(diverged), len(plan), sorted(diverged.keys()),
        )

    # A3 Decision 1 / C-1 / C-4 / F-1 (rereview 20260926T152022Z): a genuine
    # registry divergence fails only the affected asset(s), never the whole
    # run — but the per-asset terminal write is deferred until AFTER
    # claim_runnable_run succeeds below (not done here), because writing it
    # earlier — before the run is guaranteed to actually execute in this
    # invocation — would leave that asset stuck 'error' across a retry even if
    # the divergence had meanwhile resolved.
    #
    # Between here and the claim, THREE things can happen — the prior version
    # of this comment enumerated only the first two, and the rereview
    # falsified that enumeration by measurement (F-1):
    #   1. DEFER — the concurrency-cap / chart-lock / global-assets-lock
    #      checks below, all sys.exit(3). No build_runs mutation; the row
    #      stays 'planned' for a later retry of this same run_id that
    #      re-detects everything fresh. SystemExit does not subclass
    #      Exception, so the try/except below never intercepts these —
    #      a defer must NOT write, since the run retries and would
    #      re-detect the same divergence.
    #   2. SOFT LOSS OF THE CLAIM — claim_runnable_run returns False (a plain
    #      `return`, not an exception) because some OTHER concurrent actor
    #      already moved build_runs.state out of ('planned','running'), e.g.
    #      an external stop/cancel. HEAD's own _terminalize_preflight_failure
    #      UPDATE is gated on the same state list and would equally match
    #      zero rows in that interleaving — not a regression this packet
    #      introduces.
    #   3. HARD FAULT — count_other_running_runs / acquire_chart_lock /
    #      claim_runnable_run (or their own conn.commit() calls) raise a
    #      genuine exception (DB timeout, connection reset, serialization
    #      failure). Nothing in this window used to catch that: it propagated
    #      straight out of execute_run, through main.py's blanket
    #      `except Exception: sys.exit(1)` — an exit(1)-class path INSIDE
    #      this window that the prior comment's enumeration did not name.
    #      On that path a divergence detected above was logged (line ~1165)
    #      but never written to build_run_assets/asset_throughput — lost on
    #      a fault the run will simply retry into, blind to the very
    #      divergence that was already found. That is C-4's own defect class
    #      (a confident, wrong exit enumeration) recurring inside C-4's own
    #      fix. The try/except below exists ONLY to close this third case:
    #      on a genuine exception, terminalize the already-detected
    #      diverged asset(s) before re-raising, so the record survives even
    #      though this attempt still fails and the exception still reaches
    #      main.py's sys.exit(1) unchanged — only whether the divergence is
    #      RECORDED changes, not the outcome of this attempt.
    try:
        # Concurrency cap: defer if too many runs are already active.
        active_count = count_other_running_runs(cur, run_id)
        if active_count >= _MAX_CONCURRENT_RUNS:
            logger.warning(
                "[orchestrator] max concurrent runs (%d) reached (%d active) — deferring run %s",
                _MAX_CONCURRENT_RUNS, active_count, run_id,
            )
            conn.close()
            sys.exit(3)

        if not acquire_chart_lock(cur, chart_id):
            logger.warning("[orchestrator] chart %s locked by another run — deferring", chart_id)
            conn.close()
            sys.exit(3)
        # Lock acquired; commit the advisory lock transaction so it survives later commits
        conn.commit()

        holds_global_assets_lock = False
        if any(scope == "global" for scope in _asset_scopes.values()):
            if not acquire_global_assets_lock(cur):
                logger.warning("[orchestrator] global assets locked by another run — deferring %s", run_id)
                release_chart_lock(cur, chart_id)
                conn.commit()
                conn.close()
                sys.exit(3)
            holds_global_assets_lock = True
            conn.commit()

        # The dispatcher may have terminalized a failed/ambiguous job invocation
        # after this process loaded the row.  Only a planned row can be claimed;
        # losing the compare-and-swap means no asset or throughput state is touched.
        if not claim_runnable_run(conn, cur, run_id):
            logger.warning("[orchestrator] run %s is no longer runnable — refusing execution", run_id)
            if holds_global_assets_lock:
                release_global_assets_lock(cur)
            release_chart_lock(cur, chart_id)
            conn.commit()
            conn.close()
            return
    except Exception:
        # F-1: a genuine (non-SystemExit) fault anywhere in the window above.
        # If a divergence was already detected, record it now — this is the
        # ONLY place that can happen for this attempt, since main.py's blanket
        # handler below us does not know about `diverged` at all. Roll back
        # first: the connection may be left in a failed-transaction state by
        # whatever raised, and the terminal write must not be issued into that
        # (same convention as Guard B's rollback-before-further-work further
        # below). A secondary failure while terminalizing must not mask the
        # original fault — log it and still re-raise the original exception.
        if diverged:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                _terminalize_diverged_assets(conn, cur, run_id, chart_id, _asset_scopes, diverged)
            except Exception:
                logger.error(
                    "[orchestrator] run %s: failed to terminalize diverged asset(s) %s "
                    "after a hard fault in the pre-claim window — the divergence record "
                    "is lost for this attempt (logged above at detection time only)",
                    run_id, sorted(diverged.keys()), exc_info=True,
                )
        raise

    # Orphan cleanup: reset assets stuck in 'building' from a prior crashed run.
    # We hold the chart advisory lock, so no other orchestrator is running for this
    # chart. Any 'building' row in asset_throughput is from a dead run whose
    # worker connection was closed before mark_asset_error() could execute.
    cur.execute(
        """UPDATE asset_throughput
           SET state = 'error',
               last_error = 'orphaned_by_crash: prior orchestrator terminated while asset was in-flight'
           WHERE chart_id IS NOT DISTINCT FROM %s AND state = 'building'""",
        (chart_id,),
    )
    cur.execute(
        """UPDATE build_run_assets
           SET state = 'error',
               error = 'orphaned_by_crash: prior orchestrator terminated while asset was in-flight',
               ended_at = NOW()
           FROM build_runs br
           WHERE build_run_assets.run_id = br.id
             AND br.chart_id IS NOT DISTINCT FROM %s
             AND br.id != %s
             AND build_run_assets.state = 'building'""",
        (chart_id, run_id),
    )
    conn.commit()
    logger.info("[orchestrator] orphan-cleanup complete for chart %s", chart_id)

    try:
        # State is already atomically claimed above.  Keep the standard state
        # helper/event path for observers and existing instrumentation.
        mark_run_state(conn, cur, run_id, "running", started_at=True)
        emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": "running"})

        # A3 Decision 1: NOW that the run is claimed and guaranteed to run to
        # completion in this invocation (no defer path remains beyond this point),
        # write the diverged asset(s)' terminal state. seed_failed (below) blocks
        # their transitive dependents through the ordinary on_block cascade; every
        # unaffected asset in the plan still runs normally.
        if diverged:
            emit_event({
                "type": "run.registry_divergence_narrowed",
                "run_id": run_id,
                "diverged_assets": sorted(diverged.keys()),
            })
            _terminalize_diverged_assets(conn, cur, run_id, chart_id, _asset_scopes, diverged)

        # Wave-parallel execution. The scheduler enforces the SAME upstream-success
        # gate as the old serial loop (an asset runs only when all deps are 'lit'; a
        # failed/blocked dep blocks it transitively), but runs independent DAG branches
        # concurrently (width = ORCHESTRATOR_WORKER_LIMIT, default 4; 1 = serial).
        failed_assets, terminal = _schedule_parallel(
            conn, cur, run_id, chart_id, plan, action, _asset_scopes, _asset_deps,
            frozen.asset_partitions, frozen.asset_has_cowriters, force=force,
            seed_failed=set(diverged) if diverged else None,
        )

        if terminal == "stopped":
            mark_run_state(conn, cur, run_id, "stopped", ended_at=True)
            emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": "stopped"})
            return
        if terminal == "paused":
            mark_run_state(conn, cur, run_id, "paused")
            emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": "paused"})
            return

        # RR-fix (D-3): reconcile the in-process failed_assets cache against DB
        # reality (build_run_assets for this run_id) before computing the final
        # state — see _reconcile_failed_assets_from_db for the race this closes.
        conn.rollback()  # release the read snapshot so the reconciliation query sees fresh commits
        failed_assets = _reconcile_failed_assets_from_db(cur, run_id, plan, failed_assets, chart_id)
        conn.commit()

        # BA-P3 FIX 3: a run whose plan included any failed/blocked asset must NOT
        # be reported as "completed" — that reads as a clean, trustworthy build to
        # an operator when it is not (the 45/66-errored "green over-report", NF-1).
        # The run still terminates cleanly (does not hang as 'running') so the next
        # build can acquire the lock; only the terminal state differs.
        final_state = "failed" if failed_assets else "completed"
        if failed_assets:
            logger.warning(
                "[orchestrator] run %s %s with %d failed/blocked asset(s): %s",
                run_id, final_state, len(failed_assets), sorted(failed_assets),
            )
        mark_run_state(conn, cur, run_id, final_state, ended_at=True)
        emit_event({"type": "run.state_change", "run_id": run_id, "chart_id": chart_id, "state": final_state})

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
            if holds_global_assets_lock:
                release_global_assets_lock(cur)
            release_chart_lock(cur, chart_id)
            conn.commit()
        except Exception:
            pass
        conn.close()
