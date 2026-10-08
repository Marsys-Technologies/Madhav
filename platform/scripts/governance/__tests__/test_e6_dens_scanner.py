"""test_e6_dens_scanner.py: REGISTRY_REVISION 26 (Worker D, E5.7 engine-100), the Dens.served scanner repairs.

  (1) ONE real TypeScript lexer (`_ts_lex`): nested template literals (`${ ... `x` ... }`), regex literals holding a quote / bracket / `//`, comments. The four serving-root
      files the old quote loops lost sync on (registry_bridge.ts, register_p1_synthesis.ts, register_p1_ganita.ts, logger.ts) lex cleanly; a file that really does not close
      (an unclosed template / `${` / block comment, a `'` string across a newline) is STILL desynced and grades NO_DETECTOR naming it, never PASS / FAIL / N/A.
  (2) `_dynamic_from` no longer reads lower-case prose ("isolated from generation",) as a run-time table name.
  (3) `FROM ${TABLE_BY_TIER[tier]}` is read through the module's own const string map (a select the asset's table can take); a parameter / computed map stays unread.
  (4) `density_facet` (a DECLARATION): a shared-table select is attributed to the asset only when the same top-level declaration pins a declared facet value.
  Plus the real census scan inputs (no database): the exact cells that move.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_e6_dens_scanner.py -v
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_1_dens_repair as dr  # noqa: E402

tree = dr.tree
SCAN = dr._REAL_SCAN
NO_DET, FAIL, PARTIAL, PASS, NA = ac.NO_DET, ac.FAIL, ac.PARTIAL, ac.PASS, ac.NA
REPO = HERE.parents[3]


def _scan(tree, toks, outside=False, **kw):
    if outside:
        kw["outside_roots"] = (str(tree.outside),)
    return SCAN(tree.roots, list(toks), **kw)


# ───────────────────────── (1) the lexer ─────────────────────────

@pytest.mark.parametrize("src", [
    "const a = `x ${cond ? `y '${z}'` : ''} don't`;\nquery('SELECT 1');\n",                                  # nested template, quotes inside
    "const m = `a ${b.map((x) => `<${x}>`).join(',')} c`;\nconst n = 'it';\n",                              # template in an arrow in an interpolation
    "const r = v.replace(/(api[_-]?key=)[^&\\s\"'\\\\]+/gi, '$1');\nconst s = 'x';\n",                          # the logger.ts regex: quotes in a class
    "const r = /https?:\\/\\//.test(u);\nconst s = \"it's\";\n",                                                 # `//` inside a regex
    "const r = /[/'\"]/g;\nconst s = 'x';\n",                                                                  # a `/` inside a class
    "const q = x.split(/\\s*,\\s*/);\nconst t = `a`;\n",
    "const h = (a + b) / 2 / c;\nconst s = 'ok';\n",                                                           # division, not a regex
    "const d = a / b; const e = 'q'; // a don't comment\n",
    "const f = `a ${ /* it's */ x } b`;\nconst g = 1;\n",
])
def test_clean_sources_lex_without_desync(src):
    assert not ac._ts_desynced(src)
    assert len(ac._ts_mask(src)) == len(src) == len(ac._ts_mask(src, blank_strings=True))


@pytest.mark.parametrize("src", [
    "const a = 'x\n';\n",                                   # a ' string across a raw newline
    "const a = `never closed\n",                           # an unclosed template
    "const a = `x ${ y \n",                                # an unclosed interpolation
    "const a = `x ${ 'unclosed } z`;\n",                   # a string never closed inside an interpolation
    "/* never closed\nconst a = 1;\n",                     # an unclosed block comment
    "if (x) /'/.test(y);\nquery('SELECT 1');\n",           # a regex after `)`: read as division, so its stray quote desyncs (the safe direction)
    "<p>don't</p>;\nconst a = 'b\n';\n",                   # a stray apostrophe
])
def test_unparseable_sources_stay_desynced(src):
    assert ac._ts_desynced(src)


def test_a_nested_template_is_one_literal_and_its_quotes_do_not_leak():
    src = "const a = `x ${c ? `y` : 'z'} w`;\nconst b = 'SELECT 1';\n"
    spans = ac._ts_literal_spans(src)
    assert [c for _p, c in spans] == ["x ${c ? `y` : 'z'} w", "SELECT 1"]
    assert "'z'" not in ac._ts_mask(src, blank_strings=True)         # the whole template body is blanked


def test_a_regex_body_is_blanked_but_a_division_is_not():
    src = "const r = /[(\"']/g; const x = a / b;\n"
    blank = ac._ts_mask(src, blank_strings=True)
    assert "(" not in blank and "'" not in blank and "a / b" in blank
    assert ac._ts_literal_spans(src) == []                           # a regex is not a string literal


def test_comments_are_still_masked_in_place():
    src = "a // it's\nb /* c */ d\n"
    assert ac._ts_mask(src) == "a " + " " * 7 + "\nb " + " " * 7 + " d\n"


@pytest.mark.parametrize("rel", ["platform-mcp/src/tools/registry_bridge.ts", "platform-mcp/src/tools/register_p1_synthesis.ts",
                                 "platform-mcp/src/tools/register_p1_ganita.ts", "platform-mcp/src/lib/logger.ts"])
def test_the_four_files_the_old_scanner_lost_sync_on_now_lex_cleanly(rel):
    txt = (REPO / rel).read_text(encoding="utf-8")
    assert not ac._ts_desynced(txt), rel
    assert ac._ts_literal_spans(txt), rel


def test_a_registry_bridge_shaped_module_is_graded_not_unparsed(tree):
    """Nested template + a regex with quotes + a served select under a contract-less declaration: FAIL (read), never NO_DETECTOR (unparsed)."""
    tree.write(tree.tools, "bridge.ts",
               "const redact = (s: string) => s.replace(/(key=)[^&\\s\"'\\\\]+/gi, '$1')\n"
               "export const note = `a ${ok ? `it's` : `no`} b`\n"
               "export const h = { run: async () => query(`SELECT id FROM t_x WHERE a = $1`) }\n")
    cap = _scan(tree, ["t_x", "bg_x"])
    assert cap["unparsed"] == [] and cap["served"] == 1
    assert ac._grade_dens(cap, "t_x")["v"] == FAIL


def test_a_module_that_really_does_not_close_stays_no_detector_naming_the_file(tree):
    tree.write(tree.tools, "broken.ts", "const a = `never closed ${ x\nconst t = 't_x'\n")
    cap = _scan(tree, ["t_x", "bg_x"])
    g = ac._grade_dens(cap, "t_x")
    assert cap["unparsed"] == ["mcp_tools/broken.ts"] or [u.endswith("broken.ts") for u in cap["unparsed"]] == [True]
    assert g["v"] == NO_DET and "broken.ts" in g["measured"] and "lose the string scanner's sync" in g["measured"]


# ───────────────────────── (2) prose is not a run-time table name ─────────────────────────

def test_lower_case_from_in_prose_followed_by_a_property_comma_is_not_a_dynamic_table():
    src = "export const A = {\n  d: 'held-out, isolated from generation',\n  layer: 'L5',\n}\n"
    assert not ac._dynamic_from(src, ac._ts_literal_spans(src))
    src2 = "const x = `Rows from ${n} sources`\n"
    assert not ac._dynamic_from(src2, ac._ts_literal_spans(src2))


@pytest.mark.parametrize("src", [
    "const q = `SELECT a FROM ${t} WHERE x`\n",
    "const q = 'SELECT a ' + 'FROM ' + t\n",
    "const q = `select a from ${t}`\n",                           # lower-case SQL: a SELECT in the literal makes it SQL
    "const q = ['SELECT a FROM', t]\n",
])
def test_real_dynamic_selects_are_still_dynamic(src):
    assert ac._dynamic_from(src, ac._ts_literal_spans(src))


def test_a_catalogue_file_naming_a_table_beside_prose_from_does_not_block_the_n_a(tree):
    tree.write(tree.outside, "names.ts", "export const A = {\n  bg_x: { table: 't_x', d: 'held-out, isolated from generation',\n  layer: 'L5' },\n}\n")
    cap = _scan(tree, ["t_x", "bg_x"], outside=True)
    assert ac._grade_dens(cap, "t_x")["v"] == NA


# ───────────────────────── (3) a table name read through the module's own const map ─────────────────────────

MAPPED = """
const TABLE_BY_TIER: Record<string, string> = {
  summary: 't_x',
  other: 't_other',
}
export const cap = {
  id: 'cap',
  density_contract: { paginated: true, facets: [], empty_reason: true },
  run: async (tier: string) => {
    const table = TABLE_BY_TIER[tier]
    return query(`SELECT id, tier FROM ${table} WHERE chart_id = $1`)
  },
}
"""


def test_a_select_from_a_const_map_entry_is_a_served_select_of_that_table(tree):
    tree.write(tree.layers / "L0_x", "q.ts", MAPPED)
    cap = _scan(tree, ["t_x", "bg_x"], columns={"t_x": ["id", "tier"]})
    g = ac._grade_dens(cap, "t_x")
    assert cap["served"] == 1 and cap["dynamic_resolved"] and g["v"] == PASS, g
    assert "resolved from a module const map" in g["measured"]


def test_a_map_select_without_a_tier_in_the_list_is_partial_not_pass(tree):
    tree.write(tree.layers / "L0_x", "q.ts", MAPPED.replace("SELECT id, tier", "SELECT id"))
    g = ac._grade_dens(_scan(tree, ["t_x", "bg_x"], columns={"t_x": ["id", "tier"]}), "t_x")
    assert g["v"] == PARTIAL


def test_a_run_time_select_list_over_the_map_stays_unknown_never_pass(tree):
    tree.write(tree.layers / "L0_x", "q.ts", MAPPED.replace("SELECT id, tier", "SELECT ${COLS[tier]}"))
    g = ac._grade_dens(_scan(tree, ["t_x", "bg_x"], columns={"t_x": ["id", "tier"]}), "t_x")
    assert g["v"] == PARTIAL and "tier carriage not established" in g["measured"]


@pytest.mark.parametrize("variant", [
    MAPPED.replace("'t_x'", "name_of(x)"),                                        # a computed entry: the set of names is unreadable
    MAPPED.replace("const table = TABLE_BY_TIER[tier]", "const table = pick(tier)"),   # a call
    MAPPED.replace("const table = TABLE_BY_TIER[tier]", "const table = arg"),           # a parameter
    MAPPED.replace("summary: 't_x',", "summary: 't_y',"),                          # the map does not hold the asset's table
])
def test_an_unreadable_or_foreign_table_name_is_never_attributed(tree, variant):
    tree.write(tree.layers / "L0_x", "q.ts", variant)
    cap = _scan(tree, ["t_x", "bg_x"], columns={"t_x": ["id", "tier"]})
    assert cap["served"] == 0 and not cap["dynamic_resolved"]
    assert ac._grade_dens(cap, "t_x")["v"] in (NO_DET, NA)


def test_a_direct_const_string_table_is_read(tree):
    tree.write(tree.layers / "L0_x", "q.ts", "const T = 't_x'\nexport const cap = {\n  density_contract: { paginated: true, facets: [], empty_reason: true },\n"
                                              "  run: () => query(`SELECT id, verification_pass_status FROM ${T}`),\n}\n")
    g = ac._grade_dens(_scan(tree, ["t_x", "bg_x"], columns={"t_x": ["id", "verification_pass_status"]}), "t_x")
    assert g["v"] == PASS


# ───────────────────────── (4) the declared facet of a shared table ─────────────────────────

FACETED = """
export const cap = {
  id: 'cap',
  density_contract: { paginated: true, facets: [], empty_reason: true },
  run: async () => {
    const filters = ["chart_id = $1", "%s"]
    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE ${filters.join(' AND ')}`)
  },
}
"""
SHARED_COLS = {"t_shared": ["fact_id", "fact_category", "verification_pass_status"]}
FACET = {"t_shared": dict(column="fact_category", values=["ayurdaya"])}


def _faceted(tree, pred, facets=FACET):
    tree.write(tree.layers / "L0_x", "q.ts", FACETED % pred)
    cap = _scan(tree, ["t_shared", "bg_x"], shared={"t_shared"}, columns=SHARED_COLS, facets=facets)
    return ac._grade_dens(cap, "t_shared"), cap


@pytest.mark.parametrize("pred", ["fact_category = 'ayurdaya'", "fact_category IN ('ayurdaya')", "fact_category = ANY(ARRAY['ayurdaya'])",
                                  "fact_category = ANY('{ayurdaya}')", "f.fact_category = 'ayurdaya'"])
def test_a_pinned_declared_facet_value_attributes_the_shared_select_and_can_pass(tree, pred):
    g, cap = _faceted(tree, pred)
    assert g["v"] == PASS and cap["facet_attributed"], g
    assert "attributed by the declared facet" in g["measured"]


@pytest.mark.parametrize("pred", ["fact_category = 'other'", "fact_category IN ('x', 'ayurdaya')", "fact_category = ANY('{ayurdaya,z}')", "fact_category <> 'ayurdaya'", "fact_category NOT IN ('ayurdaya')",
                                  "fact_category = '${cat}'", "fact_category = $2", "fact_category = ANY($2)", "chart_id = $1"])
def test_a_predicate_that_does_not_pin_a_declared_value_attributes_nothing(tree, pred):
    g, cap = _faceted(tree, pred)
    assert g["v"] == NO_DET and not cap["facet_attributed"], (pred, g)


def test_a_bind_parameter_facet_is_reported_and_credits_nothing(tree):
    g, cap = _faceted(tree, "fact_category = ANY($2)")
    assert g["v"] == NO_DET and cap["facet_bound"] and "never guessed" in g["measured"]


def test_no_declared_facet_means_no_attribution_the_old_reading(tree):
    g, cap = _faceted(tree, "fact_category = 'ayurdaya'", facets=None)
    assert g["v"] == NO_DET and "only a table other assets share" in g["measured"]


def test_the_facet_pins_the_declaration_of_the_select_not_a_neighbouring_one(tree):
    tree.write(tree.layers / "L0_x", "q.ts",
               "export const a = { run: () => query(`SELECT fact_id FROM t_shared WHERE chart_id = $1`) }\n"
               "export const b = { run: () => query(`SELECT 1 WHERE fact_category = 'ayurdaya'`) }\n")
    cap = _scan(tree, ["t_shared", "bg_x"], shared={"t_shared"}, columns=SHARED_COLS, facets=FACET)
    assert not cap["facet_attributed"]


def test_a_facet_attributed_select_without_a_contract_is_fail_not_n_a_or_pass(tree):
    tree.write(tree.layers / "L0_x", "q.ts", FACETED.replace("  density_contract: { paginated: true, facets: [], empty_reason: true },\n", "") % "fact_category = 'ayurdaya'")
    g = ac._grade_dens(_scan(tree, ["t_shared", "bg_x"], shared={"t_shared"}, columns=SHARED_COLS, facets=FACET), "t_shared")
    assert g["v"] == FAIL


# ───────────────────────── the facet declaration itself ─────────────────────────

EV = "platform/src/lib/retrieval/registry/layers/L1_ganita/get_ayurdaya.ts:71"


def _entry(**over):
    d = dict(column="fact_category", values=["ayurdaya"], why="these chart_facts rows are the ayurdaya writer's own category", evidence=EV)
    d.update(over)
    return {"density_facet": d}


def test_a_sound_facet_declaration_is_accepted():
    assert ac.density_facet_problem(_entry()) is None
    assert ac.density_facet_problem({}) is None
    assert ac.density_facet_problem(_entry(), ["fact_category", "fact_id"]) is None


@pytest.mark.parametrize("over,needle", [
    (dict(column="fact category"), "column name"),
    (dict(values=[]), "values"),
    (dict(values=["a", "a"]), "values"),
    (dict(values=["it's"]), "values"),
    (dict(values=["${x}"]), "values"),
    (dict(why="short"), "why"),
    (dict(evidence="unverified:somewhere i looked"), "unverified"),
    (dict(evidence="platform/src/nope.ts:1"), "evidence"),
    (dict(evidence="platform/src/lib/retrieval/registry/layers/L1_ganita/get_ayurdaya.ts"), "line"),
    (dict(values=["not_in_that_file_zzz"]), "does not mention the declared value"),
    (dict(column="fact_subject_zzz"), "does not mention"),
])
def test_an_unsound_facet_declaration_is_refused(over, needle):
    bad = ac.density_facet_problem(_entry(**over))
    assert bad and needle in bad, bad


def test_a_facet_on_a_column_the_table_lacks_or_with_an_unknown_field_is_refused():
    assert "not a column" in ac.density_facet_problem(_entry(), ["fact_id"])
    e = _entry()
    e["density_facet"]["extra"] = 1
    assert "unknown field" in ac.density_facet_problem(e)
    assert "unverifiable" in ac.density_facet_measure_problem(_entry(), None, None)
    assert "unverifiable" in ac.density_facet_measure_problem(_entry(), "t", None)


def test_the_declarations_validator_runs_the_facet_check():
    assert "density_facet" in ac._DECL_ENTRY_KEYS
    with pytest.raises(ac.DeclarationsError):
        ac.validate_density_facet_declaration("assets['x']", _entry(why="x"))


# ───────────────────────── the real census scan inputs (no database) ─────────────────────────

FX = json.loads((HERE / "fixtures" / "dens_scan_inputs_2026-10-02.json").read_text(encoding="utf-8"))
LAYERS = ("L0", "L1", "L2")


@pytest.fixture(scope="module")
def real():
    rd, cache = pathlib.Path.read_text, {}

    def cached(self, *a, **k):
        key = (str(self), a, tuple(sorted(k.items())))
        if key not in cache:
            cache[key] = rd(self, *a, **k)
        return cache[key]
    pathlib.Path.read_text = cached
    out = {}
    try:
        for L in LAYERS:
            d = FX["layers"][L]
            for r in d["assets"]:
                cap = ac.capability_scan(ac.CAPS_ROOTS, r["tokens"], shared=frozenset(d["shared"]), columns=d["columns"],
                                         outside_roots=ac.DENS_OUTSIDE_ROOTS, service=(r.get("asset_kind") == "service"))
                out[r["asset_id"]] = (L, ac._grade_dens(cap, r["target_table"] or r["asset_id"]), cap)
    finally:
        pathlib.Path.read_text = rd
    return out


def _counts(real, L):
    c = {}
    for _a, (l, g, _cap) in real.items():
        if l == L:
            c[g["v"]] = c.get(g["v"], 0) + 1
    return c


def test_no_serving_root_file_is_desynced_and_no_asset_reads_the_unparsed_message(real):
    assert all(not cap["unparsed"] for _l, _g, cap in real.values())
    assert not any("lose the string scanner's sync" in g["measured"] for _l, g, _c in real.values())


def test_the_cells_that_move_are_exactly_the_ones_the_repair_reads(real):
    # DENS-SERVED: the serving capabilities of ga_structural and bo_upaya now declare their contract over the tier they already selected, so those two read PASS (they
    # read FAIL when the lexer first read their files); bo_bimba / bo_karanajala (selects live in helper functions outside the contract's entry) and bo_samvada (a view) still read FAIL.
    assert real["bo_samvada"][1]["v"] == FAIL and real["bo_samvada"][2]["served"] > 0                # a view: still a read FAIL
    # SS N-212 (a): traverse_chart_graph declares its contract and its recursive-CTE node select lists n.verification_pass_status (a UNION inside the CTE's parentheses is not a set operation on the
    # statement): bo_bimba reads PASS
    assert real["bo_bimba"][1]["v"] == PASS and real["bo_bimba"][2]["served"] > 0
    assert real["bo_karanajala"][1]["v"] == PARTIAL and real["bo_karanajala"][2]["served"] > 0       # in this fixture its tokens do not include bodha_cgm_nodes; the contract entry now counts it
    for a in ("bo_upaya", "ga_structural"):
        assert real[a][1]["v"] == PASS and real[a][2]["served"] > 0, a
    # DENS-SERVED: bo_cdlm_summary's const-map select lists all carry verification_pass_status (_select_tier_resolved), so its contract reads PASS
    assert real["bo_cdlm_summary"][1]["v"] == PASS and real["bo_cdlm_summary"][2]["dynamic_resolved"]
    assert _counts(real, "L0") == {FAIL: 4, NO_DET: 12, PARTIAL: 19, NA: 5}      # SS N-236 (function-entry helper credit): bg_gochara_citation_resolution FAIL -> PARTIAL (its served select is in fetchMitigation, called in the body of the function that returns the contract object; no tier column in the table); DENS-SERVED: 13 L0 FAIL read PARTIAL (the contracts their query capabilities now declare; no tier column in these tables)
    assert _counts(real, "L1") == {NO_DET: 8, PARTIAL: 8, PASS: 3}                  # DENS-SERVED: ga_structural FAIL -> PASS, ga_vargas PARTIAL -> PASS (get_divisionals declares its contract over SELECT *)
    assert _counts(real, "L2") == {PARTIAL: 6, NO_DET: 9, FAIL: 1, PASS: 7}    # DENS-SERVED: bo_cgm_motifs / bo_cgm_paths / bo_upaya / bo_sangati / bo_cdlm_summary read PASS; bo_pramana_mapa FAIL -> PARTIAL; bo_samvada / bo_bimba / bo_karanajala stay FAIL


def test_the_shared_table_cells_name_the_real_cause_not_a_dynamic_table_false_positive(real):
    for a in ("bg_ontology", "bg_text_index", "ga_panchanga"):
        assert real[a][1]["v"] == NO_DET and "only a table other assets share" in real[a][1]["measured"], a


# ───────────────────────── independent-review fixes (PR #3176): MED-1, MED-2, MED-3, LOW-4, LOW-5 ─────────────────────────

TWO_TOOLS = """
export function registerAll(r) {
  r.register({
    id: 'A',
    density_contract: { paginated: true, facets: [], empty_reason: true },
    run: async () => query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE chart_id = $1 AND fact_category = 'dasha'`),
  })
  r.register({
    id: 'B',
    run: async () => query(`SELECT fact_id FROM t_shared WHERE chart_id = $1 AND %s`),
  })
}
"""


def _two(tree, b_pred, facets=FACET):
    tree.write(tree.layers / "L0_x", "q.ts", TWO_TOOLS % b_pred)
    cap = _scan(tree, ["t_shared", "bg_x"], shared={"t_shared"}, columns=SHARED_COLS, facets=facets)
    return ac._grade_dens(cap, "t_shared"), cap


def test_med1_a_facet_literal_in_tool_b_does_not_credit_tool_as_contract_entry(tree):
    """The review's shape: tool A's contract entry selects a tier from chart_facts for fact_category='dasha'; tool B (same register function) pins 'ayurdaya'.
    Only B's own select is the asset's; A's select credits nothing, so there is no PASS (the contract and a tier select are not in one attributed entry)."""
    g, cap = _two(tree, "fact_category = 'ayurdaya'")
    assert g["v"] != PASS, g
    assert cap["served"] == 1 and cap["density"] == 0, cap                    # only B's select is attributed
    assert cap["facet_attributed"]


