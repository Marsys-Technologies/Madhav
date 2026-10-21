"""SR-OD1 S2 — `window_solver_check`: the independent prover of the window solver's numbers (plan §2.4), and its planted-reversion suite.

The checker is written from the written spec only (plan §2.1-2.4, S0_REPORT §2.2) and imports nothing from the builder; these tests
therefore state each claim against an ANALYTIC world (a stub ephemeris with a closed-form answer) or the frozen kernel's own arithmetic,
never against the builder's output and never by capturing what the checker currently prints.

How a claim is tested. Each claim has ONE oracle `oracle(m)` that takes the module under test and asserts what the claim says; and ONE
planted reversion `(old, new)` — a single textual change to the checker's source. `test_oracle_passes_on_the_real_checker` runs every oracle
on the real module; `test_the_single_planted_reversion_fails_the_oracle` loads a COPY of the source with that one change (exactly one
occurrence of `old`, so a reversion can never silently stop matching) and requires the SAME oracle to fail on it. A claim whose reversion
does not fail its oracle is a claim nothing measures (CLAUDE.md §N.8).

Claims (doctrine / analytic source in each oracle's docstring; D-OWNER-TESTS-20261016):

  V-1  the objective at the stored peak is the stored value            S-2  interior maxima are not missed (endpoint-only is forbidden)
  S-3  the maximum is global, not the first hump                       S-4  earliest among exact ties
  S-5  the tie rule is between distinct extrema, never a shoulder      S-6  the peak instant is exact to the second (Q12 a), not trusted
  S-7  the bound is rigorous on a falling term                         S-8  P4 is max-min, not a sum
  S-9  a one-piece step island is found (steps are exact)             S-10 step boundaries not asserted complete => not certified (H2)
  S-11 a change the listed boundaries omit is found (H2)              S-12 a station inside a support => not certified (H1)
  S-13 a Swiss station within seconds of a support end is a cut (S0 K-2)  S-14 budget exhaustion => UNVERIFIED, never a pass
  S-15 the bound threshold is the stated 1e-7 (differential vs brute force over 500 random analytic worlds)
  S-16 evidence_for at the peak is the per-root SUM                   S-17 evidence_against is NULL while a live unqualified member could feed it
  S-18 the valence is the rule authority's, from the evidence         S-19 the score is the max over ALL live members, any channel
  S-20 a per-instant channel flip is a cut                            S-21 an unqualified for-channel member => not a number
  S-22 an undeterminable operand is an honest null, never a default   S-23 the tent is the frozen kernel's arithmetic (D-RQ2, differential)
  S-24 two fixed points close together give an exact plateau, proved without search (one body ⇒ convex in its longitude)
  S-25 the max-min objective exists only where both agents are live   S-26 the +-2e-10 grey band around the 1e-9 tie threshold
  S-27 a kinked crest narrower than a sample is located and proved   S-28 ties are read off the re-derived maximum, not the stored peak's value
  S-29 tied extrema closer than ISOLATION_S => `tie_isolation_unresolved` (INCONCLUSIVE; R-3), neither a pass nor a refutation
  S-30 a close extremum that is NOT within the tie tolerance does not blank the window    S-31 tied extrema farther apart than ISOLATION_S are still decided
plus guards without a reversion: independence of the module (an AST detector that is itself shown to read false on a planted import),
the H1 sampling premise, and the S0-measured constants.
"""
from __future__ import annotations

import ast
import math
import random
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import window_solver_check as chk

from .conftest import EPHE_PATH, assert_real_ephemeris, requires_swieph

SRC = Path(chk.__file__).read_text()
T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)
FOR, AGAINST = chk.CH_FOR, chk.CH_AGAINST


def at(days: float = 0.0, seconds: float = 0.0) -> datetime:
    return T0 + timedelta(days=days, seconds=seconds)


def sky(**fns):
    """An analytic ephemeris: each body is a function of DAYS since T0 (degrees)."""
    def pos(body, d):
        return fns[body]((d - T0).total_seconds() / 86400.0) % 360.0
    return pos


def sky_s(**fns):
    """The same, as a function of SECONDS since T0."""
    def pos(body, d):
        return fns[body]((d - T0).total_seconds()) % 360.0
    return pos


def no_sky(body, d):
    raise AssertionError("a constants-only world must not touch the ephemeris")


def run(m, world, stored, **kw):
    # a bounded budget: every real-checker world here needs < 5e4 evaluations; a reverted checker that wanders is cut off (UNVERIFIED)
    args = dict(lo=world["lo"], hi=world["hi"], records=world["records"], objective=world.get("objective", m.OBJ_SUM),
                position_at=world["pos"], stored=stored, max_evals=300_000)
    args.update(kw)
    return m.check_window(**args)


def stored(m, days_or_dt, value, **kw):
    when = days_or_dt if isinstance(days_or_dt, datetime) else at(days_or_dt)
    return m.StoredWindow(when, value, **kw)


# ── analytic worlds ──────────────────────────────────────────────────────────────────────────────────────────────────────

def _tent(lon, level, orb):
    return max(0.0, 1.0 - abs((lon - level + 180.0) % 360.0 - 180.0) / orb)


def w_interior(m, days):
    """Two roots. A rises 1 deg/d toward its level 102 (orb 2.5): fa = 0.2 + 0.4 t. B falls and accelerates away from its level 201.5
    (orb 3): fb = 0.5 - t/6 - 0.4 t^2/3 (until its orb exit, t = 1.41 d). F = fa + fb = 0.7 + (0.4 - 1/6) t - 0.4 t^2/3 — a SMOOTH
    interior maximum at t* = (0.4 - 1/6) * 3 / 0.8 = 0.875 d, F* = 0.80208333."""
    pos = sky(A=lambda t: 100.0 + t, B=lambda t: 200.0 - 0.5 * t - 0.4 * t * t)
    sup = ((at(0), at(days)),)
    recs = [m.CheckRecord("a", "ra", "A", sup, tent=m.TentFactor("A", 102.0, 2.5)),
            m.CheckRecord("b", "rb", "B", sup, tent=m.TentFactor("B", 201.5, 3.0))]
    return {"lo": at(0), "hi": at(days), "records": recs, "pos": pos}


def F_interior(t):
    return _tent(100.0 + t, 102.0, 2.5) + _tent(200.0 - 0.5 * t - 0.4 * t * t, 201.5, 3.0)


T_INT = (0.4 - 1.0 / 6.0) * 3.0 / 0.8
M_INT = 0.7 + (0.4 - 1.0 / 6.0) * T_INT - 0.4 * T_INT * T_INT / 3.0


def w_humps(m, a_const, b_const):
    """Two disjoint humps on the same linear body (100 + t): A on [0, 0.5) peaks at t = 0.25 with value a_const, B on [0.5, 1) peaks at
    t = 0.75 with value b_const (a record's value = constant x tent, tent 1 at its crest)."""
    pos = sky(A=lambda t: 100.0 + t)
    recs = [m.CheckRecord("a", "ra", "A", ((at(0), at(0.5)),), constant=a_const, tent=m.TentFactor("A", 100.25, 1.0)),
            m.CheckRecord("b", "rb", "A", ((at(0.5), at(1)),), constant=b_const, tent=m.TentFactor("A", 100.75, 1.0))]
    return {"lo": at(0), "hi": at(1), "records": recs, "pos": pos}


