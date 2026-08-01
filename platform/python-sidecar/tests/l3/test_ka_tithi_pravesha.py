"""Tests for ka_tithi_pravesha (ṢAḌ-DARŚANA W3, registry item 13 — Tithi-
Praveśa lunar-return annual chart), pure logic (engine/DB-free) module.

TDD: written before services/ka_tithi_pravesha/logic.py existed (mirrors the
test-first discipline of test_ka_sudarshana_varsha.py / ga_tajaka's own
_solar_return resilience tests).

The `lunar_return` tests use a SYNTHETIC linear-in-time Moon longitude
function (real Moon mean speed, 13.176 deg/day) rather than the live
pyjhora_adapter engine — same technique ga_tajaka's own
test_ga_tajaka_solar_return_resilience.py uses for `_solar_return` (there via
patch.object; here via direct dependency injection, since `lunar_return`
takes `moon_longitude_fn` as a parameter rather than importing the engine).
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_tithi_pravesha.logic import (
    MEAN_MOON_SPEED_DEG_PER_DAY,
    ang_diff,
    lunar_return,
    pravesha_anniversary,
)


class TestAngDiff:
    def test_zero(self):
        assert ang_diff(100.0, 100.0) == 0.0

    def test_simple_positive(self):
        assert ang_diff(110.0, 100.0) == 10.0

    def test_simple_negative(self):
        assert ang_diff(90.0, 100.0) == -10.0

    def test_wraps_forward(self):
        # 359 vs 1: shortest path is -2 (359 is 2 deg "before" 1, going forward)
        assert abs(ang_diff(359.0, 1.0) - (-2.0)) < 1e-9

    def test_wraps_backward(self):
        assert abs(ang_diff(1.0, 359.0) - 2.0) < 1e-9

    def test_antipodal_is_180(self):
        assert abs(abs(ang_diff(180.0, 0.0)) - 180.0) < 1e-9


class TestPraveshaAnniversary:
    def test_year_1_is_birth_instant(self):
        birth = datetime(1984, 2, 5, 10, 43, 0)
        assert pravesha_anniversary(birth, 1) == birth

    def test_year_2_is_first_birthday(self):
        birth = datetime(1984, 2, 5, 10, 43, 0)
        assert pravesha_anniversary(birth, 2) == datetime(1985, 2, 5, 10, 43, 0)

    def test_year_43_matches_calendar_offset(self):
        birth = datetime(1984, 2, 5, 10, 43, 0)
        assert pravesha_anniversary(birth, 43) == datetime(2026, 2, 5, 10, 43, 0)

    def test_rejects_year_below_1(self):
        birth = datetime(1984, 2, 5, 10, 43, 0)
        try:
            pravesha_anniversary(birth, 0)
            assert False, "expected ValueError"
        except ValueError:
            pass


def _linear_moon_longitude_fn(anchor_dt: datetime, anchor_long: float):
    """A synthetic Moon longitude function: moves at the real mean lunar
    speed, exactly equal to `anchor_long` at `anchor_dt`. Deterministic root
    exists at `anchor_dt` for target=anchor_long."""
    def fn(dt: datetime) -> float:
        days_offset = (dt - anchor_dt).total_seconds() / 86400.0
        return (anchor_long + days_offset * MEAN_MOON_SPEED_DEG_PER_DAY) % 360.0
    return fn


class TestLunarReturnConvergesNormally:
    def test_converges_when_root_is_near_anniversary(self):
        anniversary = datetime(2026, 2, 4, 10, 43, 0)
        natal_moon = 291.0
        # Root exactly 2 days after the anniversary.
        root_instant = anniversary + timedelta(days=2)
        fn = _linear_moon_longitude_fn(root_instant, natal_moon)

        instant, audit = lunar_return(anniversary, natal_moon, fn)
        assert audit["converged"] is True
        assert audit["diff_deg"] is not None
        assert abs(audit["diff_deg"]) < 0.01
        assert abs((instant - root_instant).total_seconds()) < 60

    def test_converges_when_root_is_at_anniversary_exactly(self):
        anniversary = datetime(2026, 2, 4, 10, 43, 0)
        natal_moon = 45.0
        fn = _linear_moon_longitude_fn(anniversary, natal_moon)

        instant, audit = lunar_return(anniversary, natal_moon, fn)
        assert audit["converged"] is True
        assert abs((instant - anniversary).total_seconds()) < 60

    def test_converges_when_root_is_shortly_before_anniversary(self):
        anniversary = datetime(2026, 2, 4, 10, 43, 0)
        natal_moon = 200.0
        root_instant = anniversary - timedelta(days=3)
        fn = _linear_moon_longitude_fn(root_instant, natal_moon)

        instant, audit = lunar_return(anniversary, natal_moon, fn)
        assert audit["converged"] is True
        assert abs((instant - root_instant).total_seconds()) < 60


class TestLunarReturnAvoidsWrapDiscontinuity:
    """The regression this design specifically guards against (see logic.py's
    module docstring): a naive wide bracket around the anniversary can
    straddle ang_diff()'s -180/+180 discontinuity instead of the true
    zero-crossing, converging to a false 'root' ~180 deg off target. These
    cases construct a target whose true root sits close to where a wide
    bracket's OTHER boundary would land, and assert the result is genuinely
    near the target (diff_deg small), never near ±180."""

    def test_root_far_from_anniversary_still_converges_to_true_root_not_antipode(self):
        anniversary = datetime(2026, 6, 15, 0, 0, 0)
        natal_moon = 10.0
        # True root ~12 days after the anniversary — within reach of the
        # linear estimate, but a naive wide (+-15d) bracket without the
        # linear-estimate stage risks landing on the antipodal discontinuity.
        root_instant = anniversary + timedelta(days=12)
        fn = _linear_moon_longitude_fn(root_instant, natal_moon)

        instant, audit = lunar_return(anniversary, natal_moon, fn)
        assert audit["converged"] is True
        assert audit["diff_deg"] is not None
        assert abs(audit["diff_deg"]) < 0.01, (
            f"converged to a false root: diff_deg={audit['diff_deg']} "
            "(expected near 0, got near +-180 would indicate the "
            "discontinuity-straddling bug)"
        )

    def test_root_just_before_anniversary_by_almost_half_cycle(self):
        anniversary = datetime(2026, 9, 1, 12, 0, 0)
        natal_moon = 300.0
        root_instant = anniversary - timedelta(days=13)
        fn = _linear_moon_longitude_fn(root_instant, natal_moon)

        instant, audit = lunar_return(anniversary, natal_moon, fn)
        assert audit["converged"] is True
        assert abs(audit["diff_deg"]) < 0.01


class TestLunarReturnEngineResilience:
    """Mirrors ga_tajaka_writer.py's `_solar_return` resilience tests
    (test_ga_tajaka_solar_return_resilience.py) — a position-engine failure
    at any probed instant must degrade to converged=False, never crash or
    fabricate a value (B.10)."""

    def test_survives_engine_raising_unconditionally(self):
        anniversary = datetime(2026, 2, 4, 10, 43, 0)

        def raising_fn(dt: datetime) -> float:
            raise RuntimeError("Moshier range error")

        instant, audit = lunar_return(anniversary, 291.0, raising_fn)
        assert isinstance(instant, datetime)
        assert audit["converged"] is False
        assert audit["diff_deg"] is None
        assert audit["unconverged_reason"] == "position_engine_error_at_anniversary"
        assert instant == anniversary  # honest fallback, matches ga_tajaka's convention

    def test_survives_engine_returning_none(self):
        anniversary = datetime(2026, 2, 4, 10, 43, 0)
        calls = {"n": 0}

        def flaky_fn(dt: datetime):
            calls["n"] += 1
            if calls["n"] == 1:
                return 250.0  # anniversary probe succeeds
            return None  # every subsequent probe fails

        instant, audit = lunar_return(anniversary, 100.0, flaky_fn)
        assert isinstance(instant, datetime)
        assert audit["converged"] is False
        assert "unconverged_reason" in audit

    def test_no_sign_change_falls_back_honestly(self):
        anniversary = datetime(2026, 2, 4, 10, 43, 0)

        def constant_fn(dt: datetime) -> float:
            # Moon "stuck" far from natal position — no root in range.
            return 0.0

        instant, audit = lunar_return(anniversary, 179.9, constant_fn)
        assert audit["converged"] is False
        assert audit["unconverged_reason"] in ("no_sign_change", "position_engine_error")
        assert instant == anniversary
