"""
Tests for friendship_karaka_ref.py (G18 + G19).

Covers:
  - Structural completeness: all 9 grahas present, 8 entries each
  - Classical facts: specific mitra/shatru relationships from BPHS
  - House karaka completeness: all 12 houses, key assertions
  - Domain karaka completeness: all domains non-empty, specific values
  - Function behaviour: happy path + error cases
"""

import pytest
from pipeline.friendship_karaka_ref import (
    NATURAL_FRIENDSHIP,
    HOUSE_KARAKAS,
    DOMAIN_KARAKAS,
    get_natural_friendship,
    get_house_karaka,
    get_domain_karaka,
    get_composite_friendship,
)

GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]


# ---------------------------------------------------------------------------
# G18 — NATURAL_FRIENDSHIP structural tests
# ---------------------------------------------------------------------------

class TestNaturalFriendshipStructure:
    def test_all_nine_grahas_present(self):
        """All 9 grahas must be keys in NATURAL_FRIENDSHIP."""
        for g in GRAHAS:
            assert g in NATURAL_FRIENDSHIP, f"Missing graha key: {g}"

    def test_each_graha_has_eight_entries(self):
        """Each graha's friendship dict must have exactly 8 entries (one per other graha)."""
        for g in GRAHAS:
            others = NATURAL_FRIENDSHIP[g]
            assert len(others) == 8, (
                f"{g} has {len(others)} entries, expected 8"
            )

    def test_no_self_reference(self):
        """No graha should reference itself in its own friendship dict."""
        for g in GRAHAS:
            assert g not in NATURAL_FRIENDSHIP[g], (
                f"{g} has a self-reference in NATURAL_FRIENDSHIP"
            )

    def test_all_values_are_valid_relationships(self):
        """All relationship values must be 'mitra', 'sama', or 'shatru'."""
        valid = {"mitra", "sama", "shatru"}
        for g, others in NATURAL_FRIENDSHIP.items():
            for other, rel in others.items():
                assert rel in valid, (
                    f"Invalid relationship '{rel}' for {g}→{other}"
                )

    def test_each_graha_covers_all_others(self):
        """Each graha's dict keys must be exactly the other 8 grahas."""
        graha_set = set(GRAHAS)
        for g in GRAHAS:
            expected = graha_set - {g}
            actual = set(NATURAL_FRIENDSHIP[g].keys())
            assert expected == actual, (
                f"{g}: expected keys {expected}, got {actual}"
            )


# ---------------------------------------------------------------------------
# G18 — Classical BPHS friendship facts
# ---------------------------------------------------------------------------

