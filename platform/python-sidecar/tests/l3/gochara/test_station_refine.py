"""STATION-FIX — a station row labelled `swiss_refined` (1e-9 d) is REFINED against the ephemeris, and the station has ONE instant.

THE DEFECT: the sky-event substrate stored every station at the root of the SPLINE derivative (daily noon knots) under solver_method 'swiss_refined' /
delta_t 1e-9 d / 'swiss_bisect_tol_1e-9d', though no Swiss refinement ran for stations. Measured on the pinned files (1998-2012): the spline instant is up to 16.2 s
(Mercury; 0.7-2.7 s for the others) from the ephemeris station, i.e. the label overstated the precision by about five orders of magnitude. The database REQUIRES
the label for station rows (migration 1153: event_kind <> 'station' OR solver_method = 'swiss_refined'), so the fix refines, it does not relabel.

THE FIX: `knots.refine_station` finds the ephemeris station: it bisects the SIGN of the Swiss longitudinal speed in a ±1 d bracket to 1e-4 d and then fits the speed
around it (the speed has a noise of about 1e-8 deg/day, so its sign is not a usable root test below about 1e-6 d: measured, it flips several times within ±1e-6 d of a
station) and stores the fitted root with ITS OWN uncertainty (3 sigma) as delta_t instead of a nominal 1e-9 d. `build_arc_index(station_refiner=...)` replaces the spline
stations BEFORE the boundaries are cut, so the stored row, the arc/segment boundaries, the episode station branch and the seam junctions all use the SAME instant.

Real pinned files (skip NOT_RUN without them, a hard failure under GOCHARA_SE1_REQUIRE=1); no database.
"""
from __future__ import annotations

from datetime import date

import pytest

from services.gochara_kernel import arcs as gk_arcs
from services.gochara_kernel import contacts as gk_contacts
from services.gochara_kernel import knots as gk_knots
from services.gochara_kernel.knots import StationRefinementError, refine_station, sample_knots, station_refiner

from .conftest import EPHE_PATH, requires_swieph
from .test_a53_substrate_store import CID, CONVENTION_ROW, FakeConn

pytestmark = requires_swieph

START, END = date(1998, 1, 1), date(2008, 1, 1)
BODIES = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_cache: dict = {}


def _knots(body):
    if body not in _cache:
        _cache[body] = sample_knots(body, START, END, EPHE_PATH)
    return _cache[body]


def _speed(body, jd):
    return gk_knots.calc_sidereal_lon_speed(body, jd, EPHE_PATH)[1]


def _independent_vertex(body, jd0):
    """The test's OWN estimator: a QUARTIC fitted to the LONGITUDE over a WIDER window (±0.15 d, 301 points) than the code's cubic over ±0.05 d; its stationary
    point is the root of the fitted derivative nearest the spline station. (A parabola alone is biased by the cubic term: measured, about 2.8e-6 d.)"""
    import numpy as np
    xs = np.linspace(-0.15, 0.15, 301)
    ys = np.array([gk_knots.calc_sidereal_lon(body, jd0 + float(x), EPHE_PATH)[0] for x in xs])
    ys = np.degrees(np.unwrap(np.radians(ys)))
    c4, c3, c2, c1, _c0 = np.polyfit(xs, ys, 4)
    roots = [r.real for r in np.roots([4.0 * c4, 3.0 * c3, 2.0 * c2, c1]) if abs(r.imag) < 1e-12]
    return jd0 + min(roots, key=abs)


@pytest.mark.parametrize("body", BODIES)
def test_refined_stations_are_the_swiss_speed_root_to_the_stated_tolerance(body):
    ks = _knots(body)
    spline = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)
    refined = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg, station_refiner=station_refiner(body, EPHE_PATH))
    assert refined.station_refined and len(refined.stations) == len(spline.stations) > 0
    assert refined.stations_spline == tuple(spline.stations)
    worst = 0.0
    fixes = [station_refiner(body, EPHE_PATH)(s0) for s0 in spline.stations[:6]]
    for fix, r, s0, lon, dt in list(zip(fixes, refined.stations, spline.stations, refined.station_lons_deg, refined.station_delta_t_days))[:6]:
        assert fix.jd == r and fix.delta_t_days == dt, "the refiner is deterministic"
        truth = _independent_vertex(body, s0)
        assert abs(r - truth) <= dt + 1e-6, f"{body}: refined {r} vs the longitude-vertex estimate {truth}: {abs(r - truth) * 86400:.4f} s (stated 3 sigma {dt * 86400:.4f} s)"
        assert 1e-9 < dt < 1e-4, f"the stored uncertainty is the fit's own, not the nominal 1e-9 d: {dt}"
        worst = max(worst, abs(s0 - r) * 86400.0)
        assert abs((lon - gk_knots.calc_sidereal_lon(body, r, EPHE_PATH)[0] + 180.0) % 360.0 - 180.0) < 1e-9          # the stored longitude is the ephemeris one at that instant
    assert worst < 20.0, "the spline error is of the order measured (<= 16.2 s Mercury)"


