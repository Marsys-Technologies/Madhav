"""test_dens_served_const_map_select.py — DENS-SERVED (detector accuracy): a select list read from a module const map.

`SELECT ${columns}` with `const columns = TIER_COLUMNS[tier]` and a module-level `TIER_COLUMNS = { a: `...`, b: `...` }` was always read as a run-time
column list (tier carriage UNKNOWN: PARTIAL at best). The list is statically readable when the interpolation names a const map of string literals, so
`_select_tier_resolved` grades each value the interpolation can take:

  every value carries a tier column  -> the select carries one (so a contract in the same entry reads PASS)
  every value carries none           -> the select carries none (PARTIAL: no tier column)
  a mixture, an unreadable map, a second interpolation, or a non-map expression -> exactly the old reading (UNKNOWN)

It may only make a verdict MORE accurate: the PASS needs a tier column in EVERY reachable list.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_dens_served_const_map_select.py -v
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

tree = dr.tree                                   # the synthetic-source-tree fixture (re-exported for pytest)

MAP_TIER_ALL = (
    "const TIER_COLUMNS: Record<string, string> = {\n"
    "  a: `fact_id, verification_pass_status,\n       citation_ref`,\n"
    "  b: `rollup_id, verification_pass_status`,\n"
    "}\n")
MAP_TIER_MIXED = (
    "const TIER_COLUMNS: Record<string, string> = {\n"
    "  a: `fact_id, verification_pass_status`,\n"
    "  b: `rollup_id, citation_ref`,\n"
    "}\n")
MAP_TIER_NONE = (
    "const TIER_COLUMNS: Record<string, string> = {\n"
    "  a: `fact_id, citation_ref`,\n"
    "  b: 'rollup_id, citation_ref',\n"
    "}\n")


def _src(const_map, select_list="${columns}", pre="  const columns = TIER_COLUMNS[tier]\n"):
    return (const_map +
            "export const cap = {\n  id: 'cap',\n  density_contract: { paginated: true, facets: ['x'], empty_reason: true },\n"
            "  async handler(tier: string) {\n" + pre +
            "    return query(`SELECT " + select_list + " FROM t_x WHERE chart_id = $1`)\n  },\n}\n")


def _dens(monkeypatch, tree, src):
    tree.write(tree.layers / "L0_x", "q.ts", src)
    c = dr._measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")},
                    {"t_x": (["fact_id", "rollup_id", "citation_ref", "verification_pass_status"], [])})
    return dr._dens(c, "bg_x")


def test_every_value_of_the_const_map_carries_the_tier_reads_pass(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _src(MAP_TIER_ALL))
    assert d["v"] == ac.PASS and "verification_pass_status" in d["measured"], d


def test_one_value_without_a_tier_column_stays_unknown_partial(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _src(MAP_TIER_MIXED))
    assert d["v"] == ac.PARTIAL and "tier carriage not established" in d["measured"], d


def test_no_value_with_a_tier_column_reads_no_tier_partial(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _src(MAP_TIER_NONE))
    assert d["v"] == ac.PARTIAL and "no tier column" in d["measured"], d


def test_a_non_map_expression_is_still_a_run_time_list(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _src(MAP_TIER_ALL, pre="  const columns = buildColumns(tier)\n"))
    assert d["v"] == ac.PARTIAL and "tier carriage not established" in d["measured"], d


def test_a_second_interpolation_in_the_list_is_not_resolved(tree, monkeypatch):
    d = _dens(monkeypatch, tree, _src(MAP_TIER_ALL, select_list="${columns}, ${extra}", pre="  const columns = TIER_COLUMNS[tier]\n  const extra = 'x'\n"))
    assert d["v"] == ac.PARTIAL and "tier carriage not established" in d["measured"], d


def test_a_map_entry_with_an_interpolation_is_unreadable(tree, monkeypatch):
    bad = ("const TIER_COLUMNS: Record<string, string> = {\n"
           "  a: `fact_id, verification_pass_status`,\n"
           "  b: `rollup_id, ${extraCol}`,\n}\n")
    d = _dens(monkeypatch, tree, _src(bad))
    assert d["v"] == ac.PARTIAL and "tier carriage not established" in d["measured"], d


def test_the_resolution_function_directly():
    mod = ac._dens_facts(MAP_TIER_ALL + "const columns = TIER_COLUMNS[tier]\n")
    st, cols = ac._select_tier_resolved(mod, " ${columns} ", None, "t_x", None)
    assert st == ac.TIER_YES and cols == ["verification_pass_status"]
