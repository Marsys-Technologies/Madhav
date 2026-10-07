"""test_formgap_unset.py: FORM-GAP `unset_columns` (SS N-191; added with the bg_nakshatra declaration): a column a seed leaves empty is CHECKED, not trusted.

bg_nakshatra's seed leaves eight text columns unset in every row (basis_above, basis_below, net_result; the five pada nuance columns). A `transcription_columns` entry would exempt them with no look at the data,
so a value written there later would pass as "transcription". `unset_columns` exempts them ONLY through a bounded live read: `SELECT EXISTS (... WHERE col IS NOT NULL)` must be false in the measured slice. A value
(an empty string counts as one) is a FAIL; a read that did not happen is NO_DETECTOR, never PASS. Real PostgreSQL; the engine's own `_measure_prose` reads the asset.
"""
from __future__ import annotations

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

EV = "platform/python-sidecar/brahmagyan/l0_nakshatra.py:53"
TEST_EV = "platform/scripts/governance/__tests__/test_formgap_unset.py:1"
T = "t_unset_form"


def _un(**kw):
    return dict(column="basis_above", why="the seed leaves this key unset in every row and no writer fills it, so the live column holds no value", evidence=EV, **kw)


def _decl(unset=None, **extra):
    pn = dict(why=fs.WHY, closed_columns=[dict(column="kind", why="one of two words the seed writes", values=["a", "b"])],
              identifier_columns=[dict(column="code", why="a member of the primary key of the table", evidence=EV)],
              unset_columns=unset if unset is not None else [_un()])
    pn.update(extra)
    return {"prose_fields": [], "evidence": {"prose_fields": EV}, "prose_none": pn}


# ───────────────────────────── the validator ─────────────────────────────

def test_the_declaration_is_sound_and_the_fields_are_closed():
    assert ac.UNSET_FIELDS == ("column", "table", "why", "evidence") and ac.UNSET_MAX_COLUMNS == 16 and "unset_columns" in ac.PROSE_NONE_DECL_FIELDS
    assert ac.prose_none_problem(_decl()) is None
    doc = json.loads((pathlib.Path(ac.__file__).parent / "asset_declarations.json").read_text(encoding="utf-8"))
    assert doc["unset_declaration_fields"] == list(ac.UNSET_FIELDS) and doc["prose_none_declaration_fields"] == list(ac.PROSE_NONE_DECL_FIELDS)


@pytest.mark.parametrize("bad,needle", [
    ([], "1 to 16"),
    ("basis_above", "1 to 16"),
    ([_un(extra=1)], "unknown field"),
    ([dict(_un(), column="basis above")], "identifier"),
    ([dict(_un(), table="t;drop")], "table name"),
    ([dict(_un(), why="tbd")], "why"),
    ([dict(_un(), evidence="unverified: it is empty somewhere")], "evidence"),
    ([dict(_un(), evidence="platform/scripts/governance/golden_test_scan.py:1")], "does not mention 'basis_above'"),
    ([_un(), _un()], "listed twice"),
    ([dict(_un(), column="kind", evidence=TEST_EV)], "declared by both"),
    ([dict(_un(), column="code", evidence=TEST_EV)], "declared by both"),
])
def test_a_malformed_unset_declaration_is_refused(bad, needle):
    got = ac.prose_none_problem(_decl(unset=bad))
    assert got is not None and needle in got, got


def test_the_read_is_one_bounded_exists_that_stops_at_the_first_value():
    sql = ac.unset_read_sql("t", "c", None)
    assert sql == 'SELECT EXISTS (SELECT 1 FROM "t" WHERE "c" IS NOT NULL)::text'
    ac.set_read_scope({"t": {"where": "chart_id = 'c1'", "label": "x"}})
    try:
        scoped = ac.unset_read_sql("t", "c", dict(column="k", equals="v"))
    finally:
        ac.set_read_scope(None)
    assert "\"k\"::text = 'v'" in scoped and "(chart_id = 'c1')" in scoped and "count(" not in scoped


# ───────────────────────────── real SQL ─────────────────────────────

@pytest.fixture()
def db(monkeypatch, disposable_pg):
    pg = disposable_pg
    point_psql_at(pg, monkeypatch)
    fs.drop_tables(pg, T)
    fs.psql(pg, f"CREATE TABLE {T} (code text PRIMARY KEY, kind text, basis_above text, tags text[], n int)")
    fs.psql(pg, f"INSERT INTO {T} (code, kind, n) SELECT 'k' || g, CASE WHEN g % 2 = 0 THEN 'a' ELSE 'b' END, g FROM generate_series(1, 20) g")
    yield pg
    fs.drop_tables(pg, T)


def _m(pg, mp, decl, scope=None):
    # a real writer file gives the scope its units; what it WRITES is stood in below (the closure is about the table of this test)
    point_psql_at(pg, mp)
    mp.setattr(ac, "written_columns", lambda units, tables: {T: {"code", "kind", "basis_above", "tags", "n"}})
    cat = ac.catalog([T])
    vocab = ac.prose_vocabulary({"bg_x": decl}, {"bg_x": {T}})
    ac.set_read_scope(scope or {})
    try:
        return ac._measure_prose("bg_x", decl, dict(target_table=T), ["ga_transit_anchors.py"], cat, [], {}, (), vocab)
    finally:
        ac.set_read_scope(None)


