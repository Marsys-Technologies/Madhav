"""ND-P2-20261005 rules 1-2, BUILDER side — the near-miss geometry and its pure helpers (`services.gochara_kernel.near_miss`), no database.

A NEAR-MISS is a complete, rootless point-contact stretch with positive clearance: the body turns round at a station inside the admission band of
a ray level and leaves without reaching the level. These tests drive the builder's OWN detection (the arc index) with exact synthetic curves and
compare its bounds with the INDEPENDENT reconstruction that is already on main (`contact_certify.expected_intervals`: hourly samples and
bisection, no arc index) — bounds, the 0/360 wrap, both horizon edges, full-domain ordinals, the global clearance over several stations, and the
named refusals for unresolved geometry. The writer and the storage are in test_d1_near_miss_storage.py."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import arcs as gk_arcs
from services.gochara_kernel import contact_certify as cc
from services.gochara_kernel import inventory as inv
from services.gochara_kernel import near_miss as nm

UTC = timezone.utc
T0 = datetime(2026, 3, 1, tzinfo=UTC)
DAY = timedelta(days=1)
JD0 = 2440587.5
ORB = 1.0
CONV = "sha256:" + "cd" * 32
EDGE = math.sqrt(35.0)              # 0.3 + 0.02 d^2 = 1 at d = +-5.9161 days


def _jd(t):
    return t.timestamp() / 86400.0 + JD0


def index_of(fn, lo_days=-60, hi_days=60, step=0.25):
    """The builder's arc index over [T0 + lo, T0 + hi], knots every 6 hours, from an exact curve fn(body, t) (wrapped degrees)."""
    n = int(round((hi_days - lo_days) / step))
    ts = [T0 + timedelta(days=lo_days + k * step) for k in range(n + 1)]
    return gk_arcs.build_arc_index("Venus", [_jd(t) for t in ts], [fn("venus", t) for t in ts])


def graze(level, clearance=0.3, side=1, a=0.02, centre=0.0):
    def f(body, t):
        d = (t - T0).total_seconds() / 86400.0 - centre
        return (level + side * (clearance + a * d * d)) % 360.0
    return f


def obj(level, relation="conjunction"):
    return nm.NearMissObject("venus", relation, f"point:{level}", nm.orb_policy_id("orb_conj_slow", ORB), CONV)


WIDE = (T0 - 50 * DAY, T0 + 50 * DAY)


def days(t):
    return (t - T0).total_seconds() / 86400.0


# ── the stretch: bounds, clearance, proximity ───────────────────────────────────────────────────────────────────────────────

def test_a_near_miss_is_found_with_the_whole_stretch_its_clearance_and_its_proximity():
    f = graze(120.0)
    (found,) = nm.solve_object_near_misses(obj=obj(120.0), index=index_of(f), orb_deg=ORB, horizon=WIDE, position_at=f)
    assert abs(days(found.t_in) + EDGE) < 1e-3 and abs(days(found.t_out) - EDGE) < 1e-3
    assert abs(days(found.t_closest)) < 1e-3 and abs(found.clearance_deg - 0.3) < 1e-6
    assert abs(found.proximity - 0.7) < 1e-6 and found.ordinal == 1 and found.level_deg == 120.0
    assert found.solver_method == "swiss_refined_extremum" and found.delta_t is not None and found.delta_t <= nm.CLOSEST_BRACKET_DAYS
    assert "clipped_by_horizon" not in found.coverage and found.coverage["stations"] == 1 and found.coverage["side"] == 1


def test_the_builders_bounds_equal_the_independent_reconstruction():
    f = graze(120.0)
    (found,) = nm.solve_object_near_misses(obj=obj(120.0), index=index_of(f), orb_deg=ORB, horizon=WIDE, position_at=f)
    ((a, b),) = cc.expected_intervals(f, "venus", "conjunction", "point:120.0", *WIDE)
    assert abs((found.t_in - a).total_seconds()) < 120 and abs((found.t_out - b).total_seconds()) < 120
    g = cc.classify_graze(f, "venus", "conjunction", "point:120.0", (a, b), *WIDE)
    assert g is not None and abs(g["closest_approach_deg"] - found.clearance_deg) < 1e-3


def test_a_stretch_in_which_the_ray_level_is_crossed_is_a_contact_and_never_a_near_miss():
    def crossing(body, t):                       # the station sits 0.5 deg BELOW the ray and the ray is crossed either side
        d = (t - T0).total_seconds() / 86400.0
        return (120.0 - 0.5 + 0.02 * d * d) % 360.0
    assert nm.solve_object_near_misses(obj=obj(120.0), index=index_of(crossing), orb_deg=ORB, horizon=WIDE, position_at=crossing) == []
    assert nm.rootless_stretches(index_of(crossing), [120.0], ORB) == []


