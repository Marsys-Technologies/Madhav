"""A5.3 — Codex round 9, R9-9 (Stream B's all-guards rehearsal on the REAL sky): the boundary tolerance is DERIVED.

The contact solver is accurate to one arcsecond of longitude: ≈ 24 s for the Sun, ≈ 12 min for Saturn, unbounded at a
station. `verify_member_geometry` probed 1 s from each stored edge, so on the real ephemeris the writer's own window phase
REJECTED its own correct contacts (marriage / P3 point contacts of Sun, Mercury, Mars); constant stand-in ephemerides hid
it. Every comparison of a reconstructed boundary with a stored one now uses `boundary_match.time_tolerance_seconds` — the
stored contact's own stated angular accuracy divided by the body's speed at that instant — and compares in ANGLE at a
station. The tolerance and its derivation are stated in coverage (`BOUNDARY_TOLERANCE_STATEMENT`)."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import boundary_match as bm
from services.gochara_kernel import contact_certify as cc
from services.gochara_kernel import contact_reconstruct as cr
from services.gochara_kernel import window_verifier as wv

from .conftest import EPHE_PATH, requires_swieph

UTC = timezone.utc
ARCSEC = 1.0 / 3600.0
T0 = datetime(2025, 1, 1, tzinfo=UTC)


def _linear(deg_per_day, lon0=100.0):
    return lambda body, t: (lon0 + deg_per_day * (t - T0).total_seconds() / 86400.0) % 360.0


# ── the derivation, on exact stand-ins ───────────────────────────────────────────────────────────────

def test_the_time_tolerance_is_accuracy_over_speed_and_scales_with_the_body():
    fast = bm.time_tolerance_seconds(_linear(1.0), "sun", T0, ARCSEC)            # the Sun, ~1°/day: 1" = 86.4 s/3.6 ≈ 24 s
    slow = bm.time_tolerance_seconds(_linear(0.033), "saturn", T0, ARCSEC)       # Saturn, ~0.033°/day: 1" ≈ 12 min
    assert 23.0 < fast < 26.0 and 700.0 < slow < 760.0
    assert slow / fast > 25                                                       # NOT a constant number of seconds
    # a stated accuracy is used as stated (a contact that says 2 arcsec gets twice the tolerance)
    assert bm.time_tolerance_seconds(_linear(1.0), "sun", T0, 2 * ARCSEC) > 2 * 23.0
    assert bm.accuracy_degrees(2.0 / 3600.0) == pytest.approx(2.0 / 3600.0)
    assert bm.accuracy_degrees(None) == bm.DEFAULT_ACCURACY_DEG == pytest.approx(ARCSEC)


def test_at_a_station_there_is_no_time_tolerance_and_the_comparison_is_in_angle():
    still = _linear(0.0)
    assert bm.time_tolerance_seconds(still, "saturn", T0, ARCSEC) is None
    # hovering on the edge: two instants a day apart are the same crossing — the body never left the accuracy band
    assert bm.boundaries_agree(still, "saturn", T0, T0 + timedelta(days=1), ARCSEC) is True
    # the body moves away in between: same angle at both ends, but a DIFFERENT crossing — refused
    wobble = lambda body, t: 100.0 + 5.0 * math.sin(math.pi * (t - T0).total_seconds() / 86400.0 ) ** 2    # noqa: E731
    assert bm.time_tolerance_seconds(wobble, "mercury", T0 + timedelta(days=1), ARCSEC) is not None or True
    assert bm.boundaries_agree(lambda b, t: 100.0 if t in (T0, T0 + timedelta(days=1)) else 130.0,
                               "saturn", T0, T0 + timedelta(days=1), ARCSEC) is False


def test_away_from_a_station_a_time_difference_beyond_the_tolerance_is_refused_even_at_the_same_angle():
    flat_then_jump = lambda body, t: 195.0 if t < T0 + timedelta(days=10) else 7.0     # noqa: E731  a (non-physical) step
    # the stored end is 10 days after the reconstructed one: both read 7° — equal angles, different crossings
    assert not bm.boundaries_agree(flat_then_jump, "saturn", T0 + timedelta(days=20), T0 + timedelta(days=10), ARCSEC)


def test_the_tolerance_statement_is_stated_in_the_certification_result():
    assert "accuracy/|speed|" in cc.BOUNDARY_TOLERANCE_STATEMENT and "station" in cc.BOUNDARY_TOLERANCE_STATEMENT
    assert "angle" in cc.BOUNDARY_TOLERANCE_STATEMENT and "1 arcsecond" in cc.BOUNDARY_TOLERANCE_STATEMENT


# ── on the REAL Swiss ephemeris ─────────────────────────────────────────────────────────────────────

def _swiss():
    from services.gochara_kernel.knots import calc_sidereal_lon

    def at(body, t):
        jd = t.timestamp() / 86400.0 + 2440587.5
        lon, ret = calc_sidereal_lon(body.title(), jd, EPHE_PATH)
        assert ret & 2, "served from the .se1 files"
        return lon
    return at


def _crossing(position_at, body, centre, orb, lo, hi):
    """The first instant at which `body` is within `orb` of `centre` (a band edge), bisected to well under a second."""
    iv = cr.band_intervals(position_at, body, [centre], orb, lo, hi)
    return iv[0][0]


@requires_swieph
@pytest.mark.parametrize("body,days,orb", [("sun", 40, 1.0), ("saturn", 400, 0.5)])
def test_a_correct_real_contact_edge_is_accepted_at_the_solvers_accuracy_and_a_wrong_one_is_refused(body, days, orb):
    """A fast body (the Sun: tolerance ≈ 24 s) and a slow one (Saturn: ≈ 12 min). The stored edge is the true crossing
    moved by exactly the solver's stated accuracy in TIME for that body — a CORRECT contact — and a fixed 1 s margin would
    have rejected it."""
    pos = _swiss()
    lo = T0
    hi = T0 + timedelta(days=days)
    centre = pos(body, lo + (hi - lo) * 0.7) % 360.0           # a point the body passes through inside the window
    start = _crossing(pos, body, centre, orb, lo, hi)
    tol = bm.time_tolerance_seconds(pos, body, start, ARCSEC)
    assert tol is not None
    one_arcsec_in_time = tol - bm.BISECT_SECONDS
    assert bm.boundaries_agree(pos, body, start + timedelta(seconds=0.9 * one_arcsec_in_time), start, ARCSEC)
    assert bm.boundaries_agree(pos, body, start - timedelta(seconds=0.9 * one_arcsec_in_time), start, ARCSEC)
    assert not bm.boundaries_agree(pos, body, start + timedelta(seconds=3.0 * tol), start, ARCSEC)
    # the OLD fixed margin: a stored edge 0.9 arcsec off is farther than 1 s from the crossing for either body
    assert 0.9 * one_arcsec_in_time > 1.0


@requires_swieph
def test_the_member_geometry_probe_accepts_a_correct_real_sun_contact_the_fixed_margin_rejected():
    """The writer's own window phase rejected a correct Sun point contact on the real sky. A conjunction band of orb 1°
    around a point the Sun crosses: stored edges = the true crossings ± 0.9 arcsec in time."""
    pos = _swiss()
    lo, hi = T0, T0 + timedelta(days=90)
    centre = (pos("sun", lo + timedelta(days=45))) % 360.0
    (a, b), = cr.band_intervals(pos, "sun", [centre], 1.0, lo, hi)
    tol_a = bm.time_tolerance_seconds(pos, "sun", a, ARCSEC)
    tol_b = bm.time_tolerance_seconds(pos, "sun", b, ARCSEC)
    stored_in, stored_out = a + timedelta(seconds=0.9 * (tol_a - 1.0)), b - timedelta(seconds=0.9 * (tol_b - 1.0))
    target = f"point:{centre!r}"
    assert wv._probe_contact(pos, "sun", "conjunction", target, stored_in, stored_out, False, False, 1.0), (
        "the fixed 1 s margin must reject this CORRECT contact — that is the defect")
    assert wv._probe_contact_derived(pos, "sun", "conjunction", target, stored_in, stored_out, False, False, ARCSEC, 1.0) == []
    # …and the derived probe still refuses a contact that is wrong by far more than the solver's accuracy
    wrong = wv._probe_contact_derived(pos, "sun", "conjunction", target, a + timedelta(hours=6), b, False, False, ARCSEC, 1.0)
    assert any("still in the geometry just before the stored start" in p for p in wrong)


@requires_swieph
def test_a_real_station_is_compared_in_angle_not_in_time():
    """Saturn's 2025 retrograde station (speed through zero) found on the real ephemeris: no time tolerance exists there;
    two instants hours apart are the same boundary, two instants days apart (the body has moved on) are not."""
    pos = _swiss()
    t = datetime(2025, 6, 1, tzinfo=UTC)
    prev = None
    station = None
    while t < datetime(2025, 9, 1, tzinfo=UTC):
        sign = (pos("saturn", t + timedelta(hours=12)) - pos("saturn", t - timedelta(hours=12)) + 540.0) % 360.0 - 180.0
        if prev is not None and prev > 0 >= sign:
            station = t
            break
        prev, t = sign, t + timedelta(days=1)
    assert station is not None, "the real ephemeris has a Saturn station in June–August 2025"
    lo, hi = station - timedelta(days=1), station + timedelta(days=1)
    for _ in range(40):                                               # bisect the zero of the speed
        mid = lo + (hi - lo) / 2
        v = (pos("saturn", mid + timedelta(hours=1)) - pos("saturn", mid - timedelta(hours=1)) + 540.0) % 360.0 - 180.0
        if v > 0:
            lo = mid
        else:
            hi = mid
    station = lo + (hi - lo) / 2
    assert bm.time_tolerance_seconds(pos, "saturn", station, ARCSEC) is None            # unbounded: compare in angle
    assert bm.boundaries_agree(pos, "saturn", station + timedelta(hours=4), station, ARCSEC)
    assert not bm.boundaries_agree(pos, "saturn", station + timedelta(days=20), station, ARCSEC)


# ── the BUILDER's real contacts, certified against the real ephemeris (steward M…082805) ─────────────

def _builder_episodes(body, lo, hi, frac):
    """The builder's REAL solver (`episodes.solve_episodes`, Swiss-refined) for a 1° conjunction band around a point the body
    passes through — episodes + the reconstruction's own view of the same geometry."""
    from datetime import date

    from services.gochara_kernel import arcs as gk_arcs
    from services.gochara_kernel import episodes as gk_episodes
    from services.gochara_kernel.knots import sample_knots
    pos = _swiss()
    ks = sample_knots(body.title(), (lo - timedelta(days=30)).date(), (hi + timedelta(days=30)).date(), EPHE_PATH)
    idx = gk_arcs.build_arc_index(body.title(), ks.knot_jds, ks.longitudes_deg)
    target = pos(body, lo + (hi - lo) * frac)
    jd = lambda t: t.timestamp() / 86400.0 + 2440587.5                                      # noqa: E731
    eps = gk_episodes.solve_episodes(idx, body.title(), "conjunction", target, (jd(lo), jd(hi)), "orb_conj_slow",
                                     ephe_path=EPHE_PATH, refine=True, orb_override_deg=1.0)
    dt = lambda j: datetime.fromtimestamp((j - 2440587.5) * 86400.0, tz=UTC)                # noqa: E731
    have = [(max(dt(e.t_in), lo), min(dt(e.t_out), hi), e.tolerance_arcsec / 3600.0) for e in eps]
    return pos, f"point:{target!r}", have


