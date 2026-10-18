"""test_n431_gestalt_samvada_declared.py: SS N-431, the declarations the engine's N-430 forms (PR #3428) were built for, now written for the two assets.

bo_chart_gestalt  `writer_constant_phrases`: the builder writes fixed pointer sentences into the `note` leaves of eight JSON columns and one into every `verdict_note`; the writer scan reports every fixed literal
                  on every entry of the column family (7 sentences x 8 `.$.note` entries + the verdict_note literal on the wildcard entry = 57 findings over 8 literals). The declaration states each sentence
                  ONCE (entry as a list, literal_max 300 for the two sentences past 160 characters) and closes (live subset check) only the leaves whose stored value IS the declared sentence.
bo_samvada        `logical_key` (the view is a GROUP BY of chart_id, ayanamsha_id) and `passive_projection` (the writer runs no DDL or DML).
Offline: the real writers and the committed declarations; the live reads (label_read, view definition, duplicate/NULL/row probes) are faked, and the tests say so. Nothing here claims a live result.
"""
from __future__ import annotations

import ast
import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402

GEST, SAMVADA = "bo_chart_gestalt", "bo_samvada"
WDIR = "platform/python-sidecar/pipeline/orchestrator/writers/"
GEST_PY, SAM_PY = WDIR + "bo_chart_gestalt.py", WDIR + "bo_samvada.py"
NOTE_ENTRIES = ["defining_threads_jsonb.$.note", "headline_jsonb.$.note", "watch_list_jsonb.$.note", "central_question_jsonb.$.note", "outliers_jsonb.$.note",
                "contested_areas_jsonb.$.note", "zoom_spine_jsonb.$.note", "headline_epistemic_jsonb.$.note"]
WILD = "domain_verdict_map_jsonb.$.*.verdict_note"
# the leaves whose stored value IS the declared sentence. contested_areas stores a composed f-string; headline_epistemic's transient sentence is rewritten by _patch_fragility (a composed _fragility_note
# text) in every run(), so a closure over it would read a stray value by construction.
CLOSED = [e for e in NOTE_ENTRIES if e not in ("contested_areas_jsonb.$.note", "headline_epistemic_jsonb.$.note")]
NULL2 = ("Null.schema_default", "Null.blank_rows")


@pytest.fixture(scope="module")
def decls():
    return ac.load_asset_declarations()                        # validates the whole file (every writer_constant_phrases / logical_key / passive_projection entry)


@pytest.fixture(scope="module")
def tree():
    return ast.parse((ac.ROOT / GEST_PY).read_text(encoding="utf-8"))


def _flat(items):
    return [(d["literal"], e, d) for d in items for e in (d["entry"] if isinstance(d["entry"], list) else [d["entry"]])]


# ───────────────────────── the declarations validate ─────────────────────────

def test_the_declarations_validate(decls):
    g, s = decls[GEST], decls[SAMVADA]
    assert ac.writer_constant_phrases_problem(g) is None and ac.logical_key_problem(s) is None and ac.passive_projection_problem(s) is None
    assert s["kind"] == "view" and s["logical_key"]["object"] == "vw_chart_digest" and s["logical_key"]["columns"] == ["chart_id", "ayanamsha_id"] and s["logical_key"]["basis"] == "group_by"
    assert "projection" in s["passive_projection"]["why"].casefold()


# ───────────────────────── bo_chart_gestalt: the literals ARE the writer's sentences ─────────────────────────

def _writer_sentences(tree):
    """{literal: first line} of every plain string the builder stores under the key `note` or `verdict_note` (a dict display with a constant string value). An f-string (contested_areas) is not one."""
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value in ("note", "verdict_note") and isinstance(v, ast.Constant) and isinstance(v.value, str):
                    out.setdefault(v.value, v.lineno)
    return out


