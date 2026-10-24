"""SR-EPHE-PATH-ONCE (od1-ephe-once): the Swiss ephemeris path is set once per thread, never once per probe.

Evidence: CENTURY_SIZING E2 — `swe.set_ephe_path` closes the library's open files, so re-issuing it inside every
`knots.calc_sidereal_lon` call cost ≈75 µs against ≈0.24 µs for the probe (≈45 % of a record step).

Claims, each with ONE detector that reads false when its behaviour is reverted:
  C1  the path is set once for repeated probes of one path (builder `calc_sidereal_lon`, `calc_sidereal_lon_speed`; the
      verifier's own `near_miss_verifier._ephemeris_position` and `vedha_verifier.swiss_longitude`);
  C2  a DIFFERENT path is applied (and applied back), proved on the real backend: an empty directory makes the probe refuse
      (Moshier), the pinned directory makes it succeed, in alternation, with the environment fallback removed;
  C3  a path set by ANOTHER caller in the process invalidates the memo (the next probe re-asserts its own path);
  C4  a fresh thread sets its own path (Linux keeps the Swiss state per thread);
  C5  TIMING: a `calc_sidereal_lon` probe costs a small multiple of a bare `calc_ut`, not hundreds of times (the pre-fix
      code re-set the path each call: measured ≈370x on the pinned ephemeris; fixed ≈10x). The bound is RELATIVE to a bare
      `calc_ut` timed in the same run, best-of-N, so machine load moves both sides.
Sources: pyswisseph `set_ephe_path` closes open files (swe_set_ephe_path -> swi_close_keep_topo_etc); CENTURY_SIZING E2;
panchang_engine/swiss_state.py (SWISS_STATE_LOCK unchanged).
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone

import pytest
import swisseph as swe

from services.gochara_kernel import knots, near_miss_verifier, vedha_verifier

from .conftest import EPHE_PATH, requires_swieph

pytestmark = requires_swieph

JD = 2460000.5


@pytest.fixture
def path_spy(monkeypatch):
    """Record every `swe.set_ephe_path` argument; the call still reaches the (tracked) real function."""
    calls: list = []
    real = swe.set_ephe_path

    def spy(*a, **k):
        calls.append(a[0] if a else None)
        return real(*a, **k)

    monkeypatch.setattr(swe, "set_ephe_path", spy)
    return calls


@pytest.fixture
def fresh_memo():
    memo = getattr(knots, "_EPHE_MEMO", None)        # absent on the pre-fix code (the revert proof runs these tests there)
    if memo is not None:
        memo.state = None
    yield
    if memo is not None:
        memo.state = None
    swe.set_ephe_path(EPHE_PATH)


def test_c1_builder_sets_the_path_once_for_repeated_probes(path_spy, fresh_memo):
    for _ in range(25):
        knots.calc_sidereal_lon("Sun", JD, EPHE_PATH)
        knots.calc_sidereal_lon_speed("Mars", JD, EPHE_PATH)
    assert path_spy == [EPHE_PATH]


def test_c1_near_miss_verifier_reader_sets_the_path_once(path_spy):
    at = near_miss_verifier._ephemeris_position(EPHE_PATH)
    t = datetime(2026, 3, 1, tzinfo=timezone.utc)
    for k in range(25):
        at("sun", t + timedelta(days=k))
    assert path_spy == [EPHE_PATH]


def test_c1_vedha_verifier_reader_sets_the_path_once(path_spy):
    t = datetime(2026, 3, 1, tzinfo=timezone.utc)
    lon = vedha_verifier.swiss_longitude(EPHE_PATH, {"ayanamsha": "lahiri_chitrapaksha", "node_convention": "mean"})
    for k in range(25):
        lon("Sun", t + timedelta(days=k))
    assert path_spy == [EPHE_PATH]


def test_c2_a_different_path_is_applied_on_the_real_backend(monkeypatch, tmp_path, fresh_memo):
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)       # the C library's own fallback would otherwise find the files
    empty = str(tmp_path)
    knots.calc_sidereal_lon("Sun", JD, EPHE_PATH)            # memo now holds the pinned path
    assert knots.calc_sidereal_lon("Sun", JD, empty)[1] & 4  # applied: Moshier (the caller refuses it, F-14)
    assert knots.calc_sidereal_lon("Sun", JD, EPHE_PATH)[1] & 2  # and applied back
    assert knots.calc_sidereal_lon_speed("Sun", JD, empty)[2] & 4
    assert knots.calc_sidereal_lon_speed("Sun", JD, EPHE_PATH)[2] & 2


def test_c3_a_path_set_by_another_caller_invalidates_the_memo(path_spy, fresh_memo, tmp_path):
    knots.calc_sidereal_lon("Sun", JD, EPHE_PATH)
    knots.calc_sidereal_lon("Sun", JD, EPHE_PATH)
    assert path_spy == [EPHE_PATH]
    swe.set_ephe_path(str(tmp_path))                         # another caller moves the process to another directory
    knots.calc_sidereal_lon("Sun", JD, EPHE_PATH)
    assert path_spy == [EPHE_PATH, str(tmp_path), EPHE_PATH]


def test_c4_a_fresh_thread_sets_its_own_path(path_spy, fresh_memo):
    knots.calc_sidereal_lon("Sun", JD, EPHE_PATH)
    out: list = []
    th = threading.Thread(target=lambda: out.append(knots.calc_sidereal_lon("Sun", JD, EPHE_PATH)))
    th.start()
    th.join()
    assert out and path_spy == [EPHE_PATH, EPHE_PATH]


def _best_us(fn, n=2000, rounds=7) -> float:
    best = float("inf")
    for _ in range(rounds):
        t0 = time.perf_counter()
        for _ in range(n):
            fn()
        best = min(best, (time.perf_counter() - t0) / n)
    return best * 1e6


def test_c5_probe_cost_is_a_small_multiple_of_a_bare_calc(fresh_memo):
    flags = knots.EPHE_FLAGS
    swe.set_ephe_path(EPHE_PATH)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    knots.calc_sidereal_lon("Sun", JD, EPHE_PATH)            # warm: files open
    bare = _best_us(lambda: swe.calc_ut(JD, swe.SUN, flags))
    probe = _best_us(lambda: knots.calc_sidereal_lon("Sun", JD, EPHE_PATH))
    # pre-fix ≈ 300x+ (each probe re-set the path: ≈75 µs); fixed ≈ 10x. 60x leaves 6x headroom for load either way.
    print(f"calc_sidereal_lon {probe:.2f} us, bare calc_ut {bare:.2f} us, {probe / bare:.0f}x")
    assert probe < 60 * bare, f"calc_sidereal_lon {probe:.2f} µs vs bare calc_ut {bare:.2f} µs ({probe / bare:.0f}x)"
