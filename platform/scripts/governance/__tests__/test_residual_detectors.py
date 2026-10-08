"""test_residual_detectors.py -- the class-(a) residual detectors of the POST-#3176 prediction (Worker F, suvarna/engine-100-residual-detectors).

Each detector closes a named cell family that no declaration can close; every one is tested on the REAL writer sources that motivated it (offline, no database) and on a synthetic
fixture per rule, with the negative twin that must keep reading incomplete.

D1  Build.dag `reads_scan`: `_sql_arg_traced` follows an ANNOTATED module SQL constant (`X: Final[str] = \"\"\"...\"\"\"`, an ast.AnnAssign: ga_dashas / ga_vargas via
    ga_writers/_karaka_roles.py) and a conditional of two traced names (`A_SQL if c else B_SQL`: ga_nakshatra).
"""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_w2_3_deeper_detectors as w3  # noqa: E402

_HDR = w3._HDR


def _side(monkeypatch, tmp_path, body, extra=None):
    files = {"pipeline/orchestrator/writers/ka_up.py": _HDR + body}
    files.update(extra or {})
    return w3._sidecar(monkeypatch, tmp_path, files)


# ───────────────────────── D1: Build.dag, annotated constants and conditional SQL names ─────────────────────────

@pytest.mark.parametrize("aid", ["ga_dashas", "ga_vargas", "ga_nakshatra"])
def test_d1_the_real_writers_that_motivated_it_now_parse_complete(aid):
    files = ac.registered_ids("")[aid]
    s = ac.reads_scan(aid, files)
    assert s["incomplete"] == [], s["incomplete"]
    assert s["reads"], aid                                         # and it did read something: complete is not empty


@pytest.mark.parametrize("aid", ["bo_pramana_mapa"])        # bg_concordance moved out: its two gaps were a closure SQL name and a prose f-string (test_ss_reads_scan_residual.py, D5/D6)
def test_d1_a_genuinely_dynamic_writer_stays_incomplete(aid):
    s = ac.reads_scan(aid, ac.registered_ids("")[aid])
    assert s["incomplete"], aid                                    # a table named dynamically / SQL built at run time is not a literal: still reported


_CLS = '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'


