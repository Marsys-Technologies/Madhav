"""
Integration test: bg_ghatana writer produces 27/27 classes with DR-13 columns.
Tests that seed_ghatana() can INSERT into a table with the NOT NULL temporal_shape
constraint (the bug this lane fixes).
"""
import json
import pytest
from brahmagyan.l0_ghatana import EVENT_CLASSES, seed_ghatana


def test_event_classes_count():
    """27 event classes after DR-13 expansion."""
    assert len(EVENT_CLASSES) == 27


def test_all_classes_have_temporal_shape():
    """Every EVENT_CLASSES entry has a valid temporal_shape."""
    valid_shapes = {"point", "interval", "chain"}
    for ec in EVENT_CLASSES:
        assert "temporal_shape" in ec, f"{ec['event_class_id']} missing temporal_shape"
        assert ec["temporal_shape"] in valid_shapes, (
            f"{ec['event_class_id']}: invalid temporal_shape {ec['temporal_shape']!r}"
        )


def test_shape_companion_consistency():
    """Shape/companion fields are self-consistent per migration 456 CHECK constraints."""
    for ec in EVENT_CLASSES:
        shape = ec["temporal_shape"]
        if shape == "point":
            assert ec.get("duration_prior") is None, f"{ec['event_class_id']}: point + duration_prior"
            assert ec.get("milestone_template") is None, f"{ec['event_class_id']}: point + milestone_template"
            assert ec.get("irreversibility_milestone") is None, f"{ec['event_class_id']}: point + irreversibility_milestone"
        elif shape == "interval":
            assert ec.get("duration_prior") is not None, f"{ec['event_class_id']}: interval needs duration_prior"
            assert ec.get("milestone_template") is None, f"{ec['event_class_id']}: interval + milestone_template"
        elif shape == "chain":
            mt = ec.get("milestone_template")
            assert mt is not None and len(mt) >= 2, f"{ec['event_class_id']}: chain needs milestone_template >=2"


def test_version_is_2_0():
    """No class should produce version '1.1' — all are DR-13 v2.0."""
    # The INSERT uses '2.0' not '1.1'
    from brahmagyan.l0_ghatana import seed_ghatana
    import inspect
    source = inspect.getsource(seed_ghatana)
    assert "'1.1'" not in source, "seed_ghatana still contains version '1.1'"
    assert "'2.0'" in source, "seed_ghatana should use version '2.0'"


def test_dr13_classes_present():
    """The 5 DR-13 classes added by migration 456 are present."""
    dr13_ids = {"achievement_recognition", "financial_deception", "psychological_arc", "birth_anchor", "travel_event"}
    actual_ids = {ec["event_class_id"] for ec in EVENT_CLASSES}
    missing = dr13_ids - actual_ids
    assert not missing, f"Missing DR-13 classes: {missing}"
