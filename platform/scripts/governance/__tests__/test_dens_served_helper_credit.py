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


# The opt-in imported-reader subset mirrors the ordinary transit handler shape.
_READER_PATH = "platform/src/lib/brahmagyan/readers.ts"
_READER_EDGE = ("layers/L0_x/q.ts", "cap", _READER_PATH, "fetchRows")
_READER_IMPORT = "import { fetchRows } from '@/lib/brahmagyan/readers'\n"


def _reader_entry(call="fetchRows(args.id)", prefix=""):
    return ("export const cap = {\n  id: 'bg_x',\n  " + CONTRACT
            + "\n  provenance: { tables: ['t_x'] },\n  async handler(args) {\n    "
            + prefix + "\n    try {\n      const rows = await " + call
            + "\n      return rows\n    } catch (error) { throw error }\n  },\n}\n")


def _reader(sql="SELECT id, verification_pass_status FROM t_x"):
    return ("import { query } from '@/lib/db/client'\n"
            "export function fetchRows(id: string) {\n  const sql = `" + sql
            + "`\n  return query(sql, [id])\n}\n")


def _imported_scan(monkeypatch, tree, source=None, reader=None, bindings=None):
    source = _READER_IMPORT + _reader_entry() if source is None else source
    reader = _reader() if reader is None else reader
    tree.write(tree.layers / "L0_x", "q.ts", source)
    target = tree.tmp / _READER_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(reader, encoding="utf-8")
    monkeypatch.setattr(ac, "ROOT", tree.tmp)
    return ac.capability_scan(tree.roots, ["bg_x", "t_x"], columns={"t_x": ["id", "verification_pass_status"]},
                              outside_roots=(str(tree.tmp / "platform/src"),),
                              reader_bindings=(_READER_EDGE,) if bindings is None else bindings)


def test_explicit_named_imported_reader_earns_only_its_real_select(tree, monkeypatch):
    result = _imported_scan(monkeypatch, tree)
    assert result["served"] == 1 and result["outside"] == []
    assert ac._grade_dens(result, "bg_x")["v"] == ac.PASS
    assert result["served_at"][0][0] == _READER_PATH


@pytest.mark.parametrize("source", [
    "import { fetchRows as readRows } from '@/lib/brahmagyan/readers'\n" + _reader_entry("readRows(args.id)"),
    "import { fetchRows } from '../../platform/src/lib/brahmagyan/readers'\n" + _reader_entry(),
])
def test_exact_reader_alias_and_relative_resolution_are_supported(tree, monkeypatch, source):
    result = _imported_scan(monkeypatch, tree, source=source)
    assert result["served"] == 1 and ac._grade_dens(result, "bg_x")["v"] == ac.PASS


@pytest.mark.parametrize("source", [
    "// " + _READER_IMPORT + _reader_entry(),
    "const example = \"import { fetchRows } from '@/lib/brahmagyan/readers'\"\n" + _reader_entry(),
    _READER_IMPORT + _reader_entry("'fetchRows(args.id)'"),
    _READER_IMPORT + _reader_entry("other.fetchRows(args.id)"),
    _READER_IMPORT + _reader_entry("null") + "// fetchRows(args.id)\n",
    _READER_IMPORT + _reader_entry(prefix="return null;"),
    _READER_IMPORT + _reader_entry(prefix="fetchRows = other;"),
    _READER_IMPORT + _reader_entry(prefix="const fetchRows = other;"),
    _READER_IMPORT + _reader_entry().replace("export const cap", "export const otherCap"),
    "import { otherReader as fetchRows } from '@/lib/brahmagyan/readers'\n" + _reader_entry(),
    "import { fetchRows } from '@/lib/brahmagyan/other'\n" + _reader_entry(),
])
def test_unowned_inactive_or_shadowed_imported_reader_gets_no_credit(tree, monkeypatch, source):
    result = _imported_scan(monkeypatch, tree, source=source)
    assert result["served"] == 0 and result["density"] == 0
    assert ac._grade_dens(result, "bg_x")["v"] != ac.PASS


@pytest.mark.parametrize("bindings", [(), (_READER_EDGE, _READER_EDGE),
    ((_READER_EDGE[0], "cap", _READER_PATH, "missingReader"),)])
def test_imported_credit_requires_one_unambiguous_opt_in_edge(tree, monkeypatch, bindings):
    result = _imported_scan(monkeypatch, tree, bindings=bindings)
    assert result["served"] == 0


@pytest.mark.parametrize("reader", [
    _reader().replace("export function", "function"),
    _reader() + _reader(),
    _reader().replace("return query(sql, [id])", "return []"),
    _reader().replace("return query(sql, [id])", "return query(otherSql, [id])"),
    _reader().replace("  const sql", "  function nested() {}\n  const sql"),
])
def test_reader_export_and_actual_sql_argument_must_be_owned(tree, monkeypatch, reader):
    result = _imported_scan(monkeypatch, tree, reader=reader)
    assert result["served"] == 0


def test_unrelated_tier_read_in_same_owner_file_does_not_upgrade_or_add_credit(tree, monkeypatch):
    reader = (_reader("SELECT id FROM t_x")
              + "export function unrelated() { const sql = `SELECT verification_pass_status FROM t_x`; return query(sql, []) }\n")
    result = _imported_scan(monkeypatch, tree, reader=reader)
    assert result["served"] == 1 and result["density"] == 0
    assert ac._grade_dens(result, "bg_x")["v"] == ac.PARTIAL
    assert result["outside"] == [_READER_PATH]


def test_unrelated_brahmagyan_file_stays_outside_the_serving_roots(tree, monkeypatch):
    target = tree.tmp / "platform/src/lib/brahmagyan"
    target.mkdir(parents=True)
    (target / "unrelated.ts").write_text("export const unrelated = query(`SELECT verification_pass_status FROM t_x`)\n")
    result = _imported_scan(monkeypatch, tree, reader=_reader("SELECT id FROM t_x"))
    assert result["served"] == 1 and result["density"] == 0
    assert ac._grade_dens(result, "bg_x")["v"] == ac.PARTIAL
    assert "platform/src/lib/brahmagyan/unrelated.ts" in result["outside"]


@pytest.mark.parametrize("link_kind", ["file", "parent"])
def test_imported_reader_source_symlinks_earn_no_credit(tree, monkeypatch, link_kind):
    assert _imported_scan(monkeypatch, tree)["served"] == 1
    target = tree.tmp / _READER_PATH
    if link_kind == "file":
        relocated = tree.tmp / "relocated-reader.ts"
        target.rename(relocated)
        target.symlink_to(relocated)
    else:
        relocated = tree.tmp / "relocated-readers"
        target.parent.rename(relocated)
        target.parent.symlink_to(relocated, target_is_directory=True)
    result = ac.capability_scan(tree.roots, ["bg_x", "t_x"], columns={"t_x": ["id", "verification_pass_status"]},
                                outside_roots=(), reader_bindings=(_READER_EDGE,))
    assert result["served"] == 0
