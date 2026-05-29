"""
test_dasha_rules.py — Tests for G15 Dasha System Reference Library
====================================================================
Covers: DASHA_SYSTEMS dict structure, all 32 entries, helper functions,
        acharya-selected validation, and class groupings.

Minimum 45 assertions required per acceptance criteria.

canonical_id: G15
stream: A
session: G15-S1 [BUILD-ORCH-A-25]
"""

import re
import pytest

from pipeline.dasha_systems import (
    DASHA_SYSTEMS,
    get_dasha_system,
    list_systems_by_class,
    get_acharya_selected_systems,
    get_total_years,
    get_period_sequence,
)

# ---------------------------------------------------------------------------
# DASHA_SYSTEMS — size and structure
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {
    "name",
    "system_class",
    "total_years",
    "starting_point",
    "period_sequence",
    "period_lengths",
    "sub_period_divisor",
    "applicability_condition",
    "activation_condition",
    "classical_source",
    "acharya_selected",
}

VALID_CLASSES = {"nakshatra_based", "jaimini", "tajik", "special"}

SNAKE_CASE_RE = re.compile(r'^[a-z][a-z0-9_]*$')


class TestDashaSystemsDict:
    """DASHA_SYSTEMS top-level structure tests."""

    def test_has_at_least_32_entries(self):
        assert len(DASHA_SYSTEMS) >= 32, \
            f"Expected >=32 systems, found {len(DASHA_SYSTEMS)}"

    def test_all_entries_have_required_fields(self):
        for name, entry in DASHA_SYSTEMS.items():
            missing = REQUIRED_FIELDS - set(entry.keys())
            assert not missing, \
                f"System '{name}' is missing required fields: {missing}"

    def test_all_system_classes_are_valid(self):
        for name, entry in DASHA_SYSTEMS.items():
            assert entry["system_class"] in VALID_CLASSES, \
                f"System '{name}' has invalid system_class: {entry['system_class']}"

    def test_all_total_years_are_positive_numbers(self):
        for name, entry in DASHA_SYSTEMS.items():
            assert isinstance(entry["total_years"], (int, float)), \
                f"System '{name}' total_years is not a number: {entry['total_years']}"
            assert entry["total_years"] > 0, \
                f"System '{name}' total_years must be > 0"

    def test_all_period_sequences_are_lists(self):
        for name, entry in DASHA_SYSTEMS.items():
            assert isinstance(entry["period_sequence"], list), \
                f"System '{name}' period_sequence must be a list"

    def test_all_period_lengths_are_dicts(self):
        for name, entry in DASHA_SYSTEMS.items():
            assert isinstance(entry["period_lengths"], dict), \
                f"System '{name}' period_lengths must be a dict"

    def test_all_acharya_selected_are_bool(self):
        for name, entry in DASHA_SYSTEMS.items():
            assert isinstance(entry["acharya_selected"], bool), \
                f"System '{name}' acharya_selected must be bool"

    def test_all_names_are_snake_case(self):
        for name in DASHA_SYSTEMS:
            assert SNAKE_CASE_RE.match(name), \
                f"System name '{name}' is not valid snake_case"

    def test_all_classical_sources_are_non_empty_strings(self):
        for name, entry in DASHA_SYSTEMS.items():
            assert isinstance(entry["classical_source"], str) and entry["classical_source"].strip(), \
                f"System '{name}' must have a non-empty classical_source string"


# ---------------------------------------------------------------------------
# SPECIFIC SYSTEM VALIDATIONS
# ---------------------------------------------------------------------------