def test_a_stationless_body_never_has_a_near_miss():
    def linear(body, t):
        return (119.0 + 0.02 * (t - T0).total_seconds() / 86400.0) % 360.0      # inside the band for the whole domain, never turning
    assert nm.rootless_stretches(index_of(linear), [120.0], ORB) == []


def test_the_clearance_is_the_global_minimum_over_every_station_of_the_stretch():
    def w_shape(body, t):                        # three stations inside the band: minima 0.2 at +-4.472 d, a local maximum 0.4 at 0
        d = (t - T0).total_seconds() / 86400.0
        return (120.0 + 0.4 + 0.0005 * d ** 4 - 0.02 * d * d) % 360.0
    (found,) = nm.solve_object_near_misses(obj=obj(120.0), index=index_of(w_shape, step=0.125), orb_deg=ORB, horizon=WIDE, position_at=w_shape)
    assert found.coverage["stations"] == 3 and abs(found.clearance_deg - 0.2) < 1e-4
    assert abs(abs(days(found.t_closest)) - math.sqrt(20.0)) < 1e-2
    assert abs(days(found.t_in) + math.sqrt(60.0)) < 1e-2 and abs(days(found.t_out) - math.sqrt(60.0)) < 1e-2


def test_only_the_point_relations_have_near_misses():
    f = graze(120.0)
    span = nm.NearMissObject("venus", "residence", "span:5", "x", CONV)
    assert nm.solve_object_near_misses(obj=span, index=index_of(f), orb_deg=ORB, horizon=WIDE) == []


# ── the 0/360 wrap ───────────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level, side", [(0.6, -1), (359.5, 1), (0.0, 1), (0.0, -1)])
def test_a_near_miss_whose_band_straddles_the_0_360_cut_is_one_whole_stretch(level, side):
    """level 0.6 from below: the body is at 0.3 at the station and passes through 0/360 twice while still inside the band (edge at 359.6);
    level 359.5 from above: at 359.8, through 360 twice (edge at 0.5); level exactly 0 from either side. A wrap cut is not a boundary."""
    f = graze(level, side=side)
    index = index_of(f)
    (found,) = nm.solve_object_near_misses(obj=obj(level), index=index, orb_deg=ORB, horizon=WIDE, position_at=f)
    assert abs(days(found.t_in) + EDGE) < 1e-3 and abs(days(found.t_out) - EDGE) < 1e-3, (days(found.t_in), days(found.t_out))
    assert abs(found.clearance_deg - 0.3) < 1e-6 and found.coverage["side"] == side
    ((a, b),) = cc.expected_intervals(f, "venus", "conjunction", f"point:{level}", *WIDE)       # the independent reconstruction agrees
    assert abs((found.t_in - a).total_seconds()) < 120 and abs((found.t_out - b).total_seconds()) < 120
    if level in (0.6, 359.5):                    # the stretch really does cross the cut: the wrapped longitude is on both sides of it
        inside = [f("venus", found.t_in + (found.t_out - found.t_in) * k / 200) for k in range(1, 200)]
        assert min(inside) < 1.0 and max(inside) > 359.0


# ── the horizon edges ────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_near_miss_cut_by_the_horizon_start_is_stored_whole_and_says_where_it_is_clipped():
    f = graze(120.0)
    horizon = (T0 - 2 * DAY, T0 + 50 * DAY)
    (found,) = nm.solve_object_near_misses(obj=obj(120.0), index=index_of(f), orb_deg=ORB, horizon=horizon, position_at=f)
    assert abs(days(found.t_in) + EDGE) < 1e-3 and found.t_in < horizon[0]                    # the WHOLE stretch, not the horizon part
    assert found.coverage["clipped_by_horizon"] == ["start"]
    assert found.coverage["horizon_interval"] == [horizon[0].isoformat(), found.t_out.isoformat()]


def test_a_near_miss_cut_by_the_horizon_end_is_stored_whole_and_says_where_it_is_clipped():
    f = graze(120.0)
    horizon = (T0 - 50 * DAY, T0 + 2 * DAY)
    (found,) = nm.solve_object_near_misses(obj=obj(120.0), index=index_of(f), orb_deg=ORB, horizon=horizon, position_at=f)
    assert abs(days(found.t_out) - EDGE) < 1e-3 and found.t_out > horizon[1]
    assert found.coverage["clipped_by_horizon"] == ["end"]
    assert found.coverage["horizon_interval"] == [found.t_in.isoformat(), horizon[1].isoformat()]


