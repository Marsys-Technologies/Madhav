"""ga_dashas Mudda solar-return: the nested Sun-longitude helper owns its own mode setter.

``_sun_long_at`` (nested in ``_mudda_solar_return_jd``) called ``drik.sidereal_longitude`` relying on
the enclosing function's ``set_ayanamsa_mode``.  It is now ``_mudda_sun_long_at(jd, ayanamsha_id)``
(module level, ``with_sidereal_mode`` inside), the same nested-helper hazard as ga_sade_sati's
``_saturn_sign_at_jd``.  Real threads: fresh thread and a reused pool thread left in true_chitra,
main thread in Fagan-Bradley.  Synthetic birth only.
"""
from __future__ import annotations

import pytest
import swisseph as swe

from jhora import utils
from jhora.panchanga import drik
from ga_writers import ga_dashas_writer as GD
from tests.swiss_thread_harness import (
    SiderealModeSpy,
    main_thread_in_fagan,  # noqa: F401  (fixture)
    run_in_dirty_pool_thread,
    run_in_fresh_thread,
    run_in_lahiri_thread,
)

RUNNERS = [pytest.param(run_in_fresh_thread, id="fresh_thread"),
           pytest.param(run_in_dirty_pool_thread, id="reused_pool_thread_left_in_true_chitra")]

BIRTH_JD = utils.julian_day_number(drik.Date(2011, 2, 6), (11, 0, 0))  # synthetic
# Golden from the PRE-change code (git 1499acd54), thread selecting Lahiri itself; macOS == linux to < 1e-9.
NATAL_SUN_LAHIRI = 293.2894650242302
MUDDA_RETURN_JD_AGE_30 = 2466556.649593099


def _sun(jd, ayanamsha_id="lahiri"):
    return GD._mudda_sun_long_at(jd, ayanamsha_id)


@pytest.mark.parametrize("run", RUNNERS)
def test_mudda_sun_long_is_lahiri_on_a_thread_that_never_selected_it(run, main_thread_in_fagan,
                                                                     monkeypatch):
    spy = SiderealModeSpy(monkeypatch)
    got = run(lambda: _sun(BIRTH_JD))
    assert got == pytest.approx(NATAL_SUN_LAHIRI, abs=1e-9)
    assert spy.calls and spy.wrong_mode_calls() == []
    ref = run_in_lahiri_thread(lambda: float(drik.sidereal_longitude(BIRTH_JD, 0)) % 360.0)
    assert got == pytest.approx(ref, abs=1e-9)


@pytest.mark.parametrize("run", RUNNERS)
def test_mudda_sun_long_honours_a_non_lahiri_ayanamsha(run, main_thread_in_fagan):
    def tc_ref():
        swe.set_sid_mode(swe.SIDM_TRUE_CITRA)
        drik.set_ayanamsa_mode("TRUE_CITRA")
        return float(drik.sidereal_longitude(BIRTH_JD, 0)) % 360.0

    want = run_in_fresh_thread(tc_ref)
    assert abs(want - NATAL_SUN_LAHIRI) > 1e-3  # discriminating
    assert run(lambda: _sun(BIRTH_JD, "true_chitra")) == pytest.approx(want, abs=1e-9)


@pytest.mark.parametrize("run", RUNNERS)
def test_mudda_solar_return_entry_point_unchanged(run, main_thread_in_fagan):
    got = run(lambda: GD._mudda_solar_return_jd(NATAL_SUN_LAHIRI, BIRTH_JD, "lahiri",
                                                {"datetime_iso": "2011-02-06T11:00:00"}, 30))
    assert got == pytest.approx(MUDDA_RETURN_JD_AGE_30, abs=1e-6)  # ~0.1 s
