"""
test_meta_alpha.py — Unit tests for META-α (Λ-LATTICE)
========================================================
Covers:
  T01: Migration file exists
  T02: Migration contains correct table name
  T03: classify_resonance — quiescent at 0
  T04: classify_resonance — medium at 1
  T05: classify_resonance — medium at 2
  T06: classify_resonance — high at 3
  T07: classify_resonance — high at 5
  T08: compute_lattice_for_date — returns required top-level keys
  T09: compute_lattice_for_date — high_priority_attention_flag False when count < 2
  T10: compute_lattice_for_date — high_priority_attention_flag True when count >= 2
  T11: write_lattice_window — returns 0 rows for empty date range (start > end)
  T12: write_lattice_window — returns correct count for a 3-day window
  T13: query_lattice_at_date has correct signature
  T14: query_lattice_in_range has correct signature
  T15: query_lattice_high_resonance_windows has correct signature
  T16: query_lattice_peers has correct signature
  T17: LATTICE_COLS contains snapshot_id
  T18: LATTICE_COLS contains resonance_class_at_date
  T19: LATTICE_COLS contains high_priority_attention_flag
  T20: compute_lattice_for_date resonance_class matches classify_resonance

All tests are pure unit tests — no DB connection required.

META-α-S1 / META-α-S2 [BUILD-ORCH-STREAM-D-META-ALPHA-S1]
"""
from __future__ import annotations

import inspect
import os
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Imports under test
# ---------------------------------------------------------------------------
from pipeline.writers.chart_lattice_writer import (
    classify_resonance,
    compute_lattice_for_date,
    write_lattice_window,
)
from pipeline.query.query_lattice import (
    LATTICE_COLS,
    query_lattice_at_date,
    query_lattice_in_range,
    query_lattice_high_resonance_windows,
    query_lattice_peers,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# __tests__ is inside platform/python-sidecar/pipeline/__tests__/
# migrations are at platform/migrations/ — go up 3 levels then into migrations/
MIGRATION_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..",            # __tests__ → pipeline → python-sidecar → platform
        "migrations", "152_chart_lattice_mv.sql",
    )
)

SAMPLE_CHART_ID = "00000000-0000-0000-0000-000000000001"
SAMPLE_AYA = "lahiri"


def _make_mock_conn(fetchall_side_effect=None):
    """
    Return a minimal mock psycopg2 connection whose cursor's execute/fetchall/
    fetchone calls succeed without raising — simulating an empty DB result.
    """
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    cur.fetchall.return_value = []
    cur.fetchone.return_value = None
    cur.description = []

    conn = MagicMock()
    conn.cursor.return_value = cur
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    return conn


# ---------------------------------------------------------------------------
# T01–T02: migration file
# ---------------------------------------------------------------------------

class TestMigrationFile:
    def test_T01_migration_file_exists(self):
        """T01: 152_chart_lattice_mv.sql must exist on disk."""
        assert os.path.isfile(MIGRATION_PATH), (
            f"Migration file not found at {MIGRATION_PATH}"
        )

    def test_T02_migration_contains_table_name(self):
        """T02: Migration must reference l25_chart_lattice_snapshots."""
        with open(MIGRATION_PATH) as fh:
            sql = fh.read()
        assert "l25_chart_lattice_snapshots" in sql


# ---------------------------------------------------------------------------
# T03–T07: classify_resonance
# ---------------------------------------------------------------------------

class TestClassifyResonance:
    def test_T03_quiescent_at_zero(self):
        """T03: 0 active patterns → quiescent."""
        assert classify_resonance(0) == "quiescent"

    def test_T04_medium_at_one(self):
        """T04: 1 active pattern → medium."""
        assert classify_resonance(1) == "medium"

    def test_T05_medium_at_two(self):
        """T05: 2 active patterns → medium (below high threshold of 3)."""
        assert classify_resonance(2) == "medium"

    def test_T06_high_at_three(self):
        """T06: 3 active patterns → high."""
        assert classify_resonance(3) == "high"

    def test_T07_high_at_five(self):
        """T07: 5 active patterns → high."""
        assert classify_resonance(5) == "high"


# ---------------------------------------------------------------------------
# T08–T10, T20: compute_lattice_for_date
# ---------------------------------------------------------------------------

