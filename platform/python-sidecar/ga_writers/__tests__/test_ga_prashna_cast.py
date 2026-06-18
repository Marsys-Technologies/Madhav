"""Tests for ga_prashna_cast — direct prashna chart build path."""
import pytest
from unittest.mock import MagicMock, patch
from ga_writers.ga_prashna_cast import (
    validate_prashna_question,
    cast_prashna_chart,
    VALID_QUESTION_CLASSES,
)


def test_validate_rejects_lookup_question():
    result = validate_prashna_question("What is Jupiter's longitude?")
    assert result["valid"] is False
    assert "not a valid Prashna question" in result["reason"]


def test_validate_accepts_forward_looking_question():
    result = validate_prashna_question("Will I get the job I applied for?")
    assert result["valid"] is True


def test_valid_question_classes_coverage():
    assert "career" in VALID_QUESTION_CLASSES
    assert "marriage" in VALID_QUESTION_CLASSES
    assert "health_illness" in VALID_QUESTION_CLASSES


def test_cast_prashna_chart_returns_chart_id():
    """cast_prashna_chart inserts a prashna_charts row and calls ga_positions + ga_prashna."""
    mock_conn = MagicMock()
    # cursor() must work as both plain call and context manager
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    with patch("ga_writers.ga_prashna_cast.build_ga_positions") as mock_positions, \
         patch("ga_writers.ga_prashna_cast.seed_prashna_judgment") as mock_judgment, \
         patch("ga_writers.ga_prashna_cast.compute_prashna_judgment") as mock_compute:
        mock_positions.return_value = {"total_chart_facts_rows": 50}
        mock_judgment.return_value = 2
        mock_compute.return_value = {"judgment_text": "YES"}

        result = cast_prashna_chart(
            conn=mock_conn,
            build_id="test-build-001",
            question_text="Will the project succeed?",
            question_class="career",
            prashna_lagna_method="tajik_moment_lagna",
            question_instant="2026-06-18T22:00:00+05:30",
            question_lat=20.27,
            question_lon=85.84,
            querent_natal_chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        )

    assert "chart_id" in result
    assert isinstance(result["chart_id"], str) and len(result["chart_id"]) == 36  # UUID
    assert result["rows_inserted"] == 10  # 2 rows × 5 ayanamshas
    mock_positions.assert_called_once()
    assert mock_judgment.call_count == 5  # one per ayanamsha


def test_validate_rejects_whats_contraction():
    result = validate_prashna_question("What's my Moon sign?")
    assert result["valid"] is False


def test_validate_rejects_whats_no_apostrophe():
    result = validate_prashna_question("whats my lagna?")
    assert result["valid"] is False


def test_validate_rejects_whatre_contraction():
    result = validate_prashna_question("What're the aspects on my chart?")
    assert result["valid"] is False


def test_validate_still_accepts_genuine_horary():
    result = validate_prashna_question("Will I get this job?")
    assert result["valid"] is True
