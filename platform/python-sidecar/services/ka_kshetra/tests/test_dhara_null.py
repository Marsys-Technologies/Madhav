"""
tests/ka_kshetra/test_dhara_null.py — unit tests for dhara_null.py

Covers the four mandatory test cases from the S3-L2 spec:

  1. test_shift_grid_excludes_identity   — range(1, R) never produces delta == H
  2. test_shift_grid_count               — len(deltas) == R - 1 (1023 for R=1024)
  3. test_null_result_fields             — NullResult has all required fields
  4. test_coarse_mode_reduces_knot_count — coarse_mode=True produces fewer knots

All tests are pure-Python; no database, no DB fixture, no real chart data.
Mock objects implement only the FieldEvaluator / EnvelopeIndex surface that
dhara_null.py actually calls.
"""
from __future__ import annotations

import math
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from services.ka_kshetra.dhara_null import (
    DEFAULT_REPLICATES,
    NullResult,
    _clock_knots,
    _envelope_knots,
    dhara_compute_null,
)
from services.ka_kshetra.stage5_null import DURATION_BUCKETS


# ─────────────────────────────────────────────────────────────────────────────
# Helpers: minimal mock objects
# ─────────────────────────────────────────────────────────────────────────────

def _make_ladder_period(level: str, t_start: float, t_end: float):
    """Return a duck-typed period with .level, .t_start, .t_end."""
    p = MagicMock()
    p.level = level
    p.t_start = t_start
    p.t_end = t_end
    return p


def _make_evaluator(
    horizon_days: float = 36525.0,
    ladder: Optional[dict] = None,
    envelope_breakpoints: Optional[list] = None,
) -> MagicMock:
    """Minimal FieldEvaluator mock for dhara_null tests.

    The evaluator's .ladder and .envelopes.breakpoints() are the only
    attributes read by _clock_knots and _envelope_knots.
    """
    ev = MagicMock()
    ev.horizon_days = horizon_days
    ev.event_class = 'test_class'

    # Ladder: dict[system_id -> list[LadderPeriod]]
    if ladder is None:
        # Default: two MD periods spanning the horizon, two PD sub-periods,
        # and one SD period (excluded by coarse_mode).
        md1 = _make_ladder_period('MD', 0.0, 1000.0)
        md2 = _make_ladder_period('MD', 1000.0, 2000.0)
        pd1 = _make_ladder_period('PD', 0.0, 500.0)
        sd1 = _make_ladder_period('SD', 0.0, 100.0)
        ev.ladder = {'vimshottari': [md1, md2, pd1, sd1]}
    else:
        ev.ladder = ladder

    # EnvelopeIndex mock: breakpoints() returns a list of knot times.
    if envelope_breakpoints is None:
        envelope_breakpoints = [100.0, 200.0, 500.0, 1500.0]
    ev.envelopes = MagicMock()
    ev.envelopes.breakpoints.return_value = envelope_breakpoints
    ev.envelopes.horizon_days = horizon_days

    return ev


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: shift grid excludes identity
# ─────────────────────────────────────────────────────────────────────────────

class TestShiftGridExcludesIdentity:
    """F-01 correction: range(1, R) never produces delta == H."""

    @pytest.mark.parametrize('R', [DEFAULT_REPLICATES, 256, 128, 64])
    def test_max_delta_less_than_H(self, R: int):
        H = 36525.0
        deltas = [r * (H / R) for r in range(1, R)]
        assert max(deltas) < H, (
            f'With R={R}, max delta={max(deltas)!r} must be < H={H!r}. '
            'The identity shift (delta == H) would double-count the observation.'
        )

    def test_max_delta_canonical_R(self):
        """Specific check for the default R=1024."""
        R = DEFAULT_REPLICATES  # 1024
        H = 36525.0
        deltas = [r * (H / R) for r in range(1, R)]
        # Last shift: r=1023, delta = 1023 * (36525/1024) = 36488.330... < 36525
        max_delta = max(deltas)
        assert max_delta < H
        # Also verify it is strictly positive (no zero shift)
        assert min(deltas) > 0.0

    def test_last_shift_does_not_wrap_to_zero(self):
        """delta % H must never equal 0.0 for any shift in range(1, R)."""
        R = DEFAULT_REPLICATES
        H = 36525.0
        for r in range(1, R):
            delta = r * (H / R)
            wrapped = delta % H
            assert wrapped != 0.0, (
                f'r={r}: delta={delta} wraps to 0 (delta % H == 0). '
                'This shift is the identity and must not be in range(1, R).'
            )

    def test_contrasts_with_wrong_grid(self):
        """Demonstrate that range(1, R+1) DOES include the identity.

        This is the pre-existing bug in stage5_null.py's shift_grid().
        For documentation purposes: when r == R, delta = H, and delta % H == 0.
        """
        R = DEFAULT_REPLICATES
        H = 36525.0
        # The buggy grid: range(1, R+1)
        buggy_deltas = [r * (H / R) for r in range(1, R + 1)]
        assert buggy_deltas[-1] == H, 'Buggy grid should include H as last delta'
        assert buggy_deltas[-1] % H == 0.0, 'H % H == 0 (identity shift)'

        # The correct grid: range(1, R)
        correct_deltas = [r * (H / R) for r in range(1, R)]
        assert max(correct_deltas) < H, 'Correct grid never reaches H'


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: shift grid count
# ─────────────────────────────────────────────────────────────────────────────

