"""
test_lel_query_chart_scope.py — chart_id is REQUIRED for `lel_query` (finding F2,
LIFE_EVENTS_SCOPE_AUDIT, SS N-110).

`life_events` is PEOPLE-ENTERED, PRIVATE and chart-scoped (SS N-109). Before this
fix `lel_query(chart_id=None)` skipped the chart predicate and returned up to 200
rows of EVERY chart (including the free-text `description`), reachable through
`POST /brahma/mimamsa/lel_query` and the CLI. These tests pin:

  1. omitted / None / empty / whitespace / malformed chart_id -> ValueError, and
     NO database connection is even opened (refusal happens before any SQL);
  2. a valid chart_id returns only that chart's rows, against an in-memory stand-in
     that holds two charts' rows and honours the SQL predicate exactly as issued
     (so removing the predicate makes the cross-chart assertion fail);
  3. the issued SQL (main query AND count query) ALWAYS carries the chart_id
     predicate, with chart_id bound as the first parameter;
  4. the HTTP route refuses a missing / invalid chart_id with 4xx (422);
  5. the CLI `query` subcommand requires --chart-id, and `gate` is chart-scoped;
  6. the L5 wrapper (`l5_lel_intake.lel_query`) inherits the same refusal.

Synthetic fixtures only: event rows are placeholder strings, no real event text.
No database access (a stand-in connection object is used).
"""
from __future__ import annotations

import re
import sys
from typing import Any
from unittest.mock import patch

import pytest

from brahmagyan.mimamsa import lel_intake as mod

CHART_A = "11111111-1111-4111-8111-111111111111"
CHART_B = "22222222-2222-4222-8222-222222222222"

_PREDICATE = re.compile(r"le\.chart_id\s*=\s*%s::UUID", re.IGNORECASE)


def _row(tag: str, date: str = "2020-01-01") -> tuple:
    """A synthetic result row shaped like lel_query's SELECT list."""
    return (
        f"evt-{tag}", date, "career", f"synthetic-{tag}", "career/x",
        "yes", "Mercury", "Jupiter", "[]", 1.0, "synthetic-citation",
    )


class FakeConn:
    """
    In-memory stand-in for the psycopg connection `_get_conn()` returns.

    It stores two charts' rows and evaluates the SQL it is actually handed: if the
    SQL carries the `le.chart_id = %s::UUID` predicate it returns only the rows of
    the chart bound as the FIRST parameter; if the predicate is absent it returns
    every chart's rows (i.e. it behaves like the real table would).
    """

    def __init__(self) -> None:
        self.rows_by_chart = {
            CHART_A: [_row("a1"), _row("a2", "2021-02-02")],
            CHART_B: [_row("b1"), _row("b2", "2022-03-03"), _row("b3", "2023-04-04")],
        }
        self.issued: list[tuple[str, list[Any]]] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def _visible(self, sql: str, params: list[Any]) -> list[tuple]:
        if _PREDICATE.search(sql):
            return list(self.rows_by_chart.get(params[0], []))
        return [r for rows in self.rows_by_chart.values() for r in rows]

    def execute(self, sql: str, params: Any = None):
        params = list(params or [])
        self.issued.append((sql, params))
        visible = self._visible(sql, params)
        is_count = "COUNT(*)" in sql

        class _Result:
            def fetchall(_self):
                return [] if is_count else visible

            def fetchone(_self):
                return (len(visible),) if is_count else None

        return _Result()


def _run(**kwargs) -> tuple[dict, FakeConn]:
    conn = FakeConn()
    with patch.object(mod, "_get_conn", return_value=conn):
        return mod.lel_query(**kwargs), conn


# ── 1. refusal ────────────────────────────────────────────────────────────────

REFUSED = [
    pytest.param(None, id="None"),
    pytest.param("", id="empty"),
    pytest.param("   ", id="whitespace"),
    pytest.param("\t\n", id="whitespace-ctl"),
    pytest.param("not-a-uuid", id="malformed"),
    pytest.param("11111111-1111-4111-8111-11111111111", id="short-uuid"),
    pytest.param(CHART_A + "\n", id="trailing-newline"),
    pytest.param(" " + CHART_A, id="leading-space"),
    pytest.param("1' OR '1'='1", id="sql-ish"),
    pytest.param(12345, id="non-str-int"),
]


