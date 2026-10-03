"""
test_mi_jivanaghatana_lel_scope.py — F10 (LIFE_EVENTS_SCOPE_AUDIT, SS N-110).

`mi_jivanaghatana.run()` used to carry a dead `else: SELECT * FROM life_events
ORDER BY event_id` branch taken only when `life_events` had no `chart_id` column.
That branch read EVERY chart's people-entered rows. It is gone: a table without a
`chart_id` column now makes the writer fail loudly, and the only life_events read
that can ever be issued is the chart-scoped one.

Synthetic fixtures only; no database (stand-in cursor records the issued SQL).
"""
from __future__ import annotations

import inspect
import re

import pytest

from pipeline.orchestrator.writers import mi_jivanaghatana as mod
from pipeline.orchestrator.writers.mi_jivanaghatana import MiJivanaghatanaWriter

CHART = "11111111-1111-4111-8111-111111111111"


class _Cur:
    def __init__(self, conn):
        self._c = conn
        self._result: list = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        self._c.issued.append((s, params))
        if "information_schema.columns" in s:
            self._result = [{"column_name": c} for c in self._c.columns]
        elif "COUNT(*)" in s.upper():
            self._result = [(0,)]
        elif "FROM life_events" in s:
            self._result = []
        else:
            self._result = []

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None

    def executemany(self, sql, params_list):
        self._result = []


class _Conn:
    def __init__(self, columns):
        self.columns = columns
        self.issued: list = []

    def cursor(self, row_factory=None):
        return _Cur(self)


class _Ctx:
    def __init__(self, conn):
        self.config = {"chart_id": CHART}
        self.db_conn = conn
        self.dry_run = False


def _life_events_selects(conn):
    return [s for s, _ in conn.issued if re.search(r"\bFROM life_events\b", s)]


def test_table_without_chart_id_column_fails_loudly_and_reads_nothing():
    conn = _Conn(columns=["event_id", "event_date", "description"])  # no chart_id
    with pytest.raises(Exception) as ei:
        MiJivanaghatanaWriter().run(_Ctx(conn))
    assert "chart_id" in str(ei.value)
    assert _life_events_selects(conn) == [], (
        "no SELECT from life_events may be issued when it cannot be chart-scoped"
    )


def test_chart_scoped_read_is_the_only_life_events_select():
    conn = _Conn(columns=["chart_id", "event_id", "event_date"])
    MiJivanaghatanaWriter().run(_Ctx(conn))
    selects = _life_events_selects(conn)
    assert selects, "expected the chart-scoped read"
    for s in selects:
        assert "WHERE chart_id = %s" in s, f"unscoped life_events read: {s!r}"
    params = [p for s, p in conn.issued if "FROM life_events WHERE chart_id" in s]
    assert all(p == (CHART,) for p in params)


def test_source_has_no_unscoped_life_events_select():
    src = inspect.getsource(mod)
    for m in re.finditer(r"FROM life_events[^\"']*", src):
        assert "chart_id" in m.group(0), f"unscoped life_events read in source: {m.group(0)!r}"
