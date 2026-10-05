"""test_e6_s1_null_convention.py: E6 S1, REGISTRY_REVISION 13 (SS N-72 S1, N-73, N-74): the Null cap lifts per asset ONLY by earning it.

The ruling (verbatim): "The cap stays as the default; it LIFTS per asset only by earning it: Null reads PASS for an asset when schema_default and
blank_rows both pass AND that asset's declared null convention (pin 13: which columns may be NULL and what NULL means; no literal fallbacks, no
constant columns) is verified by the detector. No Null N/A rule (N-22 row 33 stands)."

An asset DECLARES `null_convention` (asset_declarations.json 1.9.0: table, nullable columns each with what NULL means and an optional key scope,
declared constant columns, one-line why, checkable evidence). The detector then verifies, read-only, that NULLs occur only in declared columns (and, with a
key scope, only on / exactly on the declared keys), that no declared-nullable column holds a literal fallback in place of NULL, and that no column is constant
unless declared constant. The Null checks read PASS only when schema_default and blank_rows are clean AND the convention verifies; every other path keeps the
cap exactly as before. A column pattern, a populated clean table or a forged flag never lifts it. Offline: the fetchers are stubbed; the REAL_SQL tests run
the same SQL on the disposable Postgres (skipped only where no PostgreSQL binaries exist)."""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _decl_version  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
import test_e6_na_r01_03 as r13  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

NA, NO_DET, PASS, FAIL, PARTIAL, ERRORED = ac.NA, ac.NO_DET, ac.PASS, ac.FAIL, ac.PARTIAL, ac.ERRORED
EV = "platform/scripts/governance/asset_census.py:1"          # an existing repo file: a checkable evidence pointer
SD, BR = "Null.schema_default", "Null.blank_rows"
WHY = "one seed version, one shared passage"
MEANS = "the retrieved passage states no per-graha effect clause for this graha (a disclosed gap, reserved)"

LATTA_COLS = ["table_version", "graha", "count_from_graha", "direction", "effect_description", "affliction_condition", "source_citation", "verse_ref",
              "created_at"]
LATTA_TYPES = {"table_version": "text", "graha": "text", "count_from_graha": "smallint", "direction": "text", "effect_description": "text",
               "affliction_condition": "text", "source_citation": "text", "verse_ref": "text", "created_at": "timestamp with time zone"}
CONST_COLS = ("table_version", "affliction_condition", "source_citation", "verse_ref", "created_at")


def NULLABLE(scope="exactly", column="effect_description", scope_obj=None, **over):
    n = dict(column=column, means=MEANS)
    if scope_obj is not None:
        n["scope"] = scope_obj
    elif scope == "exactly":
        n["scope"] = dict(key_column="graha", null_for=["Mars", "Saturn"], mode="exactly")
    elif scope == "only":
        n["scope"] = dict(key_column="graha", null_for=["Mars", "Saturn"], mode="only")
    n.update(over)
    return n


def SPEC(scope="exactly", **over):
    d = dict(table="bg_phaladeepika_latta", nullable=[NULLABLE(scope)], constants=[dict(column=c, why="one seed version, one shared passage") for c in CONST_COLS],
             why="Mars and Saturn carry a counting rule but the passage states no effect clause: effect_description is the one reserved-NULL column", evidence=EV)
    d.update(over)
    return d


def _col(rows, **kw):
    return dict(dict(nulls=0, distinct=rows, fallback=0), **kw)


def STATS(rows=8, **over):
    """The fetched stats of a CLEAN latta table (8 rows; Mars and Saturn NULL in effect_description; five constant columns), then `over` per column."""
    cols = {c: _col(rows) for c in LATTA_COLS}
    cols["direction"] = _col(rows, distinct=2)
    for c in CONST_COLS:
        cols[c] = _col(rows, distinct=1, sole="x")
    cols["effect_description"] = _col(rows, nulls=2, distinct=rows - 2, fallback=0, null_outside=0, null_outside_keys=[], nonnull_inside=0, nonnull_inside_keys=[])
    for c, d in over.items():
        cols[c] = dict(cols[c], **d)
    return dict(rows=rows, cols=cols)


def _grade(spec=None, stats=None, cols=LATTA_COLS, types=LATTA_TYPES):
    return ac.grade_null_convention(spec or SPEC(), list(cols), types, stats or STATS())


def _doc(extra, aid="bg_x", version="1.9.0"):
    return dict(version=version, kind_enum=list(ac.DECLARED_KINDS), assets={aid: dict({"kind": "data"}, **extra)})


def _bad(nc, match):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(dict(null_convention=nc)))


# ───────────────────────── the declaration validator ─────────────────────────

def test_validator_accepts_every_declared_form():
    for nc in (SPEC(), SPEC("only"), SPEC(None), SPEC(nullable=[], constants=[]), SPEC(evidence="unverified:the L0 review sheet"),
               SPEC(constants=[dict(column="table_version", why="one seed version per row set", value="phaladeepika_vedha_v01")]),
               SPEC(nullable=[NULLABLE("exactly"), NULLABLE(None, column="notes")])):
        ac.validate_declarations(_doc(dict(null_convention=nc)))
    ac.validate_declarations(_doc(dict(null_convention=None)))


def _nc(**over):
    return SPEC(**over)


@pytest.mark.parametrize("nc, match", [
    ({k: v for k, v in SPEC().items() if k != "why"}, r"null_convention\.why"),                                       # no reason
    (_nc(why=""), r"null_convention\.why"), (_nc(why="   "), r"null_convention\.why"), (_nc(why="two\nlines"), r"null_convention\.why"),
    (_nc(why=" padded "), r"null_convention\.why"), (_nc(why="x" * 1201), r"null_convention\.why"), (_nc(why=None), r"null_convention\.why"),
    ({k: v for k, v in SPEC().items() if k != "evidence"}, r"null_convention\.evidence"),                             # no evidence
    (_nc(evidence=""), r"null_convention\.evidence"), (_nc(evidence="unverified:"), r"null_convention\.evidence"),
    (_nc(evidence="no/such/file.md:3"), r"null_convention\.evidence"), (_nc(evidence="/etc/hosts"), r"null_convention\.evidence"),
    (_nc(evidence="../outside.md"), r"null_convention\.evidence"),
    (_nc(extra="x"), "unknown field"),
    ({k: v for k, v in SPEC().items() if k != "table"}, r"null_convention\.table"),
    (_nc(table="a b"), r"null_convention\.table"), (_nc(table='t"'), r"null_convention\.table"), (_nc(table=3), r"null_convention\.table"),
    ({k: v for k, v in SPEC().items() if k != "nullable"}, "nullable must be a list"),
    ({k: v for k, v in SPEC().items() if k != "constants"}, "constants must be a list"),
    (_nc(nullable="effect_description"), "nullable must be a list"), (_nc(constants={"column": "x"}), "constants must be a list"),
    (_nc(nullable=["effect_description"]), "nullable entry"),
    (_nc(nullable=[dict(NULLABLE(), extra=1)]), "unknown field"),
    (_nc(nullable=[{k: v for k, v in NULLABLE().items() if k != "column"}]), r"nullable\[0\]\.column"),
    (_nc(nullable=[NULLABLE(column="a b")]), r"nullable\[0\]\.column"),
    (_nc(nullable=[{k: v for k, v in NULLABLE().items() if k != "means"}]), r"nullable\[0\]\.means"),            # a nullable column with no meaning
    (_nc(nullable=[NULLABLE(means="")]), r"nullable\[0\]\.means"), (_nc(nullable=[NULLABLE(means="  ")]), r"nullable\[0\]\.means"),
    (_nc(nullable=[NULLABLE(means="a\nb")]), r"nullable\[0\]\.means"), (_nc(nullable=[NULLABLE(means=" padded ")]), r"nullable\[0\]\.means"),
    (_nc(nullable=[NULLABLE(means="x" * 1201)]), r"nullable\[0\]\.means"), (_nc(nullable=[NULLABLE(means=7)]), r"nullable\[0\]\.means"),
    (_nc(nullable=[NULLABLE(means="two words")]), r"nullable\[0\]\.means"),
    (_nc(nullable=[NULLABLE(means="N/A")]), "a fallback literal"), (_nc(nullable=[NULLABLE(means="none")]), "a fallback literal"),
    (_nc(nullable=[NULLABLE(means="Unknown")]), "a fallback literal"), (_nc(nullable=[NULLABLE(means="-")]), "a fallback literal"),
    (_nc(nullable=[NULLABLE(None, scope_obj="x")]), "scope must be an object"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=["Mars"], mode="only", extra=1))]), "unknown field"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=["Mars"], mode="sometimes"))]), "mode"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=["Mars"]))]), "mode"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=[], mode="only"))]), "null_for"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for="Mars", mode="only"))]), "null_for"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=["Mars", "Mars"], mode="only"))]), "duplicate"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=["Mars", ""], mode="only"))]), "null_for"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=["Ma\x00rs"], mode="only"))]), "null_for"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=[7], mode="only"))]), "null_for"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="g h", null_for=["Mars"], mode="only"))]), "key_column"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(null_for=["Mars"], mode="only"))]), "key_column"),
    (_nc(nullable=[NULLABLE(None, scope_obj=dict(key_column="effect_description", null_for=["Mars"], mode="only"))]), "must differ from the nullable column"),   # the key is the column itself
    (_nc(nullable=[NULLABLE(), NULLABLE()]), "duplicate"),
    (_nc(constants=[dict(column="table_version", why=WHY), dict(column="table_version", why=WHY)]), "duplicate"),
    (_nc(constants=[dict(column="effect_description", why=WHY)]), "both nullable and constant"),
    (_nc(constants=[dict(column="graha", why=WHY)]), "key_column"),                                                   # the scope's key cannot be constant
    (_nc(constants=["table_version"]), "constants entry"),
    (_nc(constants=[dict(column="table_version")]), r"constants\[0\]\.why"), (_nc(constants=[dict(column="table_version", why=" ")]), r"constants\[0\]\.why"),
    (_nc(constants=[dict(column="table_version", why="because")]), r"constants\[0\]\.why"),
    (_nc(constants=[dict(column="table_version", why="a\nb")]), r"constants\[0\]\.why"),
    (_nc(constants=[dict(column="a b", why=WHY)]), r"constants\[0\]\.column"),
    (_nc(constants=[dict(column="table_version", why=WHY, value=3)]), r"constants\[0\]\.value"),
    (_nc(constants=[dict(column="table_version", why=WHY, value="")]), r"constants\[0\]\.value"),
    (_nc(constants=[dict(column="table_version", why=WHY, extra=1)]), "unknown field"),
])
def test_validator_refuses_a_malformed_null_convention(nc, match):
    _bad(nc, match)


def test_validator_refuses_non_objects():
    for bad in ("effect_description", ["table"], 7, True):
        _bad(bad, "must be an object")


def test_validator_doc_level_field_list_must_match_when_present():
    ok = _doc({})
    ok["null_convention_declaration_fields"] = list(ac.NULL_CONVENTION_DECL_FIELDS)
    ac.validate_declarations(ok)
    for broken in (list(ac.NULL_CONVENTION_DECL_FIELDS[:-1]), list(ac.NULL_CONVENTION_DECL_FIELDS) + ["x"], list(reversed(ac.NULL_CONVENTION_DECL_FIELDS))):
        ok["null_convention_declaration_fields"] = broken
        with pytest.raises(ac.DeclarationsError, match="null_convention_declaration_fields"):
            ac.validate_declarations(ok)


def test_the_committed_file_is_1_11_0_declares_a_null_convention_only_for_the_latta_and_lists_the_fields():
    raw = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
    assert raw["version"] == _decl_version.CURRENT          # DECL-LATTA-NULL: bg_phaladeepika_latta is the first (and only) asset to declare one
    assert raw["null_convention_declaration_fields"] == list(ac.NULL_CONVENTION_DECL_FIELDS)
    # the per-asset review is the reviewed work: nothing is declared by pattern in this PR
    assert [a for a, e in raw["assets"].items() if "null_convention" in e] == ["bg_phaladeepika_latta"]
    ac.load_asset_declarations()


# ───────────────────────── the pure grader: PASS and every seeded defect ─────────────────────────

def test_a_clean_declared_convention_passes_and_says_what_it_verified():
    r = _grade()
    assert r["v"] == PASS and r["declared"] is True, r
    assert "effect_description" in r["measured"] and "Mars" in r["measured"] and "Saturn" in r["measured"], r["measured"]
    assert r["convention"]["table"] == "bg_phaladeepika_latta" and r["convention"]["rows"] == 8


def test_an_undeclared_null_in_a_non_nullable_column_flips_the_cell():
    r = _grade(stats=STATS(count_from_graha=dict(nulls=1)))
    assert r["v"] == FAIL and "count_from_graha" in r["measured"] and "undeclared NULL" in r["measured"], r
    assert r["convention"]["undeclared_nulls"] == {"count_from_graha": 1}


def test_an_undeclared_null_in_a_declared_constant_column_flips_the_cell():
    r = _grade(stats=STATS(source_citation=dict(nulls=3, distinct=1)))
    assert r["v"] == FAIL and "source_citation" in r["measured"]


@pytest.mark.parametrize("fallback", [1, 2, 8])
def test_a_literal_fallback_in_a_declared_nullable_column_flips_the_cell(fallback):
    st = STATS()
    st["cols"]["effect_description"]["fallback"] = fallback
    r = _grade(stats=st)
    assert r["v"] == FAIL and "literal fallback" in r["measured"] and "effect_description" in r["measured"], r
    assert r["convention"]["fallbacks"] == {"effect_description": fallback}


def test_a_declared_constant_column_that_varies_flips_the_cell():
    r = _grade(stats=STATS(source_citation=dict(distinct=2)))
    assert r["v"] == FAIL and "source_citation" in r["measured"] and "declared constant" in r["measured"], r
    assert r["convention"]["constant_violations"] == ["source_citation"]


def test_a_declared_constant_with_a_declared_value_fails_when_the_sole_value_differs_and_passes_when_it_matches():
    spec = SPEC(constants=[dict(column=c, why=WHY, **({"value": "v01"} if c == "table_version" else {})) for c in CONST_COLS])
    ok = STATS(table_version=dict(sole="v01"))
    assert _grade(spec, ok)["v"] == PASS
    r = _grade(spec, STATS(table_version=dict(sole="v02")))
    assert r["v"] == FAIL and "table_version" in r["measured"] and "v01" in r["measured"] and "v02" in r["measured"]


