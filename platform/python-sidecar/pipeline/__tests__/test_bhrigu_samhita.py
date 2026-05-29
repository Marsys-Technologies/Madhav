"""
test_bhrigu_samhita.py — Tests for bhrigu_samhita.py

Covers:
  - BHRIGU_BASE_RULES minimum count (≥ 24)
  - BHRIGU_GRAHA_RULES minimum count (≥ 24)
  - BHRIGU_SEQUENCE_RULES minimum count (≥ 10)
  - Required field presence on every rule
  - Public API correctness
  - Known semantic content assertions

G43 [BUILD-ORCH-A-18]
"""

import pytest

from pipeline.bhrigu_samhita import (
    BHRIGU_BASE_RULES,
    BHRIGU_GRAHA_RULES,
    BHRIGU_SEQUENCE_RULES,
    get_bhrigu_prediction,
    get_bhrigu_graha_rule,
    list_sequence_rules,
)


# ---------------------------------------------------------------------------
# 1. BHRIGU_BASE_RULES structural tests
# ---------------------------------------------------------------------------

def test_base_rules_minimum_count():
    """BHRIGU_BASE_RULES must have at least 24 entries."""
    assert len(BHRIGU_BASE_RULES) >= 24


def test_base_rules_keys_are_tuples():
    """All BHRIGU_BASE_RULES keys must be (int, str) tuples."""
    for key in BHRIGU_BASE_RULES:
        assert isinstance(key, tuple) and len(key) == 2
        assert isinstance(key[0], int)
        assert isinstance(key[1], str)


def test_base_rules_required_fields():
    """Every BHRIGU_BASE_RULES entry must have prediction, domain, confidence, citation."""
    required = {"prediction", "domain", "confidence", "citation"}
    for key, value in BHRIGU_BASE_RULES.items():
        missing = required - set(value.keys())
        assert not missing, f"Missing fields {missing} for key {key}"


def test_base_rules_no_empty_strings():
    """No BHRIGU_BASE_RULES field value may be an empty string."""
    for key, value in BHRIGU_BASE_RULES.items():
        for field, content in value.items():
            assert content.strip(), f"Empty field '{field}' for key {key}"


def test_base_rules_confidence_values():
    """confidence field must be one of: high, medium, low."""
    valid = {"high", "medium", "low"}
    for key, value in BHRIGU_BASE_RULES.items():
        assert value["confidence"] in valid, \
            f"Invalid confidence '{value['confidence']}' for key {key}"


# ---------------------------------------------------------------------------
# 2. BHRIGU_GRAHA_RULES structural tests
# ---------------------------------------------------------------------------

def test_graha_rules_minimum_count():
    """BHRIGU_GRAHA_RULES must have at least 24 entries."""
    assert len(BHRIGU_GRAHA_RULES) >= 24


def test_graha_rules_keys_are_tuples():
    """All BHRIGU_GRAHA_RULES keys must be (str, int) tuples."""
    for key in BHRIGU_GRAHA_RULES:
        assert isinstance(key, tuple) and len(key) == 2
        assert isinstance(key[0], str)
        assert isinstance(key[1], int)


def test_graha_rules_required_fields():
    """Every BHRIGU_GRAHA_RULES entry must have effect, time_of_manifestation, citation."""
    required = {"effect", "time_of_manifestation", "citation"}
    for key, value in BHRIGU_GRAHA_RULES.items():
        missing = required - set(value.keys())
        assert not missing, f"Missing fields {missing} for key {key}"


def test_graha_rules_no_empty_effect():
    """No graha rule may have an empty effect field."""
    for key, value in BHRIGU_GRAHA_RULES.items():
        assert value["effect"].strip(), f"Empty effect for key {key}"


def test_graha_rules_no_empty_citation():
    """No graha rule may have an empty citation field."""
    for key, value in BHRIGU_GRAHA_RULES.items():
        assert value["citation"].strip(), f"Empty citation for key {key}"


def test_graha_rules_house_range():
    """All house numbers in BHRIGU_GRAHA_RULES must be between 1 and 12."""
    for planet, house in BHRIGU_GRAHA_RULES:
        assert 1 <= house <= 12, f"House {house} out of range for planet {planet}"