class TestRefusal:
    @pytest.mark.parametrize("bad", REFUSED)
    def test_bad_chart_id_raises_and_never_touches_db(self, bad):
        def _boom():
            raise AssertionError("DB must not be opened for a refused chart_id")

        with patch.object(mod, "_get_conn", side_effect=_boom):
            with pytest.raises(ValueError):
                mod.lel_query(chart_id=bad)

    def test_omitted_chart_id_raises_and_never_touches_db(self):
        def _boom():
            raise AssertionError("DB must not be opened when chart_id is omitted")

        with patch.object(mod, "_get_conn", side_effect=_boom):
            with pytest.raises(ValueError):
                mod.lel_query()
            with pytest.raises(ValueError):
                mod.lel_query(domain="career", limit=10)

    def test_refused_even_with_other_filters_present(self):
        with patch.object(mod, "_get_conn", side_effect=AssertionError("no DB")):
            with pytest.raises(ValueError):
                mod.lel_query(domain="career", date_from="2020-01-01", limit=5, chart_id=None)


# ── 2. + 3. scoping ───────────────────────────────────────────────────────────

class TestScoping:
    def test_chart_a_gets_only_chart_a_rows(self):
        result, _ = _run(chart_id=CHART_A)
        ids = {e["event_id"] for e in result["events"]}
        assert ids == {"evt-a1", "evt-a2"}
        assert result["total_count"] == 2

    def test_chart_b_gets_only_chart_b_rows(self):
        result, _ = _run(chart_id=CHART_B)
        ids = {e["event_id"] for e in result["events"]}
        assert ids == {"evt-b1", "evt-b2", "evt-b3"}
        assert result["total_count"] == 3

    def test_unknown_valid_chart_returns_nothing_not_everything(self):
        other = "33333333-3333-4333-8333-333333333333"
        result, _ = _run(chart_id=other)
        assert result["events"] == []
        assert result["total_count"] == 0

    def test_every_issued_statement_carries_chart_predicate(self):
        _, conn = _run(chart_id=CHART_A, domain="career", date_from="2019-01-01",
                       date_to="2024-01-01", limit=7)
        assert len(conn.issued) == 2, "expected the row query and the count query"
        for sql, params in conn.issued:
            assert _PREDICATE.search(sql), f"statement lacks chart_id predicate: {sql[:80]!r}"
            assert params[0] == CHART_A, "chart_id must be the first bound parameter"
            assert "WHERE" in sql

    def test_predicate_present_with_no_other_filters(self):
        _, conn = _run(chart_id=CHART_B)
        for sql, params in conn.issued:
            assert _PREDICATE.search(sql)
            assert params[:1] == [CHART_B]

    def test_filter_applied_echoes_chart_id(self):
        result, _ = _run(chart_id=CHART_A)
        assert result["filter_applied"]["chart_id"] == CHART_A

    def test_uppercase_uuid_accepted(self):
        result, _ = _run(chart_id=CHART_A.upper())
        assert result["total_count"] in (0, 2)  # accepted, not refused


# ── 4. HTTP route ─────────────────────────────────────────────────────────────

def _client():
    pytest.importorskip("httpx")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    if mod.router is None:  # pragma: no cover
        pytest.skip("fastapi router unavailable")
    app = FastAPI()
    app.include_router(mod.router, prefix="/brahma/mimamsa")
    return TestClient(app)


