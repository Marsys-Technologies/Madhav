"""Golden-value narration fidelity test for bo_sudarshana (sudarshana_emitter)."""
from __future__ import annotations

from bodha_writers.sudarshana_emitter import build_signal_row

_FACT_IDS = {"graha": "g", "lagna": "l", "moon": "m", "sun": "s"}
_NOW = "2026-07-16T00:00:00+00:00"


def test_sudarshana_prose_golden():
    # All three frames land in trikona houses (5, 9, 1).
    confirmed = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="JUP", fact_ids=_FACT_IDS, now=_NOW,
        tri_frame={
            "house_from_lagna": 5, "house_from_moon": 9, "house_from_sun": 1,
            "class_from_lagna": "trikona", "class_from_moon": "trikona", "class_from_sun": "trikona",
            "agreement": "confirmed_3frame", "matching_class": "trikona",
        },
    )
    assert {
        "signal_headline_text": confirmed["signal_headline_text"],
        "signal_summary_text": confirmed["signal_summary_text"],
    } == {
        "signal_headline_text": "Jupiter: tri-frame confirmed trikona (H5 Lagna / H9 Moon / H1 Sun)",
        "signal_summary_text": (
            "category=sudarshana_agreement | graha=Jupiter | house_from_lagna=5 | "
            "house_from_moon=9 | house_from_sun=1 | class_from_lagna=trikona | "
            "class_from_moon=trikona | class_from_sun=trikona | "
            "agreement=confirmed_3frame | matching_class=trikona"
        ),
    }

    # Houses 5 (trikona), 4 (kendra), 9 (trikona): two of three match.
    partial = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="JUP", fact_ids=_FACT_IDS, now=_NOW,
        tri_frame={
            "house_from_lagna": 5, "house_from_moon": 4, "house_from_sun": 9,
            "class_from_lagna": "trikona", "class_from_moon": "kendra", "class_from_sun": "trikona",
            "agreement": "partial_2frame", "matching_class": "trikona",
        },
    )
    assert partial["signal_headline_text"] == (
        "Jupiter: tri-frame partial (trikona 2-of-3) — H5(trikona) Lagna / "
        "H4(kendra) Moon / H9(trikona) Sun"
    )

    # Houses 5 (trikona), 6 (dusthana), 11 (upachaya): all differ.
    contradicted = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="JUP", fact_ids=_FACT_IDS, now=_NOW,
        tri_frame={
            "house_from_lagna": 5, "house_from_moon": 6, "house_from_sun": 11,
            "class_from_lagna": "trikona", "class_from_moon": "dusthana", "class_from_sun": "upachaya",
            "agreement": "contradicted", "matching_class": None,
        },
    )
    assert contradicted["signal_headline_text"] == (
        "Jupiter: tri-frame CONTRADICTED — H5(trikona) from Lagna vs "
        "H6(dusthana) from Moon vs H11(upachaya) from Sun"
    )
    assert contradicted["signal_summary_text"] == (
        "category=sudarshana_agreement | graha=Jupiter | house_from_lagna=5 | "
        "house_from_moon=6 | house_from_sun=11 | class_from_lagna=trikona | "
        "class_from_moon=dusthana | class_from_sun=upachaya | "
        "agreement=contradicted | matching_class=None"
    )