def test_the_eight_literals_equal_the_writers_sentences_and_their_evidence_lines_are_the_sentences(decls, tree):
    items = decls[GEST]["writer_constant_phrases"]
    sent = _writer_sentences(tree)
    assert len(sent) == 8 and len(items) == 8 and sorted(d["literal"] for d in items) == sorted(sent)               # 7 `note` sentences + the verdict_note one, nothing more, nothing less
    for d in items:
        assert d["file"] == "bo_chart_gestalt.py" and d["form"] == "constant_write"
        path, line = d["evidence"].rsplit(":", 1)
        assert path == GEST_PY and int(line) == sent[d["literal"]]                                                    # the cited line is where the sentence starts
        assert "none" not in d["why"].casefold().split() and "null" not in d["why"].casefold().split()               # the placeholder filter's words
    assert sorted(int(d["evidence"].rsplit(":", 1)[1]) for d in items) == [158, 278, 313, 344, 396, 413, 484, 512]


def test_the_two_long_sentences_carry_literal_max_300_and_no_other_item_carries_one(decls):
    for d in decls[GEST]["writer_constant_phrases"]:
        assert (d.get("literal_max") == 300) == (len(d["literal"]) > ac.WRITER_CONSTANT_PHRASES_LITERAL_DEFAULT)
        assert len(d["literal"]) <= d.get("literal_max", ac.WRITER_CONSTANT_PHRASES_LITERAL_DEFAULT)
    assert sorted(len(d["literal"]) for d in decls[GEST]["writer_constant_phrases"] if "literal_max" in d) == [256, 269]


def test_seven_sentences_cover_the_eight_note_leaves_and_the_verdict_note_literal_covers_the_wildcard(decls):
    items = decls[GEST]["writer_constant_phrases"]
    note = [d for d in items if isinstance(d["entry"], list)]
    assert len(note) == 7 and all(d["entry"] == NOTE_ENTRIES for d in note)
    (verdict,) = [d for d in items if d["entry"] == WILD]
    assert verdict["literal"].startswith("no verdict stored") and "closed" not in verdict                                # a key-wildcard path cannot be closure-read (label_read refuses it)
    assert len(_flat(items)) == 57
    assert all(d["closed"] == CLOSED for d in note)                                                                      # six leaves; contested_areas and headline_epistemic are NOT closed
    assert {x["entry"] for x in ac._cp_expand(items) if x["_closed"]} == set(CLOSED)


# ───────────────────────── bo_chart_gestalt: the real scan against the declaration ─────────────────────────

def _scan(decl):
    ws_mod = ac._lint_module("writer_literal_scan")
    units, _ = ac.writer_scan_scope(GEST, ac.registered_ids("")[GEST])
    pf = list(decl["prose_fields"])
    ws = ws_mod.scan(units, pf, {ac.parse_prose_field(e)[0]: ["bodha_chart_gestalt"] for e in pf}, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field)
    return ws, units


def test_the_declaration_covers_every_scan_finding_and_nothing_is_stale(decls):
    ws, units = _scan(decls[GEST])
    assert len(ws["problems"]) == 57
    chk = ac.constant_phrases_check(decls[GEST]["writer_constant_phrases"], decls[GEST]["prose_fields"], ws, units)
    assert chk["problems"] == [] and chk["left"] == [] and len(chk["flat"]) == 57 and set(chk["covered"].values()) == {1}


# ───────────────────────── bo_chart_gestalt: the Null / Narr grading (live reads faked) ─────────────────────────

def _grade(decl, monkeypatch, reader):
    """prose_checks('bo_chart_gestalt') on the real writer scope with the live reads STUBBED: `reader(table, entry, values)` replaces label_read; row counts are stubbed (no blank, 500 checkable)."""
    tbl, pf = "bodha_chart_gestalt", decl["prose_fields"]
    cols = ["chart_id", "ayanamsha_id"] + sorted({ac.parse_prose_field(e)[0] for e in pf})
    types = {c: ("uuid" if c == "chart_id" else "text" if c == "ayanamsha_id" else "jsonb") for c in cols}
    files = ac.registered_ids("")[GEST]
    units, beyond = ac._delegation_scope(GEST, files)
    ctx = dict(table=tbl, own={tbl: (cols, types, {})}, tests=[], vocabulary=set(), paths=[u["path"] for u in units], units=units, beyond=beyond, root=str(ac.ROOT))
    ctx["written"] = ac.written_columns(units, [tbl])
    ctx["scan_units"], ctx["scan_beyond"] = ac.writer_scan_scope(GEST, files)
    ctx["counts"] = {e: dict(blank=0, checkable=500, scope="chart") for e in pf}
    monkeypatch.setattr(ac, "label_read", reader)
    return ac.prose_checks(GEST, decl, ctx)


