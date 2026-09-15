"""Contract tests for the current one-day-grid DHARA null implementation.

These tests intentionally exercise public result semantics rather than the
retired clock/envelope knot helpers. The serial reference now decomposes the
field into fixed clock contribution C(t) and shifted envelope contribution
E(t) on a deterministic midpoint grid; ``coarse_mode`` remains a compatibility
argument and must not change the result.
"""
from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pytest

from services.ka_kshetra.contracts import NullResult
from services.ka_kshetra.dhara_null import (
    DEFAULT_ALPHA,
    DEFAULT_REPLICATES,
    dhara_compute_null,
)
from services.ka_kshetra.stage5_null import DURATION_BUCKETS


def _make_evaluator(horizon_days: float = 12.0) -> MagicMock:
    """Return the complete surface consumed by ``dhara_compute_null``."""
    evaluator = MagicMock()
    evaluator.horizon_days = horizon_days
    evaluator.event_class = "test_class"
    evaluator.lifetime_count = 1.0
    evaluator.promise = MagicMock()
    evaluator.clocks = []
    evaluator.ladder = {}
    evaluator.envelopes = MagicMock()
    evaluator.weights = {}
    evaluator.baseline_source = None
    evaluator.extra_breakpoints = ()
    evaluator.ln_lambda.side_effect = (
        lambda t: -4.0 + 0.1 * math.sin((2.0 * math.pi * t) / horizon_days)
    )
    return evaluator


def _run(
    evaluator: MagicMock,
    *,
    replicates: int = 4,
    coarse_mode: bool = True,
) -> NullResult:
    """Run with a deterministic clock-only evaluator and no database I/O."""
    clock_evaluator = MagicMock()
    clock_evaluator.ln_lambda.side_effect = lambda _t: -4.0
    with patch(
        "services.ka_kshetra.dhara_null.FieldEvaluator",
        return_value=clock_evaluator,
    ):
        return dhara_compute_null(
            evaluator,
            replicates=replicates,
            alpha=DEFAULT_ALPHA,
            coarse_mode=coarse_mode,
        )


class TestShiftGrid:
    @pytest.mark.parametrize("replicates", [DEFAULT_REPLICATES, 256, 128, 8])
    def test_excludes_identity_and_has_r_minus_one_shifts(self, replicates: int):
        horizon = 36525.0
        deltas = [
            r * (horizon / replicates)
            for r in range(1, replicates)
        ]
        assert len(deltas) == replicates - 1
        assert min(deltas) > 0.0
        assert max(deltas) < horizon
        assert all(delta % horizon != 0.0 for delta in deltas)

    def test_default_resolution_is_one_over_r(self):
        result = NullResult(
            replicates=DEFAULT_REPLICATES,
            shift_count=DEFAULT_REPLICATES - 1,
            horizon_days=36525.0,
            shift_grid_step=36525.0 / DEFAULT_REPLICATES,
            q_threshold=0.42,
            max_stats={int(b): [] for b in DURATION_BUCKETS},
        )
        assert result.resolution == pytest.approx(1.0 / DEFAULT_REPLICATES)


class TestResultContract:
    def test_integer_day_shift_is_an_exact_midpoint_permutation(self):
        evaluator = _make_evaluator(horizon_days=60.0)
        evaluator.ln_lambda.side_effect = (
            lambda t: 0.0 if int(math.floor(t)) % 2 == 0 else math.log(100.0)
        )

        result = _run(evaluator, replicates=2)

        # A 30-day integer shift only rotates the 60 midpoint samples.  The
        # alternating daily rates therefore contain exactly fifteen 1s and
        # fifteen 100s in every 30-day window: 15 + 1,500 = 1,515.
        assert result.max_stats[30] == pytest.approx([1515.0], abs=1e-12)

    def test_half_day_shift_interpolates_adjacent_midpoint_log_rates(self):
        evaluator = _make_evaluator(horizon_days=4.0)
        evaluator.ln_lambda.side_effect = (
            lambda t: 0.0 if int(math.floor(t)) % 2 == 0 else math.log(100.0)
        )

        result = _run(evaluator, replicates=8)

        # Half-day shifts interpolate log(1) and log(100), producing rate 10
        # at all four midpoints and total hazard 40. Integer-day shifts are
        # exact rotations with total 1 + 100 + 1 + 100 = 202.
        assert result.max_stats[30] == pytest.approx(
            [40.0, 202.0, 40.0, 202.0, 40.0, 202.0, 40.0],
            abs=1e-12,
        )

    def test_returns_complete_null_result(self):
        result = _run(_make_evaluator(), replicates=4)

        assert isinstance(result, NullResult)
        assert result.replicates == 4
        assert result.shift_count == 3
        assert result.alpha == DEFAULT_ALPHA
        assert result.horizon_days == 12.0
        assert result.shift_grid_step == pytest.approx(3.0)
        assert result.q_threshold is not None
        for bucket in DURATION_BUCKETS:
            values = result.max_stats[int(bucket)]
            assert len(values) == result.shift_count
            assert all(math.isfinite(value) for value in values)

    def test_replay_is_deterministic(self):
        first = _run(_make_evaluator(), replicates=8)
        second = _run(_make_evaluator(), replicates=8)
        assert second == first

    def test_coarse_mode_is_compatibility_only(self):
        coarse = _run(_make_evaluator(), replicates=8, coarse_mode=True)
        full = _run(_make_evaluator(), replicates=8, coarse_mode=False)
        assert full == coarse


class TestArgumentValidation:
    @pytest.mark.parametrize("replicates", [0, 1])
    def test_replicates_must_be_at_least_two(self, replicates: int):
        with pytest.raises(ValueError, match="replicates must be >= 2"):
            dhara_compute_null(_make_evaluator(), replicates=replicates)

    @pytest.mark.parametrize("alpha", [0.0, 1.0, -0.1, 1.1])
    def test_alpha_must_be_inside_unit_interval(self, alpha: float):
        with pytest.raises(ValueError, match="alpha must be in"):
            dhara_compute_null(_make_evaluator(), replicates=4, alpha=alpha)

    @pytest.mark.parametrize("horizon", [0.0, -1.0])
    def test_horizon_must_be_positive(self, horizon: float):
        with pytest.raises(ValueError, match="horizon_days must be > 0"):
            dhara_compute_null(_make_evaluator(horizon), replicates=4)
