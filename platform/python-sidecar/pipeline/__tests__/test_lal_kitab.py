"""
Tests for G41 — Lal Kitab corpus: planetary house rules, remedies, and debt karmas.
Minimum 25 assertions required per BUILD-ORCH-A-17 acceptance criteria.
"""

import pytest
from pipeline.lal_kitab import (
    LAL_KITAB_RULES,
    LAL_KITAB_REMEDIES,
    LAL_KITAB_DEBT_KARMAS,
    get_lk_rules_for_planet,
    get_lk_rules_for_house,
    get_lk_remedy,
    list_debt_karmas,
)

NINE_GRAHAS = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']


# ---------------------------------------------------------------------------
# 1. LAL_KITAB_RULES structure tests
# ---------------------------------------------------------------------------

class TestLKRulesStructure:

    def test_rules_dict_is_populated(self):
        """LAL_KITAB_RULES must have at least 40 entries (9 grahas × ~4-6 houses each)."""
        assert len(LAL_KITAB_RULES) >= 40

    def test_rules_keys_are_tuples(self):
        """All keys in LAL_KITAB_RULES must be (planet, house) tuples."""
        for key in LAL_KITAB_RULES:
            assert isinstance(key, tuple), f"Key {key!r} is not a tuple"
            assert len(key) == 2, f"Key {key!r} does not have 2 elements"

    def test_rules_planet_is_string(self):
        """Planet component of each key must be a lowercase string."""
        for (planet, house) in LAL_KITAB_RULES:
            assert isinstance(planet, str)
            assert planet == planet.lower()

    def test_rules_house_is_valid_int(self):
        """House component of each key must be an integer between 1 and 12."""
        for (planet, house) in LAL_KITAB_RULES:
            assert isinstance(house, int)
            assert 1 <= house <= 12, f"House {house} out of range for planet {planet}"

    def test_all_nine_grahas_have_entries(self):
        """Every one of the 9 grahas must appear in LAL_KITAB_RULES."""
        planets_in_rules = {p for (p, _) in LAL_KITAB_RULES}
        for graha in NINE_GRAHAS:
            assert graha in planets_in_rules, f"{graha} has no entries in LAL_KITAB_RULES"

    def test_every_rule_has_effect_key(self):
        """Every rule entry must contain an 'effect' key."""
        for key, rule in LAL_KITAB_RULES.items():
            assert 'effect' in rule, f"Rule {key} missing 'effect'"

    def test_every_rule_has_remedy_key(self):
        """Every rule entry must contain a 'remedy' key."""
        for key, rule in LAL_KITAB_RULES.items():
            assert 'remedy' in rule, f"Rule {key} missing 'remedy'"

    def test_every_rule_has_condition_key(self):
        """Every rule entry must contain a 'condition' key."""
        for key, rule in LAL_KITAB_RULES.items():
            assert 'condition' in rule, f"Rule {key} missing 'condition'"

    def test_every_rule_has_classical_citation_key(self):
        """Every rule entry must contain a 'classical_citation' key."""
        for key, rule in LAL_KITAB_RULES.items():
            assert 'classical_citation' in rule, f"Rule {key} missing 'classical_citation'"

    def test_all_classical_citations_reference_lk(self):
        """All classical_citation values must reference 'LK' (Lal Kitab tradition)."""
        for key, rule in LAL_KITAB_RULES.items():
            citation = rule['classical_citation']
            assert 'LK' in citation, f"Rule {key} citation '{citation}' does not reference LK"

    def test_specific_known_rule_sun_1h(self):
        """Sun in 1H rule must exist and mention government service in effect."""
        rule = LAL_KITAB_RULES.get(('sun', 1))
        assert rule is not None
        assert 'government' in rule['effect'].lower()

    def test_specific_known_rule_sun_7h(self):
        """Sun in 7H rule must exist and mention marriage issues."""
        rule = LAL_KITAB_RULES.get(('sun', 7))
        assert rule is not None
        assert 'marriage' in rule['effect'].lower() or 'spouse' in rule['effect'].lower()

    def test_specific_known_rule_moon_4h(self):
        """Moon in 4H must exist and reference mother or property."""
        rule = LAL_KITAB_RULES.get(('moon', 4))
        assert rule is not None
        assert 'mother' in rule['effect'].lower() or 'property' in rule['effect'].lower()

    def test_specific_known_rule_mars_7h_marital(self):
        """Mars in 7H must reference marital discord (Kuja Dosha effect)."""
        rule = LAL_KITAB_RULES.get(('mars', 7))
        assert rule is not None
        assert 'marital' in rule['effect'].lower() or 'discord' in rule['effect'].lower()

    def test_specific_known_rule_ketu_12h_moksha(self):
        """Ketu in 12H must reference moksha."""
        rule = LAL_KITAB_RULES.get(('ketu', 12))
        assert rule is not None
        assert 'moksha' in rule['effect'].lower() or 'liberation' in rule['effect'].lower()

    def test_specific_known_rule_rahu_5h(self):
        """Rahu in 5H must reference unconventional children or education."""
        rule = LAL_KITAB_RULES.get(('rahu', 5))
        assert rule is not None
        assert 'unconventional' in rule['effect'].lower() or 'children' in rule['effect'].lower()

    def test_specific_known_rule_saturn_8h_longevity(self):
        """Saturn in 8H must reference long life or longevity."""
        rule = LAL_KITAB_RULES.get(('saturn', 8))
        assert rule is not None
        assert 'long life' in rule['effect'].lower() or 'longevity' in rule['effect'].lower()

    def test_specific_known_rule_jupiter_5h_children(self):
        """Jupiter in 5H must reference blessed children or teaching."""
        rule = LAL_KITAB_RULES.get(('jupiter', 5))
        assert rule is not None
        assert 'children' in rule['effect'].lower() or 'teaching' in rule['effect'].lower()

    def test_7h_has_multiple_planet_entries(self):
        """House 7 must have multiple planetary entries (at least 4 planets)."""
        planets_in_7h = [p for (p, h) in LAL_KITAB_RULES if h == 7]
        assert len(planets_in_7h) >= 4, f"Only {len(planets_in_7h)} planets in 7H rules"


