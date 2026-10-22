"""SR-OD1 N-3b — the STATION-NEIGHBOURHOOD CUT in the window solver (`window_solver._check_arc` / `_classify_tent`), SR-STATION-NEAR-END.

The convention (S0 finding K-2): the stored arc index ends at a spline station that differs from the Swiss one by up to 16.7 s, and next to a station the
Swiss speed is ~1e-8 °/day with a noisy sign and the longitude is non-monotone by up to 3.9e-9°. So a stretch or piece NO LONGER than `NEAR_STATION_S`
(120 s, EQUAL to the independent checker's `NEAR_END_S`, window_solver_check.py:42-44, 84, 351-376) that touches a LISTED station is a cut for H1, and its
kernel is read monotone within `NEAR_STATION_NOISE_DEG` / orb. The builder's constants and code are its OWN (K12): nothing is imported from the checker.

Why a station-adjacent window used to blank: 9 of the 164 major_loss P3/P4 windows (6 Jupiter, 2 Venus, 1 Mercury; DIAG_P34 §5 N-3b) had a support end or
a root cut 0.003-3.3 s from a LISTED station, the sign test / the 1e-11 monotone tolerance read the Swiss noise as a reversal, and the INDEPENDENT checker —
which already treats a station within 120 s of a support end as a cut — found a value where the builder had a blank (a guaranteed verification DISAGREE).

Claims — each with ONE oracle (the classical/analytic source is cited) and ONE planted reversion that makes it fail:

  N3B-1 a stretch <= NEAR_STATION_S touching a listed station is not sign-tested (S0 K-2; checker `_stations`: `ts - a <= e or b - ts <= e` is a cut)
        oracle: REAL Swiss Jupiter station, window ending 3 ms after it, the station listed; the builder numbers, the independent checker VERIFIES the
        builder's value and instant (the one isolated crest lies outside the zone; SR-NEAR-STATION-TIE).   reversion: drop the skip in `_check_arc`
  N3B-2 the builder's convention is EQUAL in value to the verifier's 120 s (owner ruling SR-STATION-NEAR-END)
        oracle: the same real-sky window agrees AND the constants are equal.                reversion: a 0 s convention (R2: the 9 DISAGREEs return)
  N3B-3 a piece <= NEAR_STATION_S touching a listed station is read monotone within the S0 noise bound
        oracle: analytic world, kernel wiggle of 1e-9 in the 60 s before a listed station.   reversion: drop the noise term from `tol`
  N3B-4 the tolerance is the S0 bound, not wider: a wiggle of 1e-7 (25x the bound) is still a blank
        oracle: the same world with a 1e-7 wiggle.                                           reversion: widen the bound to 1e-6
  N3B-5 the length is 120 s, not wider: an unlisted reversal inside a 600 s stretch that touches a listed station is still `monotone_arc_not_established`
        (the honest null survives; plan §2.3 H1).                                            reversion: widen the length to 3600 s
  N3B-6 the certificate's `limits` carry both numbers (the verifier of a stored certificate can see the convention it rests on)
        oracle: `stored_certificate` of a solved window.                                     reversion: drop them from `limits`
"""
from __future__ import annotations

import ast
import math
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import window_solver as sol
from services.gochara_kernel import window_solver_check as chk

from .conftest import EPHE_PATH, assert_real_ephemeris, requires_swieph

SRC = Path(sol.__file__).read_text()
CHECKER_SRC = Path(chk.__file__).read_text()


# ── analytic worlds (built from the module UNDER TEST, so a reverted copy is exercised end to end) ──────────────────────────────────────────

def _problem(m, tent, hi, lo=0.0):
    return m.Problem(lo, hi, m.OBJECTIVE_SUM, (m.Member("a", "r", ((lo, hi),), tent=tent),))


