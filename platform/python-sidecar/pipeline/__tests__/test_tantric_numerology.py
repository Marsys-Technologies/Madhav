"""
test_tantric_numerology.py — Tests for G46 (tantric correspondences) and
G47 (numerology overlays) in tantric_numerology.py.

Minimum 25 assertions required per session acceptance criteria.
"""

import pytest
from pipeline.tantric_numerology import (
    CHAKRA_GRAHA_MAP,
    SRIVIDYA_TRIANGLE,
    PYTHAGOREAN_NUMEROLOGY,
    CHALDEAN_NUMEROLOGY,
    VEDIC_ANKJYOTISH,
    GRAHA_NUMBER,
    get_chakra,
    compute_pythagorean_name_number,
    compute_chaldean_name_number,
    reduce_to_single_digit,
    get_graha_number,
    get_nakshatra_number,
)


# ---------------------------------------------------------------------------
# G46 — CHAKRA_GRAHA_MAP structural tests
# ---------------------------------------------------------------------------

class TestChakraGrahaMap:
    def test_map_has_nine_grahas(self):
        """CHAKRA_GRAHA_MAP must contain exactly 9 grahas."""
        assert len(CHAKRA_GRAHA_MAP) == 9  # assertion 1

    def test_all_nine_grahas_present(self):
        """All nine standard grahas must be present as keys."""
        expected = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
        assert set(CHAKRA_GRAHA_MAP.keys()) == expected  # assertion 2

    def test_sun_chakra_manipura(self):
        assert get_chakra("sun")["chakra"] == "manipura"  # assertion 3

    def test_sun_chakra_number(self):
        assert get_chakra("sun")["chakra_number"] == 3  # assertion 4

    def test_sun_element_fire(self):
        assert get_chakra("sun")["element"] == "fire"  # assertion 5

    def test_moon_chakra_svadhisthana(self):
        assert get_chakra("moon")["chakra"] == "svadhisthana"  # assertion 6

    def test_moon_element_water(self):
        assert get_chakra("moon")["element"] == "water"  # assertion 7

    def test_moon_bija_vam(self):
        assert get_chakra("moon")["bija_mantra"] == "VAM"  # assertion 8

    def test_mars_chakra_muladhara(self):
        assert get_chakra("mars")["chakra"] == "muladhara"  # assertion 9

    def test_mercury_chakra_vishuddha(self):
        assert get_chakra("mercury")["chakra"] == "vishuddha"  # assertion 10

    def test_jupiter_chakra_ajna(self):
        assert get_chakra("jupiter")["chakra"] == "ajna"  # assertion 11

    def test_venus_chakra_anahata(self):
        assert get_chakra("venus")["chakra"] == "anahata"  # assertion 12

    def test_saturn_chakra_sahasrara(self):
        assert get_chakra("saturn")["chakra"] == "sahasrara"  # assertion 13

    def test_saturn_element_cosmic_consciousness(self):
        assert get_chakra("saturn")["element"] == "cosmic consciousness"  # assertion 14

    def test_rahu_chakra_ajna(self):
        assert get_chakra("rahu")["chakra_number"] == 6  # assertion 15

    def test_ketu_chakra_sahasrara(self):
        assert get_chakra("ketu")["chakra_number"] == 7  # assertion 16

    def test_get_chakra_case_insensitive(self):
        """get_chakra should normalize input to lowercase."""
        assert get_chakra("SUN")["chakra"] == "manipura"  # assertion 17

    def test_get_chakra_unknown_raises(self):
        with pytest.raises(KeyError):
            get_chakra("unknown_planet")  # assertion 18


# ---------------------------------------------------------------------------
# G46 — SRIVIDYA_TRIANGLE tests
# ---------------------------------------------------------------------------

class TestSrividyaTriangle:
    def test_triangle_count(self):
        assert SRIVIDYA_TRIANGLE["triangle_count"] == 9  # assertion 19

    def test_bija_shreem(self):
        assert SRIVIDYA_TRIANGLE["bija"] == "SHREEM"  # assertion 20

    def test_central_bindu(self):
        assert SRIVIDYA_TRIANGLE["central_bindu"] == "param_shiva"  # assertion 21


# ---------------------------------------------------------------------------
# G47 — PYTHAGOREAN_NUMEROLOGY tests
# ---------------------------------------------------------------------------

class TestPythagoreanNumerology:
    def test_has_26_letters(self):
        """PYTHAGOREAN_NUMEROLOGY must cover all 26 English letters."""
        assert len(PYTHAGOREAN_NUMEROLOGY) == 26  # assertion 22

    def test_A_equals_1(self):
        assert PYTHAGOREAN_NUMEROLOGY["A"] == 1  # assertion 23

    def test_Z_equals_8(self):
        assert PYTHAGOREAN_NUMEROLOGY["Z"] == 8  # assertion 24

    def test_I_equals_9(self):
        assert PYTHAGOREAN_NUMEROLOGY["I"] == 9  # assertion 25

    def test_compute_single_letter_A(self):
        assert compute_pythagorean_name_number("A") == 1  # assertion 26

    def test_compute_single_letter_Z(self):
        assert compute_pythagorean_name_number("Z") == 8  # assertion 27

    def test_compute_ignores_spaces(self):
        """Name with spaces should produce same result as without."""
        assert compute_pythagorean_name_number("A B") == compute_pythagorean_name_number("AB")  # assertion 28

    def test_compute_case_insensitive(self):
        assert compute_pythagorean_name_number("abc") == compute_pythagorean_name_number("ABC")  # assertion 29