def w_island(m, *, complete=True, listed=("both",)):
    """A constant record whose step factor is 0.5 except on the island [0.4 d, 0.45 d), where it is 1.0."""
    island = lambda d: 1.0 if at(0.4) <= d < at(0.45) else 0.5                       # noqa: E731
    bounds = {"both": [at(0.4), at(0.45)], "start_only": [at(0.4)]}[listed[0]]
    step = m.StepFactor(island, lambda lo, hi: [b for b in bounds if lo < b < hi], complete)
    return {"lo": at(0), "hi": at(1), "pos": no_sky,
            "records": [m.CheckRecord("r", "rt", "Sun", ((at(0), at(1)),), steps=(step,))]}


DELTA = 0.0234567                                  # moves the crossing off every multiple of the checker's sampling step


def w_p4(m, delta=DELTA):
    """Jupiter rises through its level (101.5, orb 1.5): fJ = t/1.5 for t < 1.5; Saturn falls through 199 + delta (orb 1.0): fS = 2 - delta - t for
    t > 1 - delta. min(fJ, fS) peaks where they cross, t* = 1.2 - 0.6 delta d, value t*/1.5 (a KINK, narrower than any sample, and NOT at the
    midpoint of the two crests); their SUM there is twice that."""
    pos = sky(J=lambda t: 100.0 + t, S=lambda t: 200.0 - t)
    sup = ((at(0), at(2)),)
    recs = [m.CheckRecord("j", "RJ", "jupiter", sup, tent=m.TentFactor("J", 101.5, 1.5)),
            m.CheckRecord("s", "RS", "saturn", sup, tent=m.TentFactor("S", 199.0 + delta, 1.0))]
    return {"lo": at(0), "hi": at(2), "records": recs, "pos": pos, "objective": m.OBJ_MAXMIN}


T_P4 = 1.2 - 0.6 * DELTA
M_P4 = T_P4 / 1.5


def w_station(m, ts_s, end_s):
    """A body that rises until the station `ts_s` seconds after T0 and then falls: lon = 100 - 0.5e-6 (s - ts_s)^2 (a double root of its
    tent at level 100, orb 1). The support/window is [0, end_s] seconds."""
    pos = sky_s(A=lambda s: 100.0 - 0.5e-6 * (s - ts_s) ** 2)
    sup = ((at(0), at(0, end_s)),)
    return {"lo": at(0), "hi": at(0, end_s), "records": [m.CheckRecord("a", "ra", "A", sup, tent=m.TentFactor("A", 100.0, 1.0))],
            "pos": pos}


def codes(report) -> list:
    return report.codes()


# ═══════════════════════════════ the claims: ONE oracle and ONE planted reversion each ═══════════════════════════════════════

CLAIMS: dict = {}


def claim(cid: str, old: str, new: str):
    def deco(fn):
        CLAIMS[cid] = (fn, old, new)
        return fn
    return deco


@claim("V-1", "if f_star is None or abs(f_star - st.objective_value) > VALUE_TOL:", "if f_star is None:")
def oracle_value_at_peak(m):
    """The objective at the stored peak must be the stored value (plan §2.4 item 1; the float4 storage round-trip 1e-6)."""
    w = w_interior(m, 1.0)
    assert run(m, w, stored(m, T_INT, M_INT)).status == m.VERIFIED
    bad = run(m, w, stored(m, T_INT, M_INT + 1e-3))
    assert bad.status == m.REFUTED and chk.F_VALUE in codes(bad)


@claim("S-2", "pc.pure = (not (up and down)) or convex", "pc.pure = True")
def oracle_interior_maximum(m):
    """Spec §7.2 inv 2 / O-SM-4: scores keeping a functional form are solved for INTERIOR extrema; endpoint-only evaluation is forbidden.
    The smooth maximum of the analytic world (closed form above) lies above both end values; the value an endpoint-only solver stores is
    refuted, the interior maximum is proved."""
    w = w_interior(m, 1.5)
    end = at(1.5, -1e-6)
    f_end = F_interior(1.5 - 1e-6 / 86400.0)
    assert f_end < M_INT - 1e-3 and F_interior(0.0) < M_INT - 1e-3               # the world: both ends below the interior maximum
    endpoint_only = run(m, w, stored(m, end, f_end))
    assert endpoint_only.status == m.REFUTED and chk.F_ABOVE in codes(endpoint_only)
    assert run(m, w, stored(m, T_INT, M_INT)).status == m.VERIFIED


@claim("S-3", "                continue\n            for t, f in ((pc.l, pc.F_l), (pc.r - US, pc.F_r)):",
       "                return\n            for t, f in ((pc.l, pc.F_l), (pc.r - US, pc.F_r)):")
def oracle_global_not_first_hump(m):
    """The maximum is the GLOBAL one: two disjoint humps (0.6 at t = 0.25 d, then 1.0 at t = 0.75 d) — a value taken from the first hump
    is refuted, the later, higher hump is proved."""
    w = w_humps(m, 0.6, 1.0)
    first = run(m, w, stored(m, 0.25, 0.6))
    assert first.status == m.REFUTED and chk.F_ABOVE in codes(first)
    assert run(m, w, stored(m, 0.75, 1.0)).status == m.VERIFIED


@claim("S-4", "if t_star > t_hi + self.tol_s:", "if False:")
def oracle_earliest_among_ties(m):
    """Spec §7.2 inv 2 plateau rule: exact ties take the EARLIEST instant. Two humps both exactly 1.0 (t = 0.25 d and 0.75 d): the later one
    is refuted as 'an earlier tie exists', the earlier one is proved."""
    w = w_humps(m, 1.0, 1.0)
    late = run(m, w, stored(m, 0.75, 1.0))
    assert late.status == m.REFUTED and chk.F_EARLIER_TIE in codes(late)
    assert run(m, w, stored(m, 0.25, 1.0)).status == m.VERIFIED


@claim("S-5", "and cur[4] and f < cur[0]:", "and cur[4]:")
def oracle_tie_is_between_extrema(m):
    """N-11: the 1e-9 tie rule is between DISTINCT local extrema; on one smooth hump the peak is the CREST, not the first instant within
    1e-9 of it. F = M - 0.1333 (t - 0.875)^2 per d^2, so the shoulder (F >= M - 1e-9) starts about 7.5 s before the crest."""
    w = w_interior(m, 1.0)
    assert run(m, w, stored(m, T_INT, M_INT)).status == m.VERIFIED
    shoulder_s = math.sqrt(1e-9 / (0.4 / 3.0)) * 86400.0
    assert 3.0 < shoulder_s < 20.0
    t_sh = T_INT - shoulder_s / 86400.0
    shoulder = run(m, w, stored(m, t_sh, F_interior(t_sh)))
    assert shoulder.status == m.REFUTED and chk.F_INSTANT in codes(shoulder)


