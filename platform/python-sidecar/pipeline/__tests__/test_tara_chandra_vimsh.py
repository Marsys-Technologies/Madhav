"""
Tests for G22/G23/G24 — tara_chandra_vimsh.py
==============================================
Covers TARA_BALA_MATRIX, CHANDRA_BALA_MATRIX, VIMSHOTTARI_START
and all public functions. Minimum 35 assertions.
"""

import pytest

from pipeline.tara_chandra_vimsh import (
    # G22
    TARA_BALA_MATRIX,
    TARA_CLASSES,
    TARA_BENEFIC,
    TARA_MALEFIC,
    get_tara_bala,
    is_tara_benefic,
    # G23
    CHANDRA_BALA_MATRIX,
    CHANDRA_CLASS_MAP,
    get_chandra_bala,
    # G24
    VIMSHOTTARI_START,
    get_vimshottari_start,
    compute_vimshottari_elapsed_fraction,
)


# ===========================================================================
# G22 — Tara Bala Matrix (27×27)
# ===========================================================================

class TestTaraBalMatrix:
    def test_matrix_has_27_natal_keys(self):
        assert len(TARA_BALA_MATRIX) == 27

    def test_each_natal_has_27_transit_entries(self):
        for natal in range(1, 28):
            assert len(TARA_BALA_MATRIX[natal]) == 27, \
                f"natal {natal} has {len(TARA_BALA_MATRIX[natal])} entries"

    def test_all_values_are_valid_tara_classes(self):
        valid = set(TARA_CLASSES)
        for natal, row in TARA_BALA_MATRIX.items():
            for transit, cls in row.items():
                assert cls in valid, \
                    f"invalid class '{cls}' at natal={natal} transit={transit}"

    def test_same_nakshatra_is_janma(self):
        # When natal == transit count = 1 → janma
        for nak in range(1, 28):
            assert get_tara_bala(nak, nak) == "janma"

    def test_get_tara_bala_1_1_janma(self):
        assert get_tara_bala(1, 1) == "janma"

    def test_get_tara_bala_1_2_sampat(self):
        assert get_tara_bala(1, 2) == "sampat"

    def test_get_tara_bala_1_3_vipat(self):
        assert get_tara_bala(1, 3) == "vipat"

    def test_get_tara_bala_1_4_kshema(self):
        assert get_tara_bala(1, 4) == "kshema"

    def test_get_tara_bala_1_5_pratyak(self):
        assert get_tara_bala(1, 5) == "pratyak"

    def test_get_tara_bala_1_6_sadhaka(self):
        assert get_tara_bala(1, 6) == "sadhaka"

    def test_get_tara_bala_1_7_vadha(self):
        assert get_tara_bala(1, 7) == "vadha"

    def test_get_tara_bala_1_8_mitra(self):
        assert get_tara_bala(1, 8) == "mitra"

    def test_get_tara_bala_1_9_atimitra(self):
        assert get_tara_bala(1, 9) == "atimitra"

    def test_cycle_repeats_at_10(self):
        # count 10 → (10-1)%9=0 → janma
        assert get_tara_bala(1, 10) == "janma"

    def test_wrap_around_natal_27_transit_1(self):
        # natal=27, transit=1: count = ((1-27) % 27) + 1 = 2 → sampat
        assert get_tara_bala(27, 1) == "sampat"

    def test_natal_5_transit_5_janma(self):
        assert get_tara_bala(5, 5) == "janma"

    def test_natal_5_transit_12_sampat(self):
        # count = ((12-5)%27)+1 = 8 → mitra
        assert get_tara_bala(5, 12) == "mitra"

    def test_benefic_set_size(self):
        assert len(TARA_BENEFIC) == 5

    def test_malefic_set_size(self):
        assert len(TARA_MALEFIC) == 4

    def test_benefic_malefic_disjoint(self):
        assert TARA_BENEFIC.isdisjoint(TARA_MALEFIC)

    def test_is_tara_benefic_sampat(self):
        assert is_tara_benefic("sampat") is True

    def test_is_tara_benefic_kshema(self):
        assert is_tara_benefic("kshema") is True

    def test_is_tara_benefic_sadhaka(self):
        assert is_tara_benefic("sadhaka") is True

    def test_is_tara_benefic_mitra(self):
        assert is_tara_benefic("mitra") is True

    def test_is_tara_benefic_atimitra(self):
        assert is_tara_benefic("atimitra") is True

    def test_is_tara_benefic_janma_false(self):
        assert is_tara_benefic("janma") is False

    def test_is_tara_benefic_vipat_false(self):
        assert is_tara_benefic("vipat") is False

    def test_is_tara_benefic_pratyak_false(self):
        assert is_tara_benefic("pratyak") is False

    def test_is_tara_benefic_vadha_false(self):
        assert is_tara_benefic("vadha") is False

    def test_invalid_natal_raises(self):
        with pytest.raises(ValueError):
            get_tara_bala(0, 5)

    def test_invalid_transit_raises(self):
        with pytest.raises(ValueError):
            get_tara_bala(5, 28)


