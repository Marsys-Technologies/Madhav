"""test_e6_dens_label_select.py: REGISTRY_REVISION 14, SS N-74 item 5 / N-74(a): the Dens.served scanner tells a SELECT from a LABEL,
and R02 is amended to its cause-keyed reading.

  R02 decision text (N-74(a)): "an asset no served module selects rows from; being named only as a provenance label is not a select".

THE REPAIR. Before, a serving module that merely NAMED the asset (a `provenance.tables` array, `asset_id: 'x'` of a probe envelope, a
prose string, a type name) was "reach by code", so the asset stopped at the NO_DETECTOR "reach it by code, but no served select was found"
branch and could never read the N/A. Now every occurrence of the asset's tokens in a module is classified:

  SELECT     the name is in an SQL literal (SQL signal in the literal or its `+`/`,` neighbours), or a bare name used as a table (builder
             argument, call argument, unkeyed list, `const T = 't'`, a non-label key), or a name that is part of a run-time-built table name
  LABEL      the name is in a literal that is not SQL (prose, a path, a `a:b:name` id, `source: 'x (note)'`), a bare name under a label key
             (`source_table`, `table(s)`, `asset_id`, `provenance`...) in a module with no run-time table access, an import path, a
             type/interface name, an object key in a module with no run-time table access
  AMBIGUOUS  everything the scanner cannot classify: counted as a SELECT (the safe direction: only an exact "scanned, no select" reads N/A)

Two directions for every pattern: a label-only module must not make the asset reached (N/A allowed), a select must (N/A refused), every
ambiguous form must refuse the N/A. Comments keep today's R51 reading (comment-only mention blocks the N/A: a comment can assert served-ness).
Python readers are outside the served surface BY DESIGN: the scan reads `*.ts` under the serving roots only.
`ka_vedha_gochara/writer.py` (a Python L3 writer) DOES read `FROM bg_phaladeepika_latta`; the rule says no SERVED module selects from it, which
is true. Dens.served N/A means "not served directly", NOT "unused".
SERVICE ASSETS (strategist ruling on DENS): an occurrence inside a `service_probe` envelope is a REACH when the asset's REGISTRY KIND is `service`
(the capability that carries the envelope serves the service); the identical envelope on a data-kind asset stays a label. A service asset with
only a prose / label mention OUTSIDE an envelope stays a label (an ambiguous form still blocks). bg_ephemeris_engine and bg_panchanga therefore
stay NO_DETECTOR; whether Dens.served applies to services at all is a separate, later, declared rule and is not decided here.

Every test drives the real `capability_scan` / `_grade_dens` over a small synthetic tree, plus the real tree for the pinned N/A set.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_e6_dens_label_select.py -v
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
import test_w2_1_earned_verdicts as w1  # noqa: E402

tree = dr.tree                                   # the synthetic-source-tree fixture (re-exported for pytest)
NA, NO_DET = ac.NA, ac.NO_DET
TOKS = ("t_x", "bg_x")                            # the table and the asset id, as measure() hands them over


def _verdict(tree, src, toks=TOKS, where="layers", name="tool.ts"):
    tree.write(getattr(tree, where), name, src)
    cap = dr._scan(tree, list(toks))
    return ac._grade_dens(cap, "t_x"), cap


def _is_na(tree, src, **kw):
    d, cap = _verdict(tree, src, **kw)
    return d["v"] == NA, d


# ───────────────────────── LABEL forms: the asset is named, nothing selects from it -> N/A ─────────────────────────

LABELS = {
    "provenance-tables-array":
        "export const c = { run: () => ({ provenance: { tables: ['kala_x', 't_x', 'other'], source: 'served chart-scoped' } }) }\n",
    "source_table-key": "export const c = { run: () => ({ source_table: 't_x', rows: [] }) }\n",
    "table-key": "export const c = { meta: { table: 't_x' } }\n",
    "source-key-embedded-note": "export const c = { source: 'bg_x (cohort-scored scarcity)' }\n",
    "asset_id-key": "export const probe = { kind: 'service_probe', asset_id: 'bg_x', probe_id: 'x_engine' }\n",
    "asset_ids-array": "export const c = { assets: ['bg_x', 'bg_y'] }\n",
    "required_assets-array": "export const c = { required_assets: ['bg_x'] }\n",
    "endpoint-identity-id": "export const p = { endpoint_identity: 'nirmana-elevation:health-probe:bg_x' }\n",
    "source_ref-path": "export const p = { source_ref: 'platform/supabase/migrations/624_probe.sql#bg_x; platform/routers/probe.py' }\n",
    "prose-description":
        "export const c = { description: 'Retrieve chart remedy prescriptions from t_x (Remedial Matrix) for a chart in a given period.' }\n",
    "prose-source-line": "export const c = { description: 'Returns anchors for a chart. Source: t_x (150 rows, the core foundation).' }\n",
    "error-message-template":
        "export const m = (id: string) => `no rows in t_x for chart ${id}: the build has not produced anchors yet`\n",
    "emits-references-prose":
        "export const c = { description: 'Filter by date range. emits_references: anchor_id back to t_x; lel_entry_id where present.' }\n",
    "interface-name": "export interface t_x { id: string }\nexport const ok = 1\n",
    "type-alias-name": "export type bg_x = { id: string }\nexport const ok = 1\n",
    "import-path-from": "import { thing } from './t_x'\nexport const ok = thing\n",
    "import-bare-from": "import thing from 'bg_x'\nexport const ok = thing\n",
    "require-path": "const thing = require('bg_x')\nexport const ok = thing\n",
    "dynamic-import-path": "export const load = () => import('./t_x')\n",
    "map-key": "export const MAP = { t_x: ['marsys://tool/L2/get_signal_embeddings'] }\n",
    "provenance-envelope-next-to-real-sql-of-another-table":
        "export const c = { run: async () => { const r = await query(`SELECT id FROM kala_other WHERE chart_id = $1`, [1]);\n"
        "  return { r, provenance: { tables: ['kala_other', 't_x'] } } } }\n",
    "multiline-concat-prose":
        "export const c = { description: 'Returns eligibility windows for a chart ' +\n   '(t_x service) over a date range, ranked.' }\n",
}


@pytest.mark.parametrize("name", sorted(LABELS))
def test_a_module_that_only_names_the_asset_as_a_label_is_not_a_reach_and_reads_na(tree, name):
    ok, d = _is_na(tree, LABELS[name])
    assert ok, (name, d)
    assert "label" in d["measured"], d                                      # the evidence names the label-only module


def test_the_label_only_module_is_listed_not_counted_as_reaching_the_asset(tree):
    tree.write(tree.layers, "tool.ts", LABELS["provenance-tables-array"])
    cap = dr._scan(tree, list(TOKS))
    assert cap["modules"] == [] and cap["label_only"] == ["tool.ts"] and cap["served"] == 0, cap


# ───────────────────────── SELECT forms: the module reads rows from the table -> the N/A is refused ─────────────────────────

SELECTS = {
    "select-from": "export const q = () => query(`SELECT id FROM t_x WHERE chart_id = $1`, [1])\n",
    "select-from-quoted-single": "export const q = () => query('SELECT id FROM t_x')\n",
    "lowercase-select-from": "export const q = () => query('select id from t_x where chart_id = $1', [1])\n",
    "join": "export const q = () => query(`SELECT a.id FROM kala_other a JOIN t_x b ON b.id = a.id`)\n",
    "left-join-lowercase-fragment": "export const q = (s: string) => query(s + ' left join t_x b on b.id = a.id')\n",
    "insert-into": "export const q = () => query(`INSERT INTO t_x (id) VALUES ($1)`, [1])\n",
    "update": "export const q = () => query(`UPDATE t_x SET note = $1 WHERE id = $2`, ['n', 1])\n",
    "delete-from": "export const q = () => query(`DELETE FROM t_x WHERE id = $1`, [1])\n",
    "schema-qualified": "export const q = () => query(`SELECT id FROM public.t_x`)\n",
    "double-quoted-identifier": "export const q = () => query(`SELECT id FROM \"t_x\"`)\n",
    "concat-select-then-from-bare-name": "export const q = () => query('SELECT id ' + 'FROM ' + 't_x')\n",
    "concat-lowercase-second-literal": "export const q = () => query('select id ' + 'from t_x where k = $1', [1])\n",
    "comma-join": "export const q = () => query('SELECT a.id FROM kala_other a, t_x b WHERE a.id = b.id')\n",
    "builder-from-call": "export const q = () => db.from('t_x').select('id')\n",
    "builder-into-call": "export const q = () => db.insert().into('t_x')\n",
    "builder-table-call": "export const q = () => knex.table('t_x').where({ id: 1 })\n",
    "bare-name-as-call-argument": "export const q = () => readTable('t_x', 1)\n",
    "bare-name-in-unkeyed-array": "export const IDS = ['t_x', 'bg_y']\n",
    "bare-name-const": "const T = 't_x'\nexport const q = () => query(`SELECT * FROM ${T}`)\n",
    "bare-name-in-non-label-key": "export const c = { view: 't_x' }\n",
    "bare-name-chart-summary-map-value": "export const c = { chart_summary: 't_x' }\n",
    "name-flush-before-interpolation": "export const q = (s: string) => `t_x${s}`\n",
    "name-flush-after-interpolation": "export const q = (p: string) => `${p}t_x`\n",
    "name-flush-end-of-literal-then-concat": "export const q = (s: string) => ('x t_x' + s)\n",
    "name-flush-start-of-literal-after-concat": "export const q = (s: string) => (s + 't_x y')\n",
    "sql-prose-hybrid": "export const c = { description: 'SELECT the rows from t_x for the chart' }\n",
    "fragment-from-name": "export const q = (s: string) => query(s + ' from t_x x')\n",
    "dynamic-from-run-time-name-next-to-label-key":
        "export const c = { tables: ['t_x'] }\nexport const q = (t: string) => query(`SELECT id FROM ${t}`)\n",
    "builder-with-variable-next-to-label-key":
        "export const c = { tables: ['t_x'] }\nexport const q = (t: string) => db.from(t).select('id')\n",
    "dynamic-from-with-label-asset-id":
        "export const p = { asset_id: 'bg_x' }\nexport const q = (t: string) => query('SELECT id FROM ' + t)\n",
    "label-array-element-is-a-call-argument": "export const c = { tables: [pick('t_x')] }\n",
    "label-key-array-nested-in-object": "export const c = { tables: [{ name: 't_x' }] }\n",
    "map-key-next-to-run-time-table": "export const MAP = { t_x: 1 }\nexport const q = (t: string) => query(`SELECT * FROM ${t}`)\n",
    "identifier-use": "export const q = () => run(t_x)\n",
    "property-access": "export const q = (r: any) => r.t_x\n",
    "ternary-value": "export const q = (a: boolean) => (a ? t_x : null)\n",
    "string-union-type": "export type T = 't_x' | 'other'\n",
    "label-key-with-ternary": "export const c = { source_table: flag ? 't_x' : 'other' }\n",
    "template-literal-sql-with-expression": "export const q = (w: string) => query(`SELECT id FROM t_x ${w}`)\n",
    "update-prefix-no-set-uppercase": "export const q = () => query(`UPDATE t_x`)\n",
    "table-ddl": "export const q = () => query(`CREATE TABLE t_x (id int)`)\n",
    "asset-id-select-from-in-a-sql-literal": "export const q = () => query(`SELECT id FROM bg_x`)\n",
}


@pytest.mark.parametrize("name", sorted(SELECTS))
def test_a_select_or_an_unclassifiable_form_refuses_the_na(tree, name):
    d, cap = _verdict(tree, SELECTS[name])
    assert d["v"] != NA, (name, d)
    assert cap["modules"] == ["tool.ts"] and not cap["label_only"], (name, cap)        # the module IS a reach


def test_a_strict_served_select_is_still_a_reach_with_the_same_fail_verdict_as_before(tree):
    d, cap = _verdict(tree, "export const q = () => query(`SELECT id FROM t_x`)\n")
    assert d["v"] == ac.FAIL and cap["served"] == 1, d


# ───────────────────────── a label next to a select never hides the select; verdicts of reached assets do not move ─────────────────────────

def test_a_module_with_a_label_and_a_select_is_one_reach_and_keeps_its_fail(tree):
    d, cap = _verdict(tree, LABELS["provenance-tables-array"] + "export const q = () => query(`SELECT id FROM t_x`)\n")
    assert d["v"] == ac.FAIL and cap["modules"] == ["tool.ts"] and cap["label_only"] == [], (d, cap)


def test_a_label_only_module_beside_a_real_serving_module_changes_neither_the_verdict_nor_the_pass(tree):
    tree.write(tree.layers / "L0_x", "real.ts", dr._cap("SELECT id, signature_tier FROM t_x"))
    tree.write(tree.tools, "label.ts", LABELS["provenance-tables-array"])
    cap = dr._scan(tree, list(TOKS), columns={"t_x": ["id", "signature_tier"]})
    d = ac._grade_dens(cap, "t_x")
    assert d["v"] == ac.PASS, d
    assert cap["modules"] == ["L0_x/real.ts"] and len(cap["label_only"]) == 1 and cap["label_only"][0].endswith("/label.ts"), cap


def test_a_label_only_module_beside_a_served_select_elsewhere_still_reads_fail(tree):
    tree.write(tree.layers / "L0_x", "real.ts", dr._cap("SELECT id FROM t_x", contract=False))
    tree.write(tree.tools, "label.ts", LABELS["asset_id-key"])
    d = ac._grade_dens(dr._scan(tree, list(TOKS)), "t_x")
    assert d["v"] == ac.FAIL, d


def test_a_label_in_one_module_and_an_unclassifiable_name_in_another_still_refuses_the_na(tree):
    tree.write(tree.tools, "label.ts", LABELS["asset_id-key"])
    tree.write(tree.lib, "other.ts", SELECTS["bare-name-in-unkeyed-array"])
    d = ac._grade_dens(dr._scan(tree, list(TOKS)), "t_x")
    assert d["v"] == NO_DET and "no served" in d["measured"], d


def test_a_shared_table_select_in_a_capability_that_names_the_asset_by_label_still_attributes_it(tree):
    """Attribution is unchanged: the asset id in a capability (even as a label) attributes that capability's shared-table select."""
    tree.write(tree.layers, "tool.ts", "export const cap = {\n  id: 'x',\n  asset_id: 'bg_x',\n  run: () => query(`SELECT id FROM t_shared`),\n}\n")
    cap = dr._scan(tree, ["t_shared", "bg_x"], shared={"t_shared"})
    assert cap["served"] == 1 and cap["modules"] == ["tool.ts"], cap