# ---------------------------------------------------------------------------
# 2. get_lk_rules_for_planet() tests
# ---------------------------------------------------------------------------

class TestGetLKRulesForPlanet:

    def test_sun_returns_nonempty_list(self):
        result = get_lk_rules_for_planet('sun')
        assert isinstance(result, list)
        assert len(result) > 0

    def test_saturn_returns_nonempty_list(self):
        result = get_lk_rules_for_planet('saturn')
        assert len(result) > 0

    def test_rahu_returns_nonempty_list(self):
        result = get_lk_rules_for_planet('rahu')
        assert len(result) > 0

    def test_ketu_returns_nonempty_list(self):
        result = get_lk_rules_for_planet('ketu')
        assert len(result) > 0

    def test_all_grahas_return_rules(self):
        """All 9 grahas must return at least one rule."""
        for graha in NINE_GRAHAS:
            result = get_lk_rules_for_planet(graha)
            assert len(result) >= 1, f"No rules returned for {graha}"

    def test_result_includes_planet_field(self):
        """Each returned rule dict must include a 'planet' field."""
        for rule in get_lk_rules_for_planet('moon'):
            assert 'planet' in rule
            assert rule['planet'] == 'moon'

    def test_result_includes_house_field(self):
        """Each returned rule dict must include a 'house' field."""
        for rule in get_lk_rules_for_planet('jupiter'):
            assert 'house' in rule
            assert isinstance(rule['house'], int)

    def test_results_sorted_by_house(self):
        """Results for a planet must be sorted by house number ascending."""
        result = get_lk_rules_for_planet('sun')
        houses = [r['house'] for r in result]
        assert houses == sorted(houses)

    def test_case_insensitive_input(self):
        """Function should handle mixed-case planet names."""
        result_lower = get_lk_rules_for_planet('sun')
        result_upper = get_lk_rules_for_planet('SUN')
        assert len(result_lower) == len(result_upper)

    def test_unknown_planet_returns_empty_list(self):
        """Unknown planet name should return empty list, not raise exception."""
        result = get_lk_rules_for_planet('neptune')
        assert result == []


# ---------------------------------------------------------------------------
# 3. get_lk_rules_for_house() tests
# ---------------------------------------------------------------------------

class TestGetLKRulesForHouse:

    def test_house_7_returns_nonempty_list(self):
        result = get_lk_rules_for_house(7)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_house_1_has_multiple_planets(self):
        """House 1 should have multiple planetary rules."""
        result = get_lk_rules_for_house(1)
        assert len(result) >= 3

    def test_house_12_has_entries(self):
        """House 12 should have entries (spiritual/foreign significance in LK)."""
        result = get_lk_rules_for_house(12)
        assert len(result) >= 2

    def test_result_includes_planet_field(self):
        """Each returned rule must have a 'planet' field."""
        for rule in get_lk_rules_for_house(7):
            assert 'planet' in rule

    def test_result_includes_house_field(self):
        """Each returned rule must have the correct 'house' field."""
        for rule in get_lk_rules_for_house(4):
            assert rule['house'] == 4

    def test_house_out_of_range_returns_empty(self):
        """House 0 or 13 should return empty list."""
        assert get_lk_rules_for_house(0) == []
        assert get_lk_rules_for_house(13) == []


