"""SR-OD1 PRETR-early defect D-B — the sweep's support/geometry check at the edge of a node (retrograde) residence record whose neighbour's edge is ONE JD-ulp away.

Evidence (parental_event, window P3, a real build): `SweepRefusal ... its stored support contains <instant> but the contact geometry places the target outside` for a Ketu
`house_span` residence record. Rahu and Ketu cross a sign 180 deg apart at the same instant, but each stored edge is a Julian-Day double Swiss bisected to 1e-9 d, so the
two records' edges differ by one JD-ulp (40 us). The sweep cuts the component at every member's edge, which leaves a SLIVER piece (40 us, shorter than 2 ulp) at the
Ketu record's edge; the ulp probe (`_geometry_at_edge`) was clamped to THAT piece's midpoint (+20 us) and stopped 1 us short of the true edge (+21 us), so a stored edge
that is within one ulp of the sign edge read as outside. The probe is now bounded by the record's OWN stored support, never by a neighbour-cut piece.

The claims, each with ONE oracle whose planted reversion fails (B.10: a real Swiss ephemeris, the mean node, `SE_EPHE_PATH` must point at the pinned corpus):

  C1  A retrograde node record whose stored edge is within one JD-ulp of the true sign edge (here 30 us early at the ingress, 30 us late at the egress) is NOT refused
      when a neighbouring record's edge cuts a one-ulp sliver piece at that edge. The platform's boundary convention is half-open, the NEW state owns the boundary
      instant (p1_operands.py BOUNDARIES; p1_operands_check.py NAMED LIMITS; SR-OD1 R-2 / SR-H2-1S); a stored edge cannot name the sign edge closer than one ulp.
      Planted reversion: pass the PIECE `(a, b)` instead of the record's support to `_geometry_at_edge` in `draft_windows` — both ends fail.
  C2  A genuine disagreement in the same sliver geometry still refuses: a stored edge 100 us (more than one ulp) from the true edge is refused.
      Planted reversion: an unbounded probe (a tolerance of 10 ms in `jd_ulp_tolerance`'s use) — the case stops refusing.
"""
from __future__ import annotations

import dataclasses
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
_US = timedelta(microseconds=1)

pytestmark = pytest.mark.skipif(not os.environ.get("SE_EPHE_PATH"), reason="needs the pinned Swiss Ephemeris corpus (SE_EPHE_PATH)")


def _jd(t: datetime) -> float:
    return t.timestamp() / 86400.0 + _JD_UNIX_EPOCH


def _dt(jd: float) -> datetime:
    return datetime.fromtimestamp((jd - _JD_UNIX_EPOCH) * 86400.0, tz=UTC)


def _rahu(t: datetime) -> float:
    swe.set_ephe_path(os.environ["SE_EPHE_PATH"])
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.calc_ut(_jd(t), swe.MEAN_NODE, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] % 360.0


def _ketu(t: datetime) -> float:
    return (_rahu(t) + 180.0) % 360.0


def _sign(lonf, t: datetime) -> int:
    return int(lonf(t) // 30.0)


def _edge_after(lonf, t0: datetime) -> tuple[datetime, int]:
    """The first sign change of `lonf` after `t0`: the earliest whole-microsecond datetime in the NEW sign (the true edge the stored one is compared with), and that sign (0-based)."""
    s0 = _sign(lonf, t0)
    t = t0
    while _sign(lonf, t + timedelta(days=5)) == s0:
        t += timedelta(days=5)
    lo, hi = t, t + timedelta(days=5)
    while hi - lo > _US:
        mid = lo + (hi - lo) // 2
        lo, hi = (mid, hi) if _sign(lonf, mid) == s0 else (lo, mid)
    return hi, _sign(lonf, hi)


@pytest.fixture(scope="module")
def node_span():
    """One real sign residence of the mean node: Ketu (target span number, true ingress, true egress) and Rahu's own, from the same sky."""
    start = datetime(2010, 1, 1, tzinfo=UTC)
    k_in, k_sign = _edge_after(_ketu, start)
    k_out, _ = _edge_after(_ketu, k_in + timedelta(days=1))
    r_in, r_sign = _edge_after(_rahu, k_in - timedelta(days=1))
    r_out, _ = _edge_after(_rahu, r_in + timedelta(days=1))
    # preconditions of the oracle (the pinned ephemeris makes them deterministic): the node is retrograde, and Rahu / Ketu cross at the same JD cell
    assert (_ketu(k_in + timedelta(days=1)) - _ketu(k_in) + 180.0) % 360.0 - 180.0 < 0.0, "the mean node must be retrograde"
    assert abs(r_in - k_in) <= 2 * _US and abs(r_out - k_out) <= 2 * _US, (r_in - k_in, r_out - k_out)
    assert (r_sign - k_sign) % 12 == 6
    return k_in, k_out, k_sign + 1, r_in, r_out, r_sign + 1


def _node(rid, agent, lonf, lo, hi, span_no):
    rec = _rec(rid, path="P3", kind="house_span", target=f"span:{span_no}", agent=agent, longitude_at=lonf)
    return dataclasses.replace(rec, supports=((lo, hi),))


def _run(recs):
    return _draft(recs, _rows_declared)[0][0]


@pytest.mark.parametrize("end", ["start", "end"])
def test_a_node_record_edge_within_one_ulp_is_not_refused_when_a_neighbour_cuts_a_one_ulp_sliver(node_span, end):
    k_in, k_out, k_no, r_in, r_out, r_no = node_span
    ulp = ws.jd_ulp_tolerance(k_in)
    assert timedelta(microseconds=40) < ulp < timedelta(microseconds=60), ulp                # a 40 us sliver is shorter than 2 ulp, and the 30 us shift is inside one ulp
    sliver = timedelta(microseconds=40)
    shift = timedelta(microseconds=30)
    if end == "start":
        # Ketu's stored ingress is 30 us EARLY (the true edge is 30 us into the support); Rahu's support starts 40 us after Ketu's: the piece [ketu_in-30, +10) is 40 us
        ketu = _node("ketu", "ketu", _ketu, k_in - shift, k_out, k_no)
        rahu = _node("rahu", "rahu", _rahu, k_in - shift + sliver, r_out, r_no)
    else:
        # Ketu's stored egress is 30 us LATE; Rahu's support ends 40 us before Ketu's: the piece [ketu_out+30-40, ketu_out+30) is 40 us
        ketu = _node("ketu", "ketu", _ketu, k_in, k_out + shift, k_no)
        rahu = _node("rahu", "rahu", _rahu, r_in, k_out + shift - sliver, r_no)
    w = _run([ketu, rahu])
    assert w.members == 2 and w.score is not None


def test_a_node_record_edge_beyond_one_ulp_still_refuses_in_the_same_sliver_geometry(node_span):
    k_in, k_out, k_no, r_in, r_out, r_no = node_span
    ketu = _node("ketu", "ketu", _ketu, k_in - timedelta(microseconds=60), k_out, k_no)          # 60 us early: more than one ulp (42 us)
    rahu = _node("rahu", "rahu", _rahu, k_in - timedelta(microseconds=20), r_out, r_no)          # within one ulp: only Ketu's edge is wrong; the piece between is 40 us
    with pytest.raises(SweepRefusal, match=r"record ketu: .*support/geometry disagree"):
        _run([ketu, rahu])