def _faithful(table, entry, values):
    """What the live table holds if every closed leaf stores exactly one declared sentence (an ASSUMPTION of this offline test, not a reading)."""
    return [sorted(values)[0]]


def test_without_the_declaration_both_null_cells_stay_partial(decls, monkeypatch):
    d = copy.deepcopy(decls[GEST])
    del d["writer_constant_phrases"]
    out = _grade(d, monkeypatch, _faithful)
    assert all(out[c]["v"] == ac.PARTIAL and "writer_scan" not in out[c] for c in NULL2)
    assert out["Narr.agree"]["v"] == ac.PASS


def test_a_live_read_that_did_not_happen_keeps_the_cap_and_names_the_six_closed_leaves(decls, monkeypatch):
    out = _grade(decls[GEST], monkeypatch, lambda table, entry, values: None)
    for c in NULL2:
        assert out[c]["v"] == ac.PARTIAL and "writer_scan" not in out[c] and "the closure is not verified" in out[c]["measured"]
        assert all(e in out[c]["measured"] for e in CLOSED) and "headline_epistemic_jsonb.$.note: " not in out[c]["measured"] and "contested_areas_jsonb.$.note: " not in out[c]["measured"]
    assert out["Narr.agree"]["v"] == ac.PASS


def test_when_each_closed_leaf_holds_a_declared_sentence_both_null_cells_read_pass(decls, monkeypatch):
    out = _grade(decls[GEST], monkeypatch, _faithful)
    for c in NULL2:
        r = out[c]
        assert r["v"] == ac.PASS and ac.writer_scan_problem(r) is None, r["measured"][:300]
        assert "57 declared constant phrase(s) (57 finding(s))" in r["measured"]
        assert sorted(r["writer_scan"]["closed_entries"]) == sorted(CLOSED)
    assert ac.writer_scan_earned("Null.blank_rows", out["Null.blank_rows"], out)
    assert out["Narr.agree"]["v"] == ac.PASS


def test_a_stray_stored_value_on_a_closed_leaf_fails_narr_agree_and_keeps_the_cap(decls, monkeypatch):
    def stray(table, entry, values):
        return [sorted(values)[0], "a sentence the writer never declared"] if entry == "outliers_jsonb.$.note" else [sorted(values)[0]]
    out = _grade(decls[GEST], monkeypatch, stray)
    assert out["Narr.agree"]["v"] == ac.FAIL and "a sentence the writer never declared" in out["Narr.agree"]["measured"] and "outliers_jsonb.$.note" in out["Narr.agree"]["measured"]
    assert all(out[c]["v"] == ac.PARTIAL and "writer_scan" not in out[c] for c in NULL2)


def test_closing_headline_epistemic_would_read_a_stray_value_by_construction(decls, monkeypatch):
    """Why that leaf is not closed: run() always rewrites its note with _fragility_note's composed text, so a closure over the transient sentence can never hold."""
    d = copy.deepcopy(decls[GEST])
    for it in d["writer_constant_phrases"]:
        if isinstance(it["entry"], list):
            it["closed"] = CLOSED + ["headline_epistemic_jsonb.$.note"]
    composed = "fragility_class=stable: assessed by the post-loop _assess_fragility() pass across 5 ayanamsha rows of this build; 12 domain(s) comparable across >=2 rows, 0 with a disagreeing dominant valence."
    out = _grade(d, monkeypatch, lambda t, e, v: [composed] if e == "headline_epistemic_jsonb.$.note" else [sorted(v)[0]])
    assert out["Narr.agree"]["v"] == ac.FAIL and "headline_epistemic_jsonb.$.note" in out["Narr.agree"]["measured"]
    src = (ac.ROOT / GEST_PY).read_text(encoding="utf-8")
    assert 'epistemic["note"] = _fragility_note(fragility_result)' in src and "_patch_fragility(conn, chart_id, build_id, fragility_result)" in src


