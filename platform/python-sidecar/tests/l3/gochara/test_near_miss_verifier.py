"""Near-miss verifier (ND-P2 rules 1-2, FB-24..FB-29) — pure tests on synthetic signed-distance curves, no database.

The curves are analytic (distance in degrees to a ray level as a function of days from a chosen instant), so every
expected clearance, edge and state is worked by hand from the curve, never read back from the code under test.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import near_miss_verifier as nm
from services.gochara_kernel.near_miss_verifier import utc

LO, HI = utc(2000, 1, 1), utc(2000, 1, 31)
TC = utc(2000, 1, 15, 12)
ORB, VMAX = 1.0, 1.0                       # one degree band; speed bound 1 deg/day


def _x(t):
    return (t - TC).total_seconds() / 86400.0


def parabola(c, a):
    """signed distance c + a x^2 (x in days from TC): never crosses zero for c > 0"""
    return lambda t: c + a * _x(t) ** 2


def line(a):
    return lambda t: a * _x(t)


# ── the three states ─────────────────────────────────────────────────────────────────────────────────────────────
def test_a_rootless_stretch_with_certified_clearance_is_a_near_miss_with_the_hand_computed_edges():
    out = nm.derive_near_misses(parabola(0.5, 0.3), LO, HI, orb_deg=ORB, vmax_dps=VMAX)
    assert len(out) == 1 and out[0]["state"] == "near_miss" and out[0]["reason"] is None
    r = out[0]
    assert r["clearance_deg"] == pytest.approx(0.5, abs=1e-6)
    assert abs((r["t_closest"] - TC).total_seconds()) < 5
    half = (((ORB - 0.5) / 0.3) ** 0.5) * 86400                     # |d| = 1 at x = sqrt(0.5/0.3) = 1.2910 days
    assert abs((r["t_in"] - (TC - timedelta(seconds=half))).total_seconds()) < 3
    assert abs((r["t_out"] - (TC + timedelta(seconds=half))).total_seconds()) < 3
    assert not r["clipped"]


def test_a_stretch_that_crosses_the_level_is_a_contact_not_a_near_miss():
    out = nm.derive_near_misses(line(0.4), LO, HI, orb_deg=ORB, vmax_dps=VMAX)
    assert [r["state"] for r in out] == ["contact"]


def test_a_tangency_that_lands_on_a_sample_is_a_contact_and_one_between_samples_is_never_a_near_miss():
    exact = nm.derive_near_misses(parabola(0.0, 0.3), LO, HI, orb_deg=ORB, vmax_dps=VMAX)     # TC is on the hour grid
    assert [r["state"] for r in exact] == ["contact"]
    off_grid = lambda t: 1e-6 + 0.3 * (((t - TC).total_seconds() - 1800) / 86400.0) ** 2        # minimum 30 min off a sample
    out = nm.derive_near_misses(off_grid, LO, HI, orb_deg=ORB, vmax_dps=VMAX)
    assert out[0]["state"] == "unresolved"                                                         # no threshold makes it a contact or near-miss


def test_a_clearance_below_the_minimum_approach_is_unresolved_by_name_never_a_near_miss():
    out = nm.derive_near_misses(parabola(0.004, 0.3), LO, HI, orb_deg=ORB, vmax_dps=VMAX)
    assert out[0]["state"] == "unresolved" and out[0]["reason"] == "clearance_below_min_approach"
    just_above = nm.derive_near_misses(parabola(0.006, 0.3), LO, HI, orb_deg=ORB, vmax_dps=VMAX)
    assert just_above[0]["state"] == "near_miss"


def test_a_stretch_clipped_by_the_search_edge_is_unresolved_until_followed_beyond_it():
    lo = TC - timedelta(days=0.5)                                                                   # the window starts mid-stretch
    out = nm.derive_near_misses(parabola(0.5, 0.3), lo, HI, orb_deg=ORB, vmax_dps=VMAX)
    assert out[0]["clipped"] and out[0]["state"] == "unresolved" and out[0]["reason"] == "clipped_stretch_not_followed"


def test_two_separate_stretches_are_two_results_in_time_order():
    d = lambda t: 0.5 + 0.3 * min(_x(t) ** 2, (_x(t) - 8) ** 2) if True else 0         # two minima 8 days apart
    out = nm.derive_near_misses(d, LO, HI, orb_deg=ORB, vmax_dps=VMAX)
    assert [r["state"] for r in out] == ["near_miss", "near_miss"] and out[0]["t_out"] < out[1]["t_in"]




def test_a_crossing_between_two_samples_is_a_contact_even_though_no_sample_is_zero():
    crossing = lambda t: 0.4 * (_x(t) - 1800 / 86400.0)                                            # zero 30 minutes off the hour grid
    out = nm.derive_near_misses(crossing, LO, HI, orb_deg=ORB, vmax_dps=VMAX)
    assert [r["state"] for r in out] == ["contact"]                                                # the sign change is the root


def test_a_clearance_the_speed_bound_cannot_prove_is_unresolved_whatever_the_samples_show():
    out = nm.derive_near_misses(parabola(0.5, 0.3), LO, HI, orb_deg=ORB, vmax_dps=1e6)             # a speed bound that proves nothing
    assert out[0]["state"] == "unresolved" and out[0]["reason"] == "clearance_not_certified"



def test_classify_stretch_decision_table():
    c = nm.classify_stretch
    assert c(rooted=True, complete=False) == ("contact", None)                       # a verified root wins
    assert c(rooted=False, complete=False) == ("unresolved", "stretch_incomplete")
    assert c(rooted=False, complete=True, clipped_followed=False) == ("unresolved", "clipped_stretch_not_followed")
    assert c(rooted=False, complete=True, clearance_deg=0.5) == ("unresolved", "clearance_not_certified")
    assert c(rooted=False, complete=True, clearance_deg=0.0, clearance_certified=True) == ("unresolved", "clearance_not_positive")
    assert c(rooted=False, complete=True, clearance_deg=0.0049, clearance_certified=True)[1] == "clearance_below_min_approach"
    assert c(rooted=False, complete=True, clearance_deg=0.005, clearance_certified=True) == ("near_miss", None)
    # a stationless body is not a near-miss for lack of an observed root: it needs the same certification
    assert c(rooted=False, complete=True, clearance_deg=0.5, clearance_certified=False, stationless_body=True)[0] == "unresolved"


def test_the_speed_bound_proof_refuses_a_step_it_cannot_prove():
    # distance dips from 0.01 to 0.01 across a long step: |d0|+|d1| = 0.02 << vmax*gap, and the midpoint crosses zero
    d = lambda t: 0.01 - 0.02 * (1 - abs(_x(t)) / 0.5) if abs(_x(t)) < 0.5 else 0.01
    t0, t1 = TC - timedelta(days=0.5), TC + timedelta(days=0.5)
    assert nm._proved_no_crossing(d, t0, t1, d(t0), d(t1), VMAX) is False
    assert nm._proved_no_crossing(parabola(0.5, 0.3), t0, t1, parabola(0.5, 0.3)(t0), parabola(0.5, 0.3)(t1), VMAX) is True


# ── the junction field ───────────────────────────────────────────────────────────────────────────────────────────
def test_a_junction_at_t_in_is_included_and_at_t_out_excluded():
    t_in, t_out = utc(2000, 3, 1), utc(2000, 3, 11)
    ev = [("sign_ingress", t_in), ("nakshatra_ingress", t_out), ("dasha_boundary", utc(2000, 3, 5))]
    assert nm.junction_field(t_in, t_out, ev, coverage_complete=True) == {
        "kinds": ["dasha_boundary", "sign_ingress"], "complete": True}
    assert nm.junction_field(t_in, t_out, [("nakshatra_ingress", t_out)], coverage_complete=True) == {"kinds": [], "complete": True}


def test_missing_coverage_is_unknown_never_empty_and_an_unknown_kind_is_refused():
    assert nm.junction_field(utc(2000, 3, 1), utc(2000, 3, 11), [], coverage_complete=False) == {"kinds": None, "complete": False}
    assert nm.junction_field(utc(2000, 3, 1), utc(2000, 3, 11), [], coverage_complete=True)["kinds"] == []
    with pytest.raises(nm.NearMissError, match="junction_kind_unknown"):
        nm.junction_field(utc(2000, 3, 1), utc(2000, 3, 11), [("eclipse", utc(2000, 3, 2))], coverage_complete=True)


# ── the stored row ───────────────────────────────────────────────────────────────────────────────────────────────
def _row(**kw):
    base = dict(standing="near_miss", score=None, score_reason="near_miss_unscored", clearance_deg=0.4, orb_deg=1.0,
                proximity=0.6, t_in=utc(2000, 3, 1), t_out=utc(2000, 3, 4), closest_state="placed",
                t_closest=utc(2000, 3, 2), junction=["sign_ingress"], junction_complete=True)
    base.update(kw)
    return base


def test_a_well_formed_row_is_accepted_and_the_kind_names_proximity_not_strength():
    assert nm.row_problems(_row()) == []
    assert nm.PROXIMITY_NAME == "proximity"
    assert nm.row_problems(_row(closest_state="edge_unplaced", t_closest=None, junction=None, junction_complete=False)) == []


@pytest.mark.parametrize("kw,code", [
    (dict(standing="contact"), "standing_not_near_miss"),
    (dict(score=0.3), "near_miss_scored"),
    (dict(score_reason=None), "score_reason_not_near_miss_unscored"),
    (dict(clearance_deg=0.0), "clearance_not_positive"),
    (dict(clearance_deg=0.004, proximity=0.996), "clearance_below_min_approach"),
    (dict(clearance_deg=1.0, proximity=0.0), "clearance_not_inside_orb"),
    (dict(proximity=0.9), "proximity_not_one_minus_clearance_over_orb"),
    (dict(t_out=utc(2000, 3, 1)), "interval_empty"),
    (dict(t_closest=utc(2000, 3, 4)), "t_closest_outside_interval"),                 # t_out is excluded
    (dict(closest_state="edge_unplaced"), "edge_unplaced_has_t_closest"),
    (dict(closest_state="somewhere"), "closest_state_unknown"),
    (dict(junction=["sign_ingress"], junction_complete=False), "junction_present_without_complete_coverage"),
    (dict(junction=None, junction_complete=True), "junction_malformed"),
    (dict(junction=["eclipse"], junction_complete=True), "junction_malformed"),
    (dict(junction_complete=None), "junction_complete_missing"),
])
def test_each_row_defect_is_refused_by_name(kw, code):
    out = nm.row_problems(_row(**kw))
    assert any(x.startswith(code) for x in out), out


# ── ordinals ─────────────────────────────────────────────────────────────────────────────────────────────────────
def test_ordinals_follow_t_closest_then_unplaced_by_t_in_and_ignore_input_order():
    a = {"t_in": utc(2001, 1, 1), "t_closest": utc(2001, 1, 2)}
    b = {"t_in": utc(2000, 1, 1), "t_closest": utc(2000, 1, 2)}
    e1 = {"t_in": utc(2003, 1, 1), "t_closest": None}
    e0 = {"t_in": utc(2002, 1, 1), "t_closest": None}
    got = nm.assign_ordinals([e1, a, e0, b])
    assert [(o, r) for o, r in got] == [(1, b), (2, a), (3, e0), (4, e1)]
    assert nm.assign_ordinals([b, a, e0, e1]) == got


def test_adding_a_later_occurrence_to_the_full_domain_set_never_renumbers_earlier_ones():
    a = {"t_in": utc(2001, 1, 1), "t_closest": utc(2001, 1, 2)}
    b = {"t_in": utc(2000, 1, 1), "t_closest": utc(2000, 1, 2)}
    c = {"t_in": utc(2010, 1, 1), "t_closest": utc(2010, 1, 2)}
    before = dict((id(r), o) for o, r in nm.assign_ordinals([a, b]))
    after = dict((id(r), o) for o, r in nm.assign_ordinals([a, b, c]))
    assert before[id(a)] == after[id(a)] == 2 and before[id(b)] == after[id(b)] == 1


def test_an_orb_change_is_a_new_object_key():
    k1 = nm.object_key("jupiter", "aspect", "point:259.17", "orb-1.0", "conv-1")
    k2 = nm.object_key("jupiter", "aspect", "point:259.17", "orb-1.5", "conv-1")
    assert k1 != k2 and k1[:3] == k2[:3]


# ── set comparison, coverage, noninterference ────────────────────────────────────────────────────────────────────
def _nm(t_in, t_out):
    return {"state": "near_miss", "reason": None, "t_in": t_in, "t_out": t_out}


def test_the_stored_set_must_equal_the_rederived_set_and_the_reported_count():
    w1, w2 = _nm(utc(2000, 3, 1), utc(2000, 3, 4)), _nm(utc(2000, 5, 1), utc(2000, 5, 4))
    s1, s2 = {"t_in": utc(2000, 3, 1, 0, 0, 1), "t_out": utc(2000, 3, 4)}, {"t_in": utc(2000, 5, 1), "t_out": utc(2000, 5, 4)}
    assert nm.compare_sets([w1, w2], [s1, s2], reported_count=2) == []
    assert nm.compare_sets([], [], reported_count=0) == []                             # a VERIFIED empty
    assert any(x.startswith("near_miss_missing") for x in nm.compare_sets([w1, w2], [s1]))
    assert any(x.startswith("near_miss_extra") for x in nm.compare_sets([w1], [s1, s2]))
    assert any(x.startswith("near_miss_reported_not_stored") for x in nm.compare_sets([w1, w2], [s1, s2], reported_count=3))
    assert any(x.startswith("near_miss_stored_not_reported") for x in nm.compare_sets([w1, w2], [s1, s2], reported_count=1))
    un = {"state": "unresolved", "reason": "clearance_not_certified", "t_in": utc(2000, 7, 1), "t_out": utc(2000, 7, 3)}
    assert any(x.startswith("near_miss_unresolved") for x in nm.compare_sets([w1, un], [s1]))


def test_matching_is_one_to_one():
    w1 = _nm(utc(2000, 3, 1), utc(2000, 3, 4))
    w2 = _nm(utc(2000, 3, 1), utc(2000, 3, 4))                                           # a duplicate re-derived stretch
    s = {"t_in": utc(2000, 3, 1), "t_out": utc(2000, 3, 4)}
    assert any(x.startswith("near_miss_missing") for x in nm.compare_sets([w1, w2], [s]))


H = (utc(1998, 1, 1).date(), utc(2084, 2, 5).date())


def test_coverage_makes_an_empty_result_verified_only_when_complete_over_the_horizon_with_matching_count():
    ok = {"searched_complete": True, "horizon": H, "count": 0}
    assert nm.coverage_problems(ok, 0, horizon=H) == []
    assert nm.coverage_problems(dict(ok, searched_complete=False), 0, horizon=H) == ["near_miss_search_incomplete"]
    assert nm.coverage_problems(dict(ok, searched_complete=None), 0, horizon=H) == ["near_miss_search_incomplete"]
    assert nm.coverage_problems(ok, 2, horizon=H)[0].startswith("near_miss_count_mismatch")
    assert nm.coverage_problems(dict(ok, horizon=(H[0], H[0])), 0, horizon=H)[0].startswith("near_miss_search_horizon_mismatch")


def _outputs():
    return {k: [1, 2, 3] for k in nm.NONINTERFERENCE_KEYS}


def test_noninterference_compares_every_named_output_and_a_missing_key_is_refused():
    on, off = _outputs(), _outputs()
    assert nm.noninterference_problems(on, off) == [] and len(nm.NONINTERFERENCE_KEYS) == 12
    for k in nm.NONINTERFERENCE_KEYS:
        changed = dict(on, **{k: [9]})
        assert nm.noninterference_problems(changed, off) == [f"noninterference_violated: {k}"]
        missing = {x: v for x, v in on.items() if x != k}
        assert nm.noninterference_problems(missing, off) == [f"noninterference_key_missing: {k}"]
    assert "endpoint_5_t_honesty" in nm.NONINTERFERENCE_KEYS and "contact_identity_bytes" in nm.NONINTERFERENCE_KEYS
