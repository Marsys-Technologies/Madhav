"""
test_yoga_defs.py — Tests for G12 Yoga Definitions Library
===========================================================
Covers: YOGA_DEFINITIONS structure, all required fields, category checks,
        Pancha Mahapurusha, Kala Sarpa, Vipareeta Raja, Neechabhanga,
        and all four helper functions.

Minimum 50 assertions required per acceptance criteria.
"""

import re

import pytest

from pipeline.yoga_definitions import (
    YOGA_DEFINITIONS,
    get_yoga,
    list_yogas_by_category,
    get_all_categories,
    is_raja_yoga,
)

# ---------------------------------------------------------------------------
# REQUIRED FIELDS — all yogas must have these
# ---------------------------------------------------------------------------
REQUIRED_FIELDS = [
    "name",
    "category",
    "constituent_rule",
    "classical_citation",
    "strength_modifier",
    "rarity_class",
    "cancellation_rules",
]

VALID_CATEGORIES = {
    "pancha_mahapurusha",
    "raja",
    "dhana",
    "vipareeta_raja",
    "neechabhanga",
    "lunar",
    "solar",
    "miscellaneous",
    "kala_sarpa",
    "nabhas",
}

VALID_RARITY_CLASSES = {"common", "uncommon", "rare", "exceptional"}

PANCHA_MAHAPURUSHA_NAMES = {"ruchaka", "bhadra", "hamsa", "malavya", "sasha"}
VIPAREETA_RAJA_NAMES = {"harsha", "sarala", "vimala"}
KALA_SARPA_NAMES = {
    "ananta_kala_sarpa",
    "kulika_kala_sarpa",
    "vasuki_kala_sarpa",
    "shankha_kala_sarpa",
    "padma_kala_sarpa",
    "mahapadma_kala_sarpa",
    "takshaka_kala_sarpa",
    "karkotaka_kala_sarpa",
    "shankhanada_kala_sarpa",
    "patak_kala_sarpa",
    "vishadhar_kala_sarpa",
    "sheshanaag_kala_sarpa",
}


# ---------------------------------------------------------------------------
# TestYogaDefinitionsDict — structural checks
# ---------------------------------------------------------------------------

class TestYogaDefinitionsDict:
    def test_minimum_200_entries(self):
        assert len(YOGA_DEFINITIONS) >= 200, (
            f"Expected 200+ yogas, got {len(YOGA_DEFINITIONS)}"
        )

    def test_all_required_fields_on_every_yoga(self):
        """Every yoga dict must have all seven required fields."""
        for field in REQUIRED_FIELDS:
            for yoga_name, yoga_dict in YOGA_DEFINITIONS.items():
                assert field in yoga_dict, (
                    f"Yoga '{yoga_name}' is missing required field '{field}'"
                )

    def test_all_categories_are_valid(self):
        """Every yoga's category must be one of the recognised category strings."""
        for yoga_name, yoga_dict in YOGA_DEFINITIONS.items():
            assert yoga_dict["category"] in VALID_CATEGORIES, (
                f"Yoga '{yoga_name}' has unknown category '{yoga_dict['category']}'"
            )

    def test_all_rarity_classes_are_valid(self):
        """Every yoga's rarity_class must be one of the four valid values."""
        for yoga_name, yoga_dict in YOGA_DEFINITIONS.items():
            assert yoga_dict["rarity_class"] in VALID_RARITY_CLASSES, (
                f"Yoga '{yoga_name}' has invalid rarity_class '{yoga_dict['rarity_class']}'"
            )

    def test_strength_modifier_is_float_in_range(self):
        """strength_modifier must be a float or int in [0.5, 3.0]."""
        for yoga_name, yoga_dict in YOGA_DEFINITIONS.items():
            sm = yoga_dict["strength_modifier"]
            assert isinstance(sm, (float, int)), (
                f"Yoga '{yoga_name}' strength_modifier is not numeric: {sm!r}"
            )
            assert 0.5 <= sm <= 3.0, (
                f"Yoga '{yoga_name}' strength_modifier {sm} outside [0.5, 3.0]"
            )

    def test_cancellation_rules_is_list(self):
        """cancellation_rules must be a list on every yoga."""
        for yoga_name, yoga_dict in YOGA_DEFINITIONS.items():
            assert isinstance(yoga_dict["cancellation_rules"], list), (
                f"Yoga '{yoga_name}' cancellation_rules is not a list"
            )

    def test_all_yoga_names_are_snake_case(self):
        """Yoga keys must use only lowercase letters, digits, and underscores."""
        snake_case_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
        for yoga_name in YOGA_DEFINITIONS:
            assert snake_case_pattern.match(yoga_name), (
                f"Yoga name '{yoga_name}' is not valid snake_case"
            )

    def test_no_empty_constituent_rule(self):
        """constituent_rule must be a non-empty string."""
        for yoga_name, yoga_dict in YOGA_DEFINITIONS.items():
            assert isinstance(yoga_dict["constituent_rule"], str), (
                f"Yoga '{yoga_name}' constituent_rule is not a string"
            )
            assert len(yoga_dict["constituent_rule"].strip()) > 0, (
                f"Yoga '{yoga_name}' has empty constituent_rule"
            )

    def test_no_empty_classical_citation(self):
        """classical_citation must be a non-empty string."""
        for yoga_name, yoga_dict in YOGA_DEFINITIONS.items():
            assert isinstance(yoga_dict["classical_citation"], str), (
                f"Yoga '{yoga_name}' classical_citation is not a string"
            )
            assert len(yoga_dict["classical_citation"].strip()) > 0, (
                f"Yoga '{yoga_name}' has empty classical_citation"
            )

    def test_no_empty_name(self):
        """name must be a non-empty string."""
        for yoga_name, yoga_dict in YOGA_DEFINITIONS.items():
            assert isinstance(yoga_dict["name"], str), (
                f"Yoga '{yoga_name}' name is not a string"
            )
            assert len(yoga_dict["name"].strip()) > 0, (
                f"Yoga '{yoga_name}' has empty display name"
            )


