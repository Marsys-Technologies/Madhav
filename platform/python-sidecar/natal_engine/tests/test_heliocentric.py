"""
test_heliocentric.py — Heliocentric coordinate emission for all 9 grahas.

Session E-01 [BUILD-ORCH-E-01].

Native birth: 1984-02-05 10:43 IST = 1984-02-05 05:13 UTC
JD_UT ≈ 2445733.717
"""

from __future__ import annotations

import math

import pytest
import swisseph as swe

from natal_engine.positions import (
    NINE_GRAHAS_SWE,
    compute_graha_states,
    get_heliocentric,
    set_ayanamsha,
)
from natal_engine.schema import GrahaState

# ---------------------------------------------------------------------------
# Native birth Julian Day (UT)
# 1984-02-05 05:13 UTC → decimal hours = 5 + 13/60 = 5.21667
# ---------------------------------------------------------------------------
NATIVE_JD_UT = swe.julday(1984, 2, 5, 5 + 13 / 60)

# All 9 graha names for parametric tests
GRAHA_NAMES = [name for name, _ in NINE_GRAHAS_SWE] + ["Ketu"]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _setup_lahiri() -> None:
    """Set Lahiri ayanamsha (standard for most assertions)."""
    set_ayanamsha("lahiri")


# ---------------------------------------------------------------------------
# Tests: get_heliocentric() return type and range
# ---------------------------------------------------------------------------

class TestGetHeliocentricPrimitive:
    """Unit tests for the get_heliocentric() function directly."""

    def test_sun_returns_tuple_of_floats(self) -> None:
        lon, lat = get_heliocentric(swe.SUN, NATIVE_JD_UT)
        assert isinstance(lon, float)
        assert isinstance(lat, float)

    def test_sun_longitude_in_range(self) -> None:
        lon, lat = get_heliocentric(swe.SUN, NATIVE_JD_UT)
        # Sun heliocentric = Earth's position as seen from Sun → valid 0-360
        assert 0.0 <= lon < 360.0

    def test_sun_latitude_in_range(self) -> None:
        _, lat = get_heliocentric(swe.SUN, NATIVE_JD_UT)
        assert -90.0 <= lat <= 90.0

    def test_mars_longitude_in_range(self) -> None:
        lon, _ = get_heliocentric(swe.MARS, NATIVE_JD_UT)
        assert 0.0 <= lon < 360.0

    def test_mars_latitude_in_range(self) -> None:
        _, lat = get_heliocentric(swe.MARS, NATIVE_JD_UT)
        assert -90.0 <= lat <= 90.0

    def test_jupiter_longitude_in_range(self) -> None:
        lon, _ = get_heliocentric(swe.JUPITER, NATIVE_JD_UT)
        assert 0.0 <= lon < 360.0

    def test_venus_longitude_in_range(self) -> None:
        lon, _ = get_heliocentric(swe.VENUS, NATIVE_JD_UT)
        assert 0.0 <= lon < 360.0

    def test_saturn_longitude_in_range(self) -> None:
        lon, _ = get_heliocentric(swe.SATURN, NATIVE_JD_UT)
        assert 0.0 <= lon < 360.0

    def test_mercury_longitude_in_range(self) -> None:
        lon, _ = get_heliocentric(swe.MERCURY, NATIVE_JD_UT)
        assert 0.0 <= lon < 360.0

    def test_moon_sentinel_returns_zeros(self) -> None:
        """Moon returns (0.0, 0.0) sentinel because it has no heliocentric orbit."""
        lon, lat = get_heliocentric(swe.MOON, NATIVE_JD_UT)
        assert lon == 0.0
        assert lat == 0.0

    def test_rahu_sentinel_returns_zeros(self) -> None:
        """MEAN_NODE (Rahu) returns sentinel zeros."""
        lon, lat = get_heliocentric(swe.MEAN_NODE, NATIVE_JD_UT)
        assert lon == 0.0
        assert lat == 0.0


# ---------------------------------------------------------------------------
# Tests: compute_graha_states() heliocentric fields
# ---------------------------------------------------------------------------

