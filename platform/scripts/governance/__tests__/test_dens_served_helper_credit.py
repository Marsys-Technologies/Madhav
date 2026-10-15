"""test_dens_served_helper_credit.py — SS N-211 (E4): a served select in a top-level helper function of the SAME module is credited to the contract-declaring entry that CALLS it, at depth ONE.

Before: a contract entry earned PASS only from a select sitting inside its own object literal; the common shape (`handler` calls `fetchRows()` which holds the SELECT) read PARTIAL / FAIL
("its served select of the table is in a different top-level declaration"). Now the entry's direct call to a same-module helper makes that helper's select the entry's read; nothing else does:
a helper never called, a name merely mentioned, a helper reached only through another helper (depth 2), a helper that holds no tier column, and a select outside the module credit nothing.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_dens_served_helper_credit.py -v
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_1_dens_repair as dr  # noqa: E402
import test_w2_1_earned_verdicts as w1  # noqa: E402

tree = dr.tree

CONTRACT = "density_contract: { paginated: true, facets: ['a'], empty_reason: true },"
HELPER_TIER = "async function fetchRows(id: string) {\n  return query(`SELECT id, verification_pass_status FROM t_x WHERE id = $1`, [id])\n}\n"
HELPER_NO_TIER = "async function fetchRows(id: string) {\n  return query(`SELECT id FROM t_x WHERE id = $1`, [id])\n}\n"


def _entry(body):
    return f"export const cap = {{\n  id: 'bg_x',\n  {CONTRACT}\n  async handler(args) {{\n    {body}\n  }},\n}}\n"


def _dens(monkeypatch, tree, src):
    tree.write(tree.layers / "L0_x", "q.ts", src)
    c = dr._measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": (["id", "verification_pass_status"], [])})
    return dr._dens(c, "bg_x")


def test_a_helper_called_directly_by_the_entry_carries_its_tier_to_the_entry(tree, monkeypatch):
    d = _dens(monkeypatch, tree, HELPER_TIER + _entry("return fetchRows(args.id)"))
    assert d["v"] == ac.PASS and "verification_pass_status" in d["measured"], d


def test_the_helper_may_be_declared_after_the_entry_and_be_an_arrow_function(tree, monkeypatch):
    helper = "const fetchRows = async (id: string) => query(`SELECT id, verification_pass_status FROM t_x WHERE id = $1`, [id])\n"
    d = _dens(monkeypatch, tree, _entry("return fetchRows(args.id)") + helper)
    assert d["v"] == ac.PASS, d


def test_without_the_call_the_same_helper_credits_nothing(tree, monkeypatch):
    d = _dens(monkeypatch, tree, HELPER_TIER + _entry("return null"))
    assert d["v"] != ac.PASS, d


def test_a_name_only_mentioned_is_not_a_call(tree, monkeypatch):
    d = _dens(monkeypatch, tree, HELPER_TIER + _entry("const label = 'fetchRows'\n    return label"))
    assert d["v"] != ac.PASS, d


def test_a_helper_reached_through_another_helper_is_depth_two_and_credits_nothing(tree, monkeypatch):
    mid = "async function outer(id: string) {\n  return fetchRows(id)\n}\n"
    d = _dens(monkeypatch, tree, HELPER_TIER + mid + _entry("return outer(args.id)"))
    assert d["v"] != ac.PASS, d


def test_a_helper_whose_select_carries_no_tier_earns_no_pass(tree, monkeypatch):
    d = _dens(monkeypatch, tree, HELPER_NO_TIER + _entry("return fetchRows(args.id)"))
    assert d["v"] == ac.PARTIAL and "no tier column" in d["measured"], d


def test_a_method_call_with_the_same_name_is_not_the_helper(tree, monkeypatch):
    d = _dens(monkeypatch, tree, HELPER_TIER + _entry("return other.fetchRows(args.id)"))
    assert d["v"] != ac.PASS, d


def test_a_select_in_the_entrys_own_declaration_is_unchanged(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _entry("return query(`SELECT id, verification_pass_status FROM t_x`)"))
    assert d["v"] == ac.PASS, d


def test_the_helper_must_be_in_the_same_module(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "helper.ts", HELPER_TIER.replace("async function", "export async function"))
    d = _dens(monkeypatch, tree, "import { fetchRows } from './helper'\n" + _entry("return fetchRows(args.id)"))
    # the select is in another module that declares no contract: the contract-declaring module has no select of its own
    assert d["v"] != ac.PASS, d