class TestVimshottari:
    """Vimshottari is the canonical reference system."""

    def test_vimshottari_exists(self):
        assert "vimshottari" in DASHA_SYSTEMS

    def test_vimshottari_total_years(self):
        assert DASHA_SYSTEMS["vimshottari"]["total_years"] == 120

    def test_vimshottari_period_lengths_sum_to_120(self):
        pl = DASHA_SYSTEMS["vimshottari"]["period_lengths"]
        assert sum(pl.values()) == 120

    def test_vimshottari_period_lengths_has_9_grahas(self):
        pl = DASHA_SYSTEMS["vimshottari"]["period_lengths"]
        assert len(pl) == 9

    def test_vimshottari_ketu_period(self):
        assert DASHA_SYSTEMS["vimshottari"]["period_lengths"]["ketu"] == 7

    def test_vimshottari_venus_period(self):
        assert DASHA_SYSTEMS["vimshottari"]["period_lengths"]["venus"] == 20

    def test_vimshottari_saturn_period(self):
        assert DASHA_SYSTEMS["vimshottari"]["period_lengths"]["saturn"] == 19

    def test_vimshottari_is_nakshatra_based(self):
        assert DASHA_SYSTEMS["vimshottari"]["system_class"] == "nakshatra_based"

    def test_vimshottari_is_acharya_selected(self):
        assert DASHA_SYSTEMS["vimshottari"]["acharya_selected"] is True

    def test_vimshottari_period_sequence_starts_with_ketu(self):
        seq = DASHA_SYSTEMS["vimshottari"]["period_sequence"]
        assert seq[0] == "ketu"

    def test_vimshottari_period_sequence_has_venus(self):
        seq = DASHA_SYSTEMS["vimshottari"]["period_sequence"]
        assert "venus" in seq

    def test_vimshottari_period_sequence_has_sun(self):
        seq = DASHA_SYSTEMS["vimshottari"]["period_sequence"]
        assert "sun" in seq

    def test_vimshottari_period_sequence_has_mercury(self):
        seq = DASHA_SYSTEMS["vimshottari"]["period_sequence"]
        assert "mercury" in seq


class TestYogini:
    def test_yogini_exists(self):
        assert "yogini" in DASHA_SYSTEMS

    def test_yogini_total_years(self):
        assert DASHA_SYSTEMS["yogini"]["total_years"] == 36

    def test_yogini_period_lengths_sum_to_36(self):
        pl = DASHA_SYSTEMS["yogini"]["period_lengths"]
        assert sum(pl.values()) == 36

    def test_yogini_is_nakshatra_based(self):
        assert DASHA_SYSTEMS["yogini"]["system_class"] == "nakshatra_based"

    def test_yogini_is_acharya_selected(self):
        assert DASHA_SYSTEMS["yogini"]["acharya_selected"] is True

    def test_yogini_has_8_periods(self):
        assert len(DASHA_SYSTEMS["yogini"]["period_sequence"]) == 8


class TestAshtottari:
    def test_ashtottari_exists(self):
        assert "ashtottari" in DASHA_SYSTEMS

    def test_ashtottari_total_years(self):
        assert DASHA_SYSTEMS["ashtottari"]["total_years"] == 108

    def test_ashtottari_period_lengths_sum_to_108(self):
        pl = DASHA_SYSTEMS["ashtottari"]["period_lengths"]
        assert sum(pl.values()) == 108

    def test_ashtottari_is_nakshatra_based(self):
        assert DASHA_SYSTEMS["ashtottari"]["system_class"] == "nakshatra_based"

    def test_ashtottari_is_acharya_selected(self):
        assert DASHA_SYSTEMS["ashtottari"]["acharya_selected"] is True


class TestJaiminiChara:
    def test_jaimini_chara_exists(self):
        assert "jaimini_chara" in DASHA_SYSTEMS

    def test_jaimini_chara_is_jaimini_class(self):
        assert DASHA_SYSTEMS["jaimini_chara"]["system_class"] == "jaimini"

    def test_jaimini_chara_is_acharya_selected(self):
        assert DASHA_SYSTEMS["jaimini_chara"]["acharya_selected"] is True

    def test_jaimini_chara_has_12_signs_in_sequence(self):
        seq = DASHA_SYSTEMS["jaimini_chara"]["period_sequence"]
        assert len(seq) == 12


