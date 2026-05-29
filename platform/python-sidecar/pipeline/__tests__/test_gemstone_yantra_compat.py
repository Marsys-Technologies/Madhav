"""
test_gemstone_yantra_compat.py — Tests for G34/G35/G36 reference tables.

Coverage targets (≥35 assertions):
  G34 GEMSTONE_REFERENCE structure and data (assertions 1-16)
  G35 YANTRA_REFERENCE structure and data (assertions 17-22)
  G36 ASHTA_KOOTA + totals (assertions 23-28)
  NAKSHATRA_GANA (assertions 29-33)
  NAKSHATRA_NADI (assertions 34-38)
  Functions: get_gemstone, get_compatible_yantras (assertions 39-42)
  compute_gana_score (assertions 43-47)
  compute_nadi_score (assertions 48-53)
  Helper functions (assertions 54-56)
"""

import pytest

from pipeline.gemstone_yantra_compat import (
    ASHTA_KOOTA,
    ASHTA_KOOTA_MAX_TOTAL,
    COMPATIBILITY_THRESHOLDS,
    GEMSTONE_REFERENCE,
    NAKSHATRA_GANA,
    NAKSHATRA_NADI,
    YANTRA_REFERENCE,
    compute_ashta_koota_total_max,
    compute_gana_score,
    compute_nadi_score,
    get_compatible_yantras,
    get_compatibility_grade,
    get_gemstone,
    get_nakshatra_gana,
    get_nakshatra_nadi,
)


# ---------------------------------------------------------------------------
# G34 — GEMSTONE_REFERENCE
# ---------------------------------------------------------------------------

class TestGemstoneReference:

    def test_has_nine_grahas(self):
        # Assertion 1
        assert len(GEMSTONE_REFERENCE) == 9

    def test_all_navagraha_keys_present(self):
        # Assertion 2
        expected = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
        assert set(GEMSTONE_REFERENCE.keys()) == expected

    def test_sun_primary_stone_ruby(self):
        # Assertion 3
        assert GEMSTONE_REFERENCE["sun"]["primary_stone"] == "Ruby"

    def test_moon_primary_stone_contains_pearl(self):
        # Assertion 4
        assert "Pearl" in GEMSTONE_REFERENCE["moon"]["primary_stone"]

    def test_mars_primary_stone_red_coral(self):
        # Assertion 5
        assert "Coral" in GEMSTONE_REFERENCE["mars"]["primary_stone"]

    def test_mercury_primary_stone_emerald(self):
        # Assertion 6
        assert GEMSTONE_REFERENCE["mercury"]["primary_stone"] == "Emerald"

    def test_jupiter_primary_stone_yellow_sapphire(self):
        # Assertion 7
        assert "Sapphire" in GEMSTONE_REFERENCE["jupiter"]["primary_stone"]

    def test_jupiter_finger_index(self):
        # Assertion 8
        assert GEMSTONE_REFERENCE["jupiter"]["finger"] == "index"

    def test_venus_primary_stone_diamond(self):
        # Assertion 9
        assert GEMSTONE_REFERENCE["venus"]["primary_stone"] == "Diamond"

    def test_saturn_primary_stone_blue_sapphire(self):
        # Assertion 10
        assert "Sapphire" in GEMSTONE_REFERENCE["saturn"]["primary_stone"]

    def test_rahu_primary_stone_hessonite(self):
        # Assertion 11
        assert GEMSTONE_REFERENCE["rahu"]["primary_stone"] == "Hessonite"

    def test_ketu_primary_stone_cats_eye(self):
        # Assertion 12
        assert "Eye" in GEMSTONE_REFERENCE["ketu"]["primary_stone"]

    def test_every_graha_has_substitute_stones_list(self):
        # Assertion 13
        for graha, data in GEMSTONE_REFERENCE.items():
            assert isinstance(data["substitute_stones"], list), f"{graha} missing substitute_stones list"
            assert len(data["substitute_stones"]) >= 2, f"{graha} has fewer than 2 substitutes"

    def test_every_graha_has_activation_mantra(self):
        # Assertion 14
        for graha, data in GEMSTONE_REFERENCE.items():
            assert "Namah" in data["activation_mantra"], f"{graha} mantra seems incomplete"

    def test_every_graha_has_weight_range(self):
        # Assertion 15
        for graha, data in GEMSTONE_REFERENCE.items():
            assert data["weight_ratti_min"] > 0
            assert data["weight_ratti_max"] >= data["weight_ratti_min"]

    def test_every_graha_has_classical_citation(self):
        # Assertion 16
        for graha, data in GEMSTONE_REFERENCE.items():
            assert data["classical_citation"], f"{graha} missing classical citation"

    def test_get_gemstone_function_returns_dict(self):
        # Assertion 39
        result = get_gemstone("jupiter")
        assert isinstance(result, dict)
        assert result["primary_stone"] == "Yellow Sapphire"

    def test_get_gemstone_case_insensitive(self):
        # Assertion 40
        assert get_gemstone("SUN") == get_gemstone("sun")

    def test_get_gemstone_invalid_raises_key_error(self):
        # Assertion 41
        with pytest.raises(KeyError):
            get_gemstone("pluto")


