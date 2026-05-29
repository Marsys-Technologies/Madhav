"""
test_ayanamsha_registry.py — Tests for ayanamsha_utils.py
BUILD-ORCH-A-01 | G20 multi-ayanamsha support

JD 2445337.0 corresponds to native birth date 1984-02-05 (Bhubaneswar, IST).
Expected ayanamsha range for all sidereal systems: [20, 30] degrees.
"""

import pytest
import sys
import os

# Ensure pipeline package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ayanamsha_utils import ayanamsha_value, all_ayanamsha_values, SUPPORTED_AYANAMSHAS

# JD for native birth date: 1984-02-05 ~10:43 IST = ~05:13 UTC
# JD 2445337.0 is an approximate value for that date (noon UT)
NATIVE_BIRTH_JD = 2445337.0

ALL_AYANAMSHA_IDS = ["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"]


class TestAyanamshaValueReturnType:
    """ayanamsha_value() returns a float in the expected range for all supported IDs."""

    @pytest.mark.parametrize("ayanamsha_id", ALL_AYANAMSHA_IDS)
    def test_returns_float(self, ayanamsha_id: str) -> None:
        result = ayanamsha_value(NATIVE_BIRTH_JD, ayanamsha_id)
        assert isinstance(result, float), (
            f"{ayanamsha_id}: expected float, got {type(result)}"
        )

    @pytest.mark.parametrize("ayanamsha_id", ALL_AYANAMSHA_IDS)
    def test_value_in_range_20_to_30(self, ayanamsha_id: str) -> None:
        result = ayanamsha_value(NATIVE_BIRTH_JD, ayanamsha_id)
        assert 20.0 <= result <= 30.0, (
            f"{ayanamsha_id}: value {result:.4f} not in expected range [20, 30]"
        )


class TestAyanamshaConvergence:
    """All 5 canonical ayanamshas should agree within 3 degrees of each other."""

    def test_all_within_3_degrees_of_each_other(self) -> None:
        values = all_ayanamsha_values(NATIVE_BIRTH_JD)
        all_vals = list(values.values())
        min_val = min(all_vals)
        max_val = max(all_vals)
        spread = max_val - min_val
        assert spread <= 3.0, (
            f"Ayanamsha spread {spread:.4f} exceeds 3 degrees. Values: {values}"
        )

    def test_all_5_ayanamshas_computed(self) -> None:
        values = all_ayanamsha_values(NATIVE_BIRTH_JD)
        assert set(values.keys()) == set(ALL_AYANAMSHA_IDS), (
            f"Missing ayanamshas: {set(ALL_AYANAMSHA_IDS) - set(values.keys())}"
        )

    def test_lahiri_near_23_5(self) -> None:
        """Lahiri at 1984 should be approximately 23.5 degrees."""
        result = ayanamsha_value(NATIVE_BIRTH_JD, "lahiri")
        # Lahiri is well-characterised; allow +/- 0.5 degrees for JD approximation
        assert 23.0 <= result <= 24.0, (
            f"Lahiri ayanamsha {result:.4f} outside expected 23.0–24.0 range"
        )


class TestUnknownAyanamshaError:
    """Unknown ayanamsha_id should raise ValueError."""

    def test_unknown_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown ayanamsha_id"):
            ayanamsha_value(NATIVE_BIRTH_JD, "fagan_bradley")

    def test_empty_string_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown ayanamsha_id"):
            ayanamsha_value(NATIVE_BIRTH_JD, "")

    def test_misspelled_id_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown ayanamsha_id"):
            ayanamsha_value(NATIVE_BIRTH_JD, "lahri")


class TestSupportedAyanamshasList:
    """SUPPORTED_AYANAMSHAS contains exactly the 5 canonical IDs."""

    def test_exactly_5_supported(self) -> None:
        assert len(SUPPORTED_AYANAMSHAS) == 5

    def test_contains_all_canonical_ids(self) -> None:
        assert set(SUPPORTED_AYANAMSHAS) == set(ALL_AYANAMSHA_IDS)