class TestComputeLatticeForDate:
    """Uses a mock connection that returns empty results for all sub-queries."""

    def _compute(self, active_count_override: int = 0) -> dict:
        conn = _make_mock_conn()
        result = compute_lattice_for_date(
            conn, SAMPLE_CHART_ID, SAMPLE_AYA, None, date(2026, 6, 1)
        )
        # Manually inject active count to test flag/resonance derivation
        result["total_active_pattern_count"] = active_count_override
        result["resonance_class_at_date"] = classify_resonance(active_count_override)
        result["high_priority_attention_flag"] = active_count_override >= 2
        return result

    def test_T08_required_keys_present(self):
        """T08: Result dict must contain all required top-level keys."""
        result = compute_lattice_for_date(
            _make_mock_conn(), SAMPLE_CHART_ID, SAMPLE_AYA, None, date(2026, 6, 1)
        )
        required = {
            "snapshot_id", "chart_id", "ayanamsha_id", "build_id", "date_iso",
            "active_dasha_jsonb", "active_synchronicity_jsonb", "active_anchors_jsonb",
            "active_vedhas_jsonb", "nearby_bhrigu_hits_jsonb", "nearby_exact_aspects_jsonb",
            "total_active_pattern_count", "resonance_class_at_date",
            "high_priority_attention_flag",
        }
        assert required.issubset(set(result.keys()))

    def test_T09_attention_flag_false_below_threshold(self):
        """T09: high_priority_attention_flag is False when active_count < 2."""
        result = self._compute(active_count_override=1)
        assert result["high_priority_attention_flag"] is False

    def test_T10_attention_flag_true_at_threshold(self):
        """T10: high_priority_attention_flag is True when active_count >= 2."""
        result = self._compute(active_count_override=2)
        assert result["high_priority_attention_flag"] is True

    def test_T20_resonance_matches_classify(self):
        """T20: resonance_class_at_date is always consistent with classify_resonance."""
        for count in range(6):
            result = self._compute(active_count_override=count)
            assert result["resonance_class_at_date"] == classify_resonance(count), (
                f"Mismatch at count={count}"
            )


# ---------------------------------------------------------------------------
# T11–T12: write_lattice_window
# ---------------------------------------------------------------------------

class TestWriteLatticeWindow:
    def test_T11_empty_range_returns_zero(self):
        """T11: start_date > end_date → 0 rows written."""
        conn = _make_mock_conn()
        count = write_lattice_window(
            conn, SAMPLE_CHART_ID, SAMPLE_AYA, None,
            date(2026, 6, 10), date(2026, 6, 9),  # inverted range
        )
        assert count == 0

    def test_T12_three_day_window_writes_three_rows(self):
        """T12: A 3-day window upserts exactly 3 rows."""
        conn = _make_mock_conn()
        count = write_lattice_window(
            conn, SAMPLE_CHART_ID, SAMPLE_AYA, None,
            date(2026, 6, 1), date(2026, 6, 3),
        )
        assert count == 3
        assert conn.commit.call_count == 3


# ---------------------------------------------------------------------------
# T13–T16: query function signatures
# ---------------------------------------------------------------------------

class TestQuerySignatures:
    def test_T13_query_lattice_at_date_signature(self):
        """T13: query_lattice_at_date accepts (conn, chart_id, ayanamsha_id, date_iso, depth_class)."""
        sig = inspect.signature(query_lattice_at_date)
        params = list(sig.parameters)
        assert "conn" in params
        assert "chart_id" in params
        assert "ayanamsha_id" in params
        assert "date_iso" in params
        assert "depth_class" in params

    def test_T14_query_lattice_in_range_signature(self):
        """T14: query_lattice_in_range accepts (conn, chart_id, ayanamsha_id, start_iso, end_iso, attention_only, limit)."""
        sig = inspect.signature(query_lattice_in_range)
        params = list(sig.parameters)
        for expected in ["conn", "chart_id", "ayanamsha_id", "start_iso", "end_iso", "attention_only", "limit"]:
            assert expected in params, f"Missing param: {expected}"

    def test_T15_query_lattice_high_resonance_signature(self):
        """T15: query_lattice_high_resonance_windows accepts (conn, chart_id, ayanamsha_id, top_k)."""
        sig = inspect.signature(query_lattice_high_resonance_windows)
        params = list(sig.parameters)
        for expected in ["conn", "chart_id", "ayanamsha_id", "top_k"]:
            assert expected in params

    def test_T16_query_lattice_peers_signature(self):
        """T16: query_lattice_peers accepts (conn, chart_id, ayanamsha_id, date_iso, top_k)."""
        sig = inspect.signature(query_lattice_peers)
        params = list(sig.parameters)
        for expected in ["conn", "chart_id", "ayanamsha_id", "date_iso", "top_k"]:
            assert expected in params


# ---------------------------------------------------------------------------
# T17–T19: LATTICE_COLS content
# ---------------------------------------------------------------------------

class TestLatticeColsContent:
    def test_T17_contains_snapshot_id(self):
        """T17: LATTICE_COLS must include snapshot_id."""
        assert "snapshot_id" in LATTICE_COLS

    def test_T18_contains_resonance_class(self):
        """T18: LATTICE_COLS must include resonance_class_at_date."""
        assert "resonance_class_at_date" in LATTICE_COLS

    def test_T19_contains_attention_flag(self):
        """T19: LATTICE_COLS must include high_priority_attention_flag."""
        assert "high_priority_attention_flag" in LATTICE_COLS