class TestClassicalFriendshipFacts:
    def test_sun_is_mitra_to_moon(self):
        assert NATURAL_FRIENDSHIP["sun"]["moon"] == "mitra"

    def test_sun_is_mitra_to_mars(self):
        assert NATURAL_FRIENDSHIP["sun"]["mars"] == "mitra"

    def test_sun_is_mitra_to_jupiter(self):
        assert NATURAL_FRIENDSHIP["sun"]["jupiter"] == "mitra"

    def test_sun_is_sama_to_mercury(self):
        assert NATURAL_FRIENDSHIP["sun"]["mercury"] == "sama"

    def test_sun_is_shatru_to_saturn(self):
        assert NATURAL_FRIENDSHIP["sun"]["saturn"] == "shatru"

    def test_sun_is_shatru_to_venus(self):
        assert NATURAL_FRIENDSHIP["sun"]["venus"] == "shatru"

    def test_moon_is_mitra_to_sun(self):
        assert NATURAL_FRIENDSHIP["moon"]["sun"] == "mitra"

    def test_jupiter_is_mitra_to_sun(self):
        assert NATURAL_FRIENDSHIP["jupiter"]["sun"] == "mitra"

    def test_jupiter_is_mitra_to_moon(self):
        assert NATURAL_FRIENDSHIP["jupiter"]["moon"] == "mitra"

    def test_jupiter_is_mitra_to_mars(self):
        assert NATURAL_FRIENDSHIP["jupiter"]["mars"] == "mitra"

    def test_jupiter_is_shatru_to_mercury(self):
        assert NATURAL_FRIENDSHIP["jupiter"]["mercury"] == "shatru"

    def test_jupiter_is_shatru_to_venus(self):
        assert NATURAL_FRIENDSHIP["jupiter"]["venus"] == "shatru"

    def test_saturn_is_mitra_to_venus(self):
        assert NATURAL_FRIENDSHIP["saturn"]["venus"] == "mitra"

    def test_saturn_is_mitra_to_mercury(self):
        assert NATURAL_FRIENDSHIP["saturn"]["mercury"] == "mitra"

    def test_saturn_is_shatru_to_sun(self):
        assert NATURAL_FRIENDSHIP["saturn"]["sun"] == "shatru"

    def test_saturn_is_shatru_to_moon(self):
        assert NATURAL_FRIENDSHIP["saturn"]["moon"] == "shatru"

    def test_saturn_is_shatru_to_mars(self):
        assert NATURAL_FRIENDSHIP["saturn"]["mars"] == "shatru"

    def test_venus_is_mitra_to_mercury(self):
        assert NATURAL_FRIENDSHIP["venus"]["mercury"] == "mitra"

    def test_venus_is_mitra_to_saturn(self):
        assert NATURAL_FRIENDSHIP["venus"]["saturn"] == "mitra"

    def test_mars_is_mitra_to_sun(self):
        assert NATURAL_FRIENDSHIP["mars"]["sun"] == "mitra"

    def test_mars_is_mitra_to_moon(self):
        assert NATURAL_FRIENDSHIP["mars"]["moon"] == "mitra"

    def test_mars_is_shatru_to_mercury(self):
        assert NATURAL_FRIENDSHIP["mars"]["mercury"] == "shatru"

    def test_rahu_is_mitra_to_mercury(self):
        assert NATURAL_FRIENDSHIP["rahu"]["mercury"] == "mitra"

    def test_rahu_is_mitra_to_venus(self):
        assert NATURAL_FRIENDSHIP["rahu"]["venus"] == "mitra"

    def test_rahu_is_mitra_to_saturn(self):
        assert NATURAL_FRIENDSHIP["rahu"]["saturn"] == "mitra"

    def test_rahu_is_shatru_to_sun(self):
        assert NATURAL_FRIENDSHIP["rahu"]["sun"] == "shatru"

    def test_rahu_is_shatru_to_moon(self):
        assert NATURAL_FRIENDSHIP["rahu"]["moon"] == "shatru"

    def test_ketu_is_mitra_to_saturn(self):
        assert NATURAL_FRIENDSHIP["ketu"]["saturn"] == "mitra"

    def test_ketu_is_shatru_to_sun(self):
        assert NATURAL_FRIENDSHIP["ketu"]["sun"] == "shatru"

    def test_ketu_is_shatru_to_moon(self):
        assert NATURAL_FRIENDSHIP["ketu"]["moon"] == "shatru"

    def test_asymmetry_sun_saturn(self):
        """Sun sees Saturn as shatru; Saturn also sees Sun as shatru — symmetric here."""
        assert NATURAL_FRIENDSHIP["sun"]["saturn"] == "shatru"
        assert NATURAL_FRIENDSHIP["saturn"]["sun"] == "shatru"

    def test_asymmetry_sun_mercury(self):
        """Sun sees Mercury as sama; Mercury sees Sun as mitra — classic asymmetry."""
        assert NATURAL_FRIENDSHIP["sun"]["mercury"] == "sama"
        assert NATURAL_FRIENDSHIP["mercury"]["sun"] == "mitra"


# ---------------------------------------------------------------------------
# G19a — HOUSE_KARAKAS structural tests
# ---------------------------------------------------------------------------