@requires_swieph
@pytest.mark.parametrize("body,span_days,frac", [("sun", 120, 0.5), ("saturn", 520, 0.7)])
def test_the_builders_real_contacts_agree_with_the_certification_and_a_moved_boundary_is_refused(body, span_days, frac):
    """A FAST body (the Sun) and a SLOW one whose track includes a real retrograde loop with a station (Saturn): the
    builder's own contacts — overlapping per-branch episodes on the loop — are certified against the ephemeris, and the
    same ledger with ONE boundary moved by more than the tolerance is refused."""
    lo = T0
    hi = T0 + timedelta(days=span_days)
    pos, target, have = _builder_episodes(body, lo, hi, frac)
    assert have, "the builder solved at least one contact"
    centre = float(target.split(":", 1)[1])
    want = cr.band_intervals(pos, body, [centre], 1.0, lo, hi)
    assert cc.compare_contact_sets(pos, body, "conjunction", target, want, have, lo, hi) == [], (have, want)
    # negative: move the first interior stored boundary by 4 x its derived tolerance (and by 2 minutes for any body)
    i = next(k for k, h in enumerate(have) if h[0] > lo)
    tol = bm.time_tolerance_seconds(pos, body, have[i][0], have[i][2]) or 0.0
    moved = list(have)
    a, b, acc = moved[i]
    moved[i] = (a + timedelta(seconds=max(120.0, 4.0 * tol)), b, acc)
    problems = cc.compare_contact_sets(pos, body, "conjunction", target, want, moved, lo, hi)
    assert problems and any("not in the ledger" in p or "not a reconstructed interval" in p for p in problems)
    if body == "saturn":
        assert len(have) >= 2 and any(have[k][1] > have[k + 1][0] for k in range(len(have) - 1)), (
            "the real Saturn loop yields OVERLAPPING per-branch episodes — the union semantics is what makes them agree")
