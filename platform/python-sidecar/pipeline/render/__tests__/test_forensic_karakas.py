"""
Tests for pipeline/render/karakas_renderer.py (F-06)

Coverage (30+ tests):
- Empty chart_output → no crash, returns string
- All 8 chara karaka roles (AK through SK)
- All 8 chara karaka full names in output
- Natural karakas for all 12 houses (classical defaults)
- Natural karakas from chart_output override
- Karakamsa row present with sign + lord
- Swamsa row present with sign + lord
- All 10 special lagnas present in output
- Special lagna fields: longitude, sign, house, lord
- No narration verbs (lint_narration passes)
- Missing data → N/A gracefully
- Longitude formatted as DD°MM'
- Fractional longitude formatted correctly
- Sub-renderer return types
- Constants length checks
- Constants key coverage
"""
import sys
from pathlib import Path

import pytest

# Allow import from python-sidecar root
sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.karakas_renderer import (
    CHARA_KARAKA_ORDER,
    CHARA_KARAKA_FULL_NAMES,
    NATURAL_KARAKAS,
    SPECIAL_LAGNA_ORDER,
    SPECIAL_LAGNA_LABELS,
    render_karakas_section,
    _render_chara_karakas_table,
    _render_natural_karakas_table,
    _render_karakamsa_swamsa_table,
    _render_special_lagnas_table,
    _fmt_degree,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_karaka(graha: str, longitude: float, sign: str) -> dict:
    return {"graha": graha, "longitude": longitude, "sign": sign}


def _make_special_lagna(longitude: float, sign: str, house: int, lord: str) -> dict:
    return {"longitude": longitude, "sign": sign, "house": house, "lord": lord}


FULL_CHARA_KARAKAS: dict = {
    "AK":  _make_karaka("Sun",     315.5,  "Aquarius"),
    "AmK": _make_karaka("Moon",    280.25, "Capricorn"),
    "BK":  _make_karaka("Jupiter", 215.0,  "Scorpio"),
    "MK":  _make_karaka("Venus",   192.75, "Libra"),
    "PK":  _make_karaka("Saturn",  175.5,  "Virgo"),
    "GK":  _make_karaka("Mars",    140.25, "Leo"),
    "DK":  _make_karaka("Mercury", 92.0,   "Cancer"),
    "SK":  _make_karaka("Rahu",    45.5,   "Taurus"),
}

FULL_NATURAL_KARAKAS: dict = {
    "1":  "Sun",
    "2":  "Jupiter",
    "3":  "Mars",
    "4":  "Moon",
    "5":  "Jupiter",
    "6":  "Mars/Saturn",
    "7":  "Venus",
    "8":  "Saturn",
    "9":  "Jupiter/Sun",
    "10": "Mercury/Saturn/Sun",
    "11": "Jupiter",
    "12": "Saturn",
}

FULL_KARAKAMSA: dict = {"sign": "Scorpio", "lord": "Mars"}
FULL_SWAMSA:    dict = {"sign": "Aquarius", "lord": "Saturn"}

FULL_SPECIAL_LAGNAS: dict = {
    "hora_lagna":         _make_special_lagna(200.0,  "Libra",       7,  "Venus"),
    "ghati_lagna":        _make_special_lagna(115.5,  "Cancer",      4,  "Moon"),
    "varnada_lagna":      _make_special_lagna(30.0,   "Taurus",      2,  "Venus"),
    "sree_lagna":         _make_special_lagna(270.25, "Capricorn",   10, "Saturn"),
    "pranapada":          _make_special_lagna(90.0,   "Cancer",      4,  "Moon"),
    "indu_lagna":         _make_special_lagna(155.5,  "Virgo",       6,  "Mercury"),
    "bhava_lagna":        _make_special_lagna(45.75,  "Taurus",      2,  "Venus"),
    "arudha_lagna":       _make_special_lagna(180.0,  "Libra",       7,  "Venus"),
    "shri_lagna":         _make_special_lagna(60.0,   "Gemini",      3,  "Mercury"),
    "bhrigu_bindu_lagna": _make_special_lagna(120.0,  "Leo",         5,  "Sun"),
}

FULL_CHART_OUTPUT: dict = {
    "chara_karakas":  FULL_CHARA_KARAKAS,
    "natural_karakas": FULL_NATURAL_KARAKAS,
    "karakamsa":      FULL_KARAKAMSA,
    "swamsa":         FULL_SWAMSA,
    "special_lagnas": FULL_SPECIAL_LAGNAS,
}


# ---------------------------------------------------------------------------
# Tests — empty input
# ---------------------------------------------------------------------------

class TestEmptyInput:
    def test_empty_chart_output_returns_string(self):
        result = render_karakas_section({})
        assert isinstance(result, str)

    def test_empty_chart_output_no_crash(self):
        render_karakas_section({})  # must not raise

    def test_empty_chart_output_no_narration(self):
        result = render_karakas_section({})
        lint_narration(result, "karakas")  # must not raise

    def test_empty_chara_karakas_returns_string(self):
        result = render_karakas_section({"chara_karakas": {}})
        assert isinstance(result, str)

    def test_empty_special_lagnas_returns_string(self):
        result = render_karakas_section({"special_lagnas": {}})
        assert isinstance(result, str)

    def test_empty_input_contains_na(self):
        result = render_karakas_section({})
        assert "N/A" in result

    def test_empty_karakamsa_gives_na(self):
        result = _render_karakamsa_swamsa_table({}, {})
        assert "N/A" in result

    def test_empty_swamsa_gives_na(self):
        result = _render_karakamsa_swamsa_table({}, {})
        assert "N/A" in result


# ---------------------------------------------------------------------------
# Tests — full data / structure
# ---------------------------------------------------------------------------

class TestFullData:
    def test_returns_string(self):
        assert isinstance(render_karakas_section(FULL_CHART_OUTPUT), str)

    def test_no_narration_verbs(self):
        result = render_karakas_section(FULL_CHART_OUTPUT)
        lint_narration(result, "karakas")

    def test_chara_karakas_section_header_present(self):
        result = render_karakas_section(FULL_CHART_OUTPUT)
        assert "### Chara Karakas" in result

    def test_natural_karakas_section_header_present(self):
        result = render_karakas_section(FULL_CHART_OUTPUT)
        assert "### Natural Karakas" in result

    def test_karakamsa_swamsa_section_header_present(self):
        result = render_karakas_section(FULL_CHART_OUTPUT)
        assert "### Karakamsa and Swamsa" in result

    def test_special_lagnas_section_header_present(self):
        result = render_karakas_section(FULL_CHART_OUTPUT)
        assert "### Special Lagnas" in result

    def test_all_8_karaka_roles_in_output(self):
        result = _render_chara_karakas_table(FULL_CHARA_KARAKAS)
        for role in CHARA_KARAKA_ORDER:
            assert role in result, f"Karaka role '{role}' missing from output"

    def test_all_8_karaka_full_names_in_output(self):
        result = _render_chara_karakas_table(FULL_CHARA_KARAKAS)
        for role, name in CHARA_KARAKA_FULL_NAMES.items():
            assert name in result, f"Karaka full name '{name}' missing from output"

    def test_all_12_natural_karaka_houses_in_output(self):
        result = _render_natural_karakas_table(FULL_NATURAL_KARAKAS)
        for i in range(1, 13):
            assert f"| {i} |" in result, f"House {i} missing from natural karakas table"

    def test_karakamsa_sign_in_output(self):
        result = _render_karakamsa_swamsa_table(FULL_KARAKAMSA, FULL_SWAMSA)
        assert "Scorpio" in result

    def test_karakamsa_lord_in_output(self):
        result = _render_karakamsa_swamsa_table(FULL_KARAKAMSA, FULL_SWAMSA)
        assert "Mars" in result

    def test_swamsa_sign_in_output(self):
        result = _render_karakamsa_swamsa_table(FULL_KARAKAMSA, FULL_SWAMSA)
        assert "Aquarius" in result

    def test_swamsa_lord_in_output(self):
        result = _render_karakamsa_swamsa_table(FULL_KARAKAMSA, FULL_SWAMSA)
        assert "Saturn" in result

    def test_karakamsa_row_label_present(self):
        result = _render_karakamsa_swamsa_table(FULL_KARAKAMSA, FULL_SWAMSA)
        assert "Karakamsa" in result

    def test_swamsa_row_label_present(self):
        result = _render_karakamsa_swamsa_table(FULL_KARAKAMSA, FULL_SWAMSA)
        assert "Swamsa" in result

    def test_all_10_special_lagnas_in_output(self):
        result = _render_special_lagnas_table(FULL_SPECIAL_LAGNAS)
        for key in SPECIAL_LAGNA_ORDER:
            label = SPECIAL_LAGNA_LABELS[key]
            # Use the base label (strip parenthetical for Arudha Lagna)
            base = label.split(" (")[0]
            assert base in result, f"Special lagna '{label}' missing from output"

    def test_special_lagna_longitude_formatted(self):
        """hora_lagna longitude=200.0 → 200°00'."""
        result = _render_special_lagnas_table(FULL_SPECIAL_LAGNAS)
        assert "200°00'" in result

    def test_special_lagna_fractional_longitude_formatted(self):
        """ghati_lagna longitude=115.5 → 115°30'."""
        result = _render_special_lagnas_table(FULL_SPECIAL_LAGNAS)
        assert "115°30'" in result

    def test_special_lagna_sign_present(self):
        result = _render_special_lagnas_table(FULL_SPECIAL_LAGNAS)
        assert "Libra" in result  # hora_lagna sign

    def test_special_lagna_house_present(self):
        result = _render_special_lagnas_table(FULL_SPECIAL_LAGNAS)
        assert "| 7 |" in result or "7" in result  # hora_lagna house=7

    def test_special_lagna_lord_present(self):
        result = _render_special_lagnas_table(FULL_SPECIAL_LAGNAS)
        assert "Venus" in result  # hora_lagna lord

    def test_chara_karaka_graha_rendered(self):
        result = _render_chara_karakas_table(FULL_CHARA_KARAKAS)
        assert "Sun" in result  # AK graha

    def test_chara_karaka_longitude_formatted(self):
        """AK longitude=315.5 → 315°30'."""
        result = _render_chara_karakas_table(FULL_CHARA_KARAKAS)
        assert "315°30'" in result

    def test_chara_karaka_sign_rendered(self):
        result = _render_chara_karakas_table(FULL_CHARA_KARAKAS)
        assert "Aquarius" in result  # AK sign

    def test_natural_karakas_classical_defaults_used_when_empty(self):
        """When no natural_karakas in chart_output, classical defaults fill in."""
        result = _render_natural_karakas_table({})
        assert "Sun" in result      # house 1
        assert "Jupiter" in result  # house 2, 5, 11
        assert "Saturn" in result   # house 8, 12

    def test_natural_karakas_override_from_chart_output(self):
        """chart_output natural_karakas overrides canonical defaults."""
        custom = {str(i): "TestKaraka" for i in range(1, 13)}
        result = _render_natural_karakas_table(custom)
        assert "TestKaraka" in result


# ---------------------------------------------------------------------------
# Tests — missing / partial data
# ---------------------------------------------------------------------------

class TestMissingData:
    def test_missing_karaka_role_gives_na(self):
        """Missing AK entry → N/A for graha/longitude/sign."""
        partial = {k: v for k, v in FULL_CHARA_KARAKAS.items() if k != "AK"}
        result = _render_chara_karakas_table(partial)
        assert "Atmakaraka" in result  # row still rendered
        assert "N/A" in result

    def test_missing_graha_gives_na(self):
        karakas = {"AK": {"longitude": 315.5, "sign": "Aquarius"}}
        result = _render_chara_karakas_table(karakas)
        assert "N/A" in result

    def test_missing_longitude_gives_na(self):
        karakas = {"AK": {"graha": "Sun", "sign": "Aquarius"}}
        result = _render_chara_karakas_table(karakas)
        assert "N/A" in result

    def test_missing_sign_gives_na(self):
        karakas = {"AK": {"graha": "Sun", "longitude": 315.5}}
        result = _render_chara_karakas_table(karakas)
        assert "N/A" in result

    def test_missing_special_lagna_gives_na(self):
        partial = {k: v for k, v in FULL_SPECIAL_LAGNAS.items() if k != "hora_lagna"}
        result = _render_special_lagnas_table(partial)
        assert "Hora Lagna" in result
        assert "N/A" in result

    def test_missing_special_lagna_house_gives_na(self):
        lagnas = {"hora_lagna": {"longitude": 200.0, "sign": "Libra", "lord": "Venus"}}
        result = _render_special_lagnas_table(lagnas)
        assert "N/A" in result

    def test_missing_special_lagna_lord_gives_na(self):
        lagnas = {"hora_lagna": {"longitude": 200.0, "sign": "Libra", "house": 7}}
        result = _render_special_lagnas_table(lagnas)
        assert "N/A" in result

    def test_no_narration_on_partial_data(self):
        partial = {
            "chara_karakas": {"AK": {"graha": "Sun", "longitude": 315.5}},
        }
        result = render_karakas_section(partial)
        lint_narration(result, "karakas")

    def test_degree_key_fallback_for_longitude(self):
        """'degree' key used when 'longitude' is absent."""
        karakas = {"AK": {"graha": "Sun", "degree": 315.5, "sign": "Aquarius"}}
        result = _render_chara_karakas_table(karakas)
        assert "315°30'" in result


# ---------------------------------------------------------------------------
# Tests — _fmt_degree helper
# ---------------------------------------------------------------------------

class TestFmtDegree:
    def test_round_degree(self):
        assert _fmt_degree(10.0) == "10°00'"

    def test_fractional_half_degree(self):
        assert _fmt_degree(10.5) == "10°30'"

    def test_zero(self):
        assert _fmt_degree(0.0) == "0°00'"

    def test_none_returns_na(self):
        assert _fmt_degree(None) == "N/A"

    def test_string_float(self):
        assert _fmt_degree("15.75") == "15°45'"

    def test_invalid_string_returns_na(self):
        assert _fmt_degree("abc") == "N/A"

    def test_large_longitude(self):
        assert _fmt_degree(330.0) == "330°00'"

    def test_fractional_degree_18_min(self):
        # 42.3 → 42 + 0.3*60 = 42 + 18 → 42°18'
        assert _fmt_degree(42.3) == "42°18'"


# ---------------------------------------------------------------------------
# Tests — constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_chara_karaka_order_has_8_entries(self):
        assert len(CHARA_KARAKA_ORDER) == 8

    def test_chara_karaka_order_starts_with_ak(self):
        assert CHARA_KARAKA_ORDER[0] == "AK"

    def test_chara_karaka_order_ends_with_sk(self):
        assert CHARA_KARAKA_ORDER[-1] == "SK"

    def test_chara_karaka_full_names_has_8_entries(self):
        assert len(CHARA_KARAKA_FULL_NAMES) == 8

    def test_chara_karaka_full_names_covers_all_roles(self):
        for role in CHARA_KARAKA_ORDER:
            assert role in CHARA_KARAKA_FULL_NAMES, f"Missing full name for role '{role}'"

    def test_atmakaraka_full_name(self):
        assert CHARA_KARAKA_FULL_NAMES["AK"] == "Atmakaraka"

    def test_darakaraka_full_name(self):
        assert CHARA_KARAKA_FULL_NAMES["DK"] == "Darakaraka"

    def test_natural_karakas_covers_all_12_houses(self):
        for i in range(1, 13):
            assert str(i) in NATURAL_KARAKAS, f"House {i} missing from NATURAL_KARAKAS"

    def test_natural_karakas_house1_is_sun(self):
        assert NATURAL_KARAKAS["1"] == "Sun"

    def test_natural_karakas_house7_is_venus(self):
        assert NATURAL_KARAKAS["7"] == "Venus"

    def test_special_lagna_order_has_10_entries(self):
        assert len(SPECIAL_LAGNA_ORDER) == 10

    def test_special_lagna_labels_covers_all_lagnas(self):
        for key in SPECIAL_LAGNA_ORDER:
            assert key in SPECIAL_LAGNA_LABELS, f"Missing label for '{key}'"

    def test_hora_lagna_label(self):
        assert SPECIAL_LAGNA_LABELS["hora_lagna"] == "Hora Lagna"

    def test_arudha_lagna_label_contains_al(self):
        assert "AL" in SPECIAL_LAGNA_LABELS["arudha_lagna"]

    def test_bhrigu_bindu_lagna_label(self):
        assert "Bhrigu Bindu" in SPECIAL_LAGNA_LABELS["bhrigu_bindu_lagna"]


# ---------------------------------------------------------------------------
# Tests — sub-renderer return types
# ---------------------------------------------------------------------------

class TestSubRenderers:
    def test_render_chara_karakas_table_returns_string_empty(self):
        assert isinstance(_render_chara_karakas_table({}), str)

    def test_render_chara_karakas_table_returns_string_full(self):
        assert isinstance(_render_chara_karakas_table(FULL_CHARA_KARAKAS), str)

    def test_render_natural_karakas_table_returns_string_empty(self):
        assert isinstance(_render_natural_karakas_table({}), str)

    def test_render_natural_karakas_table_returns_string_full(self):
        assert isinstance(_render_natural_karakas_table(FULL_NATURAL_KARAKAS), str)

    def test_render_karakamsa_swamsa_table_returns_string(self):
        assert isinstance(_render_karakamsa_swamsa_table({}, {}), str)

    def test_render_special_lagnas_table_returns_string_empty(self):
        assert isinstance(_render_special_lagnas_table({}), str)

    def test_render_special_lagnas_table_returns_string_full(self):
        assert isinstance(_render_special_lagnas_table(FULL_SPECIAL_LAGNAS), str)

    def test_chara_karakas_table_has_header_row(self):
        result = _render_chara_karakas_table({})
        assert "| Role |" in result

    def test_natural_karakas_table_has_header_row(self):
        result = _render_natural_karakas_table({})
        assert "| House |" in result

    def test_karakamsa_swamsa_table_has_header_row(self):
        result = _render_karakamsa_swamsa_table({}, {})
        assert "| Point |" in result

    def test_special_lagnas_table_has_header_row(self):
        result = _render_special_lagnas_table({})
        assert "| Lagna |" in result

    def test_full_render_no_narration(self):
        result = render_karakas_section(FULL_CHART_OUTPUT)
        lint_narration(result, "karakas")