@pytest.mark.parametrize("pred", ["fact_category IN ('x', 'ayurdaya')", "fact_category = 'ayurdaya' OR fact_category = 'dasha'", "fact_category = 'ayurdaya' OR 1 = 1",
                                  "fact_category = ANY(ARRAY['ayurdaya', 'dasha'])"])
def test_med1_a_pin_that_is_not_wholly_declared_or_sits_beside_an_or_attributes_nothing(tree, pred):
    g, cap = _two(tree, pred)
    assert cap["served"] == 0 and not cap["facet_attributed"], (pred, cap)
    assert g["v"] == NO_DET, g


def test_med1_the_attributed_select_in_its_own_contract_entry_still_passes(tree):
    tree.write(tree.layers / "L0_x", "q.ts", TWO_TOOLS.replace("fact_category = 'dasha'", "fact_category = 'ayurdaya'").replace("%s", "fact_category = 'ayurdaya'"))
    g = ac._grade_dens(_scan(tree, ["t_shared", "bg_x"], shared={"t_shared"}, columns=SHARED_COLS, facets=FACET), "t_shared")
    assert g["v"] == PASS, g


def test_med1_two_selects_in_one_entry_each_judged_on_its_own_pin(tree):
    """Re-check MED: attribution is per SELECT. One entry: select 1 pins the declared value, select 2 pins an undeclared one: only select 1 is the asset's."""
    tree.write(tree.layers / "L0_x", "q.ts", "export const cap = {\n  id: 'c',\n  density_contract: { paginated: true, facets: [], empty_reason: true },\n"
                                              "  run: async () => { await query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE fact_category = 'ayurdaya'`); "
                                              "return query(`SELECT fact_id FROM t_shared WHERE fact_category = 'dasha'`) },\n}\n")
    cap = _scan(tree, ["t_shared", "bg_x"], shared={"t_shared"}, columns=SHARED_COLS, facets=FACET)
    assert cap["facet_attributed"] == ["L0_x/q.ts"] and cap["served"] == 1


