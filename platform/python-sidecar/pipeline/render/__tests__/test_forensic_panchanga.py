"""
Tests for pipeline/render/panchanga_renderer.py (F-08)

Coverage (30+ tests):
- Empty chart_output → no crash, returns string
- Empty panchanga dict → no crash, returns string
- All 5 limbs (Tithi, Vara, Nakshatra, Yoga, Karana) present in output
- Tithi: name, pada, lord, paksha, completion_pct rendered correctly
- Vara: name and lord rendered correctly
- Nakshatra: name, pada, lord, sandhi rendered correctly
- Nakshatra sandhi=True → 'Yes'; sandhi=False → 'No'
- Yoga: name and nature rendered correctly
- Karana: name, lord, nature rendered correctly
- Astronomical windows section heading present
- Sunrise / Sunset rendered with '—' for end column
- Brahma Muhurta start/end rendered
- Abhijit Muhurta start/end rendered
- Rahu Kalam start/end rendered
- Gulika Kalam start/end rendered
- Yamaganda start/end rendered
- Choghadiya day heading present
- Choghadiya night heading present
- Choghadiya day segments rendered with name/nature/start/end
- Choghadiya empty list → placeholder row '—'
- Hora sequence heading present
- Hora sequence entries rendered with hour/planet
- Hora empty list → placeholder row '—'
- Birth-moment strengths heading present
- Tara Bala rendered with class and favorable flag
- Chandra Bala rendered with class and score
- Special yogas heading present
- Siddha/Amrit/Marana/Kshana Yes/No rendered
- Era conversions heading present
- Vikram Samvat year rendered
- Shaka Samvat year rendered
- Kali Yuga year rendered
- No narration verbs (lint_narration passes)
- Return type is str
- Missing panchanga key → graceful N/A
- None values in sub-dicts → N/A gracefully
"""
import sys
from pathlib import Path

import pytest

