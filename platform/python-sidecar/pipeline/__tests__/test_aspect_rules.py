"""
test_aspect_rules.py — Tests for G17 aspect rule library
=========================================================
Covers: PARASHARI_GRAHA_DRISHTI, JAIMINI_RASI_DRISHTI, TAJIK_ASPECTS,
        and all four helper functions.

Minimum 35 assertions required per acceptance criteria.
"""

import pytest

from pipeline.aspect_rules import (
    PARASHARI_GRAHA_DRISHTI,
    JAIMINI_RASI_DRISHTI,
    TAJIK_ASPECTS,
    get_parashari_aspects,
    get_jaimini_aspected_signs,
    does_sign_aspect_sign_jaimini,
    get_tajik_aspect,
    parashari_aspect_houses_from_house,
)

# ---------------------------------------------------------------------------
# PARASHARI_GRAHA_DRISHTI — structure checks
# ---------------------------------------------------------------------------

NINE_GRAHAS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "rahu", "ketu"]


class TestParashariDrishtiDict:
    def test_all_nine_grahas_present(self):
        for graha in NINE_GRAHAS:
            assert graha in PARASHARI_GRAHA_DRISHTI, f"{graha} missing from PARASHARI_GRAHA_DRISHTI"

    def test_all_grahas_aspect_seventh(self):
        """Every graha must have 7 in its aspect list (7th house = opposition)."""
        for graha in NINE_GRAHAS:
            assert 7 in PARASHARI_GRAHA_DRISHTI[graha], f"{graha} does not aspect 7th"

    def test_sun_aspects_only_seventh(self):
        assert PARASHARI_GRAHA_DRISHTI["sun"] == [7]

    def test_moon_aspects_only_seventh(self):
        assert PARASHARI_GRAHA_DRISHTI["moon"] == [7]

    def test_mercury_aspects_only_seventh(self):
        assert PARASHARI_GRAHA_DRISHTI["mercury"] == [7]

    def test_venus_aspects_only_seventh(self):
        assert PARASHARI_GRAHA_DRISHTI["venus"] == [7]

    def test_mars_special_aspects(self):
        assert sorted(PARASHARI_GRAHA_DRISHTI["mars"]) == [4, 7, 8]

    def test_jupiter_special_aspects(self):
        assert sorted(PARASHARI_GRAHA_DRISHTI["jupiter"]) == [5, 7, 9]

    def test_saturn_special_aspects(self):
        assert sorted(PARASHARI_GRAHA_DRISHTI["saturn"]) == [3, 7, 10]

    def test_rahu_aspects_fifth_seventh_ninth(self):
        assert sorted(PARASHARI_GRAHA_DRISHTI["rahu"]) == [5, 7, 9]

    def test_ketu_aspects_fifth_seventh_ninth(self):
        assert sorted(PARASHARI_GRAHA_DRISHTI["ketu"]) == [5, 7, 9]


# ---------------------------------------------------------------------------
# JAIMINI_RASI_DRISHTI — structure checks
# ---------------------------------------------------------------------------

TWELVE_SIGNS = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
]


class TestJaiminiRasiDrishtiDict:
    def test_all_twelve_signs_present(self):
        for sign in TWELVE_SIGNS:
            assert sign in JAIMINI_RASI_DRISHTI, f"{sign} missing from JAIMINI_RASI_DRISHTI"

    def test_each_sign_aspects_exactly_three(self):
        for sign in TWELVE_SIGNS:
            aspects = JAIMINI_RASI_DRISHTI[sign]
            assert len(aspects) == 3, f"{sign} aspects {len(aspects)} signs, expected 3"

    def test_aries_aspects_leo(self):
        assert "leo" in JAIMINI_RASI_DRISHTI["aries"]

    def test_aries_does_not_aspect_taurus(self):
        """Taurus is adjacent fixed sign — excluded from Aries' aspects."""
        assert "taurus" not in JAIMINI_RASI_DRISHTI["aries"]

    def test_aries_aspects_scorpio_and_aquarius(self):
        assert "scorpio" in JAIMINI_RASI_DRISHTI["aries"]
        assert "aquarius" in JAIMINI_RASI_DRISHTI["aries"]

    def test_gemini_aspects_virgo_sagittarius_pisces(self):
        assert sorted(JAIMINI_RASI_DRISHTI["gemini"]) == sorted(["virgo", "sagittarius", "pisces"])

    def test_virgo_aspects_dual_signs(self):
        assert sorted(JAIMINI_RASI_DRISHTI["virgo"]) == sorted(["gemini", "sagittarius", "pisces"])

    def test_sagittarius_aspects_dual_signs(self):
        assert sorted(JAIMINI_RASI_DRISHTI["sagittarius"]) == sorted(["gemini", "virgo", "pisces"])

    def test_pisces_aspects_dual_signs(self):
        assert sorted(JAIMINI_RASI_DRISHTI["pisces"]) == sorted(["gemini", "virgo", "sagittarius"])

    def test_taurus_aspects_cancer_libra_capricorn(self):
        assert sorted(JAIMINI_RASI_DRISHTI["taurus"]) == sorted(["cancer", "libra", "capricorn"])

    def test_leo_aspects_libra_capricorn_aries(self):
        assert sorted(JAIMINI_RASI_DRISHTI["leo"]) == sorted(["libra", "capricorn", "aries"])

    def test_scorpio_aspects_capricorn_aries_cancer(self):
        assert sorted(JAIMINI_RASI_DRISHTI["scorpio"]) == sorted(["capricorn", "aries", "cancer"])

    def test_aquarius_aspects_aries_cancer_libra(self):
        assert sorted(JAIMINI_RASI_DRISHTI["aquarius"]) == sorted(["aries", "cancer", "libra"])

    def test_no_sign_aspects_itself(self):
        for sign in TWELVE_SIGNS:
            assert sign not in JAIMINI_RASI_DRISHTI[sign], f"{sign} aspects itself"


