"""test_formgap_multi_filter.py: the MULTI-FILTER-PER-TABLE form of `produced_tables` (SS, for ga_sensitive_degree).

An asset may write several row slices of ONE shared table (ga_sensitive_degree: two fact_categories of chart_facts). `produced_tables` takes one entry per slice, each `{table, filter: {column, equals}}`, all on ONE
column; the prose_none reads slice the table by the OR of them (before, a later entry for a table REPLACED the earlier one, so the first slice was never judged). Each declared slice value is CHECKED against the
writer's scan: it must occur as a string literal in the scanned writer scope (a phantom slice is a FAIL; a scan that could not be read or was cut is NO_DETECTOR). Real PostgreSQL; the engine's own `_measure_prose`.
"""
from __future__ import annotations

import ast
import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import NA, FAIL, NO_DET, CELLS  # noqa: E402

T = "t_multi_slice"
EV = "platform/scripts/governance/__tests__/test_formgap_multi_filter.py:1"


def _pt(*vals, col="cat"):
    return [dict(table=T, filter=dict(column=col, equals=v)) for v in vals]


def _decl(pt=None, **extra):
    pn = dict(why=fs.WHY, column_scope="written",
              closed_columns=[dict(column="sub", why="the subject words the writer writes in every slice", values=["s1", "s2"]), dict(column="cat", why="the two slice words of the writer", values=["cat_a", "cat_b"])],
              unset_columns=[dict(column="note", why="the writer never fills this column in a slice row", evidence=EV)])
    pn.update(extra)
    return {"prose_fields": [], "evidence": {"prose_fields": EV}, "prose_none": pn, "produced_tables": pt if pt is not None else _pt("cat_a", "cat_b")}


# ───────────────────────────── the validator and the pure helpers ─────────────────────────────

def test_several_slices_of_one_table_on_one_column_are_sound():
    assert ac.produced_tables_problem(_decl()) is None
    assert ac.multi_filter_groups(_decl()) == {T: ("cat", ["cat_a", "cat_b"])}
    assert ac.multi_filter_groups(_decl(_pt("cat_a"))) == {}


@pytest.mark.parametrize("pt,needle", [
    (_pt("cat_a") + [dict(table=T)], "names no filter"),
    ([dict(table=T)] + _pt("cat_a"), "names no filter"),
    (_pt("cat_a") + _pt("cat_b", col="other"), "SAME column"),
    (_pt("cat_a", "cat_a"), "listed twice"),
])
def test_a_malformed_multi_slice_declaration_is_refused(pt, needle):
    got = ac.produced_tables_problem(_decl(pt))
    assert got is not None and needle in got, got


def test_the_slice_predicate_and_the_merged_slice():
    assert ac._slice_pred(dict(column="c", equals="x")) == '"c"::text = \'x\''
    assert ac._slice_pred(dict(column="c", **{"in": ["x", "y'z"]})) == '"c"::text IN (\'x\', \'y\'\'z\')'
    d = ac.declared_produced_tables(_decl())
    assert ac.merged_slice(d, T) == {"column": "cat", "in": ["cat_a", "cat_b"]}
    assert ac.merged_slice(ac.declared_produced_tables(_decl(_pt("cat_a"))), T) == {"column": "cat", "equals": "cat_a"}
    assert ac.merged_slice(ac.declared_produced_tables(_decl([dict(table=T)])), T) is None
    assert ac.merged_slice(d, "other") is None


def test_the_existing_two_slice_declaration_of_bo_karanajala_still_validates():
    assert ac.produced_tables_problem(ac.load_asset_declarations()["bo_karanajala"]) is None


def test_the_rollup_guard_wants_two_verified_slices():
    ok = dict(multi_filter=[dict(table=T, column="cat", values=["a", "b"], verified=True, live_checked=True)])
    assert ac.formgap_block_problem(ok) is None
    assert ac.formgap_block_problem(dict(multi_filter=[dict(table=T, column="cat", values=["a"], verified=True, live_checked=True)])) is not None
    assert ac.formgap_block_problem(dict(multi_filter=[dict(table=T, column="cat", values=["a", "b"], verified=False, live_checked=True)])) is not None


# ───────────────────────────── the writer-scan check (pure) ─────────────────────────────

