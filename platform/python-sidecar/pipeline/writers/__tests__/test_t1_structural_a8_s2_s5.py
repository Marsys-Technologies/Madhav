"""
Tests for A8-S2 through A8-S5 writers:
  shadbala_writer.py       (G3-02)
  ashtakavarga_writer.py   (G3-03)
  yoga_register_writer.py  (G3-04 part 1)
  dosha_register_writer.py (G3-04 part 2)
  vimsopaka_writer.py      (G3-05)

All tests use unittest.mock.MagicMock() — no real DB required.
"""
import pytest
from unittest.mock import MagicMock, patch

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pipeline.writers.shadbala_writer import (
    write as shadbala_write,
    NAISARGIKA_BALA,
    REQUIRED_SHADBALA,
    _rows_for_graha,
    _build_rows,
)
from pipeline.writers.ashtakavarga_writer import (
    write as ashtakavarga_write,
    _build_bav_rows,
    _build_sav_rows,
    _build_sodhita_rows,
    _CONTRIBUTORS,
    _SIGN_ORDER,
)
from pipeline.writers.yoga_register_writer import (
    write as yoga_write,
    _rows_for_yoga,
    _yoga_subject,
)
from pipeline.writers.dosha_register_writer import (
    write as dosha_write,
    _rows_for_dosha,
    _dosha_subject,
)
from pipeline.writers.vimsopaka_writer import (
    write as vimsopaka_write,
    _build_vimsopaka_rows,
    _build_avastha_rows,
    _VARGA_GROUPS,
    _AVASTHA_SCHEMES,
    _ALL_GRAHAS,
)

# ── Constants ─────────────────────────────────────────────────────────────────
CHART_ID = "chart-test-abcdef12"
AY_ID = "lahiri"
BUILD_ID = "bld-test-001"


def _run_write(writer_fn, chart_output, chart_id=CHART_ID, ayanamsha_id=AY_ID, build_id=BUILD_ID):
    conn = MagicMock()
    with patch(f"{writer_fn.__module__}._upsert_chart_facts") as mock_upsert:
        result = writer_fn(build_id, chart_id, ayanamsha_id, chart_output, conn)
        rows = mock_upsert.call_args[0][1] if mock_upsert.called else []
    return result, rows


# ═══════════════════════════════════════════════════════════════════════════════
# SHADBALA TESTS (A8-S2 / G3-02)
# ═══════════════════════════════════════════════════════════════════════════════

