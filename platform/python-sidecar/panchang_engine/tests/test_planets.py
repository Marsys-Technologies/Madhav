"""
test_planets.py — Unit tests for planetary state computation.

Tests the 9-graha contract:
- Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
- Rahu uses MEAN_NODE (Phase 4B mandate); Ketu = Rahu + 180°
- Sun never retrograde; Mean Node always retrograde
- Rahu and Ketu never combust
- TRUE_NODE assertion guard fires on direct call
"""
import pytest
import swisseph as swe
from panchang_engine.planets import compute_all_grahas, compute_planet_state
from panchang_engine.ayanamsha import set_ayanamsha

# J2000 Julian Day
J2000 = 2451545.0

@pytest.fixture(autouse=True)
def set_lahiri():
    set_ayanamsha("lahiri")


class TestNineGrahaContract:
    def test_returns_nine_states(self):
        """compute_all_grahas must return exactly 9 PlanetState objects."""
        planets = compute_all_grahas(J2000)
        assert len(planets) == 9

    def test_planet_names_in_order(self):
        """Must return Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu."""
        planets = compute_all_grahas(J2000)
        names = [p.name for p in planets]
        expected = ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                    "Venus", "Saturn", "Rahu", "Ketu"]
        assert names == expected

    def test_sun_never_retrograde(self):
        """Sun should never be marked retrograde."""
        planets = compute_all_grahas(J2000)
        sun = next(p for p in planets if p.name == "Sun")
        assert sun.retrograde is False

    def test_mean_node_always_retrograde(self):
        """Rahu (Mean Node) is always retrograde in the mean approximation."""
        planets = compute_all_grahas(J2000)
        rahu = next(p for p in planets if p.name == "Rahu")
        assert rahu.retrograde is True

    def test_ketu_always_retrograde(self):
        """Ketu (derived from Rahu) should also be marked retrograde."""
        planets = compute_all_grahas(J2000)
        ketu = next(p for p in planets if p.name == "Ketu")
        assert ketu.retrograde is True

    def test_rahu_ketu_180_apart(self):
        """Rahu and Ketu must be exactly 180° apart (derived)."""
        planets = compute_all_grahas(J2000)
        rahu = next(p for p in planets if p.name == "Rahu")
        ketu = next(p for p in planets if p.name == "Ketu")
        diff = abs(rahu.longitude_sidereal - ketu.longitude_sidereal)
        if diff > 180:
            diff = 360 - diff
        assert abs(diff - 180.0) < 0.001, (
            f"Rahu ({rahu.longitude_sidereal}°) and Ketu ({ketu.longitude_sidereal}°) "
            f"are {diff}° apart, expected 180°."
        )

    def test_rahu_never_combust(self):
        """Rahu (shadow planet) must never be marked combust."""
        planets = compute_all_grahas(J2000)
        rahu = next(p for p in planets if p.name == "Rahu")
        assert rahu.combust is False

    def test_ketu_never_combust(self):
        """Ketu (shadow planet) must never be marked combust."""
        planets = compute_all_grahas(J2000)
        ketu = next(p for p in planets if p.name == "Ketu")
        assert ketu.combust is False

    def test_sun_never_combust(self):
        """Sun cannot combust itself."""
        planets = compute_all_grahas(J2000)
        sun = next(p for p in planets if p.name == "Sun")
        assert sun.combust is False

    def test_longitudes_in_valid_range(self):
        """All sidereal longitudes must be 0..360."""
        planets = compute_all_grahas(J2000)
        for p in planets:
            assert 0.0 <= p.longitude_sidereal < 360.0, (
                f"{p.name}: longitude {p.longitude_sidereal} out of 0..360 range"
            )

    def test_sign_ids_in_valid_range(self):
        """sign_id must be 1..12."""
        planets = compute_all_grahas(J2000)
        for p in planets:
            assert 1 <= p.sign_id <= 12, (
                f"{p.name}: sign_id {p.sign_id} out of 1..12 range"
            )

    def test_nakshatra_ids_in_valid_range(self):
        """nakshatra_id must be 1..27."""
        planets = compute_all_grahas(J2000)
        for p in planets:
            assert 1 <= p.nakshatra_id <= 27, (
                f"{p.name}: nakshatra_id {p.nakshatra_id} out of 1..27 range"
            )

    def test_nakshatra_pada_in_valid_range(self):
        """nakshatra_pada must be 1..4."""
        planets = compute_all_grahas(J2000)
        for p in planets:
            assert 1 <= p.nakshatra_pada <= 4, (
                f"{p.name}: nakshatra_pada {p.nakshatra_pada} out of 1..4 range"
            )


class TestMeanNodeAssertion:
    def test_true_node_raises_assertion(self):
        """compute_planet_state must raise AssertionError if TRUE_NODE is passed.
        This is the Phase 4B guard against accidental regression."""
        with pytest.raises(AssertionError, match="MEAN_NODE"):
            compute_planet_state(swe.TRUE_NODE, J2000)


class TestRecentDate:
    """Verify the 9-graha contract on a recent date (2026-05-19)."""

    def test_nine_grahas_recent_date(self):
        jd = swe.julday(2026, 5, 19, 6.0)  # ~6am UTC = ~11:30am IST
        planets = compute_all_grahas(jd)
        assert len(planets) == 9
        rahu = next(p for p in planets if p.name == "Rahu")
        ketu = next(p for p in planets if p.name == "Ketu")
        diff = abs(rahu.longitude_sidereal - ketu.longitude_sidereal)
        if diff > 180:
            diff = 360 - diff
        assert abs(diff - 180.0) < 0.001
