"""Golden-value narration fidelity test for bo_special_lagna.citation_human (special_lagna_emitter).

The emitter states the lagna it computed, 'Special lagna: <display name>', where INDU_LAGNA is shown as 'Indu Lagna'. Expected sentence stated by hand.
"""
from __future__ import annotations

from bodha_writers.special_lagna_emitter import build_signal_row


def test_special_lagna_citation_human_names_the_lagna():
    facts = {
        "house_d1": {"num": 5, "text": None, "fact_id": "f1"},
        "sign": {"num": None, "text": "Leo", "fact_id": "f2"},
        "sign_lord": {"num": None, "text": "Sun", "fact_id": "f3"},
        "nakshatra": {"num": None, "text": "Magha", "fact_id": "f4"},
    }
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        lagna_key="INDU_LAGNA", facts=facts, now="2026-07-16T00:00:00+00:00",
    )
    assert row["citation_human"] == "Special lagna: Indu Lagna"
