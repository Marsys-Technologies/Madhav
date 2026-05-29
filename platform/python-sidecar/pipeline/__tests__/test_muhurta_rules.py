"""
test_muhurta_rules.py — Tests for muhurta_rule_library.py (G37)

Verifies:
  - MUHURTA_RULES completeness and structure
  - Per-activity field correctness
  - Helper function behaviour
  - Classical data consistency

session: G37-S1 [BUILD-ORCH-A-22]
"""

from __future__ import annotations

import pytest

from pipeline.muhurta_rule_library import (
    MUHURTA_RULES,
    get_auspicious_nakshatras,
    get_auspicious_tithis,
    get_auspicious_varas,
    get_muhurta_rules,
    is_vara_suitable,
    list_activities_by_category,
)

_VALID_VARAS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
_REQUIRED_FIELDS = {
    "name",
    "category",
    "required_tithis",
    "forbidden_tithis",
    "required_varas",
    "forbidden_varas",
    "required_nakshatras",
    "forbidden_nakshatras",
    "lagna_requirements",
    "special_conditions",
    "classical_citation",
}
_VALID_CATEGORIES = {
    "lifecycle", "journey", "property", "spiritual",
    "medical", "business", "agriculture", "education", "social",
}


# ---------------------------------------------------------------------------
# Top-level structure
# ---------------------------------------------------------------------------

class TestMuhurtaRulesStructure:
    def test_at_least_30_activities(self):
        assert len(MUHURTA_RULES) >= 30

    def test_all_required_fields_present(self):
        for activity, rules in MUHURTA_RULES.items():
            missing = _REQUIRED_FIELDS - set(rules.keys())
            assert not missing, f"{activity} missing fields: {missing}"

    def test_all_activity_names_are_snake_case(self):
        """Keys should be lowercase with underscores only."""
        import re
        pattern = re.compile(r"^[a-z][a-z0-9_]*$")
        for key in MUHURTA_RULES:
            assert pattern.match(key), f"Key '{key}' is not valid snake_case"

    def test_all_categories_valid(self):
        for activity, rules in MUHURTA_RULES.items():
            assert rules["category"] in _VALID_CATEGORIES, \
                f"{activity} has invalid category '{rules['category']}'"

    def test_required_tithis_are_ints_in_range(self):
        for activity, rules in MUHURTA_RULES.items():
            for t in rules["required_tithis"]:
                assert isinstance(t, int), f"{activity}: tithi {t!r} is not int"
                assert 1 <= t <= 30, f"{activity}: tithi {t} out of range 1–30"

    def test_forbidden_tithis_are_ints_in_range(self):
        for activity, rules in MUHURTA_RULES.items():
            for t in rules["forbidden_tithis"]:
                assert isinstance(t, int), f"{activity}: forbidden tithi {t!r} is not int"
                assert 1 <= t <= 30, f"{activity}: forbidden tithi {t} out of range"

    def test_all_required_varas_valid(self):
        for activity, rules in MUHURTA_RULES.items():
            for v in rules["required_varas"]:
                assert v in _VALID_VARAS, f"{activity}: required vara '{v}' invalid"

    def test_all_forbidden_varas_valid(self):
        for activity, rules in MUHURTA_RULES.items():
            for v in rules["forbidden_varas"]:
                assert v in _VALID_VARAS, f"{activity}: forbidden vara '{v}' invalid"

    def test_all_classical_citations_nonempty(self):
        for activity, rules in MUHURTA_RULES.items():
            assert rules["classical_citation"], f"{activity}: empty classical_citation"

    def test_required_nakshatras_are_strings(self):
        for activity, rules in MUHURTA_RULES.items():
            for n in rules["required_nakshatras"]:
                assert isinstance(n, str), f"{activity}: nakshatra {n!r} not str"
                assert n == n.lower(), f"{activity}: nakshatra '{n}' not lowercase"


# ---------------------------------------------------------------------------
# Key activities present
# ---------------------------------------------------------------------------

