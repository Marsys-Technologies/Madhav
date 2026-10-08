"""KA-1e public answer contract: every answer names its instant, time scale,
backend, flags, node model, ayanāṃśa and coverage; local answers also name
location and civil time."""
from __future__ import annotations

import dataclasses

import pytest

import services.kala_core as kala_core
import services.kala_core.sky as sky
from services.gochara_kernel import knots
from services.kala_core.sky import (
    CivilTime, GeoLocation, LocalAnswer, SkyConvention, ephemeris_at, lagna_at,
)

J0 = 2459000.0
DELHI = GeoLocation(28.6139, 77.2090)
IST = CivilTime("Asia/Kolkata", 330)


@pytest.fixture
def seam(monkeypatch):
    import swisseph as swe

    monkeypatch.setattr(knots, "calc_sidereal_lon_speed",
                        lambda body, jd, _path: (100.0, 1.0, 2))
    monkeypatch.setattr(swe, "set_sid_mode", lambda _mode: None)
    monkeypatch.setattr(swe, "get_ayanamsa_ut", lambda _jd: 24.1)


def test_public_answer_names_its_contract(seam) -> None:
    result = ephemeris_at(J0)
    answer = result.values[0]
    assert answer.jd == J0 and answer.time_scale == "UT"
    assert answer.backend == "swieph"
    assert answer.flags == knots.EPHE_FLAGS | knots.swe.FLG_SPEED
    assert answer.flag_names == "FLG_SWIEPH|FLG_SIDEREAL|FLG_SPEED"
    assert answer.node_model == "mean"
    assert (answer.ayanamsha_id, answer.ayanamsha_deg) == ("lahiri_chitrapaksha", 24.1)
    assert answer.convention_id == SkyConvention().convention_id
    assert result.coverage.complete and result.coverage.backend == answer.backend
    assert {p.body for p in answer.positions} == set(knots.NINE_GRAHAS)


def test_local_lagna_names_location_and_civil_time() -> None:
    result = lagna_at(J0, DELHI, IST)
    answer = result.values[0]
    assert answer.kind == "lagna" and answer.time_scale == "UT"
    assert answer.location == DELHI and answer.civil_time == IST
    assert answer.local_time.startswith("2020-05-30T17:30")    # J0 is 2020-05-30 12:00 UT
    assert 0.0 <= answer.longitude_deg < 360.0
    assert answer.ayanamsha_id == "lahiri_chitrapaksha" and answer.ayanamsha_deg > 0.0
    assert result.coverage.backend == answer.backend == "swiss_houses"
    assert answer.flags == 0                                     # houses_ex with no iflag
    assert answer.flag_names == "houses_ex:tropical|hsys=P|minus_ayanamsa_ut:SIDM_LAHIRI"
    assert answer.node_model == "mean"
    assert answer.convention_id == SkyConvention().convention_id
    # The place matters: the same instant elsewhere has another ascendant.
    elsewhere = lagna_at(J0, GeoLocation(40.7128, -74.0060), CivilTime("America/New_York", -240))
    assert elsewhere.values[0].longitude_deg != pytest.approx(answer.longitude_deg, abs=1.0)


CONTRACT_FIELDS = {"jd", "time_scale", "backend", "flags", "flag_names", "node_model",
                   "ayanamsha_id", "ayanamsha_deg", "convention_id"}


@pytest.mark.parametrize("answer_type", [sky.EphemerisAnswer, LocalAnswer])
def test_every_answer_type_declares_the_contract_fields(answer_type) -> None:
    fields = {f.name for f in dataclasses.fields(answer_type)}
    assert CONTRACT_FIELDS <= fields, CONTRACT_FIELDS - fields


def test_local_answer_without_location_or_civil_time_fails() -> None:
    answer = lagna_at(J0, DELHI, IST).values[0]
    with pytest.raises(TypeError, match="location"):
        dataclasses.replace(answer, location=None)
    with pytest.raises(TypeError, match="civil-time"):
        dataclasses.replace(answer, civil_time=None)
    with pytest.raises(TypeError):
        lagna_at(J0, DELHI)                                     # civil time is not optional
    with pytest.raises(ValueError, match="zone"):
        CivilTime("", 330)


def test_sky_is_a_new_unexported_module() -> None:
    assert not hasattr(kala_core, "sky") or "sky" not in getattr(kala_core, "__all__", ())
    assert set(sky.__all__) >= {"ephemeris_at", "boundary_events", "solve_contacts",
                                "stations", "aspects", "SkyResult", "lagna_at"}
    assert LocalAnswer.__dataclass_params__.frozen
