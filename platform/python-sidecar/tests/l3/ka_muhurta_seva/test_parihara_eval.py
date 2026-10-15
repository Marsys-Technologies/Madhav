"""U1:19–27 and U11:36: source, frame, scope and unknowns are observable."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from services.ka_muhurta_seva import parihara_eval as ev

FIXTURES = Path(__file__).with_name("parihara_predicates.json")
CORPUS = Path(__file__).resolve().parents[4] / "scripts/corpus/data/muhurta_chintamani_translations.json"


def run(req, rules):
    return ev.evaluate_candidate(**req, rules=rules)


def test_source_fixtures_resolve_verbatim_not_from_memory():
    corpus = {r["chunk_id"]: r for r in json.loads(CORPUS.read_text())}
    fixtures = json.loads(FIXTURES.read_text())
    assert len(fixtures) >= 5
    for r in fixtures:
        source = corpus[r["source_chunk_id"]]
        assert source["action"] == "translated"
        assert source["priority_topic"] == "parihara"
        assert r["cancellation_condition_text"] in source["content_en"]
        assert r["source_citation"]


def test_marriage_cited_cancellation_and_exact_metadata(sky, request_data, rule):
    calls = sky()
    r = rule({"op": "all_of", "terms": [{"planet": "Venus", "house_from_lagna": [6]},
                {"planet": "Venus", "dignity": "debilitated", "varga": "rasi"}]}, priority_rank="two_hundred", tika_extension=True)
    out = run(request_data, [r])
    assert out["dosas"] == [{"dosha_canonical_id": "venus_sixth", "state": "cancelled", "by_rules": [101], "reason": None}]
    row = out["rules"][0]
    for key in ("scope", "source_citation", "source_chunk_id", "source_verse", "conjunction_reading", "tika_extension", "priority_rank", "net_standing"):
        assert row[key] == r[key]
    assert row["rule_id"] == 101 and row["result"] == "applies"
    assert len(calls) == 3 and calls[1] == (calls[0]+calls[2])/2
    assert out["ayanamsha"] == "lahiri" and out["house_system"] == "whole_sign_from_rising_sign"
    assert out["sky_coverage"]["complete"] and out["sky_coverage"]["basis"] == "start_mid_end_samples"
    assert row["terms"][0]["observed"][0]["value"] is True
    fact = row["terms"][0]["facts"][0]
    assert fact["positions"]["Venus"]["longitude_deg"] == 160.
    assert fact["lagna"]["longitude_deg"] == 0.
    assert fact["ephemeris"]["backend"] == "swieph" and fact["jd"] == calls[0]


@pytest.mark.parametrize("undertaking,scope", [("marriage","marriage"),("upanayana","upanayana"),
    ("business","general"),("education","general"),("spiritual_initiation","general"),("anything_else","general")])
def test_exact_scope_map_no_natal_or_muhurta_fallback(sky, request_data, rule, undertaking, scope):
    sky()
    request_data["undertaking"] = undertaking
    rows = [rule({"planet": "Venus", "house_from_lagna": [6]}, id=i, scope=s) for i,s in enumerate(["natal","muhurta","marriage","upanayana","general"], 1)]
    out = run(request_data, rows)
    assert {r["scope"] for r in out["rules"]} == {"general", scope}
    assert all(r["scope"] not in ("natal","muhurta") for r in out["rules"])


def test_business_excludes_marriage_only_rule(sky, request_data, rule):
    sky(); request_data["undertaking"] = "business"
    out = run(request_data, [rule({"planet":"Venus", "house_from_lagna":[6]})])
    assert out["rules"] == []
    assert out["dosas"][0]["state"] == "cancellation_unassessed"
    assert out["dosas"][0]["reason"] == "no_sourced_rule_in_scope"


@pytest.mark.parametrize("predicate,expected", [
    ({"op":"all_of","terms":[{"planet":"Mars","house_from_lagna":[4]}, {"planet":"Mars","house_from_lagna":[8]}]}, "does_not_apply"),
    ({"op":"any_of","terms":[{"planet":"Mars","house_from_lagna":[4]}, {"planet":"Mars","house_from_lagna":[8]}]}, "applies"),
    ({"planet":"Mars","house_from_lagna":[4]}, "applies"),
    ({"clause":"sarva_dosha", "planet":"Jupiter","house_from_lagna":[5]}, "applies"),
])
def test_recursive_grammar(sky, request_data, rule, predicate, expected):
    sky()
    assert run(request_data, [rule(predicate)])["rules"][0]["result"] == expected


@pytest.mark.parametrize("p,reason", [(None,"predicate_not_encoded"), ({},"predicate_not_encoded"),
    ({"op":"all_of","terms":[]},"predicate_not_encoded"),
    ({"planet":"Rahu","house_from_lagna":[1]},"predicate_not_encoded"),
    ({"planet":"Sun","strength":"strong"},"strength_undefined"),
    ({"role":"dosha_agents","each_any_of":["enemy_sign","debilitated","combust"]},"dosha_agents_unknown"),
    ({"planet":"Venus","dignity":"combust","varga":"navamsa"},"predicate_not_encoded"),
    ({"planet":"Venus","house_from_lagna":[6],"invented":True},"predicate_not_encoded"),
    ({"planet":"Venus","house_from_lagna":[True]},"predicate_not_encoded"),
    ({"op":"any_of","terms":[{"planet":"Venus","house_from_lagna":[6]}, {"planet":"Sun","strength":"strong"}]},"strength_undefined"),
])
def test_unknowns_never_cancel_or_earn_residual(sky, request_data, rule, p, reason):
    sky()
    out = run(request_data, [rule(p)])
    assert out["rules"][0]["result"] == "unassessable"
    assert out["dosas"][0]["state"] == "cancellation_unassessed"
    assert out["dosas"][0]["reason"] == reason


@pytest.mark.parametrize("seq", [[100.,220.,100.],[100.,100.,220.]])
def test_three_sample_term_changes_do_not_clear_even_when_any_of_stays_true(sky, request_data, rule, seq):
    sky(sequences={"Mars":seq})
    p={"op":"any_of","terms":[{"planet":"Venus","house_from_lagna":[6]}, {"planet":"Mars","house_from_lagna":[4]}]}
    out=run(request_data,[rule(p)])
    assert out["dosas"][0]["reason"] == "predicate_changes_within_candidate"
    assert [v["value"] for v in out["rules"][0]["terms"][1]["observed"]] == [v==100. for v in seq]


@pytest.mark.parametrize("p,lagna,positions,expected", [
    ({"planet":"Sun","house_from_lagna":[2]},330.,{"Sun":0.}, True),
    ({"planet":"Moon","vargottama":True},0.,{"Moon":1.}, True),
    ({"planet":"Moon","vargottama":True},0.,{"Moon":4.}, False),
    ({"planet":"Moon","dignity":"debilitated","varga":"navamsa"},0.,{"Moon":24.}, True),
    ({"planet":"Moon","dignity":"debilitated","varga":"navamsa"},0.,{"Moon":23.}, False),
    ({"role":"lagna_lord","house_from_lagna":[4]},0.,{"Mars":100.}, True),
    ({"role":"navamsa_lagna_lord","house_from_lagna":[2]},4.,{"Venus":40.}, True),
    ({"planet":"Sun","dignity":"enemy_sign","varga":"rasi"},0.,{"Sun":280.}, True),
])
def test_independent_frame_goldens(sky, request_data, rule, p, lagna, positions, expected):
    sky(lagna=lagna, longitudes=positions)
    row=run(request_data,[rule(p)])["rules"][0]
    assert row["result"] == ("applies" if expected else "does_not_apply")


@pytest.mark.parametrize("planet,sun,lon,speed,expected", [
    ("Mercury",0.,14.,1.,True),("Mercury",0.,14.001,1.,False),
    ("Mercury",0.,12.,-1.,True),("Mercury",0.,12.001,-1.,False),
    ("Mars",0.,16.,-1.,False),("Mars",0.,16.,1.,True),
    ("Venus",359.,1.,1.,True),("Sun",0.,0.,1.,False),
])
def test_combustion_reads_l0_orbs_and_short_arc(sky, request_data, rule, planet, sun, lon, speed, expected):
    sky(longitudes={planet:lon,"Sun":sun}, speeds={planet:speed})
    out=run(request_data,[rule({"planet":planet,"dignity":"combust","varga":"rasi"})])
    assert out["rules"][0]["result"] == ("applies" if expected else "does_not_apply")


@pytest.mark.parametrize("damage", ["missing_body","empty","wrong_backend","wrong_jd","wrong_convention","nan"])
def test_coverage_requires_real_backend_body_and_each_instant(sky, request_data, rule, damage):
    def alter(result, i):
        if i!=1: return result
        a=result.values[0]
        if damage=="empty": return replace(result,values=())
        if damage=="missing_body": a=replace(a,positions=a.positions[:-1])
        if damage=="wrong_backend": a=replace(a,backend="moshier")
        if damage=="wrong_jd": a=replace(a,jd=a.jd+1)
        if damage=="wrong_convention": a=replace(a,ayanamsha_id="raman")
        if damage=="nan": a=replace(a,positions=(replace(a.positions[0],longitude_deg=float("nan")),)+a.positions[1:])
        return replace(result,values=(a,))
    sky(alter=alter)
    out=run(request_data,[rule({"planet":"Venus","house_from_lagna":[6]})])
    assert not out["sky_coverage"]["complete"]
    assert out["dosas"][0]["reason"] == "sky_coverage_gap"


def test_v88_disagreement_retains_both_citations_and_blocks_unrelated_cancellation(sky,request_data,rule,monkeypatch):
    """Reducer control with synthetic per-rule results, not invented v.88 predicates.

    Real kartari agent/intervening-benefic conditions remain unknown. This tests
    the U11 conflict policy independently of that deliberately absent detector.
    """
    sky()
    fixtures=json.loads(FIXTURES.read_text())
    rows=[r for r in fixtures if r["dosha_canonical_id"]=="kartari"]
    request_data["dosas_present"]=["kartari"]
    rows.append(rule(None, id=999, dosha_canonical_id="kartari", source_chunk_id="muhurta_chintamani_pg0116_c02", extraction_context="mula"))
    original=ev._rule
    def synthetic_result(row,samples):
        result=original(row,samples)
        result.update(result="does_not_apply" if row["id"]==202 else "applies",reason=None)
        return result
    monkeypatch.setattr(ev,"_rule",synthetic_result)
    out=run(request_data,rows)
    assert out["dosas"][0] == {"dosha_canonical_id":"kartari","state":"cancellation_unassessed","reason":"readings_disagree","by_rules":[r["id"] for r in rows]}
    assert len({r["source_chunk_id"] for r in out["rules"]})==3


@pytest.mark.parametrize("states,expected,reason", [
    ([True],"cancelled",None),([False],"residual",None),
    ([False,None],"cancellation_unassessed","predicate_not_encoded"),
    ([],"cancellation_unassessed","no_sourced_rule_in_scope"),
])
def test_state_reduction(sky,request_data,rule,states,expected,reason):
    sky()
    rows=[rule(None if s is None else {"planet":"Venus","house_from_lagna":[6 if s else 1]},id=i) for i,s in enumerate(states)]
    d=run(request_data,rows)["dosas"][0]
    assert (d["state"],d["reason"])==(expected,reason)


def test_never_cancelled_overrides_applies(sky,request_data,rule):
    sky()
    out=run(request_data,[rule({"planet":"Venus","house_from_lagna":[6]}),rule(None,id=102,net_standing="never_cancelled")])
    assert out["dosas"][0]["state"]=="residual"
    assert out["dosas"][0]["reason"]=="never_cancelled_by_text"


def test_source_pair_unknown_is_not_treated_as_agreement(sky,request_data,rule):
    sky()
    rows=[rule({"planet":"Venus","house_from_lagna":[6]}),rule(None,id=102,extraction_context="mula_reconstructed",source_chunk_id="muhurta_chintamani_pg0115_c02")]
    assert run(request_data,rows)["dosas"][0]["state"]=="cancellation_unassessed"


def test_unsourced_never_cancelled_cannot_earn_a_verdict(sky,request_data,rule):
    sky()
    out=run(request_data,[rule(None,net_standing="never_cancelled",source_citation=None,source_chunk_id=None)])
    assert out["dosas"][0]["state"]=="cancellation_unassessed"
    assert out["rules"][0]["reason"]=="predicate_not_encoded"


def test_real_swiss_facts_roundtrip_without_recomputing_source_values(request_data,rule):
    import os
    from services.kala_core.sky.ephemeris import ephemeris_at, lagna_at, GeoLocation, CivilTime, SkyConvention
    from services.gochara_kernel.substrate import JD_UNIX_EPOCH
    out=run(request_data,[rule({"planet":"Venus","house_from_lagna":[6]})])
    # With no corpus this remains an honest gap; CI always supplies the pinned corpus.
    if not out["sky_coverage"]["complete"]:
        assert out["dosas"][0]["reason"]=="sky_coverage_gap"
        assert not os.environ.get("KALA_REQUIRE_DB")=="1", "required CI ephemeris did not answer all samples"
        return
    facts=out["rules"][0]["terms"][0]["facts"]
    for t,fact in zip(ev.candidate_times(request_data["candidate"]),facts):
        jd=t.timestamp()/86400.+JD_UNIX_EPOCH
        source=ephemeris_at(jd,SkyConvention(),bodies=ev.PLANETS).values[0]
        rising=lagna_at(jd,GeoLocation(20.27,85.84),CivilTime("UTC",330)).values[0]
        assert fact["positions"]["Venus"]["longitude_deg"]==source.position("Venus").longitude_deg
        assert fact["lagna"]["longitude_deg"]==rising.longitude_deg
        house=1+(int(source.position("Venus").longitude_deg/30)-int(rising.longitude_deg/30))%12
        assert fact["derived"]["house_from_lagna"]==house


def test_missing_ephemeris_files_never_fall_back_to_moshier(monkeypatch,tmp_path,request_data,rule):
    import os
    import swisseph as swe
    original=ev.ephemeris_at
    old_path=os.environ.get("SE_EPHE_PATH", "")
    try:
        # Swiss gives SE_EPHE_PATH precedence over set_ephe_path's argument.
        with monkeypatch.context() as patch:
            patch.setenv("SE_EPHE_PATH",str(tmp_path))
            patch.setattr(ev,"ephemeris_at",lambda *args,**kwargs:original(*args,ephe_path=str(tmp_path),**kwargs))
            out=run(request_data,[rule({"planet":"Venus","house_from_lagna":[6]})])
        assert not out["sky_coverage"]["complete"]
        assert out["dosas"][0]["reason"]=="sky_coverage_gap"
    finally:
        swe.set_ephe_path(old_path)


def test_other_verses_in_the_same_chunk_do_not_count_as_v88_readings(sky,request_data,rule,monkeypatch):
    """The pg0116_c01 chunk also contains vv.89–91: its id is not a verse id."""
    sky()
    rows=[
        rule(None,id=301),
        rule(None,id=302,extraction_context="mula_reconstructed",source_chunk_id="muhurta_chintamani_pg0115_c02"),
        rule(None,id=303,source_verse=90,source_citation="Muhūrta Cintāmaṇi v.90"),
    ]
    original=ev._rule
    def synthetic_result(row,samples):
        out=original(row,samples)
        out.update(result="applies" if row["id"]==303 else "does_not_apply",reason=None)
        return out
    monkeypatch.setattr(ev,"_rule",synthetic_result)
    out=run(request_data,rows)
    assert out["dosas"][0]["state"]=="cancelled"
    assert out["dosas"][0]["reason"] is None
