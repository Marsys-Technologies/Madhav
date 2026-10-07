"""Database oracles for the candidate replacement boundary.

The temporary table shadows the future read-model table; no persistent row is
changed. The test refuses any DSN other than the campaign's local PostgreSQL.
"""

import pytest

from services.kala_core.idempotency import replace_candidate_partition


@pytest.fixture(autouse=True)
def kala_darshana_table(conn):
    conn.execute(
        "CREATE TEMP TABLE kala_darshana ("
        " chart_id text NOT NULL, generation text NOT NULL,"
        " event_class text NOT NULL, assertion text NOT NULL,"
        " PRIMARY KEY (chart_id, generation, event_class, assertion))"
    )


def _row(chart, generation, event_class, assertion):
    return {
        "chart_id": chart,
        "generation": generation,
        "event_class": event_class,
        "assertion": assertion,
    }


def _rows(conn):
    return conn.execute(
        "SELECT chart_id, generation, event_class, assertion FROM kala_darshana "
        "ORDER BY chart_id, generation, event_class, assertion"
    ).fetchall()


def test_replace_only_requested_chart_generation_and_grain(conn):
    old = [
        _row("chart-a", "g1", "career", "old"),
        _row("chart-a", "g1", "health", "keep-grain"),
        _row("chart-a", "g2", "career", "keep-generation"),
        _row("chart-b", "g1", "career", "keep-chart"),
    ]
    for row in old:
        replace_candidate_partition(
            conn, "kala_darshana", row["chart_id"], row["generation"],
            ("event_class", row["event_class"]), [row],
        )
    replacement = _row("chart-a", "g1", "career", "new")
    assert replace_candidate_partition(
        conn, "kala_darshana", "chart-a", "g1", ("event_class", "career"),
        [replacement],
    ) == 1
    assert _rows(conn) == [
        ("chart-a", "g1", "career", "new"),
        ("chart-a", "g1", "health", "keep-grain"),
        ("chart-a", "g2", "career", "keep-generation"),
        ("chart-b", "g1", "career", "keep-chart"),
    ]


def test_empty_result_clears_only_the_requested_partition(conn):
    for event_class in ("career", "health"):
        row = _row("chart-a", "g1", event_class, "old")
        replace_candidate_partition(
            conn, "kala_darshana", "chart-a", "g1", ("event_class", event_class), [row],
        )
    assert replace_candidate_partition(
        conn, "kala_darshana", "chart-a", "g1", ("event_class", "career"), [],
    ) == 0
    assert _rows(conn) == [("chart-a", "g1", "health", "old")]


def test_bad_scope_refuses_before_delete(conn):
    row = _row("chart-a", "g1", "career", "old")
    replace_candidate_partition(
        conn, "kala_darshana", "chart-a", "g1", ("event_class", "career"), [row],
    )
    with pytest.raises(ValueError, match="outside the candidate"):
        replace_candidate_partition(
            conn, "kala_darshana", "chart-a", "g1", ("event_class", "career"),
            [_row("chart-a", "g2", "career", "bad")],
        )
    with pytest.raises(ValueError, match="outside the requested grain"):
        replace_candidate_partition(
            conn, "kala_darshana", "chart-a", "g1", ("event_class", "career"),
            [_row("chart-a", "g1", "health", "bad")],
        )
    with pytest.raises(ValueError, match="not a replaceable"):
        replace_candidate_partition(conn, "kala_issued_forecasts", "chart-a", "g1", None, [])
    assert _rows(conn) == [("chart-a", "g1", "career", "old")]
