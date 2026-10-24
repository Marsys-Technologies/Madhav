"""SR-OD1 N-3a (DIAG_P34 §5) — the builder reads the tent's offset and speed as a CONTINUOUS function of the solver's float time.

The ephemeris seam (`ka_gochara_v5.speed_at`: `jd = t.timestamp() / 86400 + 2440587.5`) reads on a Julian-Day double, a grid of 2^-31 d = 40.2 µs. Read raw, the tent
kernel is a STEP function of time that jumps by up to |speed|/orb × 40 µs ≈ 1e-10 at every step — more than the solver's own 1e-11 tolerances (`MONO_TOL`, `EPS_M`),
so a window whose support ends within one JD-ulp of its own orb crossing was blank under `monotone_arc_not_established` (50 + 5 windows of major_loss P3/P4, every one of
them a blank where the independent verifier's prover found the value). `window_solver.py` H3: "`Tent.offset` is a deterministic continuous function (the caller's seam)".
`window_sweep._kinematics` now interpolates linearly, at the exact float time, between the seam's reads at the two JD doubles that bracket it (wrap-safe), and leaves the
solver's limits (`MONO_TOL`, `EPS_M`, the certificate's `limits`) where they were.

CLAIMS, the source of each oracle and the single planted reversion that must FAIL it (every `*_reverted` test applies the reversion in-memory to the production module and
asserts that the oracle's claim then FAILS — the oracle has a detector that can read false, CLAUDE.md §N.8):

  K1  the offset is continuous in float time          oracle: a real Swiss Jupiter read every 0.5 µs moves by no more than |v|·Δt (a continuous function), never by a JD-ulp step
                                                      revert: the raw seam read (`rec.longitude_speed_at(origin + s)`, the pre-N-3a function)
  K2  the interpolation is wrap-safe                  oracle: a body crossing 360° -> 0° between two JD doubles reads the linear value (closed form), not a half-turn-off one
                                                      revert: interpolate the raw longitudes (no `_wrap180` of the step)
  K3  the speed is interpolated likewise              oracle: a seam whose speed changes linearly with JD reads linearly between nodes (closed form)
                                                      revert: the speed of the nearer / lower node
  K4  the position on the JD axis is exact            oracle: a linear world (lon = a + k·(jd − jd0)): the read equals the closed form at the TRUE time to 2e-11°,
                                                      although the origin's own JD double is up to 20 µs off its true instant
                                                      revert: position the origin by its rounded JD double only (drop the double-double low part)
  O1  a real-sky sliver is NUMBERED                   oracle: the kernel `1 − d/orb` (activity_kernel 1.1.0) peaks at 1 exactly where the body is on the target; a support that ends 6–60 µs
                                                      after its own orb exit (3 real bodies: Jupiter, prograde; Saturn, retrograde; Mercury, fast) is numbered 1.0
                                                      revert: the raw seam read -> blank `monotone_arc_not_established` (K1's reversion, here at window level)
  O2  the honest null survives                        oracle: a velocity sign change strictly inside a support, > 120 s from both ends, no listed station still blanks
                                                      `monotone_arc_not_established` (S0 K-2 / window_solver H1; none of the 55 real blanks can serve — they are all slivers)
                                                      revert: `_check_arc` relaxed -> the reversing window is numbered (wrongly)
  O3  builder = independent verifier on the fixed windows
                                                      oracle: `verify_window_semantics(solver_check=True)` over the O1 windows -> VERIFIED, the prover's own maximum is the stored one
                                                      revert: a stored objective_value + 0.01 -> `certificate_disagrees_with_stored_window` (the detector control)
  O4  a rising × falling crossing (P4) is solved and its certificate is AGREED
                                                      oracle: Jupiter's activity rises through 0.5 as Saturn's falls through 0.5 (built on the real sky): the max-min is 0.5; the verifier's
                                                      certificate check (`window_cert_check`) agrees
                                                      revert: the raw seam read -> blank
"""
from __future__ import annotations

import dataclasses
import math
from datetime import datetime, timedelta, timezone
from fractions import Fraction

import pytest

from services.gochara_kernel import window_solver as sol
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel.knots import calc_sidereal_lon, calc_sidereal_lon_speed

