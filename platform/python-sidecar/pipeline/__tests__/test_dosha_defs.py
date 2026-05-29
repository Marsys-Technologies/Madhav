"""
test_dosha_defs.py — Tests for G13 Dosha Definitions Library
=============================================================
Covers: DOSHA_DEFINITIONS structure, all required fields, category checks,
        Mangal Dosha house variants, severity checks, and all five helper functions.

Minimum 40 assertions required per acceptance criteria.
"""

import re

import pytest

from pipeline.dosha_definitions import (
    DOSHA_DEFINITIONS,
    get_dosha,
    list_doshas_by_category,
    list_doshas_by_severity,
    get_all_dosha_categories,
    get_mangal_dosha_houses,
)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = [
    "name",
    "category",
    "constituent_predicate",
    "severity",
    "cancellation_rules",
    "classical_citation",
    "affected_domains",
    "remedy_approach",
]

VALID_CATEGORIES = {
    "mangal",
    "kala_sarpa",
    "pitru",
    "matri",
    "graha_dosha",
    "dasha_dosha",
    "yoga_dosha",
    "miscellaneous",
}

VALID_SEVERITIES = {"mild", "moderate", "severe", "very_severe"}

MANGAL_DOSHA_HOUSE_KEYS = {
    "mangal_dosha_1h",
    "mangal_dosha_2h",
    "mangal_dosha_4h",
    "mangal_dosha_7h",
    "mangal_dosha_8h",
    "mangal_dosha_12h",
}


# ---------------------------------------------------------------------------
# TestDoshaDefinitionsDict — structural checks
# ---------------------------------------------------------------------------

class TestDoshaDefinitionsDict:
    def test_minimum_20_entries(self):
        assert len(DOSHA_DEFINITIONS) >= 20, (
            f"Expected 20+ doshas, got {len(DOSHA_DEFINITIONS)}"
        )

    def test_all_required_fields_on_every_entry(self):
        """Every dosha dict must have all required fields."""
        for field in REQUIRED_FIELDS:
            for dosha_name, dosha_dict in DOSHA_DEFINITIONS.items():
                assert field in dosha_dict, (
                    f"Dosha '{dosha_name}' is missing required field '{field}'"
                )

    def test_all_categories_are_valid(self):
        """Every dosha category must be one of the recognised strings."""
        for dosha_name, dosha_dict in DOSHA_DEFINITIONS.items():
            assert dosha_dict["category"] in VALID_CATEGORIES, (
                f"Dosha '{dosha_name}' has unknown category '{dosha_dict['category']}'"
            )

    def test_all_severity_values_are_valid(self):
        """Every dosha severity must be one of the four valid values."""
        for dosha_name, dosha_dict in DOSHA_DEFINITIONS.items():
            assert dosha_dict["severity"] in VALID_SEVERITIES, (
                f"Dosha '{dosha_name}' has invalid severity '{dosha_dict['severity']}'"
            )

    def test_cancellation_rules_is_list_on_every_entry(self):
        """cancellation_rules must be a list on every dosha."""
        for dosha_name, dosha_dict in DOSHA_DEFINITIONS.items():
            assert isinstance(dosha_dict["cancellation_rules"], list), (
                f"Dosha '{dosha_name}' cancellation_rules is not a list"
            )

    def test_affected_domains_is_list_on_every_entry(self):
        """affected_domains must be a list on every dosha."""
        for dosha_name, dosha_dict in DOSHA_DEFINITIONS.items():
            assert isinstance(dosha_dict["affected_domains"], list), (
                f"Dosha '{dosha_name}' affected_domains is not a list"
            )

    def test_all_dosha_names_are_snake_case(self):
        """Dosha keys must use only lowercase letters, digits, and underscores."""
        snake_case_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
        for dosha_name in DOSHA_DEFINITIONS:
            assert snake_case_pattern.match(dosha_name), (
                f"Dosha name '{dosha_name}' is not valid snake_case"
            )

    def test_no_empty_constituent_predicate(self):
        """constituent_predicate must be a non-empty string."""
        for dosha_name, dosha_dict in DOSHA_DEFINITIONS.items():
            assert isinstance(dosha_dict["constituent_predicate"], str), (
                f"Dosha '{dosha_name}' constituent_predicate is not a string"
            )
            assert len(dosha_dict["constituent_predicate"].strip()) > 0, (
                f"Dosha '{dosha_name}' has empty constituent_predicate"
            )

    def test_no_empty_classical_citation(self):
        """classical_citation must be a non-empty string."""
        for dosha_name, dosha_dict in DOSHA_DEFINITIONS.items():
            assert isinstance(dosha_dict["classical_citation"], str), (
                f"Dosha '{dosha_name}' classical_citation is not a string"
            )
            assert len(dosha_dict["classical_citation"].strip()) > 0, (
                f"Dosha '{dosha_name}' has empty classical_citation"
            )

    def test_no_empty_name(self):
        """name display field must be a non-empty string."""
        for dosha_name, dosha_dict in DOSHA_DEFINITIONS.items():
            assert isinstance(dosha_dict["name"], str), (
                f"Dosha '{dosha_name}' name is not a string"
            )
            assert len(dosha_dict["name"].strip()) > 0, (
                f"Dosha '{dosha_name}' has empty display name"
            )

    def test_no_empty_remedy_approach(self):
        """remedy_approach must be a non-empty string."""
        for dosha_name, dosha_dict in DOSHA_DEFINITIONS.items():
            assert isinstance(dosha_dict["remedy_approach"], str), (
                f"Dosha '{dosha_name}' remedy_approach is not a string"
            )
            assert len(dosha_dict["remedy_approach"].strip()) > 0, (
                f"Dosha '{dosha_name}' has empty remedy_approach"
            )


