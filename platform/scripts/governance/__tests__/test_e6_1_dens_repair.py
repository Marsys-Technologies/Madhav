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
  N/A      no code reference anywhere, cause `no-served-surface` (measured; `NA_RULE_DECISIONS` stays empty, so the rollup
           reads NO_DETECTOR: an undeclared N/A is not N/A)

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
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT fact_id, tier FROM t_x", contract=False))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    d = _dens(c, "bg_x")
    assert d["v"] == ac.FAIL and "no referencing capability that serves it declares density_contract" in d["measured"], d


def test_the_contract_and_the_tier_column_must_sit_in_the_same_capability(tree, monkeypatch):
    """Per capability, not per file (N-22 §4 point 4): capability A declares the contract over a select with no tier
    column; capability B in the same file selects a tier column but declares no contract. The FILE has both halves; no
    capability has them together."""
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT fact_id FROM t_x", name="capA")
               + _cap("SELECT tier FROM t_x", contract=False, name="capB"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    d = _dens(c, "bg_x")
    assert d["v"] == ac.PARTIAL, d


def test_a_contract_in_a_capability_that_does_not_reference_the_asset_is_not_its_contract(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT fact_id FROM other_table", name="capA")
               + _cap("SELECT tier FROM t_x", contract=False, name="capB"))
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
               + _cap("SELECT id, tier FROM t_shared", contract=False, name="capB"))
    reg = {"bg_a": w1._reg_row("bg_a", "t_shared"), "bg_b": w1._reg_row("bg_b", "t_shared")}
    d = _dens(_measure(monkeypatch, tree, reg), "bg_a")
    assert d["v"] == ac.NO_DET and "no served select" in d["measured"], d


