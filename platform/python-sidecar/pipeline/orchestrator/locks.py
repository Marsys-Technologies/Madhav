"""Advisory lock helpers for per-chart build exclusion."""
from __future__ import annotations


def acquire_chart_lock(cur, chart_id: str) -> bool:
    """Try to acquire an exclusive advisory lock on chart_id. Non-blocking."""
    cur.execute(
        "SELECT pg_try_advisory_lock(hashtext(%s)) AS got",
        (str(chart_id),),
    )
    row = cur.fetchone()
    return bool(row["got"])


def release_chart_lock(cur, chart_id: str) -> None:
    cur.execute("SELECT pg_advisory_unlock(hashtext(%s))", (str(chart_id),))