def _unit(src):
    tree = ast.parse(src)
    return dict(rel="w.py", path=pathlib.Path("w.py"), tree=tree, nodes=[tree], hop=0, via="w.py")


def test_each_declared_slice_must_be_a_value_the_writer_writes_into_the_filter_column(monkeypatch):
    monkeypatch.setattr(ac, "_delegation_scope", lambda aid, files, hops=None: ([_unit(WRITES_AB)], ()))
    got = ac.multi_filter_scan("x", ["w.py"], _decl())[T]
    assert got["found"] == ["cat_a", "cat_b"] and got["undeclared"] == []
    monkeypatch.setattr(ac, "_delegation_scope", lambda aid, files, hops=None: ([_unit('ROWS = [dict(cat="cat_a")]\n')], ()))
    assert ac.multi_filter_scan("x", ["w.py"], _decl())[T]["found"] == ["cat_a"]
    assert ac.multi_filter_scan("x", [], _decl())[T]["unread"]
    assert ac.multi_filter_scan("x", ["w.py"], _decl(_pt("cat_a"))) == {}


def test_FORGERY_a_constant_that_is_not_written_into_the_column_does_not_bind_a_slice(monkeypatch):
    """Review fix MED 6: the old scan accepted ANY string constant of the writer scope (a comparison, a docstring-like constant, an unrelated column). Only write sites bind."""
    src = ('A = "cat_a"\nB = "cat_b"\n'                                                                    # module constants nobody writes into the column
           'def run(x):\n    if x == "cat_b":\n        return dict(other="cat_b", cat="cat_a")\n')               # a comparison; another column; one real write
    monkeypatch.setattr(ac, "_delegation_scope", lambda aid, files, hops=None: ([_unit(src)], ()))
    got = ac.multi_filter_scan("x", ["w.py"], _decl())[T]
    assert got["found"] == ["cat_a"] and got["written"] == ["cat_a"]


def test_a_value_flows_through_a_carrier_name_a_default_an_assignment_and_a_conditional(monkeypatch):
    src = ('CAT_A = "cat_a"\nCAT_B = "cat_b"\n'
           'def _row(category=CAT_A):\n    return {"cat": category}\n'
           'def run(flag):\n    _row(category=CAT_B)\n    kind = "x" if flag else "y"\n    cat = "cat_a" if flag else CAT_B\n')
    monkeypatch.setattr(ac, "_delegation_scope", lambda aid, files, hops=None: ([_unit(src)], ()))
    got = ac.multi_filter_scan("x", ["w.py"], _decl())[T]
    assert got["written"] == ["cat_a", "cat_b"] and got["found"] == ["cat_a", "cat_b"]


def test_REAL_WRITER_scan_ga_sensitive_degree_writes_both_declared_categories():
    got = ac.multi_filter_scan("ga_sensitive_degree", ac.registered_ids("")["ga_sensitive_degree"],
                               dict(produced_tables=[dict(table="chart_facts", filter=dict(column="fact_category", equals=v)) for v in ("sensitive_degree_check", "sensitive_point_yogi")]))
    assert got["chart_facts"]["found"] == ["sensitive_degree_check", "sensitive_point_yogi"] and got["chart_facts"]["scan_cut"] is False
    ghost = ac.multi_filter_scan("ga_sensitive_degree", ac.registered_ids("")["ga_sensitive_degree"],
                                 dict(produced_tables=[dict(table="chart_facts", filter=dict(column="fact_category", equals=v)) for v in ("sensitive_degree_check", "sensitive_point_ghost")]))
    assert ghost["chart_facts"]["found"] == ["sensitive_degree_check"]


# ───────────────────────────── real SQL: the reads slice by the OR ─────────────────────────────

@pytest.fixture()
def db(monkeypatch, disposable_pg):
    pg = disposable_pg
    point_psql_at(pg, monkeypatch)
    fs.drop_tables(pg, T)
    fs.psql(pg, f"CREATE TABLE {T} (id serial PRIMARY KEY, cat text NOT NULL, sub text, note text)")
    fs.psql(pg, f"INSERT INTO {T} (cat, sub) SELECT CASE WHEN g % 2 = 0 THEN 'cat_a' ELSE 'cat_b' END, CASE WHEN g % 3 = 0 THEN 's1' ELSE 's2' END FROM generate_series(1, 20) g")
    fs.psql(pg, f"INSERT INTO {T} (cat, sub, note) VALUES ('cat_c', 'a free sentence another asset wrote', 'another asset note')")          # a THIRD slice, outside the declaration
    yield pg
    fs.drop_tables(pg, T)