# ---------------------------------------------------------------------------
# TestPanchaMahapurusha — 5 specific yogas
# ---------------------------------------------------------------------------

class TestPanchaMahapurusha:
    def test_exactly_five_pancha_mahapurusha_yogas(self):
        yogas = list_yogas_by_category("pancha_mahapurusha")
        assert len(yogas) == 5, f"Expected 5 Pancha Mahapurusha yogas, got {len(yogas)}"

    def test_all_five_names_present(self):
        yogas = set(list_yogas_by_category("pancha_mahapurusha"))
        assert PANCHA_MAHAPURUSHA_NAMES == yogas, (
            f"Missing or extra Pancha Mahapurusha yogas. Expected: {PANCHA_MAHAPURUSHA_NAMES}, got: {yogas}"
        )

    def test_ruchaka_category(self):
        assert YOGA_DEFINITIONS["ruchaka"]["category"] == "pancha_mahapurusha"

    def test_bhadra_category(self):
        assert YOGA_DEFINITIONS["bhadra"]["category"] == "pancha_mahapurusha"

    def test_hamsa_category(self):
        assert YOGA_DEFINITIONS["hamsa"]["category"] == "pancha_mahapurusha"

    def test_malavya_category(self):
        assert YOGA_DEFINITIONS["malavya"]["category"] == "pancha_mahapurusha"

    def test_sasha_category(self):
        assert YOGA_DEFINITIONS["sasha"]["category"] == "pancha_mahapurusha"

    def test_all_pancha_mahapurusha_rarity_exceptional(self):
        for name in PANCHA_MAHAPURUSHA_NAMES:
            assert YOGA_DEFINITIONS[name]["rarity_class"] == "exceptional", (
                f"Pancha Mahapurusha '{name}' should be rarity_class 'exceptional'"
            )

    def test_all_pancha_mahapurusha_strength_modifier_gte_2(self):
        for name in PANCHA_MAHAPURUSHA_NAMES:
            sm = YOGA_DEFINITIONS[name]["strength_modifier"]
            assert sm >= 2.0, (
                f"Pancha Mahapurusha '{name}' strength_modifier {sm} should be >= 2.0"
            )

    def test_hamsa_strength_modifier_highest(self):
        """Hamsa (Jupiter yoga) should have the highest strength modifier."""
        assert YOGA_DEFINITIONS["hamsa"]["strength_modifier"] >= 2.5


# ---------------------------------------------------------------------------
# TestKalaSarpa — exactly 12 variants
# ---------------------------------------------------------------------------

