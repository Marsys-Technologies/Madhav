"""
Test W3.3 — Multi-resolution window hierarchy with parent_window_id.

Tests for gochara_v3.resolution_hierarchy:

  1. test_resolution_tiers_ordered — RESOLUTION_TIERS has era < month < day < muhurta
     (index order, coarsest first).
  2. test_assign_parent_window_ids_basic — an era window [0, 100] contains a month
     window [10, 40]; the month window receives parent_id = era window's id.
  3. test_assign_parent_window_ids_no_parent — a window with no containing coarser
     window receives parent_window_id = None.
  4. test_era_classification — a window of duration > 365d is classified as "era",
     a window < 365d is classified as "month" (via build_era_windows logic).
  5. test_build_resolution_hierarchy_empty — when find_threshold_crossings returns []
     (always-below), all three tiers return [] and resolution_facet counts are all 0.
  6. test_resolution_facet_counts — given 1 era, 3 month, 7 day windows, the
     resolution_facet is {"era": 1, "month": 3, "day": 7}.

All tests mock find_threshold_crossings and _eval_single from interval_solver to
avoid DB/ephemeris calls. DB-free.
"""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from services.gochara_v3.resolution_hierarchy import (
    RESOLUTION_TIERS,
    ERA_MIN_DAYS,
    WindowResolutionRecord,
    HierarchyResult,
    assign_parent_window_ids,
    build_era_windows,
    build_resolution_hierarchy,
)
from services.gochara_v3.interval_solver import IntervalBoundary, ERA_SLICE_KEY_V3
from services.gochara_v3.threshold import ThresholdConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_threshold_config(lambda_thresh: float = 0.5) -> ThresholdConfig:
    """Build a minimal ThresholdConfig for testing."""
    return ThresholdConfig(
        percentile_used=0.90,
        lambda_thresh=lambda_thresh,
        implied_density=1.0,
        base_rate_cited=0.10,
        age_band_used="band_41_60",
        density_flag="ok",
        fallback_used=False,
        sample_count=100,
    )


def _make_window(
    tier: str,
    enter_jd: float,
    exit_jd: float,
    peak_jd: float = None,
    peak_lambda: float = 0.7,
    window_id: str = None,
    parent_window_id: str = None,
) -> WindowResolutionRecord:
    """Construct a WindowResolutionRecord with sensible defaults."""
    if peak_jd is None:
        peak_jd = 0.5 * (enter_jd + exit_jd)
    if window_id is None:
        window_id = str(uuid.uuid4())
    return WindowResolutionRecord(
        window_id=window_id,
        parent_window_id=parent_window_id,
        resolution_tier=tier,
        enter_jd=enter_jd,
        exit_jd=exit_jd,
        peak_jd=peak_jd,
        peak_lambda=peak_lambda,
    )


def _make_interval(
    enter_jd: float,
    exit_jd: float,
    peak_jd: float = None,
    peak_lambda: float = 0.8,
) -> IntervalBoundary:
    """Construct an IntervalBoundary fixture."""
    if peak_jd is None:
        peak_jd = 0.5 * (enter_jd + exit_jd)
    return IntervalBoundary(
        enter_jd=enter_jd,
        exit_jd=exit_jd,
        peak_jd=peak_jd,
        peak_lambda=peak_lambda,
        era_slice_key=ERA_SLICE_KEY_V3,
    )


# ---------------------------------------------------------------------------
# Test 1 — RESOLUTION_TIERS ordering
# ---------------------------------------------------------------------------

class TestResolutionTiersOrdered:
    def test_resolution_tiers_ordered(self):
        """RESOLUTION_TIERS must be (era, month, day, muhurta) — coarsest first."""
        assert RESOLUTION_TIERS[0] == "era", "era must be index 0 (coarsest)"
        assert RESOLUTION_TIERS[1] == "month", "month must be index 1"
        assert RESOLUTION_TIERS[2] == "day", "day must be index 2"
        assert RESOLUTION_TIERS[3] == "muhurta", "muhurta must be index 3 (finest built)"

    def test_tier_count(self):
        """RESOLUTION_TIERS must have exactly 4 tiers."""
        assert len(RESOLUTION_TIERS) == 4

    def test_era_before_month_before_day(self):
        """era index < month index < day index (strict coarseness ordering)."""
        assert RESOLUTION_TIERS.index("era") < RESOLUTION_TIERS.index("month")
        assert RESOLUTION_TIERS.index("month") < RESOLUTION_TIERS.index("day")
        assert RESOLUTION_TIERS.index("day") < RESOLUTION_TIERS.index("muhurta")