WRITES_AB = 'ROWS = [dict(cat="cat_a", sub="s1"), {"cat": "cat_b", "sub": "s2"}]\n'


def _m(pg, mp, decl, units_src=WRITES_AB, files=("ga_transit_anchors.py",), beyond=(), shared=(T,)):
    mp.setattr(ac, "written_columns", lambda units, tables: {T: {"cat", "sub"}})
    mp.setattr(ac, "_delegation_scope", lambda aid, f, hops=None, strict=False: ([_unit(units_src)], beyond))
    cat = ac.catalog([T])
    vocab = ac.prose_vocabulary({"x_multi": decl}, {"x_multi": {T}})
    ac.set_read_scope({})
    try:
        return ac._measure_prose("x_multi", decl, dict(target_table=T), list(files), cat, [], set(shared), (), vocab)
    finally:
        ac.set_read_scope(None)


def test_REAL_SQL_both_slices_are_judged_and_a_third_category_is_not(db, monkeypatch):
    got = _m(db, monkeypatch, _decl())
    fs.all_na(got)
    f = got["Narr.agree"]["prose_none"]["forms"]
    assert f["multi_filter"] == [dict(table=T, column="cat", values=["cat_a", "cat_b"], verified=True, live_checked=True, undeclared_live_checked=False)]


@pytest.mark.parametrize("cat", ["cat_a", "cat_b"])
def test_REAL_SQL_MUTATION_an_open_value_in_EITHER_slice_is_a_FAIL(db, monkeypatch, cat):
    """cat_a is the FIRST declared slice: before this form a later entry replaced it and its rows were never read."""
    fs.mutate_and_restore(db, T, "id", "sub", "'a sentence nobody declared'", f"cat = '{cat}'",
                          lambda: (lambda g: (g["Narr.agree"]["v"] == FAIL and "sub" in g["Narr.agree"]["measured"]) or pytest.fail(g["Narr.agree"]["measured"][:300]))(_m(db, monkeypatch, _decl())))
    assert _m(db, monkeypatch, _decl())["Narr.agree"]["v"] == NA


def test_REAL_SQL_MUTATION_a_value_in_an_unset_column_inside_a_slice_is_a_FAIL_and_outside_it_is_not(db, monkeypatch):
    fs.mutate_and_restore(db, T, "id", "note", "'a note'", "cat = 'cat_b'", lambda: (lambda g: g["Narr.agree"]["v"] == FAIL or pytest.fail("no FAIL"))(_m(db, monkeypatch, _decl())))
    assert _m(db, monkeypatch, _decl())["Narr.agree"]["v"] == NA                                  # the cat_c row's own note never counted


def test_REAL_SQL_MUTATION_a_phantom_slice_the_writer_never_writes_is_a_FAIL(db, monkeypatch):
    d = _decl(_pt("cat_a", "cat_ghost"))
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "cat_ghost" in got["Narr.agree"]["measured"] and "are not written into cat anywhere in the writer scan" in got["Narr.agree"]["measured"]


def test_REAL_SQL_a_scan_that_was_cut_or_has_no_file_is_no_detector(db, monkeypatch):
    got = _m(db, monkeypatch, _decl(), beyond=("cut.py",))
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "delegation chain" in got["Narr.agree"]["measured"]
    got = _m(db, monkeypatch, _decl(), files=())
    assert all(got[c]["v"] == NO_DET for c in CELLS)


def test_REAL_SQL_a_single_slice_declaration_reads_exactly_as_before(db, monkeypatch):
    d = _decl(_pt("cat_a"), closed_columns=[dict(column="sub", why="the subject words the writer writes in the slice", values=["s1", "s2"]), dict(column="cat", why="the slice word of the writer", values=["cat_a"])])
    got = _m(db, monkeypatch, d)
    fs.all_na(got)
    assert "multi_filter" not in got["Narr.agree"]["prose_none"].get("forms", {})