def test_a_constant_column_that_is_not_declared_constant_flips_the_cell():
    spec = SPEC(constants=[dict(column=c, why="w") for c in CONST_COLS if c != "verse_ref"])
    r = _grade(spec)
    assert r["v"] == FAIL and "verse_ref" in r["measured"] and "not declared constant" in r["measured"], r
    assert r["convention"]["undeclared_constants"] == ["verse_ref"]


def test_a_column_that_is_null_on_every_row_is_a_constant_never_a_populated_column():
    st = STATS()
    st["cols"]["effect_description"].update(nulls=8, distinct=0, null_outside=6, null_outside_keys=["Jupiter"])
    r = _grade(stats=st)
    assert r["v"] == FAIL
    st2 = STATS(count_from_graha=dict(nulls=8, distinct=0))
    spec = SPEC(nullable=[NULLABLE("exactly"), NULLABLE(None, column="count_from_graha")])
    r2 = ac.grade_null_convention(spec, LATTA_COLS, LATTA_TYPES, st2)
    assert r2["v"] == FAIL and "count_from_graha" in r2["measured"] and "every row" in r2["measured"], r2


def test_a_column_holding_one_value_and_NULL_varies_so_it_is_not_a_constant_column():
    st = STATS()
    st["cols"]["effect_description"].update(nulls=2, distinct=1)                      # {NULL, 'x'}: two states, NULL counts as a value
    assert _grade(stats=st)["v"] == PASS
    st["cols"]["effect_description"].update(nulls=0, distinct=1, null_outside=0, nonnull_inside=0)
    assert _grade(SPEC(None), st)["v"] == FAIL                                       # one value and no NULL at all: a constant column that was not declared


def test_a_null_outside_the_declared_keys_fails_in_both_modes_and_names_the_keys():
    for scope in ("exactly", "only"):
        st = STATS()
        st["cols"]["effect_description"].update(nulls=3, null_outside=1, null_outside_keys=["Jupiter"])
        r = _grade(SPEC(scope), st)
        assert r["v"] == FAIL and "Jupiter" in r["measured"] and "outside" in r["measured"], (scope, r)


def test_exactly_mode_fails_when_a_declared_reserved_null_key_holds_a_value_but_only_mode_allows_it():
    st = STATS()
    st["cols"]["effect_description"].update(nulls=1, nonnull_inside=1, nonnull_inside_keys=["Mars"])
    r = _grade(SPEC("exactly"), st)
    assert r["v"] == FAIL and "Mars" in r["measured"] and "reserved" in r["measured"], r
    assert _grade(SPEC("only"), st)["v"] == PASS


def test_a_declared_nullable_column_with_null_rows_and_no_scope_is_partial_the_meaning_is_not_machine_checked():
    r = _grade(SPEC(None))
    assert r["v"] == PARTIAL and "effect_description" in r["measured"] and "not machine-checked" in r["measured"], r
    assert r["convention"]["unscoped_null_columns"] == ["effect_description"]
    st = STATS()
    st["cols"]["effect_description"].update(nulls=0, distinct=8)
    assert _grade(SPEC(None), st)["v"] == PASS                      # nothing to verify: no NULL rows


def test_a_defect_outranks_partial():
    r = _grade(SPEC(None), STATS(count_from_graha=dict(nulls=1)))
    assert r["v"] == FAIL


@pytest.mark.parametrize("rows, v", [(0, NO_DET), (1, NO_DET)])
def test_fewer_than_two_rows_is_no_detector_variation_cannot_be_shown(rows, v):
    r = _grade(stats=dict(rows=rows, cols=STATS(rows)["cols"]))
    assert r["v"] == v and "row" in r["measured"], r


def test_a_declaration_naming_a_column_the_table_does_not_carry_fails_before_any_stats_are_read():
    for spec in (SPEC(nullable=[NULLABLE("exactly", column="no_such_col")]), SPEC(constants=[dict(column="no_such_col", why="w")]),
                 SPEC(nullable=[dict(NULLABLE("exactly"), scope=dict(key_column="no_key", null_for=["Mars"], mode="only"))])):
        r = ac.grade_null_convention(spec, LATTA_COLS, LATTA_TYPES, None)
        assert r["v"] == FAIL and "no_such_col" in r["measured"] + "no_such_col" and "not columns of" in r["measured"], r


def test_a_column_missing_its_distinct_or_nulls_count_is_malformed_not_a_pass():
    for drop in ("distinct", "nulls"):
        st = STATS()
        del st["cols"]["graha"][drop]
        with pytest.raises(ac.Unknown):
            ac.grade_null_convention(SPEC(), LATTA_COLS, LATTA_TYPES, st)


def test_the_record_never_reads_pass_on_any_unread_input():
    for st in (None, dict(rows=8), dict(rows=8, cols={}), dict(rows="8", cols=STATS()["cols"])):
        with pytest.raises(ac.Unknown):
            ac.grade_null_convention(SPEC(), LATTA_COLS, LATTA_TYPES, st)


# ───────────────────────── the check around it: table ownership, catalog, read failure ─────────────────────────

def _own(tables=None):
    return {"bg_phaladeepika_latta": (LATTA_COLS, LATTA_TYPES, {})} if tables is None else tables


def test_a_declaration_for_an_asset_without_the_table_is_refused_and_nothing_is_read(monkeypatch):
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: pytest.fail("no table, no read"))
    for own, why in ((_own({}), "owned"), (_own({"other_t": (["id"], {}, {})}), "owned")):
        r = ac.null_convention_check(SPEC(), own, set(own), ("", "whole-table"))
        assert r["v"] == NO_DET and r["declared"] is True and "bg_phaladeepika_latta" in r["measured"], r
        assert r["declaration_disagreements"][0]["field"] == "null_convention.table", r
    r = ac.null_convention_check(SPEC(), _own(), set(), ("", "whole-table"))                      # an owned table the catalog does not carry
    assert r["v"] == NO_DET and "does not exist in production" in r["measured"], r
    r = ac.null_convention_check(SPEC(), _own({"bg_phaladeepika_latta": (None, None, None)}), {"bg_phaladeepika_latta"}, ("", "whole-table"))
    assert r["v"] == NO_DET and "columns" in r["measured"], r
    r = ac.null_convention_check(SPEC(), _own(), {"bg_phaladeepika_latta"}, None)                   # a shared table whose rows cannot be scoped
    assert r["v"] == NO_DET and "scope" in r["measured"], r


def test_the_check_reads_the_declared_table_with_its_scope_and_grades_the_stats(monkeypatch):
    seen = {}
    monkeypatch.setattr(ac, "null_convention_fetch", lambda t, cols, types, spec, tail="": seen.update(a=(t, list(cols), tail)) or STATS())
    r = ac.null_convention_check(SPEC(), _own(), {"bg_phaladeepika_latta"}, (" WHERE chart_id = 'c'", "chart-scoped by count_sql"))
    assert r["v"] == PASS and seen["a"] == ("bg_phaladeepika_latta", LATTA_COLS, " WHERE chart_id = 'c'")
    assert "chart-scoped by count_sql" in r["measured"], r["measured"]


def test_a_failed_read_degrades_only_this_check(monkeypatch):
    def boom(*a, **k):
        raise ac.Unknown("connection lost")
    monkeypatch.setattr(ac, "null_convention_fetch", boom)
    r = ac.null_convention_check(SPEC(), _own(), {"bg_phaladeepika_latta"}, ("", "whole-table"))
    assert r["v"] == ERRORED and "connection lost" in r["measured"] and r["declared"] is True


# ───────────────────────── the fetcher: one read-only SELECT, strict identifiers ─────────────────────────

def _capture(monkeypatch, answer, types=None):
    """Capture the ONE table SELECT the fetch issues; the catalog kinds read is stubbed from the data_type strings (`_null_type_kind`) so it is not a second capture."""
    got = []
    tm = dict(LATTA_TYPES, **(types or {}))
    monkeypatch.setattr(ac, "null_fetch_column_kinds", lambda table, cols: {c: ac._null_type_kind(tm.get(c, "text")) for c in cols})
    monkeypatch.setattr(ac, "scalar", lambda sql: got.append(sql) or answer)
    return got


def test_the_fetch_is_one_read_only_select_that_names_every_column_and_the_scope(monkeypatch):
    got = _capture(monkeypatch, json.dumps(STATS()))
    st = ac.null_convention_fetch("bg_phaladeepika_latta", LATTA_COLS, LATTA_TYPES, SPEC(), " WHERE chart_id = 'c'")
    assert st.pop("kinds")["effect_description"] == "text" and st == STATS() and len(got) == 1
    sql = got[0]
    assert sql.lstrip().upper().startswith("SELECT") and not re.search(r"\b(insert|update|delete|drop|alter|create|truncate|grant)\b", sql, re.I)
    assert 'FROM "bg_phaladeepika_latta" WHERE chart_id = \'c\'' in sql or "FROM bg_phaladeepika_latta WHERE chart_id = 'c'" in sql
    for c in LATTA_COLS:
        assert f'"{c}"' in sql, c
    assert "'Mars'" in sql and "'Saturn'" in sql and '"graha"' in sql                                   # the scope literals and key column
    for lit in ac.LDGR_PLACEHOLDERS:
        assert "'" + lit + "'" in sql, lit
    assert re.search(r'"count_from_graha"\s*=\s*0', sql) is None                                       # the numeric 0 sentinel is read only on a declared-nullable column
    assert "count(DISTINCT" in sql


def test_the_zero_sentinel_is_read_on_a_declared_nullable_numeric_column_only(monkeypatch):
    got = _capture(monkeypatch, json.dumps(STATS()))
    spec = SPEC(nullable=[NULLABLE("exactly"), NULLABLE(None, column="count_from_graha")])
    ac.null_convention_fetch("bg_phaladeepika_latta", LATTA_COLS, LATTA_TYPES, spec, "")
    assert re.search(r'"count_from_graha"\s*=\s*0', got[0])
    got.clear()
    ac.null_convention_fetch("bg_phaladeepika_latta", LATTA_COLS, LATTA_TYPES, SPEC(nullable=[NULLABLE("exactly"), NULLABLE(None, column="direction")]), "")
    assert re.search(r'"direction"\s*=\s*0', got[0]) is None                                            # a text column is not compared with 0


def test_the_fetch_refuses_a_malformed_identifier_or_a_control_character_before_any_sql(monkeypatch):
    got = _capture(monkeypatch, "{}")
    for table, cols in (("t;DROP", ["a"]), ("t", ['a"b']), ("t", ["a b"]), ("", ["a"]), ("t", [""])):
        with pytest.raises(ac.Unknown):
            ac.null_convention_fetch(table, cols, {c: "text" for c in cols}, dict(table=table, nullable=[], constants=[]), "")
    spec = SPEC(nullable=[dict(NULLABLE("exactly"), scope=dict(key_column="graha", null_for=["Ma\x00rs"], mode="only"))])
    with pytest.raises(ac.Unknown):
        ac.null_convention_fetch("t", LATTA_COLS, LATTA_TYPES, spec, "")
    assert got == []


def test_a_quote_in_a_scope_value_is_doubled_never_closing_the_literal(monkeypatch):
    got = _capture(monkeypatch, json.dumps(STATS()))
    spec = SPEC(nullable=[dict(NULLABLE("exactly"), scope=dict(key_column="graha", null_for=["O'Brien'; DROP TABLE x; --"], mode="only"))])
    ac.null_convention_fetch("bg_phaladeepika_latta", LATTA_COLS, LATTA_TYPES, spec, "")
    assert "'O''Brien''; DROP TABLE x; --'" in got[0]


@pytest.mark.parametrize("answer", ["", "not json", "[]", "{}", '{"rows": "8", "cols": {}}', '{"rows": 8}', '{"rows": 8, "cols": {"graha": {"nulls": 0}}}',
                                    '{"rows": 8, "cols": []}'])
def test_the_fetch_raises_unknown_on_an_unparseable_or_malformed_answer(monkeypatch, answer):
    _capture(monkeypatch, answer)
    with pytest.raises(ac.Unknown):
        ac.null_convention_fetch("bg_phaladeepika_latta", LATTA_COLS, LATTA_TYPES, SPEC(), "")


# ───────────────────────── the lift: ONLY by earning it ─────────────────────────

ENTRIES = ["effect_description"]
COUNTS_OK = {"effect_description": dict(checkable=6, blank=0, scope="whole-table (table has no chart_id column)")}


def _conv(v=PASS, **kw):
    r = dict(v=v, declared=True, measured="convention measured", convention=dict(table="bg_phaladeepika_latta", rows=8))
    r.update(kw)
    return r


def _graders(sd_v=PARTIAL, br_v=PARTIAL, counts=COUNTS_OK, defaults=None):
    own = {"bg_phaladeepika_latta": (LATTA_COLS, LATTA_TYPES, dict(defaults or {}))}
    sd = ac.grade_null_schema_default_tables(ENTRIES, own)
    br = ac.grade_null_blank_rows(ENTRIES, counts)
    return sd, br


def test_the_two_graders_mark_a_genuinely_clean_outcome_and_only_that():
    sd, br = _graders()
    assert sd["v"] == PARTIAL and sd["clean"] is True and br["v"] == PARTIAL and br["clean"] is True
    sd, _ = _graders(defaults={"effect_description": "'none'::text"})
    assert sd["v"] == FAIL and not sd.get("clean")
    own_unread = {"bg_phaladeepika_latta": (LATTA_COLS, LATTA_TYPES, None)}
    assert not ac.grade_null_schema_default_tables(ENTRIES, own_unread).get("clean")
    for counts in ({"effect_description": dict(checkable=6, blank=2, scope="s")},                              # a blank row
                   {"effect_description": dict(checkable=0, blank=0, scope="s")},                              # nothing checkable
                   {"effect_description": None},                                                              # unknown
                   {"effect_description": dict(checkable=6, blank=0, scope=ac.UPPER_BOUND)},                  # a whole-table upper bound
                   None):
        assert not ac.grade_null_blank_rows(ENTRIES, counts).get("clean"), counts
    two = ["effect_description", "other"]
    assert not ac.grade_null_blank_rows(two, {"effect_description": dict(checkable=6, blank=0, scope="s"), "other": dict(checkable=0, blank=0, scope="s")}).get("clean")


