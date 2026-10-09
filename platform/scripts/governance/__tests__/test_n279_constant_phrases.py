"""test_n279_constant_phrases.py: SS N-279 `writer_constant_phrases` on the Null writer scan.

bo_karanajala writes optional suffixes (' (counted in reverse)', ', cancelled', ' (house {house})') and bo_anveshana writes four fixed reasoning-step descriptions. The scan reads the first as
`literal_fallback` ('' else-branch) and the second as `constant_write`. The declaration is CHECKED per literal: each declared literal must be present verbatim in the writer source AST and match a
scan finding; every finding must be covered; anything else keeps the cap, and a changed / removed / stale literal refuses the declaration (NO_DETECTOR). Source only: no database.
"""
from __future__ import annotations

import ast
import copy
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

WS = ac._lint_module("writer_literal_scan")
SQL = 'SQL = """INSERT INTO t (chart_id, citation_human) VALUES (%(chart_id)s, %(citation_human)s)"""\n'
SUFFIX = SQL + '''
def run(conn, chart_id, g, rev, house):
    text = f"Argala: {g}" + (" (counted in reverse)" if rev else "")
    text += (f" (house {house})" if house else "")
    conn.execute(SQL, {"chart_id": chart_id, "citation_human": text})
'''
CONST = SQL + '''
def run(conn, chart_id):
    conn.execute(SQL, {"chart_id": chart_id, "citation_human": "Low surface salience"})
'''
EVID = "platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py:690"


def _units(src, name="w.py"):
    tree = ast.parse(src)
    return [dict(rel=name, path=pathlib.Path(name), tree=tree, nodes=[tree], hop=0, via=name)]


def _scan(src):
    u = _units(src)
    ws = WS.scan(u, ["citation_human"], {"citation_human": ["t"]}, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field)
    return ws, u


def _item(form, literal, file="w.py"):
    return dict(file=file, entry="citation_human", form=form, literal=literal, why=f"citation_human carries the fixed phrase {literal!r} by design, not a stand-in for a missing value", evidence=EVID)


def _records():
    return {c: dict(v=ac.PARTIAL, clean=True, measured="no schema default / no blank row; writer literal scan is not read") for c in ac.NULL_CHECKS}


def _apply(src, items):
    ws, u = _scan(src)
    out = _records()
    ac._apply_constant_phrases(out, ["citation_human"], dict(scan_result=ws, scan_units=u, units=u), dict(writer_constant_phrases=items))
    return out, ws


def test_the_scan_reads_the_suffix_and_the_constant_as_findings_without_a_declaration():
    ws, _ = _scan(SUFFIX)
    assert ws["v"] == "PARTIAL" and {p["kind"] for p in ws["problems"]} == {"literal_fallback"} and len(ws["problems"]) == 2
    ws, _ = _scan(CONST)
    assert [p["kind"] for p in ws["problems"]] == ["constant_write"]
    out = _records()
    ws, u = _scan(CONST)
    ac._apply_constant_phrases(out, ["citation_human"], dict(scan_result=ws, scan_units=u), {})        # no declaration = no change
    assert all(r["v"] == ac.PARTIAL for r in out.values())


def test_declared_constant_write_literal_present_lifts_both_records_with_the_verified_phrase():
    out, _ = _apply(CONST, [_item("constant_write", "Low surface salience")])
    for r in out.values():
        assert r["v"] == ac.PASS and r["writer_scan"]["constant_phrases"] == [dict(verified=True, file="w.py", entry="citation_human", form="constant_write", literal="Low surface salience", findings=1)]
        assert ac.writer_scan_problem(r) is None
    assert ac.writer_scan_earned("Null.blank_rows", out["Null.blank_rows"], out)


def test_declared_optional_suffixes_lift_each_one_checked():
    out, _ = _apply(SUFFIX, [_item("optional_suffix", " (counted in reverse)"), _item("optional_suffix", " (house {house})")])
    assert all(r["v"] == ac.PASS and len(r["writer_scan"]["constant_phrases"]) == 2 for r in out.values())


def test_a_literal_edited_in_the_writer_refuses_the_declaration_no_detector():
    out, _ = _apply(CONST.replace("Low surface salience", "Low surface salience!"), [_item("constant_write", "Low surface salience")])
    assert all(r["v"] == ac.NO_DET and "not present verbatim" in r["measured"] for r in out.values())


def test_a_literal_removed_from_the_writer_refuses_the_declaration():
    out, _ = _apply(SUFFIX.replace(" (counted in reverse)", " (reverse)"), [_item("optional_suffix", " (counted in reverse)"), _item("optional_suffix", " (house {house})")])
    assert all(r["v"] == ac.NO_DET and "not present verbatim" in r["measured"] for r in out.values())
    gone = CONST.replace('"Low surface salience"', 'str(chart_id)')         # the scan is then clean on its own: the declaration lifts nothing (no constant_phrases block)
    out, ws = _apply(gone, [_item("constant_write", "Low surface salience")])
    assert ws["v"] == "PASS" and all("writer_scan" not in r and r["v"] == ac.PARTIAL for r in out.values())


def test_an_undeclared_extra_literal_still_blocks_and_is_named():
    out, _ = _apply(SUFFIX, [_item("optional_suffix", " (counted in reverse)")])      # the house suffix is on the next line: its finding is not covered
    for r in out.values():
        assert r["v"] == ac.PARTIAL and "outside every declared phrase" in r["measured"] and "writer_scan" not in r
    extra = CONST.replace('"Low surface salience"', '"Low surface salience" if chart_id else "Other fixed text"')
    ws, _ = _scan(extra)
    out, _ = _apply(extra, [_item("constant_write", "Low surface salience")])
    assert all(r["v"] in (ac.PARTIAL, ac.NO_DET) for r in out.values())


