"""test_e6_stamp_columns.py: E6 STAMP, REGISTRY_REVISION 15: `null_convention.stamp_columns`, a declared word for a WRITE-TIME stamp column.

The conflict (bg_phaladeepika_latta): the table's 8 rows were written in one seed transaction, so created_at holds ONE value on every row, and the S1 detector fails any column
that holds one value on every row unless it is declared constant. Declaring a write-time stamp 'constant' is a claim known to be false in kind, so the strategist ruled a separate
honest word: `stamp_columns: [{column, why}]`. The detector requires the column to be NOT NULL and a timestamp (timestamp / timestamptz) and exempts it from the constant test;
NOTHING ELSE is exempted. A stamp column that is nullable or not a timestamp is refused (NO_DETECTOR with the disagreement reported, never PASS; at declaration time only the shape
can be refused: the validator has no database). Offline: stubs; the REAL_SQL tests run the same SQL on the disposable Postgres."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _decl_version  # noqa: E402
import test_e6_s1_null_convention as s1  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

NA, NO_DET, PASS, FAIL, PARTIAL, ERRORED = ac.NA, ac.NO_DET, ac.PASS, ac.FAIL, ac.PARTIAL, ac.ERRORED
SD, BR = s1.SD, s1.BR
EV = s1.EV
STAMP_TEXT = ("stamp columns (write-time, constant test exempted; checked instead: NOT NULL timestamp, no NULL row, no infinity, -infinity or value at or before epoch + 1 day): "
              "created_at (timestamptz, NOT NULL, 1 distinct value(s) over 8 row(s))")
STAMP_WHY = "written by the seed transaction, one shared write time"
STAMP = dict(column="created_at", why=STAMP_WHY)
NON_STAMP_CONSTS = [c for c in s1.CONST_COLS if c != "created_at"]


_DEFAULT = object()


def SSPEC(scope="exactly", stamps=_DEFAULT, **over):
    """The latta convention with created_at as a STAMP column (not declared constant)."""
    d = s1.SPEC(scope, constants=[dict(column=c, why="one seed version, one shared passage") for c in NON_STAMP_CONSTS],
                stamp_columns=[dict(STAMP)] if stamps is _DEFAULT else stamps)
    d.update(over)
    return d


def SSTATS(rows=8, facts=None, **over):
    """The fetched stats of the clean latta table with created_at as ONE shared timestamp, plus the catalog's stamp facts."""
    st = s1.STATS(rows)
    st["cols"]["created_at"] = dict(nulls=0, distinct=1, fallback=0, sentinel=0, sole="2026-01-01 00:00:00+00")
    for c, d in over.items():
        st["cols"][c] = dict(st["cols"][c], **d)
    st["stamp_facts"] = {"created_at": dict(type="timestamptz", notnull=True)} if facts is None else facts
    return st


def _grade(spec=None, stats=None, types=s1.LATTA_TYPES, cols=s1.LATTA_COLS):
    return ac.grade_null_convention(spec or SSPEC(), list(cols), types, stats or SSTATS())


def _bad(nc, match, e=None):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_null_convention_declaration("a", nc, e or {})


# ═════════════════════════ the declaration validator ═════════════════════════

def test_validator_accepts_stamp_columns_alone_and_beside_the_other_words():
    for nc in (SSPEC(), SSPEC(stamps=[]), SSPEC(stamps=[STAMP, dict(column="updated_at", why="refreshed by the same write, one shared time")]),
               s1.SPEC(nullable=[], constants=[], stamp_columns=[STAMP]), s1.SPEC()):                              # the last: no stamp_columns key at all
        ac.validate_declarations(s1._doc(dict(null_convention=nc)))
    nc = SSPEC()
    nc.pop("stamp_columns")
    ac.validate_declarations(s1._doc(dict(null_convention=nc)))                                                     # the key is optional: every existing declaration stays valid


@pytest.mark.parametrize("stamps, match", [
    (None, "stamp_columns must be a list"), ({"column": "created_at", "why": STAMP_WHY}, "stamp_columns must be a list"), ("created_at", "stamp_columns must be a list"),
    (["created_at"], "stamp_columns entry 0 must be an object"), ([7], "stamp_columns entry 0 must be an object"),
    ([dict(STAMP, extra=1)], "unknown field"),
    ([dict(why=STAMP_WHY)], r"stamp_columns\[0\]\.column"), ([dict(STAMP, column="a b")], r"stamp_columns\[0\]\.column"), ([dict(STAMP, column='c"')], r"stamp_columns\[0\]\.column"),
    ([dict(STAMP, column=3)], r"stamp_columns\[0\]\.column"), ([dict(STAMP, column="")], r"stamp_columns\[0\]\.column"),
    ([dict(column="created_at")], r"stamp_columns\[0\]\.why"), ([dict(STAMP, why="")], r"stamp_columns\[0\]\.why"), ([dict(STAMP, why="  ")], r"stamp_columns\[0\]\.why"),
    ([dict(STAMP, why="N/A")], r"stamp_columns\[0\]\.why"), ([dict(STAMP, why="two words")], r"stamp_columns\[0\]\.why"), ([dict(STAMP, why="a\nb c d e f g h i j")], r"stamp_columns\[0\]\.why"),
    ([dict(STAMP, why=" padded reason for the column ")], r"stamp_columns\[0\]\.why"), ([dict(STAMP, why=7)], r"stamp_columns\[0\]\.why"), ([dict(STAMP, why="x" * 1201)], r"stamp_columns\[0\]\.why"),
    ([STAMP, dict(STAMP)], "declared twice"),
    ([dict(column=f"c{i}", why=STAMP_WHY) for i in range(17)], "not a convention"),
])
def test_validator_refuses_a_malformed_stamp_columns_declaration(stamps, match):
    _bad(SSPEC(stamps=stamps), match)


def test_validator_the_cap_on_the_list_length_is_the_literal_16():
    assert ac.NULL_MAX_STAMPS == 16                                                                                 # pinned as a literal: the cap cannot drift with the constant
    ok = [dict(column=f"c{i}", why=STAMP_WHY) for i in range(16)]
    ac.validate_null_convention_declaration("a", SSPEC(stamps=ok), {})                                              # 16 accepted
    _bad(SSPEC(stamps=ok + [dict(column="c16", why=STAMP_WHY)]), "not a convention")                                # 17 refused


def test_validator_a_column_may_not_be_declared_in_two_words():
    _bad(SSPEC(constants=[dict(column="created_at", why="one seed version, one shared passage")]), "stamp column AND as nullable or constant")      # stamp AND constant
    _bad(s1.SPEC(nullable=[s1.NULLABLE(None, column="created_at")], constants=[], stamp_columns=[STAMP]), "stamp column AND as nullable or constant")   # stamp AND nullable
    _bad(SSPEC(nullable=[s1.NULLABLE(None, scope_obj=dict(key_column="created_at", null_for=["x"], mode="only"))]), "scope key_column")              # stamp as a scope key
    _bad(SSPEC(allowed_literals=[dict(column="created_at", values=["x"], why="a real value of this column, said once")]), "stamp columns")           # stamp with an allowed literal
    # and the original two-word rule is unchanged
    _bad(s1.SPEC(nullable=[s1.NULLABLE(None, column="notes")], constants=[dict(column="notes", why="one seed version, one shared passage")]), "both nullable and constant")


