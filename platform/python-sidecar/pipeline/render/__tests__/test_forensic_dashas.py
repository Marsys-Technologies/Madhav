"""
Tests for pipeline/render/dashas_renderer.py (F-13)

Coverage (30+ tests):
- Empty chart_output → no crash, returns string
- All 32 systems heading present
- Vimshottari current chain table rendered
- Yogini table rendered
- Kalachakra table rendered
- Current chain table has Maha/Antar/Pratyantar/Sookshma rows
- Lord column populated
- Start date column populated
- End date column populated
- Missing data renders dash
- Next-10 Mahas section heading present
- 7 acharya systems each have next-10 table
- Next-10 table has # column
- Next-10 Years column present
- Two-pass verification heading present
- Vimshottari verification PASS rendered
- Vimshottari verification FAIL rendered
- Chara verification rendered
- Match ✓ when match=True
- Match ✗ when match=False
- Birth balance shown when present
- ALL_DASHA_SYSTEMS has 32 entries
- ACHARYA_SYSTEMS has 7 entries
- PERIOD_LEVELS has 4 entries
- render_dashas_section returns str
- No narration verbs in full output
- Next-10 table empty list renders placeholder dash
- Partial dasha data no crash
- Vimshottari appears in output
- Jaimini Chara appears in output
- Naisargika system rendered
- Mudda system rendered
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.dashas_renderer import (
    ALL_DASHA_SYSTEMS,
    ACHARYA_SYSTEMS,
    PERIOD_LEVELS,
    render_dashas_section,
    _render_current_chain,
    _render_next_10_mahas,
    _render_verification,
    _safe,
    _safe_int,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Sample data builders
# ---------------------------------------------------------------------------

def _make_current_dates() -> dict:
    return {
        "maha":       {"lord": "Jupiter", "start": "2018-03-15", "end": "2034-03-15"},
        "antar":      {"lord": "Saturn",  "start": "2024-01-10", "end": "2026-09-05"},
        "pratyantar": {"lord": "Mercury", "start": "2025-10-01", "end": "2026-02-15"},
        "sookshma":   {"lord": "Jupiter", "start": "2025-12-20", "end": "2026-01-10"},
    }


def _make_next_10() -> list:
    lords = ["Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn"]
    result = []
    for i, lord in enumerate(lords):
        start_year = 2034 + i * 2
        end_year = start_year + 2
        result.append({
            "lord": lord,
            "start": f"{start_year}-03-15",
            "end": f"{end_year}-03-15",
            "years": 2,
        })
    return result


def _make_system_data(balance: str = "Moon in Purva Bhadrapada, 4.3 years remaining") -> dict:
    return {
        "birth_nakshatra_balance": balance,
        "current_chain": ["Jupiter MD", "Saturn AD", "Mercury PD", "Jupiter SK"],
        "current_dates": _make_current_dates(),
        "next_10_mahas": _make_next_10(),
    }


def _full_chart() -> dict:
    dashas: dict = {key: _make_system_data() for key, _ in ALL_DASHA_SYSTEMS}
    return {
        "dashas": dashas,
        "d9_verification_vimshottari": {"match": True, "notes": "positions agree"},
        "d9_verification_chara": {"match": True},
    }


# ---------------------------------------------------------------------------
# Tests: module-level constants
# ---------------------------------------------------------------------------

def test_all_dasha_systems_32():
    assert len(ALL_DASHA_SYSTEMS) == 32


def test_acharya_systems_7():
    assert len(ACHARYA_SYSTEMS) == 7


def test_period_levels_4():
    assert len(PERIOD_LEVELS) == 4


def test_vimshottari_in_all_systems():
    keys = [k for k, _ in ALL_DASHA_SYSTEMS]
    assert "vimshottari" in keys


def test_kalachakra_in_all_systems():
    keys = [k for k, _ in ALL_DASHA_SYSTEMS]
    assert "kalachakra" in keys


def test_yogini_in_acharya():
    keys = [k for k, _ in ACHARYA_SYSTEMS]
    assert "yogini" in keys


# ---------------------------------------------------------------------------
# Tests: _safe helpers
# ---------------------------------------------------------------------------

def test_safe_none():
    assert _safe(None) == "—"


def test_safe_str():
    assert _safe("Jupiter") == "Jupiter"


def test_safe_int_none():
    assert _safe_int(None) == "—"


def test_safe_int_float():
    assert _safe_int(19.0) == "19"


# ---------------------------------------------------------------------------
# Tests: render_dashas_section — empty / graceful
# ---------------------------------------------------------------------------

def test_empty_chart_returns_string():
    result = render_dashas_section({})
    assert isinstance(result, str)


def test_empty_chart_no_crash():
    result = render_dashas_section({})
    assert len(result) > 0


def test_partial_data_no_crash():
    result = render_dashas_section({"dashas": {"vimshottari": {}}})
    assert "Vimshottari" in result


def test_missing_data_renders_dash():
    result = render_dashas_section({"dashas": {"vimshottari": {"current_dates": {}}}})
    assert "—" in result


# ---------------------------------------------------------------------------
# Tests: current chain section
# ---------------------------------------------------------------------------

def test_all_32_heading():
    result = render_dashas_section(_full_chart())
    assert "Current Period Chains" in result


def test_vimshottari_rendered():
    result = render_dashas_section(_full_chart())
    assert "Vimshottari" in result


def test_yogini_rendered():
    result = render_dashas_section(_full_chart())
    assert "Yogini" in result


def test_kalachakra_rendered():
    result = render_dashas_section(_full_chart())
    assert "Kalachakra" in result


def test_naisargika_rendered():
    result = render_dashas_section(_full_chart())
    assert "Naisargika" in result


def test_mudda_rendered():
    result = render_dashas_section(_full_chart())
    assert "Mudda" in result


def test_current_chain_maha_row():
    out = _render_current_chain("vimshottari", "Vimshottari", _make_system_data())
    assert "| Maha |" in out


def test_current_chain_antar_row():
    out = _render_current_chain("vimshottari", "Vimshottari", _make_system_data())
    assert "| Antar |" in out


def test_current_chain_pratyantar_row():
    out = _render_current_chain("vimshottari", "Vimshottari", _make_system_data())
    assert "| Pratyantar |" in out


def test_current_chain_sookshma_row():
    out = _render_current_chain("vimshottari", "Vimshottari", _make_system_data())
    assert "| Sookshma |" in out


def test_current_chain_lord_populated():
    out = _render_current_chain("vimshottari", "Vimshottari", _make_system_data())
    assert "Jupiter" in out


def test_current_chain_start_date():
    out = _render_current_chain("vimshottari", "Vimshottari", _make_system_data())
    assert "2018-03-15" in out


def test_birth_balance_shown():
    out = _render_current_chain("vimshottari", "Vimshottari", _make_system_data())
    assert "Purva Bhadrapada" in out


# ---------------------------------------------------------------------------
# Tests: next-10 Mahas
# ---------------------------------------------------------------------------

def test_next_10_heading():
    result = render_dashas_section(_full_chart())
    assert "Next 10 Mahadashas" in result


def test_next_10_years_column():
    out = _render_next_10_mahas("vimshottari", "Vimshottari", _make_system_data())
    assert "Years" in out


def test_next_10_number_column():
    out = _render_next_10_mahas("vimshottari", "Vimshottari", _make_system_data())
    assert "| 1 |" in out


def test_next_10_empty_renders_dash():
    out = _render_next_10_mahas("vimshottari", "Vimshottari", {})
    assert "—" in out


def test_all_7_acharya_next_10():
    result = render_dashas_section(_full_chart())
    for _, display in ACHARYA_SYSTEMS:
        assert display in result, f"Missing acharya system: {display}"


# ---------------------------------------------------------------------------
# Tests: two-pass verification
# ---------------------------------------------------------------------------

def test_verification_heading():
    result = render_dashas_section(_full_chart())
    assert "Two-Pass Dasha Verification" in result


def test_vimshottari_verification_pass():
    out = _render_verification("vimshottari", "Vimshottari", {"match": True})
    assert "PASS" in out
    assert "✓" in out


def test_vimshottari_verification_fail():
    out = _render_verification("vimshottari", "Vimshottari", {"match": False})
    assert "FAIL" in out
    assert "✗" in out


def test_chara_verification_rendered():
    result = render_dashas_section(_full_chart())
    assert "Jaimini Chara" in result


def test_verification_notes_shown():
    out = _render_verification("vimshottari", "Vimshottari", {"match": True, "notes": "positions agree"})
    assert "positions agree" in out


# ---------------------------------------------------------------------------
# Tests: no narration verbs + return type
# ---------------------------------------------------------------------------

def test_no_narration_verbs():
    result = render_dashas_section(_full_chart())
    lint_narration(result)


def test_no_narration_empty():
    result = render_dashas_section({})
    lint_narration(result)


def test_render_returns_str():
    assert isinstance(render_dashas_section(_full_chart()), str)


def test_render_non_empty():
    assert len(render_dashas_section(_full_chart())) > 0
