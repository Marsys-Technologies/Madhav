"""test_e6_1_dens_repair.py — E6.1 packet (d): the Dens scanner repair (N-22 ruling principle 4).

`Dens.served` used to read only its own layer directory (non-recursive) for the target table and the asset id,
and counted a module as "declaring density" if the file declared `density_contract:` anywhere. Two defects:
(1) 15 of 26 N/A cells had a code reference outside what the scan read (other layer directories, the MCP roots,
a `count_sql` table); (2) widening the scope alone with the file-level rule would turn 18 FAIL and 2 NO_DETECTOR
cells into an UNEARNED PASS (CLAUDE.md §N.8). The repaired rule, structural and labelled so:

  PASS     a capability (a top-level declaration) that references the asset declares `density_contract:` AND a served
           `SELECT ... FROM <the asset's table>` IN THAT SAME capability carries a tier column
  PARTIAL  such a capability declares the contract but the tier column is absent / not established
  FAIL     served (a served select of its table is found), no referencing capability declares the contract
  NO_DET   referenced but the scan cannot tell: comment-only, only through a table other assets share, no served
           select found, a missing root, or a served select outside the scanned roots
  N/A      no code reference anywhere (measured; `NA_RULE_DECISIONS` stays empty, so the rollup reads NO_DETECTOR)

Every test drives the real `capability_scan` / `measure()` over a small synthetic source tree.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_e6_1_dens_repair.py -v
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_w2_1_earned_verdicts as w1  # noqa: E402

_REAL_SCAN = w1._REAL["capability_scan"]

CONTRACT = "density_contract: { paginated: true, facets: [], empty_reason: true },"


def _cap(body_sql, contract=True, name="cap"):
    return (f"export const {name} = {{\n  id: '{name}',\n  {CONTRACT if contract else ''}\n"
            f"  run: async () => query(`{body_sql}`),\n}}\n")


class Tree:
    """A synthetic source tree shaped like the real one: `layers/` (registry layer dirs, recursive), the two MCP
    roots, and a wider `outside/` source tree (R23's roots are the only serving roots; this is the rest)."""

    def __init__(self, tmp):
        self.tmp = tmp
        self.layers, self.tools, self.lib, self.outside = (tmp / n for n in ("layers", "mcp_tools", "mcp_lib", "outside"))
        for d in (self.layers / "L0_x", self.layers / "L3_y", self.tools, self.lib, self.outside):
            d.mkdir(parents=True)
        self.roots = (str(self.layers), str(self.tools), str(self.lib))

    def write(self, where, name, body):
        (getattr(self, where) if isinstance(where, str) else where).joinpath(name).write_text(body, encoding="utf-8")


@pytest.fixture
def tree(tmp_path):
    return Tree(tmp_path)


def _scan(tree, tokens, shared=(), columns=None, outside=False):
    return _REAL_SCAN(tree.roots, tokens, shared=set(shared), columns=columns,
                      outside_roots=((str(tree.outside),) if outside else ()))


def _measure(monkeypatch, tree, reg, tables=None, outside=False):
    w1._stub_layer(monkeypatch, tree.tmp, reg, tables)
    monkeypatch.setattr(ac, "live_counts", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(ac, "capability_scan", _REAL_SCAN)
    monkeypatch.setattr(ac, "CAPS_ROOTS", tree.roots)
    monkeypatch.setattr(ac, "DENS_OUTSIDE_ROOTS", (str(tree.outside),) if outside else ())
    return ac.measure("L0")


def _dens(census, aid):
    return w1._m(census, aid, "Dens.served")


# ───────────────────────── PASS only on a real contract + tier column in the SAME served capability ─────────────────────────

def test_pass_needs_the_contract_and_a_tier_column_in_the_same_served_select(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT fact_id, verification_pass_status FROM t_x WHERE chart_id = $1"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": (["fact_id", "verification_pass_status"], [])})
    d = _dens(c, "bg_x")
    assert d["v"] == ac.PASS and "STRUCTURAL" in d["measured"] and "verification_pass_status" in d["measured"], d


def test_contract_without_a_tier_column_in_the_served_select_is_partial_never_pass(tree, monkeypatch):
    """The 18 FAIL + 2 NO_DETECTOR cells the file-level rule turned into PASS: contract declared, no tier column."""
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT fact_id, fact_value FROM t_x"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": (["fact_id", "fact_value"], [])})
    d = _dens(c, "bg_x")
    assert d["v"] == ac.PARTIAL and "no tier column" in d["measured"], d


