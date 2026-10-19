"""J-4c — the minted in-orb span edges (t_in / t_out) sit on the true band edge to within the contact's own stated delta_lambda (F-INVENTED / F-ANOMALY).

THE DEFECT: `record_store._in_orb_span_around_root` located each band edge on the arc-index SPLINE and stopped at the first bisection midpoint within the index
tolerance (1 arcsec of longitude), never polishing against the ephemeris, while the contact states delta_lambda = 1 arcsec. Measured on the J-3c measuring build
(three real contacts, jupiter / mars / mercury at roughly 0.23 / 0.73 / 2.1 degrees a day): the minted edge missed the ephemeris band edge by 1.06 to 1.47 arcsec. The
certifier's independent reconstruction is within 0.05 arcsec of the ephemeris, so it was right to refuse them: 3 `invented` + 3 `anomaly` sink records.

THE FIX: every edge the spline locates is Swiss-polished with the kernel's own refinement helper (`contacts._refine_root` -> `swiss_bisect`), inside the monotone piece
the edge lies in. No certifier tolerance is touched (N.8: the gate at zero is the correct detector).

Oracles (no golden capture; the reference is NOT the code under test): the band edge is the instant the body is exactly `orb` degrees (the 1-degree aspect/conjunction orb,
convention.ORB_TABLE) from the ray level, found here by an INDEPENDENT bisection straight on pyswisseph (sidereal Lahiri, SWIEPH) - no arc index, no kernel helper. The
certifier is `contact_certify._compare_sink_all`, fed the ledger exactly as `certify_contact_geometry` feeds it (clipped to the horizon, the contact's stated accuracy).
The targets are SYNTHETIC ray levels chosen only because the pre-fix edge misses 1 arcsec there; they are not any chart's natal point.

Real pinned files (skip NOT_RUN without them, a hard failure under GOCHARA_SE1_REQUIRE=1); no database.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.gochara_kernel import boundary_match as bm
from services.gochara_kernel import contact_certify as cc
from services.gochara_kernel import record_store as rs

from .conftest import EPHE_PATH, requires_swieph
from .test_c49_wrap_cut_support import point_edge, position_at, real_index

pytestmark = requires_swieph

UTC = timezone.utc
JD_UNIX = 2440587.5
STATION_SPEED_DEG_PER_DAY = 0.005          # the spline station is up to ~17 s from the ephemeris one (STATION-FIX), i.e. <= ~1e-4 deg/day of speed
DEG_ARCSEC = 3600.0


def _utc(y, m, d):
    return datetime(y, m, d, tzinfo=UTC)


# (label, body, class carrying the edge, synthetic ray target, horizon covering the whole contact, whether the PRE-fix edge is refused by the certifier). One or two cases for each of
# the slow / middle / fast body of the three real spots (jupiter ~0.23, mars ~0.73, mercury ~2.1 degrees a day). The pre-fix misses here are 2.05 / 1.12 (jupiter), 1.20 / 1.10 (mars),
# 1.006 / 1.005 (mercury) arcsec against the stated 1: the certifier's +1 s reconstruction slack still accepts mercury's 1.006 (the real spot was 1.061), so for mercury the control
# shows the miss in arcsec only.
CASES = [
    ("L1-like slow (jupiter)", "jupiter", "marriage", 5.98, (_utc(2007, 10, 15), _utc(2008, 3, 1)), True),
    ("L1-like slow (jupiter)", "jupiter", "marriage", 66.26, (_utc(2007, 10, 15), _utc(2008, 3, 1)), True),
    ("L2-like middle (mars)", "mars", "marriage", 117.9, (_utc(1998, 4, 15), _utc(1998, 6, 15)), True),
    ("L2-like middle (mars)", "mars", "marriage", 205.8, (_utc(1998, 4, 15), _utc(1998, 6, 15)), True),
    ("L3-like fast (mercury)", "mercury", "marriage", 26.22, (_utc(2002, 10, 1), _utc(2002, 12, 31)), False),
    ("L3-like fast (mercury)", "mercury", "marriage", 152.73, (_utc(1999, 2, 20), _utc(1999, 4, 20)), False),
]
IDS = [f"{c[1]}-{c[3]}" for c in CASES]
_SWE_BODY = {"jupiter": "JUPITER", "mars": "MARS", "mercury": "MERCURY"}


def _orb_deg(edge) -> float:
    return float(rs.ORB_TABLE[rs.POINT_ORB_SOURCE[edge.relation]]["orb_max_deg"])


# ── the independent reference: pyswisseph directly, no kernel helper, no arc index ──────────────────────────────────────────────

def _swe_state(body: str, jd: float) -> tuple[float, float]:
    """(sidereal longitude, speed in degrees/day) straight from pyswisseph: Lahiri, SWIEPH backend asserted."""
    import swisseph as swe
    swe.set_ephe_path(EPHE_PATH)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    xx, retflag = swe.calc_ut(jd, getattr(swe, _SWE_BODY[body.lower()]), swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
    assert retflag & 2 and not retflag & 4, f"{body}: ephemeris backend {retflag}"
    return xx[0], xx[3]


def _swe_lon(body: str, jd: float) -> float:
    return _swe_state(body, jd)[0]


def _at_station(body: str, t: datetime) -> bool:
    """A span that meets a station inside the band is closed AT the station (E8-2), not at an orb edge: the ephemeris speed there is ~0."""
    return abs(_swe_state(body, _jd(t))[1]) < STATION_SPEED_DEG_PER_DAY


def _jd(t: datetime) -> float:
    return t.timestamp() / 86400.0 + JD_UNIX


def _signed_sep(body: str, jd: float, level: float) -> float:
    return ((_swe_lon(body, jd) - level + 180.0) % 360.0) - 180.0


def _true_edge_jd(body: str, t: datetime, level: float, orb: float) -> float:
    """The instant, within +-2 days of `t`, the body is exactly `orb` degrees from `level` on the side `t` is on (bisection to ~1e-9 day)."""
    side = 1.0 if _signed_sep(body, _jd(t), level) > 0 else -1.0

    def g(jd):
        return _signed_sep(body, jd, level) - side * orb
    lo, hi = _jd(t) - 2.0, _jd(t) + 2.0
    g_lo, g_hi = g(lo), g(hi)
    assert g_lo * g_hi < 0, f"{body} {t}: the band edge is not bracketed within +-2 days (not an orb edge)"
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        g_mid = g(mid)
        if g_lo * g_mid <= 0:
            hi = mid
        else:
            lo, g_lo = mid, g_mid
    return 0.5 * (lo + hi)


def _edge_error_arcsec(body: str, t: datetime, level: float, orb: float) -> float:
    """How far (arcsec of longitude) the instant `t` is from the band edge: ||separation| - orb|."""
    return abs(abs(_signed_sep(body, _jd(t), level)) - orb) * DEG_ARCSEC


# ── solving ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _solve(case, *, polish: bool, monkeypatch=None):
    _label, body, klass, lam, horizon, _refused = case
    edge = point_edge(klass, "aspect", lam, body)
    idx = real_index(body.title())
    if not polish:       # the pre-fix derivation: the polish's Swiss bracket "cannot be found", so the spline edge stands (the code's own documented fallback)
        def _lost(*_a, **_k):
            raise ValueError("polish disabled (pre-fix control)")
        monkeypatch.setattr(rs, "_refine_root", _lost)
    occs = rs.solve_point_edges([edge], arc_index_for=lambda b: idx, horizon=horizon, ephe_path=EPHE_PATH, refine=True)[id(edge)]
    return edge, sorted(occs, key=lambda o: o.t_in)


def _orb_edges(case, occs):
    """[(label, instant, level)] of every minted edge that is an in-orb band edge (not clipped to the horizon, not closed at a station, which is a segment end and not an orb edge)."""
    _label, body, _klass, _lam, horizon, _refused = case
    out = []
    for o in occs:
        for name, t in (("t_in", o.t_in), ("t_out", o.t_out)):
            if t in horizon or _at_station(body, t):
                continue
            out.append((name, t, o.level_deg))
    return out


def _certify(case, edge, occs):
    """The certifier's sink_all comparison of the ledger (the minted contacts) with its own reconstruction; returns the stretch_sink."""
    _label, body, _klass, _lam, (lo, hi), _refused = case
    target = edge.obj.canonical_target
    want = cc.expected_intervals(position_at, edge.agent, edge.relation, target, lo, hi)
    have = sorted((max(o.t_in, lo), min(o.t_out, hi), bm.accuracy_degrees(o.delta_lambda)) for o in occs)
    sink: list = []
    cc._compare_sink_all(position_at, edge.agent, edge.relation, target, want, have, lo, hi, [], sink)
    return sink


