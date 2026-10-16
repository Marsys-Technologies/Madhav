"""NB-01: synthetic reducer outcomes test U11, never unknown kartari agents."""
import pytest

from services.ka_muhurta_seva import parihara_eval as ev


def readings(citation, *, tika_verse=88, mula_verse=88, mula_result="applies"):
    return [
        dict(rule_id=202, extraction_context="tika_commentary",
             source_chunk_id="muhurta_chintamani_pg0116_c01", source_verse=tika_verse,
             source_citation=citation, result="does_not_apply", reason=None),
        dict(rule_id=204, extraction_context="mula_reconstructed",
             source_chunk_id="muhurta_chintamani_pg0115_c02", source_verse=mula_verse,
             source_citation=citation, result=mula_result, reason=None),
    ]


@pytest.mark.parametrize("citation", [
    "Muhūrta Cintāmaṇi v.88", "Muhūrta Cintāmaṇi vv.88",
    "Muhūrta Cintāmaṇi verse 88", "Muhūrta Cintāmaṇi, Vivāha (88)",
    "मुहूर्तचिन्तामणि विवाह ८८", "MC, Vivāha — cited source",
])
def test_v88_conflict_uses_explicit_locator_not_display_citation(citation):
    assert ev._dosha("kartari", readings(citation)) == {
        "dosha_canonical_id": "kartari", "by_rules": [202, 204],
        "state": "cancellation_unassessed", "reason": "readings_disagree",
    }


@pytest.mark.parametrize("tika_verse,mula_verse", [(89,88),(90,88),(91,88),(88,89),(89,89)])
def test_display_v88_and_shared_chunk_cannot_override_cross_verse_locators(tika_verse,mula_verse):
    out = ev._dosha("kartari", readings("Muhūrta Cintāmaṇi v.88",
                    tika_verse=tika_verse, mula_verse=mula_verse))
    assert (out["state"], out["reason"]) == ("cancelled", None)


@pytest.mark.parametrize("field,value", [
    ("source_chunk_id", "muhurta_chintamani_pg0116_c02"),
    ("extraction_context", "mula"),
])
def test_verse_88_still_requires_the_exact_source_reading_pair(field,value):
    rows = readings("Muhūrta Cintāmaṇi v.88")
    rows[0][field] = value
    out = ev._dosha("kartari", rows)
    assert (out["state"], out["reason"]) == ("cancelled", None)


def test_explicit_v88_unknown_reading_does_not_earn_agreement():
    rows = readings("Muhūrta Cintāmaṇi, Vivāha (88)")
    rows[0].update(result="unassessable", reason="dosha_agents_unknown")
    out = ev._dosha("kartari", rows)
    assert (out["state"], out["reason"]) == ("cancellation_unassessed", "dosha_agents_unknown")


@pytest.mark.parametrize("locator", [None, "88", True, 88.0, 0, -88, {"verse":88}])
def test_invalid_or_missing_verse_locator_cannot_earn_a_rule_verdict(sky,request_data,rule,locator):
    sky()
    row = rule({"planet":"Venus", "house_from_lagna":[6]}, source_verse=locator)
    if locator is None:
        row.pop("source_verse")
    out = ev.evaluate_candidate(**request_data, rules=[row])
    assert out["rules"][0]["result"] == "unassessable"
    assert out["rules"][0]["reason"] == "source_locator_invalid"
    assert (out["dosas"][0]["state"],out["dosas"][0]["reason"]) == (
        "cancellation_unassessed", "source_locator_invalid")


def test_display_citation_is_preserved_alongside_explicit_locator(sky,request_data,rule):
    sky()
    row = rule({"planet":"Venus", "house_from_lagna":[6]},
               source_citation="Muhūrta Cintāmaṇi, Vivāha (88)")
    out = ev.evaluate_candidate(**request_data, rules=[row])
    assert out["rules"][0]["source_verse"] == 88
    assert out["rules"][0]["source_citation"] == "Muhūrta Cintāmaṇi, Vivāha (88)"
    assert out["dosas"][0]["state"] == "cancelled"


def test_missing_locator_cannot_bypass_a_potential_reading_conflict(sky,request_data,rule):
    sky()
    rows = [rule(None, source_verse=None),
            rule({"planet":"Venus", "house_from_lagna":[6]}, id=204,
                 extraction_context="mula_reconstructed",
                 source_chunk_id="muhurta_chintamani_pg0115_c02")]
    out = ev.evaluate_candidate(**request_data, rules=rows)
    assert out["rules"][1]["result"] == "applies"
    assert (out["dosas"][0]["state"],out["dosas"][0]["reason"]) == (
        "cancellation_unassessed", "source_locator_invalid")
