"""test_e6_dens_label_select.py: REGISTRY_REVISION 14, SS N-74 item 5 / N-74(a): the Dens.served scanner tells a SELECT from a LABEL by a CLOSED
ALLOW-LIST of label contexts, and R02 is amended to its cause-keyed reading.

  R02 decision text (N-74(a)): "an asset no served module selects rows from; being named only as a provenance label is not a select".

THE DESIGN (strategist, second review): a name is a LABEL only in one of these contexts, and EVERYTHING ELSE is a reach (a module that does not
read as all-label blocks the N/A). There is no consumption tracking and no open-ended shape heuristic.
  (1) an element of `provenance: { tables | source_tables: [ ... ] }` whose provenance-holding object is a property value or a return value of an
      object literal, not a call argument and not a const holder (the real envelope, query_vedha_gochara.ts);
  (2) a string that is the whole value of `source`/`source_table`/`label`/`note`/`reason`/`description`/`message`/`title`, is STRICT prose (>= 5 words
      besides the name, every one purely alphabetic with trailing sentence punctuation only), and sits in an object that is not a call argument;
  (3) the `service_probe` envelope of a SERVICE-kind asset is a reach, at any depth below the marker (a data-kind asset's envelope is not in the
      list either: also a reach);
  (4) an import / require path or a type / interface / enum / class name. A COMMENT blocks (one rule, R51).
Two directions for every pattern: an allow-list context reads N/A, every other form refuses it (each form listed by the two reviews is a test).
Python readers are outside the served surface BY DESIGN: the scan reads `*.ts` under the serving roots only. `ka_vedha_gochara/writer.py` (a
Python L3 writer) DOES read `FROM bg_phaladeepika_latta`; the rule says no SERVED module selects from it, which is true. Dens.served N/A means
"not served directly", NOT "unused". bg_cohort stays NO_DETECTOR (a comment in the same module names it); a later per-asset declared cause, not a
scanner inference from prose. bg_ephemeris_engine / bg_panchanga (registry kind `service`) stay NO_DETECTOR.

KNOWN RESIDUALS (documented, not widened): (a) regex literals holding a bracket / quote can skew the bracket scan; (b) strict prose refuses the
words `table` and `union` by name (`table t_x union all table u` is valid SQL made of alphabetic words) but other all-words SQL forms are not
enumerated; (c) a function RETURNING provenance.tables whose value flows to a same-module generic reader is outside the allow-list's premise.
A data-kind `service_probe` envelope: its own keys (`asset_id` / `endpoint_identity` / `source_ref`) are a reach; a `provenance.tables` element that
happens to sit inside it is still a LABEL for a data-kind asset (a PROBE for a service-kind asset).

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
import _decl_version  # noqa: E402
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


# ───────────────────────── the allow-list: LABEL contexts -> N/A ─────────────────────────

PROV = "export const c = { run: () => ({ provenance: { tables: [%s], source: 'served' } }) }\n"
PROSE = "a note for the reader about t_x and the rows it holds"
LABELS = {
    "provenance-tables-array": PROV % "'kala_x', 't_x', 'other'",
    "provenance-first-element": PROV % "'t_x', 'other'",
    "provenance-last-element": PROV % "'other', 't_x'",
    "provenance-only-element": PROV % "'t_x'",
    "provenance-multiline": "export const c = { run: () => ({ provenance: {\n  tables: [\n    'a',\n    't_x',\n  ],\n } }) }\n",
    "provenance-source_tables-key": "export const c = { run: () => ({ provenance: { source_tables: ['t_x'] } }) }\n",
    "provenance-in-a-returned-object": "export const f = () => { return { content: { rows: [], provenance: { tables: ['t_x'] } }, is_error: false } }\n",
    "provenance-arrow-body-with-a-brace": "export const f = () => { const a = 1; return { provenance: { tables: ['t_x'] } } }\n",
    "provenance-nested-property-values": "export const f = () => { return { a: { b: { provenance: { tables: ['t_x'] } } } } }\n",
    "provenance-with-a-ternary-free-async-return": "export const f = async () => { await g(); return { content: { provenance: { tables: ['t_x', 'u'] } } } }\n",
    "description-prose": "export const c = { description: 'Retrieve the rows for this chart from t_x and show them' }\n",
    "note-prose": "export const c = { note: '" + PROSE + "' }\n",
    "reason-prose": "export const c = { reason: '" + PROSE + "' }\n",
    "message-prose": "export const c = { message: '" + PROSE + "' }\n",
    "title-prose": "export const c = { title: '" + PROSE + "' }\n",
    "label-prose": "export const c = { label: '" + PROSE + "' }\n",
    "source-prose": "export const c = { source: '" + PROSE + "' }\n",
    "source_table-prose": "export const c = { source_table: '" + PROSE + "' }\n",
    "prose-with-the-name-in-parentheses": "export const c = { note: 'Rows come from the store (t_x), nothing else matters here.' }\n",
    "prose-with-trailing-punctuation": "export const c = { note: 'Rows come from the store t_x; nothing else matters here!' }\n",
    "prose-in-a-const-holder-object": "const REF = { description: '" + PROSE + "' }\nexport const ok = 1\n",
    "import-from-path": "import { thing } from './t_x'\nexport const ok = thing\n",
    "import-bare-from": "import thing from 'bg_x'\nexport const ok = thing\n",
    "side-effect-import": "import 't_x'\nexport const ok = 1\n",
    "require-path": "const thing = require('bg_x')\nexport const ok = thing\n",
    "dynamic-import-path": "export const load = () => import('./t_x')\n",
    "export-from-path": "export * from './t_x'\n",
    "interface-name": "export interface t_x { id: string }\nexport const ok = 1\n",
    "type-alias-name": "export type bg_x = { id: string }\nexport const ok = 1\n",
    "enum-name": "export enum t_x { A }\n",
    "class-name": "export class bg_x {}\n",
}


@pytest.mark.parametrize("name", sorted(LABELS))
def test_a_module_that_only_names_the_asset_in_an_allow_list_context_is_not_a_reach_and_reads_na(tree, name):
    ok, d = _is_na(tree, LABELS[name])
    assert ok, (name, d)
    assert "label" in d["measured"], d                                      # the evidence names the label-only module


def test_the_label_only_module_is_listed_not_counted_as_reaching_the_asset(tree):
    tree.write(tree.layers, "tool.ts", LABELS["provenance-tables-array"])
    cap = dr._scan(tree, list(TOKS))
    assert cap["modules"] == [] and cap["label_only"] == ["tool.ts"] and cap["served"] == 0, cap


# ───────────────────────── everything outside the allow-list is a reach -> the N/A is refused ─────────────────────────

SELECTS = {
    # SQL in the literal
    "select-from": "export const q = () => query(`SELECT id FROM t_x WHERE chart_id = $1`, [1])\n",
    "lowercase-select-from": "export const q = () => query('select id from t_x where chart_id = $1', [1])\n",
    "join": "export const q = () => query(`SELECT a.id FROM kala_other a JOIN t_x b ON b.id = a.id`)\n",
    "insert-into": "export const q = () => query(`INSERT INTO t_x (id) VALUES ($1)`, [1])\n",
    "update": "export const q = () => query(`UPDATE t_x SET note = $1 WHERE id = $2`, ['n', 1])\n",
    "delete-from": "export const q = () => query(`DELETE FROM t_x WHERE id = $1`, [1])\n",
    "schema-qualified": "export const q = () => query(`SELECT id FROM public.t_x`)\n",
    "concat-select-then-from-bare-name": "export const q = () => query('SELECT id ' + 'FROM ' + 't_x')\n",
    "concat-lowercase-second-literal": "export const q = () => query('select id ' + 'from t_x where k = $1', [1])\n",
    "comma-join": "export const q = () => query('SELECT a.id FROM kala_other a, t_x b WHERE a.id = b.id')\n",
    "copy-upper": "export const q = () => query('COPY t_x TO STDOUT')\n",
    "copy-lower": "export const q = () => query('copy t_x to stdout')\n",
    "long-lower-case-update": "export const q = () => query('update t_x set col1 = col_b, col2 = col_c, col3 = col_d, col4 = col_e, col5 = col_f')\n",
    "long-lower-case-create-table": "export const q = () => query('create table t_x (id int, name text, note text, created_at timestamptz, kind text)')\n",
    "lower-case-alter-table": "export const q = () => query('alter table t_x add column note text, add column kind text, add column score int')\n",
    "lower-case-drop-table": "export const q = () => query('drop table t_x')\n",
    "table-ddl": "export const q = () => query(`CREATE TABLE t_x (id int)`)\n",
    # the old label forms that are NOT in the closed list
    "label-key-table": "export const c = { meta: { table: 't_x' } }\n",
    "label-key-source_table-string": "export const c = { run: () => ({ source_table: 't_x', rows: [] }) }\n",
    "tables-array-without-provenance": "export const c = { tables: ['t_x', 'other'] }\n",
    "provenance-with-a-different-array-key": "export const c = { run: () => ({ provenance: { sources: ['t_x'] } }) }\n",
    "provenance-array-not-under-provenance": "export const c = { run: () => ({ meta: { tables: ['t_x'] } }) }\n",
    "provenance-tables-with-an-embedded-name": "export const c = { run: () => ({ provenance: { tables: ['t_x as b'] } }) }\n",
    "provenance-tables-with-a-schema-prefix": "export const c = { run: () => ({ provenance: { tables: ['public.t_x'] } }) }\n",
    "provenance-tables-concatenated-element": "export const c = { run: () => ({ provenance: { tables: ['t_x' + s] } }) }\n",
    "provenance-tables-element-in-a-call": "export const c = { run: () => ({ provenance: { tables: [pick('t_x')] } }) }\n",
    "provenance-tables-nested-array": "export const c = { run: () => ({ provenance: { tables: [['t_x']] } }) }\n",
    "provenance-tables-ternary-element": "export const c = { run: () => ({ provenance: { tables: [a ? 't_x' : 'u'] } }) }\n",
    "provenance-in-a-const-holder": "const ENV = { provenance: { tables: ['t_x'] } }\nexport const ok = 1\n",
    "provenance-in-a-call-argument": "export const c = () => send({ provenance: { tables: ['t_x'] } })\n",
    "provenance-in-a-later-call-argument": "export const c = () => send(db, { provenance: { tables: ['t_x'] } })\n",
    "provenance-in-an-array-element": "export const c = () => [{ provenance: { tables: ['t_x'] } }]\n",
    "provenance-in-a-ternary": "export const c = (a: boolean) => (a ? { provenance: { tables: ['t_x'] } } : null)\n",
    "provenance-under-a-property-of-a-call-argument": "export const c = () => send({ content: { provenance: { tables: ['t_x'] } } })\n",
    "provenance-under-a-property-of-a-const-holder": "const R = { content: { provenance: { tables: ['t_x'] } } }\nexport const ok = 1\n",
    "provenance-property-of-a-spread": "export const c = { ...{ provenance: { tables: ['t_x'] } } }\n",
    "asset_id-key": "export const p = { asset_id: 'bg_x', probe_id: 'x_engine' }\n",
    "asset_ids-array": "export const c = { assets: ['bg_x', 'bg_y'] }\n",
    "endpoint-identity-id": "export const p = { endpoint_identity: 'nirmana-elevation:health-probe:bg_x' }\n",
    "source_ref-path": "export const p = { source_ref: 'platform/supabase/migrations/624_probe.sql#bg_x' }\n",
    "probe-envelope-on-a-data-asset": "export const p = { kind: 'service_probe', asset_id: 'bg_x', probe_id: 'x_engine' }\n",
    "map-key": "export const MAP = { t_x: ['marsys://tool/L2/get_signal_embeddings'] }\n",
    "map-key-passed-on": "const M = { t_x: 1 }\nuse(M)\n",
    "name-in-an-unkeyed-array": "export const IDS = ['t_x', 'bg_y']\n",
    "const-name": "const T = 't_x'\nexport const q = () => query(`SELECT * FROM ${T}`)\n",
    "bare-name-in-a-non-label-key": "export const c = { view: 't_x' }\n",
    "chart_summary-map-value": "export const c = { chart_summary: 't_x' }\n",
    "builder-from-call": "export const q = () => db.from('t_x').select('id')\n",
    "builder-into-call": "export const q = () => db.insert().into('t_x')\n",
    "builder-table-call": "export const q = () => knex.table('t_x').where({ id: 1 })\n",
    "bare-name-as-call-argument": "export const q = () => readTable('t_x', 1)\n",
    "identifier-use": "export const q = () => run(t_x)\n",
    "property-access": "export const q = (r: any) => r.t_x\n",
    "ternary-value": "export const q = (a: boolean) => (a ? t_x : null)\n",
    "string-union-type": "export type T = 't_x' | 'other'\n",
    # prose that is NOT strict prose
    "prose-with-parentheses-under-description": "export const c = { description: 'Retrieve the rows for a chart from t_x (the Remedial Matrix) now' }\n",
    "prose-under-a-non-prose-key": "export const c = { summary: '" + PROSE + "' }\n",
    "prose-under-a-notes-key": "export const c = { notes: '" + PROSE + "' }\n",
    "prose-without-a-key": "export const m = (id: string) => `no rows in t_x for chart ${id}: the build has not produced anchors yet`\n",
    "prose-of-four-words": "export const c = { note: 'one two t_x three four' }\n",
    "prose-with-a-hyphenated-word": "export const c = { note: 'a cohort-scored note for the reader about t_x here' }\n",
    "prose-with-a-digit": "export const c = { note: 'a note for the reader about t_x and 150 rows' }\n",
    "prose-with-an-identifier-word": "export const c = { note: 'a note for the reader about t_x and chart_planet_positions' }\n",
    "prose-with-a-quote": "export const c = { note: 'a note for the reader about t_x and the \\'rows\\' it holds' }\n",
    "prose-as-a-call-argument-object": "export const c = () => send({ note: '" + PROSE + "' })\n",
    "prose-as-a-later-call-argument-object": "export const c = () => send(db, { note: '" + PROSE + "' })\n",
    "prose-in-a-spread-object": "export const c = { ...{ note: '" + PROSE + "' } }\n",
    "prose-concatenated": "export const c = { note: 'a note for the reader about t_x ' + 'and the rows it holds' }\n",
    "prose-name-head-of-a-concatenation": "export const c = { note: s + 't_x a note for the reader about and rows here' }\n",
    # MEDIUM-1: identifiers that look like words
    "snake-case-list-comma": "export const q = () => loadAll(db, 'chart_planet_positions,chart_house_cusps,t_x')\n",
    "snake-case-list-spaces": "export const q = () => loadAll(db, 'chart_planet_positions chart_house_cusps t_x')\n",
    "alias-with-a-snake-case-word": "export const q = () => db('t_x as latest_snapshot_per_chart')\n",
    "json-array-string": "export const q = () => JSON.parse('[\"chart_planet_positions\",\"chart_house_cusps\",\"t_x\"]')\n",
    "json-array-string-under-note": "export const c = { note: '[\"chart_planet_positions\",\"chart_house_cusps\",\"t_x\"]' }\n",
    "snake-case-prose-under-description": "export const c = { description: 'chart_planet_positions chart_house_cusps t_x chart_dashas chart_facts' }\n",
    "knex-alias-string": "export const q = () => knex('bg_x as b')\n",
    "builder-alias-string": "export const q = () => db.from('t_x a')\n",
    "builder-schema-qualified-string": "export const q = () => db.from('app.t_x')\n",
    "comma-list-of-tables": "export const q = () => readTables('t_x,t_y')\n",
    "two-names-in-one-string": "export const q = () => run('t_x t_y')\n",
    "sql-prefix-in-a-variable": "const A = 'SELECT * FROM '\nexport const q = () => query(A + `${'t_x'}`)\n",
    "call-argument-in-a-template-interpolation": "export const m = async () => `rows: ${await readTable('t_x')}`\n",
    "call-argument-in-a-prose-template": "export const m = async () => `Fetched the rows for this chart just now: ${await readTable('t_x')} and more`\n",
    "nested-interpolation-call": "export const m = async () => `a ${ok ? `${readTable('t_x')}` : ''} b`\n",
    # MEDIUM-2: same-module readers of the old label keys (none of them is a label any more)
    "label-key-read-through-this": "export const c = { table: 't_x', run() { return read(this.table) } }\n",
    "const-array-of-table-objects-iterated": "const SRC = [{ table: 't_x' }]\nfor (const s of SRC) fetchRows(db, s)\n",
    "const-array-of-table-objects-mapped": "const SRC = [{ table: 't_x' }]\nexport const r = SRC.map((s) => fetchRows(db, s))\n",
    "const-array-passed-to-a-call": "const SRC = [{ table: 't_x' }]\nloadAll(db, SRC)\n",
    "nested-holder-passed-to-a-call": "const CFG = { reads: { table: 't_x' } }\nloadAll(db, CFG)\n",
    "nested-holder-property-passed": "const CFG = { reads: { table: 't_x' } }\nload(db, CFG.reads)\n",
    "nested-assets-tables": "const CFG = { assets: { tables: ['t_x'] } }\nexport const ok = 1\n",
    "inline-array-of-table-objects-as-argument": "loadAll(db, [{ table: 't_x' }])\n",
    "inline-nested-reads-as-argument": "loadAll(db, { reads: [{ table: 't_x' }] })\n",
    "inline-ternary-object-as-argument": "loadAll(db, c ? { table: 't_x' } : null)\n",
    "inline-array-mapped": "export const r = [{ table: 't_x' }].map((s) => fetchRows(db, s))\n",
    "wrapper-array-go": "const REF = { table: 't_x' }\ngo([REF])\n",
    "wrapper-as-cast": "const REF = { table: 't_x' }\ngo(REF as Src)\n",
    "wrapper-non-null": "const REF = { table: 't_x' }\ngo(REF!)\n",
    "wrapper-ternary": "const REF = { table: 't_x' }\ngo(c ? REF : null)\n",
    "wrapper-nullish": "const REF = { table: 't_x' }\ngo(REF ?? d)\n",
    "wrapper-template": "const REF = { table: 't_x' }\ngo(`${REF}`)\n",
    "alias-of-the-holder": "const REF = { table: 't_x' }\nconst R2 = REF\nload(R2)\n",
    "label-key-read-through-property": "const c = { table: 't_x' }\nexport const v = c.table\n",
    "label-key-read-through-brackets": "const c = { table: 't_x' }\nexport const v = c['table']\n",
    "label-key-read-through-destructure": "const c = { table: 't_x' }\nconst { table } = c\n",
    "label-object-literal-as-call-argument": "register({ tables: ['t_x'] })\n",
    "label-object-literal-in-new-expression": "new Probe({ asset_id: 't_x' })\n",
    # L-a: a URL path read
    "url-template-read": "export const r = () => fetch(`${BASE}/rest/v1/t_x?select=*`)\n",
    "url-literal-read": "export const r = () => fetch('/rest/v1/t_x?select=*')\n",
    "url-literal-read-without-select": "export const r = () => fetch('/rest/v1/t_x?id=1')\n",
    "url-template-read-without-select": "export const r = () => fetch(`${BASE}/rest/v1/t_x?id=1`)\n",
    "url-with-a-hash": "export const r = () => get('/api/t_x#top')\n",
    "colon-id": "export const p = { note: 'health-probe:t_x' }\n",
    "path-with-hash": "export const p = { note: 'migrations/624_probe.sql#t_x' }\n",
    # concatenation / interpolation of a name
    "name-flush-before-interpolation": "export const q = (s: string) => `t_x${s}`\n",
    "name-flush-after-interpolation": "export const q = (p: string) => `${p}t_x`\n",
    "name-flush-end-of-literal-then-concat": "export const q = (s: string) => ('x t_x' + s)\n",
    "name-flush-start-of-literal-after-concat": "export const q = (s: string) => (s + 't_x y')\n",
    "sql-prose-hybrid": "export const c = { description: 'SELECT the rows from t_x for the chart' }\n",
    "fragment-from-name": "export const q = (s: string) => query(s + ' from t_x x')\n",
    "dynamic-from-run-time-name": "export const c = { tables: ['t_x'] }\nexport const q = (t: string) => query(`SELECT id FROM ${t}`)\n",
    "builder-with-variable": "export const c = { tables: ['t_x'] }\nexport const q = (t: string) => db.from(t).select('id')\n",
}


@pytest.mark.parametrize("name", sorted(SELECTS))
def test_every_form_outside_the_allow_list_refuses_the_na(tree, name):
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
    tree.write(tree.layers / "L0_x", "real.ts", dr._cap("SELECT id, tier FROM t_x"))
    tree.write(tree.tools, "label.ts", LABELS["provenance-tables-array"])
    cap = dr._scan(tree, list(TOKS), columns={"t_x": ["id", "tier"]})
    d = ac._grade_dens(cap, "t_x")
    assert d["v"] == ac.PASS, d
    assert cap["modules"] == ["L0_x/real.ts"] and len(cap["label_only"]) == 1 and cap["label_only"][0].endswith("/label.ts"), cap


def test_a_label_only_module_beside_a_served_select_elsewhere_still_reads_fail(tree):
    tree.write(tree.layers / "L0_x", "real.ts", dr._cap("SELECT id FROM t_x", contract=False))
    tree.write(tree.tools, "label.ts", LABELS["provenance-tables-array"])
    d = ac._grade_dens(dr._scan(tree, list(TOKS)), "t_x")
    assert d["v"] == ac.FAIL, d


def test_a_label_in_one_module_and_an_unclassifiable_name_in_another_still_refuses_the_na(tree):
    tree.write(tree.tools, "label.ts", LABELS["provenance-tables-array"])
    tree.write(tree.lib, "other.ts", SELECTS["name-in-an-unkeyed-array"])
    d = ac._grade_dens(dr._scan(tree, list(TOKS)), "t_x")
    assert d["v"] == NO_DET and "no served" in d["measured"], d


def test_a_shared_table_select_in_a_capability_that_names_the_asset_by_label_still_attributes_it(tree):
    """Attribution is unchanged: the asset id in a capability (even as a label) attributes that capability's shared-table select."""
    tree.write(tree.layers, "tool.ts", "export const cap = {\n  id: 'x',\n  asset_id: 'bg_x',\n  run: () => query(`SELECT id FROM t_shared`),\n}\n")
    cap = dr._scan(tree, ["t_shared", "bg_x"], shared={"t_shared"})
    assert cap["served"] == 1 and cap["modules"] == ["tool.ts"], cap


