"""test_keyed_fake_walk.py: the json-closure existence walk of a very large table, read KEYED, proven with a FAKE psql runner (no database is started).

ga_dashas.concurrent_system_lords_jsonb is a json closure whose chunked walk (ctid order over the whole table) ran 28 chunks in 604 s against the 600 s per-column budget and did not reach the end. For a
table with more than KEYED_READ_MIN_ROWS rows in scope the SAME chunk walk now runs once per partition of the leading index key, under a per-ASSET time budget. The fake answers each chunk statement from planted
rows (row i of a partition has ctid (i, 1); a planted row holds a violating leaf) and each partition can be planted to time out, to hold a different number of rows than the plan counted, or to be slow.
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
import test_n150_prose_none as pn  # noqa: E402
import test_wfixb_engine as wf  # noqa: E402

ENTRY = dict(wf.ENTRY, why="a json record whose leaves are a closed id/class set")
AFTER = re.compile(r"ctid > '\((\d+),(\d+)\)'::tid")
ROWS = re.compile(r"LIMIT (\d+)\) SELECT")


def walk_handler(db, sql, key, sel):
    """One chunk of the ctid-ordered walk: the rows of the selected partition(s) after the cursor, `rows` of them; a planted bad row ({index: leaf text}) is the sample."""
    rows = [(p.get("bad") or {}).get(i) for p in sel for i in range(1, p["n"] + 1)]
    for p in sel:                                                         # the rows the PARTITION READ counts (read_n) may differ from the plan (a table that changed under the read)
        if "read_n" in p:
            rows = rows[:-p["n"]] + [None] * p["read_n"]
    m = AFTER.search(sql)
    start = int(m.group(1)) if m else 0
    want = int(ROWS.search(sql).group(1))
    chunk = rows[start:start + want]
    if db.clock is not None:
        db.clock.t += db.chunk_secs
    sample = [x for x in chunk if x is not None][:3]
    return json.dumps(dict(rows=len(chunk), last=f"({start + len(chunk)},1)" if chunk else None, sample=sample))


def make(monkeypatch, parts, **kw):
    db = kfk.FakeKeyedDB(parts, **kw).on("'rows', (SELECT count(*) FROM ch)", walk_handler).install(monkeypatch)
    db.clock, db.chunk_secs = None, 0.0
    return db


def drive_clock(monkeypatch, db, chunk_secs):
    db.clock, db.chunk_secs = kf.Clock(), chunk_secs
    monkeypatch.setattr(ac, "_chunk_clock", db.clock)
    return db.clock


@pytest.fixture(autouse=True)
def _clean():
    ac.set_read_scope(None)
    ac.end_asset_read_budget()
    yield
    ac.set_read_scope(None)
    ac.end_asset_read_budget()


def parts3(**plants):
    p = {"1": kfk.clean(300), "2": kfk.clean(300), "3": kfk.clean(300)}
    for k, v in plants.items():
        p[k.lstrip("p")].update(v)
    return p


def small_threshold(monkeypatch):
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 500)
    monkeypatch.setattr(ac, "KEYED_PARTITION_TARGET_ROWS", 10_000)


def read_outside(est=900_000):
    return ac.prose_none_read_outside("kt", "doc", "json", ENTRY, None, est=est)


# ───────────────────────────── keyed == whole (the verdict of the closure) ─────────────────────────────

def test_a_clean_table_is_shown_closed_keyed_exactly_as_the_whole_walk(monkeypatch):
    db = make(monkeypatch, parts3())
    small_threshold(monkeypatch)
    keyed = read_outside()
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 10 ** 9)                  # the same table, the older whole-table walk
    whole = read_outside()
    assert keyed == whole == dict(violating=False, sample=[], exact=False, why_cheap=keyed["why_cheap"], exact_timed_out=False)
    assert keyed["why_cheap"] == whole["why_cheap"]


def test_the_keyed_walk_runs_the_chunk_statement_inside_each_partition_only(monkeypatch):
    db = make(monkeypatch, parts3())
    small_threshold(monkeypatch)
    read_outside()
    stmts = [s for s in db.calls if "'rows', (SELECT count(*) FROM ch)" in s]
    for key in ("1", "2", "3"):
        mine = [s for s in stmts if f'"a" = \'{key}\'' in s]
        assert mine and all("ORDER BY ctid LIMIT" in s for s in mine)
    assert all('"a" = ' in s for s in stmts)                               # no chunk statement walks the whole table


@pytest.mark.parametrize("where", ["1", "2", "3"])
def test_a_planted_violating_row_in_any_partition_is_the_same_finding_as_the_whole_walk(monkeypatch, where):
    db = make(monkeypatch, parts3(**{"p" + where: dict(bad={150: "a free sentence"})}))
    small_threshold(monkeypatch)
    keyed = read_outside()
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 10 ** 9)
    whole = read_outside()
    assert keyed == whole and keyed["violating"] is True and keyed["sample"] == ["a free sentence"] and keyed["exact"] is False


def test_a_violation_ends_the_keyed_walk_at_once(monkeypatch):
    db = make(monkeypatch, parts3(p1=dict(bad={2: "free"})))
    small_threshold(monkeypatch)
    assert read_outside()["violating"] is True
    assert not any('"a" = \'2\'' in s for s in db.calls)                   # partition 2 and 3 were never read


# ───────────────────────────── soundness ─────────────────────────────

def test_a_timed_out_partition_is_never_a_closure(monkeypatch):
    db = make(monkeypatch, parts3(p2=dict(timeout=True)))
    small_threshold(monkeypatch)
    with pytest.raises(ac.KeyedReadIncomplete) as ei:
        ac.prose_none_read_outside("kt", "doc", "json", ENTRY, None, est=900_000)
    msg = str(ei.value)
    assert "covered 2 of 3 partition(s) (600 of 900 rows)" in msg and "kt.doc (json closure walk) by kt(a)" in msg and "partition (2)" in msg
    assert "statement timeout" not in msg
    assert any('"a" = \'3\'' in s for s in db.calls)                       # the partition after the failed one was still read


def test_a_violation_in_a_read_partition_beats_a_timed_out_one(monkeypatch):
    make(monkeypatch, parts3(p1=dict(timeout=True), p2=dict(bad={7: "free sentence"})))
    small_threshold(monkeypatch)
    got = read_outside()
    assert got["violating"] is True and got["sample"] == ["free sentence"]


def test_counts_that_do_not_add_up_are_unread_and_no_row_is_walked(monkeypatch):
    db = make(monkeypatch, parts3())
    db.groups_lie = 1
    small_threshold(monkeypatch)
    with pytest.raises(ac.KeyedReadIncomplete, match="not trusted"):
        read_outside()
    assert not any("'rows', (SELECT count(*) FROM ch)" in s for s in db.calls)


def test_a_partition_that_holds_a_different_number_of_rows_than_the_plan_is_unread(monkeypatch):
    make(monkeypatch, parts3(p2=dict(read_n=299)))
    small_threshold(monkeypatch)
    with pytest.raises(ac.KeyedReadIncomplete, match=r"partition \(2\) .*299 row.*plan counted 300"):
        read_outside()


def test_the_asset_budget_running_out_mid_walk_is_unread_with_the_coverage(monkeypatch):
    db = make(monkeypatch, parts3())
    small_threshold(monkeypatch)
    drive_clock(monkeypatch, db, chunk_secs=40)                           # every chunk costs 40 fake seconds
    ac.begin_asset_read_budget(total_secs=100)
    with pytest.raises(ac.KeyedReadIncomplete) as ei:
        read_outside()
    msg = str(ei.value)
    assert "covered 0 of 3 partition(s) (0 of 900 rows)" in msg and "asset read budget" in msg and "ran out" in msg


def test_two_columns_of_one_asset_share_one_budget_and_the_coverage_is_recorded(monkeypatch):
    db = make(monkeypatch, parts3())
    small_threshold(monkeypatch)
    drive_clock(monkeypatch, db, chunk_secs=1)
    b = ac.begin_asset_read_budget(total_secs=10_000)
    one = ac.prose_none_read_outside("kt", "doc", "json", ENTRY, None, est=900_000)
    two = ac.prose_none_read_outside("kt", "doc2", "json", ENTRY, None, est=900_000)
    assert one["violating"] is False and two["violating"] is False
    assert [r["what"] for r in b.reads] == ["kt.doc (json closure walk)", "kt.doc2 (json closure walk)"] and b.spent > 0
    assert b.reads[0]["rows_covered"] == 900 and b.reads[0]["complete"] is True and b.rows_covered == 1800


def test_the_budget_a_first_column_spent_is_not_given_back_to_the_second(monkeypatch):
    db = make(monkeypatch, parts3())
    small_threshold(monkeypatch)
    clock = drive_clock(monkeypatch, db, chunk_secs=1)
    b = ac.begin_asset_read_budget(total_secs=60)
    clock.t += 59                                                          # the asset already spent 59 s on its other columns
    b.charge(59)
    with pytest.raises(ac.KeyedReadIncomplete, match="ran out|covered"):
        read_outside()


# ───────────────────────────── opt-in by structure; the grader ─────────────────────────────

def test_below_the_threshold_the_older_chunked_walk_is_the_function_called(monkeypatch):
    db = make(monkeypatch, parts3(), est=100_000)
    db.on("SELECT count(*)::text FROM", lambda d, sql, key, sel: "0")        # est < 250 000: the exact count runs first, as it always did
    monkeypatch.setattr(ac, "KEYED_READ_MIN_ROWS", 100_000)
    called = []
    monkeypatch.setattr(ac, "prose_none_fetch_existence", lambda *a, **k: called.append(a) or dict(violating=False, sample=[], exact=False))
    monkeypatch.setattr(ac, "keyed_read", lambda *a, **k: (_ for _ in ()).throw(AssertionError("keyed reader below the threshold")))
    got = ac.prose_none_read_outside("kt", "doc", "json", ENTRY, None, est=100_000, exact_timed_out=True)      # the existence read is reached (the exact count timed out)
    assert len(called) == 1 and got["violating"] is False                  # est == threshold: not MORE than it, so the older chunked walk is the function called
    assert not any("pg_index" in s for s in db.calls)
    assert ac.prose_none_read_outside("kt", "doc", "json", ENTRY, None, est=100_000) == 0                    # and below 250 000 rows the exact count still runs first, unchanged


def test_a_table_with_no_partitioning_key_falls_back_to_the_older_walk(monkeypatch):
    make(monkeypatch, parts3(), unique=True)
    small_threshold(monkeypatch)
    called = []
    monkeypatch.setattr(ac, "prose_none_fetch_existence", lambda *a, **k: called.append(a) or dict(violating=False, sample=[], exact=False))
    read_outside()
    assert len(called) == 1


def test_a_non_json_column_never_takes_the_keyed_walk(monkeypatch):
    db = make(monkeypatch, parts3())
    small_threshold(monkeypatch)
    monkeypatch.setattr(ac, "prose_none_fetch_existence", lambda *a, **k: dict(violating=False, sample=[], exact=False))
    ac.prose_none_read_outside("kt", "c", "text", dict(column="c", values=["Sun"]), None, est=900_000)
    assert not any("pg_index" in s for s in db.calls)


def test_the_chunk_statement_without_a_partition_is_unchanged():
    a = ac.prose_none_existence_chunk_sql("t", "j", "json", ENTRY, None, "(2,1)", 4)
    assert a == ac.prose_none_existence_chunk_sql("t", "j", "json", ENTRY, None, "(2,1)", 4, None)
    b = ac.prose_none_existence_chunk_sql("t", "j", "json", ENTRY, None, "(2,1)", 4, "\"a\" = '2'")
    assert "\"a\" = '2'" in b and "\"a\" = '2'" not in a and "ctid > '(2,1)'::tid" in b


def test_the_grader_reads_an_incomplete_keyed_walk_as_no_detector_with_the_coverage(monkeypatch):
    make(monkeypatch, parts3(p2=dict(timeout=True)))
    small_threshold(monkeypatch)
    monkeypatch.setattr(ac, "source_estimate_rows", lambda t: 900_000)
    tables = {"kt": (["id", "doc"], {"id": "integer", "doc": "jsonb"}, None)}
    pnd = dict(why=pn.WHY, closed_columns=[dict(column="doc", json_leaf_patterns=ENTRY["json_leaf_patterns"], why=pn.CW)])
    out = ac.prose_none_fetch_outside(tables, "kt", pnd)
    unread = out[("kt", "doc")]["unread"]
    assert unread.startswith("unread: ") and "covered 2 of 3 partition(s)" in unread and "kt.doc (json closure walk)" in unread and "neither a PASS nor a FAIL" in unread
    ctx = pn._ctx(["id", "doc"], {"id": "integer", "doc": "jsonb"}, closed_outside=out)
    cells = ac.prose_checks("x_asset", {"prose_fields": [], "evidence": {"prose_fields": pn.EV}, "prose_none": pnd}, ctx)
    assert all(v["v"] == ac.NO_DET for v in cells.values()) and not any(v["v"] in (ac.PASS, ac.NA, ac.ERRORED) for v in cells.values())
