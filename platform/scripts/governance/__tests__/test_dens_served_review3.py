"""test_dens_served_review3.py — the THIRD N-212 review round (two MED conditions), each with the reviewer's exact probe: the forged case must read NO_DETECTOR / not credited.

MED-1  the reach digest covers the token's line AND the previous / next non-blank lines: a bracket-wrapped bare name (`[\\n 't_x',\\n]`) rewritten into a call (`repo.fetch(\\n 't_x',\\n)`,
       `db.from(\\n 't_x',\\n).select()`) keeps its line number AND its own line's text, but not its digest; whitespace-only edits do not move it.
MED-2  the bind facet's dynamic `.push(` rule: the filter literal must be pushed onto the SAME array the WHERE joins (`${X.join(..)}`), before the select is built, not under a
       literal-false branch; the input must be pushed onto an array that reaches the query call's SECOND argument before it is snapshotted; an unrelated array literal, an unrelated
       `log.push(..)`, a push after the query and a push onto another array are not evidence. A literal `$k` slot reads the call's own params argument.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_dens_served_review3.py -v
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_dens_not_served as dn  # noqa: E402
import test_dens_served_review2 as r2  # noqa: E402
import test_e6_1_dens_repair as dr  # noqa: E402

tree = dr.tree


# ───────────────────────── MED-1: the digest covers the neighbouring lines ─────────────────────────

BENIGN = "export const NAMES = [\n  't_x',\n]\n"
FORGERIES = [
    ("repo.fetch(", "export const NAMES = repo.fetch(\n  't_x',\n)\n"),
    ("db.from(", "export const NAMES = db.from(\n  't_x',\n).select()\n"),
    ("query(", "export const NAMES = query(\n  't_x',\n)\n"),
    ("object call", "export const NAMES = load({\n  't_x',\n})\n"),
]


def _entry(src: str):
    return ac._reach_entry("platform/src/lib/a.ts", src, src.index("t_x"))


@pytest.mark.parametrize("name,forged", FORGERIES)
def test_med1_the_reviewers_probe_a_bracket_wrapped_name_rewritten_into_a_call_changes_the_digest(name, forged):
    a, b = _entry(BENIGN), _entry(forged)
    assert a[1] == b[1], "the token stays on the same line number"
    assert BENIGN.split("\n")[1] == forged.split("\n")[1], "and its own line is byte-identical (the old single-line digest could not tell them apart)"
    assert a[2] != b[2], (name, a, b)


@pytest.mark.parametrize("name,forged", FORGERIES)
def test_med1_the_forged_call_reads_no_detector_through_the_real_scan(tree, name, forged):
    """The reviewer's probe end to end: the benign bracket-wrapped name is declared (digest and all) and releases N/A; the same file rewritten into a call keeps the line number and the
    token's own line, and must NOT release it."""
    out = tree.outside / "lib" / "o.ts"
    out.parent.mkdir(parents=True, exist_ok=True)

    def rec(src):
        out.write_text(src, encoding="utf-8")
        cap = dr._REAL_SCAN(tree.roots, ["t_x", dn.AID], shared=set(), columns={}, outside_roots=(str(tree.outside),), outside_exclude=ac.DENS_STRICT_EXCLUDE, table_tokens=["t_x"])
        return cap, [("platform/src/lib/o.ts", n, h) for _p, n, h in cap["reach_at"]]
    cap0, reach0 = rec(BENIGN)
    assert len(reach0) == 1, cap0
    declared = dict(dn.NONE, reaches=[f"{p}:{n}#{h}" for p, n, h in reach0])
    ok = ac.dens_not_served_record(dn.AID, dict(dens_not_served=declared), "t_x", dict(cap0, reach_at=reach0, outside_named=[]), table_shared=False)
    assert ok["v"] == ac.NA, ok
    cap1, reach1 = rec(forged)
    assert reach1 and reach1[0][1] == reach0[0][1], "the forged file keeps the declared line number"
    bad = ac.dens_not_served_record(dn.AID, dict(dens_not_served=declared), "t_x", dict(cap1, reach_at=reach1, outside_named=[]), table_shared=False)
    assert bad["v"] == ac.NO_DET and "not declared" in bad["measured"], (name, bad)


