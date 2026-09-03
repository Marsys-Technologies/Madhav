"""
Downstream staleness propagation -- delta-directional (O-wave WP-1).

After an asset transitions to 'lit', all transitive downstream assets that are
NOT in the current run's plan are marked 'stale' in asset_throughput, but ONLY
when the completed asset's own output actually changed this run (compared
against its prior complete provenance receipt). A no-delta completion (e.g. an
idempotent rebuild that reproduces identical rows) emits `refreshed_no_delta`
instead -- phantom staleness on mere re-execution is exactly the defect this
replaces. See NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.1.

Dormant assets are excluded — they have no data to be stale. Building state is
excluded — leave in-flight assets alone.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def compute_downstream_ids(
    completed_asset_id: str,
    registry: list[dict],
) -> set[str]:
    """
    BFS over the reverse dependency graph to find all transitive downstream
    assets of completed_asset_id. Pure function — no DB access.

    registry: list of dicts with keys 'asset_id' and 'depends_on' (list[str]).
    """
    # Build reverse graph: for each asset, which assets depend on it
    dependents: dict[str, set[str]] = {}
    for row in registry:
        for dep in row.get('depends_on') or []:
            dependents.setdefault(dep, set()).add(row['asset_id'])

    downstream: set[str] = set()
    queue = list(dependents.get(completed_asset_id, set()))
    while queue:
        nxt = queue.pop()
        if nxt in downstream:
            continue
        downstream.add(nxt)
        queue.extend(dependents.get(nxt, set()))
    return downstream


def propagate_downstream_staleness(
    conn,
    cur,
    chart_id: Optional[str],
    completed_asset_id: str,
    plan_set: set[str],
    registry: list[dict],
    emit_fn,
    run_id: str,
) -> None:
    """
    Delta-directional: mark transitive downstream of completed_asset_id as
    'stale' ONLY when completed_asset_id's own output actually changed this
    run (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §3.1, O-wave WP-1). On a
    no-delta completion, emit `asset.refreshed_no_delta` instead of touching
    any downstream row -- visible, not silent.

    The delta signal is `build_run_assets.output_changed`, written by
    asset_runner.py's data-writer receipt capture in the SAME transaction as
    the write it describes (migration 640). This function reads it fresh:
    TRUE → propagate as before; FALSE → refreshed_no_delta only; NULL (no
    signal recorded -- a probe/service asset, or a row predating the column)
    → fail-open, propagate exactly as the pre-WP-1 code always did. Missing
    evidence must never be read as "no delta"; that would be silent
    corruption in the other direction (CLAUDE.md §N.8).

    Excludes (once propagation proceeds):
      - Assets in plan_set (they will be rebuilt in this run)
      - Assets with state 'dormant' (no data to be stale about)
      - Assets with state 'building' (leave in-flight workers alone)

    Uses RETURNING to emit events only for rows that actually changed, and reads the
    row's ACTUAL prior state so `from_state` is measured rather than asserted.

    §N.8 note (SAMĀPTI B-N8-SWEEPFIX, F-05): `from_state` used to be the literal
    "lit". The UPDATE matches `state IN ('lit', 'service_ok')` and the old RETURNING
    returned only `asset_id`, so the prior state was never read — an asset that was
    `service_ok` produced an operator-facing event (WorkflowView.tsx renders
    `from_state → to_state` verbatim) claiming it had been `lit`. A state-transition
    assertion is the narrowest possible status claim; it must be computed.

    Commits on conn — caller must provide a dedicated connection (not the main
    advisory-lock connection) and must close it after.
    """
    cur.execute(
        "SELECT output_changed FROM build_run_assets WHERE run_id = %s AND asset_id = %s",
        (run_id, completed_asset_id),
    )
    row = cur.fetchone()
    if row is not None:
        output_changed = row[0] if isinstance(row, (tuple, list)) else row.get("output_changed")
    else:
        output_changed = None
    if output_changed is False:
        try:
            emit_fn({
                "type": "asset.refreshed_no_delta",
                "chart_id": chart_id,
                "asset_id": completed_asset_id,
                "run_id": run_id,
            })
        except Exception as emit_err:
            logger.warning(
                "[staleness] refreshed_no_delta emit failed for %s: %s",
                completed_asset_id, emit_err,
            )
        logger.info(
            "[staleness] %s completed with no output delta — no downstream propagation",
            completed_asset_id,
        )
        return

    downstream = compute_downstream_ids(completed_asset_id, registry)
    targets = list(downstream - plan_set)
    if not targets:
        return

    try:
        # The self-join against a pre-UPDATE snapshot is how the OLD value is
        # obtained: a plain `RETURNING state` yields the post-UPDATE value
        # ('stale') and would be just as unearned as the literal it replaces.
        cur.execute(
            """
            UPDATE asset_throughput AS t
               SET state = 'stale'
              FROM (
                    SELECT asset_id AS prev_asset_id, state AS prev_state
                      FROM asset_throughput
                     WHERE chart_id = %s
                       AND asset_id = ANY(%s::text[])
                       AND state IN ('lit', 'service_ok')
                       FOR UPDATE
                   ) AS old
             WHERE t.chart_id = %s
               AND t.asset_id = old.prev_asset_id
            RETURNING t.asset_id, old.prev_state
            """,
            (chart_id, targets, chart_id),
        )
        rows = cur.fetchall()
        staled = [
            (r[0], r[1]) if isinstance(r, (tuple, list)) else (r['asset_id'], r['prev_state'])
            for r in rows
        ]
        conn.commit()

        for asset_id, prev_state in staled:
            try:
                emit_fn({
                    "type": "asset.state_change",
                    "chart_id": chart_id,
                    "asset_id": asset_id,
                    "from_state": prev_state,
                    "to_state": "stale",
                    "run_id": run_id,
                })
            except Exception as emit_err:
                logger.warning(
                    "[staleness] SSE emit failed for %s: %s", asset_id, emit_err
                )

        if staled:
            logger.info(
                "[staleness] %s completed → marked %d downstream stale: %s",
                completed_asset_id, len(staled), [a for a, _ in staled],
            )

    except Exception as exc:
        logger.error(
            "[staleness] propagation failed after %s: %s", completed_asset_id, exc
        )
        try:
            conn.rollback()
        except Exception:
            pass
