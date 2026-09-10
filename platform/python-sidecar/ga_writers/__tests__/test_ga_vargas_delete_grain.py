"""ga_vargas must not delete rows an earlier pass of the SAME run just wrote.

Nirmāṇa L1-W1 finding F-A3.

`replace_prior_chart_divisionals` deletes everything for the (chart, ayanamsha,
varga) scopes present in a batch. `build_ga_vargas` calls `_write_rows_batch` up
to five times per ayanamsha — the main varga loop, the D30-lords pass, the
cross-varga harmonics, and two scope-cap sentinels — so any later pass carrying a
varga an earlier pass already wrote silently erased that earlier output.

Measured live before the fix (chart 482012f1, lahiri_chitrapaksha): **D30 held 10
rows across 1 fact_category while every peer varga held 147 across 10.** The
D30-lords pass had erased the main loop's D30 output.

Nothing detected it because `_write_rows_batch` returned `len(rows)` rather than
the rows that survived — `asset_throughput.rows_written` read 38,620 against
23,542 live, a 39% loss reported as a clean build (CLAUDE.md §N.8).

These tests use a fake connection so they assert the DELETE/INSERT *behaviour*
without needing a database.
"""
from __future__ import annotations

from typing import Any

import pytest


class _FakeCursor:
    def __init__(self, log: list[tuple[str, Any]]) -> None:
        self._log = log
        self.rowcount = 0

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def execute(self, sql: str, params: Any = None) -> None:
        self._log.append(("execute", sql, params))
        if sql.strip().upper().startswith("DELETE"):
            self.rowcount = 0

    def executemany(self, sql: str, rows: Any) -> None:
        rows = list(rows)
        self._log.append(("executemany", sql, rows))
        self.rowcount = len(rows)

    def fetchone(self) -> dict:
        return {"count": 0}


class _FakeConn:
    """Enough of a psycopg3 connection for this writer's two access styles.

    `_idempotency._delete` calls `conn.execute(...)` directly; `_write_rows_batch`
    goes through `conn.cursor()`. Both are modelled so the DELETEs and the INSERT
    land in one ordered log.
    """

    def __init__(self) -> None:
        self.log: list[tuple[str, Any]] = []

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self.log)

    def execute(self, sql: str, params: Any = None) -> _FakeCursor:
        cur = _FakeCursor(self.log)
        cur.execute(sql, params)
        return cur


def _row(varga: str, subject: str) -> dict:
    return {
        "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
        "ayanamsha_id": "lahiri_chitrapaksha",
        "varga": varga,
        "fact_subject": subject,
        "verification_pass_status": "single",
    }


def _deletes(conn: _FakeConn) -> list[tuple[str, Any]]:
    return [entry for entry in conn.log if entry[0] == "execute"
            and entry[1].strip().upper().startswith("DELETE")]


def test_a_scope_is_delete_cleared_at_most_once_per_run() -> None:
    """The D30 case, reduced: two passes over the same varga, one delete."""
    from ga_writers import ga_vargas_writer as w

    conn = _FakeConn()
    cleared: set = set()

    # Pass 1 — the main varga loop writes D30's per-graha rows.
    w._write_rows_batch(conn, [_row("D30", "D30.SUN"), _row("D30", "D30.MOON")], cleared)
    assert len(_deletes(conn)) == 1, "the first pass over a scope must clear it"

    # Pass 2 — the D30-lords pass. Before the fix this DELETE removed pass 1.
    w._write_rows_batch(conn, [_row("D30", "D30.S1"), _row("D30", "D30.S2")], cleared)
    assert len(_deletes(conn)) == 1, (
        "a second pass over an already-cleared scope must NOT delete again — "
        "that is the defect that left D30 with 10 rows against its peers' 147"
    )


def test_an_unseen_scope_is_still_cleared() -> None:
    """§N.3 must survive the fix: a rebuild still REPLACES, it does not accrete."""
    from ga_writers import ga_vargas_writer as w

    conn = _FakeConn()
    cleared: set = set()
    w._write_rows_batch(conn, [_row("D30", "D30.SUN")], cleared)
    w._write_rows_batch(conn, [_row("D9", "D9.SUN")], cleared)
    assert len(_deletes(conn)) == 2, "each distinct scope must be cleared exactly once"


def test_a_fresh_run_clears_every_scope_again() -> None:
    """The set is run-scoped, never persisted — the next build re-clears."""
    from ga_writers import ga_vargas_writer as w

    for _ in range(2):
        conn = _FakeConn()
        w._write_rows_batch(conn, [_row("D30", "D30.SUN")], set())
        assert len(_deletes(conn)) == 1


def test_omitting_the_set_preserves_the_original_delete_every_time_behaviour() -> None:
    """Back-compat: a caller that passes no set gets exactly the old semantics."""
    from ga_writers import ga_vargas_writer as w

    conn = _FakeConn()
    w._write_rows_batch(conn, [_row("D30", "D30.SUN")])
    w._write_rows_batch(conn, [_row("D30", "D30.S1")])
    assert len(_deletes(conn)) == 2


def test_reports_rows_that_landed_not_rows_attempted() -> None:
    """The detection half of F-A3 (§N.8).

    ON CONFLICT DO NOTHING silently skips a colliding row. Returning len(rows)
    counted those skips as successes, which is why a 39% loss read as success.
    """
    from ga_writers import ga_vargas_writer as w

    class _PartialCursor(_FakeCursor):
        def executemany(self, sql: str, rows: Any) -> None:
            rows = list(rows)
            self._log.append(("executemany", sql, rows))
            self.rowcount = len(rows) - 1  # one row lost to a conflict

    class _PartialConn(_FakeConn):
        def cursor(self) -> _FakeCursor:
            return _PartialCursor(self.log)

    conn = _PartialConn()
    written = w._write_rows_batch(conn, [_row("D9", "A"), _row("D9", "B")], set())
    assert written == 1, "must report the row that landed, not the two attempted"