def test_REAL_SQL_unset_columns_are_exempt_only_when_the_read_finds_them_empty(db, monkeypatch):
    fs.psql(db, f"ALTER TABLE {T} DROP COLUMN tags")
    got = _m(db, monkeypatch, _decl())
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert b["forms"]["unset"] == [dict(table=T, column="basis_above", verified=True, empty=True)] and "FORM-GAP forms CHECKED: unset" in got["Narr.agree"]["measured"]


def test_REAL_SQL_MUTATION_one_value_in_the_column_is_a_FAIL(db, monkeypatch):
    fs.psql(db, f"ALTER TABLE {T} DROP COLUMN tags")
    fs.psql(db, f"UPDATE {T} SET basis_above = 'a free sentence about the nakshatra' WHERE code = 'k7'")
    got = _m(db, monkeypatch, _decl())
    assert got["Narr.agree"]["v"] == FAIL and "declared never filled but holds a value" in got["Narr.agree"]["measured"]
    fs.psql(db, f"UPDATE {T} SET basis_above = NULL")
    assert _m(db, monkeypatch, _decl())["Narr.agree"]["v"] == NA


def test_REAL_SQL_MUTATION_an_empty_string_is_a_value_not_an_unset_column(db, monkeypatch):
    fs.psql(db, f"ALTER TABLE {T} DROP COLUMN tags")
    fs.psql(db, f"UPDATE {T} SET basis_above = '' WHERE code = 'k1'")
    assert _m(db, monkeypatch, _decl())["Narr.agree"]["v"] == FAIL


def test_REAL_SQL_MUTATION_a_column_that_does_not_exist_is_a_FAIL(db, monkeypatch):
    fs.psql(db, f"ALTER TABLE {T} DROP COLUMN tags")
    got = _m(db, monkeypatch, _decl(unset=[dict(_un(), column="basis_below", evidence="platform/python-sidecar/brahmagyan/l0_nakshatra.py:53")]))
    assert got["Narr.agree"]["v"] == FAIL and "not a column" in got["Narr.agree"]["measured"]


def test_REAL_SQL_MUTATION_the_unset_form_does_not_hide_an_undeclared_open_column(db, monkeypatch):
    got = _m(db, monkeypatch, _decl())                                                       # `tags` (text[]) is open text nobody declared
    assert got["Narr.agree"]["v"] == FAIL and "tags" in got["Narr.agree"]["measured"]


def test_REAL_SQL_a_read_that_did_not_happen_is_no_detector_never_pass(db, monkeypatch):
    fs.psql(db, f"ALTER TABLE {T} DROP COLUMN tags")
    monkeypatch.setattr(ac, "scalar", lambda q: (_ for _ in ()).throw(ac.Unknown("ERROR:  canceling statement due to statement timeout")))
    tables = {T: (["code", "kind", "basis_above"], {"code": "text", "kind": "text", "basis_above": "text"}, None)}
    forms = ac.formgap_reads("bg_x", _decl(), tables, T, udts={})
    assert forms["unset"][(T, "basis_above")].get("unread")
    got = ac.grade_prose_none("bg_x", _decl(), tables, T, {}, forms=forms)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "unset" in got["Narr.agree"]["measured"]


def test_REAL_SQL_the_measured_chart_scope_slices_the_read(db, monkeypatch):
    fs.psql(db, f"ALTER TABLE {T} DROP COLUMN tags")
    fs.psql(db, f"UPDATE {T} SET basis_above = 'late value' WHERE n > 15")
    scope = {T: dict(where="n <= 10", label="the measured slice")}
    assert _m(db, monkeypatch, _decl(), scope=scope)["Narr.agree"]["v"] == NA                # the value sits outside the slice
    assert _m(db, monkeypatch, _decl())["Narr.agree"]["v"] == FAIL


def test_the_rollup_guard_refuses_an_unset_block_it_cannot_trust(db, monkeypatch):
    fs.psql(db, f"ALTER TABLE {T} DROP COLUMN tags")
    rec = _m(db, monkeypatch, _decl())["Narr.agree"]
    assert ac.prose_none_na_problem("Narr.agree", rec) is None
    forged = json.loads(json.dumps(rec))
    forged["prose_none"]["forms"]["unset"][0]["empty"] = False
    assert "does not show the column empty" in ac.prose_none_na_problem("Narr.agree", forged)
    forged = json.loads(json.dumps(rec))
    forged["prose_none"]["forms"]["unset"][0]["verified"] = False
    assert "is not verified" in ac.prose_none_na_problem("Narr.agree", forged)


def test_REAL_SQL_an_array_of_text_column_can_be_declared_unset_and_a_single_element_is_a_FAIL(db, monkeypatch):
    d = _decl(unset=[_un(), dict(_un(), column="tags", evidence=TEST_EV)])
    assert ac.prose_none_problem(d) is None
    assert _m(db, monkeypatch, d)["Narr.agree"]["v"] == NA
    fs.psql(db, f"UPDATE {T} SET tags = ARRAY['a note'] WHERE code = 'k3'")
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "tags" in got["Narr.agree"]["measured"]
    fs.psql(db, f"UPDATE {T} SET tags = '{{}}' WHERE code = 'k3'")
    assert _m(db, monkeypatch, d)["Narr.agree"]["v"] == FAIL                                 # an empty array is a value, not an unset column
