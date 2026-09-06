"""
test_ga_tajaka_f_e19_trirashipathi_order.py — F-E19 (L1_W1_ANALYSIS_BATCH_E.md, NOW,
§N.7 item 2).

`_read_trirashipathi` used `LIMIT 1` with no `ORDER BY` -- pinned fact_category + fact_key
(so the CI fact-category-pin lint passed) but the ordering half of the D1 defect class was
absent. Reproducible today only because every (chart, ayanamsha) currently has exactly
1 row/1 build (verified live: 15/15 combinations, count=1/builds=1/distinct_vals=1) -- not
because the query itself was deterministic. A future build with >1 row per key would have
silently picked one at random.

Also: a zero-row result (no exception, just an absent row) was swallowed to None with
NOTHING logged, degrading candidate_lord_jsonb scoring with no trace -- distinct from the
already-logged exception path.

DB-free: mocks `conn.execute`/`cursor.fetchone`, no real DB connection.
"""
from __future__ import annotations

import logging
import pathlib
import sys
from unittest.mock import MagicMock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from ga_writers.ga_tajaka_writer import _read_trirashipathi  # noqa: E402


def _conn_returning_row(row):
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.return_value = row
    conn.execute.return_value = cur
    return conn, cur


def test_query_now_carries_a_total_order_by_fact_id():
    conn, cur = _conn_returning_row({"fact_value_text": "MAR"})
    _read_trirashipathi(conn, "chart-1", "lahiri_chitrapaksha")
    sql = conn.execute.call_args[0][0]
    assert "ORDER BY fact_id" in sql
    assert "LIMIT 1" in sql
    # ORDER BY must come before LIMIT (a total order pinned ahead of the cutoff).
    assert sql.index("ORDER BY fact_id") < sql.index("LIMIT 1")


def test_still_returns_the_value_on_a_normal_single_row_hit():
    conn, _ = _conn_returning_row({"fact_value_text": "MAR"})
    assert _read_trirashipathi(conn, "chart-1", "lahiri_chitrapaksha") == "MAR"


def test_zero_row_result_now_logs_a_warning_instead_of_silently_swallowing(caplog):
    conn, _ = _conn_returning_row(None)
    with caplog.at_level(logging.WARNING):
        result = _read_trirashipathi(conn, "chart-1", "raman")
    assert result is None
    assert any("no tajik_triraashipathi/lord row found" in rec.message for rec in caplog.records)
    assert any("chart-1" in rec.message and "raman" in rec.message for rec in caplog.records)


def test_exception_path_still_logs_and_returns_none(caplog):
    conn = MagicMock()
    conn.execute.side_effect = RuntimeError("connection lost")
    with caplog.at_level(logging.WARNING):
        result = _read_trirashipathi(conn, "chart-1", "lahiri_chitrapaksha")
    assert result is None
    assert any("trirashipathi read failed" in rec.message for rec in caplog.records)