def test_d1_an_annotated_module_constant_is_traced(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path, 'from typing import Final\nREAD_SQL: Final[str] = """SELECT x FROM bg_up WHERE chart_id = %s"""\n' + _CLS + '        ctx.db_conn.execute(READ_SQL, (1,))\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"] == [] and list(s["reads"]) == ["bg_up"], s


def test_d1_an_annotated_constant_that_is_not_a_literal_is_not_traced(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path, 'def _mk():\n    return "SELECT x FROM bg_up"\nREAD_SQL: str = _mk()\n' + _CLS + '        ctx.db_conn.execute(READ_SQL)\n')
    assert ac.reads_scan("ka_up", ["ka_up.py"])["incomplete"], "a computed annotated constant must stay unresolved"


def test_d1_a_bare_annotation_without_a_value_is_not_traced(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path, 'READ_SQL: str\n' + _CLS + '        ctx.db_conn.execute(READ_SQL)\n')
    assert ac.reads_scan("ka_up", ["ka_up.py"])["incomplete"]


def test_d1_an_imported_annotated_constant_is_traced(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path, 'from helpers.sql import READ_SQL\n' + _CLS + '        ctx.db_conn.execute(READ_SQL)\n',
          {"helpers/__init__.py": "", "helpers/sql.py": 'from typing import Final\nREAD_SQL: Final[str] = "SELECT x FROM bg_deep"\n'})
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"] == [] and "bg_deep" in s["reads"], s


def test_d1_a_conditional_of_two_traced_names_is_traced_and_one_untraced_branch_is_not(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path, 'A_SQL = "SELECT x FROM bg_a"\nB_SQL = "SELECT x FROM bg_b"\n' + _CLS + '        ctx.db_conn.execute(A_SQL if ctx.flag else B_SQL)\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"] == [] and sorted(s["reads"]) == ["bg_a", "bg_b"], s
    _side(monkeypatch, tmp_path, 'A_SQL = "SELECT x FROM bg_a"\n' + _CLS + '        ctx.db_conn.execute(A_SQL if ctx.flag else ctx.other_sql)\n')
    assert ac.reads_scan("ka_up", ["ka_up.py"])["incomplete"], "an untraced branch keeps the parse incomplete"


def test_d1_a_plain_assigned_constant_is_still_traced(monkeypatch, tmp_path):
    _side(monkeypatch, tmp_path, 'READ_SQL = "SELECT x FROM bg_up"\n' + _CLS + '        ctx.db_conn.execute(READ_SQL)\n')
    s = ac.reads_scan("ka_up", ["ka_up.py"])
    assert s["incomplete"] == [] and list(s["reads"]) == ["bg_up"], s


# ───────────────────────── D2: the Null writer scan reads the writer at the produced-set hop depth ─────────────────────────

def _scan(aid, tables, deep):
    decl = ac.load_asset_declarations()[aid]
    pf = decl["prose_fields"]
    files = ac.registered_ids("")[aid]
    units, beyond = ac.writer_scan_scope(aid, files) if deep else ac._delegation_scope(aid, files)
    own = {t: (list(cols), None, None) for t, cols in tables.items()}
    holders = {ac.parse_prose_field(e)[0]: ac._holders(ac.parse_prose_field(e)[0], own) for e in pf}
    return ac._lint_module("writer_literal_scan").scan(units, list(pf), holders, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts,
                                                       parse_entry=ac.parse_prose_field, beyond=beyond)


MSR = {"bodha_msr_signals": ["signal_headline_text", "signal_summary_text", "citation_human"]}


@pytest.mark.parametrize("aid", ["bo_nakshatra_semantic", "bo_special_lagna", "bo_sudarshana"])
def test_d2_a_chain_cut_at_the_default_hop_limit_reads_clean_at_the_deeper_scope(aid):
    shallow, deep = _scan(aid, MSR, False), _scan(aid, MSR, True)
    assert shallow["v"] == "PARTIAL" and any("hop limit" in u for u in shallow["unresolved"]), shallow
    assert deep["v"] == "PASS" and deep["problems"] == [] and deep["unresolved"] == [], deep


@pytest.mark.parametrize("aid,tables", [("ga_nakshatra", {"chart_facts": ["citation_human"]}), ("bo_cgm_paths", {"bodha_cgm_paths": ["path_label_human", "citation_human"]}),
                                        ("bo_sangati", {"bodha_cdlm_cells": ["citation_human"], "bodha_convergence": ["citation_human"], "bodha_triangulation": ["citation_human"]})])
def test_d2_the_assets_that_already_read_clean_still_do_at_the_deeper_scope(aid, tables):
    assert _scan(aid, tables, False)["v"] == _scan(aid, tables, True)["v"] == "PASS"


def test_d2_a_deeper_scope_cannot_clear_a_finding_the_shallow_scope_made():
    for aid, tables in (("bo_anveshana", {"bodha_anveshana": ["citation_human"]}), ("bo_pratijna", {"bodha_pratijna": ["citation_human"]})):
        shallow, deep = _scan(aid, tables, False), _scan(aid, tables, True)
        assert len(deep["problems"]) >= len(shallow["problems"]), aid
        if shallow["problems"]:
            assert deep["v"] == "PARTIAL", aid


def test_d2_the_scan_scope_is_used_by_the_null_records_and_the_default_scope_is_the_fallback():
    aid = "bo_special_lagna"
    decl = ac.load_asset_declarations()[aid]
    pf = decl["prose_fields"]
    files = ac.registered_ids("")[aid]
    base = lambda: {c: dict(v=ac.PARTIAL, clean=True, measured="no schema default / no blank row; writer literal scan is not read") for c in ac.NULL_CHECKS}
    units, beyond = ac._delegation_scope(aid, files)
    su, sb = ac.writer_scan_scope(aid, files)
    own = {"bodha_msr_signals": (list(MSR["bodha_msr_signals"]), None, None)}
    shallow = base()
    ac._apply_writer_scan(shallow, pf, dict(table="bodha_msr_signals", own=own, units=units, beyond=beyond))
    assert all(r["v"] == ac.PARTIAL for r in shallow.values())                             # the default scope: the cut stays unresolved
    deep = base()
    ac._apply_writer_scan(deep, pf, dict(table="bodha_msr_signals", own=own, units=units, beyond=beyond, scan_units=su, scan_beyond=sb))
    assert all(r["v"] == ac.PASS and r["writer_scan"]["verified"] is True for r in deep.values()), deep


# ───────────────────────── D3: SQL comments are not SQL (an apostrophe in a comment hid bo_laksana's INSERT) ─────────────────────────

def _ws():
    return ac._lint_module("writer_literal_scan")


def test_d3_blank_sql_comments_keeps_the_length_and_blanks_only_comments():
    ws = _ws()
    s = "INSERT INTO t (a, -- the writer's own value, (default)\n b /* it's, a comma */, c) VALUES (%(a)s, '--not a comment', \"x--y\")"
    out = ws.blank_sql_comments(s)
    assert len(out) == len(s) and out.count("\n") == s.count("\n")
    assert "writer" not in out and "comma" not in out                       # both comments are gone
    assert "'--not a comment'" in out and '"x--y"' in out                   # a `--` inside a string / quoted identifier is text
    assert "INSERT INTO t (a," in out and "%(a)s" in out


def test_d3_an_unterminated_block_comment_and_a_trailing_line_comment_do_not_raise():
    ws = _ws()
    assert ws.blank_sql_comments("SELECT 1 /* never closed") == "SELECT 1" + " " * len(" /* never closed")
    assert ws.blank_sql_comments("SELECT 1 -- tail") == "SELECT 1" + " " * len(" -- tail")


def test_d3_an_insert_with_an_apostrophe_in_a_column_list_comment_is_read_after_blanking():
    ws = _ws()
    text = ("INSERT INTO public.t (id, -- note: the writer's own value (never the default)\n  citation_human) VALUES (%(id)s, %(citation_human)s)")
    broken_w, broken_i = ws.sql_writes(text, ["t"])
    assert broken_i and not broken_w                                        # unblanked: the apostrophe opens a string, the column list never closes
    writes, issues = ws.sql_writes(ws.blank_sql_comments(text), ["t"])
    assert issues == [] and [w["column"] for w in writes] == ["id", "citation_human"]


def test_d3_the_real_bo_laksana_insert_is_now_parsed_and_its_findings_are_visible():
    aid = "bo_laksana"
    decl = ac.load_asset_declarations()[aid]
    pf = decl["prose_fields"]
    units, beyond = ac.writer_scan_scope(aid, ac.registered_ids("")[aid])
    own = {"bodha_msr_signals": (list(MSR["bodha_msr_signals"]), None, None)}
    holders = {ac.parse_prose_field(e)[0]: ac._holders(ac.parse_prose_field(e)[0], own) for e in pf}
    r = _ws().scan(units, list(pf), holders, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field, beyond=beyond)
    assert not any("unbalanced column list" in u for u in r["unresolved"]), r["unresolved"]
    assert not any("no statement in the scanned scope writes the column" in u for u in r["unresolved"]), r["unresolved"]
    # TI-laksana-fallbacks-001 removed the `or ''` fallbacks the unparsed INSERT used to hide: the scan now reports NO literal_fallback,
    # and (FORM-GAP: a READ of a key, `fact_row.get("citation_human")`, is no longer counted as a supplier of it) the one dynamic-row-construction caveat that
    # used to keep the cell PARTIAL is gone: the real scan is CLEAN, nothing unresolved
    assert not any(p["kind"] == "literal_fallback" for p in r["problems"]), r["problems"]
    assert r["v"] == "PASS" and r["problems"] == [] and r["unresolved"] == [], (r["v"], r["problems"], r["unresolved"])


# ───────────────────────── D4: an embedding vector is not text (prose_none) ─────────────────────────

def test_d4_a_vector_column_is_no_prose_but_any_other_user_defined_type_still_is():
    assert ac.prose_none_kind("USER-DEFINED", "vector") is None and ac.prose_none_kind("user-defined", "HALFVEC") is None
    assert ac.prose_none_kind("USER-DEFINED", "mood") == "enum"                  # an enum of labels may carry text: it must still be closed
    assert ac.prose_none_kind("USER-DEFINED", None) == "enum"                    # unread type name: unknown is never "not prose"
    assert ac.prose_none_kind("ARRAY", "_text") == "array" and ac.prose_none_kind("ARRAY", "_uuid") is None


def test_d4_the_real_chunk_table_reads_n_a_with_its_embedding_vector_and_cannot_without_the_udt():
    import json
    sch = json.loads((ac.ROOT / "00_ARCHITECTURE/control/FINGERPRINT_SCHEMA_EXTRACT_L0.json").read_text(encoding="utf-8"))
    t = sch["tables"]["classical_text_chunks"]
    cols = list(t["columns"])

    def info(ty):
        low = ty.casefold()
        if "vector" in low:
            return "USER-DEFINED"
        if low.endswith("[]"):
            return "ARRAY"
        base = low.split("(")[0].strip()
        return {"character varying": "text", "varchar": "text"}.get(base, base.split(" ")[0] if base.startswith("timestamp") else base)

    types = {c: info(v["type"]) for c, v in t["columns"].items()}
    assert "embedding" in cols and types["embedding"] == "USER-DEFINED"
    udts = {"classical_text_chunks": {"embedding": "vector", **{c: "_text" for c, v in t["columns"].items() if v["type"].endswith("[]")}}}
    keys = {"classical_text_chunks": [list(t["primary_key"])] + [list(u["columns"]) for u in t["unique"]]}
    committed = ac.load_asset_declarations()["bg_texts"]
    tables = {"classical_text_chunks": (cols, types, None)}
    assert committed.get("prose_none") and committed["prose_none"].get("column_scope") == "written"
    # SS audit 2026-10-06: content_en (machine translation), verse_ref and tradition_school (composed), content_sha256 (computed) left the declaration, so the committed
    # asset no longer reads N/A; the vector / udt logic under test is exercised on the committed declaration with those four columns restored here
    removed = ("content_en", "verse_ref", "tradition_school", "content_sha256", "translator", "text_id")
    decl = copy.deepcopy(committed)
    tmpl = next(e for e in decl["prose_none"]["transcription_columns"] if e["column"] == "content_sa")
    have = {e["column"] for e in decl["prose_none"]["transcription_columns"]}
    decl["prose_none"]["transcription_columns"] += [dict(tmpl, column=c) for c in removed if c not in have]       # N-233: content_en is declared again; the other three are templated now (their templates need the live read, so they stay restored as transcriptions here)
    pn = decl["prose_none"]
    pn["templated_columns"] = []                                                                                       # the vector / udt logic is under test, not the template reads
    for k in ("closed_columns", "identifier_columns"):
        pn[k] = [e for e in pn.get(k, []) if e.get("table") != "classical_texts" and not (k == "closed_columns" and e["column"] == "text_id")]                                     # this test passes only the chunk table; the classical_texts declarations are tested in test_n233_texts_decl.py
    decl.pop("curated_corpus", None)
    units, _ = ac.writer_scan_scope("bg_texts", ac.registered_ids("")["bg_texts"])
    written = ac.written_columns(units, ["classical_text_chunks"])
    assert "embedding" in written["classical_text_chunks"]                     # the writer really writes the vector
    got = ac.grade_prose_none("bg_texts", decl, tables, "classical_text_chunks", {}, udts=udts, keys=keys, written=written)
    assert all(r["v"] == ac.NA for r in got.values()), {c: r["measured"][:120] for c, r in got.items() if r["v"] != ac.NA}
    cur = copy.deepcopy(committed)                                                                                     # N-233: the committed declaration, chunk table only and without the templated reads (they need the live table): it leaves exactly the three templated columns open
    cur["prose_none"]["templated_columns"] = []
    for k in ("closed_columns", "identifier_columns"):
        cur["prose_none"][k] = [e for e in cur["prose_none"].get(k, []) if e.get("table") != "classical_texts" and not (k == "closed_columns" and e["column"] == "text_id")]
    cur.pop("curated_corpus", None)
    now = ac.grade_prose_none("bg_texts", cur, tables, "classical_text_chunks", {}, udts=udts, keys=keys, written=written)
    assert any(r["v"] != ac.NA for r in now.values()) and all(c in " ".join(r["measured"] for r in now.values()) for c in ("verse_ref", "tradition_school", "content_sha256", "translator", "text_id")) and "content_en" not in " ".join(r["measured"] for r in now.values())
    no_udt = ac.grade_prose_none("bg_texts", decl, tables, "classical_text_chunks", {}, udts={}, keys=keys, written=written)
    assert any(r["v"] != ac.NA for r in no_udt.values())                      # the unread type name keeps the vector an open label column


@pytest.mark.parametrize("src,kept,gone", [
    ("SELECT $$a -- not a comment$$ -- real comment\n, b", "$$a -- not a comment$$", "real comment"),
    ("SELECT $tag$x -- y /* z$tag$ w -- c", "$tag$x -- y /* z$tag$", " c"),
    ("SELECT E'it\\'s -- text' -- c", "E'it\\'s -- text'", None),
    ("SELECT e'a\\\\' -- real", "e'a\\\\'", "real"),
    ("SELECT 'a''b -- x' -- c", "'a''b -- x'", None),
    ("SELECT price$ -- c", "price$", None),
])
def test_d3_dollar_quoted_and_e_strings_are_text_not_comments_review_low_4(src, kept, gone):
    out = _ws().blank_sql_comments(src)
    assert len(out) == len(src) and kept in out
    if gone:
        assert gone not in out
    assert "-- c" not in out.replace("-- not a comment", "").replace("-- text", "").replace("-- y", "")


def test_d3_an_insert_whose_value_holds_a_dollar_quoted_dashdash_is_still_parsed():
    ws = _ws()
    text = "INSERT INTO t (a, b) VALUES ($q$x -- y$q$, %(b)s) -- trailing"
    writes, issues = ws.sql_writes(ws.blank_sql_comments(text), ["t"])
    assert issues == [] and [w["column"] for w in writes] == ["a", "b"] and "$q$x -- y$q$" in writes[0]["piece"]


def test_d3_the_blankers_both_exist_and_nested_block_comments_still_nest():
    ws = _ws()
    assert callable(ws.blank_sql_literals) and ws._DOLLAR_TAG.match("$tag$")        # B's literal blanker lives beside the comment blanker (a rewrite of one must not drop the other)
    assert ws.blank_sql_comments("a /* b /* c */ d */ e") == "a " + " " * len("/* b /* c */ d */") + " e"
    assert ws.blank_sql_literals("SELECT 'INSERT INTO t'") == "SELECT '" + " " * len("INSERT INTO t") + "'"
