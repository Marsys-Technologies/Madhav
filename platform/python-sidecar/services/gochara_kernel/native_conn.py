"""The orchestrator's connection, presented with TUPLE rows (A5.3 writerbase_conformance).

The governed runner hands a writer a psycopg connection with `row_factory=dict_row`; the A5.3
stores / verifier / record code index rows by position. Rather than make every module
row-shape-agnostic (and risk one silently mis-read), the writer wraps the connection ONCE at its
entry points so all of them see tuples. This is a VIEW: it never opens, commits, rolls back or
closes anything (the connection stays caller-owned) and passes every other attribute —
`transaction()`, `info`, … — straight through. An explicit `row_factory=` on a cursor wins.

Lives here (not in the writer module) so the writer's source stays free of any connection-library
name — its lifecycle guard test forbids it.
"""
from __future__ import annotations

from typing import Any


class TupleRowsConnection:
    def __init__(self, conn: Any):
        self._conn = conn

    def execute(self, query, params=None, **kwargs):
        from psycopg.rows import tuple_row
        return self._conn.cursor(row_factory=tuple_row).execute(query, params, **kwargs)

    def cursor(self, *args, **kwargs):
        from psycopg.rows import tuple_row
        kwargs.setdefault("row_factory", tuple_row)
        return self._conn.cursor(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)


def native_connection(conn: Any) -> Any:
    """`conn` as tuple rows — only when it is a REAL psycopg connection whose row factory is not
    already tuples (a dict_row runner connection). Idempotent; an object without a `row_factory`
    (the unit-test fakes) is returned exactly as it is."""
    from psycopg.rows import tuple_row
    factory = getattr(conn, "row_factory", None)
    if isinstance(conn, TupleRowsConnection) or factory is None or factory is tuple_row:
        return conn
    return TupleRowsConnection(conn)


__all__ = ["TupleRowsConnection", "native_connection"]