def _earn(conv=None, **kw):
    sd, br = _graders(**{k: v for k, v in kw.items() if k in ("defaults", "counts")})
    return ac.earn_null_lift(ENTRIES, sd, br, conv or _conv(), dict(evidence=EV, why="w"))


def test_both_graders_clean_and_the_convention_verified_lifts_both_records_to_pass_with_the_evidence():
    out = _earn()
    assert set(out) == {SD, BR} and out[SD]["v"] == PASS and out[BR]["v"] == PASS
    for crit in (SD, BR):
        nc = out[crit]["null_convention"]
        assert nc["declared"] is True and nc["verified"] is True and nc["v"] == PASS and nc["table"] == "bg_phaladeepika_latta"
        assert nc["columns"] == ENTRIES and nc["evidence"] == EV and nc["why"] == "w"
        assert nc["schema_default_clean"] is True and nc["blank_rows_clean"] is True
        assert ac.null_lift_problem(out[crit]) is None
    cells = ac.rollup_asset("L0", out)
    assert cells["Null"]["v"] == PASS and [c["v"] for c in cells["Null"]["checks"]] == [PASS, PASS], cells["Null"]


@pytest.mark.parametrize("conv", [_conv(PARTIAL), _conv(NO_DET), _conv(ERRORED)])
def test_a_convention_that_is_not_verified_leaves_the_cap_in_place_exactly_as_today(conv):
    assert _earn(conv) == {}


def test_a_convention_fail_flips_the_null_cell_through_blank_rows():
    out = _earn(_conv(FAIL, measured="undeclared NULL in count_from_graha"))
    assert out[BR]["v"] == FAIL and "undeclared NULL" in out[BR]["measured"] and out[BR]["declared"] is True
    cells = ac.rollup_asset("L0", out)
    assert cells["Null"]["v"] == FAIL


def test_a_grader_fail_over_the_convention_columns_flips_the_cell_even_when_the_convention_passes():
    out = _earn(defaults={"effect_description": "'N/A'::text"})                  # a schema default standing in for NULL
    assert out[SD]["v"] == FAIL and SD in out and ac.rollup_asset("L0", out)["Null"]["v"] == FAIL
    out = _earn(counts={"effect_description": dict(checkable=5, blank=2, scope="whole-table (table has no chart_id column)")})
    assert out[BR]["v"] == FAIL


@pytest.mark.parametrize("kw", [dict(defaults=None, counts={"effect_description": None}),
                                dict(counts={"effect_description": dict(checkable=0, blank=0, scope="s")}),
                                dict(counts={"effect_description": dict(checkable=6, blank=0, scope=ac.UPPER_BOUND)}),
                                dict(counts=None)])
def test_a_grader_that_is_not_clean_keeps_the_cap_even_when_the_convention_passes(kw):
    assert _earn(**kw) == {}


def test_schema_default_or_blank_rows_not_clean_each_blocks_the_lift_on_its_own():
    sd, br = _graders()
    assert ac.earn_null_lift(ENTRIES, dict(sd, clean=False), br, _conv(), dict(evidence=EV, why="w")) == {}
    assert ac.earn_null_lift(ENTRIES, sd, dict(br, clean=False), _conv(), dict(evidence=EV, why="w")) == {}
    assert ac.earn_null_lift(ENTRIES, {k: v for k, v in sd.items() if k != "clean"}, br, _conv(), dict(evidence=EV, why="w")) == {}


def test_a_convention_with_no_entry_to_check_never_lifts():
    sd, br = _graders()
    assert ac.earn_null_lift([], sd, br, _conv(), dict(evidence=EV, why="w")) == {}          # nothing was checked for blank rows or defaults: vacuous, never earned


def _lifted():
    return _earn()


def test_a_column_pattern_or_a_populated_clean_table_never_lifts_the_cap():
    for rec in (dict(v=PASS, measured="no blank row, columns look right"), dict(v=PASS, measured="x", clean=True)):
        assert ac.rollup_asset("L0", {SD: dict(rec), BR: dict(rec)})["Null"]["v"] == PARTIAL
    cell = ac.rollup_asset("L0", {SD: dict(v=PASS, measured="x"), BR: dict(v=PASS, measured="x")}, dict(columns=["effect_description"]))["Null"]
    assert cell["v"] == PARTIAL and all("capped at PARTIAL" in c["reason"] for c in cell["checks"])


@pytest.mark.parametrize("forge", [
    lambda n: n.update(verified=False), lambda n: n.update(declared=False), lambda n: n.update(v=PARTIAL), lambda n: n.pop("evidence"),
    lambda n: n.update(evidence=""), lambda n: n.update(evidence="  "), lambda n: n.pop("why"), lambda n: n.update(why=""), lambda n: n.pop("table"),
    lambda n: n.update(columns=[]), lambda n: n.pop("columns"), lambda n: n.update(schema_default_clean=False), lambda n: n.update(blank_rows_clean=False),
    lambda n: n.pop("schema_default_clean"), lambda n: n.update(verified="yes"), lambda n: n.update(declared=1),
])
def test_a_forged_or_incomplete_lift_block_is_not_honoured(forge):
    out = _lifted()
    for crit in (SD, BR):
        forge(out[crit]["null_convention"])
    cell = ac.rollup_asset("L0", out)["Null"]
    assert cell["v"] == PARTIAL and all("capped at PARTIAL" in c["reason"] for c in cell["checks"]), cell


def test_a_lift_block_that_is_not_an_object_is_not_honoured():
    for bad in (None, "verified", ["verified"], 1, True):
        out = _lifted()
        out[SD]["null_convention"] = bad
        assert ac.rollup_asset("L0", out)["Null"]["v"] == PARTIAL


def test_a_lift_on_one_check_alone_is_capped_the_sibling_must_be_a_verified_pass_too():
    out = _lifted()
    one = {SD: out[SD]}
    cell = ac.rollup_asset("L0", one)["Null"]
    assert cell["v"] == NO_DET                                                   # the other Null check is unmeasured: the cell is not PASS
    assert [c["v"] for c in cell["checks"] if c["criterion"] == SD] == [PARTIAL]
    for other in (dict(v=PARTIAL, measured="x", clean=True), dict(v=PASS, measured="x"), dict(v=FAIL, measured="x")):
        cell = ac.rollup_asset("L0", {SD: out[SD], BR: other})["Null"]
        assert cell["v"] != PASS and [c["v"] for c in cell["checks"] if c["criterion"] == SD] == [PARTIAL], other
    forged = copy.deepcopy(out)
    forged[BR]["null_convention"]["verified"] = False
    assert ac.rollup_asset("L0", forged)["Null"]["v"] == PARTIAL


def test_two_lift_blocks_that_name_different_tables_or_columns_are_not_one_convention():
    out = _lifted()
    out[BR]["null_convention"]["table"] = "another_t"
    assert ac.rollup_asset("L0", out)["Null"]["v"] == PARTIAL
    out = _lifted()
    out[BR]["null_convention"]["columns"] = ["something_else"]
    assert ac.rollup_asset("L0", out)["Null"]["v"] == PARTIAL


@pytest.mark.parametrize("extra", [dict(inconclusive=True), dict(basis="declaration"), dict(basis="Declaration")])
def test_an_inconclusive_or_basis_carrying_lift_is_not_honoured(extra):
    out = _lifted()
    out[SD].update(extra)
    cell = ac.rollup_asset("L0", out)["Null"]
    assert cell["v"] != PASS


def test_null_lift_problem_names_why_each_incomplete_record_is_refused():
    assert ac.null_lift_problem(_lifted()[SD]) is None
    for extra in (dict(inconclusive=True), dict(basis="declaration"), dict(v=PARTIAL), dict(v=NO_DET)):
        assert ac.null_lift_problem(dict(_lifted()[SD], **extra)), extra
    for bad in (None, "x", [], 3):
        assert ac.null_lift_problem(bad)
    assert ac.null_lift_problem({}) == "no null_convention block"


def test_a_direct_call_without_the_sibling_records_never_lifts():
    out = _lifted()
    c = ac._check_contribution(SD, "L0", out[SD], None)                           # no all_meas: the lift needs both checks
    assert c["v"] == PARTIAL and "capped at PARTIAL" in c["reason"]
    c = ac._check_contribution(SD, "L0", out[SD], None, out)
    assert c["v"] == PASS and c["null_convention_verified"] is True and c["state"] == "MEASURED"


def test_a_lifted_check_is_still_refused_in_the_other_capped_criterion_and_a_narr_fidelity_pass_stays_capped():
    c = ac._check_contribution("Narr.fidelity_test", "L0", dict(v=PASS, measured="x", null_convention=_lifted()[SD]["null_convention"]), None, _lifted())
    assert c["v"] == PARTIAL


def test_the_cap_line_and_its_fail_through_stay_in_the_source_the_tracker_reads():
    src = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert 'if v == PASS and (crit.startswith("Null.") or crit == "Narr.fidelity_test"):' in src
    assert "capped at PARTIAL (Null: never PASS alone; fidelity_test: structural only)" in src


def test_no_null_na_rule_or_cause_is_declared_n_22_row_33_stands():
    # N-150 R1 (pin 26): the two Null rules exist, released ONLY through the checked prose_none block (the rollup refuses a record without it): see test_n150_prose_none
    assert sorted(i for i in ac.NA_RULE_DECISIONS if i.startswith("Null.")) == ["Null.blank_rows#measured:no-prose-declared", "Null.schema_default#measured:no-prose-declared"]
    assert ac.NA_CAUSES["Null.schema_default"] == ("no-prose-declared",) and ac.NA_CAUSES["Null.blank_rows"] == ("no-prose-declared",)
    for crit in (SD, BR):
        assert ac.CRITERION_REGISTRY[crit]["columns_any"] is None and ac.CRITERION_REGISTRY[crit]["asset_kinds"] is None
    # a measured N/A on a Null check is never released, declared convention or not
    c = ac._check_contribution(SD, "L0", dict(v=NA, cause="no-prose-declared", measured="x"), None)
    assert c["v"] == NO_DET


# ───────────────────────── measure(): the glue ─────────────────────────

LATTA_R = dict(target_table="bg_phaladeepika_latta", count_sql="SELECT count(*) FROM bg_phaladeepika_latta")


def _cat(cols=LATTA_COLS, types=LATTA_TYPES, defaults=None, table="bg_phaladeepika_latta"):
    return dict(exists={table}, cols={table: list(cols)}, keys={table: [["table_version", "graha"]]}, views=set(),
                types={table: dict(types)}, defaults={table: dict(defaults or {})}, types_error=None)


def _prose(monkeypatch, decl, stats=None, cat=None, counts=None, r=None, fetch=None):
    monkeypatch.setattr(ac, "null_convention_fetch", fetch or (lambda *a, **k: stats if stats is not None else STATS()))
    monkeypatch.setattr(ac, "prose_row_counts", lambda t, es, tail, types=None: {e: dict(counts or dict(checkable=6, blank=0)) for e in es})
    return ac._measure_prose("bg_phaladeepika_latta", decl, r or LATTA_R, None, cat or _cat(), [], set(), (), set())


def test_an_asset_that_declares_a_clean_convention_reads_pass_on_both_checks_end_to_end(monkeypatch):
    m = _prose(monkeypatch, dict(null_convention=SPEC(), prose_fields=None))
    assert m[SD]["v"] == PASS and m[BR]["v"] == PASS and m[SD]["null_convention"]["verified"] is True
    assert ac.rollup_asset("L0", m)["Null"]["v"] == PASS


def test_the_same_asset_without_the_declaration_reads_exactly_as_today(monkeypatch):
    for decl in (None, dict(prose_fields=None), dict(prose_fields=[]), dict(prose_fields=["effect_description"])):
        m = _prose(monkeypatch, decl)
        assert all(m[c]["v"] != PASS for c in (SD, BR)), decl
        assert "null_convention" not in m[SD] and "null_convention" not in m[BR]
    m = _prose(monkeypatch, dict(prose_fields=None))
    assert m[SD]["v"] == NO_DET and m[BR]["v"] == NO_DET
    m = _prose(monkeypatch, dict(prose_fields=["effect_description"]))
    assert m[SD]["v"] == PARTIAL and m[BR]["v"] == PARTIAL


def test_a_declared_prose_field_is_checked_with_the_convention_columns_and_must_be_clean_too(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: STATS())
    monkeypatch.setattr(ac, "prose_row_counts", lambda t, es, tail, types=None: seen.append(sorted(es)) or {e: dict(checkable=6, blank=0) for e in es})
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=SPEC(), prose_fields=["affliction_condition"]), LATTA_R, None, _cat(), [], set(), (), set())
    assert ["affliction_condition", "effect_description"] in seen
    assert m[SD]["v"] == PASS and m[SD]["null_convention"]["columns"] == ["affliction_condition", "effect_description"]
    m = _prose(monkeypatch, dict(null_convention=SPEC(), prose_fields=["affliction_condition"]), counts=dict(checkable=6, blank=1))
    assert m[BR]["v"] == FAIL


def test_the_convention_columns_are_counted_in_the_declared_table_not_in_another_owned_table_that_has_the_same_column(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: STATS())
    monkeypatch.setattr(ac, "prose_row_counts", lambda t, es, tail, types=None: seen.append((t, sorted(es))) or {e: dict(checkable=6, blank=0) for e in es})
    cat = dict(_cat(), exists={"other_t", "bg_phaladeepika_latta"}, cols={"other_t": list(LATTA_COLS), "bg_phaladeepika_latta": list(LATTA_COLS)},
               types={"other_t": dict(LATTA_TYPES), "bg_phaladeepika_latta": dict(LATTA_TYPES)}, defaults={"other_t": {}, "bg_phaladeepika_latta": {}})
    r = dict(target_table="other_t", count_sql="SELECT count(*) FROM other_t UNION ALL SELECT count(*) FROM bg_phaladeepika_latta")
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=SPEC(), prose_fields=None), r, None, cat, ["bg_phaladeepika_latta"], set(), (), set())
    assert ("bg_phaladeepika_latta", ["effect_description"]) in seen and ("other_t", ["effect_description"]) not in seen, seen


def test_each_seeded_defect_flips_the_asset_cell_end_to_end(monkeypatch):
    cases = {"undeclared NULL": STATS(count_from_graha=dict(nulls=1)),
             "constant varies": STATS(source_citation=dict(distinct=2)),
             "fallback": dict(STATS(), cols=dict(STATS()["cols"], effect_description=dict(STATS()["cols"]["effect_description"], fallback=1)))}
    for name, st in cases.items():
        m = _prose(monkeypatch, dict(null_convention=SPEC()), stats=st)
        assert m[BR]["v"] == FAIL and ac.rollup_asset("L0", m)["Null"]["v"] == FAIL, name


