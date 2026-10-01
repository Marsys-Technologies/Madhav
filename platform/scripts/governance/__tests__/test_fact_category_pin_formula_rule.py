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


# ---------------------------------------------------------------- bundled fixtures + live tree
def test_bundled_self_test_passes():
    assert lint.run_self_test() == 0


def test_live_tree_has_no_non_allowlisted_violation():
    violations = lint.scan_repo(REPO, lint.DEFAULT_PY_GLOBS, lint.DEFAULT_TS_GLOBS)
    _allowed, new = lint.partition_allowlisted(violations, lint.load_allowlist(lint.ALLOWLIST_PATH))
    assert new == [], [(v.file, v.line, v.kind) for v in new]


# ---------------------------------------------------------------- reader contract
READERS = lint.load_reader_contract()


def test_reader_list_names_the_four_serving_readers():
    files = {r["file"].rsplit("/", 1)[-1] for r in READERS}
    assert files == {"register_d7_channel.ts", "get_karakas.ts", "get_sensitive_points.ts", "address_resolver.ts"}


def test_all_listed_readers_satisfy_the_contract_today():
    assert lint.check_reader_contract(REPO, READERS) == []


def _contract_on(tmp_path, readers_text_by_rel):
    for rel, text in readers_text_by_rel.items():
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    return lint.check_reader_contract(tmp_path, [{"file": r, "why": "t"} for r in readers_text_by_rel])


GOOD_READER = (
    "import { canonicalFirstOrderSql } from './canonical_formulas'\n"
    "let sql = `SELECT fact_id, formula_id FROM chart_facts WHERE chart_id = $1`\n"
    "sql += ` ORDER BY fact_subject, ${canonicalFirstOrderSql()}, formula_id, fact_id`\n"
)


def test_split_assembly_select_then_order_by_is_accepted(tmp_path):
    assert _contract_on(tmp_path, {"r.ts": GOOD_READER}) == []


def test_missing_listed_file_is_a_violation(tmp_path):
    out = lint.check_reader_contract(tmp_path, [{"file": "nope.ts", "why": "t"}])
    assert [v.kind for v in out] == ["reader_contract"]


# ---------------------------------------------------------------- mutants: the guard must FAIL
def test_mutant_reader_stops_referencing_canonical_formulas(tmp_path):
    out = _contract_on(tmp_path, {"r.ts": GOOD_READER.replace("canonical_formulas", "something_else")})
    assert any("canonical_formulas" in v.message for v in out)


def test_mutant_reader_hides_formula_id_from_its_select(tmp_path):
    out = _contract_on(tmp_path, {"r.ts": GOOD_READER.replace("SELECT fact_id, formula_id FROM", "SELECT fact_id FROM")})
    assert any("formula_id" in v.message for v in out)


def test_mutant_reader_drops_formula_id_from_its_order_by(tmp_path):
    out = _contract_on(tmp_path, {"r.ts": GOOD_READER.replace(", formula_id, fact_id`", ", fact_id`")})
    assert any("formula_id" in v.message for v in out)


@pytest.mark.parametrize("rel,needle,repl", [
    ("platform/src/lib/retrieval/registry/layers/L1_ganita/get_karakas.ts", "unit, formula_id, verification_pass_status", "unit, verification_pass_status"),
    ("platform/src/lib/retrieval/registry/layers/L1_ganita/get_karakas.ts", ", formula_id, fact_id\n", ", fact_id\n"),
    ("platform/src/lib/retrieval/registry/layers/L1_ganita/get_sensitive_points.ts", "unit, formula_id, formula_provenance_text", "unit, formula_provenance_text"),
    ("platform/src/lib/retrieval/registry/layers/L1_ganita/get_sensitive_points.ts", "formula_id, fact_id LIMIT $3", "fact_id LIMIT $3"),
    ("platform/src/lib/retrieval/registry/layers/register_d7_channel.ts", "unit, formula_id, verification_pass_status", "unit, verification_pass_status"),
    ("platform/src/lib/retrieval/registry/layers/register_d7_channel.ts", ", formula_id, fact_id LIMIT", ", fact_id LIMIT"),
])
def test_mutants_of_the_real_readers_are_caught(tmp_path, rel, needle, repl):
    """Mutate a COPY of each real reader; the contract check must go red."""
    text = (REPO / rel).read_text(encoding="utf-8")
    assert needle in text, f"mutation anchor vanished from {rel}: {needle!r}"
    out = _contract_on(tmp_path, {rel: text.replace(needle, repl)})
    assert out, f"mutant of {rel} ({needle!r}) was NOT caught"


def test_mutant_address_resolver_loses_its_formula_pin_AND_formula_ordering(tmp_path):
    """The pin and the ordered disclosure are alternatives, so dropping only one leaves a rule-valid
    reader (the JS partitions by formula either way). Dropping both must be caught."""
    rel = "platform/src/lib/retrieval/address_resolver.ts"
    text = (REPO / rel).read_text(encoding="utf-8")
    pin, order = "AND formula_id = ANY($4::text[])", "ORDER BY fact_key, formula_id, fact_id"
    assert pin in text and order in text
    assert lint.check_reader_contract(REPO, [{"file": rel, "why": "t"}]) == []
    out = _contract_on(tmp_path, {rel: text.replace(pin, "AND fact_subject = $3").replace(order, "ORDER BY fact_key, fact_id")})
    assert out


def test_backticks_in_comments_do_not_misalign_template_literals():
    """A prose comment quoting `formula_id` must not pair with a real template literal's backtick and
    hide the SQL from the scanner (this masked a real mutant of get_karakas.ts before comments were
    stripped)."""
    src = (
        "// the page now also serves `formula_id` for each row\n"
        "const q = `SELECT fact_value_text FROM chart_facts WHERE fact_category = 'karaka_chara_position' AND fact_key = 'k'`\n"
    )
    assert ts(src), "unpinned declared-category SQL after a backtick comment must still be flagged"
    assert ts(src.replace("//", "/*", 1).replace("row\n", "row */\n", 1))


def test_mutant_declaration_loses_a_category_and_the_fixture_goes_unflagged():
    """If a category silently left the declaration the rule would stop protecting it; the parity and
    declaration tests above pin the list, and this shows the scanner honours exactly what it is given."""
    sql = "`SELECT fact_value_text FROM chart_facts WHERE fact_category = 'esoteric_point_mrityu' AND fact_key = 'k'`"
    assert lint.scan_ts_formula_text(sql, ["esoteric_point_mrityu"])
    assert lint.scan_ts_formula_text(sql, ["esoteric_point_yogi"]) == []


def test_reader_list_file_shape_is_validated(tmp_path):
    bad = tmp_path / "r.json"
    bad.write_text(json.dumps({"readers": [{"file": "a.ts"}]}))
    with pytest.raises(RuntimeError):
        lint.load_reader_contract(bad)