def test_recheck_an_unpinned_select_in_an_entry_with_a_pinned_one_is_not_attributed_and_cannot_supply_the_tier(tree):
    """The re-check's shape: the entry holds a pinned select (no tier column) and an UNPINNED select of the shared table that carries the tier. The unpinned one must not be attributed,
    so the contract + tier cannot be assembled from it: no PASS."""
    tree.write(tree.layers / "L0_x", "q.ts", "export const cap = {\n  id: 'c',\n  density_contract: { paginated: true, facets: [], empty_reason: true },\n"
                                              "  run: async () => { await query(`SELECT fact_id FROM t_shared WHERE fact_category = 'ayurdaya'`); "
                                              "return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE chart_id = $1`) },\n}\n")
    cap = _scan(tree, ["t_shared", "bg_x"], shared={"t_shared"}, columns=SHARED_COLS, facets=FACET)
    assert cap["served"] == 1 and cap["density"] == 0, cap
    assert ac._grade_dens(cap, "t_shared")["v"] != PASS


def test_recheck_a_dynamic_where_takes_its_pin_only_from_a_standalone_filter_literal(tree):
    """`WHERE ${where}` with the pin in a standalone filters literal (the real get_ayurdaya shape) is attributed; the same select with the pin only inside ANOTHER select is not."""
    ok = ("export const cap = {\n  id: 'c',\n  run: async () => { const filters = [\"chart_id = $1\", \"fact_category = 'ayurdaya'\"]; const where = filters.join(' AND ');\n"
          "    return query(`SELECT fact_id FROM t_shared WHERE ${where}`) },\n}\n")
    tree.write(tree.layers / "L0_x", "q.ts", ok)
    assert _scan(tree, ["t_shared", "bg_x"], shared={"t_shared"}, columns=SHARED_COLS, facets=FACET)["facet_attributed"] == ["L0_x/q.ts"]
    bad = ("export const cap = {\n  id: 'c',\n  run: async () => { await query(`SELECT fact_id FROM t_shared WHERE fact_category = 'ayurdaya'`);\n"
           "    return query(`SELECT fact_id FROM t_shared WHERE ${where}`) },\n}\n")
    tree.write(tree.layers / "L0_x", "q.ts", bad)
    cap = _scan(tree, ["t_shared", "bg_x"], shared={"t_shared"}, columns=SHARED_COLS, facets=FACET)
    assert cap["served"] == 1, cap                                  # only the inline-pinned select; the dynamic one borrows nothing from it