def test_validator_a_stamp_column_is_not_a_declared_prose_field():
    _bad(SSPEC(), "also a declared prose field", e=dict(prose_fields=["created_at"]))
    _bad(SSPEC(), "also a declared prose field", e=dict(prose_fields=["created_at.$.x"]))
    ac.validate_null_convention_declaration("a", SSPEC(), dict(prose_fields=["effect_description"]))


def test_the_declarations_file_lists_the_new_field_and_only_the_latta_declares_a_convention():
    raw = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
    assert raw["null_convention_declaration_fields"] == list(ac.NULL_CONVENTION_DECL_FIELDS) and "stamp_columns" in ac.NULL_CONVENTION_DECL_FIELDS
    assert raw["version"] == _decl_version.CURRENT          # 1.10.0 with DECL-LATTA (#2991); 1.11.0 with DECL-LATTA-NULL (the first null_convention + stamp_columns)
    assert "stamp_columns" in raw["description"]
    assert [a for a, e in raw["assets"].items() if "null_convention" in e] == ["bg_phaladeepika_latta"]
    ac.load_asset_declarations()


# ═════════════════════════ the pure grader: both ways ═════════════════════════

def test_a_stamp_column_with_all_equal_timestamps_passes_and_the_text_names_it_separately():
    r = _grade()
    assert r["v"] == PASS, r
    assert STAMP_TEXT in r["measured"], r["measured"]
    assert r["convention"]["stamp_columns"] == ["created_at"] and r["convention"]["stamp_nulls"] == {}
    assert r["convention"]["undeclared_constants"] == [] and r["convention"]["constant_violations"] == []


def test_the_same_column_not_declared_stamp_or_constant_fails_the_original_conflict():
    r = _grade(spec=SSPEC(stamps=[]), stats=SSTATS())
    assert r["v"] == FAIL and r["convention"]["undeclared_constants"] == ["created_at"], r
    assert "created_at" in r["measured"] and "not declared constant" in r["measured"]


def test_declared_constant_still_passes_for_the_same_column_the_s1_form_is_unchanged():
    r = ac.grade_null_convention(s1.SPEC(), list(s1.LATTA_COLS), s1.LATTA_TYPES, s1.STATS())
    assert r["v"] == PASS and "stamp columns" not in r["measured"]


def test_a_stamp_column_that_varies_also_passes_the_exemption_is_not_a_requirement_to_be_constant():
    assert _grade(stats=SSTATS(created_at=dict(distinct=8, sole=None)))["v"] == PASS


def test_a_stamp_exempts_nothing_else_another_one_value_column_still_fails():
    r = _grade(spec=SSPEC(constants=[dict(column=c, why="one seed version, one shared passage") for c in NON_STAMP_CONSTS if c != "source_citation"]))
    assert r["v"] == FAIL and r["convention"]["undeclared_constants"] == ["source_citation"], r
    assert "created_at" not in r["convention"]["undeclared_constants"]


def test_a_stamp_exempts_nothing_else_an_undeclared_null_a_fallback_and_a_scope_violation_still_fail():
    r = _grade(stats=SSTATS(count_from_graha=dict(nulls=1)))
    assert r["v"] == FAIL and r["convention"]["undeclared_nulls"] == {"count_from_graha": 1}, r
    r = _grade(stats=SSTATS(direction=dict(fallback=2)))
    assert r["v"] == FAIL and r["convention"]["fallbacks"] == {"direction": 2}, r
    r = _grade(stats=SSTATS(effect_description=dict(null_outside=1, null_outside_keys=["Jupiter"])))
    assert r["v"] == FAIL and "outside the declared keys" in r["measured"], r
    r = _grade(stats=SSTATS(table_version=dict(distinct=2)))                                                        # a declared constant that varies
    assert r["v"] == FAIL and r["convention"]["constant_violations"] == ["table_version"], r


def test_a_stamp_column_holding_a_null_row_fails_and_is_reported_separately_from_an_undeclared_null():
    r = _grade(stats=SSTATS(created_at=dict(nulls=1, distinct=7)))
    assert r["v"] == FAIL and r["convention"]["stamp_nulls"] == {"created_at": 1} and r["convention"]["undeclared_nulls"] == {}, r
    assert "declared stamp column" in r["measured"] and "created_at (1 row(s))" in r["measured"]
    r = _grade(stats=SSTATS(created_at=dict(nulls=8, distinct=0)))                                                  # NULL on every row
    assert r["v"] == FAIL and r["convention"]["stamp_nulls"] == {"created_at": 8}


@pytest.mark.parametrize("facts", [dict(type="timestamptz", notnull=False), dict(type="timestamp", notnull=False)])
def test_a_nullable_stamp_column_is_refused_no_detector_never_pass(facts):
    r = _grade(stats=SSTATS(facts={"created_at": facts}))
    assert r["v"] == NO_DET, r
    assert r["declaration_disagreements"][0]["field"] == "null_convention.stamp_columns.created_at" and "nullable" in r["declaration_disagreements"][0]["measured"]
    assert "refused" in r["measured"] and r["convention"]["stamp_refused"] == ["created_at"]


@pytest.mark.parametrize("typ", ["text", "date", "time", "timetz", "int4", "varchar", "jsonb", "uuid", "bool", "interval", "timestamptz[]", "_timestamptz"])
def test_a_stamp_column_that_is_not_a_timestamp_is_refused_no_detector_never_pass(typ):
    r = _grade(stats=SSTATS(facts={"created_at": dict(type=typ, notnull=True)}))
    assert r["v"] == NO_DET and typ in r["measured"] and r["declaration_disagreements"], r


def test_both_stamp_types_are_accepted_by_the_catalog_name():
    assert ac.NULL_STAMP_TYPES == ("timestamp", "timestamptz")
    for typ in ac.NULL_STAMP_TYPES:
        assert _grade(stats=SSTATS(facts={"created_at": dict(type=typ, notnull=True)}))["v"] == PASS


def test_the_refusal_comes_before_a_defect_and_before_the_row_count():
    r = _grade(stats=SSTATS(facts={"created_at": dict(type="text", notnull=True)}, count_from_graha=dict(nulls=1)))      # a defect elsewhere does not hide the refusal
    assert r["v"] == NO_DET
    r = _grade(stats=SSTATS(rows=1, facts={"created_at": dict(type="text", notnull=True)}))
    assert r["v"] == NO_DET and "refused" in r["measured"]                                                          # one row: still the refusal's reason, not 'vacuous'


def test_one_row_with_a_valid_stamp_is_the_usual_vacuous_no_detector():
    r = _grade(stats=SSTATS(rows=1))
    assert r["v"] == NO_DET and "constants and variation cannot be shown" in r["measured"]