# ===========================================================================
# G23 — Chandra Bala Matrix (12×12)
# ===========================================================================

class TestChandraBalMatrix:
    def test_matrix_has_12_natal_keys(self):
        assert len(CHANDRA_BALA_MATRIX) == 12

    def test_each_natal_has_12_transit_entries(self):
        for natal in range(1, 13):
            assert len(CHANDRA_BALA_MATRIX[natal]) == 12

    def test_all_values_valid_classes(self):
        valid = {"favorable", "neutral", "unfavorable"}
        for natal, row in CHANDRA_BALA_MATRIX.items():
            for transit, cls in row.items():
                assert cls in valid, \
                    f"invalid class '{cls}' at natal={natal} transit={transit}"

    def test_same_sign_is_favorable(self):
        # count=1 → favorable
        for sign in range(1, 13):
            assert get_chandra_bala(sign, sign) == "favorable"

    def test_get_chandra_bala_1_1_favorable(self):
        assert get_chandra_bala(1, 1) == "favorable"

    def test_get_chandra_bala_1_7_favorable(self):
        # count = ((7-1)%12)+1 = 7 → favorable
        assert get_chandra_bala(1, 7) == "favorable"

    def test_get_chandra_bala_1_6_unfavorable(self):
        # count = ((6-1)%12)+1 = 6 → unfavorable
        assert get_chandra_bala(1, 6) == "unfavorable"

    def test_get_chandra_bala_1_12_unfavorable(self):
        # count = ((12-1)%12)+1 = 12 → unfavorable
        assert get_chandra_bala(1, 12) == "unfavorable"

    def test_get_chandra_bala_1_3_favorable(self):
        # count = 3 → favorable
        assert get_chandra_bala(1, 3) == "favorable"

    def test_get_chandra_bala_1_11_favorable(self):
        # count = 11 → favorable
        assert get_chandra_bala(1, 11) == "favorable"

    def test_wrap_around(self):
        # natal=12, transit=1: count = ((1-12)%12)+1 = 2 → neutral
        assert get_chandra_bala(12, 1) == "neutral"

    def test_favorable_count_per_natal(self):
        # Positions 1,3,7,11 are favorable → 4 per natal sign
        for natal in range(1, 13):
            favorable = sum(
                1 for cls in CHANDRA_BALA_MATRIX[natal].values()
                if cls == "favorable"
            )
            assert favorable == 4, f"natal {natal} should have 4 favorable"

    def test_unfavorable_count_per_natal(self):
        # Positions 6,12 are unfavorable → 2 per natal sign
        for natal in range(1, 13):
            unfavorable = sum(
                1 for cls in CHANDRA_BALA_MATRIX[natal].values()
                if cls == "unfavorable"
            )
            assert unfavorable == 2, f"natal {natal} should have 2 unfavorable"

    def test_invalid_natal_raises(self):
        with pytest.raises(ValueError):
            get_chandra_bala(0, 6)

    def test_invalid_transit_raises(self):
        with pytest.raises(ValueError):
            get_chandra_bala(1, 13)

    def test_chandra_class_map_has_12_entries(self):
        assert len(CHANDRA_CLASS_MAP) == 12


# ===========================================================================
# G24 — Vimshottari Start Table
# ===========================================================================