# ---------------------------------------------------------------------------
# TestMangalDosha — 6 house variants
# ---------------------------------------------------------------------------

class TestMangalDosha:
    def test_all_6_mangal_dosha_house_variants_present(self):
        """All six classical Mangal Dosha house positions must be present."""
        for key in MANGAL_DOSHA_HOUSE_KEYS:
            assert key in DOSHA_DEFINITIONS, (
                f"'{key}' missing from DOSHA_DEFINITIONS"
            )

    def test_mangal_dosha_1h_category(self):
        assert DOSHA_DEFINITIONS["mangal_dosha_1h"]["category"] == "mangal"

    def test_mangal_dosha_2h_category(self):
        assert DOSHA_DEFINITIONS["mangal_dosha_2h"]["category"] == "mangal"

    def test_mangal_dosha_4h_category(self):
        assert DOSHA_DEFINITIONS["mangal_dosha_4h"]["category"] == "mangal"

    def test_mangal_dosha_7h_category(self):
        assert DOSHA_DEFINITIONS["mangal_dosha_7h"]["category"] == "mangal"

    def test_mangal_dosha_8h_category(self):
        assert DOSHA_DEFINITIONS["mangal_dosha_8h"]["category"] == "mangal"

    def test_mangal_dosha_12h_category(self):
        assert DOSHA_DEFINITIONS["mangal_dosha_12h"]["category"] == "mangal"

    def test_list_by_category_mangal_returns_at_least_6(self):
        result = list_doshas_by_category("mangal")
        assert len(result) >= 6, (
            f"Expected 6+ mangal doshas, got {len(result)}"
        )

    def test_mangal_dosha_7h_is_severe_or_very_severe(self):
        """7th house Mars is the most intense Mangal Dosha position."""
        severity = DOSHA_DEFINITIONS["mangal_dosha_7h"]["severity"]
        assert severity in {"severe", "very_severe"}, (
            f"mangal_dosha_7h severity should be severe or very_severe, got {severity!r}"
        )

    def test_mangal_dosha_7h_has_cancellation_rules(self):
        rules = DOSHA_DEFINITIONS["mangal_dosha_7h"]["cancellation_rules"]
        assert len(rules) >= 3, (
            f"mangal_dosha_7h should have at least 3 cancellation rules, got {len(rules)}"
        )

    def test_all_mangal_doshas_have_marriage_in_domains(self):
        """All Mangal Dosha entries must affect 'marriage'."""
        for key in MANGAL_DOSHA_HOUSE_KEYS:
            domains = DOSHA_DEFINITIONS[key]["affected_domains"]
            assert "marriage" in domains, (
                f"'{key}' affected_domains should include 'marriage'"
            )


# ---------------------------------------------------------------------------
# TestSpecificDoshas — spot checks on required doshas
# ---------------------------------------------------------------------------