@pytest.mark.parametrize("bad", [None, {}, "x", [], {"created_at": None}, {"created_at": {}}, {"created_at": dict(type="timestamptz")}, {"created_at": dict(notnull=True)},
                                 {"created_at": dict(type="timestamptz", notnull="yes")}, {"created_at": dict(type=3, notnull=True)}, {"other": dict(type="timestamptz", notnull=True)}])
def test_missing_or_malformed_catalog_facts_are_unknown_never_a_pass(bad):
    st = SSTATS()
    if bad is None:
        del st["stamp_facts"]
    else:
        st["stamp_facts"] = bad
    with pytest.raises(ac.Unknown):
        _grade(stats=st)


def test_facts_are_not_required_when_no_stamp_is_declared():
    st = SSTATS()
    del st["stamp_facts"]
    assert _grade(spec=SSPEC(stamps=[]), stats=dict(st, cols=dict(st["cols"], created_at=dict(nulls=0, distinct=8, fallback=0))))["v"] == PASS


def test_a_declared_stamp_column_the_table_does_not_carry_fails_before_any_stats_are_read():
    cols = [c for c in s1.LATTA_COLS if c != "created_at"]
    r = ac.grade_null_convention(SSPEC(), cols, s1.LATTA_TYPES, None)
    assert r["v"] == FAIL and r["convention"]["absent"] == ["created_at"], r


def test_the_declared_columns_include_the_stamp_columns():
    assert "created_at" in ac._null_declared_columns(SSPEC())
    assert "created_at" not in ac._null_declared_columns(SSPEC(stamps=[]))


# ═════════════════════════ the check around it, the fetch ═════════════════════════

def _check(spec, types=s1.LATTA_TYPES, cols=s1.LATTA_COLS, scope=("", "whole-table (table has no chart_id column)")):
    return ac.null_convention_check(dict(spec, table="bg_phaladeepika_latta"), {"bg_phaladeepika_latta": (list(cols), dict(types), {})}, {"bg_phaladeepika_latta"}, scope)


@pytest.mark.parametrize("typ", ["text", "date", "integer", "character varying", "USER-DEFINED", "time without time zone", "interval", "ARRAY", "jsonb"])
def test_a_stamp_column_whose_data_type_is_not_a_timestamp_is_refused_before_any_select(monkeypatch, typ):
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: pytest.fail("a refused declaration reads nothing"))
    monkeypatch.setattr(ac, "scalar", lambda sql: pytest.fail("a refused declaration reads nothing"))
    r = _check(SSPEC(), types=dict(s1.LATTA_TYPES, created_at=typ))
    assert r["v"] == NO_DET and "refused" in r["measured"] and "created_at" in r["measured"], r
    assert r["declaration_disagreements"][0]["field"] == "null_convention.stamp_columns.created_at"


@pytest.mark.parametrize("typ", ["timestamp with time zone", "timestamp without time zone", "timestamp(3) with time zone", "TIMESTAMP WITH TIME ZONE"])
def test_both_timestamp_data_types_pass_the_early_screen(monkeypatch, typ):
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: SSTATS())
    assert _check(SSPEC(), types=dict(s1.LATTA_TYPES, created_at=typ))["v"] == PASS


def test_the_early_screen_only_looks_at_the_declared_stamp_columns(monkeypatch):
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: SSTATS())
    assert _check(SSPEC(), types=dict(s1.LATTA_TYPES, direction="date"))["v"] == PASS                                 # an undeclared non-timestamp column is not a stamp refusal
    r = _check(SSPEC(stamps=[]), types=dict(s1.LATTA_TYPES, created_at="text"))                                       # nothing declared: no stamp screen
    assert r["v"] == FAIL and "refused" not in r["measured"] and "declaration_disagreements" not in r, r              # (was `in (PASS, FAIL, PARTIAL, ERRORED)`: that also passed a refusal-free NO_DETECTOR / a screen that ran)
    assert r["convention"]["undeclared_constants"] == ["created_at"] and "stamp_refused" not in r["convention"]    # the ordinary S1 reading of a one-value column that is neither stamp nor constant


def test_a_stamp_declaration_naming_a_missing_column_fails_in_the_check_before_any_select(monkeypatch):
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: pytest.fail("a missing column reads nothing"))
    r = _check(SSPEC(), cols=[c for c in s1.LATTA_COLS if c != "created_at"], types={c: t for c, t in s1.LATTA_TYPES.items() if c != "created_at"})
    assert r["v"] == FAIL and r["convention"]["absent"] == ["created_at"]


def _two_stub(monkeypatch, table_answer, facts_answer):
    """Stub `scalar`: the pg_catalog stamp-facts SELECT and the table SELECT are told apart by their text; the catalog kinds read is stubbed from the data_type strings."""
    got = {"facts": [], "table": []}
    monkeypatch.setattr(ac, "null_fetch_column_kinds", lambda table, cols: {c: ac._null_type_kind(s1.LATTA_TYPES.get(c, "text")) for c in cols})

    def scalar(sql):
        if "pg_attribute" in sql:
            got["facts"].append(sql)
            return facts_answer
        got["table"].append(sql)
        return table_answer
    monkeypatch.setattr(ac, "scalar", scalar)
    return got


def _table_json():
    st = SSTATS()
    return json.dumps({"rows": st["rows"], "cols": st["cols"]})


def test_the_fetch_issues_one_read_only_catalog_select_for_the_stamp_facts_only_when_stamps_are_declared(monkeypatch):
    got = _two_stub(monkeypatch, _table_json(), json.dumps({"created_at": {"t": "timestamptz", "nn": True}}))
    st = ac.null_convention_fetch("bg_phaladeepika_latta", s1.LATTA_COLS, s1.LATTA_TYPES, SSPEC(), " WHERE chart_id = 'c'")
    assert st["stamp_facts"] == {"created_at": dict(type="timestamptz", notnull=True)} and len(got["facts"]) == 1 and len(got["table"]) == 1
    sql = got["facts"][0]
    assert sql.lstrip().upper().startswith("SELECT") and "attnotnull" in sql and "typnotnull" in sql and "typbasetype" in sql
    assert "FROM pg_attribute" in sql and not __import__("re").search(r"\b(insert|update|delete|drop|alter|create|truncate|grant)\b", sql, __import__("re").I)
    assert "chart_id" not in sql                                                                                    # the catalog read is not scoped to a chart
    got = _two_stub(monkeypatch, _table_json(), "{}")
    ac.null_convention_fetch("bg_phaladeepika_latta", s1.LATTA_COLS, s1.LATTA_TYPES, SSPEC(stamps=[]), "")
    assert got["facts"] == []                                                                                       # no stamp declared: no extra read at all


@pytest.mark.parametrize("answer", ["", "not json", "[]", "{}", json.dumps({"created_at": {"t": "timestamptz"}}), json.dumps({"created_at": {"nn": True}}),
                                    json.dumps({"created_at": {"t": "timestamptz", "nn": "t"}}), json.dumps({"other": {"t": "timestamptz", "nn": True}})])