def test_med1_entry_object_picks_the_capability_entry_not_the_registering_function():
    src = "function f() { r({ id: 'A', run: () => q(`x`) }); r({ id: 'B', run: () => q(`y`) }) }"
    blank = ac._ts_mask(src, blank_strings=True)
    pos = src.index("`y`")
    lo, hi = ac._entry_object(blank, pos)
    assert "'B'" in src[lo:hi] and "'A'" not in src[lo:hi]


# ── MED-2: uniform_authority is bound to the asset and refused on a table with per-row authority ──

UA_EV = "platform/scripts/governance/asset_census.py:1"


def _ua(**over):
    d = dict(why="every row of this reference vocabulary is of uniform authority", evidence="platform/src/lib/retrieval/registry/layers/L1_ganita/get_ayurdaya.ts:71")
    d.update(over)
    return {"uniform_authority": d, "read_table": "chart_facts"}


def test_med2_the_evidence_file_must_mention_the_asset_or_its_table():
    assert ac.uniform_authority_problem(_ua(), "ga_ayurdaya") is None
    bad = ac.uniform_authority_problem(_ua(evidence=UA_EV), "bg_zzz_not_in_that_file")
    assert bad is None or "mentions neither" in bad                       # asset_census.py does name the read_table chart_facts, so the table needle is enough here
    e = _ua(evidence=UA_EV)
    e["read_table"] = "qqq_not_a_table_anywhere"
    assert "mentions neither" in ac.uniform_authority_problem(e, "qqq_not_an_asset_either")


