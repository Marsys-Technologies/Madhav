"""test_n278_name_code_pairs.py: SS N-278 `vocab_name_code_pairs` on the Vocab.alias value detector.

bodha_msr_signals.configuration_jsonb of bo_arudha / bo_nakshatra_semantic / bo_sudarshana / bo_vargottama_dhana holds {"graha": "Mercury", "graha_code": "MER"} objects whose name and code both come from the
graha vocabulary module. The column read two spelling families (PARTIAL, 'mixed'). The declaration is CHECKED: the code table is read from the module's own _SUBJECT_TO_TITLE, the asset's writer must emit the
shape, and one read of the whole scope must show every released code occurrence is the partner of its own name in the same object. Forgeries lift nothing.

No database: the audit statement is exercised through a faked `scalar` that evaluates the same question in Python (`_audit`), and the SQL text itself is checked structurally. A real-SQL rehearsal of
`vocab_pair_audit_sql` on a disposable PostgreSQL was NOT run for this change (see the PR body).
"""
from __future__ import annotations

import copy
import json
import pathlib
import shutil
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
SIDECAR = HERE.parents[2] / "python-sidecar"
sys.path.insert(0, str(SIDECAR))

import asset_census as ac  # noqa: E402

T, C = "bodha_msr_signals", "configuration_jsonb"
ASSETS = ("bo_arudha", "bo_nakshatra_semantic", "bo_sudarshana", "bo_vargottama_dhana")
OWN = {T: ([C, "chart_id"], {C: "jsonb", "chart_id": "uuid"}, None)}
DECLS = ac.load_asset_declarations()
CODES = ac.vocab_graha_code_table()
SPEC = dict(name_key="graha", code_key="graha_code", codes=CODES)


def _sample(values, key_hits=()):
    return dict(values=list(values), emb=[], key_hits=list(key_hits), complete=True, rows=len(values), oversized=0, deep=0, leaves=0, keys=0)


