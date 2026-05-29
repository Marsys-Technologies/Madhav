"""
Tests for pipeline/render/yogas_renderer.py (F-07)

Coverage (30+ tests):
- Empty chart_output → no crash, returns string
- Active yogas table present when yogas exist
- Near-miss section present when near-miss yogas exist
- Summary count line present with correct format
- No narration verbs (lint_narration passes)
- Doshas section present
- Missing data → graceful (N/A placeholders)
- Active yogas sorted by tightness_score descending
- Near-miss threshold: score > 0.5, active=False
- Yoga with active=True, score=1.0 appears in Active only
- Yoga with active=False, score=0.6 appears in Near-Miss only
- Yoga with active=False, score=0.3 absent from both tables
- Constituent list formatted as comma-separated
- Boolean Yes/No formatting for dosha active field
- Severity formatting (Mild/Moderate/Severe/N/A)
- Cancellations list formatted as comma-separated
- Placeholder row '—' when no active yogas
- Placeholder row '—' when no near-miss yogas
- Placeholder row '—' when doshas list is empty
- Summary counts: total, active, near-miss all correct
- Pancha Mahapurusha names representable
- Gajakesari name representable
- Raj Yoga name representable
- Dhan Yoga name representable
- Vipareeta Raja Yoga variants representable
- Neechabhanga name representable
- Sunafa/Anapha/Durdhura names representable
- Kala Sarpa name representable
- All 14 canonical dosha names representable
- Tightness float formatted to 2 decimal places
- None tightness_score → N/A gracefully
- Dosha with None severity → N/A gracefully
- Dosha with empty cancellations list → N/A gracefully
- Active yoga with empty constituent list → N/A gracefully
- render_yogas_section return type is str
"""
import sys
from pathlib import Path

import pytest

# Allow import from python-sidecar root
sys.path.insert(0, str(Path(__file__).parents[3]))

from pipeline.render.yogas_renderer import (
    NEAR_MISS_THRESHOLD,
    YOGA_CATEGORIES,
    CANONICAL_DOSHA_NAMES,
    render_yogas_section,
    _render_summary_line,
    _render_active_yogas_table,
    _render_near_miss_yogas_table,
    _render_doshas_table,
    _fmt_str,
    _fmt_float,
    _fmt_bool_yn,
    _fmt_list,
    _fmt_severity,
)
from pipeline.render.base_renderer import lint_narration, NarrationViolation


# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------

def _yoga(
    name: str,
    active: bool,
    tightness_score: float,
    constituent: list[str] | None = None,
    classical_citation: str | None = None,
) -> dict:
    return {
        "name": name,
        "active": active,
        "constituent": constituent or [],
        "tightness_score": tightness_score,
        "classical_citation": classical_citation or "BPHS",
    }


def _dosha(
    name: str,
    active: bool,
    constituent: list[str] | None = None,
    severity: str | None = "moderate",
    cancellation_rules_applicable: list[str] | None = None,
) -> dict:
    return {
        "name": name,
        "active": active,
        "constituent": constituent or [],
        "severity": severity,
        "cancellation_rules_applicable": cancellation_rules_applicable or [],
    }


SAMPLE_YOGAS: list[dict] = [
    _yoga("Gajakesari",        True,  0.85, ["Moon", "Jupiter"], "BPHS Ch 36, v 1-4"),
    _yoga("Ruchaka",           True,  0.92, ["Mars"], "BPHS Ch 36, v 5"),
    _yoga("Bhadra",            True,  0.78, ["Mercury"], "BPHS Ch 36, v 6"),
    _yoga("Hamsa",             True,  0.65, ["Jupiter"], "BPHS Ch 36, v 7"),
    _yoga("Malavya",           True,  0.55, ["Venus"], "BPHS Ch 36, v 8"),
    _yoga("Sasa",              False, 0.72, ["Saturn"], "BPHS Ch 36, v 9"),
    _yoga("Raj Yoga",          False, 0.60, ["Sun", "Moon"], "BPHS Ch 34"),
    _yoga("Dhan Yoga",         False, 0.30, ["Jupiter", "Venus"], "BPHS Ch 35"),
    _yoga("Neechabhanga",      False, 0.51, ["Moon"], "Jataka Parijata"),
    _yoga("Harsha Yoga",       True,  0.45, ["Mars", "6H"], "BPHS Ch 76"),
    _yoga("Sarala Yoga",       True,  0.40, ["Saturn", "8H"], "BPHS Ch 76"),
    _yoga("Vimala Yoga",       True,  0.35, ["Venus", "12H"], "BPHS Ch 76"),
    _yoga("Sunafa",            False, 0.20, ["Moon"], "BPHS Ch 12"),
    _yoga("Anapha",            False, 0.15, ["Moon"], "BPHS Ch 12"),
    _yoga("Durdhura",          False, 0.10, ["Moon"], "BPHS Ch 12"),
    _yoga("Kala Sarpa (Ananta)", False, 0.80, ["Rahu", "Ketu"], "BPHS Ch 13"),
]