def test_schema_default_or_blank_rows_not_pass_keeps_the_cap_even_with_a_verified_convention(monkeypatch):
    m = _prose(monkeypatch, dict(null_convention=SPEC()), cat=_cat(defaults={}), counts=dict(checkable=0, blank=0))
    assert ac.rollup_asset("L0", m)["Null"]["v"] != PASS and m[BR]["v"] == NO_DET
    m = _prose(monkeypatch, dict(null_convention=SPEC()), cat=dict(_cat(), defaults=None))
    assert ac.rollup_asset("L0", m)["Null"]["v"] != PASS


def _bare(rec):
    """a record without the not-earned annotation (the only thing a declared-but-unverified convention may add)"""
    return {k: v for k, v in rec.items() if k != "null_convention"}


def test_an_unverified_convention_leaves_the_records_exactly_as_prose_checks_produced_them_and_says_why(monkeypatch):
    base = _prose(monkeypatch, dict(prose_fields=None))
    m = _prose(monkeypatch, dict(null_convention=SPEC(None), prose_fields=None))                    # PARTIAL convention (unscoped NULLs)
    assert _bare(m[SD]) == base[SD] and _bare(m[BR]) == base[BR]
    for crit in (SD, BR):
        assert m[crit]["null_convention"]["verified"] is False and m[crit]["null_convention"]["v"] == PARTIAL
        assert ac.null_lift_problem(m[crit]) is not None
    m = _prose(monkeypatch, dict(null_convention=SPEC()), stats=dict(rows=1, cols=STATS(1)["cols"]))      # NO_DETECTOR convention
    assert _bare(m[SD]) == base[SD] and _bare(m[BR]) == base[BR] and m[SD]["null_convention"]["v"] == NO_DET
    assert ac.rollup_asset("L0", m)["Null"]["v"] == NO_DET


def test_a_failed_convention_read_keeps_the_cap_and_does_not_error_the_other_checks(monkeypatch):
    def boom(*a, **k):
        raise ac.Unknown("connection lost")
    base = _prose(monkeypatch, dict(prose_fields=None))
    m = _prose(monkeypatch, dict(null_convention=SPEC(), prose_fields=None), fetch=boom)
    assert _bare(m[SD]) == base[SD] and _bare(m[BR]) == base[BR] and m[SD]["null_convention"]["v"] == ERRORED
    assert all(_bare(m[c]) == base[c] for c in base)


def test_a_declaration_for_a_table_the_asset_does_not_own_never_lifts_and_is_reported(monkeypatch):
    spec = SPEC(table="some_other_table")
    m = _prose(monkeypatch, dict(null_convention=spec), fetch=lambda *a, **k: pytest.fail("a table the asset does not own is never read"))
    assert all(m[c]["v"] != PASS for c in (SD, BR))
    assert m[BR]["null_convention"]["declaration_disagreements"][0]["field"] == "null_convention.table" and m[BR]["null_convention"]["verified"] is False


def test_measure_on_a_real_layer_run_lifts_only_the_declaring_asset(monkeypatch, tmp_path):
    import test_e6_a_na_causes as nac
    reg = {"x": nac._reg_row("x", "t_decl", count_sql="SELECT count(*) FROM t_decl"), "y": nac._reg_row("y", "t_old", count_sql="SELECT count(*) FROM t_old")}
    nac._stub_layer(monkeypatch, tmp_path, reg, tables={"t_decl": (LATTA_COLS, [["table_version", "graha"]]), "t_old": (LATTA_COLS, [["table_version", "graha"]])})
    base_cat = ac.catalog
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(base_cat(ts), types={t: dict(LATTA_TYPES) for t in ("t_decl", "t_old")}, defaults={"t_decl": {}, "t_old": {}},
                                                       types_error=None))
    spec = SPEC(table="t_decl")
    monkeypatch.setattr(ac, "load_asset_declarations",
                        lambda *a, **k: {"x": dict(kind="data", null_convention=spec, prose_fields=None), "y": dict(kind="data", prose_fields=None)})
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: STATS())
    monkeypatch.setattr(ac, "prose_row_counts", lambda t, es, tail, types=None: {e: dict(checkable=6, blank=0) for e in es})
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    assert ms["x"][SD]["v"] == PASS and ms["x"][BR]["v"] == PASS
    assert ms["y"][SD]["v"] == NO_DET and ms["y"][BR]["v"] == NO_DET and "null_convention" not in ms["y"][SD]
    rolled = ac.rollup_census(ac.measure("L0"))
    assert rolled["x"]["Null"]["v"] == PASS and rolled["y"]["Null"]["v"] == NO_DET


# ───────────────────────── pin 13 ─────────────────────────

def test_revision_13_pins_the_s1_content():
    assert ac.REGISTRY_REVISION >= 13
    for crit in (SD, BR):
        e = ac.CRITERION_REGISTRY[crit]
        assert e["revision"] >= 2 and "null_convention" in e["applicability"] and "never PASS alone" in e["applicability"], crit
    assert ac.CRITERION_REGISTRY["Null.schema_default"]["detector"] == "asset_census.py:measure()"


def test_the_fingerprint_moves_with_each_s1_part(monkeypatch):
    fp = ac.registry_fingerprint()
    for crit in (SD, BR):
        monkeypatch.setattr(ac, "CRITERION_REGISTRY", {**ac.CRITERION_REGISTRY, crit: dict(ac.CRITERION_REGISTRY[crit], revision=1)})
        assert ac.registry_fingerprint() != fp
        monkeypatch.undo()
        monkeypatch.setattr(ac, "CRITERION_REGISTRY", {**ac.CRITERION_REGISTRY, crit: dict(ac.CRITERION_REGISTRY[crit], applicability="x")})
        assert ac.registry_fingerprint() != fp
        monkeypatch.undo()


def test_no_new_na_rule_or_cause_is_part_of_pin_13():
    assert r13.DECLARED_IDS == set(ac.NA_RULE_DECISIONS)                                   # the table is exactly the revision-12 one


# ───────────────────────── the cells this changes today (saved census, read only) ─────────────────────────

SAVED = pathlib.Path("/Users/Dev/suvarna-evidence/census_fresh/1e5781a")


@pytest.mark.skipif(not (SAVED / "census_L0.json").exists(), reason="the saved baseline census is not on this machine (CI)")
def test_on_the_saved_census_and_the_committed_declarations_no_cell_moves():
    """Only bg_phaladeepika_latta declares `null_convention` (1.11.0), and this rolls up the SAVED measurements (no re-measure), so every one of the 1143 cells keeps its saved
    verdict (Null: 92 NO_DETECTOR, 35 PARTIAL); the latta's Null change comes from a fresh measurement (test_e6_decl_latta_null.py)."""
    from collections import Counter
    decl = ac.load_asset_declarations()
    assert [a for a, e in decl.items() if isinstance(e, dict) and e.get("null_convention")] == ["bg_phaladeepika_latta"]
    null, moved, n = Counter(), [], 0
    for L in ("L0", "L1", "L2", "L3", "L4", "L5"):
        d = json.loads((SAVED / f"census_{L}.json").read_text(encoding="utf-8"))
        saved = d["rollup"]["layers"][L]
        now = ac.rollup_census(d[L], {a["asset_id"]: ac.facts_for_asset(a, decl) for a in d[L]["assets"]})
        for aid, cells in now.items():
            null[cells["Null"]["v"]] += 1
            for g, c in cells.items():
                n += 1
                if c["v"] != saved[aid][g]["v"]:
                    moved.append((aid, g, saved[aid][g]["v"], c["v"]))
    assert n == 1143 and moved == []
    assert dict(null) == {"NO_DETECTOR": 92, "PARTIAL": 35}


# ───────────────────────── REAL SQL: the same statements on a disposable Postgres ─────────────────────────

LATTA_SQL = ["CREATE TEMP TABLE latta_t (table_version text NOT NULL, graha text NOT NULL, count_from_graha smallint, direction text NOT NULL, "
             "effect_description text, affliction_condition text NOT NULL, source_citation text NOT NULL, verse_ref text NOT NULL, "
             "created_at timestamptz NOT NULL DEFAULT '2026-01-01', PRIMARY KEY (table_version, graha)) ON COMMIT DROP;",
             "INSERT INTO latta_t (table_version, graha, count_from_graha, direction, effect_description, affliction_condition, source_citation, verse_ref) VALUES "
             "('v01','Sun',12,'forward','Ruin of every business.','cond','cite','ref'),('v01','Mars',3,'forward',NULL,'cond','cite','ref'),"
             "('v01','Jupiter',6,'forward','Death, ruin.','cond','cite','ref'),('v01','Saturn',8,'forward',NULL,'cond','cite','ref'),"
             "('v01','Venus',5,'backward','Quarrel.','cond','cite','ref'),('v01','Mercury',7,'backward','Loss of position.','cond','cite','ref'),"
             "('v01','Rahu',9,'backward','Misery.','cond','cite','ref'),('v01','Moon',22,'backward','A great loss.','cond','cite','ref');"]
REAL_COLS = ["table_version", "graha", "count_from_graha", "direction", "effect_description", "affliction_condition", "source_citation", "verse_ref", "created_at"]
REAL_TYPES = dict(LATTA_TYPES)


def _rspec(scope="exactly", **over):
    return dict(SPEC(scope, table="latta_t"), **over)


def _check(spec=None):
    return ac.null_convention_check(spec or _rspec(), {"latta_t": (REAL_COLS, REAL_TYPES, {})}, {"latta_t"}, ("", "whole-table (table has no chart_id column)"))


def test_REAL_SQL_the_clean_latta_table_passes_with_the_reserved_null_keys_verified(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_SQL)
    st = ac.null_convention_fetch("latta_t", REAL_COLS, REAL_TYPES, _rspec(), "")
    assert st["rows"] == 8 and st["cols"]["effect_description"]["nulls"] == 2 and st["cols"]["effect_description"]["distinct"] == 6
    assert st["cols"]["effect_description"]["null_outside"] == 0 and st["cols"]["effect_description"]["nonnull_inside"] == 0
    assert st["cols"]["table_version"]["distinct"] == 1 and st["cols"]["graha"]["distinct"] == 8 and st["cols"]["direction"]["distinct"] == 2
    r = _check()
    assert r["v"] == PASS, r


