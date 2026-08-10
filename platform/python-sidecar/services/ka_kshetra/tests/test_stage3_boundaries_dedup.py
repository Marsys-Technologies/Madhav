"""Tests for the stage3_clocks boundary-deduplication guard.

L1 chart_dashas can contain duplicate (level_n, start_iso) rows for some
systems (chara_karaka has up to 5 MD rows with the same start_iso confirmed
in production — 2026-08-10). Without deduplication, write_boundary_rows
would crash with a unique-constraint violation on
(chart_id, system_id, level, t_boundary).

These tests verify that compute_boundaries_for_system deduplicates its
output by (level, t_boundary) before returning, so write_boundary_rows
never sees duplicate boundary keys within a single system's rows.
"""
from __future__ import annotations

import pytest
from services.ka_kshetra.stage3_clocks import BoundaryRow, compute_boundaries_for_system


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_dasha_row(dasha_row_id, level_n, lord_graha, start_iso, duration_days, parent_row_id=None):
    from datetime import datetime, timezone
    # psycopg returns timezone-aware datetime objects from timestamptz columns
    dt = datetime.fromisoformat(start_iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return {
        "dasha_row_id": dasha_row_id,
        "level_n": level_n,
        "lord_graha": lord_graha,
        "lord_sign": None,
        "parent_row_id": parent_row_id,
        "start_iso": dt,
        "duration_days": float(duration_days),
    }


def _make_conn(dasha_rows, sigma_t_birth=1.0, sigma_t_source="test"):
    """Return a fake connection that answers the two SELECT queries stage3 issues."""

    class FakeCursor:
        def __init__(self, rows):
            self._rows = rows

        def fetchall(self):
            return self._rows

        def fetchone(self):
            return self._rows[0] if self._rows else None

    class FakeConn:
        def execute(self_inner, sql, params=None):
            sql = sql.strip()
            # sigma_t birth query
            if "sigma_t_days" in sql and "birth" in sql.lower():
                return FakeCursor([{"sigma_t_days": sigma_t_birth, "source": sigma_t_source}])
            # chart_dashas query for boundary rows
            if "chart_dashas" in sql and "level_n BETWEEN 1 AND 4" in sql:
                return FakeCursor(dasha_rows)
            # Any other query (system sigma_t sub-queries etc.)
            return FakeCursor([])

    return FakeConn()


# ── tests ────────────────────────────────────────────────────────────────────

class TestBoundaryDeduplication:
    """compute_boundaries_for_system must deduplicate (level, t_boundary) pairs."""

    def _call(self, dasha_rows):
        conn = _make_conn(dasha_rows)
        return compute_boundaries_for_system(
            "482012f1-710e-4a25-994a-93821f5871aa",
            "chara_karaka",
            conn,
            birth_params={"datetime_iso": "1984-02-05T05:13:00", "tz_offset_hours": 5.5},
        )

    def test_no_duplicates_passthrough(self):
        """Unique rows pass through unchanged."""
        rows = [
            _make_dasha_row(1, 1, "Sun", "1980-01-01T00:00:00+00:00", 365.0),
            _make_dasha_row(2, 1, "Moon", "1981-01-01T00:00:00+00:00", 730.0),
        ]
        result = self._call(rows)
        assert len(result) == 2

    def test_duplicate_md_rows_deduplicated(self):
        """Five chart_dashas rows with the same MD start collapse to one boundary."""
        same_start = "1950-01-01T00:00:00+00:00"
        rows = [
            _make_dasha_row(i, 1, f"Graha{i}", same_start, 365.0)
            for i in range(1, 6)  # 5 duplicates — matches production observation
        ]
        result = self._call(rows)
        assert len(result) == 1, (
            f"Expected 1 deduplicated row, got {len(result)}: {result}"
        )

    def test_first_occurrence_wins(self):
        """Deduplication keeps the first row (deterministic: lowest dasha_row_id wins)."""
        same_start = "1984-02-05T05:13:00+00:00"
        rows = [
            _make_dasha_row(10, 1, "Sun", same_start, 1825.0),
            _make_dasha_row(11, 1, "Moon", same_start, 1825.0),
            _make_dasha_row(12, 1, "Mars", same_start, 1825.0),
        ]
        result = self._call(rows)
        assert len(result) == 1
        assert result[0].lord == "Sun", "First row (dasha_row_id=10, lord=Sun) must win"

    def test_different_levels_not_deduplicated(self):
        """Rows with same start_iso but DIFFERENT levels are kept (different keys)."""
        same_start = "1984-02-05T05:13:00+00:00"
        rows = [
            _make_dasha_row(1, 1, "Sun", same_start, 1825.0),
            _make_dasha_row(2, 2, "Moon", same_start, 365.0, parent_row_id=1),
        ]
        result = self._call(rows)
        # level_n=1 → "MD", level_n=2 → "AD" — different levels, both kept
        assert len(result) == 2

    def test_result_is_list_of_boundary_rows(self):
        """Return type is list[BoundaryRow] even when deduplication occurs."""
        same_start = "1975-06-15T00:00:00+00:00"
        rows = [
            _make_dasha_row(1, 1, "Jupiter", same_start, 4380.0),
            _make_dasha_row(2, 1, "Saturn", same_start, 4380.0),
        ]
        result = self._call(rows)
        assert isinstance(result, list)
        assert all(isinstance(r, BoundaryRow) for r in result)