def test_a_label_next_to_a_real_pass_is_named_in_the_evidence_text_and_the_count_excludes_it(tree):
    tree.write(tree.layers / "L0_x", "real.ts", dr._cap("SELECT id, tier FROM t_x"))
    tree.write(tree.tools, "label.ts", LABELS["provenance-tables-array"])
    d = ac._grade_dens(dr._scan(tree, list(TOKS), columns={"t_x": ["id", "tier"]}), "t_x")
    assert d["v"] == ac.PASS and "1 module(s) reach it by code: L0_x/real.ts (+1 name it only as a label)" in d["measured"], d


def test_the_na_evidence_names_every_label_only_module(tree):
    tree.write(tree.layers, "a.ts", LABELS["provenance-tables-array"])
    tree.write(tree.layers, "b.ts", LABELS["description-prose"])
    d = ac._grade_dens(dr._scan(tree, list(TOKS)), "t_x")
    assert d["v"] == NA and "2 module(s) name it only as a label" in d["measured"] and "a.ts" in d["measured"] and "b.ts" in d["measured"], d
    assert d["measured"].startswith("STRUCTURAL: 0 module(s) reference it by code in the 3 serving root(s) scanned"), d


# ───────────────────────── the other branches are untouched ─────────────────────────

def test_a_comment_only_mention_still_blocks_the_na_r51(tree):
    d, cap = _verdict(tree, "// served elsewhere: t_x, bg_x\nexport {}\n")
    assert d["v"] == NO_DET and "comments only" in d["measured"], d