# ── 1. every minted edge is within the stated delta_lambda of the ephemeris band edge ──────────────────────────────────────────────

@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_every_minted_span_edge_is_within_the_stated_delta_lambda_of_the_ephemeris_band_edge(case):
    """The contact states delta_lambda (the index tolerance, 1 arcsec); each minted t_in / t_out must be within it of the instant pyswisseph puts the body `orb` degrees
    from the ray level. The polished edge is in fact far inside it (bisection to 1e-9 day), asserted at a tenth of the stated bound and in time against the independent root."""
    _label, body, _klass, _lam, _horizon, _refused = case
    edge, occs = _solve(case, polish=True)
    orb = _orb_deg(edge)
    edges = _orb_edges(case, occs)
    assert occs and edges, "the case produced no in-orb band edge"
    for o in occs:
        assert o.delta_lambda is not None and o.delta_lambda * DEG_ARCSEC == pytest.approx(1.0)
    for name, t, level in edges:
        err = _edge_error_arcsec(body.title(), t, level, orb)
        assert err <= 0.1, f"{body} {name} {t}: {err:.4f} arcsec from the band edge (stated delta_lambda 1 arcsec)"
        root = _true_edge_jd(body.title(), t, level, orb)
        assert abs(_jd(t) - root) * 86400.0 < 0.5, f"{body} {name} {t}: {abs(_jd(t) - root) * 86400.0:.3f} s from the independent root"


