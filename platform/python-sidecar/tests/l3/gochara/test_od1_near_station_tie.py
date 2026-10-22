"""SR-OD1 — SR-NEAR-STATION-TIE (madhav-44, option A): the STATION-ZONE TIE RULE, builder and independent checker, each from its OWN code (K12).

The measured fact (S0 K-2 and the 2026-10-22 diagnosis): within <= 120 s of a Venus/Mercury (and Jupiter) station the real Swiss curve is a noise COMB — the
longitude steps by ~1e-9 deg, so F has 34-72 local maxima 0.27-1.3 s apart, ALL within TIE = 1e-9 of the zone's top. Both sides read a zone by its two ends, so they
disagreed on WHICH lone candidate stood for "the earliest distinct maximum within TIE" (6 of 6 measured windows: crest root vs window edge -> `earlier_tie_not_taken`).
No instant of the comb is decidable (Q12 is not relaxed), so the ruled outcome is the named blank:

  * BUILDER   blanks `tie_isolation_unresolved` when a listed station's zone (+-NEAR_STATION_S) reaches within TIE + its noise bound (NEAR_STATION_NOISE_DEG / orb)
              of the window's maximum;
  * CHECKER   returns UNVERIFIED `tie_isolation_unresolved` (INCONCLUSIVE class, R-6: demoted at the seal to the named blank, counted toward the 0.5 % cap) under
              the same condition, from its own code — a stored legacy number is no longer REFUTED by whichever lone candidate survived;
  * the checker's piece-end sample is a true LEFT LIMIT (one microsecond inside the piece), not the value at the cut, where the Swiss longitude steps.
  SR-STATION-NEAR-END is amended: a near-station window NUMBERS unless this condition holds.

Claims — each with ONE doctrine-grounded oracle and ONE planted reversion that makes it fail (the real Swiss sky, pinned corpus; the analytic worlds are closed form):

  NST-1 builder: the tie zone is the named blank       oracle: Venus 2029-12-16, window ending 3 ms after the station, level = the station longitude (measured case 3)
                                                       reversion: drop the blank (`if False`)
  NST-2 checker: the same window is UNVERIFIED `tie_isolation_unresolved`, INCONCLUSIVE, never REFUTED       reversion: drop the zone test (earlier_tie_not_taken returns)
  NST-3 builder: ONE isolated maximum near a station still NUMBERS (Venus, level 1e-4 deg short: the crest, ~6000 s out, is 2e-5 above the zone)      reversion: blank every zone
  NST-4 checker: that window is VERIFIED                                                                        reversion: blank every zone
  NST-5 checker: the piece-end sample is the true left limit (Venus 2031-07-20 staircase: 0.999999999985 before the crest cut, 0.9999999998 after)   reversion: sample AT the cut
  NST-6 the count of windows blanked by the rule, per class                    (`window_sweep.near_station_tie_report`)      reversion: count every blank
  NST-7 the 0.5 % cap, integers                                                                                 reversion: `>=`
  NST-8 the verifier-side confirmation of a stored builder blank (`confirm_tie_isolation`)                      reversion: always None
  NST-9 end to end (sweep -> stored blank -> independent verifier): the verifier CONFIRMS the blank             reversion: the verifier forgets the reason
  NST-10 end to end: a station just OUTSIDE the window (the sweep lists it within NEAR_STATION_S) still marks the zone   reversion: list only the stations inside
  NST-11 builder: a PLATEAU window (the max-min objective held at 1.0 over the whole window by residence steps — the tie set is the whole window, NOT inside the
         station zone) NUMBERS at its start; the zone rule blanks only a tie set that lies INSIDE the zone (the ruling, verbatim)   reversion: drop the "inside the zone" test
  NST-12 checker: the same plateau window with its stored number (1.0 at the window start) is VERIFIED, never UNVERIFIED `tie_isolation_unresolved`   reversion: drop the same test
  K12   the checker imports nothing of the builder, the builder nothing of the checker; the noise bound is a literal in each
"""
from __future__ import annotations

