"""test_wfixb_declarations.py: WFIX-B (Exec Suvarna, census 5124c348a): the declarations that closed three of the five newly exposed Narr.agree FAILs.

  * bg_muhurta_lattice (`detail`, 496 rows): the rows an EARLIER version of the same writer left in place (rolling horizon: the past is never rewritten) carry two older words the current writer no longer
    builds: the long `strength_verdict_note` of the lagna family (430 rows) and the `..._anga_at_sunrise` span convention of the tithi and nakshatra families (33 + 33 rows). Both are declared as the
    closed words they are; the CURRENT writer's words are unchanged and no row changes on a rebuild.
  * ga_dashas and ga_sensitive_degree: both write `chart_facts.citation_human`, a column the L1 assets that own chart_facts declare as narration, so the reverse leg of Narr.agree read FAIL although SS had
    already decided (N-49, prose_exclusion_decisions.json) that these two assets' citation_human is a fixed provenance string, not narration. The decision is now carried by a `prose_excluded` entry, the form
    ga_ayurdaya uses.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

DECLS = ac.load_asset_declarations()
FAIL, NA, NO_DET = ac.FAIL, ac.NA, ac.NO_DET

LEGACY_NOTE = ("Deliberately null (§N.5). Dignity is resolved at query time against bg_dignity_reference (exaltation/debilitation/moolatrikona/own_signs, BPHS-cited) and dṛṣṭi against BPHS Ch.26; "
               "a verdict stored here would be a second copy of those authorities and could drift from them.")
CURRENT_NOTE = "Deliberately null (§N.5). Resolve dignity at query time against bg_dignity_reference and dṛṣṭi against BPHS Ch.26."
LEGACY_CONV = "hindu_day_sunrise_to_next_sunrise_anga_at_sunrise"


# ───────────────────────────── bg_muhurta_lattice ─────────────────────────────

def _detail():
    return next(c for c in DECLS["bg_muhurta_lattice"]["prose_none"]["closed_columns"] if c["column"] == "detail")


def _pat(path):
    return next(p for p in _detail()["json_leaf_patterns"] if p["path"] == path)


def test_muhurta_the_current_writer_words_are_unchanged_and_the_two_legacy_words_are_added():
    assert ac.prose_none_problem(DECLS["bg_muhurta_lattice"]) is None
    import hashlib
    assert _pat("$.strength_verdict_note") == {"path": "$.strength_verdict_note", "sha256": sorted(hashlib.sha256(n.encode("utf-8")).hexdigest() for n in (CURRENT_NOTE, LEGACY_NOTE))}   # the legacy sentence is 283 characters: pinned by digest
    assert _pat("$.span_convention")["values"] == ["hindu_day_sunrise_to_next_sunrise", "true_anga_interval_clipped_to_hindu_day", LEGACY_CONV]


def test_muhurta_the_current_writer_source_still_builds_only_the_current_words():
    """The legacy words are NOT in the writer: they are the footprint of an earlier version (git e81fc2958 / f19969c5b), kept in place by the rolling horizon."""
    src = (fs.REPO / "platform/python-sidecar/pipeline/orchestrator/writers/bg_muhurta_lattice.py").read_text(encoding="utf-8")
    assert "Dignity is resolved at query time" not in src and "anga_at_sunrise" not in src
    assert "Resolve dignity at query time" in src and "true_anga_interval_clipped_to_hindu_day" in src


def _table(pg, monkeypatch, rows):
    point_psql_at(pg, monkeypatch)
    ac.psql("DROP TABLE IF EXISTS wfixb_lattice")
    ac.psql("CREATE TABLE wfixb_lattice (id serial PRIMARY KEY, detail jsonb)")
    for r in rows:
        ac.psql("INSERT INTO wfixb_lattice (detail) VALUES ('" + json.dumps(r, ensure_ascii=False).replace("'", "''") + "'::jsonb)")


def _violations(entry=None):
    return int(ac.scalar(ac.prose_none_outside_sql("wfixb_lattice", "detail", "json", entry or _detail(), None)))


def test_muhurta_REAL_SQL_the_legacy_rows_are_inside_the_closure_and_a_third_variant_is_not(monkeypatch, disposable_pg):
    rows = [
        {"sign_id": 9, "sign_name": "Dhanu", "lord": "Jupiter", "graha_positions_at": "2026-08-01T23:51:55+00:00", "strength_verdict": None, "strength_verdict_note": LEGACY_NOTE},
        {"sign_id": 9, "sign_name": "Dhanu", "lord": "Jupiter", "graha_positions_at": "2026-09-30T23:51:55+00:00", "strength_verdict": None, "strength_verdict_note": CURRENT_NOTE},
        {"name": "Anuradha", "anga_true_end_utc": "2026-08-02T16:07:20+00:00", "span_convention": LEGACY_CONV},
        {"name": "Shukla Tritiya", "paksha": "shukla", "anga_true_end_utc": "2026-08-02T17:45:49+00:00", "span_convention": LEGACY_CONV},
        {"name": "Shukla Tritiya", "paksha": "shukla", "anga_true_end_utc": "2026-10-02T17:45:49+00:00", "span_convention": "true_anga_interval_clipped_to_hindu_day"},
    ]
    _table(disposable_pg, monkeypatch, rows)
    try:
        assert _violations() == 0
        old = json.loads(json.dumps(_detail()))
        old["json_leaf_patterns"] = [p for p in old["json_leaf_patterns"]]
        for p in old["json_leaf_patterns"]:
            if p["path"] == "$.strength_verdict_note":
                p.pop("sha256")
                p["values"] = [CURRENT_NOTE]
            if p["path"] == "$.span_convention":
                p["values"] = [v for v in p["values"] if v != LEGACY_CONV]
        assert _violations(old) == 3                                                    # the declaration before WFIX-B: exactly the legacy rows are outside it
        ac.psql("INSERT INTO wfixb_lattice (detail) VALUES ('{\"strength_verdict_note\": \"Deliberately null. A reworded note nobody declared.\"}'::jsonb)")
        assert _violations() == 1
        ac.psql("DELETE FROM wfixb_lattice WHERE detail->>'strength_verdict_note' LIKE '%reworded%'")
        ac.psql("INSERT INTO wfixb_lattice (detail) VALUES ('{\"span_convention\": \"anga_at_sunrise\"}'::jsonb)")
        assert _violations() == 1
    finally:
        ac.psql("DROP TABLE IF EXISTS wfixb_lattice")


# ───────────────────────────── ga_dashas / ga_sensitive_degree ─────────────────────────────

CASES = {
    "ga_dashas": dict(target="chart_dashas", own={"chart_dashas": (["chart_id", "lord_graha", "citation_human"], {"chart_id": "uuid", "lord_graha": "text", "citation_human": "text"}),
                                                  "chart_facts": (["chart_id", "fact_key", "citation_human"], {"chart_id": "uuid", "fact_key": "text", "citation_human": "text"})},
                      written={"chart_dashas": {"lord_graha", "citation_human"}, "chart_facts": {"fact_key", "citation_human"}}),
    "ga_sensitive_degree": dict(target="chart_facts", own={"chart_facts": (["chart_id", "fact_key", "citation_human"], {"chart_id": "uuid", "fact_key": "text", "citation_human": "text"})},
                                written={"chart_facts": {"fact_key", "citation_human"}}),
}


def _ctx(aid):
    c = CASES[aid]
    vocab = ac.prose_vocabulary({a: {"prose_fields": ["citation_human"]} for a in ("ga_positions", "ga_structural")}, {"ga_positions": {"chart_facts"}, "ga_structural": {"chart_facts"}})
    return dict(table=c["target"], columns=c["own"][c["target"]][0], types=c["own"][c["target"]][1], own=dict(c["own"]), written=dict(c["written"]), vocabulary=vocab)


@pytest.mark.parametrize("aid", sorted(CASES))
def test_the_citation_human_decline_is_declared_through_prose_excluded_for_chart_facts(aid):
    e = DECLS[aid]
    assert e["prose_fields"] == [] and ac.prose_excluded_problem(aid, e) is None
    assert [(d.get("table"), d["column"], d["decision_id"]) for d in e["prose_excluded"]] == [("chart_facts", "citation_human", "N-49")]
    assert (aid, "citation_human") in ac.load_prose_exclusion_decisions()["N-49"]                      # SS decided it already (N-49): this carries the decision, it does not make one


@pytest.mark.parametrize("aid", sorted(CASES))
def test_the_reverse_leg_no_longer_fires_on_chart_facts_citation_human(aid):
    got = ac.prose_checks(aid, DECLS[aid], _ctx(aid))
    assert "treat as narration" not in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:300]


@pytest.mark.parametrize("aid", sorted(CASES))
def test_without_the_exclusion_the_reverse_leg_reads_exactly_the_census_fail(aid):
    d = json.loads(json.dumps(DECLS[aid]))
    d.pop("prose_excluded")
    got = ac.prose_checks(aid, d, _ctx(aid))
    assert got["Narr.agree"]["v"] == FAIL and got["Narr.agree"]["measured"] == (
        "prose_fields is [] but the writer writes column(s) the declarations treat as narration: chart_facts.citation_human")


@pytest.mark.parametrize("aid", sorted(CASES))
def test_the_exclusion_is_one_column_of_one_table_it_hides_no_other_narration_write(aid):
    c = CASES[aid]
    ctx = _ctx(aid)
    ctx["own"]["chart_facts"] = (["chart_id", "fact_key", "citation_human", "signal_summary_text"], dict(ctx["own"]["chart_facts"][1], signal_summary_text="text"))
    ctx["written"]["chart_facts"] = set(c["written"]["chart_facts"]) | {"signal_summary_text"}
    ctx["vocabulary"] = ac.prose_vocabulary({"ga_positions": {"prose_fields": ["citation_human", "signal_summary_text"]}}, {"ga_positions": {"chart_facts"}})
    got = ac.prose_checks(aid, DECLS[aid], ctx)
    assert got["Narr.agree"]["v"] == FAIL and "chart_facts.signal_summary_text" in got["Narr.agree"]["measured"] and "citation_human" not in got["Narr.agree"]["measured"].split("narration:")[1]
    if aid == "ga_dashas":                                                                                 # the exclusion is the chart_facts one: the same column name on chart_dashas stays judged
        ctx2 = _ctx(aid)
        ctx2["vocabulary"] = ac.prose_vocabulary({"x": {"prose_fields": ["citation_human"]}}, {"x": {"chart_dashas"}})
        got2 = ac.prose_checks(aid, DECLS[aid], ctx2)
        assert got2["Narr.agree"]["v"] == FAIL and "chart_dashas.citation_human" in got2["Narr.agree"]["measured"]


def test_ga_dashas_chart_facts_citation_human_is_the_one_literal_sentinel_sentence():
    """The N-49 rule (a composed string is narration if it states or grades a computed value), re-derived from the writer source: the ONLY chart_facts row ga_dashas writes is the scope-cap sentinel,
    and its citation_human is two adjacent string literals (one constant), nothing composed."""
    import ast
    tree = ast.parse((fs.REPO / "platform/python-sidecar/ga_writers/ga_dashas_writer.py").read_text(encoding="utf-8"))
    ins = [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and "INSERT INTO chart_facts" in n.value]
    assert len(ins) == 1                                                                                   # one chart_facts INSERT in the whole writer
    lits = [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("Prana Dasha fifth-level")]
    assert len(lits) == 1 and lits[0].value == "Prana Dasha fifth-level sub-period is explicitly not computed; the admitted L1 interval hierarchy ends at level 4."


def test_ga_sensitive_degree_every_chart_facts_citation_is_a_module_constant_of_one_string_literal():
    import ast
    tree = ast.parse((fs.REPO / "platform/python-sidecar/ga_writers/ga_sensitive_degree_writer.py").read_text(encoding="utf-8"))
    consts = {t.id: n.value for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_row"]
    assert len(calls) >= 18
    names = set()
    for c in calls:
        cite = c.args[8]                                                                                   # _row(chart_id, aya, build_id, subject, key, num, text, jsonb, citation, ...)
        if isinstance(cite, ast.Constant):                                                                 # a literal at the call site (the Sarvatobhadra row)
            assert isinstance(cite.value, str)
            continue
        assert isinstance(cite, ast.Name) and cite.id.endswith("_CITATION"), ast.dump(cite)[:80]
        names.add(cite.id)
    for nm in names:
        v = consts.get(nm)
        assert v is None or (isinstance(v, ast.Constant) and isinstance(v.value, str)), nm                  # None = imported from the classical-rule module (GANDANTA_CITATION), a constant there