def test_REAL_SQL_an_undeclared_null_in_a_non_nullable_column_flips_the_cell(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET count_from_graha = NULL WHERE graha = 'Sun';"])
    r = _check()
    assert r["v"] == FAIL and r["convention"]["undeclared_nulls"] == {"count_from_graha": 1}, r


def test_REAL_SQL_a_null_on_an_undeclared_key_and_a_value_on_a_reserved_key_flip_the_cell(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET effect_description = NULL WHERE graha = 'Jupiter';"])
    r = _check()
    assert r["v"] == FAIL and "Jupiter" in r["measured"], r
    assert _check(_rspec("only"))["v"] == FAIL                                                       # outside the declared keys in either mode
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET effect_description = 'Some effect.' WHERE graha = 'Mars';"])
    r = _check()
    assert r["v"] == FAIL and "Mars" in r["measured"], r
    assert _check(_rspec("only"))["v"] == PASS                                                       # `only`: a value on a NULL-permitted key is fine


@pytest.mark.parametrize("literal", ["", "   ", "N/A", "n/a", " None ", "NULL", "-", "unknown", "TBD", "{}", "Not Traced"])
def test_REAL_SQL_a_literal_fallback_in_the_declared_nullable_column_flips_the_cell(monkeypatch, disposable_pg, literal):
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + [f"UPDATE latta_t SET effect_description = '{literal}' WHERE graha = 'Mars';"])
    r = _check(_rspec("only"))
    assert r["v"] == FAIL and r["convention"]["fallbacks"] == {"effect_description": 1}, (literal, r)


def test_REAL_SQL_a_zero_sentinel_in_a_declared_nullable_numeric_column_flips_the_cell(monkeypatch, disposable_pg):
    spec = _rspec(nullable=[NULLABLE("exactly"), NULLABLE(None, column="count_from_graha")])
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET count_from_graha = NULL WHERE graha = 'Sun';"])
    assert _check(spec)["v"] == PARTIAL                                                              # a real NULL, no scope: meaning not machine-checked
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET count_from_graha = 0 WHERE graha = 'Sun';"])
    r = _check(spec)
    assert r["v"] == FAIL and r["convention"]["fallbacks"] == {"count_from_graha": 1}, r


def test_REAL_SQL_a_declared_constant_that_varies_and_an_undeclared_constant_flip_the_cell(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET source_citation = 'other cite' WHERE graha = 'Sun';"])
    r = _check()
    assert r["v"] == FAIL and r["convention"]["constant_violations"] == ["source_citation"], r
    s3._real(monkeypatch, disposable_pg, LATTA_SQL)
    spec = _rspec(constants=[dict(column=c, why="w") for c in CONST_COLS if c != "affliction_condition"])
    r = _check(spec)
    assert r["v"] == FAIL and r["convention"]["undeclared_constants"] == ["affliction_condition"], r
    spec = _rspec(constants=[dict(column=c, why="w", **({"value": "cond"} if c == "affliction_condition" else {})) for c in CONST_COLS])
    assert _check(spec)["v"] == PASS
    spec = _rspec(constants=[dict(column=c, why="w", **({"value": "different"} if c == "affliction_condition" else {})) for c in CONST_COLS])
    assert _check(spec)["v"] == FAIL


def test_REAL_SQL_a_column_that_is_null_on_every_row_is_a_dead_constant(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET effect_description = NULL;"])
    r = _check()
    assert r["v"] == FAIL, r


def test_REAL_SQL_the_declared_table_with_one_row_is_no_detector(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["DELETE FROM latta_t WHERE graha <> 'Sun';"])
    assert _check()["v"] == NO_DET


def test_REAL_SQL_a_null_in_the_key_column_counts_as_outside_the_declared_keys(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, [
        "CREATE TEMP TABLE k_t (k text, notes text, v int) ON COMMIT DROP;", "INSERT INTO k_t VALUES ('a', NULL, 1), (NULL, NULL, 2), ('b', 'something', 3);"])
    spec = dict(table="k_t", nullable=[dict(column="notes", means="no note was recorded for this key", scope=dict(key_column="k", null_for=["a"], mode="only"))],
                constants=[], why="w", evidence=EV)
    st = ac.null_convention_fetch("k_t", ["k", "notes", "v"], {"k": "text", "notes": "text", "v": "integer"}, spec, "")
    assert st["cols"]["notes"]["null_outside"] == 1                                  # the NULL-keyed row is outside, never silently skipped by three-valued logic


def test_REAL_SQL_json_and_array_columns_are_read_and_quotes_in_scope_values_are_safe(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, [
        "CREATE TEMP TABLE j_t (k text PRIMARY KEY, notes jsonb, tags text[]) ON COMMIT DROP;",
        "INSERT INTO j_t VALUES ('O''Brien', NULL, ARRAY['a']), ('b', '{\"x\":1}', ARRAY['b']), ('c', '{\"x\":2}', ARRAY['c']);"])
    spec = dict(table="j_t", nullable=[dict(column="notes", means="no notes were recorded for this key", scope=dict(key_column="k", null_for=["O'Brien"], mode="exactly"))],
                constants=[], why="w", evidence=EV)
    r = ac.null_convention_check(spec, {"j_t": (["k", "notes", "tags"], {"k": "text", "notes": "jsonb", "tags": "ARRAY"}, {})}, {"j_t"}, ("", "whole-table"))
    assert r["v"] == PASS, r
    s3._real(monkeypatch, disposable_pg, [
        "CREATE TEMP TABLE j_t (k text PRIMARY KEY, notes jsonb) ON COMMIT DROP;", "INSERT INTO j_t VALUES ('a', '{}'), ('b', '{\"x\":2}');"])
    r = ac.null_convention_check(dict(spec, nullable=[dict(spec["nullable"][0], scope=dict(key_column="k", null_for=["zz"], mode="only"))]),
                                 {"j_t": (["k", "notes"], {"k": "text", "notes": "jsonb"}, {})}, {"j_t"}, ("", "whole-table"))
    assert r["v"] == FAIL and r["convention"]["fallbacks"] == {"notes": 1}, r                     # an empty JSON object standing in for NULL


def test_REAL_SQL_the_whole_chain_lifts_the_cap_on_the_clean_table_and_not_on_a_defective_one(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_SQL)
    cat = dict(_cat(table="latta_t"), keys={"latta_t": [["table_version", "graha"]]})
    r = dict(target_table="latta_t", count_sql="SELECT count(*) FROM latta_t")
    decl = dict(null_convention=_rspec(), prose_fields=None)
    m = ac._measure_prose("bg_phaladeepika_latta", decl, r, None, cat, [], set(), (), set())
    assert m[SD]["v"] == PASS and m[BR]["v"] == PASS and ac.rollup_asset("L0", m)["Null"]["v"] == PASS, (m[SD], m[BR])
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET count_from_graha = NULL WHERE graha = 'Sun';"])
    m = ac._measure_prose("bg_phaladeepika_latta", decl, r, None, cat, [], set(), (), set())
    assert ac.rollup_asset("L0", m)["Null"]["v"] == FAIL
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET effect_description = '' WHERE graha = 'Mars';"])
    m = ac._measure_prose("bg_phaladeepika_latta", decl, r, None, cat, [], set(), (), set())
    assert ac.rollup_asset("L0", m)["Null"]["v"] == FAIL and m[BR]["v"] == FAIL


# ═════════════════════ adversarial review round: F1, F2, L1-L6 and the survivors ═════════════════════

# ---- F1: the chart-scope parameter must be bound before the convention read -------------------------------------------------------------------

CHART_R = dict(target_table="bg_phaladeepika_latta", count_sql="SELECT count(*) FROM bg_phaladeepika_latta WHERE chart_id = $1")


def test_F1_the_chart_scope_is_bound_before_the_convention_read_through_measure_prose(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "null_convention_fetch", lambda t, cols, types, spec, tail="": seen.append(tail) or STATS())
    monkeypatch.setattr(ac, "prose_row_counts", lambda t, es, tail, types=None: {e: dict(checkable=6, blank=0) for e in es})
    cols = LATTA_COLS + ["chart_id"]
    cat = _cat(cols=cols, types=dict(LATTA_TYPES, chart_id="uuid"))
    spec = SPEC(constants=SPEC()["constants"] + [dict(column="chart_id", why=WHY)])
    st = STATS()
    st["cols"]["chart_id"] = _col(8, distinct=1, sole="c")
    monkeypatch.setattr(ac, "null_convention_fetch", lambda t, c, ty, sp, tail="": seen.append(tail) or st)
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=spec, prose_fields=None), CHART_R, None, cat, [], set(), (), set())
    assert seen and all("$1" not in x and ac.CHART_ID in x for x in seen), seen              # bound exactly as _group_counts binds it
    assert m[SD]["v"] == PASS and m[BR]["v"] == PASS


def test_F1_an_unbindable_scope_degrades_only_this_check(monkeypatch):
    monkeypatch.setattr(ac, "CHART_ID", "362f9f17-0000-0000-0000-000000000000")               # the dead phantom: refused by _bind_chart
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: pytest.fail("an unbound scope is never read"))
    monkeypatch.setattr(ac, "prose_row_counts", lambda t, es, tail, types=None: {e: dict(checkable=6, blank=0) for e in es})
    cat = _cat(cols=LATTA_COLS + ["chart_id"], types=dict(LATTA_TYPES, chart_id="uuid"))
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=SPEC(), prose_fields=None), CHART_R, None, cat, [], set(), (), set())
    assert m[SD]["null_convention"]["v"] == ERRORED and m[SD]["v"] != PASS and m[BR]["v"] != PASS


CHART_SQL = ["CREATE TEMP TABLE cs_t (chart_id text NOT NULL, graha text NOT NULL, count_from_graha smallint, effect_description text, "
             "table_version text NOT NULL) ON COMMIT DROP;",
             "INSERT INTO cs_t VALUES " + ",".join(
                 f"('{ac.CHART_ID}','{g}',{i},{'NULL' if g in ('Mars', 'Saturn') else repr('effect of ' + g)},'v01')"
                 for i, g in enumerate(("Sun", "Mars", "Jupiter", "Saturn", "Venus", "Mercury", "Rahu", "Moon"), 1)) + ";"]
CS_TYPES = {"chart_id": "text", "graha": "text", "count_from_graha": "smallint", "effect_description": "text", "table_version": "text"}


def _cs_spec():
    return dict(table="cs_t", nullable=[NULLABLE("exactly")], constants=[dict(column="chart_id", why=WHY), dict(column="table_version", why=WHY)],
                why=SPEC()["why"], evidence=EV)


def test_REAL_SQL_F1_a_chart_scoped_count_sql_earns_the_lift_end_to_end_and_other_charts_rows_never_fail_it(monkeypatch, disposable_pg):
    other = "('00000000-0000-0000-0000-000000000001','Sun',NULL,NULL,'v99')"                 # another chart's row: undeclared NULL, a different constant
    s3._real(monkeypatch, disposable_pg, CHART_SQL + [f"INSERT INTO cs_t VALUES {other};"])
    cat = dict(exists={"cs_t"}, cols={"cs_t": list(CS_TYPES)}, keys={"cs_t": [["chart_id", "graha"]]}, views=set(), types={"cs_t": dict(CS_TYPES)}, defaults={"cs_t": {}},
               types_error=None)
    r = dict(target_table="cs_t", count_sql="SELECT count(*) FROM cs_t WHERE chart_id = $1")
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=_cs_spec(), prose_fields=None), r, None, cat, [], set(), (), set())
    assert m[SD]["v"] == PASS and m[BR]["v"] == PASS, (m[SD], m[BR])                          # the `$1` is bound; this chart's rows are clean
    assert ac.rollup_asset("L1", m)["Null"]["v"] == PASS


def test_REAL_SQL_L1_an_unbound_whole_table_read_never_fails_on_another_charts_rows(monkeypatch, disposable_pg):
    other = "('00000000-0000-0000-0000-000000000001','Sun',NULL,NULL,'v99')"
    s3._real(monkeypatch, disposable_pg, CHART_SQL + [f"INSERT INTO cs_t VALUES {other};"])
    cat = dict(exists={"cs_t"}, cols={"cs_t": list(CS_TYPES)}, keys={"cs_t": [["chart_id", "graha"]]}, views=set(), types={"cs_t": dict(CS_TYPES)}, defaults={"cs_t": {}},
               types_error=None)
    r = dict(target_table="cs_t", count_sql="SELECT count(*) FROM cs_t")                          # no chart binding, the table carries chart_id: a whole-table upper bound
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=_cs_spec(), prose_fields=None), r, None, cat, [], set(), (), set())
    conv = m[BR]["null_convention"]
    assert conv["v"] == PARTIAL and ac.UPPER_BOUND in conv["measured"] and "FAIL" in conv["measured"], conv     # the whole table reads FAIL; this chart is not failed on it
    assert m[BR]["v"] != FAIL and m[SD]["v"] != PASS and m[BR]["v"] != PASS
    assert ac.rollup_asset("L1", m)["Null"]["v"] != FAIL


def test_L1_an_upper_bound_clean_table_is_partial_never_pass_and_a_scoped_one_is_unchanged(monkeypatch):
    for label, want in ((ac.UPPER_BOUND, PARTIAL), ("chart-scoped by count_sql", PASS), ("whole-table (table has no chart_id column)", PASS)):
        monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: STATS())
        r = ac.null_convention_check(SPEC(), _own(), {"bg_phaladeepika_latta"}, ("", label))
        assert r["v"] == want, (label, r)
    st = STATS(count_from_graha=dict(nulls=1))
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: st)
    r = ac.null_convention_check(SPEC(), _own(), {"bg_phaladeepika_latta"}, ("", ac.UPPER_BOUND))
    assert r["v"] == PARTIAL and "reads FAIL" in r["measured"]
    assert ac.null_convention_check(SPEC(), _own(), {"bg_phaladeepika_latta"}, ("", "chart-scoped by count_sql"))["v"] == FAIL


# ---- F2: ONE definition of "literal fallback" (S3's), on every text-like column -----------------------------------------------------------------

F2_LITERALS = ["0", "Ｎ/Ａ", "ＮＯＮＥ", "n​/a", "n­/a", "N/A.", "N.A", "N / A", "—", "–", "...", "pending", "TBD.", "missing",
               "false", "not found", "　", " ", "", "   ", "N/A", "n/a", " None ", "NULL", "-", "unknown", "TBD", "{}", "Not Traced", "nil", "not applicable"]


def _lit_ids(v):
    return "lit-" + "-".join(f"{ord(c):04x}" for c in v)[:40] if v else "lit-empty"


@pytest.mark.parametrize("literal", F2_LITERALS, ids=_lit_ids)
def test_REAL_SQL_F2_every_placeholder_form_in_a_declared_nullable_text_column_flips_the_cell(monkeypatch, disposable_pg, literal):
    lit = literal.replace("'", "''")
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + [f"UPDATE latta_t SET effect_description = '{lit}' WHERE graha = 'Jupiter';"])
    r = _check(_rspec("only"))
    assert r["v"] == FAIL and r["convention"]["fallbacks"] == {"effect_description": 1}, (literal, r)


@pytest.mark.parametrize("literal", ["", "   ", "N/A", "none", "ＮＯＮＥ", "n​/a", "-", "pending", "false", "0", "　"], ids=_lit_ids)
def test_REAL_SQL_F2_a_placeholder_in_a_NON_nullable_text_column_is_a_fallback_too(monkeypatch, disposable_pg, literal):
    lit = literal.replace("'", "''")
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + [f"UPDATE latta_t SET direction = '{lit}' WHERE graha = 'Sun';"])
    r = _check()
    assert r["v"] == FAIL and r["convention"]["fallbacks"].get("direction") == 1, (literal, r)
    assert "not declared nullable" in r["measured"]


