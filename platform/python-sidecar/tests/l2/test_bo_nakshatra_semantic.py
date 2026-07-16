"""
Tests for bo_nakshatra_semantic / bodha_writers.nakshatra_semantic_emitter
(D-2 Lane V-5, CR-26/64).

Type specimens independently reproduced against chart 482012f1's real
lahiri_chitrapaksha facts (verified live via mcp__postgres__query before
writing this test):
  - MOON: nakshatra=Purva Bhadrapada, nakshatra_lord=Jupiter, pada=3,
    house_d1=11 (a FORENSIC-anchored fact — MARSYS canonical Moon nakshatra).
  - SUN: nakshatra=Shravana, nakshatra_lord=Moon, pada=4, house_d1=10.
  - dispositor chain for MOON: Moon -> Saturn -> Venus -> Jupiter (cycle
    detected at step 4).
  - tara bala for MOON: tara_name=Janma, tara_count=1, tara_position=1
    (Janma tara = counted-from-self, always position 1).
"""
from __future__ import annotations

import json

import pytest

from bodha_writers.nakshatra_semantic_emitter import (
    GRAHAS,
    NAKSHATRA_SEMANTIC_CLASS_PRIOR,
    NAKSHATRA_SEMANTIC_SUBSYSTEM,
    SIGNAL_TYPE_CLASS,
    _gandanta_flag,
    _degree_in_nakshatra,
    build_signal_row,
)


# ── _degree_in_nakshatra() ────────────────────────────────────────────────

def test_degree_in_nakshatra_none_when_no_longitude():
    assert _degree_in_nakshatra(None) is None


def test_degree_in_nakshatra_wraps_within_span():
    # 0 deg -> 0 within its nakshatra; one full span -> 0 (start of next nakshatra)
    span = 360.0 / 27.0
    assert _degree_in_nakshatra(0.0) == pytest.approx(0.0)
    assert _degree_in_nakshatra(span) == pytest.approx(0.0, abs=1e-9)
    assert _degree_in_nakshatra(20.0) == pytest.approx(20.0 - span, abs=1e-4)


# ── _gandanta_flag() ───────────────────────────────────────────────────────

def test_gandanta_flag_not_applicable_for_non_gandanta_nakshatra():
    is_g, zone = _gandanta_flag("Rohini", 4, 40.0)
    assert is_g is False
    assert zone == "not_applicable"


def test_gandanta_flag_tail_true_within_threshold():
    # Revati spans 346.6667-360.0; last 0.8 deg = 359.2-360.0
    is_g, zone = _gandanta_flag("Revati", 4, 359.7)
    assert is_g is True
    assert zone == "gandanta_tail_revati"


def test_gandanta_flag_tail_false_outside_threshold():
    # pada 4 but well before the tight tail zone
    is_g, zone = _gandanta_flag("Revati", 4, 350.0)
    assert is_g is False
    assert zone == "end_pada_revati"


def test_gandanta_flag_head_true_within_threshold():
    # Ashwini spans 0-13.333; first 0.8 deg
    is_g, zone = _gandanta_flag("Ashwini", 1, 0.5)
    assert is_g is True
    assert zone == "gandanta_head_ashwini"


def test_gandanta_flag_head_false_outside_threshold():
    is_g, zone = _gandanta_flag("Ashwini", 1, 5.0)
    assert is_g is False
    assert zone == "start_pada_ashwini"


def test_gandanta_flag_none_pada_or_nakshatra():
    assert _gandanta_flag(None, 4, 10.0) == (False, "not_applicable")
    assert _gandanta_flag("Revati", None, 10.0) == (False, "not_applicable")


# ── build_signal_row(): TYPE SPECIMEN — Moon on 482012f1/lahiri ──────────

def _fact(text=None, num=None, fact_id="f0"):
    return {"text": text, "num": num, "jsonb": None, "fact_id": fact_id}


