"""Golden-value narration fidelity test for bo_nakshatra_semantic.

Expected sentences are hand-composed from the emitter's documented rule:
headline = "<Graha>: <nakshatra> pada <n> (lord <L>)" + chain + tara + gandanta
bits joined by " | "; Janma tara (position 1) is a cautionary tara; a Moon
longitude of 328 deg is far from any gandanta junction.
"""
from __future__ import annotations

from bodha_writers.nakshatra_semantic_emitter import build_signal_row


def test_nakshatra_semantic_headline_and_summary_golden():
    position_facts = {
        "nakshatra": {"text": "Purva Bhadrapada", "fact_id": "f_nak"},
        "nakshatra_lord": {"text": "Jupiter", "fact_id": "f_lord"},
        "pada": {"num": 3, "fact_id": "f_pada"},
        "longitude_sidereal": {"num": 328.0, "fact_id": "f_lon"},
        "house_d1": {"num": 11, "fact_id": "f_house"},
    }
    dispositor_facts = {
        "chain_jsonb_atomic": {
            "jsonb": {"chain": ["Moon", "Saturn", "Venus", "Jupiter"],
                      "length": 4, "cycle_detected_at_step": 4},
            "fact_id": "f_chain",
        }
    }
    tara_facts = {
        "tara_name": {"text": "Janma", "fact_id": "f_tn"},
        "tara_count": {"num": 1},
        "tara_position": {"num": 1},
    }
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="MOON", position_facts=position_facts,
        dispositor_facts=dispositor_facts, tara_facts=tara_facts,
        now="2026-01-01T00:00:00+00:00",
    )
    built = {
        "signal_headline_text": row["signal_headline_text"],
        "signal_summary_text": row["signal_summary_text"],
    }
    assert built == {
        "signal_headline_text": (
            "Moon: Purva Bhadrapada pada 3 (lord Jupiter)"
            " | dispositor chain: Moon -> Saturn -> Venus -> Jupiter"
            " | tara=Janma(cautionary)"
        ),
        "signal_summary_text": (
            "category=nakshatra_semantic | graha=Moon | nakshatra=Purva Bhadrapada | "
            "nakshatra_lord=Jupiter | pada=3 | dispositor_chain_length=4 | "
            "tara_name=Janma | tara_position=1 | tara_favorable=False | "
            "gandanta_flag=False | gandanta_zone=not_applicable"
        ),
    }