import ast
import math
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.gochara_kernel import numerical_window_gate as nwg
from services.gochara_kernel import window_cert_check as wcc
from services.gochara_kernel import window_solver as sol
from services.gochara_kernel import window_solver_check as chk
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel import window_verifier as wv

from .conftest import EPHE_PATH, assert_real_ephemeris, requires_swieph
from .test_a53_window_sweep import _rec  # noqa: F401
from .test_a53_window_sweep import _restore_factor_registry  # noqa: F401  (autouse: synthetic rows never outlive their test)
from .test_od1_s3_integration import _Conn, _d, _days, _jup, _position, _stored, _member_rows, ROWS, GRAIN_P4, DAY  # noqa: F401

REASON = "tie_isolation_unresolved"          # this test's own literal: the shared name of the two sides' code, never imported from either
SRC = {"builder": Path(sol.__file__).read_text(), "checker": Path(chk.__file__).read_text(), "sweep": Path(ws.__file__).read_text(),
       "verifier": Path(wv.__file__).read_text()}
REAL = {"sol": sol, "chk": chk, "ws": ws, "wv": wv}
UTC = timezone.utc


# ── the real sky (pinned Swiss corpus) ───────────────────────────────────────────────────────────────────────────────────────────────────

def _jd(d: datetime) -> float:
    return d.timestamp() / 86400.0 + 2440587.5


def _lon_speed(body: str, jd: float):
    from services.gochara_kernel import knots
    lon, spd, rf = knots.calc_sidereal_lon_speed(body, jd, EPHE_PATH)
    assert rf & 2
    return lon, spd


def _lon_dt(body: str, d: datetime) -> float:
    from services.gochara_kernel import knots
    return knots.calc_sidereal_lon(body, _jd(d), EPHE_PATH)[0]


