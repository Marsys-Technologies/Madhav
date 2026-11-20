"""
test_w44_pool_consent.py -- DB-free tests for the F8 pool-consent gate in
w44_weight_fitting (Track I, LIFE_EVENTS_SCOPE_AUDIT finding F8, SS N-110).

`load_pooled_train_events` pools a SECOND chart's people-entered life events with
the native's. It must consume a row only when that row carries
`life_events.pool_consent = true` AND the global cross-chart pool is switched on
(the same two-key consume-side firewall as
services.mimamsa.lel_calibration.may_consume_into_pool). A row with
pool_consent false/NULL is NEVER pooled; if nothing is consented the second chart
contributes nothing and the result says so (no fabricated fallback).

Fixtures are synthetic (generated ids and dates); no real event content.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))  # scripts/
sys.path.insert(0, str(Path(__file__).parents[4]))  # platform/python-sidecar/

from kala_admission import w44_weight_fitting as W  # noqa: E402

CHART = "00000000-0000-4000-8000-0000000000aa"  # synthetic second chart


class _Cur:
    def __init__(self, conn):
        self._c = conn
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self._c.executed.append((sql, params))
        if "information_schema.tables" in sql:
            self._rows = [{"table_name": "life_events"}]
        else:
            self._rows = list(self._c.event_rows)

    def fetchall(self):
        return self._rows


class _Conn:
    """Returns the supplied life_events rows exactly as a dict_row connection would
    (the SQL is not emulated: the gate under test must hold in Python)."""

    def __init__(self, event_rows):
        self.event_rows = event_rows
        self.executed = []

    def cursor(self):
        return _Cur(self)


def _row(n, consent):
    return {"event_id": f"SYN.{n}", "event_date": date(2001, 1, n), "pool_consent": consent}


@pytest.fixture(autouse=True)
def _pool_flag_off(monkeypatch):
    monkeypatch.delenv("MIMAMSA_CROSS_CHART_POOL", raising=False)


def test_consent_false_rows_are_excluded_and_counted():
    conn = _Conn([_row(1, False), _row(2, False)])
    pairs, withheld = W.load_pooled_train_events(conn, CHART, pool_override="on")
    assert pairs == []
    assert withheld == 2


def test_consent_true_rows_are_included_when_pool_on():
    conn = _Conn([_row(1, True), _row(2, True)])
    pairs, withheld = W.load_pooled_train_events(conn, CHART, pool_override="on")
    assert pairs == [("SYN.1", date(2001, 1, 1)), ("SYN.2", date(2001, 1, 2))]
    assert withheld == 0


def test_mixed_only_consented_rows_pooled():
    conn = _Conn([_row(1, True), _row(2, False), _row(3, None), _row(4, True)])
    pairs, withheld = W.load_pooled_train_events(conn, CHART, pool_override="on")
    assert [p[0] for p in pairs] == ["SYN.1", "SYN.4"]
    assert withheld == 2  # the False row and the NULL row


def test_consent_true_but_global_pool_off_is_not_consumed():
    """Two keys required (may_consume_into_pool): consent alone is not enough."""
    conn = _Conn([_row(1, True)])
    pairs, withheld = W.load_pooled_train_events(conn, CHART)  # env unset -> OFF
    assert pairs == []
    assert withheld == 1


def test_tuple_rows_are_gated_too():
    conn = _Conn([("SYN.1", date(2001, 1, 1), True), ("SYN.2", date(2001, 1, 2), False)])
    pairs, withheld = W.load_pooled_train_events(conn, CHART, pool_override="on")
    assert [p[0] for p in pairs] == ["SYN.1"]
    assert withheld == 1


def test_train_split_still_enforced():
    conn = _Conn([
        {"event_id": "SYN.OLD", "event_date": date(2001, 1, 1), "pool_consent": True},
        {"event_id": "SYN.NEW", "event_date": date(2021, 1, 1), "pool_consent": True},
    ])
    pairs, _ = W.load_pooled_train_events(conn, CHART, pool_override="on")
    assert [p[0] for p in pairs] == ["SYN.OLD"]


def test_query_selects_pool_consent_and_is_chart_scoped():
    conn = _Conn([])
    W.load_pooled_train_events(conn, CHART, pool_override="on")
    sql, params = conn.executed[-1]
    assert "pool_consent" in sql
    assert "chart_id = %s" in sql
    assert params == (CHART,)


def test_legacy_wrapper_returns_only_consented_pairs():
    conn = _Conn([_row(1, True), _row(2, False)])
    pairs = W.load_abhinandan_train_events(conn, CHART, pool_override="on")
    assert [p[0] for p in pairs] == ["SYN.1"]
    assert W.load_abhinandan_train_events(_Conn([_row(1, False)]), CHART, pool_override="on") == []


def test_empty_when_nothing_consented_no_fabricated_fallback():
    conn = _Conn([_row(1, False)])
    pairs, withheld = W.load_pooled_train_events(conn, CHART, pool_override="on")
    assert pairs == [] and withheld == 1


def test_main_fit_uses_gate_not_raw_loader():
    """The fit entry point must call the gated loader and report the withheld count
    (a regression to the ungated read would drop both)."""
    src = Path(W.__file__).read_text(encoding="utf-8")
    assert "load_pooled_train_events(conn, ABHINANDAN_CHART_ID" in src
    assert "abhinandan_events_withheld_no_pool_consent" in src
