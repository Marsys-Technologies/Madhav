"""Golden-value tests for the narration ga_vichara composes (prose batch 2, E5.7 Narr.fidelity_test).

ga_vichara stores two columns in its own table that carry composed sentences, and its daridra post-pass writes a third on the one chart_facts row it emits:
  * value_text on a varga_ratification_divergence row: "<GRAHA>: D1 <dignity> vs <varga> <dignity> — <domain> ratification fails in <varga>" (ga_vichara_writer.py, the f-string in
    build_varga_ratification_rows), which STATES the two computed dignities and grades the ratification as failed;
  * source_citation on a valence_pass row: the verdict citation of the shared valence doctrine (valence_doctrine.graha_valence), two fixed source phrases followed by the four signed
    components and the 4-way valence it computed.
Each test builds a fixture, calls the REAL builder, and asserts the string against an expected sentence stated here by hand (the components follow from the doctrine's published tables:
natural nature Jupiter +1.0 / Mars -1.0, functional yogakaraka +1.5 / functional_benefic +1.0 / functional_malefic -1.0 ..., dignity and lordship contact texture 0). Nothing is recomputed
from the writer's own formula.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_daridra_postpass as pp  # noqa: E402
from ga_writers import ga_vichara_writer as gv  # noqa: E402

NATURAL = "BPHS Ch.3 (graha svabhāva) — DR-9 natural-nature grounds."
FUNCTIONAL = "BPHS Ch.34 (functional benefic/malefic per lagna) — stored fact, §N.5."


def _link(fid, lord, src_h, tgt_h, kind="lord_placed", varga="D1"):
    return {"fact_id": fid, "fact_category": "bhava_significance_link", "fact_subject": f"{varga}_{lord}", "fact_key": f"{lord}_{src_h}_{tgt_h}", "fact_value_text": "kendra_link",
            "fact_value_num": None,
            "fact_value_jsonb": {"varga": varga, "link_kind": kind, "lord": lord, "source_house": src_h, "target_house": tgt_h, "link_type": "kendra_link"}}


def _functional(fid, subject, klass):
    return {"fact_id": fid, "fact_category": "graha_functional_class_per_ascendant", "fact_subject": subject, "fact_key": "bphs_canonical", "fact_value_text": klass,
            "fact_value_num": None, "fact_value_jsonb": None}


def _dignity(fid, varga, subject, dignity):
    return {"fact_id": fid, "fact_category": "graha_dignity_per_varga", "fact_subject": f"{varga}_{subject}", "fact_key": "dignity_state", "fact_value_text": dignity,
            "fact_value_num": None, "fact_value_jsonb": {"varga": varga, "sign": "Cancer", "house": 4}}


def test_varga_ratification_divergence_value_text_states_both_dignities_and_the_failed_domain():
    facts = [
        _link("l1", "Venus", 2, 2),                                        # Venus lords the 2nd house of D1: the wealth subject set is {Venus, Jupiter (karaka)}
        _dignity("d1jup", "D1", "JUP", "exalted"), _dignity("d9jup", "D9", "JUP", "debilitated"),                  # Jupiter: positive in D1, negative in D9 -> oppose
        _dignity("d1ven", "D1", "VEN", "own"), _dignity("d9ven", "D9", "VEN", "own"),                              # Venus agrees in D9: no divergence row
        _dignity("d1sat", "D1", "SAT", "debilitated"), _dignity("d10sat", "D10", "SAT", "own"),                    # Saturn (career karaka): negative in D1, positive in D10 -> oppose
    ]
    domains = {"wealth": {"vargas": ["D1", "D9"], "houses": [2], "karaka": "Jupiter", "provisional": False},
               "career": {"vargas": ["D1", "D10"], "houses": [10], "karaka": "Saturn", "provisional": True}}
    rows, _lookup = gv.build_varga_ratification_rows(gv.VicharaFactIndex(facts), domains, 0.2, 0.6, 1.4)
    assert [r["value_text"] for r in rows if r["vichara_family"] == "varga_ratification_divergence"] == [
        "JUPITER: D1 exalted vs D9 debilitated — wealth ratification fails in D9",
        "SATURN: D1 debilitated vs D10 own — career ratification fails in D10",
    ]


def _facts(lord, functional_class):
    return [_link("lk1", lord, 9, 2), _functional("fc1", gv.PLANET_TO_SUBJECT[lord], functional_class)]


def test_valence_pass_source_citation_states_the_four_signed_components_and_the_benefic_verdict():
    # Jupiter lording a house placed in the 2nd, stored functional class yogakaraka: natural +1.00, functional +1.50, no dignity, lordship has no contact texture: benefic, net clamped to 1.5
    rows = gv.build_valence_pass_rows(gv.VicharaFactIndex(_facts("Jupiter", "yogakaraka")), "D1", {})
    assert [(r["value_text"], r["source_citation"]) for r in rows] == [
        ("strong_benefic", "BPHS Ch.3 (graha svabhāva) — DR-9 natural-nature grounds. BPHS Ch.34 (functional benefic/malefic per lagna) — stored fact, §N.5. [natural=+1.00 functional=+1.50 dignity=+0.00 contact=+0.00 → benefic]")]


def test_valence_pass_source_citation_states_the_malefic_verdict_and_the_mixed_verdict():
    # Mars with a stored functional_malefic class: natural -1.00, functional -1.00: malefic, net clamped to -1.5
    malefic = gv.build_valence_pass_rows(gv.VicharaFactIndex(_facts("Mars", "functional_malefic")), "D1", {})
    assert [(r["value_text"], r["source_citation"]) for r in malefic] == [
        ("strong_malefic", "BPHS Ch.3 (graha svabhāva) — DR-9 natural-nature grounds. BPHS Ch.34 (functional benefic/malefic per lagna) — stored fact, §N.5. [natural=-1.00 functional=-1.00 dignity=+0.00 contact=+0.00 → malefic]")]
    # Jupiter with a stored functional_malefic class: natural +1.00 against functional -1.00, both sides reach the 0.4 threshold: mixed
    mixed = gv.build_valence_pass_rows(gv.VicharaFactIndex(_facts("Jupiter", "functional_malefic")), "D1", {})
    assert [(r["value_text"], r["source_citation"]) for r in mixed] == [
        ("mixed", "BPHS Ch.3 (graha svabhāva) — DR-9 natural-nature grounds. BPHS Ch.34 (functional benefic/malefic per lagna) — stored fact, §N.5. [natural=+1.00 functional=-1.00 dignity=+0.00 contact=+0.00 → mixed]")]


def _aspect_fact(fid, graha_subject, varga, target_house, offset):
    return {"fact_id": fid, "fact_category": "aspect_parashari_per_varga", "fact_subject": f"{varga}_{graha_subject}", "fact_key": f"house_{target_house}", "fact_value_text": None,
            "fact_value_num": 1.0, "fact_value_jsonb": {"varga": varga, "source_sign": "Aries", "source_house": 1, "target_house": target_house, "offset": offset, "ayanamsha_id": "lahiri_chitrapaksha"}}


def test_aspect_sourced_valence_pass_source_citation_states_the_harsh_aspect_contact_texture():
    # Mars (stored functional_malefic) aspecting the 2nd house with its harsh 4th aspect: natural -1.00, functional -1.00, no dignity; the harsh special aspect is -0.40 and onto a supportive house -0.20 more
    facts = [_aspect_fact("a1", "MAR", "D1", 2, 4), _functional("fc1", "MAR", "functional_malefic")]
    rows = gv.build_aspect_valence_rows(gv.VicharaFactIndex(facts), "D1", {})
    assert [(r["value_text"], r["source_citation"]) for r in rows] == [
        ("strong_malefic", "BPHS Ch.3 (graha svabhāva) — DR-9 natural-nature grounds. BPHS Ch.34 (functional benefic/malefic per lagna) — stored fact, §N.5. [natural=-1.00 functional=-1.00 dignity=+0.00 contact=-0.60 → malefic]")]


# ── the daridra dosha_label row ga_vichara's post-pass writes into chart_facts (ga_daridra_postpass; the row's citation_human is composed by ga_structural_writer._build_dosha_rows) ──
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AY_ID = "lahiri_chitrapaksha"
# 11th lord (Venus, Cancer lagna) in H8 dusthana: daridra forms (the fixture of tests/test_ga_daridra_postpass.py)
DARIDRA_CHART = {
    "ascendant": {"sign": "Cancer", "sign_id": 4, "longitude": 100.0},
    "grahas": [
        {"name": "Venus", "sign": "Sagittarius", "sign_id": 9, "house": 8, "longitude": 250.0, "retrograde": False},
        {"name": "Sun", "sign": "Aries", "sign_id": 1, "house": 10, "longitude": 10.0, "retrograde": False},
        {"name": "Moon", "sign": "Cancer", "sign_id": 4, "house": 1, "longitude": 100.0, "retrograde": False},
        {"name": "Mars", "sign": "Capricorn", "sign_id": 10, "house": 7, "longitude": 280.0, "retrograde": False},
        {"name": "Mercury", "sign": "Pisces", "sign_id": 12, "house": 9, "longitude": 340.0, "retrograde": False},
        {"name": "Jupiter", "sign": "Libra", "sign_id": 7, "house": 4, "longitude": 190.0, "retrograde": False},
        {"name": "Saturn", "sign": "Aquarius", "sign_id": 11, "house": 8, "longitude": 310.0, "retrograde": False},
        {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 11, "longitude": 48.0, "retrograde": True},
        {"name": "Ketu", "sign": "Scorpio", "sign_id": 8, "house": 5, "longitude": 228.0, "retrograde": True},
    ],
}
DARIDRA_ENTRY = {"canonical_id": "daridra", "name_en": "Daridra", "formation_rule_jsonb": {"requires": "11th lord in dusthana or 2nd/11th lords afflicted"},
                 "classical_citations": {}, "source_chunk_ids": [], "category": "dosha"}


class _CannedCursor:
    """A cursor stand-in driven by the table the executed SQL names: the wealth varga_ratification row of chart_vichara and the fired ga_yoga_firings rows are injected per test."""

    def __init__(self, vichara_row, yoga_rows):
        self._q, self._vichara_row, self._yoga_rows = "", vichara_row, yoga_rows

    def execute(self, query, params=None):
        self._q = query

    def fetchone(self):
        return self._vichara_row if "chart_vichara" in self._q else None

    def fetchall(self):
        return self._yoga_rows if "ga_yoga_firings" in self._q else []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _CannedConn:
    def __init__(self, vichara_row=None, yoga_rows=None):
        self._vichara_row, self._yoga_rows = vichara_row, yoga_rows or []

    def cursor(self, row_factory=None):
        return _CannedCursor(self._vichara_row, self._yoga_rows)


def test_daridra_label_citation_human_states_the_chart_the_label_and_a_standing_verdict():
    rows = pp.build_daridra_label_rows(_CannedConn(), CHART_ID, "test-build-001", AY_ID, chart_output=DARIDRA_CHART, dosha_catalog=[DARIDRA_ENTRY])
    assert [r["citation_human"] for r in rows] == ["Dosha Daridra (daridra) labels chart 482012f1 (lahiri_chitrapaksha): bespoke_detector:daridra."]


def test_daridra_label_citation_human_states_the_cancelling_ground_when_one_holds():
    dhana = pp.build_daridra_label_rows(_CannedConn(yoga_rows=[("dhana_yoga_house_lords", '["sun", "mercury", "venus"]')]), CHART_ID, "test-build-001", AY_ID,
                                        chart_output=DARIDRA_CHART, dosha_catalog=[DARIDRA_ENTRY])
    assert [r["citation_human"] for r in dhana] == [
        "Dosha Daridra (daridra) labels chart 482012f1 (lahiri_chitrapaksha): bespoke_detector:daridra. CANCELLED: brahma_dosha_catalog daridra cancellation_conditions "
        "('dhana/raja yoga present'): dhana_structure_fires:dhana_yoga_house_lords — Daridra does not serve as a finding."]
    exalted = pp.build_daridra_label_rows(_CannedConn(vichara_row=(1.4, {"d1_dignity": "exalted"})), CHART_ID, "test-build-001", AY_ID,
                                          chart_output=DARIDRA_CHART, dosha_catalog=[DARIDRA_ENTRY])
    assert [r["citation_human"] for r in exalted] == [
        "Dosha Daridra (daridra) labels chart 482012f1 (lahiri_chitrapaksha): bespoke_detector:daridra. CANCELLED: brahma_dosha_catalog daridra cancellation_conditions "
        "('dhana/raja yoga present'): 11L_Venus_exalted_per_ga_vichara_varga_ratification — Daridra does not serve as a finding."]
