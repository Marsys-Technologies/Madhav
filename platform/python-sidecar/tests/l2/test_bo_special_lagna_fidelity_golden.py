"""Golden-value narration fidelity test for bo_special_lagna (special_lagna_emitter)."""
from __future__ import annotations

from bodha_writers.special_lagna_emitter import build_signal_row


def test_special_lagna_prose_golden():
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
    assert {
        "signal_headline_text": row["signal_headline_text"],
        "signal_summary_text": row["signal_summary_text"],
    } == {
        "signal_headline_text": "Indu Lagna in H5 (Leo, lord Sun) — governs wealth",
        "signal_summary_text": (
            "category=special_lagna | lagna=Indu Lagna | house_d1=5 | sign=Leo | "
            "sign_lord=Sun | nakshatra=Magha | domains=['wealth']"
        ),
    }
