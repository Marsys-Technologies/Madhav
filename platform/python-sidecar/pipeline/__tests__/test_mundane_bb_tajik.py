"""
test_mundane_bb_tajik.py — Tests for G48 + G49 + G50 reference modules
=======================================================================
Covers:
  - mundane_astrology.py (G48): Jupiter-Saturn conjunctions, slow-planet alignments,
    historical correlations, and helper functions.
  - bhrigu_bindu.py (G49): BB computation, activation check, activation significance.
  - tajik_tables.py (G50): Hadda lords, Tajik aspects, year lord rules, Mudda dasha.

session: G48-G49-G50-S1 [BUILD-ORCH-A-15]
"""

from __future__ import annotations

import math
import pytest

from pipeline.mundane_astrology import (
    JUPITER_SATURN_CONJUNCTIONS,
    SLOW_PLANET_ALIGNMENTS,
    HISTORICAL_CORRELATIONS,
    get_conjunctions_by_element,
    get_conjunctions_by_sign,
    get_next_conjunction_after,
)
from pipeline.bhrigu_bindu import (
    BHRIGU_BINDU_RULES,
    compute_bhrigu_bindu,
    get_activation_significance,
    is_planet_activating_bb,
)
from pipeline.tajik_tables import (
    HADDA_LORDS,
    MUDDA_PATYAYINI_RULES,
    TAJIK_ASPECTS_EXTENDED,
    YEAR_LORD_RULES,
    get_hadda_lord,
    get_mudda_period_days,
    get_tajik_aspect_info,
    get_year_lord_rules,
)

# ===========================================================================
# G48 — MUNDANE ASTROLOGY
# ===========================================================================


class TestJupiterSaturnConjunctions:
    def test_minimum_count(self):
        assert len(JUPITER_SATURN_CONJUNCTIONS) >= 8

    def test_all_have_date_approx(self):
        assert all("date_approx" in c for c in JUPITER_SATURN_CONJUNCTIONS)

    def test_all_have_element(self):
        assert all("element" in c for c in JUPITER_SATURN_CONJUNCTIONS)

    def test_all_have_sign(self):
        assert all("sign" in c for c in JUPITER_SATURN_CONJUNCTIONS)

    def test_all_have_longitude_approx(self):
        assert all("longitude_approx" in c for c in JUPITER_SATURN_CONJUNCTIONS)

    def test_all_have_era_name(self):
        assert all("era_name" in c for c in JUPITER_SATURN_CONJUNCTIONS)

    def test_all_have_notes(self):
        assert all("notes" in c for c in JUPITER_SATURN_CONJUNCTIONS)

    def test_2020_conjunction_sign_is_aquarius(self):
        """The 2020 Great Mutation conjunction should be in Aquarius."""
        entries_2020 = [
            c for c in JUPITER_SATURN_CONJUNCTIONS if c["date_approx"].startswith("2020")
        ]
        assert len(entries_2020) >= 1, "Expected at least one 2020 conjunction"
        entry = entries_2020[0]
        assert entry["sign"].lower() == "aquarius"

    def test_2020_conjunction_element_is_air(self):
        entries_2020 = [
            c for c in JUPITER_SATURN_CONJUNCTIONS if c["date_approx"].startswith("2020")
        ]
        assert entries_2020[0]["element"].lower() == "air"

    def test_2020_conjunction_longitude_near_aquarius(self):
        """Aquarius starts at 300° sidereal; 0° Aquarius = longitude ~300°."""
        entries_2020 = [
            c for c in JUPITER_SATURN_CONJUNCTIONS if c["date_approx"].startswith("2020")
        ]
        lon = entries_2020[0]["longitude_approx"]
        # Aquarius spans 300-330°; conjunction was near 0° of the sign
        assert 295.0 <= lon <= 335.0 or 0.0 <= lon <= 5.0, (
            f"Longitude {lon} does not fall in Aquarius range"
        )

    def test_get_conjunctions_by_element_air_nonempty(self):
        result = get_conjunctions_by_element("air")
        assert len(result) >= 1

    def test_get_conjunctions_by_element_air_all_air(self):
        result = get_conjunctions_by_element("air")
        assert all(c["element"].lower() == "air" for c in result)

    def test_get_conjunctions_by_element_case_insensitive(self):
        result_lower = get_conjunctions_by_element("earth")
        result_upper = get_conjunctions_by_element("EARTH")
        assert len(result_lower) == len(result_upper)

    def test_get_conjunctions_by_sign_aquarius_contains_2020(self):
        result = get_conjunctions_by_sign("aquarius")
        years = [int(c["date_approx"][:4]) for c in result]
        assert 2020 in years

    def test_get_conjunctions_by_sign_empty_for_unknown(self):
        result = get_conjunctions_by_sign("pluto")  # not a sign
        assert result == []

    def test_get_conjunctions_by_sign_case_insensitive(self):
        lower = get_conjunctions_by_sign("capricorn")
        upper = get_conjunctions_by_sign("CAPRICORN")
        assert len(lower) == len(upper)

    def test_get_next_conjunction_after_1990(self):
        result = get_next_conjunction_after(1990)
        assert result is not None
        assert int(result["date_approx"][:4]) > 1990

    def test_get_next_conjunction_after_far_future_returns_none(self):
        result = get_next_conjunction_after(2200)
        assert result is None

    def test_get_next_conjunction_after_2019_is_2020(self):
        result = get_next_conjunction_after(2019)
        assert result is not None
        assert int(result["date_approx"][:4]) == 2020


