"""test_dens_served_bind_facet.py — SS N-211 (E3 i) and (E2 table-less form).

E3 (i): a shared table's select is attributed to an asset through its declared `density_facet` even when the facet column is filtered by a BIND PARAMETER (`col = ANY($2)`), provided
  1. the declaration names the `input` that binds the column AND the one serving module (`served_by`),
  2. the SQL of the select (or a standalone filter literal of its entry) really filters the declared column by a bind parameter (the engine verifies it, never the declaration),
  3. the capability ENTRY that holds the select documents that input in its `input_schema`,
  4. the file the select sits in IS the declared `served_by`.
A literal pin (the old rule) is unchanged. Each condition has a mutation test: drop it and the select is not attributed.

E2 table-less form: `uniform_authority.tables` for an asset with no target table, checked against the tables it owns and their catalog columns (a tier column anywhere refuses it).

Run:
  python -m pytest platform/scripts/governance/__tests__/test_dens_served_bind_facet.py -v
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
COLS = {"t_shared": ["fact_id", "fact_category", "verification_pass_status"]}


def _src(*, input_schema="input_schema: { chart_id: { type: 'string' }, categories: { type: 'array' } },", sql="SELECT fact_id, verification_pass_status FROM t_shared WHERE fact_category = ANY($2::text[])",
         contract="density_contract: { paginated: true, facets: ['categories'], empty_reason: true },"):
    return ("export const cap = {\n  id: 'cap_x',\n  " + contract + "\n  " + input_schema + "\n"
            "  async handler(args) {\n    return query(`" + sql + "`, [args.chart_id, args.categories])\n  },\n}\n")


def _scan(tree, src, *, values=("sade",), served_by="L0_x/q.ts", column="fact_category", inp="categories"):
    tree.write(tree.layers / "L0_x", "q.ts", src)
    # the scan compares served_by with the module's repo path; files of the synthetic tree report their absolute path
    sb = str(tree.layers / "L0_x" / "q.ts") if served_by == "L0_x/q.ts" else served_by
    f = dict(column=column, values=list(values), input=inp, served_by=sb)
    return _REAL_SCAN(tree.roots, ["t_shared", "bg_x"], shared={"t_shared"}, columns=COLS, outside_roots=(), facets={"t_shared": f})


def test_a_bound_filter_whose_input_the_capability_documents_is_attributed_and_passes(tree):
    cap = _scan(tree, _src())
    assert cap["facet_attributed"] == ["L0_x/q.ts"] and cap["facet_bound_credited"] == ["L0_x/q.ts"], cap
    g = ac._grade_dens(cap, "t_shared")
    assert g["v"] == ac.PASS and "bind-parameter facet" in g["measured"], g


def test_mutation_without_the_input_documented_in_the_entry_nothing_is_attributed(tree):
    cap = _scan(tree, _src(input_schema="input_schema: { chart_id: { type: 'string' } },"))
    assert not cap["facet_attributed"] and cap["facet_bound"] == ["L0_x/q.ts"], cap
    assert ac._grade_dens(cap, "t_shared")["v"] == ac.NO_DET


def test_mutation_without_a_bind_filter_on_the_declared_column_nothing_is_attributed(tree):
    cap = _scan(tree, _src(sql="SELECT fact_id, verification_pass_status FROM t_shared WHERE chart_id = $1"))
    assert not cap["facet_attributed"] and not cap["facet_bound_credited"], cap


def test_mutation_a_bind_filter_on_another_column_is_not_the_declared_facet(tree):
    cap = _scan(tree, _src(sql="SELECT fact_id, verification_pass_status FROM t_shared WHERE fact_subject = ANY($2::text[])"))
    assert not cap["facet_attributed"], cap


def test_mutation_another_module_than_served_by_is_not_credited(tree):
    cap = _scan(tree, _src(), served_by="platform/src/lib/other.ts")
    assert not cap["facet_attributed"] and cap["facet_bound"] == ["L0_x/q.ts"], cap


def test_a_declared_input_that_is_only_a_nested_key_is_not_documented(tree):
    cap = _scan(tree, _src(input_schema="input_schema: { chart_id: { type: 'string', meta: { categories: 1 } } },"))
    assert not cap["facet_attributed"], cap


def test_an_input_named_like_a_longer_key_is_not_the_input(tree):
    cap = _scan(tree, _src(input_schema="input_schema: { chart_id: { type: 'string' }, all_categories: { type: 'array' } },"))
    assert not cap["facet_attributed"], cap


def test_the_literal_pin_rule_is_unchanged(tree):
    tree.write(tree.layers / "L0_x", "q.ts", _src(sql="SELECT fact_id, verification_pass_status FROM t_shared WHERE fact_category = 'sade'"))
    cap = _REAL_SCAN(tree.roots, ["t_shared", "bg_x"], shared={"t_shared"}, columns=COLS, outside_roots=(), facets={"t_shared": dict(column="fact_category", values=["sade"])})
    assert cap["facet_attributed"] == ["L0_x/q.ts"] and not cap["facet_bound_credited"], cap
    assert ac._grade_dens(cap, "t_shared")["v"] == ac.PASS


def test_the_bound_credit_still_needs_the_contract_and_the_tier_in_the_same_entry(tree):
    no_contract = _scan(tree, _src(contract=""))
    assert ac._grade_dens(no_contract, "t_shared")["v"] == ac.FAIL
    no_tier = _scan(tree, _src(sql="SELECT fact_id FROM t_shared WHERE fact_category = ANY($2::text[])"))
    assert ac._grade_dens(no_tier, "t_shared")["v"] == ac.PARTIAL


@pytest.mark.parametrize("mut,frag", [
    (lambda d: d.pop("served_by"), "go together"),
    (lambda d: d.pop("input"), "go together"),
    (lambda d: d.update(served_by="platform/src/nope/missing.ts"), "existing"),
    (lambda d: d.update(served_by="../../etc/passwd"), "existing"),
    (lambda d: d.update(input="not an identifier"), "input_schema key"),
])
def test_the_declaration_form_is_checked(mut, frag):
    d = dict(column="fact_category", values=["ayurdaya"], why="the ayurdaya rows are the fact_category value this asset's writer stores",
             evidence="platform/src/lib/retrieval/registry/layers/L1_ganita/get_ayurdaya.ts:71", input="categories",
             served_by="platform/src/lib/retrieval/registry/layers/L1_ganita/get_ayurdaya.ts")
    assert ac.density_facet_problem(dict(density_facet=d)) is None
    mut(d)
    bad = ac.density_facet_problem(dict(density_facet=d))
    assert bad and frag in bad, bad


def test_the_value_cap_admits_the_33_panchanga_categories():
    assert ac.DENS_FACET_MAX_VALUES >= 33


# ───────────────────────────── the table-less uniform_authority form ─────────────────────────────

UA = dict(why="every row of the five seeded tables is static reference data of uniform authority", evidence="platform/scripts/governance/asset_census.py:1",
          tables=["t_a", "t_b"])


def _ua(**kw):
    e = dict(uniform_authority=dict(UA, **kw))
    return e


def test_table_less_form_passes_for_an_asset_with_no_table_that_owns_the_tables():
    cols = {"t_a": ["id", "classical_citation"], "t_b": ["id", "rule"]}
    assert ac.uniform_authority_measure_problem(_ua(), None, None, None, owned=["t_a", "t_b"], owned_columns=cols) is None


@pytest.mark.parametrize("kw,args,frag", [
    ({}, dict(table="t_a"), "table-less form"),                                              # an asset WITH a target table declares it without `tables`
    ({}, dict(owned=["t_a"]), "does not own"),                                               # t_b is not one of its count_sql tables
    ({}, dict(columns={"t_a": ["id"], "t_b": None}), "columns unknown"),                     # a view / absent table
    ({}, dict(columns={"t_a": ["id", "verification_pass_status"], "t_b": ["id"]}), "tier column"),
    ({"tables": []}, {}, "tables must be"),
    ({"tables": ["t_a", "t_a"]}, {}, "tables must be"),
    ({"tables": ["bad name"]}, {}, "tables must be"),
])
def test_table_less_form_refusals(kw, args, frag):
    owned = args.get("owned", ["t_a", "t_b"])
    cols = args.get("columns", {"t_a": ["id", "classical_citation"], "t_b": ["id", "rule"]})
    bad = ac.uniform_authority_measure_problem(_ua(**kw), args.get("table"), None, None, owned=owned, owned_columns=cols)
    assert bad and frag in bad, bad


def test_table_less_declared_tier_columns_count_as_tier_columns_too():
    e = _ua()
    e["density_tier_columns"] = [dict(column="rule", why="rule is the verification tier of this table", evidence="platform/scripts/governance/asset_census.py:1")]
    bad = ac.uniform_authority_measure_problem(e, None, None, None, owned=["t_a", "t_b"], owned_columns={"t_a": ["id"], "t_b": ["id", "rule"]})
    assert bad and "tier column" in bad, bad


def test_table_less_asset_passes_dens_through_any_one_capability_that_declares_the_contract_and_serves_one_of_its_tables(tree):
    tree.write(tree.layers / "L0_x", "q.ts",
               "export const cap = {\n  id: 'cap_x',\n  density_contract: { paginated: false, facets: ['a'], empty_reason: true },\n  run: () => query(`SELECT id, rule FROM t_b`),\n}\n")
    cap = _REAL_SCAN(tree.roots, ["t_a", "t_b", "bg_x"], shared=set(), columns={}, outside_roots=())
    assert ac._grade_dens(cap, "bg_x", uniform_authority=True)["v"] == ac.PASS
    assert ac._grade_dens(cap, "bg_x", uniform_authority=False)["v"] == ac.PARTIAL        # the declaration is the only thing that lifts it