class TestShadbala:

    def test_shadbala_write_returns_int(self):
        result, _ = _run_write(shadbala_write, {})
        assert isinstance(result, int)

    def test_shadbala_empty_chart_output_returns_nonzero(self):
        """Absent shadbala → still writes 9 grahas × 9 rows = 81 rows."""
        result, rows = _run_write(shadbala_write, {})
        assert result == 81
        assert len(rows) == 81

    def test_shadbala_with_data_returns_81_rows(self):
        chart_output = {
            "shadbala": {
                "sun": {"sthana_bala": 120.0, "dig_bala": 60.0, "kala_bala": 45.0,
                        "chesta_bala": 30.0, "drik_bala": -10.0},
            }
        }
        result, rows = _run_write(shadbala_write, chart_output)
        assert result == 81

    def test_naisargika_bala_sun_is_60(self):
        assert NAISARGIKA_BALA["sun"] == 60.0

    def test_naisargika_bala_saturn_is_8_57(self):
        assert abs(NAISARGIKA_BALA["saturn"] - 8.57) < 0.01

    def test_naisargika_bala_moon_is_51_43(self):
        assert abs(NAISARGIKA_BALA["moon"] - 51.43) < 0.01

    def test_naisargika_bala_mars_is_17_14(self):
        assert abs(NAISARGIKA_BALA["mars"] - 17.14) < 0.01

    def test_naisargika_bala_rahu_is_0(self):
        assert NAISARGIKA_BALA["rahu"] == 0.0

    def test_naisargika_bala_ketu_is_0(self):
        assert NAISARGIKA_BALA["ketu"] == 0.0

    def test_required_shadbala_mercury_is_420(self):
        assert REQUIRED_SHADBALA["mercury"] == 420.0

    def test_required_shadbala_sun_is_390(self):
        assert REQUIRED_SHADBALA["sun"] == 390.0

    def test_required_shadbala_moon_is_360(self):
        assert REQUIRED_SHADBALA["moon"] == 360.0

    def test_required_shadbala_rahu_is_0(self):
        assert REQUIRED_SHADBALA["rahu"] == 0.0

    def test_shadbala_rows_for_graha_sun_has_9_rows(self):
        rows = _rows_for_graha(CHART_ID, AY_ID, BUILD_ID, "sun", {})
        assert len(rows) == 9

    def test_shadbala_rows_include_all_fact_keys(self):
        rows = _rows_for_graha(CHART_ID, AY_ID, BUILD_ID, "sun", {})
        fact_keys = [r[10] for r in rows]  # fact_key is index 10
        assert "sthana_bala" in fact_keys
        assert "dig_bala" in fact_keys
        assert "kala_bala" in fact_keys
        assert "chesta_bala" in fact_keys
        assert "naisargika_bala" in fact_keys
        assert "drik_bala" in fact_keys
        assert "total_shadbala" in fact_keys
        assert "required_shadbala" in fact_keys
        assert "shadbala_ratio" in fact_keys

    def test_shadbala_naisargika_uses_constant_when_absent(self):
        rows = _rows_for_graha(CHART_ID, AY_ID, BUILD_ID, "sun", {})
        naisargika_row = next(r for r in rows if r[10] == "naisargika_bala")
        # value_number is index 12
        assert naisargika_row[12] == 60.0

    def test_shadbala_ratio_zero_when_required_is_zero(self):
        rows = _rows_for_graha(CHART_ID, AY_ID, BUILD_ID, "rahu", {})
        ratio_row = next(r for r in rows if r[10] == "shadbala_ratio")
        assert ratio_row[12] == 0.0

    def test_shadbala_total_is_sum_of_sub_balas(self):
        bala = {"sthana_bala": 100.0, "dig_bala": 50.0, "kala_bala": 40.0,
                "chesta_bala": 30.0, "drik_bala": -5.0}
        rows = _rows_for_graha(CHART_ID, AY_ID, BUILD_ID, "sun", bala)
        total_row = next(r for r in rows if r[10] == "total_shadbala")
        # total = 100 + 50 + 40 + 30 + 60 (naisargika) + (-5)
        assert abs(total_row[12] - 275.0) < 0.01

    def test_shadbala_ratio_computed_correctly(self):
        bala = {"sthana_bala": 200.0, "dig_bala": 0.0, "kala_bala": 0.0,
                "chesta_bala": 0.0, "drik_bala": 0.0}
        rows = _rows_for_graha(CHART_ID, AY_ID, BUILD_ID, "sun", bala)
        ratio_row = next(r for r in rows if r[10] == "shadbala_ratio")
        # total = 200 + 60 naisargika = 260, required = 390, ratio = 260/390
        expected = 260.0 / 390.0
        assert abs(ratio_row[12] - expected) < 0.001

    def test_shadbala_fact_category_is_shadbala(self):
        rows = _rows_for_graha(CHART_ID, AY_ID, BUILD_ID, "sun", {})
        for r in rows:
            assert r[8] == "shadbala"  # fact_category index

    def test_shadbala_all_9_grahas_present(self):
        rows = _build_rows(CHART_ID, AY_ID, BUILD_ID, {})
        subjects = {r[9] for r in rows}  # fact_subject index
        for graha in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]:
            assert graha in subjects


