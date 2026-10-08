"""KA-1e ephemeris oracles: two day paths, canonical ayanāṃśa, no silent
Moshier, memo cache keyed by JD and convention (ALGO 3.18)."""
from __future__ import annotations

import os
from datetime import date

import pytest

from services.gochara_kernel import knots
from services.kala_core.sky import ephemeris as eph
from services.kala_core.sky import DailyRow, EphemerisCache, SkyConvention, row_jd
from services.kala_core.vocab import NullReason

J0 = 2459000.0
NUTATION_DEG = 16.5 / 3600.0      # the frame difference the real paths show
RATES = {"Sun": 0.9856, "Moon": 13.176, "Saturn": 0.0335}
BODIES = tuple(RATES)
NOON_2020_06_01 = 2459002.0     # JD of 2020-06-01 12:00 UT, independent of row_jd


def true_sidereal(body: str, jd: float) -> float:
    return (40.0 * BODIES.index(body) + RATES[body] * (jd - J0)) % 360.0


def ayanamsha(jd: float) -> float:
    return 24.0 + (jd - J0) * 1.4e-5


@pytest.fixture
def seam(monkeypatch):
    """A fake Swiss: sidereal positions by the flag path, ayanāṃśa by the mode path."""
    import swisseph as swe

    calls: list[tuple[str, float]] = []
    state = {"retflag": 2}

    def calc(body, jd, _path):
        calls.append((body, jd))
        return (true_sidereal(body, jd) - NUTATION_DEG) % 360.0, RATES[body], state["retflag"]

    monkeypatch.setattr(knots, "calc_sidereal_lon_speed", calc)
    monkeypatch.setattr(swe, "set_sid_mode", lambda _mode: None)
    monkeypatch.setattr(swe, "get_ayanamsa_ut", ayanamsha)
    return calls, state


def stored_row(day: date, epoch_jd: float) -> DailyRow:
    tropical = {b: ((true_sidereal(b, epoch_jd) + ayanamsha(epoch_jd)) % 360.0, RATES[b])
                for b in BODIES}
    return DailyRow(day, tropical, backend="swieph", node_model="mean")


def arcsec(a: float, b: float) -> float:
    d = (a - b) % 360.0
    return min(d, 360.0 - d) * 3600.0


def test_both_day_paths_agree_at_one_jd(seam) -> None:
    day = date(2020, 6, 1)
    noon = NOON_2020_06_01
    assert row_jd(day) == noon                          # the row's abscissa is noon UT
    from_row = eph.ephemeris_from_row(stored_row(day, noon), noon, bodies=BODIES)
    instant = eph.ephemeris_at(noon, bodies=BODIES)
    assert from_row.available and instant.available
    a, b = from_row.values[0], instant.values[0]
    assert a.backend == b.backend == "swieph" and a.jd == b.jd
    for body in BODIES:
        assert arcsec(a.position(body).longitude_deg,
                      b.position(body).longitude_deg) <= eph.PATH_AGREEMENT_ARCSEC


def test_twelve_hour_epoch_mutant_fails(seam) -> None:
    """A row read at 00:00 UT (the old path B epoch) is not the noon row."""
    day = date(2020, 6, 1)
    noon = NOON_2020_06_01
    row = stored_row(day, noon)
    assert not eph.ephemeris_from_row(row, noon - 0.5, bodies=BODIES).available
    assert eph.ephemeris_from_row(row, noon, bodies=BODIES).available
    # And a row that really was computed at midnight disagrees beyond tolerance.
    midnight_row = stored_row(day, noon - 0.5)
    moved = eph.ephemeris_from_row(midnight_row, noon, bodies=BODIES).values[0]
    instant = eph.ephemeris_at(noon, bodies=BODIES).values[0]
    assert arcsec(moved.position("Moon").longitude_deg,
                  instant.position("Moon").longitude_deg) > eph.PATH_AGREEMENT_ARCSEC


def test_canonical_ayanamsha_is_accepted(seam) -> None:
    convention = SkyConvention()
    assert convention.ayanamsha_id == "lahiri_chitrapaksha" and convention.computable
    result = eph.ephemeris_at(J0, convention, bodies=BODIES)
    assert result.available
    assert result.values[0].ayanamsha_id == "lahiri_chitrapaksha"
    assert result.values[0].ayanamsha_deg == pytest.approx(ayanamsha(J0))