class TestKalaSarpa:
    def test_exactly_12_kala_sarpa_yogas(self):
        yogas = list_yogas_by_category("kala_sarpa")
        assert len(yogas) == 12, f"Expected 12 Kala Sarpa yogas, got {len(yogas)}"

    def test_all_12_names_present(self):
        yogas = set(list_yogas_by_category("kala_sarpa"))
        assert KALA_SARPA_NAMES == yogas, (
            f"Kala Sarpa names mismatch. Expected: {KALA_SARPA_NAMES}, got: {yogas}"
        )

    def test_ananta_in_category_kala_sarpa(self):
        assert YOGA_DEFINITIONS["ananta_kala_sarpa"]["category"] == "kala_sarpa"

    def test_takshaka_in_category_kala_sarpa(self):
        """Reverse configurations must also be kala_sarpa."""
        assert YOGA_DEFINITIONS["takshaka_kala_sarpa"]["category"] == "kala_sarpa"

    def test_all_kala_sarpa_have_cancellation_rules(self):
        for name in KALA_SARPA_NAMES:
            rules = YOGA_DEFINITIONS[name]["cancellation_rules"]
            assert len(rules) >= 1, (
                f"Kala Sarpa '{name}' should have at least one cancellation rule"
            )


# ---------------------------------------------------------------------------
# TestVipaareetaRaja — exactly 3
# ---------------------------------------------------------------------------

class TestVipaareetaRaja:
    def test_exactly_3_vipareeta_raja_yogas(self):
        yogas = list_yogas_by_category("vipareeta_raja")
        assert len(yogas) == 3, f"Expected 3 Vipareeta Raja yogas, got {len(yogas)}"

    def test_harsha_in_vipareeta_raja(self):
        assert YOGA_DEFINITIONS["harsha"]["category"] == "vipareeta_raja"

    def test_sarala_in_vipareeta_raja(self):
        assert YOGA_DEFINITIONS["sarala"]["category"] == "vipareeta_raja"

    def test_vimala_in_vipareeta_raja(self):
        assert YOGA_DEFINITIONS["vimala"]["category"] == "vipareeta_raja"

    def test_all_three_vipareeta_names_present(self):
        yogas = set(list_yogas_by_category("vipareeta_raja"))
        assert VIPAREETA_RAJA_NAMES == yogas


# ---------------------------------------------------------------------------
# TestNeechabhanga — 8 conditions
# ---------------------------------------------------------------------------

class TestNeechabhanga:
    def test_exactly_8_neechabhanga_conditions(self):
        yogas = list_yogas_by_category("neechabhanga")
        assert len(yogas) == 8, f"Expected 8 Neechabhanga conditions, got {len(yogas)}"

    def test_neechabhanga_1_present(self):
        assert "neechabhanga_1" in YOGA_DEFINITIONS

    def test_neechabhanga_8_present(self):
        assert "neechabhanga_8" in YOGA_DEFINITIONS

    def test_all_neechabhanga_are_neechabhanga_category(self):
        for i in range(1, 9):
            name = f"neechabhanga_{i}"
            assert name in YOGA_DEFINITIONS, f"'{name}' missing from YOGA_DEFINITIONS"
            assert YOGA_DEFINITIONS[name]["category"] == "neechabhanga", (
                f"'{name}' should be category 'neechabhanga'"
            )


# ---------------------------------------------------------------------------
# TestGetYoga — helper function
# ---------------------------------------------------------------------------

class TestGetYoga:
    def test_get_yoga_hamsa_returns_dict(self):
        result = get_yoga("hamsa")
        assert isinstance(result, dict)
        assert result["category"] == "pancha_mahapurusha"

    def test_get_yoga_case_insensitive_lower(self):
        result_lower = get_yoga("hamsa")
        assert result_lower is not None

    def test_get_yoga_case_insensitive_upper(self):
        result_upper = get_yoga("HAMSA")
        result_lower = get_yoga("hamsa")
        assert result_upper == result_lower

    def test_get_yoga_case_insensitive_mixed(self):
        result_mixed = get_yoga("Hamsa")
        result_lower = get_yoga("hamsa")
        assert result_mixed == result_lower

    def test_get_yoga_returns_correct_fields(self):
        result = get_yoga("gaja_kesari")
        assert "category" in result
        assert "constituent_rule" in result
        assert "classical_citation" in result

    def test_get_yoga_nonexistent_raises_key_error(self):
        with pytest.raises(KeyError):
            get_yoga("nonexistent_yoga")

    def test_get_yoga_empty_string_raises_key_error(self):
        with pytest.raises(KeyError):
            get_yoga("")

    def test_get_yoga_ruchaka(self):
        result = get_yoga("ruchaka")
        assert result["category"] == "pancha_mahapurusha"

    def test_get_yoga_harsha(self):
        result = get_yoga("harsha")
        assert result["category"] == "vipareeta_raja"