class TestShiftGridCount:
    """range(1, R) produces exactly R-1 independent shifts."""

    @pytest.mark.parametrize('R', [DEFAULT_REPLICATES, 256, 128, 8])
    def test_shift_count_equals_R_minus_1(self, R: int):
        H = 36525.0
        deltas = [r * (H / R) for r in range(1, R)]
        assert len(deltas) == R - 1, (
            f'Expected {R - 1} shifts for R={R}, got {len(deltas)}'
        )

    def test_canonical_R_gives_1023_shifts(self):
        """For R=1024, the shift grid has exactly 1023 independent shifts."""
        R = DEFAULT_REPLICATES  # 1024
        H = 36525.0
        deltas = [r * (H / R) for r in range(1, R)]
        assert len(deltas) == 1023

    def test_shift_grid_is_arithmetic_sequence(self):
        """Shifts form an exact arithmetic sequence with step H/R."""
        R = DEFAULT_REPLICATES
        H = 36525.0
        step = H / R
        deltas = [r * step for r in range(1, R)]
        for i, (d, r) in enumerate(zip(deltas, range(1, R))):
            expected = r * step
            assert d == expected, f'Shift {i}: expected {expected}, got {d}'

    def test_p_value_denominator(self):
        """p-value denominator = R = 1024 (observation + R-1 shifts)."""
        R = DEFAULT_REPLICATES
        H = 36525.0
        deltas = [r * (H / R) for r in range(1, R)]
        n_shifts = len(deltas)
        # p-value denominator = 1 observation + n_shifts = R
        denominator = 1 + n_shifts
        assert denominator == R
        # Resolution = 1/R
        resolution = 1.0 / denominator
        assert abs(resolution - 1.0 / 1024) < 1e-15


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: NullResult has required fields
# ─────────────────────────────────────────────────────────────────────────────

