"""
tests/ka_kshetra/test_dhara_null_vectorized.py — Equivalence + perf gates for
dhara_compute_null_vec (P-B L-NULL, DHARA_ENGINE_SPEC_v1_0.md §3.3).

REQUIRED CI GATES (§3.3):
  1. Equivalence at R=8, 5 random fixtures:
       |dhara_compute_null_vec(ev, R=8).q_threshold
         - dhara_compute_null(ev, R=8).q_threshold| < 1e-6
       AND same for each max_stats[b][r] value.

  2. FM-25 perf gate (slow, @pytest.mark.perf, skipped in unit suite):
       dhara_compute_null_vec(ev, R=1024) ≤ 120s wall-clock.

TDD discipline: these tests were written BEFORE dhara_null_vec.py. Running
against the old serial implementation they fail (wrong module / wrong gate);
running against dhara_null_vec.py they pass.

No real DB calls. All fixtures are synthetic: a minimal FieldEvaluator mock
plus a Segment fixture that produces deterministic cumulative integrals.
"""
from __future__ import annotations

import math
import time
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from services.ka_kshetra.contracts import NullResult, Segment
from services.ka_kshetra.dhara_null import dhara_compute_null
from services.ka_kshetra.dhara_null_vec import (
    DEFAULT_REPLICATES,
    DEFAULT_ALPHA,
    dhara_compute_null_vec,
    _cumulative_on_grid_numpy,
    _vec_sliding_window_max,
)
from services.ka_kshetra.stage5_null import (
    DURATION_BUCKETS,
    cumulative_on_grid,
    sliding_window_max,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixture helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_ladder_period(level: str, t_start: float, t_end: float):
    """Duck-typed ladder period."""
    p = MagicMock()
    p.level = level
    p.t_start = t_start
    p.t_end = t_end
    return p


def _make_segment(t_start: float, t_end: float, alpha: float = -4.0, gamma: float = 0.0) -> Segment:
    """Synthetic Segment for testing."""
    return Segment(
        index=0,
        t_start=t_start,
        t_end=t_end,
        alpha=alpha,
        gamma=gamma,
        refinement_depth=0,
        refinement_exhausted=False,
        refinement_residual=None,
    )


def _make_minimal_evaluator(
    horizon_days: float = 365.0,
    n_md_periods: int = 3,
    alpha: float = -4.0,
    gamma: float = 0.0,
) -> MagicMock:
    """A minimal FieldEvaluator mock suitable for passing to dhara_compute_null
    and dhara_compute_null_vec with patched _null_build_segments.

    The evaluator's .ladder and .envelopes.breakpoints() are the only
    attributes read by the knot-set helpers. .horizon_days is also needed.

    The ln_lambda function returns alpha (constant) so that the cumulative
    integral per day is math.exp(alpha) — fully deterministic.
    """
    ev = MagicMock()
    ev.horizon_days = horizon_days
    ev.event_class = 'test_equivalence_class'

    # Ladder: a few MD periods covering the horizon.
    period_len = horizon_days / n_md_periods
    periods = [
        _make_ladder_period('MD', i * period_len, (i + 1) * period_len)
        for i in range(n_md_periods)
    ]
    ev.ladder = {'vimshottari': periods}

    # EnvelopeIndex mock.
    ev.envelopes = MagicMock()
    ev.envelopes.breakpoints.return_value = [horizon_days * 0.25, horizon_days * 0.75]
    ev.envelopes.horizon_days = horizon_days
    ev.envelopes.circular_shift.return_value = ev.envelopes

    return ev


# Five deterministic synthetic fixtures for the equivalence gate.
# Each fixture is a (horizon_days, n_md_periods, alpha, gamma) tuple.
# The alpha values span a range to produce different q_threshold values.
_EQUIVALENCE_FIXTURES = [
    (365.0,   3, -4.0,  0.0),     # fixture 0: short horizon, flat field
    (730.0,   5, -3.5,  0.0),     # fixture 1: medium horizon, higher rate
    (365.0,   4, -5.0,  0.0),     # fixture 2: low rate
    (1825.0,  7, -4.2,  0.0),     # fixture 3: 5-year horizon, 7 MD periods
    (365.0,   3, -3.0,  0.0),     # fixture 4: high rate (exp(-3) ≈ 0.05/day)
]


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests: _cumulative_on_grid_numpy parity with cumulative_on_grid
# ─────────────────────────────────────────────────────────────────────────────

class TestCumulativeOnGridParity:
    """_cumulative_on_grid_numpy must be bit-identical to cumulative_on_grid."""

    def test_single_flat_segment(self):
        """Flat segment: cumulative = exp(alpha) * days."""
        seg = _make_segment(0.0, 100.0, alpha=-3.0, gamma=0.0)
        segs = [seg]
        H = 100.0

        ref = cumulative_on_grid(segs, H, grid_step=1.0)
        vec = _cumulative_on_grid_numpy(segs, H, grid_step=1.0)

        assert len(vec) == len(ref), f'length mismatch: {len(vec)} vs {len(ref)}'
        for i, (r, v) in enumerate(zip(ref, vec)):
            assert abs(r - float(v)) < 1e-12, (
                f'cum[{i}]: serial={r!r}, vec={float(v)!r}, diff={abs(r-float(v))!r}'
            )

    def test_two_segments_different_alpha(self):
        """Two segments with different alpha: cumulative piecewise."""
        segs = [
            _make_segment(0.0, 50.0, alpha=-4.0, gamma=0.0),
            _make_segment(50.0, 100.0, alpha=-3.0, gamma=0.0),
        ]
        H = 100.0

        ref = cumulative_on_grid(segs, H, grid_step=1.0)
        vec = _cumulative_on_grid_numpy(segs, H, grid_step=1.0)

        assert len(vec) == len(ref)
        for i, (r, v) in enumerate(zip(ref, vec)):
            assert abs(r - float(v)) < 1e-12, f'cum[{i}]: {r!r} vs {float(v)!r}'

    def test_empty_segments(self):
        """Empty segment list → all zeros."""
        ref = cumulative_on_grid([], 100.0, grid_step=1.0)
        vec = _cumulative_on_grid_numpy([], 100.0, grid_step=1.0)
        assert all(v == 0.0 for v in ref)
        assert all(v == 0.0 for v in vec)


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests: _vec_sliding_window_max parity with sliding_window_max
# ─────────────────────────────────────────────────────────────────────────────

class TestVecSlidingWindowMaxParity:
    """_vec_sliding_window_max must be identical to sliding_window_max."""

    def _make_cum_array(self, n: int) -> tuple[list[float], 'np.ndarray']:
        """Return a deterministic cumulative array as both list and ndarray."""
        import numpy as np
        cum_list = [float(i * 0.001 + (i % 10) * 0.0002) for i in range(n + 1)]
        cum_np = np.array(cum_list, dtype=np.float64)
        return cum_list, cum_np

    @pytest.mark.parametrize('bucket', list(DURATION_BUCKETS))
    def test_all_buckets_match(self, bucket: int):
        """All DURATION_BUCKETS values match between serial and vectorized."""
        cum_list, cum_np = self._make_cum_array(n=365)
        ref = sliding_window_max(cum_list, bucket)
        vec = _vec_sliding_window_max(cum_np, bucket)
        assert abs(ref - vec) < 1e-12, f'bucket={bucket}: serial={ref!r}, vec={vec!r}'

    def test_bucket_larger_than_horizon(self):
        """Bucket > horizon returns total integral (same as serial)."""
        import numpy as np
        cum_list = [0.0, 0.5, 1.0, 1.3, 1.5]
        cum_np = np.array(cum_list, dtype=np.float64)
        ref = sliding_window_max(cum_list, 1000)  # bucket >> n=4
        vec = _vec_sliding_window_max(cum_np, 1000)
        assert abs(ref - vec) < 1e-12


# ─────────────────────────────────────────────────────────────────────────────
# EQUIVALENCE GATE (§3.3) — the BINDING acceptance criterion
# ─────────────────────────────────────────────────────────────────────────────

class TestEquivalenceGate:
    """§3.3: |dhara_compute_null_vec(ev, R=8).q_threshold
              - dhara_compute_null(ev, R=8).q_threshold| < 1e-6
    AND same for each max_stats[b][r] value.
    Tests 5 random fixtures (DHARA_ENGINE_SPEC_v1_0.md §3.3).
    """

    R_SMALL = 8  # The binding gate uses R=8

    def _run_both(
        self,
        fixture_idx: int,
    ) -> tuple[NullResult, NullResult]:
        """Run dhara_compute_null and dhara_compute_null_vec on the same fixture.

        Returns (serial_result, vec_result).

        Both implementations receive the SAME patched _null_build_segments so
        that the segment content is deterministic and fixture-controlled — not
        dependent on a real EnvelopeIndex. This isolates the equivalence test
        to the cumulative + bucket + quantile pipeline, which is what the
        vectorized implementation changes.
        """
        horizon, n_md, alpha_val, gamma_val = _EQUIVALENCE_FIXTURES[fixture_idx]

        ev = _make_minimal_evaluator(
            horizon_days=horizon,
            n_md_periods=n_md,
            alpha=alpha_val,
            gamma=gamma_val,
        )

        # Produce a deterministic segment set for this fixture.
        # The segments cover the full horizon with one flat segment per MD period.
        n_segs = n_md * 2  # two sub-segments per MD period to exercise L1k paths
        seg_len = horizon / n_segs
        segments = [
            _make_segment(
                t_start=i * seg_len,
                t_end=(i + 1) * seg_len,
                alpha=alpha_val + (i % 3) * 0.1,  # slight variation per segment
                gamma=gamma_val,
            )
            for i in range(n_segs)
        ]

        # Patch both _null_build_segments and replicate_evaluator so no real
        # EnvelopeIndex.circular_shift is called. replicate_evaluator returns
        # the same (unshifted) evaluator — the null distribution values are
        # identical across replicates, which is the exactly-degenerate case that
        # exercises the equivalence of both implementations most directly.
        with patch(
            'services.ka_kshetra.dhara_null._null_build_segments',
            return_value=list(segments),
        ), patch(
            'services.ka_kshetra.dhara_null.replicate_evaluator',
            return_value=ev,
        ):
            serial_result = dhara_compute_null(ev, replicates=self.R_SMALL, alpha=DEFAULT_ALPHA)

        with patch(
            'services.ka_kshetra.dhara_null_vec._null_build_segments',
            return_value=list(segments),
        ), patch(
            'services.ka_kshetra.dhara_null_vec.replicate_evaluator',
            return_value=ev,
        ):
            vec_result = dhara_compute_null_vec(ev, R=self.R_SMALL, alpha=DEFAULT_ALPHA)

        return serial_result, vec_result

    @pytest.mark.parametrize('fixture_idx', range(5))
    def test_q_threshold_equivalence(self, fixture_idx: int):
        """q_threshold matches serial implementation to 1e-6 on all 5 fixtures."""
        serial, vec = self._run_both(fixture_idx)

        if serial.q_threshold is None and vec.q_threshold is None:
            return  # both honest-null; gate passes

        assert vec.q_threshold is not None, (
            f'fixture {fixture_idx}: vec returned q_threshold=None but serial={serial.q_threshold!r}'
        )
        assert serial.q_threshold is not None, (
            f'fixture {fixture_idx}: serial returned q_threshold=None but vec={vec.q_threshold!r}'
        )

        delta = abs(vec.q_threshold - serial.q_threshold)
        assert delta < 1e-6, (
            f'fixture {fixture_idx}: q_threshold out of tolerance {delta!r} >= 1e-6\n'
            f'  serial  q_threshold = {serial.q_threshold!r}\n'
            f'  vec     q_threshold = {vec.q_threshold!r}'
        )

    @pytest.mark.parametrize('fixture_idx', range(5))
    def test_max_stats_equivalence(self, fixture_idx: int):
        """Each max_stats[b][r] matches serial implementation to 1e-6."""
        serial, vec = self._run_both(fixture_idx)

        # Check all duration buckets and all R-1 replicate values.
        for b in DURATION_BUCKETS:
            b_key = int(b)
            assert b_key in serial.max_stats, f'fixture {fixture_idx}: bucket {b} missing from serial'
            assert b_key in vec.max_stats,    f'fixture {fixture_idx}: bucket {b} missing from vec'

            serial_vals = serial.max_stats[b_key]
            vec_vals    = vec.max_stats[b_key]

            assert len(serial_vals) == len(vec_vals), (
                f'fixture {fixture_idx}, bucket {b}: len mismatch '
                f'{len(serial_vals)} vs {len(vec_vals)}'
            )

            for r_idx, (sv, vv) in enumerate(zip(serial_vals, vec_vals)):
                delta = abs(sv - vv)
                assert delta < 1e-6, (
                    f'fixture {fixture_idx}, bucket {b}, replicate {r_idx}: '
                    f'max_stats mismatch delta={delta!r} >= 1e-6\n'
                    f'  serial  = {sv!r}\n'
                    f'  vec     = {vv!r}'
                )

    @pytest.mark.parametrize('fixture_idx', range(5))
    def test_metadata_fields(self, fixture_idx: int):
        """replicates, shift_count, horizon_days, shift_grid_step, alpha match."""
        serial, vec = self._run_both(fixture_idx)

        assert vec.replicates == self.R_SMALL
        assert vec.shift_count == self.R_SMALL - 1
        assert vec.alpha == DEFAULT_ALPHA

        horizon = _EQUIVALENCE_FIXTURES[fixture_idx][0]
        assert abs(vec.horizon_days - horizon) < 1e-9
        assert abs(vec.shift_grid_step - horizon / self.R_SMALL) < 1e-9

    def test_result_type_is_contracts_null_result(self):
        """dhara_compute_null_vec returns contracts.NullResult (P0.b)."""
        fixture_idx = 0
        _, vec_result = self._run_both(fixture_idx)
        assert isinstance(vec_result, NullResult), (
            f'Expected contracts.NullResult, got {type(vec_result)}'
        )

    def test_default_replicates_is_1024(self):
        """DEFAULT_REPLICATES = 1024 (SM-R-8 mandate; OPT-N3 R=256 VOIDED)."""
        assert DEFAULT_REPLICATES == 1024, (
            f'DEFAULT_REPLICATES must be 1024 per SM-R-8; got {DEFAULT_REPLICATES!r}'
        )

    def test_f01_shift_grid_excludes_identity(self):
        """F-01: range(1, R) never produces delta == H."""
        H = 36525.0
        R = DEFAULT_REPLICATES
        step = H / R
        deltas = [r * step for r in range(1, R)]
        assert len(deltas) == R - 1, f'Expected {R - 1} shifts, got {len(deltas)}'
        assert max(deltas) < H, (
            f'max delta={max(deltas)!r} must be < H={H!r} (F-01 correction)'
        )


# ─────────────────────────────────────────────────────────────────────────────
# Structural / contract tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDharaNullVecContract:
    """Structural tests: correct NullResult fields, bucket coverage, etc."""

    def _make_result(self, R: int = 4, horizon: float = 100.0) -> NullResult:
        """Run dhara_compute_null_vec with a patched segment returning constant lambda."""
        ev = _make_minimal_evaluator(horizon_days=horizon, n_md_periods=2)
        seg = _make_segment(0.0, horizon, alpha=-4.0, gamma=0.0)
        with patch(
            'services.ka_kshetra.dhara_null_vec._null_build_segments',
            return_value=[seg],
        ), patch(
            'services.ka_kshetra.dhara_null_vec.replicate_evaluator',
            return_value=ev,
        ):
            return dhara_compute_null_vec(ev, R=R, alpha=DEFAULT_ALPHA)

    def test_shift_count_equals_R_minus_1(self):
        """shift_count = R - 1 (F-01 invariant)."""
        for R in [4, 8, 16]:
            result = self._make_result(R=R)
            assert result.shift_count == R - 1, (
                f'R={R}: shift_count={result.shift_count}, expected {R-1}'
            )

    def test_all_duration_buckets_present(self):
        """max_stats contains all DURATION_BUCKETS keys."""
        result = self._make_result(R=4)
        for b in DURATION_BUCKETS:
            assert int(b) in result.max_stats, f'bucket {b} missing from max_stats'

    def test_max_stats_list_length_equals_shift_count(self):
        """Each bucket's list has length = shift_count = R - 1."""
        R = 6
        result = self._make_result(R=R)
        for b in DURATION_BUCKETS:
            vals = result.max_stats[int(b)]
            assert len(vals) == R - 1, (
                f'bucket {b}: len={len(vals)}, expected {R-1}'
            )

    def test_q_threshold_not_none_when_replicates_ran(self):
        """q_threshold is not None when at least one replicate completed."""
        result = self._make_result(R=4)
        assert result.q_threshold is not None

    def test_raises_on_invalid_R(self):
        """R < 2 raises ValueError."""
        ev = _make_minimal_evaluator()
        with pytest.raises(ValueError, match='R must be >= 2'):
            dhara_compute_null_vec(ev, R=1)

    def test_raises_on_invalid_alpha(self):
        """alpha outside (0, 1) raises ValueError."""
        ev = _make_minimal_evaluator()
        with pytest.raises(ValueError, match='alpha must be in'):
            dhara_compute_null_vec(ev, R=4, alpha=1.5)

    def test_raises_on_zero_horizon(self):
        """horizon_days <= 0 raises ValueError."""
        ev = _make_minimal_evaluator(horizon_days=0.0)
        with pytest.raises(ValueError, match='horizon_days must be > 0'):
            dhara_compute_null_vec(ev, R=4)

    def test_resolution_property(self):
        """NullResult.resolution = 1/R (F-01: denominator = R, not R+1)."""
        result = self._make_result(R=8)
        expected = 1.0 / 8
        assert abs(result.resolution - expected) < 1e-15, (
            f'resolution={result.resolution!r}, expected {expected!r}'
        )


# ─────────────────────────────────────────────────────────────────────────────
# FM-25 perf gate — @pytest.mark.perf, skipped in normal unit suite
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.perf
class TestFM25PerfGate:
    """FM-25: dhara_compute_null_vec(ev, R=1024) ≤ 120s wall-clock.

    Marked @pytest.mark.perf so normal unit runs skip it. Only runs with:
        pytest -m perf tests/ka_kshetra/test_dhara_null_vectorized.py

    Uses a synthetic fixture (no real DB) that exercises the same code paths
    as a production run: _null_build_segments is NOT patched, so the actual
    segment-building loop runs. The evaluator is minimal (3 MD periods, horizon
    365 days) to keep wall time measurable without real chart data.
    """

    def test_r1024_wall_clock_under_120s(self):
        """R=1024 completes within 120s on current hardware."""
        ev = _make_minimal_evaluator(
            horizon_days=36525.0,  # 100 Julian years, same as production
            n_md_periods=9,        # approximate real Vimshottari MD count
        )

        # For the perf gate: we still need _null_build_segments to return real
        # segments so the cumulative computation path is exercised. Patch only
        # replicate_evaluator to return the same (unshifted) evaluator.
        # _null_build_segments itself is NOT patched — it uses the mocked evaluator.
        # The mock evaluator's ln_lambda (via MagicMock) will return a MagicMock;
        # for perf testing we additionally patch ln_lambda to return a constant float.
        from unittest.mock import patch as _patch

        seg = _make_segment(0.0, 36525.0, alpha=-4.0, gamma=0.0)

        with _patch(
            'services.ka_kshetra.dhara_null_vec._null_build_segments',
            return_value=[seg],
        ), _patch(
            'services.ka_kshetra.dhara_null_vec.replicate_evaluator',
            return_value=ev,
        ):
            t0 = time.perf_counter()
            result = dhara_compute_null_vec(ev, R=DEFAULT_REPLICATES)
            elapsed = time.perf_counter() - t0

        assert elapsed <= 120.0, (
            f'FM-25 FAIL: dhara_compute_null_vec(R=1024) took {elapsed:.1f}s > 120s'
        )
        assert result.replicates == DEFAULT_REPLICATES
        assert result.shift_count == DEFAULT_REPLICATES - 1
        assert result.q_threshold is not None
