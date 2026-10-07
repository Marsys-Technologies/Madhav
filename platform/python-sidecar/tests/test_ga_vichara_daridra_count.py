"""
test_ga_vichara_daridra_count.py -- SS ruling N-196 (TI-prose-batch2-writers).

ga_vichara's substep writes TWO things: its chart_vichara rows, and (since #3204, `ga_daridra_postpass`) the
chart_facts dosha_label / daridra row. The substep used to return the chart_vichara count only, so the daridra row
was WRITTEN but NOT COUNTED in rows_written. It now returns chart_vichara rows + the daridra rows it wrote, and the
daridra row is bound as a literal tuple of an explicit-column INSERT (the form the writer-source scan can read).

Replay is offline, on a chart where daridra forms (the shape of test_ga_daridra_postpass.CHART: 11th lord Venus in the
8th house, a fired dhana yoga cancels it). Production: daridra forms for 1c826d5a and cb73cd3d (1 row per ayanamsha),
not for the native 482012f1.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import ga_writers.ga_daridra_postpass as pp
import ga_writers.ga_vichara_writer as gw
from test_ga_daridra_postpass import CHART as DARIDRA_CHART, DARIDRA_ENTRY
from test_ga_vichara_identity_and_asof import AYA, CHART, RUN, FakeConn, FakeCursor


class _ReplayCursor(FakeCursor):
    """FakeCursor + the three statements the post-pass issues (no database)."""

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if s.startswith("SELECT value_num, value_jsonb FROM chart_vichara"):
            self.rows = []                                           # no wealth ratification row: Ground A reads D1
        elif s.startswith("SELECT yoga_canonical_id, constituent_planets FROM ga_yoga_firings"):
            self.rows = [("dhana_yoga_house_lords", '["sun", "mercury", "venus"]')]
        elif s.startswith("SELECT fact_id FROM chart_facts WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = %s"):
            self.rows = []                                           # ga_structural's _real_fact_id_ref: no constituent facts
        elif s.startswith("INSERT INTO chart_facts"):
            self.c.daridra_inserts.append((s, params))
        else:
            super().execute(sql, params)


class _ReplayConn(FakeConn):
    def __init__(self):
        super().__init__()
        self.daridra_inserts: list[tuple] = []
        self.deletes: list[str] = []

    def cursor(self, row_factory=None):
        return _ReplayCursor(self)

    def execute(self, sql, params=None):
        self.deletes.append(" ".join(sql.split()))

        class _C:
            rowcount = 0
        return _C()


@pytest.fixture
def daridra_forms(monkeypatch):
    monkeypatch.setattr(pp._gsw, "_load_dosha_catalog", lambda conn: [DARIDRA_ENTRY])
    monkeypatch.setattr(pp._gsw, "compute_chart", lambda inputs, ayanamsha_id: DARIDRA_CHART)
    monkeypatch.setattr(pp._gsw, "_validate_chart_output_complete", lambda c: None)
    monkeypatch.setattr(pp, "authorize_chart_fact_delete", lambda *a, **k: None)


def test_rows_written_counts_the_daridra_row_when_daridra_forms(daridra_forms):
    conn = _ReplayConn()
    n = gw.build_ga_vichara_substep(CHART, RUN, AYA, conn, birth_params={"x": 1})
    assert len(conn.daridra_inserts) == 1                       # the post-pass really wrote the row ...
    assert len(conn.inserted) > 0
    assert n == len(conn.inserted) + 1                          # ... and the substep counts it: chart_vichara + daridra
    assert n != len(conn.inserted)                              # (the base returned chart_vichara only)


def test_the_daridra_row_is_bound_as_one_explicit_column_tuple(daridra_forms):
    conn = _ReplayConn()
    gw.build_ga_vichara_substep(CHART, RUN, AYA, conn, birth_params={"x": 1})
    (sql, params), = conn.daridra_inserts
    cols = [c.strip() for c in sql.split("(", 1)[1].split(")", 1)[0].split(",")]
    assert cols == pp._gsw._CF_INSERT_COLS
    assert isinstance(params, tuple) and len(params) == len(cols) == 18
    got = dict(zip(cols, params))
    assert (got["fact_category"], got["fact_subject"], got["fact_key"]) == ("dosha_label", "daridra", "dosha_name")
    assert got["chart_id"] == CHART and got["ayanamsha_id"] == AYA and got["build_id"] == RUN
    assert isinstance(got["fact_value_jsonb"], str) and '"bhanga_active": true' in got["fact_value_jsonb"]


def test_the_insert_statement_is_the_one_ga_structural_uses():
    """Same statement text as ga_structural's `_CF_INSERT_SQL`: the daridra row's ON CONFLICT / SET list cannot drift."""
    assert " ".join(pp._DARIDRA_INSERT_SQL.split()) == " ".join(pp._gsw._CF_INSERT_SQL.split())


def test_a_chart_where_daridra_does_not_form_counts_chart_vichara_only(monkeypatch):
    from test_ga8_writer import MOCK_CHART_OUTPUT
    monkeypatch.setattr(pp._gsw, "_load_dosha_catalog", lambda conn: [DARIDRA_ENTRY])
    monkeypatch.setattr(pp._gsw, "compute_chart", lambda inputs, ayanamsha_id: MOCK_CHART_OUTPUT)
    monkeypatch.setattr(pp._gsw, "_validate_chart_output_complete", lambda c: None)
    monkeypatch.setattr(pp, "authorize_chart_fact_delete", lambda *a, **k: None)
    conn = _ReplayConn()
    n = gw.build_ga_vichara_substep(CHART, RUN, AYA, conn, birth_params={"x": 1})
    assert conn.daridra_inserts == []
    assert n == len(conn.inserted)                              # the native's case: rows_written == chart_vichara rows


def test_the_post_pass_return_value_is_what_the_substep_adds(monkeypatch):
    monkeypatch.setattr(pp, "emit_daridra_label_post_pass", lambda *a, **k: 1)
    conn = FakeConn()
    assert gw.build_ga_vichara_substep(CHART, RUN, AYA, conn) == len(conn.inserted) + 1
    monkeypatch.setattr(pp, "emit_daridra_label_post_pass", lambda *a, **k: 0)
    conn = FakeConn()
    assert gw.build_ga_vichara_substep(CHART, RUN, AYA, conn) == len(conn.inserted)