def test_the_fetch_raises_unknown_on_an_unparseable_or_incomplete_catalog_answer(monkeypatch, answer):
    _two_stub(monkeypatch, _table_json(), answer)
    with pytest.raises(ac.Unknown):
        ac.null_convention_fetch("bg_phaladeepika_latta", s1.LATTA_COLS, s1.LATTA_TYPES, SSPEC(), "")


def test_the_stamp_facts_fetch_refuses_a_malformed_identifier_before_any_sql(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda sql: pytest.fail("no SQL for a malformed identifier"))
    for t, cols in (('t"', ["a"]), ("t", ['a"b']), ("t;drop", ["a"]), (3, ["a"]), ("t", [3])):
        with pytest.raises(ac.Unknown):
            ac.null_fetch_stamp_facts(t, cols)


def test_a_failed_stamp_facts_read_degrades_only_this_check_to_errored(monkeypatch):
    _two_stub(monkeypatch, _table_json(), "")
    assert _check(SSPEC())["v"] == ERRORED


# ═════════════════════════ the lift, the block, the reader's binding ═════════════════════════

ENTRIES = s1.ENTRIES


def _earn(stamps, conv=None):
    sd, br = s1._graders()
    decl = dict(evidence=EV, why="w", stamp_columns=[dict(column=c, why=STAMP_WHY) for c in stamps])
    return ac.earn_null_lift(ENTRIES, sd, br, conv or s1._conv(), decl)


def test_the_lift_block_carries_the_stamp_columns_not_among_the_covered_columns():
    out = _earn(["created_at"])
    for crit in (SD, BR):
        nc = out[crit]["null_convention"]
        assert nc["stamp_columns"] == ["created_at"] and nc["columns"] == ENTRIES and ac.null_lift_problem(out[crit]) is None
    assert ac.rollup_asset("L0", out)["Null"]["v"] == PASS
    assert _earn([])[SD]["null_convention"]["stamp_columns"] == []


@pytest.mark.parametrize("forge", [
    lambda n: n.update(stamp_columns="created_at"), lambda n: n.update(stamp_columns=None), lambda n: n.update(stamp_columns={"created_at": 1}), lambda n: n.update(stamp_columns=[7]),
    lambda n: n.update(stamp_columns=[""]), lambda n: n.update(stamp_columns=["created_at", "created_at"]), lambda n: n.update(stamp_columns=["effect_description"]),
])
def test_a_malformed_stamp_columns_block_is_not_honoured(forge):
    out = _earn(["created_at"])
    forge(out[SD]["null_convention"])
    assert ac.null_lift_problem(out[SD]) is not None and ac.null_lift_earned(SD, out[SD], out) is False
    assert ac.rollup_asset("L0", out)["Null"]["v"] == PARTIAL


def test_a_block_without_the_key_is_the_empty_list_and_still_earns():
    out = _earn([])
    for c in (SD, BR):
        del out[c]["null_convention"]["stamp_columns"]
    assert ac.null_lift_earned(SD, out[SD], out) is True


def test_two_blocks_that_disagree_on_the_stamp_columns_are_not_one_convention():
    out = _earn(["created_at"])
    out[BR]["null_convention"]["stamp_columns"] = []
    assert ac.null_lift_earned(SD, out[SD], out) is False and ac.null_lift_earned(BR, out[BR], out) is False
    assert ac.rollup_asset("L0", out)["Null"]["v"] == PARTIAL
    out = _earn(["created_at"])
    out[BR]["null_convention"]["stamp_columns"] = ["updated_at"]
    assert ac.null_lift_earned(SD, out[SD], out) is False
    out = _earn(["created_at"])
    del out[BR]["null_convention"]["stamp_columns"]                                                                 # absent == [] on one side, ['created_at'] on the other
    assert ac.null_lift_earned(SD, out[SD], out) is False


def test_the_stamp_never_widens_what_earns_a_convention_that_fails_still_flips_the_cell():
    r = _grade(stats=SSTATS(count_from_graha=dict(nulls=1)))
    sd, br = s1._graders()
    out = ac.earn_null_lift(ENTRIES, sd, br, dict(r, convention=r["convention"]), dict(evidence=EV, why="w", stamp_columns=[STAMP]))
    assert out[BR]["v"] == FAIL and ac.rollup_asset("L0", out)["Null"]["v"] == FAIL
    r = _grade(stats=SSTATS(facts={"created_at": dict(type="text", notnull=True)}))                                  # a refused stamp: NO_DETECTOR: nothing lifted, cap stays
    assert r["v"] == NO_DET and s1._earn(r) == {}


# ═════════════════════════ measure(): the glue, stubbed ═════════════════════════

def test_through_measure_prose_a_stamp_declaration_earns_the_lift_and_the_block_names_it(monkeypatch):
    m = s1._prose(monkeypatch, dict(null_convention=SSPEC(), prose_fields=None), stats=SSTATS())
    assert m[SD]["v"] == PASS and m[BR]["v"] == PASS, (m[SD], m[BR])
    assert m[SD]["null_convention"]["stamp_columns"] == ["created_at"] and m[SD]["null_convention"]["columns"] == ["effect_description"]
    assert "stamp columns (write-time, constant test exempted" in m[SD]["measured"]
    assert ac.rollup_asset("L0", m)["Null"]["v"] == PASS


def test_through_measure_prose_the_same_asset_without_the_word_fails_the_conflict(monkeypatch):
    m = s1._prose(monkeypatch, dict(null_convention=SSPEC(stamps=[]), prose_fields=None), stats=SSTATS())
    assert m[BR]["v"] == FAIL and ac.rollup_asset("L0", m)["Null"]["v"] == FAIL


def test_through_measure_prose_a_nullable_stamp_keeps_the_cap_and_says_why(monkeypatch):
    m = s1._prose(monkeypatch, dict(null_convention=SSPEC(), prose_fields=None), stats=SSTATS(facts={"created_at": dict(type="timestamptz", notnull=False)}))
    assert m[SD]["v"] != PASS and m[BR]["v"] != PASS and m[SD]["null_convention"]["v"] == NO_DET and m[SD]["null_convention"]["verified"] is False
    assert ac.rollup_asset("L0", m)["Null"]["v"] != PASS


# ═════════════════════════ REAL SQL: the same statements on a disposable Postgres ═════════════════════════

LATTA_STAMP_SQL = list(s1.LATTA_SQL)                                    # created_at timestamptz NOT NULL DEFAULT '2026-01-01': one value on all 8 rows


def _variant(old, new):
    out = [x.replace(old, new) for x in s1.LATTA_SQL]
    assert out != s1.LATTA_SQL, old
    return out


def _real_check(monkeypatch, pg, setup, spec=None, types=None):
    s3._real(monkeypatch, pg, setup)
    return ac.null_convention_check(dict(spec or SSPEC(), table="latta_t"), {"latta_t": (list(s1.REAL_COLS), dict(types or s1.REAL_TYPES), {})}, {"latta_t"},
                                    ("", "whole-table (table has no chart_id column)"))