# ───────────────────────── the other branches are untouched ─────────────────────────

def test_a_comment_only_mention_still_blocks_the_na_r51(tree):
    d, cap = _verdict(tree, "// served elsewhere: t_x, bg_x\nexport {}\n")
    assert d["v"] == NO_DET and "comments only" in d["measured"], d


def test_a_label_in_code_and_a_comment_in_another_module_keeps_the_na_blocked_by_the_comment(tree):
    tree.write(tree.tools, "label.ts", LABELS["asset_id-key"])
    tree.write(tree.lib, "note.ts", "// reads bg_x through a generic route\nexport {}\n")
    d = ac._grade_dens(dr._scan(tree, list(TOKS)), "t_x")
    assert d["v"] == NO_DET and "comments only" in d["measured"], d


def test_a_desynced_serving_file_is_still_unparsed_not_read_for_labels(tree):
    d, cap = _verdict(tree, "const re = /'/;\nexport const c = { asset_id: 'bg_x' }\n")
    assert d["v"] == NO_DET and cap["unparsed"] == ["tool.ts"] and not cap["label_only"], (d, cap)


def test_a_label_in_the_serving_roots_does_not_hide_a_served_select_outside_them(tree):
    tree.write(tree.tools, "label.ts", LABELS["asset_id-key"])
    tree.write(tree.outside, "route.ts", dr._cap("SELECT id FROM t_x", contract=False))
    d = ac._grade_dens(dr._scan(tree, list(TOKS), outside=True), "t_x")
    assert d["v"] == NO_DET and "outside the scanned serving roots" in d["measured"], d