@claim("S-6", "PEAK_INSTANT_TOLERANCE_S = 1.0 ", "PEAK_INSTANT_TOLERANCE_S = 3600.0 ")
def oracle_peak_exact_to_the_second(m):
    """Owner decision SOLVER-TOLERANCES (Q12 a): the strongest moment is exact to the SECOND. A stored crest 0.5 s late is accepted; one 30 s
    late (whose objective value differs by 1.6e-8, invisible to the value and bound checks) is refuted."""
    w = w_interior(m, 1.0)
    ok = T_INT + 0.5 / 86400.0
    assert run(m, w, stored(m, ok, F_interior(ok))).status == m.VERIFIED
    late = T_INT + 30.0 / 86400.0
    bad = run(m, w, stored(m, late, F_interior(late)))
    assert bad.status == m.REFUTED and chk.F_INSTANT in codes(bad)


@claim("S-7", "total += max(sum(max(v1[i] for i in g) for g in groups), sum(max(v2[i] for i in g) for g in groups))",
       "total += sum(max(v2[i] for i in g) for g in groups)")
def oracle_bound_on_falling_term(m):
    """The first-order enclosure is rigorous on a FALLING term: one tent already past its crest, 1 - t on [0, 1): the supremum is at the
    left end. A stored value taken at t = 0.5 is refuted, the left-end value is proved."""
    pos = sky(A=lambda t: 100.0 + t)
    w = {"lo": at(0), "hi": at(1), "pos": pos,
         "records": [m.CheckRecord("a", "ra", "A", ((at(0), at(1)),), tent=m.TentFactor("A", 100.0, 1.0))]}
    low = run(m, w, stored(m, 0.5, 0.5))
    assert low.status == m.REFUTED and chk.F_ABOVE in codes(low)
    assert run(m, w, stored(m, 0.0, 1.0)).status == m.VERIFIED


@claim("S-8", "return min(max(vals[i] for i in g) for g in pc.groups)", "return sum(max(vals[i] for i in g) for g in pc.groups)")
def oracle_p4_is_max_min(m):
    """Plan §2.1 / spec O-RP-3 (R3-S02) / Phaladipika XVII.12 (the joint Jupiter-Saturn transit, D-P4): P4's objective is the MAX-MIN of the
    two agents' activity — peak at the crossing, value t*/1.5; the SUM of the same activities (twice that) is not the stored value."""
    w = w_p4(m)
    assert run(m, w, stored(m, T_P4, M_P4)).status == m.VERIFIED
    summed = run(m, w, stored(m, T_P4, 2 * M_P4))
    assert summed.status == m.REFUTED and chk.F_VALUE in codes(summed)


@claim("S-27", "got = self._locate(cur, pt)\n                if got[1] >= theta:", "got = self._locate(cur, pt)\n                if cur[0] >= theta:")
def oracle_a_crest_narrower_than_a_sample(m):
    """The extremum enumeration samples F every 0.0864 s, but the max-min crest is a kink whose top (F within 1e-9 of the maximum) is ~4e-5 s
    wide: a sampled peak is only a CANDIDATE, the located crest must itself reach the tie threshold. The off-grid kink is proved, and the same
    crest stored 0.4 s late (inside the second) is too."""
    w = w_p4(m)
    assert run(m, w, stored(m, T_P4, M_P4)).status == m.VERIFIED
    near = at(T_P4, 0.05)                                           # the kink loses <= 1.2e-5 per second: 0.05 s keeps the value inside 1e-6
    assert run(m, w, stored(m, near, M_P4)).status == m.VERIFIED


@claim("S-28", "m_hat = max(f for _, f in cands)", "m_hat = f_star")
def oracle_ties_are_read_off_the_rederived_maximum(m):
    """The stored value is a float4 and the stored peak may sit up to a second from the crest (a kinked crest loses ~1e-5 per second), so the
    tie threshold is taken from the RE-DERIVED maximum, not from the value at the stored instant. An earlier hump 5e-9 below the maximum is
    NOT a tie (the frozen tolerance is 1e-9); the later maximum, stored 0.05 s off its crest, is proved."""
    w = w_humps(m, 1.0 - 5e-9, 1.0)
    assert run(m, w, stored(m, at(0.75, 0.05), 1.0)).status == m.VERIFIED


@claim("S-26", "GREY = 2e-10 ", "GREY = 0.0 ")
def oracle_grey_band(m):
    """Plan §2.4 item 3 / interpretation I-2: an earlier hump AT the 1e-9 tie boundary (here 9e-10 below the maximum — float-ambiguous, inside
    the +-2e-10 grey band) does not make the later maximum a refutation; one clearly inside the tie (5e-10 below) does; one clearly outside
    (1.1e-9 below) is no tie. Two humps on [0, 0.5) and [0.5, 1): the later one is the exact 1.0."""
    assert run(m, w_humps(m, 1.0 - 9e-10, 1.0), stored(m, 0.75, 1.0)).status == m.VERIFIED
    inside = run(m, w_humps(m, 1.0 - 5e-10, 1.0), stored(m, 0.75, 1.0))
    assert inside.status == m.REFUTED and chk.F_EARLIER_TIE in codes(inside)
    assert run(m, w_humps(m, 1.0 - 1.1e-9, 1.0), stored(m, 0.75, 1.0)).status == m.VERIFIED


def w_close(m, gap_s, b_const=1.0):
    """Two distinct crests of ONE root `gap_s` seconds apart on a fast body (lon = 100 + 0.01 s): record a (tent level 100.10, orb 0.05) crests at
    s = 10 over its support [0, 10 + gap/2), record b (level 100 + 0.01 (10 + gap)) crests at s = 10 + gap over [10 + gap/2, 30 + gap) at height
    `b_const`. Per-root max: F peaks at 1.0 twice with a dip to 0.8 (gap 2) between them — two distinct local maxima, tied when b_const = 1."""
    pos = sky_s(A=lambda s: 100.0 + 0.01 * s)
    split, end = 10.0 + gap_s / 2.0, 30.0 + gap_s
    recs = [m.CheckRecord("a", "R", "A", ((at(0), at(0, split)),), tent=m.TentFactor("A", 100.10, 0.05)),
            m.CheckRecord("b", "R", "A", ((at(0, split), at(0, end)),), constant=b_const,
                          tent=m.TentFactor("A", 100.0 + 0.01 * (10.0 + gap_s), 0.05))]
    return {"lo": at(0), "hi": at(0, end), "records": recs, "pos": pos}


@claim("S-29", "if y - x <= ISOLATION_S]", "if False]")
def oracle_close_ties_are_not_isolated(m):
    """SR-PLAN-REVIEW-RECONCILED R-3 (GPT B4 / window_solver H5): two distinct maxima, both exactly 1.0, 2 s apart (inside ISOLATION_S = 2 x the
    builder's LEAF, <= 4 s): the earliest distinct one is not something either side's sampling scale can certify, so the window is the named
    INCONCLUSIVE blank `tie_isolation_unresolved` — whichever of the two the stored peak sits at, and never a REFUTED `earlier_tie_not_taken`
    for the later one (that would be a verdict the enumeration cannot back)."""
    w = w_close(m, 2.0)
    for when in (10.0, 12.0):
        rep = run(m, w, stored(m, at(0, when), 1.0))
        assert rep.status == m.UNVERIFIED and chk.U_ISOLATION in codes(rep) and not rep.findings, (when, rep.status, codes(rep))
    assert len(rep.rederived["tie_cluster"]) == 1


