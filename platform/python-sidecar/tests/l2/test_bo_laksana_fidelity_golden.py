"""Golden-value narration fidelity tests for bo_laksana.

Expected sentences are hand-composed from the writer's templates and rules:
  - fact path: headline "<SUBJECT> (H<house>, <varga>): <cat words>: <key words> = <value> [<asset>]";
    summary "category=.. | key=.. | value_text=.. | <sorted config k=v>";
  - D9 cross-check: Sun exalted in D1 (tier 3) with a debilitated D9 (tier -2)
    is the 'broken_promise' classification, malefic, absent any L1 neecha-bhanga redemption.
"""
from __future__ import annotations

from pipeline.orchestrator.writers import bo_laksana
from pipeline.orchestrator.writers.bo_laksana import (
    _build_headline_text,
    _build_navamsha_cross_check_signals,
    _build_summary_text,
)


def test_bo_laksana_fact_path_headline_summary_golden():
    config = {"varga": "D1", "house": 10, "graha": "Sun", "dropped": None}
    row = {
        "signal_headline_text": _build_headline_text(
            "graha_position", "sign", "Capricorn", None, "ga_positions",
            fact_subject="sun", house=10, varga_id="D1",
        ),
        "signal_summary_text": _build_summary_text(
            "graha_position", "sign", "Capricorn", None, config,
        ),
    }
    assert row == {
        "signal_headline_text": "SUN (H10, D1): graha position: sign = Capricorn [ga_positions]",
        "signal_summary_text": (
            "category=graha_position | key=sign | value_text=Capricorn | "
            "graha=Sun | house=10 | varga=D1"
        ),
    }


def test_bo_laksana_d9_cross_check_headline_summary_citation_golden(monkeypatch):
    monkeypatch.setattr(bo_laksana, "_build_d1_dignity_map",
                        lambda conn, chart_id, aya: {"Sun": ("exalted", "fact_sun_d1")})
    monkeypatch.setattr(bo_laksana, "_build_d9_dignity_map",
                        lambda conn, chart_id, aya: {"Sun": "debilitated"})
    monkeypatch.setattr(bo_laksana, "_build_nbry_redemption_map",
                        lambda conn, chart_id, aya: {})
    monkeypatch.setattr(bo_laksana, "_build_nbry_d9_redemption_map",
                        lambda conn, chart_id, aya: {})
    signals = _build_navamsha_cross_check_signals(
        None, "c", "lahiri_chitrapaksha", "b", "2026-01-01T00:00:00+00:00",
        {}, {}, {},
    )
    assert len(signals) == 1
    built = {
        "signal_headline_text": signals[0]["signal_headline_text"],
        "signal_summary_text": signals[0]["signal_summary_text"],
        "citation_human": signals[0]["citation_human"],
    }
    assert built == {
        "signal_headline_text": "D9 cross-check: Sun D1=exalted × D9=debilitated → broken_promise",
        "signal_summary_text": (
            "category=navamsha_d9_cross_check | key=sun | d1_dignity=exalted | "
            "d9_dignity=debilitated | classification=broken_promise | valence=malefic"
        ),
        "citation_human": "Navamsha D9 cross-check: Sun D1=exalted × D9=debilitated → broken_promise",
    }