class TestSpecificDoshas:
    def test_kala_sarpa_dosha_present(self):
        assert "kala_sarpa_dosha" in DOSHA_DEFINITIONS

    def test_kala_sarpa_dosha_category(self):
        assert DOSHA_DEFINITIONS["kala_sarpa_dosha"]["category"] == "kala_sarpa"

    def test_kala_sarpa_dosha_is_severe(self):
        assert DOSHA_DEFINITIONS["kala_sarpa_dosha"]["severity"] in {"severe", "very_severe"}

    def test_guru_chandal_dosha_present(self):
        assert "guru_chandal_dosha" in DOSHA_DEFINITIONS

    def test_guru_chandal_dosha_has_jupiter_or_dharma_in_predicate_or_domains(self):
        """guru_chandal_dosha should reference Jupiter or dharma."""
        d = DOSHA_DEFINITIONS["guru_chandal_dosha"]
        predicate_lower = d["constituent_predicate"].lower()
        domains_lower = " ".join(d["affected_domains"]).lower()
        has_reference = (
            "jupiter" in predicate_lower
            or "dharma" in predicate_lower
            or "jupiter" in domains_lower
            or "dharma" in domains_lower
        )
        assert has_reference, (
            "guru_chandal_dosha should reference Jupiter or dharma in predicate or domains"
        )

    def test_grahan_dosha_present(self):
        assert "grahan_dosha" in DOSHA_DEFINITIONS

    def test_grahan_dosha_references_sun_or_moon_in_predicate(self):
        """grahan_dosha should mention Sun or Moon in its predicate."""
        predicate = DOSHA_DEFINITIONS["grahan_dosha"]["constituent_predicate"].lower()
        assert "sun" in predicate or "moon" in predicate, (
            "grahan_dosha constituent_predicate should mention sun or moon"
        )

    def test_pitru_dosha_present(self):
        assert "pitru_dosha" in DOSHA_DEFINITIONS

    def test_pitru_dosha_category(self):
        assert DOSHA_DEFINITIONS["pitru_dosha"]["category"] == "pitru"

    def test_matri_dosha_present(self):
        assert "matri_dosha" in DOSHA_DEFINITIONS

    def test_matri_dosha_category(self):
        assert DOSHA_DEFINITIONS["matri_dosha"]["category"] == "matri"

    def test_shrapit_dosha_is_very_severe(self):
        assert DOSHA_DEFINITIONS["shrapit_dosha"]["severity"] == "very_severe"

    def test_angarak_dosha_is_severe(self):
        assert DOSHA_DEFINITIONS["angarak_dosha"]["severity"] == "severe"

    def test_kemadrum_dosha_present(self):
        assert "kemadrum_dosha" in DOSHA_DEFINITIONS

    def test_vish_dosha_present(self):
        assert "vish_dosha" in DOSHA_DEFINITIONS

    def test_gandanta_dosha_present(self):
        assert "gandanta_dosha" in DOSHA_DEFINITIONS

    def test_gandanta_dosha_is_miscellaneous(self):
        assert DOSHA_DEFINITIONS["gandanta_dosha"]["category"] == "miscellaneous"

    def test_papa_kartari_dosha_present(self):
        assert "papa_kartari_dosha" in DOSHA_DEFINITIONS

    def test_papa_kartari_dosha_is_mild(self):
        assert DOSHA_DEFINITIONS["papa_kartari_dosha"]["severity"] == "mild"


# ---------------------------------------------------------------------------
# TestGetDosha — helper function
# ---------------------------------------------------------------------------

class TestGetDosha:
    def test_get_dosha_returns_dict(self):
        result = get_dosha("mangal_dosha_7h")
        assert isinstance(result, dict)

    def test_get_dosha_case_insensitive_upper(self):
        result_lower = get_dosha("mangal_dosha_7h")
        result_upper = get_dosha("MANGAL_DOSHA_7H")
        assert result_lower == result_upper

    def test_get_dosha_case_insensitive_mixed(self):
        result_lower = get_dosha("guru_chandal_dosha")
        result_mixed = get_dosha("Guru_Chandal_Dosha")
        assert result_lower == result_mixed

    def test_get_dosha_returns_correct_category(self):
        result = get_dosha("mangal_dosha_7h")
        assert result["category"] == "mangal"

    def test_get_dosha_returns_correct_severity(self):
        result = get_dosha("mangal_dosha_7h")
        assert result["severity"] in {"severe", "very_severe"}

    def test_get_dosha_nonexistent_raises_key_error(self):
        with pytest.raises(KeyError):
            get_dosha("nonexistent_dosha")

    def test_get_dosha_empty_string_raises_key_error(self):
        with pytest.raises(KeyError):
            get_dosha("")

    def test_get_dosha_shrapit_returns_dict(self):
        result = get_dosha("shrapit_dosha")
        assert isinstance(result, dict)
        assert result["category"] == "graha_dosha"

    def test_get_dosha_pitru_returns_dict(self):
        result = get_dosha("pitru_dosha")
        assert result["category"] == "pitru"


