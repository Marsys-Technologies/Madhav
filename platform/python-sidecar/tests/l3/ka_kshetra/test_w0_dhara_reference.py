"""Independent W0 numerical references for the DHARA/integrator boundary.

These fixtures contain no chart or person data.  Expected values are computed
from Decimal arithmetic or from a Decimal composite-Simpson oracle implemented
in this file; production integration, window, and sweep helpers are never used
to manufacture an expected value.

Precision disclosure
--------------------
* Decimal context: 60 significant digits.
* Smooth suppression oracle: 4,096 Simpson sub-intervals.  The chosen true
  hazard is linear, so Simpson is algebraically exact apart from Decimal
  rounding; it is also checked against the closed-form value 11/40.
* Stored-field arithmetic: 1e-12 absolute at exact knots/crossings and 5e-13
  relative for a closed-form log-linear expected count.
* DHARA-vs-true-curved-field acceptance: 0.003 day at the threshold crossing,
  0.3% for the full-horizon integral, and 0.5% for the window expected count.
  These bounds are tighter than the sweep's 0.02-nat midpoint tolerance while
  acknowledging that DHARA deliberately stores a piecewise log-linear field.
"""
from __future__ import annotations

import math
import sys
from decimal import Decimal, localcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.ka_kshetra import integrator as I  # noqa: E402
from services.ka_kshetra.contracts import Segment  # noqa: E402
from services.ka_kshetra.dhara_sweep import dhara_build_segments  # noqa: E402


_D = Decimal
_DECIMAL_PRECISION = 60
_SIMPSON_INTERVALS = 4_096


def _decimal_simpson(fn, a: Decimal, b: Decimal, n: int) -> Decimal:
    """Composite Simpson quadrature independent of production helpers."""
    assert n > 0 and n % 2 == 0
    with localcontext() as ctx:
        ctx.prec = _DECIMAL_PRECISION
        h = (b - a) / _D(n)
        total = fn(a) + fn(b)
        for i in range(1, n):
            total += (_D(4) if i % 2 else _D(2)) * fn(a + _D(i) * h)
        return +(total * h / _D(3))


def _decimal_loglinear_integral(
    lambda_start: Decimal,
    lambda_end: Decimal,
    width: Decimal,
) -> Decimal:
    """Exact integral of exponential interpolation between two positive values."""
    with localcontext() as ctx:
        ctx.prec = _DECIMAL_PRECISION
        if lambda_start == lambda_end:
            return +(lambda_start * width)
        return +(
            width
            * (lambda_end - lambda_start)
            / (lambda_end.ln() - lambda_start.ln())
        )


def _segment(index: int, t0: float, t1: float, lambda0: float, lambda1: float) -> Segment:
    gamma = (math.log(lambda1) - math.log(lambda0)) / (t1 - t0)
    return Segment(
        index=index,
        t_start=t0,
        t_end=t1,
        alpha=math.log(lambda0),
        gamma=gamma,
    )


def test_integrator_respects_right_hand_clock_step_and_decimal_window_oracle() -> None:
    """A clock step is right-continuous without contaminating the left interval.

    Fixture (days, hazard/day): [0,2) is flat at 1/4; at the clock knot t=2
    the right-hand value jumps to 1; it rises log-linearly to 4 at t=4 and
    falls log-linearly to 1 at t=6.  At q=2 the exact window is [3,5], and
    its exact expected count is 4/ln(2).
    """
    segments = [
        _segment(0, 0.0, 2.0, 0.25, 0.25),
        _segment(1, 2.0, 4.0, 1.0, 4.0),
        _segment(2, 4.0, 6.0, 4.0, 1.0),
    ]

    assert I.lambda_at(segments, 2.0 - 1e-9) == pytest.approx(0.25, abs=1e-12)
    assert I.lambda_at(segments, 2.0) == pytest.approx(1.0, abs=1e-12)
    assert I.lambda_at(segments, -1e-9) == 0.0
    assert I.lambda_at(segments, 6.0 + 1e-9) == 0.0

    windows = I.find_windows(segments, q=2.0)
    assert len(windows) == 1
    window = windows[0]
    assert (window.t_start, window.t_end, window.t_peak) == pytest.approx(
        (3.0, 5.0, 4.0), abs=1e-12
    )

    with localcontext() as ctx:
        ctx.prec = _DECIMAL_PRECISION
        one_side = _decimal_loglinear_integral(_D(2), _D(4), _D(1))
        expected_count = +(one_side * _D(2))
        closed_form = +(_D(4) / _D(2).ln())
    assert expected_count == closed_form
    assert window.expected_count == pytest.approx(float(expected_count), rel=5e-13)
    assert I.find_windows(segments, q=4.0 + 1e-12) == []


class _NoEnvelopeKnots:
    def breakpoints(self) -> list[float]:
        return []


class _SuppressionCurvatureEvaluator:
    """Non-person DHARA fixture with true lambda(t)=1/2*(1-9t/10), t in [0,1]."""

    horizon_days = 1.0
    ladder: dict = {}
    envelopes = _NoEnvelopeKnots()
    _ladder_bsearch: dict = {}

    def lord_stacks_at(self, _t: float) -> dict:
        return {}

    @staticmethod
    def _lambda(t: float) -> float:
        return 0.5 * (1.0 - 0.9 * t)

    def ln_lambda(self, t: float) -> float:
        return math.log(self._lambda(t))

    def terms_at(self, t: float) -> SimpleNamespace:
        return SimpleNamespace(
            ln_lambda=self.ln_lambda(t),
            suppression_term=1.0 - 0.9 * t,
        )


def test_dhara_suppression_curvature_matches_decimal_oracle() -> None:
    """Suppression curvature, crossing, and expected count match an external oracle."""
    segments = dhara_build_segments(_SuppressionCurvatureEvaluator())
    assert any(segment.refinement_depth == 1 for segment in segments)

    with localcontext() as ctx:
        ctx.prec = _DECIMAL_PRECISION

        def true_lambda(t: Decimal) -> Decimal:
            return _D("0.5") * (_D(1) - _D("0.9") * t)

        oracle_full = _decimal_simpson(
            true_lambda, _D(0), _D(1), _SIMPSON_INTERVALS
        )
        assert oracle_full == _D(11) / _D(40)

        threshold = _D("0.25")
        oracle_crossing = (_D(1) - threshold / _D("0.5")) / _D("0.9")
        oracle_window_count = (
            _D("0.5") * oracle_crossing
            - _D("0.225") * oracle_crossing * oracle_crossing
        )
        assert oracle_crossing == _D(5) / _D(9)
        assert abs(oracle_window_count - _D(5) / _D(24)) < _D("1e-58")

    stored_full = I.integrate(segments, 0.0, 1.0)
    assert stored_full == pytest.approx(float(oracle_full), rel=0.003)

    windows = I.find_windows(segments, q=0.25)
    assert len(windows) == 1
    window = windows[0]
    assert window.t_start == pytest.approx(0.0, abs=1e-12)
    assert window.t_end == pytest.approx(float(oracle_crossing), abs=0.003)
    assert window.t_peak == pytest.approx(0.0, abs=1e-12)
    assert window.lambda_peak == pytest.approx(0.5, rel=1e-12)
    assert window.expected_count == pytest.approx(float(oracle_window_count), rel=0.005)

    # Negative case: a threshold above the true and stored maximum is empty.
    assert I.find_windows(segments, q=0.5 + 1e-12) == []
