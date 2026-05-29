"""
Tests for pipeline/render/strengths_renderer.py (F-10)

Coverage (30+ tests):
- Empty chart_output → no crash, returns string
- BAV section heading present
- BAV table has 8 contributor rows
- All BAV contributor names present
- SAV section heading present
- SAV row present in output
- Trikona Reduced row present
- Ekadhipathya Reduced row present
- Sodhita SAV row present
- Kakshya section heading present
- Kakshya table has 9 graha rows
- Kakshya Total column present
- Shadbala section heading present
- Shadbala table has 9 graha rows
- 6 sub-bala column names in shadbala header
- Shadbala Required column present
- Shadbala Ratio column present
- Shadbala numeric values formatted to 1 decimal
- Ishta/Kashta section heading present
- Ishta Phala column present
- Kashta Phala column present
- Ishta/Kashta table has 9 graha rows
- Bhava Bala section heading present
- Bhava Bala table has 12 house rows
- Bhava Bala sub-bala columns present (Bhavadhipati, Drishti, Dig)
- Bhava Bala Total column present
- Placeholder dash rendered for missing BAV data
- Placeholder dash rendered for missing Shadbala data
- Placeholder dash rendered for missing Bhava Bala data
- No narration verbs in full output
- BAV sign columns all 12 signs present in header
- render_strengths_section returns str type
- Ratio formatted to 2 decimal places
- Lagna contributor present in BAV
- House keys work as int or str
- SAV sign abbreviations in header row
- Full section includes all 6 sub-section headings
- GRAHAS constant has 9 grahas
- BAV_CONTRIBUTORS constant has 8 entries
- SIGNS constant has 12 signs
- Kakshya values sum in Total column
- Shadbala negative Drik Bala rendered correctly
"""
import sys
from pathlib import Path

import pytest