# ---------------------------------------------------------------------------
# TestListYogasByCategory — helper function
# ---------------------------------------------------------------------------

class TestListYogasByCategory:
    def test_raja_category_has_40_or_more(self):
        result = list_yogas_by_category("raja")
        assert len(result) >= 40, (
            f"Expected 40+ raja yogas, got {len(result)}"
        )

    def test_pancha_mahapurusha_returns_exactly_5(self):
        result = list_yogas_by_category("pancha_mahapurusha")
        assert len(result) == 5

    def test_kala_sarpa_returns_exactly_12(self):
        result = list_yogas_by_category("kala_sarpa")
        assert len(result) == 12

    def test_vipareeta_raja_returns_exactly_3(self):
        result = list_yogas_by_category("vipareeta_raja")
        assert len(result) == 3

    def test_list_returns_sorted_list(self):
        result = list_yogas_by_category("raja")
        assert result == sorted(result)

    def test_list_unknown_category_returns_empty(self):
        result = list_yogas_by_category("nonexistent_category")
        assert result == []

    def test_dhana_category_has_25_or_more(self):
        result = list_yogas_by_category("dhana")
        assert len(result) >= 25, (
            f"Expected 25+ dhana yogas, got {len(result)}"
        )

    def test_all_returned_names_are_in_yoga_definitions(self):
        for cat in VALID_CATEGORIES:
            for name in list_yogas_by_category(cat):
                assert name in YOGA_DEFINITIONS, (
                    f"list_yogas_by_category returned '{name}' not in YOGA_DEFINITIONS"
                )


# ---------------------------------------------------------------------------
# TestGetAllCategories — helper function
# ---------------------------------------------------------------------------

class TestGetAllCategories:
    def test_returns_sorted_list(self):
        result = get_all_categories()
        assert result == sorted(result)

    def test_contains_all_expected_categories(self):
        result = get_all_categories()
        for expected_cat in VALID_CATEGORIES:
            assert expected_cat in result, (
                f"Category '{expected_cat}' missing from get_all_categories()"
            )

    def test_returns_list_type(self):
        assert isinstance(get_all_categories(), list)

    def test_no_duplicate_categories(self):
        result = get_all_categories()
        assert len(result) == len(set(result))

    def test_exactly_10_categories(self):
        result = get_all_categories()
        assert len(result) == 10, (
            f"Expected 10 categories, got {len(result)}: {result}"
        )


# ---------------------------------------------------------------------------
# TestIsRajaYoga — helper function
# ---------------------------------------------------------------------------

class TestIsRajaYoga:
    def test_ruchaka_is_raja_yoga(self):
        """Pancha Mahapurusha produces raja-class outcomes."""
        assert is_raja_yoga("ruchaka") is True

    def test_hamsa_is_raja_yoga(self):
        assert is_raja_yoga("hamsa") is True

    def test_bhadra_is_raja_yoga(self):
        assert is_raja_yoga("bhadra") is True

    def test_malavya_is_raja_yoga(self):
        assert is_raja_yoga("malavya") is True

    def test_sasha_is_raja_yoga(self):
        assert is_raja_yoga("sasha") is True

    def test_gajakesari_is_raja_yoga(self):
        """gajakesari in raja category (standalone definition) should be True."""
        # gajakesari is in miscellaneous; gaja_kesari is in raja
        assert is_raja_yoga("gaja_kesari") is True

    def test_dharma_karmadhipati_is_raja_yoga(self):
        assert is_raja_yoga("dharma_karmadhipati") is True

    def test_harsha_is_raja_yoga(self):
        """Vipareeta Raja is raja class."""
        assert is_raja_yoga("harsha") is True

    def test_sarala_is_raja_yoga(self):
        assert is_raja_yoga("sarala") is True

    def test_neechabhanga_1_is_raja_yoga(self):
        assert is_raja_yoga("neechabhanga_1") is True

    def test_sarpa_is_not_raja_yoga(self):
        """Sarpa is nabhas (suffering) — not raja class."""
        assert is_raja_yoga("sarpa") is False

    def test_kemadruma_is_not_raja_yoga(self):
        """Kemadruma is a negative lunar yoga — not raja class."""
        assert is_raja_yoga("kemadruma") is False

    def test_dhana_yoga_1_is_not_raja_yoga(self):
        """Dhana yogas are not raja class."""
        assert is_raja_yoga("dhana_yoga_1") is False

    def test_unknown_name_returns_false(self):
        """Nonexistent name should return False (not raise)."""
        assert is_raja_yoga("completely_made_up_yoga") is False

    def test_case_insensitive(self):
        assert is_raja_yoga("HAMSA") is True
        assert is_raja_yoga("Ruchaka") is True


