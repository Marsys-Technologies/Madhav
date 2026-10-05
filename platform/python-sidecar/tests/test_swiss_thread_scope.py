"""``pyjhora_adapter._swiss_thread_scope.with_sidereal_mode``: mode + path pinned on the CALLING thread.

Real threads (see ``tests/swiss_thread_harness.py``): a brand-new thread and a reused pool thread
that a previous task left in a different ayanamsha, with the main thread left in Fagan-Bradley.
On Linux the sidereal mode and the ephemeris path are per thread, so these are discriminating
there (CI); on macOS the state is process-global and the PRIMARY assertions still hold.
"""
from __future__ import annotations

import os
import sys
import threading

import pytest
import swisseph as swe

from panchang_engine.swiss_backend import OutOfCorpusRangeError, SwissBackendError, ensure_swiss_backend
from pyjhora_adapter._ayanamsha import AYANAMSHA_MAP, resolve_mode
from pyjhora_adapter._swiss_thread_scope import with_sidereal_mode
from tests.swiss_thread_harness import (
    PINNED_FLAGS,
    PINNED_FRESH_THREAD_MISS_DEG,
    PINNED_JD,
    PINNED_SUN_LAHIRI_J2000,
    lahiri_ayanamsa_at,
    main_thread_in_fagan,  # noqa: F401  (fixture)
    run_in_dirty_pool_thread,
    run_in_fresh_thread,
)

RUNNERS = [pytest.param(run_in_fresh_thread, id="fresh_thread"),
           pytest.param(run_in_dirty_pool_thread, id="reused_pool_thread_left_in_true_chitra")]


def _sun_sidereal_via_helper(ayanamsha_id: str = "lahiri", **kw) -> float:
    with with_sidereal_mode(ayanamsha_id, PINNED_JD, **kw):
        return swe.calc_ut(PINNED_JD, swe.SUN, PINNED_FLAGS)[0][0]


@pytest.mark.parametrize("run", RUNNERS)
def test_shared_pinned_reference_sun_lahiri_j2000_through_the_helper(run, main_thread_in_fagan):
    """Pravaha's SHA-pinned reference: Sun, Lahiri, JD 2451545.0 = 256.5156961838706 deg."""
    got = run(_sun_sidereal_via_helper)
    assert abs(got - PINNED_SUN_LAHIRI_J2000) < 1e-9, got