def test_REAL_SQL_F2_a_legitimate_value_that_collides_with_the_list_must_be_declared_never_guessed(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET direction = 'none' WHERE graha = 'Sun';"])
    assert _check()["v"] == FAIL
    allowed = _rspec(allowed_literals=[dict(column="direction", values=["none"], why="a graha with no direction is stored as the word none")])
    assert _check(allowed)["v"] == PASS
    still = _rspec(allowed_literals=[dict(column="direction", values=["none"], why="a graha with no direction is stored as the word none")])
    s3._real(monkeypatch, disposable_pg, LATTA_SQL + ["UPDATE latta_t SET direction = 'N/A' WHERE graha = 'Sun';"])
    assert _check(still)["v"] == FAIL                                                       # only the declared literal is allowed, not its neighbours


def test_REAL_SQL_F2_the_pass_text_names_the_columns_actually_checked(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, LATTA_SQL)
    r = _check()
    assert r["v"] == PASS
    for c in ("table_version", "graha", "direction", "effect_description", "affliction_condition", "source_citation", "verse_ref"):
        assert c in r["measured"], c
    assert "count_from_graha" not in r["convention"]["fallback_checked_columns"]              # a non-nullable smallint cannot hold a text fallback
    assert set(r["convention"]["fallback_checked_columns"]) >= {"table_version", "graha", "direction", "effect_description"}


def test_REAL_SQL_F2_array_and_json_columns_use_the_same_definition(monkeypatch, disposable_pg):
    sp = dict(table="aj_t", nullable=[dict(column="notes", means="the source gives no note for this row", scope=dict(key_column="k", null_for=["a"], mode="only")),
                                      dict(column="tags", means="no tag was recorded for this row at all", scope=dict(key_column="k", null_for=["a"], mode="only"))],
              constants=[], why=SPEC()["why"], evidence=EV)
    types = {"k": "text", "notes": "jsonb", "tags": "ARRAY", "v": "integer"}
    for notes, tags, ok in (("'{\"x\":1}'", "ARRAY['t1']", True), ("'\"N/A\"'", "ARRAY['t1']", False), ("'null'", "ARRAY['t1']", False), ("'[]'", "ARRAY['t1']", False),
                            ("'{\"x\":1}'", "ARRAY['t1','none']", False), ("'{\"x\":1}'", "ARRAY[]::text[]", False), ("'{\"x\":1}'", "ARRAY['Ｎ/Ａ']", False)):
        s3._real(monkeypatch, disposable_pg, [
            "CREATE TEMP TABLE aj_t (k text PRIMARY KEY, notes jsonb, tags text[], v int NOT NULL) ON COMMIT DROP;",
            f"INSERT INTO aj_t VALUES ('a', NULL, NULL, 1), ('b', {notes}, {tags}, 2), ('c', '{{\"y\":2}}', ARRAY['t2'], 3);"])
        r = ac.null_convention_check(sp, {"aj_t": (["k", "notes", "tags", "v"], types, {})}, {"aj_t"}, ("", "whole-table"))
        assert (r["v"] == PASS) is ok, (notes, tags, r)


def test_REAL_SQL_F2_the_ground_truth_of_the_shared_predicate_is_s3s_ldgr_lacking_text(monkeypatch, disposable_pg):
    """The convention's fallback test IS `_ldgr_lacking_text`: for every literal, the convention flags it exactly when S3's predicate says the text lacks a value."""
    s3._real(monkeypatch, disposable_pg, [])
    for lit in F2_LITERALS + ["Phaladeepika 26.42", "श्लोक १", "Ruin of every business.", "a", "x1"]:
        q = lit.replace("'", "''")
        got = ac.scalar(f"SELECT {ac._ldgr_lacking_text(chr(39) + q + chr(39) + '::text')}")
        s3._real(monkeypatch, disposable_pg, [f"CREATE TEMP TABLE one_t (k int, c text, d text) ON COMMIT DROP;", f"INSERT INTO one_t VALUES (1, '{q}', 'x'), (2, 'a real value', 'y');"])
        sp = dict(table="one_t", nullable=[], constants=[], why=SPEC()["why"], evidence=EV)
        rec = ac.null_convention_check(sp, {"one_t": (["k", "c", "d"], {"k": "integer", "c": "text", "d": "text"}, {})}, {"one_t"}, ("", "whole-table"))
        assert (rec["v"] == FAIL and "c" in rec["convention"]["fallbacks"]) == (got in ("t", "true")), (lit, got, rec["v"])


# ---- L2/L3/L4/L6 and the survivors: validator and detector ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("nc, match", [
    (SPEC(allowed_literals="direction"), "allowed_literals must be a list"),
    (SPEC(allowed_literals=["direction"]), "allowed_literals entry 0"),
    (SPEC(allowed_literals=[dict(column="direction", values=["none"], why=WHY, extra=1)]), "unknown field"),
    (SPEC(allowed_literals=[dict(column="a b", values=["none"], why=WHY)]), r"allowed_literals\[0\]\.column"),
    (SPEC(allowed_literals=[dict(column="direction", values=[], why=WHY)]), r"allowed_literals\[0\]\.values"),
    (SPEC(allowed_literals=[dict(column="direction", values="none", why=WHY)]), r"allowed_literals\[0\]\.values"),
    (SPEC(allowed_literals=[dict(column="direction", values=["none", "none"], why=WHY)]), "duplicate"),
    (SPEC(allowed_literals=[dict(column="direction", values=[""], why=WHY)]), r"values entry"),
    (SPEC(allowed_literals=[dict(column="direction", values=["a\\b"], why=WHY)]), r"values entry"),
    (SPEC(allowed_literals=[dict(column="direction", values=["a b"], why=WHY)]), r"values entry"),
    (SPEC(allowed_literals=[dict(column="direction", values=[str(i) for i in range(21)], why=WHY)]), r"allowed_literals\[0\]\.values"),
    (SPEC(allowed_literals=[dict(column="direction", values=["none"])]), r"allowed_literals\[0\]\.why"),
    (SPEC(allowed_literals=[dict(column="direction", values=["none"], why="TBD later")]), r"allowed_literals\[0\]\.why"),
    (SPEC(allowed_literals=[dict(column="direction", values=["none"], why=WHY)] * 2), "duplicate"),
    (SPEC(allowed_literals=[dict(column="effect_description", values=["none"], why=WHY)]), "the fallback itself"),                  # nullable: NULL is the only absent value
    (SPEC(allowed_literals=[dict(column="direction", values=["x"], why=WHY)] * 65), "at most"),
    (SPEC(nullable=[NULLABLE("exactly", means="reserved NULL here for the graha")]), r"nullable\[0\]\.means"),                      # S3 placeholder word 'NULL'
    (SPEC(nullable=[NULLABLE("exactly", means="to be decided, TBD for every graha")]), r"nullable\[0\]\.means"),
    (SPEC(nullable=[NULLABLE("exactly", means="pending the next passage review")]), r"nullable\[0\]\.means"),
    (SPEC(nullable=[NULLABLE("exactly", means="no effect clause in the passage")]), r"nullable\[0\]\.means"),
    (SPEC(nullable=[NULLABLE("exactly", means="x" * 5 + " a b")]), r"nullable\[0\]\.means"),                                          # too short in characters
    (SPEC(constants=[dict(column="table_version", why="unknown for all rows here")]), r"constants\[0\]\.why"),
    (SPEC(constants=[dict(column="table_version", why="one seed version per set")]), r"constants\[0\]\.why"),
    (SPEC(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=["Ma rs"], mode="only"))]), r"null_for entry"),    # line separator
    (SPEC(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=["Ma​rs"], mode="only"))]), r"null_for entry"),    # format character
    (SPEC(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=["Ma\\rs"], mode="only"))]), "backslash"),               # the backslash rule on its own
    (SPEC(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=["x" * 129], mode="only"))]), r"null_for entry"),
    (SPEC(nullable=[NULLABLE(None, scope_obj=dict(key_column="graha", null_for=[str(i) for i in range(101)], mode="only"))]), "more than"),
    (SPEC(nullable=[NULLABLE(None, column=f"c{i}") for i in range(65)]), "more than 64"),
    (SPEC(constants=[dict(column=f"c{i}", why=WHY) for i in range(257)]), "more than"),
])
def test_validator_review_round_refusals(nc, match):
    _bad(nc, match)


def test_the_nullable_and_constant_rule_stands_alone():
    ok = SPEC(nullable=[NULLABLE(None, column="notes")], constants=[dict(column="table_version", why=WHY)])
    ac.validate_declarations(_doc(dict(null_convention=ok)))
    both = SPEC(nullable=[NULLABLE(None, column="notes")], constants=[dict(column="notes", why=WHY)])
    _bad(both, "both nullable and constant")
    _bad(SPEC(nullable=[NULLABLE(None, column="notes")], constants=[dict(column="notes", why=WHY, value="x")]), r"\['notes'\] are both nullable and constant")


def test_the_validator_accepts_an_allowed_literal_on_a_non_nullable_column():
    ac.validate_declarations(_doc(dict(null_convention=SPEC(allowed_literals=[dict(column="direction", values=["none", "N/A"], why="a graha with no direction stores these words")]))))
    ac.validate_declarations(_doc(dict(null_convention=SPEC(allowed_literals=None))))


def test_L6_a_scope_key_the_table_does_not_carry_fails_before_any_read_like_an_absent_nullable_column(monkeypatch):
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: pytest.fail("a declaration the table cannot back is never read"))
    for spec in (SPEC(nullable=[dict(NULLABLE("exactly"), scope=dict(key_column="no_key", null_for=["Mars"], mode="only"))]),
                 SPEC(nullable=[NULLABLE("exactly", column="no_such_col")]), SPEC(constants=[dict(column="no_such_col", why=WHY)]),
                 SPEC(allowed_literals=[dict(column="no_such_col", values=["none"], why=WHY)])):
        r = ac.null_convention_check(spec, _own(), {"bg_phaladeepika_latta"}, ("", "whole-table"))
        assert r["v"] == FAIL and "not columns of" in r["measured"], r


def test_L6_numerics_that_differ_only_in_formatting_are_one_constant_value():
    types = dict(LATTA_TYPES, count_from_graha="numeric")
    spec = SPEC(constants=SPEC()["constants"] + [dict(column="count_from_graha", why=WHY, value="1")])
    st = STATS(count_from_graha=dict(distinct=1, sole="1.00"))
    assert ac.grade_null_convention(spec, LATTA_COLS, types, st)["v"] == PASS                      # 1 == 1.00 as a number
    assert ac.grade_null_convention(spec, LATTA_COLS, dict(types, count_from_graha="text"), st)["v"] == FAIL    # as text they differ
    assert ac.grade_null_convention(spec, LATTA_COLS, types, STATS(count_from_graha=dict(distinct=1, sole="2")))["v"] == FAIL
    assert ac.grade_null_convention(spec, LATTA_COLS, types, STATS(count_from_graha=dict(distinct=1, sole="abc")))["v"] == FAIL


def test_REAL_SQL_L6_the_distinct_count_of_a_numeric_column_is_by_value(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, [
        "CREATE TEMP TABLE n_t (k int PRIMARY KEY, w numeric NOT NULL) ON COMMIT DROP;", "INSERT INTO n_t VALUES (1, 1), (2, 1.0), (3, 1.00);"])
    spec = dict(table="n_t", nullable=[], constants=[dict(column="w", why=WHY, value="1")], why=SPEC()["why"], evidence=EV)
    r = ac.null_convention_check(spec, {"n_t": (["k", "w"], {"k": "integer", "w": "numeric"}, {})}, {"n_t"}, ("", "whole-table"))
    assert r["v"] == PASS, r


def test_L4_a_failed_read_of_any_kind_ends_errored_never_a_crash(monkeypatch):
    for exc in (ac.Unknown("x"), ac.CheckTimeout("client timeout"), OSError("disk"), ValueError("bad"), UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad")):
        def boom(*a, **k):
            raise exc
        monkeypatch.setattr(ac, "null_convention_fetch", boom)
        r = ac.null_convention_check(SPEC(), _own(), {"bg_phaladeepika_latta"}, ("", "whole-table"))
        assert r["v"] == ERRORED and r["declared"] is True, (exc, r)


def test_L4_an_unexpected_error_from_the_convention_ends_errored_in_measure_prose(monkeypatch):
    """The `except` around the convention call in _measure_prose: the records stay what prose_checks wrote, annotated errored, and nothing reads PASS."""
    base = _prose(monkeypatch, dict(prose_fields=None))
    for exc in (ac.Unknown("x"), OSError("o"), ValueError("v")):
        def boom(*a, **k):
            raise exc
        monkeypatch.setattr(ac, "_measure_null_convention", boom)
        m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=SPEC(), prose_fields=None), LATTA_R, None, _cat(), [], set(), (), set())
        assert m[SD]["null_convention"]["v"] == ERRORED and m[BR]["null_convention"]["verified"] is False
        assert _bare(m[SD]) == base[SD] and _bare(m[BR]) == base[BR]
        monkeypatch.undo()


def test_a_failed_count_read_inside_the_convention_path_ends_capped_with_no_pass(monkeypatch):
    def boom(t, es, tail, types=None):
        raise ac.Unknown("connection lost")
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: STATS())
    monkeypatch.setattr(ac, "prose_row_counts", boom)
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=SPEC(), prose_fields=None), LATTA_R, None, _cat(), [], set(), (), set())
    assert ac.rollup_asset("L0", m)["Null"]["v"] != PASS and m[BR]["v"] != PASS and m[SD]["v"] != PASS
    assert m[BR]["null_convention"]["verified"] is False


def test_a_declared_prose_field_outside_the_declared_table_keeps_the_cap(monkeypatch):
    monkeypatch.setattr(ac, "null_convention_fetch", lambda *a, **k: STATS())
    monkeypatch.setattr(ac, "prose_row_counts", lambda t, es, tail, types=None: {e: dict(checkable=6, blank=0) for e in es})
    cat = dict(_cat(), exists={"bg_phaladeepika_latta", "other_t"}, cols={"bg_phaladeepika_latta": list(LATTA_COLS), "other_t": ["id", "narrative"]},
               types={"bg_phaladeepika_latta": dict(LATTA_TYPES), "other_t": {"id": "integer", "narrative": "text"}},
               defaults={"bg_phaladeepika_latta": {}, "other_t": {}})
    r = dict(target_table="bg_phaladeepika_latta", count_sql="SELECT count(*) FROM bg_phaladeepika_latta")
    m = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=SPEC(), prose_fields=["narrative"]), r, None, cat, ["other_t"], set(), (), set())
    assert m[SD]["v"] != PASS and m[BR]["v"] != PASS and m[BR]["null_convention"]["uncovered_prose_fields"] == ["narrative"]
    ok = ac._measure_prose("bg_phaladeepika_latta", dict(null_convention=SPEC(), prose_fields=["affliction_condition"]), r, None, cat, ["other_t"], set(), (), set())
    assert ok[SD]["v"] == PASS                                                                   # a prose field IN the declared table is covered


# ---- L5: the distinct count skips the expensive types ---------------------------------------------------------------------------------------------

def test_L5_a_json_or_bytea_column_is_not_distinct_counted_unless_declared_constant_and_is_named_as_not_examined(monkeypatch):
    types = {"k": "text", "doc": "jsonb", "blob": "bytea", "emb": "USER-DEFINED", "cst": "jsonb"}
    got = _capture(monkeypatch, "{}", types)
    spec = dict(table="t", nullable=[], constants=[dict(column="cst", why=WHY)], why=SPEC()["why"], evidence=EV)
    try:
        ac.null_convention_fetch("t", list(types), types, spec, "")
    except ac.Unknown:
        pass
    sql = got[0]
    assert 'count(DISTINCT "k"::text)' in sql and 'count(DISTINCT "cst"::text)' in sql
    for c in ("doc", "blob", "emb"):
        assert f'count(DISTINCT "{c}"' not in sql, c
    st = dict(rows=3, cols={"k": _col(3), "doc": dict(nulls=0, distinct=None, fallback=0), "blob": dict(nulls=0, distinct=None), "emb": dict(nulls=0, distinct=None),
                            "cst": dict(nulls=0, distinct=1, sole="{}", fallback=0)})
    r = ac.grade_null_convention(spec, list(types), types, st)
    assert r["v"] == PASS and r["convention"]["constants_not_examined"] == ["doc", "blob", "emb"] and "constants NOT examined (kind not distinct-counted, cost): doc (json), blob (blob), emb (blob)" in r["measured"]


def test_L5_a_missing_distinct_on_a_countable_column_is_malformed():
    st = STATS()
    st["cols"]["graha"]["distinct"] = None
    with pytest.raises(ac.Unknown):
        ac.grade_null_convention(SPEC(), LATTA_COLS, LATTA_TYPES, st)