class TestComputeGrahaStatesHeliocentricFields:
    """Integration tests: verify heliocentric fields are present + valid on all 9 grahas."""

    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        _setup_lahiri()

    @pytest.fixture
    def states(self) -> list[GrahaState]:
        return compute_graha_states(NATIVE_JD_UT)

    def test_all_nine_grahas_present(self, states: list[GrahaState]) -> None:
        names = {s.name for s in states}
        assert names == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}

    @pytest.mark.parametrize("graha_name", GRAHA_NAMES)
    def test_heliocentric_longitude_key_present(self, states: list[GrahaState], graha_name: str) -> None:
        state = next(s for s in states if s.name == graha_name)
        d = state.__dict__ if hasattr(state, "__dict__") else vars(state)
        assert "heliocentric_longitude" in d, f"{graha_name} missing heliocentric_longitude"

    @pytest.mark.parametrize("graha_name", GRAHA_NAMES)
    def test_heliocentric_latitude_key_present(self, states: list[GrahaState], graha_name: str) -> None:
        state = next(s for s in states if s.name == graha_name)
        d = state.__dict__ if hasattr(state, "__dict__") else vars(state)
        assert "heliocentric_latitude" in d, f"{graha_name} missing heliocentric_latitude"

    @pytest.mark.parametrize("graha_name", GRAHA_NAMES)
    def test_heliocentric_longitude_in_range(self, states: list[GrahaState], graha_name: str) -> None:
        state = next(s for s in states if s.name == graha_name)
        assert 0.0 <= state.heliocentric_longitude <= 360.0, (
            f"{graha_name} helio_lon {state.heliocentric_longitude} out of range"
        )

    @pytest.mark.parametrize("graha_name", GRAHA_NAMES)
    def test_heliocentric_latitude_in_range(self, states: list[GrahaState], graha_name: str) -> None:
        state = next(s for s in states if s.name == graha_name)
        assert -90.0 <= state.heliocentric_latitude <= 90.0, (
            f"{graha_name} helio_lat {state.heliocentric_latitude} out of range"
        )

    def test_jupiter_helio_lon_differs_from_geocentric(self, states: list[GrahaState]) -> None:
        """Jupiter's heliocentric longitude must differ meaningfully from geocentric.

        Geocentric includes the Earth's own orbital displacement vs heliocentric.
        At native birth the two should differ by > 0.1° (typically several degrees).
        """
        jup = next(s for s in states if s.name == "Jupiter")
        diff = abs(jup.heliocentric_longitude - jup.longitude_deg) % 360.0
        diff = min(diff, 360.0 - diff)  # smallest angular distance
        assert diff > 0.1, (
            f"Jupiter helio_lon ({jup.heliocentric_longitude:.4f}) suspiciously "
            f"close to geocentric ({jup.longitude_deg:.4f}); diff={diff:.4f}°"
        )

    def test_moon_helio_lon_mirrors_geocentric(self, states: list[GrahaState]) -> None:
        """Moon heliocentric lon must mirror its geocentric lon (our convention)."""
        moon = next(s for s in states if s.name == "Moon")
        assert math.isclose(moon.heliocentric_longitude, moon.longitude_deg, abs_tol=1e-6)

    def test_rahu_helio_lat_is_zero(self, states: list[GrahaState]) -> None:
        """Rahu is on the ecliptic plane → helio_lat must be 0.0."""
        rahu = next(s for s in states if s.name == "Rahu")
        assert rahu.heliocentric_latitude == 0.0

    def test_ketu_helio_lat_is_zero(self, states: list[GrahaState]) -> None:
        """Ketu is on the ecliptic plane → helio_lat must be 0.0."""
        ketu = next(s for s in states if s.name == "Ketu")
        assert ketu.heliocentric_latitude == 0.0

    def test_ketu_helio_lon_is_rahu_antipodal(self, states: list[GrahaState]) -> None:
        """Ketu heliocentric longitude must be Rahu's + 180° mod 360."""
        rahu = next(s for s in states if s.name == "Rahu")
        ketu = next(s for s in states if s.name == "Ketu")
        expected = (rahu.heliocentric_longitude + 180.0) % 360.0
        assert math.isclose(ketu.heliocentric_longitude, expected, abs_tol=1e-6)

    def test_chart_output_dict_has_helio_fields(self, states: list[GrahaState]) -> None:
        """Serialised dict (as emitted in chart_output) must carry the helio keys."""
        from dataclasses import asdict
        for state in states:
            d = asdict(state)
            assert "heliocentric_longitude" in d, f"{state.name}: key missing in asdict"
            assert "heliocentric_latitude" in d, f"{state.name}: key missing in asdict"

    def test_sun_helio_lon_is_valid_not_zero(self, states: list[GrahaState]) -> None:
        """Sun heliocentric lon = Earth's heliocentric position → must be > 0.1°.

        The Sun sits at the heliocentric origin; we substitute Earth's position
        (swe.EARTH + FLG_HELCTR).  Earth is never at exactly 0° on 1984-02-05
        (tropical heliocentric lon ≈ 135.6°).
        """
        sun = next(s for s in states if s.name == "Sun")
        # Earth's heliocentric longitude on native birth date is ~135.6° (tropical)
        assert sun.heliocentric_longitude > 0.1, (
            f"Sun helio_lon={sun.heliocentric_longitude} — expected Earth's position ~135°"
        )

    def test_no_nan_or_inf_in_helio_fields(self, states: list[GrahaState]) -> None:
        """No NaN or Inf values should appear in heliocentric fields."""
        for state in states:
            assert math.isfinite(state.heliocentric_longitude), (
                f"{state.name}: helio_lon is not finite"
            )
            assert math.isfinite(state.heliocentric_latitude), (
                f"{state.name}: helio_lat is not finite"
            )