# ---------------------------------------------------------------------------
# 4. LAL_KITAB_REMEDIES tests
# ---------------------------------------------------------------------------

class TestLKRemedies:

    def test_remedies_has_nine_grahas(self):
        """LAL_KITAB_REMEDIES must have entries for all 9 grahas."""
        for graha in NINE_GRAHAS:
            assert graha in LAL_KITAB_REMEDIES, f"{graha} missing from LAL_KITAB_REMEDIES"

    def test_saturn_fasting_day_saturday(self):
        assert LAL_KITAB_REMEDIES['saturn']['fasting_day'] == 'Saturday'

    def test_moon_metal_contains_silver(self):
        assert 'Silver' in LAL_KITAB_REMEDIES['moon']['metal']

    def test_sun_fasting_day_sunday(self):
        assert LAL_KITAB_REMEDIES['sun']['fasting_day'] == 'Sunday'

    def test_jupiter_fasting_day_thursday(self):
        assert LAL_KITAB_REMEDIES['jupiter']['fasting_day'] == 'Thursday'

    def test_mars_metal_contains_copper(self):
        assert 'Copper' in LAL_KITAB_REMEDIES['mars']['metal']

    def test_venus_fasting_day_friday(self):
        assert LAL_KITAB_REMEDIES['venus']['fasting_day'] == 'Friday'

    def test_mercury_fasting_day_wednesday(self):
        assert LAL_KITAB_REMEDIES['mercury']['fasting_day'] == 'Wednesday'

    def test_rahu_fasting_day_saturday(self):
        assert LAL_KITAB_REMEDIES['rahu']['fasting_day'] == 'Saturday'

    def test_ketu_fasting_day_tuesday(self):
        assert LAL_KITAB_REMEDIES['ketu']['fasting_day'] == 'Tuesday'

    def test_every_remedy_has_required_keys(self):
        """Every remedy entry must have remedies, fasting_day, metal, donate keys."""
        required_keys = {'remedies', 'fasting_day', 'metal', 'donate'}
        for graha, data in LAL_KITAB_REMEDIES.items():
            missing = required_keys - set(data.keys())
            assert not missing, f"{graha} remedy missing keys: {missing}"

    def test_remedies_field_is_list(self):
        """The 'remedies' field must be a list for each graha."""
        for graha, data in LAL_KITAB_REMEDIES.items():
            assert isinstance(data['remedies'], list), f"{graha} 'remedies' is not a list"

    def test_remedies_list_nonempty(self):
        """The 'remedies' list must have at least 5 entries per graha."""
        for graha, data in LAL_KITAB_REMEDIES.items():
            assert len(data['remedies']) >= 5, f"{graha} has fewer than 5 remedies"

    def test_lk_specific_key_present(self):
        """Each remedy should document the LK-specific signature remedy."""
        for graha, data in LAL_KITAB_REMEDIES.items():
            assert 'lk_specific' in data, f"{graha} missing 'lk_specific' key"

    def test_gemstone_key_present(self):
        """Each remedy must reference a gemstone."""
        for graha, data in LAL_KITAB_REMEDIES.items():
            assert 'gemstone' in data, f"{graha} missing 'gemstone' key"


# ---------------------------------------------------------------------------
# 5. get_lk_remedy() function tests
# ---------------------------------------------------------------------------

class TestGetLKRemedy:

    def test_saturn_returns_correct_data(self):
        result = get_lk_remedy('saturn')
        assert result['fasting_day'] == 'Saturday'
        assert 'Iron' in result['metal'] or 'Steel' in result['metal']

    def test_moon_remedy_fasting_monday(self):
        result = get_lk_remedy('moon')
        assert result['fasting_day'] == 'Monday'

    def test_case_insensitive(self):
        lower = get_lk_remedy('jupiter')
        upper = get_lk_remedy('JUPITER')
        assert lower == upper

    def test_unknown_planet_returns_empty_dict(self):
        result = get_lk_remedy('uranus')
        assert result == {}

    def test_all_grahas_return_data(self):
        for graha in NINE_GRAHAS:
            result = get_lk_remedy(graha)
            assert result, f"get_lk_remedy('{graha}') returned empty"


# ---------------------------------------------------------------------------
# 6. LAL_KITAB_DEBT_KARMAS tests
# ---------------------------------------------------------------------------