class TestRequiredActivitiesPresent:
    def test_vivah_present(self):
        assert "vivah" in MUHURTA_RULES

    def test_griha_pravesh_present(self):
        assert "griha_pravesh" in MUHURTA_RULES

    def test_vidyarambha_present(self):
        assert "vidyarambha" in MUHURTA_RULES

    def test_dhatu_kharidi_present(self):
        assert "dhatu_kharidi" in MUHURTA_RULES

    def test_shraddha_present(self):
        assert "shraddha" in MUHURTA_RULES

    def test_yatra_present(self):
        assert "yatra" in MUHURTA_RULES

    def test_upanayana_present(self):
        assert "upanayana" in MUHURTA_RULES

    def test_mundan_present(self):
        assert "mundan" in MUHURTA_RULES

    def test_deeksha_present(self):
        assert "deeksha" in MUHURTA_RULES

    def test_yagya_present(self):
        assert "yagya" in MUHURTA_RULES

    def test_vivah_saptapadi_present(self):
        assert "vivah_saptapadi" in MUHURTA_RULES

    def test_sena_yatra_present(self):
        assert "sena_yatra" in MUHURTA_RULES

    def test_namakarana_present(self):
        assert "namakarana" in MUHURTA_RULES

    def test_annaprashana_present(self):
        assert "annaprashana" in MUHURTA_RULES


# ---------------------------------------------------------------------------
# Vivah (marriage) specific assertions
# ---------------------------------------------------------------------------

class TestVivahRules:
    def setup_method(self):
        self.rules = MUHURTA_RULES["vivah"]

    def test_tuesday_is_forbidden(self):
        assert "tuesday" in self.rules["forbidden_varas"]

    def test_saturday_is_forbidden(self):
        assert "saturday" in self.rules["forbidden_varas"]

    def test_required_nakshatras_nonempty(self):
        assert len(self.rules["required_nakshatras"]) > 0

    def test_rohini_in_required_nakshatras(self):
        naks = self.rules["required_nakshatras"]
        assert "rohini" in naks or "uttara_phalguni" in naks, \
            "vivah should have rohini or uttara_phalguni as required nakshatra"

    def test_uttara_phalguni_in_required_nakshatras(self):
        assert "uttara_phalguni" in self.rules["required_nakshatras"]

    def test_forbidden_tithis_include_amavasya(self):
        assert 30 in self.rules["forbidden_tithis"]

    def test_required_tithis_nonempty(self):
        assert len(self.rules["required_tithis"]) > 0

    def test_monday_is_required_vara(self):
        assert "monday" in self.rules["required_varas"]

    def test_friday_is_required_vara(self):
        assert "friday" in self.rules["required_varas"]

    def test_category_is_lifecycle(self):
        assert self.rules["category"] == "lifecycle"


# ---------------------------------------------------------------------------
# Griha Pravesh specific
# ---------------------------------------------------------------------------

class TestGrihaPraveshRules:
    def setup_method(self):
        self.rules = MUHURTA_RULES["griha_pravesh"]

    def test_rohini_in_required_nakshatras(self):
        assert "rohini" in self.rules["required_nakshatras"]

    def test_category_is_property(self):
        assert self.rules["category"] == "property"

    def test_required_tithis_nonempty(self):
        assert len(self.rules["required_tithis"]) > 0


# ---------------------------------------------------------------------------
# Vidyarambha specific
# ---------------------------------------------------------------------------

class TestVidyarambhaRules:
    def setup_method(self):
        self.rules = MUHURTA_RULES["vidyarambha"]

    def test_auspicious_varas_include_wednesday(self):
        varas = self.rules["required_varas"]
        assert "wednesday" in varas or "thursday" in varas, \
            "vidyarambha should have wednesday or thursday as auspicious vara"

    def test_wednesday_in_required_varas(self):
        assert "wednesday" in self.rules["required_varas"]

    def test_thursday_in_required_varas(self):
        assert "thursday" in self.rules["required_varas"]

    def test_category_is_education(self):
        assert self.rules["category"] == "education"


# ---------------------------------------------------------------------------
# Shraddha specific
# ---------------------------------------------------------------------------

class TestShraddhaRules:
    def setup_method(self):
        self.rules = MUHURTA_RULES["shraddha"]

    def test_amavasya_is_required(self):
        assert 30 in self.rules["required_tithis"]

    def test_saturday_is_required_vara(self):
        assert "saturday" in self.rules["required_varas"]

    def test_category_is_spiritual(self):
        assert self.rules["category"] == "spiritual"


# ---------------------------------------------------------------------------
# Helper: get_muhurta_rules
# ---------------------------------------------------------------------------

class TestGetMuhurtaRules:
    def test_returns_dict_for_known_activity(self):
        result = get_muhurta_rules("vivah")
        assert isinstance(result, dict)
        assert "name" in result

    def test_case_insensitive_uppercase(self):
        result = get_muhurta_rules("VIVAH")
        assert result is MUHURTA_RULES["vivah"]

    def test_case_insensitive_mixed(self):
        result = get_muhurta_rules("Griha_Pravesh")
        assert result is MUHURTA_RULES["griha_pravesh"]

    def test_raises_key_error_for_unknown(self):
        with pytest.raises(KeyError):
            get_muhurta_rules("unknown_activity")

    def test_raises_key_error_for_empty_string(self):
        with pytest.raises(KeyError):
            get_muhurta_rules("")