# ═══════════════════════════════════════════════════════════════════════════════
# ASHTAKAVARGA TESTS (A8-S3 / G3-03)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAshtakavarga:

    def test_ashtakavarga_write_returns_int(self):
        result, _ = _run_write(ashtakavarga_write, {})
        assert isinstance(result, int)

    def test_ashtakavarga_empty_chart_output_returns_1_placeholder(self):
        result, rows = _run_write(ashtakavarga_write, {})
        assert result == 1
        assert len(rows) == 1

    def test_ashtakavarga_placeholder_value_text_is_not_computed(self):
        _, rows = _run_write(ashtakavarga_write, {})
        assert rows[0][11] == "not_computed"  # value_text index

    def test_ashtakavarga_placeholder_value_number_is_0(self):
        _, rows = _run_write(ashtakavarga_write, {})
        assert rows[0][12] == 0.0

    def test_ashtakavarga_bav_full_data_stores_96_rows(self):
        """8 contributors × 12 signs = 96 BAV rows."""
        bav = {}
        for contributor in _CONTRIBUTORS:
            bav[contributor] = {sign: 4 for sign in _SIGN_ORDER}
        chart_output = {"ashtakavarga": {"bav": bav}}
        result, rows = _run_write(ashtakavarga_write, chart_output)
        assert result == 96

    def test_ashtakavarga_bav_rows_correct_count(self):
        bav = {}
        for contributor in _CONTRIBUTORS:
            bav[contributor] = {sign: i % 9 for i, sign in enumerate(_SIGN_ORDER)}
        rows = _build_bav_rows(CHART_ID, AY_ID, BUILD_ID, bav)
        assert len(rows) == 96

    def test_ashtakavarga_sav_12_rows(self):
        sav = {sign: 28 for sign in _SIGN_ORDER}
        rows = _build_sav_rows(CHART_ID, AY_ID, BUILD_ID, sav)
        assert len(rows) == 12

    def test_ashtakavarga_sodhita_12_rows(self):
        sodhita = {sign: 22 for sign in _SIGN_ORDER}
        rows = _build_sodhita_rows(CHART_ID, AY_ID, BUILD_ID, sodhita)
        assert len(rows) == 12

    def test_ashtakavarga_sav_plus_bav_count(self):
        bav = {c: {s: 3 for s in _SIGN_ORDER} for c in _CONTRIBUTORS}
        sav = {s: 24 for s in _SIGN_ORDER}
        chart_output = {"ashtakavarga": {"bav": bav, "sav": sav}}
        result, rows = _run_write(ashtakavarga_write, chart_output)
        assert result == 108  # 96 BAV + 12 SAV

    def test_ashtakavarga_fact_category(self):
        bav = {c: {s: 4 for s in _SIGN_ORDER} for c in _CONTRIBUTORS}
        rows = _build_bav_rows(CHART_ID, AY_ID, BUILD_ID, bav)
        for r in rows:
            assert r[8] == "ashtakavarga"

    def test_ashtakavarga_bav_list_format_accepted(self):
        """BAV can also be a list of 12 values per contributor."""
        bav = {c: [4] * 12 for c in _CONTRIBUTORS}
        rows = _build_bav_rows(CHART_ID, AY_ID, BUILD_ID, bav)
        assert len(rows) == 96

    def test_ashtakavarga_sav_subject_is_sav(self):
        sav = {sign: 28 for sign in _SIGN_ORDER}
        rows = _build_sav_rows(CHART_ID, AY_ID, BUILD_ID, sav)
        for r in rows:
            assert r[9] == "sav"

    def test_ashtakavarga_sodhita_subject_is_sodhita_sav(self):
        sodhita = {sign: 22 for sign in _SIGN_ORDER}
        rows = _build_sodhita_rows(CHART_ID, AY_ID, BUILD_ID, sodhita)
        for r in rows:
            assert r[9] == "sodhita_sav"

    def test_ashtakavarga_bav_key_format(self):
        """fact_key should be bav_{sign}_{house_num}."""
        bav = {"sun": {sign: 4 for sign in _SIGN_ORDER}}
        rows = _build_bav_rows(CHART_ID, AY_ID, BUILD_ID, bav)
        sun_rows = [r for r in rows if r[9] == "sun"]
        assert sun_rows[0][10] == "bav_aries_1"
        assert sun_rows[-1][10] == "bav_pisces_12"


# ═══════════════════════════════════════════════════════════════════════════════
# YOGA REGISTER TESTS (A8-S4 / G3-04)
# ═══════════════════════════════════════════════════════════════════════════════