def _audit(rows):
    """The pair audit answer computed in Python from json rows: what `vocab_pair_audit_sql` is written to return."""
    def leaves(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from leaves(v)
        elif isinstance(x, list):
            for v in x:
                yield from leaves(v)
    objs = [r for r in rows if isinstance(r, dict) and "graha_code" in r]
    ok = [r for r in objs if isinstance(r.get("graha"), str) and isinstance(r["graha_code"], str) and CODES.get(r["graha_code"]) == r["graha"]]
    bad = sorted({(r.get("graha"), r["graha_code"]) for r in objs if r not in ok}, key=str)[:5]
    return dict(rows=len(rows), code_leaves=sum(1 for r in rows for s in leaves(r) if s in CODES), with_code_key=len(objs), paired=len(ok),
                bad=[list(b) for b in bad], pairs=[list(p) for p in sorted({(r["graha"], r["graha_code"]) for r in ok})])


GOOD = [{"graha": "Mercury", "graha_code": "MER", "house": 3}, {"graha": "Ketu", "graha_code": "KET_MEAN"}, {"graha": "Sun", "graha_code": "SUN", "occupants": ["Moon"]}]


@pytest.fixture
def fake_db(monkeypatch):
    """`put(rows)`: the vocab statements answer from these json rows. The pair audit goes through the REAL `vocab_fetch_pair_audit` (statement built, parsed), answered by `_audit`."""
    state = dict(rows=[])

    def scalar(sql, *a, **k):
        assert "jsonb_path_query" in sql and "strict $.**" in sql            # only the pair audit is asked here
        return json.dumps(_audit(state["rows"]))
    monkeypatch.setattr(ac, "scalar", scalar)
    return lambda rows: state.__setitem__("rows", rows)


# ───────────────────────── the code table and the declarations ─────────────────────────

def test_the_code_table_is_read_from_the_vocabulary_modules_own_table_never_typed():
    from brahmagyan import graha_vocabulary as gv
    assert CODES == dict(gv._SUBJECT_TO_TITLE) and CODES["MER"] == "Mercury" and CODES["KET_MEAN"] == "Ketu" and CODES["RAH_MEAN"] == "Rahu"
    src = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert '"RAH_MEAN": "Rahu"' not in src and "'RAH_MEAN': 'Rahu'" not in src          # the engine never types the table
    mine = json.dumps([DECLS[a]["vocab_name_code_pairs"] for a in ASSETS])
    assert not any(code in mine for code in ("MER", "KET_MEAN", "RAH_MEAN", "Mercury"))    # nor does a declaration


@pytest.mark.parametrize("aid", ASSETS)
def test_each_of_the_four_assets_declares_exactly_the_one_column_and_the_sets_resolve(aid):
    e = DECLS[aid]
    assert [(d["table"], d["column"], d["name_key"], d["code_key"]) for d in e["vocab_name_code_pairs"]] == [(T, C, "graha", "graha_code")]
    sets, problems = ac.vocab_name_code_pair_sets(e, aid, OWN)
    assert problems == [] and set(sets) == {(T.lower(), C.lower())}
    assert sets[(T.lower(), C.lower())]["codes"] == CODES


def test_no_other_asset_declares_it():
    assert sorted(a for a, e in DECLS.items() if e.get("vocab_name_code_pairs")) == sorted(ASSETS)


# ───────────────────────── refusals: the declaration's own claims ─────────────────────────

def test_a_column_that_is_not_json_or_not_present_or_a_table_not_owned_is_refused():
    e = DECLS["bo_arudha"]
    assert ac.vocab_name_code_pair_sets(e, "bo_arudha", {T: ([C], {C: "text"}, None)})[0] == {}
    assert "json" in ac.vocab_name_code_pair_sets(e, "bo_arudha", {T: ([C], {C: "text"}, None)})[1][0]
    assert ac.vocab_name_code_pair_sets(e, "bo_arudha", {T: (["chart_id"], {"chart_id": "uuid"}, None)})[0] == {}
    assert ac.vocab_name_code_pair_sets(e, "bo_arudha", {})[0] == {}
    assert ac.vocab_name_code_pair_sets(e, "bo_arudha", {T: (None, None, None)})[0] == {}


def test_a_writer_that_does_not_emit_the_shape_is_refused():
    e = copy.deepcopy(DECLS["bo_arudha"])
    e["vocab_name_code_pairs"][0]["name_key"] = "graha_label"                    # the emitter builds no dict with that key
    sets, problems = ac.vocab_name_code_pair_sets(e, "bo_arudha", OWN)
    assert sets == {} and "does not write that shape" in problems[0]
    sets, problems = ac.vocab_name_code_pair_sets(DECLS["bo_arudha"], "bo_sudarshana", OWN)       # another asset's writer does not import this emitter
    assert sets == {} and "not the asset's emitter" in problems[0]
    sets, problems = ac.vocab_name_code_pair_sets(DECLS["bo_arudha"], "bo_no_such_asset", OWN)
    assert sets == {} and problems


def test_an_unreadable_module_or_a_table_that_is_not_the_released_comprehension_reads_no_detector(tmp_path):
    sets, problems = ac.vocab_name_code_pair_sets(DECLS["bo_arudha"], "bo_arudha", OWN, root=tmp_path)
    assert sets == {} and "code table could not be read" in problems[0]
    bdir = tmp_path / "platform" / "python-sidecar" / "brahmagyan"
    bdir.mkdir(parents=True)
    shutil.copy(SIDECAR / "brahmagyan" / "graha_vocabulary.py", bdir / "graha_vocabulary.py")
    assert ac.vocab_graha_code_table(tmp_path) == CODES
    (bdir / "graha_vocabulary.py").write_text("from brahmagyan.l0_semantic_release import SEMANTIC_RELEASE\n_SUBJECT_TO_TITLE = {'MER': 'Mars'}\n", encoding="utf-8")
    with pytest.raises(ac.Unknown):
        ac.vocab_graha_code_table(tmp_path)                                      # a typed table is not the module's released comprehension
    (bdir / "graha_vocabulary.py").write_text("from brahmagyan.l0_semantic_release import SEMANTIC_RELEASE\n_SUBJECT_TO_TITLE = {e['canonical_subject_code']: open('x') for e in SEMANTIC_RELEASE['entities']}\n", encoding="utf-8")
    with pytest.raises(ac.Unknown):
        ac.vocab_graha_code_table(tmp_path)                                      # a call inside the comprehension is never evaluated


def test_a_malformed_declaration_fails_validation():
    base = DECLS["bo_arudha"]
    assert ac.vocab_name_code_pairs_problem(base) is None
    for mut in (lambda d: d["vocab_name_code_pairs"][0].update(extra=1), lambda d: d["vocab_name_code_pairs"][0].update({"class": "rashi"}),
                lambda d: d["vocab_name_code_pairs"][0].update(code_key="graha"), lambda d: d["vocab_name_code_pairs"][0].update(evidence="no/such/file.py:1"),
                lambda d: d["vocab_name_code_pairs"].append(copy.deepcopy(d["vocab_name_code_pairs"][0]))):
        d = copy.deepcopy(base)
        mut(d)
        assert ac.vocab_name_code_pairs_problem(d)


# ───────────────────────── the grading (pure) ─────────────────────────

def test_without_the_declaration_the_name_and_code_read_as_a_mixed_column():
    rec = ac.vocab_grade_column(T, C, "json", _sample(["Mercury", "MER", "Ketu", "KET_MEAN"]))
    assert rec["mixed"] is True


def test_with_a_verified_audit_the_codes_are_lifted_and_named_and_the_column_is_one_family():
    rep = ac.vocab_pair_report(_audit(GOOD), SPEC)
    assert rep["violations"] == [] and rep["paired"] == {"MER", "KET_MEAN", "SUN"}
    rec = ac.vocab_grade_column(T, C, "json", _sample(["Mercury", "MER", "Ketu", "KET_MEAN", "Sun", "SUN", "Moon"]), paired=rep["paired"])
    assert rec["mixed"] is False and rec["paired_codes"] == ["KET_MEAN", "MER", "SUN"] and "MER" not in rec["canonical"]


def test_a_code_not_in_the_verified_set_is_still_graded_beside_lifted_ones():
    rec = ac.vocab_grade_column(T, C, "json", _sample(["Mercury", "MER", "MAR"]), paired=frozenset({"MER"}))
    assert rec["mixed"] is True and "MAR" in rec["canonical"]


def test_forgery_a_mismatched_pair_lifts_nothing_and_is_a_fail():
    rows = GOOD + [{"graha": "Mars", "graha_code": "MER"}]
    rep = ac.vocab_pair_report(_audit(rows), SPEC)
    assert rep["paired"] == frozenset() and "'Mars' beside 'MER'" in rep["violations"][0] and "that code is 'Mercury'" in rep["violations"][0]
    rec = ac.vocab_grade_column(T, C, "json", _sample(["Mercury", "MER", "Mars"]), paired=rep["paired"])
    assert rec["mixed"] is True
    out = ac.vocab_values_record([rec], [], [T], pair_reports={f"{T}.{C}": {**rep, "paired": sorted(rep["paired"])}})
    assert out["v"] == ac.FAIL and "contradicted" in out["measured"]


def test_forgery_an_unknown_code_beside_a_canonical_name_is_a_fail_not_a_pass():
    rep = ac.vocab_pair_report(_audit(GOOD + [{"graha": "Mercury", "graha_code": "XXX"}]), SPEC)
    assert rep["paired"] == frozenset() and "not a released code" in rep["violations"][0]
    rec = ac.vocab_grade_column(T, C, "json", _sample(["Mercury", "Sun"]))
    assert ac.vocab_values_record([rec], [], [T])["v"] == ac.PASS                 # today the unknown code is invisible by value ...
    out = ac.vocab_values_record([rec], [], [T], pair_reports={f"{T}.{C}": {**rep, "paired": []}})
    assert out["v"] == ac.FAIL                                                    # ... the audit is what catches it


def test_forgery_a_lowercased_or_variant_name_with_a_valid_code_is_not_a_pair():
    for name in ("mercury", "MERCURY", "Mercury ", "Budha"):
        rep = ac.vocab_pair_report(_audit([{"graha": name, "graha_code": "MER"}]), SPEC)
        assert rep["paired"] == frozenset() and rep["violations"], name


def test_forgery_a_code_without_a_name_or_a_non_string_name_is_not_a_pair():
    for obj in ({"graha_code": "MER"}, {"graha": None, "graha_code": "MER"}, {"graha": 3, "graha_code": "MER"}, {"graha": "Mercury", "graha_code": 5}):
        rep = ac.vocab_pair_report(_audit([obj]), SPEC)
        assert rep["paired"] == frozenset() and rep["violations"], obj


def test_forgery_a_code_anywhere_else_in_the_column_voids_the_lift():
    for obj in ({"graha": "Mercury", "graha_code": "MER", "lord": "MAR"}, {"graha": "Mercury", "graha_code": "MER", "occupants": ["SUN"]},
                {"nested": {"graha": "Mercury", "graha_code": "MER"}}, {"graha": "MER"}, ["MER"]):
        rep = ac.vocab_pair_report(_audit(GOOD + [obj]), SPEC)
        assert rep["paired"] == frozenset() and any("outside a verified" in v for v in rep["violations"]), obj


def test_an_extra_undeclared_column_gets_no_lift():
    rec = ac.vocab_grade_column(T, "citation_ref", "text", _sample(["Mercury", "MER"]))        # no `paired` for another column: still mixed
    assert rec["mixed"] is True
    sets, _ = ac.vocab_name_code_pair_sets(DECLS["bo_arudha"], "bo_arudha", OWN)
    assert (T.lower(), "citation_ref") not in sets


def test_an_unreadable_audit_reads_no_detector_never_pass():
    rep = ac.vocab_pair_report(dict(unread="the pair audit exceeded the statement timeout: x"), SPEC)
    assert rep["paired"] == frozenset() and rep["unread"]
    rec = ac.vocab_grade_column(T, C, "json", _sample(["Mercury"]))
    out = ac.vocab_values_record([rec], [], [T], pair_reports={f"{T}.{C}": {**rep, "paired": []}})
    assert out["v"] == ac.NO_DET and out["declaration_disagreements"][0]["field"] == "vocab_name_code_pairs"


def test_the_refusal_record_is_no_detector_and_names_the_problem():
    r = ac.vocab_name_code_pairs_refuse({"vocab_values": {"x": 1}}, ["a: b"], DECLS["bo_arudha"])
    assert r["v"] == ac.NO_DET and "a: b" in r["measured"] and r["declaration_disagreements"][0]["field"] == "vocab_name_code_pairs"


# ───────────────────────── the fetch path (statement built and parsed, the answer faked) ─────────────────────────

def test_the_audit_statement_is_a_single_read_only_select_over_the_whole_scope_with_the_codes_from_the_table():
    sql = ac.vocab_pair_audit_sql(T, C, SPEC, "chart_id IS NULL")
    assert sql.lstrip().upper().startswith("WITH") and "chart_id IS NULL" in sql and "strict $.**" in sql and "LIMIT" in sql
    assert all(w not in sql.upper() for w in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER "))
    assert "('MER','Mercury')" in sql and "('KET_MEAN','Ketu')" in sql


def test_the_fetch_path_end_to_end_with_a_faked_answer(fake_db):
    fake_db(GOOD)
    assert ac.vocab_pair_report(ac.vocab_fetch_pair_audit(T, C, SPEC, None), SPEC)["paired"] == {"MER", "KET_MEAN", "SUN"}
    fake_db(GOOD + [{"graha": "Mars", "graha_code": "MER"}])
    assert ac.vocab_pair_report(ac.vocab_fetch_pair_audit(T, C, SPEC, None), SPEC)["paired"] == frozenset()


def test_the_fetch_path_reads_a_timeout_or_a_malformed_answer_as_unread(monkeypatch):
    def boom(sql, *a, **k):
        raise ac.Unknown("ERROR:  canceling statement due to statement timeout")
    monkeypatch.setattr(ac, "scalar", boom)
    aud = ac.vocab_fetch_pair_audit(T, C, SPEC, None)
    assert "statement timeout" in aud["unread"] and ac.vocab_pair_report(aud, SPEC)["unread"]
    monkeypatch.setattr(ac, "scalar", lambda *a, **k: json.dumps({"rows": 1}))
    assert "unread" in ac.vocab_fetch_pair_audit(T, C, SPEC, None)