class TestHouseKarakasStructure:
    def test_all_twelve_houses_present(self):
        """All 12 houses must have entries."""
        for h in range(1, 13):
            assert h in HOUSE_KARAKAS, f"House {h} missing from HOUSE_KARAKAS"

    def test_all_houses_have_non_empty_lists(self):
        """Every house must have at least one karaka."""
        for h in range(1, 13):
            assert len(HOUSE_KARAKAS[h]) > 0, f"House {h} has empty karaka list"

    def test_house_1_contains_sun(self):
        assert "sun" in HOUSE_KARAKAS[1]

    def test_house_2_contains_jupiter(self):
        assert "jupiter" in HOUSE_KARAKAS[2]

    def test_house_3_contains_mars(self):
        assert "mars" in HOUSE_KARAKAS[3]

    def test_house_3_contains_mercury(self):
        assert "mercury" in HOUSE_KARAKAS[3]

    def test_house_4_contains_moon(self):
        assert "moon" in HOUSE_KARAKAS[4]

    def test_house_5_contains_jupiter(self):
        assert "jupiter" in HOUSE_KARAKAS[5]

    def test_house_7_contains_venus(self):
        assert "venus" in HOUSE_KARAKAS[7]

    def test_house_8_contains_saturn(self):
        assert "saturn" in HOUSE_KARAKAS[8]

    def test_house_9_contains_jupiter(self):
        assert "jupiter" in HOUSE_KARAKAS[9]

    def test_house_10_contains_sun(self):
        assert "sun" in HOUSE_KARAKAS[10]

    def test_house_10_contains_saturn(self):
        assert "saturn" in HOUSE_KARAKAS[10]

    def test_house_12_contains_ketu(self):
        assert "ketu" in HOUSE_KARAKAS[12]

    def test_all_karaka_values_are_valid_grahas(self):
        """Every karaka value must be a known graha name."""
        graha_set = set(GRAHAS)
        for h, karakas in HOUSE_KARAKAS.items():
            for k in karakas:
                assert k in graha_set, (
                    f"House {h} has unknown karaka '{k}'"
                )


# ---------------------------------------------------------------------------
# G19b — DOMAIN_KARAKAS structural tests
# ---------------------------------------------------------------------------

class TestDomainKarakasStructure:
    def test_all_domains_have_non_empty_lists(self):
        """Every domain key must map to a non-empty list."""
        for domain, karakas in DOMAIN_KARAKAS.items():
            assert len(karakas) > 0, f"Domain '{domain}' has empty karaka list"

    def test_marriage_contains_venus(self):
        assert "venus" in DOMAIN_KARAKAS["marriage"]

    def test_marriage_contains_jupiter(self):
        assert "jupiter" in DOMAIN_KARAKAS["marriage"]

    def test_children_contains_jupiter(self):
        assert "jupiter" in DOMAIN_KARAKAS["children"]

    def test_children_contains_moon(self):
        assert "moon" in DOMAIN_KARAKAS["children"]

    def test_career_contains_saturn(self):
        assert "saturn" in DOMAIN_KARAKAS["career"]

    def test_career_contains_sun(self):
        assert "sun" in DOMAIN_KARAKAS["career"]

    def test_wealth_contains_jupiter(self):
        assert "jupiter" in DOMAIN_KARAKAS["wealth"]

    def test_health_contains_sun(self):
        assert "sun" in DOMAIN_KARAKAS["health"]

    def test_education_contains_mercury(self):
        assert "mercury" in DOMAIN_KARAKAS["education"]

    def test_spirituality_contains_ketu(self):
        assert "ketu" in DOMAIN_KARAKAS["spirituality"]

    def test_longevity_contains_saturn(self):
        assert "saturn" in DOMAIN_KARAKAS["longevity"]

    def test_siblings_contains_mars(self):
        assert "mars" in DOMAIN_KARAKAS["siblings"]

    def test_mother_contains_moon(self):
        assert "moon" in DOMAIN_KARAKAS["mother"]

    def test_father_contains_sun(self):
        assert "sun" in DOMAIN_KARAKAS["father"]

    def test_enemies_contains_mars(self):
        assert "mars" in DOMAIN_KARAKAS["enemies"]

    def test_all_domain_karaka_values_valid(self):
        """Every domain karaka must be a known graha."""
        graha_set = set(GRAHAS)
        for domain, karakas in DOMAIN_KARAKAS.items():
            for k in karakas:
                assert k in graha_set, (
                    f"Domain '{domain}' has unknown karaka '{k}'"
                )


