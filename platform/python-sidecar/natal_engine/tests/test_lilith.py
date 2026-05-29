"""
test_lilith.py — Mean Lilith + True Lilith both emitted.

Session E-04 [BUILD-ORCH-E-04].

Native birth: 1984-02-05 10:43 IST = 1984-02-05 05:13 UTC
JD_UT ≈ 2445733.717

Validates:
- compute_lilith_states() returns both entries: lilith_mean, lilith_true
- Both have longitude in range [0, 360)
- Both have sign + nakshatra + pada fields
- Mean and True Lilith differ (they measure different orbital constructs)
- abs difference between mean and true Lilith < 30° (within ~1 sign; typically < 5°)
- lilith_mean['retro'] is a bool (mean apogee is always prograde: retro=False)
- lilith_true['retro'] is a bool (osculating apogee can vary direction)
- All longitude values are finite (no NaN / Inf)
- compute_chart() exposes 'lilith_variants' key with both sub-keys
- chart_output['grahas'] still has exactly 9 entries (no regression)
"""

from __future__ import annotations

import math

import pytest
import swisseph as swe

from natal_engine import compute_chart
from natal_engine.positions import compute_lilith_states, set_ayanamsha

# ---------------------------------------------------------------------------
# Native birth Julian Day (UT)
# 1984-02-05 05:13 UTC → decimal hours = 5 + 13/60
# ---------------------------------------------------------------------------
NATIVE_JD_UT = swe.julday(1984, 2, 5, 5 + 13 / 60)

# Native birth inputs (used for compute_chart integration tests)
NATIVE_INPUTS: dict = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "place_name": "Bhubaneswar, Odisha, India",
    "subject_label": "Abhisek Mohanty",
}

# Approximate Lahiri ayanamsha at native birth
_LAHIRI_AYAN_DEG = 23.5


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def lahiri_ayanamsha():
    """Ensure Lahiri ayanamsha is active for all tests in this module."""
    set_ayanamsha("lahiri")


@pytest.fixture
def lilith_states() -> dict:
    """Raw compute_lilith_states() output for native birth."""
    return compute_lilith_states(
        NATIVE_JD_UT,
        ayanamsha_deg=_LAHIRI_AYAN_DEG,
        geo_lat=20.27,
        geo_lon=85.84,
    )


@pytest.fixture
def chart_output() -> dict:
    """compute_chart() output for native birth (Lahiri ayanamsha)."""
    return compute_chart(NATIVE_INPUTS, ayanamsha_id="lahiri")


# ---------------------------------------------------------------------------
# Tests: compute_lilith_states() — 2 keys present
# ---------------------------------------------------------------------------

class TestLilithKeys:
    """Both Lilith entries must be present in compute_lilith_states() output."""

    def test_lilith_mean_key_present(self, lilith_states: dict) -> None:
        assert "lilith_mean" in lilith_states, "lilith_mean key missing"

    def test_lilith_true_key_present(self, lilith_states: dict) -> None:
        assert "lilith_true" in lilith_states, "lilith_true key missing"

    def test_exactly_two_entries(self, lilith_states: dict) -> None:
        assert len(lilith_states) == 2, (
            f"Expected 2 entries (lilith_mean + lilith_true), got {len(lilith_states)}"
        )


# ---------------------------------------------------------------------------
# Tests: longitude range and finiteness
# ---------------------------------------------------------------------------

class TestLilithLongitudeRange:
    """Both Lilith longitudes must be finite and in range [0, 360)."""

    @pytest.mark.parametrize("key", ["lilith_mean", "lilith_true"])
    def test_longitude_in_range(self, lilith_states: dict, key: str) -> None:
        lon = lilith_states[key]["longitude"]
        assert 0.0 <= lon < 360.0, f"{key} longitude {lon:.4f} out of range [0, 360)"

    @pytest.mark.parametrize("key", ["lilith_mean", "lilith_true"])
    def test_longitude_is_finite(self, lilith_states: dict, key: str) -> None:
        lon = lilith_states[key]["longitude"]
        assert math.isfinite(lon), f"{key} longitude is not finite: {lon}"


# ---------------------------------------------------------------------------
# Tests: mean vs true Lilith difference
# ---------------------------------------------------------------------------

class TestMeanTrueLilithDifference:
    """Mean and True Lilith must differ and be within ~1 sign of each other."""

    def test_mean_and_true_lilith_differ(self, lilith_states: dict) -> None:
        """Mean apogee and osculating apogee measure different orbital constructs."""
        mean_lon = lilith_states["lilith_mean"]["longitude"]
        true_lon = lilith_states["lilith_true"]["longitude"]
        assert mean_lon != true_lon, (
            "lilith_mean and lilith_true have identical longitudes — "
            "expected a non-zero difference"
        )

    def test_mean_true_diff_within_30_degrees(self, lilith_states: dict) -> None:
        """True Lilith oscillates around Mean Lilith; diff typically < 5°, always < 30°."""
        mean_lon = lilith_states["lilith_mean"]["longitude"]
        true_lon = lilith_states["lilith_true"]["longitude"]
        diff = abs(mean_lon - true_lon)
        diff = min(diff, 360.0 - diff)  # smallest arc
        assert diff < 30.0, (
            f"lilith_mean ({mean_lon:.4f}°) and lilith_true ({true_lon:.4f}°) "
            f"differ by {diff:.4f}° — expected < 30°"
        )