def _station_world(m, wiggle: float):
    """A body sitting at offset 0.5 (orb 1) whose support starts 60 s before its LISTED station S: in that 60 s stretch it is disturbed by a `wiggle`-sized
    noise (a V in the kernel: -w, +w, -w at the start, middle and end of the piece) and its speed sign flips (Swiss speed noise). After S it climbs cleanly toward the
    target (offset 0.5 -> 0.4, kernel 0.5 -> 0.6): the window's one maximum is its END, ~880 s past the zone, so the zone's comb does not touch it (SR-NEAR-STATION-TIE)."""
    s, hi = 1000.0, 2000.0

    def noise(t):
        return wiggle * math.cos(2.0 * math.pi * (t - s + 30.0) / 60.0) if s - 60.0 <= t <= s else 0.0

    def vel(t):
        if s - 60.0 <= t <= s:
            return 1e-9 if math.cos(2.0 * math.pi * (t - s + 30.0) / 7.0) > 0 else -1e-9      # a noisy sign
        return -1e-4
    tent = m.Tent(offset=lambda t: 0.5 - 1e-4 * max(0.0, t - s) + noise(t), orb=1.0, velocity=vel, stations=(s,), min_station_spacing=20 * 86400.0)
    return _problem(m, tent, hi, lo=s - 60.0)


def _reversal_world(m):
    """An unlisted velocity reversal at t = 450 s inside the 600 s stretch [0, 600] that ends at the LISTED station 600 (offset = 0.2 + c (t-450)^2, c = 1e-6)."""
    c = 1e-6
    tent = m.Tent(offset=lambda t: 0.2 + c * (t - 450.0) ** 2, orb=1.0, velocity=lambda t: 2.0 * c * (t - 450.0), stations=(600.0,),
                  min_station_spacing=20 * 86400.0)
    return _problem(m, tent, 5000.0)


def _solve(m, problem):
    return m.solve(problem)


# ── the real sky (pinned Swiss corpus) ───────────────────────────────────────────────────────────────────────────────────────────────────────

def _jd(d: datetime) -> float:
    return d.timestamp() / 86400.0 + 2440587.5


def _lon_speed(jd: float):
    from services.gochara_kernel import knots
    lon, spd, rf = knots.calc_sidereal_lon_speed("Jupiter", jd, EPHE_PATH)
    assert rf & 2
    return lon, spd


def _lon_dt(body: str, d: datetime) -> float:
    from services.gochara_kernel import knots
    return knots.calc_sidereal_lon(body, _jd(d), EPHE_PATH)[0]


