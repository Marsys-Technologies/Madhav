"""Contract tests for the ka_graha_sancara compatibility facade."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.ka_graha_sancara import get_ephemeris, sky_ephemeris_at
from services.kala_core.sky import SkyConvention, ephemeris_at


def test_facade_preserves_the_declared_backend_and_jd() -> None:
    """Replacing the facade with a different sky path must break this contract."""
    jd = 2460482.5
    convention = SkyConvention()

    facade = sky_ephemeris_at(jd, convention)
    direct = ephemeris_at(jd, convention)

    assert facade.available is True
    assert facade.values[0].jd == jd
    assert facade.values[0].backend == direct.values[0].backend


def test_facade_returns_information_unavailable_without_a_swiss_backend() -> None:
    """A missing backend must not be disguised as a computed position."""
    result = sky_ephemeris_at(2300000.0, SkyConvention())

    assert result.available is False
    assert result.null_reason.value == "information_unavailable"


def test_public_compatibility_facade_accepts_the_canonical_convention() -> None:
    """Replacing the public facade with the legacy engine rejects this L1 convention."""
    instant = datetime(2024, 6, 21, tzinfo=timezone.utc)

    result = get_ephemeris(instant, ayanamsha="lahiri_chitrapaksha")
    shared = ephemeris_at(2460482.5, SkyConvention())

    assert result.source == shared.values[0].backend
    assert result.grahas["Moon"].sidereal_lon_deg == shared.values[0].position("Moon").longitude_deg


def test_public_compatibility_facade_preserves_the_requested_instant() -> None:
    """Replacing the JD conversion with a date-only path makes this twelve-hour mutant pass."""
    start = datetime(2024, 6, 21, tzinfo=timezone.utc)
    end = start + timedelta(hours=12)

    start_moon = get_ephemeris(start).grahas["Moon"].sidereal_lon_deg
    end_moon = get_ephemeris(end).grahas["Moon"].sidereal_lon_deg

    assert start_moon != end_moon