def test_med2_the_validator_passes_the_asset_id():
    with pytest.raises(ac.DeclarationsError, match="mentions neither"):
        ac.validate_declarations(dict(version="9.9.9", kind_enum=list(ac.DECLARED_KINDS),
                                      assets={"qqq_asset": dict(kind="data", uniform_authority=dict(why="every row is of uniform authority here", evidence=UA_EV), read_table="qqq_tbl")}))


@pytest.mark.parametrize("cols,ok", [(["id", "tier"], False), (["id", "verification_pass_status"], False), (["id", "name"], True)])
def test_med2_a_table_with_a_tier_vocabulary_column_refuses_the_uniform_authority_declaration(cols, ok):
    got = ac.uniform_authority_measure_problem(_ua(), "t", cols, "ga_ayurdaya")
    assert (got is None) is ok, got
    if not ok:
        assert "per-row authority" in got


def test_med2_an_unknown_table_or_columns_is_unverifiable_never_accepted():
    assert "unverifiable" in ac.uniform_authority_measure_problem(_ua(), None, ["id"], "ga_ayurdaya")
    assert "unverifiable" in ac.uniform_authority_measure_problem(_ua(), "t", None, "ga_ayurdaya")
    assert ac.uniform_authority_measure_problem({}, "t", None) is None


