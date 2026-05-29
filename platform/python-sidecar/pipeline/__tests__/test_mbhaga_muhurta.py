"""
Tests for G25 + G26: mbhaga_muhurta_ref.py
Minimum 30 assertions covering MRITYUBHAGA_DEGREES, GANDANTA_ZONES,
PUSHKARA_NAVAMSAS, TITHI_QUALITY, VARA_QUALITY, NAKSHATRA_MUHURTA_CLASS,
and all six helper functions.
"""

import pytest
from pipeline.mbhaga_muhurta_ref import (
    MRITYUBHAGA_DEGREES,
    GANDANTA_ZONES,
    PUSHKARA_NAVAMSAS,
    TITHI_QUALITY,
    VARA_QUALITY,
    NAKSHATRA_MUHURTA_CLASS,
    ABHIJIT_MUHURTA,
    is_gandanta,
    is_pushkara,
    is_mrityubhaga,
    get_tithi_quality,
    get_vara_quality,
    get_nakshatra_muhurta_class,
)


# ---------------------------------------------------------------------------
# G25 — Data structure tests
# ---------------------------------------------------------------------------

class TestMrityubhagaData:
    def test_has_seven_grahas(self):
        """MRITYUBHAGA_DEGREES must cover all 7 classical grahas."""
        assert len(MRITYUBHAGA_DEGREES) == 7                          # assertion 1

    def test_expected_grahas_present(self):
        expected = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}
        assert set(MRITYUBHAGA_DEGREES.keys()) == expected            # assertion 2

    def test_each_graha_has_12_entries(self):
        """Each graha must have exactly 12 critical-degree entries (one per sign)."""
        for graha, entries in MRITYUBHAGA_DEGREES.items():
            assert len(entries) == 12, f"{graha} should have 12 entries"  # assertions 3–9

    def test_sun_aries_critical_degree(self):
        """Sun mrityubhaga in Aries (index 0) should be 20°."""
        sun_entries = dict((si, d) for si, d in MRITYUBHAGA_DEGREES["sun"])
        assert sun_entries[0] == 20                                   # assertion 10

    def test_moon_cancer_critical_degree(self):
        """Moon mrityubhaga in Cancer (index 3) should be 25°."""
        moon_entries = dict((si, d) for si, d in MRITYUBHAGA_DEGREES["moon"])
        assert moon_entries[3] == 25                                  # assertion 11


class TestGandantaData:
    def test_three_gandanta_zones(self):
        assert len(GANDANTA_ZONES) == 3                               # assertion 12

    def test_pisces_aries_zone(self):
        zone = next(z for z in GANDANTA_ZONES if z["from_sign"] == "pisces")
        assert zone["to_sign"] == "aries"                             # assertion 13
        assert zone["from_sign_index"] == 11                          # assertion 14
        assert zone["to_sign_index"] == 0                             # assertion 15

    def test_cancer_leo_zone_exists(self):
        names = [z["from_sign"] for z in GANDANTA_ZONES]
        assert "cancer" in names                                      # assertion 16

    def test_scorpio_sagittarius_zone_exists(self):
        names = [z["from_sign"] for z in GANDANTA_ZONES]
        assert "scorpio" in names                                     # assertion 17


class TestPushkaraData:
    def test_24_pushkara_entries(self):
        """12 signs × 2 navamsas = 24 entries."""
        assert len(PUSHKARA_NAVAMSAS) == 24                           # assertion 18

    def test_all_signs_covered(self):
        signs = {e["sign"] for e in PUSHKARA_NAVAMSAS}
        assert len(signs) == 12                                       # assertion 19

    def test_navamsa_numbers_are_4_and_8(self):
        navamsa_nums = {e["navamsa"] for e in PUSHKARA_NAVAMSAS}
        assert navamsa_nums == {4, 8}                                 # assertion 20


# ---------------------------------------------------------------------------
# G25 — Helper function tests
# ---------------------------------------------------------------------------