# ---------------------------------------------------------------------------
# Test 2 — assign_parent_window_ids basic containment
# ---------------------------------------------------------------------------

class TestAssignParentWindowIds:
    def test_assign_parent_window_ids_basic(self):
        """An era window [0,100] containing a month window [10,40] → month gets parent."""
        era_id = str(uuid.uuid4())
        month_id = str(uuid.uuid4())

        era_win = _make_window("era", enter_jd=0.0, exit_jd=100.0, window_id=era_id)
        month_win = _make_window("month", enter_jd=10.0, exit_jd=40.0, window_id=month_id)

        result = assign_parent_window_ids([era_win, month_win])

        # Find the month window in result
        month_result = next(w for w in result if w.window_id == month_id)
        era_result = next(w for w in result if w.window_id == era_id)

        assert month_result.parent_window_id == era_id, (
            f"month window should have parent={era_id}, got {month_result.parent_window_id}"
        )
        assert era_result.parent_window_id is None, (
            "era window should have no parent (no coarser tier above it)"
        )

    def test_assign_parent_window_ids_no_parent(self):
        """A window with no containing coarser window gets parent_window_id=None."""
        # Only a month window — no era window to parent it
        month_id = str(uuid.uuid4())
        month_win = _make_window("month", enter_jd=10.0, exit_jd=40.0, window_id=month_id)

        result = assign_parent_window_ids([month_win])
        assert len(result) == 1
        assert result[0].parent_window_id is None

    def test_assign_parent_picks_widest_coarser_window(self):
        """When two era windows both contain a month window, the wider one is chosen."""
        wide_era_id = str(uuid.uuid4())
        narrow_era_id = str(uuid.uuid4())
        month_id = str(uuid.uuid4())

        # Both era windows contain [20, 30]
        wide_era = _make_window("era", enter_jd=0.0, exit_jd=100.0, window_id=wide_era_id)
        narrow_era = _make_window("era", enter_jd=15.0, exit_jd=35.0, window_id=narrow_era_id)
        month_win = _make_window("month", enter_jd=20.0, exit_jd=30.0, window_id=month_id)

        result = assign_parent_window_ids([wide_era, narrow_era, month_win])
        month_result = next(w for w in result if w.window_id == month_id)

        # wide_era (span=100) > narrow_era (span=20) → wide_era is chosen
        assert month_result.parent_window_id == wide_era_id

    def test_assign_parent_does_not_assign_same_tier_as_parent(self):
        """A window at tier T must not receive a parent at tier T (only coarser)."""
        month_a_id = str(uuid.uuid4())
        month_b_id = str(uuid.uuid4())

        # Two month windows, one containing the other
        month_a = _make_window("month", enter_jd=0.0, exit_jd=60.0, window_id=month_a_id)
        month_b = _make_window("month", enter_jd=5.0, exit_jd=35.0, window_id=month_b_id)

        result = assign_parent_window_ids([month_a, month_b])
        # Neither should get the other as parent (same tier)
        for w in result:
            assert w.parent_window_id is None, (
                f"month window {w.window_id} incorrectly got parent {w.parent_window_id}"
            )

    def test_assign_parent_preserves_all_window_ids(self):
        """assign_parent_window_ids must return the same set of window_ids as input."""
        ids = [str(uuid.uuid4()) for _ in range(5)]
        windows = [
            _make_window("era", 0.0, 1000.0, window_id=ids[0]),
            _make_window("month", 10.0, 40.0, window_id=ids[1]),
            _make_window("month", 50.0, 80.0, window_id=ids[2]),
            _make_window("day", 12.0, 13.0, window_id=ids[3]),
            _make_window("day", 55.0, 56.0, window_id=ids[4]),
        ]

        result = assign_parent_window_ids(windows)
        result_ids = {w.window_id for w in result}
        assert result_ids == set(ids)


# ---------------------------------------------------------------------------
# Test 4 — era vs month classification
# ---------------------------------------------------------------------------