def test_a_horizon_inside_the_stretch_is_clipped_at_both_ends():
    f = graze(120.0)
    (found,) = nm.solve_object_near_misses(obj=obj(120.0), index=index_of(f), orb_deg=ORB, horizon=(T0 - DAY, T0 + DAY), position_at=f)
    assert found.coverage["clipped_by_horizon"] == ["start", "end"]


def test_the_horizon_is_half_open_a_stretch_that_only_touches_an_edge_is_outside():
    f = graze(120.0)
    index = index_of(f)
    (whole,) = nm.solve_object_near_misses(obj=obj(120.0), index=index, orb_deg=ORB, horizon=WIDE)
    assert nm.solve_object_near_misses(obj=obj(120.0), index=index, orb_deg=ORB, horizon=(T0 - 50 * DAY, whole.t_in)) == []    # ends where it begins
    assert nm.solve_object_near_misses(obj=obj(120.0), index=index, orb_deg=ORB, horizon=(whole.t_out, T0 + 50 * DAY)) == []   # begins where it ends
    assert len(nm.solve_object_near_misses(obj=obj(120.0), index=index, orb_deg=ORB,
                                           horizon=(T0 - 50 * DAY, whole.t_in + timedelta(seconds=1)))) == 1


# ── identity: full-domain ordinals ───────────────────────────────────────────────────────────────────────────────────────────

def _periodic(body, t):                          # a near-miss every 200 days (clearance 0.3); 2.3 deg away in between
    d = (t - T0).total_seconds() / 86400.0
    return (120.0 + 0.3 + 1.0 - math.cos(2 * math.pi * d / 200.0)) % 360.0


def test_ordinals_are_over_the_full_domain_so_a_horizon_never_renumbers():
    index = index_of(_periodic, lo_days=-100, hi_days=500, step=0.5)
    o = obj(120.0)
    everything = nm.solve_object_near_misses(obj=o, index=index, orb_deg=ORB, horizon=(T0 - 90 * DAY, T0 + 490 * DAY))
    assert [x.ordinal for x in everything] == [1, 2, 3] and [round(days(x.t_closest)) for x in everything] == [0, 200, 400]
    (second,) = nm.solve_object_near_misses(obj=o, index=index, orb_deg=ORB, horizon=(T0 + 150 * DAY, T0 + 250 * DAY))
    assert second.ordinal == 2 and second.near_miss_id == everything[1].near_miss_id
    assert len({x.near_miss_id for x in everything}) == 3


def test_an_orb_change_is_a_new_object_and_the_namespace_is_not_the_contact_namespace():
    from services.gochara_kernel.substrate import PhysicalObjectId
    a = nm.NearMissObject("venus", "conjunction", "point:120.0", nm.orb_policy_id("orb_conj_slow", 1.0), CONV)
    b = nm.NearMissObject("venus", "conjunction", "point:120.0", nm.orb_policy_id("orb_conj_slow", 1.5), CONV)
    assert a.uuid != b.uuid and nm.near_miss_id(a, 1) != nm.near_miss_id(b, 1) and nm.near_miss_id(a, 1) != nm.near_miss_id(a, 2)
    assert a.uuid != PhysicalObjectId("venus", "conjunction", "point:120.0", CONV).uuid       # a near-miss object is not a physical object


# ── unresolved is refused by name, never stored ─────────────────────────────────────────────────────────────────────────────

def test_a_clearance_below_the_certified_minimum_is_unresolved():
    f = graze(120.0, clearance=0.003)
    with pytest.raises(nm.NearMissUnresolved, match="near_miss_unresolved_clearance"):
        nm.solve_object_near_misses(obj=obj(120.0), index=index_of(f), orb_deg=ORB, horizon=WIDE, position_at=f)


def test_a_turn_that_runs_into_the_edge_of_the_index_domain_is_unresolved():
    f = graze(120.0)
    index = index_of(f, lo_days=-3, hi_days=60)                  # the domain starts inside the band, before the station
    (s,) = nm.rootless_stretches(index, [120.0], ORB)
    assert s.touches_domain_edge
    with pytest.raises(nm.NearMissUnresolved, match="near_miss_unresolved_domain_edge"):
        nm.solve_object_near_misses(obj=obj(120.0), index=index, orb_deg=ORB, horizon=(T0 - 3 * DAY, T0 + 50 * DAY), position_at=f)
    # outside the build horizon the same stretch is nobody's question
    assert nm.solve_object_near_misses(obj=obj(120.0), index=index, orb_deg=ORB, horizon=(T0 + 20 * DAY, T0 + 50 * DAY)) == []


