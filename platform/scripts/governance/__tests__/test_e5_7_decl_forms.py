"""test_e5_7_decl_forms.py: E5.7 W2 (SS rulings 2026-10-06): the per-asset reverse leg, the declared prose EXCLUSION form and the closed-values LABEL form.

Every test drives the real census functions; the database is never touched (psql is replaced where a read would happen).
Run: python -m pytest platform/scripts/governance/__tests__/test_e5_7_decl_forms.py -q
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402

PASS, FAIL, PARTIAL, NO_DET, NA = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA


# ───────────────────────── (2) the reverse leg is scoped per asset ─────────────────────────

REG = {
    "bo_pramana_mapa": dict(target_table="synthesis_quality_scorecard", count_sql="SELECT count(*) FROM synthesis_quality_scorecard"),
    "bg_avastha_schemes": dict(target_table="bg_avastha_schemes", count_sql="SELECT count(*) FROM bg_avastha_schemes"),
    "bo_laksana": dict(target_table="bodha_msr_signals", count_sql="SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1"),
    "bo_sudarshana": dict(target_table="bodha_msr_signals", count_sql="SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1"),
}
DECLS = {"bo_pramana_mapa": dict(prose_fields=["notes"]), "bo_laksana": dict(prose_fields=["citation_human"]),
         "bg_avastha_schemes": dict(prose_fields=[]), "bo_sudarshana": dict(prose_fields=["signal_headline_text"])}


def test_asset_tables_are_the_target_plus_the_count_sql_tables():
    t = ac.declared_asset_tables(REG)
    assert t["bo_pramana_mapa"] == {"synthesis_quality_scorecard"} and t["bo_laksana"] == {"bodha_msr_signals"}


def test_a_column_declared_by_one_asset_does_not_hit_an_unrelated_writer_of_the_same_column_name():
    v = ac.prose_vocabulary(DECLS, ac.declared_asset_tables(REG))
    assert v["notes"] == {"synthesis_quality_scorecard"}
    assert ac.prose_reverse_leg({"bg_avastha_schemes": {"notes", "scheme"}}, v) == []            # an unrelated L0 table
    assert ac.prose_reverse_leg({"synthesis_quality_scorecard": {"notes"}}, v) == ["synthesis_quality_scorecard.notes"]
    # the legacy global form is unchanged: any asset declaring the name flips every writer of it
    assert ac.prose_reverse_leg({"bg_avastha_schemes": {"notes"}}, ac.prose_vocabulary(DECLS)) == ["bg_avastha_schemes.notes"]


def test_a_shared_table_is_still_judged_against_every_asset_that_declares_a_column_of_it():
    v = ac.prose_vocabulary(DECLS, ac.declared_asset_tables(REG))
    # bo_sudarshana writes citation_human into bodha_msr_signals, which bo_laksana declares: still a hit (the shared-table case the reverse leg exists for)
    assert ac.prose_reverse_leg({"bodha_msr_signals": {"citation_human"}}, v) == ["bodha_msr_signals.citation_human"]


def test_a_declaring_asset_with_unknown_tables_is_a_wildcard_never_weaker_than_the_global_reading():
    v = ac.prose_vocabulary({"x_unknown": dict(prose_fields=["notes"])}, {})
    assert v == {"notes": {None}}
    assert ac.prose_reverse_leg({"any_table": {"notes"}}, v) == ["any_table.notes"]


def test_the_empty_prose_asset_reads_fail_only_for_a_table_the_declaring_asset_owns():
    entry = {"prose_fields": [], "evidence": {"prose_fields": "platform/python-sidecar/pipeline/orchestrator/writers/ph_x.py:10"}}
    v = ac.prose_vocabulary(DECLS, ac.declared_asset_tables(REG))

    def ctx(table):
        return dict(table=table, own={table: (["id", "notes"], {"id": "text", "notes": "text"}, {})}, tests=(), vocabulary=v, counts=None, paths=[], written={table: {"notes"}})
    hit = ac.prose_checks("t_asset", entry, ctx("synthesis_quality_scorecard"))
    assert hit["Narr.agree"]["v"] == FAIL and "synthesis_quality_scorecard.notes" in hit["Narr.agree"]["measured"]
    miss = ac.prose_checks("t_asset", entry, ctx("bg_avastha_schemes"))
    assert miss["Narr.agree"]["v"] != FAIL


def test_the_real_declarations_scope_notes_to_the_scorecard_table_only():
    decl = ac.load_asset_declarations()
    census = ac.ROOT / "00_ARCHITECTURE" / "control" / "census"
    tabs = {}
    for ts, L in (("193639", "L0"), ("194909", "L1"), ("195251", "L2")):
        doc = json.loads((census / f"asset_census_2026-10-04T{ts}+0530.json").read_text(encoding="utf-8"))[L]
        for a in doc["assets"]:
            tabs[a["asset_id"]] = {t for t in ([a["target_table"]] if a.get("target_table") else []) + list(a.get("count_sql_tables") or [])}
    v = ac.prose_vocabulary(decl, tabs)
    assert v["notes"] == {"synthesis_quality_scorecard"}
    assert ac.prose_reverse_leg({"bg_avastha_schemes": {"notes"}, "bg_dignity_reference": {"notes"}}, v) == []


# ───────────────────────── (1) the declared prose EXCLUSION form ─────────────────────────

REGISTER = {"N-49": {"id": "N-49", "state": "decided"}, "F-0": {"id": "F-0", "state": "decided"}}
DECLINES = {"N-49": {("bo_x", "citation_human")}}
EVID = "platform/python-sidecar/pipeline/orchestrator/writers/ph_x.py:10"
WHY = "the writer states only the graha it profiled in a fixed template, an entity name that states no computed value"


def _entry(**kw):
    e = {"prose_fields": ["signal_headline_text"], "evidence": {"prose_fields": EVID},
         "prose_excluded": [dict(column="citation_human", decision_id="N-49", why=WHY)]}
    e.update(kw)
    return e


def _problem(e, aid="bo_x"):
    return ac.prose_excluded_problem(aid, e, REGISTER, DECLINES)


def test_a_sound_exclusion_is_accepted():
    assert _problem(_entry()) is None
    assert ac.prose_excluded_problem("bo_x", {"prose_fields": ["a"]}, REGISTER, DECLINES) is None          # no key: nothing to check


def test_an_unknown_decision_id_is_refused():
    bad = _entry(prose_excluded=[dict(column="citation_human", decision_id="N-9999", why=WHY)])
    assert "not a usable decision" in _problem(bad)


def test_a_superseded_or_undecided_decision_is_not_usable(tmp_path):
    f = tmp_path / "d.jsonl"
    f.write_text('{"_schema": "x"}\n{"id": "N-1", "state": "decided"}\n{"id": "N-2", "state": "decided", "supersedes": "N-1"}\n{"id": "N-3", "state": "delegated"}\n', encoding="utf-8")
    reg = ac.load_decisions_register(f)
    assert set(reg) == {"N-2"}


def test_a_decision_that_is_not_a_decline_for_that_asset_and_column_is_refused():
    other_col = _entry(prose_excluded=[dict(column="signal_summary_text", decision_id="N-49", why=WHY)])
    assert "not a recorded decline" in _problem(other_col)
    other_decision = _entry(prose_excluded=[dict(column="citation_human", decision_id="F-0", why=WHY)])
    assert "not a recorded decline" in _problem(other_decision)                                           # F-0 exists in the register but declines nothing here
    assert "not a recorded decline" in _problem(_entry(), aid="bo_other")                                  # N-49 declines bo_x, not bo_other


def test_an_exclusion_on_a_column_that_is_declared_prose_is_refused():
    bad = _entry(prose_fields=["signal_headline_text", "citation_human"])
    assert "declared prose" in _problem(bad)


def test_shape_errors_are_refused():
    for bad in ([], [dict(column="citation_human", decision_id="N-49")], [dict(column="1x", decision_id="N-49", why=WHY)],
                [dict(column="citation_human", decision_id="N-49", why=WHY)] * 2, "x"):
        assert _problem(_entry(prose_excluded=bad)) is not None, bad


def _ctx(cols, written, vocab=None, table="t"):
    return dict(table=table, own={table: (cols, {c: "text" for c in cols}, {})}, tests=(), vocabulary=vocab if vocab is not None else {"citation_human"},
                counts=None, paths=[], written={table: set(written)})


def _checked(e, ctx):
    return ac.checked_prose_exclusions("bo_x", e, ac._own3(ctx), ctx["table"], REGISTER, DECLINES)


def test_the_check_applies_an_exclusion_when_the_column_exists_on_the_table():
    ex, block, fail, unread = _checked(_entry(), _ctx(["signal_headline_text", "citation_human"], ["citation_human"]))
    assert ex == {"t.citation_human"} and fail is None and block["excluded"][0]["table"] == "t" and block["excluded"][0]["decision_id"] == "N-49"


def test_a_missing_column_is_a_contradiction_not_an_exclusion():
    ex, block, fail, unread = _checked(_entry(), _ctx(["signal_headline_text"], ["signal_headline_text"]))
    assert ex == set() and "does not carry" in fail


def test_unknown_columns_leave_the_exclusion_unapplied_never_assumed():
    ctx = dict(table="t", own={"t": (None, None, None)}, tests=(), vocabulary={"citation_human"}, counts=None, paths=[], written={"t": {"citation_human"}})
    ex, block, fail, unread = _checked(_entry(), ctx)
    assert ex == set() and fail is None and "not applied" in unread


def test_the_check_re_validates_the_decision_at_measure_time():
    bad = _entry(prose_excluded=[dict(column="citation_human", decision_id="N-9999", why=WHY)])
    ex, block, fail, unread = _checked(bad, _ctx(["citation_human"], ["citation_human"]))
    assert ex == set() and "refused" in fail


def test_an_excluded_vocabulary_column_no_longer_makes_narr_agree_partial_but_an_undeclared_one_still_does(monkeypatch):
    monkeypatch.setattr(ac, "load_decisions_register", lambda path=None: REGISTER)
    monkeypatch.setattr(ac, "load_prose_exclusion_decisions", lambda path=None: DECLINES)
    cols = ["signal_headline_text", "citation_human", "other_note"]
    base = _entry(prose_fields=["signal_headline_text"])
    base.pop("prose_excluded")
    without = ac.prose_checks("bo_x", base, _ctx(cols, ["signal_headline_text", "citation_human"]))["Narr.agree"]
    assert without["v"] == PARTIAL and "citation_human" in without["measured"]
    with_ex = ac.prose_checks("bo_x", _entry(), _ctx(cols, ["signal_headline_text", "citation_human"]))["Narr.agree"]
    assert with_ex["v"] == PASS and with_ex["prose_excluded"]["excluded"][0]["column"] == "citation_human" and "EXCLUDED by declaration" in with_ex["measured"]
    two = ac.prose_checks("bo_x", _entry(), _ctx(cols, ["signal_headline_text", "citation_human", "other_note"], vocab={"citation_human", "other_note"}))["Narr.agree"]
    assert two["v"] == PARTIAL and "other_note" in two["measured"]
    missing = ac.prose_checks("bo_x", _entry(), _ctx(["signal_headline_text"], ["signal_headline_text"]))["Narr.agree"]
    assert missing["v"] == FAIL


def test_the_real_four_assets_declare_the_exclusion_and_the_decline_table_equals_the_citation_decisions():
    import re
    decl = ac.load_asset_declarations()
    for a in ("bo_nakshatra_semantic", "bo_special_lagna", "bo_sudarshana", "bo_cgm_paths"):
        pe = decl[a]["prose_excluded"]
        assert [(x["column"], x["decision_id"]) for x in pe] == [("citation_human", "N-49")], a
        assert "citation_human" not in decl[a]["prose_fields"]
    src = (HERE / "test_e6_1_declarations.py").read_text(encoding="utf-8")
    table = json.loads(re.search(r'CITATION_DECISIONS = json.loads\(r"""(.*?)"""\)', src, re.S).group(1))
    declined = {(a, "citation_human") for a, d in table.items() if d["decision"] == "decline"}
    assert ac.load_prose_exclusion_decisions()["N-49"] == declined
    assert "N-49" in ac.load_decisions_register()


# ───────────────────────── (3) the closed-values LABEL form ─────────────────────────

LC = [dict(column="central_question_jsonb.$.linking_mechanism", values=["domain_tension", "cross_domain_contrast"],
           why="a graded one-word label chosen from the domain overlap of the two poles", evidence="platform/python-sidecar/pipeline/orchestrator/writers/bo_chart_gestalt.py:382")]


def test_an_undeclared_stored_value_fails_narr_agree():
    r = ac.grade_label_columns(LC, {LC[0]["column"]: ["domain_tension", "multi_ayanamsha_tested"]})
    assert r["v"] == FAIL and "multi_ayanamsha_tested" in r["measured"] and r["label_columns"]["undeclared"]


def test_a_declared_value_never_seen_is_allowed_and_reported():
    r = ac.grade_label_columns(LC, {LC[0]["column"]: ["domain_tension"]})
    assert r["v"] == PASS and "cross_domain_contrast" in r["measured"] and r["label_columns"]["declared_never_seen"]


def test_all_declared_values_seen_passes_without_a_note():
    r = ac.grade_label_columns(LC, {LC[0]["column"]: ["cross_domain_contrast", "domain_tension"]})
    assert r["v"] == PASS and "never seen" not in r["measured"]


def test_an_unread_vocabulary_is_partial_never_pass_and_too_many_values_are_not_closed():
    assert ac.grade_label_columns(LC, {LC[0]["column"]: None})["v"] == PARTIAL
    assert ac.grade_label_columns(LC, {})["v"] == PARTIAL
    many = [f"v{i}" for i in range(ac.MAX_LABEL_VALUES + 1)]
    assert ac.grade_label_columns(LC, {LC[0]["column"]: many})["v"] == PARTIAL


def test_an_empty_or_malformed_declared_vocabulary_is_refused():
    base = {"prose_fields": ["a"], "label_columns": copy.deepcopy(LC)}
    assert ac.label_columns_problem(base) is None
    for mut in (lambda d: d.update(values=[]), lambda d: d.update(values=["a", "a"]), lambda d: d.update(values=[" x"]), lambda d: d.update(values="x"),
                lambda d: d.update(evidence="platform/x.py"), lambda d: d.update(why="n/a"), lambda d: d.pop("why"), lambda d: d.update(column="1bad")):
        e = copy.deepcopy(base)
        mut(e["label_columns"][0])
        assert ac.label_columns_problem(e) is not None
    assert ac.label_columns_problem({"prose_fields": ["a"], "label_columns": []}) is not None
    assert ac.label_columns_problem({"prose_fields": [LC[0]["column"]], "label_columns": copy.deepcopy(LC)}) is not None      # a prose entry is not a label column


def test_the_distinct_values_query_is_read_only_and_path_aware():
    q = ac.label_distinct_sql("bodha_chart_gestalt", "central_question_jsonb.$.linking_mechanism")
    assert q.startswith("SELECT DISTINCT") and "#>> '{linking_mechanism}'" in q and "jsonb_typeof" in q and f"LIMIT {ac.MAX_LABEL_VALUES + 1}" in q
    assert not any(w in q.upper() for w in ("INSERT", "UPDATE", "DELETE", "DROP"))
    assert ac.label_distinct_sql("t", "label").startswith('SELECT DISTINCT "label"::text FROM t')
    with pytest.raises(ValueError):
        ac.label_distinct_sql("t; DROP TABLE x", "label")


def test_measure_reads_the_distinct_values_and_fails_the_asset_on_a_stray_label(monkeypatch):
    decl = {"prose_fields": ["doc"], "evidence": {"prose_fields": EVID}, "label_columns": copy.deepcopy(LC)}
    decl["label_columns"][0]["column"] = "doc2.$.linking_mechanism"
    r = dict(target_table="t", count_sql="SELECT count(*) FROM t WHERE chart_id = $1")
    cat = dict(exists={"t"}, cols={"t": ["chart_id", "doc", "doc2"]}, types={"t": {"chart_id": "text", "doc": "text", "doc2": "jsonb"}}, defaults={"t": {}})

    def run(values):
        monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: [[v] for v in values] if "DISTINCT" in sql else [["0", "0"]])
        return ac._measure_prose("a_x", decl, r, [], cat, [], set(), (), set())["Narr.agree"]
    assert run(["domain_tension"])["v"] != FAIL
    bad = run(["domain_tension", "old_literal"])
    assert bad["v"] == FAIL and "old_literal" in bad["measured"]
    # a failed read leaves the asset unread (never PASS)
    def boom(sql, *a, **k):
        raise ac.Unknown("db down")
    monkeypatch.setattr(ac, "psql", boom)
    assert ac._measure_prose("a_x", decl, r, [], cat, [], set(), (), set())["Narr.agree"]["v"] != PASS


# ───────────────────────── review round 3 (MED 2 / LOW): an exclusion is by table.column, never by bare name ─────────────────────────

def _two_table_ctx(vocab=None):
    own = {"t1": (["signal_headline_text", "citation_human"], {}, {}), "t2": (["citation_human", "x"], {}, {})}
    return dict(table="t1", own=own, tests=(), vocabulary=vocab if vocab is not None else {"citation_human"}, counts=None, paths=[],
                written={"t1": {"signal_headline_text", "citation_human"}, "t2": {"citation_human"}})


def test_an_exclusion_exempts_only_the_named_table_not_a_same_named_write_elsewhere(monkeypatch):
    monkeypatch.setattr(ac, "load_decisions_register", lambda path=None: REGISTER)
    monkeypatch.setattr(ac, "load_prose_exclusion_decisions", lambda path=None: DECLINES)
    ex, block, fail, unread = ac.checked_prose_exclusions("bo_x", _entry(), ac._own3(_two_table_ctx()), "t1", REGISTER, DECLINES)
    assert ex == {"t1.citation_human"} and fail is None
    out = ac.prose_checks("bo_x", _entry(), _two_table_ctx())["Narr.agree"]
    assert out["v"] == PARTIAL and "t2.citation_human" in out["measured"] and "t1.citation_human" not in out["measured"].split("(undeclared):")[1]
    # naming the second table instead exempts t2 and leaves t1's write undeclared
    e2 = _entry(prose_excluded=[dict(column="citation_human", decision_id="N-49", why=WHY, table="t2")])
    out2 = ac.prose_checks("bo_x", e2, _two_table_ctx())["Narr.agree"]
    assert out2["v"] == PARTIAL and "t1.citation_human" in out2["measured"]
    # both tables named: both exempt
    e3 = _entry(prose_excluded=[dict(column="citation_human", decision_id="N-49", why=WHY), dict(column="citation_human", decision_id="N-49", why=WHY, table="t2")])
    assert _problem(e3) is not None                                              # the column is listed twice: one entry per column
    assert ac.prose_checks("bo_x", _entry(), _two_table_ctx())["Narr.agree"]["v"] != PASS


def test_the_exclusion_table_must_be_an_owned_table_that_carries_the_column(monkeypatch):
    own = ac._own3(_two_table_ctx())
    bad_table = _entry(prose_excluded=[dict(column="citation_human", decision_id="N-49", why=WHY, table="t3")])
    ex, block, fail, unread = ac.checked_prose_exclusions("bo_x", bad_table, own, "t1", REGISTER, DECLINES)
    assert ex == set() and "not an owned table" in fail
    no_col = _entry(prose_excluded=[dict(column="citation_human", decision_id="N-49", why=WHY, table="t2")])
    own2 = dict(own, t2=(["x"], {}, {}))
    ex, block, fail, unread = ac.checked_prose_exclusions("bo_x", no_col, own2, "t1", REGISTER, DECLINES)
    assert "not a column of t2" in fail
    assert _problem(_entry(prose_excluded=[dict(column="citation_human", decision_id="N-49", why=WHY, table="1x")])) is not None


def test_the_decline_table_pin_to_the_citation_decisions_is_test_only():
    doc = json.loads(ac.PROSE_EXCLUSION_DECISIONS_PATH.read_text(encoding="utf-8"))
    assert "test-only" in doc["description"] and "no runtime" in doc["description"]


def test_blind_spot_an_empty_prose_asset_writing_a_prose_column_into_its_own_unshared_table_rests_on_prose_none():
    """With the per-asset vocabulary a `prose_fields: []` asset that writes a column some OTHER asset declares as prose, into its OWN table, is no longer a Narr.agree FAIL by name: the
    reverse leg does not reach it. Its Narr / Null cells then rest on the checked prose_none (a bare [] reads NO_DETECTOR at the rollup), which is what holds the line."""
    reg = {"owner": dict(target_table="t_owner", count_sql="SELECT count(*) FROM t_owner"), "empty": dict(target_table="t_empty", count_sql="SELECT count(*) FROM t_empty")}
    v = ac.prose_vocabulary({"owner": dict(prose_fields=["notes"]), "empty": dict(prose_fields=[])}, ac.declared_asset_tables(reg))
    entry = {"prose_fields": [], "evidence": {"prose_fields": EVID}}
    ctx = dict(table="t_empty", own={"t_empty": (["id", "notes"], {"id": "text", "notes": "text"}, {})}, tests=(), vocabulary=v, counts=None, paths=[], written={"t_empty": {"notes"}})
    rec = ac.prose_checks("empty", entry, ctx)
    assert rec["Narr.agree"]["v"] != FAIL                                     # no longer a name-based FAIL ...
    cells = ac.rollup_asset("L2", rec, {})
    assert cells["Narr"]["v"] == NO_DET and cells["Null"]["v"] == NO_DET       # ... and a bare [] never reads N/A: only a checked prose_none releases it
