"""
tests/test_ka_kshetra_uncertainty.py — Lane B (ṢAḌ-DARŚANA W2), item 24-full.

Pure-math test suite for `services.ka_kshetra.uncertainty` — no DB required
for the bulk of the suite (mirrors `tests/test_ka_gochara_sweep.py`'s
documented no-DB pattern for pure modules). The DB-facing wrappers
(`fetch_sigma_t_days`, `fetch_sigma_a_degrees`) are exercised against small
fake connection objects exposing `.execute(sql, params).fetchall()`,
returning dict rows (mirrors `pipeline/orchestrator/db.py`'s
`row_factory=psycopg.rows.dict_row`).
"""
from __future__ import annotations

import math

import pytest

from services.ka_kshetra import uncertainty as U


# ── wrap180 / unwrap_longitudes ─────────────────────────────────────────────

class TestWrap180:
    def test_identity_within_range(self):
        assert U.wrap180(10.0) == pytest.approx(10.0)
        assert U.wrap180(-10.0) == pytest.approx(-10.0)

    def test_wraps_above_180(self):
        assert U.wrap180(200.0) == pytest.approx(-160.0)

    def test_wraps_below_negative_180(self):
        assert U.wrap180(-200.0) == pytest.approx(160.0)

    def test_boundary_360_wraps_to_zero(self):
        assert U.wrap180(360.0) == pytest.approx(0.0, abs=1e-9)


class TestUnwrapLongitudes:
    def test_empty(self):
        assert U.unwrap_longitudes({}) == {}

    def test_no_wrap_needed(self):
        vals = {"a": 10.0, "b": 12.0, "c": 9.5}
        out = U.unwrap_longitudes(vals)
        assert out == pytest.approx(vals)

    def test_wraps_a_value_just_below_360_relative_to_anchor_near_zero(self):
        # anchor at 1.0deg; a second ayanamsha's Moon sits at 359.5deg (i.e.
        # really -1.5deg relative to anchor, wrapping through 0/360) -- must
        # NOT be treated as ~358.5deg away.
        vals = {"a": 1.0, "b": 359.5}
        out = U.unwrap_longitudes(vals)
        assert out["a"] == pytest.approx(1.0)
        assert out["b"] == pytest.approx(-0.5)  # 1.0 + (-1.5)

    def test_anchors_on_first_item_order(self):
        vals = {"z": 359.0, "a": 1.0}
        out = U.unwrap_longitudes(vals)
        # anchor is 'z' (first inserted) = 359.0; 'a' (1.0) unwraps to 361.0
        assert out["z"] == pytest.approx(359.0)
        assert out["a"] == pytest.approx(361.0)


# ── compute_sigma_a_degrees ──────────────────────────────────────────────────

class TestComputeSigmaA:
    def test_requires_at_least_two_points(self):
        with pytest.raises(ValueError):
            U.compute_sigma_a_degrees({"lahiri_chitrapaksha": 10.0})

    def test_simple_range(self):
        longitudes = {
            "lahiri_chitrapaksha": 10.0,
            "true_chitra": 10.5,
            "krishnamurti": 9.7,
            "raman": 10.2,
            "surya_siddhanta_classical": 8.9,
        }
        result = U.compute_sigma_a_degrees(longitudes)
        assert result.range_deg == pytest.approx(10.5 - 8.9)
        assert result.sigma_a_deg == pytest.approx((10.5 - 8.9) / math.sqrt(12.0))
        assert result.n_ayanamshas == 5

    def test_handles_wraparound_near_zero(self):
        # Without unwrapping this would look like a ~359deg range.
        longitudes = {"a": 0.2, "b": 359.8}
        result = U.compute_sigma_a_degrees(longitudes)
        assert result.range_deg == pytest.approx(0.4, abs=1e-9)


# ── compute_sigma_t_days ─────────────────────────────────────────────────────

