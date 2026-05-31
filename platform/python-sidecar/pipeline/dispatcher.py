"""
pipeline.dispatcher — Cascade-invalidation and resume dispatcher for MARSYS-JIS build pipeline.

Provides:
  - _load_dep_graph(conn)       — load forward-edge dependency graph from build_dependencies
  - compute_descendants(asset)  — transitive set of assets that depend on given asset
  - poll_stop_signal(...)        — check per-asset stop request in build_events
  - upsert_checkpoint(...)       — write/update build_checkpoints row
  - rebuild_asset(...)           — cascade-invalidate asset + descendants, re-enqueue
  - resume_build(...)            — return pending (asset, ayanamsha) pairs and emit resume event
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from pipeline.build_events import emit_node_added, emit_edge_added

logger = logging.getLogger(__name__)

# ── Per-build SSE emit dedup sets ─────────────────────────────────────────────
# Reset these at build start by calling reset_sse_emit_state().

_emitted_nodes: Set[Tuple[str, str]] = set()   # (asset_id, ayanamsha_id)
_emitted_edges: Set[Tuple[str, str]] = set()   # (from_asset, to_asset)


def reset_sse_emit_state() -> None:
    """Reset per-build SSE dedup state. Call at the start of each new build."""
    global _emitted_nodes, _emitted_edges
    _emitted_nodes = set()
    _emitted_edges = set()

# ── Dependency graph cache ─────────────────────────────────────────────────────

_dep_graph: Dict[str, List[str]] = {}   # asset_id -> list of assets that depend on it (forward edges)
_dep_loaded = False


def _load_dep_graph(conn) -> None:
    """Load forward-edge dependency graph from build_dependencies table."""
    global _dep_graph, _dep_loaded
    if _dep_loaded:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT asset_id, depends_on FROM build_dependencies")
        rows = cur.fetchall()
    except Exception:
        # Fallback: try dict-style cursor
        try:
            rows = conn.execute("SELECT asset_id, depends_on FROM build_dependencies").fetchall()
        except Exception as exc:
            logger.error("_load_dep_graph: failed to query build_dependencies: %s", exc)
            return

    # Build forward edges (dependents): for each dep -> list of assets that need it
    reverse: Dict[str, List[str]] = defaultdict(list)
    for row in rows:
        # Support both dict-style and tuple-style rows
        if isinstance(row, dict):
            asset_id = row['asset_id']
            depends_on = row['depends_on'] or []
        else:
            asset_id = row[0]
            depends_on = row[1] or []
        for dep in depends_on:
            reverse[dep].append(asset_id)
    _dep_graph = dict(reverse)
    _dep_loaded = True
    logger.debug("_load_dep_graph: loaded %d forward-edge entries", len(_dep_graph))


def reset_dep_graph() -> None:
    """Reset the cached dependency graph (useful for testing)."""
    global _dep_graph, _dep_loaded
    _dep_graph = {}
    _dep_loaded = False


def compute_descendants(asset_id: str) -> Set[str]:
    """Return transitive set of assets that depend on asset_id (forward DAG walk)."""
    visited: Set[str] = set()
    queue = [asset_id]
    while queue:
        node = queue.pop()
        if node in visited:
            continue
        visited.add(node)
        for child in _dep_graph.get(node, []):
            queue.append(child)
    visited.discard(asset_id)  # exclude self; callers add self explicitly
    return visited


# ── Stop-signal polling ────────────────────────────────────────────────────────

def poll_stop_signal(build_id: str, asset_id: str, conn) -> bool:
    """
    Check if a stop has been requested for this asset in this build.
    build_events uses 'asset' column (not 'asset_id').
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT stop_requested FROM build_events WHERE build_id=%s AND asset=%s "
            "ORDER BY emitted_at DESC LIMIT 1",
            (build_id, asset_id)
        )
        row = cur.fetchone()
    except Exception:
        try:
            row = conn.execute(
                "SELECT stop_requested FROM build_events WHERE build_id=%s AND asset=%s "
                "ORDER BY emitted_at DESC LIMIT 1",
                (build_id, asset_id)
            ).fetchone()
        except Exception as exc:
            logger.warning("poll_stop_signal: query failed: %s", exc)
            return False

    if row is None:
        return False
    val = row['stop_requested'] if isinstance(row, dict) else row[0]
    return bool(val)


# ── Checkpoint upsert ─────────────────────────────────────────────────────────