def test_a_shared_only_name_is_never_relabelled(tree):
    tree.write(tree.tools, "tool.ts", "export const c = { source: 'chart_facts rows' }\n")
    d = ac._grade_dens(dr._scan(tree, ["chart_facts", "bg_x"], shared={"chart_facts"}), "t_x")
    assert d["v"] == ac.NO_DET, d


def test_the_outside_probe_is_unchanged_a_names_map_still_reads_na_and_a_dynamic_from_still_blocks(tree):
    tree.write(tree.outside, "names.ts", "export const NAMES = { bg_x: 't_x' }\n")
    assert ac._grade_dens(dr._scan(tree, list(TOKS), outside=True), "t_x")["v"] == NA
    tree.write(tree.outside, "dyn.ts", "const T = 't_x';\nexport const q = () => query(`SELECT id FROM ${T}`);\n")
    assert ac._grade_dens(dr._scan(tree, list(TOKS), outside=True), "t_x")["v"] == NO_DET


# ───────────────────────── the classifier itself (unit level) ─────────────────────────

def _kinds(src, tok="t_x"):
    return ac._ref_kinds(src, tok)


@pytest.mark.parametrize("src, want", [
    ("export const c = { tables: ['t_x'] }", ["label"]),
    ("export const c = { tables: ['a', 't_x', 'b'] }", ["label"]),
    ("export const c = { 'tables': ['t_x'] }", ["label"]),
    ("export const c = { table: 't_x' }", ["label"]),
    ("export const c = { table : \n 't_x' }", ["label"]),
    ("export const c = { Table: 't_x' }", ["label"]),                      # the key vocabulary is case-insensitive
    ("export const c = { SOURCE_TABLE: 't_x' }", ["label"]),
    ("export const c = { notes: 'about t_x here' }", ["label"]),
    ("export const c = { x: `SELECT 1 FROM t_x` }", ["select"]),
    ("export const c = { x: 'select 1 from t_x' }", ["select"]),
    ("export const c = { x: 'sELeCt 1 FrOm t_x' }", ["select"]),
    ("export const c = { x: 'FROM t_x' }", ["select"]),
    ("export const c = { x: 'JOIN t_x' }", ["select"]),
    ("export const c = { x: 'INTO t_x' }", ["select"]),
    ("export const c = { x: 'UPDATE t_x' }", ["select"]),
    ("export const c = { x: 'x $1 t_x' }", ["select"]),                    # a bind placeholder is an SQL signal
    ("export const c = { x: 't_x::text' }", ["select"]),                   # so is a cast
    ("export const c = { x: 't_x ORDER BY id' }", ["select"]),
    ("export const c = { x: 't_x LIMIT 5' }", ["select"]),
    ("export const c = { x: 'WHERE t_x.id = 1' }", ["select"]),
    ("export const c = { x: 'ON CONFLICT t_x' }", ["select"]),
    ("export const c = { x: 'TRUNCATE t_x' }", ["select"]),
    ("export const c = { x: 'a' + 'b ' + 't_x' }", ["ambiguous"]),
    ("export const c = { x: ['t_x'] }", ["ambiguous"]),
    ("export const c = { x: 't_x' }", ["ambiguous"]),
    ("run(t_x)", ["ambiguous"]),
    ("export const c = { x: `${a}t_x` }", ["ambiguous"]),
    ("export const c = { x: `t_x${a}` }", ["ambiguous"]),
    ("type t_x = number", ["label"]),
    ("interface t_x { a: 1 }", ["label"]),
    ("enum t_x { A }", ["label"]),
    ("class t_x {}", ["label"]),
    ("const m = { t_x: 1 }", ["label"]),
    ("const m = { t_x?: 1 }", ["label"]),
    ("const m = { a: 1, t_x: 1 }", ["label"]),
    ("// t_x in a comment\nexport const c = 1", []),                       # comments are not occurrences (R51 handles them)
    ("export const c = { x: 'ok' }", []),
])
def test_ref_kind_unit(src, want):
    assert _kinds(src) == want, (src, _kinds(src))


