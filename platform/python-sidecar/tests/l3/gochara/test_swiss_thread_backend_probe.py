"""C31 — swiss_thread_scope.ensure_swiss_thread_backend: fail-closed backend probe.

Converges the C26 per-thread preparation with swiss_backend's backend honesty (SS ruling
N-28: Moshier must never be silent) for the computing call sites that prepare their own
thread. The probe is on the CALLING thread (Linux: path and mode are per-thread C state)
and re-asserts path and mode on EVERY call.

Pins: the .se1 path must be set (None/blank raises), an empty directory raises (the
library would silently substitute Moshier), and WITH the SHA-pinned corpus the probe
passes and the sidereal Lahiri Sun at J2000 is the measured 256.5156961838706°
(Suvarṇa's S-L1 reference, already pinned by test_swiss_per_thread_state.py).

Runs under the tests/l3/gochara conftest gate: corpus tests skip without the pinned .se1
corpus; GOCHARA_SE1_REQUIRE=1 (CI) turns an unusable corpus into a hard failure.
"""
from __future__ import annotations

import threading

import pytest
import swisseph as swe

from panchang_engine.swiss_thread_scope import (
    SwissThreadBackendError,
    ensure_swiss_thread_backend,
    prepare_swiss_thread,
)

from .conftest import EPHE_PATH, J2000_JD, assert_real_ephemeris, requires_swieph

PINNED_SUN_LAHIRI_LON_J2000 = 256.5156961838706
PINNED_LAHIRI_AYANAMSA_J2000 = 23.85709235370888
TOL_DEG = 1e-9


def test_none_path_raises_before_any_library_call():
    with pytest.raises(SwissThreadBackendError, match="path is not set"):
        ensure_swiss_thread_backend(None, swe.SIDM_LAHIRI)


def test_blank_path_raises_before_any_library_call():
    with pytest.raises(SwissThreadBackendError, match="path is not set"):
        ensure_swiss_thread_backend("   ", swe.SIDM_LAHIRI)


def test_an_empty_directory_is_not_a_backend(monkeypatch, tmp_path):
    # hide SE_EPHE_PATH from the C library too (it is searched after set_ephe_path — the
    # measured caveat in swiss_backend's docstring), so the empty dir is all there is
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)
    monkeypatch.delenv("SWE_EPHE_PATH", raising=False)
    with pytest.raises(SwissThreadBackendError, match="not swieph"):
        ensure_swiss_thread_backend(str(tmp_path), swe.SIDM_LAHIRI)


@requires_swieph
def test_with_the_pinned_corpus_the_probe_passes_and_the_sun_hits_the_pin():
    assert_real_ephemeris()
    ensure_swiss_thread_backend(EPHE_PATH, swe.SIDM_LAHIRI)
    xx, retflag = swe.calc_ut(J2000_JD, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED)
    assert retflag & swe.FLG_SWIEPH
    assert abs(xx[0] - PINNED_SUN_LAHIRI_LON_J2000) <= TOL_DEG, (
        f"sidereal Lahiri Sun at J2000 is {xx[0]!r}, pinned {PINNED_SUN_LAHIRI_LON_J2000} "
        f"(diff {abs(xx[0] - PINNED_SUN_LAHIRI_LON_J2000):.3e}°)"
    )


@requires_swieph
def test_the_probe_and_the_pin_hold_on_a_fresh_thread():
    """The probe pins the CALLING thread: a fresh thread must pass it itself and then hit the pin."""
    assert_real_ephemeris()
    out: list[float] = []

    def work():
        ensure_swiss_thread_backend(EPHE_PATH, swe.SIDM_LAHIRI)
        xx, _rf = swe.calc_ut(J2000_JD, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED)
        out.append(xx[0])

    t = threading.Thread(target=work)
    t.start()
    t.join()
    assert len(out) == 1
    assert abs(out[0] - PINNED_SUN_LAHIRI_LON_J2000) <= TOL_DEG


@requires_swieph
def test_mode_is_reasserted_on_every_call_over_a_contaminated_thread():
    """A thread left in another ayanamsha is repaired by the probe call itself (S-L1:
    'prepared earlier' is never a sound assumption on a pooled worker)."""
    assert_real_ephemeris()
    prepare_swiss_thread(EPHE_PATH, swe.SIDM_FAGAN_BRADLEY)          # contaminate this thread
    assert abs(swe.get_ayanamsa_ut(J2000_JD) - PINNED_LAHIRI_AYANAMSA_J2000) > 0.8
    ensure_swiss_thread_backend(EPHE_PATH, swe.SIDM_LAHIRI)          # mode on EVERY call
    assert abs(swe.get_ayanamsa_ut(J2000_JD) - PINNED_LAHIRI_AYANAMSA_J2000) <= TOL_DEG