# ---------------------------------------------------------------------------
# G35 — YANTRA_REFERENCE
# ---------------------------------------------------------------------------

class TestYantraReference:

    def test_has_at_least_ten_entries(self):
        # Assertion 17
        assert len(YANTRA_REFERENCE) >= 10

    def test_contains_all_nine_graha_yantras(self):
        # Assertion 18
        graha_names = {y.get("graha") for y in YANTRA_REFERENCE if "graha" in y}
        expected = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
        assert expected == graha_names

    def test_sri_yantra_present(self):
        # Assertion 19
        names = [y["name"] for y in YANTRA_REFERENCE]
        assert any("Sri Yantra" in name for name in names)

    def test_vastu_yantra_present(self):
        # Assertion 20
        names = [y["name"] for y in YANTRA_REFERENCE]
        assert any("Vastu" in name for name in names)

    def test_every_yantra_has_mantra_syllables(self):
        # Assertion 21
        for y in YANTRA_REFERENCE:
            assert y.get("mantra_syllables"), f"{y['name']} missing mantra_syllables"

    def test_every_yantra_has_structure_description(self):
        # Assertion 22
        for y in YANTRA_REFERENCE:
            assert y.get("structure_description"), f"{y['name']} missing structure_description"

    def test_get_compatible_yantras_returns_list(self):
        # Assertion 42
        result = get_compatible_yantras("wealth")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_get_compatible_yantras_marriage(self):
        # Extra: verify marriage keyword finds Venus Yantra at minimum
        result = get_compatible_yantras("marriage")
        names = [y["name"] for y in result]
        assert any("Venus" in n for n in names)

    def test_get_compatible_yantras_no_match_returns_empty(self):
        # Extra: nonsense keyword
        result = get_compatible_yantras("xyznonexistent")
        assert result == []


# ---------------------------------------------------------------------------
# G36 — ASHTA_KOOTA
# ---------------------------------------------------------------------------

class TestAshtaKoota:

    def test_has_exactly_eight_kootas(self):
        # Assertion 23
        assert len(ASHTA_KOOTA) == 8

    def test_all_eight_koota_keys_present(self):
        # Assertion 24
        expected = {"varna", "vashya", "tara", "yoni", "graha_maitri", "gana", "bhakoot", "nadi"}
        assert set(ASHTA_KOOTA.keys()) == expected

    def test_max_points_sum_equals_36(self):
        # Assertion 25
        total = sum(v["max_points"] for v in ASHTA_KOOTA.values())
        assert total == 36

    def test_nadi_has_max_points_8(self):
        # Assertion 26
        assert ASHTA_KOOTA["nadi"]["max_points"] == 8

    def test_gana_has_max_points_6(self):
        # Assertion 27
        assert ASHTA_KOOTA["gana"]["max_points"] == 6

    def test_varna_has_max_points_1(self):
        # Assertion 28
        assert ASHTA_KOOTA["varna"]["max_points"] == 1

    def test_ashta_koota_max_total_constant_equals_36(self):
        # Assertion 54
        assert ASHTA_KOOTA_MAX_TOTAL == 36

    def test_compute_ashta_koota_total_max_function(self):
        # Assertion 55
        assert compute_ashta_koota_total_max() == 36

    def test_compatibility_grade_excellent(self):
        # Assertion 56
        assert get_compatibility_grade(33) == "excellent"

    def test_compatibility_grade_good(self):
        assert get_compatibility_grade(28) == "good"

    def test_compatibility_grade_average(self):
        assert get_compatibility_grade(22) == "average"

    def test_compatibility_grade_poor(self):
        assert get_compatibility_grade(10) == "poor"

    def test_each_koota_has_description(self):
        for koota, data in ASHTA_KOOTA.items():
            assert data.get("description"), f"{koota} missing description"

    def test_each_koota_has_scoring_rule(self):
        for koota, data in ASHTA_KOOTA.items():
            assert data.get("scoring_rule"), f"{koota} missing scoring_rule"


