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

# M-10 fix: _build_special_lagnas_rows now delegates to chart_data["special_lagnas"]
# (PyJHora-native), rather than computing hand-rolled Sun-offset proxies. Mock
# a populated dict matching pyjhora_adapter.special_lagnas.compute_special_lagnas().
CHART_DATA_SPECIAL_LAGNAS = {
    "special_lagnas": {
        "bhava_lagna": {"longitude_deg": 12.3, "sign": "Aries", "sign_id": 1, "degree_in_sign": 12.3},
        "hora_lagna": {"longitude_deg": 60.8, "sign": "Gemini", "sign_id": 3, "degree_in_sign": 0.8},
        "ghati_lagna": {"longitude_deg": 254.1, "sign": "Sagittarius", "sign_id": 9, "degree_in_sign": 14.1},
        "vighati_lagna": {"longitude_deg": 197.8, "sign": "Libra", "sign_id": 7, "degree_in_sign": 17.8},
        "indu_lagna": {"longitude_deg": 237.0, "sign": "Scorpio", "sign_id": 8, "degree_in_sign": 27.0},
        "sree_lagna": {"longitude_deg": 202.9, "sign": "Libra", "sign_id": 7, "degree_in_sign": 22.9},
        "varnada_lagna": {"longitude_deg": 102.4, "sign": "Cancer", "sign_id": 4, "degree_in_sign": 12.4},
    }
}


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
        CHART_DATA_SPECIAL_LAGNAS, ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    subjects = {r["fact_subject"] for r in rows}
    for expected in ["HORA_LAGNA", "GHATI_LAGNA", "BHAVA_LAGNA"]:
        assert expected in subjects, f"Missing {expected}"


def test_special_lagnas_indu_sree_varnada_added():
    """M-10: Indu/Sree/Varnada Lagna are newly delegated (previously absent)."""
    rows = _build_special_lagnas_rows(
        CHART_DATA_SPECIAL_LAGNAS, ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    subjects = {r["fact_subject"] for r in rows}
    for expected in ["INDU_LAGNA", "SREE_LAGNA", "VARNADA_LAGNA"]:
        assert expected in subjects, f"Missing {expected}"


def test_special_lagnas_vighati_is_delegated_not_floored():
    """M-10: Vighati Lagna is now delegated to PyJHora (drik.vighati_lagna),
    which derives it from the birth JD directly — no longer floored for lack
    of sub-second precision."""
    rows = _build_special_lagnas_rows(
        CHART_DATA_SPECIAL_LAGNAS, ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    vighati_rows = [r for r in rows if r.get("fact_subject") == "VIGHATI_LAGNA"]
    assert len(vighati_rows) >= 1
    for r in vighati_rows:
        assert r.get("verification_pass_status") == "two_pass_verified"


def test_special_lagnas_others_two_pass_verified():
    # M-10 fix (R6-1d) supersedes the M-22/R6-1f stamp demotion this test
    # previously encoded: HORA_LAGNA/GHATI_LAGNA/BHAVA_LAGNA no longer use
    # the fabricated Sun-within-sign-offset proxy that justified downgrading
    # them to "documented_approximation" — they are now delegated to
    # PyJHora's real time-since-sunrise derivation (drik.hora_lagna /
    # drik.ghati_lagna / drik.bhava_lagna) via chart_data["special_lagnas"],
    # same as VIGHATI_LAGNA/INDU_LAGNA/SREE_LAGNA/VARNADA_LAGNA. With a real
    # independent computation now backing every subject, the honest tier is
    # "two_pass_verified", not a demoted stamp on a fabricated formula that
    # no longer exists in this writer.
    rows = _build_special_lagnas_rows(
        CHART_DATA_SPECIAL_LAGNAS, ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    non_vighati = [r for r in rows if r.get("fact_subject") != "VIGHATI_LAGNA"]
    assert non_vighati, "expected HORA_LAGNA/GHATI_LAGNA/BHAVA_LAGNA rows"
    for r in non_vighati:
        assert r.get("verification_pass_status") == "two_pass_verified"


def test_special_lagnas_floors_when_native_absent():
    """M-10: with no chart_data['special_lagnas'] (PyJHora unavailable), every
    subject floors rather than serving a fabricated Sun-offset substitute."""
    rows = _build_special_lagnas_rows(
        CHART_DATA_EMPTY, ALL_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, PANCHANGA_SUNDAY)
    assert len(rows) > 0
    for r in rows:
        assert r.get("verification_pass_status") == "floored"
        assert r.get("fact_value_num") is None


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


# ---------------------------------------------------------------------------
# Regression: AK divergence must NOT halt the writer (ValueError → warning)
# ---------------------------------------------------------------------------
# Scenario mirrors Abhinandan Mohanty 1c826d5a: Parashari AK = Mercury,
# KN Rao AK = Rahu (Rahu's reverse-degree > Mercury's degree in sign).
# Previously _build_karaka_rows raised ValueError on divergence; that halt
# was removed in cf38e029. These tests lock in the non-fatal behaviour.

from ga_writers.ga_sensitive_writer import _build_karaka_rows

_AK_DIV_LONGS = {
    # Mercury at 29.0° in sign → Parashari AK (highest non-Rahu degree)
    "MER": 29.0,
    # Rahu at 0.5° in sign → reverse-degree = 30 - 0.5 = 29.5° → KN Rao AK
    "RAH_MEAN": 0.5,
    # All other grahas well below Mercury
    "SUN": 10.0,
    "MOON": 12.0,
    "MAR": 5.0,
    "JUP": 8.0,
    "VEN": 15.0,
    "SAT": 3.0,
    "KET_MEAN": 180.5,
    "LAGNA": 10.0,
}


def test_ak_divergence_does_not_raise():
    """AK divergence (Parashari ≠ KN Rao) must log a warning, never raise."""
    rows = _build_karaka_rows(
        _AK_DIV_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, halt_log_path="/dev/null"
    )
    assert len(rows) > 0, "Expected karaka rows even with AK divergence"


def test_ak_divergence_emits_both_schools():
    """Both Parashari and KN Rao schools are emitted when AK diverges."""
    rows = _build_karaka_rows(
        _AK_DIV_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, halt_log_path="/dev/null"
    )
    schools = {r.get("formula_id") for r in rows}
    assert "parashari_rahu_excluded" in schools
    assert "kn_rao_rahu_included" in schools


def test_ak_divergence_parashari_ak_is_mercury():
    """Parashari AK is Mercury (highest degree in sign excluding Rahu)."""
    rows = _build_karaka_rows(
        _AK_DIV_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, halt_log_path="/dev/null"
    )
    parashari_ak = [
        r for r in rows
        if r.get("formula_id") == "parashari_rahu_excluded"
        and r.get("fact_subject") == "ATMAKARAKA"
        and r.get("fact_key") == "assigned_graha"
    ]
    assert len(parashari_ak) == 1
    assert parashari_ak[0]["fact_value_text"] == "Mercury"


def test_ak_divergence_knrao_ak_is_rahu():
    """KN Rao AK is Rahu (reverse-degree reckoning gives Rahu the highest effective degree)."""
    rows = _build_karaka_rows(
        _AK_DIV_LONGS, CHART_ID, AYA_ID, BUILD_ID, ENG_VER, halt_log_path="/dev/null"
    )
    knrao_ak = [
        r for r in rows
        if r.get("formula_id") == "kn_rao_rahu_included"
        and r.get("fact_subject") == "ATMAKARAKA"
        and r.get("fact_key") == "assigned_graha"
    ]
    assert len(knrao_ak) == 1
    assert knrao_ak[0]["fact_value_text"] == "Rahu"
