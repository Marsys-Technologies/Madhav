"""TI-L0-04 (folded into the DENS-SCANNER stream, REGISTRY_REVISION 26; originally held PR #3105) (Track I, L0 INDEX section 8, SS Q2, R, PROVISIONAL until the J1 review): Dens.served for a reference
vocabulary of uniform authority.

Dens.served PASSes today only when ONE capability declares `density_contract` AND its own served select carries a
tier column (`DENS_TIER_COLUMN`). Among the populated columns of the 40 L0 target tables no tier-like column exists
(the one candidate, `cost_tier`, is a cost tier), so an L0 asset could not reach PASS by declaring a contract alone.
SS Q2: a vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then
PASSes on the `density_contract` FACETS without a tier column; mixed-authority tables still need a real tier.

The rule implemented (asset_census.py `capability_scan` + `_grade_dens`), and nothing wider:
  * PASS (new) only when ALL of: the asset's declaration says `uniform_authority: true`; a capability entry that
    references the asset declares `density_contract` as an inline object whose `facets` list is non-empty; and the
    SAME capability entry holds a real served `SELECT ... FROM <the asset's table>` (not a sub-select, an
    INSERT...SELECT or a UNION branch).
  * The existing tier-column PASS is unchanged and is tested first (its text is unchanged).
  * Everything else is unchanged: no declaration, `facets: []`, facets that are not an inline list, a contract that
    does not serve the table, no contract at all (FAIL), an unparsed file (NO_DETECTOR), the N/A readings.
The declaration key `uniform_authority` is inert until TI-L0-03 declares it (declarations file), so no census cell
moves on today's declarations.

Same synthetic-tree harness as test_e6_1_dens_repair.py.
"""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_1_dens_repair as dr  # noqa: E402
import test_w2_1_earned_verdicts as w1  # noqa: E402

tree = dr.tree                                   # the synthetic-source-tree fixture (re-exported for pytest)
UA = dict(why="every row of this reference vocabulary is of uniform authority", evidence="platform/scripts/governance/asset_census.py:1")
FACETS = "density_contract: { paginated: true, facets: ['graha', 'direction'], empty_reason: true },"
NO_FACETS = "density_contract: { paginated: true, facets: [], empty_reason: true },"
IDENT_FACETS = "density_contract: { paginated: true, facets: FACET_NAMES, empty_reason: true },"
IDENT_CONTRACT = "density_contract: SHARED_CONTRACT,"


def _cap(sql, contract=FACETS, name="cap"):
    return (f"export const {name} = {{\n  id: '{name}',\n  {contract}\n"
            f"  run: async () => query(`{sql}`),\n}}\n")


def _dens(monkeypatch, tree, src, *, uniform=True, tables=None, name="q.ts", extra=None):
    tree.write(tree.layers / "L0_x", name, src)
    for fname, body in (extra or {}).items():
        tree.write(tree.layers / "L0_x", fname, body)
    decls = {"bg_x": dict(kind="data", **({"uniform_authority": UA if uniform else None} if uniform is not None else {}))}
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: copy.deepcopy(decls))
    c = dr._measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")},
                    tables if tables is not None else {"t_x": (["fact_id", "fact_value"], [])})
    return dr._dens(c, "bg_x")


# ───────────────────────────── the new PASS ─────────────────────────────