def test_REAL_SQL_the_original_conflict_the_shared_created_at_passes_as_a_stamp_and_fails_when_undeclared(monkeypatch, disposable_pg):
    r = _real_check(monkeypatch, disposable_pg, LATTA_STAMP_SQL)
    assert r["v"] == PASS, r
    assert STAMP_TEXT in r["measured"]
    r = _real_check(monkeypatch, disposable_pg, LATTA_STAMP_SQL, spec=SSPEC(stamps=[]))                             # the SAME column, neither stamp nor constant
    assert r["v"] == FAIL and r["convention"]["undeclared_constants"] == ["created_at"], r
    r = _real_check(monkeypatch, disposable_pg, LATTA_STAMP_SQL, spec=s1.SPEC(table="latta_t"))                      # declared constant (the S1 way): still PASS, no stamp text
    assert r["v"] == PASS and "stamp columns" not in r["measured"]


def test_REAL_SQL_a_stamp_exempts_nothing_else(monkeypatch, disposable_pg):
    for sql, key in ((["UPDATE latta_t SET count_from_graha = NULL WHERE graha = 'Sun';"], "undeclared_nulls"),
                     (["UPDATE latta_t SET source_citation = 'other cite' WHERE graha = 'Sun';"], "constant_violations"),
                     (["UPDATE latta_t SET direction = 'N/A' WHERE graha = 'Sun';"], "fallbacks"),
                     (["UPDATE latta_t SET effect_description = NULL WHERE graha = 'Jupiter';"], "scope_violations")):
        r = _real_check(monkeypatch, disposable_pg, LATTA_STAMP_SQL + sql)
        assert r["v"] == FAIL and r["convention"][key], (key, r)
    r = _real_check(monkeypatch, disposable_pg, LATTA_STAMP_SQL, spec=SSPEC(constants=[dict(column=c, why="one seed version, one shared passage") for c in NON_STAMP_CONSTS if c != "verse_ref"]))
    assert r["v"] == FAIL and r["convention"]["undeclared_constants"] == ["verse_ref"]                              # another one-value column is still an undeclared constant


def test_REAL_SQL_a_varied_stamp_passes_too(monkeypatch, disposable_pg):
    r = _real_check(monkeypatch, disposable_pg, LATTA_STAMP_SQL + ["UPDATE latta_t SET created_at = '2026-01-02'::timestamptz + (count_from_graha || ' seconds')::interval;"])
    assert r["v"] == PASS and "created_at (timestamptz, NOT NULL, 8 distinct" in r["measured"], r


def test_REAL_SQL_a_nullable_timestamp_column_is_refused_even_with_no_NULL_row(monkeypatch, disposable_pg):
    r = _real_check(monkeypatch, disposable_pg, _variant("created_at timestamptz NOT NULL DEFAULT", "created_at timestamptz DEFAULT"))
    assert r["v"] == NO_DET and "nullable" in r["measured"] and r["declaration_disagreements"][0]["measured"] == "type timestamptz, nullable", r


def test_REAL_SQL_a_column_dropped_to_nullable_with_a_NULL_row_is_refused_not_failed(monkeypatch, disposable_pg):
    r = _real_check(monkeypatch, disposable_pg, LATTA_STAMP_SQL + ["ALTER TABLE latta_t ALTER COLUMN created_at DROP NOT NULL;", "UPDATE latta_t SET created_at = NULL WHERE graha = 'Sun';"])
    assert r["v"] == NO_DET and r["v"] != PASS, r


@pytest.mark.parametrize("ddl, claimed, kind", [
    ("created_at text NOT NULL DEFAULT '2026-01-01'", "timestamp with time zone", "text"),                          # the table is text, the types map (information_schema) claims a timestamp: the CATALOG decides
    ("created_at text NOT NULL DEFAULT '2026-01-01'", "text", "text"),                                              # ... and the early screen refuses a text column before any SELECT
    ("created_at date NOT NULL DEFAULT '2026-01-01'", "date", "date"),
    ("created_at date NOT NULL DEFAULT '2026-01-01'", "timestamp with time zone", "date"),
    ("created_at integer NOT NULL DEFAULT 5", "integer", "int4"),
    ("created_at time NOT NULL DEFAULT '10:00'", "time without time zone", "time"),
])
def test_REAL_SQL_a_stamp_column_that_is_not_a_timestamp_is_refused(monkeypatch, disposable_pg, ddl, claimed, kind):
    setup = _variant("created_at timestamptz NOT NULL DEFAULT '2026-01-01'", ddl)
    r = _real_check(monkeypatch, disposable_pg, setup, types=dict(s1.REAL_TYPES, created_at=claimed))
    assert r["v"] == NO_DET and r["declaration_disagreements"][0]["field"] == "null_convention.stamp_columns.created_at", r
    if "timestamp" in claimed:      # the types map claims a timestamp: the early screen passes and the CATALOG's type is what is reported (was `kind in .. or claimed in ..`: either string anywhere passed)
        assert f"created_at is type {kind}, NOT NULL" in r["measured"] and "the table contradicts the declaration" in r["measured"], r
        assert r["convention"]["stamp_refused"] == ["created_at"]
    else:                           # the early screen refuses on the information_schema type and reads nothing
        assert f"(created_at is {claimed})" in r["measured"] and "nothing read" in r["measured"], r


def test_REAL_SQL_timestamp_without_time_zone_passes(monkeypatch, disposable_pg):
    r = _real_check(monkeypatch, disposable_pg, _variant("created_at timestamptz NOT NULL DEFAULT '2026-01-01'", "created_at timestamp NOT NULL DEFAULT '2026-01-01'"),
                    types=dict(s1.REAL_TYPES, created_at="timestamp without time zone"))
    assert r["v"] == PASS and "created_at (timestamp, NOT NULL" in r["measured"], r


def test_REAL_SQL_a_domain_over_a_timestamp_is_resolved_and_its_not_null_counts(monkeypatch, disposable_pg):
    base = "created_at timestamptz NOT NULL DEFAULT '2026-01-01'"
    dom = lambda ddl_dom, ddl_col: [ddl_dom] + _variant(base, ddl_col)                                                # noqa: E731
    r = _real_check(monkeypatch, disposable_pg, dom("CREATE DOMAIN ts_nn AS timestamptz NOT NULL;", "created_at ts_nn DEFAULT '2026-01-01'"))
    assert r["v"] == PASS, r                                                                                          # NOT NULL declared on the domain: the catalog guarantees it
    r = _real_check(monkeypatch, disposable_pg, dom("CREATE DOMAIN ts_n AS timestamptz;", "created_at ts_n DEFAULT '2026-01-01'"))
    assert r["v"] == NO_DET and "nullable" in r["measured"], r                                                        # a plain domain over a timestamp, column nullable
    r = _real_check(monkeypatch, disposable_pg, dom("CREATE DOMAIN ts_n2 AS timestamptz;", "created_at ts_n2 NOT NULL DEFAULT '2026-01-01'"))
    assert r["v"] == PASS, r                                                                                          # the column's own NOT NULL on a domain column
    r = _real_check(monkeypatch, disposable_pg, dom("CREATE DOMAIN txt_d AS text NOT NULL;", "created_at txt_d DEFAULT '2026-01-01'"))
    assert r["v"] == NO_DET and "text" in r["measured"], r                                                            # a domain over text is not a timestamp


