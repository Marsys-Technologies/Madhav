"""SR-OD1 od1-drishti-edge — the BUILDER solver's dṛṣṭi (graduated aspect) step at the stored sign INGRESSES (review lane ar-verifier, "the builder's
solver has the same zero slack").

`window_store._aspect_offset_provider` read the aspecting graha's sign AT the stored ingress `t_exact` with zero slack. A stored ingress is a Julian-Day double
Swiss bisected to 1e-9 d and converted by `jd_to_utc` (−21..+20 µs off the true edge), so the new state's first instant read the OLD sign (or the previous
piece's last probe read the NEW one) and the solver's H2 detector blanked the window `state_boundaries_incomplete`: 43/43 real P3/P4-style ingresses.
The fix applies the boundary convention od1-ar-sweep introduced (half-open, the new state owns the boundary instant, at exactly one JD-ulp:
`window_sweep.jd_ulp_tolerance`, never looser). A real Swiss ephemeris (B.10), `SE_EPHE_PATH` must point at the pinned corpus.

The claims, each with ONE oracle whose planted reversion fails:

  D1  Every stored-style ingress (1e-9 d bisect, `jd_to_utc`) of Jupiter / Saturn / Mars (12 + 6 + 25 = 43) yields a SOLVED window, not a
      `state_boundaries_incomplete` blank. Planted reversion: the zero-slack read (`_read_instant` returns `t`) — 43 blanks.
  D2  A stored ingress 1 s off the true edge (early or late) still refuses (blank `state_boundaries_incomplete`): the slack is one JD-ulp, not seconds.
      Planted reversion: a slack of seconds in `jd_ulp_tolerance`'s use here — the 1 s cases stop refusing.
  D3  The read never leaves the state: a stored ingress closer to its neighbour than 2 ulp is clamped to the midpoint (no read crosses the neighbouring edge).
      Planted reversion: drop the midpoint clamp — the read crosses the neighbour.
  D4  (pair review DE-B1) The PRODUCTION path, `WindowStore.read_grain`, hands the body's stored sign ingresses to the offset provider: on every one of the
      43 stored-style ingresses the record's `aspect_offset_at` reads the NEW sign at the stored edge and not the new sign one µs before it (half-open, the
      new state owns the edge; Parāśara's whole-sign graduated dṛṣṭi changes only at a sign ingress). Planted reversion: `read_grain` calls the provider
      without the list — the 43 blanks return in production while every direct-provider oracle above still passes.
  D5  (pair review DE-B2) The slack is one JD-ulp, not a round millisecond: an ingress listed 1 ms off the true edge (either way) still refuses on the
      builder, as it does on the verifier. Planted reversion: `_read_instant`'s tolerance becomes 1 ms.
"""
from __future__ import annotations

import os
from datetime import timedelta

import pytest

pytest.importorskip("swisseph")

from services.gochara_kernel import window_solver as sol                      # noqa: E402
from services.gochara_kernel import window_store as wst                       # noqa: E402
from services.gochara_kernel.window_store import WindowStore                  # noqa: E402
from services.gochara_kernel.window_sweep import jd_ulp_tolerance             # noqa: E402
from services.gochara_rules import drishti as rd                              # noqa: E402
from tests.l3.gochara.test_od1_sweep_geometry_edges import (                  # noqa: E402
    _SAT, _MARS, _jd, _lon, _true_edge)
import swisseph as swe                                                        # noqa: E402

pytestmark = pytest.mark.skipif(not os.environ.get("SE_EPHE_PATH"), reason="needs the pinned Swiss Ephemeris corpus (SE_EPHE_PATH)")

_JUP = swe.JUPITER
_JD0 = 2455197.5          # 2010-01-01