def test_uniform_authority_with_facets_in_the_serving_capability_reads_pass(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, fact_value FROM t_x"))
    assert d["v"] == ac.PASS, d
    assert "uniform_authority" in d["measured"] and "facets" in d["measured"] and "no tier column" in d["measured"], d


def test_without_the_declaration_the_same_capability_stays_partial(tree, monkeypatch):
    """The key test: `uniform_authority` is the ONLY thing that turns this PARTIAL into PASS."""
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, fact_value FROM t_x"), uniform=None)
    assert d["v"] == ac.PARTIAL and "no tier column" in d["measured"], d


def test_uniform_authority_false_is_not_a_release(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, fact_value FROM t_x"), uniform=False)
    assert d["v"] == ac.PARTIAL, d


def test_empty_facets_do_not_carry_the_pass(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, fact_value FROM t_x", contract=NO_FACETS))
    assert d["v"] == ac.PARTIAL, d


def test_facets_that_are_not_an_inline_list_are_not_established(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, fact_value FROM t_x", contract=IDENT_FACETS))
    assert d["v"] == ac.PARTIAL, d


def test_a_contract_that_is_not_an_inline_object_is_not_established(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, fact_value FROM t_x", contract=IDENT_CONTRACT))
    assert d["v"] != ac.PASS, d


def test_a_facets_key_outside_the_contract_object_is_not_the_contracts_facets(tree, monkeypatch):
    src = ("export const cap = {\n  id: 'cap',\n  facets: ['graha'],\n  " + NO_FACETS +
           "\n  run: async () => query(`SELECT fact_id FROM t_x`),\n}\n")
    d = _dens(monkeypatch, tree, src)
    assert d["v"] == ac.PARTIAL, d


def test_a_facets_list_nested_inside_the_contract_is_not_the_contracts_own(tree, monkeypatch):
    contract = "density_contract: { paginated: true, meta: { facets: ['graha'] }, facets: [], empty_reason: true },"
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, fact_value FROM t_x", contract=contract))
    assert d["v"] == ac.PARTIAL, d


def test_facets_named_only_inside_a_string_literal_do_not_count(tree, monkeypatch):
    contract = "density_contract: { paginated: true, note: \"facets: ['graha']\", facets: [], empty_reason: true },"
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, fact_value FROM t_x", contract=contract))
    assert d["v"] == ac.PARTIAL, d


def test_facets_named_only_in_a_comment_do_not_count(tree, monkeypatch):
    contract = "density_contract: { paginated: true, /* facets: ['graha'] */ facets: [], empty_reason: true },"
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, fact_value FROM t_x", contract=contract))
    assert d["v"] == ac.PARTIAL, d


# ───────────────────────────── the contract must be the serving capability's ─────────────────────────────

def test_a_contract_in_a_sibling_capability_does_not_carry_the_pass(tree, monkeypatch):
    src = _cap("SELECT fact_id FROM other_table", name="capA") + _cap("SELECT fact_id FROM t_x", contract="", name="capB")
    d = _dens(monkeypatch, tree, src)
    assert d["v"] != ac.PASS, d


def test_a_union_branch_or_insert_select_is_not_a_served_read(tree, monkeypatch):
    for sql in ("SELECT fact_id FROM other_table UNION ALL SELECT fact_id FROM t_x",
                "INSERT INTO sink SELECT fact_id FROM t_x"):
        d = _dens(monkeypatch, tree, _cap(sql), tables={"t_x": (["fact_id"], [])})
        assert d["v"] != ac.PASS, (sql, d)


def test_no_contract_anywhere_is_still_fail(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, fact_value FROM t_x", contract=""))
    assert d["v"] == ac.FAIL, d


# ───────────────────────────── precedence and non-regression ─────────────────────────────

def test_the_tier_column_pass_is_unchanged_and_wins(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id, verification_pass_status FROM t_x"),
              tables={"t_x": (["fact_id", "verification_pass_status"], [])})
    assert d["v"] == ac.PASS and "verification_pass_status" in d["measured"] and "uniform_authority" not in d["measured"], d


def test_a_module_that_cannot_be_parsed_never_passes_on_the_declaration_alone(tree, monkeypatch):
    # an unbalanced quote desyncs the string scanner: neither the contract nor the facets can be read
    d = _dens(monkeypatch, tree, "export const cap = { note: 'it's t_x', " + FACETS + " }\n")
    assert d["v"] != ac.PASS, d


def test_a_not_served_asset_stays_not_applicable_whatever_it_declares(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _cap("SELECT fact_id FROM unrelated_table"))
    assert d["v"] == ac.NA, d


# ───────────────────────────── the declaration validator (N-154 Q1: {why, evidence}) ─────────────────────────────

def _doc(entry):
    return dict(version="9.9.9", kind_enum=list(ac.DECLARED_KINDS), assets={"bg_x": entry})


def test_validator_accepts_an_object_with_why_and_evidence_or_null():
    ac.validate_declarations(_doc(dict(kind="data", uniform_authority=UA)))
    ac.validate_declarations(_doc(dict(kind="data", uniform_authority=None)))


@pytest.mark.parametrize("value", [True, False, "true", 1, [True], {}, {"why": "every row of this vocabulary is of uniform authority"},
                                   dict(UA, extra=1), dict(UA, why="short"), dict(UA, why="a reason with three plain words only"),
                                   dict(UA, evidence="unverified:somewhere i looked"), dict(UA, evidence="platform/src/nope.ts:1"),
                                   dict(UA, evidence="platform/scripts/governance/asset_census.py"), dict(UA, evidence="platform/scripts/governance/asset_census.py:99999999")])
def test_validator_refuses_a_bare_boolean_and_an_unsound_object(value):
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations(_doc(dict(kind="data", uniform_authority=value)))