class TestComputeSigmaTDays:
    def test_no_candidates_returns_default(self):
        sigma, source = U.compute_sigma_t_days([])
        assert sigma == pytest.approx(U.DEFAULT_SIGMA_T_DAYS)
        assert source == "default_120s_assumption"

    def test_single_usable_candidate_returns_default(self):
        cands = [U.RectificationCandidate(offset_minutes=5, lel_fit_score=0.9, lagna_stable=True)]
        sigma, source = U.compute_sigma_t_days(cands)
        assert source == "default_120s_assumption"

    def test_unstable_lagna_excluded(self):
        cands = [
            U.RectificationCandidate(offset_minutes=5, lel_fit_score=0.9, lagna_stable=False),
            U.RectificationCandidate(offset_minutes=-5, lel_fit_score=0.9, lagna_stable=False),
        ]
        sigma, source = U.compute_sigma_t_days(cands)
        assert source == "default_120s_assumption"

    def test_null_fit_score_excluded(self):
        cands = [
            U.RectificationCandidate(offset_minutes=5, lel_fit_score=None, lagna_stable=True),
            U.RectificationCandidate(offset_minutes=-5, lel_fit_score=None, lagna_stable=True),
        ]
        sigma, source = U.compute_sigma_t_days(cands)
        assert source == "default_120s_assumption"

    def test_weighted_std_of_real_spread(self):
        # Two candidates, equal weight, offsets +-30 minutes -> weighted std
        # in days should be 30/1440 (population std of a symmetric 2-point set).
        cands = [
            U.RectificationCandidate(offset_minutes=30, lel_fit_score=1.0, lagna_stable=True),
            U.RectificationCandidate(offset_minutes=-30, lel_fit_score=1.0, lagna_stable=True),
        ]
        sigma, source = U.compute_sigma_t_days(cands)
        assert source == "rectification_posterior_weighted_std"
        assert sigma == pytest.approx(30.0 / 1440.0)

    def test_degenerate_zero_spread_floors_at_default(self):
        cands = [
            U.RectificationCandidate(offset_minutes=10, lel_fit_score=0.8, lagna_stable=True),
            U.RectificationCandidate(offset_minutes=10, lel_fit_score=0.6, lagna_stable=True),
        ]
        sigma, source = U.compute_sigma_t_days(cands)
        assert source == "rectification_posterior_weighted_std"
        assert sigma == pytest.approx(U.DEFAULT_SIGMA_T_DAYS)


# ── DB-facing wrappers (fake conn) ───────────────────────────────────────────