class TestSlowPlanetAlignments:
    def test_minimum_count(self):
        assert len(SLOW_PLANET_ALIGNMENTS) >= 20

    def test_all_have_planets(self):
        assert all("planets" in a for a in SLOW_PLANET_ALIGNMENTS)

    def test_all_have_date_approx(self):
        assert all("date_approx" in a for a in SLOW_PLANET_ALIGNMENTS)

    def test_all_have_sign(self):
        assert all("sign" in a for a in SLOW_PLANET_ALIGNMENTS)

    def test_all_have_type(self):
        assert all("type" in a for a in SLOW_PLANET_ALIGNMENTS)

    def test_planets_field_is_list(self):
        assert all(isinstance(a["planets"], list) for a in SLOW_PLANET_ALIGNMENTS)


class TestHistoricalCorrelations:
    def test_minimum_count(self):
        assert len(HISTORICAL_CORRELATIONS) >= 10

    def test_all_have_event_type(self):
        assert all("event_type" in h for h in HISTORICAL_CORRELATIONS)

    def test_all_have_planetary_trigger(self):
        assert all("planetary_trigger" in h for h in HISTORICAL_CORRELATIONS)

    def test_all_have_description(self):
        assert all("description" in h for h in HISTORICAL_CORRELATIONS)


# ===========================================================================
# G49 — BHRIGU BINDU
# ===========================================================================


class TestBhriguBinduComputation:
    def test_simple_midpoint(self):
        """Moon at 30°, Rahu at 150°: midpoint = 90°."""
        result = compute_bhrigu_bindu(30.0, 150.0)
        assert abs(result - 90.0) < 0.001

    def test_wrap_around_case(self):
        """Moon at 350°, Rahu at 10°: arc = 20°, midpoint = 0°."""
        result = compute_bhrigu_bindu(350.0, 10.0)
        assert abs(result - 0.0) < 1.0  # within 1° tolerance for wrap

    def test_same_longitude(self):
        """Moon and Rahu at same point: BB = that longitude."""
        result = compute_bhrigu_bindu(45.0, 45.0)
        assert abs(result - 45.0) < 0.001

    def test_exactly_opposite(self):
        """Opposite points: arc = 180°; midpoint is arbitrary but must be valid."""
        result = compute_bhrigu_bindu(0.0, 180.0)
        assert 0.0 <= result < 360.0

    def test_result_in_range(self):
        """Result must always be in [0, 360)."""
        for moon, rahu in [(355.0, 5.0), (90.0, 270.0), (0.0, 0.0), (180.0, 0.0)]:
            result = compute_bhrigu_bindu(moon, rahu)
            assert 0.0 <= result < 360.0, f"Out of range for moon={moon}, rahu={rahu}"