def test_a_contract_in_a_declaration_that_only_names_the_asset_id_is_not_its_serving_capability(tree, monkeypatch):
    """The contract sits in a capability that mentions `bg_x` in a string but serves no rows of its table, and nothing
    in the module selects from the table: there is no served select — never a PARTIAL (a contract is not credited to a
    capability that does not serve the table). REGISTRY_REVISION 14 (SS N-74(a)): the mention is a LABEL (prose under a
    non-label key, not SQL), so the module is not a reach and the asset reads the N/A with the label-only module named;
    before 14 this read NO_DETECTOR ("reach it by code, no served select"). A mention the scan cannot classify still reads
    NO_DETECTOR: see test_e6_dens_label_select.py."""
    tree.write(tree.tools, "tool.ts", "export const cap = {\n  " + CONTRACT + "\n  note: 'a note that covers bg_x for the reader of this page',\n}\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.NA and "only as a label" in d["measured"], d
    # a short embedded name is NOT recognised as a label by default (SS DENS review M1): the scan cannot tell, so NO_DETECTOR
    for body in ("note: 'covers bg_x',", "tags: ['bg_x'],"):
        tree.write(tree.tools, "tool.ts", "export const cap = {\n  " + CONTRACT + "\n  " + body + "\n}\n")
        d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
        assert d["v"] == ac.NO_DET and "no served select" in d["measured"], (body, d)


def test_a_contract_and_a_served_select_in_different_declarations_is_partial_with_that_reason(tree, monkeypatch):
    """A helper holds the SQL (with the tier column); the descriptor that declares the contract only calls it. The
    scan cannot attribute the select to the contract, so: PARTIAL, never PASS, and it says why."""
    tree.write(tree.tools, "tool.ts",
               "async function load() {\n  return query(`SELECT id, tier FROM t_x`)\n}\n"
               "export const cap = {\n  " + CONTRACT + "\n  note: 't_x',\n  run: () => load(),\n}\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.PARTIAL and "different top-level declaration" in d["measured"], d


def test_a_fail_names_a_contract_declared_elsewhere_in_the_module_so_the_limit_is_visible(tree, monkeypatch):
    """The descriptor that declares the contract never names the asset; a helper elsewhere in the file serves it. The
    verdict stays FAIL (no attribution), and the evidence says where a contract does sit — a reviewer sees the limit."""
    tree.write(tree.tools, "tool.ts",
               "export const cap = {\n  " + CONTRACT + "\n  run: () => other(),\n}\n"
               "async function other() {\n  return query(`SELECT id, tier FROM t_x`)\n}\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.FAIL and "declared in" in d["measured"] and "not in a capability that serves it" in d["measured"], d


@pytest.mark.parametrize("col, ok", [
    # DENS-TIER-GUARD (N-98, REGISTRY_REVISION 23): the vocabulary is CLOSED. `signature_tier` / `efficacy_tier` counted under the open `\w+_tier` regex (that
    # assertion is the one the guard reverses: they now count only when declared, test_e6_dens_tier_guard.py); `cost_tier` / `access_tier` never count.
    ("verification_pass_status", True), ("tier", True), ("signature_tier", False), ("efficacy_tier", False), ("cost_tier", False), ("access_tier", False),
    ("frontier", False), ("tiered_x", False), ("tier_note", False), ("confidence", False), ("fact_value", False),
])
def test_the_tier_column_vocabulary_is_exact(tree, monkeypatch, col, ok):
    tree.write(tree.layers / "L0_x", "q.ts", _cap(f"SELECT fact_id, {col} FROM t_x"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    assert (_dens(c, "bg_x")["v"] == ac.PASS) is ok, (col, _dens(c, "bg_x"))


def test_a_qualified_tier_column_of_another_table_does_not_count_when_columns_are_unknown_too(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts",
               _cap("SELECT a.fact_id, b.tier FROM t_x a JOIN t_other b ON b.id = a.oid"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    assert _dens(c, "bg_x")["v"] == ac.PARTIAL
    tree.write(tree.layers / "L0_x", "q.ts",
               _cap("SELECT a.fact_id, a.tier FROM t_x a JOIN t_other b ON b.id = a.oid"))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")["v"] == ac.PASS


def test_a_density_contract_named_in_a_string_is_not_a_declaration(tree, monkeypatch):
    """R232 carried into the repaired rule: a string that says `density_contract:` declares nothing."""
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id, tier FROM t_x", contract=False).replace(
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
               _cap("SELECT a.fact_id, b.tier FROM t_x a JOIN t_other b ON b.id = a.oid"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": (["fact_id", "oid"], [])})
    assert _dens(c, "bg_x")["v"] == ac.PARTIAL


# ───────────────────────── SELECT * and run-time select lists: never guessed ─────────────────────────

def test_select_star_resolves_through_the_catalog_columns(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT * FROM t_x"))
    reg = {"bg_x": w1._reg_row("bg_x", "t_x")}
    assert _dens(_measure(monkeypatch, tree, reg, {"t_x": (["id", "tier"], [])}), "bg_x")["v"] == ac.PASS
    assert _dens(_measure(monkeypatch, tree, reg, {"t_x": (["id", "v"], [])}), "bg_x")["v"] == ac.PARTIAL


def test_select_star_with_unknown_columns_is_not_a_pass(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT * FROM t_x"))
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.PARTIAL and "not established" in d["measured"], d


def test_a_run_time_select_list_does_not_hide_an_explicit_tier_column_but_never_implies_one(tree, monkeypatch):
    reg = {"bg_x": w1._reg_row("bg_x", "t_x")}
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT ${cols} FROM t_x"))
    assert _dens(_measure(monkeypatch, tree, reg), "bg_x")["v"] == ac.PARTIAL
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT ${cols}, tier FROM t_x"))
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
    tree.write(tree.tools, "tool.ts", _cap("SELECT id, tier FROM t_events"))
    reg = {"bg_x": w1._reg_row("bg_x", None, count_sql="SELECT count(*) FROM t_events")}
    assert _dens(_measure(monkeypatch, tree, reg), "bg_x")["v"] == ac.PASS


def test_a_registry_only_reference_with_a_served_select_is_found(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id, tier FROM t_x"))
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
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id, tier FROM t_shared"))
    reg = {"bg_a": w1._reg_row("bg_a", "t_shared"), "bg_b": w1._reg_row("bg_b", "t_shared")}
    c = _measure(monkeypatch, tree, reg)
    for aid in reg:
        d = _dens(c, aid)
        assert d["v"] == ac.NO_DET and "shared" in d["measured"], (aid, d)


def test_the_asset_id_attributes_a_reader_of_a_shared_table(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id, tier FROM t_shared WHERE k = 'bg_a'"))
    reg = {"bg_a": w1._reg_row("bg_a", "t_shared"), "bg_b": w1._reg_row("bg_b", "t_shared")}
    c = _measure(monkeypatch, tree, reg, {"t_shared": (["id", "tier"], [])})
    assert _dens(c, "bg_a")["v"] == ac.PASS and _dens(c, "bg_b")["v"] == ac.NO_DET


# ───────────────────────── registry, rollup and the declared-rule door ─────────────────────────

def test_dens_served_criterion_revision_is_bumped_and_says_structural():
    e = ac.CRITERION_REGISTRY["Dens.served"]
    assert e["revision"] == 7 and "tier column" in e["applicability"], e                 # 5: SS N-74(a), select vs label; 6: SS N-98, closed tier vocabulary; 7: TI-L0-04 (uniform_authority)


def test_an_undeclared_rule_leaves_a_measured_dens_na_reading_no_detector_in_the_cell(tree, monkeypatch):
    # REGISTRY_REVISION 9 declares Dens.served#measured:no-served-surface (SS N-65); this is the UNDECLARED path
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {})
    tree.write(tree.tools, "tool.ts", _cap("SELECT id FROM unrelated"))
    c = _measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")})
    assert _dens(c, "bg_x")["v"] == ac.NA
    cell = ac.rollup_asset("L0", next(a for a in c["assets"] if a["asset_id"] == "bg_x")["measurements"])["Dens"]
    assert cell["v"] == ac.NO_DET, cell
    chk = next(k for k in cell["checks"] if k["criterion"] == "Dens.served")
    assert chk["cause"] == "no-served-surface" and chk["rule_id"] == "Dens.served#measured:no-served-surface", chk
    # ... and with the approved rule declared (the production table) the same measurement reads N/A
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Dens.served#measured:no-served-surface": "N-22/N-22a row 19; N-65 (test)"})
    cell = ac.rollup_asset("L0", next(a for a in c["assets"] if a["asset_id"] == "bg_x")["measurements"])["Dens"]
    assert cell["v"] == ac.NA, cell


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
    ("function-of-tier", "lower(tier) AS s, id"),
    ("coalesce-of-tier", "coalesce(tier, 'x') AS tier"),
    ("tier-led-expression", "tier IS NOT NULL AS has_tier, id"),
    ("tier-concatenation", "tier || '-x' AS label"),
    ("tier-comparison", "tier = 'gold' AS is_gold"),
]


@pytest.mark.parametrize("sid, sel", _FALSE_TIER_SHAPES, ids=[s[0] for s in _FALSE_TIER_SHAPES])
@pytest.mark.parametrize("cols", [None, ["id", "score", "tier"]], ids=["cols-unknown", "cols-known"])
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


@pytest.mark.parametrize("sel", ["tier", "t_x.tier", "x.tier AS t", "tier::text", "DISTINCT tier",
                                 "id, \"tier\"", "verification_pass_status", "a.id, x.verification_pass_status AS it"])
@pytest.mark.parametrize("cols", [None, ["id", "tier", "verification_pass_status"]],
                         ids=["cols-unknown", "cols-known"])
def test_a_plain_tier_column_item_still_counts(sel, cols):
    st, got = ac._select_tier(sel, "x", "t_x", cols)
    assert st == ac.TIER_YES and got, (sel, st, got)


# ───────────────────────── review findings 3 and 4: test files are not a serving surface; constants and evidence text pinned ─────────────────────────

def test_test_files_and_tests_directories_are_excluded_from_the_serving_roots(tree, monkeypatch):
    """A `*.test.ts` or a file under `__tests__/` holding a contract plus a tier select is a fixture, not a capability:
    it must never mint PASS (nor count as a module reaching the asset)."""
    (tree.tools / "__tests__").mkdir()
    sql = "SELECT id, tier FROM t_x"
    tree.write(tree.tools / "__tests__", "x.ts", _cap(sql))
    tree.write(tree.tools, "x.test.ts", _cap(sql))
    tree.write(tree.layers / "L0_x" , "y.test.ts", _cap(sql))
    cap = _scan(tree, ["t_x", "bg_x"])
    assert cap["modules"] == [] and cap["density"] == 0, cap
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.NA, d          # nothing real reaches it: not a PASS, and not credited to a fixture
    # the same file OUTSIDE a tests path is a real capability
    tree.write(tree.tools, "x.ts", _cap(sql))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")["v"] == ac.PASS


def test_test_files_outside_the_serving_roots_do_not_block_na(tree, monkeypatch):
    (tree.outside / "__tests__").mkdir()
    tree.write(tree.outside / "__tests__", "route.ts", _cap("SELECT id FROM t_x", contract=False))
    tree.write(tree.outside, "route.test.tsx", _cap("SELECT id FROM t_x", contract=False))
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")["v"] == ac.NA


def test_the_wider_probe_covers_both_source_trees_including_the_mcp_server():
    """Constant pin: a probe that drops `platform-mcp/src` lets an asset served only there read N/A."""
    assert "platform-mcp/src" in ac.DENS_OUTSIDE_ROOTS and "platform/src" in ac.DENS_OUTSIDE_ROOTS
    assert ac.dens_tier_counts("verification_pass_status") and ac.dens_tier_counts("tier") and not ac.dens_tier_counts("evidence_tier")      # closed list (N-98)


def test_a_tier_column_without_a_contract_is_surfaced_in_the_fail_evidence(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT fact_id, tier FROM t_x", contract=False))
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.FAIL and "a tier column is selected without a contract in: L0_x/q.ts" in d["measured"], d


def test_a_fail_with_a_contract_elsewhere_in_the_module_names_where(tree, monkeypatch):
    tree.write(tree.tools, "tool.ts",
               "export const cap = {\n  " + CONTRACT + "\n  run: () => other(),\n}\n"
               "async function other() {\n  return query(`SELECT id FROM t_x`)\n}\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}), "bg_x")
    assert d["v"] == ac.FAIL and "a density_contract is declared in" in d["measured"] and "tool.ts" in d["measured"], d


# ───────────────────────── review findings 5 and 6: the outside probe never reads N/A on an unreadable or merely-named file ─────────────────────────
# A served select the string scanner cannot see must not be read as "no served select". An apostrophe in JSX text
# (`<p>don't</p>`) flips the scanner's string state for the rest of a `.tsx` file; a `FROM ${T}` names its table at
# run time. Both, and a comment that names the asset (R51), keep the asset off the closable N/A.

def _blocked(d):
    return d["v"] == ac.NO_DET and "outside the scanned serving roots" in d["measured"], d


def test_a_jsx_apostrophe_does_not_hide_a_later_served_select_behind_na(tree, monkeypatch):
    tree.write(tree.outside, "page.tsx",
               "export function P() {\n  return <p>don't</p>\n}\n"
               "export async function load() {\n  return query('SELECT id FROM t_x')\n}\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")
    assert _blocked(d)[0], d
    assert "page.tsx" in d["measured"], d


def test_any_textual_reference_in_a_tsx_file_blocks_na(tree, monkeypatch):
    """`.tsx` is not parsed reliably (JSX text): a bare reference is enough to keep the asset off N/A."""
    tree.write(tree.outside, "view.tsx", "export const V = () => <span>t_x</span>\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")
    assert _blocked(d)[0] and "view.tsx" in d["measured"], d


def test_a_ts_file_the_scanner_ends_desynced_on_is_a_textual_reference_not_a_miss(tree, monkeypatch):
    """A regex literal holding a quote opens a phantom string for the rest of the file; the scanner never sees the
    select. A desynced file falls back to the textual rule."""
    tree.write(tree.outside, "odd.ts",
               "const re = /'/;\nexport const q = () => query('SELECT id FROM t_x');\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")
    assert _blocked(d)[0] and "odd.ts" in d["measured"], d


def test_a_dynamic_table_name_in_a_file_that_holds_the_table_blocks_na(tree, monkeypatch):
    tree.write(tree.outside, "dyn.ts",
               "const T = 't_x';\nexport const q = () => query(`SELECT id FROM ${T} WHERE k = $1`);\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")
    assert _blocked(d)[0] and "dyn.ts" in d["measured"] and "run-time" in d["measured"], d


def test_a_dynamic_from_in_a_file_that_never_names_the_asset_does_not_block_na(tree, monkeypatch):
    tree.write(tree.outside, "dyn.ts", "export const q = (t: string) => query(`SELECT id FROM ${t}`);\n")
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")["v"] == ac.NA


@pytest.mark.parametrize("name", ["registry_data.ts", "types.tsx"])
def test_a_comment_naming_the_asset_outside_the_serving_roots_blocks_na_r51(tree, monkeypatch, name):
    """R51 on the outside probe: bg_vidhi_floors is named in a comment of platform/src/lib/vidhi/registry_data.ts and
    types.ts and served through platform-mcp/src/resources/vidhi — it must not read the closable N/A."""
    tree.write(tree.outside, name, "/**\n * seeded by `bg_x.py` (DB table t_x)\n */\nexport const X = 1\n")
    d = _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")
    assert _blocked(d)[0] and name in d["measured"], d


def test_a_comment_naming_the_asset_outside_the_roots_is_named_in_the_scan_result(tree):
    tree.write(tree.outside, "c.ts", "// served elsewhere: bg_x\nexport {}\n")
    cap = _scan(tree, ["t_x", "bg_x"], outside=True)
    assert cap["outside"] == [] and any("c.ts" in n for n in cap["outside_named"]), cap


def test_a_clean_ts_reference_that_is_neither_select_nor_comment_still_reads_na(tree, monkeypatch):
    """Unchanged: a names-map in a cleanly parsed `.ts` file holds no served select and no comment."""
    tree.write(tree.outside, "names.ts", "export const NAMES = { bg_x: 't_x' }\n")
    assert _dens(_measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, outside=True), "bg_x")["v"] == ac.NA


def test_a_known_catalog_that_lacks_the_named_column_does_not_credit_it():
    """With the table's columns known, a tier NAME that is not one of them (an alias, another table's column) counts
    for nothing."""
    assert ac._select_tier("tier", None, "t_x", ["id", "v"]) == (ac.TIER_NO, [])
    assert ac._select_tier("tier", None, "t_x", ["id", "tier"]) == (ac.TIER_YES, ["tier"])


def test_the_desync_detector_reads_quotes_newlines_and_comments():
    assert ac._ts_desynced("const a = 'x\n';\n")                       # a ' string across a raw newline
    assert ac._ts_desynced("const a = \"x\n\";\n")
    assert ac._ts_desynced("const a = `never closed\n")                # unterminated to EOF
    assert ac._ts_desynced("const re = /'/;\nquery('SELECT 1');\n")    # a stray quote
    assert not ac._ts_desynced("const a = 'it\\'s';\nconst b = `x\ny`;\n// it's a comment\n/* don't */\n")
    assert not ac._ts_desynced("")


# ───────────────────────── re-review: PASS is the closable direction (§N.8) — no false PASS, no false FAIL/N-A ─────────────────────────

def _cap_obj(body_sql, contract=True, name="a"):
    return (f"{{ id: '{name}', {CONTRACT if contract else ''} run: async () => query(`{body_sql}`) }}")


def _reg_x():
    return {"bg_x": w1._reg_row("bg_x", "t_x")}


# (1a) contract and tier select in one top-level declaration but DIFFERENT capability entries

def test_a_sibling_capability_in_the_same_array_does_not_lend_its_contract(tree, monkeypatch):
    """`register([A, B])`: A declares the contract (its select has no tier), B selects a tier column and declares
    nothing. One top-level declaration holds both halves; no capability ENTRY has them together."""
    tree.write(tree.layers / "L0_x", "q.ts",
               "export const caps = [\n  " + _cap_obj("SELECT id FROM t_x", name="a") + ",\n  "
               + _cap_obj("SELECT id, tier FROM t_x", contract=False, name="b") + ",\n]\n")
    d = _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")
    assert d["v"] == ac.PARTIAL and "no tier column" in d["measured"], d


def test_a_contract_in_one_entry_and_the_tier_select_in_a_sibling_of_another_asset_is_never_pass(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts",
               "export const caps = [\n  " + _cap_obj("SELECT id FROM other_table", name="a") + ",\n  "
               + _cap_obj("SELECT id, tier FROM t_x", contract=False, name="b") + ",\n]\n")
    d = _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")
    assert d["v"] == ac.PARTIAL and "different capability entry" in d["measured"], d


def test_each_entry_carrying_its_own_contract_and_tier_select_passes(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts",
               "export const caps = [\n  " + _cap_obj("SELECT id FROM other_table", name="a") + ",\n  "
               + _cap_obj("SELECT id, tier FROM t_x", name="b") + ",\n]\n")
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PASS


# (1b) a contract key whose value is undefined / null / false declares nothing

@pytest.mark.parametrize("val", ["undefined", "null", "false"])
def test_a_contract_key_with_no_real_value_is_not_a_declaration(tree, monkeypatch, val):
    body = ("export const cap = {\n  id: 'a',\n  density_contract: %s,\n  run: async () => query(`SELECT id, tier FROM t_x`),\n}\n" % val)
    tree.write(tree.layers / "L0_x", "q.ts", body)
    d = _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")
    assert d["v"] == ac.FAIL, (val, d)


@pytest.mark.parametrize("val", ["{ paginated: true }", "DENSITY", "buildContract()"])
def test_a_contract_key_with_an_object_or_identifier_value_is_a_declaration(tree, monkeypatch, val):
    body = ("export const cap = {\n  id: 'a',\n  density_contract: %s,\n  run: async () => query(`SELECT id, tier FROM t_x`),\n}\n" % val)
    tree.write(tree.layers / "L0_x", "q.ts", body)
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PASS


# (1c, 1d) only the served READ is credited: not a sub-select, an INSERT...SELECT or a UNION branch

@pytest.mark.parametrize("sql", [
    "SELECT id FROM other WHERE k IN (SELECT tier FROM t_x)",
    "INSERT INTO z (tier) SELECT tier FROM t_x",
    "WITH w AS (SELECT tier FROM t_x) SELECT id FROM w",
    "SELECT id FROM other UNION SELECT tier FROM t_x",
    "CREATE TABLE z AS SELECT tier FROM t_x",
], ids=["where-subselect", "insert-select", "cte-body", "union-branch", "create-as"])
def test_a_tier_column_outside_the_served_read_is_never_a_pass(tree, monkeypatch, sql):
    tree.write(tree.layers / "L0_x", "q.ts", _cap(sql))
    d = _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")
    assert d["v"] == ac.PARTIAL, (sql, d)


def test_the_outer_select_owns_its_from_even_with_a_subselect_in_its_list(tree, monkeypatch):
    """The FROM's own SELECT is the outer one (paren balance), so the select is the served read; a `(SELECT …)` in its
    list still makes the list unattributable (UNKNOWN -> PARTIAL, never PASS)."""
    sel = list(ac._served_selects("t_x", ["SELECT (SELECT max(v) FROM o) AS m, x.tier FROM t_x x"], strict=True))
    assert len(sel) == 1 and sel[0][3].startswith(" (SELECT max(v) FROM o) AS m"), sel
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT (SELECT max(v) FROM o) AS m, x.tier FROM t_x x"))
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PARTIAL


# (3) `SELECT` must be a whole word

@pytest.mark.parametrize("extra", ["is_selected", "reselect_count", "selected"])
def test_a_column_name_holding_select_does_not_truncate_the_select_list(tree, monkeypatch, extra):
    tree.write(tree.layers / "L0_x", "q.ts", _cap(f"SELECT id, tier, {extra} FROM t_x"))
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PASS
    assert [s.strip() for _i, _m, _a, s in ac._served_selects("t_x", [f"SELECT id, {extra} FROM t_x"])] == [f"id, {extra}"]


# (2) a run-time table name in every spelling

@pytest.mark.parametrize("frag", [
    "FROM \"${T}\"", "FROM public.${T}", "FROM public.\"${T}\"", "JOIN ${T}", "FROM ONLY ${T}",
])
def test_a_dynamic_table_name_in_any_spelling_blocks_na(tree, monkeypatch, frag):
    tree.write(tree.outside, "dyn.ts", "const T = 't_x';\nexport const q = () => query(`SELECT id FROM o %s WHERE k = $1`);\n" % frag
               if frag.startswith("JOIN") else "const T = 't_x';\nexport const q = () => query(`SELECT id %s WHERE k = $1`);\n" % frag)
    d = _dens(_measure(monkeypatch, tree, _reg_x(), outside=True), "bg_x")
    assert _blocked(d)[0] and "run-time" in d["measured"], (frag, d)


@pytest.mark.parametrize("src", [
    "const T = 't_x';\nexport const q = () => query('SELECT id FROM ' + T);\n",
    "const T = 't_x';\nexport const q = () => query('SELECT id FROM t_' + SUFFIX);\n",
    "const T = 't_x';\nexport const q = () => query('SELECT id ' + 'FROM ' + T + ' WHERE 1');\n",
])
def test_a_concatenated_table_name_blocks_na(tree, monkeypatch, src):
    tree.write(tree.outside, "dyn.ts", src)
    d = _dens(_measure(monkeypatch, tree, _reg_x(), outside=True), "bg_x")
    assert _blocked(d)[0] and "run-time" in d["measured"], (src, d)


# (4) a comment naming the asset + a code reference to the table

def test_a_comment_naming_the_asset_blocks_na_even_when_the_table_is_in_code(tree, monkeypatch):
    tree.write(tree.outside, "m.ts", "// serves bg_x\nexport const T = 't_x'\n")
    d = _dens(_measure(monkeypatch, tree, _reg_x(), outside=True), "bg_x")
    assert _blocked(d)[0] and "m.ts" in d["measured"], d


# (5) a desynced file INSIDE a serving root

def test_a_desynced_serving_root_file_that_names_the_asset_is_no_detector_never_fail(tree, monkeypatch):
    tree.write(tree.tools, "odd.ts", "const re = /'/;\n" + _cap("SELECT id, tier FROM t_x", contract=False))
    d = _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")
    assert d["v"] == ac.NO_DET and "odd.ts" in d["measured"] and "string scanner" in d["measured"], d


def test_a_desynced_file_never_mints_pass(tree, monkeypatch):
    tree.write(tree.tools, "odd.ts", "const re = /'/;\n" + _cap("SELECT id, tier FROM t_x"))
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.NO_DET


def test_a_clean_pass_stands_when_a_desynced_file_also_names_the_asset(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id, tier FROM t_x"))
    tree.write(tree.tools, "odd.ts", "const re = /'/;\nconst x = 't_x';\n")
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PASS


def test_a_desynced_file_that_never_names_the_asset_changes_nothing(tree, monkeypatch):
    tree.write(tree.tools, "odd.ts", "const re = /'/;\nconst x = 'unrelated';\n")
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id FROM t_x", contract=False))
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.FAIL


# (6) mutants that only a targeted fixture kills

def test_an_outside_root_that_overlaps_a_serving_root_adds_no_outside_tail(tree):
    tree.write(tree.layers / "L0_x", "q.ts", _cap("SELECT id, tier FROM t_x"))
    cap = _REAL_SCAN(tree.roots, ["t_x", "bg_x"], outside_roots=(str(tree.tmp),))
    assert cap["outside"] == [] and cap["outside_named"] == [], cap
    assert ac._grade_dens(cap, "t_x")["v"] == ac.PASS and "outside" not in ac._grade_dens(cap, "t_x")["measured"]


def test_the_outside_probe_reads_every_token_not_only_the_first(tree, monkeypatch):
    """The served select is of a `count_sql` table (a later token); the file also names the asset's own table."""
    tree.write(tree.outside, "r.ts", "const A = 't_x';\nexport const q = () => query('SELECT id FROM t_events');\n")
    reg = {"bg_x": w1._reg_row("bg_x", "t_x", count_sql="SELECT count(*) FROM t_events")}
    d = _dens(_measure(monkeypatch, tree, reg, outside=True), "bg_x")
    assert _blocked(d)[0] and "r.ts" in d["measured"], d


@pytest.mark.parametrize("src", ["// note {\nexport const a = 1\n", "/* note } */ export const a = 1\n", "// note {"])
def test_ts_mask_blanks_a_comment_to_its_last_character(src):
    m = ac._ts_mask(src)
    assert len(m) == len(src) and "{" not in m and "}" not in m, m


def test_a_comment_ending_in_a_brace_does_not_shift_the_declaration_boundaries(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts",
               "export const capA = { id: 'a', " + CONTRACT + " run: () => query(`SELECT id FROM t_x`) } // {\n"
               "export const capB = { id: 'b', run: () => query(`SELECT id, tier FROM t_x`) }\n")
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PARTIAL


@pytest.mark.parametrize("rel", ["a.d.ts", "node_modules/p/x.ts", "generated/g.ts"])
def test_declaration_files_node_modules_and_generated_code_do_not_block_na(tree, monkeypatch, rel):
    p = tree.outside / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_cap("SELECT id FROM t_x", contract=False), encoding="utf-8")
    assert _dens(_measure(monkeypatch, tree, _reg_x(), outside=True), "bg_x")["v"] == ac.NA


def test_the_tier_vocabulary_is_case_insensitive():
    for c in ("TIER", "Tier", "VERIFICATION_PASS_STATUS"):
        assert ac.dens_tier_counts(c), c
    assert ac._select_tier("Tier", None, "t_x", None)[0] == ac.TIER_YES
    assert ac._select_tier("Signature_Tier", None, "t_x", None)[0] == ac.TIER_NO          # N-98: closed list; only a declared name counts (test_e6_dens_tier_guard.py)


def test_a_from_literal_after_a_complete_select_is_not_a_select_list_for_it():
    """`'SELECT id, tier FROM other'` then `'FROM t_x'`: the second literal is prose/another clause; the first literal's
    SELECT already has its FROM."""
    assert list(ac._served_selects("t_x", ["SELECT id, tier FROM other ", "FROM t_x"])) == []
    assert [s for _i, _m, _a, s in ac._served_selects("t_x", ["SELECT id, tier ", "FROM t_x"])] == [" id, tier "]


def test_a_from_whose_select_is_unbalanced_is_not_borrowed_from_the_previous_literal():
    """`EXTRACT(year FROM t_x)` has a SELECT in its literal but none that owns the FROM; the previous literal's
    dangling SELECT is not its list either."""
    assert list(ac._served_selects("t_x", ["SELECT tier ", "SELECT EXTRACT(year FROM t_x) AS y"], strict=True)) == []


def test_a_literal_ending_in_from_is_dynamic_only_when_it_is_concatenated_on():
    def dyn(src):
        return ac._dynamic_from(src, ac._ts_literal_spans(src))
    assert dyn("const q = 'SELECT id FROM ' + T;\n")
    assert dyn("const q = 'SELECT id FROM '\n  + T;\n")
    assert not dyn("const q = 'SELECT id FROM';\nconst T = 't_x';\n")
    assert not dyn("const q = 'SELECT id FROM t_x' ;\n")
    assert dyn("const q = `SELECT id FROM public.${T}`;\n") and dyn("const q = `SELECT id FROM \"${T}\"`;\n")
    assert dyn("const q = `SELECT 1 FROM o JOIN ${T}`;\n") and dyn("const q = `SELECT 1 FROM ONLY ${T}`;\n")


# ───────────────────────── final review: SQL comments, split literals, more dynamic spellings, regex/contract edges ─────────────────────────

@pytest.mark.parametrize("sql", [
    "SELECT id FROM other WHERE k IN ( /* c */ SELECT id, tier FROM t_x)",
    "SELECT id FROM other WHERE k IN (-- c\nSELECT id, tier FROM t_x)",
    "SELECT id FROM other WHERE k IN (/* a */ /* b */\n  SELECT id, tier FROM t_x)",
    "INSERT INTO z (tier) /* c */ SELECT tier FROM t_x",
    "SELECT id FROM other UNION -- c\n SELECT tier FROM t_x",
], ids=["block-comment", "line-comment", "two-comments", "insert-comment", "union-comment"])
def test_a_sql_comment_does_not_hide_the_subselect_paren_or_write_prefix(tree, monkeypatch, sql):
    tree.write(tree.layers / "L0_x", "q.ts", _cap(sql))
    d = _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")
    assert d["v"] == ac.PARTIAL, (sql, d)


def test_a_comment_inside_the_select_owner_search_does_not_unbalance_it():
    """A `)` inside a SQL comment is not a paren."""
    sel = list(ac._served_selects("t_x", ["SELECT id, /* ) */ tier FROM t_x"], strict=True))
    assert len(sel) == 1 and sel[0][3] is not None and "tier" in sel[0][3], sel


@pytest.mark.parametrize("lits, served", [
    (["x IN (", "SELECT id, tier FROM t_x)"], False),                   # sub-select split across literals
    (["x IN (", "SELECT id, tier ", "FROM t_x)"], False),               # ... and the FROM split off too
    (["INSERT INTO z (a) ", "SELECT tier FROM t_x"], False),
    (["SELECT id FROM o UNION ", "SELECT tier FROM t_x"], False),
    (["x IN ( /* c */ ", "SELECT tier FROM t_x)"], False),
    (["SELECT id, tier ", "FROM t_x"], True),                           # the plain split select
    (["Create a chart", "SELECT id, tier FROM t_x"], True),             # an unrelated prose literal before it
    (["a", "SELECT id, tier ", "FROM t_x"], True),
], ids=["sub-split", "sub-split-from", "insert-split", "union-split", "comment-split", "plain-split", "prose-before", "plain-split-2"])
def test_a_select_at_the_start_of_a_literal_reads_its_context_from_the_previous_literal(lits, served):
    got = list(ac._served_selects("t_x", lits, strict=True))
    assert len(got) == 1, got
    assert (got[0][3] is not None) is served, got


def test_the_split_select_and_the_split_subselect_end_to_end(tree, monkeypatch):
    tree.write(tree.layers / "L0_x", "q.ts",
               "export const cap = {\n  id: 'a',\n  " + CONTRACT + "\n  run: () => query('SELECT id, tier ' + 'FROM t_x'),\n}\n")
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PASS
    tree.write(tree.layers / "L0_x", "q.ts",
               "export const cap = {\n  id: 'a',\n  " + CONTRACT + "\n  run: () => query('SELECT id FROM o WHERE k IN (' + 'SELECT id, tier FROM t_x)'),\n}\n")
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PARTIAL


# (2) more run-time table-name spellings

@pytest.mark.parametrize("src", [
    "export const q = () => query(`SELECT id FROM \"public\".\"${T}\"`);\n",
    "export const q = () => query('SELECT id FROM '.concat(T));\n",
    "export const q = () => query(['SELECT id FROM', T].join(' '));\n",
    "export const q = () => query(format('SELECT id FROM %I', T));\n",
    "export const q = () => query(format('SELECT id FROM public.%I WHERE k = %L', T, K));\n",
    "export const q = () => query('SELECT id FROM ' /* table */ + T);\n",
    "export const q = () => query('SELECT id FROM ' // table\n  + T);\n",
    "export const q = () => query('SELECT id FROM public.' + T);\n",
])
def test_more_dynamic_table_name_spellings_block_na(tree, monkeypatch, src):
    tree.write(tree.outside, "dyn.ts", "const T = 't_x';\n" + src)
    d = _dens(_measure(monkeypatch, tree, _reg_x(), outside=True), "bg_x")
    assert _blocked(d)[0] and "run-time" in d["measured"], (src, d)


def test_a_complete_table_name_that_is_not_concatenated_is_not_dynamic():
    def dyn(src):
        return ac._dynamic_from(src, ac._ts_literal_spans(src))
    assert not dyn("const a = ['SELECT id FROM t_x'];\n")
    assert not dyn("const a = format('no table here %I', T);\n")


# (4) contract regex and entry-span edges

@pytest.mark.parametrize("val", ["trueValue", "nullableContract", "falsey", "undefinedContract"])
def test_an_identifier_that_merely_starts_like_a_literal_is_a_real_contract_value(tree, monkeypatch, val):
    body = ("export const cap = {\n  id: 'a',\n  density_contract: %s,\n  run: async () => query(`SELECT id, tier FROM t_x`),\n}\n" % val)
    tree.write(tree.layers / "L0_x", "q.ts", body)
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PASS


def test_density_contract_true_is_not_a_declaration(tree, monkeypatch):
    body = ("export const cap = {\n  id: 'a',\n  density_contract: true,\n  run: async () => query(`SELECT id, tier FROM t_x`),\n}\n")
    tree.write(tree.layers / "L0_x", "q.ts", body)
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.FAIL


def test_enclosing_object_skips_nested_objects_on_both_sides():
    src = "x { a: { b: 1 }, k: 2, c: { d: { e: 3 } } } y"
    pos = src.index("k:")
    s, e = ac._enclosing_object(src, pos)
    assert src[s] == "{" and src[e - 1] == "}" and src[s:e] == "{ a: { b: 1 }, k: 2, c: { d: { e: 3 } } }", (s, e)
    assert ac._enclosing_object("no braces k: 1", 10) == (0, len("no braces k: 1"))


def test_a_nested_object_before_the_contract_key_does_not_hide_the_entry(tree, monkeypatch):
    body = ("export const caps = [\n"
            "  { id: 'a', meta: { x: { y: 1 } }, density_contract: { paginated: true }, run: async () => query(`SELECT id, tier FROM t_x`) },\n"
            "  { id: 'b', run: async () => query(`SELECT id FROM t_x`) },\n]\n")
    tree.write(tree.layers / "L0_x", "q.ts", body)
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PASS
    # the contract sits in entry B; A (with the tier select) has none
    body = ("export const caps = [\n"
            "  { id: 'a', meta: { x: { y: 1 } }, run: async () => query(`SELECT id, tier FROM t_x`) },\n"
            "  { id: 'b', meta: { z: 1 }, density_contract: { paginated: true }, run: async () => query(`SELECT id FROM t_x`) },\n]\n")
    tree.write(tree.layers / "L0_x", "q.ts", body)
    assert _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["v"] == ac.PARTIAL


def test_the_unparsed_message_names_the_real_causes(tree, monkeypatch):
    tree.write(tree.tools, "odd.ts", "const re = /'/;\n" + _cap("SELECT id FROM t_x", contract=False))
    m = _dens(_measure(monkeypatch, tree, _reg_x()), "bg_x")["measured"]
    assert "nested template literal" in m and "regex" in m and "unbalanced quote" in m and "odd.ts" in m, m


def test_a_word_from_inside_a_sql_comment_does_not_cancel_a_split_select():
    got = list(ac._served_selects("t_x", ["SELECT id, tier /* from elsewhere */ ", "FROM t_x"], strict=True))
    assert len(got) == 1 and got[0][3] is not None, got
    assert list(ac._served_selects("t_x", ["SELECT id FROM o ", "FROM t_x"], strict=True)) == []