# Allow import from python-sidecar root
sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.strengths_renderer import (
    GRAHAS,
    SIGNS,
    BAV_CONTRIBUTORS,
    GRAHA_DISPLAY,
    SIGN_DISPLAY,
    BAV_CONTRIBUTOR_DISPLAY,
    render_strengths_section,
    _render_bav,
    _render_sav,
    _render_kakshya,
    _render_shadbala,
    _render_ishta_kashta,
    _render_bhava_bala,
    _fmt_int,
    _fmt_float,
    _fmt_ratio,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Sample data builders
# ---------------------------------------------------------------------------

def _make_bav() -> dict:
    """8 contributors × 12 signs, all value = 4."""
    return {
        contrib: {sign: 4 for sign in SIGNS}
        for contrib in BAV_CONTRIBUTORS
    }


def _make_sav() -> dict:
    """12 signs, value = 32 (8 × 4)."""
    return {sign: 32 for sign in SIGNS}


def _make_sodhita(offset: int = 0) -> dict:
    return {sign: 30 + offset for sign in SIGNS}


def _make_kakshya() -> dict:
    """9 grahas, each with 8 kakshya contributors = 1."""
    return {
        graha: {contrib: 1 for contrib in BAV_CONTRIBUTORS}
        for graha in GRAHAS
    }


def _make_shadbala_entry(
    sthana: float = 120.5,
    dig: float = 60.0,
    kala: float = 45.3,
    chesta: float = 30.2,
    naisargika: float = 60.0,
    drik: float = -10.5,
    total: float = 305.5,
    required: float = 390.0,
    ratio: float = 0.783,
    ishta: float = 45.2,
    kashta: float = 25.3,
) -> dict:
    return {
        "sthana_bala":     sthana,
        "dig_bala":        dig,
        "kala_bala":       kala,
        "chesta_bala":     chesta,
        "naisargika_bala": naisargika,
        "drik_bala":       drik,
        "total":           total,
        "required":        required,
        "ratio":           ratio,
        "ishta_phala":     ishta,
        "kashta_phala":    kashta,
    }


def _make_shadbala() -> dict:
    return {graha: _make_shadbala_entry() for graha in GRAHAS}


def _make_bhava_bala() -> dict:
    return {
        str(h): {
            "bhavadhipati_bala":  80.0,
            "bhava_drishti_bala": 20.0,
            "bhava_dig_bala":     15.0,
            "total":              115.0,
        }
        for h in range(1, 13)
    }


def _full_chart() -> dict:
    return {
        "ashtakavarga": {
            "bav":                  _make_bav(),
            "sav":                  _make_sav(),
            "trikona_reduced":      _make_sodhita(-2),
            "ekadhipathya_reduced": _make_sodhita(-4),
            "sodhita_sav":          _make_sodhita(-6),
            "kakshya":              _make_kakshya(),
        },
        "shadbala":    _make_shadbala(),
        "bhava_bala":  _make_bhava_bala(),
    }


# ---------------------------------------------------------------------------
# Tests — empty chart (no crash)
# ---------------------------------------------------------------------------

class TestEmptyChart:
    def test_empty_returns_string(self):
        result = render_strengths_section({})
        assert isinstance(result, str)

    def test_empty_no_crash(self):
        # Must not raise
        render_strengths_section({})

    def test_empty_none_values_no_crash(self):
        render_strengths_section({
            "ashtakavarga": None,
            "shadbala":     None,
            "bhava_bala":   None,
        })


# ---------------------------------------------------------------------------
# Tests — BAV section
# ---------------------------------------------------------------------------

class TestBAVSection:
    def test_bav_heading_present(self):
        result = _render_bav({})
        assert "Bhinnashtakavarga" in result

    def test_bav_8_contributor_rows(self):
        result = _render_bav({"bav": _make_bav()})
        for contrib in BAV_CONTRIBUTORS:
            assert BAV_CONTRIBUTOR_DISPLAY[contrib] in result

    def test_bav_lagna_contributor_present(self):
        result = _render_bav({"bav": _make_bav()})
        assert "Lagna" in result

    def test_bav_all_12_signs_in_header(self):
        result = _render_bav({"bav": _make_bav()})
        for sign in SIGNS:
            assert SIGN_DISPLAY[sign] in result

    def test_bav_values_rendered(self):
        result = _render_bav({"bav": _make_bav()})
        # All cells should be "4"
        assert "4" in result

    def test_bav_missing_data_renders_dash(self):
        result = _render_bav({})
        assert "—" in result

    def test_bav_partial_data_renders_dash(self):
        bav = {"sun": {"aries": 4}}  # only one entry
        result = _render_bav({"bav": bav})
        assert "—" in result

    def test_bav_8x12_label_in_heading(self):
        result = _render_bav({})
        assert "8" in result and "12" in result


# ---------------------------------------------------------------------------
# Tests — SAV section
# ---------------------------------------------------------------------------

class TestSAVSection:
    def test_sav_heading_present(self):
        result = _render_sav({})
        assert "Sarvashtakavarga" in result

    def test_sav_row_present(self):
        result = _render_sav({"sav": _make_sav()})
        assert "| SAV |" in result

    def test_trikona_reduced_row_present(self):
        result = _render_sav({"trikona_reduced": _make_sodhita()})
        assert "Trikona" in result

    def test_ekadhipathya_reduced_row_present(self):
        result = _render_sav({"ekadhipathya_reduced": _make_sodhita()})
        assert "Ekadhipathya" in result

    def test_sodhita_sav_row_present(self):
        result = _render_sav({"sodhita_sav": _make_sodhita()})
        assert "Sodhita SAV" in result

    def test_sav_sign_abbreviations_in_header(self):
        result = _render_sav({})
        # Check a few abbreviations
        assert "Ari" in result
        assert "Tau" in result
        assert "Pis" in result

    def test_sav_values_rendered(self):
        result = _render_sav({"sav": _make_sav()})
        assert "32" in result


# ---------------------------------------------------------------------------
# Tests — Kakshya section
# ---------------------------------------------------------------------------

class TestKakshyaSection:
    def test_kakshya_heading_present(self):
        result = _render_kakshya({})
        assert "Kakshya" in result

    def test_kakshya_9_graha_rows(self):
        result = _render_kakshya({"kakshya": _make_kakshya()})
        for graha in GRAHAS:
            assert GRAHA_DISPLAY[graha] in result

    def test_kakshya_total_column_present(self):
        result = _render_kakshya({"kakshya": _make_kakshya()})
        assert "Total" in result

    def test_kakshya_total_value_correct(self):
        """8 contributors × 1 = total 8 per graha."""
        result = _render_kakshya({"kakshya": _make_kakshya()})
        assert "| 8 |" in result

    def test_kakshya_missing_data_renders_zero(self):
        """Missing kakshya data → 0 per cell, total 0."""
        result = _render_kakshya({})
        assert "| 0 |" in result


# ---------------------------------------------------------------------------
# Tests — Shadbala section
# ---------------------------------------------------------------------------

class TestShadBalaSection:
    def test_shadbala_heading_present(self):
        result = _render_shadbala({})
        assert "Shadbala" in result

    def test_shadbala_9_graha_rows(self):
        result = _render_shadbala(_make_shadbala())
        for graha in GRAHAS:
            assert GRAHA_DISPLAY[graha] in result

    def test_shadbala_6_sub_bala_columns(self):
        result = _render_shadbala({})
        for col in ("Sthana", "Dig", "Kala", "Chesta", "Naisargika", "Drik"):
            assert col in result

    def test_shadbala_required_column_present(self):
        result = _render_shadbala({})
        assert "Required" in result

    def test_shadbala_ratio_column_present(self):
        result = _render_shadbala({})
        assert "Ratio" in result

    def test_shadbala_total_column_present(self):
        result = _render_shadbala({})
        assert "Total" in result

    def test_shadbala_numeric_1_decimal(self):
        result = _render_shadbala(_make_shadbala())
        assert "120.5" in result

    def test_shadbala_ratio_2_decimal(self):
        result = _render_shadbala(_make_shadbala())
        assert "0.78" in result

    def test_shadbala_negative_drik_bala_rendered(self):
        result = _render_shadbala(_make_shadbala())
        assert "-10.5" in result

    def test_shadbala_missing_data_renders_dash(self):
        result = _render_shadbala({})
        assert "—" in result


# ---------------------------------------------------------------------------
# Tests — Ishta/Kashta Phala section
# ---------------------------------------------------------------------------

class TestIshtaKashtaSection:
    def test_ishta_kashta_heading_present(self):
        result = _render_ishta_kashta({})
        assert "Ishta" in result and "Kashta" in result

    def test_ishta_phala_column_present(self):
        result = _render_ishta_kashta({})
        assert "Ishta Phala" in result

    def test_kashta_phala_column_present(self):
        result = _render_ishta_kashta({})
        assert "Kashta Phala" in result

    def test_ishta_kashta_9_graha_rows(self):
        result = _render_ishta_kashta(_make_shadbala())
        for graha in GRAHAS:
            assert GRAHA_DISPLAY[graha] in result

    def test_ishta_kashta_values_rendered(self):
        result = _render_ishta_kashta(_make_shadbala())
        assert "45.2" in result
        assert "25.3" in result

    def test_ishta_kashta_missing_data_renders_dash(self):
        result = _render_ishta_kashta({})
        assert "—" in result


# ---------------------------------------------------------------------------
# Tests — Bhava Bala section
# ---------------------------------------------------------------------------

class TestBhavaBalaSection:
    def test_bhava_bala_heading_present(self):
        result = _render_bhava_bala({})
        assert "Bhava Bala" in result

    def test_bhava_bala_12_house_rows(self):
        result = _render_bhava_bala(_make_bhava_bala())
        for h in range(1, 13):
            assert f"| {h} |" in result

    def test_bhava_bala_sub_bala_columns(self):
        result = _render_bhava_bala({})
        assert "Bhavadhipati" in result
        assert "Drishti" in result
        assert "Dig" in result

    def test_bhava_bala_total_column_present(self):
        result = _render_bhava_bala({})
        assert "Total" in result

    def test_bhava_bala_values_rendered(self):
        result = _render_bhava_bala(_make_bhava_bala())
        assert "80.0" in result
        assert "115.0" in result

    def test_bhava_bala_house_key_as_int(self):
        """Keys as int (not str) should also work."""
        data = {
            h: {
                "bhavadhipati_bala":  50.0,
                "bhava_drishti_bala": 10.0,
                "bhava_dig_bala":     5.0,
                "total":              65.0,
            }
            for h in range(1, 13)
        }
        result = _render_bhava_bala(data)
        assert "50.0" in result

    def test_bhava_bala_missing_data_renders_dash(self):
        result = _render_bhava_bala({})
        assert "—" in result


# ---------------------------------------------------------------------------
# Tests — Full section integration
# ---------------------------------------------------------------------------

class TestFullSection:
    def test_full_section_returns_str(self):
        result = render_strengths_section(_full_chart())
        assert isinstance(result, str)

    def test_full_section_all_6_headings(self):
        result = render_strengths_section(_full_chart())
        assert "Bhinnashtakavarga" in result
        assert "Sarvashtakavarga"  in result
        assert "Kakshya"           in result
        assert "Shadbala"          in result
        assert "Ishta"             in result
        assert "Bhava Bala"        in result

    def test_no_narration_verbs(self):
        result = render_strengths_section(_full_chart())
        lint_narration(result, section="strengths")  # must not raise

    def test_no_narration_verbs_empty_chart(self):
        result = render_strengths_section({})
        lint_narration(result, section="strengths_empty")


# ---------------------------------------------------------------------------
# Tests — Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_grahas_has_9_entries(self):
        assert len(GRAHAS) == 9

    def test_signs_has_12_entries(self):
        assert len(SIGNS) == 12

    def test_bav_contributors_has_8_entries(self):
        assert len(BAV_CONTRIBUTORS) == 8

    def test_bav_contributors_includes_lagna(self):
        assert "lagna" in BAV_CONTRIBUTORS

    def test_bav_contributors_no_rahu_ketu(self):
        assert "rahu" not in BAV_CONTRIBUTORS
        assert "ketu" not in BAV_CONTRIBUTORS


# ---------------------------------------------------------------------------
# Tests — Format helpers
# ---------------------------------------------------------------------------

class TestFormatHelpers:
    def test_fmt_int_none_returns_dash(self):
        assert _fmt_int(None) == "—"

    def test_fmt_int_value(self):
        assert _fmt_int(4) == "4"

    def test_fmt_int_float_truncates(self):
        assert _fmt_int(3.9) == "3"

    def test_fmt_float_none_returns_dash(self):
        assert _fmt_float(None) == "—"

    def test_fmt_float_one_decimal(self):
        assert _fmt_float(120.5) == "120.5"

    def test_fmt_float_negative(self):
        assert _fmt_float(-10.5) == "-10.5"

    def test_fmt_ratio_two_decimal(self):
        assert _fmt_ratio(0.783) == "0.78"

    def test_fmt_ratio_none_returns_dash(self):
        assert _fmt_ratio(None) == "—"
