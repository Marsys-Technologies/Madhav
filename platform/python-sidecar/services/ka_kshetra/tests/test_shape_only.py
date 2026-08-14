"""
tests/ka_kshetra/test_shape_only.py — CI gates for P3-a shape_only tier

Three mandatory gate tests (DHARA_ENGINE_SPEC_v1_0.md §4.1, SM-R-10):

  1. test_baseline_is_synthetic_tag
     hazard.baseline_rate(shape_only=True) → (rate, True) — is_synthetic tag
     hazard.baseline_rate(shape_only=False) → (rate, False) — calibrated path
     The tag from baseline_rate propagates into HazardTerms.baseline_is_synthetic
     via hazard.evaluate(); tested here via baseline_rate directly (the lowest-level
     unit) so the test has no dependency on lord_stacks/weights plumbing.

  2. test_require_baseline_shape_only_returns_constant
     stage4_field.require_baseline(None, ..., shape_only=True) → SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT
     stage4_field.require_baseline(None, ..., shape_only=False) → raises ClassSkipped
     stage4_field.require_baseline(positive, ..., shape_only=True) → returns the calibrated value
     (i.e. calibrated prior is NEVER silently overridden by shape_only)

  3. test_calibrated_c1_guard_unchanged
     With shape_only=False (the default), all original ClassSkipped paths still fire:
     - None lifetime_count → ClassSkipped('no_class_prior_row')
     - non-positive lifetime_count → ClassSkipped('class_prior_not_positive')

All tests are pure-Python; no database, no DB fixture, no real chart data.
"""
from __future__ import annotations

import math
import pytest

from services.ka_kshetra.contracts import SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT
from services.ka_kshetra.stage4_field import (
    ClassSkipped,
    require_baseline,
)
import services.ka_kshetra.hazard as hazard


# ── Gate 1: baseline_is_synthetic tag via hazard.baseline_rate ────────────────

class TestBaselineIsSyntheticTag:
    """P3-a §N.8 earned-signal: baseline_is_synthetic tag produced by hazard.baseline_rate.

    hazard.baseline_rate() is the lowest-level unit that produces the
    (rate, is_synthetic) tuple — this is the detector behind the §N.8 tag.
    The is_synthetic bool propagates up through hazard.evaluate() into
    HazardTerms.baseline_is_synthetic and then to writer._ClassContext.
    """

    def test_shape_only_true_tags_synthetic(self):
        """baseline_rate(shape_only=True) → (rate, True) — tag is TRUE."""
        rate, is_synthetic = hazard.baseline_rate(0.0, shape_only=True)
        assert is_synthetic is True, (
            "baseline_rate(shape_only=True) must return is_synthetic=True "
            "(§N.8 earned-signal: this is the detector behind the tag)"
        )

    def test_calibrated_path_tags_not_synthetic(self):
        """baseline_rate with a valid lifetime (shape_only=False) → (rate, False)."""
        rate, is_synthetic = hazard.baseline_rate(10.0, shape_only=False)
        assert is_synthetic is False, (
            "Calibrated path (shape_only=False) must return is_synthetic=False"
        )

    def test_calibrated_path_default_kwarg_tags_not_synthetic(self):
        """baseline_rate without shape_only kwarg defaults to False tag."""
        rate, is_synthetic = hazard.baseline_rate(10.0)
        assert is_synthetic is False

    def test_shape_only_uses_synthetic_constant_not_calibrated_prior(self):
        """When shape_only=True, the actual rate comes from SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT.

        Synthetic λ⁰ = 1.0 / DAYS_PER_CENTURY ≈ 2.74e-5 events/day.
        Calibrated λ⁰ for 999 lifetime events = 999 / DAYS_PER_CENTURY ≈ 0.0274 events/day.
        These differ by ~1000× — the synthetic constant must win when shape_only=True.
        """
        expected_lam0 = SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT / hazard.DAYS_PER_CENTURY

        # shape_only=True: synthetic constant must produce the rate, not the 999 arg
        rate_synthetic, is_synthetic = hazard.baseline_rate(999.0, shape_only=True)
        assert is_synthetic is True
        assert math.isclose(rate_synthetic, expected_lam0, rel_tol=1e-12), (
            f"Expected synthetic rate {expected_lam0:.6e}, got {rate_synthetic:.6e} "
            "— calibrated prior was used instead of SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT"
        )

        # For contrast: calibrated path with same 999.0 produces a much larger rate
        rate_calibrated, is_cal = hazard.baseline_rate(999.0, shape_only=False)
        assert is_cal is False
        assert rate_calibrated > rate_synthetic * 100, (
            "Calibrated rate for 999 lifetime events must be much larger than synthetic"
        )


# ── Gate 2: require_baseline shape_only synthetic constructor ─────────────────

