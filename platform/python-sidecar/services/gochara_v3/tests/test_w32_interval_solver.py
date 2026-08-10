"""
Test W3.2 — Root-solved interval production and chain milestone scoring.

Tests for gochara_v3.interval_solver:

  TestFindThresholdCrossings:
    1. test_single_interval_detected — lambda above threshold for days 5-15 of
       a 30-day range; verifies enter≈5, exit≈15, peak within [5,15].
    2. test_no_interval_when_always_below — lambda always 0.05 (below threshold);
       verifies empty list.
    3. test_two_intervals_detected — two separate above-threshold episodes;
       verifies 2 IntervalBoundary results.

  TestScoreChainMilestones:
    4. test_milestones_scored_at_own_jd — each milestone uses its own JD
       (anchor + offset), not the anchor alone.
    5. test_empty_milestone_template — returns empty list (I4 honest null).
    6. test_irreversibility_flag — a milestone with is_irreversibility_milestone=True
       is flagged correctly.

All tests use unittest.mock.patch to mock engine calls — DB-free, ephemeris-free.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.gochara_v3.interval_solver import (
    ERA_SLICE_KEY_V3,
    IntervalBoundary,
    MilestoneScore,
    find_threshold_crossings,
    score_chain_milestones,
)
from services.gochara_v3.threshold import ThresholdConfig


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

# Base JD for tests: arbitrary but stable (roughly 2026-01-01 noon)
_BASE_JD = 2461042.0


def _make_threshold_config(lambda_thresh: float = 0.30) -> ThresholdConfig:
    """Build a minimal ThresholdConfig for test use."""
    return ThresholdConfig(
        percentile_used=0.80,
        lambda_thresh=lambda_thresh,
        implied_density=10.0,
        base_rate_cited=0.20,
        age_band_used="band_41_60",
        density_flag="ok",
        fallback_used=False,
        sample_count=5200,
    )


def _make_mock_context():
    """Build a minimal mock ClassContext."""
    ctx = MagicMock()
    ctx.event_class = "marriage"
    ctx.chart_id = "test-chart-id"
    return ctx


def _make_mock_intensity_result(raw_lambda: float, jd: float):
    """Build a mock IntensityResult with the given raw_lambda and t_jd."""
    result = MagicMock()
    result.raw_lambda = raw_lambda
    result.t_jd = jd
    return result


def _make_evaluate_lambda_vector_side_effect(lambda_fn):
    """
    Returns a side_effect function for mocking evaluate_lambda_vector.

    lambda_fn(jd) -> float: the lambda value at a given JD.

    The mock will return [MockIntensityResult(raw_lambda=lambda_fn(jd))]
    for a single-element jd_array.
    """
    def side_effect(swe, context, jd_array, v1_parity_mode=False, **kwargs):
        results = []
        for jd in jd_array:
            lam = lambda_fn(float(jd))
            results.append(_make_mock_intensity_result(lam, float(jd)))
        return results
    return side_effect


# ---------------------------------------------------------------------------
# TestFindThresholdCrossings
# ---------------------------------------------------------------------------

class TestFindThresholdCrossings:
    """Tests for find_threshold_crossings (bisection root-solver)."""

    def test_single_interval_detected(self):
        """Lambda is above threshold for days 5–15 of a 30-day range.

        With threshold=0.30, we use a lambda function that:
          - returns 0.05 for jd < base+5 and jd > base+15
          - returns 0.80 for base+5 <= jd <= base+15

        We expect exactly one IntervalBoundary with:
          - enter_jd close to base+5 (within bisect tolerance 0.1 days)
          - exit_jd close to base+15 (within bisect tolerance 0.1 days)
          - peak_jd within [enter_jd, exit_jd]
          - peak_lambda ≈ 0.80
          - era_slice_key == ERA_SLICE_KEY_V3
        """
        base_jd = _BASE_JD
        threshold_config = _make_threshold_config(lambda_thresh=0.30)
        context = _make_mock_context()
        swe = MagicMock()

        def lambda_fn(jd: float) -> float:
            day_offset = jd - base_jd
            if 5.0 <= day_offset <= 15.0:
                return 0.80
            return 0.05

        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
            side_effect=_make_evaluate_lambda_vector_side_effect(lambda_fn),
        ):
            intervals = find_threshold_crossings(
                swe, context,
                start_jd=base_jd,
                end_jd=base_jd + 30.0,
                threshold_config=threshold_config,
                coarse_step_days=1.0,   # daily for precision in test
                bisect_tol_days=0.1,
            )

        assert len(intervals) == 1, (
            f"Expected exactly 1 interval, got {len(intervals)}: {intervals}"
        )
        iv = intervals[0]

        # enter_jd should be within 0.5 days of base_jd + 5
        assert abs(iv.enter_jd - (base_jd + 5.0)) < 0.5, (
            f"enter_jd={iv.enter_jd:.4f} not close to base+5={base_jd+5.0:.4f}"
        )
        # exit_jd should be within 0.5 days of base_jd + 15
        assert abs(iv.exit_jd - (base_jd + 15.0)) < 0.5, (
            f"exit_jd={iv.exit_jd:.4f} not close to base+15={base_jd+15.0:.4f}"
        )
        # peak_jd must be within [enter_jd, exit_jd]
        assert iv.enter_jd <= iv.peak_jd <= iv.exit_jd, (
            f"peak_jd={iv.peak_jd:.4f} not in [{iv.enter_jd:.4f}, {iv.exit_jd:.4f}]"
        )
        # peak_lambda should be approximately 0.80
        assert iv.peak_lambda == pytest.approx(0.80, abs=0.05), (
            f"peak_lambda={iv.peak_lambda} not close to 0.80"
        )
        # era_slice_key must be the v3 constant
        assert iv.era_slice_key == ERA_SLICE_KEY_V3, (
            f"era_slice_key={iv.era_slice_key!r} != {ERA_SLICE_KEY_V3!r}"
        )

    def test_no_interval_when_always_below(self):
        """Lambda always 0.05 — never crosses threshold 0.30 → empty list."""
        base_jd = _BASE_JD
        threshold_config = _make_threshold_config(lambda_thresh=0.30)
        context = _make_mock_context()
        swe = MagicMock()

        def lambda_fn(jd: float) -> float:
            return 0.05  # always below 0.30

        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
            side_effect=_make_evaluate_lambda_vector_side_effect(lambda_fn),
        ):
            intervals = find_threshold_crossings(
                swe, context,
                start_jd=base_jd,
                end_jd=base_jd + 30.0,
                threshold_config=threshold_config,
                coarse_step_days=1.0,
                bisect_tol_days=0.1,
            )

        assert intervals == [], (
            f"Expected empty list when lambda always below threshold, got {intervals}"
        )

    def test_two_intervals_detected(self):
        """Two separate above-threshold episodes → exactly 2 IntervalBoundary results.

        Episode 1: days 3–7 (lambda=0.80 above thresh=0.30)
        Episode 2: days 18–25 (lambda=0.75 above thresh=0.30)
        """
        base_jd = _BASE_JD
        threshold_config = _make_threshold_config(lambda_thresh=0.30)
        context = _make_mock_context()
        swe = MagicMock()

        def lambda_fn(jd: float) -> float:
            day_offset = jd - base_jd
            if 3.0 <= day_offset <= 7.0:
                return 0.80
            if 18.0 <= day_offset <= 25.0:
                return 0.75
            return 0.05

        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
            side_effect=_make_evaluate_lambda_vector_side_effect(lambda_fn),
        ):
            intervals = find_threshold_crossings(
                swe, context,
                start_jd=base_jd,
                end_jd=base_jd + 30.0,
                threshold_config=threshold_config,
                coarse_step_days=1.0,
                bisect_tol_days=0.1,
            )

        assert len(intervals) == 2, (
            f"Expected 2 intervals for 2 episodes, got {len(intervals)}: {intervals}"
        )

        # Intervals should be in chronological order
        assert intervals[0].enter_jd < intervals[1].enter_jd, (
            "Intervals should be sorted by enter_jd"
        )

        # First interval peak should be near day 5 (midpoint of days 3–7)
        assert base_jd + 2.0 <= intervals[0].peak_jd <= base_jd + 8.0, (
            f"First interval peak_jd={intervals[0].peak_jd:.4f} not near days 3–7"
        )

        # Second interval peak should be near day 21 (midpoint of days 18–25)
        assert base_jd + 17.0 <= intervals[1].peak_jd <= base_jd + 26.0, (
            f"Second interval peak_jd={intervals[1].peak_jd:.4f} not near days 18–25"
        )

        # Both should carry the v3 era_slice_key
        for iv in intervals:
            assert iv.era_slice_key == ERA_SLICE_KEY_V3


# ---------------------------------------------------------------------------
# TestScoreChainMilestones
# ---------------------------------------------------------------------------

class TestScoreChainMilestones:
    """Tests for score_chain_milestones (chain milestone scoring)."""

    def test_milestones_scored_at_own_jd(self):
        """Each milestone is evaluated at its own JD (anchor + offset), not anchor alone.

        Template: 3 milestones with offsets 0, 30, 90 days.
        We verify by checking that the evaluate_lambda_vector mock receives
        JDs matching (anchor + offset) for each milestone.
        """
        anchor_jd = _BASE_JD
        threshold_config = _make_threshold_config(lambda_thresh=0.30)
        context = _make_mock_context()
        swe = MagicMock()

        milestone_template = [
            {"milestone_id": "onset", "typical_offset_days": 0.0,
             "is_irreversibility_milestone": False},
            {"milestone_id": "commitment", "typical_offset_days": 30.0,
             "is_irreversibility_milestone": False},
            {"milestone_id": "completion", "typical_offset_days": 90.0,
             "is_irreversibility_milestone": True},
        ]

        # Track which JDs were passed to evaluate_lambda_vector
        called_jds: list[float] = []

        def lambda_fn(jd: float) -> float:
            called_jds.append(jd)
            # Vary lambda by offset from anchor to verify per-milestone evaluation
            offset = jd - anchor_jd
            if offset < 1.0:
                return 0.40   # onset: above threshold
            elif offset < 60.0:
                return 0.25   # commitment: below threshold
            else:
                return 0.55   # completion: above threshold

        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
            side_effect=_make_evaluate_lambda_vector_side_effect(lambda_fn),
        ):
            scores = score_chain_milestones(
                swe, context, anchor_jd, milestone_template, threshold_config,
            )

        assert len(scores) == 3, f"Expected 3 scores, got {len(scores)}"

        # Verify milestone_jd values match anchor + offset
        assert scores[0].milestone_jd == pytest.approx(anchor_jd + 0.0, abs=1e-6)
        assert scores[1].milestone_jd == pytest.approx(anchor_jd + 30.0, abs=1e-6)
        assert scores[2].milestone_jd == pytest.approx(anchor_jd + 90.0, abs=1e-6)

        # Verify evaluate_lambda_vector was called with the three distinct JDs
        assert len(called_jds) == 3, (
            f"Expected 3 evaluate_lambda_vector calls, got {len(called_jds)}"
        )
        assert pytest.approx(anchor_jd + 0.0, abs=1e-6) in [
            pytest.approx(jd, abs=1e-6) for jd in called_jds
        ], "Anchor JD not called"
        assert pytest.approx(anchor_jd + 30.0, abs=1e-6) in [
            pytest.approx(jd, abs=1e-6) for jd in called_jds
        ], "Offset +30 JD not called"
        assert pytest.approx(anchor_jd + 90.0, abs=1e-6) in [
            pytest.approx(jd, abs=1e-6) for jd in called_jds
        ], "Offset +90 JD not called"

        # Verify threshold gating
        assert scores[0].is_above_threshold is True, (
            "onset (lambda=0.40 > thresh=0.30) should be above threshold"
        )
        assert scores[1].is_above_threshold is False, (
            "commitment (lambda=0.25 < thresh=0.30) should be below threshold"
        )
        assert scores[2].is_above_threshold is True, (
            "completion (lambda=0.55 > thresh=0.30) should be above threshold"
        )

    def test_empty_milestone_template(self):
        """Empty milestone template → returns [] (I4: honest null, no fabrication)."""
        anchor_jd = _BASE_JD
        threshold_config = _make_threshold_config()
        context = _make_mock_context()
        swe = MagicMock()

        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
        ) as mock_eval:
            scores = score_chain_milestones(
                swe, context, anchor_jd, [], threshold_config,
            )

        assert scores == [], (
            f"Expected empty list for empty milestone_template, got {scores}"
        )
        # evaluate_lambda_vector must never be called for an empty template
        mock_eval.assert_not_called()

    def test_irreversibility_flag(self):
        """A milestone with is_irreversibility_milestone=True is flagged correctly."""
        anchor_jd = _BASE_JD
        threshold_config = _make_threshold_config(lambda_thresh=0.30)
        context = _make_mock_context()
        swe = MagicMock()

        milestone_template = [
            {"milestone_id": "onset", "typical_offset_days": 0.0,
             "is_irreversibility_milestone": False},
            {"milestone_id": "point_of_no_return", "typical_offset_days": 45.0,
             "is_irreversibility_milestone": True},
            {"milestone_id": "close", "typical_offset_days": 120.0,
             "is_irreversibility_milestone": False},
        ]

        def lambda_fn(jd: float) -> float:
            return 0.50  # all milestones above threshold

        with patch(
            "services.gochara_v3.interval_solver.evaluate_lambda_vector",
            side_effect=_make_evaluate_lambda_vector_side_effect(lambda_fn),
        ):
            scores = score_chain_milestones(
                swe, context, anchor_jd, milestone_template, threshold_config,
            )

        assert len(scores) == 3

        # Verify irreversibility flags
        assert scores[0].is_irreversibility_milestone is False, (
            "onset should not be an irreversibility milestone"
        )
        assert scores[1].is_irreversibility_milestone is True, (
            "point_of_no_return should be flagged as irreversibility milestone"
        )
        assert scores[2].is_irreversibility_milestone is False, (
            "close should not be an irreversibility milestone"
        )

        # Verify milestone IDs are preserved correctly
        assert scores[0].milestone_id == "onset"
        assert scores[1].milestone_id == "point_of_no_return"
        assert scores[2].milestone_id == "close"

        # All above threshold (lambda=0.50 > thresh=0.30)
        for score in scores:
            assert score.is_above_threshold is True, (
                f"milestone {score.milestone_id}: lambda=0.50 should be above thresh=0.30"
            )
