"""Golden-value narration fidelity test for bo_sudarshana.citation_human (sudarshana_emitter).

The emitter states the graha the tri-frame row is about, 'Sudarshana Chakra tri-frame: <Graha>' (code JUP is Jupiter). Expected sentence stated by hand.
"""
from __future__ import annotations

from bodha_writers.sudarshana_emitter import build_signal_row


def test_sudarshana_citation_human_names_the_graha():
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="JUP", fact_ids={"graha": "g", "lagna": "l", "moon": "m", "sun": "s"},
        now="2026-07-16T00:00:00+00:00",
        tri_frame={
            "house_from_lagna": 5, "house_from_moon": 9, "house_from_sun": 1,
            "class_from_lagna": "trikona", "class_from_moon": "trikona", "class_from_sun": "trikona",
            "agreement": "confirmed_3frame", "matching_class": "trikona",
        },
    )
    assert row["citation_human"] == "Sudarshana Chakra tri-frame: Jupiter"