@pytest.mark.parametrize("src", [
    "export const c = { x: 'CREATE TABLE t_x' }",
    "export const c = { x: 't_x SET note = 1' }",
    "export const c = { x: 'WHERE t_x' }",
    "export const c = { x: 't_x RETURNING id' }",
    "export const c = { x: 't_x UNION' }",
    "export const c = { x: 'insert into t_x (id) values (1)' }",
    "export const c = { x: 'delete from t_x' }",
    "export const c = { x: 'merge into t_x using s' }",
    "export const c = { x: 'select 1 union select 2 from t_x' }",
    "export const c = { x: 't_x group by k' }",
    "export const c = { x: 't_x offset 5' }",
    "export const c = { x: 't_x limit 5' }",
    "export const c = { x: 't_x order by id' }",
    "export const c = { x: 'where t_x.id = 1' }",
    "export const c = { x: 'where t_x in (1, 2)' }",
    "export const c = { x: 'where t_x is null' }",
    "export const c = { x: 'on conflict (id) do nothing -- t_x' }",
    "export const c = { x: 'x join t_x' }",
    "export const c = { x: 'x JOIN t_x' }",
], ids=lambda s: s[26:60])
def test_every_sql_signal_marks_the_literal_a_select_not_a_label(src):
    assert _kinds(src) == ["select"], (src, _kinds(src))


@pytest.mark.parametrize("src", [
    "export const c = { d: 'rows where present, or limit to the first few' + ' t_x' }",
    "export const c = { d: 'the union of t_x and its siblings' }",
    "export const c = { d: 'a table of t_x rows, set aside, updated' }",
    "export const c = { d: 'returning t_x quickly' }",
    "export const c = { d: 'truncate the list for t_x' }",
    "export const c = { d: 'a where clause on t_x is not used' }",
])
def test_prose_with_a_lower_case_sql_word_is_not_mistaken_for_a_select_signal_where_the_word_is_not_sql(src):
    """`where` / `returning` / `truncate` are upper-case-only signals (prose says them); `union` / `limit` are signals only in SQL shape.
    The first and second forms are classified, not asserted label: they pin that `where present` alone is not an SQL signal."""
    kinds = _kinds(src)
    assert kinds and all(k in ("label", "select", "ambiguous") for k in kinds)
    if "where present" in src:
        assert kinds == ["ambiguous"], kinds                      # glued to a concatenated literal edge: unclassifiable, and NOT a select signal
    if "returning" in src or "truncate" in src or "a where clause" in src or "union of" in src or "a table of" in src:
        assert kinds == ["label"], (src, kinds)


def test_a_label_key_vocabulary_is_exact_not_substring_or_prefix():
    assert _kinds("export const c = { table_x: 't_x' }") == ["ambiguous"]
    assert _kinds("export const c = { mytable: 't_x' }") == ["ambiguous"]
    assert _kinds("export const c = { tables_loader: 't_x' }") == ["ambiguous"]


def test_the_label_keys_are_the_documented_provenance_vocabulary():
    assert ac.DENS_LABEL_KEYS == frozenset({
        "source_table", "source_tables", "table", "tables", "source", "sources", "source_ref", "source_surface", "provenance",
        "asset_id", "asset_ids", "assets", "required_assets", "backing_tables"})


def test_the_label_key_arrays_need_the_array_to_sit_directly_under_the_key():
    assert _kinds("export const c = { tables: ['t_x'] }") == ["label"]
    assert _kinds("export const c = { tables: [['t_x']] }") == ["ambiguous"]
    assert _kinds("export const c = { other: { tables: 1 }, list: ['t_x'] }") == ["ambiguous"]
    assert _kinds("export const c = { tables: foo(['t_x']) }") == ["ambiguous"]


def test_an_array_under_a_label_key_is_the_only_bracket_that_lends_the_key_not_a_paren_or_an_object():
    assert _kinds("export const c = { tables: ('t_x') }") == ["ambiguous"]
    assert _kinds("export const c = { tables: { a: 't_x' } }") == ["ambiguous"]
    assert _kinds("export const c = { tables: [ 'a',\n 't_x' ] }") == ["label"]


def test_a_label_key_must_start_an_entry_a_ternary_branch_named_like_one_does_not_count():
    assert _kinds("export const c = { v: flag ? tables : 't_x' }") == ["ambiguous"]
    assert _kinds("export const c = { v: 1, tables: 't_x' }") == ["label"]
    assert _kinds("export const c = {\n  tables: 't_x' }") == ["label"]


