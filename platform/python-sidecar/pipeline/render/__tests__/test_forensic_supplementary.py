"""
Tests for pipeline/render/supplementary_renderer.py (F-14)

Coverage (30+ tests):
- Empty chart_output → no crash, returns string
- KP Cuspal section heading present
- KP table has 12 cusp rows
- Sub-Lord column present
- Nakshatra Lord column present
- Sub-Sub-Lord column present
- KP cusp data populated
- KP missing data renders dash
- Tajik section heading present
- Year Lord row present
- Hadda Lord row present
- Tajik missing data renders dash
- Midpoints section heading present
- Sun/Moon midpoint row present
- ASC/MC midpoint row present
- Midpoint longitude formatted to 2 decimals
- Eclipse section heading present
- Nearest solar eclipse row present
- Nearest lunar eclipse row present
- Eclipse date present in output
- Eclipse type present in output
- Nadi-Amsa section heading present
- Nadi-Amsa has 9 graha rows
- Rishi column populated
- Division column populated
- Argala section heading present
- Argala matrix has 12 rows
- Argala A encoding correct
- Virodha V encoding correct
- Astronomical section heading present
- Julian Day present
- GAST present
- LST present
- Birth place present
- Latitude present
- Longitude present
- render_supplementary_section returns str
- No narration verbs in full output
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.supplementary_renderer import (
    GRAHAS,
    GRAHA_DISPLAY,
    SIGNS,
    SIGN_DISPLAY,
    MIDPOINT_PAIRS,
    render_supplementary_section,
    _render_kp_cuspal,
    _render_tajik,
    _render_midpoints,
    _render_eclipses,
    _render_nadi_amsa,
    _render_argala,
    _render_astronomical,
    _safe,
    _fmt_float,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Sample data builders
# ---------------------------------------------------------------------------

def _make_kp_cuspal() -> dict:
    return {
        str(c): {"sub_lord": "Jupiter", "nakshatra_lord": "Moon", "sub_sub_lord": "Saturn"}
        for c in range(1, 13)
    }


def _make_tajik() -> dict:
    return {"year_lord": "Saturn", "hadda_lord": "Mercury"}


def _make_midpoints() -> dict:
    return {
        "sun_moon":      {"longitude": 260.5, "sign": "Sagittarius"},
        "asc_mc":        {"longitude": 170.2, "sign": "Virgo"},
        "sun_saturn":    {"longitude": 310.0, "sign": "Aquarius"},
        "moon_jupiter":  {"longitude": 45.3,  "sign": "Taurus"},
        "mercury_venus": {"longitude": 88.1,  "sign": "Gemini"},
        "mars_saturn":   {"longitude": 195.5, "sign": "Libra"},
        "jupiter_saturn":{"longitude": 240.0, "sign": "Sagittarius"},
    }


def _make_eclipses() -> dict:
    return {
        "nearest_solar": {"date": "1984-05-30", "type": "Partial", "eclipse_id": "S1984-05"},
        "nearest_lunar": {"date": "1984-05-15", "type": "Total",   "eclipse_id": "L1984-05"},
    }


def _make_nadi_amsa() -> dict:
    return {
        graha: {"rishi": "Vasishtha", "division": "D150"}
        for graha in GRAHAS
    }


def _make_argala() -> dict:
    """Sparse argala matrix: aries→cancer=argala, aries→capricorn=virodha."""
    argala: dict = {}
    for sign in SIGNS:
        argala[sign] = {}
    argala["aries"]["cancer"]    = "argala"
    argala["aries"]["capricorn"] = "virodha"
    return argala


def _make_astronomical() -> dict:
    return {
        "julian_day":           2445706.9,
        "sidereal_time_gast":   "14h 22m 18s",
        "local_sidereal_time":  "19h 48m 42s",
        "birth_place":          "Bhubaneswar, Odisha, India",
        "lat":                  20.2961,
        "lon":                  85.8245,
    }


def _full_chart() -> dict:
    return {
        "kp_cuspal":         _make_kp_cuspal(),
        "tajik_varshphal":   _make_tajik(),
        "midpoints":         _make_midpoints(),
        "eclipse_proximity": _make_eclipses(),
        "nadi_amsa":         _make_nadi_amsa(),
        "argala":            _make_argala(),
        "astronomical":      _make_astronomical(),
    }


# ---------------------------------------------------------------------------
# Tests: empty / graceful
# ---------------------------------------------------------------------------

def test_empty_chart_returns_string():
    result = render_supplementary_section({})
    assert isinstance(result, str)


def test_empty_chart_no_crash():
    result = render_supplementary_section({})
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Tests: KP Cuspal
# ---------------------------------------------------------------------------

def test_kp_heading():
    result = render_supplementary_section(_full_chart())
    assert "KP Cuspal" in result


def test_kp_12_cusps():
    out = _render_kp_cuspal(_make_kp_cuspal())
    for c in range(1, 13):
        assert f"| {c} |" in out


def test_kp_sub_lord_column():
    out = _render_kp_cuspal(_make_kp_cuspal())
    assert "Sub-Lord" in out


def test_kp_nakshatra_lord_column():
    out = _render_kp_cuspal(_make_kp_cuspal())
    assert "Nakshatra Lord" in out


def test_kp_sub_sub_lord_column():
    out = _render_kp_cuspal(_make_kp_cuspal())
    assert "Sub-Sub-Lord" in out


def test_kp_data_populated():
    out = _render_kp_cuspal(_make_kp_cuspal())
    assert "Jupiter" in out


def test_kp_missing_data_dash():
    out = _render_kp_cuspal({})
    assert "—" in out


# ---------------------------------------------------------------------------
# Tests: Tajik Varshphal
# ---------------------------------------------------------------------------

def test_tajik_heading():
    result = render_supplementary_section(_full_chart())
    assert "Tajik Varshphal" in result


def test_tajik_year_lord():
    out = _render_tajik(_make_tajik())
    assert "Year Lord" in out
    assert "Saturn" in out


def test_tajik_hadda_lord():
    out = _render_tajik(_make_tajik())
    assert "Hadda Lord" in out
    assert "Mercury" in out


def test_tajik_missing_dash():
    out = _render_tajik({})
    assert "—" in out


# ---------------------------------------------------------------------------
# Tests: Midpoints
# ---------------------------------------------------------------------------

def test_midpoints_heading():
    result = render_supplementary_section(_full_chart())
    assert "Midpoints" in result


def test_midpoints_sun_moon():
    out = _render_midpoints(_make_midpoints())
    assert "Sun/Moon" in out


def test_midpoints_asc_mc():
    out = _render_midpoints(_make_midpoints())
    assert "ASC/MC" in out


def test_midpoints_longitude_format():
    out = _render_midpoints(_make_midpoints())
    assert "260.50" in out


def test_midpoints_sign_present():
    out = _render_midpoints(_make_midpoints())
    assert "Sagittarius" in out


# ---------------------------------------------------------------------------
# Tests: Eclipse proximity
# ---------------------------------------------------------------------------

def test_eclipse_heading():
    result = render_supplementary_section(_full_chart())
    assert "Eclipse Proximity" in result


def test_eclipse_solar_row():
    out = _render_eclipses(_make_eclipses())
    assert "Nearest Solar" in out


def test_eclipse_lunar_row():
    out = _render_eclipses(_make_eclipses())
    assert "Nearest Lunar" in out


def test_eclipse_date_present():
    out = _render_eclipses(_make_eclipses())
    assert "1984-05-30" in out


def test_eclipse_type_present():
    out = _render_eclipses(_make_eclipses())
    assert "Partial" in out


def test_eclipse_id_present():
    out = _render_eclipses(_make_eclipses())
    assert "S1984-05" in out


# ---------------------------------------------------------------------------
# Tests: Nadi-Amsa
# ---------------------------------------------------------------------------

def test_nadi_heading():
    result = render_supplementary_section(_full_chart())
    assert "Nadi-Amsa" in result


def test_nadi_9_rows():
    out = _render_nadi_amsa(_make_nadi_amsa())
    for g in GRAHA_DISPLAY.values():
        assert f"| {g} |" in out


def test_nadi_rishi_populated():
    out = _render_nadi_amsa(_make_nadi_amsa())
    assert "Vasishtha" in out


def test_nadi_division_populated():
    out = _render_nadi_amsa(_make_nadi_amsa())
    assert "D150" in out


# ---------------------------------------------------------------------------
# Tests: Argala matrix
# ---------------------------------------------------------------------------

def test_argala_heading():
    result = render_supplementary_section(_full_chart())
    assert "Argala" in result


def test_argala_12_rows():
    out = _render_argala(_make_argala())
    for sign in SIGN_DISPLAY.values():
        assert sign in out


def test_argala_a_encoding():
    out = _render_argala(_make_argala())
    assert "| A |" in out or " A |" in out


def test_argala_v_encoding():
    out = _render_argala(_make_argala())
    assert "| V |" in out or " V |" in out


def test_argala_key_legend():
    out = _render_argala(_make_argala())
    assert "Key" in out


# ---------------------------------------------------------------------------
# Tests: Astronomical
# ---------------------------------------------------------------------------

def test_astronomical_heading():
    result = render_supplementary_section(_full_chart())
    assert "Astronomical Data" in result


def test_astronomical_julian_day():
    out = _render_astronomical(_make_astronomical())
    assert "Julian Day" in out
    assert "2445706" in out


def test_astronomical_gast():
    out = _render_astronomical(_make_astronomical())
    assert "GAST" in out
    assert "14h 22m 18s" in out


def test_astronomical_lst():
    out = _render_astronomical(_make_astronomical())
    assert "Local Sidereal Time" in out
    assert "19h 48m 42s" in out


def test_astronomical_birth_place():
    out = _render_astronomical(_make_astronomical())
    assert "Bhubaneswar" in out


def test_astronomical_latitude():
    out = _render_astronomical(_make_astronomical())
    assert "20.2961" in out


def test_astronomical_longitude():
    out = _render_astronomical(_make_astronomical())
    assert "85.8245" in out


# ---------------------------------------------------------------------------
# Tests: no narration verbs + return type
# ---------------------------------------------------------------------------

def test_no_narration_verbs():
    result = render_supplementary_section(_full_chart())
    lint_narration(result)


def test_no_narration_empty():
    result = render_supplementary_section({})
    lint_narration(result)


def test_render_returns_str():
    assert isinstance(render_supplementary_section(_full_chart()), str)


def test_render_non_empty():
    assert len(render_supplementary_section(_full_chart())) > 0