def test_a_label_in_code_and_a_comment_in_another_module_keeps_the_na_blocked_by_the_comment(tree):
    tree.write(tree.tools, "label.ts", LABELS["provenance-tables-array"])
    tree.write(tree.lib, "note.ts", "// reads bg_x through a generic route\nexport {}\n")
    d = ac._grade_dens(dr._scan(tree, list(TOKS)), "t_x")
    assert d["v"] == NO_DET and "comments only" in d["measured"], d


def test_a_desynced_serving_file_is_still_unparsed_not_read_for_labels(tree):
    d, cap = _verdict(tree, "if (x) /'/.test(y);\nexport const c = { asset_id: 'bg_x' }\n")
    assert d["v"] == NO_DET and cap["unparsed"] == ["tool.ts"] and not cap["label_only"], (d, cap)


def test_a_label_in_the_serving_roots_does_not_hide_a_served_select_outside_them(tree):
    tree.write(tree.tools, "label.ts", LABELS["provenance-tables-array"])
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


# ───────────────────────── SQL signals, concatenation chains, comments ─────────────────────────

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


def test_a_comment_between_concatenated_literals_does_not_break_the_join():
    assert _kinds("run('select a ' + /* the table */ 'from t_x')") == ["select"]
    assert _kinds("run('select a ' + // the table\n 'from t_x')") == ["select"]