@claim("S-30", "ties = sorted(t for t, f in cands if f >= theta)", "ties = sorted(t for t, f in cands)")
def oracle_a_close_non_tie_does_not_blank(m):
    """The frozen tie tolerance is 1e-9 (N-11, window_sweep._TIE): a second crest 2 s away but 1.1e-9 BELOW the maximum is no tie, so the
    window is decided as before — the earlier, higher crest is proved, and the same peak stored at the lower later crest is refuted."""
    w = w_close(m, 2.0, b_const=1.0 - 1.1e-9)
    rep = run(m, w, stored(m, at(0, 10.0), 1.0))
    assert rep.status == m.VERIFIED, (rep.status, codes(rep))
    assert chk.U_ISOLATION not in codes(rep)


@claim("S-31", "ISOLATION_S = 4.0 ", "ISOLATION_S = 1e9 ")
def oracle_separated_ties_are_still_decided(m):
    """The detector is a proximity test, not a blanket blank: two exact ties 20 s apart (farther than ISOLATION_S) keep the frozen rule — the
    earliest is proved, the later one refuted as `earlier_tie_not_taken`."""
    w = w_close(m, 20.0)
    assert run(m, w, stored(m, at(0, 10.0), 1.0)).status == m.VERIFIED
    late = run(m, w, stored(m, at(0, 30.0), 1.0))
    assert late.status == m.REFUTED and chk.F_EARLIER_TIE in codes(late) and chk.U_ISOLATION not in codes(late)


@claim("S-9", "cuts.update(c for c in (self._sec(x) for x in st.boundaries(self._dt(a), self._dt(b))) if a < c < b)", "pass")
def oracle_step_island(m):
    """Steps are exact: a one-piece island [0.4 d, 0.45 d) of value 1.0 inside a value-0.5 record is the maximum (earliest instant 0.4 d); a
    value of 0.5 that missed the island is refuted."""
    w = w_island(m)
    missed = run(m, w, stored(m, 0.0, 0.5))
    assert missed.status == m.REFUTED and chk.F_ABOVE in codes(missed)
    assert run(m, w, stored(m, 0.4, 1.0)).status == m.VERIFIED


@claim("S-10", "if st.boundaries is None or not st.complete:", "if st.boundaries is None:")
def oracle_incomplete_boundaries(m):
    """H2: a state factor whose change instants are not ASSERTED complete over the support cannot be solved piecewise: no number is
    certified (the builder's blank reason `state_boundaries_incomplete`)."""
    rep = run(m, w_island(m, complete=False), stored(m, 0.4, 1.0))
    assert rep.status == m.REFUTED and chk.F_H2 in codes(rep)


@claim("S-11", "if abs(self._step_value(rec, st, t) - x0) > 1e-12:", "if False:")
def oracle_hidden_change(m):
    """H2: the listed boundaries are checked against the factor's own values — a change the list omits (here the island's end at 0.45 d,
    with the list asserted complete) is found, not trusted."""
    rep = run(m, w_island(m, complete=True, listed=("start_only",)), stored(m, 0.4, 1.0))
    assert rep.status == m.REFUTED and chk.F_H2 in codes(rep)


@claim("S-12", "if ts - a <= e or b - ts <= e:", "if True:")
def oracle_h1_station_inside(m):
    """H1 (N-1): a tent-bearing support must lie in one monotone arc. A body that reverses at t = 0.5 d, strictly inside the support (half a day
    from either end), is not certified: `monotone_arc_not_established`."""
    pos = sky(A=lambda t: 100.3 + 2.0 * (t - 0.5) ** 2)
    w = {"lo": at(0), "hi": at(1), "pos": pos,
         "records": [m.CheckRecord("a", "ra", "A", ((at(0), at(1)),), tent=m.TentFactor("A", 100.5, 1.0))]}
    rep = run(m, w, stored(m, 0.5, 0.9))
    assert rep.status == m.REFUTED and chk.F_H1 in codes(rep)


@claim("S-13", "cuts.append(ts)", "pass")
def oracle_near_end_station_is_a_cut(m):
    """S0 finding K-2: the stored arcs end at a SPLINE station that differs from the Swiss one by up to 16.7 s, so the Swiss function turns
    back a few seconds before the support end. Analytic world: the body touches its level (value 1.0) at the station, 10 s before the end;
    the end value is 1 - 5e-5. The value taken at the support end is refuted, the station's 1.0 is proved."""
    w = w_station(m, 3590.0, 3600.0)
    end_value = 1.0 - 0.5e-6 * 10.0 ** 2
    low = run(m, w, stored(m, at(0, 3600.0 - 1e-6), end_value))
    assert low.status == m.REFUTED and chk.F_ABOVE in codes(low)
    assert run(m, w, stored(m, at(0, 3590.0), 1.0)).status == m.VERIFIED


@claim("S-14", 'self.unverified.append((U_BUDGET, f"more than {self.max_evals} ephemeris evaluations needed"))', "pass")
def oracle_budget_exhaustion(m):
    """Plan §2.4 / Q13 a: a window the verifier cannot settle inside its budget is UNVERIFIED — never a pass, never a best-found number.
    The smooth-maximum world needs ~3e4 ephemeris evaluations; with 300 it must not come back VERIFIED."""
    rep = run(m, w_interior(m, 1.0), stored(m, T_INT, M_INT), max_evals=300)
    assert rep.status == m.UNVERIFIED and chk.U_BUDGET in codes(rep) and not m.satisfies_gate(rep)


@claim("S-16", "want_for = sum(for_roots.values())", "want_for = max(for_roots.values(), default=0.0)")
def oracle_evidence_for_is_the_sum(m):
    """Plan §2.1 / QUALIFICATION_TABLE: evidence_for is the SUM over roots of the per-root max for-channel value (never the max over roots).
    Two roots valued 1.0 and 0.5 give 1.5."""
    recs = [m.CheckRecord("a", "r1", "Sun", ((at(0), at(1)),), constant=1.0), m.CheckRecord("b", "r2", "Sun", ((at(0), at(1)),), constant=0.5)]
    w = {"lo": at(0), "hi": at(1), "pos": no_sky, "records": recs}
    assert run(m, w, stored(m, 0.0, 1.5, evidence_for=1.5)).status == m.VERIFIED
    wrong = run(m, w, stored(m, 0.0, 1.5, evidence_for=1.0))
    assert wrong.status == m.REFUTED and chk.F_EVFOR in codes(wrong)


