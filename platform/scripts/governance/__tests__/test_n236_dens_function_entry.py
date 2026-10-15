"""test_n236_dens_function_entry.py: the depth-ONE helper credit when the contract object sits in an entry FUNCTION that calls the helper in its body (SS N-236).

register_gochara_windows.ts / computeGocharaElectionAvoidance: `const mitigation = await fetchMitigation(..)` is called in the function body, and the `density_contract` sits in the object the function RETURNS.
The E4 rule looked for the call only inside the contract object's own braces. Now, when the contract object is the ONLY one in its enclosing top-level function, a direct call anywhere in that function's body
is the entry's own call. Still depth ONE, same module, a name that is a call (not a mention, not `x.name(`); a declaration holding SEVERAL contract objects keeps the old object-span rule; no tier column, no PASS.
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


def _fn(body_before, in_obj=""):
    return f"export async function computeX(args) {{\n  {body_before}\n  return {{\n    id: 'bg_x',\n    {CONTRACT}\n    {in_obj}\n  }}\n}}\n"


def _dens(monkeypatch, tree, src):
    tree.write(tree.layers / "L0_x", "q.ts", src)
    c = dr._measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": (["id", "verification_pass_status"], [])})
    return dr._dens(c, "bg_x")


def test_a_helper_called_in_the_function_body_before_the_returned_contract_object_is_the_entrys_read(tree, monkeypatch):
    d = _dens(monkeypatch, tree, HELPER_TIER + _fn("const m = await fetchRows(args.id)", "m,"))
    assert d["v"] == ac.PASS and "verification_pass_status" in d["measured"], d


def test_the_call_inside_the_object_still_works_as_before(tree, monkeypatch):
    d = _dens(monkeypatch, tree, HELPER_TIER + _fn("", "rows: await fetchRows(args.id),"))
    assert d["v"] == ac.PASS, d


# ───────────────────────── MUTATIONS: each stops the credit ─────────────────────────

def test_MUTATION_no_call_in_the_function_credits_nothing(tree, monkeypatch):
    assert _dens(monkeypatch, tree, HELPER_TIER + _fn("const m = null", "m,"))["v"] != ac.PASS


def test_MUTATION_a_name_only_mentioned_or_a_method_call_is_not_the_helper(tree, monkeypatch):
    assert _dens(monkeypatch, tree, HELPER_TIER + _fn("const label = 'fetchRows'", "label,"))["v"] != ac.PASS
    assert _dens(monkeypatch, tree, HELPER_TIER + _fn("const m = await other.fetchRows(args.id)", "m,"))["v"] != ac.PASS


def test_MUTATION_a_call_in_a_different_function_is_not_the_entrys_call(tree, monkeypatch):
    other = "async function elsewhere(id: string) {\n  return fetchRows(id)\n}\n"
    assert _dens(monkeypatch, tree, HELPER_TIER + other + _fn("const m = null", "m,"))["v"] != ac.PASS


def test_MUTATION_depth_two_is_still_not_credited(tree, monkeypatch):
    mid = "async function outer(id: string) {\n  return fetchRows(id)\n}\n"
    assert _dens(monkeypatch, tree, HELPER_TIER + mid + _fn("const m = await outer(args.id)", "m,"))["v"] != ac.PASS


def test_MUTATION_a_helper_without_a_tier_column_earns_no_pass(tree, monkeypatch):
    d = _dens(monkeypatch, tree, HELPER_NO_TIER + _fn("const m = await fetchRows(args.id)", "m,"))
    assert d["v"] == ac.PARTIAL and "no tier column" in d["measured"], d


def test_MUTATION_two_contract_objects_in_one_function_keep_the_object_span_rule(tree, monkeypatch):
    """A function that returns two entries: a call before them belongs to neither object; it must NOT be credited to both."""
    two = (f"export async function computeBoth(args) {{\n  const m = await fetchRows(args.id)\n  return [\n    {{ id: 'a', {CONTRACT} m }},\n    {{ id: 'b', {CONTRACT} z: 1 }},\n  ]\n}}\n")
    assert _dens(monkeypatch, tree, HELPER_TIER + two)["v"] != ac.PASS


def test_MUTATION_the_helper_that_is_the_entrys_own_declaration_is_judged_by_position(tree, monkeypatch):
    own = _fn("const m = await query(`SELECT id FROM t_x`)", "m,")                       # a select inside the entry itself, no tier: PARTIAL, never credited by the call rule
    assert _dens(monkeypatch, tree, own)["v"] == ac.PARTIAL