def test_a_second_undeclared_suffix_on_the_same_line_is_not_hidden_by_the_scans_one_finding_per_line():
    src = SQL + 'def run(conn, c, g, rev, h):\n    t = f"A {g}" + (" (counted in reverse)" if rev else "") + (" (extra)" if h else "")\n    conn.execute(SQL, {"chart_id": c, "citation_human": t})\n'
    ws, u = _scan(src)
    assert len(ws["problems"]) == 1
    out, _ = _apply(src, [_item("optional_suffix", " (counted in reverse)")])
    assert all(r["v"] == ac.PARTIAL and "outside every declared phrase" in r["measured"] for r in out.values())


def test_a_declared_literal_that_flags_nothing_any_more_is_a_stale_declaration():
    out, _ = _apply(CONST, [_item("constant_write", "Low surface salience"), _item("optional_suffix", " (counted in reverse)")])
    assert all(r["v"] == ac.NO_DET for r in out.values())


def test_a_fallback_the_declaration_does_not_name_keeps_the_cap():
    src = CONST.replace('"Low surface salience"', '"Low surface salience" + (g or "")').replace("def run(conn, chart_id)", "def run(conn, chart_id, g)")
    ws, _ = _scan(src)
    out, _ = _apply(src, [_item("constant_write", "Low surface salience")])
    assert ws["problems"] and all(r["v"] in (ac.PARTIAL, ac.NO_DET) for r in out.values())


def test_a_data_level_finding_is_never_lifted():
    ws, u = _scan(CONST)
    out = _records()
    out["Null.blank_rows"] = dict(v=ac.FAIL, measured="a blank row")
    ac._apply_constant_phrases(out, ["citation_human"], dict(scan_result=ws, scan_units=u), dict(writer_constant_phrases=[_item("constant_write", "Low surface salience")]))
    assert out["Null.blank_rows"]["v"] == ac.FAIL and out["Null.schema_default"]["v"] == ac.PARTIAL


def test_the_entry_must_be_a_declared_prose_field_and_the_file_in_scope():
    ws, u = _scan(CONST)
    for item in (dict(_item("constant_write", "Low surface salience"), entry="other_col"), _item("constant_write", "Low surface salience", file="elsewhere.py")):
        out = _records()
        ac._apply_constant_phrases(out, ["citation_human"], dict(scan_result=ws, scan_units=u), dict(writer_constant_phrases=[item]))
        assert all(r["v"] == ac.NO_DET for r in out.values())


def test_a_tampered_lift_block_is_not_earned():
    out, _ = _apply(CONST, [_item("constant_write", "Low surface salience")])
    r = copy.deepcopy(out["Null.blank_rows"])
    r["writer_scan"]["constant_phrases"][0]["verified"] = False
    assert ac.writer_scan_problem(r) is not None
    r = copy.deepcopy(out["Null.blank_rows"])
    r["writer_scan"]["constant_phrases"][0]["entry"] = "not_an_entry"
    assert ac.writer_scan_problem(r) is not None


def test_malformed_declarations_fail_validation():
    good = dict(writer_constant_phrases=[_item("constant_write", "Low surface salience")])
    assert ac.writer_constant_phrases_problem(good) is None
    for mut in (lambda d: d["writer_constant_phrases"][0].update(form="blanket"), lambda d: d["writer_constant_phrases"][0].update(literal=""),
                lambda d: d["writer_constant_phrases"][0].update(extra=1), lambda d: d["writer_constant_phrases"][0].update(evidence="no/such/file.py:1"),
                lambda d: d["writer_constant_phrases"].append(copy.deepcopy(d["writer_constant_phrases"][0]))):
        d = copy.deepcopy(good)
        mut(d)
        assert ac.writer_constant_phrases_problem(d)


def test_the_committed_declarations_validate_and_name_each_literal():
    decls = ac.load_asset_declarations()
    kar = {(d["form"], d["literal"]) for d in decls["bo_karanajala"]["writer_constant_phrases"]}
    assert kar == {("optional_suffix", " (counted in reverse)"), ("optional_suffix", ", cancelled"), ("optional_suffix", " (house {house})")}
    ana = {d["literal"] for d in decls["bo_anveshana"]["writer_constant_phrases"]}
    assert ana == {"Low surface salience — acharya less likely to notice", "High structural + convergence consequence", "Semantic meaning-vector far from chart centroid", "Bridges multiple analytical subsystems"}
    for aid in ("bo_karanajala", "bo_anveshana"):
        assert all(d["entry"] in decls[aid]["prose_fields"] and d["file"] == f"{aid}.py" for d in decls[aid]["writer_constant_phrases"])


def test_every_committed_literal_is_present_verbatim_in_the_real_writer_on_this_checkout():
    decls = ac.load_asset_declarations()
    for aid in ("bo_karanajala", "bo_anveshana"):
        units, _ = ac.writer_scan_scope(aid, ac.registered_ids("")[aid])
        ws = WS.scan(units, list(decls[aid]["prose_fields"]), {ac.parse_prose_field(e)[0]: [t["table"] for t in decls[aid]["produced_tables"]] for e in decls[aid]["prose_fields"]},
                     is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field)
        chk = ac.constant_phrases_check(decls[aid]["writer_constant_phrases"], decls[aid]["prose_fields"], ws, units)
        assert chk["problems"] == [] and len(chk["covered"]) == len(decls[aid]["writer_constant_phrases"])