class TestIsGandanta:
    def test_pisces_late_is_gandanta(self):
        """Pisces 28° (last 3°20') should be gandanta."""
        assert is_gandanta(11, 28.0) is True                          # assertion 21

    def test_aries_early_is_gandanta(self):
        """Aries 1° (first 3°20') should be gandanta."""
        assert is_gandanta(0, 1.0) is True                            # assertion 22

    def test_aries_mid_is_not_gandanta(self):
        """Aries 15° is well outside the gandanta zone."""
        assert is_gandanta(0, 15.0) is False                          # assertion 23

    def test_cancer_late_is_gandanta(self):
        """Cancer 27° should be gandanta (water sign tail)."""
        assert is_gandanta(3, 27.0) is True                           # assertion 24

    def test_leo_early_is_gandanta(self):
        """Leo 2° should be gandanta (fire sign head)."""
        assert is_gandanta(4, 2.0) is True                            # assertion 25

    def test_scorpio_late_is_gandanta(self):
        """Scorpio 29° should be gandanta."""
        assert is_gandanta(7, 29.0) is True                           # assertion 26

    def test_sagittarius_early_is_gandanta(self):
        """Sagittarius 0.5° should be gandanta."""
        assert is_gandanta(8, 0.5) is True                            # assertion 27

    def test_taurus_any_is_not_gandanta(self):
        """Taurus has no gandanta involvement at all."""
        assert is_gandanta(1, 27.0) is False                          # assertion 28
        assert is_gandanta(1, 2.0) is False                           # assertion 29

    def test_exact_boundary_pisces(self):
        """Exactly 26.666° in Pisces is the start of gandanta."""
        assert is_gandanta(11, 26.666) is True                        # assertion 30


class TestIsPushkara:
    def test_4th_navamsa_is_pushkara(self):
        """10°–13.33° is the 4th navamsa → Pushkara."""
        assert is_pushkara(0, 11.0) is True                           # assertion 31
        assert is_pushkara(5, 12.5) is True                           # assertion 32

    def test_8th_navamsa_is_pushkara(self):
        """23.33°–26.67° is the 8th navamsa → Pushkara."""
        assert is_pushkara(3, 24.0) is True                           # assertion 33
        assert is_pushkara(11, 25.5) is True                          # assertion 34

    def test_other_navamsa_not_pushkara(self):
        """1st navamsa (0°–3.33°) is not Pushkara."""
        assert is_pushkara(0, 2.0) is False                           # assertion 35
        assert is_pushkara(6, 17.0) is False                          # assertion 36


class TestIsMrityubhaga:
    def test_sun_mrityubhaga_aries(self):
        """Sun at exactly 20° Aries → mrityubhaga (orb=1°)."""
        assert is_mrityubhaga("sun", 0, 20.0) is True                 # assertion 37

    def test_sun_mrityubhaga_aries_within_orb(self):
        """Sun at 19.5° Aries → within 1° orb of 20° → True."""
        assert is_mrityubhaga("sun", 0, 19.5) is True                 # assertion 38

    def test_sun_mrityubhaga_aries_outside_orb(self):
        """Sun at 18° Aries → 2° away from 20° → False with default 1° orb."""
        assert is_mrityubhaga("sun", 0, 18.0) is False                # assertion 39

    def test_moon_mrityubhaga_aries(self):
        """Moon mrityubhaga in Aries is 26°."""
        assert is_mrityubhaga("moon", 0, 26.0) is True                # assertion 40

    def test_saturn_mrityubhaga_taurus(self):
        """Saturn mrityubhaga in Taurus (index 1) is 11°."""
        assert is_mrityubhaga("saturn", 1, 11.0) is True              # assertion 41

    def test_case_insensitive_graha(self):
        """Graha name lookup is case-insensitive."""
        assert is_mrityubhaga("SUN", 0, 20.0) is True                 # assertion 42

    def test_graha_not_mrityubhaga_in_other_sign(self):
        """Venus mrityubhaga in Aries is 27°; at 10° Aries it is not."""
        assert is_mrityubhaga("venus", 0, 10.0) is False              # assertion 43


# ---------------------------------------------------------------------------
# G26 — Data structure tests
# ---------------------------------------------------------------------------

class TestTithiData:
    def test_30_tithis_defined(self):
        assert len(TITHI_QUALITY) == 30                               # assertion 44

    def test_purnima_is_good(self):
        assert TITHI_QUALITY[15]["quality"] == "good"                 # assertion 45

    def test_amavasya_is_inauspicious(self):
        assert TITHI_QUALITY[30]["quality"] == "inauspicious"         # assertion 46

    def test_all_tithis_have_quality_field(self):
        for t, info in TITHI_QUALITY.items():
            assert "quality" in info, f"tithi {t} missing quality"   # assertions 47–76


class TestVaraData:
    def test_seven_varas_defined(self):
        assert len(VARA_QUALITY) == 7                                 # assertion 77

    def test_thursday_is_good(self):
        assert VARA_QUALITY["thursday"]["quality"] == "good"          # assertion 78

    def test_tuesday_is_inauspicious(self):
        assert VARA_QUALITY["tuesday"]["quality"] == "inauspicious"   # assertion 79

    def test_sunday_is_mixed(self):
        assert VARA_QUALITY["sunday"]["quality"] == "mixed"           # assertion 80


