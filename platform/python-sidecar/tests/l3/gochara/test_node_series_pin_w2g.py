"""Node-series step 1b — the `services/w2g` readers (P1 `fetch_body_series`, P2 `DbArcSource.load`)
and the W2G validators P14 (V2) / P15 (V4). Split out of the step-1 PR because `db_source.py` and the W2G validators are in the
import closure of the L0 writer `bg_gochara_arcs`: editing them moves an L0 writer digest and so needs an
L0 pins re-admission (a separate authority) — see the PR body.

Same layers and fixtures as `test_node_series_pin.py` (real PostgreSQL throwaway database with a
decoy MEAN series; recorded SQL)."""
from __future__ import annotations

import pytest

from services.w2g import db_source
from services.w2g_validations import v2_ephemeris_coverage as v2
from services.w2g_validations import v4_transition_sizing as v4
from services.w2g_validations._db import query_fn_from_conn
from services.w2g import node_series  # noqa: F401
from services.w2g.node_series import NODE_SERIES_PREDICATE, NodeSeriesError

from .test_node_series_pin import (  # noqa: F401  (node_db is a fixture)
    N_DAYS,
    _day,
    _make_pinned_series_ambiguous,
    _true_lon,
    node_db,
)


# P1 ─ w2g/db_source.fetch_body_series

@pytest.mark.parametrize("body", ["Rahu", "Ketu"])
def test_p1_fetch_body_series_reads_only_the_true_node_series(node_db, body):
    jds, lons = db_source.fetch_body_series(query_fn_from_conn(node_db), body)
    assert len(jds) == N_DAYS
    assert lons == pytest.approx([_true_lon(body, i) for i in range(N_DAYS)], abs=1e-5)


def test_p1_the_null_trap_a_non_node_body_is_not_dropped(node_db):
    """`node_mode` is NULL for Sun..Saturn: a bare `node_mode='true'` would return nothing."""
    jds, lons = db_source.fetch_body_series(query_fn_from_conn(node_db), "Sun")
    assert len(jds) == N_DAYS
    assert lons == pytest.approx([_true_lon("Sun", i) for i in range(N_DAYS)], abs=1e-5)


def test_p1_a_duplicate_date_in_the_pinned_series_fails_loudly(node_db):
    _make_pinned_series_ambiguous(node_db, _day(5), "Rahu")
    with pytest.raises(NodeSeriesError, match="Rahu"):
        db_source.fetch_body_series(query_fn_from_conn(node_db), "Rahu")


# P2 ─ w2g/db_source.DbArcSource.load

def test_p2_dbarcsource_load_fits_over_the_true_series_in_exactly_two_queries(node_db):
    jd0 = db_source.noon_ut_jd(_day(0).year, _day(0).month, _day(0).day)
    jd1 = db_source.noon_ut_jd(_day(N_DAYS - 1).year, _day(N_DAYS - 1).month, _day(N_DAYS - 1).day)
    for body in ("Sun", "Rahu"):
        direction = 1 if body == "Sun" else -1
        node_db.execute(
            "INSERT INTO bg_gochara_arcs VALUES ('9.9', %s, 0, %s, %s, %s, %s, %s, 0)",
            (body, jd0, jd1, _true_lon(body, 0), _true_lon(body, N_DAYS - 1), direction))
    src = db_source.DbArcSource(query_fn_from_conn(node_db), "9.9")
    out = src.load(["Sun", "Rahu"])
    assert src.queries_issued == 2
    # the knots are NOON-UT abscissae (db_source.noon_ut_jd), whatever the calendar helper says
    d7 = _day(7)
    mid = db_source.noon_ut_jd(d7.year, d7.month, d7.day)
    rahu_arc = out["Rahu"][0]
    assert rahu_arc.evaluator(mid) == pytest.approx(_true_lon("Rahu", 7), abs=1e-4)
    assert out["Sun"][0].evaluator(mid) == pytest.approx(_true_lon("Sun", 7), abs=1e-4)


def test_p2_a_duplicate_date_in_the_pinned_series_fails_loudly(node_db):
    _make_pinned_series_ambiguous(node_db, _day(2), "Ketu")
    node_db.execute(
        "INSERT INTO bg_gochara_arcs VALUES ('9.9', 'Ketu', 0, 1, 2, 0, 1, 1, 0)")
    with pytest.raises(NodeSeriesError, match="Ketu"):
        db_source.DbArcSource(query_fn_from_conn(node_db), "9.9").load(["Ketu"])


def test_p1_p2_recorded_statements_carry_the_pin():
    seen: list[str] = []

    def rec(sql, params=()):
        seen.append(sql)
        return [{"table_name": "ephemeris_daily"}] if "information_schema" in sql else []

    db_source.fetch_body_series(rec, "Rahu")
    db_source.DbArcSource(rec, "x").load(["Rahu"])
    ephemeris_sql = [s for s in seen if "FROM ephemeris_daily" in s]
    assert len(ephemeris_sql) == 2, ephemeris_sql      # P1, P2 knots
    literal = "(body NOT IN ('Rahu', 'Ketu') OR node_mode = 'true')"
    assert all(literal in s for s in ephemeris_sql), ephemeris_sql


# P14 ─ V2 coverage

def test_p14_v2_counts_one_row_per_date_for_the_pinned_series(node_db):
    r = v2.validate_v2_ephemeris_coverage(query_fn_from_conn(node_db))
    per_body = r.data["per_body"]
    for body in ("Rahu", "Ketu"):
        assert per_body[body]["n_rows"] == per_body[body]["n_distinct_dates"] == N_DAYS, body
        assert per_body[body]["one_row_per_date"] is True
    assert r.data["duplicate_date_bodies"] == []      # the decoy MEAN rows are not double-counted


# P15 ─ V4 transition sizing

def test_p15_v4_steps_are_counted_on_the_pinned_series_only(node_db):
    q = query_fn_from_conn(node_db)
    args = ["tropical", _day(0), _day(N_DAYS - 1)]
    variation = {r["body"]: r for r in q(v4._shortest_arc_sum_sql(), args)}
    assert {b: int(variation[b]["n_steps"]) for b in ("Sun", "Rahu", "Ketu")} == {
        "Sun": N_DAYS - 1, "Rahu": N_DAYS - 1, "Ketu": N_DAYS - 1}
    # total variation of the TRUE node is 19 days * 0.053°; the decoy would add its own
    assert float(variation["Rahu"]["total_variation_deg"]) == pytest.approx(0.053 * (N_DAYS - 1), abs=1e-4)
    stations = {r["body"]: r for r in q(v4._global_transition_sql(), args)}
    assert set(stations) >= {"Sun", "Rahu", "Ketu"}


def test_p14_recorded_statement_carries_the_pin():
    seen: list[str] = []

    def rec(sql, params=()):
        seen.append(sql)
        return [{"table_name": "ephemeris_daily"}] if "information_schema" in sql else []

    v2.validate_v2_ephemeris_coverage(rec)
    ephemeris_sql = [s for s in seen if "FROM ephemeris_daily" in s]
    assert len(ephemeris_sql) == 1, ephemeris_sql      # the P14 per-body coverage aggregate
    literal = "(body NOT IN ('Rahu', 'Ketu') OR node_mode = 'true')"
    assert literal in ephemeris_sql[0], ephemeris_sql


def test_v4_statements_carry_the_null_safe_pin():
    literal = "(body NOT IN ('Rahu', 'Ketu') OR node_mode = 'true')"
    assert literal in v4._shortest_arc_sum_sql()
    assert literal in v4._global_transition_sql()
