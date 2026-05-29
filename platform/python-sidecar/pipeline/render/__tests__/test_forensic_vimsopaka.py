"""
Tests for pipeline/render/vimsopaka_renderer.py (F-11)

Coverage (30+ tests):
- Empty chart_output → no crash, returns string
- Vimsopaka section heading present
- Vimsopaka table has 9 graha rows
- All 4 varga group names in header (Saptavarga, Dashavarga, Shadvarga, Shodasavarga)
- Vimsopaka score formatted to 1 decimal
- Missing vimsopaka score renders as dash
- All 9 graha names in vimsopaka table
- 5 avastha scheme sections present
- Baladi heading present
- Jagradadi heading present
- Deeptadi heading present
- Lajjitadi heading present
- Shayanaadi heading present
- Each avastha table has 9 graha rows
- Avastha name column populated
- Avastha effect column populated
- Missing avastha data renders dash
- Graceful on empty vimsopaka dict
- Graceful on empty avasthas dict
- Graceful on partial graha data
- render_vimsopaka_section returns str
- GRAHAS constant has 9 entries
- VARGA_GROUPS has 4 entries
- AVASTHA_SCHEMES has 5 entries
- GRAHA_DISPLAY maps all 9 grahas
- Saptavarga score value present in output
- Shodasavarga score value present in output
- Baladi avastha name present (e.g. Yuva)
- Deeptadi avastha name present (e.g. Deepta)
- Lajjitadi effect present
- Shayanaadi effect present
- No narration verbs in full output
- render_vimsopaka_section output non-empty
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.vimsopaka_renderer import (
    GRAHAS,
    GRAHA_DISPLAY,
    VARGA_GROUPS,
    AVASTHA_SCHEMES,
    render_vimsopaka_section,
    _render_vimsopaka,
    _render_avastha_scheme,
    _fmt_score,
    _safe_str,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Sample data builders
# ---------------------------------------------------------------------------

def _make_vimsopaka() -> dict:
    return {
        graha: {
            "saptavarga":   15.2,
            "dashavarga":   13.5,
            "shadvarga":    12.0,
            "shodasavarga": 10.8,
        }
        for graha in GRAHAS
    }


def _make_avastha_entry(name: str = "Yuva", effect: str = "full strength") -> dict:
    return {"name": name, "effect": effect}


def _make_avasthas() -> dict:
    scheme_data = {
        "baladi":     {"name": "Yuva",     "effect": "full strength"},
        "jagradadi":  {"name": "Jagrat",   "effect": "active"},
        "deeptadi":   {"name": "Deepta",   "effect": "exalted state"},
        "lajjitadi":  {"name": "Mudita",   "effect": "pleased"},
        "shayanaadi": {"name": "Standing", "effect": "upright"},
    }
    return {graha: dict(scheme_data) for graha in GRAHAS}


def _full_chart() -> dict:
    return {
        "vimsopaka": _make_vimsopaka(),
        "avasthas":  _make_avasthas(),
    }


# ---------------------------------------------------------------------------
# Tests: module-level constants
# ---------------------------------------------------------------------------

def test_grahas_has_9_entries():
    assert len(GRAHAS) == 9


def test_varga_groups_has_4_entries():
    assert len(VARGA_GROUPS) == 4


def test_avastha_schemes_has_5_entries():
    assert len(AVASTHA_SCHEMES) == 5


def test_graha_display_maps_all_9():
    for g in GRAHAS:
        assert g in GRAHA_DISPLAY
        assert len(GRAHA_DISPLAY[g]) > 0


# ---------------------------------------------------------------------------
# Tests: _fmt_score
# ---------------------------------------------------------------------------

def test_fmt_score_none():
    assert _fmt_score(None) == "—"


def test_fmt_score_float():
    assert _fmt_score(15.2) == "15.2"


def test_fmt_score_int():
    assert _fmt_score(10) == "10.0"


def test_fmt_score_zero():
    assert _fmt_score(0) == "0.0"


def test_fmt_score_max():
    assert _fmt_score(20) == "20.0"


# ---------------------------------------------------------------------------
# Tests: render_vimsopaka_section — empty / graceful
# ---------------------------------------------------------------------------

def test_empty_chart_returns_string():
    result = render_vimsopaka_section({})
    assert isinstance(result, str)


def test_empty_chart_no_crash():
    result = render_vimsopaka_section({})
    assert len(result) > 0


def test_graceful_empty_vimsopaka():
    result = render_vimsopaka_section({"vimsopaka": {}})
    assert "Vimsopaka" in result


def test_graceful_empty_avasthas():
    result = render_vimsopaka_section({"avasthas": {}})
    assert "Avastha" in result


def test_graceful_partial_graha():
    partial = {"vimsopaka": {"sun": {"saptavarga": 12.0}}}
    result = render_vimsopaka_section(partial)
    assert "Sun" in result
    assert "—" in result


# ---------------------------------------------------------------------------
# Tests: Vimsopaka section
# ---------------------------------------------------------------------------

def test_vimsopaka_heading_present():
    result = render_vimsopaka_section(_full_chart())
    assert "Vimsopaka Dignities" in result


def test_vimsopaka_4_group_headers():
    result = render_vimsopaka_section(_full_chart())
    assert "Saptavarga" in result
    assert "Dashavarga" in result
    assert "Shadvarga" in result
    assert "Shodasavarga" in result


def test_vimsopaka_9_graha_rows():
    out = _render_vimsopaka(_make_vimsopaka())
    for g in GRAHA_DISPLAY.values():
        assert f"| {g} |" in out


def test_vimsopaka_saptavarga_score():
    result = render_vimsopaka_section(_full_chart())
    assert "15.2" in result


def test_vimsopaka_shodasavarga_score():
    result = render_vimsopaka_section(_full_chart())
    assert "10.8" in result


def test_vimsopaka_missing_score_dash():
    result = render_vimsopaka_section({"vimsopaka": {"sun": {}}})
    assert "—" in result


def test_vimsopaka_sun_row_present():
    result = render_vimsopaka_section(_full_chart())
    assert "| Sun |" in result


def test_vimsopaka_ketu_row_present():
    result = render_vimsopaka_section(_full_chart())
    assert "| Ketu |" in result


# ---------------------------------------------------------------------------
# Tests: Avastha sections
# ---------------------------------------------------------------------------

def test_baladi_heading_present():
    result = render_vimsopaka_section(_full_chart())
    assert "Baladi" in result


def test_jagradadi_heading_present():
    result = render_vimsopaka_section(_full_chart())
    assert "Jagradadi" in result


def test_deeptadi_heading_present():
    result = render_vimsopaka_section(_full_chart())
    assert "Deeptadi" in result


def test_lajjitadi_heading_present():
    result = render_vimsopaka_section(_full_chart())
    assert "Lajjitadi" in result


def test_shayanaadi_heading_present():
    result = render_vimsopaka_section(_full_chart())
    assert "Shayanaadi" in result


def test_baladi_name_yuva():
    result = render_vimsopaka_section(_full_chart())
    assert "Yuva" in result


def test_deeptadi_name_deepta():
    result = render_vimsopaka_section(_full_chart())
    assert "Deepta" in result


def test_lajjitadi_effect_present():
    result = render_vimsopaka_section(_full_chart())
    assert "pleased" in result


def test_shayanaadi_effect_upright():
    result = render_vimsopaka_section(_full_chart())
    assert "upright" in result


def test_jagradadi_effect_active():
    result = render_vimsopaka_section(_full_chart())
    assert "active" in result


def test_avastha_9_rows_per_scheme():
    avasthas = _make_avasthas()
    for scheme_key, scheme_display, scheme_note in AVASTHA_SCHEMES:
        out = _render_avastha_scheme(scheme_key, scheme_display, scheme_note, avasthas)
        for g in GRAHA_DISPLAY.values():
            assert f"| {g} |" in out, f"Missing {g} in {scheme_display}"


def test_avastha_missing_data_dash():
    result = render_vimsopaka_section({"avasthas": {"sun": {}}})
    assert "—" in result


def test_avastha_effect_column_label():
    result = render_vimsopaka_section(_full_chart())
    assert "Effect" in result


# ---------------------------------------------------------------------------
# Tests: no narration verbs
# ---------------------------------------------------------------------------

def test_no_narration_verbs_full():
    result = render_vimsopaka_section(_full_chart())
    # Should not raise NarrationViolation
    lint_narration(result)


def test_no_narration_verbs_empty():
    result = render_vimsopaka_section({})
    lint_narration(result)


# ---------------------------------------------------------------------------
# Tests: return type
# ---------------------------------------------------------------------------

def test_render_returns_str():
    assert isinstance(render_vimsopaka_section(_full_chart()), str)


def test_render_non_empty():
    assert len(render_vimsopaka_section(_full_chart())) > 0
