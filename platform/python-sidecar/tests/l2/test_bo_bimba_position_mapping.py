import pytest
from pipeline.orchestrator.writers.bo_bimba import _SUBJECT_TO_GRAHA, KNOWN_GRAHAS


def test_all_known_grahas_have_mapping():
    """Every KNOWN_GRAHA must be reachable via the fact_subject mapping."""
    mapped_values = set(_SUBJECT_TO_GRAHA.values())
    for graha in KNOWN_GRAHAS:
        assert graha in mapped_values, (
            f"KNOWN_GRAHA '{graha}' has no entry in _SUBJECT_TO_GRAHA — "
            f"it will never get position_in_chart_jsonb populated"
        )


def test_subject_to_graha_mapping_is_correct():
    """Spot-check that abbreviated codes map to full English names."""
    assert _SUBJECT_TO_GRAHA["MAR"] == "Mars"
    assert _SUBJECT_TO_GRAHA["MER"] == "Mercury"
    assert _SUBJECT_TO_GRAHA["JUP"] == "Jupiter"
    assert _SUBJECT_TO_GRAHA["VEN"] == "Venus"
    assert _SUBJECT_TO_GRAHA["SAT"] == "Saturn"
    assert _SUBJECT_TO_GRAHA["RAH_MEAN"] == "Rahu"
    assert _SUBJECT_TO_GRAHA["KET_MEAN"] == "Ketu"
    assert _SUBJECT_TO_GRAHA["SUN"] == "Sun"
    assert _SUBJECT_TO_GRAHA["MOON"] == "Moon"


def test_title_case_fallback_does_not_produce_wrong_values():
    """Demonstrate the old bug: subject.title() was wrong for abbreviated codes."""
    assert "MAR".title() != "Mars"     # was producing "Mar"
    assert "MER".title() != "Mercury"  # was producing "Mer"
    assert "JUP".title() != "Jupiter"  # was producing "Jup"
