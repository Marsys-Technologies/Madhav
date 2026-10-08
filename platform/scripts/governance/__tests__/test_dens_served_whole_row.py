"""test_dens_served_whole_row.py — SS N-212 ruling E8: `to_jsonb(<alias>)` in a served select's list is the WHOLE ROW as jsonb, hence a tier column, under three conditions.

  1  the alias is the asset's OWN table in the SAME select (that select's `FROM|JOIN <table> <alias>`, or the bare table name): a different table's alias, a CTE / sub-select alias,
     or a `to_jsonb(..)` that sits inside a sub-select of the list is not credited;
  2  the table's columns are known and hold a tier column (`tier` / `verification_pass_status` / a declared one): columns unknown reads UNKNOWN, a table without the column reads NO;
  3  partial projections do not count: `row_to_json`, `to_json`, `jsonb_build_object(..)`, `to_jsonb(d) - 'col'`, `jsonb_agg(to_jsonb(d))`; neither does text inside a string literal or an SQL comment
     (a comma inside a line comment used to split a `to_jsonb(d)` item out of the commented text).

The form credits a select that OWNS the asset table's FROM and is a served read. A CTE body (`WITH page_rows AS (SELECT to_jsonb(d) AS row .. FROM t d ..)`) is not a served read by the existing
rule (`_is_served_read`), so bo_yantra_mechanism's query_mechanisms.ts still reads PARTIAL: the pinned test below states why (E9, open ruling).

Run:
  python -m pytest platform/scripts/governance/__tests__/test_dens_served_whole_row.py -v
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_1_dens_repair as dr  # noqa: E402

tree = dr.tree
_REAL_SCAN = dr._REAL_SCAN
COLS = ["mechanism_id", "mechanism_class", "valence", "verification_pass_status", "build_id"]
NO_TIER_COLS = ["mechanism_id", "mechanism_class", "valence", "build_id"]


def _sel(sel, alias="d", cols=COLS, table="t_mech", declared=()):
    return ac._select_tier(sel, alias, table, cols, declared)


# ───────────────────────────── the select-list reader ─────────────────────────────

@pytest.mark.parametrize("sel,alias", [
    ("to_jsonb(d) AS row, d.mechanism_class AS order_class ", "d"),
    ("to_jsonb(d)", "d"),
    ("to_jsonb(d)::jsonb AS row", "d"),
    ("to_jsonb( d ) AS row", "d"),
    ("to_jsonb(t_mech) AS row", None),                      # the bare table name, no alias
    ("to_jsonb(D)", "d"),
])
def test_the_whole_row_of_the_assets_own_alias_carries_the_tier_column(sel, alias):
    st, cs = _sel(sel, alias)
    assert st == ac.TIER_YES and cs == ["verification_pass_status"], (sel, st, cs)


def test_a_declared_tier_column_is_carried_by_the_whole_row_too():
    st, cs = _sel("to_jsonb(d)", cols=["id", "severity"], declared=["severity"])
    assert st == ac.TIER_YES and cs == ["severity"]


@pytest.mark.parametrize("name,sel,alias", [
    ("another table's alias", "to_jsonb(o) AS row", "d"),
    ("the alias of a CTE / sub-select", "to_jsonb(cte_rows) AS row", "d"),
    ("the asset table's name while it is aliased elsewhere", "to_jsonb(other) AS row", "d"),
])
def test_condition1_an_alias_that_is_not_the_assets_own_is_not_credited(name, sel, alias):
    assert _sel(sel, alias)[0] != ac.TIER_YES, name


def test_condition1_the_alias_must_be_this_selects_own_not_a_driving_tables():
    # `SELECT to_jsonb(d) FROM driver d JOIN t_mech m ...`: the handed-over list belongs to the select whose JOIN is the asset (alias m); d is the driver
    assert _sel("to_jsonb(d) AS row FROM driver d JOIN ", "m")[0] != ac.TIER_YES


def test_condition1_a_to_jsonb_inside_a_sub_select_of_the_list_is_not_credited():
    st, cs = _sel("(SELECT to_jsonb(d) FROM other d LIMIT 1) AS row, d.mechanism_id")
    assert st == ac.TIER_UNKNOWN and not cs


def test_condition2_a_table_without_the_tier_column_is_not_credited():
    st, cs = _sel("to_jsonb(d) AS row", cols=NO_TIER_COLS)
    assert st == ac.TIER_NO and not cs


def test_condition2_unknown_columns_never_read_as_a_tier_column():
    st, cs = _sel("to_jsonb(d) AS row", cols=None)
    assert st == ac.TIER_UNKNOWN and not cs


@pytest.mark.parametrize("name,sel", [
    ("row_to_json", "row_to_json(d) AS row"),
    ("to_json", "to_json(d) AS row"),
    ("jsonb_build_object (a partial projection)", "jsonb_build_object('id', d.mechanism_id, 'class', d.mechanism_class) AS row"),
    ("the tier key removed", "to_jsonb(d) - 'verification_pass_status' AS row"),
    ("a wrapper around the whole row", "jsonb_agg(to_jsonb(d)) AS rows"),
    ("a function of the whole row", "jsonb_strip_nulls(to_jsonb(d)) AS row"),
    ("a string literal", "'to_jsonb(d)' AS note, d.mechanism_id"),
    ("a block comment", "/* to_jsonb(d), */ d.mechanism_id"),
    ("a line comment", "d.mechanism_id -- to_jsonb(d)\n"),
    ("a comma inside a line comment (the split forgery)", "d.mechanism_id, -- note, to_jsonb(d)\n, d.valence"),
    ("a comma inside a line comment, item after the newline", "d.mechanism_id, -- note, to_jsonb(d)\n d.valence"),
    ("a comma inside a block comment", "d.mechanism_id, /* x,\n to_jsonb(d)\n */ d.valence"),
    ("an apostrophe in a comment hiding the item", "d.mechanism_id, -- don't\n d.valence, /* it's */ d.build_id"),
])
def test_condition3_partial_projections_wrappers_literals_and_comments_do_not_count(name, sel):
    assert _sel(sel)[0] != ac.TIER_YES, name


def test_condition3_sensitivity_without_the_comment_blanking_the_comma_forgery_would_read_yes(monkeypatch):
    """Sensitivity of the comment tests: with the pre-E8 literal-only blanking the commented text splits a `to_jsonb(d)` item out and the list would read YES."""
    import re
    forged = "d.mechanism_id, -- note, to_jsonb(d)\n, d.valence"
    assert _sel(forged)[0] != ac.TIER_YES
    monkeypatch.setattr(ac, "_SQL_LIT_COMMENT", re.compile(r"'[^']*'"))
    assert _sel(forged)[0] == ac.TIER_YES


def test_existing_readings_are_unchanged():
    assert _sel("d.verification_pass_status, d.mechanism_id")[0] == ac.TIER_YES
    assert _sel("d.mechanism_id, d.valence")[0] == ac.TIER_NO
    assert _sel("*", cols=COLS)[0] == ac.TIER_YES
    assert _sel("*", cols=None)[0] == ac.TIER_UNKNOWN
    assert _sel("d.* , 1", cols=COLS)[0] == ac.TIER_YES


# ───────────────────────────── through the scan, and the grade ─────────────────────────────

def _src(sql, *, contract="density_contract: { paginated: true, facets: [], empty_reason: true },"):
    return ("export const cap = {\n  id: 'bg_x',\n  " + contract + "\n  async handler(args) {\n    return query(`" + sql + "`, [args.chart_id])\n  },\n}\n")


def _grade(tree, sql, cols=COLS, **kw):
    tree.write(tree.layers / "L0_x", "q.ts", _src(sql, **kw))
    cap = _REAL_SCAN(tree.roots, ["t_mech", "bg_x"], shared=set(), columns={"t_mech": cols}, outside_roots=())
    return cap, ac._grade_dens(cap, "t_mech")


def test_scan_a_top_level_whole_row_select_in_a_contract_entry_reads_pass(tree):
    cap, g = _grade(tree, "SELECT to_jsonb(d) AS row FROM t_mech d WHERE d.chart_id = $1")
    assert g["v"] == ac.PASS and cap["dense"] and cap["dense"][0][1] == ["verification_pass_status"], (cap, g)


def test_scan_a_join_whose_asset_alias_is_the_one_projected_reads_pass(tree):
    cap, g = _grade(tree, "SELECT to_jsonb(m) AS row FROM driver x JOIN t_mech m ON m.id = x.id WHERE x.chart_id = $1")
    assert g["v"] == ac.PASS, (cap, g)


@pytest.mark.parametrize("name,sql,cols", [
    ("a different table's alias", "SELECT to_jsonb(o) AS row FROM other o JOIN t_mech d ON d.id = o.id", COLS),
    ("the driving table's alias while the asset is only joined", "SELECT to_jsonb(x) AS row FROM driver x JOIN t_mech m ON m.id = x.id", COLS),
    ("the asset table has no tier column", "SELECT to_jsonb(d) AS row FROM t_mech d", NO_TIER_COLS),
    ("row_to_json", "SELECT row_to_json(d) AS row FROM t_mech d", COLS),
    ("jsonb_build_object", "SELECT jsonb_build_object('id', d.mechanism_id) AS row FROM t_mech d", COLS),
    ("to_jsonb in a comment", "SELECT d.mechanism_id, -- note, to_jsonb(d)\n d.valence FROM t_mech d", COLS),
    ("to_jsonb in a string literal", "SELECT 'to_jsonb(d)' AS note, d.mechanism_id FROM t_mech d", COLS),
    ("to_jsonb inside a sub-select of the list", "SELECT (SELECT to_jsonb(d) LIMIT 1) AS row FROM t_mech d", COLS),
])
def test_scan_the_forgeries_are_not_credited(tree, name, sql, cols):
    cap, g = _grade(tree, sql, cols)
    assert g["v"] != ac.PASS and not cap["dense"], (name, cap, g)


def test_scan_the_cte_body_shape_of_query_mechanisms_stays_partial_E9(tree):
    """bo_yantra_mechanism's `WITH page_rows AS (SELECT to_jsonb(d) AS row, .. FROM t_mech d ..) SELECT jsonb_agg(page_rows.row) ..`: the whole row is in a CTE BODY, which the served-read rule
    does not credit (a CTE body is a sub-query; E8 condition 3). Propagating a CTE's `to_jsonb(d) AS row` to the final select that aggregates `<cte>.row` would be a further rule (E9, open)."""
    sql = ("WITH page_rows AS (SELECT to_jsonb(d) AS row, d.mechanism_class AS order_class FROM t_mech d WHERE d.chart_id = $1) "
           "SELECT COALESCE((SELECT jsonb_agg(page_rows.row) FROM page_rows), '[]'::jsonb) AS rows")
    cap, g = _grade(tree, sql)
    assert g["v"] == ac.PARTIAL and not cap["dense"], (cap, g)


def test_the_committed_query_mechanisms_module_is_still_partial_for_that_reason():
    """The real module: its served select of bodha_mechanisms is the page_rows CTE body, so no served select earns a tier column (E9)."""
    mod = (HERE.parents[2] / "src/lib/retrieval/registry/layers/L2_bodha/query_mechanisms.ts").read_text(encoding="utf-8")
    assert "WITH" in mod and "page_rows AS (" in mod and "to_jsonb(d) AS row" in mod
    cap = ac.capability_scan(ac.CAPS_ROOTS, ["bodha_mechanisms", "bo_yantra_mechanism"], shared=frozenset(), columns={"bodha_mechanisms": COLS}, outside_roots=())
    assert not any("query_mechanisms.ts" in n for n, _c in cap["dense"]), cap["dense"]
