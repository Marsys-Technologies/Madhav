"""test_keyed_fake_presence.py: the Ldgr.source_presence EXISTENCE read of a very large table, read KEYED, proven with a FAKE psql runner (no database is started).

ga_dashas' row-level source (citation_human) is read by existence because the table is large; that single statement (any row, any judged row, up to 3 rows lacking a source, any row naming one) timed out, so
the cell read NO_DETECTOR. For a table with more than KEYED_READ_MIN_ROWS rows in scope the SAME statement now runs once per partition of the leading index key. The partition answers combine as the
whole-table answer would: any_row / judged / sourced / excepted are OR-ed, the lacking sample is the first rows found. PASS still needs EVERY partition clean.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _keyed_fake as kfk  # noqa: E402
import _keyed_fixture as kf  # noqa: E402
import test_n151_ldgr_source as n  # noqa: E402

PASS, FAIL, PARTIAL, NO_DET, ERRORED = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.ERRORED
LDGR = "Ldgr.source_presence"
SRC = n._row(dict(column="c", kinds=["K1"]), citation_state="sourced")
PRED = ac._ldgr_lacking("c", "text")


def presence_handler(db, sql, key, sel):
    d = dict(any_row=any(p["n"] > 0 for p in sel), judged=any(p.get("judged", True) for p in sel), lacking=[x for p in sel for x in p.get("lacking", [])][:ac.LDGR_SAMPLE_LIMIT],
             sourced=any(p.get("sourced", True) for p in sel), has_keys="'has_keys',true" in sql)
    if "'excepted'" in sql:
        d["excepted"] = any(p.get("excepted", False) for p in sel)
    if key is not db.ALL:
        d["n"] = sel[0].get("read_n", sel[0]["n"])
    return json.dumps(d)


@pytest.fixture(autouse=True)
def _clean():
    ac.set_read_scope(None)
    ac.end_asset_read_budget()
    yield
    ac.set_read_scope(None)
    ac.end_asset_read_budget()


def parts3(**plants):
    p = {"1": kfk.clean(40000), "2": kfk.clean(40000), "3": kfk.clean(40000)}
    for k, v in plants.items():
        p[k.lstrip("p")].update(v)
    return p


def make(monkeypatch, parts=None, **kw):
    db = kfk.FakeKeyedDB(parts or parts3(), **kw)
    db.on("'any_row'", presence_handler).on("pg_attribute", lambda d, sql, key, sel: json.dumps({"c": "text"}), partition_reads=False)
    return db.install(monkeypatch)


def stats(**kw):
    return ac.source_read_stats("t", PRED, ["id"], exc=kw.get("exc"))


def whole(monkeypatch, **kw):
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 10 ** 9)
    try:
        return stats(**kw)
    finally:
        monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 100_000)


def test_clean_keyed_equals_clean_whole(monkeypatch):
    db = make(monkeypatch)
    keyed = stats()
    assert keyed == whole(monkeypatch) and keyed["lacking_at_least"] == 0 and keyed["any_row"] and keyed["judged"] and keyed["sourced"] and keyed["exact"] is False
    assert len(db.partition_statements("'any_row'")) == 3 and len(db.whole_statements("'any_row'")) == 1
    assert all("'n'" in s for s in db.partition_statements("'any_row'"))


@pytest.mark.parametrize("where", ["1", "2", "3"])
def test_a_lacking_row_in_any_partition_is_a_partial_exactly_as_whole(monkeypatch, where):
    make(monkeypatch, parts3(**{"p" + where: dict(lacking=[{"id": 77}])}))
    keyed = stats()
    assert keyed == whole(monkeypatch) and keyed["lacking_at_least"] == 1 and keyed["sample"] == [{"id": 77}] and keyed["sourced"] is True


def test_no_row_naming_a_source_anywhere_is_the_fail_reading(monkeypatch):
    make(monkeypatch, {k: dict(v, lacking=[{"id": int(k)}], sourced=False) for k, v in parts3().items()})
    keyed = stats()
    assert keyed == whole(monkeypatch) and keyed["sourced"] is False and keyed["lacking_at_least"] == 1
    assert ac.grade_ldgr_source_presence(dict(source_column="c", citation_state="sourced"), keyed, "t")["v"] == FAIL


def test_the_sample_is_bounded_and_the_excepted_flag_is_or_ed(monkeypatch):
    make(monkeypatch, parts3(p1=dict(lacking=[{"id": i} for i in range(5)]), p3=dict(excepted=True)))
    exc = '("tier")::text = \'p\''
    keyed = stats(exc=exc)
    assert keyed == whole(monkeypatch, exc=exc) and len(keyed["sample"]) == ac.LDGR_SAMPLE_LIMIT and keyed["excepted"] is True


def test_a_pass_needs_every_partition_a_timed_out_one_is_never_a_pass(monkeypatch):
    db = make(monkeypatch, parts3(p2=dict(timeout=True)))
    with pytest.raises(ac.KeyedReadIncomplete) as ei:
        stats()
    msg = str(ei.value)
    assert "covered 2 of 3 partition(s) (80000 of 120000 rows)" in msg and "partition (2) timed out" in msg and "statement timeout" not in msg and "t (existence read)" in msg.replace("t.source", "t")
    assert len(db.partition_statements("'any_row'")) == 3


def test_a_finding_with_a_source_elsewhere_stands_even_when_a_later_partition_timed_out(monkeypatch):
    make(monkeypatch, parts3(p1=dict(lacking=[{"id": 1}]), p3=dict(timeout=True)))
    got = stats()
    assert got["lacking_at_least"] == 1 and got["sourced"] is True       # the PARTIAL reading is decided by what was read: another partition cannot undo it


def test_a_lack_without_a_known_source_cannot_decide_fail_versus_partial_if_a_partition_is_unread(monkeypatch):
    make(monkeypatch, parts3(p1=dict(lacking=[{"id": 1}], sourced=False), p2=dict(timeout=True), p3=dict(sourced=False)))
    with pytest.raises(ac.KeyedReadIncomplete):
        stats()


def test_counts_that_do_not_add_up_are_unread_and_no_partition_is_read(monkeypatch):
    db = make(monkeypatch)
    db.groups_lie = 3
    with pytest.raises(ac.KeyedReadIncomplete, match="not trusted"):
        stats()
    assert db.partition_statements("'any_row'") == []


def test_a_partition_that_changed_under_the_read_is_unread(monkeypatch):
    make(monkeypatch, parts3(p3=dict(read_n=39999)))
    with pytest.raises(ac.KeyedReadIncomplete, match=r"partition \(3\) holds 39999 row\(s\), the plan counted 40000"):
        stats()


def test_the_asset_budget_running_out_is_unread(monkeypatch):
    db = make(monkeypatch)
    clock = kf.Clock()
    monkeypatch.setattr(ac, "_chunk_clock", clock)
    real = ac.scalar

    def slow(sql):
        if "'any_row'" in sql and '"a" = ' in sql:
            clock.t += 50
        return real(sql)
    monkeypatch.setattr(ac, "scalar", slow)
    ac.begin_asset_read_budget(total_secs=60)
    with pytest.raises(ac.KeyedReadIncomplete, match="covered 2 of 3.*1 partition\\(s\\) not reached.*60s ran out"):
        stats()


# ───────────────────────────── routing, and the cell the grader writes ─────────────────────────────

def test_below_the_threshold_the_older_whole_table_existence_read_is_the_function_called(monkeypatch):
    db = make(monkeypatch, est=100_000)
    called = []
    real = ac.source_fetch_presence
    monkeypatch.setattr(ac, "source_fetch_presence", lambda *a, **k: called.append((a, k)) or real(*a, **k))
    monkeypatch.setattr(ac, "keyed_read", lambda *a, **k: (_ for _ in ()).throw(AssertionError("keyed reader below the threshold")))
    db.est = 249_999                                                       # (below LDGR_CHEAP_MIN_ROWS the exact read runs first)
    db.on("'rows',count(*)", lambda d, sql, key, sel: json.dumps(dict(rows=10, lacking=0, sample=[])))
    got = stats()
    assert got["rows"] == 10 and called == []                              # est <= threshold on a small table: the exact read answered, exactly as before
    db.est = 100_000
    monkeypatch.setattr(ac, "LDGR_CHEAP_MIN_ROWS", 50_000)                 # now the existence read runs: est 100 000 is not MORE than the threshold
    got = stats()
    assert len(called) == 1 and called[0][1].get("part") is None and not any("pg_index" in s for s in db.calls)


def test_the_exact_read_timing_out_on_a_large_table_falls_to_the_keyed_existence_read(monkeypatch):
    db = make(monkeypatch, est=200_000)                                    # above the keyed threshold, below LDGR_CHEAP_MIN_ROWS: the exact read is tried first
    state = {"exact": 0}

    def exact(d, sql, key, sel):
        state["exact"] += 1
        raise ac.Unknown(kfk.TIMEOUT)
    db.on("'rows',count(*)", exact)
    got = stats()
    assert state["exact"] == 1 and got["exact"] is False and got["why_cheap"] == "the exact row count exceeded the statement timeout"
    assert len(db.partition_statements("'any_row'")) == 3


def _check(monkeypatch, db):
    return ac.source_declared_check("x", SRC, "t", ["id", "c"], rows=10, keys=[["id"]])[LDGR]


def test_the_cell_is_the_same_pass_keyed_as_whole_with_the_same_wording(monkeypatch):
    make(monkeypatch)
    keyed = _check(monkeypatch, None)
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 10 ** 9)
    ref = _check(monkeypatch, None)
    assert keyed["v"] == PASS and keyed == ref


def test_the_cell_is_the_same_partial_keyed_as_whole_with_the_same_wording(monkeypatch):
    make(monkeypatch, parts3(p2=dict(lacking=[{"id": 9}])))
    keyed = _check(monkeypatch, None)
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 10 ** 9)
    ref = _check(monkeypatch, None)
    assert keyed["v"] == PARTIAL and keyed == ref and "at least 1 row lacks one and at least 1 row names one" in keyed["measured"]


def test_the_cell_of_an_incomplete_read_is_no_detector_with_the_coverage_text(monkeypatch):
    make(monkeypatch, parts3(p2=dict(timeout=True)))
    rec = _check(monkeypatch, None)
    assert rec["v"] == NO_DET and rec["v"] not in (PASS, ERRORED) and rec["declared"] is True
    t = rec["measured"]
    assert t.startswith("NO_DETECTOR") and "covered 2 of 3 partition(s) (80000 of 120000 rows)" in t and "neither a PASS nor a FAIL" in t
    assert rec["source"]["read"] == "existence" and rec["source"]["keyed"] is True


def test_untrusted_counts_read_no_detector_not_errored(monkeypatch):
    db = make(monkeypatch)
    db.groups_lie = 2
    rec = _check(monkeypatch, db)
    assert rec["v"] == NO_DET and "not trusted" in rec["measured"]


def test_any_other_failure_is_still_errored(monkeypatch):
    db = make(monkeypatch)
    db.on("'any_row'", lambda d, sql, key, sel: (_ for _ in ()).throw(ac.Unknown("ERROR:  permission denied for table t")))
    db.handlers.reverse()
    rec = _check(monkeypatch, db)
    assert rec["v"] == ERRORED and "permission denied" in rec["measured"]


def test_the_statement_without_a_partition_is_unchanged():
    a = ac.source_presence_sql("t", PRED, ["id"], None)
    assert a == ac.source_presence_sql("t", PRED, ["id"], None, None) and "'n'" not in a
    b = ac.source_presence_sql("t", PRED, ["id"], None, ac.KeyedPartition(("a",), ("1",), 5))
    assert "\"a\" = '1'" in b and "'n'," in b and b.count("EXISTS") == a.count("EXISTS")