# ── MED-3: the uniform_authority PASS needs the entry's own select and a non-label reference inside that same entry ──

UA_FACETS = "density_contract: { paginated: true, facets: ['a'], empty_reason: true },"


def _ua_scan(tree, src, **kw):
    tree.write(tree.layers / "L0_x", "q.ts", src)
    return _scan(tree, ["t_x", "bg_x"], columns={"t_x": ["id", "name"]}, **kw)


def test_med3_a_contract_entry_with_its_own_select_and_a_reference_inside_it_carries_the_pass(tree):
    cap = _ua_scan(tree, "export const cap = {\n  id: 'bg_x',\n  " + UA_FACETS + "\n  run: () => query(`SELECT id, name FROM t_x`),\n}\n")
    assert cap["facet_dense"] and ac._grade_dens(cap, "t_x", True)["v"] == PASS


def test_med3_a_contract_entry_that_does_not_hold_the_select_does_not(tree):
    cap = _ua_scan(tree, "export const a = {\n  id: 'bg_x',\n  " + UA_FACETS + "\n  run: () => query(`SELECT 1 FROM other`),\n}\n"
                         "export const b = {\n  id: 'b2',\n  run: () => query(`SELECT id, name FROM t_x`),\n}\n")
    assert not cap["facet_dense"] and ac._grade_dens(cap, "t_x", True)["v"] != PASS


