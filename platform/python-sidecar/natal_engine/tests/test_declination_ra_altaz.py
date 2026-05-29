"""
test_declination_ra_altaz.py — Tests for equatorial (RA/declination) and
horizon (altitude/azimuth) coordinates added in BUILD-ORCH-E-02.

Native birth data: 1984-02-05 10:43 IST, Bhubaneswar
  JD ≈ swe.julday(1984, 2, 5, 5.2167)  [10:43 IST = 05:13 UT ≈ 5.2167h UT]
  geo_lat = 20.27°N, geo_lon = 85.84°E
"""
from __future__ import annotations

import swisseph as swe
import pytest

from natal_engine.positions import (
    compute_graha_states,
    get_equatorial,
    get_horizontal,
    set_ayanamsha,
    _OOB_THRESHOLD,
)
from natal_engine.schema import GrahaState, validate_chart_output


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NATIVE_JD = swe.julday(1984, 2, 5, 5.2167)  # native birth JD (UT)
NATIVE_LAT = 20.27   # Bhubaneswar geographic latitude
NATIVE_LON = 85.84   # Bhubaneswar geographic longitude

# Expected ranges / spot values
SUN_DEC_APPROX = -16.17   # Sun declination in Feb 1984 (south of equator)
SUN_DEC_TOLERANCE = 2.0   # ±2° tolerance for test assertion


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def set_lahiri():
    """Ensure Lahiri ayanamsha is set for all tests in this module."""
    set_ayanamsha("lahiri")
    yield


@pytest.fixture(scope="module")
def native_states():
    """Compute graha states once for the native birth moment."""
    set_ayanamsha("lahiri")
    return compute_graha_states(NATIVE_JD, geo_lat=NATIVE_LAT, geo_lon=NATIVE_LON)


# ---------------------------------------------------------------------------
# get_equatorial unit tests
# ---------------------------------------------------------------------------

class TestGetEquatorial:
    def test_returns_tuple_of_two_floats(self):
        result = get_equatorial(swe.SUN, NATIVE_JD)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(v, float) for v in result)

    def test_ra_in_range_0_360(self):
        ra, _ = get_equatorial(swe.SUN, NATIVE_JD)
        assert 0.0 <= ra < 360.0, f"RA out of range: {ra}"

    def test_declination_in_range_minus90_to_plus90(self):
        _, dec = get_equatorial(swe.SUN, NATIVE_JD)
        assert -90.0 <= dec <= 90.0, f"Declination out of range: {dec}"

    def test_sun_declination_south_in_february(self):
        """Sun is south of equator in Feb — declination should be negative."""
        _, dec = get_equatorial(swe.SUN, NATIVE_JD)
        assert dec < 0.0, f"Sun should be south of equator in Feb; got dec={dec}"

    def test_sun_declination_approx_minus17(self):
        """Sun declination in Feb 1984 should be around -16 to -18 degrees."""
        _, dec = get_equatorial(swe.SUN, NATIVE_JD)
        assert abs(dec - SUN_DEC_APPROX) < SUN_DEC_TOLERANCE, (
            f"Sun dec={dec:.3f} not within {SUN_DEC_TOLERANCE}° of {SUN_DEC_APPROX}"
        )

    def test_moon_equatorial_valid(self):
        ra, dec = get_equatorial(swe.MOON, NATIVE_JD)
        assert 0.0 <= ra < 360.0
        assert -90.0 <= dec <= 90.0

    def test_different_bodies_give_different_ra(self):
        """Sun and Moon should not share the same RA at any given moment."""
        ra_sun, _ = get_equatorial(swe.SUN, NATIVE_JD)
        ra_moon, _ = get_equatorial(swe.MOON, NATIVE_JD)
        assert abs(ra_sun - ra_moon) > 0.1, "Sun and Moon RA should differ"

    def test_rahu_node_equatorial_valid(self):
        """Mean node should yield a valid equatorial position."""
        ra, dec = get_equatorial(swe.MEAN_NODE, NATIVE_JD)
        assert 0.0 <= ra < 360.0
        assert -90.0 <= dec <= 90.0


# ---------------------------------------------------------------------------
# get_horizontal unit tests
# ---------------------------------------------------------------------------

class TestGetHorizontal:
    def test_returns_tuple_of_two_floats(self):
        result = get_horizontal(NATIVE_JD, NATIVE_LON, NATIVE_LAT, 315.0, 0.0)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(v, float) for v in result)

    def test_azimuth_in_range_0_360(self):
        az, _ = get_horizontal(NATIVE_JD, NATIVE_LON, NATIVE_LAT, 315.0, 0.0)
        assert 0.0 <= az < 360.0, f"Azimuth out of range: {az}"

    def test_altitude_in_range_minus90_to_plus90(self):
        _, alt = get_horizontal(NATIVE_JD, NATIVE_LON, NATIVE_LAT, 315.0, 0.0)
        assert -90.0 <= alt <= 90.0, f"Altitude out of range: {alt}"

    def test_sun_altitude_positive_at_native_birth(self):
        """Birth time is 10:43 IST — Sun should be above the horizon."""
        # Use tropical Sun ecliptic lon for azalt
        trop_result, _ = swe.calc_ut(NATIVE_JD, swe.SUN, swe.FLG_SWIEPH)
        trop_lon, trop_lat = trop_result[0] % 360.0, trop_result[1]
        _, alt = get_horizontal(NATIVE_JD, NATIVE_LON, NATIVE_LAT, trop_lon, trop_lat)
        assert alt > 0.0, f"Sun should be above horizon at 10:43 IST; got alt={alt:.3f}"

    def test_azimuth_north_convention(self):
        """Verify azimuth convention: result should be in [0, 360)."""
        az, _ = get_horizontal(NATIVE_JD, NATIVE_LON, NATIVE_LAT, 90.0, 0.0)
        assert 0.0 <= az < 360.0