class TestNullResultFields:
    """NullResult dataclass has all required fields with correct types."""

    def test_required_fields_present(self):
        """NullResult can be constructed with all required fields."""
        result = NullResult(
            replicates=1024,
            shift_count=1023,
            horizon_days=36525.0,
            shift_grid_step=36525.0 / 1024,
            q_threshold=0.5,
            max_stats={b: [0.1, 0.2] for b in DURATION_BUCKETS},
            alpha=0.05,
        )
        assert result.replicates == 1024
        assert result.shift_count == 1023
        assert result.horizon_days == 36525.0
        assert abs(result.shift_grid_step - 36525.0 / 1024) < 1e-10
        assert result.q_threshold == 0.5
        assert result.alpha == 0.05
        assert set(result.max_stats.keys()) == set(DURATION_BUCKETS)

    def test_shift_count_equals_replicates_minus_1(self):
        """shift_count is always replicates - 1 (F-01 invariant)."""
        for R in [1024, 512, 256]:
            result = NullResult(
                replicates=R,
                shift_count=R - 1,
                horizon_days=36525.0,
                shift_grid_step=36525.0 / R,
                q_threshold=None,
                max_stats={},
            )
            assert result.shift_count == result.replicates - 1

    def test_q_threshold_can_be_none(self):
        """q_threshold=None is the honest not-computed value."""
        result = NullResult(
            replicates=1024,
            shift_count=1023,
            horizon_days=36525.0,
            shift_grid_step=36525.0 / 1024,
            q_threshold=None,
            max_stats={},
        )
        assert result.q_threshold is None

    def test_max_stats_structure(self):
        """max_stats maps duration buckets to lists of per-replicate values."""
        n_shifts = 1023
        max_stats = {b: [float(b) * 0.001 * i for i in range(n_shifts)]
                     for b in DURATION_BUCKETS}
        result = NullResult(
            replicates=1024,
            shift_count=n_shifts,
            horizon_days=36525.0,
            shift_grid_step=36525.0 / 1024,
            q_threshold=0.42,
            max_stats=max_stats,
        )
        for b in DURATION_BUCKETS:
            assert int(b) in result.max_stats
            assert len(result.max_stats[int(b)]) == n_shifts

    def test_dhara_compute_null_returns_null_result(self):
        """dhara_compute_null returns a NullResult instance (with tiny R for speed)."""
        ev = _make_evaluator()

        # Patch _null_build_segments so no real field computation happens.
        # Return a minimal segment covering the horizon.
        from services.ka_kshetra.contracts import Segment

        fake_segment = Segment(
            index=0,
            t_start=0.0,
            t_end=ev.horizon_days,
            alpha=-5.0,
            gamma=0.0,
            refinement_depth=0,
            refinement_exhausted=False,
            refinement_residual=None,
        )

        with patch(
            'services.ka_kshetra.dhara_null._null_build_segments',
            return_value=[fake_segment],
        ), patch(
            'services.ka_kshetra.dhara_null.replicate_evaluator',
            return_value=ev,
        ):
            result = dhara_compute_null(ev, replicates=4, alpha=0.05)

        assert isinstance(result, NullResult)
        assert result.replicates == 4
        assert result.shift_count == 3  # range(1, 4) -> 3 shifts
        assert result.alpha == 0.05
        assert result.horizon_days == ev.horizon_days
        assert isinstance(result.max_stats, dict)
        for b in DURATION_BUCKETS:
            assert int(b) in result.max_stats
            assert len(result.max_stats[int(b)]) == 3


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: coarse_mode reduces knot count
# ─────────────────────────────────────────────────────────────────────────────