@claim("S-17", "against_null = (not self.against_evaluated) or bool(unq_against)", "against_null = (not self.against_evaluated)")
def oracle_evidence_against_null(m):
    """QUALIFICATION_TABLE rule 5: evidence_against is NULL when a live unqualified against-channel member could feed it — a stored 0.0
    would be an invented judgment (N.7 item 6)."""
    recs = [m.CheckRecord("f", "r1", "Sun", ((at(0), at(1)),), constant=1.0),
            m.CheckRecord("u", "r2", "Sun", ((at(0), at(1)),), channel=AGAINST, qualified=False)]
    w = {"lo": at(0), "hi": at(1), "pos": no_sky, "records": recs}
    assert run(m, w, stored(m, 0.0, 1.0, evidence_against=None), against_evaluated=True).status == m.VERIFIED
    wrong = run(m, w, stored(m, 0.0, 1.0, evidence_against=0.0), against_evaluated=True)
    assert wrong.status == m.REFUTED and chk.F_EVAGAINST in codes(wrong)


@claim("S-18", "if st.outcome_valence != want_v.outcome_valence_for_native:", "if False:")
def oracle_valence(m):
    """Spec §3 three-field valence: the outcome valence is the rule authority's, from class polarity and the evidence at the peak.
    `bereavement` is an adverse-polarity class, so occurrence with no against-evidence is `adverse`."""
    w = {"lo": at(0), "hi": at(1), "pos": no_sky, "records": [m.CheckRecord("a", "r1", "Sun", ((at(0), at(1)),), constant=1.0)]}
    kw = dict(event_class="bereavement", against_evaluated=True)
    assert run(m, w, stored(m, 0.0, 1.0, evidence_against=0.0, outcome_valence="adverse"), **kw).status == m.VERIFIED
    wrong = run(m, w, stored(m, 0.0, 1.0, evidence_against=0.0, outcome_valence="favourable"), **kw)
    assert wrong.status == m.REFUTED and chk.F_VALENCE in codes(wrong)


@claim("S-19", "want_score = max((v for _, _, v in lv), default=0.0)", "want_score = max((v for _, c, v in lv if c == CH_FOR), default=0.0)")
def oracle_score_over_all_channels(m):
    """QUALIFICATION_TABLE rule 4: the score is the max live record product at the peak over ALL live members of ANY channel. A for-record
    of 0.5 and an against-record of 0.9 live together: score 0.9."""
    recs = [m.CheckRecord("f", "r1", "Sun", ((at(0), at(1)),), constant=0.5),
            m.CheckRecord("c", "r2", "Sun", ((at(0), at(1)),), constant=0.9, channel=AGAINST)]
    w = {"lo": at(0), "hi": at(1), "pos": no_sky, "records": recs}
    assert run(m, w, stored(m, 0.0, 0.5, score=0.9), against_evaluated=True).status == m.VERIFIED
    wrong = run(m, w, stored(m, 0.0, 0.5, score=0.5), against_evaluated=True)
    assert wrong.status == m.REFUTED and chk.F_SCORE in codes(wrong)


@claim("S-20", "if rec.channel_at is not None and rec.channel_boundaries is not None:", "if False:")
def oracle_channel_flip_is_a_cut(m):
    """W-3 / BPHS 3.11 (the Moon's paksa flips at 180 deg elongation): a record whose side is decided PER INSTANT counts for the for-channel
    only after the flip; the flip instant (0.4 d) is a piece boundary and the earliest maximum."""
    flip = at(0.4)
    rec = m.CheckRecord("a", "r1", "Moon", ((at(0), at(1)),), channel=None, channel_at=lambda d: FOR if d >= flip else AGAINST,
                        channel_boundaries=lambda lo, hi: [flip] if lo < flip < hi else [])
    w = {"lo": at(0), "hi": at(1), "pos": no_sky, "records": [rec]}
    assert run(m, w, stored(m, 0.4, 1.0)).status == m.VERIFIED
    early = run(m, w, stored(m, 0.0, 1.0))
    assert early.status == m.REFUTED and chk.F_VALUE in codes(early)


@claim("S-21", "if self.objective == OBJ_SUM and rec.channel != CH_AGAINST:\n                    self._add(F_UNQ", "if False:\n                    self._add(F_UNQ")
def oracle_unqualified_for_member(m):
    """QUALIFICATION_TABLE rule 1: an unqualified member on the for / unknown channel makes the objective unqualified — a window carrying a
    number while such a member is live is refuted."""
    recs = [m.CheckRecord("a", "r1", "Sun", ((at(0), at(1)),), constant=1.0),
            m.CheckRecord("u", "r2", "Sun", ((at(0), at(1)),), qualified=False, channel=FOR)]
    rep = run(m, {"lo": at(0), "hi": at(1), "pos": no_sky, "records": recs}, stored(m, 0.0, 1.0))
    assert rep.status == m.REFUTED and chk.F_UNQ in codes(rep)


@claim("S-22", 'raise _Undet(f"record {rec.record_id}: a step factor is undeterminable at {self._dt(t).isoformat()}")', "x = 0.0")
def oracle_undeterminable_is_a_null(m):
    """N.7 item 6: an honest null beats a plausible default — a step factor that cannot be read at an instant makes the number
    unprovable (`operand_undeterminable`), it is not read as 0."""
    step = m.StepFactor(lambda d: None, lambda lo, hi: [], True)
    w = {"lo": at(0), "hi": at(1), "pos": no_sky, "records": [m.CheckRecord("a", "r1", "Sun", ((at(0), at(1)),), steps=(step,))]}
    rep = run(m, w, stored(m, 0.0, 0.0))
    assert rep.status == m.REFUTED and chk.F_UNDET in codes(rep)


@claim("S-24", "convex = not pc.mixed and len([k for k in by_body if k is not None]) <= 1", "convex = False")
def oracle_two_fixed_points_make_an_exact_plateau(m):
    """Two natal points 0.5 deg apart, one body, orb 1: while the body is between them one tent rises exactly as the other falls, so F is
    EXACTLY flat (1.5) for half a day — a trapezoid, earliest maximum at the first point's crest (t = 0.5 d). One body ⇒ F is a convex
    function of its (monotone) longitude: the supremum is an end value, no interior extremum exists, nothing needs searching. A modest
    budget proves it; the later end of the plateau is refuted as 'an earlier tie exists'."""
    pos = sky(A=lambda t: 100.0 + t)
    sup = ((at(0), at(2)),)
    recs = [m.CheckRecord("a", "ra", "A", sup, tent=m.TentFactor("A", 100.5, 1.0)),
            m.CheckRecord("b", "rb", "A", sup, tent=m.TentFactor("A", 101.0, 1.0))]
    w = {"lo": at(0), "hi": at(2), "records": recs, "pos": pos}
    rep = run(m, w, stored(m, 0.5, 1.5), max_evals=3000)
    assert rep.status == m.VERIFIED, rep
    late = run(m, w, stored(m, 1.0, 1.5), max_evals=3000)
    assert late.status == m.REFUTED and chk.F_EARLIER_TIE in codes(late), late