def _wrap180(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def _jupiter_station(start: datetime) -> datetime:
    """The first Swiss speed sign change of Jupiter after `start` (the test's own scan + bisection to 1 µs)."""
    v = lambda d: _lon_speed(_jd(d))[1]                                                            # noqa: E731
    d, prev = start, v(start)
    for _ in range(200):
        nxt = d + timedelta(days=2.0)
        cur = v(nxt)
        if (prev > 0) != (cur > 0):
            lo, hi = d, nxt
            for _ in range(60):
                mid = lo + (hi - lo) / 2
                lo, hi = (mid, hi) if (v(mid) > 0) == (prev > 0) else (lo, mid)
            return lo + (hi - lo) / 2
        d, prev = nxt, cur
    raise AssertionError("no Jupiter station found")


def _continuous_kin(origin: datetime):
    """The test's OWN continuous seam: longitude and speed (deg/s) interpolated between the two neighbouring Julian-Day doubles. (The sweep's seam is the
    od1-seam lane's concern, N-3a; this test isolates the station cut from it.)"""
    base = _jd(origin)

    def at(sec: float):
        x = sec / 86400.0
        j = base + x
        f = (base - j) + x
        ulp = math.ulp(j)
        j0 = j if f >= 0 else j - ulp
        frac = (f / ulp) if f >= 0 else (f / ulp + 1.0)
        l0, s0 = _lon_speed(j0)
        l1, s1 = _lon_speed(j0 + ulp)
        return (l0 + frac * _wrap180(l1 - l0)) % 360.0, (s0 + frac * (s1 - s0)) / 86400.0
    return at


def _real_sky_window(m, short: float = 1e-7):
    """Jupiter's first 2030-03 station S; the window [S - 2 d, S + 3 ms) (the support ends 3 ms after the Swiss station, the station is LISTED — the
    stretch between them is 3 ms); the tent's level is the station longitude `short` degrees short. With the default 1e-7° the crest (kernel 1.0) lies
    ~650 s from the station: ONE isolated maximum outside the 120 s zone, whose value is 2e-8 above the zone's, so the window still NUMBERS
    (SR-NEAR-STATION-TIE amends SR-STATION-NEAR-END: with `short` = 1e-9° the crest, ~70 s out, is inside the zone and the window is the named blank)."""
    assert_real_ephemeris()
    st = _jupiter_station(datetime(2030, 3, 1, tzinfo=timezone.utc))
    lo, hi = st - timedelta(days=2), st + timedelta(seconds=0.003)
    origin, length = lo, (hi - lo).total_seconds()
    level, orb = _lon_dt("Jupiter", st) - short, 5.0
    at = _continuous_kin(origin)
    listed = (st - origin).total_seconds()
    tent = m.Tent(offset=lambda s: _wrap180(at(s)[0] - level), orb=orb, velocity=lambda s: at(s)[1], stations=(listed,), min_station_spacing=19.75 * 86400.0)
    res = m.solve(m.Problem(0.0, length, m.OBJECTIVE_SUM, (m.Member("a", "r", ((0.0, length),), tent=tent),)))
    return res, st, lo, hi, origin, level, orb, listed


# ═══════════════════════════════ the claims: ONE oracle and ONE planted reversion each ═══════════════════════════════════════════════════

CLAIMS: dict = {}
REAL_SKY = {"N3B-1", "N3B-2"}


def claim(cid: str, old: str, new: str):
    def deco(fn):
        CLAIMS[cid] = (fn, old, new)
        return fn
    return deco


def _builder_equals_verifier(m):
    res, st, lo, hi, origin, level, orb, listed = _real_sky_window(m)
    assert res.status == m.SOLVED, (res.reason, res.detail)                       # the builder numbers
    peak = origin + timedelta(seconds=res.instant)
    assert 120.0 < (st - peak).total_seconds() < 1500.0, (peak, st)               # the isolated crest lies OUTSIDE the zone, before the station
    rec = chk.CheckRecord("a", "r", "jupiter", ((lo, hi),), tent=chk.TentFactor("Jupiter", level, orb))
    rep = chk.check_window(lo=lo, hi=hi, records=[rec], objective=chk.OBJ_SUM, position_at=_lon_dt, stored=chk.StoredWindow(peak, res.value), max_evals=300_000)
    assert rep.status == chk.VERIFIED, rep                                           # the independent verifier AGREES on value and instant
    assert res.value == pytest.approx(1.0, abs=1e-9)


@claim("N3B-1", "    if length <= 2 * TIME_TOL or _touches_station(tent, x, y):\n", "    if length <= 2 * TIME_TOL:\n")
def oracle_stretch_next_to_a_listed_station_is_a_cut(m):
    _builder_equals_verifier(m)


@claim("N3B-2", "NEAR_STATION_S = 120.0\n", "NEAR_STATION_S = 0.0\n")
def oracle_the_convention_equals_the_verifiers(m):
    _builder_equals_verifier(m)                                                    # behaviour first: a 0 s convention blanks here (the 9 DISAGREEs)
    assert m.NEAR_STATION_S == chk.NEAR_END_S == 120.0


@claim("N3B-3", "        tol += NEAR_STATION_NOISE_DEG / tent.orb\n", "        tol += 0.0\n")
def oracle_piece_next_to_a_listed_station_is_monotone_within_the_s0_bound(m):
    res = _solve(m, _station_world(m, wiggle=1e-9))
    assert res.status == m.SOLVED, (res.reason, res.detail)
    assert res.value == pytest.approx(0.6, abs=1e-8)                              # kernel 1 - 0.4/1 at the window end, to the wiggle


@claim("N3B-4", "NEAR_STATION_NOISE_DEG = 3.9e-9\n", "NEAR_STATION_NOISE_DEG = 1e-6\n")
def oracle_a_wiggle_beyond_the_s0_bound_still_blanks(m):
    res = _solve(m, _station_world(m, wiggle=1e-7))
    assert res.status == m.BLANK and res.reason == m.REASON_MONOTONE, (res.status, res.reason, res.detail)
    assert "not monotone" in res.detail


@claim("N3B-5", "NEAR_STATION_S = 120.0\n", "NEAR_STATION_S = 3600.0\n")
def oracle_an_unlisted_reversal_beyond_120_s_still_blanks(m):
    res = _solve(m, _reversal_world(m))
    assert res.status == m.BLANK and res.reason == m.REASON_MONOTONE, (res.status, res.reason, res.detail)
    assert "velocity changes sign" in res.detail


@claim("N3B-6", '"NEAR_STATION_S": NEAR_STATION_S, "NEAR_STATION_NOISE_DEG": NEAR_STATION_NOISE_DEG, ', "")
def oracle_the_certificate_carries_the_convention(m):
    res = _solve(m, _station_world(m, wiggle=1e-9))
    assert res.status == m.SOLVED
    cert = m.stored_certificate(res, objective=m.OBJECTIVE_SUM, t0_iso="2030-01-01T00:00:00+00:00")
    assert cert is not None
    lim = cert["limits"]
    assert lim.get("NEAR_STATION_S") == 120.0 and lim.get("NEAR_STATION_NOISE_DEG") == 3.9e-9, lim


# ═══════════════════════════════ the harness ═══════════════════════════════════════════════════════════════════════════════════════════

_COUNT = [0]


def reverted_module(old: str, new: str):
    """The solver's source with exactly ONE occurrence of `old` replaced by `new`, loaded as a throw-away module."""
    assert old != new and SRC.count(old) == 1, f"the planted reversion must match exactly once, matched {SRC.count(old)}x: {old[:70]!r}"
    _COUNT[0] += 1
    name = f"_reverted_window_solver_n3b_{_COUNT[0]}"
    mod = types.ModuleType(name)
    mod.__file__ = name
    sys.modules[name] = mod                                           # dataclasses resolve their annotations through sys.modules
    try:
        exec(compile(SRC.replace(old, new), name, "exec"), mod.__dict__)
    finally:
        sys.modules.pop(name, None)
    return mod


ALL_CASES = [pytest.param(cid, marks=requires_swieph if cid in REAL_SKY else (), id=cid) for cid in sorted(CLAIMS)]


@pytest.mark.parametrize("cid", ALL_CASES)
def test_oracle_passes_on_the_real_solver(cid):
    CLAIMS[cid][0](sol)


@pytest.mark.parametrize("cid", ALL_CASES)
def test_the_single_planted_reversion_fails_the_oracle(cid):
    oracle, old, new = CLAIMS[cid]
    reverted = reverted_module(old, new)          # built OUTSIDE the raises-block: a reversion that no longer matches is an ERROR, not a pass
    with pytest.raises(AssertionError):
        oracle(reverted)


def test_every_claim_has_exactly_one_reversion_and_one_oracle():
    assert set(CLAIMS) == {"N3B-1", "N3B-2", "N3B-3", "N3B-4", "N3B-5", "N3B-6"}
    assert len({(old, new) for _, old, new in CLAIMS.values()}) == len(CLAIMS)           # no two claims share a reversion


# ═══════════════════════════════ guards (no reversion: a property of the module) ═════════════════════════════════════════════════════════

def _imports(source: str) -> list:
    out = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = ("." * node.level) + (node.module or "")
            out += [base] + [f"{base}.{a.name}" for a in node.names]
    return out


def _imports_the_checker(source: str) -> bool:
    return any("window_solver_check" in n for n in _imports(source))


def test_k12_the_builder_imports_nothing_of_the_checker():
    assert not _imports_the_checker(SRC)


def test_the_k12_detector_reads_false_on_a_planted_import():
    for planted in ("from . import window_solver_check", "from .window_solver_check import NEAR_END_S", "import services.gochara_kernel.window_solver_check"):
        assert _imports_the_checker(SRC + "\n" + planted + "\n"), planted


def test_the_builders_constants_are_its_own_literals_equal_to_the_checkers():
    """Equal in value (owner ruling), separate in code: the builder's number is a literal in its own source, and equals the checker's `NEAR_END_S`."""
    assert "NEAR_STATION_S = 120.0\n" in SRC and "NEAR_STATION_NOISE_DEG = 3.9e-9\n" in SRC
    assert "NEAR_END_S = 120.0" in CHECKER_SRC and chk.NEAR_END_S == sol.NEAR_STATION_S
    assert sol.NEAR_STATION_S >= 2 * 16.7                      # S0 K-2: the spline/Swiss offset measured up to 16.7 s is well inside the convention