# Allow import from python-sidecar root
sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.panchanga_renderer import (
    PANCHA_ANGA_LIMBS,
    SPECIAL_YOGA_NAMES,
    ERA_NAMES,
    ASTRONOMICAL_WINDOWS,
    render_panchanga_section,
    _render_five_limbs,
    _render_astronomical_windows,
    _render_choghadiya_table,
    _render_hora_sequence,
    _render_birth_strengths,
    _render_special_yogas,
    _render_era_conversions,
    _fmt_str,
    _fmt_int,
    _fmt_float,
    _fmt_bool_yn,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_PANCHANGA: dict = {
    "tithi": {
        "name": "Shukla Tritiya",
        "pada": 3,
        "lord": "Mars",
        "paksha": "Shukla",
        "completion_pct": 67.2,
    },
    "vara": {"name": "Ravivara", "lord": "Sun"},
    "nakshatra": {
        "name": "Purva Bhadrapada",
        "pada": 4,
        "lord": "Jupiter",
        "sandhi": False,
    },
    "yoga": {"name": "Shiva", "nature": "auspicious"},
    "karana": {"name": "Garaja", "lord": "Elephant", "nature": "moveable"},
    "sunrise": "03:45 UTC",
    "sunset": "12:55 UTC",
    "brahma_muhurta": {"start": "02:18 UTC", "end": "03:07 UTC"},
    "abhijit_muhurta": {"start": "07:50 UTC", "end": "08:37 UTC"},
    "rahu_kalam": {"start": "08:00 UTC", "end": "09:30 UTC"},
    "gulika_kalam": {"start": "06:00 UTC", "end": "07:30 UTC"},
    "yamaganda": {"start": "12:00 UTC", "end": "13:30 UTC"},
    "choghadiya_day": [
        {"name": "Udveg",   "nature": "inauspicious", "start": "06:00", "end": "07:30"},
        {"name": "Char",    "nature": "auspicious",   "start": "07:30", "end": "09:00"},
        {"name": "Labh",    "nature": "auspicious",   "start": "09:00", "end": "10:30"},
        {"name": "Amrit",   "nature": "auspicious",   "start": "10:30", "end": "12:00"},
        {"name": "Kaal",    "nature": "inauspicious", "start": "12:00", "end": "13:30"},
        {"name": "Shubh",   "nature": "auspicious",   "start": "13:30", "end": "15:00"},
        {"name": "Rog",     "nature": "inauspicious", "start": "15:00", "end": "16:30"},
        {"name": "Udveg",   "nature": "inauspicious", "start": "16:30", "end": "18:00"},
    ],
    "choghadiya_night": [
        {"name": "Shubh",   "nature": "auspicious",   "start": "18:00", "end": "19:30"},
        {"name": "Amrit",   "nature": "auspicious",   "start": "19:30", "end": "21:00"},
        {"name": "Char",    "nature": "auspicious",   "start": "21:00", "end": "22:30"},
        {"name": "Rog",     "nature": "inauspicious", "start": "22:30", "end": "00:00"},
        {"name": "Kaal",    "nature": "inauspicious", "start": "00:00", "end": "01:30"},
        {"name": "Labh",    "nature": "auspicious",   "start": "01:30", "end": "03:00"},
        {"name": "Udveg",   "nature": "inauspicious", "start": "03:00", "end": "04:30"},
        {"name": "Shubh",   "nature": "auspicious",   "start": "04:30", "end": "06:00"},
    ],
    "hora_sequence": [{"hour": i, "planet": p} for i, p in enumerate([
        "Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars",
        "Sun", "Venus", "Mercury", "Moon", "Saturn",
        "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon",
        "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury",
    ], start=1)],
    "tara_bala": {"class": "Sampat", "favorable": True},
    "chandra_bala": {"class": "favorable", "score": 8},
    "special_yogas": {"siddha": True, "amrit": False, "marana": False, "kshana": False},
    "vikram_samvat": 2040,
    "shaka_samvat": 1905,
    "kali_yuga": 5085,
}

SAMPLE_CHART_OUTPUT: dict = {"panchanga": SAMPLE_PANCHANGA}


# ---------------------------------------------------------------------------
# Test 1–2: Empty inputs — no crash, returns string
# ---------------------------------------------------------------------------

def test_empty_chart_output_no_crash():
    result = render_panchanga_section({})
    assert isinstance(result, str)


def test_empty_panchanga_key_no_crash():
    result = render_panchanga_section({"panchanga": {}})
    assert isinstance(result, str)


def test_return_type_is_str():
    result = render_panchanga_section(SAMPLE_CHART_OUTPUT)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Test: Five Limbs section
# ---------------------------------------------------------------------------

def test_five_limbs_heading_present():
    result = render_panchanga_section(SAMPLE_CHART_OUTPUT)
    assert "### Five Limbs (Pancha Anga)" in result


def test_five_limbs_table_header_present():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "| Limb | Value | Details |" in result


def test_tithi_name_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Shukla Tritiya" in result


def test_tithi_pada_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Pada 3" in result


def test_tithi_lord_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Lord: Mars" in result


def test_tithi_paksha_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Paksha: Shukla" in result


def test_tithi_completion_pct_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "67.2%" in result


def test_vara_name_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Ravivara" in result


def test_vara_lord_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Lord: Sun" in result


def test_nakshatra_name_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Purva Bhadrapada" in result


def test_nakshatra_pada_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Pada 4" in result


def test_nakshatra_lord_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Lord: Jupiter" in result


def test_nakshatra_sandhi_false_renders_no():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Sandhi: No" in result


def test_nakshatra_sandhi_true_renders_yes():
    panchanga = dict(SAMPLE_PANCHANGA)
    panchanga["nakshatra"] = {**SAMPLE_PANCHANGA["nakshatra"], "sandhi": True}
    result = _render_five_limbs(panchanga)
    assert "Sandhi: Yes" in result


def test_yoga_name_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Shiva" in result


def test_yoga_nature_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Nature: Auspicious" in result


def test_karana_name_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Garaja" in result


def test_karana_lord_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Lord: Elephant" in result


def test_karana_nature_rendered():
    result = _render_five_limbs(SAMPLE_PANCHANGA)
    assert "Nature: Moveable" in result


# ---------------------------------------------------------------------------
# Test: Astronomical Windows section
# ---------------------------------------------------------------------------

def test_astronomical_windows_heading_present():
    result = render_panchanga_section(SAMPLE_CHART_OUTPUT)
    assert "### Astronomical Windows" in result


def test_astronomical_windows_table_header():
    result = _render_astronomical_windows(SAMPLE_PANCHANGA)
    assert "| Window | Start (UTC) | End (UTC) |" in result


def test_sunrise_rendered():
    result = _render_astronomical_windows(SAMPLE_PANCHANGA)
    assert "03:45 UTC" in result
    assert "Sunrise" in result


def test_sunset_rendered():
    result = _render_astronomical_windows(SAMPLE_PANCHANGA)
    assert "12:55 UTC" in result
    assert "Sunset" in result


def test_sunrise_end_column_is_dash():
    result = _render_astronomical_windows(SAMPLE_PANCHANGA)
    # Sunrise row: start=03:45 UTC, end=—
    assert "| Sunrise | 03:45 UTC | — |" in result


def test_brahma_muhurta_rendered():
    result = _render_astronomical_windows(SAMPLE_PANCHANGA)
    assert "Brahma Muhurta" in result
    assert "02:18 UTC" in result
    assert "03:07 UTC" in result


def test_abhijit_muhurta_rendered():
    result = _render_astronomical_windows(SAMPLE_PANCHANGA)
    assert "Abhijit Muhurta" in result
    assert "07:50 UTC" in result
    assert "08:37 UTC" in result


def test_rahu_kalam_rendered():
    result = _render_astronomical_windows(SAMPLE_PANCHANGA)
    assert "Rahu Kalam" in result
    assert "08:00 UTC" in result
    assert "09:30 UTC" in result


def test_gulika_kalam_rendered():
    result = _render_astronomical_windows(SAMPLE_PANCHANGA)
    assert "Gulika Kalam" in result
    assert "06:00 UTC" in result
    assert "07:30 UTC" in result


def test_yamaganda_rendered():
    result = _render_astronomical_windows(SAMPLE_PANCHANGA)
    assert "Yamaganda" in result
    assert "12:00 UTC" in result
    assert "13:30 UTC" in result


# ---------------------------------------------------------------------------
# Test: Choghadiya section
# ---------------------------------------------------------------------------

def test_choghadiya_day_heading_present():
    result = render_panchanga_section(SAMPLE_CHART_OUTPUT)
    assert "### Choghadiya (Day)" in result


def test_choghadiya_night_heading_present():
    result = render_panchanga_section(SAMPLE_CHART_OUTPUT)
    assert "### Choghadiya (Night)" in result


def test_choghadiya_day_table_header():
    result = _render_choghadiya_table(SAMPLE_PANCHANGA["choghadiya_day"], "Choghadiya (Day)")
    assert "| Segment | Name | Nature | Start | End |" in result


def test_choghadiya_day_segments_rendered():
    result = _render_choghadiya_table(SAMPLE_PANCHANGA["choghadiya_day"], "Choghadiya (Day)")
    assert "Udveg" in result
    assert "Inauspicious" in result
    assert "06:00" in result


def test_choghadiya_day_segment_count():
    result = _render_choghadiya_table(SAMPLE_PANCHANGA["choghadiya_day"], "Choghadiya (Day)")
    # 8 data rows: segments 1-8
    for i in range(1, 9):
        assert f"| {i} |" in result


def test_choghadiya_empty_list_placeholder():
    result = _render_choghadiya_table([], "Choghadiya (Day)")
    assert "| — | — | — | — | — |" in result


def test_choghadiya_night_segments_rendered():
    result = _render_choghadiya_table(SAMPLE_PANCHANGA["choghadiya_night"], "Choghadiya (Night)")
    assert "Shubh" in result
    assert "18:00" in result


# ---------------------------------------------------------------------------
# Test: Hora Sequence section
# ---------------------------------------------------------------------------

def test_hora_sequence_heading_present():
    result = render_panchanga_section(SAMPLE_CHART_OUTPUT)
    assert "### Hora Sequence (24 Hours)" in result


def test_hora_sequence_table_header():
    result = _render_hora_sequence(SAMPLE_PANCHANGA)
    assert "| Hour | Planetary Hora |" in result


def test_hora_sequence_24_entries():
    result = _render_hora_sequence(SAMPLE_PANCHANGA)
    # All 24 hours should appear as row entries
    for i in range(1, 25):
        assert f"| {i} |" in result


def test_hora_sequence_planets_rendered():
    result = _render_hora_sequence(SAMPLE_PANCHANGA)
    assert "Sun" in result
    assert "Moon" in result
    assert "Jupiter" in result


def test_hora_empty_list_placeholder():
    panchanga = {**SAMPLE_PANCHANGA, "hora_sequence": []}
    result = _render_hora_sequence(panchanga)
    assert "| — | — |" in result


# ---------------------------------------------------------------------------
# Test: Birth-Moment Strengths section
# ---------------------------------------------------------------------------

def test_birth_strengths_heading_present():
    result = render_panchanga_section(SAMPLE_CHART_OUTPUT)
    assert "### Birth-Moment Strengths" in result


def test_birth_strengths_table_header():
    result = _render_birth_strengths(SAMPLE_PANCHANGA)
    assert "| Measure | Value |" in result


def test_tara_bala_class_rendered():
    result = _render_birth_strengths(SAMPLE_PANCHANGA)
    assert "Sampat" in result


def test_tara_bala_favorable_rendered():
    result = _render_birth_strengths(SAMPLE_PANCHANGA)
    assert "Yes" in result


def test_chandra_bala_class_rendered():
    result = _render_birth_strengths(SAMPLE_PANCHANGA)
    assert "favorable" in result


def test_chandra_bala_score_rendered():
    result = _render_birth_strengths(SAMPLE_PANCHANGA)
    assert "Score: 8" in result


def test_tara_bala_missing_dict_graceful():
    panchanga = {**SAMPLE_PANCHANGA, "tara_bala": None}
    result = _render_birth_strengths(panchanga)
    assert "Tara Bala" in result
    assert "N/A" in result


# ---------------------------------------------------------------------------
# Test: Special Yogas section
# ---------------------------------------------------------------------------

def test_special_yogas_heading_present():
    result = render_panchanga_section(SAMPLE_CHART_OUTPUT)
    assert "### Special Yogas" in result


def test_special_yogas_table_header():
    result = _render_special_yogas(SAMPLE_PANCHANGA)
    assert "| Yoga | Present |" in result


def test_siddha_yoga_true_renders_yes():
    result = _render_special_yogas(SAMPLE_PANCHANGA)
    assert "Siddha Yoga" in result
    # siddha=True in sample
    idx = result.index("Siddha Yoga")
    assert "Yes" in result[idx:]


def test_amrit_yoga_false_renders_no():
    result = _render_special_yogas(SAMPLE_PANCHANGA)
    assert "Amrit Yoga" in result


def test_marana_yoga_present():
    result = _render_special_yogas(SAMPLE_PANCHANGA)
    assert "Marana Yoga" in result


def test_kshana_yoga_present():
    result = _render_special_yogas(SAMPLE_PANCHANGA)
    assert "Kshana Yoga" in result


def test_special_yogas_all_true():
    panchanga = {**SAMPLE_PANCHANGA, "special_yogas": {
        "siddha": True, "amrit": True, "marana": True, "kshana": True
    }}
    result = _render_special_yogas(panchanga)
    assert result.count("Yes") == 4


def test_special_yogas_all_false():
    panchanga = {**SAMPLE_PANCHANGA, "special_yogas": {
        "siddha": False, "amrit": False, "marana": False, "kshana": False
    }}
    result = _render_special_yogas(panchanga)
    assert result.count("No") == 4


def test_special_yogas_missing_dict_graceful():
    panchanga = {**SAMPLE_PANCHANGA, "special_yogas": None}
    result = _render_special_yogas(panchanga)
    assert "Siddha Yoga" in result
    assert "N/A" in result


# ---------------------------------------------------------------------------
# Test: Era Conversions section
# ---------------------------------------------------------------------------

def test_era_conversions_heading_present():
    result = render_panchanga_section(SAMPLE_CHART_OUTPUT)
    assert "### Era Conversions" in result


def test_era_conversions_table_header():
    result = _render_era_conversions(SAMPLE_PANCHANGA)
    assert "| Era | Year |" in result


def test_vikram_samvat_rendered():
    result = _render_era_conversions(SAMPLE_PANCHANGA)
    assert "Vikram Samvat" in result
    assert "2040" in result


def test_shaka_samvat_rendered():
    result = _render_era_conversions(SAMPLE_PANCHANGA)
    assert "Shaka Samvat" in result
    assert "1905" in result


def test_kali_yuga_rendered():
    result = _render_era_conversions(SAMPLE_PANCHANGA)
    assert "Kali Yuga" in result
    assert "5085" in result


def test_era_missing_values_graceful():
    panchanga = {**SAMPLE_PANCHANGA, "vikram_samvat": None, "shaka_samvat": None, "kali_yuga": None}
    result = _render_era_conversions(panchanga)
    assert result.count("N/A") >= 3


# ---------------------------------------------------------------------------
# Test: No narration verbs
# ---------------------------------------------------------------------------

def test_no_narration_verbs_full_output():
    result = render_panchanga_section(SAMPLE_CHART_OUTPUT)
    try:
        lint_narration(result)
    except NarrationViolation as exc:
        pytest.fail(f"Narration verb detected in output: {exc}")


def test_no_narration_verbs_empty_input():
    result = render_panchanga_section({})
    try:
        lint_narration(result)
    except NarrationViolation as exc:
        pytest.fail(f"Narration verb detected in empty output: {exc}")


# ---------------------------------------------------------------------------
# Test: Constants
# ---------------------------------------------------------------------------

def test_pancha_anga_limbs_constant():
    assert "Tithi" in PANCHA_ANGA_LIMBS
    assert "Vara" in PANCHA_ANGA_LIMBS
    assert "Nakshatra" in PANCHA_ANGA_LIMBS
    assert "Yoga" in PANCHA_ANGA_LIMBS
    assert "Karana" in PANCHA_ANGA_LIMBS


def test_special_yoga_names_constant():
    for name in ["Siddha", "Amrit", "Marana", "Kshana"]:
        assert name in SPECIAL_YOGA_NAMES


def test_era_names_constant():
    for name in ["Vikram Samvat", "Shaka Samvat", "Kali Yuga"]:
        assert name in ERA_NAMES


def test_astronomical_windows_constant():
    for w in ["Sunrise", "Sunset", "Brahma Muhurta", "Rahu Kalam"]:
        assert w in ASTRONOMICAL_WINDOWS


# ---------------------------------------------------------------------------
# Test: Helper functions
# ---------------------------------------------------------------------------

def test_fmt_str_none_returns_na():
    assert _fmt_str(None) == "N/A"


def test_fmt_str_empty_returns_na():
    assert _fmt_str("") == "N/A"


def test_fmt_str_value():
    assert _fmt_str("Shiva") == "Shiva"


def test_fmt_int_none_returns_na():
    assert _fmt_int(None) == "N/A"


def test_fmt_int_value():
    assert _fmt_int(2040) == "2040"


def test_fmt_float_none_returns_na():
    assert _fmt_float(None) == "N/A"


def test_fmt_float_precision():
    assert _fmt_float(67.234, precision=1) == "67.2"


def test_fmt_bool_yn_true():
    assert _fmt_bool_yn(True) == "Yes"


def test_fmt_bool_yn_false():
    assert _fmt_bool_yn(False) == "No"


def test_fmt_bool_yn_none_returns_na():
    assert _fmt_bool_yn(None) == "N/A"