def test_med1_a_neighbour_line_edit_moves_the_digest_and_whitespace_does_not():
    base = _entry(BENIGN)
    assert _entry("export const NAMES = [\n  't_x',\n  'other',\n]\n")[2] != base[2]                  # the next line changed
    assert _entry("export const NAMES = [\n\n\n    't_x'  ,\n\n]\n")[2] == _entry("export const NAMES = [\n  't_x'  ,\n]\n")[2]     # blank lines and indentation are tolerated
    assert _entry("export   const NAMES =   [\n\t't_x',\n  ]\n")[2] == base[2]
    assert _entry("// a leading comment\nexport const NAMES = [\n  't_x',\n]\n")[1] == base[1] + 1        # the line number follows the file


def test_med1_a_token_on_the_first_or_last_line_has_a_digest():
    assert len(ac._reach_entry("a.ts", "t_x", 0)[2]) == 8
    assert len(ac._reach_entry("a.ts", "a\nt_x\n\n\n", 2)[2]) == 8


# ───────────────────────── MED-2: the dynamic push rule ─────────────────────────

SQL = "SELECT fact_id, verification_pass_status FROM t_shared WHERE ${filters.join(' AND ')}"
FILTER = "`fact_category = ANY($${p++}::text[])`"
HEAD = "export const cap = {\n  id: 'cap_x',\n  density_contract: { paginated: true, facets: ['categories'], empty_reason: true },\n  input_schema: { chart_id: { type: 'string' }, categories: { type: 'array', required: true } },\n  async handler(args) {\n"
TAIL = "  },\n}\n"


def _h(body: str) -> str:
    return HEAD + body + TAIL


def _good(*, filt_push="    filters.push(" + FILTER + ")\n", par_push="    params.push(args.categories)\n", pre="", query="    return query(`" + SQL + "`, params)\n", wrap=("", "")):
    return _h("    const filters = ['chart_id = $1']\n    const params = [args.chart_id]\n    let p = 2\n" + pre + wrap[0] + filt_push + par_push + wrap[1] + query)


def _credited(tree, src):
    return r2._scan(tree, src)["facet_bound_credited"] == ["L0_x/q.ts"]


def test_med2_the_good_dynamic_shape_is_credited(tree):
    assert _credited(tree, _good())


def test_med2_a_variable_params_array_built_with_a_spread_is_credited(tree):
    src = _good(query="    const paramsA = [...params, 5]\n    const sqlA = `" + SQL + "`\n    return query(sqlA, paramsA)\n")
    assert _credited(tree, src)


def test_med2_a_literal_dollar_k_slot_reads_the_call_params_argument(tree):
    src = _h("    const where = `chart_id = $1 AND fact_category = ANY($2::text[])`\n    const whereParams = [args.chart_id, args.categories]\n    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE ${where}`, [...whereParams, 10, 0])\n")
    assert _credited(tree, src)


