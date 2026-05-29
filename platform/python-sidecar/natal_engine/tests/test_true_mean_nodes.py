"""
test_true_mean_nodes.py — True Node + Mean Node both emitted separately.

Session E-03 [BUILD-ORCH-E-03].

Native birth: 1984-02-05 10:43 IST = 1984-02-05 05:13 UTC
JD_UT ≈ 2445733.717

Validates:
- compute_node_states() returns all 4 entries: rahu_true, ketu_true, rahu_mean, ketu_mean
- All 4 nodes have retro=True (astronomical convention: nodes always retrograde)
- ketu = rahu + 180° (mod 360) for both node types
- True node and mean node differ by a small amount (< 2° for native birth date)
- All 4 nodes have longitude in range [0, 360)
- All 4 nodes have sign + nakshatra fields
- compute_chart() exposes node_variants dict with the same 4 keys
- No NaN / Inf values in longitude fields
"""

from __future__ import annotations

import math

import pytest
import swisseph as swe

from natal_engine import compute_chart
from natal_engine.positions import compute_node_states, set_ayanamsha

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

# Ayanamsha value approx for Lahiri at native birth (used as sentinel)
_LAHIRI_AYAN_DEG = 23.5  # approximate; exact value set by swisseph


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _setup_lahiri() -> None:
    set_ayanamsha("lahiri")


@pytest.fixture(autouse=True)
def lahiri_ayanamsha():
    """Ensure Lahiri ayanamsha is active for all tests in this module."""
    _setup_lahiri()


@pytest.fixture
def node_states() -> dict:
    """Raw compute_node_states() output for native birth."""
    return compute_node_states(
        NATIVE_JD_UT,
        ayanamsha_deg=_LAHIRI_AYAN_DEG,
        geo_lat=20.27,
        geo_lon=85.84,
    )


@pytest.fixture
def chart_output() -> dict:
    """compute_chart() output for native birth (Lahiri ayanamsha via default jh_true_chitra).

    We call with explicit ayanamsha_id='lahiri' so the node_states fixture and
    the chart_output fixture use the same sidereal mode.
    """
    return compute_chart(NATIVE_INPUTS, ayanamsha_id="lahiri")


# ---------------------------------------------------------------------------
# Tests: compute_node_states() — 4 keys present
# ---------------------------------------------------------------------------

class TestNodeVariantsKeys:
    """All 4 node entries must be present in compute_node_states() output."""

    def test_rahu_true_key_present(self, node_states: dict) -> None:
        assert "rahu_true" in node_states, "rahu_true key missing"

    def test_ketu_true_key_present(self, node_states: dict) -> None:
        assert "ketu_true" in node_states, "ketu_true key missing"

    def test_rahu_mean_key_present(self, node_states: dict) -> None:
        assert "rahu_mean" in node_states, "rahu_mean key missing"

    def test_ketu_mean_key_present(self, node_states: dict) -> None:
        assert "ketu_mean" in node_states, "ketu_mean key missing"

    def test_exactly_four_entries(self, node_states: dict) -> None:
        assert len(node_states) == 4, f"Expected 4 entries, got {len(node_states)}"


# ---------------------------------------------------------------------------
# Tests: retrograde flag — nodes are always retrograde
# ---------------------------------------------------------------------------

class TestNodeRetrograde:
    """Both rahu and ketu for both node types must have retro=True."""

    def test_rahu_true_retrograde(self, node_states: dict) -> None:
        assert node_states["rahu_true"]["retro"] is True

    def test_ketu_true_retrograde(self, node_states: dict) -> None:
        assert node_states["ketu_true"]["retro"] is True

    def test_rahu_mean_retrograde(self, node_states: dict) -> None:
        assert node_states["rahu_mean"]["retro"] is True

    def test_ketu_mean_retrograde(self, node_states: dict) -> None:
        assert node_states["ketu_mean"]["retro"] is True


# ---------------------------------------------------------------------------
# Tests: antipodal relationship — ketu = rahu + 180° mod 360
# ---------------------------------------------------------------------------

class TestAntipodal:
    """Ketu must be exactly 180° away from Rahu (mod 360)."""

    def test_ketu_true_is_rahu_true_antipodal(self, node_states: dict) -> None:
        rahu_lon = node_states["rahu_true"]["longitude"]
        ketu_lon = node_states["ketu_true"]["longitude"]
        expected = (rahu_lon + 180.0) % 360.0
        assert math.isclose(ketu_lon, expected, abs_tol=1e-6), (
            f"ketu_true lon={ketu_lon:.4f} != rahu_true+180={expected:.4f}"
        )

    def test_ketu_mean_is_rahu_mean_antipodal(self, node_states: dict) -> None:
        rahu_lon = node_states["rahu_mean"]["longitude"]
        ketu_lon = node_states["ketu_mean"]["longitude"]
        expected = (rahu_lon + 180.0) % 360.0
        assert math.isclose(ketu_lon, expected, abs_tol=1e-6), (
            f"ketu_mean lon={ketu_lon:.4f} != rahu_mean+180={expected:.4f}"
        )


# ---------------------------------------------------------------------------
# Tests: true vs mean node difference (must be small but non-zero)
# ---------------------------------------------------------------------------

