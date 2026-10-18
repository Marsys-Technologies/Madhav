"""test_dens_served_review2.py — the SECOND N-212 review round: every hole the focused re-review found has a forgery / mutation test.

1  dens_not_served: a real read of the table OUTSIDE the serving roots, in every form, must not release N/A (reaches now cover platform/src and platform-mcp/src as a whole)
2  the paren rule: a UNION / INSERT context a select is still INSIDE is kept; only closed groups are blanked (the traverse shape still reads)
3  reaches carry a digest of the line's text: a line mutated in place keeps its number but not its digest
6  a LABEL occurrence plus a run-time FROM in one module cannot be ruled out
7  the bind facet reads only the statement's own top-level WHERE, the declared input's slot, and a push()ed / assigned filter literal
8  every module a Dens PASS credits is in the vitest CASES
9  .mts / .cts / .jsx are scanned

Run:
  python -m pytest platform/scripts/governance/__tests__/test_dens_served_review2.py -v
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_dens_not_served as dn  # noqa: E402
import test_e6_1_dens_repair as dr  # noqa: E402
import test_w2_1_earned_verdicts as w1  # noqa: E402

tree = dr.tree
_REAL_SCAN = dr._REAL_SCAN
AID = dn.AID


# ───────────────────────── 1: outside-the-roots reads, every form ─────────────────────────

OUTSIDE_FORMS = [
    ("comma join", "export const f = () => query(`SELECT * FROM a, b, t_x WHERE a.id = t_x.id`)\n"),
    ("JOIN then comma join", "export const f = () => query(`SELECT * FROM a JOIN b ON a.id = b.id, t_x WHERE 1=1`)\n"),
    ("multiline comma join", "export const f = () => query(`SELECT *\n  FROM a\n  JOIN b ON a.id = b.id,\n       t_x x\n WHERE 1=1`)\n"),
    ("TABLE ONLY", "export const f = () => query('TABLE ONLY t_x')\n"),
    ("TABLE shorthand", "export const f = () => query('TABLE t_x')\n"),
    ("COPY ... TO STDOUT", "export const f = () => query('COPY t_x TO STDOUT')\n"),
    ("second call argument", "export const f = () => repo.fetch(1, 't_x')\n"),
    ("object value", "export const f = () => repo.fetch({ table: 't_x' })\n"),
    ("array element", "export const f = () => repo.fetch(['t_x'])\n"),
    ("variable passed to a call", "const T = 't_x'\nexport const f = () => repo.fetch(T)\n"),
    ("plain select", "export const f = () => query(`SELECT id FROM t_x`)\n"),
    ("query builder", "export const f = () => db.from('t_x').select('id')\n"),
]


@pytest.mark.parametrize("form,src", OUTSIDE_FORMS)
@pytest.mark.parametrize("where", ["lib/o.ts", "app/api/x/route.ts", "retrieval/registry/knowledge/k.ts"])
def test_finding1_a_real_read_outside_the_roots_never_reads_na(tree, form, src, where):
    cap, d = dn._probe(tree, None, outside_name=where, outside_src=src)
    assert d["v"] in (ac.FAIL, ac.NO_DET) and d["v"] != ac.NA, (form, where, d)
    assert dn._rollup(d)["v"] != ac.NA


def test_finding1_a_comment_only_mention_outside_the_roots_is_still_tolerated(tree):
    cap, d = dn._probe(tree, None, outside_name="lib/o.ts", outside_src="// t_x is read by the sidecar, not here\nexport const f = 1\n")
    assert d["v"] == ac.NA, d


def test_finding1_a_declared_outside_occurrence_is_accepted_and_a_second_one_is_not(tree):
    """The outside occurrences are declared exactly like the in-root ones: declare the benign mention and it releases; add one more and it flips."""
    src = "export const NOTE = { table: 't_x' }\n"
    out = tree.outside / "lib" / "o.ts"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(src, encoding="utf-8")
    cap = _REAL_SCAN(tree.roots, ["t_x", AID], shared=set(), columns={}, outside_roots=(str(tree.outside),), outside_exclude=ac.DENS_STRICT_EXCLUDE, table_tokens=["t_x"])
    assert len(cap["reach_at"]) == 1, cap["reach_at"]
    p, ln, h = cap["reach_at"][0]
    declared = dict(dn.NONE, reaches=[f"platform/src/lib/o.ts:{ln}#{h}"])
    same = ac.dens_not_served_record(AID, dict(dens_not_served=declared), "t_x", dict(cap, reach_at=[("platform/src/lib/o.ts", ln, h)], outside_named=[]), table_shared=False)
    assert same["v"] == ac.NA, same
    out.write_text(src + "export const g = () => db.from('t_x')\n", encoding="utf-8")
    cap2 = _REAL_SCAN(tree.roots, ["t_x", AID], shared=set(), columns={}, outside_roots=(str(tree.outside),), outside_exclude=ac.DENS_STRICT_EXCLUDE, table_tokens=["t_x"])
    flipped = ac.dens_not_served_record(AID, dict(dens_not_served=declared), "t_x", dict(cap2, reach_at=[("platform/src/lib/o.ts", a, b) for _p, a, b in cap2["reach_at"]], outside_named=[]), table_shared=False)
    assert flipped["v"] == ac.NO_DET and "not declared" in flipped["measured"], flipped


# ───────────────────────── 3: the line digest ─────────────────────────

def test_finding3_a_line_mutated_in_place_keeps_its_number_but_not_its_digest():
    benign = "export const NOTE = { label: 'see t_x docs' }\n"
    off = benign.index("t_x")
    base = ac._reach_entry("platform/src/lib/a.ts", benign, off)
    for mutated in ("export const f = () => db.from('t_x')\n", "export const f = () => repo.fetch(1, 't_x')\n", "TABLE t_x\n",
                    "export const f = () => query('SELECT * FROM o, t_x')\n", "export const NOTE = { label: 't_x', again: 't_x' }\n"):
        got = ac._reach_entry("platform/src/lib/a.ts", mutated, mutated.index("t_x"))
        assert got[1] == base[1] and got[2] != base[2], (mutated, got, base)
        declared = dict(dn.NONE, reaches=[f"{base[0]}:{base[1]}#{base[2]}"])
        rec = dn._rec(declared, cap=dict(reach_at=[got]))
        assert rec["v"] == ac.NO_DET and "not declared" in rec["measured"], (mutated, rec)
    assert ac._reach_entry("platform/src/lib/a.ts", "  export   const NOTE = { label: 'see t_x docs' }  \n", 30)[2] == base[2]      # whitespace-only edits do not move the digest


def test_finding3_the_reaches_format_requires_the_digest():
    bad = ac.dens_not_served_problem(dict(dens_not_served=dict(dn.NONE, reaches=["platform/src/lib/a.ts:10"])), AID)
    assert bad and "reaches is required" in bad, bad


# ───────────────────────── 6: a label plus a run-time FROM ─────────────────────────

def test_finding6_a_label_occurrence_in_a_module_with_a_run_time_from_cannot_be_ruled_out(tree):
    src = "export const meta = () => ({ provenance: { tables: ['t_x'] } })\nexport const q = (n) => query(`SELECT id FROM ${n}`)\n"
    cap, d = dn._probe(tree, src)
    assert cap["reach_at"] == [] and cap["reach_dynamic"], cap          # only a LABEL: no declared reach to compare
    assert d["v"] == ac.NO_DET and "run-time table name" in d["measured"], d


# ───────────────────────── 2: the paren rule ─────────────────────────

CONTRACT = "density_contract: { paginated: true, facets: [], empty_reason: true },"


def _dens(monkeypatch, tree, sql):
    tree.write(tree.layers / "L0_x", "q.ts", f"export const cap = {{\n  id: 'bg_x',\n  {CONTRACT}\n  run: () => query(`{sql}`),\n}}\n")
    c = dr._measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": (["id", "tier", "label"], [])})
    return dr._dens(c, "bg_x")


@pytest.mark.parametrize("sql", [
    "WITH r AS (SELECT id, tier FROM o UNION SELECT id, tier FROM t_x) SELECT * FROM r",
    "SELECT * FROM (SELECT id, label FROM o UNION ALL SELECT id, tier FROM t_x) s",
    "WITH c AS (INSERT INTO log SELECT id, tier FROM t_x RETURNING id) SELECT id FROM c",
])
def test_finding2_a_select_still_inside_a_union_or_insert_group_earns_no_tier_credit(monkeypatch, tree, sql):
    d = _dens(monkeypatch, tree, sql)
    assert d["v"] != ac.PASS, (sql, d)


def test_finding2_the_closed_cte_shape_of_traverse_still_reads(monkeypatch, tree):
    sql = ("WITH RECURSIVE bfs AS (SELECT id FROM t_x UNION SELECT e.b FROM bfs JOIN e ON e.a = bfs.id), visited AS (SELECT DISTINCT id FROM bfs) "
           "SELECT n.id, n.tier FROM t_x n JOIN visited v ON n.id = v.id")
    d = _dens(monkeypatch, tree, sql)
    assert d["v"] == ac.PASS and "tier" in d["measured"], d


def test_finding2_a_top_level_union_and_insert_select_stay_excluded(monkeypatch, tree):
    assert _dens(monkeypatch, tree, "SELECT id, tier FROM o UNION SELECT id, tier FROM t_x")["v"] != ac.PASS
    assert _dens(monkeypatch, tree, "INSERT INTO log SELECT id, tier FROM t_x")["v"] != ac.PASS


# ───────────────────────── 7: the bind facet ─────────────────────────

COLS = {"t_shared": ["fact_id", "fact_category", "verification_pass_status", "fact_subject"]}


def _src(sql, *, schema="input_schema: { chart_id: { type: 'string' }, categories: { type: 'array' } },", body_extra="", params="[args.chart_id, args.categories]"):
    return ("export const cap = {\n  id: 'cap_x',\n  density_contract: { paginated: true, facets: ['categories'], empty_reason: true },\n  " + schema + "\n"
            "  async handler(args) {\n" + body_extra + "    return query(`" + sql + "`, " + params + ")\n  },\n}\n")


def _scan(tree, src):
    tree.write(tree.layers / "L0_x", "q.ts", src)
    f = dict(column="fact_category", values=["sade"], input="categories", served_by=str(tree.layers / "L0_x" / "q.ts"))
    return _REAL_SCAN(tree.roots, ["t_shared", "bg_x"], shared={"t_shared"}, columns=COLS, outside_roots=(), facets={"t_shared": f})


GOOD = "SELECT fact_id, verification_pass_status FROM t_shared WHERE chart_id = $1 AND fact_category = ANY($2::text[])"


def test_finding7_the_good_shape_is_credited(tree):
    assert _scan(tree, _src(GOOD))["facet_bound_credited"] == ["L0_x/q.ts"]


@pytest.mark.parametrize("name,sql", [
    ("a sub-select on another table with the same unqualified column", "SELECT fact_id, verification_pass_status FROM t_shared WHERE fact_id IN (SELECT id FROM other WHERE fact_category = ANY($2::text[]))"),
    ("bind text inside an SQL string literal", "SELECT fact_id, verification_pass_status FROM t_shared WHERE note = 'fact_category = ANY($2::text[])'"),
    ("the predicate only in HAVING", "SELECT fact_id, verification_pass_status FROM t_shared WHERE chart_id = $1 GROUP BY fact_id, verification_pass_status HAVING max(fact_category) = ANY($2::text[])"),
    ("the predicate only in ORDER BY", "SELECT fact_id, verification_pass_status FROM t_shared WHERE chart_id = $1 ORDER BY fact_category = ANY($2::text[])"),
    ("the predicate only in the select list", "SELECT fact_id, verification_pass_status, (fact_category = ANY($2::text[])) AS hit FROM t_shared WHERE chart_id = $1"),
])
def test_finding7_the_predicate_must_sit_in_the_statements_own_top_level_where(tree, name, sql):
    cap = _scan(tree, _src(sql))
    assert not cap["facet_attributed"], (name, cap)


def test_finding7_the_slot_must_carry_the_declared_input(tree):
    other = _src(GOOD, params="[args.chart_id, args.something_else]")
    assert not _scan(tree, other)["facet_attributed"]
    first = _src("SELECT fact_id, verification_pass_status FROM t_shared WHERE fact_category = ANY($1::text[])", params="[args.chart_id, args.categories]")
    assert not _scan(tree, first)["facet_attributed"]          # $1 is the chart id, not the categories


def _conditional(extra_literal, *, push=True, schema="input_schema: { chart_id: { type: 'string' }, categories: { type: 'array', required: true } },"):
    filt = "filters.push(`fact_category = ANY($2::text[])`)" if push else "const unused = `fact_category = ANY($2::text[])`"
    return ("export const cap = {\n  id: 'cap_x',\n  density_contract: { paginated: true, facets: ['categories'], empty_reason: true },\n  " + schema + "\n"
            "  async handler(args) {\n    const filters = ['chart_id = $1']\n    " + filt + "\n" + extra_literal +
            "    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE ${filters.join(' AND ')}`, [args.chart_id, args.categories])\n  },\n}\n")


def test_finding7_a_pushed_filter_is_credited_a_dead_literal_is_not(tree):
    assert _scan(tree, _conditional(""))["facet_bound_credited"] == ["L0_x/q.ts"]
    assert not _scan(tree, _conditional("", push=False))["facet_attributed"]                         # an unused literal that merely looks like the filter
    desc = _conditional("").replace("filters.push(`fact_category = ANY($2::text[])`)", "const description = `fact_category = ANY($2::text[]) is the filter`")
    assert not _scan(tree, desc)["facet_attributed"]


def test_finding7_a_variable_assigned_where_is_credited(tree):
    src = ("export const cap = {\n  id: 'cap_x',\n  density_contract: { paginated: true, facets: ['categories'], empty_reason: true },\n"
           "  input_schema: { chart_id: { type: 'string' }, categories: { type: 'array', required: true } },\n"
           "  async handler(args) {\n    let where = `chart_id = $1 AND fact_category = ANY($2::text[])`\n"
           "    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE ${where}`, [args.chart_id, args.categories])\n  },\n}\n")
    assert _scan(tree, src)["facet_bound_credited"] == ["L0_x/q.ts"]


# ───────────────────────── 9: more extensions ─────────────────────────

@pytest.mark.parametrize("name", ["p.mts", "p.cts"])
def test_finding9_mts_and_cts_modules_in_the_roots_are_scanned(tree, name):
    cap, d = dn._probe(tree, "export const t = { run: () => query(`SELECT id FROM t_x`) }\n", name=name)
    assert cap["served"] == 1 and d["v"] == ac.FAIL, (name, d)


def test_finding9_a_jsx_file_outside_the_roots_that_names_the_table_is_named(tree):
    cap, d = dn._probe(tree, None, outside_name="components/C.jsx", outside_src="export const C = () => <p>don't read t_x</p>\n")
    assert any("unparsed file" in x for x in cap["outside_named"]) and d["v"] == ac.NO_DET, (cap, d)


# ───────────────────────── 8: every credited module is in the vitest CASES ─────────────────────────

def dens_claims_gap(credited, vitest_text: str, repo_root: pathlib.Path) -> list[str]:
    """The credited modules whose contract claims no test checks. A platform module (under the layers root) must be imported by dens_served_contracts.test.ts (a `'../'` import: a layer-root
    module is `'../name'`, a layer module `'../L0_x/name'`). A platform-mcp module (`platform-mcp/...`, which the platform vitest cannot import) must have its OWN claims test, the sibling
    `<module>_dens_served.test.ts`, which imports the module by its relative path (`'./<module>'` or `'./<module>.js'`): the one narrowing of the rule, not an exemption by package
    (a platform-mcp module without that sibling file, or whose sibling does not import it, is still reported)."""
    imported = set(re.findall(r"from '\.\./(?:L\d_[a-z]+/)?([a-z_0-9]+)'", vitest_text))      # a layer-root module (register_d9_judgment) is imported as '../name'

    def claimed(m: str) -> bool:
        stem = pathlib.PurePosixPath(m).stem
        if m.startswith("platform-mcp/"):
            t = (repo_root / m).with_name(f"{stem}_dens_served.test.ts")
            return t.is_file() and re.search(r"from '\./" + re.escape(stem) + r"(?:\.js)?'", t.read_text(encoding="utf-8")) is not None
        return stem in imported

    return sorted(m for m in credited if not claimed(m))


def test_finding8b_a_platform_mcp_module_needs_its_own_sibling_claims_test(tmp_path):
    """Sensitivity of the narrowing in finding8: a credited platform-mcp module is covered ONLY by a sibling `<module>_dens_served.test.ts` that imports it relatively."""
    mod = "platform-mcp/src/tools/retrieval/register_x.ts"
    d = tmp_path / "platform-mcp/src/tools/retrieval"
    d.mkdir(parents=True)
    (d / "register_x.ts").write_text("export {}\n", encoding="utf-8")
    vitest = "import { a } from '../L0_brahmagyan/query_a'\n"
    assert dens_claims_gap([mod, "L0_brahmagyan/query_a.ts"], vitest, tmp_path) == [mod]                               # no sibling test: reported
    (d / "register_x_dens_served.test.ts").write_text("import { y } from './other.js'\n", encoding="utf-8")
    assert dens_claims_gap([mod], vitest, tmp_path) == [mod]                                                           # a sibling that does not import the module: reported
    (d / "register_x_dens_served.test.ts").write_text("import { x } from './register_x.js'\n", encoding="utf-8")
    assert dens_claims_gap([mod], vitest, tmp_path) == []                                                              # the sibling imports it: covered
    assert dens_claims_gap([mod, "L0_brahmagyan/query_b.ts"], vitest, tmp_path) == ["L0_brahmagyan/query_b.ts"]        # a platform module is never covered by an mcp sibling
    assert dens_claims_gap(["platform-mcp/src/tools/retrieval/register_x.ts"], "import { x } from '../register_x'\n", tmp_path) == []   # (and the sibling rule is the one that applies, not the import list)


def test_finding8_every_module_a_dens_pass_credits_is_in_the_vitest_cases():
    """The committed scan inputs (127 assets, tokens / shared tables / catalog columns) run through the same scan measure() runs, with the committed declarations' facets and tier columns:
    every capability module that EARNS a PASS must be imported by dens_served_contracts.test.ts, which checks its contract claims against its handler. The modules collected are
    the scan's `dense` entries (a contract-declaring entry whose own select carries the tier column) and its `facet_dense` entries (a facet-attributed entry: pinned or bind-credited),
    for every asset the scan grades PASS, with NO exemption by file name or by package."""
    import test_e6_dens_label_select as ls
    decl = ac.load_asset_declarations()
    credited = set()
    for L, d in ls.FX["layers"].items():
        for r in d["assets"]:
            sd = decl.get(r["asset_id"]) or {}
            tbl = r["target_table"]
            df = ({tbl.lower(): dict(column=sd["density_facet"]["column"], values=list(sd["density_facet"]["values"]), input=sd["density_facet"].get("input"),
                                     served_by=sd["density_facet"].get("served_by"))} if (tbl and isinstance(sd.get("density_facet"), dict)) else None)
            dt = ({tbl.lower(): [x["column"] for x in sd["density_tier_columns"]]} if (tbl and isinstance(sd.get("density_tier_columns"), list)) else None)
            cap = ac.capability_scan(ac.CAPS_ROOTS, r["tokens"], shared=frozenset(d["shared"]), columns=d["columns"], outside_roots=(), service=(r.get("asset_kind") == "service"),
                                     tier_declared=dt, facets=df)
            g = ac._grade_dens(cap, tbl or r["asset_id"], uniform_authority=isinstance(sd.get("uniform_authority"), dict))
            if g["v"] == ac.PASS:
                credited.update(n for n, _c in (cap.get("dense") or []))
                credited.update(cap.get("facet_dense") or [])
    vitest = (HERE.parents[2] / "src/lib/retrieval/registry/layers/__tests__/dens_served_contracts.test.ts").read_text(encoding="utf-8")
    missing = dens_claims_gap(credited, vitest, HERE.parents[3])
    assert credited, "the committed inputs credit no PASS at all: the check would be vacuous"
    assert missing == [], f"modules credited by a Dens PASS but absent from dens_served_contracts.test.ts: {missing}"


def test_finding2_mutation_the_old_whole_group_blanking_would_credit_the_shapes(monkeypatch, tree):
    """Sensitivity of the tests above: with the pre-review rule (blank everything at paren depth > 0, an unclosed group too) the first shape reads PASS, i.e. the rule WAS the hole."""
    def old(sql):
        out, depth = [], 0
        for ch in sql:
            if ch == "(":
                depth += 1
                out.append(" ")
            elif ch == ")":
                depth = max(depth - 1, 0)
                out.append(" ")
            else:
                out.append(ch if depth == 0 else (ch if ch == "\n" else " "))
        return "".join(out)
    sql = "WITH r AS (SELECT id, tier FROM o UNION SELECT id, tier FROM t_x) SELECT * FROM r"
    assert _dens(monkeypatch, tree, sql)["v"] != ac.PASS
    monkeypatch.setattr(ac, "_sql_top_level", old)
    assert _dens(monkeypatch, tree, sql)["v"] == ac.PASS