def test_a_comment_between_concatenated_literals_does_not_break_the_join():
    assert _kinds("run('select a ' + /* the table */ 'from t_x')") == ["select"]
    assert _kinds("run('select a ' + // the table\n 'from t_x')") == ["select"]


def test_a_built_in_from_is_not_a_table_builder_but_a_table_builder_is():
    lab = "export const c = { tables: ['t_x'] }\n"
    assert _kinds(lab + "const a = Array.from(s)") == ["label"]
    assert _kinds(lab + "const a = Uint8Array.from(s)") == ["label"]
    assert _kinds(lab + "const a = Buffer.from(s)") == ["label"]
    assert _kinds(lab + "const a = db.from(s)") == ["ambiguous"]
    assert _kinds(lab + "const a = db.into(s)") == ["ambiguous"]
    assert _kinds(lab + "const a = db.table(s)") == ["ambiguous"]
    assert _kinds(lab + "const a = db.insertInto(s)") == ["ambiguous"]
    assert _kinds(lab + "const a = db.from('lit')") == ["label"]


def test_a_sql_looking_prose_sentence_ending_in_from_and_joined_to_a_name_is_still_a_run_time_table():
    """`_dynamic_from(prose_tail_ok)` forgives only a PROSE tail (five words, no SQL signal); an SQL list that ends in `from` is dynamic."""
    lab = "export const c = { tables: ['t_x'] }\n"
    assert _kinds(lab + "run('select id name kind score weight from ' + t)") == ["ambiguous"]
    assert _kinds(lab + "const d = 'Retrieve vedha rows for a chart from ' + t") == ["label"]
    assert _kinds(lab + "run('x from ' + t)") == ["ambiguous"]


def test_a_bracket_inside_a_string_does_not_end_the_enclosing_array():
    assert _kinds("export const c = { tables: ['a]b', 't_x'] }") == ["label"]
    assert _kinds("export const c = { tables: ['a[b', 't_x'] }") == ["label"]


def test_a_bare_name_may_carry_a_schema_prefix_and_identifier_quotes_but_nothing_else():
    assert _kinds("export const c = { tables: ['public.t_x'] }") == ["label"]
    assert _kinds("export const c = { tables: ['\"t_x\"'] }") == ["label"]
    assert _kinds("export const c = { tables: ['\"public\".\"t_x\"'] }") == ["label"]
    assert _kinds("export const c = { tables: ['  t_x  '] }") == ["label"]
    assert _kinds("export const c = { x: 'public.t_x' }") == ["ambiguous"]


@pytest.mark.parametrize("src", [
    "export const c = { x: 'update t_x' }",
    "export const c = { x: 'into t_x' }",
    "export const c = { x: 'from public.t_x' }",
    "export const c = { x: 'from \"public\".\"t_x\"' }",
    "export const c = { x: 'from only t_x' }",
    "export const c = { x: 'table t_x' }",
    "export const c = { x: 'truncate t_x' }",
    "export const c = { x: 'lateral t_x' }",
    "export const c = { x: '\"t_x\"' }",
])
def test_a_lower_case_sql_fragment_that_ends_at_the_name_is_ambiguous_never_a_label(src):
    assert _kinds(src) == ["ambiguous"], (src, _kinds(src))


def test_a_label_next_to_a_real_pass_is_named_in_the_evidence_text_and_the_count_excludes_it(tree):
    tree.write(tree.layers / "L0_x", "real.ts", dr._cap("SELECT id, signature_tier FROM t_x"))
    tree.write(tree.tools, "label.ts", LABELS["provenance-tables-array"])
    d = ac._grade_dens(dr._scan(tree, list(TOKS), columns={"t_x": ["id", "signature_tier"]}), "t_x")
    assert d["v"] == ac.PASS and "1 module(s) reach it by code: L0_x/real.ts (+1 name it only as a label)" in d["measured"], d


def test_the_na_evidence_names_every_label_only_module(tree):
    tree.write(tree.layers, "a.ts", LABELS["asset_id-key"])
    tree.write(tree.layers, "b.ts", LABELS["prose-description"])
    d = ac._grade_dens(dr._scan(tree, list(TOKS)), "t_x")
    assert d["v"] == NA and "2 module(s) name it only as a label" in d["measured"] and "a.ts" in d["measured"] and "b.ts" in d["measured"], d
    assert d["measured"].startswith("STRUCTURAL: 0 module(s) reference it by code in the 3 serving root(s) scanned"), d


def test_the_head_and_the_tail_of_a_concatenated_name_are_ambiguous():
    assert _kinds("run(prefix + 't_x rows')") == ["ambiguous"]
    assert _kinds("run('rows t_x' + suffix)") == ["ambiguous"]
    assert _kinds("run('rows t_x'.concat(suffix))") == ["ambiguous"]
    assert _kinds("run('rows t_x', other)") == ["label"]
    assert _kinds("run('pre t_x post' + other)") == ["label"]


def test_a_dynamic_table_access_in_the_module_turns_bare_labels_and_keys_ambiguous_but_not_prose():
    dyn = "\nexport const q = (t: string) => query(`SELECT id FROM ${t}`)"
    assert _kinds("export const c = { tables: ['t_x'] }" + dyn) == ["ambiguous"]
    assert _kinds("export const c = { t_x: 1 }" + dyn) == ["ambiguous"]
    assert _kinds("export const c = { note: 'about t_x here' }" + dyn) == ["label"]       # prose cannot build a table name
    bld = "\nexport const q = (t: string) => db.from(t).select()"
    assert _kinds("export const c = { tables: ['t_x'] }" + bld) == ["ambiguous"]
    assert _kinds("export const c = { tables: ['t_x'] }\nexport const q = () => db.from('other').select()") == ["label"]


def test_prose_with_a_lowercase_from_before_the_name_is_a_label_only_when_it_is_prose_shaped():
    assert _kinds("export const c = { d: 'Returns predictive anchors for a chart from t_x (ph_nimitta).' }") == ["label"]
    assert _kinds("export const c = { d: 'from t_x' }") == ["ambiguous"]
    assert _kinds("export const c = { d: ' from t_x x' }") == ["ambiguous"]
    assert _kinds("export const c = { d: 'a b from t_x' }") == ["ambiguous"]


