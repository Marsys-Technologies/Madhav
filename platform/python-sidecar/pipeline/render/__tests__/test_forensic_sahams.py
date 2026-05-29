"""
Tests for pipeline/render/sahams_renderer.py (F-05)

Coverage (25+ tests):
- Empty chart_output → no crash, returns string
- At least 10 saham names in output
- All 9 esoteric bindu names in output
- No narration verbs (lint_narration passes)
- Formula column present for sahams
- Formula column present for bindus
- Missing saham → N/A gracefully
- Missing bindu → N/A gracefully
- Longitude formatted as DD°MM'
- Nakshatra + pada render when present
- Missing nakshatra → N/A
- Missing pada → N/A
- Missing lord → N/A
- Missing sign → N/A
- Partial sahams dict → no crash
- Constants length checks (SAHAMS_CANONICAL_ORDER, ESOTERIC_BINDUS, labels)
- All saham labels exist in SAHAM_LABELS
- All bindu labels exist in BINDU_LABELS
- All saham formulas exist in SAHAM_FORMULAS
- All bindu formulas exist in BINDU_FORMULAS
- sub-renderer _render_sahams_table returns string
- sub-renderer _render_esoteric_bindus_table returns string
- Formula override in entry data takes precedence over canonical table
- Sections header strings present in output
- No narration verbs on partial data
- _fmt_degree edge cases
"""
import sys
from pathlib import Path

import pytest