# ---------------------------------------------------------------------------
# 3. BHRIGU_SEQUENCE_RULES structural tests
# ---------------------------------------------------------------------------

def test_sequence_rules_minimum_count():
    """BHRIGU_SEQUENCE_RULES must have at least 10 entries."""
    assert len(BHRIGU_SEQUENCE_RULES) >= 10


def test_sequence_rules_required_fields():
    """Every sequence rule must have sequence, meaning, timing, citation."""
    required = {"sequence", "meaning", "timing", "citation"}
    for i, rule in enumerate(BHRIGU_SEQUENCE_RULES):
        missing = required - set(rule.keys())
        assert not missing, f"Missing fields {missing} at index {i}"


def test_sequence_rules_sequence_format():
    """Sequence field must use 'A→B' format."""
    for rule in BHRIGU_SEQUENCE_RULES:
        assert "→" in rule["sequence"], \
            f"Sequence '{rule['sequence']}' missing → separator"


def test_sequence_rules_no_empty_meaning():
    """No sequence rule may have an empty meaning field."""
    for i, rule in enumerate(BHRIGU_SEQUENCE_RULES):
        assert rule["meaning"].strip(), f"Empty meaning at index {i}"


# ---------------------------------------------------------------------------
# 4. get_bhrigu_prediction API tests
# ---------------------------------------------------------------------------

def test_get_bhrigu_prediction_returns_dict():
    """get_bhrigu_prediction must return a dict."""
    result = get_bhrigu_prediction(1, "aries")
    assert isinstance(result, dict)


def test_get_bhrigu_prediction_non_empty():
    """get_bhrigu_prediction(1, 'aries') must return a non-empty dict."""
    result = get_bhrigu_prediction(1, "aries")
    assert result


def test_get_bhrigu_prediction_required_keys():
    """Result of get_bhrigu_prediction must contain prediction, domain, confidence, citation."""
    result = get_bhrigu_prediction(1, "aries")
    for key in ("prediction", "domain", "confidence", "citation"):
        assert key in result, f"Key '{key}' missing from result"


def test_get_bhrigu_prediction_case_insensitive():
    """get_bhrigu_prediction should normalise moon_sign to lowercase."""
    result_lower = get_bhrigu_prediction(1, "aries")
    result_upper = get_bhrigu_prediction(1, "ARIES")
    assert result_lower == result_upper


def test_get_bhrigu_prediction_missing_returns_empty():
    """get_bhrigu_prediction for unknown combo must return empty dict."""
    result = get_bhrigu_prediction(99, "atlantis")
    assert result == {}


def test_get_bhrigu_prediction_sun9_sagittarius():
    """Sun in 9H + Sagittarius should mention spiritual/guru content."""
    result = get_bhrigu_prediction(9, "sagittarius")
    assert result
    combined = (result.get("prediction", "") + " " + result.get("domain", "")).lower()
    assert any(term in combined for term in ("spirit", "guru", "philosoph", "education", "dharma"))


def test_get_bhrigu_prediction_sun1_leo():
    """Sun in 1H + Leo should indicate creative authority."""
    result = get_bhrigu_prediction(1, "leo")
    assert result
    assert result["confidence"] == "high"


# ---------------------------------------------------------------------------
# 5. get_bhrigu_graha_rule API tests
# ---------------------------------------------------------------------------

def test_get_bhrigu_graha_rule_returns_dict():
    """get_bhrigu_graha_rule must return a dict."""
    result = get_bhrigu_graha_rule("jupiter", 8)
    assert isinstance(result, dict)


def test_get_bhrigu_graha_rule_jupiter_8_inheritance():
    """Jupiter in 8H rule must mention inheritance or secret knowledge."""
    result = get_bhrigu_graha_rule("jupiter", 8)
    assert result
    effect = result.get("effect", "").lower()
    assert any(term in effect for term in ("inheritance", "secret", "legacy", "occult", "unexpected"))


def test_get_bhrigu_graha_rule_saturn_12_liberation():
    """Saturn in 12H rule must mention liberation or foreign."""
    result = get_bhrigu_graha_rule("saturn", 12)
    assert result
    effect = result.get("effect", "").lower()
    assert any(term in effect for term in ("liberation", "foreign", "spiritual", "renunciation"))


