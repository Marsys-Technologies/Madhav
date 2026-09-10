"""
tests/ka_kshetra/test_p3b_suppression.py — TDD gate tests for P3-b serving suppression.

Three mandatory gate tests (PURNA_KSHETRA_PLAN_v1_1.md P3-b, SM-Δ1 L-SERVE-B):

  1. test_suppress_expected_count_when_baseline_is_synthetic_true
     interval_from_window() with baseline_is_synthetic=True → expected_count is None

  2. test_emit_float_when_baseline_is_synthetic_false
     interval_from_window() with baseline_is_synthetic=False → expected_count == float(value)
     (Calibrated path: C-1 guard COMPLETELY UNCHANGED)

  3. test_emit_float_when_baseline_is_synthetic_absent
     interval_from_window() with no baseline_is_synthetic key → expected_count == float(value)
     (Backwards compatibility: pre-PR #1279 rows that have no column at all)

All tests are pure-Python; no database, no DB fixture, no real chart data.
"""
from __future__ import annotations

from datetime import datetime

import pytest

from services.ka_kshetra.stage8_spec import interval_from_window


# ── Shared minimal window fixture ──────────────────────────────────────────────

def _make_window(**overrides) -> dict:
    """Return a minimal kala_field_windows row dict sufficient for interval_from_window.

    Defaults represent a calibrated window (baseline_is_synthetic absent/False).
    Override any key via kwargs.
    """
    base = {
        "window_id": "wid-test-001",
        "event_class": "career_change",
        "t_start": 100.0,
        "t_end": 200.0,
        "t_peak": 150.0,
        "expected_count": 3.7,
        "null_p": 0.12,
        "confidence_tier": "calibrated",
        "temporal_shape": "interval",
        "precision_regime": "day_grade",
        "track_id": "domain:career",
    }
    base.update(overrides)
    return base


_T_ZERO = datetime(1984, 2, 5, 10, 43, 0)  # Abhisek Mohanty birth instant (IST, approximated)


# ── Gate 1: suppress when baseline_is_synthetic=True ─────────────────────────

class TestSuppressExpectedCountWhenSynthetic:
    """P3-b §N.8 earned-signal: expected_count is None for shape_only (synthetic) windows."""

    def test_suppress_expected_count_when_baseline_is_synthetic_true(self):
        """interval_from_window with baseline_is_synthetic=True → expected_count is None.

        This is the core P3-b gate: shape_only windows have no empirically derived
        expected_count and must not emit a float that looks like a calibrated prediction.
        """
        window = _make_window(baseline_is_synthetic=True)
        result = interval_from_window(window, t_zero=_T_ZERO, track_id="domain:career")
        assert result["expected_count"] is None, (
            "interval_from_window with baseline_is_synthetic=True must suppress "
            "expected_count to None — shape_only windows have no empirically derived count"
        )


# ── Gate 2: calibrated path emits float (C-1 guard unchanged) ────────────────

class TestEmitFloatWhenCalibrated:
    """Calibrated path (baseline_is_synthetic=False) must continue to emit float expected_count.

    C-1 guard: the existing calibrated flow is COMPLETELY UNCHANGED by P3-b.
    """

    def test_emit_float_when_baseline_is_synthetic_false(self):
        """interval_from_window with baseline_is_synthetic=False → expected_count == float(value)."""
        expected = 3.7
        window = _make_window(baseline_is_synthetic=False, expected_count=expected)
        result = interval_from_window(window, t_zero=_T_ZERO, track_id="domain:career")
        assert result["expected_count"] == float(expected), (
            f"Calibrated window (baseline_is_synthetic=False) must emit "
            f"expected_count={float(expected)!r}, got {result['expected_count']!r}"
        )
        assert result["expected_count"] is not None, (
            "Calibrated window must NEVER suppress expected_count to None"
        )

    def test_emit_float_is_a_float_type_when_calibrated(self):
        """The emitted value is an actual Python float, not an int or other type."""
        window = _make_window(baseline_is_synthetic=False, expected_count=5)
        result = interval_from_window(window, t_zero=_T_ZERO, track_id="domain:career")
        assert isinstance(result["expected_count"], float), (
            "expected_count for calibrated window must be a Python float "
            f"(got {type(result['expected_count']).__name__})"
        )


# ── Gate 3: absent baseline_is_synthetic key → backwards compat ──────────────

class TestEmitFloatWhenBaselineIsSyntheticAbsent:
    """Backwards compatibility: rows written before PR #1279 have no baseline_is_synthetic key.

    interval_from_window must treat the absent key as falsy (same as False),
    preserving the original calibrated behaviour for all pre-existing rows.
    """

    def test_emit_float_when_baseline_is_synthetic_absent(self):
        """interval_from_window with no baseline_is_synthetic key → expected_count == float(value)."""
        expected = 2.5
        window = _make_window(expected_count=expected)
        # Confirm key is actually absent
        assert "baseline_is_synthetic" not in window, (
            "Test fixture must not have baseline_is_synthetic key for this backwards-compat test"
        )
        result = interval_from_window(window, t_zero=_T_ZERO, track_id="domain:career")
        assert result["expected_count"] == float(expected), (
            f"Window with absent baseline_is_synthetic must emit expected_count={float(expected)!r} "
            f"(backwards compat), got {result['expected_count']!r}"
        )
        assert result["expected_count"] is not None, (
            "Absent baseline_is_synthetic must NEVER suppress expected_count to None"
        )