class TestNakshatraData:
    def test_27_nakshatras_defined(self):
        assert len(NAKSHATRA_MUHURTA_CLASS) == 27                     # assertion 81

    def test_rohini_is_dhruva(self):
        assert NAKSHATRA_MUHURTA_CLASS[4]["class"] == "dhruva"        # assertion 82

    def test_all_nakshatras_have_class(self):
        valid_classes = {"dhruva", "chara", "mridu", "ugra", "tikshna", "sadharana"}
        for n, info in NAKSHATRA_MUHURTA_CLASS.items():
            assert info["class"] in valid_classes, \
                f"nakshatra {n} has unknown class {info['class']}"     # assertions 83–109

    def test_nakshatra_1_has_class(self):
        assert isinstance(get_nakshatra_muhurta_class(1), str)        # assertion 110


class TestAbhijitMuhurta:
    def test_abhijit_duration(self):
        assert ABHIJIT_MUHURTA["duration_mins"] == 48                 # assertion 111

    def test_abhijit_quality(self):
        assert ABHIJIT_MUHURTA["quality"] == "highly_auspicious"      # assertion 112

    def test_abhijit_center(self):
        assert ABHIJIT_MUHURTA["center"] == "solar_noon"              # assertion 113


# ---------------------------------------------------------------------------
# G26 — Helper function tests
# ---------------------------------------------------------------------------

class TestGetTithiQuality:
    def test_purnima_returns_good(self):
        assert get_tithi_quality(15) == "good"                        # assertion 114

    def test_amavasya_returns_inauspicious(self):
        assert get_tithi_quality(30) == "inauspicious"                # assertion 115

    def test_dwitiya_returns_good(self):
        assert get_tithi_quality(2) == "good"                         # assertion 116

    def test_chaturthi_returns_mixed(self):
        assert get_tithi_quality(4) == "mixed"                        # assertion 117

    def test_dark_tithi_17_is_inauspicious(self):
        assert get_tithi_quality(17) == "inauspicious"                # assertion 118

    def test_invalid_tithi_raises(self):
        with pytest.raises(ValueError):
            get_tithi_quality(0)                                       # assertion 119

    def test_invalid_tithi_31_raises(self):
        with pytest.raises(ValueError):
            get_tithi_quality(31)                                      # assertion 120


class TestGetVaraQuality:
    def test_thursday_good(self):
        assert get_vara_quality("thursday") == "good"                 # assertion 121

    def test_tuesday_inauspicious(self):
        assert get_vara_quality("tuesday") == "inauspicious"          # assertion 122

    def test_monday_good(self):
        assert get_vara_quality("monday") == "good"                   # assertion 123

    def test_friday_good(self):
        assert get_vara_quality("friday") == "good"                   # assertion 124

    def test_saturday_mixed(self):
        assert get_vara_quality("saturday") == "mixed"                # assertion 125

    def test_case_insensitive(self):
        assert get_vara_quality("THURSDAY") == "good"                 # assertion 126

    def test_invalid_weekday_raises(self):
        with pytest.raises(ValueError):
            get_vara_quality("funday")                                 # assertion 127


class TestGetNakshatraMuhurtaClass:
    def test_rohini_dhruva(self):
        assert get_nakshatra_muhurta_class(4) == "dhruva"             # assertion 128

    def test_punarvasu_chara(self):
        assert get_nakshatra_muhurta_class(7) == "chara"              # assertion 129

    def test_mrigashira_mridu(self):
        assert get_nakshatra_muhurta_class(5) == "mridu"              # assertion 130

    def test_mula_tikshna(self):
        assert get_nakshatra_muhurta_class(19) == "tikshna"           # assertion 131

    def test_vishakha_sadharana(self):
        assert get_nakshatra_muhurta_class(16) == "sadharana"         # assertion 132

    def test_all_27_return_strings(self):
        for n in range(1, 28):
            cls = get_nakshatra_muhurta_class(n)
            assert isinstance(cls, str) and len(cls) > 0             # assertions 133–159

    def test_invalid_nakshatra_raises(self):
        with pytest.raises(ValueError):
            get_nakshatra_muhurta_class(28)                            # assertion 160

    def test_nakshatra_0_raises(self):
        with pytest.raises(ValueError):
            get_nakshatra_muhurta_class(0)                             # assertion 161
