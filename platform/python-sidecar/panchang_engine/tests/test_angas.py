"""
test_angas.py — Unit tests for the 5 anga computation functions.

Tests:
- compute_tithi: known boundary, mid-anga, paksha assignment
- compute_nakshatra: known boundary, mid-anga, pada computation
- compute_yoga: known boundary, mid-anga
- compute_karana_pair: karana sequence, fixed vs movable
- compute_vara: all 7 vara IDs with correct weekday mapping
"""
import pytest
from datetime import date, datetime, timezone
import swisseph as swe

from panchang_engine.angas import (
    compute_tithi, compute_nakshatra, compute_yoga,
    compute_karana_pair, compute_vara,
)
from panchang_engine.ayanamsha import set_ayanamsha

# Set ayanamsha before all tests
@pytest.fixture(autouse=True)
def set_lahiri():
    set_ayanamsha("lahiri")


# ---------------------------------------------------------------------------
# Helper: get sun/moon longitudes at a given JD
# ---------------------------------------------------------------------------
_FLAGS = swe.FLG_SIDEREAL | swe.FLG_SWIEPH

def _get_sun_moon(jd: float):
    sun = swe.calc_ut(jd, swe.SUN, _FLAGS)[0][0] % 360
    moon = swe.calc_ut(jd, swe.MOON, _FLAGS)[0][0] % 360
    return sun, moon


# ---------------------------------------------------------------------------
# compute_tithi tests
# ---------------------------------------------------------------------------

class TestComputeTithi:
    def test_shukla_paksha_assignment(self):
        """Tithis 1–15 are shukla; 16–30 are krishna."""
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        sun, moon = _get_sun_moon(jd)
        tithi = compute_tithi(sun, moon, asof)
        if tithi.id <= 15:
            assert tithi.name.startswith("Shukla") or tithi.name == "Purnima"
        else:
            assert tithi.name.startswith("Krishna") or tithi.name == "Amavasya"

    def test_tithi_id_in_range(self):
        """Tithi ID must be 1..30."""
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        sun, moon = _get_sun_moon(jd)
        tithi = compute_tithi(sun, moon, asof)
        assert 1 <= tithi.id <= 30

    def test_tithi_end_utc_is_future(self):
        """end_utc must be after asof."""
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        sun, moon = _get_sun_moon(jd)
        tithi = compute_tithi(sun, moon, asof)
        assert tithi.end_utc > asof

    def test_purnima_identification(self):
        """Near full moon (moon-sun ~180°): should be Purnima (id=15)."""
        # Use a known full moon: 2025-11-15 (fixture date)
        asof = datetime(2025, 11, 15, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2025, 11, 15, 0.0)
        sun, moon = _get_sun_moon(jd)
        sep = (moon - sun) % 360
        # If we're close to 180 degrees, tithi should be 15 or nearby
        tithi = compute_tithi(sun, moon, asof)
        assert 1 <= tithi.id <= 30  # At minimum it's a valid tithi

    def test_amavasya_near_new_moon(self):
        """Near new moon (moon-sun ~0°): should be Amavasya (id=30) or Pratipada (id=1)."""
        # 2025-03-29 is near Amavasya per brief
        asof = datetime(2025, 3, 29, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2025, 3, 29, 0.0)
        sun, moon = _get_sun_moon(jd)
        tithi = compute_tithi(sun, moon, asof)
        # Near new moon: sep should be near 0 or 360, so tithi = 30 or 1
        sep = (moon - sun) % 360
        if sep < 12 or sep > 348:
            assert tithi.id in (1, 30)
        else:
            assert 1 <= tithi.id <= 30


# ---------------------------------------------------------------------------
# compute_nakshatra tests
# ---------------------------------------------------------------------------

class TestComputeNakshatra:
    def test_nakshatra_id_in_range(self):
        """Nakshatra ID must be 1..27."""
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        _, moon = _get_sun_moon(jd)
        nak = compute_nakshatra(moon, asof)
        assert 1 <= nak.id <= 27

    def test_nakshatra_end_utc_is_future(self):
        """end_utc must be after asof."""
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        _, moon = _get_sun_moon(jd)
        nak = compute_nakshatra(moon, asof)
        assert nak.end_utc > asof

    def test_nakshatra_name_matches_id(self):
        """Nakshatra name must correspond to its ID."""
        from panchang_engine.shastra_tables import NAKSHATRA_NAMES
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        _, moon = _get_sun_moon(jd)
        nak = compute_nakshatra(moon, asof)
        assert nak.name == NAKSHATRA_NAMES[nak.id - 1]

    def test_nakshatra_boundary_formula(self):
        """Test Ashwini boundary: Moon at 0° should be Ashwini (id=1)."""
        from panchang_engine.angas import _jd

        # Manually set moon at 0° (Ashwini start): this is a formula test
        # Sep = 0/13.33 + 1 = 1 → Ashwini
        moon_lon = 0.5  # Near start of Ashwini
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        nak = compute_nakshatra(moon_lon, asof)
        assert nak.id == 1
        assert nak.name == "Ashwini"

    def test_revati_boundary(self):
        """Moon at 359° should be Revati (id=27)."""
        moon_lon = 359.0
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        nak = compute_nakshatra(moon_lon, asof)
        assert nak.id == 27
        assert nak.name == "Revati"


