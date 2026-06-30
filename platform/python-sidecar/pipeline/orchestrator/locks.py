"""Advisory lock helpers for per-chart build exclusion."""
from __future__ import annotations


def acquire_chart_lock(cur, chart_id: str) -> bool:
    """Try to acquire an exclusive advisory lock on chart_id. Non-blocking.

    hashtext() returns int32 (range -2^31 .. 2^31-1). Two distinct chart_id
    UUIDs collide with probability ~1/(2^31) per pair — negligible at hundreds
    of charts, but documented here so future maintainers are aware.
    """
    cur.execute(
        "SELECT pg_try_advisory_lock(hashtext(%s)) AS got",
        (str(chart_id),),
    )
    row = cur.fetchone()
    return bool(row["got"])


def release_chart_lock(cur, chart_id: str) -> None:
    cur.execute("SELECT pg_advisory_unlock(hashtext(%s))", (str(chart_id),))
