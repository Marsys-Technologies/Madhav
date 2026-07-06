"""
test_ga_condition_savepoint_guard.py — BA-P3 (2026-07-06): ga_condition's
per-graha chart_dashas / chart_divisionals lookups must be SAVEPOINT-guarded so
a single slow/failed read (e.g. a chart_dashas lookup that hits
statement_timeout under load) rolls back cleanly instead of poisoning the
shared substep transaction. The prior swallow-without-rollback turned one slow
query into InFailedSqlTransaction on every subsequent statement + the final
DELETE — a failed L1 ga_condition that blocked the entire L2-L5 DAG.

DB-free: a fake psycopg-shaped connection/cursor records execute() calls and
can be told to raise on the main SELECT.
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers.ga_condition_writer import (  # noqa: E402
    _load_dasha_periods,
    _load_varga_dignity_spread,
)


class _FakeCursor:
    def __init__(self, calls, fail_on_select):
        self._calls = calls
        self._fail_on_select = fail_on_select

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        self._calls.append(s)
        if self._fail_on_select and s.upper().startswith("SELECT"):
            raise RuntimeError("canceling statement due to statement timeout")

    def fetchall(self):
        return []


class _FakeConn:
    def __init__(self, fail_on_select=False):
        self.calls: list[str] = []
        self._fail_on_select = fail_on_select

    def cursor(self, row_factory=None):
        return _FakeCursor(self.calls, self._fail_on_select)


def test_dasha_lookup_rolls_back_savepoint_on_timeout():
    conn = _FakeConn(fail_on_select=True)
    # must not raise, must return the safe (None, None) default
    result = _load_dasha_periods(conn, "chart-1", "Sun", condition_score=0.9)
    assert result == (None, None)
    joined = " | ".join(conn.calls)
    assert "SAVEPOINT sp_ga_cond_dasha" in joined
    assert "ROLLBACK TO SAVEPOINT sp_ga_cond_dasha" in joined
    # never RELEASE on the failure path
    assert "RELEASE SAVEPOINT sp_ga_cond_dasha" not in joined


def test_dasha_lookup_releases_savepoint_on_success():
    conn = _FakeConn(fail_on_select=False)
    result = _load_dasha_periods(conn, "chart-1", "Sun", condition_score=0.9)
    assert result == (None, None)  # no rows from the fake → safe default
    joined = " | ".join(conn.calls)
    assert "SAVEPOINT sp_ga_cond_dasha" in joined
    assert "RELEASE SAVEPOINT sp_ga_cond_dasha" in joined
    assert "ROLLBACK TO SAVEPOINT sp_ga_cond_dasha" not in joined


def test_varga_spread_rolls_back_savepoint_on_timeout():
    conn = _FakeConn(fail_on_select=True)
    result = _load_varga_dignity_spread(conn, "chart-1", "lahiri_chitrapaksha", "Moon")
    assert result is None
    joined = " | ".join(conn.calls)
    assert "SAVEPOINT sp_ga_cond_varga" in joined
    assert "ROLLBACK TO SAVEPOINT sp_ga_cond_varga" in joined
    assert "RELEASE SAVEPOINT sp_ga_cond_varga" not in joined


def test_varga_spread_releases_savepoint_on_success():
    conn = _FakeConn(fail_on_select=False)
    result = _load_varga_dignity_spread(conn, "chart-1", "lahiri_chitrapaksha", "Moon")
    assert result is None  # no rows → safe default
    joined = " | ".join(conn.calls)
    assert "SAVEPOINT sp_ga_cond_varga" in joined
    assert "RELEASE SAVEPOINT sp_ga_cond_varga" in joined
    assert "ROLLBACK TO SAVEPOINT sp_ga_cond_varga" not in joined
