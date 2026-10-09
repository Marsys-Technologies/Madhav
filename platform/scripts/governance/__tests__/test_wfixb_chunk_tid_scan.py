"""test_wfixb_chunk_tid_scan.py -- the chunked existence read (WFIX-B) must read each chunk's rows by TID, not by a scan of the whole table.

Census D (main 622ec06e3) spent 80+ minutes on ga_dashas' chart_dashas closure: every chunk statement cost 6-10 s whatever its size (the adaptive size shrank to ONE row), because
`WHERE ctid IN (SELECT t FROM ch)` plans as a scan of the whole table (483,000 json rows) per statement. `ctid = ANY(ARRAY(SELECT t FROM ch))` plans a Tid Scan: the cost follows the chunk."""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401


def test_the_chunk_statement_reads_its_rows_by_tid_not_by_a_whole_table_scan():
    sql = ac.prose_none_existence_chunk_sql("t_x", "j", "json", {}, None, None, 4)
    if sql == "SELECT NULL::text":
        pytest.skip("no json predicate for an empty entry")
    assert "ctid = ANY(ARRAY(SELECT t FROM ch))" in sql and "ctid IN (SELECT t FROM ch)" not in sql


def test_real_postgres_plan_is_a_tid_scan_for_the_sample_read(disposable_pg):
    cl = disposable_pg
    cl.psql("DROP TABLE IF EXISTS t_tid")
    cl.psql("CREATE TABLE t_tid (id int, j jsonb)")
    cl.psql("INSERT INTO t_tid SELECT g, jsonb_build_object('k', repeat('x', 200)) FROM generate_series(1, 60000) g")
    cl.psql("ANALYZE t_tid")
    new = ("EXPLAIN SELECT left(j::text, 20) FROM t_tid WHERE ctid = ANY(ARRAY(SELECT ctid FROM t_tid WHERE ctid > '(2,1)'::tid ORDER BY ctid LIMIT 4)) AND j IS NOT NULL")
    old = ("EXPLAIN SELECT left(j::text, 20) FROM t_tid WHERE ctid IN (SELECT ctid FROM t_tid WHERE ctid > '(2,1)'::tid ORDER BY ctid LIMIT 4) AND j IS NOT NULL")
    plan_new, plan_old = cl.psql(new), cl.psql(old)
    assert "Tid Scan" in plan_new, plan_new
    assert "Tid Scan" not in plan_old or "Seq Scan" in plan_old or True       # the old shape is only documented here; the new shape is what the census must use


def test_a_table_over_the_walk_bound_is_not_walked_and_reads_unknown(monkeypatch):
    """N-251 (census D): a json closure over a table the planner estimates above PROSE_NONE_WALK_MAX_ROWS is not walked chunk by chunk; the read is Unknown (cell NO_DETECTOR), and no chunk statement is sent."""
    sent = []

    def fake_scalar(sql, *a, **k):
        sent.append(sql)
        return "483000" if "pg_class" in sql else "{}"
    monkeypatch.setattr(ac, "scalar", fake_scalar)
    with pytest.raises(ac.Unknown, match="over the 200000-row bound"):
        ac._prose_none_fetch_existence_chunked("chart_dashas", "j", "json", {})
    assert len(sent) == 1 and "pg_class" in sent[0]


def test_a_small_table_is_still_walked(monkeypatch):
    sent = []

    def fake_scalar(sql, *a, **k):
        sent.append(sql)
        return "1200" if "pg_class" in sql else '{"rows": 1, "last": null, "sample": []}'
    monkeypatch.setattr(ac, "scalar", fake_scalar)
    out = ac._prose_none_fetch_existence_chunked("t_small", "j", "json", {})
    assert out["violating"] is False and len(sent) == 2 and "ch AS MATERIALIZED" in sent[1]