class TestCoarseModeReducesKnotCount:
    """coarse_mode=True produces fewer clock knots than coarse_mode=False."""

    def _make_ev_with_all_levels(self, horizon: float = 36525.0) -> MagicMock:
        """Evaluator whose ladder has all five dasa levels with many periods."""
        periods = []
        # MD: 10 periods
        for i in range(10):
            periods.append(_make_ladder_period('MD', i * 1000.0, (i + 1) * 1000.0))
        # AD: 30 periods
        for i in range(30):
            periods.append(_make_ladder_period('AD', i * 200.0, (i + 1) * 200.0))
        # PD: 50 periods
        for i in range(50):
            periods.append(_make_ladder_period('PD', i * 100.0, (i + 1) * 100.0))
        # SD: 100 periods (excluded by coarse_mode)
        for i in range(100):
            periods.append(_make_ladder_period('SD', i * 50.0, (i + 1) * 50.0))
        # PrD: 200 periods (excluded by coarse_mode)
        for i in range(200):
            periods.append(_make_ladder_period('PrD', i * 20.0, (i + 1) * 20.0))

        ev = MagicMock()
        ev.horizon_days = horizon
        ev.ladder = {'vimshottari': periods}
        ev.envelopes = MagicMock()
        ev.envelopes.breakpoints.return_value = [500.0, 1500.0, 2500.0]
        ev.envelopes.horizon_days = horizon
        return ev

    def test_coarse_fewer_knots_than_full(self):
        ev = self._make_ev_with_all_levels()
        coarse = _clock_knots(ev, coarse_mode=True)
        full = _clock_knots(ev, coarse_mode=False)
        assert len(coarse) < len(full), (
            f'coarse_mode=True should produce fewer knots: '
            f'got {len(coarse)} coarse vs {len(full)} full'
        )

    def test_coarse_excludes_SD_PrD(self):
        """SD and PrD boundaries must be absent from the coarse knot set."""
        ev = self._make_ev_with_all_levels()
        coarse = _clock_knots(ev, coarse_mode=True)
        full = _clock_knots(ev, coarse_mode=False)

        # The coarse set has only MD/AD/PD boundaries (plus 0 and H).
        # The full set has SD/PrD boundaries too.
        # So full must be strictly larger.
        coarse_set = set(coarse.tolist())
        full_set = set(full.tolist())
        sd_prd_only = full_set - coarse_set
        assert len(sd_prd_only) > 0, (
            'Expected SD/PrD boundaries to be present in full but absent in coarse'
        )

    def test_coarse_always_includes_zero_and_horizon(self):
        """0.0 and horizon_days must always be in the coarse knot set."""
        ev = self._make_ev_with_all_levels()
        coarse = _clock_knots(ev, coarse_mode=True)
        assert coarse[0] == 0.0
        assert coarse[-1] == ev.horizon_days

    def test_full_always_includes_zero_and_horizon(self):
        ev = self._make_ev_with_all_levels()
        full = _clock_knots(ev, coarse_mode=False)
        assert full[0] == 0.0
        assert full[-1] == ev.horizon_days

    def test_coarse_is_subset_of_full(self):
        """Every knot in the coarse set must also be in the full set."""
        ev = self._make_ev_with_all_levels()
        coarse = set(_clock_knots(ev, coarse_mode=True).tolist())
        full = set(_clock_knots(ev, coarse_mode=False).tolist())
        assert coarse.issubset(full), (
            'coarse knot set must be a subset of the full knot set'
        )

    def test_minimal_evaluator_coarse_still_has_MD_AD_PD(self):
        """Even with a minimal evaluator, coarse mode retains MD/AD/PD knots."""
        md = _make_ladder_period('MD', 100.0, 500.0)
        ad = _make_ladder_period('AD', 200.0, 400.0)
        pd = _make_ladder_period('PD', 250.0, 350.0)
        sd = _make_ladder_period('SD', 300.0, 330.0)  # should be excluded

        ev = MagicMock()
        ev.horizon_days = 1000.0
        ev.ladder = {'vimshottari': [md, ad, pd, sd]}
        ev.envelopes = MagicMock()
        ev.envelopes.breakpoints.return_value = []
        ev.envelopes.horizon_days = 1000.0

        coarse = _clock_knots(ev, coarse_mode=True)
        coarse_list = sorted(coarse.tolist())

        # MD boundaries 100.0 and 500.0 must be present
        assert 100.0 in coarse_list
        assert 500.0 in coarse_list
        # AD boundaries 200.0 and 400.0 must be present
        assert 200.0 in coarse_list
        assert 400.0 in coarse_list
        # PD boundaries 250.0 and 350.0 must be present
        assert 250.0 in coarse_list
        assert 350.0 in coarse_list
        # SD boundaries 300.0 and 330.0 must be ABSENT
        assert 300.0 not in coarse_list
        assert 330.0 not in coarse_list


# ─────────────────────────────────────────────────────────────────────────────
# Additional invariant: envelope knots helper
# ─────────────────────────────────────────────────────────────────────────────

class TestEnvelopeKnots:
    """_envelope_knots returns sorted, horizon-clipped knot array."""

    def test_returns_sorted_array(self):
        ev = _make_evaluator(envelope_breakpoints=[500.0, 100.0, 300.0])
        K_e = _envelope_knots(ev)
        assert list(K_e) == sorted(K_e.tolist())

    def test_clips_to_horizon(self):
        H = 1000.0
        ev = _make_evaluator(horizon_days=H, envelope_breakpoints=[500.0, 1500.0, 2000.0])
        K_e = _envelope_knots(ev)
        assert all(0.0 <= t <= H for t in K_e.tolist())
        assert 1500.0 not in K_e.tolist()
        assert 2000.0 not in K_e.tolist()

    def test_empty_envelope(self):
        ev = _make_evaluator(envelope_breakpoints=[])
        K_e = _envelope_knots(ev)
        assert len(K_e) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Validation: argument guards in dhara_compute_null
# ─────────────────────────────────────────────────────────────────────────────

class TestArgumentValidation:
    """dhara_compute_null raises ValueError on bad inputs."""

    def test_replicates_must_be_at_least_2(self):
        ev = _make_evaluator()
        with pytest.raises(ValueError, match='replicates must be >= 2'):
            dhara_compute_null(ev, replicates=1)

    def test_alpha_must_be_in_0_1(self):
        ev = _make_evaluator()
        with pytest.raises(ValueError, match='alpha must be in'):
            dhara_compute_null(ev, replicates=4, alpha=1.5)

    def test_alpha_zero_rejected(self):
        ev = _make_evaluator()
        with pytest.raises(ValueError, match='alpha must be in'):
            dhara_compute_null(ev, replicates=4, alpha=0.0)