def test_documentation_unprepared_fresh_thread_misses_the_pinned_reference(main_thread_in_fagan):
    """WITHOUT the helper a fresh thread computes in the library default (Fagan-Bradley) and misses
    the pinned reference by ~0.8832076 deg.  True only where the state is per thread (Linux)."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # main thread: Lahiri

    def bare():
        return swe.calc_ut(PINNED_JD, swe.SUN, PINNED_FLAGS)[0][0]

    fresh = run_in_fresh_thread(bare)
    if abs(fresh - PINNED_SUN_LAHIRI_J2000) < 1e-9:
        if sys.platform.startswith("linux"):
            pytest.fail("on Linux a fresh thread must NOT inherit the main thread's Lahiri mode")
        pytest.skip("sidereal mode is process-global on this platform (macOS): a fresh thread "
                    "inherits the main thread's mode, so the hazard cannot be shown here")
    assert abs((PINNED_SUN_LAHIRI_J2000 - fresh) - PINNED_FRESH_THREAD_MISS_DEG) < 1e-6, fresh


@pytest.mark.parametrize("run", RUNNERS)
def test_helper_selects_the_requested_mode_on_the_calling_thread(run, main_thread_in_fagan):
    jd = PINNED_JD

    def seen():
        with with_sidereal_mode("lahiri", jd):
            return swe.get_ayanamsa_ut(jd)

    assert abs(run(seen) - lahiri_ayanamsa_at(jd)) < 1e-9


@pytest.mark.parametrize("run", RUNNERS)
@pytest.mark.parametrize("ayanamsha_id", ["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"])
@pytest.mark.parametrize("via_jhora", [False, True])
def test_helper_raw_and_jhora_paths_select_the_same_swiss_mode(run, ayanamsha_id, via_jhora,
                                                               main_thread_in_fagan):
    _name, sidm = resolve_mode(ayanamsha_id)
    jd = 2446066.5

    def reference():
        # Pinned through the existing helper first, exactly like the helper under test: on Linux the
        # per-thread swisseph state also includes ephemeris-dependent state (delta-T / tidal
        # acceleration, set by the first SWIEPH calc), which moves the star-based true_chitra
        # ayanamsa by ~3.5e-7 deg and surya_siddhanta by ~1.2e-8 deg between a thread that has
        # computed from the .se1 files and one that has not.
        ensure_swiss_backend(jd)
        swe.set_sid_mode(sidm)
        return swe.get_ayanamsa_ut(jd)

    def via_helper():
        with with_sidereal_mode(ayanamsha_id, jd, via_jhora=via_jhora):
            return swe.get_ayanamsa_ut(jd)

    assert run(via_helper) == pytest.approx(run_in_fresh_thread(reference), abs=1e-9)


def test_resolve_mode_ints_are_the_swisseph_constants():
    assert AYANAMSHA_MAP["lahiri"][1] == swe.SIDM_LAHIRI
    assert AYANAMSHA_MAP["true_chitra"][1] == swe.SIDM_TRUE_CITRA
    assert AYANAMSHA_MAP["kp"][1] == swe.SIDM_KRISHNAMURTI
    assert AYANAMSHA_MAP["raman"][1] == swe.SIDM_RAMAN
    assert AYANAMSHA_MAP["surya_siddhanta"][1] == swe.SIDM_SURYASIDDHANTA


def test_helper_pins_the_ephemeris_path_on_the_calling_thread(monkeypatch, main_thread_in_fagan):
    """``set_ephe_path`` is called, with the configured ``SE_EPHE_PATH``, on the thread that computes."""
    want = os.environ.get("SE_EPHE_PATH", "").strip()
    assert want, "the py-sidecar suite runs with SE_EPHE_PATH (conftest / CI)"
    seen: list[tuple[int, str]] = []
    real = swe.set_ephe_path

    def spy(path=None):
        seen.append((threading.get_ident(), path))
        return real(path)

    monkeypatch.setattr(swe, "set_ephe_path", spy)

    def body():
        with with_sidereal_mode("lahiri", PINNED_JD):
            pass
        return threading.get_ident()

    tid = run_in_fresh_thread(body)
    assert (tid, want) in seen


def test_helper_fails_closed_without_se_ephe_path_and_leaves_the_mode_untouched(monkeypatch):
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)

    def body():
        swe.set_sid_mode(swe.SIDM_RAMAN)
        before = swe.get_ayanamsa_ut(PINNED_JD)
        with pytest.raises(SwissBackendError):
            with with_sidereal_mode("lahiri", PINNED_JD):
                pytest.fail("body must not run when the backend cannot be pinned")
        return before, swe.get_ayanamsa_ut(PINNED_JD)

    before, after = run_in_fresh_thread(body)
    assert before == after


def test_helper_refuses_a_jd_outside_the_corpus_window_and_leaves_the_mode_untouched():
    def body():
        swe.set_sid_mode(swe.SIDM_RAMAN)
        before = swe.get_ayanamsa_ut(PINNED_JD)
        with pytest.raises(OutOfCorpusRangeError):
            with with_sidereal_mode("lahiri", 2000000.0):
                pytest.fail("body must not run for an out-of-corpus JD")
        return before, swe.get_ayanamsa_ut(PINNED_JD)

    before, after = run_in_fresh_thread(body)
    assert before == after


def test_helper_rejects_an_unknown_ayanamsha_before_touching_swiss_state():
    def body():
        swe.set_sid_mode(swe.SIDM_RAMAN)
        before = swe.get_ayanamsa_ut(PINNED_JD)
        with pytest.raises(ValueError):
            with with_sidereal_mode("not_an_ayanamsha", PINNED_JD):
                pytest.fail("unreachable")
        return before, swe.get_ayanamsa_ut(PINNED_JD)

    before, after = run_in_fresh_thread(body)
    assert before == after