def _ingresses(body, n: int, tol: float):
    """The first `n` consecutive sign ingresses after 2010 as (instant, sign entered 0-based). `tol` = 0: the TRUE edge (to the whole µs). `tol` > 0: the
    instant EXACTLY as the substrate stores it — the contact layer's own `swiss_bisect` (1e-9 d) converted by `substrate.jd_to_utc` (−21..+20 µs off)."""
    if not tol:
        out, jd = [], _JD0
        for _ in range(n):
            t, s = _true_edge(body, jd, 0.0)
            out.append((t, s))
            jd = _jd(t) + 1.0
        return out
    from services.gochara_kernel import contacts as C, knots as K, substrate as S
    ep = os.environ["SE_EPHE_PATH"]
    title = {_JUP: "Jupiter", _SAT: "Saturn", _MARS: "Mars"}[body]
    out, jd = [], _JD0
    s0 = int(K.calc_sidereal_lon(title, jd, ep)[0] // 30)
    while len(out) < n:
        s1 = int(K.calc_sidereal_lon(title, jd + 2.0, ep)[0] // 30)
        if s1 != s0:
            level = (s1 * 30.0) if (s1 - s0) % 12 == 1 else (s0 * 30.0)
            r, _ = C.swiss_bisect(title, jd, jd + 2.0, level, ep, tol_days=tol)
            out.append((S.jd_to_utc(r), s1)); s0 = s1
        jd += 2.0
    return out


def _solve(body, name, edges, k, stored, provider_list=True):
    """The builder solver over one window [c-2d, c+2d] around edge `k` of `edges`, whose dṛṣṭi is the step read through the REAL provider with the
    STORED ingress list `stored`; the step's boundary list is the stored ingress (as `read_grain` supplies it)."""
    c, s_new = edges[k]
    tgt = (s_new + 3) % 12 + 1                                           # a target 4 houses from the sign entered: a real offset-changing aspect
    off = wst._aspect_offset_provider(f"span:{tgt}", name, lambda n, t: _lon(body, t), stored if provider_list else None)
    lo, hi = c - timedelta(days=2), c + timedelta(days=2)
    at = lambda s: lo + timedelta(seconds=s)
    val = lambda s: rd.graduated_drishti(name.title(), off(at(s)), factor_ref=("graduated_drishti", "1.0.0"))["value"]
    cs = (stored[k] - lo).total_seconds()
    step = sol.Step(value_at=val, boundaries=lambda a, b: [cs] if a < cs < b else [], complete=True)
    length = (hi - lo).total_seconds()
    return sol.solve(sol.Problem(lo=0.0, hi=length, objective=sol.OBJECTIVE_SUM,
                                 members=(sol.Member(key="r", group="R", supports=((0.0, length),), steps=(step,)),)))


_BODIES = ((_JUP, "jupiter", 12), (_SAT, "saturn", 6), (_MARS, "mars", 25))


@pytest.fixture(scope="module")
def stored_style():
    return {name: (body, _ingresses(body, n, 1e-9)) for body, name, n in _BODIES}


def _results(stored_style, *, provider_list):
    out = []
    for name, (body, edges) in stored_style.items():
        stored = [t for t, _ in edges]
        for k in range(len(edges)):
            out.append(_solve(body, name, edges, k, stored, provider_list))
    return out


def test_d1_every_stored_style_ingress_is_numbered_not_blank(stored_style):
    res = _results(stored_style, provider_list=True)
    assert len(res) == 43
    blanks = [(r.status, r.reason) for r in res if r.status != sol.SOLVED]
    assert blanks == [], blanks


def test_d1_detector_reads_false_without_the_stored_list(stored_style):
    """The earned signal: the same 43 windows through the zero-slack read ARE the 43 blanks (the detector can read false)."""
    res = _results(stored_style, provider_list=False)
    assert len(res) == 43
    assert all(r.status == sol.BLANK and r.reason == sol.REASON_BOUNDARIES for r in res)


@pytest.mark.parametrize("shift", [timedelta(seconds=1), -timedelta(seconds=1)])
def test_d2_a_stored_ingress_one_second_off_the_true_edge_still_refuses(shift):
    for body, name in ((_MARS, "mars"), (_JUP, "jupiter")):
        true = _ingresses(body, 4, 0.0)
        stored = [t + shift for t, _ in true]
        for k in range(len(true)):
            r = _solve(body, name, true, k, stored)
            assert r.status == sol.BLANK and r.reason == sol.REASON_BOUNDARIES, (name, k, shift, r.status, r.reason)


def test_d3_the_read_never_crosses_the_neighbouring_stored_edge():
    from datetime import datetime, timezone
    c1 = datetime(2010, 3, 1, tzinfo=timezone.utc)
    c2 = c1 + jd_ulp_tolerance(c1)                                       # a state shorter than 2 ulp
    stored = [c1, c2]
    mid = c1 + (c2 - c1) / 2
    for t in (c1, c1 + (c2 - c1) / 4, mid - timedelta(microseconds=1)):  # the state [c1, c2): every read stays inside it
        assert c1 <= wst._read_instant(t, stored) <= c2
    assert wst._read_instant(c1, stored) <= mid                          # the new state's first read is clamped to the midpoint, not c1 + ulp


def test_d2_a_stored_ingress_one_millisecond_off_the_true_edge_still_refuses_on_the_builder():
    """DE-B2: one ulp (tens of µs), not a round millisecond — the builder refuses where the verifier refuses."""
    for shift in (timedelta(milliseconds=1), -timedelta(milliseconds=1)):
        for body, name in ((_MARS, "mars"), (_JUP, "jupiter")):
            true = _ingresses(body, 4, 0.0)
            stored = [t + shift for t, _ in true]
            for k in range(len(true)):
                r = _solve(body, name, true, k, stored)
                assert r.status == sol.BLANK and r.reason == sol.REASON_BOUNDARIES, (name, k, shift, r.status, r.reason)


class _Range:
    def __init__(self, lower, upper):
        self.lower, self.upper = lower, upper


class _Res:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None


class _GrainConn:
    """One aspect record per stored ingress (the record's support = [c - 2 d, c + 2 d)); the substrate's sign-ingress rows for the body."""
    def __init__(self, agent, stored, targets):
        self.agent, self.stored, self.targets = agent, stored, targets

    def execute(self, sql, params=None):
        if "completed_horizon" in sql:
            return _Res([(_Range(self.stored[0] - timedelta(days=400), self.stored[-1] + timedelta(days=400)),)])
        if "event_kind = 'sign_ingress'" in sql:
            assert params == (self.agent, "conv-1"), params
            return _Res([(c, 0.0, "swiss_bisect_tol_1e-9d", None, None, None) for c in self.stored])
        if "ka_gochara_relationship_record r" in sql:
            return _Res([(f"r{k}", f"c{k}", "P3", "1.0.0", "aspect", "house_span", self.agent, "scored", "admitted", f"span:{tgt}", None,
                          c - timedelta(days=2), c + timedelta(days=2), True, False, None, "conv-1", None)
                         for k, (c, tgt) in enumerate(zip(self.stored, self.targets))])
        raise AssertionError(sql)


def test_d4_read_grain_hands_the_stored_ingresses_to_the_offset_provider():
    """DE-B1: the wiring (`crossings[key]` -> `_aspect_offset_provider`) in the production `read_grain`, over the 43 real stored-style ingresses."""
    n_checked = 0
    for body, name, n in _BODIES:
        edges = _ingresses(body, n, 1e-9)
        stored = [t for t, _ in edges]
        targets = [(s + 3) % 12 + 1 for _, s in edges]
        recs = WindowStore(_GrainConn(name, stored, targets)).read_grain(
            chart_id="x", generation="5.0", event_class="career", path_id="P3", rule_version="1.0.0",
            position_at=lambda title, t, _b=body: _lon(_b, t))
        assert len(recs) == n
        by_id = {r.record_id: r for r in recs}
        for k, (c, s_new) in enumerate(edges):
            off = by_id[f"r{k}"].aspect_offset_at
            new = (targets[k] - 1 - s_new) % 12 + 1                      # inclusive whole-sign offset from the sign ENTERED
            assert off(c) == new, (name, k, c, off(c), new)                # the new state owns its edge
            assert off(c - timedelta(microseconds=1)) != new, (name, k, c)  # the old state still owns the instant before it
            n_checked += 1
    assert n_checked == 43