class TestYogaRegister:

    def test_yoga_write_returns_int(self):
        result, _ = _run_write(yoga_write, {})
        assert isinstance(result, int)

    def test_yoga_empty_returns_1_placeholder(self):
        result, rows = _run_write(yoga_write, {})
        assert result == 1

    def test_yoga_empty_list_returns_placeholder(self):
        result, rows = _run_write(yoga_write, {"yogas": []})
        assert result == 1

    def test_yoga_active_stored_as_yes(self):
        chart_output = {"yogas": [
            {"name": "Raja Yoga", "active": True, "tightness": 0.85,
             "constituents": ["jupiter", "saturn"], "classical_citation": "BPHS Ch 34"}
        ]}
        _, rows = _run_write(yoga_write, chart_output)
        active_rows = [r for r in rows if r[10] == "active"]
        assert len(active_rows) == 1
        assert active_rows[0][11] == "yes"  # value_text

    def test_yoga_inactive_stored_as_no(self):
        chart_output = {"yogas": [
            {"name": "Dhana Yoga", "active": False, "tightness": 0.0,
             "constituents": ["jupiter"], "classical_citation": "BPHS"}
        ]}
        _, rows = _run_write(yoga_write, chart_output)
        active_rows = [r for r in rows if r[10] == "active"]
        assert active_rows[0][11] == "no"

    def test_yoga_active_value_number_is_1_for_active(self):
        chart_output = {"yogas": [
            {"name": "Raja Yoga", "active": True, "tightness": 0.9, "constituents": []}
        ]}
        _, rows = _run_write(yoga_write, chart_output)
        active_rows = [r for r in rows if r[10] == "active"]
        assert active_rows[0][12] == 1.0

    def test_yoga_tightness_stored(self):
        chart_output = {"yogas": [
            {"name": "Gaja Kesari", "active": True, "tightness": 0.72, "constituents": ["jupiter", "moon"]}
        ]}
        _, rows = _run_write(yoga_write, chart_output)
        tightness_rows = [r for r in rows if r[10] == "tightness"]
        assert abs(tightness_rows[0][12] - 0.72) < 0.001

    def test_yoga_constituent_stored_as_comma_joined(self):
        chart_output = {"yogas": [
            {"name": "Gaja Kesari", "active": True, "tightness": 0.5,
             "constituents": ["jupiter", "moon"]}
        ]}
        _, rows = _run_write(yoga_write, chart_output)
        constituent_rows = [r for r in rows if r[10] == "constituent"]
        assert "jupiter" in constituent_rows[0][11]
        assert "moon" in constituent_rows[0][11]

    def test_yoga_3_rows_per_yoga(self):
        chart_output = {"yogas": [
            {"name": "Raja Yoga", "active": True, "tightness": 0.8, "constituents": ["sun"]}
        ]}
        result, rows = _run_write(yoga_write, chart_output)
        assert result == 3

    def test_yoga_subject_normalised(self):
        assert _yoga_subject("Raja Yoga") == "raja_yoga"
        assert _yoga_subject("Gaja-Kesari") == "gaja_kesari"

    def test_yoga_fact_category_is_yoga_register(self):
        rows = _rows_for_yoga(CHART_ID, AY_ID, BUILD_ID,
                              {"name": "Test Yoga", "active": True, "tightness": 0.5,
                               "constituents": []})
        for r in rows:
            assert r[8] == "yoga_register"

    def test_yoga_multiple_yogas_correct_row_count(self):
        chart_output = {"yogas": [
            {"name": "Yoga A", "active": True, "tightness": 0.9, "constituents": []},
            {"name": "Yoga B", "active": False, "tightness": 0.1, "constituents": ["mars"]},
            {"name": "Yoga C", "active": True, "tightness": 0.5, "constituents": ["venus", "jupiter"]},
        ]}
        result, _ = _run_write(yoga_write, chart_output)
        assert result == 9  # 3 yogas × 3 rows each


