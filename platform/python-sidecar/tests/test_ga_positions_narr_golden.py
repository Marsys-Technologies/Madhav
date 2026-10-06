"""
tests/test_ga_positions_narr_golden.py -- Narr golden-value test for ga_positions

``chart_facts.citation_human`` is narration: the sentence a reader sees for a position fact
(CLAUDE.md section N.7 item 5: verified fact != verified prose).

What this pins, on the pure helper ``_citation_human_position`` and on ``_build_chalit_rows``
(hand-built chart_output, no database): for the native's anchors (Sun in Capricorn,
Moon in Purva Bhadrapada, Aries lagna so Capricorn is the 10th whole-sign house) the
sentences name the graha, the sign / nakshatra / house and the ayanamsha (rendered title-case).
A sidereal longitude of 291.5 deg is 21.5 deg into Capricorn (270-300).
"""
from __future__ import annotations

from ga_writers.ga_positions_writer import _build_chalit_rows, _citation_human_position


def test_positions_citation_human_sign_nakshatra_longitude_and_chalit_house() -> None:
    citation_human_sun_sign = _citation_human_position("Sun", "sign", "Capricorn", None, "lahiri")
    citation_human_moon_nakshatra = _citation_human_position("Moon", "nakshatra", "Purva Bhadrapada", None, "lahiri")
    citation_human_sun_longitude = _citation_human_position("Sun", "longitude_sidereal", None, 291.5, "lahiri")
    citation_human_sun_house = _citation_human_position("Sun", "house_d1", None, 10.0, "lahiri")
    chalit_rows = _build_chalit_rows(
        {
            "bhava_chalit": {
                "graha_chalit": {
                    "Sun": {
                        "chalit_house": 10,
                        "whole_sign_house": 10,
                        "dist_to_madhya_deg": 2.5,
                        "dist_to_nearest_boundary_deg": 12.5,
                        "nearest_boundary": "start",
                        "sandhi_flag": False,
                        "sandhi_reasons": [],
                    }
                }
            }
        },
        "chart-fixture", "build-fixture", "lahiri", "2026-01-01T00:00:00+00:00",
    )
    chalit_by_key = {r["fact_key"]: r for r in chalit_rows}

    assert citation_human_sun_sign == "Sun is in Capricorn (Lahiri)."
    assert citation_human_moon_nakshatra == "Moon nakshatra: Purva Bhadrapada (Lahiri)."
    assert citation_human_sun_longitude == "Sun sidereal longitude: 291.500000 deg (Lahiri)."
    assert citation_human_sun_house == "Sun whole-sign house: 10 (Lahiri)."
    assert chalit_by_key["chalit_house_sripati"]["citation_human"] == "Sun Sripati bhāva-chalit house: 10 (Lahiri)."