class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeConn:
    """Records the last SQL/params issued and returns pre-seeded rows."""

    def __init__(self, rows):
        self._rows = rows
        self.last_sql = None
        self.last_params = None

    def execute(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params
        return _FakeCursor(self._rows)


class TestFetchSigmaTDays:
    def test_no_rows_falls_back_to_default(self):
        conn = _FakeConn([])
        sigma, source = U.fetch_sigma_t_days("chart-1", conn)
        assert source == "default_120s_assumption"
        assert sigma == pytest.approx(U.DEFAULT_SIGMA_T_DAYS)
        assert "phala_rectification" in conn.last_sql

    def test_real_rows_produce_weighted_estimate(self):
        rows = [
            {"offset_minutes": 20, "lel_fit_score": 0.9, "lagna_stable": True},
            {"offset_minutes": -20, "lel_fit_score": 0.9, "lagna_stable": True},
            {"offset_minutes": 100, "lel_fit_score": None, "lagna_stable": True},
            {"offset_minutes": 5, "lel_fit_score": 0.5, "lagna_stable": False},
        ]
        conn = _FakeConn(rows)
        sigma, source = U.fetch_sigma_t_days("chart-1", conn)
        assert source == "rectification_posterior_weighted_std"
        assert sigma == pytest.approx(20.0 / 1440.0)


class TestFetchSigmaADegrees:
    def test_reads_moon_longitude_across_ayanamshas(self):
        rows = [
            {"ayanamsha_id": "lahiri_chitrapaksha", "fact_value_num": 10.0},
            {"ayanamsha_id": "true_chitra", "fact_value_num": 10.4},
            {"ayanamsha_id": "krishnamurti", "fact_value_num": 9.8},
            {"ayanamsha_id": "raman", "fact_value_num": 10.1},
            {"ayanamsha_id": "surya_siddhanta_classical", "fact_value_num": 9.0},
        ]
        conn = _FakeConn(rows)
        result = U.fetch_sigma_a_degrees("chart-1", conn)
        assert result.n_ayanamshas == 5
        assert result.range_deg == pytest.approx(10.4 - 9.0)
        assert "graha_position" in conn.last_sql
        assert "longitude_sidereal" in conn.last_sql
        assert conn.last_params[1] == "MOON"


# ── propagate_fractional_arc_sigma_t ─────────────────────────────────────────

class TestPropagateFractionalArcSigmaT:
    def test_rejects_zero_moon_velocity(self):
        with pytest.raises(ValueError):
            U.propagate_fractional_arc_sigma_t(
                v_moon_dps=0.0, sigma_t_birth_days=U.DEFAULT_SIGMA_T_DAYS,
                sigma_a_deg=0.5, t_balance_days=16 * 365.25,
            )

    def test_rejects_nonpositive_span(self):
        with pytest.raises(ValueError):
            U.propagate_fractional_arc_sigma_t(
                v_moon_dps=13.0, sigma_t_birth_days=U.DEFAULT_SIGMA_T_DAYS,
                sigma_a_deg=0.5, t_balance_days=16 * 365.25, l_span_deg=0.0,
            )

    def test_matches_hand_computed_values(self):
        v_moon = 13.176  # deg/day, roughly mean lunar velocity
        sigma_t_birth = U.DEFAULT_SIGMA_T_DAYS
        sigma_a = 0.9  # deg
        t_balance = 16.0 * 365.25  # Jupiter MD, days

        result = U.propagate_fractional_arc_sigma_t(
            v_moon_dps=v_moon,
            sigma_t_birth_days=sigma_t_birth,
            sigma_a_deg=sigma_a,
            t_balance_days=t_balance,
            l_span_deg=U.NAK_SPAN_DEG,
        )

        expected_sigma_lambda = math.sqrt((v_moon * sigma_t_birth) ** 2 + sigma_a ** 2)
        expected_sigma_f = expected_sigma_lambda / U.NAK_SPAN_DEG
        expected_sigma_t = math.sqrt((t_balance * expected_sigma_f) ** 2 + sigma_t_birth ** 2)

        assert result.sigma_lambda_deg == pytest.approx(expected_sigma_lambda)
        assert result.sigma_f == pytest.approx(expected_sigma_f)
        assert result.sigma_t_days == pytest.approx(expected_sigma_t)
        # With sigma_a=0.9deg dominating a 120s-default birth-time term,
        # the ayanamsha term should dominate here.
        assert result.dominant_uncertainty_source == "ayanamsha"

    def test_birth_time_dominates_when_sigma_a_is_tiny(self):
        result = U.propagate_fractional_arc_sigma_t(
            v_moon_dps=13.0,
            sigma_t_birth_days=1.0,  # a full day of birth-time uncertainty
            sigma_a_deg=1e-6,
            t_balance_days=16.0 * 365.25,
            l_span_deg=U.NAK_SPAN_DEG,
        )
        assert result.dominant_uncertainty_source == "birth_time"

    def test_pada_span_used_for_kalachakra(self):
        result = U.propagate_fractional_arc_sigma_t(
            v_moon_dps=13.0,
            sigma_t_birth_days=U.DEFAULT_SIGMA_T_DAYS,
            sigma_a_deg=0.5,
            t_balance_days=7.0 * 365.25,
            l_span_deg=U.PADA_SPAN_DEG,
        )
        # Same math, just a smaller span -> larger sigma_f than the nakshatra case.
        result_nak = U.propagate_fractional_arc_sigma_t(
            v_moon_dps=13.0,
            sigma_t_birth_days=U.DEFAULT_SIGMA_T_DAYS,
            sigma_a_deg=0.5,
            t_balance_days=7.0 * 365.25,
            l_span_deg=U.NAK_SPAN_DEG,
        )
        assert result.sigma_f > result_nak.sigma_f


class TestSigmaTBirthTimeOnly:
    def test_passthrough(self):
        sigma, source = U.sigma_t_birth_time_only(0.5)
        assert sigma == 0.5
        assert source == "birth_time"


# ── evaluate_precision_support ───────────────────────────────────────────────

class TestEvaluatePrecisionSupport:
    def test_instant_when_width_within_10pct_of_period(self):
        # width = 2*1.96*sigma_t; choose sigma_t so width = 0.05 * period
        period = 100.0
        width_target = 0.05 * period
        sigma_t = width_target / (2 * U.Z_95)
        result = U.evaluate_precision_support(t_boundary_days=1000.0, sigma_t_days=sigma_t, period_days=period)
        assert result.precision_state == "instant"
        assert result.width_days == pytest.approx(width_target)
        assert result.interval_lo == pytest.approx(1000.0 - U.Z_95 * sigma_t)
        assert result.interval_hi == pytest.approx(1000.0 + U.Z_95 * sigma_t)

    def test_interval_when_width_between_10pct_and_100pct(self):
        period = 100.0
        width_target = 0.5 * period
        sigma_t = width_target / (2 * U.Z_95)
        result = U.evaluate_precision_support(t_boundary_days=0.0, sigma_t_days=sigma_t, period_days=period)
        assert result.precision_state == "interval"

    def test_precision_unsupported_when_width_exceeds_period(self):
        period = 100.0
        width_target = 1.5 * period
        sigma_t = width_target / (2 * U.Z_95)
        result = U.evaluate_precision_support(t_boundary_days=0.0, sigma_t_days=sigma_t, period_days=period)
        assert result.precision_state == "precision_unsupported"

    def test_boundary_at_exactly_10pct_is_instant(self):
        period = 100.0
        sigma_t = (0.10 * period) / (2 * U.Z_95)
        result = U.evaluate_precision_support(t_boundary_days=0.0, sigma_t_days=sigma_t, period_days=period)
        assert result.precision_state == "instant"

    def test_boundary_at_exactly_100pct_is_interval(self):
        period = 100.0
        sigma_t = (1.00 * period) / (2 * U.Z_95)
        result = U.evaluate_precision_support(t_boundary_days=0.0, sigma_t_days=sigma_t, period_days=period)
        assert result.precision_state == "interval"

    def test_zero_sigma_is_always_instant(self):
        result = U.evaluate_precision_support(t_boundary_days=42.0, sigma_t_days=0.0, period_days=10.0)
        assert result.precision_state == "instant"
        assert result.width_days == 0.0

    def test_rejects_negative_sigma(self):
        with pytest.raises(ValueError):
            U.evaluate_precision_support(t_boundary_days=0.0, sigma_t_days=-1.0, period_days=10.0)

    def test_rejects_nonpositive_period(self):
        with pytest.raises(ValueError):
            U.evaluate_precision_support(t_boundary_days=0.0, sigma_t_days=1.0, period_days=0.0)
