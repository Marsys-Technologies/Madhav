"""Day mapping for any longitude (SUR-RB-6, yardstick 3.1): civil date D -> the sunrise that starts on D at the birthplace.

Sunrise is computed in UT from latitude and longitude; the civil date is the LOCAL SOLAR date (UT + lon/15 h), never a tz
database. Checked against an independent low-precision sunrise equation (NOAA series, no ephemeris) at far-east and
far-west longitudes and at high latitude, and against the repo's own IST sunrise for an Indian place.
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone

import pytest

pytest.importorskip("swisseph")

from services.rulebook.engine import constants as K  # noqa: E402
from services.rulebook.engine import dayatom  # noqa: E402


def noaa_sunrise_utc(d: date, lat: float, lon: float):
    """Independent: NOAA general solar position series. Returns the sunrise of LOCAL SOLAR date d as a UT datetime, or None."""
    doy = d.timetuple().tm_yday
    g = 2 * math.pi / 365.0 * (doy - 1)  # fractional year evaluated at local solar noon of d
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (
        0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
        - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g)
    )
    phi = math.radians(lat)
    c = (math.cos(math.radians(90.833)) - math.sin(phi) * math.sin(decl)) / (math.cos(phi) * math.cos(decl))
    if c < -1 or c > 1:
        return None
    ha = math.degrees(math.acos(c))
    minutes = 720.0 - 4.0 * (lon + ha) - eqt  # minutes after 00:00 UT of the calendar date d (may fall outside 0..1440)
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(minutes=minutes)


def solar_date_of(utc: datetime, lon: float) -> date:
    return (utc + timedelta(hours=lon / 15.0)).date()


PLACES = [
    ("east_170E_equator", 0.0, 170.0),
    ("east_170E_mid_north", 45.0, 170.0),
    ("east_170E_mid_south", -35.0, 170.0),
    ("west_170W_equator", 0.0, -170.0),
    ("west_170W_mid_north", 45.0, -170.0),
    ("west_170W_mid_south", -35.0, -170.0),
    ("antimeridian_west_179_9W", 10.0, -179.9),
    ("antimeridian_east_179_9E", 10.0, 179.9),
    ("india", 20.27, 85.84),
    ("greenwich", 51.5, 0.0),
    ("high_lat_64N", 64.1, -21.9),
    ("high_lat_64S", -64.0, 60.0),
]
YEAR = [date(2003, 1, 1) + timedelta(days=i) for i in range(365)]


@pytest.mark.parametrize("name,lat,lon", PLACES, ids=[p[0] for p in PLACES])
def test_every_civil_date_gets_one_sunrise_on_that_local_solar_date_matching_an_independent_formula(name, lat, lon):
    prov = dayatom.SolarSunrise(lat, lon)
    tol = 6.0 if abs(lat) > 60 else 3.0  # minutes; the series is a low-precision cross-check
    prev = None
    for d in YEAR:
        got = prov.sunrise_utc(d)
        want = noaa_sunrise_utc(d, lat, lon)
        assert (got is None) == (want is None), (name, d)
        if got is None:
            continue
        assert solar_date_of(got, lon) == d, (name, d, got)
        assert abs((got - want).total_seconds()) / 60.0 < tol, (name, d, got, want)
        if prev is not None:
            assert 0 < (got - prev).total_seconds() <= 26 * 3600  # consecutive days, one sunrise each, strictly increasing
        prev = got


def test_far_east_and_far_west_sunrises_fall_on_different_ut_dates_from_the_civil_date():
    d = date(2003, 3, 21)
    east = dayatom.SolarSunrise(0.0, 170.0).sunrise_utc(d)  # local 06:00 = UT 18:40 of the previous day
    west = dayatom.SolarSunrise(0.0, -170.0).sunrise_utc(d)  # local 06:00 = UT 17:20 of the same day
    assert east.date() == date(2003, 3, 20) and abs((east - datetime(2003, 3, 20, 18, 40, tzinfo=timezone.utc)).total_seconds()) < 12 * 60
    assert west.date() == date(2003, 3, 21) and abs((west - datetime(2003, 3, 21, 17, 20, tzinfo=timezone.utc)).total_seconds()) < 12 * 60
    # Two places 340 degrees apart in longitude: the east one rises ~23h20m earlier in UT than the west one on the SAME civil date
    assert 21 * 3600 < (west - east).total_seconds() < 25 * 3600


def test_the_tz_database_is_not_consulted():
    """No zoneinfo access happens: the provider needs only latitude and longitude."""
    import zoneinfo

    class Boom:
        def __getattr__(self, n):  # pragma: no cover - would fail the test if touched
            raise AssertionError("tz database used")

    real = zoneinfo.ZoneInfo
    zoneinfo.ZoneInfo = Boom()  # type: ignore[assignment]
    try:
        assert dayatom.SolarSunrise(-35.0, 170.0).sunrise_utc(date(2003, 6, 1)) is not None
    finally:
        zoneinfo.ZoneInfo = real  # type: ignore[assignment]


def test_polar_day_and_polar_night_give_no_sunrise_not_a_made_up_one():
    prov = dayatom.SolarSunrise(70.0, 25.0)  # northern Norway
    assert prov.sunrise_utc(date(2003, 6, 21)) is None  # midnight sun
    assert prov.sunrise_utc(date(2003, 12, 21)) is None  # polar night
    assert prov.sunrise_utc(date(2003, 3, 21)) is not None
    no_rise = [d for d in YEAR if prov.sunrise_utc(d) is None]
    assert 60 < len(no_rise) < 160
    # the days with a sunrise next to a gap still map to their own solar date
    for d in YEAR:
        u = prov.sunrise_utc(d)
        if u is not None:
            assert solar_date_of(u, 25.0) == d


def test_grid_with_no_sunrise_days_reads_not_assessed_for_time_varying_states():
    from services.rulebook.engine.dayatom import build_grid

    prov = dayatom.SolarSunrise(70.0, 25.0)
    g = build_grid(date(2003, 5, 1), date(2003, 8, 31), prov)
    assert g.no_sunrise_days > 30 and g.sunrise_jd.count(None) == g.no_sunrise_days
    known = [j for j in g.sunrise_jd if j is not None]
    assert all(b > a for a, b in zip(known, known[1:]))


def test_matches_the_repos_ist_sunrise_for_an_indian_place_every_day_of_a_leap_year():
    from services.rulebook.engine.dayatom import PanchangEngineSunrise

    solar, ist = dayatom.SolarSunrise(20.27, 85.84), PanchangEngineSunrise(20.27, 85.84)
    d = date(2004, 1, 1)
    while d.year == 2004:
        assert abs((solar.sunrise_utc(d) - ist.sunrise_utc(d)).total_seconds()) <= 1.5, d  # the IST civil date and the solar date coincide here
        d += timedelta(days=1)


def test_invalid_coordinates_are_refused():
    for lat, lon in ((91, 0), (0, 181), (float("nan"), 0)):
        with pytest.raises(ValueError):
            dayatom.SolarSunrise(lat, lon)