def test_a_tier_column_without_a_contract_is_fail(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT fact_id, signature_tier FROM t_x", contract=False))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    d = _dens(c, "bg_x")
    assert d["v"] == ac.FAIL and "no referencing capability that serves it declares density_contract" in d["measured"], d


def test_the_contract_and_the_tier_column_must_sit_in_the_same_capability(tree, monkeypatch):
    """Per capability, not per file (N-22 §4 point 4): capability A declares the contract over a select with no tier
    column; capability B in the same file selects a tier column but declares no contract. The FILE has both halves; no
    capability has them together."""
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT fact_id FROM t_x", name="capA")
               + _cap("SELECT signature_tier FROM t_x", contract=False, name="capB"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    d = _dens(c, "bg_x")
    assert d["v"] == ac.PARTIAL, d


def test_a_contract_in_a_capability_that_does_not_reference_the_asset_is_not_its_contract(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT fact_id FROM other_table", name="capA")
               + _cap("SELECT signature_tier FROM t_x", contract=False, name="capB"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    assert _dens(c, "bg_x")["v"] == ac.FAIL


def test_a_run_time_select_list_with_known_catalog_columns_is_not_established_either(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT ${cols} FROM t_x"))
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": (["id", "v"], [])}), "bg_x")
    assert d["v"] == ac.PARTIAL and "not established" in d["measured"], d


def test_a_select_of_a_shared_table_in_a_capability_that_never_names_the_asset_is_not_its_served_select(tree, monkeypatch):
    """bg_a's id sits in capability A (contract, no select); capability B reads the shared table with a tier column and
    never names bg_a. B's select is the table's, not bg_a's: the scan has no served select for bg_a."""
    tree.write(tree.layers / "L0_x", "q.ts", "export const capA = {\n  " + CONTRACT + "\n  note: 'bg_a',\n}\n"
               + _cap("SELECT id, signature_tier FROM t_shared", contract=False, name="capB"))
    reg = {"bg_a": w1._reg_row("bg_a", "t_shared"), "bg_b": w1._reg_row("bg_b", "t_shared")}
    d = _dens(_measure(monkeypatch, tree, reg), "bg_a")
    assert d["v"] == ac.NO_DET and "no served select" in d["measured"], d


def test_a_contract_in_a_declaration_that_only_names_the_asset_id_is_not_its_serving_capability(tree, monkeypatch):
    """The contract sits in a capability that mentions `bg_x` in a string but serves no rows of its table, and nothing
    in the module selects from the table: there is no served select, so the scan cannot tell — not a PARTIAL."""
    tree.write(tree.tools, "tool.ts", "export const cap = {\n  " + CONTRACT + "\n  note: 'covers bg_x',\n}\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.NO_DET and "no served select" in d["measured"], d


def test_a_contract_and_a_served_select_in_different_declarations_is_partial_with_that_reason(tree, monkeypatch):
    """A helper holds the SQL (with the tier column); the descriptor that declares the contract only calls it. The
    scan cannot attribute the select to the contract, so: PARTIAL, never PASS, and it says why."""
    tree.write(tree.tools, "tool.ts",
               "async function load() {\n  return query(`SELECT id, signature_tier FROM t_x`)\n}\n"
               "export const cap = {\n  " + CONTRACT + "\n  note: 't_x',\n  run: () => load(),\n}\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.PARTIAL and "different top-level declaration" in d["measured"], d


def test_a_fail_names_a_contract_declared_elsewhere_in_the_module_so_the_limit_is_visible(tree, monkeypatch):
    """The descriptor that declares the contract never names the asset; a helper elsewhere in the file serves it. The
    verdict stays FAIL (no attribution), and the evidence says where a contract does sit — a reviewer sees the limit."""
    tree.write(tree.tools, "tool.ts",
               "export const cap = {\n  " + CONTRACT + "\n  run: () => other(),\n}\n"
               "async function other() {\n  return query(`SELECT id, signature_tier FROM t_x`)\n}\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.FAIL and "declared in" in d["measured"] and "not in a capability that serves it" in d["measured"], d


@pytest.mark.parametrize("col, ok", [
    ("verification_pass_status", True), ("tier", True), ("signature_tier", True), ("efficacy_tier", True),
    ("frontier", False), ("tiered_x", False), ("tier_note", False), ("confidence", False), ("fact_value", False),
])
def test_the_tier_column_vocabulary_is_exact(tree, monkeypatch, col, ok):
    tree.write(tree.layers / "L0_x", "q.ts", _cap(f"SELECT fact_id, {col} FROM t_x"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    assert (_dens(c, "bg_x")["v"] == ac.PASS) is ok, (col, _dens(c, "bg_x"))


def test_a_qualified_tier_column_of_another_table_does_not_count_when_columns_are_unknown_too(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts",
               _cap("SELECT a.fact_id, b.signature_tier FROM t_x a JOIN t_other b ON b.id = a.oid"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    assert _dens(c, "bg_x")["v"] == ac.PARTIAL
    tree.write(tree.layers / "L0_x", "q.ts",
               _cap("SELECT a.fact_id, a.signature_tier FROM t_x a JOIN t_other b ON b.id = a.oid"))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")["v"] == ac.PASS


def test_a_density_contract_named_in_a_string_is_not_a_declaration(tree, monkeypatch):
    """R232 carried into the repaired rule: a string that says `density_contract:` declares nothing."""
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id, signature_tier FROM t_x", contract=False).replace(
        "  run:", "  note: 'density_contract: pending',\n  run:"))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")["v"] == ac.FAIL


def test_the_availability_probe_catalogue_is_not_a_served_surface(tree, monkeypatch):
    """`retrieval/registry/knowledge/` mirrors a handler's own source query as a read-only availability probe: it serves
    no rows, so it neither blocks N/A nor counts as serving."""
    (tree.outside / "retrieval" / "registry" / "knowledge").mkdir(parents=True)
    tree.write(tree.outside / "retrieval" / "registry" / "knowledge", "source_query_availability.ts",
               _cap("SELECT id FROM t_x", contract=False))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")["v"] == ac.NA


def test_a_served_select_under_a_path_that_only_contains_the_word_knowledge_still_blocks_na(tree, monkeypatch):
    (tree.outside / "knowledge_base").mkdir()
    tree.write(tree.outside / "knowledge_base", "route.ts", _cap("SELECT id FROM t_x", contract=False))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")["v"] == ac.NO_DET


def test_a_qualified_tier_column_of_another_table_does_not_count_when_columns_are_known(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts",
               _cap("SELECT a.fact_id, b.signature_tier FROM t_x a JOIN t_other b ON b.id = a.oid"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": (["fact_id", "oid"], [])})
    assert _dens(c, "bg_x")["v"] == ac.PARTIAL


# ───────────────────────── SELECT * and run-time select lists: never guessed ─────────────────────────

def test_select_star_resolves_through_the_catalog_columns(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT * FROM t_x"))
    reg = {"bg_x": w1._reg_row("bg_x", "t_x")}
    assert _dens(_measure(monkeypatch, tree, reg, {"t_x": (["id", "signature_tier"], [])}), "bg_x")["v"] == ac.PASS
    assert _dens(_measure(monkeypatch, tree, reg, {"t_x": (["id", "v"], [])}), "bg_x")["v"] == ac.PARTIAL


def test_select_star_with_unknown_columns_is_not_a_pass(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT * FROM t_x"))
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.PARTIAL and "not established" in d["measured"], d


def test_a_run_time_select_list_does_not_hide_an_explicit_tier_column_but_never_implies_one(tree, monkeypatch):
    reg = {"bg_x": w1._reg_row("bg_x", "t_x")}
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT ${cols} FROM t_x"))
    assert _dens(_measure(monkeypatch, tree, reg), "bg_x")["v"] == ac.PARTIAL
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT ${cols}, signature_tier FROM t_x"))
    assert _dens(_measure(monkeypatch, tree, reg), "bg_x")["v"] == ac.PASS


# ───────────────────────── scope: each repaired path stops the asset reading N/A (R222's behavioural rule) ─────────────────────────

def test_a_reference_in_another_layer_directory_is_found(tree, monkeypatch):
    tree.write(tree.layers / "L3_y", "q.ts", _cap("SELECT id FROM t_x", contract=False))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")["v"] == ac.FAIL


def test_a_reference_in_a_file_at_the_layers_root_is_found(tree, monkeypatch):
    tree.write(tree.layers, "register_d7.ts", _cap("SELECT id FROM t_x", contract=False))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")["v"] == ac.FAIL


@pytest.mark.parametrize("where", ["tools", "lib"])
def test_an_mcp_only_reference_is_found_and_named_by_root(tree, monkeypatch, where):
    tree.write(getattr(tree, where), "tool.ts", _cap("SELECT id FROM t_x", contract=False))
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.FAIL and f"{getattr(tree, where)}/tool.ts" in d["measured"], d


def test_a_reference_through_a_count_sql_table_only_is_found(tree, monkeypatch):
    tree.write(tree.tools, "tool.ts", _cap("SELECT id, signature_tier FROM t_events"))
    reg = {"bg_x": w1._reg_row("bg_x", None, count_sql="SELECT count(*) FROM t_events")}
    assert _dens(_measure(monkeypatch, tree, reg), "bg_x")["v"] == ac.PASS


def test_a_registry_only_reference_with_a_served_select_is_found(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id, signature_tier FROM t_x"))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")["v"] == ac.PASS


# ───────────────────────── honest NO_DETECTOR and N/A ─────────────────────────

def test_a_comment_only_mention_is_no_detector_never_na(tree, monkeypatch):
    tree.write(tree.tools, "tool.ts", "// served elsewhere: t_x, bg_x\n/* density_contract: { } */\nexport {}\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.NO_DET and "comments only" in d["measured"], d


def test_no_reference_anywhere_in_the_scanned_roots_is_a_measured_na(tree, monkeypatch):
    tree.write(tree.tools, "tool.ts", _cap("SELECT id FROM unrelated"))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")["v"] == ac.NA


def test_a_code_reference_with_no_served_select_is_no_detector_not_fail(tree, monkeypatch):
    """An asset id in an array / registry list is a reference, not a served select: the scan cannot tell."""
    tree.write(tree.layers / "L0_x", "q.ts", "export const IDS = ['bg_x', 'bg_y']\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.NO_DET and "no served select" in d["measured"], d


def test_a_missing_root_is_no_detector_never_na(tree, monkeypatch):
    tree.lib.rmdir()
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.NO_DET and "never scanned" in d["measured"], d


def test_a_served_select_outside_the_serving_roots_keeps_the_asset_off_na(tree, monkeypatch):
    tree.write(tree.outside, "route.ts", _cap("SELECT id FROM t_x", contract=False))
    reg = {"bg_x": w1._reg_row("bg_x", "t_x")}
    d = _dens(_measure(monkeypatch, tree, reg, outside=True), "bg_x")
    assert d["v"] == ac.NO_DET and "outside the scanned serving roots" in d["measured"] and "route.ts" in d["measured"], d
    assert _dens(_measure(monkeypatch, tree, reg, outside=False), "bg_x")["v"] == ac.NA


def test_an_outside_reference_that_is_not_a_served_select_does_not_block_na(tree, monkeypatch):
    tree.write(tree.outside, "names.ts", "export const NAMES = { bg_x: 't_x' }\n")
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")["v"] == ac.NA


# ───────────────────────── shared tables: a reader of a shared table does not serve every asset ─────────────────────────

def test_a_shared_table_alone_never_attributes_a_serving_capability(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id, signature_tier FROM t_shared"))
    reg = {"bg_a": w1._reg_row("bg_a", "t_shared"), "bg_b": w1._reg_row("bg_b", "t_shared")}
    c = _measure(monkeypatch, tree, reg)
    for aid in reg:
        d = _dens(c, aid)
        assert d["v"] == ac.NO_DET and "shared" in d["measured"], (aid, d)


def test_the_asset_id_attributes_a_reader_of_a_shared_table(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id, signature_tier FROM t_shared WHERE k = 'bg_a'"))
    reg = {"bg_a": w1._reg_row("bg_a", "t_shared"), "bg_b": w1._reg_row("bg_b", "t_shared")}
    c = _measure(monkeypatch, tree, reg, {"t_shared": (["id", "signature_tier"], [])})
    assert _dens(c, "bg_a")["v"] == ac.PASS and _dens(c, "bg_b")["v"] == ac.NO_DET


# ───────────────────────── registry, rollup and the declared-rule door ─────────────────────────

def test_dens_served_criterion_revision_is_bumped_and_says_structural():
    e = ac.CRITERION_REGISTRY["Dens.served"]
    assert e["revision"] == 4 and "tier column" in e["applicability"], e


def test_na_rule_decisions_stays_empty_so_a_measured_dens_na_reads_no_detector_in_the_cell(tree, monkeypatch):
    assert ac.NA_RULE_DECISIONS == {}
    tree.write(tree.tools, "tool.ts", _cap("SELECT id FROM unrelated"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    assert _dens(c, "bg_x")["v"] == ac.NA
    cell = ac.rollup_asset("L0", next(a for a in c["assets"] if a["asset_id"] == "bg_x")["measurements"])["Dens"]
    assert cell["v"] == ac.NO_DET, cell


def test_the_legacy_call_shape_still_lists_modules_by_code(tmp_path):
    (tmp_path / "query_real.ts").write_text("export const c = query(`SELECT * FROM t_x`)\n", encoding="utf-8")
    (tmp_path / "query_comment.ts").write_text("// t_x\nexport {}\n", encoding="utf-8")
    cap = _REAL_SCAN(str(tmp_path), ["t_x", "bg_x"])
    assert cap["modules"] == ["query_real.ts"] and cap["comment_only"] == ["query_comment.ts"], cap


# ───────────────────────── review finding 1: a tier NAME inside an expression is not a tier COLUMN ─────────────────────────
# `_select_tier` used to credit any tier-named token anywhere in the select list. A column is carried only when a select
# ITEM is the column itself — `(qualifier.)?name`, optionally `::cast` and `AS alias`.

_FALSE_TIER_SHAPES = [
    ("count-distinct", "count(DISTINCT tier) AS n, id"),
    ("count-filter", "count(*) FILTER (WHERE tier = 'gold') AS n"),
    ("case-aliased-as-tier", "CASE WHEN score > 1 THEN 'hi' ELSE 'lo' END AS tier, id"),
    ("function-of-tier", "lower(signature_tier) AS s, id"),
    ("coalesce-of-tier", "coalesce(tier, 'x') AS tier"),
]


@pytest.mark.parametrize("sid, sel", _FALSE_TIER_SHAPES, ids=[s[0] for s in _FALSE_TIER_SHAPES])
@pytest.mark.parametrize("cols", [None, ["id", "score", "tier", "signature_tier"]], ids=["cols-unknown", "cols-known"])
def test_a_tier_name_inside_an_expression_is_never_a_tier_column(sid, sel, cols):
    st, got = ac._select_tier(sel, None, "t_x", cols)
    assert st != ac.TIER_YES and got == [], (sid, st, got)


def test_a_subselect_tier_is_never_credited_to_the_asset_table():
    """The scanner hands over the text after the LAST `SELECT`, so a sub-select's own list arrives truncated —
    `SELECT (SELECT tier FROM other) AS z, id FROM t_x` gives ` tier FROM other) AS z, id `. A FROM inside the list,
    with an unqualified name, cannot be attributed to the asset table: UNKNOWN, never YES."""
    for cols in (None, ["id", "tier"]):
        assert ac._select_tier(" tier FROM other) AS z, id ", None, "t_x", cols)[0] == ac.TIER_UNKNOWN
        assert ac._select_tier(" (SELECT tier FROM other) AS z, id ", None, "t_x", cols)[0] == ac.TIER_UNKNOWN


def test_an_unqualified_tier_when_the_asset_table_is_the_join_target_is_unknown_not_yes():
    """`SELECT tier FROM drv JOIN t_x`: the scanner's select list is ` tier FROM drv ` — the driving table has the
    column, the asset table is only joined."""
    for cols in (None, ["id", "tier"]):
        assert ac._select_tier(" tier FROM drv d ", "x", "t_x", cols)[0] == ac.TIER_UNKNOWN
    # qualified by the asset's own alias/table is still a real carry even with a FROM in the list
    assert ac._select_tier(" x.tier FROM drv d ", "x", "t_x", None) == (ac.TIER_YES, ["tier"])
    # qualified by the driving table is not the asset's
    assert ac._select_tier(" d.tier FROM drv d ", "x", "t_x", None)[0] == ac.TIER_NO


def test_the_false_tier_shapes_do_not_mint_pass_through_the_scan(tree, monkeypatch):
    """End to end (the scanner's own truncation and attribution, not a hand-fed list)."""
    reg = {"bg_x": w1._reg_row("bg_x", "t_x")}
    for sql in ("SELECT count(DISTINCT tier) AS n FROM t_x",
                "SELECT count(*) FILTER (WHERE tier = 'a') AS n FROM t_x",
                "SELECT CASE WHEN a THEN 1 END AS tier, id FROM t_x",
                "SELECT (SELECT tier FROM other) AS z, id FROM t_x",
                "SELECT tier FROM drv d JOIN t_x x ON x.id = d.xid"):
        tree.write(tree.layers / "L0_x", "q.ts", _cap(sql))
        d = _dens(_measure(monkeypatch, tree, reg), "bg_x")
        assert d["v"] != ac.PASS, (sql, d)


@pytest.mark.parametrize("sel", ["tier", "t_x.tier", "x.tier AS t", "signature_tier::text", "DISTINCT tier",
                                 "id, \"tier\"", "verification_pass_status", "a.id, x.indication_tier AS it"])
@pytest.mark.parametrize("cols", [None, ["id", "tier", "signature_tier", "verification_pass_status", "indication_tier"]],
                         ids=["cols-unknown", "cols-known"])
def test_a_plain_tier_column_item_still_counts(sel, cols):
    st, got = ac._select_tier(sel, "x", "t_x", cols)
    assert st == ac.TIER_YES and got, (sel, st, got)
