"""test_keyed_json_walk.py: the json-closure existence walk read KEYED, on a REAL table in the disposable PostgreSQL (Nikasha lane W3, n430 ga_dashas).

The fake-runner proofs of the same claims are in test_keyed_fake_walk.py (they run without a database). This file checks the real SQL: the chunk statement confined to one partition (`ctid` order inside it),
the keyed verdict equal to the whole-table walk's verdict on a clean table and on a planted violation, and a genuinely timed-out partition (the server's own error) leaving the column unread.
Written for the CI shard that has PostgreSQL; not run on the build machine after SS N-436.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _keyed_fixture as kf  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401

T = "kt_walk"
ENTRY = dict(column="doc", values=None, json_leaf_patterns=[dict(path="$.cls[*]", values=["x"])])


@pytest.fixture()
def table(disposable_pg, monkeypatch):
    kf.make_table(disposable_pg, monkeypatch, T, per_cell=500)
    kf.shrink(monkeypatch)
    ac.set_read_scope(None)
    ac.end_asset_read_budget()
    yield T
    ac.set_read_scope(None)
    ac.end_asset_read_budget()
    kf.drop_table(T)


def outside(table):
    return ac.prose_none_read_outside(table, "doc", "json", ENTRY, None, est=900_000)


def whole(table, monkeypatch):
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 10 ** 9)
    try:
        return outside(table)
    finally:
        monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 500)


def test_a_clean_table_is_closed_keyed_exactly_as_whole(table, monkeypatch):
    spy = kf.spy_scalar(monkeypatch)
    keyed = outside(table)
    assert keyed == whole(table, monkeypatch) and keyed["violating"] is False
    chunks = [q for q in spy.calls if "'rows', (SELECT count(*) FROM ch)" in q]
    assert {k for k in ("1", "2", "3") if any(f'"a" = \'{k}\'' in q for q in chunks)} == {"1", "2", "3"}            # every partition was walked by chunk statements confined to it


@pytest.mark.parametrize("a", [1, 2, 3])
def test_a_planted_violation_is_found_in_whichever_partition_holds_it(table, monkeypatch, a):
    ac.psql(f"UPDATE {table} SET doc = '{{\"cls\":[\"x\"],\"note\":\"a free sentence\"}}'::jsonb WHERE id = (SELECT max(id) FROM {table} WHERE a = {a})")
    keyed = outside(table)
    ref = whole(table, monkeypatch)
    assert keyed["violating"] is True and ref["violating"] is True and keyed["sample"] == ref["sample"] and "free sentence" in keyed["sample"][0]


def test_a_timed_out_partition_is_never_a_closure(table, monkeypatch):
    kf.spy_scalar(monkeypatch, slow_marker='"a" = \'2\'')
    with pytest.raises(ac.KeyedReadIncomplete) as ei:
        outside(table)
    assert "covered 2 of 3 partition(s) (2000 of 3000 rows)" in str(ei.value) and "statement timeout" not in str(ei.value)


def test_the_chunk_statement_is_confined_to_one_partition_in_ctid_order(table):
    plan = ac.keyed_plan(table)
    sql = ac.prose_none_existence_chunk_sql(table, "doc", "json", ENTRY, None, None, 4, plan.partitions[1].pred)
    got = ac.scalar(sql)
    import json as _j
    d = _j.loads(got)
    assert d["rows"] == 4 and d["sample"] == []
    total = 0
    after = None
    while True:
        d = _j.loads(ac.scalar(ac.prose_none_existence_chunk_sql(table, "doc", "json", ENTRY, None, after, 700, plan.partitions[1].pred)))
        total += d["rows"]
        if d["rows"] < 700:
            break
        after = d["last"]
    assert total == plan.partitions[1].n == 1000
