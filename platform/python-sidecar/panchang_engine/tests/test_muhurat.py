"""
test_muhurat.py — Muhurat module smoke tests.

Updated P2 re-arch (2026-06-09): tz_offset_minutes is now required (no default).
All find_muhurat calls pass tz_offset_minutes=330 (IST) explicitly.
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


def test_find_muhurat_invalid_event_raises():
    """find_muhurat raises ValueError for an unsupported event."""
    from panchang_engine.muhurat import find_muhurat
    with pytest.raises(ValueError, match="not in MVP set"):
        find_muhurat("unsupported", date(2026, 1, 1), date(2026, 1, 31), 20.27, 85.84, 330)


def test_find_muhurat_returns_list():
    """find_muhurat returns a list (may be non-empty for real dates)."""
    from panchang_engine.muhurat import find_muhurat
    result = find_muhurat("vivah", date(2026, 1, 1), date(2026, 1, 31), 20.27, 85.84, 330)
    assert isinstance(result, list)


def test_find_muhurat_sorted_by_score():
    """find_muhurat returns windows sorted by score descending."""
    from panchang_engine.muhurat import find_muhurat
    result = find_muhurat("vivah", date(2026, 1, 1), date(2026, 1, 31), 20.27, 85.84, 330, top_n=10)
    scores = [w.score for w in result]
    assert scores == sorted(scores, reverse=True), "Windows not sorted by score"


def test_find_muhurat_top_n_respected():
    """find_muhurat returns at most top_n windows."""
    from panchang_engine.muhurat import find_muhurat
    result = find_muhurat("vivah", date(2026, 1, 1), date(2026, 3, 31), 20.27, 85.84, 330, top_n=5)
    assert len(result) <= 5


def test_all_events_supported():
    """All 6 MVP events are recognized."""
    from panchang_engine.muhurat import is_supported_event, EVENTS_MVP
    assert len(EVENTS_MVP) == 6
    for event in EVENTS_MVP:
        assert is_supported_event(event), f"EVENTS_MVP entry '{event}' not recognized"
