"""SR-OD1 achievement_recognition defect (2) — the sweep's support/geometry check at the stored contact EDGES (AR_DIAG §2).

The claims, each with ONE oracle whose planted reversion fails (B.10: a real Swiss ephemeris, not a stand-in; SE_EPHE_PATH must point at the pinned corpus):

  C1  A record whose support edge equals the true sign edge to within ONE JD-ulp — on either side, at either end — is not refused. The platform's
      boundary convention is half-open, the NEW state owns the boundary instant (p1_operands.py BOUNDARIES; p1_operands_check.py NAMED LIMITS; SR-OD1
      R-2 / SR-H2-1S), and a stored edge is a Julian-Day double (ulp ≈ 40 µs at JD 2.46e6), so it cannot name the edge any closer than that.
      Planted reversion: `_geometry_at_edge` without the ulp probe (return the exact-edge answer) — the four ulp cases and the stored-edge cases fail.
  C2  A genuine disagreement still refuses: the same span extended 1 s past the real egress (or started 1 s before the real ingress) is refused.
      Planted reversion: a tolerance of seconds instead of one ulp — the 1 s cases stop refusing.
  C3  The tolerance is derived from the JD double (`jd_ulp_tolerance`), not a round constant: it is 40–41 µs at the 2010s' JD and the next double above the
      instant's JD is within it. Planted reversion: a constant 1 ms — the bound assertion fails.
"""
from __future__ import annotations

import dataclasses
import math
import os
from datetime import datetime, timedelta, timezone

import pytest

swe = pytest.importorskip("swisseph")

from services.gochara_kernel import window_sweep as ws                       # noqa: E402
from services.gochara_kernel.window_sweep import SweepRefusal                # noqa: E402
from tests.l3.gochara.test_a53_window_sweep import (                         # noqa: E402,F401
    _draft, _rec, _restore_factor_registry, _rows_declared)

UTC = timezone.utc
_JD_UNIX_EPOCH = 2440587.5
_MARS, _SAT = swe.MARS, swe.SATURN

pytestmark = pytest.mark.skipif(not os.environ.get("SE_EPHE_PATH"), reason="needs the pinned Swiss Ephemeris corpus (SE_EPHE_PATH)")


def _jd(t: datetime) -> float:
    return t.timestamp() / 86400.0 + _JD_UNIX_EPOCH


def _dt(jd: float) -> datetime:
    return datetime.fromtimestamp((jd - _JD_UNIX_EPOCH) * 86400.0, tz=UTC)


def _lon(body, t: datetime) -> float:
    swe.set_ephe_path(os.environ["SE_EPHE_PATH"])
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.calc_ut(_jd(t), body, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] % 360.0