def test_an_ephemeris_that_contradicts_the_arc_index_is_unresolved():
    f = graze(120.0)

    def crossing_sky(body, t):                                   # the "ephemeris" says the body is on the OTHER side of the ray at the station
        d = (t - T0).total_seconds() / 86400.0
        return (120.0 - 0.3 + 0.02 * d * d) % 360.0
    with pytest.raises(nm.NearMissUnresolved, match="near_miss_unresolved_refinement"):
        nm.solve_object_near_misses(obj=obj(120.0), index=index_of(f), orb_deg=ORB, horizon=WIDE, position_at=crossing_sky)


def test_without_an_ephemeris_the_arc_index_value_is_kept_and_the_method_says_so():
    f = graze(120.0)
    (found,) = nm.solve_object_near_misses(obj=obj(120.0), index=index_of(f), orb_deg=ORB, horizon=WIDE)
    assert found.solver_method == "arc_index_extremum" and found.delta_t is None and abs(found.clearance_deg - 0.3) < 1e-6


# ── the junction field's daśā part ───────────────────────────────────────────────────────────────────────────────────────────

def _d(n):
    return T0 + n * DAY


ROWS = [inv.DashaRow("md-1", 1, "saturn", _d(-100), _d(100)),
        inv.DashaRow("ad-1", 2, "venus", _d(-100), _d(0)), inv.DashaRow("ad-2", 2, "sun", _d(0), _d(100)),
        inv.DashaRow("pd-1", 3, "mars", _d(-1), _d(1))]
HZ = (_d(-100), _d(100))


def test_an_ad_boundary_inside_the_stretch_is_listed_with_its_source_row():
    out = nm.dasha_junctions(ROWS, _d(-5), _d(5), HZ)
    assert out["state"] == "complete"
    assert {(e["level"], e["t"]) for e in out["events"]} == {("AD", _d(0).isoformat())}
    assert all(e["dasha_row_id"] in ("ad-1", "ad-2") for e in out["events"])                   # a PD boundary is not a junction


def test_a_boundary_at_t_in_is_inside_and_at_t_out_is_outside():
    assert [e["t"] for e in nm.dasha_junctions(ROWS, _d(0), _d(5), HZ)["events"]] == [_d(0).isoformat()]
    assert nm.dasha_junctions(ROWS, _d(-5), _d(0), HZ)["events"] == []


def test_missing_dasha_coverage_is_unknown_never_empty():
    assert nm.dasha_junctions(ROWS, _d(-5), _d(5), (_d(-2), _d(100)))["state"] == "unknown"     # the stretch starts before the horizon
    assert nm.dasha_junctions(ROWS[:2], _d(-5), _d(5), HZ)["state"] == "unknown"                # the AD rows stop at T0: a gap
    assert nm.dasha_junctions([], _d(-5), _d(5), HZ) == {"state": "unknown", "events": []}
    assert nm.dasha_junctions(ROWS, _d(-5), _d(-1), HZ) == {"state": "complete", "events": []}  # covered and none: a verified none


# ── the in-build cross-check with the certifier ─────────────────────────────────────────────────────────────────────────────

KEY = ("venus", "conjunction", "point:120.0")
STORED = [{"body": "venus", "relation": "conjunction", "target": "point:120.0", "near_miss_id": "id-1", "t_in": _d(-6), "t_out": _d(6),
           "clearance_deg": 0.3}]
REPORTED = [{"body": "venus", "relation": "conjunction", "target": "point:120.0", "interval": [_d(-6).isoformat(), _d(6).isoformat()],
             "closest_approach_deg": 0.3}]


def _rec(**kw):
    base = dict(reported=REPORTED, stored=STORED, searched={KEY}, obligations=[KEY], horizon=HZ)
    base.update(kw)
    return nm.reconcile_with_certifier(**base)


def test_the_two_derivations_agree():
    assert _rec() == [] and _rec(reported=[], stored=[]) == []


def test_each_disagreement_is_refused_by_name():
    assert _rec(stored=[])[0].startswith("near_miss_reported_but_unstored:")
    assert _rec(reported=[])[0].startswith("near_miss_stored_but_unreported:")
    assert _rec(searched=set())[0].startswith("near_miss_unsearched:")
    other = [dict(STORED[0], target="point:121.0")]
    assert sorted(p.split(":")[0] for p in _rec(stored=other)) == ["near_miss_reported_but_unstored",    # another object's row pairs with nothing
                                                                   "near_miss_stored_but_unreported"]
    two = REPORTED * 2
    assert [p.split(":")[0] for p in _rec(reported=two)] == ["near_miss_reported_but_unstored"]           # pairing is one to one


def test_a_stored_near_miss_outside_the_horizon_is_not_expected_from_the_certifier():
    far = [dict(STORED[0], t_in=_d(200), t_out=_d(210))]
    assert _rec(reported=[], stored=far) == []
