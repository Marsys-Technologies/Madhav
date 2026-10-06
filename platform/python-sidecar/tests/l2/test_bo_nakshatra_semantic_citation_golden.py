"""Golden-value narration fidelity test for bo_nakshatra_semantic.citation_human (nakshatra_semantic_emitter).

The emitter states the row's own graha in a fixed template, 'Nakshatra-semantic profile: <Graha>', with the graha shown by its title-case name
(code MOON is the Moon). The expected sentence is stated by hand from that rule, not read from the builder.
"""
from __future__ import annotations

from bodha_writers.nakshatra_semantic_emitter import build_signal_row


def test_nakshatra_semantic_citation_human_names_the_graha():
    position_facts = {
        "nakshatra": {"text": "Purva Bhadrapada", "fact_id": "f_nak"},
        "nakshatra_lord": {"text": "Jupiter", "fact_id": "f_lord"},
        "pada": {"num": 3, "fact_id": "f_pada"},
        "longitude_sidereal": {"num": 328.0, "fact_id": "f_lon"},
        "house_d1": {"num": 11, "fact_id": "f_house"},
    }
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="MOON", position_facts=position_facts,
        dispositor_facts={}, tara_facts={}, now="2026-01-01T00:00:00+00:00",
    )
    assert row["citation_human"] == "Nakshatra-semantic profile: Moon"