class TestBhriguBinduActivation:
    def test_within_orb_activates(self):
        """Planet 1° away from BB within default 3° orb: True."""
        assert is_planet_activating_bb(90.0, 91.0) is True

    def test_outside_orb_does_not_activate(self):
        """Planet 5° away from BB: False with default 3° orb."""
        assert is_planet_activating_bb(90.0, 95.0) is False

    def test_exact_conjunction_activates(self):
        assert is_planet_activating_bb(45.0, 45.0) is True

    def test_exactly_at_orb_boundary_activates(self):
        """Exactly at 3.0° difference: should return True (≤ orb)."""
        assert is_planet_activating_bb(90.0, 93.0, 3.0) is True

    def test_just_outside_orb(self):
        assert is_planet_activating_bb(90.0, 93.1, 3.0) is False

    def test_wrap_around_activation(self):
        """Planet at 359°, BB at 1°: circular distance = 2°; should activate at 3°."""
        assert is_planet_activating_bb(359.0, 1.0, 3.0) is True

    def test_custom_tight_orb(self):
        """1° orb: planet 2° away should NOT activate."""
        assert is_planet_activating_bb(90.0, 92.0, 1.0) is False


class TestBhriguBinduRulesAndSignificance:
    def test_rules_has_computation_key(self):
        assert "computation" in BHRIGU_BINDU_RULES

    def test_rules_has_activation_window(self):
        assert "activation_window_deg" in BHRIGU_BINDU_RULES

    def test_activation_window_is_3(self):
        assert BHRIGU_BINDU_RULES["activation_window_deg"] == 3.0

    def test_house_position_significance_has_12_keys(self):
        house_dict = BHRIGU_BINDU_RULES["house_position_significance"]
        # Count integer keys (1-12)
        integer_keys = [k for k in house_dict if isinstance(k, int)]
        assert len(integer_keys) == 12

    def test_saturn_significance_contains_karmic(self):
        sig = get_activation_significance("saturn")
        assert "karmic" in sig.lower() or "major" in sig.lower()

    def test_jupiter_significance_present(self):
        sig = get_activation_significance("jupiter")
        assert len(sig) > 10

    def test_unknown_planet_returns_unknown(self):
        sig = get_activation_significance("pluton")
        assert "unknown" in sig.lower()

    def test_case_insensitive_significance(self):
        sig_lower = get_activation_significance("saturn")
        sig_upper = get_activation_significance("SATURN")
        assert sig_lower == sig_upper

    def test_transiting_planets_ranked_length(self):
        ranked = BHRIGU_BINDU_RULES["transiting_planets_ranked"]
        assert len(ranked) == 9  # 9 grahas


# ===========================================================================
# G50 — TAJIK TABLES
# ===========================================================================


class TestHaddaLords:
    def test_all_12_signs_present(self):
        assert len(HADDA_LORDS) == 12

    def test_each_sign_has_5_sections(self):
        for sign, sections in HADDA_LORDS.items():
            assert len(sections) == 5, f"{sign} has {len(sections)} sections, expected 5"

    def test_aries_first_section_is_jupiter(self):
        assert get_hadda_lord("aries", 0.0) == "jupiter"

    def test_aries_second_section_is_venus(self):
        assert get_hadda_lord("aries", 7.0) == "venus"

    def test_aries_mercury_section(self):
        assert get_hadda_lord("aries", 15.0) == "mercury"

    def test_aries_mars_section(self):
        assert get_hadda_lord("aries", 22.0) == "mars"

    def test_aries_saturn_section(self):
        assert get_hadda_lord("aries", 27.0) == "saturn"

    def test_taurus_first_section_is_venus(self):
        assert get_hadda_lord("taurus", 0.0) == "venus"

    def test_taurus_mercury_section(self):
        assert get_hadda_lord("taurus", 10.0) == "mercury"

    def test_gemini_first_is_mercury(self):
        assert get_hadda_lord("gemini", 0.0) == "mercury"

    def test_capricorn_first_is_mercury(self):
        assert get_hadda_lord("capricorn", 0.0) == "mercury"

    def test_pisces_first_is_venus(self):
        assert get_hadda_lord("pisces", 0.0) == "venus"

    def test_case_insensitive_sign(self):
        assert get_hadda_lord("ARIES", 0.0) == "jupiter"
        assert get_hadda_lord("Taurus", 0.0) == "venus"

    def test_unknown_sign_raises_key_error(self):
        with pytest.raises(KeyError):
            get_hadda_lord("unknown_sign", 10.0)

    def test_out_of_range_degree_raises_value_error(self):
        with pytest.raises(ValueError):
            get_hadda_lord("aries", 30.0)

    def test_sections_cover_0_to_30_continuously(self):
        """Each sign's sections must be contiguous from 0 to 30 with no gaps."""
        for sign, sections in HADDA_LORDS.items():
            sorted_sections = sorted(sections, key=lambda s: s["start_deg"])
            # First section starts at 0
            assert sorted_sections[0]["start_deg"] == 0.0, (
                f"{sign}: first section doesn't start at 0"
            )
            # Last section ends at 30
            assert sorted_sections[-1]["end_deg"] == 30.0, (
                f"{sign}: last section doesn't end at 30"
            )
            # Each section starts where the previous ends (no gaps, no overlaps)
            for i in range(1, len(sorted_sections)):
                assert sorted_sections[i]["start_deg"] == sorted_sections[i - 1]["end_deg"], (
                    f"{sign}: gap between section {i-1} and {i}"
                )

    def test_all_lords_are_valid_grahas(self):
        valid_lords = {"mercury", "venus", "mars", "jupiter", "saturn"}
        for sign, sections in HADDA_LORDS.items():
            for sec in sections:
                assert sec["lord"] in valid_lords, (
                    f"{sign}: invalid lord '{sec['lord']}'"
                )