def test_a_neighbour_literal_connected_by_plus_or_comma_lends_its_sql_signal_but_a_distant_one_does_not():
    assert _kinds("run('SELECT a ' + 'from t_x')") == ["select"]
    assert _kinds("run(['SELECT a', 'from t_x'])") == ["select"]
    assert _kinds("run('SELECT a ' + \n 'from t_x')") == ["select"]
    far = "const a = 'SELECT 1'\nconst z = 5\nexport const c = { note: 'Returns rows for a chart from the sidecar service t_x here.' }"
    assert _kinds(far) == ["label"]
    near = "const a = 'SELECT 1' + 'Returns rows for a chart from the sidecar service t_x here.'"
    assert _kinds(near) == ["select"]


def test_the_concatenation_chain_reaches_two_literals_each_way_and_no_further():
    assert _kinds("run('SELECT a ' + 'b ' + 't_x z')") == ["select"]
    assert _kinds("run('t_x z' + ' b' + ' FROM x')") == ["select"]
    assert _kinds("run('SELECT a ' + 'b ' + 'c ' + 't_x z')") == ["ambiguous"]
    assert _kinds("run('t_x z' + ' b' + ' c' + ' FROM x')") == ["ambiguous"]





def test_an_upper_case_table_keyword_alone_is_a_select_signal():
    assert _kinds("run('TABLE t_x')") == ["select"]


def test_a_comment_in_the_same_module_as_label_only_code_blocks_the_na(tree):
    d, cap = _verdict(tree, LABELS["provenance-tables-array"] + "// t_x is served through a generic route\n")
    assert d["v"] == NO_DET and cap["label_only"] == ["tool.ts"] and cap["label_comment"] == ["tool.ts"], (d, cap)
    assert "comment" in d["measured"] and "never the closable N/A" in d["measured"], d
    assert d["measured"].startswith("NO_DETECTOR"), d


@pytest.mark.parametrize("comment", ["// bg_x serves it\n", "/* t_x is read elsewhere */\n", "/**\n * t_x\n */\n"])
def test_every_comment_form_naming_either_token_blocks(tree, comment):
    d, cap = _verdict(tree, LABELS["provenance-tables-array"] + comment)
    assert d["v"] == NO_DET and cap["label_comment"] == ["tool.ts"], (comment, d)


def test_the_same_label_only_module_without_a_comment_still_reads_na_and_names_no_comment(tree):
    d, cap = _verdict(tree, LABELS["provenance-tables-array"])
    assert d["v"] == NA and cap["label_comment"] == [], (d, cap)
    d, cap = _verdict(tree, LABELS["provenance-tables-array"] + "// an unrelated note\n")
    assert d["v"] == NA and cap["label_comment"] == [], (d, cap)


def test_a_comment_in_another_module_blocks_and_a_comment_in_a_hit_module_changes_nothing(tree):
    tree.write(tree.layers, "label.ts", LABELS["provenance-tables-array"])
    tree.write(tree.layers, "note.ts", "// t_x\nexport {}\n")
    d = ac._grade_dens(dr._scan(tree, list(TOKS)), "t_x")
    assert d["v"] == NO_DET and "comments only" in d["measured"], d
    d, cap = _verdict(tree, "// t_x\nexport const q = () => query(`SELECT id FROM t_x`)\n", name="sel.ts")
    assert d["v"] == ac.FAIL, d


def test_a_comment_inside_a_string_is_not_a_comment(tree):
    d, cap = _verdict(tree, "export const c = { source: 'see http://x/t_x for the long form of this page' }\n")
    assert d["v"] == NO_DET and cap["label_comment"] == [] and cap["comment_only"] == [] and cap["modules"] == ["tool.ts"], (d, cap)


# ───────────────────────── the classifier itself (unit level) ─────────────────────────

def _kinds(src, tok="t_x", service=False):
    return ac._ref_kinds(src, tok, service)


@pytest.mark.parametrize("src, want", [
    ("export const f = () => ({ provenance: { tables: ['t_x'] } })", ["label"]),
    ("export const f = () => { return { provenance: { tables: ['a', 't_x', 'b'] } } }", ["label"]),
    ("export const f = () => { return { provenance: { source_tables: ['t_x'] } } }", ["label"]),
    ("export const f = () => { return { 'provenance': { 'tables': ['t_x'] } } }", ["label"]),
    ("export const f = () => { return { provenance: { tables: [ 't_x' ] } } }", ["label"]),
    ("export const f = () => { return { PROVENANCE: { Tables: ['t_x'] } } }", ["label"]),
    ("export const f = () => { return { content: { provenance: { tables: ['t_x'] } } } }", ["label"]),
    ("export const f = () => { return ({ provenance: { tables: ['t_x'] } }) }", ["label"]),
    ("const f = () => ({ provenance: { tables: ['t_x'] } })", ["label"]),
    ("export const f = () => { return { provenance: { tables: [\"t_x\"] } } }", ["label"]),
    ("export const f = () => { return { provenance: { tables: [`t_x`] } } }", ["label"]),
    ("export const f = () => { return { provenance: { tables: ['t_x'], backing_data_reachable: true } } }", ["label"]),
    ("export const f = () => { return { provenance: { source: 'x', tables: ['t_x'] } } }", ["label"]),
    # outside the envelope
    ("export const f = () => { return { prov: { tables: ['t_x'] } } }", ["ambiguous"]),
    ("export const f = () => { return { provenance: { table: ['t_x'] } } }", ["ambiguous"]),
    ("export const f = () => { return { provenance: { tables: 't_x' } } }", ["ambiguous"]),
    ("export const f = () => { return { provenance: [ { tables: ['t_x'] } ] } }", ["ambiguous"]),
    ("export const f = () => { return { provenance: { tables: { a: 't_x' } } } }", ["ambiguous"]),
    ("export const f = () => { return { provenance: { x: { tables: ['t_x'] } } } }", ["ambiguous"]),
    ("export const f = () => { return provenance({ tables: ['t_x'] }) }", ["ambiguous"]),
    ("const a = x ? 1 : { provenance: { tables: ['t_x'] } }", ["ambiguous"]),
    ("const a = { provenance: { tables: ['t_x'] } }", ["ambiguous"]),
    ("let a; a = { provenance: { tables: ['t_x'] } }", ["ambiguous"]),
    ("export const f = () => { return { provenance: { tables: ['t_x', ...more] } } }", ["label"]),
    # strict prose
    ("export const c = { note: 'one two three four five t_x' }", ["label"]),
    ("export const c = { note: 'one two three four t_x' }", ["ambiguous"]),
    ("export const c = { Note: 'one two three four five t_x' }", ["label"]),
    ("export const c = { 'note': 'one two three four five t_x' }", ["label"]),
    ("export const c = { note: 'one two three four five (t_x)' }", ["label"]),
    ("export const c = { note: 'one two three four five (t_x).' }", ["label"]),
    ("export const c = { note: 'one two t_x, three four five.' }", ["label"]),
    ("export const c = { note: 'One two. Three four five: t_x!' }", ["label"]),
    ("export const c = { note: 'one two three four five xt_x' }", []),
    ("export const c = { note: 'one two three four five t_x1' }", []),
    ("export const c = { note: 'one two three (four) five t_x' }", ["ambiguous"]),
    ("export const c = { note: 'one two three four five t_x =' }", ["ambiguous"]),
    ("export const c = { note: 'one two three four five * t_x' }", ["ambiguous"]),
    ("export const c = { note: 'one two three four five 7 t_x' }", ["ambiguous"]),
    ("export const c = { note: 'one two three four five a_b t_x' }", ["ambiguous"]),
    ("export const c = { note: 'one two three four five a-b t_x' }", ["ambiguous"]),
    ("export const c = { note: 'one two three four five t_x/t_y' }", ["ambiguous"]),
    ("export const c = { note: 'one two three four five \"t_x\"' }", ["ambiguous"]),
    ("export const c = { note: `one two three four five t_x` }", ["label"]),
    ("export const c = { note: `one two ${a} three four five t_x` }", ["ambiguous"]),
    ("export const c = { note: 'one two three four five t_x' + s }", ["ambiguous"]),
    ("export const c = { note: s + 'one two three four five t_x' }", ["ambiguous"]),
    ("export const c = { note: 'one two three four five t_x' }, y = 1", ["label"]),
    ("run({ note: 'one two three four five t_x' })", ["ambiguous"]),
    ("run(a, { note: 'one two three four five t_x' })", ["ambiguous"]),
    ("run(a)({ note: 'one two three four five t_x' })", ["ambiguous"]),
    ("run[a]({ note: 'one two three four five t_x' })", ["ambiguous"]),
    ("new Run({ note: 'one two three four five t_x' })", ["ambiguous"]),
    ("return ({ note: 'one two three four five t_x' })", ["label"]),
    ("const c = ({ note: 'one two three four five t_x' })", ["label"]),
    ("f = () => ({ note: 'one two three four five t_x' })", ["label"]),
    ("const c = [{ note: 'one two three four five t_x' }]", ["label"]),
    ("const c = [x, { note: 'one two three four five t_x' }]", ["label"]),
    ("run(...{ note: 'one two three four five t_x' })", ["ambiguous"]),
    ("export const c = { x: 1, reason: 'one two three four five t_x' }", ["label"]),
    ("export const c = { a: { message: 'one two three four five t_x' } }", ["label"]),
    ("export const c = { description: 'one two three four five t_x' }", ["label"]),
    ("export const c = { title: 'one two three four five t_x' }", ["label"]),
    ("export const c = { label: 'one two three four five t_x' }", ["label"]),
    ("export const c = { source: 'one two three four five t_x' }", ["label"]),
    ("export const c = { source_table: 'one two three four five t_x' }", ["label"]),
    ("export const c = { sources: 'one two three four five t_x' }", ["ambiguous"]),
    ("export const c = { text: 'one two three four five t_x' }", ["ambiguous"]),
    ("export const c = { x: 'one two three four five t_x' }", ["ambiguous"]),
    ("export const c = { a ? note : 'one two three four five t_x' }", ["ambiguous"]),
    ("export const c = { note: 'one two three four five t_x and again t_x' }", ["label", "label"]),
    ("export const c = { note: 'one two three four five t_x and again t_x_y' }", ["ambiguous"]),
    # SQL, imports, types
    ("run('SELECT a FROM t_x')", ["select"]),
    ("import x from 't_x'", ["label"]),
    ("import { a, b } from \"t_x\"", ["label"]),
    ("export * from 't_x'", ["label"]),
    ("import 't_x'", ["label"]),
    ("const m = require('t_x')", ["label"]),
    ("const m = await import('t_x')", ["label"]),
    ("register('t_x')", ["ambiguous"]),
    ("x.from('t_x')", ["ambiguous"]),
    ("from('t_x')", ["ambiguous"]),
    ("import a from 'x-t_x'", ["label"]),
    ("import a from './t_x/index'", ["label"]),
    ("type t_x = number", ["label"]),
    ("interface t_x { a: 1 }", ["label"]),
    ("enum t_x { A }", ["label"]),
    ("class t_x {}", ["label"]),
    ("const t_x = 1", ["ambiguous"]),
    ("const m = { t_x: 1 }", ["ambiguous"]),
    ("// t_x in a comment\nexport const c = 1", []),
    ("export const c = { x: 'ok' }", []),
])
def test_closed_list_unit_table(src, want):
    assert _kinds(src) == want, (src, _kinds(src))