# ---------------------------------------------------------------------------
# Function behaviour tests
# ---------------------------------------------------------------------------

class TestGetNaturalFriendship:
    def test_sun_moon_returns_mitra(self):
        assert get_natural_friendship("sun", "moon") == "mitra"

    def test_sun_saturn_returns_shatru(self):
        assert get_natural_friendship("sun", "saturn") == "shatru"

    def test_moon_mars_returns_sama(self):
        assert get_natural_friendship("moon", "mars") == "sama"

    def test_uppercase_input_normalised(self):
        assert get_natural_friendship("Sun", "Moon") == "mitra"

    def test_invalid_graha1_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown graha"):
            get_natural_friendship("pluto", "sun")

    def test_invalid_graha2_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown graha"):
            get_natural_friendship("sun", "pluto")

    def test_self_reference_raises_value_error(self):
        with pytest.raises(ValueError, match="must differ"):
            get_natural_friendship("sun", "sun")

    def test_returns_string(self):
        result = get_natural_friendship("jupiter", "venus")
        assert isinstance(result, str)
        assert result in {"mitra", "sama", "shatru"}


class TestGetHouseKaraka:
    def test_house_1_returns_list_with_sun(self):
        result = get_house_karaka(1)
        assert isinstance(result, list)
        assert "sun" in result

    def test_house_7_returns_list_with_venus(self):
        result = get_house_karaka(7)
        assert "venus" in result

    def test_house_12_returns_list_with_saturn_and_ketu(self):
        result = get_house_karaka(12)
        assert "saturn" in result
        assert "ketu" in result

    def test_out_of_range_house_raises_value_error(self):
        with pytest.raises(ValueError):
            get_house_karaka(0)

    def test_house_13_raises_value_error(self):
        with pytest.raises(ValueError):
            get_house_karaka(13)

    def test_returns_independent_copy(self):
        """Mutating the returned list must not affect HOUSE_KARAKAS."""
        result = get_house_karaka(1)
        result.append("__test__")
        assert "__test__" not in HOUSE_KARAKAS[1]


class TestGetDomainKaraka:
    def test_marriage_returns_venus(self):
        result = get_domain_karaka("marriage")
        assert "venus" in result

    def test_children_returns_jupiter(self):
        result = get_domain_karaka("children")
        assert "jupiter" in result

    def test_career_returns_saturn(self):
        result = get_domain_karaka("career")
        assert "saturn" in result

    def test_uppercase_domain_normalised(self):
        result = get_domain_karaka("MARRIAGE")
        assert "venus" in result

    def test_unknown_domain_raises_key_error(self):
        with pytest.raises(KeyError):
            get_domain_karaka("romance")

    def test_returns_list(self):
        result = get_domain_karaka("wealth")
        assert isinstance(result, list)
        assert len(result) > 0


class TestGetCompositeFriendship:
    def test_stub_returns_natural_for_sun_moon(self):
        """Stub should return same as natural friendship."""
        assert get_composite_friendship("sun", "moon") == get_natural_friendship("sun", "moon")

    def test_stub_returns_natural_for_sun_saturn(self):
        assert get_composite_friendship("sun", "saturn") == "shatru"

    def test_stub_raises_for_invalid_graha(self):
        with pytest.raises(ValueError):
            get_composite_friendship("sun", "neptune")