def test_the_fetch_needs_every_column_type():
    with pytest.raises(ac.Unknown, match="data type"):
        ac.null_convention_fetch("bg_phaladeepika_latta", LATTA_COLS, {"graha": "text"}, SPEC(), "")
    r = ac.null_convention_check(SPEC(), _own({"bg_phaladeepika_latta": (LATTA_COLS, {"graha": "text"}, {})}), {"bg_phaladeepika_latta"}, ("", "whole-table"))
    assert r["v"] == NO_DET and "data types" in r["measured"]


# ═════════════════ re-review round: M1 and the LOW findings (types, JSON leaves, arrays, exemptions, cost) ═════════════════

def _mp_real(monkeypatch, pg, setup, table, types, spec, count_sql=None):
    """Run the whole convention path THROUGH _measure_prose on the disposable Postgres: `setup` creates TEMP table `table`; `types` is its information_schema data_type map."""
    s3._real(monkeypatch, pg, setup)
    cat = dict(exists={table}, cols={table: list(types)}, keys={table: [["k"]]}, views=set(), types={table: dict(types)}, defaults={table: {}}, types_error=None)
    r = dict(target_table=table, count_sql=count_sql or f"SELECT count(*) FROM {table}")
    return ac._measure_prose("bg_x", dict(null_convention=dict(spec, table=table), prose_fields=None), r, None, cat, [], set(), (), set())


def _cv(m):
    """What the detector said about the convention (the annotation / the lift block): independent of whether the Null checks could be lifted (a table with no nullable
    column has no entry to check for blank rows, so its records stay capped even when the convention verifies)."""
    return m[BR]["null_convention"]["v"]


def _gspec(nullable=(), constants=(), allowed=None, why=None):
    d = dict(table="x_t", nullable=list(nullable), constants=list(constants), why=SPEC()["why"], evidence=EV)
    if allowed:
        d["allowed_literals"] = allowed
    return d


def _nul(column, scope_keys=None):
    n = dict(column=column, means="the source gives no value for this row, so the cell stays empty")
    if scope_keys:
        n["scope"] = dict(key_column="k", null_for=scope_keys, mode="only")
    return n


M1_SQL = ["CREATE TYPE mood_t AS ENUM ('good', 'bad', 'N/A');",
          "CREATE TEMP TABLE x_t (k text PRIMARY KEY, flag boolean, born date, seen timestamptz, mood mood_t, w int NOT NULL) ON COMMIT DROP;",
          "INSERT INTO x_t VALUES ('a', NULL, NULL, NULL, NULL, 1), ('b', true, '2020-01-01', '2020-01-02 00:00+00', 'good', 2), ('c', false, '2021-01-01', '2021-01-02 00:00+00', 'bad', 3);"]
M1_TYPES = {"k": "text", "flag": "boolean", "born": "date", "seen": "timestamp with time zone", "mood": "USER-DEFINED", "w": "integer"}


def test_REAL_SQL_M1_nullable_boolean_date_timestamptz_and_enum_columns_reach_pass_through_measure_prose(monkeypatch, disposable_pg):
    spec = _gspec([_nul(c, ["a"]) for c in ("flag", "born", "seen", "mood")])
    m = _mp_real(monkeypatch, disposable_pg, M1_SQL, "x_t", M1_TYPES, spec)
    conv = m[BR]["null_convention"]
    assert m[SD]["v"] == PASS and m[BR]["v"] == PASS, (m[SD], m[BR])
    assert conv["verified"] is True
    assert ac.rollup_asset("L1", m)["Null"]["v"] == PASS


def test_M1_a_nullable_non_text_column_without_a_fallback_stat_is_not_malformed():
    types = {"k": "text", "flag": "boolean", "born": "date", "seen": "timestamp with time zone", "w": "integer"}
    nullable = {c: _nul(c, ["a"]) for c in ("flag", "born", "seen")}
    cols = list(types)
    per = {c: dict(nulls=0, distinct=3) for c in cols}
    for c in nullable:
        per[c].update(nulls=1, distinct=2, null_outside=0, null_outside_keys=[])
    per["k"]["fallback"] = 0
    st = dict(rows=3, cols=per)
    spec = _gspec(list(nullable.values()))
    r = ac.grade_null_convention(spec, cols, types, st)
    assert r["v"] == PASS, r
    assert set(r["convention"]["fallback_not_applicable"]) == {"flag", "born", "seen", "w"}
    for c in ("flag", "born", "seen"):
        assert f"{c} (" in r["measured"]
    assert "NOT examined for a literal fallback" in r["measured"]
    bad = copy.deepcopy(st)
    del bad["cols"]["k"]["fallback"]                                  # a text column that lost its fallback stat IS malformed: fail closed
    with pytest.raises(ac.Unknown):
        ac.grade_null_convention(spec, cols, types, bad)
    bad2 = copy.deepcopy(st)
    bad2["cols"]["flag"].pop("null_outside")                          # a scoped nullable column without its scope stats too
    with pytest.raises(ac.Unknown):
        ac.grade_null_convention(spec, cols, types, bad2)


def test_REAL_SQL_LOW1_enum_label_text_and_a_domain_over_text_are_fallback_checked(monkeypatch, disposable_pg):
    spec = _gspec([_nul(c, ["a"]) for c in ("flag", "born", "seen", "mood")])
    types = dict(M1_TYPES)
    ok = _mp_real(monkeypatch, disposable_pg, M1_SQL, "x_t", types, spec)
    assert ok[BR]["v"] == PASS, ok[BR]
    flip = _mp_real(monkeypatch, disposable_pg, M1_SQL + ["UPDATE x_t SET mood = 'N/A' WHERE k = 'b';"], "x_t", types, spec)      # the enum LABEL 'N/A' is a fallback
    assert flip[BR]["v"] == FAIL and "mood" in flip[BR]["null_convention"]["convention"]["fallbacks"], flip[BR]
    dom = ["CREATE DOMAIN txt_d AS text;", "CREATE TEMP TABLE x_t (k text PRIMARY KEY, d txt_d, w int NOT NULL) ON COMMIT DROP;",
           "INSERT INTO x_t VALUES ('a', 'real value', 1), ('b', 'N/A', 2), ('c', 'another', 3);"]
    r = _mp_real(monkeypatch, disposable_pg, dom, "x_t", {"k": "text", "d": "text", "w": "integer"}, _gspec())
    assert r[BR]["v"] == FAIL and r[BR]["null_convention"]["convention"]["fallbacks"] == {"d": 1}
    r = _mp_real(monkeypatch, disposable_pg, dom + ["UPDATE x_t SET d = 'fine ' || k;"], "x_t", {"k": "text", "d": "text", "w": "integer"}, _gspec())
    assert _cv(r) == PASS                                                                    # a domain over text with real values is fine


def test_REAL_SQL_LOW1_citext_is_text_when_the_extension_exists(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, [])
    if not ac.psql("SELECT 1 FROM pg_available_extensions WHERE name = 'citext'"):
        pytest.skip("the citext extension is not installed in this PostgreSQL")
    setup = ["CREATE EXTENSION IF NOT EXISTS citext;", "CREATE TEMP TABLE x_t (k text PRIMARY KEY, c citext, w int NOT NULL) ON COMMIT DROP;",
             "INSERT INTO x_t VALUES ('a', 'real', 1), ('b', 'N/A', 2), ('c', 'other', 3);"]
    kinds = None
    s3._real(monkeypatch, disposable_pg, setup)
    assert ac.null_fetch_column_kinds("x_t", ["k", "c", "w"]) == {"k": "text", "c": "text", "w": "num"}
    r = _mp_real(monkeypatch, disposable_pg, setup, "x_t", {"k": "text", "c": "USER-DEFINED", "w": "integer"}, _gspec())
    assert r[BR]["v"] == FAIL and r[BR]["null_convention"]["convention"]["fallbacks"] == {"c": 1}


def test_null_kind_from_the_catalog_covers_every_category():
    f = ac._null_kind_from_catalog
    assert [f("text", "S", None), f("citext", "S", None), f("mood", "E", None), f("int4", "N", None), f("bool", "B", None), f("jsonb", "U", None), f("json", "U", None),
            f("bytea", "U", None), f("vector", "U", None), f("tsvector", "U", None), f("uuid", "U", None), f("date", "D", None), f("timestamptz", "D", None)] == \
        ["text", "text", "text", "num", "bool", "json", "json", "blob", "blob", "blob", "other", "other", "other"]
    assert [f("_text", "A", "S"), f("_mood", "A", "E"), f("_float8", "A", "N"), f("_bool", "A", "B"), f("_uuid", "A", "U")] == \
        ["array_text", "array_text", "array_num", "array_bool", "array_other"]


@pytest.mark.parametrize("value, bad", [("'{\"src\":\"N/A\"}'", True), ("'[\"N/A\"]'", True), ("'{\"a\":null}'", True), ("'[null]'", True), ("'[\"none\"]'", True),
                                        ("'{\"a\":{\"b\":\"\\uff2e/\\uff21\"}}'", True), ("'{\"a\":{\"b\":[\"pending\"]}}'", True), ("'null'", True), ("'{}'", True), ("'[]'", True),
                                        ("'\"N/A\"'", True), ("'{\"a\":{\"b\":\"real\"},\"c\":[\"x\",\"y\"]}'", False), ("'{\"n\":3}'", False), ("'\"a real note\"'", False)])
def test_REAL_SQL_LOW2_json_is_checked_at_every_depth(monkeypatch, disposable_pg, value, bad):
    setup = ["CREATE TEMP TABLE x_t (k text PRIMARY KEY, doc jsonb, w int NOT NULL) ON COMMIT DROP;",
             f"INSERT INTO x_t VALUES ('a', NULL, 1), ('b', {value}, 2), ('c', '{{\"z\":\"fine\"}}', 3);"]
    spec = _gspec([_nul("doc", ["a"])])
    m = _mp_real(monkeypatch, disposable_pg, setup, "x_t", {"k": "text", "doc": "jsonb", "w": "integer"}, spec)
    assert (m[BR]["v"] == FAIL) is bad, (value, m[BR])


def test_REAL_SQL_LOW2_a_json_allowed_literal_is_compared_per_string_leaf(monkeypatch, disposable_pg):
    setup = ["CREATE TEMP TABLE x_t (k text PRIMARY KEY, doc jsonb NOT NULL, w int NOT NULL) ON COMMIT DROP;",
             "INSERT INTO x_t VALUES ('a', '{\"s\":\"none\"}', 1), ('b', '{\"s\":\"x\"}', 2);"]
    types = {"k": "text", "doc": "jsonb", "w": "integer"}
    assert _cv(_mp_real(monkeypatch, disposable_pg, setup, "x_t", types, _gspec())) == FAIL
    al = [dict(column="doc", values=["none"], why="a leaf with no value is stored as the word none")]
    got = _mp_real(monkeypatch, disposable_pg, setup, "x_t", types, _gspec(allowed=al))
    assert _cv(got) == PASS
    assert [a["column"] for a in got[BR]["null_convention"]["convention"]["allowed_literals_in_force"]] == ["doc"]            # a json exemption takes effect, so it is in force


ARR_TYPES = {"k": "text", "ia": "ARRAY", "ba": "ARRAY", "na": "ARRAY", "ta": "ARRAY", "w": "integer"}


def _arr_setup(ia, ba, na, ta):
    return ["CREATE TEMP TABLE x_t (k text PRIMARY KEY, ia int[], ba boolean[], na numeric[], ta text[], w int NOT NULL) ON COMMIT DROP;",
            f"INSERT INTO x_t VALUES ('a', ARRAY[1,2], ARRAY[true,false], ARRAY[1.5,2], ARRAY['t1','t2'], 1), ('b', {ia}, {ba}, {na}, {ta}, 2), "
            "('c', ARRAY[3], ARRAY[true], ARRAY[3.5], ARRAY['t3'], 3);"]


@pytest.mark.parametrize("ia, ba, na, ta, fails", [
    ("ARRAY[0,5]", "ARRAY[false]", "ARRAY[0.0,2]", "ARRAY['t1']", False),                 # NON-nullable numeric/bool arrays: a 0 / false element is a real value
    ("ARRAY[]::int[]", "ARRAY[true]", "ARRAY[1]", "ARRAY['t1']", True),                     # an empty array stands in for absent
    ("ARRAY[1]", "ARRAY[]::boolean[]", "ARRAY[1]", "ARRAY['t1']", True),
    ("ARRAY[1]", "ARRAY[true]", "ARRAY[]::numeric[]", "ARRAY['t1']", True),
    ("ARRAY[1]", "ARRAY[true]", "ARRAY[1]", "ARRAY[]::text[]", True),
    ("ARRAY[1]", "ARRAY[true]", "ARRAY[1]", "ARRAY['t1','N/A']", True),                     # a text element that lacks
    ("ARRAY[1]", "ARRAY[true]", "ARRAY[1]", "ARRAY['ＮＯＮＥ']", True),
])
def test_REAL_SQL_LOW3_arrays_are_element_wise_consistent(monkeypatch, disposable_pg, ia, ba, na, ta, fails):
    r = _mp_real(monkeypatch, disposable_pg, _arr_setup(ia, ba, na, ta), "x_t", ARR_TYPES, _gspec())
    assert (_cv(r) == FAIL) is fails, r[BR]


def test_REAL_SQL_LOW3_a_zero_element_is_a_sentinel_only_in_a_declared_nullable_numeric_array(monkeypatch, disposable_pg):
    setup = _arr_setup("ARRAY[0,5]", "ARRAY[false]", "ARRAY[0.0,2]", "ARRAY['t1']")
    plain = _mp_real(monkeypatch, disposable_pg, setup, "x_t", ARR_TYPES, _gspec())
    assert _cv(plain) == PASS
    nul = _mp_real(monkeypatch, disposable_pg, setup, "x_t", ARR_TYPES, _gspec([_nul("ia", ["a"]), _nul("na", ["a"])]))
    assert _cv(nul) == FAIL and set(nul[BR]["null_convention"]["convention"]["fallbacks"]) == {"ia", "na"}                # int[] 0 and numeric[] 0.0 == 0
    boolnul = _mp_real(monkeypatch, disposable_pg, setup, "x_t", ARR_TYPES, _gspec([_nul("ba", ["a"])]))
    assert "ba" not in boolnul[BR]["null_convention"]["convention"]["fallbacks"]                                                                                        # false is never a sentinel