@pytest.mark.parametrize("body", ("Saturn", "Jupiter"))
def test_the_stored_uncertainty_covers_what_the_ephemeris_longitude_and_speed_disagree_on(body):
    """For the slow planets Swiss's speed root differs from the stationary point of its own longitudes by up to ~5e-6 d (0.4 s), and moves by ~0.1 s with the fit
    window alone (the speed noise is not white). The stored delta_t must cover that disagreement. Re-derived HERE from the fix's own grid centre: the test samples the
    speed itself, fits its own quadratics over each window, and compares every root with the stored station."""
    import numpy as np
    ks = _knots(body)
    spline = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)
    checked = 0
    for s0 in spline.stations[:8]:
        fix = station_refiner(body, EPHE_PATH)(s0)
        wide = max(gk_knots.STATION_SPEED_WINDOWS_DAYS)
        xs = np.linspace(-wide, wide, gk_knots.STATION_SAMPLE_POINTS)
        sp = np.array([gk_knots.calc_sidereal_lon_speed(body, fix.centre_jd + float(x), EPHE_PATH)[1] for x in xs])
        worst = 0.0
        for w in gk_knots.STATION_SPEED_WINDOWS_DAYS:
            m = np.abs(xs) <= w + 1e-12
            q2, q1, q0 = np.polyfit(xs[m], sp[m], 2)
            roots = [t.real for t in np.roots([q2, q1, q0]) if abs(t.imag) < 1e-12]
            worst = max(worst, abs(min(roots, key=abs) - (fix.jd - fix.centre_jd)))
        assert abs(worst - fix.speed_spread_days) < 1e-9, "the reported spread is the test's own"
        assert fix.delta_t_days >= worst - 1e-9, f"{body}: a speed root is {worst * 86400:.3f} s from the stored station, delta_t covers only {fix.delta_t_days * 86400:.3f} s"
        assert fix.delta_t_days >= gk_knots.STATION_SIGMA_K * fix.sigma_longitude_days - 1e-9
        checked += 1
    assert checked >= 5


def test_the_spline_station_really_is_off_by_seconds_so_the_refinement_is_not_a_no_op():
    """Mercury, 1998-2008: some station moves by more than a second (the measured spline error). Guards the 'refinement does nothing' mutation."""
    ks = _knots("Mercury")
    refined = gk_arcs.build_arc_index("Mercury", ks.knot_jds, ks.longitudes_deg, station_refiner=station_refiner("Mercury", EPHE_PATH))
    shifts = [abs(r - s) * 86400.0 for r, s in zip(refined.stations, refined.stations_spline)]
    assert max(shifts) > 1.0 and max(shifts) < 20.0, shifts


def test_one_station_instant_arcs_segments_and_the_episode_station_branch_use_the_refined_value():
    ks = _knots("Mercury")
    idx = gk_arcs.build_arc_index("Mercury", ks.knot_jds, ks.longitudes_deg, station_refiner=station_refiner("Mercury", EPHE_PATH))
    boundaries = {seg.start_jd for seg in idx.segments} | {seg.end_jd for seg in idx.segments}
    for st in idx.stations:
        assert st in boundaries, "a segment boundary IS the refined station"
    for st in idx.stations_spline:
        assert st not in boundaries or st in idx.stations, "no segment boundary stays at a replaced spline station"
    flagged = [seg for seg in idx.segments if seg.station_bounded[0] or seg.station_bounded[1]]
    assert flagged and all((seg.start_jd in idx.stations) == seg.station_bounded[0] for seg in idx.segments if seg.start_jd != idx.knot_jds[0])


def test_spans_move_only_at_station_seams_and_by_at_most_the_measured_spline_error_contact_roots_are_unchanged():
    """Contact identity comes from the ORDERED exact-root list: count, order and instants of every boundary root are unchanged; only segment ends at
    stations move, each by the (measured) spline error."""
    for body in ("Saturn", "Mercury"):
        ks = _knots(body)
        old = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)
        new = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg, station_refiner=station_refiner(body, EPHE_PATH))
        assert len(old.segments) == len(new.segments) and len(old.arcs) == len(new.arcs)
        moved = 0
        for a, b in zip(old.segments, new.segments):
            for x, y, flag in ((a.start_jd, b.start_jd, a.station_bounded[0]), (a.end_jd, b.end_jd, a.station_bounded[1])):
                if flag:
                    assert abs(x - y) * 86400.0 < 20.0
                    moved += x != y
                else:
                    assert x == y, "a non-station boundary never moves"
        assert moved > 0
        for relation in gk_contacts.BOUNDARY_RELATIONS:
            ro = gk_contacts.find_boundary_roots(old, body, relation, EPHE_PATH, refine=True)
            rn = gk_contacts.find_boundary_roots(new, body, relation, EPHE_PATH, refine=True)
            assert [r.level_deg for r in ro] == [r.level_deg for r in rn], f"{body}: the ordered contact list (its ordinals) is unchanged"
            assert max(abs(a.exact_jd - b.exact_jd) for a, b in zip(ro, rn)) < 1e-8, f"{body}: contact instants unchanged (the production mode: Swiss-refined roots; the unrefined spline roots carry a 1-arcsec solver tolerance and move by seconds with the bracket, so they are not the comparison)"