# ---------------------------------------------------------------------------
# G47 — CHALDEAN_NUMEROLOGY tests
# ---------------------------------------------------------------------------

class TestChaldeanNumerology:
    def test_has_26_letters(self):
        """CHALDEAN_NUMEROLOGY must cover all 26 English letters."""
        assert len(CHALDEAN_NUMEROLOGY) == 26  # assertion 30

    def test_A_equals_1(self):
        assert CHALDEAN_NUMEROLOGY["A"] == 1  # assertion 31

    def test_F_equals_8(self):
        """Chaldean F=8 (differs from Pythagorean F=6)."""
        assert CHALDEAN_NUMEROLOGY["F"] == 8  # assertion 32

    def test_no_9_assigned(self):
        """In Chaldean system the digit 9 is sacred and never assigned."""
        assert 9 not in CHALDEAN_NUMEROLOGY.values()  # assertion 33

    def test_chaldean_compute_A(self):
        assert compute_chaldean_name_number("A") == 1  # assertion 34

    def test_chaldean_differs_from_pythagorean_for_F(self):
        """F maps to 6 in Pythagorean but 8 in Chaldean."""
        assert compute_pythagorean_name_number("F") != compute_chaldean_name_number("F")  # assertion 35


# ---------------------------------------------------------------------------
# G47 — reduce_to_single_digit tests
# ---------------------------------------------------------------------------

class TestReduceToSingleDigit:
    def test_single_digit_unchanged(self):
        assert reduce_to_single_digit(5) == 5  # assertion 36

    def test_29_reduces_to_2(self):
        """29 → 2+9=11 → 1+1=2 (11 is a master number, but 29 is not)."""
        assert reduce_to_single_digit(29) == 2  # assertion 37

    def test_master_number_11_preserved(self):
        assert reduce_to_single_digit(11) == 11  # assertion 38

    def test_master_number_22_preserved(self):
        assert reduce_to_single_digit(22) == 22  # assertion 39

    def test_master_number_33_preserved(self):
        assert reduce_to_single_digit(33) == 33  # assertion 40

    def test_large_number_reduces(self):
        """999 → 27 → 9"""
        assert reduce_to_single_digit(999) == 9  # assertion 41


# ---------------------------------------------------------------------------
# G47 — GRAHA_NUMBER tests
# ---------------------------------------------------------------------------

class TestGrahaNumber:
    def test_has_nine_grahas(self):
        assert len(GRAHA_NUMBER) == 9  # assertion 42

    def test_sun_is_1(self):
        assert get_graha_number("sun") == 1  # assertion 43

    def test_moon_is_2(self):
        assert get_graha_number("moon") == 2  # assertion 44

    def test_jupiter_is_3(self):
        assert get_graha_number("jupiter") == 3  # assertion 45

    def test_rahu_is_4(self):
        assert get_graha_number("rahu") == 4  # assertion 46

    def test_mercury_is_5(self):
        assert get_graha_number("mercury") == 5  # assertion 47

    def test_venus_is_6(self):
        assert get_graha_number("venus") == 6  # assertion 48

    def test_ketu_is_7(self):
        assert get_graha_number("ketu") == 7  # assertion 49

    def test_saturn_is_8(self):
        assert get_graha_number("saturn") == 8  # assertion 50

    def test_mars_is_9(self):
        assert get_graha_number("mars") == 9  # assertion 51

    def test_unknown_graha_raises(self):
        with pytest.raises(KeyError):
            get_graha_number("unknown")  # assertion 52


# ---------------------------------------------------------------------------
# G47 — VEDIC_ANKJYOTISH + get_nakshatra_number tests
# ---------------------------------------------------------------------------

class TestVedicAnkJyotish:
    def test_has_27_entries(self):
        """VEDIC_ANKJYOTISH must cover all 27 nakshatras."""
        assert len(VEDIC_ANKJYOTISH) == 27  # assertion 53

    def test_nakshatra_1_is_1(self):
        assert get_nakshatra_number(1) == 1  # assertion 54

    def test_nakshatra_9_is_9(self):
        assert get_nakshatra_number(9) == 9  # assertion 55

    def test_nakshatra_10_is_1_cycle_repeats(self):
        """After 9, the cycle restarts at 1."""
        assert get_nakshatra_number(10) == 1  # assertion 56

    def test_nakshatra_18_is_9(self):
        assert get_nakshatra_number(18) == 9  # assertion 57

    def test_nakshatra_19_is_1(self):
        assert get_nakshatra_number(19) == 1  # assertion 58

    def test_nakshatra_27_is_9(self):
        assert get_nakshatra_number(27) == 9  # assertion 59

    def test_nakshatra_out_of_range_raises(self):
        with pytest.raises(KeyError):
            get_nakshatra_number(28)  # assertion 60

    def test_nakshatra_zero_raises(self):
        with pytest.raises(KeyError):
            get_nakshatra_number(0)  # assertion 61

    def test_all_values_in_range_1_to_9(self):
        """All VEDIC_ANKJYOTISH values must be in 1-9."""
        assert all(1 <= v <= 9 for v in VEDIC_ANKJYOTISH.values())  # assertion 62