class TestEraClassification:
    """Test that build_era_windows classifies windows by duration correctly."""

    def test_era_classification_long_interval(self):
        """A window of duration > ERA_MIN_DAYS (365d) is classified as 'era'."""
        # 500-day interval → era
        long_interval = _make_interval(enter_jd=0.0, exit_jd=500.0)

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=[long_interval],
        ):
            swe = MagicMock()
            context = MagicMock()
            config = _make_threshold_config()

            windows = build_era_windows(swe, context, 0.0, 1000.0, config)

        assert len(windows) == 1
        assert windows[0].resolution_tier == "era", (
            f"500d window should be 'era', got '{windows[0].resolution_tier}'"
        )

    def test_era_classification_short_interval(self):
        """A window of duration < ERA_MIN_DAYS (365d) is classified as 'month'."""
        # 90-day interval → month
        short_interval = _make_interval(enter_jd=0.0, exit_jd=90.0)

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=[short_interval],
        ):
            swe = MagicMock()
            context = MagicMock()
            config = _make_threshold_config()

            windows = build_era_windows(swe, context, 0.0, 500.0, config)

        assert len(windows) == 1
        assert windows[0].resolution_tier == "month", (
            f"90d window should be 'month', got '{windows[0].resolution_tier}'"
        )

    def test_era_boundary_exactly_365d(self):
        """A window of duration exactly ERA_MIN_DAYS is classified as 'era'."""
        boundary_interval = _make_interval(enter_jd=0.0, exit_jd=ERA_MIN_DAYS)

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=[boundary_interval],
        ):
            swe = MagicMock()
            context = MagicMock()
            config = _make_threshold_config()

            windows = build_era_windows(swe, context, 0.0, 2000.0, config)

        assert len(windows) == 1
        assert windows[0].resolution_tier == "era"


# ---------------------------------------------------------------------------
# Test 5 — build_resolution_hierarchy empty (always-below λ)
# ---------------------------------------------------------------------------

class TestBuildResolutionHierarchyEmpty:
    def test_build_resolution_hierarchy_empty(self):
        """When find_threshold_crossings returns [], all tiers are empty and facet=0."""
        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=[],
        ):
            swe = MagicMock()
            context = MagicMock()
            config = _make_threshold_config()

            result = build_resolution_hierarchy(swe, context, 0.0, 1000.0, config)

        assert isinstance(result, HierarchyResult)
        assert result.era_windows == []
        assert result.month_windows == []
        assert result.day_windows == []
        assert result.resolution_facet == {"era": 0, "month": 0, "day": 0}

    def test_resolution_facet_keys_always_present(self):
        """resolution_facet must always have 'era', 'month', 'day' keys."""
        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=[],
        ):
            swe = MagicMock()
            context = MagicMock()
            config = _make_threshold_config()

            result = build_resolution_hierarchy(swe, context, 0.0, 1000.0, config)

        assert "era" in result.resolution_facet
        assert "month" in result.resolution_facet
        assert "day" in result.resolution_facet


# ---------------------------------------------------------------------------
# Test 6 — resolution_facet counts
# ---------------------------------------------------------------------------

class TestResolutionFacetCounts:
    def test_resolution_facet_counts(self):
        """Given 1 era, 3 month, 7 day windows, resolution_facet is {era:1, month:3, day:7}."""
        # We construct a HierarchyResult directly (testing the facet field, not the builder).
        era_wins = [_make_window("era", 0.0, 1000.0)]
        month_wins = [
            _make_window("month", 0.0, 30.0),
            _make_window("month", 30.0, 60.0),
            _make_window("month", 60.0, 90.0),
        ]
        day_wins = [_make_window("day", float(i), float(i + 1)) for i in range(7)]

        facet = {
            "era": len(era_wins),
            "month": len(month_wins),
            "day": len(day_wins),
        }

        result = HierarchyResult(
            era_windows=era_wins,
            month_windows=month_wins,
            day_windows=day_wins,
            resolution_facet=facet,
        )

        assert result.resolution_facet == {"era": 1, "month": 3, "day": 7}

    def test_resolution_facet_from_builder(self):
        """build_resolution_hierarchy produces correct facet counts end-to-end."""
        # Patch find_threshold_crossings to return one era-length interval (500d).
        # Also patch _eval_single to return a constant above threshold.
        era_interval = _make_interval(enter_jd=0.0, exit_jd=500.0, peak_lambda=0.9)

        with patch(
            "services.gochara_v3.resolution_hierarchy.find_threshold_crossings",
            return_value=[era_interval],
        ), patch(
            "services.gochara_v3.resolution_hierarchy._eval_single",
            return_value=0.8,
        ):
            swe = MagicMock()
            context = MagicMock()
            config = _make_threshold_config(lambda_thresh=0.5)

            result = build_resolution_hierarchy(swe, context, 0.0, 1000.0, config)

        # Should have 1 era window
        assert result.resolution_facet["era"] == 1
        assert result.resolution_facet["era"] == len(result.era_windows)
        assert result.resolution_facet["month"] == len(result.month_windows)
        assert result.resolution_facet["day"] == len(result.day_windows)

        # Facet counts must be non-negative
        for tier, count in result.resolution_facet.items():
            assert count >= 0, f"facet count for {tier} must be >= 0, got {count}"