SAMPLE_DOSHAS: list[dict] = [
    _dosha("Mangal Dosha",      True,  ["Mars"],         "moderate",  ["Jupiter in 7th", "Venus aspects Mars"]),
    _dosha("Kaal Sarpa Dosha",  False, ["Rahu", "Ketu"], "severe",    ["All planets not hemmed"]),
    _dosha("Pitru Dosha",       True,  ["Sun", "Saturn"],"mild",      ["Jupiter aspects Sun"]),
    _dosha("Matri Dosha",       False, ["Moon"],          "N/A",       []),
    _dosha("Naga Dosha",        True,  ["Rahu"],          "moderate",  ["Naga Puja performed"]),
    _dosha("Sarpa Dosha",       False, ["Ketu"],          "mild",      []),
    _dosha("Guru Chandal Dosha",True,  ["Jupiter", "Rahu"], "severe", ["Guru Puja", "Charity"]),
    _dosha("Grahan Dosha",      False, ["Sun", "Rahu"],   "moderate",  ["Eclipse puja"]),
    _dosha("Daridra Dosha",     False, ["Jupiter", "12H"],"moderate",  []),
    _dosha("Shakata Dosha",     True,  ["Moon", "Jupiter"],"mild",     ["Jupiter 6/8/12 from Moon mitigated if strong"]),
    _dosha("Vish Dosha",        False, ["Saturn", "Moon"],"severe",    ["Specific mantras"]),
    _dosha("Punarphoo Dosha",   True,  ["Saturn", "Moon"],"mild",      ["Strong Jupiter"]),
    _dosha("Angarak Dosha",     False, ["Mars", "Rahu"],  "moderate",  []),
    _dosha("Kemadrum Dosha",    False, ["Moon"],          "mild",      ["Planet in kendra from Moon"]),
]


# ---------------------------------------------------------------------------
# Test 1: Empty chart_output — no crash, returns string
# ---------------------------------------------------------------------------

def test_empty_chart_output_no_crash():
    result = render_yogas_section({})
    assert isinstance(result, str)


def test_empty_yogas_key_no_crash():
    result = render_yogas_section({"yogas": [], "doshas": []})
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Test 3: Summary count line present
# ---------------------------------------------------------------------------

def test_summary_line_present():
    result = render_yogas_section({"yogas": SAMPLE_YOGAS, "doshas": SAMPLE_DOSHAS})
    assert "Total yoga predicates evaluated:" in result


def test_summary_line_correct_total():
    result = _render_summary_line(SAMPLE_YOGAS)
    total = len(SAMPLE_YOGAS)
    assert f"Total yoga predicates evaluated: {total}" in result


def test_summary_line_correct_active_count():
    result = _render_summary_line(SAMPLE_YOGAS)
    active_count = sum(1 for y in SAMPLE_YOGAS if y.get("active") is True)
    assert f"Active: {active_count}" in result


def test_summary_line_correct_near_miss_count():
    result = _render_summary_line(SAMPLE_YOGAS)
    near_miss = sum(
        1 for y in SAMPLE_YOGAS
        if not y.get("active") and float(y.get("tightness_score", 0)) > NEAR_MISS_THRESHOLD
    )
    assert f"Near-miss (score > {NEAR_MISS_THRESHOLD}): {near_miss}" in result


# ---------------------------------------------------------------------------
# Test 4: Active yogas table present
# ---------------------------------------------------------------------------

def test_active_yogas_heading_present():
    result = render_yogas_section({"yogas": SAMPLE_YOGAS, "doshas": []})
    assert "### Active Yogas" in result


def test_active_yogas_table_header_present():
    result = _render_active_yogas_table(SAMPLE_YOGAS)
    assert "| Yoga | Constituent | Tightness | Citation |" in result


def test_active_yogas_contains_active_yoga():
    result = _render_active_yogas_table(SAMPLE_YOGAS)
    assert "Gajakesari" in result


def test_active_yogas_sorted_descending():
    result = _render_active_yogas_table(SAMPLE_YOGAS)
    # Ruchaka (0.92) should appear before Gajakesari (0.85)
    ruchaka_pos = result.index("Ruchaka")
    gajakesari_pos = result.index("Gajakesari")
    assert ruchaka_pos < gajakesari_pos


