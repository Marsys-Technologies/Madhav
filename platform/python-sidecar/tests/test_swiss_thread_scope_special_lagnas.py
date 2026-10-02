"""pyjhora_adapter.special_lagnas: ``_special_ascendant`` / ``_varnada_lagna_bv_raman`` select the
sidereal mode and the .se1 path on the thread that computes.

They carried no setter of their own (only ``compute_special_lagnas`` set the mode, a different
function): a bare call from a fresh Linux thread returned Fagan-Bradley longitudes (-0.883 deg) and
from a reused pool thread whatever ayanamsha the previous task left.  They now take ``ayanamsha_id``
(None = lahiri) and select it themselves; ``compute_special_lagnas`` passes its own.  Real threads:
fresh thread and a reused pool thread left in true_chitra / raman, main thread in Fagan-Bradley.
Synthetic birth only (no native data).
"""
from __future__ import annotations

import pytest
import swisseph as swe

from jhora import utils
from jhora.panchanga import drik
from pyjhora_adapter import special_lagnas as sl
from tests.swiss_thread_harness import (
    SiderealModeSpy,
    main_thread_in_fagan,  # noqa: F401  (fixture)
    run_in_dirty_pool_thread,
    run_in_fresh_thread,
    run_in_lahiri_thread,
)

RUNNERS = [pytest.param(run_in_fresh_thread, id="fresh_thread"),
           pytest.param(run_in_dirty_pool_thread, id="reused_pool_thread_left_in_true_chitra")]

LAT, LON, TZ = 23.26, 77.41, 5.5  # synthetic (Bhopal-like), same as test_special_lagna_sunrise_sun CASES[0]
DOB = drik.Date(2011, 2, 6)
TOB = (11, 0, 0)
JD = utils.julian_day_number(DOB, TOB)

# Golden values captured from the PRE-change code (git 1499acd54) on a thread that selected the mode
# itself; identical on macOS and linux/amd64 to < 1e-9 deg.
LAHIRI_HORA = (1, 21.760283067830642)
LAHIRI_BHAVA = (11, 22.325014073409875)
LAHIRI_VARNADA = (9, 9.734767629142695)
TC_HORA = (1, 21.77614452134361)
TC_VARNADA = (9, 9.750629092021946)
LAHIRI_LONGITUDES = {"bhava_lagna": 352.3250140734099, "hora_lagna": 51.76028306783064,
                     "ghati_lagna": 230.06609005109294, "vighati_lagna": 259.0058847442351,
                     "varnada_lagna": 279.7347676291427}


def _place():
    return drik.Place("subject", LAT, LON, TZ)


def _approx(pair, want):
    assert pair[0] == want[0]
    assert pair[1] == pytest.approx(want[1], abs=1e-9)


@pytest.mark.parametrize("run", RUNNERS)
def test_special_ascendant_is_lahiri_on_a_thread_that_never_selected_it(run, main_thread_in_fagan,
                                                                        monkeypatch):
    spy = SiderealModeSpy(monkeypatch)
    got = run(lambda: sl._special_ascendant(JD, _place(), lagna_rate_factor=sl._HORA_RATE_DEG_PER_MIN))
    _approx(got, LAHIRI_HORA)
    assert spy.calls and spy.wrong_mode_calls() == []


@pytest.mark.parametrize("run", RUNNERS)
def test_rate_lagnas_default_to_lahiri_on_a_thread_that_never_selected_it(run, main_thread_in_fagan):
    _approx(run(lambda: sl.hora_lagna(JD, _place())), LAHIRI_HORA)
    _approx(run(lambda: sl.bhava_lagna(JD, _place())), LAHIRI_BHAVA)


@pytest.mark.parametrize("run", RUNNERS)
def test_varnada_lagna_is_lahiri_on_a_thread_that_never_selected_it(run, main_thread_in_fagan,
                                                                     monkeypatch):
    spy = SiderealModeSpy(monkeypatch)
    got = run(lambda: sl._varnada_lagna_bv_raman(DOB, TOB, _place()))
    _approx(got, LAHIRI_VARNADA)
    assert spy.calls and spy.wrong_mode_calls() == []


def test_an_unprepared_value_would_differ_from_the_golden_by_the_fagan_offset(main_thread_in_fagan):
    """Precondition: the goldens are discriminating (Fagan-Bradley moves the degree by ~0.88 deg)."""
    # raw check through PyJHora's own upstream routine under an explicit Fagan-Bradley mode
    def upstream_fagan():
        swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)
        return drik.hora_lagna(JD, _place())

    got = run_in_fresh_thread(upstream_fagan)
    assert abs(got[1] - LAHIRI_HORA[1]) > 0.5 or got[0] != LAHIRI_HORA[0]


@pytest.mark.parametrize("dirty", [swe.SIDM_RAMAN, swe.SIDM_FAGAN_BRADLEY],
                         ids=["pool_left_in_raman", "pool_left_in_fagan"])
def test_ayanamsha_id_is_honoured_not_forced_to_lahiri(dirty, main_thread_in_fagan):
    """A non-Lahiri ayanamsha passed in is the one selected, on a fresh and on a reused thread."""
    fresh = run_in_fresh_thread(lambda: (
        sl.hora_lagna(JD, _place(), ayanamsha_id="true_chitra"),
        sl._varnada_lagna_bv_raman(DOB, TOB, _place(), ayanamsha_id="true_chitra")))
    pooled = run_in_dirty_pool_thread(lambda: (
        sl.hora_lagna(JD, _place(), ayanamsha_id="true_chitra"),
        sl._varnada_lagna_bv_raman(DOB, TOB, _place(), ayanamsha_id="true_chitra")), dirty_sidm=dirty)
    for got in (fresh, pooled):
        _approx(got[0], TC_HORA)
        _approx(got[1], TC_VARNADA)


@pytest.mark.parametrize("run", RUNNERS)
def test_compute_special_lagnas_entry_point_unchanged(run, main_thread_in_fagan):
    out = run(lambda: sl.compute_special_lagnas(JD, DOB, TOB, "lahiri", lat=LAT, lon=LON, tz=TZ))
    ref = run_in_lahiri_thread(lambda: sl.compute_special_lagnas(JD, DOB, TOB, "lahiri",
                                                                 lat=LAT, lon=LON, tz=TZ))
    assert set(out) == set(ref)
    for name, want in LAHIRI_LONGITUDES.items():
        assert out[name]["longitude_deg"] == pytest.approx(want, abs=1e-9), name
    for name in ref:
        assert "error" not in out[name], (name, out[name])
        assert out[name]["longitude_deg"] == pytest.approx(ref[name]["longitude_deg"], abs=1e-9), name