# ═══════════════════════════════════════════════════════════════════════════════
# DOSHA REGISTER TESTS (A8-S4 / G3-04)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDoshaRegister:

    def test_dosha_write_returns_int(self):
        result, _ = _run_write(dosha_write, {})
        assert isinstance(result, int)

    def test_dosha_empty_returns_placeholder(self):
        result, rows = _run_write(dosha_write, {})
        assert result == 1

    def test_dosha_empty_list_returns_placeholder(self):
        result, rows = _run_write(dosha_write, {"doshas": []})
        assert result == 1

    def test_dosha_active_stored_as_yes(self):
        chart_output = {"doshas": [
            {"name": "Mangal Dosha", "active": True, "severity": "high",
             "tightness": 0.9, "constituents": ["mars"]}
        ]}
        _, rows = _run_write(dosha_write, chart_output)
        active_rows = [r for r in rows if r[10] == "active"]
        assert active_rows[0][11] == "yes"

    def test_dosha_severity_stored(self):
        chart_output = {"doshas": [
            {"name": "Mangal Dosha", "active": True, "severity": "moderate",
             "tightness": 0.5, "constituents": ["mars", "saturn"]}
        ]}
        _, rows = _run_write(dosha_write, chart_output)
        severity_rows = [r for r in rows if r[10] == "severity"]
        assert severity_rows[0][11] == "moderate"

    def test_dosha_severity_high_value_is_3(self):
        chart_output = {"doshas": [
            {"name": "Kaal Sarpa", "active": True, "severity": "high",
             "tightness": 0.95, "constituents": []}
        ]}
        _, rows = _run_write(dosha_write, chart_output)
        severity_rows = [r for r in rows if r[10] == "severity"]
        assert severity_rows[0][12] == 3.0

    def test_dosha_4_rows_per_dosha(self):
        chart_output = {"doshas": [
            {"name": "Mangal Dosha", "active": True, "severity": "high",
             "tightness": 0.9, "constituents": ["mars"]}
        ]}
        result, rows = _run_write(dosha_write, chart_output)
        assert result == 4

    def test_dosha_fact_category_is_dosha_register(self):
        rows = _rows_for_dosha(CHART_ID, AY_ID, BUILD_ID,
                               {"name": "Test Dosha", "active": True, "severity": "low",
                                "tightness": 0.2, "constituents": []})
        for r in rows:
            assert r[8] == "dosha_register"

    def test_dosha_subject_normalised(self):
        assert _dosha_subject("Mangal Dosha") == "mangal_dosha"
        assert _dosha_subject("Kaal-Sarpa") == "kaal_sarpa"

    def test_dosha_constituent_stored(self):
        chart_output = {"doshas": [
            {"name": "Mangal Dosha", "active": True, "severity": "high",
             "tightness": 0.9, "constituents": ["mars", "saturn"]}
        ]}
        _, rows = _run_write(dosha_write, chart_output)
        constituent_rows = [r for r in rows if r[10] == "constituent"]
        assert "mars" in constituent_rows[0][11]

    def test_dosha_tightness_stored(self):
        chart_output = {"doshas": [
            {"name": "Mangal Dosha", "active": True, "severity": "high",
             "tightness": 0.77, "constituents": []}
        ]}
        _, rows = _run_write(dosha_write, chart_output)
        tightness_rows = [r for r in rows if r[10] == "tightness"]
        assert abs(tightness_rows[0][12] - 0.77) < 0.001


# ═══════════════════════════════════════════════════════════════════════════════
# VIMSOPAKA + AVASTHA TESTS (A8-S5 / G3-05)
# ═══════════════════════════════════════════════════════════════════════════════