def test_med3_a_label_only_mention_of_the_asset_inside_the_entry_is_not_a_reference(tree):
    """The contract entry's select reads ANOTHER table; the asset's table is only a provenance label in it, its real select sits in a sibling entry of the same declaration."""
    src = ("export function reg(r) {\n  r({ id: 'c1', " + UA_FACETS + " run: () => query(`SELECT id FROM other_tbl`),\n"
           "    out: () => ({ provenance: { tables: ['t_x'] } }) })\n"
           "  r({ id: 'c2', run: () => query(`SELECT id, name FROM t_x`) })\n}\n")
    cap = _ua_scan(tree, src)
    assert not cap["facet_dense"] and ac._grade_dens(cap, "t_x", True)["v"] != PASS


def test_med3_a_shared_table_select_attributed_by_facet_never_carries_a_uniform_authority_pass(tree):
    tree.write(tree.layers / "L0_x", "q.ts", "export const cap = {\n  id: 'bg_x',\n  " + UA_FACETS + "\n  run: () => query(`SELECT fact_id FROM t_shared WHERE fact_category = 'ayurdaya'`),\n}\n")
    cap = _scan(tree, ["t_shared", "bg_x"], shared={"t_shared"}, columns=SHARED_COLS, facets=FACET)
    assert cap["facet_attributed"] and not cap["facet_dense"]
    assert ac._grade_dens(cap, "t_shared", True)["v"] != PASS