def _wrap180(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def _station(body: str, start: datetime) -> datetime:
    """The first Swiss speed sign change of `body` after `start` (the test's own scan + bisection to 1 µs)."""
    v = lambda d: _lon_speed(body, _jd(d))[1]                                                      # noqa: E731
    d, prev = start, v(start)
    for _ in range(400):
        nxt = d + timedelta(days=1.0)
        cur = v(nxt)
        if (prev > 0) != (cur > 0):
            lo, hi = d, nxt
            for _ in range(60):
                mid = lo + (hi - lo) / 2
                lo, hi = (mid, hi) if (v(mid) > 0) == (prev > 0) else (lo, mid)
            return lo + (hi - lo) / 2
        d, prev = nxt, cur
    raise AssertionError(f"no {body} station found")


def _continuous_kin(body: str, origin: datetime):
    """The test's OWN continuous seam: longitude and speed (deg/s) interpolated between the two neighbouring Julian-Day doubles (the sweep's seam is the
    od1-seam lane's concern; this test isolates the zone rule from it)."""
    base = _jd(origin)

    def at(sec: float):
        x = sec / 86400.0
        j = base + x
        f = (base - j) + x
        ulp = math.ulp(j)
        j0 = j if f >= 0 else j - ulp
        frac = (f / ulp) if f >= 0 else (f / ulp + 1.0)
        l0, s0 = _lon_speed(body, j0)
        l1, s1 = _lon_speed(body, j0 + ulp)
        return (l0 + frac * _wrap180(l1 - l0)) % 360.0, (s0 + frac * (s1 - s0)) / 86400.0
    return at


ORB = 5.0


def _case(body: str, scan_from: datetime, side: str, short: float):
    """A window 3 ms past (`end_after`) / 3 ms before (`start_before`) a REAL Swiss station of `body`, the station LISTED, the tent's level the station
    longitude `short` degrees short. 2 days of support on the other side."""
    assert_real_ephemeris()
    st = _station(body, scan_from)
    lo, hi = (st - timedelta(days=2), st + timedelta(seconds=0.003)) if side == "end_after" else (st - timedelta(seconds=0.003), st + timedelta(days=2))
    length = (hi - lo).total_seconds()
    level = _lon_dt(body, st) - short
    return SimpleNamespace(body=body, st=st, lo=lo, hi=hi, length=length, level=level, listed=(st - lo).total_seconds(), at=_continuous_kin(body, lo))


def _problem(m, c):
    tent = m.Tent(offset=lambda s: _wrap180(c.at(s)[0] - c.level), orb=ORB, velocity=lambda s: c.at(s)[1], stations=(c.listed,), min_station_spacing=19.75 * 86400.0)
    return m.Problem(0.0, c.length, m.OBJECTIVE_SUM, (m.Member("a", "r", ((0.0, c.length),), tent=tent),))


def _record(k, c):
    return k.CheckRecord("a", "r", c.body.lower(), ((c.lo, c.hi),), tent=k.TentFactor(c.body, c.level, ORB))


def _check(k, c, peak, value):
    return k.check_window(lo=c.lo, hi=c.hi, records=[_record(k, c)], objective=k.OBJ_SUM, position_at=_lon_dt, stored=k.StoredWindow(peak, value), max_evals=300_000)


# measured case 3 (Venus 2029-12-16, window end 3 ms after the station, level = the station longitude): the legacy builder numbered the window END, value 1.0
def tie_case():
    return _case("Venus", datetime(2029, 9, 1, tzinfo=UTC), "end_after", 0.0)


# a near-station window with ONE isolated maximum: the crest (kernel 1.0) is ~6000 s before the station, 2e-5 above the zone's value
def isolated_case():
    return _case("Venus", datetime(2029, 9, 1, tzinfo=UTC), "end_after", 1e-4)


# ═══════════════════════════════ the claims: ONE oracle and ONE planted reversion each ═══════════════════════════════════════════════════

CLAIMS: dict = {}
REAL_SKY = {"NST-1", "NST-2", "NST-3", "NST-4", "NST-5", "NST-8"}


def claim(cid: str, target: str, old: str, new: str):
    def deco(fn):
        CLAIMS[cid] = (fn, target, old, new)
        return fn
    return deco


@claim("NST-1", "builder", "    if zone_tie is not None:\n        raise _Blank(REASON_TIE_ISOLATION, zone_tie)\n",
       "    if False:\n        raise _Blank(REASON_TIE_ISOLATION, zone_tie)\n")
def oracle_the_builder_blanks_the_tie_zone(mods):
    c = tie_case()
    res = mods.sol.solve(_problem(mods.sol, c))
    assert (res.status, res.reason, res.value, res.instant) == (mods.sol.BLANK, REASON, None, None), (res.status, res.reason, res.value)


@claim("NST-2", "checker", "        zone = self._zone_tie(m_hat, ties)\n", "        zone = None\n")
def oracle_the_checker_returns_the_inconclusive_blank_never_a_refutation(mods):
    c = tie_case()
    rep = _check(mods.chk, c, c.hi - timedelta(microseconds=1), 1.0)                  # the number the legacy builder stored: the window end, 1.0
    assert rep.status == mods.chk.UNVERIFIED and not rep.findings, (rep.status, rep.codes())
    assert rep.codes() == [REASON]
    assert {r for r, _d in rep.unverified} <= wcc.INCONCLUSIVE_REASONS                  # R-6: INCONCLUSIVE -> demoted to the named blank, counted toward the cap


@claim("NST-3", "builder", "        if zone_top >= top - TIE - noise and all(lo <= t <= hi for t in ties):\n", "        if True:\n")
def oracle_an_isolated_maximum_near_a_station_still_numbers(mods):
    c = isolated_case()
    res = mods.sol.solve(_problem(mods.sol, c))
    assert res.status == mods.sol.SOLVED, (res.reason, res.detail)
    assert res.value == pytest.approx(1.0, abs=1e-9)
    assert 120.0 < c.listed - res.instant < 20000.0, c.listed - res.instant                # the crest, outside the zone, before the station
    direct = 1.0 - abs(_wrap180(_lon_dt(c.body, c.lo + timedelta(seconds=res.instant)) - c.level)) / ORB
    assert direct == pytest.approx(1.0, abs=1e-8)                                           # and the real Swiss sky is at its crest there


@claim("NST-4", "checker", "            if zone_top is not None and zone_top >= m_hat - TIE - noise and all(lo <= t <= hi for t in ties):\n", "            if zone_top is not None:\n")
def oracle_the_checker_verifies_the_isolated_maximum(mods):
    c = isolated_case()
    res = sol.solve(_problem(sol, c))                                                      # the REAL builder's number
    assert res.status == sol.SOLVED
    rep = _check(mods.chk, c, c.lo + timedelta(seconds=res.instant), res.value)
    assert rep.status == mods.chk.VERIFIED, (rep.status, rep.codes())


@claim("NST-5", "checker", "self._vals(pc, r - US if r - l > 2 * US else r)", "self._vals(pc, r)")
def oracle_the_piece_end_sample_is_the_true_left_limit(mods):
    """Venus 2031-07-20, window starting 3 ms before the station, level 1e-9 short: the crest cut (the tent root, ~21.11 s out) sits on a STAIRCASE jump of the
    Swiss longitude — F is 0.999999999985039 just before it and 0.999999999788872 at it. The first piece's right sample must be the former (the left limit)."""
    c = _case("Venus", datetime(2031, 1, 1, tzinfo=UTC), "start_before", 1e-9)
    k = mods.chk
    eng = k._Engine(c.lo, c.hi, [_record(k, c)], k.OBJ_SUM, k.StoredWindow(c.lo, 1.0), _lon_dt, peak_tolerance_s=1.0, max_evals=300_000,
                    event_class=None, against_evaluated=False)
    xs = eng._cuts()
    pieces = [eng._make_piece(l, r) for l, r in zip(xs, xs[1:])]
    crest = next(p for p in pieces if 10.0 < p.r < 30.0)                                 # the piece that ends at the crest root
    f = lambda t: 1.0 - abs(_wrap180(_lon_dt(c.body, c.lo + timedelta(seconds=t)) - c.level)) / ORB     # noqa: E731  (the test's own direct read)
    left, at_cut = f(crest.r - 1e-6), f(crest.r)
    assert left - at_cut > 1e-10                                                          # the world has the step this claim is about
    assert crest.F_r == pytest.approx(left, abs=1e-14)                                    # the sample is the value just BEFORE the cut …
    assert abs(crest.F_r - at_cut) > 1e-10                                                # … not the value at it


def _drafts(n_tie, n_budget, n_numbered):
    mk = lambda reason, peak: ws.WindowDraft(interval=(_d(0), _d(1)), peak_instant=peak, score=None, evidence_for=None, evidence_against=None,      # noqa: E731
                                             outcome_valence_for_native="unqualified", severity=None, record_ids=(), null_states_used=[], unresolved={},
                                             members=1, qualified_members=1, unqualified_reason=reason)
    return ([mk(REASON, None) for _ in range(n_tie)] + [mk("solver_budget_exhausted", None) for _ in range(n_budget)]
            + [mk(None, _d(0.5)) for _ in range(n_numbered)])


@claim("NST-6", "sweep", "d.unqualified_reason == _solver.REASON_TIE_ISOLATION", "d.unqualified_reason is not None")
def oracle_the_count_of_windows_blanked_by_the_rule_per_class(mods):
    rep = mods.ws.near_station_tie_report({"major_loss": _drafts(2, 3, 5), "marriage": _drafts(1, 0, 9)})
    assert rep["near_station_tie_blanked"] == 3 and rep["windows"] == 20, rep               # only the rule's own blanks: the 3 budget blanks are not counted
    assert rep["per_class"] == {"major_loss": {"windows": 10, "blanked": 2}, "marriage": {"windows": 10, "blanked": 1}}
    assert rep["schema"] == "near_station_tie_blanked/1" and rep["rule"] == "SR-NEAR-STATION-TIE"


@claim("NST-7", "sweep", '"cap_exceeded": blanked * 1000 > windows * NEAR_STATION_TIE_CAP_PER_MILLE', '"cap_exceeded": blanked * 1000 >= windows * NEAR_STATION_TIE_CAP_PER_MILLE')
def oracle_the_cap_is_half_a_percent_in_integers(mods):
    at_cap = mods.ws.near_station_tie_report({"k": _drafts(5, 0, 995)})                 # exactly 0.5 %: not above it
    over = mods.ws.near_station_tie_report({"k": _drafts(6, 0, 994)})
    assert (at_cap["cap_exceeded"], over["cap_exceeded"], at_cap["cap_per_mille"]) == (False, True, 5), (at_cap, over)


@claim("NST-8", "checker", "            return self._isolation(top, sorted(t for t, f in cands if f >= top - TIE))\n", "            return None\n")
def oracle_the_verifier_side_confirmation_of_a_stored_blank(mods):
    c, iso = tie_case(), isolated_case()
    kw = dict(objective=mods.chk.OBJ_SUM, position_at=_lon_dt, max_evals=300_000)
    why = mods.chk.confirm_tie_isolation(lo=c.lo, hi=c.hi, records=[_record(mods.chk, c)], **kw)
    assert why is not None and "SR-NEAR-STATION-TIE" in why, why                           # the blank is confirmed by the prover's OWN derivation …
    assert mods.chk.confirm_tie_isolation(lo=iso.lo, hi=iso.hi, records=[_record(mods.chk, iso)], **kw) is None       # … and a window with an isolated maximum is not


# the end-to-end P4 world (analytic, the S3 harness'): Jupiter and Saturn both reach the target (activity 1.0) on day 5, where Saturn turns round — its Swiss
# station; the min-activity peak (1.0) is AT the station. `end` days: the window ends 10 s after the station (station inside) or 50 s before it (just outside).
def _turning5(t):
    return (100.0 + 0.05 * (_days(t) - 5.0) ** 2) % 360.0


def _p4_station_world(end_s_from_station: float):
    span = (0.0, 5.0 + end_s_from_station / DAY)
    st = _d(5.0)
    return [_rec("J", path="P4", agent="jupiter", root="RJ", supports=(span,), relation="conjunction", kind="degree_point", longitude_at=_jup),
            _rec("S", path="P4", agent="saturn", root="RS", supports=(span,), relation="conjunction", kind="degree_point", longitude_at=_turning5,
                 station_instants=lambda st=st: [st])]


@claim("NST-9", "verifier", "                if reason == SOLVER_TIE_ZONE_REASON:\n", "                if False:\n")
def oracle_end_to_end_the_verifier_confirms_the_stored_blank(mods):
    recs = _p4_station_world(10.0)
    (draft,) = mods.ws.draft_windows("marriage", recs, ROWS, solver=mods.ws.PRODUCTION_SOLVER)[0]
    assert (draft.peak_instant, draft.unqualified_reason) == (None, REASON), (draft.peak_instant, draft.unqualified_reason)
    conn = _Conn([_stored(draft, "w0")], _member_rows(recs), [(r.record_id, r.canonical_target) for r in recs])
    report = mods.wv.verify_window_semantics(conn, factor_rows=ROWS("P4", "1.0.0"), policy=mods.wv.POLICY_VERSION,
                                             position_at=_position({"jupiter": _jup, "saturn": _turning5}), **GRAIN_P4)
    assert report["status"] == "VERIFIED" and report["solver_blank_windows"] == {REASON: 1}, report


@claim("NST-10", "sweep", "                                                                        if -_solver.NEAR_STATION_S <= (t - origin).total_seconds() <= L + _solver.NEAR_STATION_S))",
       "                                                                        if 0.0 < (t - origin).total_seconds() < L))")
def oracle_end_to_end_a_station_just_outside_the_window_still_marks_the_zone(mods):
    recs = _p4_station_world(-50.0)                                                        # the window ends 50 s BEFORE Saturn's station
    (draft,) = mods.ws.draft_windows("marriage", recs, ROWS, solver=mods.ws.PRODUCTION_SOLVER)[0]
    assert (draft.peak_instant, draft.unqualified_reason) == (None, REASON), (draft.peak_instant, draft.unqualified_reason)


# ── the ruling is applied LITERALLY (review F-1 against od1-plateau-tie): a zone blanks only a tie set that lies INSIDE it ─────────────────────────────────────
# SR-NEAR-STATION-TIE (DECISIONS_SURROGATE madhav-44): "When a window tie set (>=2 maxima within TIE of the top) lies inside a <=120 s station zone and the tied
# maxima differ from the top by no more than the S0 near-station noise bound, the builder blanks". The 7 parental_event P4 / 3 property_acquisition P4 windows
# the zone test over-blanked have max-min F == 1.0 over the WHOLE window (each agent held at 1.0 by a constant residence step), one maximum from the window start,
# no comb: the tie set is not inside the zone. Closed-form worlds (no sky): a Jupiter tent whose station sits S s into a window of L s, beside two constant steps.
PL_S, PL_L = 500_000.0, 2_000_000.0
PL_K = 1e-7                                  # the offset's curvature: deg/s^2 (velocity 0 at the station)


@claim("NST-11", "builder", "        if zone_top >= top - TIE - noise and all(lo <= t <= hi for t in ties):\n", "        if zone_top >= top - TIE - noise:\n")
def oracle_a_plateau_window_whose_tie_set_is_not_inside_the_zone_numbers(mods):
    m = mods.sol
    tent = m.Tent(offset=lambda t: PL_K * (t - PL_S) ** 2 + 0.3, orb=1.0, velocity=lambda t: 2 * PL_K * (t - PL_S), stations=(PL_S,), min_station_spacing=1e9)
    members = (m.Member(key="jup_res", group="jupiter", supports=((0.0, PL_L),), steps=(m.constant_step(1.0),)),
               m.Member(key="jup_tent", group="jupiter", supports=((0.0, PL_L),), tent=tent),
               m.Member(key="sat_res", group="saturn", supports=((0.0, PL_L),), steps=(m.constant_step(1.0),)))
    res = m.solve(m.Problem(lo=0.0, hi=PL_L, objective=m.OBJECTIVE_MINMAX, members=members))
    assert (res.status, res.value, res.instant) == (m.SOLVED, 1.0, 0.0), (res.status, res.reason, res.value, res.instant)


@claim("NST-12", "checker", "            if zone_top is not None and zone_top >= m_hat - TIE - noise and all(lo <= t <= hi for t in ties):\n",
       "            if zone_top is not None and zone_top >= m_hat - TIE - noise:\n")
def oracle_the_checker_verifies_the_plateau_window_it_must_not_blank(mods):
    k = mods.chk
    t0 = datetime(2030, 1, 1, tzinfo=UTC)
    pos = lambda body, d: ((100.0 + PL_K * ((d - t0).total_seconds() - PL_S) ** 2) if body == "J" else 200.0) % 360.0               # noqa: E731
    lo, hi = t0, t0 + timedelta(seconds=PL_L)
    recs = [k.CheckRecord("jr", "Rj", "jupiter", ((lo, hi),)),                                   # the Jupiter residence step, 1.0 over the window
            k.CheckRecord("jt", "Rt", "jupiter", ((lo, t0 + timedelta(seconds=PL_S + 10.0)),), tent=k.TentFactor("J", 100.3, 5.0)),   # its tent ends 10 s past the station
            k.CheckRecord("sr", "Rs", "saturn", ((lo, hi),))]                                    # the Saturn residence step
    rep = k.check_window(lo=lo, hi=hi, records=recs, objective=k.OBJ_MAXMIN, position_at=pos, stored=k.StoredWindow(lo, 1.0), max_evals=300_000)
    assert rep.status == k.VERIFIED and not rep.unverified, (rep.status, rep.codes())


# ═══════════════════════════════ the harness ═══════════════════════════════════════════════════════════════════════════════════════════

_COUNT = [0]


def reverted_module(target: str, old: str, new: str):
    """`target`'s source with exactly ONE occurrence of `old` replaced by `new`, loaded as a throw-away module of the kernel package."""
    src = SRC[target]
    assert old != new and src.count(old) == 1, f"the planted reversion must match exactly once, matched {src.count(old)}x: {old[:70]!r}"
    _COUNT[0] += 1
    name = f"services.gochara_kernel._reverted_nst_{target}_{_COUNT[0]}"
    mod = types.ModuleType(name)
    mod.__file__, mod.__package__ = name, "services.gochara_kernel"
    sys.modules[name] = mod                                           # dataclasses resolve their annotations through sys.modules
    try:
        exec(compile(src.replace(old, new), name, "exec"), mod.__dict__)
    finally:
        sys.modules.pop(name, None)
    return mod


def _mods(**replaced):
    return SimpleNamespace(**{**REAL, **replaced})


ALL_CASES = [pytest.param(cid, marks=requires_swieph if cid in REAL_SKY else (), id=cid) for cid in sorted(CLAIMS, key=lambda s: int(s.split("-")[1]))]


@pytest.mark.parametrize("cid", ALL_CASES)
def test_oracle_passes_on_the_real_code(cid):
    CLAIMS[cid][0](_mods())


@pytest.mark.parametrize("cid", ALL_CASES)
def test_the_single_planted_reversion_fails_the_oracle(cid):
    oracle, target, old, new = CLAIMS[cid]
    reverted = reverted_module(target, old, new)          # built OUTSIDE the raises-block: a reversion that no longer matches is an ERROR, not a pass
    with pytest.raises((AssertionError, RuntimeError)):
        oracle(_mods(**{{"builder": "sol", "checker": "chk", "sweep": "ws", "verifier": "wv"}[target]: reverted}))


def test_every_claim_has_exactly_one_reversion_and_one_oracle():
    assert set(CLAIMS) == {f"NST-{i}" for i in range(1, 13)}
    assert len({(t, old, new) for _, t, old, new in CLAIMS.values()}) == len(CLAIMS)           # no two claims share a reversion


@requires_swieph
def test_planting_the_removal_of_the_checker_zone_rule_brings_earlier_tie_not_taken_back():
    """The measured failure (case 3), restored by the planted removal: the checker REFUTES the legacy number by the earlier distinct extremum it finds."""
    _oracle, target, old, new = CLAIMS["NST-2"]
    k = reverted_module(target, old, new)
    c = tie_case()
    rep = _check(k, c, c.hi - timedelta(microseconds=1), 1.0)
    assert rep.status == k.REFUTED and k.F_EARLIER_TIE in rep.codes(), (rep.status, rep.codes())


# B-1 (review X-20261022T175406Z-review-lane-pt): the zone rule must not relax Q12. Owner decision SOLVER-TOLERANCES Q12(a): the peak instant is exact to the
# second. A stored instant OUTSIDE every station zone (+-tol_s) and within tol_s of no qualifying extremum is REFUTED peak_instant_mismatch (as at the base
# e6be81efb), not demoted to the named blank. Case 3 (Venus 2029-12-16), instant 200.003 s before the window end (the zone is the last 120 s + noise), with the
# objective read there (2.2e-8 below the top: inside the float4 value tolerance, 22 x TIE from a tie).
_B1_OLD = '"tie_zone" in self.rederived and not in_zone and'


def _b1_check(k):
    c = tie_case()
    t = c.hi - timedelta(seconds=200.003)
    v = 1.0 - abs(_wrap180(_lon_dt(c.body, t) - c.level)) / ORB
    assert v < 1.0 - 1e-8                                                                 # not a tie of the maximum
    rep = _check(k, c, t, v)
    assert rep.status == k.REFUTED and k.F_INSTANT in rep.codes(), (rep.status, rep.codes())


@requires_swieph
def test_b1_instant_outside_every_zone_at_no_extremum_is_still_refuted_peak_instant_mismatch():
    _b1_check(chk)


@requires_swieph
def test_b1_planting_the_removal_of_the_outside_the_zone_refutation_fails_the_oracle():
    k = reverted_module("checker", _B1_OLD, "False and")
    with pytest.raises(AssertionError):
        _b1_check(k)


# the six windows of the 2026-10-22 diagnosis (3 Venus, 3 Mercury): (body, scan from, side, level short by, the number the LEGACY builder stored — seconds from the
# window start, value). They are inputs (a stored number the checker meets), not expected outputs: the expected outcome is the ruling's — the named blank.
SIX = [("Venus", datetime(2031, 1, 1, tzinfo=UTC), "start_before", 1e-9, 21.11234035954414, 0.9999999999999375),
       ("Venus", datetime(2029, 9, 1, tzinfo=UTC), "end_after", 1e-9, 172778.93651437596, 1.0),
       ("Venus", datetime(2029, 9, 1, tzinfo=UTC), "end_after", 0.0, 172799.999999, 1.0),
       ("Mercury", datetime(2029, 1, 1, tzinfo=UTC), "end_after", 0.0, 172799.999999, 1.0),
       ("Mercury", datetime(2029, 5, 1, tzinfo=UTC), "end_after", 0.0, 172799.999999, 1.0),
       ("Mercury", datetime(2029, 5, 1, tzinfo=UTC), "start_before", 1e-9, 15.912816315252098, 0.9999999999999659)]


@requires_swieph
@pytest.mark.parametrize("body,scan,side,short,legacy_s,legacy_v", SIX, ids=[f"{b}-{sd}-{sh:g}-{i}" for i, (b, _s, sd, sh, _t, _v) in enumerate(SIX)])
def test_the_six_measured_windows_are_the_same_named_blank_on_both_sides(body, scan, side, short, legacy_s, legacy_v):
    c = _case(body, scan, side, short)
    res = sol.solve(_problem(sol, c))
    assert (res.status, res.reason) == (sol.BLANK, REASON), (res.status, res.reason)                  # the builder: the named blank
    rep = _check(chk, c, c.lo + timedelta(seconds=legacy_s), legacy_v)                                 # the checker, on the legacy number: the SAME name, not a refutation
    assert rep.status == chk.UNVERIFIED and rep.codes() == [REASON], (rep.status, rep.codes())


# ═══════════════════════════════ guards (no reversion: a property of the modules) ═════════════════════════════════════════════════════════

def _imports(source: str) -> list:
    out = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = ("." * node.level) + (node.module or "")
            out += [base] + [f"{base}.{a.name}" for a in node.names]
    return out


def _imports_leaf(source: str, leaf: str) -> bool:
    """Does `source` import a module whose last dotted component is `leaf`?"""
    return any(n.rstrip(".").split(".")[-1] == leaf for n in _imports(source))


def test_k12_the_checker_imports_nothing_of_the_builder_and_the_builder_nothing_of_the_checker():
    assert not _imports_leaf(SRC["checker"], "window_solver")
    assert not _imports_leaf(SRC["builder"], "window_solver_check")


def test_the_k12_detector_reads_false_on_a_planted_import():
    for planted in ("from . import window_solver", "from .window_solver import NEAR_STATION_S", "import services.gochara_kernel.window_solver"):
        assert _imports_leaf(SRC["checker"] + "\n" + planted + "\n", "window_solver"), planted
    for planted in ("from . import window_solver_check", "from .window_solver_check import NEAR_END_S", "import services.gochara_kernel.window_solver_check"):
        assert _imports_leaf(SRC["builder"] + "\n" + planted + "\n", "window_solver_check"), planted


def test_each_side_keeps_its_own_literal_noise_bound_and_the_two_are_equal():
    assert "NEAR_STATION_NOISE_DEG = 3.9e-9\n" in SRC["builder"] and "NEAR_END_NOISE_DEG = 3.9e-9 " in SRC["checker"]
    assert sol.NEAR_STATION_NOISE_DEG == chk.NEAR_END_NOISE_DEG == 3.9e-9                                # S0 K-2: the measured non-monotonicity next to a station
    assert "def _station_zone_tie(" in SRC["builder"] and "def _zone_tie(" in SRC["checker"]            # each side: its own function, in its own file


def test_the_blank_has_one_name_everywhere_and_it_is_inconclusive_at_the_gate():
    assert sol.REASON_TIE_ISOLATION == chk.U_ISOLATION == REASON
    assert REASON in wcc.INCONCLUSIVE_REASONS and REASON in nwg.INCONCLUSIVE_REASONS                   # demoted, counted toward the 0.5 % cap
    assert nwg.reason_group(REASON) == nwg.SOLVER_CERTIFICATE
