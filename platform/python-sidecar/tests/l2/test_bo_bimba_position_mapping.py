"""
Tests for bo_bimba._SUBJECT_TO_GRAHA mapping fix.

Root cause: _fetch_graha_positions used subject.title() to convert L1 fact_subject
codes to KNOWN_GRAHAS names. SUN→Sun and MOON→Moon work accidentally (4-letter codes
title-case to the full name), but MAR→Mar, MER→Mer, JUP→Jup, VEN→Ven, SAT→Sat all
produce wrong values. This test suite guards against regression.
"""
import pytest


def test_all_known_grahas_have_mapping():
    """Every KNOWN_GRAHA must be reachable via the fact_subject mapping."""
    from pipeline.orchestrator.writers.bo_bimba import _SUBJECT_TO_GRAHA, KNOWN_GRAHAS
    mapped_values = set(_SUBJECT_TO_GRAHA.values())
    for graha in KNOWN_GRAHAS:
        assert graha in mapped_values, (
            f"KNOWN_GRAHA '{graha}' has no entry in _SUBJECT_TO_GRAHA — "
            f"it will never get position_in_chart_jsonb populated"
        )


def test_subject_to_graha_mapping_is_correct():
    """Spot-check that abbreviated L1 codes map to full English graha names."""
    from pipeline.orchestrator.writers.bo_bimba import _SUBJECT_TO_GRAHA
    assert _SUBJECT_TO_GRAHA["MAR"] == "Mars"
    assert _SUBJECT_TO_GRAHA["MER"] == "Mercury"
    assert _SUBJECT_TO_GRAHA["JUP"] == "Jupiter"
    assert _SUBJECT_TO_GRAHA["VEN"] == "Venus"
    assert _SUBJECT_TO_GRAHA["SAT"] == "Saturn"
    assert _SUBJECT_TO_GRAHA["RAH_MEAN"] == "Rahu"
    assert _SUBJECT_TO_GRAHA["KET_MEAN"] == "Ketu"
    assert _SUBJECT_TO_GRAHA["SUN"] == "Sun"
    assert _SUBJECT_TO_GRAHA["MOON"] == "Moon"


def test_old_title_case_was_wrong():
    """Document the original bug: title() on abbreviated codes produces wrong values."""
    assert "MAR".title() != "Mars"    # produced "Mar"
    assert "MER".title() != "Mercury" # produced "Mer"
    assert "JUP".title() != "Jupiter" # produced "Jup"
    assert "VEN".title() != "Venus"   # produced "Ven"
    assert "SAT".title() != "Saturn"  # produced "Sat"


def test_mapping_covers_all_expected_l1_fact_subjects():
    """All L1 fact_subject codes observed in chart_facts must be in the mapping."""
    from pipeline.orchestrator.writers.bo_bimba import _SUBJECT_TO_GRAHA
    l1_codes = {"SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN"}
    for code in l1_codes:
        assert code in _SUBJECT_TO_GRAHA, f"L1 code '{code}' not in _SUBJECT_TO_GRAHA"


def test_fallback_preserves_unknown_subjects():
    """The .get(..., subject.title()) fallback handles unknown fact_subject codes."""
    from pipeline.orchestrator.writers.bo_bimba import _SUBJECT_TO_GRAHA
    unknown = "UNKNOWN_CODE"
    result = _SUBJECT_TO_GRAHA.get(unknown.upper(), unknown.title())
    assert result == "Unknown_Code"  # title() fallback, not a crash