# ── LOW-4: the facet declaration is a tenth FAIL move, asserted on the real tree ──

def test_low4_ga_ayurdaya_with_its_committed_facet_reads_pass_on_the_real_tree():
    decl = ac.load_asset_declarations()
    if not (decl.get("ga_ayurdaya") or {}).get("density_facet"):
        pytest.skip("ga_ayurdaya declares no density_facet in this tree")
    d = FX["layers"]["L1"]
    r = next(x for x in d["assets"] if x["asset_id"] == "ga_ayurdaya")
    f = decl["ga_ayurdaya"]["density_facet"]
    base = ac.capability_scan(ac.CAPS_ROOTS, r["tokens"], shared=frozenset(d["shared"]), columns=d["columns"], outside_roots=ac.DENS_OUTSIDE_ROOTS)
    assert ac._grade_dens(base, "chart_facts")["v"] == NO_DET                       # without the facet: only a shared table is referenced
    cap = ac.capability_scan(ac.CAPS_ROOTS, r["tokens"], shared=frozenset(d["shared"]), columns=d["columns"], outside_roots=ac.DENS_OUTSIDE_ROOTS,
                             facets={"chart_facts": dict(column=f["column"], values=list(f["values"]))})
    g = ac._grade_dens(cap, "chart_facts")
    # attributed by its own entry's pin; DENS-SERVED: get_ayurdaya now declares density_contract and selects verification_pass_status in that same entry, so PASS
    assert g["v"] == PASS and cap["facet_attributed"] == ["L1_ganita/get_ayurdaya.ts"], g


# ── LOW-5: a lower-case concatenated select is still a run-time table read ──

@pytest.mark.parametrize("src", [
    "const q = 'select a ' + 'from ' + t\n",
    "const q = ['select a', 'from', t]\n",
    "const q = 'select a ' + 'from ${t}'\n".replace("'from ${t}'", "`from ${t}`"),
    "const q = 'select a '.concat('join ', t)\n",
])
def test_low5_a_lower_case_concatenated_select_is_dynamic(src):
    assert ac._dynamic_from(src, ac._ts_literal_spans(src))


@pytest.mark.parametrize("src", [
    "const d = { a: 'isolated from generation', b: 'x' }\n",
    "const x = 'rows from ' + n + ' sources'\n",
    "const x = `see ${a} from ${b}`\n",
])
def test_low5_prose_with_a_lower_case_from_is_still_not_a_table_name(src):
    assert not ac._dynamic_from(src, ac._ts_literal_spans(src))


# ── re-check LOWs: declared tier columns and whole-identifier evidence ──

def test_recheck_the_tier_refusal_counts_the_assets_declared_tier_columns():
    e = _ua()
    assert ac.uniform_authority_measure_problem(e, "t", ["id", "indication_tier"], "ga_ayurdaya") is None          # not in the closed vocabulary, not declared
    e["density_tier_columns"] = [dict(column="indication_tier", why="verification tier", evidence="x:1")]
    got = ac.uniform_authority_measure_problem(e, "t", ["id", "indication_tier"], "ga_ayurdaya")
    assert got and "per-row authority" in got and "indication_tier" in got


def test_recheck_the_evidence_must_name_the_asset_as_a_whole_identifier(tmp_path, monkeypatch):
    f = tmp_path / "ev.ts"
    f.write_text("// reads ga_yogas only\n")
    monkeypatch.setattr(ac, "ROOT", tmp_path)
    monkeypatch.setattr(ac, "_s3_evidence_problem", lambda *a, **k: None)
    e = dict(why="every row of this reference vocabulary is of uniform authority", evidence="ev.ts:1")
    assert "mentions neither" in ac.uniform_authority_problem({"uniform_authority": e}, "ga_yoga")
    assert ac.uniform_authority_problem({"uniform_authority": e}, "ga_yogas") is None
    f.write_text("// reads ga_yoga\n")
    assert ac.uniform_authority_problem({"uniform_authority": e}, "ga_yoga") is None
