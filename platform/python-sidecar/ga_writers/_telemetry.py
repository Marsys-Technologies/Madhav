"""Shared asset_throughput telemetry for the L1 Gaṇita writers.

Every writer historically carried its own `_update_asset_throughput` that INSERTed
into columns the table does not have (`row_count`, `build_state`, `last_build_id`,
`status`, `pct_complete`, `updated_at`) with mismatched ON CONFLICT targets, so the
upsert always raised and was swallowed by a best-effort guard — telemetry never
landed. This helper writes the *actual* asset_throughput schema:

    (chart_id, asset_id, state, rows_written, last_measured_build_id,
     last_built_at, last_measured_at)

upserting on the real partial unique key `(chart_id, asset_id) WHERE chart_id IS
NOT NULL`. It remains best-effort — wrapped in a psycopg savepoint so a telemetry
failure can never poison the build transaction (the cockpit reads count_sql from
asset_registry, not this table) — but now it succeeds.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_UPSERT_SQL = """
INSERT INTO asset_throughput
  (chart_id, asset_id, state, rows_written, last_measured_build_id,
   last_built_at, last_measured_at)
VALUES (%s, %s, %s, %s, %s::uuid, NOW(), NOW())
ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
DO UPDATE SET
  state                   = EXCLUDED.state,
  rows_written            = EXCLUDED.rows_written,
  last_measured_build_id  = EXCLUDED.last_measured_build_id,
  last_built_at           = NOW(),
  last_measured_at        = NOW()
"""


def update_asset_throughput(
    conn: Any,
    asset_id: str,
    chart_id: str,
    build_id: str,
    rows_written: int,
    *,
    state: str = "lit",
) -> None:
    """Best-effort upsert of a writer's per-chart build state into asset_throughput.

    SET semantics: `rows_written` is the final/cumulative total for the asset, not a
    delta. `state` is one of the asset_throughput CHECK values
    (dormant/building/lit/stale/error)."""
    try:
        with conn.transaction():
            conn.execute(_UPSERT_SQL, [chart_id, asset_id, state, rows_written, str(build_id)])
        logger.info("[telemetry] asset_throughput %s chart=%s rows=%d state=%s",
                    asset_id, chart_id, rows_written, state)
    except Exception as exc:  # noqa: BLE001 — telemetry is non-fatal
        logger.warning("[telemetry] asset_throughput update failed (non-fatal): %s", exc)