def test_REAL_SQL_the_whole_chain_lifts_the_cap_and_a_refused_stamp_never_does(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_STAMP_SQL)
    cat = dict(s1._cat(table="latta_t"), keys={"latta_t": [["table_version", "graha"]]})
    r = dict(target_table="latta_t", count_sql="SELECT count(*) FROM latta_t")
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=dict(SSPEC(), table="latta_t"), prose_fields=None), r, None, cat, [], set(), (), set())
    assert m[SD]["v"] == PASS and m[BR]["v"] == PASS and ac.rollup_asset("L0", m)["Null"]["v"] == PASS, (m[SD], m[BR])
    assert m[SD]["null_convention"]["stamp_columns"] == ["created_at"] and ac.null_lift_earned(SD, m[SD], m)
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=dict(SSPEC(stamps=[]), table="latta_t"), prose_fields=None), r, None, cat, [], set(), (), set())
    assert ac.rollup_asset("L0", m)["Null"]["v"] == FAIL                                                              # the undeclared one-value column flips the cell
    s3._real(monkeypatch, disposable_pg, _variant("created_at timestamptz NOT NULL DEFAULT", "created_at timestamptz DEFAULT"))
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=dict(SSPEC(), table="latta_t"), prose_fields=None), r, None, cat, [], set(), (), set())
    assert ac.rollup_asset("L0", m)["Null"]["v"] != PASS and m[SD]["null_convention"]["v"] == NO_DET


STAMP_CHART_SQL = [x.replace("table_version text NOT NULL)", "table_version text NOT NULL, created_at timestamptz NOT NULL DEFAULT now())") for x in s1.CHART_SQL]
CS_STAMP_TYPES = dict(s1.CS_TYPES, created_at="timestamp with time zone")


def _cs_stamp_spec():
    return dict(table="cs_t", nullable=[s1.NULLABLE("exactly")], constants=[dict(column="chart_id", why=s1.WHY), dict(column="table_version", why=s1.WHY)],
                stamp_columns=[dict(STAMP)], why=s1.SPEC()["why"], evidence=EV)


def _cs_cat():
    return dict(exists={"cs_t"}, cols={"cs_t": list(CS_STAMP_TYPES)}, keys={"cs_t": [["chart_id", "graha"]]}, views=set(), types={"cs_t": dict(CS_STAMP_TYPES)}, defaults={"cs_t": {}},
                types_error=None)


def test_REAL_SQL_chart_scoped_binding_still_works_with_a_stamp_column(monkeypatch, disposable_pg):
    other = "('00000000-0000-0000-0000-000000000001','Sun',NULL,NULL,'v99','2020-01-01')"      # another chart's row: undeclared NULL, other constant, other created_at
    s3._real(monkeypatch, disposable_pg, STAMP_CHART_SQL + [f"INSERT INTO cs_t VALUES {other};"])
    r = dict(target_table="cs_t", count_sql="SELECT count(*) FROM cs_t WHERE chart_id = $1")
    m = ac._measure_prose("bg_x", dict(null_convention=_cs_stamp_spec(), prose_fields=None), r, None, _cs_cat(), [], set(), (), set())
    assert m[SD]["v"] == PASS and m[BR]["v"] == PASS, (m[SD], m[BR])                                                  # this chart's rows only: clean, one shared created_at
    assert ac.rollup_asset("L1", m)["Null"]["v"] == PASS and m[SD]["null_convention"]["stamp_columns"] == ["created_at"]
    r = dict(target_table="cs_t", count_sql="SELECT count(*) FROM cs_t")                                              # unbound whole-table read: an upper bound, never FAIL
    m = ac._measure_prose("bg_x", dict(null_convention=_cs_stamp_spec(), prose_fields=None), r, None, _cs_cat(), [], set(), (), set())
    assert m[BR]["null_convention"]["v"] == PARTIAL and m[BR]["v"] != FAIL and m[BR]["v"] != PASS


# ═════════════════════════ pin 15 ═════════════════════════

def test_revision_15_pins_the_stamp_content():
    assert ac.REGISTRY_REVISION >= 15
    for crit in (SD, BR):
        e = ac.CRITERION_REGISTRY[crit]
        assert e["revision"] == 8 and "stamp_columns" in e["applicability"] and "never PASS alone" in e["applicability"], crit      # 5: the Null writer scan reads the produced-set hop depth (residual detector D2)


def test_the_fingerprint_moves_with_each_stamp_part(monkeypatch):
    fp = ac.registry_fingerprint()
    for crit in (SD, BR):
        monkeypatch.setattr(ac, "CRITERION_REGISTRY", {**ac.CRITERION_REGISTRY, crit: dict(ac.CRITERION_REGISTRY[crit], revision=2)})
        assert ac.registry_fingerprint() != fp
        monkeypatch.undo()
        monkeypatch.setattr(ac, "CRITERION_REGISTRY", {**ac.CRITERION_REGISTRY, crit: dict(ac.CRITERION_REGISTRY[crit], applicability=ac.CRITERION_REGISTRY[crit]["applicability"].replace("stamp_columns", "x"))})
        assert ac.registry_fingerprint() != fp
        monkeypatch.undo()


def test_no_new_na_rule_or_cause_is_part_of_pin_15():
    import test_e6_na_r01_03 as r13
    assert r13.DECLARED_IDS == set(ac.NA_RULE_DECISIONS)
    assert not [k for k in ac.NA_CAUSES if k.startswith("Null.") and k not in ("Null.schema_default", "Null.blank_rows")]


SAVED = pathlib.Path("/Users/Dev/suvarna-evidence/census_fresh/1e5781a")


@pytest.mark.skipif(not (SAVED / "census_L0.json").exists(), reason="the saved baseline census is not on this machine (CI)")
def test_on_the_saved_censuses_pin_15_moves_no_cell_and_no_check():
    """Only bg_phaladeepika_latta declares a null_convention with a stamp (1.11.0), and this rolls up the SAVED measurements (no re-measure): every one of the 1143 cells keeps its saved verdict AND the very same per-check verdicts as the revision-14 reading."""
    decl = ac.load_asset_declarations()
    assert [a for a, e in decl.items() if isinstance(e, dict) and (e.get("null_convention") or {}).get("stamp_columns")] == ["bg_phaladeepika_latta"]
    n, moved = 0, []
    for L in ("L0", "L1", "L2", "L3", "L4", "L5"):
        d = json.loads((SAVED / f"census_{L}.json").read_text(encoding="utf-8"))
        saved = d["rollup"]["layers"][L]
        now = ac.rollup_census(d[L], {a["asset_id"]: ac.facts_for_asset(a, decl) for a in d[L]["assets"]})
        for aid, cells in now.items():
            for g, c in cells.items():
                n += 1
                if c["v"] != saved[aid][g]["v"] or ("checks" in saved[aid][g] and [x["v"] for x in c.get("checks", [])] != [x["v"] for x in saved[aid][g]["checks"]]):
                    moved.append((aid, g, saved[aid][g]["v"], c["v"]))
    assert n == 1143 and sorted(moved) == sorted((a, "Narr", "N/A", "NO_DETECTOR") for a in ("bg_doshas", "bg_ontology", "bg_yogas", "bo_laksana_rerank"))      # E5.7: the four converted assets read NO_DETECTOR on a saved census until re-measured with their checked prose_none (a saved unchecked N/A is no release)