# ---------------------------------------------------------------------------
# NAKSHATRA_GANA
# ---------------------------------------------------------------------------

class TestNakshatraGana:

    def test_has_27_entries(self):
        # Assertion 29
        assert len(NAKSHATRA_GANA) == 27

    def test_all_keys_1_to_27(self):
        # Assertion 30
        assert set(NAKSHATRA_GANA.keys()) == set(range(1, 28))

    def test_ashwini_1_is_deva(self):
        # Assertion 31
        assert NAKSHATRA_GANA[1] == "deva"

    def test_krittika_3_is_rakshasa(self):
        # Assertion 32
        assert NAKSHATRA_GANA[3] == "rakshasa"

    def test_bharani_2_is_manushya(self):
        # Assertion 33
        assert NAKSHATRA_GANA[2] == "manushya"

    def test_only_three_gana_values_used(self):
        gana_vals = set(NAKSHATRA_GANA.values())
        assert gana_vals == {"deva", "manushya", "rakshasa"}

    def test_pushya_8_is_deva(self):
        assert NAKSHATRA_GANA[8] == "deva"

    def test_magha_10_is_rakshasa(self):
        assert NAKSHATRA_GANA[10] == "rakshasa"

    def test_revati_27_is_deva(self):
        assert NAKSHATRA_GANA[27] == "deva"

    def test_get_nakshatra_gana_function(self):
        assert get_nakshatra_gana(1) == "deva"
        assert get_nakshatra_gana(3) == "rakshasa"
        assert get_nakshatra_gana(2) == "manushya"

    def test_get_nakshatra_gana_invalid_raises(self):
        with pytest.raises(KeyError):
            get_nakshatra_gana(28)


# ---------------------------------------------------------------------------
# NAKSHATRA_NADI
# ---------------------------------------------------------------------------

class TestNakshatraNadi:

    def test_has_27_entries(self):
        # Assertion 34
        assert len(NAKSHATRA_NADI) == 27

    def test_all_keys_1_to_27(self):
        # Assertion 35
        assert set(NAKSHATRA_NADI.keys()) == set(range(1, 28))

    def test_adi_group_is_1_4_7_10_13_16_19_22_25(self):
        # Assertion 36
        adi_naks = [n for n, v in NAKSHATRA_NADI.items() if v == "adi"]
        assert sorted(adi_naks) == [1, 4, 7, 10, 13, 16, 19, 22, 25]

    def test_madhya_group_is_2_5_8_11_14_17_20_23_26(self):
        # Assertion 37
        madhya_naks = [n for n, v in NAKSHATRA_NADI.items() if v == "madhya"]
        assert sorted(madhya_naks) == [2, 5, 8, 11, 14, 17, 20, 23, 26]

    def test_antya_group_is_3_6_9_12_15_18_21_24_27(self):
        # Assertion 38
        antya_naks = [n for n, v in NAKSHATRA_NADI.items() if v == "antya"]
        assert sorted(antya_naks) == [3, 6, 9, 12, 15, 18, 21, 24, 27]

    def test_only_three_nadi_values_used(self):
        nadi_vals = set(NAKSHATRA_NADI.values())
        assert nadi_vals == {"adi", "madhya", "antya"}

    def test_each_nadi_has_exactly_nine_nakshatras(self):
        from collections import Counter
        counts = Counter(NAKSHATRA_NADI.values())
        assert counts["adi"] == 9
        assert counts["madhya"] == 9
        assert counts["antya"] == 9

    def test_get_nakshatra_nadi_function(self):
        assert get_nakshatra_nadi(1) == "adi"
        assert get_nakshatra_nadi(2) == "madhya"
        assert get_nakshatra_nadi(3) == "antya"

    def test_get_nakshatra_nadi_invalid_raises(self):
        with pytest.raises(KeyError):
            get_nakshatra_nadi(0)