def test_build_signal_row_moon_type_specimen():
    position_facts = {
        "nakshatra": _fact(text="Purva Bhadrapada", fact_id="fnak"),
        "nakshatra_lord": _fact(text="Jupiter", fact_id="fnaklord"),
        "pada": _fact(num=3, fact_id="fpada"),
        "longitude_sidereal": _fact(num=327.055230133129, fact_id="flon"),
        "house_d1": _fact(num=11, fact_id="fhouse"),
    }
    dispositor_facts = {
        "chain_jsonb_atomic": {
            "jsonb": {"chain": ["Moon", "Saturn", "Venus", "Jupiter"],
                      "signs": ["Aquarius", "Libra", "Sagittarius", "Sagittarius"],
                      "length": 4, "cycle_detected_at_step": 4},
            "fact_id": "fdisp",
        }
    }
    tara_facts = {
        "tara_name": _fact(text="Janma", fact_id="ftaraname"),
        "tara_count": _fact(num=1, fact_id="ftaracount"),
        "tara_position": _fact(num=1, fact_id="ftarapos"),
    }
    row = build_signal_row(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        ayanamsha_id="lahiri_chitrapaksha",
        build_id="00000000-0000-0000-0000-000000000000",
        graha_code="MOON",
        position_facts=position_facts,
        dispositor_facts=dispositor_facts,
        tara_facts=tara_facts,
        now="2026-07-16T00:00:00+00:00",
    )
    assert row is not None
    cfg = json.loads(row["configuration_jsonb"])
    assert cfg["nakshatra"] == "Purva Bhadrapada"
    assert cfg["nakshatra_lord"] == "Jupiter"
    assert cfg["pada"] == 3
    assert cfg["dispositor_chain"] == ["Moon", "Saturn", "Venus", "Jupiter"]
    assert cfg["tara_name"] == "Janma"
    assert cfg["tara_position"] == 1
    # Janma tara (position 1) is classically cautionary (Janma/Vipat/Pratyak/Naidhana)
    assert cfg["tara_favorable"] is False
    assert row["signal_type_class"] == SIGNAL_TYPE_CLASS == "nakshatra_semantic"
    assert row["source_subsystem"] == NAKSHATRA_SEMANTIC_SUBSYSTEM == "nakshatra"
    assert NAKSHATRA_SEMANTIC_CLASS_PRIOR == 1.00
    assert row["computed_salience"] > 0
    assert "fnak" in row["constituent_facts_array"]
    assert "fdisp" in row["constituent_facts_array"]
    assert "ftaraname" in row["constituent_facts_array"]


def test_build_signal_row_returns_none_without_nakshatra_fact():
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="SUN", position_facts={}, dispositor_facts=None,
        tara_facts=None, now="2026-07-16T00:00:00+00:00",
    )
    assert row is None


def test_build_signal_row_not_null_columns_populated():
    position_facts = {
        "nakshatra": _fact(text="Shravana", fact_id="f1"),
        "nakshatra_lord": _fact(text="Moon", fact_id="f2"),
        "pada": _fact(num=4, fact_id="f3"),
        "longitude_sidereal": _fact(num=291.962617284992, fact_id="f4"),
        "house_d1": _fact(num=10, fact_id="f5"),
    }
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="SUN", position_facts=position_facts, dispositor_facts=None,
        tara_facts=None, now="2026-07-16T00:00:00+00:00",
    )
    not_null_cols = [
        "signal_id", "chart_id", "ayanamsha_id", "build_id",
        "signal_type_id", "signal_type_class", "signal_tradition",
        "fact_kind", "source_l1_asset", "source_subsystem", "lel_origin",
        "configuration_jsonb", "constituent_facts_array",
        "deterministic_strength", "verification_certainty",
        "computed_salience", "salience_formula_version",
        "domains_affected_array", "domain_salience_jsonb",
        "active_duration_class", "verification_pass_status",
        "citation_ref", "citation_human", "computed_at", "engine_version",
    ]
    for col in not_null_cols:
        assert row[col] is not None, f"{col} must not be None (NOT NULL column)"


def test_all_9_grahas_covered():
    assert len(GRAHAS) == 9
    assert set(GRAHAS) == {"SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN"}


# ── L0 class_priors seed: nakshatra_semantic row (append-only, DIS.019) ───

def test_l0_class_priors_has_nakshatra_semantic_row():
    from brahmagyan.l0_class_priors import CLASS_ROWS

    matches = [r for r in CLASS_ROWS if r[0] == "nakshatra_semantic"]
    assert len(matches) == 1, "exactly one nakshatra_semantic row expected (append-only)"
    _, prior, _ = matches[0]
    assert prior == 1.00  # DIS.019/DR-6 ratified value


def test_bo_nakshatra_semantic_writer_is_registered():
    from pipeline.orchestrator.writers.bo_nakshatra_semantic import BoNakshatraSemanticWriter
    from pipeline.orchestrator.writers import get_writer

    assert BoNakshatraSemanticWriter.asset_id == "bo_nakshatra_semantic"
    assert get_writer("bo_nakshatra_semantic") is BoNakshatraSemanticWriter