def test_the_pin_15_edit_leaves_the_s1_field_helpers_alone():
    assert ac.NULL_CONVENTION_DECL_FIELDS == ("table", "nullable", "constants", "stamp_columns", "allowed_literals", "why", "evidence")
    assert ac.NULL_STAMP_FIELDS == ("column", "why")


# ═════════════════════════ review round: SENTINEL timestamps are the stamp column's literal fallback ═════════════════════════

def test_a_stamp_column_holding_a_sentinel_timestamp_fails_and_the_count_is_in_the_text():
    r = _grade(stats=SSTATS(created_at=dict(sentinel=8)))
    assert r["v"] == FAIL and r["convention"]["stamp_sentinels"] == {"created_at": 8}, r
    assert "sentinel timestamp" in r["measured"] and "created_at (8 row(s))" in r["measured"], r["measured"]
    r = _grade(stats=SSTATS(created_at=dict(sentinel=1, distinct=2)))                                              # mixed: real stamps plus ONE sentinel
    assert r["v"] == FAIL and r["convention"]["stamp_sentinels"] == {"created_at": 1}


def test_a_clean_stamp_reports_no_sentinels_and_the_block_says_so():
    r = _grade()
    assert r["v"] == PASS and r["convention"]["stamp_sentinels"] == {}


def test_a_missing_or_malformed_sentinel_count_on_a_timestamp_stamp_is_unknown():
    for bad in (None, "0", 1.5, True):
        st = SSTATS()
        if bad is None:
            del st["cols"]["created_at"]["sentinel"]
        else:
            st["cols"]["created_at"]["sentinel"] = bad
        with pytest.raises(ac.Unknown):
            _grade(stats=st)
    st = SSTATS(facts={"created_at": dict(type="text", notnull=True)})                                             # a refused stamp is never graded: it needs no sentinel count
    del st["cols"]["created_at"]["sentinel"]
    assert _grade(stats=st)["v"] == NO_DET


def test_the_sentinel_counter_is_built_in_the_columns_own_type_only_for_timestamp_stamps(monkeypatch):
    for typ in ("timestamptz", "timestamp"):
        got = _two_stub(monkeypatch, _table_json(), json.dumps({"created_at": {"t": typ, "nn": True}}))
        ac.null_convention_fetch("bg_phaladeepika_latta", s1.LATTA_COLS, s1.LATTA_TYPES, SSPEC(), "")
        sql = got["table"][0]
        assert sql.count("'sentinel'") == 1 and f"<= 'epoch'::{typ} + interval '1 day'" in sql and "= 'infinity'" in sql and "= '-infinity'" in sql, (typ, sql)
        assert not __import__("re").search(r"\b(insert|update|delete|drop|alter|create|truncate|grant)\b", sql, __import__("re").I)
    got = _two_stub(monkeypatch, _table_json(), json.dumps({"created_at": {"t": "text", "nn": True}}))              # a text stamp is refused later: no timestamp predicate may run on it
    ac.null_convention_fetch("bg_phaladeepika_latta", s1.LATTA_COLS, s1.LATTA_TYPES, SSPEC(), "")
    assert "'sentinel'" not in got["table"][0]
    got = _two_stub(monkeypatch, _table_json(), "{}")                                                               # no stamp declared: no sentinel counter at all
    ac.null_convention_fetch("bg_phaladeepika_latta", s1.LATTA_COLS, s1.LATTA_TYPES, SSPEC(stamps=[]), "")
    assert "'sentinel'" not in got["table"][0]


def test_the_sentinel_predicate_refuses_a_non_timestamp_type():
    for typ in ("date", "text", "int4", ""):
        with pytest.raises(ac.Unknown):
            ac._null_stamp_sentinel_sql("c", typ)


# the accounting is a strict partition: every column of the table is in EXACTLY ONE of: fallback-checked, element-not-inspected, type-cannot-hold-one (not examined), stamp (examined for NULL / sentinel instead)

def _partition(block, cols):
    groups = [block["fallback_checked_columns"], block["elements_not_inspected"], block["fallback_not_applicable"], block["stamp_columns"]]
    flat = [c for g in groups for c in g]
    assert len(flat) == len(set(flat)), ("a column is in two groups", groups)
    assert sorted(flat) == sorted(cols), ("a column is in no group", sorted(set(cols) - set(flat)))


def test_the_pass_accounting_is_a_strict_partition_a_stamp_is_in_the_stamp_group_only():
    r = _grade()
    assert r["v"] == PASS
    _partition(r["convention"], s1.LATTA_COLS)
    assert r["convention"]["stamp_columns"] == ["created_at"] and "created_at" not in r["convention"]["fallback_not_applicable"]
    assert "count_from_graha" in r["convention"]["fallback_not_applicable"]                                         # a real non-examined column is still named
    assert "NOT examined for a literal fallback (the type cannot hold one): count_from_graha (smallint)" in r["measured"], r["measured"]
    assert "created_at (timestamp with time zone)" not in r["measured"]                                             # the stamp is not claimed unexamined
    assert "except the stamp column(s) named next" in r["measured"]                                                  # 'no other column constant' no longer sits unqualified beside a 1-distinct stamp


def test_the_partition_holds_without_a_stamp_too_and_the_wording_is_unchanged_there():
    r = ac.grade_null_convention(s1.SPEC(), list(s1.LATTA_COLS), s1.LATTA_TYPES, s1.STATS())
    _partition(r["convention"], s1.LATTA_COLS)
    assert "no other column constant" in r["measured"] and "except the stamp" not in r["measured"]
    assert "created_at (timestamp with time zone)" in r["measured"]                                                 # an undeclared-stamp timestamp is still named as not examined


def test_the_stamp_wording_no_longer_claims_a_stamp_cannot_hold_a_placeholder():
    r = _grade()
    assert "no infinity, -infinity or value at or before epoch + 1 day" in r["measured"]                           # the PASS claims exactly what was checked: the bound is named
    assert "no sentinel timestamp" not in r["measured"]
    assert "the type cannot hold one): created_at" not in r["measured"] and ", created_at (" not in r["measured"].split("NOT examined for a literal fallback")[-1]


# ---- REAL SQL: both timestamp types, every sentinel flavour -------------------------------------------------------------------------------

TS_FLAVOURS = {"timestamptz": ("timestamptz", "timestamp with time zone", "'2026-03-04 05:06:07+00'"),
               "timestamp": ("timestamp", "timestamp without time zone", "'2026-03-04 05:06:07'")}