# ---------------------------------------------------------------------------
# Tests: retro field is a bool
# ---------------------------------------------------------------------------

class TestLilithRetroField:
    """retro must be a Python bool for both Lilith points."""

    def test_lilith_mean_retro_is_bool(self, lilith_states: dict) -> None:
        retro = lilith_states["lilith_mean"]["retro"]
        assert isinstance(retro, bool), (
            f"lilith_mean retro is {type(retro).__name__}, expected bool"
        )

    def test_lilith_true_retro_is_bool(self, lilith_states: dict) -> None:
        retro = lilith_states["lilith_true"]["retro"]
        assert isinstance(retro, bool), (
            f"lilith_true retro is {type(retro).__name__}, expected bool"
        )

    def test_lilith_mean_is_prograde(self, lilith_states: dict) -> None:
        """Mean apogee moves prograde (always positive speed) by astronomical definition."""
        speed = lilith_states["lilith_mean"]["speed"]
        assert speed > 0.0, (
            f"lilith_mean speed={speed:.6f} — mean apogee is always prograde (speed > 0)"
        )

    def test_lilith_mean_retro_false(self, lilith_states: dict) -> None:
        """Mean apogee is always prograde, so retro must be False."""
        assert lilith_states["lilith_mean"]["retro"] is False, (
            "lilith_mean retro should be False (mean apogee is always prograde)"
        )


# ---------------------------------------------------------------------------
# Tests: required metadata fields present
# ---------------------------------------------------------------------------

class TestLilithMetadataFields:
    """Both Liliths must carry sign, nakshatra, pada, sign_index fields."""

    @pytest.mark.parametrize("key", ["lilith_mean", "lilith_true"])
    def test_sign_field_present(self, lilith_states: dict, key: str) -> None:
        assert "sign" in lilith_states[key], f"{key} missing 'sign' field"
        assert isinstance(lilith_states[key]["sign"], str)
        assert len(lilith_states[key]["sign"]) > 0

    @pytest.mark.parametrize("key", ["lilith_mean", "lilith_true"])
    def test_nakshatra_field_present(self, lilith_states: dict, key: str) -> None:
        assert "nakshatra" in lilith_states[key], f"{key} missing 'nakshatra' field"
        assert isinstance(lilith_states[key]["nakshatra"], str)
        assert len(lilith_states[key]["nakshatra"]) > 0

    @pytest.mark.parametrize("key", ["lilith_mean", "lilith_true"])
    def test_pada_field_in_range(self, lilith_states: dict, key: str) -> None:
        pada = lilith_states[key]["pada"]
        assert 1 <= pada <= 4, f"{key} pada={pada} outside valid range 1–4"

    @pytest.mark.parametrize("key", ["lilith_mean", "lilith_true"])
    def test_sign_index_in_range(self, lilith_states: dict, key: str) -> None:
        sign_idx = lilith_states[key]["sign_index"]
        assert 1 <= sign_idx <= 12, f"{key} sign_index={sign_idx} outside valid range 1–12"


# ---------------------------------------------------------------------------
# Tests: compute_chart() integration — lilith_variants in chart output
# ---------------------------------------------------------------------------

class TestComputeChartLilithIntegration:
    """compute_chart() must expose lilith_variants with both keys."""

    def test_chart_output_has_lilith_variants_key(self, chart_output: dict) -> None:
        assert "lilith_variants" in chart_output, (
            "compute_chart() missing 'lilith_variants' key"
        )

    def test_chart_lilith_variants_has_two_entries(self, chart_output: dict) -> None:
        lv = chart_output["lilith_variants"]
        assert len(lv) == 2, (
            f"lilith_variants has {len(lv)} entries, expected 2"
        )

    def test_chart_lilith_mean_present(self, chart_output: dict) -> None:
        assert "lilith_mean" in chart_output["lilith_variants"]

    def test_chart_lilith_true_present(self, chart_output: dict) -> None:
        assert "lilith_true" in chart_output["lilith_variants"]

    def test_chart_grahas_still_nine(self, chart_output: dict) -> None:
        """The main grahas array must still have exactly 9 entries (no regression)."""
        assert len(chart_output["grahas"]) == 9, (
            f"grahas array has {len(chart_output['grahas'])} entries; expected 9"
        )

    def test_chart_lilith_mean_longitude_in_range(self, chart_output: dict) -> None:
        lon = chart_output["lilith_variants"]["lilith_mean"]["longitude"]
        assert 0.0 <= lon < 360.0, f"chart lilith_mean longitude {lon:.4f} out of range"

    def test_chart_lilith_true_longitude_in_range(self, chart_output: dict) -> None:
        lon = chart_output["lilith_variants"]["lilith_true"]["longitude"]
        assert 0.0 <= lon < 360.0, f"chart lilith_true longitude {lon:.4f} out of range"

    def test_chart_node_variants_still_present(self, chart_output: dict) -> None:
        """E-03 node_variants must not be displaced by the E-04 addition."""
        assert "node_variants" in chart_output, (
            "compute_chart() missing 'node_variants' key — E-03 regression"
        )
        assert len(chart_output["node_variants"]) == 4, (
            "node_variants must still have 4 entries (E-03 regression check)"
        )
