"""Contract tests for the ka_graha_sancara compatibility facade."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.ka_graha_sancara import get_ephemeris, sky_ephemeris_at
from services.kala_core.sky import EphemerisCache, SkyConvention, ephemeris_at
from services.kala_core.sky import ephemeris as shared_ephemeris


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


@pytest.mark.parametrize("field", [
    "jd", "time_scale", "path", "backend", "flags", "flag_names", "node_model",
    "ayanamsha_id", "ayanamsha_deg", "convention_id",
])
def test_public_facade_carries_the_shared_instant_metadata(field: str) -> None:
    """Dropping any convention field must fail even if positions still agree."""
    instant = datetime(2024, 6, 21, 12, tzinfo=timezone.utc)
    shared = ephemeris_at(2460483.0, SkyConvention())
    public = get_ephemeris(instant)

    assert getattr(public, field, None) == getattr(shared.values[0], field)


def test_public_facade_carries_coverage() -> None:
    instant = datetime(2024, 6, 21, 12, tzinfo=timezone.utc)

    assert getattr(get_ephemeris(instant), "coverage", None) == ephemeris_at(
        2460483.0, SkyConvention()).coverage


def test_public_facade_declares_the_mean_node_used_for_rahu() -> None:
    public = get_ephemeris(datetime(2024, 6, 21, 12, tzinfo=timezone.utc))
    shared = ephemeris_at(2460483.0, SkyConvention(node_model="mean"))

    assert (getattr(public, "node_model", None), public.grahas["Rahu"].sidereal_lon_deg) == (
        "mean", shared.values[0].position("Rahu").longitude_deg)


def test_public_facade_preserves_unavailable_coverage_and_null() -> None:
    instant = datetime(1500, 1, 1, tzinfo=timezone.utc)
    jd = 2268923.5
    shared = ephemeris_at(jd, SkyConvention())
    public = get_ephemeris(instant)

    assert (public.source, public.grahas, getattr(public, "jd", None),
            getattr(public, "coverage", None), getattr(public, "null_reason", None),
            getattr(public, "ayanamsha_deg", None)) == (
        "information_unavailable", {}, jd, shared.coverage, shared.null_reason, None)


def test_public_facade_reuses_one_cache_for_the_same_jd_and_convention(monkeypatch) -> None:
    """Discarding the caller's cache repeats all nine Swiss computations."""
    cache = EphemerisCache()
    instant = datetime(2024, 6, 21, 12, tzinfo=timezone.utc)
    calls = []
    compute = shared_ephemeris._knots.calc_sidereal_lon_speed

    def counted_compute(*args, **kwargs):
        calls.append(args)
        return compute(*args, **kwargs)

    monkeypatch.setattr(shared_ephemeris._knots, "calc_sidereal_lon_speed", counted_compute)
    get_ephemeris(instant, _cache=cache)
    get_ephemeris(instant, ayanamsha="lahiri_chitrapaksha", _cache=cache)

    assert (cache.computes, len(calls)) == (1, 9)


def test_public_facade_cache_keeps_different_instants_separate() -> None:
    cache = EphemerisCache()
    instant = datetime(2024, 6, 21, 12, tzinfo=timezone.utc)
    first = get_ephemeris(instant, _cache=cache)
    second = get_ephemeris(instant + timedelta(hours=12), _cache=cache)

    assert (cache.computes, first.grahas["Moon"] == second.grahas["Moon"]) == (2, False)


def test_public_facade_declares_metadata_when_backend_files_are_missing(monkeypatch) -> None:
    """An in-range file failure carries attempted conventions, never positions."""
    def missing_backend(*args, **kwargs):
        raise shared_ephemeris._knots.EphemerisBackendError("Sun", 4, "missing Swiss files")

    monkeypatch.setattr(shared_ephemeris._knots, "calc_sidereal_lon_speed", missing_backend)
    public = get_ephemeris(datetime(2024, 6, 21, 12, tzinfo=timezone.utc))
    shared = ephemeris_at(2460483.0, SkyConvention())

    assert (public.source, public.grahas, public.jd, public.time_scale, public.backend,
            public.flags, public.flag_names, public.node_model, public.ayanamsha_id,
            public.ayanamsha_deg, public.convention_id, public.coverage, public.null_reason) == (
        "information_unavailable", {}, 2460483.0, "UT", shared.coverage.backend,
        shared_ephemeris.EPHE_FLAGS, shared_ephemeris.EPHE_FLAG_NAMES, "mean",
        "lahiri_chitrapaksha", None, SkyConvention().convention_id,
        shared.coverage, shared.null_reason)
