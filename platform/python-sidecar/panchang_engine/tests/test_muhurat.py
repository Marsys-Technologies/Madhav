"""
test_muhurat.py — Muhurat scaffold tests.
Session 4C-1-S2.

3 trivial tests to verify the scaffold is callable without errors.
Full scoring tests land in 4C.6.
"""
from datetime import date
import pytest


def test_is_supported_event_valid():
    """vivah is in EVENTS_MVP."""
    from panchang_engine.muhurat import is_supported_event
    assert is_supported_event("vivah") is True


def test_is_supported_event_invalid():
    """An unknown event is not in EVENTS_MVP."""
    from panchang_engine.muhurat import is_supported_event
    assert is_supported_event("invalid_event") is False


def test_find_muhurat_returns_empty_list():
    """Scaffold find_muhurat returns [] for a valid event."""
    from panchang_engine.muhurat import find_muhurat
    result = find_muhurat("vivah", date(2026, 1, 1), date(2026, 1, 31), 20.27, 85.84)
    assert result == []


def test_find_muhurat_invalid_event_raises():
    """find_muhurat raises ValueError for an unsupported event."""
    from panchang_engine.muhurat import find_muhurat
    with pytest.raises(ValueError, match="not in MVP set"):
        find_muhurat("unsupported", date(2026, 1, 1), date(2026, 1, 31), 20.27, 85.84)


def test_score_muhurat_returns_zero():
    """Scaffold score_muhurat returns 0.0 for any valid input."""
    from panchang_engine.muhurat import score_muhurat
    assert score_muhurat(date(2026, 1, 1), 20.27, 85.84, "vivah") == 0.0


def test_all_events_supported():
    """All 6 MVP events are recognized."""
    from panchang_engine.muhurat import is_supported_event, EVENTS_MVP
    assert len(EVENTS_MVP) == 6
    for event in EVENTS_MVP:
        assert is_supported_event(event), f"EVENTS_MVP entry '{event}' not recognized"