@pytest.mark.parametrize("src, want", [
    ("run(provenance: { tables: ['t_x'] })", ["ambiguous"]),
    ("return (x, provenance: { tables: ['t_x'] })", ["ambiguous"]),                # the holder is not an object literal
    ("export const f = () => { return { provenance: { tables: ['a]b', 't_x'] } } }", ["label"]),    # a bracket inside a string is not structure
    ("export const f = () => { return { provenance: { tables: ['a[b', 't_x'] } } }", ["label"]),
    ("import('./${ t_x')", ["label"]),                                                # `${` in a plain-quoted string is text, not an interpolation
    ("return (x, b: { provenance: { tables: ['t_x'] } })", ["ambiguous"]),         # a parent that is not an object literal
    ("export const f = () => { return { x: a ? 1 : { provenance: { tables: ['t_x'] } } } }", ["ambiguous"]),   # a ternary colon is not a property
    ("export const f = () => { throw { provenance: { tables: ['t_x'] } } }", ["ambiguous"]),                  # only `return` / an arrow body returns
    ("export const f = () => { yield { provenance: { tables: ['t_x'] } } }", ["ambiguous"]),
    ("export const f = () => { return { provenance: { tables: [cond && 't_x', 'u'] } } }", ["ambiguous"]),   # the element's predecessor
    ("export const f = () => { return { provenance: { tables: ['t_x'.toString()] } } }", ["ambiguous"]),      # the element's successor
    ("export const f = () => { return { provenance: { tables: [a, 't_x'] } } }", ["label"]),
    ("run(a, note: 'one two three four five t_x')", ["ambiguous"]),                   # the prose object is not an object literal
    ("run(a)[b, { note: 'one two three four five t_x' }]", ["label"]),                # a later ELEMENT of an array is not a later call argument
    ("import(`./${readTable('t_x')}`)", ["ambiguous"]),                               # code inside an interpolation, even in an import
    ("import(`./${ ({a: 1}).a + g('t_x') }`)", ["ambiguous"]),
    ("import(`${p}t_x`)", ["ambiguous"]),                                              # glued to a closed interpolation
    ("import(`t_x${p}`)", ["ambiguous"]),
    ("import(`./t_x`)", ["label"]),
    ("require('t_x' + s)", ["ambiguous"]),                                             # the tail of a concatenation, even in a require
    ("require('t_x'.concat(s))", ["ambiguous"]),
])
def test_closed_list_edge_cases(src, want):
    assert _kinds(src) == want, (src, _kinds(src))


@pytest.mark.parametrize("w", ["return", "await", "yield", "typeof", "void", "throw", "delete"])
def test_a_grouping_paren_after_one_of_these_words_is_not_a_call(w):
    src = f"f = () => {{ {w} ({{ note: 'one two three four five t_x' }}) }}"
    assert _kinds(src) == ["label"], (w, _kinds(src))


@pytest.mark.parametrize("w", ["run", "of", "in", "case", "foo_bar", "x1", "$f"])
def test_a_paren_after_any_other_word_is_a_call(w):
    src = f"{w} ({{ note: 'one two three four five t_x' }})"
    assert _kinds(src) == ["ambiguous"], (w, _kinds(src))


@pytest.mark.parametrize("prefix, want", [
    ("return ", "label"), ("=> ", "label"), ("=> (", "label"), ("return (", "label"), ("= ", "label"), (": ", "label"), ("[", "label"),
    ("f(", "ambiguous"), ("f(a, ", "ambiguous"), ("f(a)(", "ambiguous"), ("new F(", "ambiguous"), ("...", "ambiguous"),
])
def test_the_object_call_argument_guard_for_prose(prefix, want):
    close = {"(": ")", "f(": ")", "f(a, ": ")", "f(a)(": ")", "new F(": ")", "[": "]", "return (": ")", "=> (": ")", "(": ")"}.get(prefix, "")
    src = f"{prefix}{{ note: 'one two three four five t_x' }}{close}"
    assert _kinds(src) == [want], (prefix, _kinds(src))


@pytest.mark.parametrize("c, tok, want", [
    ("one two three four five t_x", "t_x", True),
    ("one two three four t_x", "t_x", False),
    ("one two three four five", "t_x", False),                          # the name does not occur
    ("one two three four five six", "t_x", False),
    ("t_x", "t_x", False),
    ("one two three four five t_x.", "t_x", True),
    ("one two three four five (t_x)", "t_x", True),
    ("one two three four five (t_x),", "t_x", True),
    ("one two three four five t_x;", "t_x", True),
    ("one two three four five (t_x", "t_x", True),
    ("one two three four five t_x)", "t_x", True),
    ("one two three four five t_x?!", "t_x", True),
    ("one,two three four five six t_x", "t_x", False),               # a comma BETWEEN words (a list) is not trailing punctuation
    ("one two three four five six t_x t_x", "t_x", True),
    ("one two three four five x_t", "t_x", False),
    ("one two three four five t_x_", "t_x", False),
    ("one two three four five t-x", "t_x", False),
    ("one two three4 four five six t_x", "t_x", False),
    ("one two three four five six_ t_x", "t_x", False),
    ("one two three four five (six) t_x", "t_x", False),
    ("one two three four five six= t_x", "t_x", False),
    ("one two three four five six* t_x", "t_x", False),
    ("one two three four five 'six' t_x", "t_x", False),
    ("one two three four five \"six\" t_x", "t_x", False),
    ("one two three four five `six` t_x", "t_x", False),
    ("one two three four five a-b t_x", "t_x", False),
    ("one two three four five a,b t_x", "t_x", False),
    ("one two three four five a.b t_x", "t_x", False),
    ("one\ttwo\nthree four five six t_x", "t_x", True),
    ("chart_planet_positions chart_house_cusps t_x chart_dashas chart_facts", "t_x", False),
])
def test_strict_prose_unit(c, tok, want):
    assert ac._strict_prose(c, tok) is want, (c, ac._strict_prose(c, tok))