class TestTajikAspects:
    def test_trine_nature_is_friendly(self):
        info = get_tajik_aspect_info("trine")
        assert info["nature"] == "friendly"

    def test_square_nature_is_inimical(self):
        info = get_tajik_aspect_info("square")
        assert info["nature"] == "inimical"

    def test_conjunction_strength_is_1(self):
        info = get_tajik_aspect_info("conjunction")
        assert info["strength_modifier"] == 1.0

    def test_opposition_strength_is_0_5(self):
        info = get_tajik_aspect_info("opposition")
        assert info["strength_modifier"] == 0.5

    def test_unknown_aspect_raises_key_error(self):
        with pytest.raises(KeyError):
            get_tajik_aspect_info("nonexistent")

    def test_all_5_aspects_present(self):
        for aspect in ["conjunction", "sextile", "square", "trine", "opposition"]:
            info = get_tajik_aspect_info(aspect)
            assert "degrees" in info

    def test_trine_degrees_is_120(self):
        assert get_tajik_aspect_info("trine")["degrees"] == 120

    def test_opposition_degrees_is_180(self):
        assert get_tajik_aspect_info("opposition")["degrees"] == 180


class TestYearLordAndMuddaRules:
    def test_year_lord_rules_has_muntha_computation(self):
        assert "muntha_computation" in YEAR_LORD_RULES

    def test_year_lord_rules_has_year_lord_selection(self):
        assert "year_lord_selection" in YEAR_LORD_RULES

    def test_year_lord_rules_returned_by_function(self):
        rules = get_year_lord_rules()
        assert rules is YEAR_LORD_RULES

    def test_mudda_period_days_sun(self):
        assert get_mudda_period_days("sun") == 11

    def test_mudda_period_days_venus(self):
        assert get_mudda_period_days("venus") == 52

    def test_mudda_period_days_moon(self):
        assert get_mudda_period_days("moon") == 32

    def test_mudda_period_days_saturn(self):
        assert get_mudda_period_days("saturn") == 23

    def test_mudda_period_days_ketu(self):
        assert get_mudda_period_days("ketu") == 7

    def test_mudda_period_days_case_insensitive(self):
        assert get_mudda_period_days("SUN") == get_mudda_period_days("sun")

    def test_mudda_period_days_unknown_raises_key_error(self):
        with pytest.raises(KeyError):
            get_mudda_period_days("pluto")

    def test_mudda_single_pass_sum_is_240(self):
        total = sum(MUDDA_PATYAYINI_RULES["mudda_dasha"]["period_days"].values())
        assert total == 240

    def test_mudda_period_sequence_has_9_planets(self):
        seq = MUDDA_PATYAYINI_RULES["mudda_dasha"]["period_sequence"]
        assert len(seq) == 9

    def test_patyayini_total_years_is_120(self):
        assert MUDDA_PATYAYINI_RULES["patyayini_dasha"]["total_years"] == 120