class TestTrueMeanDifference:
    """True node and mean node must differ by a small amount (< 2°)."""

    def test_rahu_true_vs_mean_within_2_degrees(self, node_states: dict) -> None:
        true_lon = node_states["rahu_true"]["longitude"]
        mean_lon = node_states["rahu_mean"]["longitude"]
        diff = abs(true_lon - mean_lon)
        diff = min(diff, 360.0 - diff)  # smallest arc
        assert diff < 2.0, (
            f"rahu_true ({true_lon:.4f}°) and rahu_mean ({mean_lon:.4f}°) "
            f"differ by {diff:.4f}° — expected < 2°"
        )

    def test_rahu_true_and_mean_are_not_identical(self, node_states: dict) -> None:
        """True and mean nodes should differ (they measure different things)."""
        true_lon = node_states["rahu_true"]["longitude"]
        mean_lon = node_states["rahu_mean"]["longitude"]
        # They should not be exactly identical (at native birth they differ by ~0.5°)
        assert true_lon != mean_lon, (
            "rahu_true and rahu_mean are identical — expected a small but non-zero difference"
        )


# ---------------------------------------------------------------------------
# Tests: longitude range [0, 360)
# ---------------------------------------------------------------------------

class TestLongitudeRange:
    """All 4 node longitudes must be in range [0, 360)."""

    @pytest.mark.parametrize("key", ["rahu_true", "ketu_true", "rahu_mean", "ketu_mean"])
    def test_longitude_in_range(self, node_states: dict, key: str) -> None:
        lon = node_states[key]["longitude"]
        assert 0.0 <= lon < 360.0, f"{key} longitude {lon:.4f} out of range [0, 360)"

    @pytest.mark.parametrize("key", ["rahu_true", "ketu_true", "rahu_mean", "ketu_mean"])
    def test_longitude_is_finite(self, node_states: dict, key: str) -> None:
        lon = node_states[key]["longitude"]
        assert math.isfinite(lon), f"{key} longitude is not finite: {lon}"


# ---------------------------------------------------------------------------
# Tests: required metadata fields present
# ---------------------------------------------------------------------------

class TestMetadataFields:
    """All 4 nodes must carry sign and nakshatra fields."""

    @pytest.mark.parametrize("key", ["rahu_true", "ketu_true", "rahu_mean", "ketu_mean"])
    def test_sign_field_present(self, node_states: dict, key: str) -> None:
        assert "sign" in node_states[key], f"{key} missing 'sign' field"
        assert isinstance(node_states[key]["sign"], str)
        assert len(node_states[key]["sign"]) > 0

    @pytest.mark.parametrize("key", ["rahu_true", "ketu_true", "rahu_mean", "ketu_mean"])
    def test_nakshatra_field_present(self, node_states: dict, key: str) -> None:
        assert "nakshatra" in node_states[key], f"{key} missing 'nakshatra' field"
        assert isinstance(node_states[key]["nakshatra"], str)
        assert len(node_states[key]["nakshatra"]) > 0

    @pytest.mark.parametrize("key", ["rahu_true", "ketu_true", "rahu_mean", "ketu_mean"])
    def test_pada_field_in_range(self, node_states: dict, key: str) -> None:
        pada = node_states[key]["pada"]
        assert 1 <= pada <= 4, f"{key} pada={pada} outside valid range 1–4"

    @pytest.mark.parametrize("key", ["rahu_true", "ketu_true", "rahu_mean", "ketu_mean"])
    def test_sign_index_in_range(self, node_states: dict, key: str) -> None:
        sign_idx = node_states[key]["sign_index"]
        assert 1 <= sign_idx <= 12, f"{key} sign_index={sign_idx} outside valid range 1–12"


# ---------------------------------------------------------------------------
# Tests: compute_chart() integration — node_variants in chart output
# ---------------------------------------------------------------------------

class TestComputeChartIntegration:
    """compute_chart() must expose node_variants with all 4 keys."""

    def test_chart_output_has_node_variants_key(self, chart_output: dict) -> None:
        assert "node_variants" in chart_output, "compute_chart() missing 'node_variants' key"

    def test_chart_node_variants_has_four_entries(self, chart_output: dict) -> None:
        nv = chart_output["node_variants"]
        assert len(nv) == 4, f"node_variants has {len(nv)} entries, expected 4"

    def test_chart_rahu_true_present(self, chart_output: dict) -> None:
        assert "rahu_true" in chart_output["node_variants"]

    def test_chart_ketu_true_present(self, chart_output: dict) -> None:
        assert "ketu_true" in chart_output["node_variants"]

    def test_chart_rahu_mean_present(self, chart_output: dict) -> None:
        assert "rahu_mean" in chart_output["node_variants"]

    def test_chart_ketu_mean_present(self, chart_output: dict) -> None:
        assert "ketu_mean" in chart_output["node_variants"]

    def test_chart_grahas_still_nine(self, chart_output: dict) -> None:
        """The main grahas array must still have exactly 9 entries (no regressions)."""
        assert len(chart_output["grahas"]) == 9, (
            f"grahas array has {len(chart_output['grahas'])} entries; expected 9"
        )

    def test_chart_node_variants_retro_true(self, chart_output: dict) -> None:
        """All 4 node_variants entries must have retro=True in chart output."""
        nv = chart_output["node_variants"]
        for key in ("rahu_true", "ketu_true", "rahu_mean", "ketu_mean"):
            assert nv[key]["retro"] is True, f"node_variants[{key}] retro is not True"