def upsert_checkpoint(
    build_id: str,
    asset_id: str,
    ayanamsha_id: str,
    status: str,
    conn,
    pct: float = 0,
    error_text: str = None,
) -> None:
    """
    Upsert a build_checkpoints row.
    Sets started_at on first 'running' transition; sets completed_at on terminal states.
    Increments retry_count on each new 'running' transition.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    terminal = status in ('success', 'failed', 'stopped', 'skipped')

    upsert_sql = """
        INSERT INTO build_checkpoints
            (build_id, asset_id, ayanamsha_id, status, pct_complete, error_text,
             started_at, completed_at, retry_count)
        VALUES (%s, %s, %s, %s, %s, %s,
            CASE WHEN %s = 'running' THEN NOW() ELSE NULL END,
            CASE WHEN %s = ANY(ARRAY['success','failed','stopped','skipped']) THEN NOW() ELSE NULL END,
            0)
        ON CONFLICT (build_id, asset_id, ayanamsha_id) DO UPDATE SET
            status       = EXCLUDED.status,
            pct_complete = EXCLUDED.pct_complete,
            error_text   = EXCLUDED.error_text,
            started_at   = COALESCE(build_checkpoints.started_at, EXCLUDED.started_at),
            completed_at = EXCLUDED.completed_at,
            retry_count  = build_checkpoints.retry_count
                           + CASE WHEN EXCLUDED.status = 'running' THEN 1 ELSE 0 END
    """
    params = (
        build_id, asset_id, ayanamsha_id, status, pct, error_text,
        status,  # for started_at CASE
        status,  # for completed_at CASE
    )
    try:
        cur = conn.cursor()
        cur.execute(upsert_sql, params)
    except Exception:
        try:
            conn.execute(upsert_sql, params)
        except Exception as exc:
            logger.error("upsert_checkpoint: failed for %s/%s/%s: %s", build_id, asset_id, ayanamsha_id, exc)
            raise


# ── Rebuild (cascade-invalidate) ──────────────────────────────────────────────

def rebuild_asset(asset_id: str, chart_id: str, build_id: str, conn) -> None:
    """
    Cascade-invalidate asset + all transitive descendants, then re-enqueue.

    Steps:
      1. Walk forward dep graph to collect all affected assets.
      2. DELETE chart_facts rows for each affected asset's category_prefix.
      3. DELETE build_checkpoints rows for the affected assets in this build.
      4. Emit a build_events row signalling rebuild_requested.
    """
    _load_dep_graph(conn)
    targets = {asset_id} | compute_descendants(asset_id)
    logger.info(
        "rebuild_asset: invalidating %d assets (root=%s, build=%s, chart=%s)",
        len(targets), asset_id, build_id, chart_id,
    )

    # Get category_prefix for each target
    targets_list = list(targets)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT asset_id, category_prefix FROM build_dependencies WHERE asset_id = ANY(%s)",
            (targets_list,)
        )
        rows = cur.fetchall()
    except Exception:
        rows = conn.execute(
            "SELECT asset_id, category_prefix FROM build_dependencies WHERE asset_id = ANY(%s)",
            (targets_list,)
        ).fetchall()

    prefix_map = {}
    for row in rows:
        if isinstance(row, dict):
            prefix_map[row['asset_id']] = row['category_prefix']
        else:
            prefix_map[row[0]] = row[1]

    # Delete chart_facts rows for each target's category_prefix
    for tgt in targets:
        prefix = prefix_map.get(tgt)
        if prefix:
            try:
                cur = conn.cursor()
                cur.execute(
                    "DELETE FROM chart_facts WHERE chart_id=%s AND ayanamsha_id IS NOT DISTINCT FROM ayanamsha_id "
                    "AND category LIKE %s",
                    (chart_id, prefix + '%')
                )
                deleted = cur.rowcount
            except Exception:
                try:
                    cur = conn.execute(
                        "DELETE FROM chart_facts WHERE chart_id=%s AND category LIKE %s",
                        (chart_id, prefix + '%')
                    )
                    deleted = cur.rowcount if hasattr(cur, 'rowcount') else 0
                except Exception as exc:
                    logger.warning("rebuild_asset: chart_facts delete for %s failed: %s", tgt, exc)
                    deleted = 0
            logger.debug("rebuild_asset: deleted %d chart_facts rows for %s (prefix=%s)", deleted, tgt, prefix)

        # Delete build_checkpoints for this asset in this build
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM build_checkpoints WHERE build_id=%s AND asset_id=%s",
                (build_id, tgt)
            )
        except Exception:
            try:
                conn.execute(
                    "DELETE FROM build_checkpoints WHERE build_id=%s AND asset_id=%s",
                    (build_id, tgt)
                )
            except Exception as exc:
                logger.warning("rebuild_asset: checkpoint delete for %s failed: %s", tgt, exc)

    # Emit rebuild_requested event
    # build_events columns: build_id, stage_seq (auto), chart_id, ayanamsha_role, asset, stage, status,
    #                       percent, message, metadata, emitted_at
    cascade_payload = json.dumps({'cascade_targets': targets_list, 'root_asset': asset_id})
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO build_events
                (build_id, stage_seq, chart_id, ayanamsha_role, asset, stage, status, metadata, emitted_at)
            VALUES (
                %s,
                COALESCE((SELECT MAX(stage_seq)+1 FROM build_events WHERE build_id=%s), 1),
                %s, 'all', %s, 'dispatch', 'rebuild_requested', %s::jsonb, NOW()
            )
            """,
            (build_id, build_id, chart_id, asset_id, cascade_payload)
        )
    except Exception as exc:
        logger.warning("rebuild_asset: build_events insert failed (non-fatal): %s", exc)

    logger.info("rebuild_asset: complete — %d assets invalidated for root=%s", len(targets), asset_id)