class TestVimshottariStart:
    def test_table_has_27_entries(self):
        assert len(VIMSHOTTARI_START) == 27

    def test_nakshatra_1_ketu(self):
        assert get_vimshottari_start(1)["lord"] == "ketu"

    def test_nakshatra_1_years_7(self):
        assert get_vimshottari_start(1)["years"] == 7

    def test_nakshatra_2_venus(self):
        assert get_vimshottari_start(2)["lord"] == "venus"

    def test_nakshatra_2_years_20(self):
        assert get_vimshottari_start(2)["years"] == 20

    def test_nakshatra_3_sun(self):
        assert get_vimshottari_start(3)["lord"] == "sun"

    def test_nakshatra_4_moon(self):
        assert get_vimshottari_start(4)["lord"] == "moon"

    def test_nakshatra_5_mars(self):
        assert get_vimshottari_start(5)["lord"] == "mars"

    def test_nakshatra_6_rahu(self):
        assert get_vimshottari_start(6)["lord"] == "rahu"

    def test_nakshatra_7_jupiter(self):
        assert get_vimshottari_start(7)["lord"] == "jupiter"

    def test_nakshatra_8_saturn(self):
        assert get_vimshottari_start(8)["lord"] == "saturn"

    def test_nakshatra_9_mercury(self):
        assert get_vimshottari_start(9)["lord"] == "mercury"

    def test_nakshatra_10_ketu_cycle_repeats(self):
        # Cycle repeats: 10 = 1+9 → ketu
        assert get_vimshottari_start(10)["lord"] == "ketu"

    def test_nakshatra_19_ketu_third_cycle(self):
        # 19 = 1+18 → ketu
        assert get_vimshottari_start(19)["lord"] == "ketu"

    def test_nakshatra_27_mercury(self):
        assert get_vimshottari_start(27)["lord"] == "mercury"

    def test_total_years_across_all_27_is_360(self):
        # 27 nakshatras = 3 full dasha cycles × 120 years
        total = sum(v["years"] for v in VIMSHOTTARI_START.values())
        assert total == 360

    def test_single_cycle_years_sum_120(self):
        # 9 consecutive nakshatras (1-9) sum to 120
        total = sum(get_vimshottari_start(n)["years"] for n in range(1, 10))
        assert total == 120

    def test_invalid_nakshatra_raises(self):
        with pytest.raises(ValueError):
            get_vimshottari_start(0)

    def test_invalid_nakshatra_28_raises(self):
        with pytest.raises(ValueError):
            get_vimshottari_start(28)

    def test_all_lords_are_strings(self):
        for nak, entry in VIMSHOTTARI_START.items():
            assert isinstance(entry["lord"], str), f"nak {nak} lord not str"

    def test_all_years_are_positive_ints(self):
        for nak, entry in VIMSHOTTARI_START.items():
            assert isinstance(entry["years"], int), f"nak {nak} years not int"
            assert entry["years"] > 0, f"nak {nak} years <= 0"


# ===========================================================================
# G24 — compute_vimshottari_elapsed_fraction
# ===========================================================================

class TestVimshottariElapsedFraction:
    def test_pada_1_returns_0(self):
        assert compute_vimshottari_elapsed_fraction(1, 1) == 0.0

    def test_pada_2_returns_025(self):
        assert compute_vimshottari_elapsed_fraction(1, 2) == pytest.approx(0.25)

    def test_pada_3_returns_050(self):
        assert compute_vimshottari_elapsed_fraction(1, 3) == pytest.approx(0.50)

    def test_pada_4_returns_075(self):
        assert compute_vimshottari_elapsed_fraction(1, 4) == pytest.approx(0.75)

    def test_fraction_independent_of_nakshatra(self):
        # Fraction logic depends only on pada
        for nak in [1, 9, 14, 27]:
            assert compute_vimshottari_elapsed_fraction(nak, 1) == 0.0
            assert compute_vimshottari_elapsed_fraction(nak, 4) == pytest.approx(0.75)

    def test_invalid_pada_raises(self):
        with pytest.raises(ValueError):
            compute_vimshottari_elapsed_fraction(1, 0)

    def test_invalid_pada_5_raises(self):
        with pytest.raises(ValueError):
            compute_vimshottari_elapsed_fraction(1, 5)

    def test_invalid_nakshatra_raises(self):
        with pytest.raises(ValueError):
            compute_vimshottari_elapsed_fraction(0, 1)
