"""test_fact_category_pin_formula_rule.py -- the multi-formula extension of check_fact_category_pinning.py
(the permanent guard of INVESTIGATION_L1_DUPLICATE_KEYS_v1_0.md; SS decision 2026-10-01).

The rule: a SELECT FROM chart_facts that names a declared multi-formula category (declared ONCE, in
platform/python-sidecar/brahmagyan/canonical_formulas.py, loaded by path) must pin formula_id or
disclose all variants (formula_id selected AND ordered by). Plus the structural reader contract for
dynamic-category readers (multi_formula_readers.json). These tests drive the real scanner functions;
the mutants at the bottom prove the guard fails when the property is removed.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_fact_category_pin_formula_rule.py -q
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import check_fact_category_pinning as lint  # noqa: E402

REPO = lint.REPO_ROOT
CATS = lint.load_multi_formula_categories()

UNPINNED_PY = '''
cur.execute("""SELECT fact_value_num FROM chart_facts
   WHERE chart_id=%s AND fact_category='esoteric_point_yogi' AND fact_key='longitude_sidereal'""", [c])
'''
PINNED_PY = UNPINNED_PY.replace("AND fact_key='longitude_sidereal'", "AND fact_key='longitude_sidereal' AND formula_id='bphs_93_20'")
IN_PINNED_PY = UNPINNED_PY.replace("AND fact_key='longitude_sidereal'", "AND fact_key='longitude_sidereal' AND formula_id IN ('bphs_93_20')")
ANY_PINNED_PY = UNPINNED_PY.replace("AND fact_key='longitude_sidereal'", "AND fact_key='longitude_sidereal' AND formula_id = ANY(%s)")

DISCLOSED_TS = (
    "const q = `SELECT fact_id, fact_subject, fact_value_text, formula_id FROM chart_facts "
    "WHERE chart_id = $1 AND fact_category = 'karaka_chara_position' AND fact_key = 'assigned_graha' "
    "ORDER BY fact_subject, formula_id, fact_id`"
)


def py(text):
    return lint.scan_python_formula_text(text, CATS)


def ts(text):
    return lint.scan_ts_formula_text(text, CATS)


# ---------------------------------------------------------------- the declaration the lint reads
def test_lint_reads_the_seven_declared_categories_from_the_one_declaration():
    assert CATS == [
        "karaka_chara_position", "esoteric_point_yogi", "esoteric_point_avayogi",
        "esoteric_point_brahma", "esoteric_point_shiva", "esoteric_point_vishnu", "esoteric_point_mrityu",
    ]


def test_an_unreadable_declaration_fails_loudly_never_degrades_to_nothing_declared(tmp_path):
    with pytest.raises(RuntimeError):
        lint.load_multi_formula_categories(tmp_path / "missing.py")
    empty = tmp_path / "empty.py"
    empty.write_text("CANONICAL_FORMULAS = {}\n")
    with pytest.raises(RuntimeError):
        lint.load_multi_formula_categories(empty)


# ---------------------------------------------------------------- flags / passes
def test_flags_declared_category_with_fact_key_but_no_formula_pin():
    assert py(UNPINNED_PY), "category + fact_key without a formula pin must be flagged"


@pytest.mark.parametrize("text", [PINNED_PY, IN_PINNED_PY, ANY_PINNED_PY])
def test_a_formula_pin_passes(text):
    assert py(text) == []


def test_all_variants_disclosure_passes():
    assert ts(DISCLOSED_TS) == []


def test_formula_id_only_in_an_order_by_case_is_not_a_pin():
    sql = (
        "`SELECT fact_subject FROM chart_facts WHERE fact_category = 'esoteric_point_mrityu' AND fact_key = 'x' "
        "ORDER BY CASE WHEN formula_id = 'bphs_ch39' THEN 0 ELSE 1 END, fact_id`"
    )
    assert ts(sql), "a canonical-first CASE in ORDER BY neither pins nor discloses"


def test_selected_but_not_ordered_is_a_half_disclosure():
    sql = "`SELECT fact_subject, formula_id FROM chart_facts WHERE fact_category = 'karaka_chara_position' ORDER BY fact_subject`"
    assert ts(sql)


def test_ordered_but_not_selected_is_flagged_the_rows_cannot_be_labelled():
    sql = "`SELECT fact_subject FROM chart_facts WHERE fact_category = 'karaka_chara_position' ORDER BY fact_subject, formula_id`"
    assert ts(sql)


def test_select_star_counts_as_selecting_formula_id():
    sql = "`SELECT * FROM chart_facts WHERE fact_category = 'karaka_chara_position' ORDER BY fact_subject, formula_id, fact_id`"
    assert ts(sql) == []


def test_undeclared_category_needs_no_formula_pin():
    assert ts("`SELECT fact_value_text FROM chart_facts WHERE fact_category = 'graha_position' AND fact_key = 'sign'`") == []


def test_zero_row_probe_and_aggregate_count_are_exempt():
    probe = "`SELECT fact_id FROM chart_facts WHERE fact_category = ANY(ARRAY['karaka_chara_position']::text[]) ORDER BY fact_id LIMIT 0`"
    count = "`SELECT COUNT(*)::int AS n FROM chart_facts WHERE fact_category = 'esoteric_point_mrityu'`"
    assert ts(probe) == [] and ts(count) == []


def test_non_select_statements_are_out_of_scope():
    assert py('cur.execute("DELETE FROM chart_facts WHERE fact_category = \'esoteric_point_yogi\'")') == []


def test_every_declared_category_is_checked_not_only_the_first():
    for cat in CATS:
        sql = f"`SELECT fact_value_text FROM chart_facts WHERE fact_category = '{cat}' AND fact_key = 'k'`"
        assert ts(sql), cat


# ---------------------------------------------------------------- false-negative closures (PR #2866 review)
def test_formula_id_is_not_null_is_not_a_pin():
    for tail in ("AND formula_id IS NOT NULL", "AND formula_id IS NULL", "AND formula_id <> 'alt_96_40'",
                 "AND formula_id != 'alt_96_40'", "AND formula_id NOT IN ('alt_96_40')"):
        sql = f"`SELECT fact_value_num FROM chart_facts WHERE fact_category = 'esoteric_point_yogi' AND fact_key = 'k' {tail}`"
        assert ts(sql), f"{tail!r} must not count as a formula pin"


def test_the_word_formula_id_anywhere_in_the_where_is_not_enough():
    for tail in ("AND formula_id IS NOT NULL", "AND fact_id <> formula_id", "AND length(formula_id) > 3"):
        sql = f"`SELECT fact_value_num FROM chart_facts WHERE fact_category = 'esoteric_point_yogi' AND fact_key = 'k' {tail}`"
        assert ts(sql), tail


def test_a_pin_inside_a_subselect_does_not_pin_the_outer_statement():
    sql = (
        "`SELECT fact_value_num FROM chart_facts WHERE fact_category = 'esoteric_point_yogi' AND fact_key = 'k' "
        "AND fact_subject IN (SELECT fact_subject FROM chart_facts WHERE formula_id = 'bphs_93_20')`"
    )
    assert ts(sql), "the outer read is unpinned; the subselect's formula_id = ... is not its WHERE"


def test_a_pinned_outer_statement_is_not_failed_by_an_unrelated_subselect():
    sql = (
        "`SELECT fact_value_num FROM chart_facts WHERE fact_category = 'esoteric_point_yogi' AND fact_key = 'k' "
        "AND formula_id = 'bphs_93_20' AND fact_subject IN (SELECT fact_subject FROM chart_facts WHERE fact_key = 'sign')`"
    )
    assert ts(sql) == []


def test_a_nested_subselect_that_itself_reads_a_declared_category_unpinned_is_flagged():
    sql = (
        "`SELECT fact_value_num FROM chart_facts WHERE fact_category = 'graha_position' AND formula_id = 'x' "
        "AND fact_subject IN (SELECT fact_subject FROM chart_facts WHERE fact_category = 'esoteric_point_yogi' AND fact_key = 'k')`"
    )
    assert ts(sql)


UNION_MASKED = (
    "`SELECT fact_value_num FROM chart_facts WHERE fact_category = 'esoteric_point_yogi' AND fact_key = 'k' "
    "UNION ALL SELECT fact_value_num FROM chart_facts WHERE fact_category = 'esoteric_point_avayogi' AND formula_id = 'bphs_93_20'`"
)


def test_a_pinned_union_branch_cannot_mask_an_unpinned_one():
    assert ts(UNION_MASKED)
    assert ts(UNION_MASKED.replace("UNION ALL", "UNION"))
    assert ts(UNION_MASKED.replace("UNION ALL", "INTERSECT"))


def test_every_union_branch_pinned_passes():
    both = UNION_MASKED.replace("AND fact_key = 'k' UNION", "AND fact_key = 'k' AND formula_id = 'bphs_93_20' UNION")
    assert ts(both) == []


def test_a_trailing_union_order_by_governs_every_branch_for_disclosure():
    sql = (
        "`SELECT fact_id, formula_id FROM chart_facts WHERE fact_category = 'esoteric_point_yogi' "
        "UNION ALL SELECT fact_id, formula_id FROM chart_facts WHERE fact_category = 'esoteric_point_avayogi' "
        "ORDER BY formula_id, fact_id`"
    )
    assert ts(sql) == []


@pytest.mark.parametrize("frm", ["FROM public.chart_facts", "JOIN chart_facts cf ON cf.fact_id = x.fact_id", "FROM \"chart_facts\""])
def test_join_and_schema_qualified_chart_facts_are_scanned(frm):
    sql = f"`SELECT cf.fact_value_num FROM other x {frm} WHERE cf.fact_category = 'esoteric_point_yogi' AND cf.fact_key = 'k'`"
    if frm.startswith("FROM public") or frm.startswith('FROM "'):
        sql = f"`SELECT fact_value_num {frm} WHERE fact_category = 'esoteric_point_yogi' AND fact_key = 'k'`"
    assert ts(sql), frm


def test_schema_qualified_pinned_read_passes():
    assert ts("`SELECT fact_value_num FROM public.chart_facts WHERE fact_category = 'esoteric_point_yogi' AND formula_id = 'bphs_93_20'`") == []


@pytest.mark.parametrize("pred", ["fact_category LIKE 'esoteric_point_%'", "fact_category ILIKE 'karaka_chara%'",
                                  "fact_category ~ '^esoteric_point_'"])
def test_a_like_or_regex_prefix_naming_declared_categories_is_flagged(pred):
    assert ts(f"`SELECT fact_value_num FROM chart_facts WHERE {pred} AND fact_key = 'k'`"), pred


def test_a_like_prefix_matching_no_declared_category_is_ignored():
    assert ts("`SELECT fact_value_num FROM chart_facts WHERE fact_category LIKE 'panchanga_%' AND fact_key = 'k'`") == []


def test_single_and_double_quoted_ts_sql_strings_are_scanned():
    unpinned = "SELECT fact_value_num FROM chart_facts WHERE fact_category = 'esoteric_point_yogi' AND fact_key = 'k'"
    assert ts(f'const q = "{unpinned}"')
    assert ts("const q = 'SELECT fact_value_num FROM chart_facts WHERE fact_category = ANY(\\'x\\') AND fact_category = \\'esoteric_point_yogi\\''")


def test_a_comment_marker_inside_a_string_cannot_blank_the_sql_after_it():
    src = (
        "const hint = 'use /* here'\n"
        "const q = `SELECT fact_value_text FROM chart_facts WHERE fact_category = 'karaka_chara_position' AND fact_key = 'k'`\n"
        "/* a real comment */\n"
    )
    assert ts(src), "the old comment blanker erased the q literal between the string's /* and the real */"


def test_a_url_in_a_string_is_not_a_comment():
    src = (
        "const u = 'https://example.org/x'\n"
        "const q = `SELECT fact_value_text FROM chart_facts WHERE fact_category = 'karaka_chara_position' AND fact_key = 'k'`\n"
    )
    assert ts(src)


def test_nested_template_expressions_are_scanned_as_code():
    src = "const q = `SELECT a FROM chart_facts WHERE fact_category = 'esoteric_point_yogi' ${ids ? `AND build_id = ANY($4)` : ''}`"
    assert ts(src)


# ---------------------------------------------------------------- bundled fixtures + live tree
def test_bundled_self_test_passes():
    assert lint.run_self_test() == 0


def test_live_tree_has_no_non_allowlisted_violation():
    violations = lint.scan_repo(REPO, lint.DEFAULT_PY_GLOBS, lint.DEFAULT_TS_GLOBS)
    _allowed, new = lint.partition_allowlisted(violations, lint.load_allowlist(lint.ALLOWLIST_PATH))
    assert new == [], [(v.file, v.line, v.kind) for v in new]


# ---------------------------------------------------------------- reader contract
CONTRACT = lint.load_reader_contract()
READERS = CONTRACT["readers"]
BY_FILE = {r["file"].rsplit("/", 1)[-1]: r for r in READERS}


def test_reader_list_names_the_four_serving_readers():
    assert set(BY_FILE) == {"register_d7_channel.ts", "get_karakas.ts", "get_sensitive_points.ts", "address_resolver.ts"}
    assert BY_FILE["address_resolver.ts"]["mode"] == "pin"
    for name in ("register_d7_channel.ts", "get_karakas.ts", "get_sensitive_points.ts"):
        assert BY_FILE[name]["mode"] == "disclose"
        assert {"canonicalFirstOrderSql", "fact_subject", "fact_id"} <= set(BY_FILE[name]["order_tokens"])


def test_all_listed_readers_satisfy_the_contract_today():
    assert lint.check_reader_contract(REPO, CONTRACT) == []


def test_known_open_readers_are_recorded_and_not_double_listed():
    known = {k["file"].rsplit("/", 1)[-1]: k for k in CONTRACT["known_open_readers"]}
    for name in ("get_strength.ts", "get_nakshatra.ts", "get_dispositors.ts", "get_avasthas.ts", "get_dignity.ts",
                 "get_panchanga.ts", "get_yoga_dosha.ts", "get_structural_signals.ts", "get_aspects.ts",
                 "get_bhava_bala.ts", "get_sade_sati.ts", "get_ashtakavarga.ts", "bo_laksana.py", "bo_upaya.py",
                 "209_ga5_sensitive_points_mv.sql", "207_ga3_materialized_views.sql", "get_database_schema.ts",
                 "facts_store.ts"):
        assert name in known, name
    assert not set(known) & set(BY_FILE)


def _entry(**kw):
    base = {"file": "r.ts", "why": "t", "mode": "disclose", "select_markers": ["fact_value_jsonb"],
            "order_tokens": ["canonicalFirstOrderSql", "fact_subject", "fact_id"]}
    base.update(kw)
    return base


def _contract_on(tmp_path, text_by_rel, entries=None):
    for rel, text in text_by_rel.items():
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    entries = entries or [_entry(file=r) for r in text_by_rel]
    return lint.check_reader_contract(tmp_path, {"readers": entries, "known_open_readers": []})


GOOD_READER = (
    "import { canonicalFirstOrderSql } from './canonical_formulas'\n"
    "let sql = `SELECT fact_id, fact_subject, fact_value_jsonb, formula_id FROM chart_facts WHERE chart_id = $1`\n"
    "sql += ` ORDER BY fact_subject, ${canonicalFirstOrderSql()}, formula_id, fact_id`\n"
)


def test_split_assembly_select_then_order_by_is_accepted(tmp_path):
    assert _contract_on(tmp_path, {"r.ts": GOOD_READER}) == []


def test_missing_listed_file_is_a_violation(tmp_path):
    out = lint.check_reader_contract(tmp_path, {"readers": [_entry(file="nope.ts")], "known_open_readers": []})
    assert [v.kind for v in out] == ["reader_contract"]


def test_a_marker_that_matches_nothing_is_a_violation_not_a_silent_pass(tmp_path):
    out = _contract_on(tmp_path, {"r.ts": GOOD_READER}, [_entry(select_markers=["not_in_the_file"])])
    assert any("marker" in v.message for v in out)


# ---------------------------------------------------------------- mutants: the guard must FAIL
def test_mutant_reader_stops_referencing_canonical_formulas(tmp_path):
    out = _contract_on(tmp_path, {"r.ts": GOOD_READER.replace("canonical_formulas", "something_else")})
    assert any("canonical_formulas" in v.message for v in out)


def test_mutant_reader_hides_formula_id_from_its_select(tmp_path):
    out = _contract_on(tmp_path, {"r.ts": GOOD_READER.replace("fact_value_jsonb, formula_id FROM", "fact_value_jsonb FROM")})
    assert any("formula_id" in v.message for v in out)


@pytest.mark.parametrize("old,new", [
    ("${canonicalFirstOrderSql()}, formula_id, fact_id", "formula_id, fact_id"),          # drops the canonical-first rank
    ("fact_subject, ${canonicalFirstOrderSql()}", "${canonicalFirstOrderSql()}"),         # drops the subject
    ("formula_id, fact_id`", "formula_id`"),                                              # drops the PK tiebreak
    ("${canonicalFirstOrderSql()}, formula_id, fact_id", "${canonicalFirstOrderSql()}, fact_id"),  # drops formula_id
])
def test_mutant_reader_weakens_its_order_by(tmp_path, old, new):
    assert old in GOOD_READER
    assert _contract_on(tmp_path, {"r.ts": GOOD_READER.replace(old, new)}), (old, new)


def test_mutant_pin_mode_reader_loses_only_its_pin(tmp_path):
    reader = (
        "import { x } from './canonical_formulas'\n"
        "const q = `SELECT fact_id, formula_id FROM chart_facts WHERE fact_category = 'karaka_chara_position' "
        "AND formula_id = ANY($4::text[]) ORDER BY fact_key, formula_id, fact_id`\n"
    )
    entry = _entry(mode="pin", select_markers=["fact_category = 'karaka_chara_position'"], order_tokens=["fact_key", "fact_id"])
    assert _contract_on(tmp_path, {"r.ts": reader}, [entry]) == []
    stripped = reader.replace("AND formula_id = ANY($4::text[]) ", "")  # still selects + orders by formula_id
    assert _contract_on(tmp_path, {"r.ts": stripped}, [entry]), "pin mode must not accept a disclosure"


def _real(rel_name):
    r = BY_FILE[rel_name]
    return r, (REPO / r["file"]).read_text(encoding="utf-8")


@pytest.mark.parametrize("name,needle,repl", [
    ("get_karakas.ts", "unit, formula_id, verification_pass_status", "unit, verification_pass_status"),
    ("get_karakas.ts", "${canonicalFirstOrderSql()}, formula_id, fact_id", "formula_id, fact_id"),
    ("get_karakas.ts", "fact_key, fact_subject, ${canonicalFirstOrderSql()}", "fact_key, ${canonicalFirstOrderSql()}"),
    ("get_karakas.ts", ", formula_id, fact_id\n", ", formula_id\n"),
    ("get_sensitive_points.ts", "unit, formula_id, formula_provenance_text", "unit, formula_provenance_text"),
    ("get_sensitive_points.ts", "fact_subject, ${canonicalFirstOrderSql()}, formula_id, fact_id LIMIT $3", "formula_id, fact_id LIMIT $3"),
    ("get_sensitive_points.ts", "${canonicalFirstOrderSql()}, formula_id, fact_id LIMIT $3", "formula_id, fact_id LIMIT $3"),
    ("get_sensitive_points.ts", "formula_id, fact_id LIMIT $3", "formula_id LIMIT $3"),
    ("register_d7_channel.ts", "unit, formula_id, verification_pass_status", "unit, verification_pass_status"),
    ("register_d7_channel.ts", ", ${canonicalFirstOrderSql()}, formula_id, fact_id LIMIT", ", formula_id, fact_id LIMIT"),
    ("register_d7_channel.ts", ", formula_id, fact_id LIMIT", ", formula_id LIMIT"),
    ("address_resolver.ts", "AND formula_id = ANY($4::text[])", "AND fact_subject = $3"),
    ("address_resolver.ts", "ORDER BY fact_key, formula_id, fact_id", "ORDER BY fact_key, formula_id"),
])
def test_mutants_of_the_real_readers_are_caught(tmp_path, name, needle, repl):
    """Mutate a COPY of each real reader; the contract check must go red (every one used to survive or
    be caught only by luck: the weak 'some qualifying select per file' rule let several through)."""
    entry, text = _real(name)
    assert needle in text, f"mutation anchor vanished from {entry['file']}: {needle!r}"
    out = _contract_on(tmp_path, {entry["file"]: text.replace(needle, repl)}, [entry])
    assert out, f"mutant of {entry['file']} ({needle!r}) was NOT caught"


def test_address_resolver_pin_only_removal_is_caught_even_though_disclosure_remains(tmp_path):
    entry, text = _real("address_resolver.ts")
    pin = "AND formula_id = ANY($4::text[])"
    assert lint.check_reader_contract(REPO, {"readers": [entry], "known_open_readers": []}) == []
    out = _contract_on(tmp_path, {entry["file"]: text.replace(pin, "AND fact_subject = $3")}, [entry])
    assert any("pin" in v.message for v in out)


def test_backticks_in_comments_do_not_misalign_template_literals():
    src = (
        "// the page now also serves `formula_id` for each row\n"
        "const q = `SELECT fact_value_text FROM chart_facts WHERE fact_category = 'karaka_chara_position' AND fact_key = 'k'`\n"
    )
    assert ts(src), "unpinned declared-category SQL after a backtick comment must still be flagged"
    assert ts(src.replace("//", "/*", 1).replace("row\n", "row */\n", 1))


def test_mutant_declaration_loses_a_category_and_the_fixture_goes_unflagged():
    sql = "`SELECT fact_value_text FROM chart_facts WHERE fact_category = 'esoteric_point_mrityu' AND fact_key = 'k'`"
    assert lint.scan_ts_formula_text(sql, ["esoteric_point_mrityu"])
    assert lint.scan_ts_formula_text(sql, ["esoteric_point_yogi"]) == []


def test_reader_list_file_shape_is_validated(tmp_path):
    for bad in (
        {"readers": [{"file": "a.ts"}]},
        {"readers": [{"file": "a.ts", "why": "t", "select_markers": ["x"]}]},
        {"readers": [{"file": "a.ts", "why": "t", "select_markers": ["x"], "order_tokens": ["y"], "mode": "weird"}]},
        {"readers": [_entry()], "known_open_readers": [{"file": "r.ts", "status": "OPEN", "why": "t"}]},
        {"readers": [_entry()], "known_open_readers": [{"file": "z.ts"}]},
    ):
        p = tmp_path / "r.json"
        p.write_text(json.dumps(bad))
        with pytest.raises(RuntimeError):
            lint.load_reader_contract(p)