def test_absent_swiss_data_is_unavailable_never_moshier(seam) -> None:
    _calls, state = seam
    state["retflag"] = 4                                 # Swiss fell back to Moshier
    result = eph.ephemeris_at(J0, bodies=BODIES)
    assert result.values == ()
    assert result.null_reason is NullReason.INFORMATION_UNAVAILABLE
    assert result.coverage.covered is None


def test_moon_file_probe_failure_is_unavailable(monkeypatch) -> None:
    def calc(body, jd, _path):
        raise knots.EphemerisBackendError(body, 2, detail="semo file missing")

    monkeypatch.setattr(knots, "calc_sidereal_lon_speed", calc)
    result = eph.ephemeris_at(J0, bodies=("Moon",))
    assert result.null_reason is NullReason.INFORMATION_UNAVAILABLE


def test_outside_the_file_interval_is_unavailable(seam) -> None:
    calls, _state = seam
    result = eph.ephemeris_at(eph.SWISS_FILE_INTERVAL_JD[1] + 1.0, bodies=BODIES)
    assert result.null_reason is NullReason.INFORMATION_UNAVAILABLE and calls == []


def test_conventions_the_seam_cannot_compute_are_inapplicable(seam) -> None:
    assert eph.ephemeris_at(J0, SkyConvention("raman")).null_reason \
        is NullReason.METHOD_INAPPLICABLE
    assert eph.ephemeris_at(J0, SkyConvention(node_model="true")).null_reason \
        is NullReason.METHOD_INAPPLICABLE
    with pytest.raises(ValueError, match="unknown L1 ayanamsha"):
        SkyConvention("guess")


def test_cache_key_includes_jd_and_convention(seam) -> None:
    cache = EphemerisCache()
    canonical, alias = SkyConvention(), SkyConvention("lahiri")
    assert canonical.convention_id != alias.convention_id
    first = eph.ephemeris_at(J0, canonical, bodies=BODIES, cache=cache)
    assert eph.ephemeris_at(J0, canonical, bodies=BODIES, cache=cache) is first
    assert cache.computes == 1
    swapped = eph.ephemeris_at(J0, alias, bodies=BODIES, cache=cache)
    assert cache.computes == 2
    assert swapped.values[0].ayanamsha_id == "lahiri"
    assert swapped.values[0].convention_id == alias.convention_id
    eph.ephemeris_at(J0 + 1.0, canonical, bodies=BODIES, cache=cache)
    assert cache.computes == 3


def test_unavailable_answers_are_not_memoised(seam) -> None:
    _calls, state = seam
    cache = EphemerisCache()
    state["retflag"] = 4
    assert not eph.ephemeris_at(J0, bodies=BODIES, cache=cache).available
    state["retflag"] = 2
    assert eph.ephemeris_at(J0, bodies=BODIES, cache=cache).available


@pytest.mark.skipif(not os.environ.get("SE_EPHE_PATH"), reason="NOT_RUN: no pinned .se1 corpus")
def test_real_swiss_day_paths_agree() -> None:
    """The stored row is Swiss tropical at noon UT, as ephemeris_daily holds it."""
    import swisseph as swe

    day = date(2020, 1, 1)
    noon = row_jd(day)
    ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Saturn": swe.SATURN}
    instant = eph.ephemeris_at(noon, bodies=tuple(ids))
    if not instant.available:
        pytest.skip("NOT_RUN: Swiss files not served at this instant")
    tropical = {}
    for body, sid in ids.items():
        out, _flag = swe.calc_ut(noon, sid, swe.FLG_SWIEPH | swe.FLG_SPEED)
        tropical[body] = (out[0], out[3])
    row = DailyRow(day, tropical, backend="swieph", node_model="mean")
    stored = eph.ephemeris_from_row(row, noon, bodies=tuple(ids)).values[0]
    for body in ids:
        assert arcsec(stored.position(body).longitude_deg,
                      instant.values[0].position(body).longitude_deg) <= eph.PATH_AGREEMENT_ARCSEC
