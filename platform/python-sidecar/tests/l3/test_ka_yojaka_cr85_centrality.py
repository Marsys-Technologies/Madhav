"""
Tests for ka_yojaka's CR-85 stub-removal fix (D-2 Lane V-4): the
_extract_primary_graha normalization that makes cgm_centrality_weight resolve
against real bodha_cgm_nodes.node_subject values instead of defaulting to the
flat 0.5 stub for nearly every predicate.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.ka_yojaka import (
    _normalize_graha_to_node_subject,
    _extract_primary_graha,
)


def test_normalize_short_code_to_title_case():
    assert _normalize_graha_to_node_subject("MAR") == "Mars"
    assert _normalize_graha_to_node_subject("SUN") == "Sun"
    assert _normalize_graha_to_node_subject("RAH_MEAN") == "Rahu"
    assert _normalize_graha_to_node_subject("KET_MEAN") == "Ketu"


def test_normalize_lowercase_full_name():
    assert _normalize_graha_to_node_subject("mars") == "Mars"
    assert _normalize_graha_to_node_subject("saturn") == "Saturn"


def test_normalize_already_title_case_passthrough():
    assert _normalize_graha_to_node_subject("Venus") == "Venus"


def test_normalize_unrecognized_token_returns_none():
    assert _normalize_graha_to_node_subject("not_a_graha") is None
    assert _normalize_graha_to_node_subject("") is None
    assert _normalize_graha_to_node_subject(None) is None


def test_extract_primary_graha_normalizes_short_code():
    """Before the CR-85 fix this returned the raw 'MAR' verbatim, which would
    never match a bodha_cgm_nodes.node_subject='Mars' key — the flat-0.5 stub."""
    signal = {"configuration_jsonb": {"graha": "MAR"}}
    assert _extract_primary_graha(signal) == "Mars"


def test_extract_primary_graha_falls_through_unresolvable_key_to_next():
    """A key present but not a real graha token no longer short-circuits the
    whole extraction (prior behavior: returned the garbage value verbatim,
    guaranteeing a cgm_pagerank miss even when a LATER key had a real graha)."""
    signal = {"configuration_jsonb": {"fact_value_text": "not_a_graha", "graha": "VEN"}}
    assert _extract_primary_graha(signal) == "Venus"


def test_extract_primary_graha_json_string_config():
    import json
    signal = {"configuration_jsonb": json.dumps({"primary_graha": "sat"})}
    assert _extract_primary_graha(signal) == "Saturn"


def test_extract_primary_graha_no_match_returns_none():
    signal = {"configuration_jsonb": {"house": 7}}
    assert _extract_primary_graha(signal) is None