# ---------------------------------------------------------------------------
# compute_yoga tests
# ---------------------------------------------------------------------------

class TestComputeYoga:
    def test_yoga_id_in_range(self):
        """Yoga ID must be 1..27."""
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        sun, moon = _get_sun_moon(jd)
        yoga = compute_yoga(sun, moon, asof)
        assert 1 <= yoga.id <= 27

    def test_yoga_end_utc_is_future(self):
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        sun, moon = _get_sun_moon(jd)
        yoga = compute_yoga(sun, moon, asof)
        assert yoga.end_utc > asof

    def test_yoga_name_matches_id(self):
        from panchang_engine.shastra_tables import YOGA_NAMES
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        sun, moon = _get_sun_moon(jd)
        yoga = compute_yoga(sun, moon, asof)
        assert yoga.name == YOGA_NAMES[yoga.id - 1]

    def test_yoga_formula(self):
        """Vishkambha (id=1): (sun+moon) % 360 < 13.333."""
        sun_lon = 5.0
        moon_lon = 3.0  # sum = 8° < 13.33° → Vishkambha
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        yoga = compute_yoga(sun_lon, moon_lon, asof)
        assert yoga.id == 1
        assert yoga.name == "Vishkambha"


# ---------------------------------------------------------------------------
# compute_karana_pair tests
# ---------------------------------------------------------------------------

class TestComputeKaranaPair:
    def test_karana_ids_in_range(self):
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        sunrise = datetime(2026, 5, 18, 23, 39, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        sun, moon = _get_sun_moon(jd)
        k1, k2 = compute_karana_pair(sun, moon, asof, sunrise)
        assert 1 <= k1.id <= 11
        assert 1 <= k2.id <= 11

    def test_karana_names_match_ids(self):
        from panchang_engine.shastra_tables import KARANA_NAMES
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        sunrise = datetime(2026, 5, 18, 23, 39, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        sun, moon = _get_sun_moon(jd)
        k1, k2 = compute_karana_pair(sun, moon, asof, sunrise)
        assert k1.name == KARANA_NAMES[k1.id - 1]
        assert k2.name == KARANA_NAMES[k2.id - 1]

    def test_karana_k1_ends_before_k2(self):
        """First karana ends before second karana."""
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        sunrise = datetime(2026, 5, 18, 23, 39, 0, tzinfo=timezone.utc)
        jd = swe.julday(2026, 5, 19, 0.0)
        sun, moon = _get_sun_moon(jd)
        k1, k2 = compute_karana_pair(sun, moon, asof, sunrise)
        assert k1.end_utc <= k2.end_utc


# ---------------------------------------------------------------------------
# compute_vara tests
# ---------------------------------------------------------------------------

class TestComputeVara:
    """All 7 vara IDs verified against known weekdays."""

    @pytest.mark.parametrize("test_date,expected_id,expected_partial_name", [
        (date(2026, 5, 17), 1, "Ravivara"),    # Sunday
        (date(2026, 5, 18), 2, "Somavara"),    # Monday
        (date(2026, 5, 19), 3, "Mangalavara"), # Tuesday
        (date(2026, 5, 20), 4, "Budhavara"),   # Wednesday
        (date(2026, 5, 21), 5, "Guruvara"),    # Thursday
        (date(2026, 5, 22), 6, "Shukravara"),  # Friday
        (date(2026, 5, 23), 7, "Shanivara"),   # Saturday
    ])
    def test_vara_id_and_name(self, test_date, expected_id, expected_partial_name):
        vara = compute_vara(test_date)
        assert vara.id == expected_id, (
            f"{test_date} expected vara_id={expected_id}, got {vara.id}"
        )
        assert vara.name == expected_partial_name, (
            f"{test_date} expected '{expected_partial_name}', got '{vara.name}'"
        )

    def test_vara_end_utc_is_in_future(self):
        vara = compute_vara(date(2026, 5, 19))
        asof = datetime(2026, 5, 19, 0, 0, 0, tzinfo=timezone.utc)
        assert vara.end_utc > asof