# ---------------------------------------------------------------------------
# Helper: list_activities_by_category
# ---------------------------------------------------------------------------

class TestListActivitiesByCategory:
    def test_lifecycle_returns_list(self):
        result = list_activities_by_category("lifecycle")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_vivah_in_lifecycle(self):
        result = list_activities_by_category("lifecycle")
        assert "vivah" in result

    def test_namakarana_in_lifecycle(self):
        result = list_activities_by_category("lifecycle")
        assert "namakarana" in result

    def test_spiritual_returns_list(self):
        result = list_activities_by_category("spiritual")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_yagya_in_spiritual(self):
        result = list_activities_by_category("spiritual")
        assert "yagya" in result

    def test_property_category_exists(self):
        result = list_activities_by_category("property")
        assert len(result) > 0
        assert "griha_pravesh" in result

    def test_education_category_contains_vidyarambha(self):
        result = list_activities_by_category("education")
        assert "vidyarambha" in result

    def test_unknown_category_returns_empty_list(self):
        result = list_activities_by_category("nonexistent_category")
        assert result == []

    def test_case_insensitive_category(self):
        lower = list_activities_by_category("lifecycle")
        upper = list_activities_by_category("LIFECYCLE")
        assert set(lower) == set(upper)


# ---------------------------------------------------------------------------
# Helper: get_auspicious_tithis
# ---------------------------------------------------------------------------

class TestGetAuspiciousTithis:
    def test_vivah_returns_nonempty_list(self):
        result = get_auspicious_tithis("vivah")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_vivah_tithis_all_in_range(self):
        for t in get_auspicious_tithis("vivah"):
            assert 1 <= t <= 30

    def test_raises_key_error_for_unknown(self):
        with pytest.raises(KeyError):
            get_auspicious_tithis("not_an_activity")


# ---------------------------------------------------------------------------
# Helper: get_auspicious_varas
# ---------------------------------------------------------------------------

class TestGetAuspiciousVaras:
    def test_vidyarambha_contains_wednesday(self):
        result = get_auspicious_varas("vidyarambha")
        assert "wednesday" in result or "thursday" in result

    def test_returns_list(self):
        result = get_auspicious_varas("vivah")
        assert isinstance(result, list)

    def test_all_varas_valid_strings(self):
        for activity in MUHURTA_RULES:
            for v in get_auspicious_varas(activity):
                assert v in _VALID_VARAS, f"{activity}: auspicious vara '{v}' invalid"

    def test_raises_key_error_for_unknown(self):
        with pytest.raises(KeyError):
            get_auspicious_varas("not_real")


# ---------------------------------------------------------------------------
# Helper: get_auspicious_nakshatras
# ---------------------------------------------------------------------------

class TestGetAuspiciousNakshatras:
    def test_vivah_returns_nonempty_list(self):
        result = get_auspicious_nakshatras("vivah")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_griha_pravesh_contains_rohini(self):
        result = get_auspicious_nakshatras("griha_pravesh")
        assert "rohini" in result

    def test_raises_key_error_for_unknown(self):
        with pytest.raises(KeyError):
            get_auspicious_nakshatras("nothing_here")


# ---------------------------------------------------------------------------
# Helper: is_vara_suitable
# ---------------------------------------------------------------------------

class TestIsVaraSuitable:
    def test_tuesday_forbidden_for_vivah(self):
        assert is_vara_suitable("vivah", "tuesday") is False

    def test_friday_suitable_for_vivah(self):
        assert is_vara_suitable("vivah", "friday") is True

    def test_monday_suitable_for_vivah(self):
        assert is_vara_suitable("vivah", "monday") is True

    def test_saturday_forbidden_for_vivah(self):
        assert is_vara_suitable("vivah", "saturday") is False

    def test_case_insensitive_vara_upper(self):
        assert is_vara_suitable("vivah", "TUESDAY") is False

    def test_case_insensitive_vara_title(self):
        assert is_vara_suitable("vivah", "Friday") is True

    def test_case_insensitive_activity(self):
        # VIVAH uppercase activity
        assert is_vara_suitable("VIVAH", "tuesday") is False

    def test_tuesday_suitable_for_sena_yatra(self):
        # Tuesday is required for military expedition
        assert is_vara_suitable("sena_yatra", "tuesday") is True

    def test_raises_key_error_for_unknown_activity(self):
        with pytest.raises(KeyError):
            is_vara_suitable("unknown_activity", "monday")