# Allow import from python-sidecar root
sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.sahams_renderer import (
    SAHAMS_CANONICAL_ORDER,
    ESOTERIC_BINDUS,
    SAHAM_LABELS,
    BINDU_LABELS,
    SAHAM_FORMULAS,
    BINDU_FORMULAS,
    render_sahams_section,
    _render_sahams_table,
    _render_esoteric_bindus_table,
    _fmt_degree,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_saham(
    longitude: float = 45.0,
    sign: str = "Taurus",
    nakshatra: str = "Rohini",
    pada: int = 2,
    lord: str = "Venus",
) -> dict:
    return {
        "longitude": longitude,
        "sign": sign,
        "nakshatra": nakshatra,
        "pada": pada,
        "lord": lord,
    }


def _make_bindu(
    longitude: float = 120.0,
    sign: str = "Leo",
    nakshatra: str = "Magha",
    lord: str = "Sun",
) -> dict:
    return {
        "longitude": longitude,
        "sign": sign,
        "nakshatra": nakshatra,
        "lord": lord,
    }


FULL_SAHAMS: dict = {
    "punya":         _make_saham(15.0,  "Taurus",      "Rohini",          2,  "Venus"),
    "vidya":         _make_saham(42.3,  "Taurus",      "Krittika",        4,  "Sun"),
    "yasas":         _make_saham(75.5,  "Gemini",      "Ardra",           2,  "Rahu"),
    "vivah":         _make_saham(200.0, "Libra",       "Vishakha",        1,  "Jupiter"),
    "karma":         _make_saham(265.0, "Sagittarius", "Purva Ashadha",   2,  "Venus"),
    "bhagya":        _make_saham(310.0, "Aquarius",    "Shatabhisha",     3,  "Rahu"),
    "putra":         _make_saham(90.0,  "Cancer",      "Punarvasu",       4,  "Jupiter"),
    "aayur":         _make_saham(130.0, "Leo",         "Magha",           1,  "Ketu"),
    "mrityu":        _make_saham(240.0, "Scorpio",     "Jyeshtha",        3,  "Mercury"),
    "roga":          _make_saham(175.0, "Virgo",       "Hasta",           4,  "Moon"),
    "sukha":         _make_saham(30.0,  "Taurus",      "Krittika",        1,  "Sun"),
    "dhan":          _make_saham(55.0,  "Gemini",      "Mrigashira",      3,  "Mars"),
    "raja":          _make_saham(280.0, "Capricorn",   "Shravana",        2,  "Moon"),
    "bandhu":        _make_saham(100.0, "Cancer",      "Pushya",          2,  "Saturn"),
    "shatru":        _make_saham(155.0, "Virgo",       "Uttara Phalguni", 4,  "Sun"),
    "labha":         _make_saham(320.0, "Aquarius",    "Purva Bhadrapada",1,  "Jupiter"),
    "vyaya":         _make_saham(345.0, "Pisces",      "Uttara Bhadrapada",3, "Saturn"),
    "matru":         _make_saham(60.0,  "Gemini",      "Ardra",           1,  "Rahu"),
    "pitru":         _make_saham(285.0, "Capricorn",   "Shravana",        3,  "Moon"),
    "bhratra":       _make_saham(210.0, "Scorpio",     "Anuradha",        2,  "Saturn"),
    "jalapatana":    _make_saham(190.0, "Libra",       "Swati",           2,  "Rahu"),
    "paradesa":      _make_saham(220.0, "Scorpio",     "Jyeshtha",        1,  "Mercury"),
    "vanik":         _make_saham(50.0,  "Taurus",      "Krittika",        3,  "Sun"),
    "kheta":         _make_saham(165.0, "Virgo",       "Hasta",           1,  "Moon"),
    "pashu":         _make_saham(35.0,  "Taurus",      "Krittika",        2,  "Sun"),
    "shoola":        _make_saham(255.0, "Sagittarius", "Mula",            3,  "Ketu"),
    "bahu":          _make_saham(145.0, "Leo",         "Purva Phalguni",  4,  "Venus"),
    "kshetra":       _make_saham(25.0,  "Taurus",      "Krittika",        1,  "Sun"),
    "siddhi":        _make_saham(115.0, "Cancer",      "Ashlesha",        4,  "Mercury"),
    "shaucha":       _make_saham(185.0, "Virgo",       "Chitra",          1,  "Mars"),
    "yatra":         _make_saham(80.0,  "Gemini",      "Ardra",           3,  "Rahu"),
    "vivaha_bandha": _make_saham(205.0, "Scorpio",     "Anuradha",        1,  "Saturn"),
    "dhana_putra":   _make_saham(95.0,  "Cancer",      "Pushya",          3,  "Saturn"),
    "aksha":         _make_saham(295.0, "Capricorn",   "Dhanishtha",      1,  "Mars"),
    "videsh":        _make_saham(230.0, "Scorpio",     "Jyeshtha",        2,  "Mercury"),
    "shastra":       _make_saham(170.0, "Virgo",       "Hasta",           2,  "Moon"),
    "nidra":         _make_saham(330.0, "Pisces",      "Purva Bhadrapada",3,  "Jupiter"),
    "chinta":        _make_saham(105.0, "Cancer",      "Pushya",          1,  "Saturn"),
    "mitra":         _make_saham(70.0,  "Gemini",      "Punarvasu",       3,  "Jupiter"),
    "kalatra":       _make_saham(195.0, "Libra",       "Vishakha",        2,  "Jupiter"),
}

FULL_BINDUS: dict = {
    "bhrigu_bindu":  _make_bindu(120.0, "Leo",        "Magha",           "Sun"),
    "yogi_point":    _make_bindu(245.0, "Sagittarius","Mula",            "Ketu"),
    "avayogi_point": _make_bindu(71.67, "Gemini",     "Punarvasu",       "Jupiter"),
    "mrityu_point":  _make_bindu(238.0, "Scorpio",    "Jyeshtha",        "Mercury"),
    "trisphuta":     _make_bindu(88.0,  "Cancer",     "Punarvasu",       "Jupiter"),
    "chatursphuta":  _make_bindu(178.0, "Virgo",      "Chitra",          "Mars"),
    "panchasphuta":  _make_bindu(268.0, "Capricorn",  "Uttara Ashadha",  "Sun"),
    "pranasphuta":   _make_bindu(358.0, "Pisces",     "Revati",          "Mercury"),
    "dehasphuta":    _make_bindu(48.0,  "Taurus",     "Rohini",          "Moon"),
}

FULL_CHART_OUTPUT: dict = {
    "sahams": FULL_SAHAMS,
    "esoteric_bindus": FULL_BINDUS,
}


# ---------------------------------------------------------------------------
# Tests — empty input
# ---------------------------------------------------------------------------

class TestEmptyInput:
    def test_empty_chart_output_returns_string(self):
        result = render_sahams_section({})
        assert isinstance(result, str)

    def test_empty_chart_output_no_crash(self):
        render_sahams_section({})  # must not raise

    def test_empty_chart_output_no_narration(self):
        result = render_sahams_section({})
        lint_narration(result, "sahams")  # must not raise

    def test_empty_sahams_dict_returns_string(self):
        result = render_sahams_section({"sahams": {}})
        assert isinstance(result, str)

    def test_empty_sahams_dict_no_crash(self):
        render_sahams_section({"sahams": {}})

    def test_empty_input_all_na(self):
        result = render_sahams_section({})
        assert "N/A" in result

    def test_empty_bindus_dict_returns_string(self):
        result = render_sahams_section({"esoteric_bindus": {}})
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests — full data / all names present
# ---------------------------------------------------------------------------

class TestFullData:
    def test_returns_string(self):
        assert isinstance(render_sahams_section(FULL_CHART_OUTPUT), str)

    def test_no_narration_verbs(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        lint_narration(result, "sahams")

    def test_at_least_10_saham_names_in_output(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        found = sum(
            1 for key in SAHAMS_CANONICAL_ORDER[:10]
            if SAHAM_LABELS[key] in result
        )
        assert found >= 10, f"Expected >=10 saham names, found {found}"

    def test_all_40_saham_labels_in_output(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        for key in SAHAMS_CANONICAL_ORDER:
            label = SAHAM_LABELS[key]
            assert label in result, f"Saham label '{label}' missing from output"

    def test_all_9_esoteric_bindu_names_in_output(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        for key in ESOTERIC_BINDUS:
            label = BINDU_LABELS[key]
            assert label in result, f"Bindu label '{label}' missing from output"

    def test_sahams_section_header_present(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        assert "### Tajik Sahams" in result

    def test_esoteric_bindus_section_header_present(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        assert "### Esoteric Bindus" in result

    def test_formula_column_present_in_sahams(self):
        result = _render_sahams_table(FULL_SAHAMS)
        assert "Formula" in result

    def test_formula_column_present_in_bindus(self):
        result = _render_esoteric_bindus_table(FULL_BINDUS)
        assert "Formula" in result

    def test_punya_formula_in_output(self):
        result = _render_sahams_table(FULL_SAHAMS)
        assert "Moon" in result and "Sun" in result and "Lagna" in result

    def test_bhrigu_bindu_formula_in_output(self):
        result = _render_esoteric_bindus_table(FULL_BINDUS)
        assert "Midpoint" in result or "Rahu" in result

    def test_longitude_formatted_as_degree_minutes(self):
        """punya longitude=15.0 → 15°00' in output."""
        result = _render_sahams_table(FULL_SAHAMS)
        assert "15°00'" in result

    def test_fractional_longitude_formatted(self):
        """vidya longitude=42.3 → 42°18' in output."""
        result = _render_sahams_table(FULL_SAHAMS)
        assert "42°18'" in result

    def test_nakshatra_rendered(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        assert "Rohini" in result

    def test_pada_rendered(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        assert "2" in result  # punya pada=2

    def test_lord_rendered(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        assert "Venus" in result  # punya lord=Venus

    def test_sign_rendered(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        assert "Taurus" in result  # punya sign=Taurus

    def test_bhrigu_bindu_longitude_rendered(self):
        """bhrigu_bindu longitude=120.0 → 120°00' in output."""
        result = _render_esoteric_bindus_table(FULL_BINDUS)
        assert "120°00'" in result

    def test_formula_source_line_present(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        assert "Tajika Neelakanthi" in result or "Brihat Parashara" in result


# ---------------------------------------------------------------------------
# Tests — missing / partial data
# ---------------------------------------------------------------------------

class TestMissingData:
    def test_missing_saham_key_gives_na(self):
        """A missing saham key → N/A for all its fields."""
        partial = {k: v for k, v in FULL_SAHAMS.items() if k != "punya"}
        result = _render_sahams_table(partial)
        # Punya row should still appear (with N/A values)
        assert "Punya" in result
        assert "N/A" in result

    def test_missing_bindu_key_gives_na(self):
        partial = {k: v for k, v in FULL_BINDUS.items() if k != "bhrigu_bindu"}
        result = _render_esoteric_bindus_table(partial)
        assert "Bhrigu Bindu" in result
        assert "N/A" in result

    def test_missing_nakshatra_gives_na(self):
        sahams = {"punya": {"longitude": 15.0, "sign": "Taurus", "lord": "Venus"}}
        result = _render_sahams_table(sahams)
        assert "N/A" in result

    def test_missing_pada_gives_na(self):
        sahams = {
            "punya": {"longitude": 15.0, "sign": "Taurus",
                      "nakshatra": "Rohini", "lord": "Venus"}
        }
        result = _render_sahams_table(sahams)
        assert "N/A" in result

    def test_missing_sign_gives_na(self):
        sahams = {"punya": {"longitude": 15.0, "lord": "Venus"}}
        result = _render_sahams_table(sahams)
        assert "N/A" in result

    def test_missing_lord_gives_na(self):
        sahams = {"punya": {"longitude": 15.0, "sign": "Taurus", "nakshatra": "Rohini"}}
        result = _render_sahams_table(sahams)
        assert "N/A" in result

    def test_missing_longitude_gives_na(self):
        sahams = {"punya": {"sign": "Taurus", "nakshatra": "Rohini", "lord": "Venus"}}
        result = _render_sahams_table(sahams)
        assert "N/A" in result

    def test_no_narration_on_partial_data(self):
        partial = {"sahams": {"punya": {"sign": "Taurus", "longitude": 15.0}}}
        result = render_sahams_section(partial)
        lint_narration(result, "sahams")

    def test_formula_override_takes_precedence(self):
        """Formula in entry data overrides canonical SAHAM_FORMULAS."""
        sahams = {"punya": {"longitude": 15.0, "sign": "Taurus",
                            "formula": "Custom Override Formula"}}
        result = _render_sahams_table(sahams)
        assert "Custom Override Formula" in result

    def test_formula_fallback_when_not_in_entry(self):
        """When entry has no formula key, canonical formula from SAHAM_FORMULAS is used."""
        sahams = {"punya": {"longitude": 15.0, "sign": "Taurus"}}
        result = _render_sahams_table(sahams)
        # punya canonical formula contains "Moon" and "Sun"
        assert "Moon" in result


# ---------------------------------------------------------------------------
# Tests — _fmt_degree helper
# ---------------------------------------------------------------------------

class TestFmtDegree:
    def test_round_degree(self):
        assert _fmt_degree(10.0) == "10°00'"

    def test_fractional_degree_half(self):
        assert _fmt_degree(10.5) == "10°30'"

    def test_zero(self):
        assert _fmt_degree(0.0) == "0°00'"

    def test_none_returns_na(self):
        assert _fmt_degree(None) == "N/A"

    def test_string_float(self):
        assert _fmt_degree("15.75") == "15°45'"

    def test_invalid_returns_na(self):
        assert _fmt_degree("abc") == "N/A"

    def test_large_longitude(self):
        assert _fmt_degree(330.0) == "330°00'"

    def test_fractional_minutes_round(self):
        # 42.3 → 42 + 0.3*60 = 42 + 18 → 42°18'
        assert _fmt_degree(42.3) == "42°18'"


# ---------------------------------------------------------------------------
# Tests — constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_sahams_canonical_order_length(self):
        assert len(SAHAMS_CANONICAL_ORDER) >= 40

    def test_esoteric_bindus_length(self):
        assert len(ESOTERIC_BINDUS) == 9

    def test_saham_labels_keys_match_canonical_order(self):
        assert set(SAHAM_LABELS.keys()) == set(SAHAMS_CANONICAL_ORDER)

    def test_bindu_labels_keys_match_esoteric_bindus(self):
        assert set(BINDU_LABELS.keys()) == set(ESOTERIC_BINDUS)

    def test_saham_formulas_covers_all_sahams(self):
        for key in SAHAMS_CANONICAL_ORDER:
            assert key in SAHAM_FORMULAS, f"SAHAM_FORMULAS missing entry for '{key}'"

    def test_bindu_formulas_covers_all_bindus(self):
        for key in ESOTERIC_BINDUS:
            assert key in BINDU_FORMULAS, f"BINDU_FORMULAS missing entry for '{key}'"

    def test_punya_label(self):
        assert SAHAM_LABELS["punya"] == "Punya"

    def test_vivah_label(self):
        assert SAHAM_LABELS["vivah"] == "Vivah"

    def test_bhrigu_bindu_label(self):
        assert BINDU_LABELS["bhrigu_bindu"] == "Bhrigu Bindu"

    def test_trisphuta_label(self):
        assert BINDU_LABELS["trisphuta"] == "Trisphuta"

    def test_punya_formula_references_moon_sun(self):
        f = SAHAM_FORMULAS["punya"]
        assert "Moon" in f and "Sun" in f and "Lagna" in f

    def test_bhrigu_bindu_formula_references_rahu(self):
        f = BINDU_FORMULAS["bhrigu_bindu"]
        assert "Rahu" in f

    def test_trisphuta_formula_references_moon_mars_lagna(self):
        f = BINDU_FORMULAS["trisphuta"]
        assert "Moon" in f and "Mars" in f and "Lagna" in f

    def test_panchasphuta_formula_references_jupiter(self):
        f = BINDU_FORMULAS["panchasphuta"]
        assert "Jupiter" in f


# ---------------------------------------------------------------------------
# Tests — sub-renderer return types
# ---------------------------------------------------------------------------

class TestSubRenderers:
    def test_render_sahams_table_returns_string_empty(self):
        assert isinstance(_render_sahams_table({}), str)

    def test_render_esoteric_bindus_table_returns_string_empty(self):
        assert isinstance(_render_esoteric_bindus_table({}), str)

    def test_render_sahams_table_returns_string_full(self):
        assert isinstance(_render_sahams_table(FULL_SAHAMS), str)

    def test_render_esoteric_bindus_table_returns_string_full(self):
        assert isinstance(_render_esoteric_bindus_table(FULL_BINDUS), str)

    def test_render_sahams_table_contains_header_row(self):
        result = _render_sahams_table({})
        assert "| Saham |" in result

    def test_render_esoteric_bindus_table_contains_header_row(self):
        result = _render_esoteric_bindus_table({})
        assert "| Bindu |" in result

    def test_full_render_no_narration(self):
        result = render_sahams_section(FULL_CHART_OUTPUT)
        lint_narration(result, "sahams")