@claim("S-25", "groups, defined = list(agents.values()), set(agents) == P4_AGENTS", "groups, defined = list(agents.values()), bool(agents)")
def oracle_p4_defined_only_where_both_live(m):
    """Plan §2.1: the max-min objective is defined only on pieces where BOTH agents are live. Jupiter (1.0) lives on [0, 1) and Saturn
    (0.4) on [0.5, 1.5): the objective exists on [0.5, 1) only, value 0.4 — Jupiter alone on [0, 0.5) is not an objective value of 1.0."""
    recs = [m.CheckRecord("j", "RJ", "jupiter", ((at(0), at(1)),), constant=1.0),
            m.CheckRecord("s", "RS", "saturn", ((at(0.5), at(1.5)),), constant=0.4)]
    w = {"lo": at(0), "hi": at(1.5), "pos": no_sky, "records": recs, "objective": m.OBJ_MAXMIN}
    assert run(m, w, stored(m, 0.5, 0.4)).status == m.VERIFIED
    assert run(m, w, stored(m, 0.0, 1.0)).status == m.REFUTED


@claim("S-23", "return max(0.0, 1.0 - abs(self._s(tent, t)) / float(tent.orb_deg))", "return 1.0 - abs(self._s(tent, t)) / float(tent.orb_deg)")
def oracle_tent_is_the_frozen_kernel(m):
    """D-RQ2 / spec §7.2 inv 3: the activity kernel is angular, `max(0, 1 - |d|/orb)`, d the seam-safe distance along the directed ray.
    Differential against the frozen `kernel_factor.activity_kernel` on 400 random (longitude, level, ray, orb) points — including points
    beyond the orb (value 0) and across the 360 seam."""
    from services.gochara_rules import kernel_factor as kf
    from services.gochara_rules import registry as reg
    from .test_a53_window_sweep import _kernel_row
    saved = dict(reg.FACTORS)
    try:
        rng = random.Random(23)
        for orb in (0.5, 1.0, 2.0, 5.0):
            row = _kernel_row(orb)
            ref = (row["factor_id"], row["rule_version"])
            eng = m._Engine(at(0), at(1), [], m.OBJ_SUM, m.StoredWindow(at(0), 0.0), lambda b, d: LON[0], peak_tolerance_s=1.0,
                            max_evals=10 ** 9, event_class=None, against_evaluated=False)
            for _ in range(100):
                level = rng.choice([rng.uniform(0.0, 360.0), rng.uniform(0.0, 3.0), rng.uniform(357.0, 360.0 - 1e-9)])
                lon = (level + rng.uniform(-2.5 * orb, 2.5 * orb)) % 360.0
                ray = rng.choice([None, 60.0, 90.0, 180.0, 270.0])
                LON[0] = lon
                want = kf.activity_kernel("degree_point", f"point:{level!r}", factor_ref=ref, body_longitude_deg=lon,
                                          aspect_angle_deg=ray)["value"]
                eng._lon_cache.clear()
                got = eng._tent(m.TentFactor("X", level, orb, ray), 0.0)
                assert got == want, (lon, level, ray, orb, got, want)
    finally:
        reg.FACTORS.clear()
        reg.FACTORS.update(saved)


LON = [0.0]


# ── plain scenarios (no reversion: each pins an end-to-end case the claims above do not exercise) ─────────────────────────────────

def test_a_crossing_of_the_360_seam_is_proved_at_its_crest():
    """The tent is the seam-safe angular distance: a body going 359.5 -> 0.5 across the level 0 peaks at t = 0.5 d (also along a 180 deg ray)."""
    for lon0, level, ray in ((359.5, 0.0, None), (179.5, 0.0, 180.0)):
        pos = sky(A=lambda t, lon0=lon0: lon0 + t)
        w = {"lo": at(0), "hi": at(1), "pos": pos, "records": [
            chk.CheckRecord("a", "ra", "A", ((at(0), at(1)),), tent=chk.TentFactor("A", level, 1.0, ray))]}
        assert run(chk, w, stored(chk, 0.5, 1.0)).status == chk.VERIFIED
        assert run(chk, w, stored(chk, 0.0, 0.5)).status == chk.REFUTED


def test_a_record_with_two_supports_and_the_earliest_of_a_repeated_maximum():
    recs = [chk.CheckRecord("a", "r1", "Sun", ((at(0), at(0.3)), (at(0.6), at(1))), constant=1.0),
            chk.CheckRecord("b", "r1", "Sun", ((at(0.3), at(0.6)),), constant=0.5)]
    w = {"lo": at(0), "hi": at(1), "pos": no_sky, "records": recs}                 # one root: 1.0, 0.5, 1.0 in turn
    assert run(chk, w, stored(chk, 0.0, 1.0)).status == chk.VERIFIED
    late = run(chk, w, stored(chk, 0.6, 1.0))
    assert late.status == chk.REFUTED and chk.F_EARLIER_TIE in codes(late)


def test_an_identically_zero_objective_peaks_at_the_window_start():
    """QUALIFICATION_TABLE rule 3: an against-only population has the identically-zero objective; its earliest maximum is the start."""
    recs = [chk.CheckRecord("a", "r1", "Sun", ((at(0), at(1)),), constant=1.0, channel=AGAINST)]
    w = {"lo": at(0), "hi": at(1), "pos": no_sky, "records": recs}
    assert run(chk, w, stored(chk, 0.0, 0.0), against_evaluated=True).status == chk.VERIFIED
    assert run(chk, w, stored(chk, 0.5, 0.0), against_evaluated=True).status == chk.REFUTED


def test_the_stored_peak_must_lie_in_the_half_open_window():
    w = w_interior(chk, 1.0)
    out = run(chk, w, chk.StoredWindow(at(1.0), 0.8))
    assert out.status == chk.REFUTED and chk.F_OUTSIDE in codes(out)


def test_an_unsupported_objective_and_a_naive_instant_are_refused():
    w = w_interior(chk, 1.0)
    with pytest.raises(ValueError):
        run(chk, w, stored(chk, 0.5, 0.7), objective="sum_of_everything")
    with pytest.raises(ValueError):
        chk.check_window(lo=datetime(2030, 1, 1), hi=datetime(2030, 1, 2), records=[], objective=chk.OBJ_SUM,
                         stored=chk.StoredWindow(datetime(2030, 1, 1, 12), 0.0), position_at=no_sky)


# ── S-15: the differential over 500 random analytic worlds (builder-independent brute force) ─────────────────────────────────