SENTINELS = ["'epoch'", "'infinity'", "'-infinity'", "'1970-01-01 00:00:00'", "'1970-01-01 00:00:00+00'", "'0001-01-01 00:00:00'", "'0001-01-01'", "'1970-01-02 00:00:00'"]


def _lit(v, typ):
    """A timestamp literal; for timestamptz a bare date-time gets an explicit +00 so the test does not depend on the server's TimeZone setting."""
    return v if typ == "timestamp" or not v[1].isdigit() or "+" in v else v[:-1] + "+00'"


def _ts_setup(typ):
    if typ == "timestamptz":
        return list(LATTA_STAMP_SQL)                                    # the base table already is timestamptz
    return _variant("created_at timestamptz NOT NULL DEFAULT '2026-01-01'", f"created_at {typ} NOT NULL DEFAULT '2026-01-01'")


@pytest.mark.parametrize("typ", ["timestamptz", "timestamp"])
def test_REAL_SQL_real_write_times_pass_on_both_timestamp_types(monkeypatch, disposable_pg, typ):
    t, dt, real = TS_FLAVOURS[typ]
    r = _real_check(monkeypatch, disposable_pg, _ts_setup(t), types=dict(s1.REAL_TYPES, created_at=dt))
    assert r["v"] == PASS and r["convention"]["stamp_sentinels"] == {}, r                                           # one shared real value on every row
    r = _real_check(monkeypatch, disposable_pg, _ts_setup(t) + [f"UPDATE latta_t SET created_at = {real}::{t} + (count_from_graha || ' seconds')::interval;"],
                    types=dict(s1.REAL_TYPES, created_at=dt))
    assert r["v"] == PASS, r
    r = _real_check(monkeypatch, disposable_pg, _ts_setup(t) + [f"UPDATE latta_t SET created_at = {_lit(chr(39) + '1970-01-02 00:00:01' + chr(39), t)}::{t};"], types=dict(s1.REAL_TYPES, created_at=dt))
    assert r["v"] == PASS, r                                                                                          # one second past the boundary is a (very early) real time


@pytest.mark.parametrize("typ", ["timestamptz", "timestamp"])
@pytest.mark.parametrize("sentinel", SENTINELS)
def test_REAL_SQL_every_sentinel_flavour_fails_on_both_timestamp_types_all_rows_and_mixed(monkeypatch, disposable_pg, typ, sentinel):
    t, dt, real = TS_FLAVOURS[typ]
    types = dict(s1.REAL_TYPES, created_at=dt)
    sentinel = _lit(sentinel, typ)
    r = _real_check(monkeypatch, disposable_pg, _ts_setup(t) + [f"UPDATE latta_t SET created_at = {sentinel}::{t};"], types=types)
    assert r["v"] == FAIL and r["convention"]["stamp_sentinels"] == {"created_at": 8}, (sentinel, r)
    assert "sentinel timestamp" in r["measured"] and "created_at (8 row(s))" in r["measured"], r["measured"]
    r = _real_check(monkeypatch, disposable_pg, _ts_setup(t) + [f"UPDATE latta_t SET created_at = {real}::{t};", f"UPDATE latta_t SET created_at = {sentinel}::{t} WHERE graha = 'Sun';"],
                    types=types)
    assert r["v"] == FAIL and r["convention"]["stamp_sentinels"] == {"created_at": 1}, (sentinel, r)               # real stamps + ONE sentinel


@pytest.mark.parametrize("typ", ["timestamptz", "timestamp"])
def test_REAL_SQL_a_column_default_of_each_sentinel_and_a_stored_generated_1970_column_fail(monkeypatch, disposable_pg, typ):
    t, dt, _ = TS_FLAVOURS[typ]
    types = dict(s1.REAL_TYPES, created_at=dt)
    for default in ("'epoch'", "'infinity'", "'-infinity'", "'1970-01-01 00:00:00+00'", "'0001-01-01 00:00:00+00'"):
        setup = _variant("created_at timestamptz NOT NULL DEFAULT '2026-01-01'", f"created_at {t} NOT NULL DEFAULT {default}")
        r = _real_check(monkeypatch, disposable_pg, setup, types=types)
        assert r["v"] == FAIL and r["convention"]["stamp_sentinels"] == {"created_at": 8}, (default, r)
    gen = _variant("created_at timestamptz NOT NULL DEFAULT '2026-01-01'", f"created_at {t} GENERATED ALWAYS AS ('1970-01-01 00:00:00+00'::{t}) STORED NOT NULL")
    r = _real_check(monkeypatch, disposable_pg, gen, types=types)
    assert r["v"] == FAIL and r["convention"]["stamp_sentinels"] == {"created_at": 8}, r


def test_REAL_SQL_the_same_sentinel_column_undeclared_still_fails_through_the_constant_test(monkeypatch, disposable_pg):
    r = _real_check(monkeypatch, disposable_pg, LATTA_STAMP_SQL + ["UPDATE latta_t SET created_at = 'epoch';"], spec=SSPEC(stamps=[]))
    assert r["v"] == FAIL and r["convention"]["undeclared_constants"] == ["created_at"]


def test_REAL_SQL_the_whole_chain_a_sentinel_stamp_never_lifts_the_cap(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_STAMP_SQL + ["UPDATE latta_t SET created_at = 'epoch';"])
    cat = dict(s1._cat(table="latta_t"), keys={"latta_t": [["table_version", "graha"]]})
    r = dict(target_table="latta_t", count_sql="SELECT count(*) FROM latta_t")
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=dict(SSPEC(), table="latta_t"), prose_fields=None), r, None, cat, [], set(), (), set())
    assert ac.rollup_asset("L0", m)["Null"]["v"] == FAIL and "sentinel timestamp" in m[BR]["measured"], m[BR]["measured"]


def test_the_pass_and_fail_texts_name_the_exact_bound_in_the_verdict_and_in_the_block():
    bound = "no infinity, -infinity or value at or before epoch + 1 day"
    r = _grade()
    assert bound in r["measured"]
    ann = ac._null_annotation(r)                                                                                    # the block text a Null record carries is the same string
    assert bound in ann["measured"] and "sentinel timestamp" not in ann["measured"]
    f = _grade(stats=SSTATS(created_at=dict(sentinel=2)))
    want = "infinity, -infinity or any value at or before epoch + 1 day (epoch, 1970-01-01, year 0001 and earlier"
    assert want in f["measured"] and "created_at (2 row(s))" in f["measured"], f["measured"]
    assert want in ac._null_annotation(f)["measured"]
    raw = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))["description"]
    assert "no infinity, -infinity or value at or before epoch + 1 day" in raw and "no sentinel timestamp (infinity" not in raw


def test_through_measure_prose_the_record_text_names_the_bound(monkeypatch):
    m = s1._prose(monkeypatch, dict(null_convention=SSPEC(), prose_fields=None), stats=SSTATS())
    assert "no infinity, -infinity or value at or before epoch + 1 day" in m[SD]["measured"] and "no infinity, -infinity or value at or before epoch + 1 day" in m[BR]["null_convention"]["convention"]
