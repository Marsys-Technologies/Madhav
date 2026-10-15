"""test_keyed_source_presence.py: the Ldgr.source_presence existence read read KEYED, on a REAL table in the disposable PostgreSQL (Nikasha lane W3, n430 ga_dashas citation_human).

The fake-runner proofs of the same claims are in test_keyed_fake_presence.py (they run without a database). This file checks the real SQL: the per-partition statement (every sub-select confined to one
partition, plus the partition's own count), the keyed answer equal to the whole-table answer on a clean table, a table with a lacking row and a table with no sourced row, and a genuinely timed-out
partition (the server's own error). Written for the CI shard that has PostgreSQL; not run on the build machine after SS N-436.
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

T = "kt_src"
PRED = ac._ldgr_lacking("citation_human", "text")


@pytest.fixture()
def table(disposable_pg, monkeypatch):
    kf.make_table(disposable_pg, monkeypatch, T, per_cell=500)
    kf.shrink(monkeypatch)
    monkeypatch.setattr(ac, "LDGR_CHEAP_MIN_ROWS", 1000)                   # the 3000-row table is 'large' for the existence read as well
    ac.set_read_scope(None)
    ac.end_asset_read_budget()
    yield T
    ac.set_read_scope(None)
    ac.end_asset_read_budget()
    kf.drop_table(T)


def keyed(table):
    return ac.source_read_stats(table, PRED, ["id"])


def whole(table, monkeypatch):
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 10 ** 9)
    try:
        return ac.source_read_stats(table, PRED, ["id"])
    finally:
        monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 500)


def test_a_clean_table_reads_the_same_keyed_as_whole(table, monkeypatch):
    spy = kf.spy_scalar(monkeypatch)
    got = keyed(table)
    assert got == whole(table, monkeypatch) and got["lacking_at_least"] == 0 and got["sourced"] is True
    part_stmts = [s for s in spy.calls if "'any_row'" in s and '"a" = ' in s]
    assert len(part_stmts) == 3 and all("'n'," in s for s in part_stmts)


@pytest.mark.parametrize("a", [1, 2, 3])
def test_a_row_lacking_a_source_in_any_partition_is_the_same_partial(table, monkeypatch, a):
    ac.psql(f"UPDATE {table} SET citation_human = NULL WHERE id = (SELECT max(id) FROM {table} WHERE a = {a})")
    got = keyed(table)
    ref = whole(table, monkeypatch)
    assert got["lacking_at_least"] == ref["lacking_at_least"] == 1 and got["sourced"] is True and got["sample"] == ref["sample"] and len(got["sample"]) == 1


def test_no_row_naming_a_source_is_the_fail_reading(table, monkeypatch):
    ac.psql(f"UPDATE {table} SET citation_human = NULL")
    got = keyed(table)
    ref = whole(table, monkeypatch)
    assert got["sourced"] is False and ref["sourced"] is False and got["lacking_at_least"] == 1 and len(got["sample"]) == ac.LDGR_SAMPLE_LIMIT


def test_a_timed_out_partition_is_never_a_pass(table, monkeypatch):
    kf.spy_scalar(monkeypatch, slow_marker="'any_row'", slow_secs=2)
    with pytest.raises(ac.KeyedReadIncomplete) as ei:
        keyed(table)
    assert "covered 0 of 3 partition(s)" in str(ei.value) and "statement timeout" not in str(ei.value)