def _rand_world(m, rng):
    p4 = rng.random() < 0.3
    nrec = 2 if p4 else rng.randint(2, 3)
    bodies, recs, spec = {}, [], []
    for i in range(nrec):
        v = rng.choice([-1, 1]) * rng.uniform(0.3, 1.5)
        a = rng.uniform(-0.1, 0.1)                                     # |v + 2 a t| >= 0.1 on the window: no station inside
        l0 = rng.uniform(20.0, 300.0)
        name = f"b{i}"
        bodies[name] = (lambda t, l0=l0, v=v, a=a: l0 + v * t + a * t * t)
        tc = rng.uniform(-0.3, 1.3)
        orb = rng.choice([0.5, 1.0, 2.0, 5.0])
        level = bodies[name](tc)
        const = rng.choice([1.0, 0.8, 0.5])
        isl = (rng.uniform(0.1, 0.5), rng.uniform(0.55, 0.9), rng.choice([0.0, 0.6])) if rng.random() < 0.3 else None
        agent = ("jupiter" if i == 0 else "saturn") if p4 else "sun"
        root = f"R{i}" if p4 else f"R{rng.randint(0, 1)}"
        spec.append((name, level, orb, const, isl, agent, root))
        steps = ()
        if isl is not None:
            lo_, hi_, val = isl
            steps = (m.StepFactor(lambda d, lo_=lo_, hi_=hi_, val=val: val if at(lo_) <= d < at(hi_) else 1.0,
                                  lambda lo, hi, lo_=lo_, hi_=hi_: [x for x in (at(lo_), at(hi_)) if lo < x < hi], True),)
        recs.append(m.CheckRecord(f"r{i}", root, agent, ((at(0), at(1)),), constant=const, steps=steps,
                                  tent=m.TentFactor(name, level, orb)))
    return ({"lo": at(0), "hi": at(1), "records": recs, "pos": sky(**bodies), "objective": m.OBJ_MAXMIN if p4 else m.OBJ_SUM},
            bodies, spec, p4)


def _edge_s(days):
    """A step edge as the world sees it: the microsecond-quantised instant, in seconds since T0."""
    return (at(days) - T0).total_seconds()


def _brute_F(bodies, spec, p4, ts):
    """The objective at `ts` seconds since T0 straight from its definition, with its own arithmetic (plan §2.1) — no code shared with the
    checker. Island edges are the microsecond-quantised instants the world uses."""
    per = {}
    for name, level, orb, const, isl, agent, root in spec:
        v = const * _tent(bodies[name](ts / 86400.0) % 360.0, level % 360.0, orb)
        if isl is not None and _edge_s(isl[0]) <= ts < _edge_s(isl[1]):
            v *= isl[2]
        key = agent if p4 else root
        per[key] = max(per.get(key, 0.0), v)
    return min(per.values()) if p4 else sum(per.values())


def _brute_truth(bodies, spec, p4):
    """(value, seconds): a dense 30 s scan, golden-section polish of the best cells, and the one-microsecond-before-a-drop candidates
    (every instant is quantised to the microsecond, as a stored instant is)."""
    F = lambda ts: _brute_F(bodies, spec, p4, ts)                                  # noqa: E731
    grid = [i * 30.0 for i in range(2880)]
    vals = [F(t) for t in grid]
    n = len(grid)
    peaks = [i for i in range(n) if vals[i] >= vals[max(i - 1, 0)] and vals[i] >= vals[min(i + 1, n - 1)]]   # every local maximum of the grid
    cands = [(vals[i], grid[i]) for i in peaks]
    end = 86400.0 - 1e-6
    cands.append((F(end), end))
    for s in spec:
        for x in ((_edge_s(s[4][0]), _edge_s(s[4][1])) if s[4] else ()):
            cands.append((F(x - 1e-6), x - 1e-6))
            cands.append((F(x), x))
    g = (math.sqrt(5) - 1) / 2
    found = list(cands)
    for f0, t0 in cands:
        a, b = max(0.0, t0 - 30.0), min(end, t0 + 30.0)
        for _ in range(60):
            c, d = b - g * (b - a), a + g * (b - a)
            if F(c) >= F(d):
                b = d
            else:
                a = c
        tm = round(0.5 * (a + b), 6)
        found.append((F(tm), tm))
    top = max(f for f, _ in found)
    return top, min(t for f, t in found if f >= top - 1e-10)                       # the EARLIEST of exact ties (spec §7.2 inv 2)


@claim("S-15", "BOUND_TOL = 1e-7 ", "BOUND_TOL = 1e-5 ")
def oracle_differential_500_worlds(m):
    """The checker agrees with an independent dense brute force on 500 random analytic worlds (linear / quadratic bodies, 2-3 tents, step
    islands, sum and max-min objectives): the true (instant, value) is PROVED, and the same instant with a value 5e-7 too low — inside the
    float4 storage round-trip, so only the 1e-7 bound threshold can see it — is REFUTED as 'the objective exceeds the stored maximum'."""
    rng = random.Random(2026102101)
    worlds = checked = 0
    for k in range(500):
        world, bodies, spec, p4 = _rand_world(m, rng)
        m_true, t_true = _brute_truth(bodies, spec, p4)
        when = at(0, t_true)
        if m_true < 0.05:                                               # an (almost) identically-zero objective: nothing to separate
            continue
        worlds += 1
        good = run(m, world, stored(m, when, m_true))
        assert good.status == m.VERIFIED, (k, good.findings, good.unverified, m_true, t_true)
        low = run(m, world, stored(m, when, m_true - 5e-7))
        assert low.status == m.REFUTED and chk.F_ABOVE in codes(low), (k, low.findings, low.unverified)
        checked += 1
    assert checked == worlds and worlds >= 450, worlds


# ═══════════════════════════════ the harness ════════════════════════════════════════════════════════════════════════════════

_COUNT = [0]


def reverted_module(old: str, new: str):
    """The checker's source with exactly ONE occurrence of `old` replaced by `new`, loaded as a throw-away module."""
    assert old != new and SRC.count(old) == 1, f"the planted reversion must match exactly once, matched {SRC.count(old)}x: {old[:70]!r}"
    _COUNT[0] += 1
    name = f"_reverted_window_solver_check_{_COUNT[0]}"
    mod = types.ModuleType(name)
    mod.__file__ = name
    sys.modules[name] = mod                                           # dataclasses resolve their annotations through sys.modules
    try:
        exec(compile(SRC.replace(old, new), name, "exec"), mod.__dict__)
    finally:
        sys.modules.pop(name, None)
    return mod


@pytest.mark.parametrize("cid", sorted(CLAIMS))
def test_oracle_passes_on_the_real_checker(cid):
    CLAIMS[cid][0](chk)


@pytest.mark.parametrize("cid", sorted(CLAIMS))
def test_the_single_planted_reversion_fails_the_oracle(cid):
    oracle, old, new = CLAIMS[cid]
    reverted = reverted_module(old, new)          # built OUTSIDE the raises-block: a reversion that no longer matches is an ERROR, not a pass
    with pytest.raises(AssertionError):
        oracle(reverted)


def test_every_claim_has_exactly_one_reversion_and_one_oracle():
    assert set(CLAIMS) == {"V-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-8", "S-9", "S-10", "S-11", "S-12", "S-13", "S-14",
                           "S-15", "S-16", "S-17", "S-18", "S-19", "S-20", "S-21", "S-22", "S-23", "S-24", "S-25", "S-26", "S-27", "S-28", "S-29", "S-30", "S-31"}
    assert len({old for _, old, _ in CLAIMS.values()}) == len(CLAIMS)             # no two claims share a reversion site


# ═══════════════════════════════ guards (no reversion: they measure a property of the module) ═════════════════════════════════

_FORBIDDEN = ("window_sweep", "window_solver", "window_verifier", "kernel_factor", "gochara_kernel", "gochara_rules.records")


