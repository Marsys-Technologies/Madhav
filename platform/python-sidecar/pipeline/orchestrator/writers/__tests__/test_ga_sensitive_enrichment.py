# test_ga_sensitive_enrichment.py
"""Tests for the 5 new Tier-1 classical sensitive point builder functions."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from ga_writers.ga_sensitive_writer import (
    _build_gulika_mandi_sensitive_rows,
    _build_sun_derived_upagrahas_rows,
    _build_special_lagnas_rows,
    _build_sphuta_completion_rows,
    _build_yogi_system_completion_rows,
)

CHART_ID = "test-chart-id"
AYA_ID = "lahiri"
BUILD_ID = "test-build"
ENG_VER = "1.0"

ALL_LONGS = {
    "SUN": 296.5,    # Capricorn
    "MOON": 332.0,   # Pisces / Purva Bhadrapada
    "MAR": 200.0,
    "MER": 280.0,
    "JUP": 240.0,
    "VEN": 310.0,
    "SAT": 210.0,
    "RAH_MEAN": 90.0,
    "KET_MEAN": 270.0,
    "LAGNA": 10.0,   # Aries
}

PANCHANGA_SUNDAY = {"vara": 0, "is_daytime": True, "tithi_id": 3}
CHART_DATA_EMPTY = {}


def test_gulika_mandi_returns_both_subjects():
    rows = _build_gulika_mandi_sensitive_rows(
        CHART_DATA_EMPTY, ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    subjects = {r["fact_subject"] for r in rows}
    assert "GULIKA" in subjects
    assert "MANDI" in subjects


def test_gulika_mandi_category():
    rows = _build_gulika_mandi_sensitive_rows(
        CHART_DATA_EMPTY, ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    for r in rows:
        assert r["fact_category"] == "sensitive_point_gulika_mandi"


def test_gulika_mandi_has_longitude_rows():
    rows = _build_gulika_mandi_sensitive_rows(
        CHART_DATA_EMPTY, ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    long_rows = [r for r in rows if r.get("fact_key") == "longitude_sidereal"]
    assert len(long_rows) >= 2


def test_sun_derived_all_four_subjects():
    rows = _build_sun_derived_upagrahas_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    subjects = {r["fact_subject"] for r in rows}
    for expected in ["KALA_SUN", "MRITYU_SUN", "ARTHA_PRAHARA", "YAMAGHANTAKA"]:
        assert expected in subjects, f"Missing {expected}"


def test_sun_derived_category():
    rows = _build_sun_derived_upagrahas_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    for r in rows:
        assert r["fact_category"] == "sun_derived_upagraha"


def test_sun_derived_two_pass_verified():
    rows = _build_sun_derived_upagrahas_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    for r in rows:
        assert r.get("verification_pass_status") == "two_pass_verified"


def test_special_lagnas_has_hora_ghati_bhava():
    rows = _build_special_lagnas_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    subjects = {r["fact_subject"] for r in rows}
    for expected in ["HORA_LAGNA", "GHATI_LAGNA", "BHAVA_LAGNA"]:
        assert expected in subjects, f"Missing {expected}"


def test_special_lagnas_vighati_is_floored():
    rows = _build_special_lagnas_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    vighati_rows = [r for r in rows if r.get("fact_subject") == "VIGHATI_LAGNA"]
    assert len(vighati_rows) >= 1
    for r in vighati_rows:
        assert r.get("verification_pass_status") == "floored"


def test_special_lagnas_others_two_pass_verified():
    rows = _build_special_lagnas_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    non_vighati = [r for r in rows if r.get("fact_subject") != "VIGHATI_LAGNA"]
    for r in non_vighati:
        assert r.get("verification_pass_status") == "two_pass_verified"


def test_sphuta_completion_both_subjects():
    rows = _build_sphuta_completion_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER)
    subjects = {r["fact_subject"] for r in rows}
    assert "BEEJA_SPHUTA" in subjects
    assert "KSHETRA_SPHUTA" in subjects


def test_sphuta_completion_category():
    rows = _build_sphuta_completion_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER)
    for r in rows:
        assert r["fact_category"] == "esoteric_point_sphuta_fertility"


def test_sphuta_completion_all_two_pass_verified():
    rows = _build_sphuta_completion_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER)
    for r in rows:
        assert r.get("verification_pass_status") == "two_pass_verified"


def test_yogi_system_has_yogi_graha_rows():
    rows = _build_yogi_system_completion_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    yogi_rows = [r for r in rows if r.get("fact_subject") == "YOGI_GRAHA"]
    assert len(yogi_rows) >= 3  # assigned_graha, nakshatra, yogi_point_longitude


def test_yogi_system_dagdha_rashi_sunday():
    rows = _build_yogi_system_completion_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    dagdha_rows = [r for r in rows if r.get("fact_subject", "").startswith("DAGDHA_RASHI_")]
    assert len(dagdha_rows) >= 2
    sign_values = {r.get("fact_value_text") for r in dagdha_rows}
    assert "Leo" in sign_values
    assert "Scorpio" in sign_values


def test_yogi_graha_is_valid_planet():
    rows = _build_yogi_system_completion_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    assigned_rows = [r for r in rows
                     if r.get("fact_subject") == "YOGI_GRAHA"
                     and r.get("fact_key") == "assigned_graha"]
    assert len(assigned_rows) == 1
    valid_planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    assert assigned_rows[0]["fact_value_text"] in valid_planets


def test_yogi_system_all_two_pass_verified():
    rows = _build_yogi_system_completion_rows(
        ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    for r in rows:
        assert r.get("verification_pass_status") == "two_pass_verified"