def test_the_allow_list_vocabularies_are_the_documented_closed_sets():
    assert ac.PROV_ARRAY_KEYS == frozenset({"tables", "source_tables"})
    assert ac.PROSE_KEYS == frozenset({"source", "source_table", "label", "note", "reason", "description", "message", "title"})


@pytest.mark.parametrize("src, want", [
    ("run('t_x')", ["ambiguous"]),
    ("run('t_x as b')", ["ambiguous"]),
    ("run('t_x a')", ["ambiguous"]),
    ("run('app.t_x')", ["ambiguous"]),
    ("run('t_x,t_y')", ["ambiguous"]),
    ("run('[\"t_x\"]')", ["ambiguous"]),
    ("run('COPY t_x TO STDOUT')", ["select"]),
    ("run('copy t_x to stdout')", ["select"]),
    ("run('copy t_x (id) from stdin')", ["select"]),
    ("run('update t_x set a = b')", ["select"]),
    ("run('update t_x a set a = b')", ["select"]),
    ("run('update only t_x set a = b')", ["select"]),
    ("run('create table t_x (id int)')", ["select"]),
    ("run('create or replace view t_x as x')", ["select"]),
    ("run('create unlogged table t_x (a int)')", ["select"]),
    ("run('create materialized view t_x as x')", ["select"]),
    ("run('create global temporary table t_x (a int)')", ["select"]),
    ("run('create index t_x')", ["select"]),
    ("run('alter table t_x add c int')", ["select"]),
    ("run('alter view t_x rename')", ["select"]),
    ("run('drop table t_x')", ["select"]),
    ("run('drop index t_x')", ["select"]),
    ("run(`${await readTable('t_x')}`)", ["ambiguous"]),
    ("run(`Fetched the rows for this chart just now: ${await readTable('t_x')} and more`)", ["ambiguous"]),
    ("run(`${a}${b ? 't_x' : 'u'} text`)", ["ambiguous"]),
    ("run(`a ${ {x: 1}.x } then some words around t_x for the reader here`)", ["ambiguous"]),
    ("run('a note ${ about t_x for the reader here')", ["ambiguous"]),
    ("run(`a note ${ about t_x for the reader here`)", ["ambiguous"]),
    ("run(`Fetched the rows for this chart ${ ({a: 1}).a + readTable('t_x') } and more`)", ["ambiguous"]),
    ("run(`${p}t_x and four more words after it here`)", ["ambiguous"]),
    ("run(`words before and more words t_x${s} here`)", ["ambiguous"]),
    ("run(prefix + 't_x and four more words after it here')", ["ambiguous"]),
    ("run('words before and more words then t_x' + suffix)", ["ambiguous"]),
    ("run('words before and more words then t_x'.concat(suffix))", ["ambiguous"]),
    ("run('TABLE t_x')", ["select"]),
    ("run('COPY t_x')", ["select"]),
    ("run('./t_x')", ["ambiguous"]),
    ("run('a/b/t_x')", ["ambiguous"]),
    ("run('f.sql#t_x')", ["ambiguous"]),
    ("run('t_x:note')", ["ambiguous"]),
    ("run('health-probe:t_x')", ["ambiguous"]),
    ("run(`${BASE}/rest/v1/t_x?select=*`)", ["select"]),
    ("run('/rest/v1/t_x?select=*')", ["select"]),
    ("run(`${BASE}/rest/v1/t_x?id=1`)", ["ambiguous"]),
    ("run('/rest/v1/t_x?id=1')", ["ambiguous"]),
    ("run('/rest/v1/t_x')", ["ambiguous"]),
])
def test_forms_outside_the_allow_list_unit_table(src, want):
    assert _kinds(src) == want, (src, _kinds(src))


@pytest.mark.parametrize("src", [
    "export const c = { x: 'insert into t_x (id) values (1)' }",
    "export const c = { x: 'delete from t_x'}",
    "export const c = { x: 'merge into t_x using s' }",
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
    "export const c = { x: 'CREATE TABLE t_x' }",
    "export const c = { x: 't_x SET note = 1' }",
    "export const c = { x: 'WHERE t_x' }",
    "export const c = { x: 't_x RETURNING id' }",
    "export const c = { x: 't_x UNION' }",
    "export const c = { x: 'select 1 union select 2 from t_x' }",
    "export const c = { x: 'x $1 t_x' }",
    "export const c = { x: 't_x::text' }",
    "export const c = { x: 'FROM t_x' }",
    "export const c = { x: 'JOIN t_x' }",
    "export const c = { x: 'INTO t_x' }",
    "export const c = { x: 'UPDATE t_x' }",
    "export const c = { x: 'TRUNCATE t_x' }",
    "export const c = { x: 'ON CONFLICT t_x' }",
])
def test_every_sql_signal_unit_marks_the_literal_a_select(src):
    assert _kinds(src) == ["select"], (src, _kinds(src))


@pytest.mark.parametrize("src", [
    "export const c = { note: 'a note on returning t_x rows quickly to the caller' }",
    "export const c = { note: 'we truncate the list shown for t_x in the view' }",
    "export const c = { note: 'a where clause on t_x is not used here' }",
    "export const c = { note: 'the selected rows and updated notes for t_x joined view subselect' }",
    "export const c = { note: 'lower copy t_x for the reader of this page now' }",
])
def test_lower_case_sql_looking_words_in_strict_prose_are_not_a_select_signal(src):
    assert _kinds(src) == ["label"], (src, _kinds(src))


def test_the_prose_threshold_is_exactly_five_words_besides_the_name():
    assert ac._strict_prose("one two three four five t_x", "t_x") and not ac._strict_prose("one two three four t_x", "t_x")


def test_every_occurrence_is_classified_and_one_ambiguous_one_decides():
    kinds = _kinds("export const c = { note: 'one two three four five t_x', run: () => query('SELECT 1 FROM t_x') }")
    assert kinds == ["label", "select"], kinds
    assert ac._module_reaches(kinds) and not ac._module_reaches(["label", "label"]) and not ac._module_reaches([])


def test_a_label_in_one_token_and_an_ambiguous_form_of_another_token_is_one_reach(tree):
    """`kinds` is read over EVERY referencing token of the asset (the table AND the asset id), not the first only."""
    d, cap = _verdict(tree, LABELS["provenance-tables-array"] + "export const IDS = ['bg_x']\n")
    assert d["v"] == NO_DET and cap["modules"] == ["tool.ts"] and not cap["label_only"], (d, cap)
    d, cap = _verdict(tree, "export const IDS = ['t_x']\n" + PROV % "'bg_x'")
    assert d["v"] == NO_DET and cap["modules"] == ["tool.ts"], (d, cap)
    d, cap = _verdict(tree, PROV % "'t_x', 'bg_x'")
    assert d["v"] == NA and cap["label_only"] == ["tool.ts"], (d, cap)


def test_a_comment_naming_the_table_while_the_code_labels_the_asset_id_blocks_here(tree):
    d, cap = _verdict(tree, "// reads t_x\n" + PROV % "'bg_x'")
    assert d["v"] == NO_DET and cap["label_comment"] == ["tool.ts"], (d, cap)


# ───────────────────────── third review: L1 (a served select beside a provenance label), L2 (generic / optional calls), L3 (import methods), L5 ─────────────────────────