# ---------------------------------------------------------------------------
# TAJIK_ASPECTS — structure checks
# ---------------------------------------------------------------------------

FIVE_TAJIK_ASPECTS = ["conjunction", "sextile", "square", "trine", "opposition"]


class TestTajikAspectsDict:
    def test_five_aspects_present(self):
        assert len(TAJIK_ASPECTS) == 5

    def test_all_aspect_names_present(self):
        for name in FIVE_TAJIK_ASPECTS:
            assert name in TAJIK_ASPECTS, f"{name} missing from TAJIK_ASPECTS"

    def test_conjunction_degree_zero(self):
        assert TAJIK_ASPECTS["conjunction"]["degrees"] == 0

    def test_sextile_degree_sixty(self):
        assert TAJIK_ASPECTS["sextile"]["degrees"] == 60

    def test_square_degree_ninety(self):
        assert TAJIK_ASPECTS["square"]["degrees"] == 90

    def test_trine_degree_120(self):
        assert TAJIK_ASPECTS["trine"]["degrees"] == 120

    def test_opposition_degree_180(self):
        assert TAJIK_ASPECTS["opposition"]["degrees"] == 180

    def test_trine_nature_friendly(self):
        assert TAJIK_ASPECTS["trine"]["nature"] == "friendly"

    def test_square_nature_inimical(self):
        assert TAJIK_ASPECTS["square"]["nature"] == "inimical"

    def test_conjunction_nature_neutral(self):
        assert TAJIK_ASPECTS["conjunction"]["nature"] == "neutral"

    def test_each_aspect_has_orb_fields(self):
        for name, aspect in TAJIK_ASPECTS.items():
            assert "orb_applying" in aspect, f"{name} missing orb_applying"
            assert "orb_separating" in aspect, f"{name} missing orb_separating"


# ---------------------------------------------------------------------------
# get_parashari_aspects()
# ---------------------------------------------------------------------------

class TestGetParashariAspects:
    def test_mars_returns_4_7_8(self):
        assert get_parashari_aspects("mars") == [4, 7, 8]

    def test_sun_returns_7(self):
        assert get_parashari_aspects("sun") == [7]

    def test_jupiter_returns_5_7_9(self):
        assert get_parashari_aspects("jupiter") == [5, 7, 9]

    def test_saturn_returns_3_7_10(self):
        assert get_parashari_aspects("saturn") == [3, 7, 10]

    def test_case_insensitive(self):
        assert get_parashari_aspects("Mars") == get_parashari_aspects("mars")
        assert get_parashari_aspects("JUPITER") == get_parashari_aspects("jupiter")

    def test_unknown_graha_raises_key_error(self):
        with pytest.raises(KeyError):
            get_parashari_aspects("pluto")


# ---------------------------------------------------------------------------
# get_jaimini_aspected_signs() + does_sign_aspect_sign_jaimini()
# ---------------------------------------------------------------------------

class TestJaiminiFunctions:
    def test_get_jaimini_aries_aspects(self):
        result = get_jaimini_aspected_signs("aries")
        assert "leo" in result
        assert "scorpio" in result
        assert "aquarius" in result

    def test_get_jaimini_gemini_aspects(self):
        result = get_jaimini_aspected_signs("gemini")
        assert sorted(result) == sorted(["virgo", "sagittarius", "pisces"])

    def test_case_insensitive_get(self):
        assert get_jaimini_aspected_signs("Aries") == get_jaimini_aspected_signs("aries")

    def test_does_aries_aspect_leo_true(self):
        assert does_sign_aspect_sign_jaimini("aries", "leo") is True

    def test_does_aries_aspect_taurus_false(self):
        assert does_sign_aspect_sign_jaimini("aries", "taurus") is False

    def test_does_gemini_aspect_virgo_true(self):
        assert does_sign_aspect_sign_jaimini("gemini", "virgo") is True

    def test_does_gemini_not_aspect_aries(self):
        assert does_sign_aspect_sign_jaimini("gemini", "aries") is False

    def test_case_insensitive_does_aspect(self):
        assert does_sign_aspect_sign_jaimini("Aries", "Leo") is True

    def test_unknown_sign_returns_false(self):
        assert does_sign_aspect_sign_jaimini("atlantis", "aries") is False


