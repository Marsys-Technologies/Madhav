"""Contract tests for the ka_graha_sancara compatibility facade."""
from __future__ import annotations

from services.ka_graha_sancara import sky_ephemeris_at
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