def test_a_provenance_label_beside_a_served_select_in_the_same_declaration_is_served_not_na(tree):
    """`if not sels and not _module_reaches(kinds)`: a module whose only occurrence of the asset is a provenance label is NOT label-only when the SAME
    declaration holds a strict served select of a table the asset shares (attribution by the asset id): it is served (FAIL), never the N/A."""
    tree.write(tree.layers, "tool.ts",
               "export const cap = {\n  id: 'x',\n  run: () => {\n    query(`SELECT id FROM t_shared`)\n"
               "    return { provenance: { tables: ['bg_x'] } }\n  },\n}\n")
    cap = dr._scan(tree, ["t_shared", "bg_x"], shared={"t_shared"})
    d = ac._grade_dens(cap, "t_shared")
    assert d["v"] == ac.FAIL and cap["served"] == 1 and cap["modules"] == ["tool.ts"] and not cap["label_only"], (d, cap)
    assert ac._ref_kinds(tree.layers.joinpath("tool.ts").read_text(encoding="utf-8"), "bg_x") == ["label"]      # the occurrence itself IS a label


P = "{ reason: 'read t_x rows from the store for every chart' }"


@pytest.mark.parametrize("src, want", [
    (f"query({P})", "ambiguous"),
    (f"query<Row>({P})", "ambiguous"),
    (f"query<Row, Other>({P})", "ambiguous"),
    (f"query?.({P})", "ambiguous"),
    (f"query!({P})", "ambiguous"),
    (f"new Q<R>({P})", "ambiguous"),
    (f"new Q({P})", "ambiguous"),
    (f"query<Row>(a, {P})", "ambiguous"),
    (f"query?.(a, {P})", "ambiguous"),
    (f"new Q<R>(a, {P})", "ambiguous"),
    (f"const f = () => ({P})", "label"),
    (f"const f = (a) => ({P})", "label"),
    (f"const f = async () => ({P})", "label"),
    (f"const f = () => ({P}).x", "label"),
    (f"const f = (x: Array<number>) => ({P})", "label"),
    (f"const a = [...({P})]", "label"),
    (f"return ({P})", "label"),
    (f"const c = ({P})", "label"),
    (f"const c = x ? ({P}) : null", "label"),
])
def test_generic_optional_non_null_and_new_calls_are_calls_an_arrow_is_not(src, want):
    assert _kinds(src) == [want], (src, _kinds(src))


@pytest.mark.parametrize("src, want", [
    ("import x from 't_x'", "label"),
    ("import { a } from \"t_x\"", "label"),
    ("export * from 't_x'", "label"),
    ("import 't_x'", "label"),
    ("const m = require('t_x')", "label"),
    ("const m = await import('t_x')", "label"),
    ("const m = await import(`./t_x`)", "label"),
    ("loader.import('t_x')", "ambiguous"),
    ("x.require('t_x')", "ambiguous"),
    ("this.import('t_x')", "ambiguous"),
    ("a?.import('t_x')", "ambiguous"),
    ("myimport('t_x')", "ambiguous"),
    ("$require('t_x')", "ambiguous"),
    ("_import('t_x')", "ambiguous"),
    ("from`t_x`", "ambiguous"),
    ("import`t_x`", "ambiguous"),
    ("sql from`t_x`", "ambiguous"),
    ("afrom 't_x'", "ambiguous"),
    ("a.from 't_x'", "ambiguous"),
    ("$import 't_x'", "ambiguous"),
])
def test_import_paths_are_label_methods_and_tagged_templates_are_not(src, want):
    assert _kinds(src) == [want], (src, _kinds(src))


@pytest.mark.parametrize("c, want", [
    ("one two three four five t_x", True),
    ("one two table three four five t_x", False),
    ("one two Table three four five t_x", False),
    ("one two table, three four five t_x", False),
    ("one two union three four five t_x", False),
    ("one two UNION three four five t_x", False),
    ("table t_x union all table facts", False),
    ("one two tables three four five t_x", True),
    ("one two tabled unions three four five t_x", True),
])
def test_strict_prose_refuses_the_words_table_and_union(c, want):
    assert ac._strict_prose(c, "t_x") is want, c


def test_a_provenance_tables_element_inside_a_probe_envelope_is_a_label_for_data_and_a_probe_for_a_service():
    src = "export const f = () => ({ kind: 'service_probe', provenance: { tables: ['t_x'] } })"
    assert _kinds(src, service=False) == ["label"]
    assert _kinds(src, service=True) == ["probe"]
    keys = "export const f = () => ({ kind: 'service_probe', asset_id: 't_x' })"
    assert _kinds(keys, service=False) == ["ambiguous"] and _kinds(keys, service=True) == ["probe"]


# ───────────────────────── service-kind assets: a service_probe envelope is a reach, at any depth ─────────────────────────

PROBE = ("export const cap = { run: () => null, probe: { kind: 'service_probe', asset_id: 'bg_x', probe_id: 'x_engine', "
         "endpoint_identity: 'nirmana-elevation:health-probe:bg_x', source_ref: 'platform/python-sidecar/scripts/c.json#bg_x' } }\n")


def _svc(tree, src, service, toks=TOKS):
    tree.write(tree.layers, "tool.ts", src)
    cap = ac.capability_scan(tree.roots, list(toks), shared=set(), columns=None, outside_roots=(), service=service)
    return ac._grade_dens(cap, "t_x"), cap


@pytest.mark.parametrize("service", [True, False])
def test_a_service_probe_envelope_is_a_reach_for_every_kind_of_asset(tree, service):
    d, cap = _svc(tree, PROBE, service)
    assert d["v"] == NO_DET and cap["modules"] == ["tool.ts"] and not cap["label_only"], (service, d, cap)


@pytest.mark.parametrize("src", [
    "export const probe = { kind: 'service_probe', asset_id: 'bg_x' }",
    "export const probe = { kind: 'service_probe', meta: { asset_id: 'bg_x' } }",
    "export const probe = { kind: 'service_probe', meta: { a: { b: { c: { asset_id: 'bg_x' } } } } }",
    "export const probe = { meta: { a: [ { asset_id: 'bg_x' } ] }, kind: 'service_probe' }",
    "export const probe = { kind: PROBE_KIND, asset_id: 'bg_x' }",
    "export const probe = { kind: probeKind(), asset_id: 'bg_x' }",
    "const base = { kind: 'service_probe' }\nexport const probe = { ...base, asset_id: 'bg_x' }",
    "export const probe = { a: { ...base, asset_id: 'bg_x' } }",
    "export const probe = { kind: \"service_probe\", asset_id: 'bg_x' }",
    "export const probe = { kind: `service_probe`, asset_id: 'bg_x' }",
    "export const probe = { kind: 'service_probe', x: { prov: { tables: ['bg_x'] } } }",
])
def test_for_a_service_asset_every_depth_below_the_marker_is_the_envelope(src):
    assert _kinds(src, "bg_x", service=True) == ["probe"], (src, _kinds(src, "bg_x", service=True))
    assert _kinds(src, "bg_x", service=False) == ["ambiguous"], (src, _kinds(src, "bg_x", service=False))


@pytest.mark.parametrize("src", [
    "export const probe = { kind: 'something_else', asset_id: 'bg_x' }",
    "export const probe = { asset_id: 'bg_x' }",
    "export const a = { kind: 'service_probe' }\nexport const probe = { asset_id: 'bg_x' }",
    "export const a = { kind: 'service_probe', asset_id: 'other' }\nexport const b = { x: { asset_id: 'bg_x' } }",
])
def test_the_marker_in_a_sibling_or_another_object_is_not_the_envelope(src):
    assert _kinds(src, "bg_x", service=True) == ["ambiguous"], (src, _kinds(src, "bg_x", service=True))


def test_the_envelope_marker_is_recognised_in_any_string_quote_and_only_as_the_whole_string():
    for q in ("'", '"', "`"):
        src = f"export const p = {{ kind: {q}service_probe{q}, asset_id: 't_x' }}"
        assert _kinds(src, "t_x", service=True) == ["probe"]
        assert _kinds(src.replace("service_probe", "other_probe"), "t_x", service=True) == ["ambiguous"]
        assert _kinds(src.replace("service_probe", "my_service_probe_x"), "t_x", service=True) == ["ambiguous"]


def test_inside_an_envelope_every_non_select_form_is_a_probe_and_a_select_keeps_its_name():
    src = "export const p = { kind: 'service_probe', q: 'SELECT id FROM t_x', n: 'one two three four five t_x' }"
    assert _kinds(src, service=True) == ["select", "probe"]
    assert _kinds("export const p = { kind: 'service_probe', ids: pick('t_x') }", service=True) == ["probe"]


def test_a_service_envelope_beside_a_real_select_is_still_the_select_verdict(tree):
    d, cap = _svc(tree, PROBE + "export const q = () => query(`SELECT id FROM t_x`)\n", True)
    assert d["v"] == ac.FAIL and cap["served"] == 1, d


