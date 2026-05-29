"""
Tests for pipeline/render/upagrahas_renderer.py (F-04)

Coverage (25 tests):
- Empty chart_output → no crash, returns string
- All 7 upagraha names appear in output
- Mrityu Sahama appears in output
- No narration verbs (lint_narration passes)
- Day/night variants render when present
- Missing upagraha → N/A gracefully
- House column present
- BPHS reference line present
- Saturn-derived section header present
- Longitude formatted as DD°MM'
- Nakshatra + pada render when present
- Missing nakshatra → N/A
- Missing pada → N/A
- Missing house → N/A
- Missing sign → N/A
- Partial upagrahas dict → no crash
- Constants length checks (UPAGRAHAS, SATURN_DERIVED, labels)
- Day-birth formula value renders when present
- Night-birth formula value renders when present
- Day/night absent → N/A
- _render_upagrahas_table returns string
- _render_saturn_derived_table returns string
- No narration on partial data
- All BPHS refs appear in output
- Upagraha section header present
"""
import sys
from pathlib import Path

import pytest

# Allow import from python-sidecar root
sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.upagrahas_renderer import (
    UPAGRAHAS,
    SATURN_DERIVED,
    UPAGRAHA_LABELS,
    SATURN_DERIVED_LABELS,
    BPHS_REFS,
    render_upagrahas_section,
    _render_upagrahas_table,
    _render_saturn_derived_table,
    _fmt_degree,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_upagraha(
    sign: str = "Sagittarius",
    degree: float = 10.5,
    nakshatra: str = "Purva Ashadha",
    pada: int = 2,
    house: int = 9,
    day_birth_value: float = 10.5,
    night_birth_value: float = 20.2,
) -> dict:
    return {
        "longitude": degree,
        "sign": sign,
        "nakshatra": nakshatra,
        "pada": pada,
        "degree": degree,
        "house": house,
        "day_birth_value": day_birth_value,
        "night_birth_value": night_birth_value,
    }


FULL_UPAGRAHAS: dict = {
    "gulika": _make_upagraha("Sagittarius", 10.5,  "Purva Ashadha",  2, 9,  10.5,  20.2),
    "maandi": _make_upagraha("Capricorn",   15.0,  "Shravana",       3, 10, 15.0,  25.5),
    "dhuma":  _make_upagraha("Aries",       5.75,  "Ashwini",        1, 1,  5.75,  35.75),
    "vyatipata": _make_upagraha("Libra",    24.3,  "Vishakha",       4, 7,  24.3,  54.3),
    "parivesha": _make_upagraha("Pisces",   18.0,  "Revati",         1, 12, 18.0,  48.0),
    "indrachapa": _make_upagraha("Gemini",   2.0,  "Mrigashira",     2, 3,   2.0,  32.0),
    "upaketu":   _make_upagraha("Virgo",   12.25,  "Hasta",          3, 6,  12.25, 42.25),
    "mrityu_sahama": {
        "longitude": 195.5,
        "sign": "Libra",
        "nakshatra": "Chitra",
        "pada": 3,
        "degree": 15.5,
        "house": 7,
    },
}

FULL_CHART_OUTPUT: dict = {"upagrahas": FULL_UPAGRAHAS}


# ---------------------------------------------------------------------------
# Tests — empty input
# ---------------------------------------------------------------------------

class TestEmptyInput:
    def test_empty_chart_output_returns_string(self):
        result = render_upagrahas_section({})
        assert isinstance(result, str)

    def test_empty_chart_output_no_crash(self):
        render_upagrahas_section({})  # must not raise

    def test_empty_chart_output_no_narration(self):
        result = render_upagrahas_section({})
        lint_narration(result, "upagrahas")  # must not raise

    def test_empty_upagrahas_dict_returns_string(self):
        result = render_upagrahas_section({"upagrahas": {}})
        assert isinstance(result, str)

    def test_empty_upagrahas_dict_no_crash(self):
        render_upagrahas_section({"upagrahas": {}})

    def test_empty_input_all_na(self):
        result = render_upagrahas_section({})
        assert "N/A" in result


# ---------------------------------------------------------------------------
# Tests — full data / all names present
# ---------------------------------------------------------------------------

class TestFullData:
    def test_returns_string(self):
        assert isinstance(render_upagrahas_section(FULL_CHART_OUTPUT), str)

    def test_no_narration_verbs(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        lint_narration(result, "upagrahas")

    def test_all_7_upagraha_labels_in_output(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        for key in UPAGRAHAS:
            label = UPAGRAHA_LABELS[key]
            assert label in result, f"Upagraha label '{label}' missing from output"

    def test_mrityu_sahama_in_output(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        assert "Mrityu Sahama" in result

    def test_upagraha_section_header_present(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        assert "### Upagrahas" in result

    def test_saturn_derived_section_header_present(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        assert "Saturn-Derived Points" in result

    def test_house_column_in_upagrahas_table(self):
        result = _render_upagrahas_table(FULL_UPAGRAHAS)
        assert "House" in result

    def test_house_column_in_saturn_derived_table(self):
        result = _render_saturn_derived_table(FULL_UPAGRAHAS)
        assert "House" in result

    def test_bphs_formula_source_line_present(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        assert "BPHS Ch 4" in result

    def test_day_birth_formula_column_present(self):
        result = _render_upagrahas_table(FULL_UPAGRAHAS)
        assert "Day-Birth Formula" in result

    def test_night_birth_formula_column_present(self):
        result = _render_upagrahas_table(FULL_UPAGRAHAS)
        assert "Night-Birth Formula" in result

    def test_day_birth_value_renders(self):
        """Gulika day_birth_value=10.5 → 10°30' in output."""
        result = _render_upagrahas_table(FULL_UPAGRAHAS)
        assert "10°30'" in result

    def test_night_birth_value_renders(self):
        """Gulika night_birth_value=20.2 → 20°12' in output."""
        result = _render_upagrahas_table(FULL_UPAGRAHAS)
        assert "20°12'" in result

    def test_nakshatra_rendered(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        assert "Purva Ashadha" in result

    def test_pada_rendered(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        # Gulika pada=2 appears in the table cell
        assert "2" in result

    def test_house_number_rendered(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        assert "9" in result  # Gulika house=9

    def test_sign_rendered(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        assert "Sagittarius" in result

    def test_mrityu_sahama_sign_rendered(self):
        result = render_upagrahas_section(FULL_CHART_OUTPUT)
        assert "Chitra" in result  # nakshatra for mrityu_sahama

    def test_bphs_ref_in_upagrahas_table(self):
        result = _render_upagrahas_table(FULL_UPAGRAHAS)
        # Check that at least one BPHS Ch 4 ref is present
        assert "Ch 4, v 33-36" in result
        assert "Ch 4, v 37-38" in result


# ---------------------------------------------------------------------------
# Tests — missing / partial data
# ---------------------------------------------------------------------------

class TestMissingData:
    def test_missing_upagraha_key_gives_na(self):
        """A missing upagraha key → N/A for all its fields."""
        partial = {k: v for k, v in FULL_UPAGRAHAS.items() if k != "dhuma"}
        result = _render_upagrahas_table(partial)
        # Dhuma row should still appear (with N/A values)
        assert "Dhuma" in result
        assert "N/A" in result

    def test_missing_nakshatra_gives_na(self):
        upagrahas = {
            "gulika": {"sign": "Aries", "degree": 5.0, "house": 1}
        }
        result = _render_upagrahas_table(upagrahas)
        assert "N/A" in result

    def test_missing_pada_gives_na(self):
        upagrahas = {
            "gulika": {"sign": "Aries", "degree": 5.0, "house": 1,
                       "nakshatra": "Ashwini"}
        }
        result = _render_upagrahas_table(upagrahas)
        # pada cell should be N/A
        assert "N/A" in result

    def test_missing_sign_gives_na(self):
        upagrahas = {"gulika": {"degree": 5.0, "house": 1}}
        result = _render_upagrahas_table(upagrahas)
        assert "N/A" in result

    def test_missing_house_gives_na(self):
        upagrahas = {"gulika": {"sign": "Aries", "degree": 5.0}}
        result = _render_upagrahas_table(upagrahas)
        assert "N/A" in result

    def test_missing_day_birth_value_gives_na(self):
        upagrahas = {"gulika": {"sign": "Aries", "degree": 5.0, "house": 1,
                                "night_birth_value": 35.0}}
        result = _render_upagrahas_table(upagrahas)
        assert "N/A" in result

    def test_missing_night_birth_value_gives_na(self):
        upagrahas = {"gulika": {"sign": "Aries", "degree": 5.0, "house": 1,
                                "day_birth_value": 5.0}}
        result = _render_upagrahas_table(upagrahas)
        assert "N/A" in result

    def test_missing_mrityu_sahama_gives_na(self):
        partial = {k: v for k, v in FULL_UPAGRAHAS.items()
                   if k != "mrityu_sahama"}
        result = _render_saturn_derived_table(partial)
        assert "Mrityu Sahama" in result
        assert "N/A" in result

    def test_no_narration_on_partial_data(self):
        partial = {"upagrahas": {"gulika": {"sign": "Aries", "degree": 5.0}}}
        result = render_upagrahas_section(partial)
        lint_narration(result, "upagrahas")


# ---------------------------------------------------------------------------
# Tests — _fmt_degree helper
# ---------------------------------------------------------------------------

class TestFmtDegree:
    def test_round_degree(self):
        assert _fmt_degree(10.0) == "10°00'"

    def test_fractional_degree(self):
        assert _fmt_degree(10.5) == "10°30'"

    def test_zero(self):
        assert _fmt_degree(0.0) == "0°00'"

    def test_none_returns_na(self):
        assert _fmt_degree(None) == "N/A"

    def test_string_float(self):
        assert _fmt_degree("15.75") == "15°45'"

    def test_invalid_returns_na(self):
        assert _fmt_degree("abc") == "N/A"


# ---------------------------------------------------------------------------
# Tests — constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_upagrahas_length(self):
        assert len(UPAGRAHAS) == 7

    def test_saturn_derived_length(self):
        assert len(SATURN_DERIVED) == 1

    def test_upagraha_labels_keys_match_upagrahas(self):
        assert set(UPAGRAHA_LABELS.keys()) == set(UPAGRAHAS)

    def test_saturn_derived_labels_keys_match(self):
        assert set(SATURN_DERIVED_LABELS.keys()) == set(SATURN_DERIVED)

    def test_bphs_refs_covers_all_upagrahas(self):
        for key in UPAGRAHAS:
            assert key in BPHS_REFS, f"BPHS_REFS missing entry for '{key}'"

    def test_bphs_refs_covers_saturn_derived(self):
        for key in SATURN_DERIVED:
            assert key in BPHS_REFS, f"BPHS_REFS missing entry for '{key}'"

    def test_gulika_label(self):
        assert "Gulika" in UPAGRAHA_LABELS["gulika"]
        assert "Mandi" in UPAGRAHA_LABELS["gulika"]

    def test_indrachapa_label(self):
        assert "Indrachapa" in UPAGRAHA_LABELS["indrachapa"]

    def test_mrityu_sahama_label(self):
        assert "Mrityu Sahama" in SATURN_DERIVED_LABELS["mrityu_sahama"]


# ---------------------------------------------------------------------------
# Tests — sub-renderer return types
# ---------------------------------------------------------------------------

class TestSubRenderers:
    def test_render_upagrahas_table_returns_string(self):
        assert isinstance(_render_upagrahas_table({}), str)

    def test_render_saturn_derived_table_returns_string(self):
        assert isinstance(_render_saturn_derived_table({}), str)

    def test_render_upagrahas_table_full_returns_string(self):
        assert isinstance(_render_upagrahas_table(FULL_UPAGRAHAS), str)

    def test_render_saturn_derived_table_full_returns_string(self):
        assert isinstance(_render_saturn_derived_table(FULL_UPAGRAHAS), str)
