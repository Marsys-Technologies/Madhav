"""
test_upagrahas.py — Upagraha + outer planet computation tests.
FORENSIC: birth 1984-02-05, Bhubaneswar.
"""
from datetime import datetime, timedelta
import pytest

BIRTH = datetime(1984, 2, 5, 10, 43, 0)
LAT, LON, TZ = 20.27, 85.84, 330


def _get_birth_sunrise():
    from panchang_engine.timings import compute_sunrise_sunset
    from datetime import date
    return compute_sunrise_sunset(date(1984, 2, 5), LAT, LON, TZ)


def test_upagrahas_returns_8():
    from panchang_engine.upagrahas import compute_upagrahas
    sunrise_utc, sunset_utc = _get_birth_sunrise()
    planets = compute_upagrahas(sunrise_utc, sunset_utc, vara_id=1)  # Sunday
    names = {p.name for p in planets}
    assert "Gulika" in names, f"Missing Gulika. Got: {names}"
    assert "Mandi" in names, f"Missing Mandi. Got: {names}"
    assert len(planets) == 8, f"Expected 8 upagrahas, got {len(planets)}"


def test_outer_planets_returns_3():
    from panchang_engine.upagrahas import compute_outer_planets
    instant_utc = BIRTH - timedelta(minutes=TZ)
    planets = compute_outer_planets(instant_utc)
    names = {p.name for p in planets}
    assert "Uranus" in names
    assert "Neptune" in names
    assert "Pluto" in names
    assert len(planets) == 3


def test_dhuma_formula():
    """Dhuma = Sun_lon + 133.333; verify formula is applied."""
    from panchang_engine.upagrahas import compute_upagrahas_from_sun_lon
    results = compute_upagrahas_from_sun_lon(sun_lon=0.0, vara_id=1)
    dhuma = next((u for u in results if u.name == "Dhuma"), None)
    assert dhuma is not None, "Dhuma not found"
    assert abs(dhuma.longitude_sidereal - 133.333) < 0.01, (
        f"Expected ~133.333, got {dhuma.longitude_sidereal}"
    )


def test_upagrahas_have_valid_positions():
    from panchang_engine.upagrahas import compute_upagrahas
    sunrise_utc, sunset_utc = _get_birth_sunrise()
    planets = compute_upagrahas(sunrise_utc, sunset_utc, vara_id=1)
    for p in planets:
        assert 0 <= p.longitude_sidereal < 360, f"{p.name}: lon out of range: {p.longitude_sidereal}"
        assert 1 <= p.sign_id <= 12, f"{p.name}: sign_id out of range"
        assert 1 <= p.nakshatra_id <= 27, f"{p.name}: nakshatra_id out of range"