class TestNaisargika:
    def test_naisargika_exists(self):
        assert "naisargika" in DASHA_SYSTEMS

    def test_naisargika_is_acharya_selected(self):
        assert DASHA_SYSTEMS["naisargika"]["acharya_selected"] is True

    def test_naisargika_total_years(self):
        assert DASHA_SYSTEMS["naisargika"]["total_years"] == 120

    def test_naisargika_period_lengths_sum_to_120(self):
        pl = DASHA_SYSTEMS["naisargika"]["period_lengths"]
        assert sum(pl.values()) == 120


class TestMudda:
    def test_mudda_exists(self):
        assert "mudda" in DASHA_SYSTEMS

    def test_mudda_is_acharya_selected(self):
        assert DASHA_SYSTEMS["mudda"]["acharya_selected"] is True

    def test_mudda_total_years(self):
        assert DASHA_SYSTEMS["mudda"]["total_years"] == 1

    def test_mudda_is_tajik_class(self):
        assert DASHA_SYSTEMS["mudda"]["system_class"] == "tajik"


class TestKalachakra:
    def test_kalachakra_exists(self):
        assert "kalachakra" in DASHA_SYSTEMS

    def test_kalachakra_is_acharya_selected(self):
        assert DASHA_SYSTEMS["kalachakra"]["acharya_selected"] is True

    def test_kalachakra_total_years(self):
        assert DASHA_SYSTEMS["kalachakra"]["total_years"] == 100

    def test_kalachakra_is_special_class(self):
        assert DASHA_SYSTEMS["kalachakra"]["system_class"] == "special"


# ---------------------------------------------------------------------------
# HELPER FUNCTION TESTS
# ---------------------------------------------------------------------------

class TestGetAcharyaSelectedSystems:
    def test_returns_list_of_7(self):
        result = get_acharya_selected_systems()
        assert len(result) == 7, \
            f"Expected 7 acharya-selected systems, got {len(result)}: {result}"

    def test_vimshottari_in_acharya_selected(self):
        assert "vimshottari" in get_acharya_selected_systems()

    def test_kalachakra_in_acharya_selected(self):
        assert "kalachakra" in get_acharya_selected_systems()

    def test_mudda_in_acharya_selected(self):
        assert "mudda" in get_acharya_selected_systems()

    def test_naisargika_in_acharya_selected(self):
        assert "naisargika" in get_acharya_selected_systems()

    def test_jaimini_chara_in_acharya_selected(self):
        assert "jaimini_chara" in get_acharya_selected_systems()

    def test_yogini_in_acharya_selected(self):
        assert "yogini" in get_acharya_selected_systems()

    def test_ashtottari_in_acharya_selected(self):
        assert "ashtottari" in get_acharya_selected_systems()

    def test_returns_sorted_list(self):
        result = get_acharya_selected_systems()
        assert result == sorted(result)


class TestListSystemsByClass:
    def test_nakshatra_based_has_at_least_12(self):
        result = list_systems_by_class("nakshatra_based")
        assert len(result) >= 12, \
            f"Expected >=12 nakshatra_based systems, got {len(result)}: {result}"

    def test_jaimini_has_at_least_12(self):
        result = list_systems_by_class("jaimini")
        assert len(result) >= 12, \
            f"Expected >=12 jaimini systems, got {len(result)}: {result}"

    def test_tajik_has_at_least_4(self):
        result = list_systems_by_class("tajik")
        assert len(result) >= 4, \
            f"Expected >=4 tajik systems, got {len(result)}: {result}"

    def test_special_has_at_least_4(self):
        result = list_systems_by_class("special")
        assert len(result) >= 4, \
            f"Expected >=4 special systems, got {len(result)}: {result}"

    def test_vimshottari_in_nakshatra_based(self):
        assert "vimshottari" in list_systems_by_class("nakshatra_based")

    def test_jaimini_chara_in_jaimini(self):
        assert "jaimini_chara" in list_systems_by_class("jaimini")

    def test_mudda_in_tajik(self):
        assert "mudda" in list_systems_by_class("tajik")

    def test_kalachakra_in_special(self):
        assert "kalachakra" in list_systems_by_class("special")

    def test_unknown_class_returns_empty_list(self):
        result = list_systems_by_class("nonexistent_class")
        assert result == []

    def test_returns_sorted_list(self):
        result = list_systems_by_class("nakshatra_based")
        assert result == sorted(result)