class TestHttpRoute:
    URL = "/brahma/mimamsa/lel_query"

    @pytest.mark.parametrize(
        "body",
        [
            {},
            {"domain": "career"},
            {"chart_id": None},
            {"chart_id": ""},
            {"chart_id": "   "},
            {"chart_id": "not-a-uuid"},
        ],
        ids=["empty-body", "no-chart", "null", "empty", "whitespace", "malformed"],
    )
    def test_route_refuses_bad_chart_id_with_4xx(self, body):
        client = _client()
        with patch.object(mod, "_get_conn", side_effect=AssertionError("no DB")):
            r = client.post(self.URL, json=body)
        assert 400 <= r.status_code < 500, (r.status_code, r.text[:200])

    def test_route_valid_chart_returns_only_its_rows(self):
        client = _client()
        conn = FakeConn()
        with patch.object(mod, "_get_conn", return_value=conn):
            r = client.post(self.URL, json={"chart_id": CHART_B})
        assert r.status_code == 200
        ids = {e["event_id"] for e in r.json()["events"]}
        assert ids == {"evt-b1", "evt-b2", "evt-b3"}
        assert all(_PREDICATE.search(sql) for sql, _ in conn.issued)

    def test_route_schema_marks_chart_id_required(self):
        client = _client()
        schema = client.app.openapi()["components"]["schemas"]["_LelQueryRequest"]
        assert "chart_id" in schema.get("required", [])


# ── 5. CLI + gate ─────────────────────────────────────────────────────────────

class TestCli:
    def _main(self, argv: list[str]):
        with patch.object(sys, "argv", ["lel_intake", *argv]):
            mod.main()

    def test_cli_query_requires_chart_id(self, capsys):
        with patch.object(mod, "_get_conn", side_effect=AssertionError("no DB")):
            with pytest.raises(SystemExit) as ei:
                self._main(["query"])
        assert ei.value.code != 0
        assert "--chart-id" in capsys.readouterr().err

    def test_cli_query_with_chart_id_is_scoped(self, capsys):
        conn = FakeConn()
        with patch.object(mod, "_get_conn", return_value=conn):
            self._main(["query", "--chart-id", CHART_A])
        out = capsys.readouterr().out
        assert "evt-a1" in out and "evt-b1" not in out
        assert all(_PREDICATE.search(sql) for sql, _ in conn.issued)

    def test_cli_query_rejects_malformed_chart_id(self):
        with patch.object(mod, "_get_conn", side_effect=AssertionError("no DB")):
            with pytest.raises(ValueError):
                self._main(["query", "--chart-id", "nope"])

    def test_cli_gate_requires_chart_id(self, capsys):
        with patch.object(mod, "_get_conn", side_effect=AssertionError("no DB")):
            with pytest.raises(SystemExit) as ei:
                self._main(["gate"])
        assert ei.value.code != 0

    def test_gate_refuses_missing_or_bad_chart_id(self):
        with patch.object(mod, "_get_conn", side_effect=AssertionError("no DB")):
            for bad in (None, "", "  ", "bad"):
                with pytest.raises(ValueError):
                    mod.run_acceptance_gate(chart_id=bad)

    def test_gate_count_queries_are_chart_scoped(self):
        issued: list[tuple[str, list[Any]]] = []

        class _GateConn:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def execute(self, sql, params=None):
                issued.append((sql, list(params or [])))

                class _R:
                    def fetchone(_s):
                        return (57,)

                    def fetchall(_s):
                        return []

                return _R()

        with patch.object(mod, "_get_conn", return_value=_GateConn()):
            with patch.object(mod, "lel_query", return_value={"events": [{"x": 1}]}) as lq:
                mod.run_acceptance_gate(chart_id=CHART_A)
        assert issued, "gate issued no SQL"
        for sql, params in issued:
            assert "chart_id" in sql, f"gate statement not chart-scoped: {sql[:90]!r}"
            assert CHART_A in params
        for call in lq.call_args_list:
            assert call.kwargs.get("chart_id") == CHART_A


# ── 6. L5 wrapper ─────────────────────────────────────────────────────────────

class TestL5Wrapper:
    def test_l5_wrapper_refuses_missing_chart_id(self):
        from brahmagyan.mimamsa import l5_lel_intake as l5

        with patch.object(mod, "_get_conn", side_effect=AssertionError("no DB")):
            with pytest.raises(ValueError):
                l5.lel_query()
            with pytest.raises(ValueError):
                l5.lel_query(chart_id="")