# ---------------------------------------------------------------------------
# TestListDoshasByCategory — helper function
# ---------------------------------------------------------------------------

class TestListDoshasByCategory:
    def test_mangal_category_returns_at_least_6(self):
        result = list_doshas_by_category("mangal")
        assert len(result) >= 6

    def test_returns_sorted_list(self):
        result = list_doshas_by_category("mangal")
        assert result == sorted(result)

    def test_unknown_category_returns_empty_list(self):
        result = list_doshas_by_category("nonexistent_category")
        assert result == []

    def test_all_returned_names_in_dosha_definitions(self):
        for cat in VALID_CATEGORIES:
            for name in list_doshas_by_category(cat):
                assert name in DOSHA_DEFINITIONS, (
                    f"list_doshas_by_category returned '{name}' not in DOSHA_DEFINITIONS"
                )

    def test_pitru_category_has_at_least_2(self):
        result = list_doshas_by_category("pitru")
        assert len(result) >= 2

    def test_graha_dosha_category_has_at_least_5(self):
        result = list_doshas_by_category("graha_dosha")
        assert len(result) >= 5


# ---------------------------------------------------------------------------
# TestListDoshasBySeverity — helper function
# ---------------------------------------------------------------------------

class TestListDoshasBySeverity:
    def test_very_severe_returns_list(self):
        result = list_doshas_by_severity("very_severe")
        assert isinstance(result, list)

    def test_severe_returns_list(self):
        result = list_doshas_by_severity("severe")
        assert isinstance(result, list)

    def test_moderate_returns_list(self):
        result = list_doshas_by_severity("moderate")
        assert isinstance(result, list)

    def test_mild_returns_list(self):
        result = list_doshas_by_severity("mild")
        assert isinstance(result, list)

    def test_unknown_severity_returns_empty_list(self):
        result = list_doshas_by_severity("nonexistent_severity")
        assert result == []

    def test_very_severe_contains_shrapit(self):
        result = list_doshas_by_severity("very_severe")
        assert "shrapit_dosha" in result

    def test_returns_sorted_list(self):
        result = list_doshas_by_severity("moderate")
        assert result == sorted(result)

    def test_all_returned_names_in_dosha_definitions(self):
        for sev in VALID_SEVERITIES:
            for name in list_doshas_by_severity(sev):
                assert name in DOSHA_DEFINITIONS, (
                    f"list_doshas_by_severity returned '{name}' not in DOSHA_DEFINITIONS"
                )


# ---------------------------------------------------------------------------
# TestGetAllDoshaCategories — helper function
# ---------------------------------------------------------------------------

class TestGetAllDoshaCategories:
    def test_returns_sorted_list(self):
        result = get_all_dosha_categories()
        assert result == sorted(result)

    def test_returns_list_type(self):
        assert isinstance(get_all_dosha_categories(), list)

    def test_no_duplicate_categories(self):
        result = get_all_dosha_categories()
        assert len(result) == len(set(result))

    def test_contains_mangal(self):
        result = get_all_dosha_categories()
        assert "mangal" in result

    def test_contains_pitru(self):
        result = get_all_dosha_categories()
        assert "pitru" in result

    def test_contains_graha_dosha(self):
        result = get_all_dosha_categories()
        assert "graha_dosha" in result


# ---------------------------------------------------------------------------
# TestGetMangalDoshaHouses — helper function
# ---------------------------------------------------------------------------

class TestGetMangalDoshaHouses:
    def test_returns_list(self):
        assert isinstance(get_mangal_dosha_houses(), list)

    def test_returns_exactly_six_houses(self):
        assert len(get_mangal_dosha_houses()) == 6

    def test_contains_all_classical_mangal_houses(self):
        result = get_mangal_dosha_houses()
        for house in [1, 2, 4, 7, 8, 12]:
            assert house in result, (
                f"House {house} should be in Mangal Dosha houses"
            )

    def test_returns_sorted_list(self):
        result = get_mangal_dosha_houses()
        assert result == sorted(result), "get_mangal_dosha_houses() should return a sorted list"

    def test_exact_classical_list(self):
        assert get_mangal_dosha_houses() == [1, 2, 4, 7, 8, 12]