# ───────────────────────── bo_samvada: logical_key and passive_projection (live reads faked) ─────────────────────────

def _view_statement():
    t = ast.parse((ac.ROOT / SAM_PY).read_text(encoding="utf-8"))
    return next(ast.literal_eval(n.value) for n in t.body if isinstance(n, ast.Assign) and any(getattr(x, "id", None) == "_CREATE_VIEW_CLEAN" for x in n.targets))


def test_the_evidence_lines_are_the_group_by_and_the_run_definition(decls):
    lines = (ac.ROOT / SAM_PY).read_text(encoding="utf-8").splitlines()
    lk, pp = decls[SAMVADA]["logical_key"]["evidence"], decls[SAMVADA]["passive_projection"]["evidence"]
    assert lk == f"{SAM_PY}:135" and lines[134].startswith("GROUP BY m.chart_id, m.ayanamsha_id")
    assert pp == f"{SAM_PY}:147" and lines[146].strip().startswith("def run(self, ctx")


def test_the_committed_view_statement_proves_the_declared_key(decls):
    lk = decls[SAMVADA]["logical_key"]
    assert ac.viewdef_proves_key(ac.viewdef_group_by(_view_statement()), lk["columns"]) is None


def test_vocab_identity_reads_pass_on_the_declared_logical_key_with_faked_database_reads(decls, monkeypatch):
    monkeypatch.setattr(ac, "identity_duplicates", lambda tbl, kd: (False, "0 duplicate(s)"))
    monkeypatch.setattr(ac, "identity_has_rows", lambda tbl: True)
    monkeypatch.setattr(ac, "scalar", lambda sql: "f" if "IS NULL" in sql else None)
    vd = _view_statement()
    monkeypatch.setattr(ac, "view_definition", lambda view: (vd, len(vd)))
    cat = dict(views={"vw_chart_digest"}, cols={"vw_chart_digest": ["chart_id", "ayanamsha_id", "msr_signal_count"]})
    r = ac.logical_key_identity("vw_chart_digest", decls[SAMVADA], cat)
    assert r["v"] == ac.PASS and ac.logical_key_block_problem(r) is None and r["logical_key"]["duplicates"] == r["logical_key"]["null_keys"] == 0
    assert ac._check_contribution("Vocab.identity", "L2", r, None)["v"] == ac.PASS


def test_idem_pattern_and_count_integrity_release_to_na_on_the_declared_passive_projection(decls):
    pp = decls[SAMVADA]["passive_projection"]
    b = ac.passive_projection_facts(SAMVADA, ac.registered_ids("")[SAMVADA], ["vw_chart_digest"], True, True)
    assert b["written"] == b["update_only"] == b["delete_only"] == b["scan_hit"] == [] and ac.passive_projection_scan_problem(b) is None
    declared = dict(b, why=pp["why"], evidence=pp["evidence"])
    idem = ac._measure_idem(SAMVADA, ac.registered_ids("")[SAMVADA], "upsert", True, ["vw_chart_digest"], False, None, passive=declared)
    assert idem["v"] == ac.NA and idem["cause"] == "passive-projection" and ac.passive_projection_na_problem("Idem.pattern", idem) is None
    rec = dict(v=ac.PARTIAL, measured="count_sql=yes, integrity_check_sql=yes — a constant count_sql cannot fail")
    cnt = ac.passive_count_integrity(rec, "count_sql=yes, integrity_check_sql=yes", declared)
    assert cnt["v"] == ac.NA and cnt["cause"] == "passive-projection-constant-count" and ac.passive_projection_na_problem("Build.count_integrity", cnt) is None