def test_the_probe_kind_is_a_reach_in_the_unit_classifier():
    assert ac.PROBE_REF == "probe" and ac._module_reaches(["probe"])


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
    assert seen == [False] and dr._dens(census, "bg_x")["v"] == NO_DET




def test_the_carr_no_carriage_docstring_describes_the_dens_na_as_no_served_select():
    d = ac.grade_carr_no_carriage.__doc__
    assert "scanned, no served select" in d and "REGISTRY_REVISION 14" in d and 'meaning "scanned, no reference"' not in d, d
    assert ac.NA_CAUSES["Dens.served"] == ("no-served-surface", "dens-not-served", "dens-owned-by-sibling")      # SS N-211: + dens-not-served / dens-owned-by-sibling (the measured no-served-surface cause is unchanged)


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
R02_LABEL_REPAIR = ("bg_phaladeepika_latta", "bg_vedha_malefic_scale")
COMMENT_BLOCKED = ("bg_cohort",)        # label-only in code, but a comment in the same module names it: blocks the N/A (SS DENS L2, option ii)
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
        assert g["v"] == NO_DET and cap["modules"] and not cap["label_only"], (a, g, cap)
        assert "reach it by code" in g["measured"], g
    assert real_dens["bg_panchanga"][1]["modules"] == ["L0_brahmagyan/call_panchanga_service.ts"]


def test_the_probe_envelope_is_a_reach_whatever_the_registry_kind_the_closed_list_has_no_envelope_context():
    """A data-kind asset's envelope is not in the allow-list either: scanned as data or as service, both stay NO_DETECTOR."""
    for a in SERVICE_PROBE_ONLY:
        for svc in (False, True):
            cap = ac.capability_scan(ac.CAPS_ROOTS, [a], shared=frozenset(), columns={}, outside_roots=ac.DENS_OUTSIDE_ROOTS, service=svc)
            assert ac._grade_dens(cap, a)["v"] == NO_DET, (a, svc)


def test_the_real_registry_kind_is_what_the_fixture_carries_for_every_asset():
    kinds = {r["asset_id"]: r.get("asset_kind") for d in FX["layers"].values() for r in d["assets"]}
    assert len(kinds) == 127 and all(kinds.values())
    assert kinds["bg_ephemeris_engine"] == kinds["bg_panchanga"] == "service"
    assert kinds["bg_phaladeepika_latta"] == kinds["bg_cohort"] == kinds["bg_vedha_malefic_scale"] == "data"




def test_the_three_earlier_na_assets_read_exactly_the_text_they_read_before(real_dens):
    for a in R02_PRE_N74:
        g, _c = real_dens[a]
        assert g["measured"] == ("STRUCTURAL: 0 module(s) reference it by code in the 3 serving root(s) scanned, and no served select "
                                 "of it exists in the wider source scanned; declaring density_contract: 0"), g


def test_the_two_flips_rest_on_the_provenance_tables_envelope_and_nothing_else(real_dens):
    for a in R02_LABEL_REPAIR:
        g, cap = real_dens[a]
        assert cap["label_only"] == ["L3_kala/query_vedha_gochara.ts"] and not cap["modules"] and cap["served"] == 0, (a, cap)
        assert "label" in g["measured"], g
    src = (REPO / "platform/src/lib/retrieval/registry/layers/L3_kala/query_vedha_gochara.ts").read_text(encoding="utf-8")
    assert "provenance: {" in src and "tables: [" in src


def test_bg_cohort_stays_no_detector_its_prose_is_not_strict_and_a_comment_names_it(real_dens):
    """kala_ritual_resonance.ts / priority.ts name bg_cohort in prose with identifiers, hyphens and parentheses (not strict prose) and in
    comments: a reach. Its 'no retrieval capability wired' is a later per-asset DECLARED cause, not a scanner inference from prose."""
    g, cap = real_dens["bg_cohort"]
    assert g["v"] == NO_DET and cap["modules"], (g, cap)


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
    # DENS-TIER-GUARD (N-98, pin 23): was (5, 26, 43). The closed tier vocabulary moves THREE real PASS cells to PARTIAL (ga_medical and ga_vastu selected `indication_tier`, mi_kula
    # `evidence_tier`: neither is `tier` / `verification_pass_status` and none is declared); FAIL / N/A / NO_DETECTOR counts do not move (test_e6_dens_tier_guard.py names the three).
    # DENS-SCANNER (REGISTRY_REVISION 26): the real lexer reads the four files the quote loops lost sync on, so nine NO_DETECTOR cells become a read FAIL
    # (ga_structural, bo_bimba, bo_karanajala, bo_samvada, bo_upaya, ka_jivana_parva, ph_muhurta, ph_nimitta, ph_rectification) and bo_cdlm_summary (a const-map table) a PARTIAL:
    # (2, 29, 43) + 1 PARTIAL + 9 FAIL; N/A unchanged; NO_DETECTOR 48 - 10.
    # DENS-SERVED: the L0 / L1 / L2 query capabilities declare the contract their handlers honour (13 L0 FAIL -> PARTIAL; ga_ayurdaya, ga_structural, ga_vargas, bo_cgm_motifs, bo_cgm_paths,
    # bo_upaya, bo_sangati, bo_cdlm_summary -> PASS; bo_pramana_mapa FAIL -> PARTIAL): (2, 30, 52) -> (9, 42, 33). The uniform_authority / density_tier_columns declarations are not read here (the
    # scan reads source, not declarations): they move six more L0 cells PARTIAL -> PASS in the census.
    assert (c["PASS"], c["PARTIAL"], c["FAIL"]) == (10, 43, 31), c      # SS N-212 (a): + bo_bimba PASS, bo_karanajala FAIL -> PARTIAL (traverse_chart_graph declares its contract; the CTE node select lists the tier)
    assert c["N/A"] == 5 and c["NO_DETECTOR"] == 38, c


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
    assert ids == ["Dens.served#measured:no-served-surface", "Dens.served#measured:dens-not-served", "Dens.served#measured:dens-owned-by-sibling"], ids      # SS N-211 adds the two declaration-keyed, checked causes
    for a in R02_PRE_N74 + R02_LABEL_REPAIR:
        assert a not in ac.NA_RULE_DECISIONS["Dens.served#measured:no-served-surface"], a


def test_the_python_reader_clause_of_the_old_text_is_gone_and_replaced_by_the_select_reading():
    t = ac.NA_RULE_DECISIONS["Dens.served#measured:no-served-surface"]
    assert "three L0 tables" not in t, t


def test_dens_served_criterion_revision_5_states_the_select_reading():
    e = ac.CRITERION_REGISTRY["Dens.served"]
    assert e["revision"] == 11 and "tier column" in e["applicability"] and "label" in e["applicability"], e      # 6: N-98 closed tier vocabulary; 7: DENS-SCANNER; 9: DENS-SERVED (const-map select lists)


def test_registry_revision_is_at_least_14_and_the_declarations_file_is_at_the_decl_latta_version():
    assert ac.REGISTRY_REVISION >= 14          # pin 15 (STAMP) is stacked on this one
    # 1.9.0 at pin 14 (the Dens PR did not touch the file); 1.10.0 after DECL-LATTA, 1.11.0 after DECL-LATTA-NULL (bg_phaladeepika_latta's entry only)
    assert json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["version"] == _decl_version.CURRENT


def test_only_dens_served_changed_in_the_criterion_registry_at_14():
    """Everything else in the registry is the rev-13 content: the one revision-5 entry is Dens.served."""
    revs = {k: v["revision"] for k, v in ac.CRITERION_REGISTRY.items() if v["revision"] != 1}
    assert revs.get("Dens.served") == 11          # 5 at pin 14; 6 at pin 23 (DENS-TIER-GUARD, N-98); 7 at pin 26 (DENS-SCANNER); 9 at pin 26 (DENS-SERVED)
    assert set(ac.NA_CAUSES["Dens.served"]) == {"no-served-surface", "dens-not-served", "dens-owned-by-sibling"}


def test_the_na_cell_is_released_by_the_rule_in_the_rollup_with_the_new_text():
    m = {"Dens.served": dict(v=NA, measured="m", cause="no-served-surface")}
    cell = ac.rollup_asset("L0", m)["Dens"]
    assert cell["v"] == NA and cell["checks"][0]["rule_id"] == "Dens.served#measured:no-served-surface"
    assert "N-74(a)" in cell["checks"][0]["decision"], cell