def test_get_bhrigu_graha_rule_mars_3_siblings():
    """Mars in 3H rule must mention siblings or courage."""
    result = get_bhrigu_graha_rule("mars", 3)
    assert result
    effect = result.get("effect", "").lower()
    assert any(term in effect for term in ("sibling", "courage", "journey", "entrepreneur"))


def test_get_bhrigu_graha_rule_moon_10_career():
    """Moon in 10H rule must mention public career or mother."""
    result = get_bhrigu_graha_rule("moon", 10)
    assert result
    effect = result.get("effect", "").lower()
    assert any(term in effect for term in ("public", "career", "mother", "fame", "vocation"))


def test_get_bhrigu_graha_rule_mercury_11_communication():
    """Mercury in 11H rule must mention communication or technology gains."""
    result = get_bhrigu_graha_rule("mercury", 11)
    assert result
    effect = result.get("effect", "").lower()
    assert any(term in effect for term in ("communication", "technology", "gain", "network"))


def test_get_bhrigu_graha_rule_venus_5_romance():
    """Venus in 5H rule must mention romance or creative children."""
    result = get_bhrigu_graha_rule("venus", 5)
    assert result
    effect = result.get("effect", "").lower()
    assert any(term in effect for term in ("romantic", "affair", "child", "creative", "artistic"))


def test_get_bhrigu_graha_rule_rahu_2_foreign_money():
    """Rahu in 2H rule must mention foreign money or unconventional speech."""
    result = get_bhrigu_graha_rule("rahu", 2)
    assert result
    effect = result.get("effect", "").lower()
    assert any(term in effect for term in ("foreign", "money", "speech", "unconventional"))


def test_get_bhrigu_graha_rule_case_insensitive():
    """get_bhrigu_graha_rule should normalise planet name to lowercase."""
    r1 = get_bhrigu_graha_rule("Jupiter", 8)
    r2 = get_bhrigu_graha_rule("JUPITER", 8)
    assert r1 == r2


def test_get_bhrigu_graha_rule_missing_returns_empty():
    """get_bhrigu_graha_rule for unknown combo must return empty dict."""
    result = get_bhrigu_graha_rule("neptune", 13)
    assert result == {}


# ---------------------------------------------------------------------------
# 6. list_sequence_rules API tests
# ---------------------------------------------------------------------------

def test_list_sequence_rules_returns_list():
    """list_sequence_rules must return a list."""
    result = list_sequence_rules()
    assert isinstance(result, list)


def test_list_sequence_rules_non_empty():
    """list_sequence_rules must return at least 10 items."""
    result = list_sequence_rules()
    assert len(result) >= 10


def test_list_sequence_rules_each_has_sequence_key():
    """Every item returned by list_sequence_rules must have a 'sequence' key."""
    for rule in list_sequence_rules():
        assert "sequence" in rule


def test_list_sequence_rules_each_has_meaning_key():
    """Every item returned by list_sequence_rules must have a 'meaning' key."""
    for rule in list_sequence_rules():
        assert "meaning" in rule


def test_list_sequence_rules_each_has_citation_key():
    """Every item returned by list_sequence_rules must have a 'citation' key."""
    for rule in list_sequence_rules():
        assert "citation" in rule


def test_list_sequence_rules_returns_copies():
    """list_sequence_rules must return copies, not references to originals."""
    rules = list_sequence_rules()
    rules[0]["sequence"] = "MUTATED"
    fresh = list_sequence_rules()
    assert fresh[0]["sequence"] != "MUTATED"


def test_list_sequence_rules_contains_rahu_jupiter():
    """list_sequence_rules must include a Rahu→Jupiter sequence."""
    seqs = [r["sequence"] for r in list_sequence_rules()]
    assert "Rahu→Jupiter" in seqs


def test_list_sequence_rules_contains_ketu_venus():
    """list_sequence_rules must include a Ketu→Venus sequence."""
    seqs = [r["sequence"] for r in list_sequence_rules()]
    assert "Ketu→Venus" in seqs
