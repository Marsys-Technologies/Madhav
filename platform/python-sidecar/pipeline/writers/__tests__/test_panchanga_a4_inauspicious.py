"""
Tests for emit_inauspicious_windows() — A4-S3.
"""
import pytest
from pipeline.writers.panchanga_writer_a4 import (
    emit_inauspicious_windows,
    RAHU_KALAM_POS,
    YAMAGANDA_POS,
    GULIKA_POS,
    _kalam_window,
)

# Native birth day: 1984-02-05, Sunday (weekday=0)
CHART_ID    = "test-chart-a4s3-00000000"
BUILD_ID    = "test-build-a4s3"
WEEKDAY_SUN = 0   # Sunday

SUNRISE_ISO = "1984-02-05T06:22:00"
SUNSET_ISO  = "1984-02-05T17:58:00"

EXPECTED_CATEGORIES = [
    "panchanga_rahu_kalam",
    "panchanga_yamaganda_kalam",
    "panchanga_gulika_kalam",
    "panchanga_durmuhurta",
    "panchanga_varjyam",
    "panchanga_visha_ghati",
    "panchanga_sashtighati",
    "panchanga_yamakantaka",
    "panchanga_krakaca",
]


@pytest.fixture
def rows():
    return emit_inauspicious_windows(
        CHART_ID, BUILD_ID, WEEKDAY_SUN, SUNRISE_ISO, SUNSET_ISO
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


def test_rahu_kalam_sunday_is_7th_eighth():
    """On Sunday, Rahu Kalam occupies the 7th eighth of the day."""
    assert RAHU_KALAM_POS[WEEKDAY_SUN] == 7

    from datetime import datetime
    s, e, _ = _kalam_window(SUNRISE_ISO, SUNSET_ISO, 7)
    sr = datetime.fromisoformat(SUNRISE_ISO)
    ss = datetime.fromisoformat(SUNSET_ISO)
    seg = (ss - sr).total_seconds() / 8

    expected_start = sr.timestamp() + 6 * seg
    expected_end   = sr.timestamp() + 7 * seg

    assert abs(datetime.fromisoformat(s).timestamp() - expected_start) < 1
    assert abs(datetime.fromisoformat(e).timestamp() - expected_end) < 1


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


def test_rahu_kalam_start_before_end(rows):
    from datetime import datetime
    rahu = [r for r in rows if r["fact_category"] == "panchanga_rahu_kalam"]
    starts = {r["fact_key"]: r["fact_value_text"] for r in rahu if r["fact_key"] == "start_iso"}
    ends   = {r["fact_key"]: r["fact_value_text"] for r in rahu if r["fact_key"] == "end_iso"}
    assert datetime.fromisoformat(starts["start_iso"]) < datetime.fromisoformat(ends["end_iso"])