class TestGetTotalYears:
    def test_vimshottari_returns_120(self):
        assert get_total_years("vimshottari") == 120.0

    def test_returns_float(self):
        result = get_total_years("vimshottari")
        assert isinstance(result, float)

    def test_yogini_returns_36(self):
        assert get_total_years("yogini") == 36.0

    def test_ashtottari_returns_108(self):
        assert get_total_years("ashtottari") == 108.0

    def test_mudda_returns_1(self):
        assert get_total_years("mudda") == 1.0

    def test_kalachakra_returns_100(self):
        assert get_total_years("kalachakra") == 100.0


class TestGetDashaSystem:
    def test_returns_correct_entry(self):
        result = get_dasha_system("vimshottari")
        assert result["total_years"] == 120

    def test_case_insensitive_upper(self):
        result = get_dasha_system("VIMSHOTTARI")
        assert result["total_years"] == 120

    def test_case_insensitive_mixed(self):
        result = get_dasha_system("Vimshottari")
        assert result["total_years"] == 120

    def test_case_insensitive_jaimini_chara(self):
        result = get_dasha_system("JAIMINI_CHARA")
        assert result["system_class"] == "jaimini"

    def test_nonexistent_raises_key_error(self):
        with pytest.raises(KeyError):
            get_dasha_system("nonexistent")

    def test_empty_string_raises_key_error(self):
        with pytest.raises(KeyError):
            get_dasha_system("")


class TestGetPeriodSequence:
    def test_vimshottari_contains_ketu(self):
        seq = get_period_sequence("vimshottari")
        assert "ketu" in seq

    def test_vimshottari_contains_venus(self):
        seq = get_period_sequence("vimshottari")
        assert "venus" in seq

    def test_vimshottari_contains_sun(self):
        seq = get_period_sequence("vimshottari")
        assert "sun" in seq

    def test_vimshottari_contains_moon(self):
        seq = get_period_sequence("vimshottari")
        assert "moon" in seq

    def test_vimshottari_contains_mars(self):
        seq = get_period_sequence("vimshottari")
        assert "mars" in seq

    def test_vimshottari_contains_rahu(self):
        seq = get_period_sequence("vimshottari")
        assert "rahu" in seq

    def test_vimshottari_contains_jupiter(self):
        seq = get_period_sequence("vimshottari")
        assert "jupiter" in seq

    def test_vimshottari_contains_saturn(self):
        seq = get_period_sequence("vimshottari")
        assert "saturn" in seq

    def test_vimshottari_contains_mercury(self):
        seq = get_period_sequence("vimshottari")
        assert "mercury" in seq

    def test_vimshottari_sequence_length(self):
        seq = get_period_sequence("vimshottari")
        assert len(seq) == 9

    def test_yogini_sequence_length(self):
        seq = get_period_sequence("yogini")
        assert len(seq) == 8

    def test_case_insensitive(self):
        seq = get_period_sequence("VIMSHOTTARI")
        assert "ketu" in seq

    def test_nonexistent_raises_key_error(self):
        with pytest.raises(KeyError):
            get_period_sequence("nonexistent_system")


# ---------------------------------------------------------------------------
# CROSS-CUTTING: all system names are snake_case
# ---------------------------------------------------------------------------

class TestSnakeCaseNames:
    def test_all_names_match_snake_case_pattern(self):
        for name in DASHA_SYSTEMS:
            assert SNAKE_CASE_RE.match(name), \
                f"'{name}' is not valid snake_case (must match [a-z][a-z0-9_]*)"

    def test_no_uppercase_in_any_name(self):
        for name in DASHA_SYSTEMS:
            assert name == name.lower(), \
                f"Name '{name}' contains uppercase characters"

    def test_no_spaces_in_any_name(self):
        for name in DASHA_SYSTEMS:
            assert " " not in name, \
                f"Name '{name}' contains a space"