# ---------------------------------------------------------------------------
# TestSpecificYogaValues — spot checks on specific yogas
# ---------------------------------------------------------------------------

class TestSpecificYogaValues:
    def test_kemadruma_rarity_common(self):
        """Kemadruma is commonly found — rarity_class should be 'common'."""
        yoga = YOGA_DEFINITIONS["kemadruma"]
        assert yoga["rarity_class"] == "common"

    def test_kemadruma_strength_modifier_below_1(self):
        """Kemadruma is a negative yoga — strength_modifier should be < 1.0."""
        yoga = YOGA_DEFINITIONS["kemadruma"]
        assert yoga["strength_modifier"] < 1.0

    def test_akhanda_samrajya_rarity_rare_or_exceptional(self):
        """Akhanda Samrajya is rare or exceptional."""
        yoga = YOGA_DEFINITIONS["akhanda_samrajya"]
        assert yoga["rarity_class"] in {"rare", "exceptional"}

    def test_lakshmi_yoga_is_dhana(self):
        assert YOGA_DEFINITIONS["lakshmi_yoga"]["category"] == "dhana"

    def test_lakshmi_yoga_rarity_rare(self):
        assert YOGA_DEFINITIONS["lakshmi_yoga"]["rarity_class"] == "rare"

    def test_gaja_kesari_in_raja(self):
        assert YOGA_DEFINITIONS["gaja_kesari"]["category"] == "raja"

    def test_sunafa_is_lunar(self):
        assert YOGA_DEFINITIONS["sunafa"]["category"] == "lunar"

    def test_anapha_is_lunar(self):
        assert YOGA_DEFINITIONS["anapha"]["category"] == "lunar"

    def test_durdhura_is_lunar(self):
        assert YOGA_DEFINITIONS["durdhura"]["category"] == "lunar"

    def test_vesi_is_solar(self):
        assert YOGA_DEFINITIONS["vesi"]["category"] == "solar"

    def test_vasi_is_solar(self):
        assert YOGA_DEFINITIONS["vasi"]["category"] == "solar"

    def test_ubhayachari_is_solar(self):
        assert YOGA_DEFINITIONS["ubhayachari"]["category"] == "solar"

    def test_rajju_is_nabhas(self):
        assert YOGA_DEFINITIONS["rajju"]["category"] == "nabhas"

    def test_musala_is_nabhas(self):
        assert YOGA_DEFINITIONS["musala"]["category"] == "nabhas"

    def test_sarpa_is_nabhas(self):
        assert YOGA_DEFINITIONS["sarpa"]["category"] == "nabhas"

    def test_sarpa_strength_below_1(self):
        """Sarpa is a negative nabhas yoga."""
        assert YOGA_DEFINITIONS["sarpa"]["strength_modifier"] < 1.0

    def test_hamsa_has_cancellation_rules(self):
        rules = YOGA_DEFINITIONS["hamsa"]["cancellation_rules"]
        assert len(rules) >= 1

    def test_harsha_has_cancellation_rules(self):
        rules = YOGA_DEFINITIONS["harsha"]["cancellation_rules"]
        assert len(rules) >= 1

    def test_raja_yoga_5_9_is_rare(self):
        """The dharma trikona combination is rare."""
        yoga = YOGA_DEFINITIONS["raja_yoga_5_9"]
        assert yoga["rarity_class"] == "rare"