# ---------------------------------------------------------------------------
# GrahaState field presence tests (schema-level)
# ---------------------------------------------------------------------------

class TestGrahaStateFields:
    def test_all_grahas_have_declination_deg(self, native_states):
        for g in native_states:
            assert hasattr(g, "declination_deg"), f"{g.name} missing declination_deg"
            assert isinstance(g.declination_deg, float)

    def test_all_grahas_have_right_ascension_deg(self, native_states):
        for g in native_states:
            assert hasattr(g, "right_ascension_deg"), f"{g.name} missing right_ascension_deg"
            assert isinstance(g.right_ascension_deg, float)

    def test_all_grahas_have_altitude_deg(self, native_states):
        for g in native_states:
            assert hasattr(g, "altitude_deg"), f"{g.name} missing altitude_deg"
            assert isinstance(g.altitude_deg, float)

    def test_all_grahas_have_azimuth_deg(self, native_states):
        for g in native_states:
            assert hasattr(g, "azimuth_deg"), f"{g.name} missing azimuth_deg"
            assert isinstance(g.azimuth_deg, float)

    def test_all_grahas_have_out_of_bounds(self, native_states):
        for g in native_states:
            assert hasattr(g, "out_of_bounds"), f"{g.name} missing out_of_bounds"
            assert isinstance(g.out_of_bounds, bool)

    def test_declination_within_valid_range_all_grahas(self, native_states):
        for g in native_states:
            assert -90.0 <= g.declination_deg <= 90.0, (
                f"{g.name} declination_deg={g.declination_deg} out of range"
            )

    def test_ra_within_valid_range_all_grahas(self, native_states):
        for g in native_states:
            assert 0.0 <= g.right_ascension_deg < 360.0, (
                f"{g.name} right_ascension_deg={g.right_ascension_deg} out of range"
            )

    def test_azimuth_within_valid_range_all_grahas(self, native_states):
        for g in native_states:
            assert 0.0 <= g.azimuth_deg < 360.0, (
                f"{g.name} azimuth_deg={g.azimuth_deg} out of range"
            )

    def test_altitude_within_valid_range_all_grahas(self, native_states):
        for g in native_states:
            assert -90.0 <= g.altitude_deg <= 90.0, (
                f"{g.name} altitude_deg={g.altitude_deg} out of range"
            )


# ---------------------------------------------------------------------------
# Spot-value tests for the native birth chart
# ---------------------------------------------------------------------------

class TestNativeBirthSpotValues:
    def test_sun_declination_approx(self, native_states):
        sun = next(g for g in native_states if g.name == "Sun")
        assert abs(sun.declination_deg - SUN_DEC_APPROX) < SUN_DEC_TOLERANCE, (
            f"Sun dec={sun.declination_deg:.3f}, expected ~{SUN_DEC_APPROX}"
        )

    def test_sun_not_out_of_bounds(self, native_states):
        """Sun rarely goes OOB — at birth (Feb 1984) it is firmly within bounds."""
        sun = next(g for g in native_states if g.name == "Sun")
        assert not sun.out_of_bounds, (
            f"Sun should not be OOB; dec={sun.declination_deg:.3f}"
        )

    def test_sun_above_horizon_at_birth(self, native_states):
        """10:43 IST is mid-morning — Sun must be above horizon."""
        sun = next(g for g in native_states if g.name == "Sun")
        assert sun.altitude_deg > 0.0, (
            f"Sun altitude={sun.altitude_deg:.3f} should be positive at 10:43 IST"
        )

    def test_oob_flag_consistent_with_declination(self, native_states):
        """out_of_bounds must equal |dec| > 23.5° for every graha."""
        for g in native_states:
            expected_oob = abs(g.declination_deg) > _OOB_THRESHOLD
            assert g.out_of_bounds == expected_oob, (
                f"{g.name}: out_of_bounds={g.out_of_bounds} but "
                f"|dec|={abs(g.declination_deg):.3f} vs threshold={_OOB_THRESHOLD}"
            )

    def test_nine_grahas_total(self, native_states):
        assert len(native_states) == 9

    def test_ketu_ra_is_rahu_plus_180(self, native_states):
        """Ketu RA should be Rahu RA + 180° (antipodal)."""
        rahu = next(g for g in native_states if g.name == "Rahu")
        ketu = next(g for g in native_states if g.name == "Ketu")
        expected_ketu_ra = (rahu.right_ascension_deg + 180.0) % 360.0
        assert abs(ketu.right_ascension_deg - expected_ketu_ra) < 0.01, (
            f"Ketu RA={ketu.right_ascension_deg:.4f} expected {expected_ketu_ra:.4f}"
        )

    def test_ketu_declination_is_negative_rahu(self, native_states):
        """Ketu declination should be the negative of Rahu's (antipodal)."""
        rahu = next(g for g in native_states if g.name == "Rahu")
        ketu = next(g for g in native_states if g.name == "Ketu")
        assert abs(ketu.declination_deg + rahu.declination_deg) < 0.01, (
            f"Ketu dec={ketu.declination_deg:.4f} != -Rahu dec={rahu.declination_deg:.4f}"
        )