# ── Resume build ───────────────────────────────────────────────────────────────

def resume_build(chart_id: str, build_id: str, conn) -> List[tuple]:
    """
    Return list of (asset_id, ayanamsha_id) tuples that have already succeeded,
    and emit a resume_requested event so the dispatcher skips completed pairs.
    """
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT asset_id, ayanamsha_id FROM build_checkpoints WHERE build_id=%s AND status='success'",
            (build_id,)
        )
        rows = cur.fetchall()
    except Exception:
        rows = conn.execute(
            "SELECT asset_id, ayanamsha_id FROM build_checkpoints WHERE build_id=%s AND status='success'",
            (build_id,)
        ).fetchall()

    done = []
    for row in rows:
        if isinstance(row, dict):
            done.append((row['asset_id'], row['ayanamsha_id']))
        else:
            done.append((row[0], row[1]))

    skip_completed = [list(x) for x in done]
    resume_payload = json.dumps({'skip_completed': skip_completed})

    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO build_events
                (build_id, stage_seq, chart_id, ayanamsha_role, asset, stage, status, metadata, emitted_at)
            VALUES (
                %s,
                COALESCE((SELECT MAX(stage_seq)+1 FROM build_events WHERE build_id=%s), 1),
                %s, 'all', 'PIPELINE', 'dispatch', 'resume_requested', %s::jsonb, NOW()
            )
            """,
            (build_id, build_id, chart_id, resume_payload)
        )
    except Exception as exc:
        logger.warning("resume_build: build_events insert failed (non-fatal): %s", exc)

    logger.info("resume_build: %d completed (asset, ayanamsha) pairs found for build=%s", len(done), build_id)
    return done


# ── SSE graph event helpers ────────────────────────────────────────────────────

def notify_first_row_write(
    conn,
    build_id: str,
    chart_id: str,
    asset_id: str,
    ayanamsha_id: str,
    row_count: int,
    layer: str,
) -> None:
    """
    Emit a node_added SSE event the FIRST time a writer successfully writes
    rows for a given (asset_id, ayanamsha_id) pair within a build.

    Deduped with _emitted_nodes — subsequent calls for the same pair are
    no-ops. Non-fatal: exceptions are swallowed.

    Call this from the build orchestrator immediately after a writer's first
    successful row-write for each (asset_id, ayanamsha_id) combination.
    """
    key = (asset_id, ayanamsha_id)
    if key in _emitted_nodes:
        return
    _emitted_nodes.add(key)
    try:
        emit_node_added(conn, build_id, chart_id, asset_id, ayanamsha_id, row_count, layer)
    except Exception as e:
        logger.warning("notify_first_row_write: emit_node_added failed for %s/%s: %s", asset_id, ayanamsha_id, e)


def notify_downstream_edges(
    conn,
    build_id: str,
    chart_id: str,
    asset_id: str,
) -> None:
    """
    Emit edge_added SSE events for all upstream→asset_id edges from the
    build_dependencies table, ONCE per build.

    Deduped with _emitted_edges — subsequent calls for the same edge pair are
    no-ops. Non-fatal: exceptions are swallowed.

    Call this when a downstream asset begins processing (before its first
    row-write) so the graph shows the edge as the node comes online.
    Requires _load_dep_graph() to have been called first.
    """
    # Find all upstreams: iterate dep graph to find which assets list asset_id
    # as a dependent. The dep_graph maps upstream -> list[downstream].
    _load_dep_graph(conn)
    for upstream, downstreams in _dep_graph.items():
        if asset_id not in downstreams:
            continue
        edge_key = (upstream, asset_id)
        if edge_key in _emitted_edges:
            continue
        _emitted_edges.add(edge_key)
        try:
            emit_edge_added(conn, build_id, chart_id, upstream, asset_id, "data_flow")
        except Exception as e:
            logger.warning(
                "notify_downstream_edges: emit_edge_added failed for %s->%s: %s",
                upstream, asset_id, e
            )