# ---------------------------------------------------------------------------
# Test 5: Near-miss section present
# ---------------------------------------------------------------------------

def test_near_miss_heading_present():
    result = render_yogas_section({"yogas": SAMPLE_YOGAS, "doshas": []})
    assert "### Near-Miss Yogas" in result


def test_near_miss_table_header_present():
    result = _render_near_miss_yogas_table(SAMPLE_YOGAS)
    assert "| Yoga | Constituent | Tightness | Citation |" in result


def test_near_miss_contains_near_miss_yoga():
    result = _render_near_miss_yogas_table(SAMPLE_YOGAS)
    # Sasa: active=False, score=0.72 → near-miss
    assert "Sasa" in result


def test_near_miss_excludes_active_yoga():
    result = _render_near_miss_yogas_table(SAMPLE_YOGAS)
    # Gajakesari is active=True → must not appear in near-miss table
    assert "Gajakesari" not in result


def test_near_miss_excludes_low_score_inactive():
    result = _render_near_miss_yogas_table(SAMPLE_YOGAS)
    # Dhan Yoga: active=False, score=0.30 → below threshold
    assert "Dhan Yoga" not in result


# ---------------------------------------------------------------------------
# Test 6: Doshas section present
# ---------------------------------------------------------------------------

def test_doshas_section_heading_present():
    result = render_yogas_section({"yogas": [], "doshas": SAMPLE_DOSHAS})
    assert "### Doshas Register" in result


def test_doshas_table_header_present():
    result = _render_doshas_table(SAMPLE_DOSHAS)
    assert "| Dosha | Active | Constituent | Severity | Cancellations Applicable |" in result


def test_doshas_contains_mangal_dosha():
    result = _render_doshas_table(SAMPLE_DOSHAS)
    assert "Mangal Dosha" in result


def test_doshas_active_yes_no_format():
    result = _render_doshas_table(SAMPLE_DOSHAS)
    assert "Yes" in result
    assert "No" in result


def test_doshas_severity_capitalized():
    result = _render_doshas_table(SAMPLE_DOSHAS)
    assert "Moderate" in result or "Mild" in result or "Severe" in result


# ---------------------------------------------------------------------------
# Test 7: No narration verbs
# ---------------------------------------------------------------------------

def test_no_narration_verbs_full_section():
    result = render_yogas_section({"yogas": SAMPLE_YOGAS, "doshas": SAMPLE_DOSHAS})
    lint_narration(result)  # raises NarrationViolation if fails


# ---------------------------------------------------------------------------
# Test 8: Missing data → graceful
# ---------------------------------------------------------------------------

def test_yoga_missing_name_graceful():
    yogas = [{"active": True, "tightness_score": 0.9, "constituent": ["Sun"]}]
    result = _render_active_yogas_table(yogas)
    assert "N/A" in result


def test_yoga_missing_tightness_graceful():
    yogas = [{"name": "Test Yoga", "active": True, "constituent": ["Sun"]}]
    result = _render_active_yogas_table(yogas)
    assert "Test Yoga" in result
    assert "N/A" in result


def test_yoga_missing_constituent_graceful():
    yogas = [{"name": "Test Yoga", "active": True, "tightness_score": 0.8}]
    result = _render_active_yogas_table(yogas)
    assert "Test Yoga" in result


def test_dosha_missing_severity_graceful():
    doshas = [{"name": "Test Dosha", "active": True, "constituent": ["Mars"]}]
    result = _render_doshas_table(doshas)
    assert "Test Dosha" in result
    assert "N/A" in result


def test_dosha_empty_cancellations_graceful():
    doshas = [{"name": "Test Dosha", "active": False, "constituent": ["Rahu"], "severity": "mild", "cancellation_rules_applicable": []}]
    result = _render_doshas_table(doshas)
    assert "Test Dosha" in result
    assert "N/A" in result


# ---------------------------------------------------------------------------
# Test 9: Placeholder rows when empty
# ---------------------------------------------------------------------------

def test_active_yogas_placeholder_when_none_active():
    yogas = [_yoga("Some Yoga", False, 0.3)]
    result = _render_active_yogas_table(yogas)
    assert "| — |" in result


def test_near_miss_placeholder_when_none():
    yogas = [_yoga("Active Yoga", True, 0.9)]
    result = _render_near_miss_yogas_table(yogas)
    assert "| — |" in result


def test_doshas_placeholder_when_empty():
    result = _render_doshas_table([])
    assert "| — |" in result