def test_REAL_SQL_LOW3_allowed_literals_compare_per_array_element(monkeypatch, disposable_pg):
    setup = _arr_setup("ARRAY[1]", "ARRAY[true]", "ARRAY[1]", "ARRAY['none','t9']")
    assert _cv(_mp_real(monkeypatch, disposable_pg, setup, "x_t", ARR_TYPES, _gspec())) == FAIL
    al = [dict(column="ta", values=["none"], why="an element with no tag is stored as the word none")]
    assert _cv(_mp_real(monkeypatch, disposable_pg, setup, "x_t", ARR_TYPES, _gspec(allowed=al))) == PASS
    setup2 = _arr_setup("ARRAY[1]", "ARRAY[true]", "ARRAY[1]", "ARRAY['none','N/A']")
    assert _cv(_mp_real(monkeypatch, disposable_pg, setup2, "x_t", ARR_TYPES, _gspec(allowed=al))) == FAIL            # only the declared element is exempt


def test_LOW4_the_exemptions_in_force_are_named_in_the_pass_text_and_the_block():
    al = [dict(column="direction", values=["none", "N/A"], why="a graha with no direction stores these words")]
    spec = _rspec(allowed_literals=al)
    r = ac.grade_null_convention(spec, LATTA_COLS, LATTA_TYPES, STATS())
    assert r["v"] == PASS
    assert r["convention"]["allowed_literals_in_force"] == [dict(column="direction", values=["none", "N/A"], why="a graha with no direction stores these words")]
    assert "allowed literals in force" in r["measured"] and "direction" in r["measured"] and "a graha with no direction stores these words" in r["measured"]
    assert "allowed literals in force" not in ac.grade_null_convention(SPEC(), LATTA_COLS, LATTA_TYPES, STATS())["measured"]


def test_LOW6_a_numeric_array_column_is_not_distinct_counted_and_is_named_not_examined(monkeypatch):
    types = {"k": "text", "emb": "ARRAY", "w": "integer"}
    got = _capture(monkeypatch, "{}", {"k": "text", "emb": "double precision[]", "w": "integer"})
    spec = dict(table="t", nullable=[], constants=[], why=SPEC()["why"], evidence=EV)
    try:
        ac.null_convention_fetch("t", ["k", "emb", "w"], types, spec, "")
    except ac.Unknown:
        pass
    assert 'count(DISTINCT "emb"' not in got[0] and 'count(DISTINCT "k"::text)' in got[0] and 'count(DISTINCT "w")' in got[0]
    st = dict(rows=3, kinds={"k": "text", "emb": "array_num", "w": "num"},
              cols={"k": dict(nulls=0, distinct=3, fallback=0), "emb": dict(nulls=0, distinct=None, fallback=0), "w": dict(nulls=0, distinct=3)})
    r = ac.grade_null_convention(spec, ["k", "emb", "w"], types, st)
    assert r["v"] == PASS and r["convention"]["constants_not_examined"] == ["emb"] and "emb (array_num)" in r["measured"]
    assert "emb" in r["convention"]["fallback_checked_columns"]                                                           # an empty embedding is still a fallback
    bad = copy.deepcopy(st)
    bad["cols"]["emb"]["distinct"] = 3                                                                                    # a skipped kind that reports a count is malformed
    with pytest.raises(ac.Unknown):
        ac.grade_null_convention(spec, ["k", "emb", "w"], types, bad)


def test_REAL_SQL_LOW6_float_array_embeddings_pass_without_a_distinct_count(monkeypatch, disposable_pg):
    setup = ["CREATE TEMP TABLE x_t (k text PRIMARY KEY, emb float8[] NOT NULL, w int NOT NULL) ON COMMIT DROP;",
             "INSERT INTO x_t VALUES ('a', ARRAY[0.1,0.2], 1), ('b', ARRAY[0.1,0.2], 2);"]                              # two identical embeddings: would read as an undeclared constant if counted
    r = _mp_real(monkeypatch, disposable_pg, setup, "x_t", {"k": "text", "emb": "ARRAY", "w": "integer"}, _gspec())
    assert _cv(r) == PASS
    assert "emb (array_num)" in r[BR]["null_convention"]["measured"]


def test_the_sample_key_list_is_capped_at_five_while_the_count_is_not(monkeypatch, disposable_pg):
    setup = ["CREATE TEMP TABLE x_t (k text PRIMARY KEY, n text, w int NOT NULL) ON COMMIT DROP;",
             "INSERT INTO x_t SELECT 'k' || lpad(g::text, 2, '0'), NULL, g FROM generate_series(1, 12) g;"]
    s3._real(monkeypatch, disposable_pg, setup)
    spec = dict(table="x_t", nullable=[dict(column="n", means="the source gives no value for these rows at all", scope=dict(key_column="k", null_for=["zz"], mode="exactly"))],
                constants=[], why=SPEC()["why"], evidence=EV)
    st = ac.null_convention_fetch("x_t", ["k", "n", "w"], {"k": "text", "n": "text", "w": "integer"}, spec, "")
    n = st["cols"]["n"]
    assert n["null_outside"] == 12 and n["null_outside_keys"] == ["k01", "k02", "k03", "k04", "k05"]


def test_the_grader_failure_inside_the_convention_path_ends_capped_with_no_pass(monkeypatch):
    """The `except (Unknown, DeclarationsError)` around the two graders in _measure_null_convention: a grader that cannot read leaves the base records, annotated."""
    base = _prose(monkeypatch, dict(prose_fields=None))
    for exc in (ac.Unknown("x"), ac.DeclarationsError("y")):
        def boom(*a, **k):
            raise exc
        monkeypatch.setattr(ac, "grade_null_schema_default_tables", boom)
        m = _prose(monkeypatch, dict(null_convention=SPEC(), prose_fields=None))
        assert m[SD]["v"] != PASS and m[BR]["v"] != PASS and m[SD]["null_convention"]["verified"] is False
        assert _bare(m[SD]) == base[SD] and _bare(m[BR]) == base[BR]
        assert m[SD]["null_convention"]["v"] == PASS                  # the INNER catch keeps the detector's own verdict (the outer one in _measure_prose would say ERRORED)
        monkeypatch.undo()


def test_stray_fallback_stats_on_a_column_that_cannot_hold_one_are_ignored():
    st = STATS(created_at=dict(fallback=3), count_from_graha=dict(fallback=2))                 # a timestamp and a non-nullable smallint: no fallback test applies
    r = _grade(stats=st)
    assert r["v"] == PASS and r["convention"]["fallbacks"] == {}


def test_REAL_SQL_the_catalog_kinds_read_refuses_what_the_catalog_does_not_answer(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, ["CREATE TEMP TABLE kk_t (a text, b int) ON COMMIT DROP;"])
    assert ac.null_fetch_column_kinds("kk_t", ["a", "b"]) == {"a": "text", "b": "num"}
    for table, cols in (("no_such_t", ["a"]), ("kk_t", ["a", "no_such_col"])):
        with pytest.raises(ac.Unknown):
            ac.null_fetch_column_kinds(table, cols)
    for bad in ("t;DROP", 'a"b', "", None):
        with pytest.raises(ac.Unknown):
            ac.null_fetch_column_kinds(bad, ["a"])


def test_the_kinds_the_fetch_resolved_beat_the_data_type_strings():
    types = dict(LATTA_TYPES, effect_description="USER-DEFINED")                                 # as information_schema reports an enum / citext
    st = STATS()
    st["kinds"] = {c: ac._null_type_kind(LATTA_TYPES[c]) for c in LATTA_COLS}                   # the catalog says effect_description is text
    assert ac.grade_null_convention(SPEC(), LATTA_COLS, types, st)["convention"]["fallback_checked_columns"].count("effect_description") == 1
    st2 = STATS()                                                                                  # no resolved kinds: the string says blob, which is skipped and needs distinct None
    with pytest.raises(ac.Unknown):
        ac.grade_null_convention(SPEC(), LATTA_COLS, types, st2)


def test_REAL_SQL_a_domain_is_resolved_to_its_base_type(monkeypatch, disposable_pg):
    setup = ["CREATE DOMAIN jd AS jsonb;", "CREATE DOMAIN ta_d AS text[];", "CREATE DOMAIN bd AS bytea;",
             "CREATE TEMP TABLE dd_t (k text PRIMARY KEY, j jd, a ta_d, b bd) ON COMMIT DROP;"]
    s3._real(monkeypatch, disposable_pg, setup)
    assert ac.null_fetch_column_kinds("dd_t", ["k", "j", "a", "b"]) == {"k": "text", "j": "json", "a": "array_text", "b": "blob"}
    ins = ["INSERT INTO dd_t VALUES ('a', '{\"s\":\"fine\"}', ARRAY['x'], '\\x01'), ('b', '{\"s\":\"N/A\"}', ARRAY['y'], '\\x02');"]
    r = _mp_real(monkeypatch, disposable_pg, setup + ins, "dd_t", {"k": "text", "j": "jsonb", "a": "ARRAY", "b": "bytea"}, _gspec())
    assert _cv(r) == FAIL and r[BR]["null_convention"]["convention"]["fallbacks"] == {"j": 1}               # the nested leaf of a jsonb DOMAIN


# ═════════════════ strategist round: the PASS text claims exactly what was checked ═════════════════

def _elem_setup(ja):
    return ["CREATE TEMP TABLE x_t (k text PRIMARY KEY, label text NOT NULL, ja jsonb[], ia inet[], w int NOT NULL) ON COMMIT DROP;",
            f"INSERT INTO x_t VALUES ('a', 'first', ARRAY['{{\"a\":\"ok\"}}'::jsonb], ARRAY['10.0.0.1'::inet], 1), ('b', 'second', {ja}, ARRAY['10.0.0.2'::inet], 2);"]


ELEM_TYPES = {"k": "text", "label": "text", "ja": "ARRAY", "ia": "ARRAY", "w": "integer"}


def test_REAL_SQL_an_array_whose_elements_are_not_inspected_passes_but_is_listed_as_not_examined(monkeypatch, disposable_pg):
    ja = "ARRAY['{\"a\":\"N/A\"}'::jsonb]"                                  # a placeholder INSIDE a jsonb[] element: not inspected, so it still passes ...
    r = _mp_real(monkeypatch, disposable_pg, _elem_setup(ja), "x_t", ELEM_TYPES, _gspec())
    conv, text = r[BR]["null_convention"]["convention"], r[BR]["null_convention"]["measured"]
    assert _cv(r) == PASS
    assert ac.null_fetch_column_kinds("x_t", ["ja", "ia", "label"]) == {"ja": "array_other", "ia": "array_other", "label": "text"}
    assert set(conv["elements_not_inspected"]) == {"ja", "ia"}                                  # ... but it is LISTED, and absent from the checked list
    assert set(conv["fallback_checked_columns"]) == {"k", "label"} and "ja" not in conv["fallback_checked_columns"]
    assert "NOT examined (element contents not inspected; only an empty array is a fallback): " in text and "ja (ARRAY)" in text and "ia (ARRAY)" in text
    chk = re.search(r"no literal fallback in the (\d+) text-like / declared-nullable column\(s\) checked \(([^)]*)\)", text)
    assert chk and int(chk.group(1)) == 2 == len(chk.group(2).split(", ")) and set(chk.group(2).split(", ")) == {"k", "label"}          # the count matches the list: 2, not 4


def test_REAL_SQL_an_empty_array_of_an_uninspected_kind_is_still_a_fallback(monkeypatch, disposable_pg):
    for ja in ("ARRAY[]::jsonb[]", "'{}'::jsonb[]"):
        r = _mp_real(monkeypatch, disposable_pg, _elem_setup(ja), "x_t", ELEM_TYPES, _gspec())
        assert _cv(r) == FAIL and r[BR]["null_convention"]["convention"]["fallbacks"] == {"ja": 1}, r[BR]


def test_the_pass_text_counts_match_the_lists_for_every_kind():
    types = {"k": "text", "ja": "ARRAY", "flag": "boolean", "n": "integer", "ta": "ARRAY", "w": "integer"}
    kinds = {"k": "text", "ja": "array_other", "flag": "bool", "n": "num", "ta": "array_text", "w": "num"}
    per = {c: dict(nulls=0, distinct=3, fallback=0) for c in types}
    for c in ("flag", "n", "w"):
        per[c].pop("fallback")
    r = ac.grade_null_convention(dict(table="t", nullable=[], constants=[], why=SPEC()["why"], evidence=EV), list(types), types, dict(rows=3, kinds=kinds, cols=per))
    conv = r["convention"]
    assert r["v"] == PASS and conv["fallback_checked_columns"] == ["k", "ta"] and conv["elements_not_inspected"] == ["ja"] and conv["fallback_not_applicable"] == ["flag", "n", "w"]
    assert "in the 2 text-like / declared-nullable column(s) checked (k, ta)" in r["measured"]
    assert len(conv["fallback_checked_columns"]) + len(conv["elements_not_inspected"]) + len(conv["fallback_not_applicable"]) == len(types)      # every column is accounted for exactly once


def test_an_allowed_literal_with_no_effect_on_the_column_type_is_not_printed_as_in_force():
    types = dict(LATTA_TYPES, flag="boolean", nums="ARRAY")
    cols = LATTA_COLS + ["flag", "nums"]
    kinds = {c: ac._null_type_kind(types[c]) for c in cols}
    kinds["nums"] = "array_num"
    st = STATS()
    st["cols"]["flag"] = dict(nulls=0, distinct=2)
    st["cols"]["nums"] = dict(nulls=0, distinct=None, fallback=0)
    st["kinds"] = kinds
    al = [dict(column="direction", values=["none"], why="a graha with no direction stores the word none"),
          dict(column="flag", values=["N/A"], why="a flag never holds a placeholder word at all"),
          dict(column="nums", values=["0"], why="a numeric array element is never a placeholder word")]
    r = ac.grade_null_convention(_rspec(allowed_literals=al), cols, types, st)
    conv = r["convention"]
    assert r["v"] == PASS and [a["column"] for a in conv["allowed_literals_in_force"]] == ["direction"] and conv["allowed_literals_no_effect"] == ["flag", "nums"]
    assert "allowed literals in force (declared exemptions): direction" in r["measured"] and "flag [" not in r["measured"].split("allowed literals in force")[1].split("; NOT")[0]
    assert "allowed_literals with no effect on the column type (not in force): flag, nums" in r["measured"]