# ── 2. the certifier reads the ledger as agreeing: 0 invented, 0 anomaly ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_the_certifier_emits_no_invented_and_no_anomaly_for_the_minted_contacts(case, monkeypatch):
    """MEASURING_BUILD_CONTRACT MB-2.1 collect mode. Post-fix: every record is a plain `contact`. The pre-fix control (same inputs, polish disabled) is read false by the SAME
    detector - at least one `invented` and one `anomaly` - so the zero above is measured, not assumed (N.8)."""
    edge, occs = _solve(case, polish=True)
    kinds = [r["kind"] for r in _certify(case, edge, occs)]
    assert kinds and set(kinds) == {"contact"}, kinds
    if case[5]:
        edge0, occs0 = _solve(case, polish=False, monkeypatch=monkeypatch)
        kinds0 = [r["kind"] for r in _certify(case, edge0, occs0)]
        assert kinds0.count("invented") >= 1 and kinds0.count("anomaly") >= 1, kinds0


# ── 3. the pre-fix edge really did miss by more than the stated bound on the case; the polish is deterministic and refine=False is untouched ──

@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_the_prefix_edge_misses_the_stated_bound_and_the_polish_is_deterministic(case, monkeypatch):
    _label, body, _klass, _lam, _horizon, _refused = case
    edge, occs = _solve(case, polish=True)
    _e2, occs2 = _solve(case, polish=True)
    assert [(o.t_in, o.t_out, o.t_exact) for o in occs] == [(o.t_in, o.t_out, o.t_exact) for o in occs2]      # same inputs -> same bytes
    _e0, occs0 = _solve(case, polish=False, monkeypatch=monkeypatch)
    orb = _orb_deg(edge)
    worst = max(_edge_error_arcsec(body.title(), t, level, orb) for _n, t, level in _orb_edges(case, occs0))
    assert worst > 1.0, f"the control no longer exhibits the defect ({worst:.3f} arcsec): pick another synthetic target"


def test_refine_false_never_polishes_against_the_ephemeris(monkeypatch):
    """The spline-only path (synthetic curves, no ephemeris) is the old derivation, bit for bit: the Swiss polish is never entered."""
    def _boom(*_a, **_k):
        raise AssertionError("refine=False must not reach the Swiss polish")
    monkeypatch.setattr(rs, "_refine_root", _boom)
    _label, body, klass, lam, horizon, _refused = CASES[0]
    edge = point_edge(klass, "aspect", lam, body)
    idx = real_index(body.title())
    occs = rs.solve_point_edges([edge], arc_index_for=lambda b: idx, horizon=horizon, refine=False)[id(edge)]
    assert occs