DECOYS = {
    "filter pushed onto another array": _good(filt_push="    other.push(" + FILTER + ")\n"),
    "unrelated log.push of the filter text": _good(filt_push="    log.push(" + FILTER + ")\n"),
    "the filter literal only declared, never pushed": _good(filt_push="    const unused = " + FILTER + "\n"),
    "filter push under if (false)": _good(wrap=("    if (false) {\n", "    }\n")),
    "filter push under if (0)": _good(wrap=("    if (0) {\n", "    }\n")),
    "filter push under if (!true)": _good(wrap=("    if (!true) {\n", "    }\n")),
    "filter push under if (false && x)": _good(wrap=("    if (args.x && false) {\n", "    }\n")),
    "filter push under an unbraced if (false)": _good(filt_push="    if (false) filters.push(" + FILTER + ")\n"),
    "filter push behind false &&": _good(filt_push="    false && filters.push(" + FILTER + ")\n"),
    "filter push in the else of if (true)": _good(wrap=("    if (true) { p += 0 } else {\n", "    }\n")),
    "filter pushed AFTER the select is built": _good(filt_push="", par_push="", query="    const sql = `" + SQL + "`\n    filters.push(" + FILTER + ")\n    params.push(args.categories)\n    return query(sql, params)\n"),
    "input pushed onto another array": _good(par_push="    decoy.push(args.categories)\n"),
    "input pushed under if (false)": _good(par_push="    if (false) { params.push(args.categories) }\n"),
    "input pushed after the query": _good(par_push="", query="    const r = query(`" + SQL + "`, params)\n    params.push(args.categories)\n    return r\n"),
    "input pushed is not the declared input": _good(par_push="    params.push(args.something_else)\n"),
    "unrelated push between the filter and the input": _good(par_push="    log.push('x')\n    params.push(args.categories)\n"),
    "params of the call is another array": _good(query="    const decoy = [args.chart_id, args.categories]\n    return query(`" + SQL + "`, decoy)\n"),
    "params argument missing": _good(query="    return query(`" + SQL + "`)\n"),
    "spread of an array the input is not pushed onto": _good(query="    const decoy = [args.chart_id]\n    return query(`" + SQL + "`, [...decoy, 5])\n"),
    "array snapshotted by a spread before the push": _good(par_push="", query="    const snap = [...params]\n    params.push(args.categories)\n    return query(`" + SQL + "`, snap)\n"),
}


@pytest.mark.parametrize("name", sorted(DECOYS))
def test_med2_every_decoy_is_not_credited(tree, name):
    cap = r2._scan(tree, DECOYS[name])
    assert not cap["facet_attributed"] and not cap["facet_bound_credited"], (name, cap)


def test_med2_the_decoys_differ_from_the_good_shape_only_in_the_named_detail():
    assert all(src != _good() for src in DECOYS.values())


LITERAL_DECOYS = {
    "an unrelated array literal supplies $2": _h("    const where = `chart_id = $1 AND fact_category = ANY($2::text[])`\n    const decoy = [args.chart_id, args.categories]\n    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE ${where}`, [args.chart_id, args.nothing])\n"),
    "a nested array literal supplies $2": _h("    const where = `chart_id = $1 AND fact_category = ANY($2::text[])`\n    log(x, [args.chart_id, args.categories])\n    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE ${where}`, params)\n"),
    "the call params array names the input at the wrong position": _h("    const where = `chart_id = $1 AND fact_category = ANY($2::text[])`\n    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE ${where}`, [args.categories, args.chart_id])\n"),
    "a reassigned params identifier": _h("    const where = `chart_id = $1 AND fact_category = ANY($2::text[])`\n    let params = [args.chart_id, args.categories]\n    params = [args.chart_id]\n    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE ${where}`, params)\n"),
    "the where assignment under if (false)": _h("    let where = `chart_id = $1`\n    if (false) { where = `chart_id = $1 AND fact_category = ANY($2::text[])` }\n    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE ${where}`, [args.chart_id, args.categories])\n"),
}


@pytest.mark.parametrize("name", sorted(LITERAL_DECOYS))
def test_med2_literal_slot_decoys_are_not_credited(tree, name):
    cap = r2._scan(tree, LITERAL_DECOYS[name])
    assert not cap["facet_attributed"], (name, cap)


def test_med2_the_direct_where_with_a_literal_slot_and_a_foreign_params_array_is_not_credited(tree):
    src = _h("    const decoy = [args.chart_id, args.categories]\n    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE chart_id = $1 AND fact_category = ANY($2::text[])`, [args.chart_id, args.nothing])\n")
    assert not r2._scan(tree, src)["facet_attributed"]
    good = _h("    return query(`SELECT fact_id, verification_pass_status FROM t_shared WHERE chart_id = $1 AND fact_category = ANY($2::text[])`, [args.chart_id, args.categories])\n")
    assert _credited(tree, good)