def test_FORGERY_a_value_the_writer_writes_that_no_slice_declares_is_a_FAIL(db, monkeypatch):
    """Review fix MED 6: the produced-table slices must cover what the writer writes; a third value written into the filter column is a FAIL, never N/A."""
    src = WRITES_AB + 'ROWS += [dict(cat="cat_c", sub="s1")]\n'
    got = _m(db, monkeypatch, _decl(), units_src=src)
    assert got["Narr.agree"]["v"] == FAIL and "no declared slice names" in got["Narr.agree"]["measured"] and "cat_c" in got["Narr.agree"]["measured"]
    assert all(got[c]["v"] != NA for c in CELLS)


def test_FORGERY_a_phantom_slice_bound_only_by_an_unrelated_constant_is_a_FAIL(db, monkeypatch):
    src = 'GHOST = "cat_ghost"\nROWS = [dict(cat="cat_a", sub="s1")]\n'
    got = _m(db, monkeypatch, _decl(_pt("cat_a", "cat_ghost")), units_src=src)
    assert got["Narr.agree"]["v"] == FAIL and "cat_ghost" in got["Narr.agree"]["measured"]


# ───────────────────────────── re-review fix MED 3: the LIVE values of the filter column ─────────────────────────────

LOOP_WRITER = WRITES_AB + 'for c in ("cat_c",):\n    ROWS.append({"cat": c, "sub": "s1"})\n'          # the AST sees no write site of cat_c (a loop variable)


def test_FORGERY_a_loop_variable_write_of_an_undeclared_value_is_a_FAIL_on_a_table_the_asset_owns(db, monkeypatch):
    got = _m(db, monkeypatch, _decl(), units_src=LOOP_WRITER, shared=())
    assert got["Narr.agree"]["v"] == FAIL and "holds live value(s)" in got["Narr.agree"]["measured"] and "cat_c" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    assert all(got[c]["v"] != NA for c in CELLS)


def test_a_shared_table_cannot_attribute_other_assets_values_so_the_live_subset_is_not_asked_and_says_so(db, monkeypatch):
    got = _m(db, monkeypatch, _decl(), shared=(T,))
    fs.all_na(got)
    assert got["Narr.agree"]["prose_none"]["forms"]["multi_filter"] == [dict(table=T, column="cat", values=["cat_a", "cat_b"], verified=True, live_checked=True, undeclared_live_checked=False)]


def test_FORGERY_a_dead_write_site_does_not_stand_for_a_slice_the_table_never_holds(db, monkeypatch):
    """The AST finds `dict(cat="cat_ghost")` in dead code and binds the phantom slice; the live read finds no cat_ghost row while other values are present: FAIL."""
    src = WRITES_AB + 'def never_called():\n    return dict(cat="cat_ghost", sub="s1")\n'
    for shared in ((), (T,)):
        got = _m(db, monkeypatch, _decl(_pt("cat_a", "cat_b", "cat_ghost")), units_src=src, shared=shared)
        assert got["Narr.agree"]["v"] == FAIL and "cat_ghost" in got["Narr.agree"]["measured"] and "hold no row" in got["Narr.agree"]["measured"], (shared, got["Narr.agree"]["measured"][:400])


def test_an_empty_filter_column_in_the_scope_is_no_detector_never_na(db, monkeypatch):
    fs.psql(db, f"UPDATE {T} SET cat = 'zzz'")                                            # no row carries a declared slice any more: the reads judge nothing
    got = _m(db, monkeypatch, _decl(), shared=())
    assert all(got[c]["v"] != NA for c in CELLS)


def test_the_rollup_guard_wants_the_live_check_on_a_multi_filter_entry():
    assert ac.formgap_block_problem(dict(multi_filter=[dict(table=T, column="cat", values=["a", "b"], verified=True)])) is not None
    assert ac.formgap_block_problem(dict(multi_filter=[dict(table=T, column="cat", values=["a", "b"], verified=True, live_checked=True)])) is None


def test_the_live_read_is_one_bounded_statement():
    sql = ac.filter_live_sql("t", "c")
    assert sql.count("SELECT DISTINCT") == 1 and f"LIMIT {ac.FILTER_LIVE_MAX}" in sql and "count(" not in sql
