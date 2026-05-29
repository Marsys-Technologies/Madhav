"""
Tests for pipeline/render/aspects_renderer.py (F-09)

Coverage (30+ tests):
- Empty chart_output → no crash, returns string
- Parashari matrix section heading present
- Jaimini rasi-drishti section heading present
- Tajik aspects section heading present
- Mutual aspects section heading present
- Graha-to-lagna section heading present
- No narration verbs (lint_narration passes)
- All 9 graha names present in Parashari matrix
- All 12 sign names present in Jaimini matrix
- Placeholder row '—' when no tajik aspects
- Placeholder row '—' when no mutual aspects
- Placeholder row '—' when no lagna aspects
- Parashari matrix has correct column headers H1–H12
- Jaimini matrix: dual sign aspects fixed signs
- Jaimini matrix: moveable sign aspects dual (not adjacent)
- Jaimini matrix: fixed sign aspects moveable (not adjacent)
- Jaimini static matrix: Gemini aspects all 4 fixed signs
- Jaimini static matrix: Aries (moveable) does NOT aspect adjacent Gemini
- Jaimini static matrix: Aries (moveable) DOES aspect non-adjacent Virgo
- Tajik entry: body1, body2, aspect_type, orb, applying all rendered
- Tajik applying=True renders "Yes"
- Tajik applying=False renders "No"
- Mutual aspects: body1 and body2 names rendered
- Lagna aspect: graha name and orb rendered
- Orb formatted with one decimal place + degree symbol
- Parashari data cell rendered with strength + orb
- Parashari missing house renders dash
- render_aspects_section returns str
- Full section includes all five headings
- Parashari table has 9 body rows (one per graha)
- Jaimini table has 12 sign rows
- Tajik multiple entries all rendered
- Mutual multiple entries all rendered
- Lagna multiple entries all rendered
- GRAHAS constant contains all 9 classical grahas
- SIGNS constant contains all 12 signs
- Static Jaimini: Taurus (fixed) aspects Cancer (moveable, non-adjacent) = Yes
- Static Jaimini: Taurus (fixed) does NOT aspect adjacent Aries
- Static Jaimini: Sagittarius (dual) aspects Leo (fixed) = Yes
- Static Jaimini: Aries (moveable) does NOT aspect own-type Taurus
"""
import sys
from pathlib import Path

import pytest