def independence_problems(source: str) -> list:
    """The imports of `source` that would break independence from the builder: any module of the kernel, or the builder's rule modules,
    except the ONE lazily imported rule authority (valence)."""
    bad = []
    for node in ast.walk(ast.parse(source)):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = ("." * node.level) + (node.module or "")
            names = [base] + [f"{base}.{a.name}" for a in node.names]
        for n in names:
            if node_is_relative_or_forbidden(n) and n not in ("services.gochara_rules",):
                bad.append(n)
    return bad


def node_is_relative_or_forbidden(n: str) -> bool:
    return n.startswith(".") or any(f in n for f in _FORBIDDEN)


def test_the_module_imports_nothing_of_the_builder():
    assert independence_problems(SRC) == []
    allowed = [n for n in ("services.gochara_rules.valence",) if n in SRC or "valence" in SRC]
    assert allowed, "the one shared rule authority (valence) is the only gochara import"


def test_the_independence_detector_reads_false_on_a_planted_import():
    for planted in ("from . import window_sweep", "from .window_sweep import SweepRecord", "import services.gochara_kernel.window_solver",
                    "from services.gochara_rules import kernel_factor"):
        assert independence_problems(SRC + "\n" + planted + "\n"), planted


def test_importing_the_checker_does_not_load_the_builder():
    import subprocess
    root = str(Path(__file__).resolve().parents[3])
    code = (f"import sys; sys.path.insert(0, {root!r}); from services.gochara_kernel import window_solver_check\n"
            "bad = [m for m in ('services.gochara_kernel.window_sweep', 'services.gochara_kernel.window_solver') if m in sys.modules]\n"
            "print('LOADED', bad) if bad else print('CLEAN')\n")
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, cwd=root)
    assert out.stdout.strip() == "CLEAN", out.stdout + out.stderr


def test_h1_sampling_premise_and_the_s0_measured_constants():
    # S0_REPORT §2.1: the minimum station spacing on the real sky is 19.7585 d (Mercury); two sampling intervals must fit inside it so
    # no reversal PAIR can hide between samples (a single reversal always flips the sampled sign)
    assert 2 * chk.H1_SAMPLE_S / 86400.0 < chk.MIN_STATION_SPACING_D <= 19.7585
    # S0_REPORT §2.2: the spline-vs-Swiss station offset reaches 16.7 s (Mercury); a cut window of E seconds must clear it with margin
    assert chk.NEAR_END_S >= 2 * 16.7
    assert chk.PEAK_INSTANT_TOLERANCE_S == 1.0                                    # SOLVER-TOLERANCES: Q12 a, to the second
    assert chk.TIE == 1e-9 and chk.GREY == 2e-10 and chk.VALUE_TOL == 1e-6 and chk.BOUND_TOL == 1e-7


def test_the_objective_names_and_channels_are_the_frozen_strings():
    # restated, not imported (the module must not import the builder); equality is asserted HERE against the verifier's own literals
    from services.gochara_kernel import window_verifier as wv
    assert chk.CH_FOR == "evidence_for_occurrence" and chk.CH_AGAINST == "evidence_against_occurrence"
    assert chk.OBJ_SUM == "evidence_for_per_root_sum" and chk.OBJ_MAXMIN == "max_min_agent_activity"
    assert wv.POLICY_VERSION == "window_qualification/1"


# ═══════════════════════════════ the real sky (pinned Swiss corpus): H1 and the correct-window case ═══════════════════════════

def _swiss():
    assert_real_ephemeris()
    import swisseph as swe
    from services.gochara_kernel import knots

    def pos(body, d):
        jd = swe.julday(d.year, d.month, d.day, d.hour + d.minute / 60.0 + (d.second + d.microsecond / 1e6) / 3600.0)
        return knots.calc_sidereal_lon(body, jd, EPHE_PATH)[0]
    return pos


def _station(pos, body, start, step_days=2.0, span_days=400):
    """The first reversal of `body`'s longitude after `start`, bisected on the centred-difference velocity (the test's own scan)."""
    def v(d):
        h = timedelta(minutes=10)
        return ((pos(body, d + h) - pos(body, d - h) + 180.0) % 360.0 - 180.0)
    d, prev = start, v(start)
    for _ in range(int(span_days / step_days)):
        nxt = d + timedelta(days=step_days)
        cur = v(nxt)
        if (prev > 0) != (cur > 0):
            lo, hi = d, nxt
            for _ in range(40):
                mid = lo + (hi - lo) / 2
                if (v(mid) > 0) == (prev > 0):
                    lo = mid
                else:
                    hi = mid
            return lo + (hi - lo) / 2
        d, prev = nxt, cur
    raise AssertionError("no station found")


@requires_swieph
def test_real_sky_a_station_inside_a_saturn_support_is_not_certified():
    pos = _swiss()
    st = _station(pos, "Saturn", datetime(2030, 1, 1, tzinfo=timezone.utc))
    lo, hi = st - timedelta(days=3), st + timedelta(days=3)
    rec = chk.CheckRecord("sat", "r", "saturn", ((lo, hi),), tent=chk.TentFactor("Saturn", pos("Saturn", st), 1.0))
    rep = chk.check_window(lo=lo, hi=hi, records=[rec], objective=chk.OBJ_SUM, position_at=pos,
                           stored=chk.StoredWindow(st, 1.0))
    assert rep.status == chk.REFUTED and chk.F_H1 in rep.codes(), rep


@requires_swieph
def test_real_sky_a_mid_arc_crossing_is_proved_at_its_crest():
    pos = _swiss()
    t0 = datetime(2030, 3, 1, tzinfo=timezone.utc)
    level = pos("Jupiter", t0 + timedelta(days=1))
    # the test's own root: bisect the monotone offset of Jupiter to the level (no checker code)
    lo, hi = t0, t0 + timedelta(days=2)
    s = lambda d: (pos("Jupiter", d) - level + 180.0) % 360.0 - 180.0             # noqa: E731
    sgn = s(lo) > 0
    for _ in range(60):
        mid = lo + (hi - lo) / 2
        lo, hi = (mid, hi) if (s(mid) > 0) == sgn else (lo, mid)
    crest = lo + (hi - lo) / 2
    w_lo, w_hi = crest - timedelta(hours=18), crest + timedelta(hours=18)
    rec = chk.CheckRecord("jup", "r", "jupiter", ((w_lo, w_hi),), tent=chk.TentFactor("Jupiter", level, 1.0))
    rep = chk.check_window(lo=w_lo, hi=w_hi, records=[rec], objective=chk.OBJ_SUM, position_at=pos,
                           stored=chk.StoredWindow(crest, 1.0))
    assert rep.status == chk.VERIFIED, rep
    off = chk.check_window(lo=w_lo, hi=w_hi, records=[rec], objective=chk.OBJ_SUM, position_at=pos,
                           stored=chk.StoredWindow(crest + timedelta(minutes=5), 1.0))
    assert off.status == chk.REFUTED and chk.F_VALUE in off.codes()               # 5 min off the crest: the value is no longer 1.0
