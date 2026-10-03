"""ga_sade_sati Saturn helpers must select Lahiri + the .se1 path on the thread that computes.

``_saturn_sign_at_jd`` (a SIGN at a JD is ayanamsha-dependent) and ``_saturn_speed_at_jd`` /
``_detect_saturn_retrogrades`` used to inherit the mode from ``_detect_saturn_sign_changes``'s
``set_sid_mode`` (a DIFFERENT function) or from whatever the thread held.  Real threads: a fresh
thread and a reused pool thread left in true_chitra, main thread in Fagan-Bradley.  On Linux the
mode is per thread, so these fail without the in-function setter (mutation proof in the lane report);
on macOS the primary assertions still hold.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
import swisseph as swe

from ga_writers import ga_sade_sati_writer as W
from tests.swiss_thread_harness import (
    SiderealModeSpy,
    main_thread_in_fagan,  # noqa: F401  (fixture)
    run_in_dirty_pool_thread,
    run_in_fresh_thread,
    run_in_lahiri_thread,
)

RUNNERS = [pytest.param(run_in_fresh_thread, id="fresh_thread"),
           pytest.param(run_in_dirty_pool_thread, id="reused_pool_thread_left_in_true_chitra")]

# 1984-12-21 03:24 UT Saturn enters Scorpio (Lahiri); Fagan-Bradley's ingress is ~9 days later.
# JD 2446060.5 (1984-12-25 00:00 UT): Lahiri 210.499 deg = Scorpio (sign 8), Fagan 209.616 = Libra (7).
SIGN_JD = 2446060.5
LAHIRI_SIGN = 8
FAGAN_SIGN = 7

_UTC = timezone.utc
RETRO_WINDOW = (datetime(1993, 1, 1, tzinfo=_UTC), datetime(1995, 1, 1, tzinfo=_UTC))
# Golden values captured from the PRE-change code (git 1499acd54, thread selecting Lahiri itself).
RETRO_GOLDEN = [
    ("1993-06-09T00:00:00+00:00", "1993-10-30T23:59:00+00:00"),
    ("1994-06-22T00:00:00+00:00", "1994-11-09T23:59:00+00:00"),
]
SIGN_WINDOW = (datetime(1993, 1, 1, tzinfo=_UTC), datetime(1997, 1, 1, tzinfo=_UTC))
SIGN_GOLDEN = [
    ("1993-03-05T12:57:39+00:00", "Capricorn", "Aquarius"),
    ("1993-10-15T06:29:31+00:00", "Aquarius", "Capricorn"),
    ("1993-11-09T23:36:05+00:00", "Capricorn", "Aquarius"),
    ("1995-06-02T05:05:09+00:00", "Aquarius", "Pisces"),
    ("1995-08-09T20:30:28+00:00", "Pisces", "Aquarius"),
    ("1996-02-16T12:54:50+00:00", "Aquarius", "Pisces"),
]


def _sign_in_mode(sidm: int) -> int:
    def f():
        swe.set_sid_mode(sidm)
        lon = swe.calc_ut(SIGN_JD, swe.SATURN, swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][0] % 360.0
        return int(lon // 30) + 1

    return run_in_fresh_thread(f)


def test_chosen_jd_really_separates_lahiri_from_fagan_saturn_signs():
    """Precondition that makes the sign test meaningful: the two modes disagree at SIGN_JD."""
    assert _sign_in_mode(swe.SIDM_LAHIRI) == LAHIRI_SIGN
    assert _sign_in_mode(swe.SIDM_FAGAN_BRADLEY) == FAGAN_SIGN


# true_chitra is within 0.02 deg of Lahiri, so a pool thread left there still gets the Lahiri SIGN at
# SIGN_JD; a pool thread left in Fagan-Bradley (the other ayanamsha that flips it) is the one that
# makes the reused-thread case discriminating for a SIGN.
SIGN_RUNNERS = RUNNERS + [
    pytest.param(lambda fn: run_in_dirty_pool_thread(fn, dirty_sidm=swe.SIDM_FAGAN_BRADLEY),
                 id="reused_pool_thread_left_in_fagan_bradley"),
]


@pytest.mark.parametrize("run", SIGN_RUNNERS)
def test_saturn_sign_at_jd_returns_the_lahiri_sign_on_a_thread_that_never_selected_it(
        run, main_thread_in_fagan):
    assert run(lambda: W._saturn_sign_at_jd(SIGN_JD)) == LAHIRI_SIGN


@pytest.mark.parametrize("run", RUNNERS)
def test_saturn_speed_at_jd_is_computed_under_lahiri(run, main_thread_in_fagan, monkeypatch):
    jd = SIGN_JD
    spy = SiderealModeSpy(monkeypatch)
    got = run(lambda: W._saturn_speed_at_jd(jd))
    assert spy.calls, "the function must compute through swe.calc_ut"
    assert spy.wrong_mode_calls() == []
    ref = run_in_lahiri_thread(
        lambda: swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL | swe.FLG_SPEED)[0][3])
    assert got == pytest.approx(ref, abs=1e-12)


@pytest.mark.parametrize("run", RUNNERS)
def test_detect_saturn_retrogrades_entry_point(run, main_thread_in_fagan, monkeypatch):
    """Every sidereal calc of the entry point runs under Lahiri (the retro windows themselves are
    mode-insensitive, measured, so the mode is asserted at the calc), and the output is unchanged."""
    spy = SiderealModeSpy(monkeypatch)
    out = run(lambda: [(r["start_utc"].isoformat(), r["end_utc"].isoformat())
                       for r in W._detect_saturn_retrogrades(*RETRO_WINDOW)])
    assert out == RETRO_GOLDEN
    assert len(spy.calls) > 200
    assert spy.wrong_mode_calls() == []


@pytest.mark.parametrize("run", RUNNERS)
def test_detect_saturn_sign_changes_entry_point_unchanged(run, main_thread_in_fagan, monkeypatch):
    """The hoisted sign helper is wired in: ingress instants equal the pre-change golden values."""
    spy = SiderealModeSpy(monkeypatch)
    out = run(lambda: [(c["date_utc"].isoformat(), c["sign_from"], c["sign_to"])
                       for c in W._detect_saturn_sign_changes(*SIGN_WINDOW)])
    assert out == SIGN_GOLDEN
    assert spy.wrong_mode_calls() == []


def test_the_closures_were_hoisted_so_each_helper_owns_its_setter():
    import inspect

    for fn in (W._saturn_sign_at_jd, W._saturn_speed_at_jd):
        assert "with_sidereal_mode(" in inspect.getsource(fn.__wrapped__)