def test_a_spline_station_that_is_not_an_ephemeris_station_is_refused_not_papered_over():
    with pytest.raises(StationRefinementError, match="not an ephemeris station"):
        refine_station("Saturn", 2455000.5 + 200.0, EPHE_PATH)                    # mid-direct-motion jd: the speed has one sign across the bracket


def test_a_refiner_that_moves_a_station_too_far_or_out_of_order_is_refused():
    ks = _knots("Mars")
    with pytest.raises(ValueError, match="moved"):
        gk_arcs.build_arc_index("Mars", ks.knot_jds, ks.longitudes_deg, station_refiner=lambda jd: (jd + 5.0, 10.0, 1e-6))
    # a synthetic trajectory with two stations 1.2 d apart (f' = k (t-4)(t-5.2)); a refiner that moves them 0.8 d towards each other reorders them
    import numpy as np
    knots = [2460000.0 + i for i in range(10)]
    poly = np.polynomial.Polynomial.fromroots([4.0, 5.2]).integ()
    lons = [100.0 + 0.05 * float(poly(i)) for i in range(10)]
    plain = gk_arcs.build_arc_index("Mars", knots, lons)
    assert len(plain.stations) == 2
    moves = iter([0.8, -0.8])
    with pytest.raises(ValueError, match="strictly ordered"):
        gk_arcs.build_arc_index("Mars", knots, lons, station_refiner=lambda jd: (jd + next(moves), 10.0, 1e-6))


def test_the_substrate_refuses_an_index_with_spline_stations_and_stores_the_refined_instant_otherwise():
    from services.gochara_kernel.substrate import SkyEventStore
    ks = _knots("Mars")
    unrefined = gk_arcs.build_arc_index("Mars", ks.knot_jds, ks.longitudes_deg)
    with pytest.raises(ValueError, match="without a station refiner"):
        SkyEventStore(FakeConn({"convention": [CONVENTION_ROW]})).build_boundary_substrate("Mars", index=unrefined, refine=False, convention_id=CID)
    refined = gk_arcs.build_arc_index("Mars", ks.knot_jds, ks.longitudes_deg, station_refiner=station_refiner("Mars", EPHE_PATH))
    conn = FakeConn({"convention": [CONVENTION_ROW]})
    counts = SkyEventStore(conn).build_boundary_substrate("Mars", index=refined, refine=False, convention_id=CID)
    assert counts["stations"] == len(refined.stations) > 0
    stored = [p for sql, p in conn.statements if "INSERT INTO public.ka_gochara_sky_event" in sql and p[4] == "station"]
    assert len(stored) == len(refined.stations)
    from services.gochara_kernel.substrate import jd_to_utc
    assert [p[6] for p in stored] == [jd_to_utc(j) for j in refined.stations], "the stored instant IS the arc index's station (ONE instant)"
    assert [p[10] for p in stored] == [float(d) for d in refined.station_delta_t_days] and all(p[11] == "swiss_speed_root_fit_3sigma" for p in stored)
    assert all(p[10] != 1e-9 for p in stored), "no nominal 1e-9 d claim"


def test_every_production_arc_index_build_that_feeds_station_rows_or_the_record_phase_passes_the_station_refiner():
    """The ONE-instant rule is only as good as its call sites: the substrate (which stores the stations) and the v5 writer's record-phase arc cache (which splits
    arcs and seams) must both build their index with the refiner. Checked on the syntax tree, so a new unrefined build in either file fails here."""
    import ast
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[3]
    for rel in ("services/gochara_kernel/substrate.py", "pipeline/orchestrator/writers/ka_gochara_v5.py"):
        tree = ast.parse((root / rel).read_text())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) == "build_arc_index"]
        assert calls, f"{rel}: expected a build_arc_index call"
        for c in calls:
            assert any(k.arg == "station_refiner" for k in c.keywords), f"{rel}:{c.lineno}: build_arc_index without station_refiner="
