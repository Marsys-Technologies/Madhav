"""
Shared fake psycopg connection that reproduces the PRODUCTION row-factory
configuration: the orchestrator connection is created with
`row_factory=psycopg.rows.dict_row` (pipeline/orchestrator/db.py:26), so
`cur.fetchall()` returns plain dicts and numeric indexing (`row[0]`) raises
KeyError — exactly the crash the 2026-08-02 L0 global build (run 6fd72ed9) hit
in bg_parihara_rules (KeyError: 1) and bg_reference (KeyError: 0).

The pre-existing writer tests exercised tuple-row shapes, which is the
test-shape trap that let those bugs through CI. Every test built on this fake
runs the writer against dict rows by default, like production; a cursor opened
with an explicit `row_factory=psycopg.rows.tuple_row` gets tuples, matching
real psycopg semantics.
"""
from __future__ import annotations

from typing import Any

import psycopg.rows

# Sentinel: (cols, rows) for SELECTs; DML statements resolve to (None, None).
_DML = (None, None)


class FakeCursor:
    def __init__(self, conn: "FakeDictRowConnection", row_factory: Any = None):
        self._conn = conn
        # Real psycopg: a cursor without an explicit row_factory inherits the
        # connection's current row_factory AT CURSOR CREATION time.
        self._row_factory = row_factory if row_factory is not None else conn.row_factory
        self._result: list[Any] | None = None
        self.description: list[tuple] | None = None
        self.rowcount = -1

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    def _shape(self, cols: list[str], row: tuple) -> Any:
        if self._row_factory is psycopg.rows.tuple_row:
            return tuple(row)
        # Production default (dict_row): plain dict — numeric index → KeyError.
        return dict(zip(cols, row))

    def execute(self, sql: str, params: Any = None) -> None:
        self._conn.executed.append(sql)
        self._conn.maybe_fail(sql)
        cols, rows = self._conn.resolve(sql)
        if cols is None:
            self.description = None
            self._result = None
            self.rowcount = 1  # DML: pretend one row affected
        else:
            self.description = [(c, None, None, None, None, None, None) for c in cols]
            self._result = [self._shape(cols, r) for r in rows]
            self.rowcount = len(rows)

    def executemany(self, sql: str, rows_seq: Any) -> None:
        self._conn.executed.append(sql)
        self._conn.maybe_fail(sql)
        self.description = None
        self._result = None
        self.rowcount = len(list(rows_seq))

    def fetchall(self) -> list[Any]:
        return list(self._result or [])

    def fetchone(self) -> Any:
        if not self._result:
            return None
        return self._result[0]


class FakeDictRowConnection:
    """
    Emulates the orchestrator connection: default row_factory is dict_row.

    `tables` is a list of (sql_substring_lowercase, cols, rows_of_tuples);
    the first entry whose substring appears in the executed SQL (whitespace-
    normalized, lowercased) supplies the result set. Unmatched statements are
    treated as DML no-ops.

    `fail_on` is an optional lowercase SQL substring; any execute/executemany
    whose SQL contains it raises RuntimeError("injected failure") — used to
    prove the §N.8 re-raise semantics.
    """

    def __init__(
        self,
        tables: list[tuple[str, list[str] | None, list[tuple] | None]] | None = None,
        fail_on: str | None = None,
    ):
        self.row_factory = psycopg.rows.dict_row
        self._tables = tables or []
        self.fail_on = fail_on
        self.executed: list[str] = []

    def cursor(self, row_factory: Any = None) -> FakeCursor:
        return FakeCursor(self, row_factory)

    @staticmethod
    def _norm(sql: str) -> str:
        return " ".join(sql.split()).lower()

    def resolve(self, sql: str) -> tuple[list[str] | None, list[tuple] | None]:
        s = self._norm(sql)
        for substring, cols, rows in self._tables:
            if substring in s:
                return cols, rows
        return _DML

    def maybe_fail(self, sql: str) -> None:
        if self.fail_on and self.fail_on in self._norm(sql):
            raise RuntimeError(f"injected failure on: {self.fail_on}")