# ---------------------------------------------------------------------------
# compute_gana_score
# ---------------------------------------------------------------------------

class TestComputeGanaScore:

    def test_deva_deva_equals_6(self):
        # Assertion 43 — Ashwini(1)=deva, Pushya(8)=deva
        assert compute_gana_score(1, 8) == 6

    def test_manushya_manushya_equals_6(self):
        # Assertion 44 — Bharani(2)=manushya, Ardra(6)=manushya
        assert compute_gana_score(2, 6) == 6

    def test_rakshasa_rakshasa_equals_6(self):
        # Assertion 45 — Krittika(3)=rakshasa, Rohini(4)=rakshasa
        assert compute_gana_score(3, 4) == 6

    def test_deva_manushya_equals_5(self):
        # Assertion 46 — Ashwini(1)=deva, Bharani(2)=manushya
        assert compute_gana_score(1, 2) == 5

    def test_manushya_rakshasa_equals_1(self):
        # Assertion 47 — Bharani(2)=manushya, Krittika(3)=rakshasa
        assert compute_gana_score(2, 3) == 1

    def test_deva_rakshasa_equals_0(self):
        # Ashwini(1)=deva, Krittika(3)=rakshasa
        assert compute_gana_score(1, 3) == 0

    def test_rakshasa_deva_equals_0(self):
        # Reverse: Krittika(3)=rakshasa, Ashwini(1)=deva
        assert compute_gana_score(3, 1) == 0

    def test_manushya_deva_equals_5(self):
        # Bharani(2)=manushya, Ashwini(1)=deva
        assert compute_gana_score(2, 1) == 5

    def test_score_is_non_negative_integer(self):
        for boy in range(1, 28):
            for girl in range(1, 28):
                score = compute_gana_score(boy, girl)
                assert isinstance(score, int)
                assert 0 <= score <= 6


# ---------------------------------------------------------------------------
# compute_nadi_score
# ---------------------------------------------------------------------------

class TestComputeNadiScore:

    def test_same_nadi_adi_adi_equals_0(self):
        # Assertion 48 — Ashwini(1)=adi, Rohini(4)=adi — Nadi Dosha
        assert compute_nadi_score(1, 4) == 0

    def test_same_nadi_madhya_madhya_equals_0(self):
        # Assertion 49 — Bharani(2)=madhya, Mrigashira(5)=madhya
        assert compute_nadi_score(2, 5) == 0

    def test_same_nadi_antya_antya_equals_0(self):
        # Assertion 50 — Krittika(3)=antya, Ardra(6)=antya
        assert compute_nadi_score(3, 6) == 0

    def test_different_nadi_adi_madhya_equals_8(self):
        # Assertion 51 — Ashwini(1)=adi, Bharani(2)=madhya
        assert compute_nadi_score(1, 2) == 8

    def test_different_nadi_adi_antya_equals_8(self):
        # Assertion 52 — Ashwini(1)=adi, Krittika(3)=antya
        assert compute_nadi_score(1, 3) == 8

    def test_different_nadi_madhya_antya_equals_8(self):
        # Assertion 53 — Bharani(2)=madhya, Krittika(3)=antya
        assert compute_nadi_score(2, 3) == 8

    def test_nadi_score_only_0_or_8(self):
        for boy in range(1, 28):
            for girl in range(1, 28):
                score = compute_nadi_score(boy, girl)
                assert score in (0, 8), f"Unexpected nadi score {score} for nak {boy},{girl}"

    def test_same_nakshatra_same_nadi_is_zero(self):
        # Same nakshatra → same nadi → Nadi Dosha
        for n in range(1, 28):
            assert compute_nadi_score(n, n) == 0

    def test_known_antya_pair_27_3_equals_0(self):
        # Revati(27)=antya, Krittika(3)=antya
        assert compute_nadi_score(27, 3) == 0

    def test_adi_25_madhya_26_equals_8(self):
        # Purva Bhadra(25)=adi, Uttara Bhadra(26)=madhya
        assert compute_nadi_score(25, 26) == 8