def test_a_neighbour_literal_connected_by_plus_or_comma_lends_its_sql_signal_but_a_distant_one_does_not():
    assert _kinds("run('SELECT a ' + 'from t_x')") == ["select"]
    assert _kinds("run(['SELECT a', 'from t_x'])") == ["select"]
    assert _kinds("run('SELECT a ' + \n 'from t_x')") == ["select"]
    far = "const a = 'SELECT 1'\nconst z = 5\nexport const c = { d: 'Returns rows for a chart from the sidecar service t_x here.' }"
    assert _kinds(far) == ["label"]


def test_an_sql_signal_needs_a_whole_word():
    assert _kinds("export const c = { d: 'the selected rows and updated notes for t_x, joined view, subselect' }") == ["label"]


def test_import_and_require_paths_are_labels_but_other_calls_are_not():
    assert _kinds("import x from 't_x'") == ["label"]
    assert _kinds("import { a, b } from \"t_x\"") == ["label"]
    assert _kinds("export * from 't_x'") == ["label"]
    assert _kinds("const m = require('t_x')") == ["label"]
    assert _kinds("const m = await import('t_x')") == ["label"]
    assert _kinds("register('t_x')") == ["ambiguous"]
    assert _kinds("x.from('t_x')") == ["ambiguous"]
    assert _kinds("from('t_x')") == ["ambiguous"]


def test_every_occurrence_is_classified_and_one_ambiguous_one_decides():
    kinds = _kinds("export const c = { tables: ['t_x'], d: 'about t_x', run: () => query('SELECT 1 FROM t_x') }")
    assert kinds == ["label", "label", "select"], kinds
    assert ac._module_reaches(kinds) and not ac._module_reaches(["label", "label"]) and not ac._module_reaches([])


# ───────────────────────── service-kind assets: a service_probe envelope is a reach ─────────────────────────

PROBE = ("export const cap = { run: () => null, probe: { kind: 'service_probe', asset_id: 'bg_x', probe_id: 'x_engine', "
         "endpoint_identity: 'nirmana-elevation:health-probe:bg_x', source_ref: 'platform/python-sidecar/scripts/c.json#bg_x' } }\n")


def _svc(tree, src, service, toks=TOKS):
    tree.write(tree.layers, "tool.ts", src)
    cap = ac.capability_scan(tree.roots, list(toks), shared=set(), columns=None, outside_roots=(), service=service)
    return ac._grade_dens(cap, "t_x"), cap


def test_a_service_probe_envelope_is_a_reach_for_a_service_kind_asset(tree):
    d, cap = _svc(tree, PROBE, True)
    assert d["v"] == NO_DET and cap["modules"] == ["tool.ts"] and not cap["label_only"], (d, cap)


def test_the_identical_envelope_on_a_data_kind_asset_is_a_label(tree):
    d, cap = _svc(tree, PROBE, False)
    assert d["v"] == NA and cap["label_only"] == ["tool.ts"] and not cap["modules"], (d, cap)


@pytest.mark.parametrize("key", ["asset_id", "endpoint_identity", "source_ref"])
def test_each_envelope_key_alone_is_a_reach_for_a_service_and_a_label_for_data(tree, key):
    val = {"asset_id": "'bg_x'", "endpoint_identity": "'nirmana:health-probe:bg_x'", "source_ref": "'c.json#bg_x'"}[key]
    src = f"export const probe = {{ kind: 'service_probe', {key}: {val} }}\n"
    assert _svc(tree, src, True)[0]["v"] == NO_DET
    assert _svc(tree, src, False)[0]["v"] == NA


def test_a_service_asset_with_only_a_prose_or_label_mention_outside_an_envelope_stays_a_label(tree):
    for src in (LABELS["prose-description"], "export const c = { asset_id: 'bg_x' }\n", LABELS["provenance-tables-array"]):
        d, cap = _svc(tree, src, True)
        assert d["v"] == NA and cap["label_only"] == ["tool.ts"], (src, d)


def test_an_envelope_in_one_object_does_not_reach_a_label_in_a_sibling_object(tree):
    src = ("export const a = { kind: 'service_probe', asset_id: 'other_asset' }\n"
           "export const b = { asset_id: 'bg_x' }\n")
    assert _svc(tree, src, True)[0]["v"] == NA          # the 'service_probe' string belongs to a's object, not b's
    assert _svc(tree, "export const b = { kind: 'service_probe', nested: { asset_id: 'bg_x' } }\n", True)[0]["v"] == NA   # the innermost object holds no 'service_probe'


def test_a_service_envelope_beside_a_real_select_is_still_the_select_verdict(tree):
    d, cap = _svc(tree, PROBE + "export const q = () => query(`SELECT id FROM t_x`)\n", True)
    assert d["v"] == ac.FAIL and cap["served"] == 1, d


def test_the_service_flag_never_touches_a_non_label_form(tree):
    d, cap = _svc(tree, SELECTS["bare-name-in-unkeyed-array"], True)
    assert d["v"] == NO_DET and cap["modules"] == ["tool.ts"], d
    d, cap = _svc(tree, SELECTS["select-from"], True)
    assert d["v"] == ac.FAIL


def test_the_probe_kind_is_a_reach_in_the_unit_classifier():
    assert _kinds(PROBE.replace("bg_x", "t_x")) == ["label", "label", "label"]
    assert ac._ref_kinds(PROBE.replace("bg_x", "t_x"), "t_x", service=True) == ["probe", "probe", "probe"]
    assert ac._module_reaches(["probe"]) and ac.PROBE_REF == "probe"


def test_inside_an_envelope_only_a_label_becomes_a_probe_other_kinds_keep_their_name():
    src = "export const p = { kind: 'service_probe', q: 'SELECT id FROM t_x', n: 'a note about t_x here' }"
    assert ac._ref_kinds(src, "t_x", service=True) == ["select", "probe"]
    assert ac._ref_kinds("export const p = { kind: 'service_probe', ids: pick('t_x') }", "t_x", service=True) == ["ambiguous"]


@pytest.mark.parametrize("q", ["'", '"', "`"])
def test_the_envelope_marker_is_recognised_in_any_string_quote(q):
    src = f"export const p = {{ kind: {q}service_probe{q}, asset_id: 't_x' }}"
    assert ac._ref_kinds(src, "t_x", service=True) == ["probe"]
    assert ac._ref_kinds(src.replace("service_probe", "other_probe"), "t_x", service=True) == ["label"]
    assert ac._ref_kinds(src.replace("service_probe", "my_service_probe_x"), "t_x", service=True) == ["label"]


