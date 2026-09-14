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
    def __init__(self, calls, param_calls, fail_on_select, rows, rows_by_params):
        self._calls = calls
        self._param_calls = param_calls
        self._fail_on_select = fail_on_select
        self._rows = rows
        self._rows_by_params = rows_by_params

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        self._calls.append(s)
        self._param_calls.append((s, params))
        if self._fail_on_select and s.upper().startswith("SELECT"):
            raise RuntimeError("canceling statement due to statement timeout")
        if s.upper().startswith("SELECT") and self._rows_by_params is not None:
            self._rows = self._rows_by_params.get(tuple(params), [])

    def fetchall(self):
        return self._rows


class _FakeConn:
    def __init__(self, fail_on_select=False, rows=None, rows_by_params=None):
        self.calls: list[str] = []
        self.param_calls: list[tuple[str, object]] = []
        self._fail_on_select = fail_on_select
        self._rows = rows or []
        self._rows_by_params = rows_by_params

    def cursor(self, row_factory=None):
        return _FakeCursor(
            self.calls, self.param_calls, self._fail_on_select,
            self._rows, self._rows_by_params,
        )


def test_dasha_lookup_rolls_back_savepoint_on_timeout():
    conn = _FakeConn(fail_on_select=True)
    # must not raise, must return the safe (None, None) default
    result = _load_dasha_periods(
        conn, "chart-1", "Sun", "lahiri_chitrapaksha", "build-1",
        condition_score=0.9,
    )
    assert result == (None, None)
    joined = " | ".join(conn.calls)
    assert "SAVEPOINT sp_ga_cond_dasha" in joined
    assert "ROLLBACK TO SAVEPOINT sp_ga_cond_dasha" in joined
    # never RELEASE on the failure path
    assert "RELEASE SAVEPOINT sp_ga_cond_dasha" not in joined


def test_dasha_lookup_releases_savepoint_on_success():
    conn = _FakeConn(fail_on_select=False)
    result = _load_dasha_periods(
        conn, "chart-1", "Sun", "lahiri_chitrapaksha", "build-1",
        condition_score=0.9,
    )
    assert result == (None, None)  # no rows from the fake → safe default
    joined = " | ".join(conn.calls)
    assert "SAVEPOINT sp_ga_cond_dasha" in joined
    assert "RELEASE SAVEPOINT sp_ga_cond_dasha" in joined
    assert "ROLLBACK TO SAVEPOINT sp_ga_cond_dasha" not in joined


def test_dasha_lookup_preserves_exact_source_row_identity():
    conn = _FakeConn(rows=[(
        "11111111-1111-4111-8111-111111111111",
        "vimshottari", "lahiri_chitrapaksha", "build-1",
        1, "Sun", "2000-01-01", "2006-01-01",
    )])
    peak, weak = _load_dasha_periods(
        conn, "chart-1", "Sun", "lahiri_chitrapaksha", "build-1",
        condition_score=0.9, dignity_d1="exalted"
    )
    assert weak is None
    assert peak[0]["source_dasha_row_id"] == "11111111-1111-4111-8111-111111111111"
    assert peak[0]["source_ayanamsha_id"] == "lahiri_chitrapaksha"
    assert peak[0]["source_build_id"] == "build-1"


def test_dasha_lookup_is_scoped_to_exact_ayanamsha_and_build():
    aya_a_row = (
        "11111111-1111-4111-8111-111111111111", "vimshottari", "aya-a", "build-a",
        1, "Sun", "2000-01-01", "2006-01-01",
    )
    aya_b_row = (
        "22222222-2222-4222-8222-222222222222", "vimshottari", "aya-b", "build-b",
        1, "Sun", "2001-01-01", "2007-01-01",
    )
    conn = _FakeConn(rows_by_params={
        ("chart-1", "aya-a", "build-a", "Sun"): [aya_a_row],
        ("chart-1", "aya-b", "build-b", "Sun"): [aya_b_row],
    })
    peak_a, _ = _load_dasha_periods(
        conn, "chart-1", "Sun", "aya-a", "build-a", condition_score=0.9,
    )
    peak_b, _ = _load_dasha_periods(
        conn, "chart-1", "Sun", "aya-b", "build-b", condition_score=0.9,
    )
    assert peak_a[0]["source_dasha_row_id"] != peak_b[0]["source_dasha_row_id"]
    assert peak_a[0]["source_ayanamsha_id"] == "aya-a"
    assert peak_b[0]["source_build_id"] == "build-b"
    _load_dasha_periods(
        conn, "chart-1", "Sun", "lahiri_chitrapaksha", "build-1",
        condition_score=0.9,
    )
    select = next(call for call in conn.calls if call.upper().startswith("SELECT"))
    assert "ayanamsha_id = %s" in select
    assert "build_id = %s" in select
    select_params = [
        params for sql, params in conn.param_calls if sql.upper().startswith("SELECT")
    ]
    assert ("chart-1", "aya-a", "build-a", "Sun") in select_params
    assert ("chart-1", "aya-b", "build-b", "Sun") in select_params


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