from .conftest import _PROBLEMS, EPHE_PATH
from .test_a53_window_sweep import _rec, _rows_declared  # noqa: F401
from .test_a53_window_sweep import _restore_factor_registry  # noqa: F401  (autouse: synthetic rows never outlive their test)
from .test_od1_s3_integration import GRAIN_P3, GRAIN_P4, ROWS, _tamper, _verify

UTC = timezone.utc
DAY = 86400.0
JD_EPOCH = 2440587.5
needs_swiss = pytest.mark.skipif(bool(_PROBLEMS), reason="NOT_RUN: pinned .se1 ephemeris files missing or mismatched")


# ── the real sky (the production seams' own formulas, `ka_gochara_v5.position_at` / `speed_at`) ────────────────────────

def _jd(t: datetime) -> float:
    return t.timestamp() / 86400.0 + JD_EPOCH


def _pos(body: str, t: datetime) -> float:
    lon, rf = calc_sidereal_lon(body.title(), _jd(t), EPHE_PATH)
    assert rf & 2
    return lon


def _speed_seam(body: str):
    def seam(t: datetime):
        lon, per_day, rf = calc_sidereal_lon_speed(body.title(), _jd(t), EPHE_PATH)
        assert rf & 2
        return lon, per_day
    return seam


def _wrap(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def _bisect(f, a: datetime, b: datetime) -> datetime:
    """The instant in [a, b] where the monotone `f` (negative at a, positive at b) crosses zero."""
    for _ in range(70):
        m = a + (b - a) / 2
        a, b = (m, b) if f(m) < 0 else (a, m)
    return b


def _raw_kinematics(rec, origin, cfg):
    """The function BEFORE N-3a (the planted reversion of K1, O1, O4): the seam read at the solver's time rounded to the seam's own JD double."""
    cache: dict = {}

    def at(s):
        got = cache.get(s)
        if got is None:
            lon, per_day = rec.longitude_speed_at(origin + timedelta(seconds=s))
            got = cache[s] = (float(lon), float(per_day) / DAY)
            if len(cache) > 16:
                cache.clear()
        return got
    return at


def _speed_record(seam, agent="jupiter", **kw):
    """A record whose ONLY ephemeris contact is `seam` (position and speed from one read), as the writer's records are."""
    return _rec("R", path=kw.pop("path", "P3"), agent=agent, root=kw.pop("root", "RR"), supports=((0, 1),), relation="conjunction", kind="degree_point",
                longitude_at=lambda t: seam(t)[0], longitude_speed_at=seam, **kw)


# ═════ K1: the offset is continuous in float time ═══════════════════════════════════════════════════════════════════════

ORIGIN = datetime(2012, 6, 5, 3, 21, 9, 123457, tzinfo=UTC)


@needs_swiss
def test_k1_a_real_swiss_read_is_a_continuous_function_of_the_solver_time():
    """Oracle: a continuous function moves by no more than |v|·Δt (+ the seam's float noise) between two reads Δt apart. Over 600 reads at Δt = 0.5 µs (≈ 15 JD-ulps)
    Jupiter's longitude moves by 1.3e-12° per step; one raw JD-ulp step is 1e-10°."""
    seam = _speed_seam("jupiter")
    at = ws._kinematics(_speed_record(seam), ORIGIN, ws.PRODUCTION_SOLVER)
    s0, dt = 3.0e6, 0.5e-6
    lons = [at(s0 + k * dt)[0] for k in range(600)]
    v = abs(at(s0)[1])                                                # deg/s
    worst = max(abs(_wrap(b - a)) for a, b in zip(lons, lons[1:]))
    assert worst <= 1.1 * v * dt + 1e-13, f"the offset jumps by {worst:.3e} deg between reads {dt:g} s apart (|v|·Δt = {v * dt:.3e})"


@needs_swiss
def test_k1_reverted_the_raw_seam_read_jumps_by_a_jd_ulp_step_and_the_oracle_notices(monkeypatch):
    monkeypatch.setattr(ws, "_kinematics", _raw_kinematics)
    with pytest.raises(AssertionError, match="the offset jumps"):
        test_k1_a_real_swiss_read_is_a_continuous_function_of_the_solver_time()


# ═════ K2 / K3 / K4: the interpolation itself, closed-form worlds ═══════════════════════════════════════════════════════

def _linear_seam(lon0, k_deg_per_day, jd0, speed=None):
    """lon = lon0 + k·(jd − jd0) [deg, wrapped], where jd is the seam's own JD double (what the production seam computes from the datetime)."""
    def seam(t):
        jd = _jd(t)
        return (lon0 + k_deg_per_day * (jd - jd0)) % 360.0, (k_deg_per_day if speed is None else speed(jd))
    return seam


def _true_jd(origin: datetime, s: float) -> Fraction:
    """The exact JD of `origin + s seconds` (rational arithmetic; independent of the code under test)."""
    us = (origin - datetime(1970, 1, 1, tzinfo=UTC)) // timedelta(microseconds=1)
    return Fraction(us, 86_400_000_000) + Fraction(JD_EPOCH) + Fraction(s) / 86400


def test_k4_the_read_is_at_the_true_instant_not_at_the_rounded_origin():
    """Source: the seam's grid is the JD double (2^-31 d). A linear world lon = 100 + 1.0·(jd − jd0) has the closed form at the TRUE time; the origin below sits
    ≈ 17 µs from its own nearest JD double, so an origin positioned by its rounded double alone is 1.9e-10° off (1° per day × 17 µs)."""
    origin = datetime(2012, 6, 5, 3, 21, 9, 123457, tzinfo=UTC)
    jd0 = 2456000.0
    at = ws._kinematics(_speed_record(_linear_seam(100.0, 1.0, jd0)), origin, ws.PRODUCTION_SOLVER)
    worst = 0.0
    for s in (0.0, 1.0e-6, 17.0e-6, 40.0e-6, 3.7, 86400.0 * 3.3 + 0.123456, 1.0e6 + 2.5e-5):
        expected = 100.0 + float(_true_jd(origin, s) - Fraction(jd0))
        worst = max(worst, abs(at(s)[0] - expected))
    assert worst < 2e-11, f"the read is {worst:.2e} deg off the closed form at the true time"


def test_k4_reverted_positioning_the_origin_by_its_rounded_jd_double_is_caught(monkeypatch):
    origin = datetime(2012, 6, 5, 3, 21, 9, 123457, tzinfo=UTC)
    assert abs(float(_true_jd(origin, 0.0) - Fraction(_jd(origin)))) * DAY > 5e-6          # the fixture does sit > 5 µs from its rounded double
    real = ws._split_jd
    monkeypatch.setattr(ws, "_split_jd", lambda o: (real(o)[0], 0.0))                  # the low part dropped
    with pytest.raises(AssertionError, match="off the closed form"):
        test_k4_the_read_is_at_the_true_instant_not_at_the_rounded_origin()


def test_k2_the_interpolation_is_wrap_safe_across_360():
    """A body at 359.99999999° moving 0.2°/day crosses 360° inside one JD-ulp bracket: the longitude read must be the linear value, in [0, 360), never a half-turn off."""
    origin = datetime(2012, 6, 5, tzinfo=UTC)
    jd_cross = float(_true_jd(origin, 0.30 * DAY))                       # a JD double: the instant the body passes 360° (= 0°)
    at = ws._kinematics(_speed_record(_linear_seam(0.0, 0.2, jd_cross)), origin, ws.PRODUCTION_SOLVER)
    s_cross = float((Fraction(jd_cross) - _true_jd(origin, 0.0)) * 86400)
    for ds in (-2.0e-4, -3.1e-5, -1.0e-6, 0.0, 1.0e-6, 3.1e-5, 2.0e-4):
        lon = at(s_cross + ds)[0]
        assert 0.0 <= lon < 360.0
        assert abs(_wrap(lon - 0.2 * ds / DAY)) < 2e-11, f"at {ds:+g} s from the crossing the read is {lon!r}"


def test_k2_reverted_interpolating_the_raw_longitudes_gives_a_half_turn_across_the_wrap(monkeypatch):
    monkeypatch.setattr(ws, "_wrap180", lambda x: x)
    with pytest.raises(AssertionError):
        test_k2_the_interpolation_is_wrap_safe_across_360()


def test_k3_the_speed_is_interpolated_between_the_two_reads_likewise():
    """A seam whose speed changes by 1e6 deg/day per day (so one JD-ulp moves it by 4.7e-4 deg/day): the read speed is linear in the true time between the nodes."""
    origin = datetime(2012, 6, 5, 3, 21, 9, 123457, tzinfo=UTC)
    jd0 = 2456000.0
    seam = _linear_seam(100.0, 0.2, jd0, speed=lambda jd: 5.0 + 1.0e6 * (jd - jd0))
    at = ws._kinematics(_speed_record(seam), origin, ws.PRODUCTION_SOLVER)
    for s in (0.0, 1.0e-5, 2.0e-5, 3.0e-5, 4.0e-5, 12.5e-5, 3.0):
        expected = (5.0 + 1.0e6 * float(_true_jd(origin, s) - Fraction(jd0))) / DAY
        assert abs(at(s)[1] - expected) < 1e-11, f"s={s}: speed {at(s)[1]!r} vs {expected!r}"          # deg/s; a node-step is up to 5e-9


def test_k3_reverted_the_speed_of_the_lower_node_is_a_step_and_is_caught(monkeypatch):
    real = ws._kinematics

    def lower_node_speed(rec, origin, cfg):
        at = real(rec, origin, cfg)

        def f(s):
            lon, _ = at(s)
            jd = _true_jd(origin, s)
            node = float(jd)
            node = node if Fraction(node) <= jd else math.nextafter(node, -math.inf)
            return lon, rec.longitude_speed_at(ws._jd_to_datetime(node))[1] / DAY
        return f
    monkeypatch.setattr(ws, "_kinematics", lower_node_speed)
    with pytest.raises(AssertionError, match="speed"):
        test_k3_the_speed_is_interpolated_between_the_two_reads_likewise()


# ═════ O1: a real-sky sliver is numbered ════════════════════════════════════════════════════════════════════════════════

#: (body, a date it is in the sky, days to search for its orb exit). Jupiter prograde; Saturn retrograde; Mercury fast. The orb is the TEST orb 1.0° (`ROWS`).
SLIVER_SKIES = [("jupiter", datetime(2012, 6, 1, 12, tzinfo=UTC), 60), ("saturn", datetime(2013, 3, 1, 12, tzinfo=UTC), 80), ("mercury", datetime(2011, 3, 1, 12, tzinfo=UTC), 30)]
#: where the support END sits relative to the body's own orb exit [µs] — the stored instant is exact only to one JD-ulp (40.2 µs), so any of these is what a build can store
SLIVER_ENDS_US = range(0, 61, 6)


def _sliver_record(body, t_in, span_days, end_us):
    """A conjunction record on the real sky: the target point is placed so the body ENTERS the 1° orb at `t_in` and crosses the target (kernel 1.0) mid-support; the support
    ends `end_us` µs after the body's own orb exit."""
    sgn = 1.0 if calc_sidereal_lon_speed(body.title(), _jd(t_in), EPHE_PATH)[1] > 0 else -1.0
    level = (_pos(body, t_in) + sgn * 1.0) % 360.0
    t_out = _bisect(lambda t: sgn * _wrap(_pos(body, t) - level) - 1.0, t_in, t_in + timedelta(days=span_days))
    rec = _rec("A", path="P3", agent=body, root="RA", supports=((0, 1),), relation="conjunction", kind="degree_point", target=f"point:{level!r}",
               longitude_at=lambda t: _pos(body, t), longitude_speed_at=_speed_seam(body))
    return dataclasses.replace(rec, supports=((t_in, t_out + timedelta(microseconds=end_us)),))


def _sliver_drafts(body, t_in, span_days):
    return [(e, _sliver_record(body, t_in, span_days, e)) for e in SLIVER_ENDS_US]


@needs_swiss
@pytest.mark.parametrize("body,t_in,span", SLIVER_SKIES, ids=[s[0] for s in SLIVER_SKIES])
def test_o1_a_support_ending_within_a_jd_ulp_of_its_orb_exit_is_numbered_at_the_kernels_peak(body, t_in, span):
    for end_us, rec in _sliver_drafts(body, t_in, span):
        (draft,) = ws.draft_windows("marriage", [rec], ROWS, solver=ws.PRODUCTION_SOLVER)[0]
        assert draft.unqualified_reason is None and draft.unresolved == {}, f"{body}: support end +{end_us} µs: {draft.unqualified_reason}"
        assert abs(draft.objective_value - 1.0) < 1e-12 and draft.peak_instant is not None      # kernel 1 − d/orb is 1 where the body is ON the target


@needs_swiss
@pytest.mark.parametrize("body,t_in,span", SLIVER_SKIES, ids=[s[0] for s in SLIVER_SKIES])
def test_o1_reverted_the_raw_seam_blanks_a_sliver_window_under_monotone_arc_not_established(monkeypatch, body, t_in, span):
    """The reversion makes O1's claim false: with the raw seam read at least one of the windows O1 numbers is blank under the named reason (DIAG_P34 cluster A)."""
    monkeypatch.setattr(ws, "_kinematics", _raw_kinematics)
    reasons = {ws.draft_windows("marriage", [rec], ROWS, solver=ws.PRODUCTION_SOLVER)[0][0].unqualified_reason for _e, rec in _sliver_drafts(body, t_in, span)}
    assert "monotone_arc_not_established" in reasons
    with pytest.raises(AssertionError):
        test_o1_a_support_ending_within_a_jd_ulp_of_its_orb_exit_is_numbered_at_the_kernels_peak(body, t_in, span)


# ═════ O2: the honest null survives ═════════════════════════════════════════════════════════════════════════════════════

T0 = datetime(2010, 1, 1, tzinfo=UTC)


def _turning_seam(t):
    """A body that moves AWAY from the target to 3° (outside the 1° orb: kernel 0) on day 1.5 and turns back through it: lon = 97 + 0.444 (d − 1.5)². Its speed changes sign on
    day 1.5 — strictly inside a (0, 10) d support, 129 600 s from the start and 734 400 s from the end, no station listed. The kernel is flat 0 where it turns, so the
    solver's piece classification cannot see the reversal; only H1 (the velocity-sign check between stations) can."""
    d = (t - T0).total_seconds() / DAY
    return (97.0 + 0.444 * (d - 1.5) ** 2) % 360.0, 0.888 * (d - 1.5)


def _turning_draft():
    rec = _rec("A", path="P3", agent="saturn", root="RA", supports=((0, 10),), relation="conjunction", kind="degree_point",
               longitude_at=lambda t: _turning_seam(t)[0], longitude_speed_at=_turning_seam)
    return ws.draft_windows("marriage", [rec], ROWS, solver=ws.PRODUCTION_SOLVER)[0][0]


def test_o2_a_reversal_inside_the_support_still_blanks_under_its_named_reason_through_the_continuous_seam():
    draft = _turning_draft()
    assert draft.peak_instant is None and draft.score is None and draft.unqualified_reason == "monotone_arc_not_established"
    assert draft.unresolved == {"monotone_arc_not_established": 1}


def test_o2_reverted_with_the_arc_check_relaxed_the_reversing_window_is_numbered_wrongly(monkeypatch):
    monkeypatch.setattr(sol, "_check_arc", lambda *a, **k: None)
    with pytest.raises(AssertionError):
        test_o2_a_reversal_inside_the_support_still_blanks_under_its_named_reason_through_the_continuous_seam()


# ═════ O3: builder = independent verifier on the fixed windows ═════════════════════════════════════════════════════════

def _swiss_position(body, t):
    return _pos(body, t)


@needs_swiss
@pytest.mark.parametrize("body,t_in,span", SLIVER_SKIES, ids=[s[0] for s in SLIVER_SKIES])
def test_o3_the_independent_verifier_reproduces_every_fixed_sliver_window(body, t_in, span):
    for end_us, rec in _sliver_drafts(body, t_in, span)[::2]:
        (draft,) = ws.draft_windows("marriage", [rec], ROWS, solver=ws.PRODUCTION_SOLVER)[0]
        report = _verify([draft], [rec], ROWS("P3", "1.0.0"), _swiss_position, grain=GRAIN_P3)
        assert report["status"] == "VERIFIED", (body, end_us)
        assert (report["solver_checked_windows"], report["numeric_reproduced"], report["fully_reproduced"]) == (1, 1, 1)
        assert report["windows_detail"][0]["objective_value"] == pytest.approx(draft.objective_value, abs=1e-10)


@needs_swiss
def test_o3_detector_control_a_stored_maximum_moved_by_0_01_is_reported():
    """The zero above is earned: the same verifier refuses the same window with its stored maximum moved by 0.01."""
    body, t_in, span = SLIVER_SKIES[0]
    rec = _sliver_record(body, t_in, span, 30)
    (draft,) = ws.draft_windows("marriage", [rec], ROWS, solver=ws.PRODUCTION_SOLVER)[0]
    with pytest.raises(RuntimeError, match="certificate_disagrees_with_stored_window"):
        _verify([_tamper(draft, objective_value=draft.objective_value + 0.01, score=draft.score + 0.01)], [rec], ROWS("P3", "1.0.0"), _swiss_position, grain=GRAIN_P3)


# ═════ O4: a rising × falling crossing (P4) is solved and its certificate agreed ═══════════════════════════════════════

def _crossing_records(tc: datetime, jin_us: int, jout_us: int, sin_us: int, sout_us: int):
    """P4 on the real sky (both prograde at `tc`): Jupiter is 0.5° short of its target at `tc` (activity RISING through 0.5), Saturn is 0.5° past its own (activity FALLING
    through 0.5). Each support runs from the body's orb entry to its orb exit, moved by the given µs. The max-min is the crossing: 0.5."""
    out = []
    for body, root, sign_in, shifts in (("jupiter", "RJ", +1.0, (jin_us, jout_us)), ("saturn", "RS", -1.0, (sin_us, sout_us))):
        sgn = 1.0 if calc_sidereal_lon_speed(body.title(), _jd(tc), EPHE_PATH)[1] > 0 else -1.0
        level = (_pos(body, tc) + sign_in * sgn * 0.5) % 360.0
        entry = _bisect(lambda t: sgn * _wrap(_pos(body, t) - level) + 1.0, tc - timedelta(days=40), tc)
        exit_ = _bisect(lambda t: sgn * _wrap(_pos(body, t) - level) - 1.0, tc, tc + timedelta(days=80))
        rec = _rec(root[1], path="P4", agent=body, root=root, supports=((0, 1),), relation="conjunction", kind="degree_point", target=f"point:{level!r}",
                   longitude_at=lambda t, _b=body: _pos(_b, t), longitude_speed_at=_speed_seam(body))
        out.append(dataclasses.replace(rec, supports=((entry + timedelta(microseconds=shifts[0]), exit_ + timedelta(microseconds=shifts[1])),)))
    return out


CROSSING_TC = datetime(2012, 8, 1, 12, tzinfo=UTC)
CROSSING_ENDS_US = [(0, 4, 0, 4), (0, 20, 0, 36), (0, 36, 0, 12)]       # (J entry, J exit, S entry, S exit) shifts: the exits sit 4–36 µs past their orb crossings


@needs_swiss
def test_o4_a_rising_times_falling_crossing_is_numbered_and_its_certificate_is_agreed():
    for ends in CROSSING_ENDS_US:
        recs = _crossing_records(CROSSING_TC, *ends)
        (draft,) = ws.draft_windows("marriage", recs, ROWS, solver=ws.PRODUCTION_SOLVER)[0]
        assert draft.unqualified_reason is None, (ends, draft.unqualified_reason)
        assert abs(draft.objective_value - 0.5) < 1e-9                           # min(act_J, act_S) crosses at 0.5 exactly by construction
        assert draft.solver_certificate is not None and draft.solver_certificate["outcome"] == "solved"
        report = _verify([draft], recs, ROWS("P4", "1.0.0"), _swiss_position, grain=GRAIN_P4)
        assert report["status"] == "VERIFIED" and (report["solver_checked_windows"], report["fully_reproduced"]) == (1, 1), ends


@needs_swiss
def test_o4_reverted_the_raw_seam_blanks_the_crossing_window(monkeypatch):
    # SR-P1-SLIVER-D2: the raw-seam blank lived in the 4-36 us pieces this fixture's support ends cut — pieces shorter than one JD ulp, which are no longer classified
    # at all. The claim measured here (the continuous seam) is independent of that rule, so the rule is switched off to keep the reversion observable.
    monkeypatch.setattr(sol, "sliver_resolution_s", lambda origin_jd, t: 0.0)
    monkeypatch.setattr(ws, "_kinematics", _raw_kinematics)
    reasons = {ws.draft_windows("marriage", _crossing_records(CROSSING_TC, *ends), ROWS, solver=ws.PRODUCTION_SOLVER)[0][0].unqualified_reason for ends in CROSSING_ENDS_US}
    assert reasons & {"monotone_arc_not_established", "solver_certificate_incomplete"}
    with pytest.raises(AssertionError):
        test_o4_a_rising_times_falling_crossing_is_numbered_and_its_certificate_is_agreed()