class TestVimsopaka:

    def test_vimsopaka_write_returns_int(self):
        result, _ = _run_write(vimsopaka_write, {})
        assert isinstance(result, int)

    def test_vimsopaka_empty_chart_output_returns_2_placeholders(self):
        """No vimsopaka AND no avasthas → 2 placeholder rows."""
        result, rows = _run_write(vimsopaka_write, {})
        assert result == 2

    def test_vimsopaka_score_stored_per_graha(self):
        vimsopaka_data = {
            "sun": {"saptavarga": 15.5, "dashavarga": 12.0, "shadvarga": 10.0, "shodasavarga": 8.0}
        }
        rows = _build_vimsopaka_rows(CHART_ID, AY_ID, BUILD_ID, vimsopaka_data)
        sun_rows = [r for r in rows if r[9] == "sun"]
        assert len(sun_rows) == 4

    def test_vimsopaka_all_4_varga_groups_present(self):
        vimsopaka_data = {
            "sun": {"saptavarga": 15.5, "dashavarga": 12.0, "shadvarga": 10.0, "shodasavarga": 8.0}
        }
        rows = _build_vimsopaka_rows(CHART_ID, AY_ID, BUILD_ID, vimsopaka_data)
        sun_rows = [r for r in rows if r[9] == "sun"]
        fact_keys = {r[10] for r in sun_rows}
        for vg in _VARGA_GROUPS:
            assert vg in fact_keys

    def test_vimsopaka_fact_category(self):
        vimsopaka_data = {"sun": {"saptavarga": 15.0}}
        rows = _build_vimsopaka_rows(CHART_ID, AY_ID, BUILD_ID, vimsopaka_data)
        for r in rows:
            assert r[8] == "vimsopaka"

    def test_vimsopaka_full_data_9_grahas_4_groups_36_rows(self):
        vimsopaka_data = {
            g: {"saptavarga": 10.0, "dashavarga": 8.0, "shadvarga": 6.0, "shodasavarga": 4.0}
            for g in _ALL_GRAHAS
        }
        rows = _build_vimsopaka_rows(CHART_ID, AY_ID, BUILD_ID, vimsopaka_data)
        assert len(rows) == 36  # 9 grahas × 4 groups

    def test_vimsopaka_score_value_number_correct(self):
        vimsopaka_data = {"sun": {"saptavarga": 18.75}}
        rows = _build_vimsopaka_rows(CHART_ID, AY_ID, BUILD_ID, vimsopaka_data)
        saptavarga_row = next(r for r in rows if r[9] == "sun" and r[10] == "saptavarga")
        assert abs(saptavarga_row[12] - 18.75) < 0.001

    def test_avastha_scheme_names_in_output(self):
        avastha_data = {
            "sun": {"baladi": "bala", "jagradadi": "jagrad",
                    "deeptadi": "deepta", "lajjitadi": "lajjita", "shayanaadi": "shayana"}
        }
        rows = _build_avastha_rows(CHART_ID, AY_ID, BUILD_ID, avastha_data)
        sun_rows = [r for r in rows if r[9] == "sun"]
        assert len(sun_rows) == 5
        fact_keys = {r[10] for r in sun_rows}
        for scheme in _AVASTHA_SCHEMES:
            assert scheme in fact_keys

    def test_avastha_value_text_stored(self):
        avastha_data = {"moon": {"baladi": "kumara"}}
        rows = _build_avastha_rows(CHART_ID, AY_ID, BUILD_ID, avastha_data)
        moon_baladi = next(r for r in rows if r[9] == "moon" and r[10] == "baladi")
        assert moon_baladi[11] == "kumara"

    def test_avastha_fact_category(self):
        avastha_data = {"sun": {"baladi": "bala"}}
        rows = _build_avastha_rows(CHART_ID, AY_ID, BUILD_ID, avastha_data)
        for r in rows:
            assert r[8] == "avastha"

    def test_avastha_full_data_9_grahas_5_schemes_45_rows(self):
        avastha_data = {
            g: {s: "test_state" for s in _AVASTHA_SCHEMES}
            for g in _ALL_GRAHAS
        }
        rows = _build_avastha_rows(CHART_ID, AY_ID, BUILD_ID, avastha_data)
        assert len(rows) == 45  # 9 grahas × 5 schemes

    def test_vimsopaka_present_avastha_absent_correct_count(self):
        chart_output = {
            "vimsopaka": {
                g: {"saptavarga": 10.0, "dashavarga": 8.0, "shadvarga": 6.0, "shodasavarga": 4.0}
                for g in _ALL_GRAHAS
            }
        }
        result, rows = _run_write(vimsopaka_write, chart_output)
        # 36 vimsopaka rows + 1 avastha placeholder
        assert result == 37

    def test_both_absent_returns_2(self):
        result, rows = _run_write(vimsopaka_write, {})
        assert result == 2

    def test_both_present_correct_count(self):
        chart_output = {
            "vimsopaka": {
                g: {"saptavarga": 10.0, "dashavarga": 8.0, "shadvarga": 6.0, "shodasavarga": 4.0}
                for g in _ALL_GRAHAS
            },
            "avasthas": {
                g: {s: "state" for s in _AVASTHA_SCHEMES}
                for g in _ALL_GRAHAS
            },
        }
        result, rows = _run_write(vimsopaka_write, chart_output)
        assert result == 81  # 36 + 45