class TestLKDebtKarmas:

    def test_debt_karmas_has_at_least_five_entries(self):
        """LAL_KITAB_DEBT_KARMAS must have at least 5 entries."""
        assert len(LAL_KITAB_DEBT_KARMAS) >= 5

    def test_each_entry_has_debt_type(self):
        """Every debt karma entry must have 'debt_type' field."""
        for entry in LAL_KITAB_DEBT_KARMAS:
            assert 'debt_type' in entry, f"Entry missing 'debt_type': {entry}"

    def test_each_entry_has_indicator(self):
        """Every debt karma entry must have 'indicator' field."""
        for entry in LAL_KITAB_DEBT_KARMAS:
            assert 'indicator' in entry, f"Entry missing 'indicator': {entry}"

    def test_each_entry_has_remedy(self):
        """Every debt karma entry must have 'remedy' field."""
        for entry in LAL_KITAB_DEBT_KARMAS:
            assert 'remedy' in entry, f"Entry missing 'remedy': {entry}"

    def test_pitr_rin_present(self):
        """Pitr Rin (Father/Ancestor debt) must be in the list."""
        types = [e['debt_type'] for e in LAL_KITAB_DEBT_KARMAS]
        assert 'Pitr Rin' in types

    def test_matri_rin_present(self):
        """Matri Rin (Mother debt) must be in the list."""
        types = [e['debt_type'] for e in LAL_KITAB_DEBT_KARMAS]
        assert 'Matri Rin' in types

    def test_bhai_rin_present(self):
        """Bhai Rin (Sibling debt) must be in the list."""
        types = [e['debt_type'] for e in LAL_KITAB_DEBT_KARMAS]
        assert 'Bhai Rin' in types

    def test_atma_rin_present(self):
        """Atma Rin (Soul/Self debt) must be in the list."""
        types = [e['debt_type'] for e in LAL_KITAB_DEBT_KARMAS]
        assert 'Atma Rin' in types

    def test_each_entry_has_classical_citation(self):
        """Every debt karma entry must have 'classical_citation' field."""
        for entry in LAL_KITAB_DEBT_KARMAS:
            assert 'classical_citation' in entry

    def test_symptoms_field_is_list(self):
        """The 'symptoms' field must be a list for each entry."""
        for entry in LAL_KITAB_DEBT_KARMAS:
            assert 'symptoms' in entry, f"Entry '{entry['debt_type']}' missing 'symptoms'"
            assert isinstance(entry['symptoms'], list)
            assert len(entry['symptoms']) >= 3


# ---------------------------------------------------------------------------
# 7. list_debt_karmas() function tests
# ---------------------------------------------------------------------------

class TestListDebtKarmas:

    def test_returns_list(self):
        result = list_debt_karmas()
        assert isinstance(result, list)

    def test_returns_at_least_five(self):
        result = list_debt_karmas()
        assert len(result) >= 5

    def test_returns_same_as_constant(self):
        """list_debt_karmas() should return the same data as LAL_KITAB_DEBT_KARMAS."""
        assert list_debt_karmas() is LAL_KITAB_DEBT_KARMAS

    def test_each_entry_has_required_fields(self):
        """Spot-check required fields in returned entries."""
        for entry in list_debt_karmas():
            assert 'debt_type' in entry
            assert 'indicator' in entry
            assert 'remedy' in entry


# ---------------------------------------------------------------------------
# 8. Cross-cutting integrity tests
# ---------------------------------------------------------------------------

class TestCrossIntegrity:

    def test_rule_count_at_least_forty(self):
        """Total LK rules must meet the minimum of 40 entries."""
        assert len(LAL_KITAB_RULES) >= 40

    def test_remedy_count_exactly_nine(self):
        """LAL_KITAB_REMEDIES must have exactly 9 graha entries."""
        assert len(LAL_KITAB_REMEDIES) == 9

    def test_rahu_and_ketu_both_in_rules(self):
        """Both shadow planets must have rules."""
        planets = {p for (p, _) in LAL_KITAB_RULES}
        assert 'rahu' in planets
        assert 'ketu' in planets

    def test_all_effect_fields_nonempty(self):
        """No rule should have an empty 'effect' string."""
        for key, rule in LAL_KITAB_RULES.items():
            assert rule['effect'].strip(), f"Rule {key} has empty 'effect'"

    def test_all_remedy_fields_nonempty(self):
        """No rule should have an empty 'remedy' string."""
        for key, rule in LAL_KITAB_RULES.items():
            assert rule['remedy'].strip(), f"Rule {key} has empty 'remedy'"