# ---------------------------------------------------------------------------
# Test 10: Yoga category names representable
# ---------------------------------------------------------------------------

def test_gajakesari_name_representable():
    y = [_yoga("Gajakesari", True, 0.85, ["Moon", "Jupiter"], "BPHS Ch 36")]
    result = _render_active_yogas_table(y)
    assert "Gajakesari" in result


def test_pancha_mahapurusha_ruchaka_representable():
    y = [_yoga("Ruchaka", True, 0.9, ["Mars"], "BPHS Ch 36")]
    result = _render_active_yogas_table(y)
    assert "Ruchaka" in result


def test_pancha_mahapurusha_bhadra_representable():
    y = [_yoga("Bhadra", True, 0.8, ["Mercury"], "BPHS Ch 36")]
    result = _render_active_yogas_table(y)
    assert "Bhadra" in result


def test_pancha_mahapurusha_hamsa_representable():
    y = [_yoga("Hamsa", True, 0.75, ["Jupiter"], "BPHS Ch 36")]
    result = _render_active_yogas_table(y)
    assert "Hamsa" in result


def test_pancha_mahapurusha_malavya_representable():
    y = [_yoga("Malavya", True, 0.7, ["Venus"], "BPHS Ch 36")]
    result = _render_active_yogas_table(y)
    assert "Malavya" in result


def test_pancha_mahapurusha_sasa_near_miss():
    y = [_yoga("Sasa", False, 0.72, ["Saturn"], "BPHS Ch 36")]
    result = _render_near_miss_yogas_table(y)
    assert "Sasa" in result


def test_raj_yoga_representable():
    y = [_yoga("Raj Yoga", True, 0.6, ["Sun", "Moon"], "BPHS Ch 34")]
    result = _render_active_yogas_table(y)
    assert "Raj Yoga" in result


def test_dhan_yoga_representable():
    y = [_yoga("Dhan Yoga", True, 0.55, ["Jupiter", "Venus"], "BPHS Ch 35")]
    result = _render_active_yogas_table(y)
    assert "Dhan Yoga" in result


def test_vipareeta_raja_harsha_representable():
    y = [_yoga("Harsha Yoga", True, 0.65, ["Mars", "6H"], "BPHS Ch 76")]
    result = _render_active_yogas_table(y)
    assert "Harsha Yoga" in result


def test_vipareeta_raja_sarala_representable():
    y = [_yoga("Sarala Yoga", True, 0.60, ["Saturn", "8H"], "BPHS Ch 76")]
    result = _render_active_yogas_table(y)
    assert "Sarala Yoga" in result


def test_vipareeta_raja_vimala_representable():
    y = [_yoga("Vimala Yoga", True, 0.55, ["Venus", "12H"], "BPHS Ch 76")]
    result = _render_active_yogas_table(y)
    assert "Vimala Yoga" in result


def test_neechabhanga_representable():
    y = [_yoga("Neechabhanga", True, 0.7, ["Moon"], "Jataka Parijata")]
    result = _render_active_yogas_table(y)
    assert "Neechabhanga" in result


def test_sunafa_representable():
    y = [_yoga("Sunafa", False, 0.55, ["Moon"], "BPHS Ch 12")]
    result = _render_near_miss_yogas_table(y)
    assert "Sunafa" in result


def test_anapha_representable():
    y = [_yoga("Anapha", False, 0.58, ["Moon"], "BPHS Ch 12")]
    result = _render_near_miss_yogas_table(y)
    assert "Anapha" in result


def test_durdhura_representable():
    y = [_yoga("Durdhura", False, 0.62, ["Moon"], "BPHS Ch 12")]
    result = _render_near_miss_yogas_table(y)
    assert "Durdhura" in result


def test_kala_sarpa_representable():
    y = [_yoga("Kala Sarpa (Ananta)", False, 0.80, ["Rahu", "Ketu"], "BPHS Ch 13")]
    result = _render_near_miss_yogas_table(y)
    assert "Kala Sarpa" in result


# ---------------------------------------------------------------------------
# Test 11: All 14 canonical dosha names representable
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("dosha_name", [
    "Mangal Dosha",
    "Kaal Sarpa Dosha",
    "Pitru Dosha",
    "Matri Dosha",
    "Naga Dosha",
    "Sarpa Dosha",
    "Guru Chandal Dosha",
    "Grahan Dosha",
    "Daridra Dosha",
    "Shakata Dosha",
    "Vish Dosha",
    "Punarphoo Dosha",
    "Angarak Dosha",
    "Kemadrum Dosha",
])
def test_canonical_dosha_name_representable(dosha_name: str):
    d = [_dosha(dosha_name, True, ["Mars"], "moderate", ["Some cancellation"])]
    result = _render_doshas_table(d)
    assert dosha_name in result