def _sign(body, jd: float) -> int:
    return int(_lon(body, _dt(jd)) // 30.0)


def _ingress(body, jd0: float, tol: float) -> tuple[float, int]:
    """The first sign change after `jd0`: its JD bisected to `tol` days (the substrate stores 1e-9; 0 = to adjacent doubles, the TRUE edge), and the sign entered (0-based)."""
    jd, s0 = jd0, _sign(body, jd0)
    while _sign(body, jd + 5.0) == s0:
        jd += 5.0
    lo, hi = jd, jd + 5.0
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if mid in (lo, hi):
            break
        lo, hi = (mid, hi) if _sign(body, mid) == s0 else (lo, mid)
    return hi, _sign(body, hi)


def _true_edge(body, jd: float, tol: float) -> tuple[datetime, int]:
    """The ingress as a datetime. tol > 0: as the substrate stores it (JD bisected to `tol`, converted). tol = 0: the TRUE edge to the whole microsecond
    (the earliest µs datetime in the new sign), so that the oracles can plant a support edge a known distance from it."""
    j, s = _ingress(body, jd, tol)
    if tol:
        return _dt(j), s
    hi = _dt(j)
    lo = hi - timedelta(microseconds=200)
    assert _sign(body, _jd(lo)) != s
    while hi - lo > timedelta(microseconds=1):
        mid = lo + (hi - lo) // 2
        lo, hi = (lo, mid) if _sign(body, _jd(mid)) == s else (mid, hi)
    return hi, s


def _span(body, start: datetime, tol: float = 0.0):
    """A REAL residence span of `body`: (enter, leave, 1-based span number) from two consecutive Swiss ingresses after `start`."""
    e1, s1 = _true_edge(body, _jd(start), tol)
    e2, _ = _true_edge(body, _jd(e1) + 1.0, tol)
    return e1, e2, s1 + 1


def _record(body, agent, lo, hi, span_no):
    rec = _rec("r", path="P3", kind="sign_span", target=f"span:{span_no}", agent=agent,
               longitude_at=lambda t, _b=body: _lon(_b, t))
    return dataclasses.replace(rec, supports=((lo, hi),))


def _run(rec):
    return _draft([rec], _rows_declared)[0][0]


@pytest.fixture(scope="module")
def mars():
    return _span(_MARS, datetime(2010, 1, 1, tzinfo=UTC))


@pytest.fixture(scope="module")
def saturn():
    return _span(_SAT, datetime(2010, 1, 1, tzinfo=UTC))


@pytest.fixture(scope="module")
def stored_style():
    """The same spans with edges as the substrate stores them: bisected only to 1e-9 d."""
    start = datetime(2010, 1, 1, tzinfo=UTC)
    return ((_MARS, "mars", _span(_MARS, start, 1e-9)), (_SAT, "saturn", _span(_SAT, start, 1e-9)))


def _ulp(t: datetime) -> timedelta:
    return ws.jd_ulp_tolerance(t)


# ── C1 ───────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("end", ["start", "end"])
@pytest.mark.parametrize("direction", [-1, +1])
def test_a_support_edge_within_one_jd_ulp_of_the_true_sign_edge_is_not_refused(mars, end, direction):
    lo, hi, no = mars
    shift = direction * (_ulp(lo) - timedelta(microseconds=2))        # strictly within one ulp of the true edge, early or late
    s_lo, s_hi = (lo + shift, hi) if end == "start" else (lo, hi + shift)
    w = _run(_record(_MARS, "mars", s_lo, s_hi, no))
    assert w.score == 1.0 and w.members == 1


def test_the_stored_style_edges_of_real_swiss_spans_are_not_refused(stored_style):
    """The edges exactly as the substrate stores them (bisected to 1e-9 d, converted through the JD double): AR_DIAG measured 74 % of these refused."""
    for body, agent, (lo, hi, no) in stored_style:
        w = _run(_record(body, agent, lo, hi, no))
        assert w.score == 1.0, (agent, lo, hi)


# ── C2 ───────────────────────────────────────────────────────────────────────────────────────────────

def test_a_genuine_one_second_disagreement_still_refuses(mars):
    lo, hi, no = mars
    one_s = timedelta(seconds=1)
    with pytest.raises(SweepRefusal, match="support/geometry disagree"):
        _run(_record(_MARS, "mars", lo, hi + one_s, no))              # the support runs 1 s past the real egress
    with pytest.raises(SweepRefusal, match="support/geometry disagree"):
        _run(_record(_MARS, "mars", lo - one_s, hi, no))              # the support starts 1 s before the real ingress


def test_an_edge_just_beyond_one_jd_ulp_still_refuses(mars):
    lo, hi, no = mars
    beyond = ws.jd_ulp_tolerance(hi) + timedelta(microseconds=20)
    with pytest.raises(SweepRefusal, match="support/geometry disagree"):
        _run(_record(_MARS, "mars", lo, hi + beyond, no))
    with pytest.raises(SweepRefusal, match="support/geometry disagree"):
        _run(_record(_MARS, "mars", lo - beyond, hi, no))


# ── C3 ───────────────────────────────────────────────────────────────────────────────────────────────

def test_the_tolerance_is_one_jd_ulp_of_the_instant_not_a_round_constant():
    t = datetime(2010, 1, 1, tzinfo=UTC)
    tol = ws.jd_ulp_tolerance(t)
    jd = _jd(t)
    next_jd = math.nextafter(jd, math.inf)
    spacing = (next_jd - jd) * 86400.0
    assert spacing + 1e-6 <= tol.total_seconds() < spacing + 3e-6          # one double's spacing, rounded up to the µs, plus the datetime's µs
    assert timedelta(microseconds=30) < tol < timedelta(microseconds=60)
