"""test_n176_prose_none_existence.py: the bounded EXISTENCE read of a declared prose_none closure (SS N-176 / interim census 42e96d491, 2026-10-07).

All six ERRORED cells of the interim census were ONE asset, bo_drishti (Null.schema_default, Null.blank_rows, Narr.agree, Narr.checkable, Narr.fidelity_test, Narr.lint:
`canceling statement due to statement timeout`). The live closure read counted every row of bodha_question_lenses (three jsonb documents per row) and sat OUTSIDE the per-check guard, so one
timeout turned all six cells ERRORED. The closure is now read like the Ldgr existence read: a large table (catalog estimate) or an exact read that timed out is read by ONE bounded statement per column that
stops at the first violating rows (LIMIT, no count(*), no ORDER BY) and answers a bounded sample; the verdict is exact (PASS only when the scan reached the end without a violating row); if even that read times
out the closure is NOT READ and the six cells read NO_DETECTOR with the cause (never ERRORED, never PASS). A small table keeps the exact count and its text byte for byte.

These tests prove (a) the SQL shape, (b) on a DISPOSABLE PostgreSQL the bounded verdict equals the exact verdict on every fixture (closed column with all-in-vocabulary rows, one stray value, json leaves with a
uuid / timestamp pattern, a stray string leaf, NULLs, an empty table, array / enum / json forms), (c) the routing and failure modes, (d) the grader's text never states a total for an existence read, (e) the
label-columns twin (the closed-values check) degrades the same way.
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
import test_n150_prose_none as pn  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, NA, ERRORED = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA, ac.ERRORED
TIMEOUT = "ERROR:  canceling statement due to statement timeout"
UUID1 = "11111111-2222-3333-4444-555555555555"
UUID2 = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


# ───────────────────────────── (a) the SQL shape ─────────────────────────────

ENTRIES = {
    "text_values": ("text", dict(column="c", values=["Sun", "Moon"])),
    "array_values": ("array", dict(column="c", values=["x", "y"])),
    "json_values": ("json", dict(column="c", values=["v", "q"])),
    "json_no_leaves": ("json", dict(column="c", values=None, no_string_leaves=True)),
    "json_patterns": ("json", dict(column="c", values=None, json_leaf_patterns=[dict(path="$.ids[*]", kind="uuid"), dict(path="$.at", kind="iso8601_timestamp"),
                                                                                 dict(path="$.cls[*]", values=["a", "b"])])),
}


@pytest.mark.parametrize("name", sorted(ENTRIES))
def test_the_existence_statement_is_bounded_with_no_count_sort_or_group(name):
    kind, entry = ENTRIES[name]
    sql = ac.prose_none_existence_sql("big_t", "c", kind, entry, None)
    assert f'FROM "big_t"' in sql and f"LIMIT {ac.PROSE_NONE_SAMPLE_LIMIT}) s" in sql          # the sample is bounded and stops the scan at the first violating rows
    over = sql.replace("jsonb_path_query(", "").replace("unnest(", "")
    assert "ORDER BY" not in sql.upper() and "GROUP BY" not in sql.upper() and "DISTINCT" not in sql.upper()
    assert not re.search(r"count\s*\(\*\)\s*::text", sql, re.I) and 'SELECT count(*)::text FROM "big_t"' not in sql      # no whole-table count over the target
    assert sql.count('FROM "big_t"') == 1 and sql.count("LIMIT") == 1 and over.count("LIMIT") == 1                               # ONE scan of the target, bounded by ONE LIMIT


def test_the_exact_statement_it_complements_counts_every_row_and_is_unchanged():
    """The 'before' shape (kept byte for byte for a small table): one whole-table count(*) over the rows that leave the closure."""
    sql = ac.prose_none_outside_sql("t", "c", "text", dict(column="c", values=["Sun", "Moon"]), None)
    assert sql == 'SELECT count(*)::text FROM "t" WHERE "c" IS NOT NULL AND "c"::text <> ALL(ARRAY[\'Sun\',\'Moon\']::text[])'
    kind, entry = ENTRIES["json_patterns"]
    full = ac.prose_none_outside_sql("t", "c", kind, entry, None)
    assert full.startswith('SELECT count(*)::text FROM "t" WHERE "c" IS NOT NULL AND (SELECT count(*) FROM jsonb_path_query("c"::jsonb, \'strict $.**\')')
    f = ac.prose_none_outside_sql("t", "c", "text", dict(column="c", values=["a"]), dict(column="k", equals="x"))
    assert f == 'SELECT count(*)::text FROM "t" WHERE "k"::text = \'x\' AND "c" IS NOT NULL AND "c"::text <> ALL(ARRAY[\'a\']::text[])'


def test_both_reads_embed_the_very_same_predicate():
    for name, (kind, entry) in ENTRIES.items():
        cond = ac._prose_none_cond('"c"', kind, entry)
        assert cond in ac.prose_none_outside_sql("t", "c", kind, entry, None), name
        assert cond in ac.prose_none_existence_sql("t", "c", kind, entry, None), name
    assert ac._prose_none_cond('"c"', "text", dict(column="c", values=None, no_string_leaves=True)) is None             # json-only forms on a non-json column: the grader refuses them first
    assert ac.prose_none_existence_sql("t", "c", "text", dict(column="c", values=None, no_string_leaves=True), None) == "SELECT NULL::text"


# ───────────────────── (b) the bounded verdict equals the exact verdict (real SQL) ─────────────────────

def _mk(pg, monkeypatch, table, ddl, rows):
    """A real table on the disposable cluster (dropped by the caller's finalizer): psql() reaches it."""
    point_psql_at(pg, monkeypatch)
    ac.psql(f"DROP TABLE IF EXISTS {table}")
    ac.psql(f"CREATE TABLE {table} ({ddl})")
    for r in rows:
        ac.psql(f"INSERT INTO {table} VALUES ({r})")


FIXTURES = {
    "text_all_in_vocabulary": ("c text", ["'Sun'", "'Moon'", "'Sun'", "NULL"], "text", dict(column="c", values=["Sun", "Moon"]), 0),
    "text_one_stray_value": ("c text", ["'Sun'", "'Moon'", "'Mars'", "NULL"], "text", dict(column="c", values=["Sun", "Moon"]), 1),
    "text_stray_is_the_last_row": ("c text", [f"'Sun'" for _ in range(60)] + ["'Mars'"], "text", dict(column="c", values=["Sun", "Moon"]), 1),
    "text_nulls_only": ("c text", ["NULL", "NULL"], "text", dict(column="c", values=["Sun"]), 0),
    "text_empty_table": ("c text", [], "text", dict(column="c", values=["Sun"]), 0),
    "array_clean": ("c text[]", ["ARRAY['x','y']", "ARRAY['x']", "NULL", "ARRAY[]::text[]"], "array", dict(column="c", values=["x", "y"]), 0),
    "array_stray_element": ("c text[]", ["ARRAY['x','y']", "ARRAY['x','z']"], "array", dict(column="c", values=["x", "y"]), 1),
    "json_values_clean": ("c jsonb", ["'{\"k\":\"v\",\"n\":1}'::jsonb", "'[\"q\"]'::jsonb", "NULL"], "json", dict(column="c", values=["v", "q"]), 0),
    "json_values_stray_leaf": ("c jsonb", ["'{\"k\":\"v\"}'::jsonb", "'{\"k\":\"free prose\"}'::jsonb"], "json", dict(column="c", values=["v", "q"]), 1),
    "json_no_string_leaves_clean": ("c jsonb", ["'{\"a\":1,\"b\":[2,3],\"d\":null}'::jsonb", "NULL"], "json", dict(column="c", values=None, no_string_leaves=True), 0),
    "json_no_string_leaves_violated": ("c jsonb", ["'{\"a\":1}'::jsonb", "'{\"a\":\"x\"}'::jsonb"], "json", dict(column="c", values=None, no_string_leaves=True), 1),
    "json_patterns_clean": ("c jsonb", [f"'{{\"ids\":[\"{UUID1}\",\"{UUID2}\"],\"at\":\"2026-10-07T01:15:00+05:30\",\"cls\":[\"a\",\"b\"],\"n\":3}}'::jsonb", "NULL",
                                        f"'{{\"ids\":[],\"cls\":[\"a\"]}}'::jsonb"], "json",
                            dict(column="c", values=None, json_leaf_patterns=[dict(path="$.ids[*]", kind="uuid"), dict(path="$.at", kind="iso8601_timestamp"), dict(path="$.cls[*]", values=["a", "b"])]), 0),
    "json_patterns_stray_string_leaf": ("c jsonb", [f"'{{\"ids\":[\"{UUID1}\"],\"cls\":[\"a\"]}}'::jsonb", f"'{{\"ids\":[\"{UUID1}\"],\"cls\":[\"a\"],\"note\":\"a sentence\"}}'::jsonb"], "json",
                                        dict(column="c", values=None, json_leaf_patterns=[dict(path="$.ids[*]", kind="uuid"), dict(path="$.cls[*]", values=["a", "b"])]), 1),
    "json_patterns_declared_path_wrong_shape": ("c jsonb", [f"'{{\"ids\":[\"{UUID1}\"]}}'::jsonb", "'{\"ids\":[\"not-a-uuid\"]}'::jsonb"], "json",
                                                dict(column="c", values=None, json_leaf_patterns=[dict(path="$.ids[*]", kind="uuid")]), 1),
    "json_patterns_value_outside_closed_values": ("c jsonb", ["'{\"cls\":[\"a\"]}'::jsonb", "'{\"cls\":[\"zzz\"]}'::jsonb"], "json",
                                                  dict(column="c", values=None, json_leaf_patterns=[dict(path="$.cls[*]", values=["a", "b"])]), 1),
}


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_REAL_SQL_the_bounded_verdict_equals_the_exact_verdict(monkeypatch, disposable_pg, name):
    ddl, rows, kind, entry, want = FIXTURES[name]
    t = "n176_closure"
    _mk(disposable_pg, monkeypatch, t, ddl, rows)
    try:
        exact = int(ac.scalar(ac.prose_none_outside_sql(t, "c", kind, entry, None)))
        cheap = ac.prose_none_fetch_existence(t, "c", kind, entry, None)
        assert exact == want, (name, exact)
        assert cheap["violating"] is (exact > 0), (name, exact, cheap)                    # the SAME verdict: no violating row <=> none exists
        assert cheap["exact"] is False and len(cheap["sample"]) <= ac.PROSE_NONE_SAMPLE_LIMIT
        assert (len(cheap["sample"]) > 0) == (exact > 0) and all(len(s) <= ac.PROSE_NONE_SAMPLE_CHARS for s in cheap["sample"])
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_a_filter_slices_both_reads_the_same_way(monkeypatch, disposable_pg):
    t = "n176_closure_f"
    _mk(disposable_pg, monkeypatch, t, "fact_category text, note text", ["'dasha_scope_cap','a'", "'other','free prose here'", "'dasha_scope_cap','b'"])
    try:
        entry, filt = dict(column="note", values=["a", "b"]), dict(column="fact_category", equals="dasha_scope_cap")
        assert int(ac.scalar(ac.prose_none_outside_sql(t, "note", "text", entry, filt))) == 0
        assert ac.prose_none_fetch_existence(t, "note", "text", entry, filt)["violating"] is False
        assert int(ac.scalar(ac.prose_none_outside_sql(t, "note", "text", entry, None))) == 1
        assert ac.prose_none_fetch_existence(t, "note", "text", entry, None)["violating"] is True
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_the_sample_names_at_most_three_real_offenders_cut_to_the_limit(monkeypatch, disposable_pg):
    t = "n176_closure_s"
    rows = ["'Sun'"] + [f"'Stray{i}'" for i in range(6)] + ["'" + "x" * 300 + "'"]
    _mk(disposable_pg, monkeypatch, t, "c text", rows)
    try:
        got = ac.prose_none_fetch_existence(t, "c", "text", dict(column="c", values=["Sun"]), None)
        assert got["violating"] and len(got["sample"]) == ac.PROSE_NONE_SAMPLE_LIMIT and all(s.startswith("Stray") for s in got["sample"])
        assert all(len(s) <= ac.PROSE_NONE_SAMPLE_CHARS for s in got["sample"])
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_REAL_SQL_the_routing_end_to_end_gives_ints_for_a_small_table_and_dicts_for_a_large_one(monkeypatch, disposable_pg):
    t = "n176_closure_r"
    _mk(disposable_pg, monkeypatch, t, "id int, c text", ["1,'Sun'", "2,'Mars'"])
    try:
        tables = {t: (["id", "c"], {"id": "integer", "c": "text"}, None)}
        decl = dict(why=pn.WHY, closed_columns=[pn._cc("c", ["Sun", "Moon"], table=None)])
        monkeypatch.setattr(ac, "source_estimate_rows", lambda tb: None)
        assert ac.prose_none_fetch_outside(tables, t, decl) == {(t, "c"): 1}                      # unknown size: the exact count, as before
        monkeypatch.setattr(ac, "source_estimate_rows", lambda tb: ac.LDGR_CHEAP_MIN_ROWS - 1)
        assert ac.prose_none_fetch_outside(tables, t, decl) == {(t, "c"): 1}                      # still small: exact
        monkeypatch.setattr(ac, "source_estimate_rows", lambda tb: ac.LDGR_CHEAP_MIN_ROWS)
        got = ac.prose_none_fetch_outside(tables, t, decl)[(t, "c")]
        assert isinstance(got, dict) and got["violating"] is True and "catalog estimates" in got["why_cheap"] and got["sample"] == ["Mars"]
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


# ───────────────────────────── (c) routing and failure modes ─────────────────────────────

class Server:
    """A fake `scalar`: answers the catalog estimate, the exact count and the existence statement from scripted behaviour and records every statement."""

    def __init__(self, estimate="-1", exact="0", cheap="[]"):
        self.estimate, self.exact, self.cheap, self.sql = estimate, exact, cheap, []

    def __call__(self, q):
        self.sql.append(q)
        if "reltuples" in q:
            return self.estimate
        beh = self.cheap if "jsonb_agg" in q else self.exact
        if isinstance(beh, Exception):
            raise beh
        return beh


def _read(monkeypatch, srv):
    monkeypatch.setattr(ac, "scalar", srv)
    return ac.prose_none_read_outside("big_t", "c", "text", dict(column="c", values=["Sun"]), None)


def _target_reads(srv):
    return [q for q in srv.sql if 'FROM "big_t"' in q]


def test_a_large_table_is_read_by_existence_straight_away_and_never_counted(monkeypatch):
    srv = Server(estimate=str(ac.LDGR_CHEAP_MIN_ROWS), exact=AssertionError("the exact count must not run on a large table"), cheap='["Mars"]')
    got = _read(monkeypatch, srv)
    assert got["violating"] is True and got["sample"] == ["Mars"] and got["exact"] is False and "catalog estimates" in got["why_cheap"]
    assert len(_target_reads(srv)) == 1 and "count(" not in _target_reads(srv)[0]


def test_a_small_table_keeps_the_exact_count_and_never_runs_the_existence_read(monkeypatch):
    for est in ("-1", str(ac.LDGR_CHEAP_MIN_ROWS - 1), "0"):
        srv = Server(estimate=est, exact="4", cheap=AssertionError("the existence read must not run on a small table"))
        assert _read(monkeypatch, srv) == 4
        assert len(_target_reads(srv)) == 1 and "count(*)" in _target_reads(srv)[0]


@pytest.mark.parametrize("err", [ac.Unknown(TIMEOUT), ac.CheckTimeout("client-side timeout after 180s (psql killed): SELECT ...")])
def test_an_exact_count_that_times_out_falls_back_to_the_existence_read(monkeypatch, err):
    srv = Server(estimate="1000", exact=err, cheap="[]")
    got = _read(monkeypatch, srv)
    assert got["violating"] is False and got["exact"] is False and "exceeded the statement timeout" in got["why_cheap"]
    assert ["count(*)" in q for q in _target_reads(srv)] == [True, False]                          # exact tried once, then the existence read


@pytest.mark.parametrize("err", [ac.Unknown(TIMEOUT), ac.CheckTimeout("client-side timeout after 180s (psql killed)")])
def test_when_even_the_existence_read_times_out_the_closure_is_not_read_never_errored(monkeypatch, err):
    for srv in (Server(estimate=str(10 ** 7), cheap=err), Server(estimate="5", exact=ac.Unknown(TIMEOUT), cheap=err)):
        got = _read(monkeypatch, srv)
        assert "unread" in got and "also exceeded the statement timeout" in got["unread"] and "neither a PASS nor a FAIL" in got["unread"]


def test_one_exact_timeout_per_table_the_other_columns_go_straight_to_existence_and_the_estimate_is_read_once(monkeypatch):
    """bo_drishti closes 12 columns of one table: an exact count that times out must cost ONE statement timeout for the table, not one per column; the catalog estimate is one lookup per table."""
    srv = Server(estimate="1000", exact=ac.Unknown(TIMEOUT), cheap="[]")
    monkeypatch.setattr(ac, "scalar", srv)
    cols = ["a", "b", "c", "d"]
    tables = {"big_t": (cols, {c: "text" for c in cols}, None)}
    got = ac.prose_none_fetch_outside(tables, "big_t", dict(why=pn.WHY, closed_columns=[pn._cc(c, ["Sun"]) for c in cols]))
    assert all(isinstance(v, dict) and v["violating"] is False for v in got.values()) and len(got) == 4
    exact_tries = [q for q in srv.sql if "count(*)::text" in q]
    assert len(exact_tries) == 1                                                             # ONE exact attempt (the first column), then existence for the rest
    assert sum(1 for q in srv.sql if "reltuples" in q) == 1                                  # ONE estimate lookup for the table
    assert "already exceeded the statement timeout" in got[("big_t", "d")]["why_cheap"] and "exceeded the statement timeout" in got[("big_t", "a")]["why_cheap"]


def test_any_other_failure_still_raises_so_the_cells_read_errored_as_before(monkeypatch):
    with pytest.raises(ac.Unknown, match="does not exist"):
        _read(monkeypatch, Server(estimate="5", exact=ac.Unknown('ERROR:  relation "big_t" does not exist')))
    with pytest.raises(ac.Unknown, match="permission denied"):
        _read(monkeypatch, Server(estimate=str(10 ** 7), cheap=ac.Unknown("ERROR:  permission denied for table big_t")))
    with pytest.raises(ac.Unknown, match="unparseable"):
        _read(monkeypatch, Server(estimate=str(10 ** 7), cheap="not json"))
    with pytest.raises(ac.Unknown, match="unparseable count"):
        _read(monkeypatch, Server(estimate="5", exact="abc"))


# ───────────────────── (d) what the grader reads: same verdicts, no invented total ─────────────────────

def _grade(outside):
    return pn._run(pn._decl(pn._cc()), pn._ctx(pn.COLS, pn.TYPES, closed_outside=outside))


def test_a_clean_existence_read_reads_na_on_all_six_cells_with_the_checked_block_naming_the_read():
    got = _grade({("t", "graha"): dict(violating=False, sample=[], exact=False, why_cheap="the catalog estimates 9 rows")})
    for c in ac.NARR_CHECKS + ac.NULL_CHECKS:
        assert got[c]["v"] == NA, (c, got[c])
    b = got["Narr.agree"]["prose_none"]
    assert b["existence_reads"] == ["t.graha"] and b["closed"] == [dict(table="t", column="graha", kind="text", read="existence")] and b["unread"] == [] and b["contradicted"] == []
    assert "bounded existence read" in got["Narr.agree"]["measured"] and "rows were not counted" in got["Narr.agree"]["measured"]
    assert ac.prose_none_na_problem("Narr.agree", got["Narr.agree"]) is None                        # the rollup's own guard accepts the checked block


def test_a_violating_existence_read_is_the_same_fail_with_at_least_one_and_the_sample_never_a_total():
    got = _grade({("t", "graha"): dict(violating=True, sample=["Mars", "a long sentence"], exact=False, why_cheap="x")})
    assert got["Narr.agree"]["v"] == FAIL and all(got[c]["v"] == NO_DET for c in ac.NARR_CHECKS[1:] + ac.NULL_CHECKS)
    text = got["Narr.agree"]["measured"]
    assert "at least 1 row holds text outside the declared closed vocabulary" in text and "no total is stated" in text and "'Mars'" in text.replace('"', "'") and "row(s) hold" not in text
    exact = _grade({("t", "graha"): 2})["Narr.agree"]
    assert exact["v"] == FAIL and "2 row(s) hold text outside the declared closed vocabulary" in exact["measured"]       # the exact text, byte for byte


def test_an_unread_closure_is_no_detector_on_all_six_with_the_cause_never_na_never_errored():
    cause = "the existence read (first violating row, bounded sample, no counting) also exceeded the statement timeout (ERROR: canceling statement due to statement timeout): no closure verdict was reached"
    got = _grade({("t", "graha"): dict(unread=cause)})
    for c in ac.NARR_CHECKS + ac.NULL_CHECKS:
        assert got[c]["v"] == NO_DET and got[c]["v"] not in (ERRORED, NA, PASS) and "also exceeded the statement timeout" in got[c]["measured"], (c, got[c])


def test_the_exact_path_is_unchanged_for_a_small_table():
    ok = _grade({("t", "graha"): 0})
    assert all(ok[c]["v"] == NA for c in ac.NARR_CHECKS + ac.NULL_CHECKS)
    assert ok["Narr.agree"]["prose_none"]["closed"] == [dict(table="t", column="graha", kind="text")] and "existence_reads" not in ok["Narr.agree"]["prose_none"]
    assert "existence" not in ok["Narr.agree"]["measured"]


def test_measure_never_errors_the_six_cells_on_a_closure_timeout(monkeypatch):
    """The six cells of bo_drishti: the timeout inside the closure read is handled where it happens (no Unknown escapes _measure_prose), so measure()'s per-check guard is never the one that reads it."""
    srv = Server(estimate="5", exact=ac.Unknown(TIMEOUT), cheap=ac.Unknown(TIMEOUT))
    monkeypatch.setattr(ac, "scalar", srv)
    tables = {"t": (["id", "c"], {"id": "integer", "c": "text"}, None)}
    out = ac.prose_none_fetch_outside(tables, "t", dict(why=pn.WHY, closed_columns=[pn._cc("c", ["Sun"])]))
    assert "unread" in out[("t", "c")]


# ───────────────────── (e) the label-columns twin (the closed-values check) ─────────────────────

LC = [dict(column="label", values=["a", "b"], why="reviewed", evidence="platform/scripts/governance/asset_census.py:1")]


def test_the_stray_statement_is_bounded_for_every_label_form():
    for entry in ("label", "label.$.k", "label.$.items[*].k"):
        sql = ac.label_stray_sql("t", entry, ["a", "b"])
        assert f"LIMIT {ac.PROSE_NONE_SAMPLE_LIMIT}" in sql and "DISTINCT" not in sql.upper() and "count(" not in sql and "ORDER BY" not in sql.upper(), entry


def test_a_bounded_label_read_grades_like_the_exact_one():
    ok = ac.grade_label_columns(LC, {"label": dict(stray=[], bounded=True)})
    assert ok["v"] == PASS and ok["label_columns"]["closed"] == ["label"]
    bad = ac.grade_label_columns(LC, {"label": dict(stray=["zzz"], bounded=True)})
    assert bad["v"] == FAIL and "undeclared value(s), at least ['zzz']" in bad["measured"] and "no total is stated" in bad["measured"]
    assert ac.grade_label_columns(LC, {"label": None})["v"] == PARTIAL                              # a read that did not happen: unchanged


def test_REAL_SQL_the_stray_read_agrees_with_the_distinct_read(monkeypatch, disposable_pg):
    t = "n176_labels"
    _mk(disposable_pg, monkeypatch, t, "label text, doc jsonb", ["'a','{\"k\":\"a\",\"items\":[{\"k\":\"b\"}]}'::jsonb", "'b','{\"k\":\"b\"}'::jsonb", "NULL,NULL"])
    try:
        for entry, clean in (("label", True), ("doc.$.k", True), ("doc.$.items[*].k", True)):
            assert ac.label_fetch_stray(t, entry, ["a", "b"])["stray"] == [] and clean
            assert set(ac.label_fetch_distinct(t, entry)) <= {"a", "b"}
        ac.psql(f"INSERT INTO {t} VALUES ('zzz','{{\"k\":\"zzz\",\"items\":[{{\"k\":\"zzz\"}}]}}'::jsonb)")
        for entry in ("label", "doc.$.k", "doc.$.items[*].k"):
            assert ac.label_fetch_stray(t, entry, ["a", "b"])["stray"] == ["zzz"]
            assert "zzz" in ac.label_fetch_distinct(t, entry)
    finally:
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def test_a_label_distinct_read_that_times_out_falls_back_to_the_stray_read(monkeypatch):
    """The wiring `_measure_prose` uses (`label_read`): DISTINCT cancelled -> the bounded stray read; both cancelled, or any other failure -> not read (PARTIAL, as before); a read that works is unchanged."""
    def boom(exc):
        def f(*a, **k):
            raise exc
        return f
    monkeypatch.setattr(ac, "label_fetch_distinct", lambda t, e: ["a", "b"])
    assert ac.label_read("t", "label", ["a", "b"]) == ["a", "b"]
    monkeypatch.setattr(ac, "label_fetch_distinct", boom(ac.Unknown(TIMEOUT)))
    monkeypatch.setattr(ac, "label_fetch_stray", lambda t, e, v: dict(stray=["zzz"], bounded=True))
    assert ac.label_read("t", "label", ["a", "b"]) == dict(stray=["zzz"], bounded=True)
    monkeypatch.setattr(ac, "label_fetch_stray", boom(ac.Unknown(TIMEOUT)))
    assert ac.label_read("t", "label", ["a", "b"]) is None
    monkeypatch.setattr(ac, "label_fetch_distinct", boom(ac.Unknown('ERROR:  relation "t" does not exist')))
    assert ac.label_read("t", "label", ["a", "b"]) is None