# ---------------------------------------------------------------------------
# Test 12: Tightness formatting
# ---------------------------------------------------------------------------

def test_tightness_formatted_two_decimal_places():
    y = [_yoga("Test", True, 0.856789, ["Sun"])]
    result = _render_active_yogas_table(y)
    assert "0.86" in result


def test_tightness_none_graceful():
    y = [{"name": "Test", "active": True, "constituent": ["Sun"], "tightness_score": None}]
    result = _render_active_yogas_table(y)
    assert "N/A" in result


# ---------------------------------------------------------------------------
# Test 13: Constituent list formatting
# ---------------------------------------------------------------------------

def test_constituent_list_joined_with_comma():
    y = [_yoga("Test", True, 0.9, ["Moon", "Jupiter", "Venus"])]
    result = _render_active_yogas_table(y)
    assert "Moon, Jupiter, Venus" in result


def test_constituent_empty_list_graceful():
    y = [{"name": "Test", "active": True, "tightness_score": 0.9, "constituent": []}]
    result = _render_active_yogas_table(y)
    assert "N/A" in result


# ---------------------------------------------------------------------------
# Test 14: _fmt_bool_yn
# ---------------------------------------------------------------------------

def test_fmt_bool_yn_true():
    assert _fmt_bool_yn(True) == "Yes"


def test_fmt_bool_yn_false():
    assert _fmt_bool_yn(False) == "No"


def test_fmt_bool_yn_none():
    assert _fmt_bool_yn(None) == "N/A"


# ---------------------------------------------------------------------------
# Test 15: _fmt_severity
# ---------------------------------------------------------------------------

def test_fmt_severity_mild():
    assert _fmt_severity("mild") == "Mild"


def test_fmt_severity_moderate():
    assert _fmt_severity("moderate") == "Moderate"


def test_fmt_severity_severe():
    assert _fmt_severity("severe") == "Severe"


def test_fmt_severity_none():
    assert _fmt_severity(None) == "N/A"


def test_fmt_severity_na_string():
    assert _fmt_severity("N/A") == "N/A"


# ---------------------------------------------------------------------------
# Test 16: render_yogas_section return type
# ---------------------------------------------------------------------------

def test_render_yogas_section_returns_str():
    result = render_yogas_section({"yogas": SAMPLE_YOGAS, "doshas": SAMPLE_DOSHAS})
    assert isinstance(result, str)


def test_render_yogas_section_non_empty():
    result = render_yogas_section({"yogas": SAMPLE_YOGAS, "doshas": SAMPLE_DOSHAS})
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Test 17: NEAR_MISS_THRESHOLD constant
# ---------------------------------------------------------------------------

def test_near_miss_threshold_value():
    assert NEAR_MISS_THRESHOLD == 0.5


def test_yoga_exactly_at_threshold_not_near_miss():
    y = [_yoga("At Threshold", False, 0.5, ["Moon"])]
    result = _render_near_miss_yogas_table(y)
    assert "At Threshold" not in result


def test_yoga_just_above_threshold_is_near_miss():
    y = [_yoga("Just Above", False, 0.51, ["Moon"])]
    result = _render_near_miss_yogas_table(y)
    assert "Just Above" in result


# ---------------------------------------------------------------------------
# Test 18: CANONICAL_DOSHA_NAMES constant coverage
# ---------------------------------------------------------------------------

def test_canonical_dosha_names_contains_all_14():
    assert len(CANONICAL_DOSHA_NAMES) >= 14


def test_canonical_dosha_names_contains_mangal():
    assert "Mangal Dosha" in CANONICAL_DOSHA_NAMES


def test_canonical_dosha_names_contains_kemadrum():
    assert "Kemadrum Dosha" in CANONICAL_DOSHA_NAMES


# ---------------------------------------------------------------------------
# Test 19: Dosha severity N/A for inactive dosha
# ---------------------------------------------------------------------------

def test_dosha_na_severity_in_output():
    d = [_dosha("Matri Dosha", False, ["Moon"], "N/A", [])]
    result = _render_doshas_table(d)
    assert "N/A" in result


# ---------------------------------------------------------------------------
# Test 20: Full section includes all three table headings
# ---------------------------------------------------------------------------

def test_full_section_all_three_headings():
    result = render_yogas_section({"yogas": SAMPLE_YOGAS, "doshas": SAMPLE_DOSHAS})
    assert "### Active Yogas" in result
    assert "### Near-Miss Yogas" in result
    assert "### Doshas Register" in result
