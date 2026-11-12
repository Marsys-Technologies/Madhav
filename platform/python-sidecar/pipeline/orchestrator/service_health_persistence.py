"""Build-owned persistence for registered service self-test telemetry."""
from __future__ import annotations

from datetime import datetime
from typing import Literal


def persist_tulana_selftest_health(
    conn,
    *,
    health: Literal["healthy", "degraded"],
    observed_at: datetime,
    detail_json: str,
) -> None:
    """Record Tulana's self-test result in the caller's transaction."""
    conn.execute(
        """
        UPDATE asset_registry
        SET service_health   = %s,
            last_selftest_at = %s,
            selftest_detail  = %s
        WHERE asset_id = 'ka_tulana'
        """,
        [health, observed_at, detail_json],
    )
