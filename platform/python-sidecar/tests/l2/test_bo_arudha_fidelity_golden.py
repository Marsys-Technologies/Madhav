"""Golden-value narration fidelity test for bo_arudha (arudha_emitter)."""
from __future__ import annotations

from bodha_writers.arudha_emitter import build_signal_rows


def test_arudha_prose_golden():
    arudha_facts = {
        "ARUDHA_A1": {"house_d1": {"num": 9, "fact_id": "fal"}, "sign": {"text": "Sagittarius"}},
        "ARUDHA_A2": {"house_d1": {"num": 3, "fact_id": "fa2"}, "sign": {"text": "Cancer"}},
    }
    graha_houses = {
        "JUP": {"house_d1": 9, "fact_id": "fjup"},
        "SUN": {"house_d1": 10, "fact_id": "fsun"},
    }
    rows = build_signal_rows(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        arudha_facts=arudha_facts, graha_houses=graha_houses,
        now="2026-07-16T00:00:00+00:00",
    )
    by_id = {r["signal_type_id"]: r for r in rows}

    # AL in house 9 (a trikona house) of Sagittarius.
    al_row = by_id["arudha:AL_bhava_relation"]
    assert {
        "signal_headline_text": al_row["signal_headline_text"],
        "signal_summary_text": al_row["signal_summary_text"],
        "citation_human": al_row["citation_human"],
    } == {
        "signal_headline_text": "Arudha Lagna (AL) in H9 (Sagittarius) — classical category: trikona",
        "signal_summary_text": "category=arudha | AL_house=9 | AL_sign=Sagittarius | AL_category=trikona",
        "citation_human": "Arudha: Arudha Lagna (AL) in H9 (Sagittarius) — classical category: trikona",
    }

    # Jupiter shares AL's house: a natural benefic conjunct.
    jup_row = by_id["arudha:AL_conjunction:JUP"]
    assert jup_row["signal_headline_text"] == "Jupiter conjunct Arudha Lagna in H9 — benefic on public image"
    assert jup_row["signal_summary_text"] == "category=arudha | AL_house=9 | graha=Jupiter | tenor=benefic"
    assert jup_row["citation_human"] == "Arudha: Jupiter conjunct Arudha Lagna in H9 — benefic on public image"

    # A2 in house 3 with no occupant.
    a2_row = by_id["arudha:ARUDHA_A2_tenancy"]
    assert a2_row["signal_headline_text"] == "A2 (dhana arudha) in H3 (Cancer) — untenanted"