class TestRequireBaselineShapeOnly:
    """require_baseline() returns SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT for shape_only classes."""

    def test_none_lifetime_shape_only_true_returns_constant(self):
        result = require_baseline(None, 'test_class', shape_only=True)
        assert result == SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT, (
            f"require_baseline(None, shape_only=True) must return "
            f"SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT ({SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT}), "
            f"got {result}"
        )

    def test_non_positive_lifetime_shape_only_true_returns_constant(self):
        """A non-positive prior (edge case) with shape_only=True also returns synthetic constant."""
        result = require_baseline(0.0, 'test_class', shape_only=True)
        assert result == SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT

        result_neg = require_baseline(-5.0, 'test_class', shape_only=True)
        assert result_neg == SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT

    def test_nan_lifetime_shape_only_true_returns_constant(self):
        result = require_baseline(float('nan'), 'test_class', shape_only=True)
        assert result == SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT

    def test_positive_lifetime_shape_only_true_uses_calibrated_value(self):
        """CRITICAL INVARIANT: a class WITH a calibrated prior is NEVER overridden.

        Even when shape_only=True is passed, a valid lifetime_count takes precedence.
        The writer's _is_shape_only_class() enforces that shape_only=True is only
        passed when lifetime is None — but hazard/stage4 must also be correct here.
        """
        calibrated_value = 12.5
        result = require_baseline(calibrated_value, 'test_class', shape_only=True)
        assert result == calibrated_value, (
            "A class with a valid calibrated prior must NEVER be overridden by "
            "SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT — calibrated path must win"
        )

    def test_synthetic_constant_value_is_1_0(self):
        """Pin: SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT == 1.0.

        This value is referenced in the migration comment and spec §4.1.
        Changing it silently would cause cross-snapshot null_p diffs.
        """
        assert SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT == 1.0, (
            "SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT must be exactly 1.0 (pinned per spec §4.1). "
            "Changing this value produces cross-snapshot diffs in null_p comparisons."
        )


# ── Gate 3: calibrated C-1 guard COMPLETELY UNCHANGED ────────────────────────

class TestCalibratedC1GuardUnchanged:
    """The C-1 guard (ClassSkipped when no prior) is COMPLETELY UNCHANGED for shape_only=False.

    This is the non-negotiable safety guarantee from DHARA_ENGINE_SPEC_v1_0.md §4.1.
    """

    def test_none_lifetime_default_raises_class_skipped(self):
        """Default shape_only=False: None lifetime_count → ClassSkipped."""
        with pytest.raises(ClassSkipped) as exc_info:
            require_baseline(None, 'foreign_settlement', shape_only=False)
        assert exc_info.value.reason == 'no_class_prior_row', (
            "C-1 guard must raise ClassSkipped with reason='no_class_prior_row' "
            "when lifetime_count is None and shape_only=False"
        )

    def test_none_lifetime_no_kwarg_raises_class_skipped(self):
        """shape_only defaults to False — the original call signature must still work."""
        with pytest.raises(ClassSkipped):
            require_baseline(None, 'marriage')

    def test_non_positive_lifetime_default_raises_class_skipped(self):
        """C-1 guard: non-positive lifetime_count with shape_only=False → ClassSkipped."""
        with pytest.raises(ClassSkipped) as exc_info:
            require_baseline(0.0, 'foreign_settlement', shape_only=False)
        assert exc_info.value.reason == 'class_prior_not_positive'

        with pytest.raises(ClassSkipped) as exc_info2:
            require_baseline(-1.0, 'foreign_settlement', shape_only=False)
        assert exc_info2.value.reason == 'class_prior_not_positive'

    def test_nan_lifetime_default_raises_class_skipped(self):
        """NaN is not positive-finite → ClassSkipped with shape_only=False."""
        with pytest.raises(ClassSkipped) as exc_info:
            require_baseline(float('nan'), 'foreign_settlement', shape_only=False)
        assert exc_info.value.reason == 'class_prior_not_positive'

    def test_hazard_baseline_rate_calibrated_raises_on_nan(self):
        """hazard.baseline_rate with NaN and shape_only=False raises ValueError.

        This confirms the calibrated path does NOT silently substitute the
        synthetic constant when given invalid input. The C-1 discipline is
        enforced at both the baseline_rate level (ValueError) and the
        require_baseline level (ClassSkipped) — two independent guards.
        """
        with pytest.raises(ValueError):
            hazard.baseline_rate(float('nan'), shape_only=False)

    def test_hazard_baseline_rate_default_raises_on_none_equivalent(self):
        """baseline_rate with shape_only=False and non-positive lifetime → ValueError."""
        with pytest.raises(ValueError):
            hazard.baseline_rate(0.0, shape_only=False)

        with pytest.raises(ValueError):
            hazard.baseline_rate(float('nan'), shape_only=False)

    def test_hazard_baseline_rate_shape_only_true_returns_tuple(self):
        """baseline_rate(shape_only=True) returns (synthetic_rate, True) — not a float."""
        result = hazard.baseline_rate(0.0, shape_only=True)
        assert isinstance(result, tuple), "baseline_rate must return tuple[float, bool]"
        rate, is_synthetic = result
        assert is_synthetic is True
        expected = SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT / hazard.DAYS_PER_CENTURY
        assert math.isclose(rate, expected, rel_tol=1e-12), (
            f"Synthetic rate must be {expected:.6e}, got {rate:.6e}"
        )

    def test_hazard_baseline_rate_calibrated_returns_tuple_false(self):
        """baseline_rate with a valid lifetime (shape_only=False) returns (rate, False)."""
        result = hazard.baseline_rate(10.0)
        assert isinstance(result, tuple)
        rate, is_synthetic = result
        assert is_synthetic is False
        expected = 10.0 / hazard.DAYS_PER_CENTURY
        assert math.isclose(rate, expected, rel_tol=1e-12)
