"""Compatibility and arithmetic tests for the historical DHARA vec API."""
from __future__ import annotations

import math
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from services.ka_kshetra.contracts import NullResult, Segment
from services.ka_kshetra.dhara_null import dhara_compute_null
from services.ka_kshetra.dhara_null_vec import (
    DEFAULT_ALPHA,
    DEFAULT_REPLICATES,
    _cumulative_on_grid_numpy,
    _vec_sliding_window_max,
    dhara_compute_null_vec,
)
from services.ka_kshetra.stage5_null import (
    DURATION_BUCKETS,
    cumulative_on_grid,
    sliding_window_max,
)


def _segment(start: float, end: float, alpha: float) -> Segment:
    return Segment(
        index=0,
        t_start=start,
        t_end=end,
        alpha=alpha,
        gamma=0.0,
        refinement_depth=0,
        refinement_exhausted=False,
        refinement_residual=None,
    )


def _evaluator(horizon_days: float = 24.0) -> MagicMock:
    evaluator = MagicMock()
    evaluator.horizon_days = horizon_days
    evaluator.event_class = "compatibility_test"
    evaluator.lifetime_count = 1.0
    evaluator.promise = MagicMock()
    evaluator.clocks = []
    evaluator.ladder = {}
    evaluator.envelopes = MagicMock()
    evaluator.weights = {}
    evaluator.baseline_source = None
    evaluator.extra_breakpoints = ()
    evaluator.ln_lambda.side_effect = (
        lambda t: -4.0 + 0.2 * math.sin((2.0 * math.pi * t) / horizon_days)
    )
    return evaluator


def _run_serial_or_compat(fn, evaluator, *, replicates: int):
    clock_evaluator = MagicMock()
    clock_evaluator.ln_lambda.side_effect = lambda _t: -4.0
    with patch(
        "services.ka_kshetra.dhara_null.FieldEvaluator",
        return_value=clock_evaluator,
    ):
        if fn is dhara_compute_null_vec:
            return fn(evaluator, R=replicates, alpha=DEFAULT_ALPHA)
        return fn(evaluator, replicates=replicates, alpha=DEFAULT_ALPHA)


class TestCumulativeHelper:
    @pytest.mark.parametrize(
        "segments",
        [
            [_segment(0.0, 100.0, -3.0)],
            [_segment(0.0, 50.0, -4.0), _segment(50.0, 100.0, -3.0)],
            [],
        ],
    )
    def test_matches_serial_helper(self, segments):
        expected = cumulative_on_grid(segments, 100.0, grid_step=1.0)
        actual = _cumulative_on_grid_numpy(segments, 100.0, grid_step=1.0)
        assert np.asarray(actual) == pytest.approx(expected, abs=1e-12)


class TestSlidingWindowHelper:
    @pytest.mark.parametrize("bucket", list(DURATION_BUCKETS))
    def test_matches_serial_helper(self, bucket: int):
        cumulative = np.cumsum(np.linspace(0.001, 0.01, 366))
        expected = sliding_window_max(cumulative.tolist(), bucket)
        actual = _vec_sliding_window_max(cumulative, bucket)
        assert actual == pytest.approx(expected, abs=1e-12)

    def test_bucket_larger_than_horizon_returns_total(self):
        cumulative = np.array([0.0, 0.5, 1.0, 1.5])
        assert _vec_sliding_window_max(cumulative, 1000) == 1.5


class TestCompatibilityEntryPoint:
    @pytest.mark.parametrize("replicates", [4, 8])
    def test_is_exactly_the_active_ce_engine(self, replicates: int):
        serial = _run_serial_or_compat(
            dhara_compute_null,
            _evaluator(),
            replicates=replicates,
        )
        compatibility = _run_serial_or_compat(
            dhara_compute_null_vec,
            _evaluator(),
            replicates=replicates,
        )
        assert compatibility == serial
        assert compatibility.shift_count == replicates - 1
        assert compatibility.resolution == pytest.approx(1.0 / replicates)

    def test_forwards_legacy_argument_names_without_semantic_translation(self):
        expected = NullResult(
            replicates=8,
            shift_count=7,
            horizon_days=24.0,
            shift_grid_step=3.0,
            q_threshold=0.5,
            max_stats={int(bucket): [1.0] * 7 for bucket in DURATION_BUCKETS},
            alpha=0.1,
        )
        evaluator = _evaluator()
        with patch(
            "services.ka_kshetra.dhara_null.dhara_compute_null",
            return_value=expected,
        ) as active:
            actual = dhara_compute_null_vec(
                evaluator,
                R=8,
                alpha=0.1,
                coarse_mode=False,
            )
        assert actual is expected
        active.assert_called_once_with(
            evaluator,
            replicates=8,
            alpha=0.1,
            coarse_mode=False,
        )

    def test_default_replicates_remains_1024(self):
        assert DEFAULT_REPLICATES == 1024


@pytest.mark.perf
def test_r1024_compatibility_path_under_120_seconds():
    evaluator = _evaluator(horizon_days=36525.0)
    started = time.perf_counter()
    result = _run_serial_or_compat(
        dhara_compute_null_vec,
        evaluator,
        replicates=DEFAULT_REPLICATES,
    )
    elapsed = time.perf_counter() - started

    assert elapsed <= 120.0
    assert result.replicates == DEFAULT_REPLICATES
    assert result.shift_count == DEFAULT_REPLICATES - 1
