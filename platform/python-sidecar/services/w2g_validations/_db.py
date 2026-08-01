"""
w2g_validations._db — the one narrow DB seam every W2G validation goes
through.

WHY A SEAM AT ALL: every validation in this package is a PURE function of a
`QueryFn` — `(sql: str, params: Sequence) -> list[dict]`. That makes each
validation unit-testable against canned rows with NO live database, and
makes the live run a one-line adapter over a real psycopg connection. It
also makes the read-only posture structural rather than a promise: this
module issues nothing but SELECTs and never commits, rolls back, or closes
a caller-owned connection.

Bind-time validations are DIAGNOSTIC and run OUTSIDE the orchestrator's
substep transaction. This module therefore deliberately does NOT reach for
`savepoint_scope` — it is not running inside `SAVEPOINT writer_exec` and has
no outer savepoint to protect. When the 2.0 WRITER later invokes these same
validations at bind time on `ctx.db_conn`, it must wrap them the way every
other in-substep read is wrapped (see
`services/gochara_intensity/_dbutil.savepoint_scope`) — that wrapping is the
writer's job, not this module's, and is called out here so the writer lane
does not miss it.
"""
from __future__ import annotations

from typing import Any, Callable, Protocol, Sequence

QueryFn = Callable[[str, Sequence[Any]], list[dict]]


class _Cursorish(Protocol):  # pragma: no cover - typing aid only
    description: Any

    def fetchall(self) -> list[Any]: ...


def query_fn_from_conn(conn) -> QueryFn:
    """Adapt a psycopg (v2 or v3) connection into a `QueryFn`.

    The returned callable NEVER commits, rolls back, or closes `conn` —
    the caller owns the transaction, always.
    """

    def _query(sql: str, params: Sequence[Any] = ()) -> list[dict]:
        cur = conn.cursor()
        try:
            cur.execute(sql, list(params))
            rows = cur.fetchall()
            if not rows:
                return []
            if isinstance(rows[0], dict):
                return [dict(r) for r in rows]
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        finally:
            try:
                cur.close()
            except Exception:  # noqa: BLE001 - cursor close is best-effort
                pass

    return _query


def table_exists(query: QueryFn, table_name: str) -> bool:
    rows = query(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = %s",
        [table_name],
    )
    return bool(rows)


def column_names(query: QueryFn, table_name: str) -> list[str]:
    rows = query(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s "
        "ORDER BY ordinal_position",
        [table_name],
    )
    return [r["column_name"] for r in rows]


__all__ = ["QueryFn", "query_fn_from_conn", "table_exists", "column_names"]
