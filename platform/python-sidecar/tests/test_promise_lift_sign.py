"""
tests/test_promise_lift_sign.py — Regression guard for Fix 1: _promise_lift sign inversion.

TDD: these tests were written BEFORE the fix. They describe the correct semantics.

Correct semantics per R6 / BA-P5B spec:
  - 'promised'  : grade is promise strength → lift > 1.0, rising with grade
  - 'conditional': same boost direction, same formula
  - 'denied'    : grade is denial strength  → lift < 1.0 for grade > 0,
                  lift ≈ 1.0 (neutral) for grade ≈ 0 (no denial evidence)
                  floor at 0.1 (never a complete gate)
  - 'no_evidence': lift == 1.0 always (no information)

The PREVIOUS bug (sign inversion in 'denied' branch):
  denied + grade=10 → max(0.20, 1.0 - 1.0*0.80) = 0.20 — under-suppressive
  denied + grade=0  → max(0.20, 1.0 - 0*0.80) = 1.0 — neutral (same as no_evidence!)
  So grade had ALMOST NO EFFECT on the suppression strength for mid-range grades.

The FIXED semantics:
  denied + grade=0  → 1.0  (neutral: no denial evidence → no suppression)
  denied + grade=5  → 0.5  (moderate denial → moderate suppression)
  denied + grade=10 → 0.1  (floor: strong denial → strong suppression, but never 0)
  promised + grade=0  → 1.0  (neutral: no promise evidence → no boost)
  promised + grade=10 → 2.5  (maximum boost)
  no_evidence → 1.0 always
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SIDECAR = Path(__file__).parent.parent
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))

from services.ph_nimitta.engine import _promise_lift  # noqa: E402


# ── 'denied' branch: grade should SUPPRESS (lift < 1.0) for grade > 0 ────────

def test_denied_grade_0_is_neutral():
    """denied + grade=0 means no denial evidence → lift should be 1.0 (neutral)."""
    result = _promise_lift(grade=0.0, status='denied')
    assert result == pytest.approx(1.0, abs=1e-6), (
        f"denied + grade=0 should be neutral (1.0); got {result}. "
        "grade=0 means zero denial evidence — should not suppress."
    )


def test_denied_grade_10_is_maximally_suppressive():
    """denied + grade=10 means strong denial → lift should be near floor (0.1)."""
    result = _promise_lift(grade=10.0, status='denied')
    assert result == pytest.approx(0.1, abs=1e-6), (
        f"denied + grade=10 should hit suppression floor (0.1); got {result}."
    )


def test_denied_grade_5_is_moderately_suppressive():
    """denied + grade=5 → lift should be 0.5 (halfway suppressed)."""
    result = _promise_lift(grade=5.0, status='denied')
    assert result == pytest.approx(0.5, abs=1e-6), (
        f"denied + grade=5 should give lift=0.5; got {result}."
    )


def test_denied_higher_grade_gives_lower_lift():
    """The denied branch must be MONOTONICALLY DECREASING with grade."""
    lifts = [_promise_lift(grade=float(g), status='denied') for g in range(11)]
    for i in range(1, len(lifts)):
        assert lifts[i] <= lifts[i - 1], (
            f"denied lift must decrease as grade increases; "
            f"lifts[{i-1}]={lifts[i-1]}, lifts[{i}]={lifts[i]}"
        )


def test_denied_lift_never_below_floor():
    """denied lift is floored at 0.1 — promise is a modifier, never a gate."""
    for grade in [8.0, 9.0, 10.0, 10.5, 12.0]:
        result = _promise_lift(grade=grade, status='denied')
        assert result >= 0.1, (
            f"denied lift floored at 0.1; grade={grade} → {result}"
        )


# ── 'promised' branch: grade should BOOST (lift > 1.0) for grade > 0 ─────────

def test_promised_grade_0_is_neutral():
    """promised + grade=0 → lift = 1.0 (no promise evidence → no boost)."""
    result = _promise_lift(grade=0.0, status='promised')
    assert result == pytest.approx(1.0, abs=1e-6), (
        f"promised + grade=0 should be neutral (1.0); got {result}."
    )


def test_promised_grade_10_is_maximum_boost():
    """promised + grade=10 → lift = 2.5 (full boost)."""
    result = _promise_lift(grade=10.0, status='promised')
    assert result == pytest.approx(2.5, abs=1e-6), (
        f"promised + grade=10 should give lift=2.5; got {result}."
    )


def test_promised_higher_grade_gives_higher_lift():
    """The promised branch must be MONOTONICALLY INCREASING with grade."""
    lifts = [_promise_lift(grade=float(g), status='promised') for g in range(11)]
    for i in range(1, len(lifts)):
        assert lifts[i] >= lifts[i - 1], (
            f"promised lift must increase as grade increases; "
            f"lifts[{i-1}]={lifts[i-1]}, lifts[{i}]={lifts[i]}"
        )


# ── 'conditional' branch: same boost direction as 'promised' ──────────────────

def test_conditional_grade_0_is_neutral():
    result = _promise_lift(grade=0.0, status='conditional')
    assert result == pytest.approx(1.0, abs=1e-6), (
        f"conditional + grade=0 should be neutral (1.0); got {result}."
    )


def test_conditional_grade_10_is_maximum_boost():
    result = _promise_lift(grade=10.0, status='conditional')
    assert result == pytest.approx(2.5, abs=1e-6), (
        f"conditional + grade=10 should give lift=2.5; got {result}."
    )


# ── 'no_evidence' branch: always neutral ──────────────────────────────────────

def test_no_evidence_grade_0_is_neutral():
    result = _promise_lift(grade=0.0, status='no_evidence')
    assert result == pytest.approx(1.0, abs=1e-6), (
        f"no_evidence + grade=0 should be 1.0; got {result}."
    )


def test_no_evidence_grade_10_is_still_neutral():
    """no_evidence is always 1.0 regardless of grade — no information."""
    result = _promise_lift(grade=10.0, status='no_evidence')
    assert result == pytest.approx(1.0, abs=1e-6), (
        f"no_evidence + grade=10 should still be 1.0; got {result}."
    )


# ── Direction-inversion anti-regression: denied ≠ promised ───────────────────

def test_denied_and_promised_are_opposite_directions():
    """denied + grade=8 must give a LOWER lift than promised + grade=8.
    This is the core sign-inversion regression guard."""
    denied_lift = _promise_lift(grade=8.0, status='denied')
    promised_lift = _promise_lift(grade=8.0, status='promised')
    assert denied_lift < 1.0, (
        f"denied + grade=8 must suppress (lift < 1.0); got {denied_lift}"
    )
    assert promised_lift > 1.0, (
        f"promised + grade=8 must boost (lift > 1.0); got {promised_lift}"
    )
    assert denied_lift < promised_lift, (
        f"denied lift ({denied_lift}) must be less than promised lift ({promised_lift})"
    )