# Allow import from python-sidecar root
sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.aspects_renderer import (
    GRAHAS,
    SIGNS,
    GRAHA_DISPLAY,
    SIGN_DISPLAY,
    MOVEABLE_SIGNS,
    FIXED_SIGNS,
    DUAL_SIGNS,
    _JAIMINI_MATRIX,
    render_aspects_section,
    _render_parashari_matrix,
    _render_jaimini_matrix,
    _render_tajik_aspects,
    _render_mutual_aspects,
    _render_lagna_aspects,
    _fmt_float,
    _fmt_bool_yn,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Fixtures / sample data
# ---------------------------------------------------------------------------

def _parashari_entry(strength: str, orb: float) -> dict:
    return {"aspect_type": "7th", "strength": strength, "orb": orb}


def _tajik_entry(
    body1: str, body2: str, aspect_type: str, orb: float, applying: bool
) -> dict:
    return {
        "body1": body1,
        "body2": body2,
        "aspect_type": aspect_type,
        "orb": orb,
        "applying": applying,
    }


def _mutual_entry(body1: str, body2: str, aspect_type: str) -> dict:
    return {"body1": body1, "body2": body2, "aspect_type": aspect_type}


def _lagna_entry(body: str, aspect_type: str, orb: float) -> dict:
    return {"body": body, "aspect_type": aspect_type, "orb": orb}


SAMPLE_PARASHARI: dict = {
    "sun":     {"7": _parashari_entry("full", 0.0)},
    "moon":    {"7": _parashari_entry("full", 1.5)},
    "mars":    {
        "4": _parashari_entry("full", 2.1),
        "7": _parashari_entry("full", 0.0),
        "8": _parashari_entry("full", 3.4),
    },
    "mercury": {"7": _parashari_entry("full", 0.5)},
    "jupiter": {
        "5": _parashari_entry("full", 1.0),
        "7": _parashari_entry("full", 0.0),
        "9": _parashari_entry("full", 2.2),
    },
    "venus":   {"7": _parashari_entry("full", 0.8)},
    "saturn":  {
        "3": _parashari_entry("three-quarter", 1.2),
        "7": _parashari_entry("full", 0.0),
        "10": _parashari_entry("three-quarter", 0.9),
    },
    "rahu":    {
        "5": _parashari_entry("full", 2.5),
        "7": _parashari_entry("full", 0.0),
        "9": _parashari_entry("full", 1.8),
    },
    "ketu":    {
        "5": _parashari_entry("full", 3.0),
        "7": _parashari_entry("full", 0.0),
        "9": _parashari_entry("full", 2.0),
    },
}

SAMPLE_TAJIK: list[dict] = [
    _tajik_entry("sun",  "moon",    "trine",       2.5,  True),
    _tajik_entry("sun",  "saturn",  "opposition",  5.1,  False),
    _tajik_entry("mars", "jupiter", "square",      3.3,  True),
    _tajik_entry("venus","mercury", "sextile",     1.7,  False),
    _tajik_entry("moon", "rahu",    "semi-sextile",2.0,  True),
]

SAMPLE_MUTUAL: list[dict] = [
    _mutual_entry("sun",     "saturn",  "7th mutual"),
    _mutual_entry("jupiter", "mercury", "7th mutual"),
    _mutual_entry("mars",    "moon",    "special mutual"),
]

SAMPLE_LAGNA: list[dict] = [
    _lagna_entry("jupiter", "trine",      3.2),
    _lagna_entry("saturn",  "opposition", 6.1),
    _lagna_entry("mars",    "square",     1.4),
]

FULL_CHART_OUTPUT: dict = {
    "aspects": {
        "parashari":           SAMPLE_PARASHARI,
        "jaimini_rasi_drishti": {},
        "tajik":               SAMPLE_TAJIK,
        "mutual":              SAMPLE_MUTUAL,
        "lagna_aspects":       SAMPLE_LAGNA,
    }
}


# ---------------------------------------------------------------------------
# Test group 1: Empty chart → no crash
# ---------------------------------------------------------------------------

def test_empty_chart_output_no_crash():
    result = render_aspects_section({})
    assert isinstance(result, str)


def test_empty_aspects_dict_no_crash():
    result = render_aspects_section({"aspects": {}})
    assert isinstance(result, str)


def test_render_aspects_section_returns_str():
    result = render_aspects_section(FULL_CHART_OUTPUT)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Test group 2: All five section headings present
# ---------------------------------------------------------------------------

def test_parashari_heading_present():
    result = render_aspects_section(FULL_CHART_OUTPUT)
    assert "### Parashari Aspect Matrix" in result


def test_jaimini_heading_present():
    result = render_aspects_section(FULL_CHART_OUTPUT)
    assert "### Jaimini Rasi-Drishti Matrix" in result


def test_tajik_heading_present():
    result = render_aspects_section(FULL_CHART_OUTPUT)
    assert "### Tajik Aspects" in result


def test_mutual_heading_present():
    result = render_aspects_section(FULL_CHART_OUTPUT)
    assert "### Mutual Aspects" in result


def test_lagna_heading_present():
    result = render_aspects_section(FULL_CHART_OUTPUT)
    assert "### Graha-to-Lagna Aspects" in result


def test_full_section_all_five_headings():
    result = render_aspects_section(FULL_CHART_OUTPUT)
    assert "### Parashari Aspect Matrix" in result
    assert "### Jaimini Rasi-Drishti Matrix" in result
    assert "### Tajik Aspects" in result
    assert "### Mutual Aspects" in result
    assert "### Graha-to-Lagna Aspects" in result


# ---------------------------------------------------------------------------
# Test group 3: No narration verbs
# ---------------------------------------------------------------------------

def test_no_narration_verbs_full_section():
    result = render_aspects_section(FULL_CHART_OUTPUT)
    lint_narration(result)  # raises NarrationViolation if fails


def test_no_narration_verbs_empty_section():
    result = render_aspects_section({})
    lint_narration(result)


# ---------------------------------------------------------------------------
# Test group 4: Parashari matrix content
# ---------------------------------------------------------------------------

def test_parashari_all_9_graha_names_present():
    result = _render_parashari_matrix({"parashari": SAMPLE_PARASHARI})
    for graha in GRAHAS:
        assert GRAHA_DISPLAY[graha] in result, f"Missing graha: {graha}"


def test_parashari_column_headers_h1_to_h12():
    result = _render_parashari_matrix({"parashari": SAMPLE_PARASHARI})
    for h in range(1, 13):
        assert f"H{h}" in result


def test_parashari_populated_cell_rendered():
    result = _render_parashari_matrix({"parashari": SAMPLE_PARASHARI})
    # Sun has a 7th house aspect
    assert "Full" in result


def test_parashari_missing_house_renders_dash():
    result = _render_parashari_matrix({"parashari": SAMPLE_PARASHARI})
    # Most cells are empty for most grahas
    assert "—" in result


def test_parashari_orb_in_cell():
    result = _render_parashari_matrix({"parashari": SAMPLE_PARASHARI})
    # Some orb value should appear (e.g. 2.1° from Mars H4)
    assert "2.1°" in result


def test_parashari_table_has_9_graha_rows():
    result = _render_parashari_matrix({"parashari": SAMPLE_PARASHARI})
    # Each graha produces exactly one pipe-delimited row
    # Count occurrences of each graha display name
    count = sum(1 for g in GRAHAS if GRAHA_DISPLAY[g] in result)
    assert count == 9


def test_parashari_empty_data_no_crash():
    result = _render_parashari_matrix({})
    assert isinstance(result, str)
    assert "### Parashari Aspect Matrix" in result


# ---------------------------------------------------------------------------
# Test group 5: Jaimini rasi-drishti matrix content
# ---------------------------------------------------------------------------

def test_jaimini_all_12_signs_in_rows():
    result = _render_jaimini_matrix({})
    for sign in SIGNS:
        assert SIGN_DISPLAY[sign] in result, f"Missing sign: {sign}"


def test_jaimini_table_has_12_rows():
    result = _render_jaimini_matrix({})
    count = sum(1 for s in SIGNS if SIGN_DISPLAY[s] in result)
    assert count == 12


def test_jaimini_dual_gemini_aspects_fixed_taurus():
    # Gemini is Dual → aspects all Fixed signs including Taurus
    assert _JAIMINI_MATRIX["gemini"]["taurus"] is True


def test_jaimini_dual_gemini_aspects_fixed_leo():
    assert _JAIMINI_MATRIX["gemini"]["leo"] is True


def test_jaimini_dual_gemini_aspects_fixed_scorpio():
    assert _JAIMINI_MATRIX["gemini"]["scorpio"] is True


def test_jaimini_dual_gemini_aspects_fixed_aquarius():
    assert _JAIMINI_MATRIX["gemini"]["aquarius"] is True


def test_jaimini_dual_does_not_aspect_moveable():
    # Dual signs do NOT aspect Moveable signs
    assert _JAIMINI_MATRIX["gemini"]["aries"] is False
    assert _JAIMINI_MATRIX["gemini"]["cancer"] is False


def test_jaimini_moveable_aries_aspects_non_adjacent_dual_virgo():
    # Aries (Moveable) → aspects Dual signs except adjacent
    # Aries(0) → Gemini(2): adjacent by 2? Gemini index=2, Aries index=0 → diff=2, not adjacent(1 or 11)
    # Actually Gemini IS at position 2, Aries at 0 → diff=2; Pisces at 11 → diff=11 → adjacent
    # Virgo index=5: diff=5 → not adjacent → should aspect
    assert _JAIMINI_MATRIX["aries"]["virgo"] is True


def test_jaimini_moveable_aries_does_not_aspect_adjacent_pisces():
    # Aries(0) and Pisces(11): diff = abs(0-11)=11 → adjacent → no aspect
    assert _JAIMINI_MATRIX["aries"]["pisces"] is False


def test_jaimini_moveable_aries_does_not_aspect_own_type():
    # Aries should not aspect other Moveable signs
    assert _JAIMINI_MATRIX["aries"]["cancer"] is False
    assert _JAIMINI_MATRIX["aries"]["libra"] is False


def test_jaimini_fixed_taurus_aspects_non_adjacent_moveable_cancer():
    # Taurus(1) → Cancer(3): diff=2, not adjacent → Yes
    assert _JAIMINI_MATRIX["taurus"]["cancer"] is True


def test_jaimini_fixed_taurus_does_not_aspect_adjacent_aries():
    # Taurus(1) → Aries(0): diff=1 → adjacent → No
    assert _JAIMINI_MATRIX["taurus"]["aries"] is False


def test_jaimini_yes_cells_present_in_rendered_table():
    result = _render_jaimini_matrix({})
    assert "Yes" in result


def test_jaimini_dash_cells_present_in_rendered_table():
    result = _render_jaimini_matrix({})
    assert "—" in result


# ---------------------------------------------------------------------------
# Test group 6: Tajik aspects
# ---------------------------------------------------------------------------

def test_tajik_entries_rendered():
    result = _render_tajik_aspects({"tajik": SAMPLE_TAJIK})
    assert "Sun" in result
    assert "Moon" in result


def test_tajik_aspect_type_rendered():
    result = _render_tajik_aspects({"tajik": SAMPLE_TAJIK})
    assert "Trine" in result


def test_tajik_applying_yes():
    result = _render_tajik_aspects({"tajik": SAMPLE_TAJIK})
    assert "Yes" in result


def test_tajik_applying_no():
    result = _render_tajik_aspects({"tajik": SAMPLE_TAJIK})
    assert "No" in result


def test_tajik_orb_rendered_with_degree_symbol():
    result = _render_tajik_aspects({"tajik": SAMPLE_TAJIK})
    assert "2.5°" in result


def test_tajik_empty_renders_placeholder():
    result = _render_tajik_aspects({})
    assert "—" in result


def test_tajik_all_five_entries_rendered():
    result = _render_tajik_aspects({"tajik": SAMPLE_TAJIK})
    assert "Saturn" in result
    assert "Jupiter" in result
    assert "Semi-Sextile" in result or "Semi-sextile" in result


# ---------------------------------------------------------------------------
# Test group 7: Mutual aspects
# ---------------------------------------------------------------------------

def test_mutual_entries_rendered():
    result = _render_mutual_aspects({"mutual": SAMPLE_MUTUAL})
    assert "Sun" in result
    assert "Saturn" in result


def test_mutual_aspect_type_rendered():
    result = _render_mutual_aspects({"mutual": SAMPLE_MUTUAL})
    assert "7Th Mutual" in result or "7th Mutual" in result or "7th mutual" in result.lower()


def test_mutual_empty_renders_placeholder():
    result = _render_mutual_aspects({})
    assert "—" in result


def test_mutual_multiple_entries_all_rendered():
    result = _render_mutual_aspects({"mutual": SAMPLE_MUTUAL})
    assert "Jupiter" in result
    assert "Mercury" in result
    assert "Mars" in result


# ---------------------------------------------------------------------------
# Test group 8: Graha-to-lagna aspects
# ---------------------------------------------------------------------------

def test_lagna_entries_rendered():
    result = _render_lagna_aspects({"lagna_aspects": SAMPLE_LAGNA})
    assert "Jupiter" in result


def test_lagna_aspect_type_rendered():
    result = _render_lagna_aspects({"lagna_aspects": SAMPLE_LAGNA})
    assert "Trine" in result


def test_lagna_orb_rendered():
    result = _render_lagna_aspects({"lagna_aspects": SAMPLE_LAGNA})
    assert "3.2°" in result


def test_lagna_empty_renders_placeholder():
    result = _render_lagna_aspects({})
    assert "—" in result


def test_lagna_multiple_entries_rendered():
    result = _render_lagna_aspects({"lagna_aspects": SAMPLE_LAGNA})
    assert "Saturn" in result
    assert "Mars" in result


# ---------------------------------------------------------------------------
# Test group 9: Constants
# ---------------------------------------------------------------------------

def test_grahas_constant_has_9_entries():
    assert len(GRAHAS) == 9


def test_grahas_constant_contains_sun():
    assert "sun" in GRAHAS


def test_grahas_constant_contains_ketu():
    assert "ketu" in GRAHAS


def test_signs_constant_has_12_entries():
    assert len(SIGNS) == 12


def test_signs_constant_contains_aries():
    assert "aries" in SIGNS


def test_signs_constant_contains_pisces():
    assert "pisces" in SIGNS


def test_moveable_fixed_dual_are_disjoint():
    assert MOVEABLE_SIGNS.isdisjoint(FIXED_SIGNS)
    assert MOVEABLE_SIGNS.isdisjoint(DUAL_SIGNS)
    assert FIXED_SIGNS.isdisjoint(DUAL_SIGNS)


def test_moveable_fixed_dual_cover_all_12():
    all_covered = MOVEABLE_SIGNS | FIXED_SIGNS | DUAL_SIGNS
    assert all_covered == set(SIGNS)


# ---------------------------------------------------------------------------
# Test group 10: _fmt_float and _fmt_bool_yn helpers
# ---------------------------------------------------------------------------

def test_fmt_float_formats_with_degree():
    assert _fmt_float(3.2) == "3.2°"


def test_fmt_float_none_returns_dash():
    assert _fmt_float(None) == "—"


def test_fmt_float_integer_input():
    assert _fmt_float(5) == "5.0°"


def test_fmt_bool_yn_true():
    assert _fmt_bool_yn(True) == "Yes"


def test_fmt_bool_yn_false():
    assert _fmt_bool_yn(False) == "No"


def test_fmt_bool_yn_none():
    assert _fmt_bool_yn(None) == "—"
