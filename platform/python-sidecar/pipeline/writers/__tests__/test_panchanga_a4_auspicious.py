"""
Tests for emit_auspicious_windows() — A4-S4.
"""
import pytest
from pipeline.writers.panchanga_writer_a4 import emit_auspicious_windows

# Native birth day: 1984-02-05, Sunday (weekday=0)
CHART_ID    = "test-chart-a4s4-00000000"
BUILD_ID    = "test-build-a4s4"
WEEKDAY_SUN = 0   # Sunday

SUNRISE_ISO = "1984-02-05T06:22:00"
SUNSET_ISO  = "1984-02-05T17:58:00"

EXPECTED_CATEGORIES = [
    "panchanga_abhijit_muhurta",
    "panchanga_brahma_muhurta",
    "panchanga_pratah_sandhya",
    "panchanga_madhyahna_sandhya",
    "panchanga_sayam_sandhya",
    "panchanga_amrit_kaal",
    "panchanga_vijaya_muhurta",
    "panchanga_godhuli_muhurta",
    "panchanga_nishita_kala",
]


@pytest.fixture
def rows():
    return emit_auspicious_windows(
        CHART_ID, BUILD_ID, WEEKDAY_SUN, SUNRISE_ISO, SUNSET_ISO
    )


@pytest.fixture
def rows_wednesday():
    return emit_auspicious_windows(
        CHART_ID, BUILD_ID, 3, SUNRISE_ISO, SUNSET_ISO, is_wednesday=True
    )


def test_nine_categories_emitted(rows):
    emitted = {r["fact_category"] for r in rows}
    assert emitted == set(EXPECTED_CATEGORIES), (
        f"Missing: {set(EXPECTED_CATEGORIES) - emitted}"
    )


def test_all_have_start_iso(rows):
    for cat in EXPECTED_CATEGORIES:
        cat_rows = [r for r in rows if r["fact_category"] == cat]
        keys = {r["fact_key"] for r in cat_rows}
        assert "start_iso" in keys, f"{cat} missing start_iso"


def test_all_have_end_iso(rows):
    for cat in EXPECTED_CATEGORIES:
        cat_rows = [r for r in rows if r["fact_category"] == cat]
        keys = {r["fact_key"] for r in cat_rows}
        assert "end_iso" in keys, f"{cat} missing end_iso"


def test_all_have_duration_minutes(rows):
    for cat in EXPECTED_CATEGORIES:
        cat_rows = [r for r in rows if r["fact_category"] == cat]
        keys = {r["fact_key"] for r in cat_rows}
        assert "duration_minutes" in keys, f"{cat} missing duration_minutes"


def test_all_two_pass_verified(rows):
    for r in rows:
        assert r["verification_pass_status"] == "two_pass_verified", (
            f"{r['fact_category']}/{r['fact_key']} has status {r['verification_pass_status']!r}"
        )


def test_ayanamsha_invariant(rows):
    for r in rows:
        assert r["ayanamsha_id"] == "INVARIANT", (
            f"{r['fact_category']}/{r['fact_key']} has ayanamsha_id {r['ayanamsha_id']!r}"
        )


def test_abhijit_has_applicable_flag(rows):
    abhijit = [r for r in rows if r["fact_category"] == "panchanga_abhijit_muhurta"]
    keys = {r["fact_key"] for r in abhijit}
    assert "applicable_flag" in keys, "abhijit_muhurta missing applicable_flag key"


def test_abhijit_wednesday_flag_false(rows_wednesday):
    abhijit = [r for r in rows_wednesday if r["fact_category"] == "panchanga_abhijit_muhurta"]
    flag_row = next(r for r in abhijit if r["fact_key"] == "applicable_flag")
    assert flag_row["fact_value_text"] == "False", (
        f"Expected 'False' on Wednesday, got {flag_row['fact_value_text']!r}"
    )


def test_abhijit_non_wednesday_flag_true(rows):
    abhijit = [r for r in rows if r["fact_category"] == "panchanga_abhijit_muhurta"]
    flag_row = next(r for r in abhijit if r["fact_key"] == "applicable_flag")
    assert flag_row["fact_value_text"] == "True", (
        f"Expected 'True' on non-Wednesday, got {flag_row['fact_value_text']!r}"
    )


def test_row_structure(rows):
    """Each row has the required schema keys."""
    required = {
        "fact_id", "chart_id", "ayanamsha_id", "build_id",
        "fact_category", "fact_subject", "fact_key",
        "fact_value_num", "fact_value_text",
        "citation_ref", "citation_human", "source_calculation",
        "verification_pass_status", "engine_version", "computed_at",
    }
    for r in rows:
        missing = required - r.keys()
        assert not missing, f"Row {r['fact_category']}/{r['fact_key']} missing keys: {missing}"


def test_fact_ids_unique(rows):
    ids = [r["fact_id"] for r in rows]
    assert len(ids) == len(set(ids)), "Duplicate fact_ids detected"


def test_brahma_muhurta_before_sunrise(rows):
    from datetime import datetime
    brahma = [r for r in rows if r["fact_category"] == "panchanga_brahma_muhurta"]
    end_row = next(r for r in brahma if r["fact_key"] == "end_iso")
    sr = datetime.fromisoformat(SUNRISE_ISO)
    end_dt = datetime.fromisoformat(end_row["fact_value_text"])
    assert end_dt <= sr, f"Brahma muhurta end {end_dt} should be <= sunrise {sr}"