def test_measure_hands_the_registry_kind_to_the_scan(monkeypatch, tree):
    """measure() passes `service=(registry asset_kind == 'service')` -- the kind the census already reads, not a declaration."""
    seen = []
    real = dr._REAL_SCAN

    def spy(*a, **k):
        seen.append(k.get("service"))
        return real(*a, **k)
    tree.write(tree.layers, "tool.ts", PROBE)
    reg = {"bg_x": dict(w1._reg_row("bg_x", "t_x"), asset_kind="service")}
    w1._stub_layer(monkeypatch, tree.tmp, reg, None)
    monkeypatch.setattr(ac, "capability_scan", spy)
    monkeypatch.setattr(ac, "live_counts", lambda *a, **k: ({}, {}))
    monkeypatch.setattr(ac, "CAPS_ROOTS", tree.roots)
    monkeypatch.setattr(ac, "DENS_OUTSIDE_ROOTS", ())
    census = ac.measure("L0")
    assert seen == [True], seen
    assert dr._dens(census, "bg_x")["v"] == NO_DET
    seen.clear()
    reg = {"bg_x": dict(w1._reg_row("bg_x", "t_x"), asset_kind="data")}
    w1._stub_layer(monkeypatch, tree.tmp, reg, None)
    monkeypatch.setattr(ac, "capability_scan", spy)
    census = ac.measure("L0")
    assert seen == [False] and dr._dens(census, "bg_x")["v"] == NA


# ───────────────────────── Python readers are outside the served surface, by design ─────────────────────────

def test_a_python_reader_of_the_table_is_outside_the_served_surface_and_does_not_block_the_na(tree):
    py = tree.tmp / "python-sidecar" / "services"
    py.mkdir(parents=True)
    (py / "writer.py").write_text("SQL = 'SELECT id FROM t_x'\n# bg_x is read here at build time\n", encoding="utf-8")
    cap = dr._scan(tree, list(TOKS), outside=True)
    assert ac._grade_dens(cap, "t_x")["v"] == NA, cap
    # and even a python file placed INSIDE a scanned root is not read: only `*.ts` / `*.tsx` are the served surface
    (tree.tools / "reader.py").write_text("SQL = 'SELECT id FROM t_x'\n", encoding="utf-8")
    (tree.outside / "reader.py").write_text("SQL = 'SELECT id FROM t_x'\n", encoding="utf-8")
    assert ac._grade_dens(dr._scan(tree, list(TOKS), outside=True), "t_x")["v"] == NA


def test_the_real_scan_roots_name_no_python_tree():
    for r in tuple(ac.CAPS_ROOTS) + tuple(ac.DENS_OUTSIDE_ROOTS):
        assert "python" not in r and "sidecar" not in r, r
    assert "TypeScript" in ac.capability_scan.__doc__ and "Python" in ac.capability_scan.__doc__
    assert "NOT SERVED DIRECTLY" in ac.capability_scan.__doc__.upper() and "ka_vedha_gochara" in ac.capability_scan.__doc__


# ───────────────────────── the real tree ─────────────────────────

FX = json.loads((HERE / "fixtures" / "dens_scan_inputs_2026-10-02.json").read_text(encoding="utf-8"))
R02_PRE_N74 = ("bg_gochara_arcs", "bg_kota_chakra_rings", "bg_kp_sublord_division")
R02_LABEL_REPAIR = ("bg_cohort", "bg_phaladeepika_latta", "bg_vedha_malefic_scale")
SERVICE_PROBE_ONLY = ("bg_ephemeris_engine", "bg_panchanga")          # registry kind `service`, named only by a service_probe envelope: a reach
REPO = HERE.parents[3]


@pytest.fixture(scope="module")
def real_dens():
    """The REAL scan over the committed 127-asset inputs (verdict-free) against the current source tree. File reads are cached."""
    real, cache = pathlib.Path.read_text, {}

    def cached(self, *a, **k):
        key = (str(self), a, tuple(sorted(k.items())))
        if key not in cache:
            cache[key] = real(self, *a, **k)
        return cache[key]
    pathlib.Path.read_text = cached
    try:
        out = {}
        for L, d in FX["layers"].items():
            for r in d["assets"]:
                cap = ac.capability_scan(ac.CAPS_ROOTS, r["tokens"], shared=frozenset(d["shared"]), columns=d["columns"],
                                         outside_roots=ac.DENS_OUTSIDE_ROOTS, service=(r.get("asset_kind") == "service"))
                out[r["asset_id"]] = (ac._grade_dens(cap, r["target_table"] or r["asset_id"]), cap)
    finally:
        pathlib.Path.read_text = real
    assert len(out) == 127
    return out


def test_the_real_tree_reads_na_on_exactly_the_three_earlier_assets_plus_the_label_repair_set(real_dens):
    na = sorted(a for a, (g, _c) in real_dens.items() if g["v"] == NA)
    assert na == sorted(R02_PRE_N74 + R02_LABEL_REPAIR), na
    for a in na:
        assert real_dens[a][0]["cause"] == "no-served-surface", a


def test_the_two_service_assets_named_only_by_their_probe_envelope_stay_no_detector(real_dens):
    for a in SERVICE_PROBE_ONLY:
        g, cap = real_dens[a]
        assert g["v"] == NO_DET and cap["modules"], (a, g, cap)
        assert "reach it by code" in g["measured"], g
    # the prose `reason:` in get_av_transit_gating.ts is outside any envelope: a label (the service asset is reached by the envelopes, not by it)
    assert real_dens["bg_ephemeris_engine"][1]["label_only"] == ["L1_ganita/get_av_transit_gating.ts"]
    assert real_dens["bg_panchanga"][1]["label_only"] == []
    assert real_dens["bg_panchanga"][1]["modules"] == ["L0_brahmagyan/call_panchanga_service.ts"]