# ---------------------------------------------------------------------------
# get_tajik_aspect()
# ---------------------------------------------------------------------------

class TestGetTajikAspect:
    def test_exact_conjunction_returns_conjunction(self):
        result = get_tajik_aspect(0)
        assert result is not None
        assert result["name"] == "conjunction"

    def test_exact_trine_returns_trine(self):
        result = get_tajik_aspect(120)
        assert result is not None
        assert result["name"] == "trine"

    def test_exact_opposition_returns_opposition(self):
        result = get_tajik_aspect(180)
        assert result is not None
        assert result["name"] == "opposition"

    def test_exact_sextile_returns_sextile(self):
        result = get_tajik_aspect(60)
        assert result is not None
        assert result["name"] == "sextile"

    def test_exact_square_returns_square(self):
        result = get_tajik_aspect(90)
        assert result is not None
        assert result["name"] == "square"

    def test_45_degrees_returns_none(self):
        """45° is not a recognised Tajik aspect."""
        assert get_tajik_aspect(45) is None

    def test_30_degrees_returns_none(self):
        assert get_tajik_aspect(30) is None

    def test_within_trine_orb_matches(self):
        """119° is within the 8° applying orb of trine (120°)."""
        result = get_tajik_aspect(119)
        assert result is not None
        assert result["name"] == "trine"

    def test_result_dict_includes_name(self):
        result = get_tajik_aspect(0)
        assert "name" in result
        assert "degrees" in result
        assert "nature" in result


# ---------------------------------------------------------------------------
# parashari_aspect_houses_from_house()
# ---------------------------------------------------------------------------

class TestParashariAspectHousesFromHouse:
    def test_mars_from_house_1(self):
        """Mars in H1 aspects H4, H7, H8."""
        result = parashari_aspect_houses_from_house(1, "mars")
        assert sorted(result) == [4, 7, 8]

    def test_sun_from_house_1(self):
        """Sun in H1 aspects H7."""
        result = parashari_aspect_houses_from_house(1, "sun")
        assert result == [7]

    def test_jupiter_from_house_7(self):
        """Jupiter in H7 aspects H11, H1, H3 (offsets 5,7,9 from H7)."""
        # offset 5: (7-1+5-1)%12+1 = 10%12+1 = 11
        # offset 7: (7-1+7-1)%12+1 = 12%12+1 = 1
        # offset 9: (7-1+9-1)%12+1 = 14%12+1 = 3
        result = parashari_aspect_houses_from_house(7, "jupiter")
        assert sorted(result) == [1, 3, 11]

    def test_saturn_from_house_4(self):
        """Saturn in H4 aspects H6, H10, H1 (offsets 3,7,10 from H4)."""
        # offset 3:  (4-1+3-1)%12+1 = 5%12+1 = 6
        # offset 7:  (4-1+7-1)%12+1 = 9%12+1 = 10
        # offset 10: (4-1+10-1)%12+1 = 12%12+1 = 1
        result = parashari_aspect_houses_from_house(4, "saturn")
        assert sorted(result) == [1, 6, 10]

    def test_wrap_around_12th_house(self):
        """Mars in H11 aspects H2, H5, H6 (wrap modulo 12)."""
        # offset 4:  (11-1+4-1)%12+1 = 13%12+1 = 2
        # offset 7:  (11-1+7-1)%12+1 = 16%12+1 = 5
        # offset 8:  (11-1+8-1)%12+1 = 17%12+1 = 6
        result = parashari_aspect_houses_from_house(11, "mars")
        assert sorted(result) == [2, 5, 6]

    def test_invalid_house_raises_value_error(self):
        with pytest.raises(ValueError):
            parashari_aspect_houses_from_house(0, "mars")

    def test_invalid_house_13_raises_value_error(self):
        with pytest.raises(ValueError):
            parashari_aspect_houses_from_house(13, "sun")

    def test_case_insensitive_graha(self):
        assert parashari_aspect_houses_from_house(1, "Mars") == parashari_aspect_houses_from_house(1, "mars")

    def test_all_houses_return_valid_range(self):
        """For every house and every graha, all aspected houses must be in 1–12."""
        for house in range(1, 13):
            for graha in NINE_GRAHAS:
                aspects = parashari_aspect_houses_from_house(house, graha)
                for h in aspects:
                    assert 1 <= h <= 12, f"house {h} out of range for {graha} from H{house}"