def test_the_same_two_assets_scanned_as_data_kind_would_read_na_which_is_exactly_the_registry_kind_split():
    """The split is the registry kind and nothing else: the identical scan with service=False labels the envelope."""
    for a in SERVICE_PROBE_ONLY:
        cap = ac.capability_scan(ac.CAPS_ROOTS, [a], shared=frozenset(), columns={}, outside_roots=ac.DENS_OUTSIDE_ROOTS, service=False)
        assert ac._grade_dens(cap, a)["v"] == NA, a
        cap = ac.capability_scan(ac.CAPS_ROOTS, [a], shared=frozenset(), columns={}, outside_roots=ac.DENS_OUTSIDE_ROOTS, service=True)
        assert ac._grade_dens(cap, a)["v"] == NO_DET, a


def test_the_real_registry_kind_is_what_the_fixture_carries_for_every_asset():
    kinds = {r["asset_id"]: r.get("asset_kind") for d in FX["layers"].values() for r in d["assets"]}
    assert len(kinds) == 127 and all(kinds.values())
    assert kinds["bg_ephemeris_engine"] == kinds["bg_panchanga"] == "service"
    assert kinds["bg_phaladeepika_latta"] == kinds["bg_cohort"] == kinds["bg_vedha_malefic_scale"] == "data"


def test_the_label_repair_assets_are_label_only_in_the_real_modules_named_in_the_evidence(real_dens):
    for a in R02_LABEL_REPAIR:
        g, cap = real_dens[a]
        assert cap["label_only"] and not cap["modules"] and cap["served"] == 0, (a, cap)
        assert "label" in g["measured"], g
    assert real_dens["bg_phaladeepika_latta"][1]["label_only"] == ["L3_kala/query_vedha_gochara.ts"]


def test_the_three_earlier_na_assets_read_exactly_the_text_they_read_before(real_dens):
    for a in R02_PRE_N74:
        g, _c = real_dens[a]
        assert g["measured"] == ("STRUCTURAL: 0 module(s) reference it by code in the 3 serving root(s) scanned, and no served select "
                                 "of it exists in the wider source scanned; declaring density_contract: 0"), g


def test_bg_phaladeepika_latta_python_reader_exists_but_is_not_the_served_surface(real_dens):
    """ka_vedha_gochara's writer reads the three vedha tables from Python; the scan does not look there and must not count it."""
    py = (REPO / "platform/python-sidecar/services/ka_vedha_gochara/writer.py").read_text(encoding="utf-8")
    assert "FROM bg_phaladeepika_latta" in py                                  # the reader is real (the test is not vacuous)
    g, cap = real_dens["bg_phaladeepika_latta"]
    assert g["v"] == NA and cap["modules"] == [] and cap["outside"] == [] and cap["outside_named"] == [], (g, cap)


def test_bg_sarvatobhadra_grid_stays_no_detector_because_a_comment_names_it_r51(real_dens):
    g, cap = real_dens["bg_sarvatobhadra_grid"]
    assert g["v"] == NO_DET and cap["comment_only"] and not cap["modules"], (g, cap)


def test_no_pass_partial_or_fail_cell_moves_on_the_real_tree(real_dens):
    from collections import Counter
    c = Counter(g["v"] for g, _cap in real_dens.values())
    assert (c["PASS"], c["PARTIAL"], c["FAIL"]) == (5, 26, 43), c
    assert c["N/A"] == 6 and c["NO_DETECTOR"] == 47, c


def test_a_real_select_is_never_relabelled_on_the_real_tree():
    """bg_texts is selected in SQL (`FROM classical_text_chunks c`) in query_classical_texts.ts: still a reach."""
    cap = ac.capability_scan(ac.CAPS_ROOTS, ["classical_text_chunks", "bg_texts"], shared=frozenset(), columns={},
                             outside_roots=())
    assert "L0_brahmagyan/query_classical_texts.ts" in cap["modules"], cap


# ───────────────────────── R02 decision text, criterion revision, pin ─────────────────────────

def test_R02_decision_text_is_the_cause_keyed_reading_and_cites_N74a():
    t = ac.NA_RULE_DECISIONS["Dens.served#measured:no-served-surface"]
    assert "an asset no served module selects rows from" in t, t
    assert "being named only as a provenance label is not a select" in t, t
    assert "N-74(a)" in t and "N-22" in t and "N-65" in t, t
    assert "not served directly" in t and "not 'unused'" in t and "service_probe envelope is a reach" in t, t
    ac.validate_na_rule_decisions()


def test_the_rule_is_still_cause_keyed_not_asset_keyed():
    ids = [r for r in ac.NA_RULE_DECISIONS if r.startswith("Dens.served")]
    assert ids == ["Dens.served#measured:no-served-surface"], ids
    for a in R02_PRE_N74 + R02_LABEL_REPAIR:
        assert a not in ac.NA_RULE_DECISIONS["Dens.served#measured:no-served-surface"], a


def test_the_python_reader_clause_of_the_old_text_is_gone_and_replaced_by_the_select_reading():
    t = ac.NA_RULE_DECISIONS["Dens.served#measured:no-served-surface"]
    assert "three L0 tables" not in t, t


def test_dens_served_criterion_revision_5_states_the_select_reading():
    e = ac.CRITERION_REGISTRY["Dens.served"]
    assert e["revision"] == 5 and "tier column" in e["applicability"] and "label" in e["applicability"], e


def test_registry_revision_is_14_and_the_declarations_file_is_untouched():
    assert ac.REGISTRY_REVISION == 14
    assert json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["version"] == "1.9.0"


def test_only_dens_served_changed_in_the_criterion_registry_at_14():
    """Everything else in the registry is the rev-13 content: the one revision-5 entry is Dens.served."""
    revs = {k: v["revision"] for k, v in ac.CRITERION_REGISTRY.items() if v["revision"] != 1}
    assert revs.get("Dens.served") == 5
    assert set(ac.NA_CAUSES["Dens.served"]) == {"no-served-surface"}


def test_the_na_cell_is_released_by_the_rule_in_the_rollup_with_the_new_text():
    m = {"Dens.served": dict(v=NA, measured="m", cause="no-served-surface")}
    cell = ac.rollup_asset("L0", m)["Dens"]
    assert cell["v"] == NA and cell["checks"][0]["rule_id"] == "Dens.served#measured:no-served-surface"
    assert "N-74(a)" in cell["checks"][0]["decision"], cell
