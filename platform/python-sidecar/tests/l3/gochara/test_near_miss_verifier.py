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
ORB, BODY = 1.0, "mars"                  # one degree band; Mars: the verifier's own speed bound is 1 deg/day


def _x(t):
    return (t - TC).total_seconds() / 86400.0


def parabola(c, a):
    """signed distance c + a x^2 (x in days from TC): never crosses zero for c > 0"""
    return lambda t: c + a * _x(t) ** 2


def line(a):
    return lambda t: a * _x(t)


CENTRE = 100.0


def _derive(dist, *, body=BODY, lo=None, hi=None, centre=CENTRE, **kw):
    """derive_near_misses on a synthetic signed-distance curve: the body's longitude is the level plus the distance"""
    position_at = lambda b, t: (centre + dist(t)) % 360.0                                             # noqa: E731
    return nm.derive_near_misses(position_at, body, [centre], lo or LO, hi or HI, orb_deg=ORB, **kw)


# ── the three states ─────────────────────────────────────────────────────────────────────────────────────────────
def test_a_rootless_stretch_with_certified_clearance_is_a_near_miss_with_the_hand_computed_edges():
    out = _derive(parabola(0.5, 0.3))
    assert len(out) == 1 and out[0]["state"] == "near_miss" and out[0]["reason"] is None
    r = out[0]
    assert r["clearance_deg"] == pytest.approx(0.5, abs=1e-6)
    assert abs((r["t_closest"] - TC).total_seconds()) < 5
    half = (((ORB - 0.5) / 0.3) ** 0.5) * 86400                     # |d| = 1 at x = sqrt(0.5/0.3) = 1.2910 days
    assert abs((r["t_in"] - (TC - timedelta(seconds=half))).total_seconds()) < 3
    assert abs((r["t_out"] - (TC + timedelta(seconds=half))).total_seconds()) < 3
    assert not r["clipped"]


def test_a_stretch_that_crosses_the_level_is_a_contact_not_a_near_miss():
    out = _derive(line(0.4))
    assert [r["state"] for r in out] == ["contact"]


def test_a_tangency_is_never_a_near_miss_and_this_verifier_cannot_call_it_a_contact():
    exact = _derive(parabola(0.0, 0.3))     # touches the level exactly at TC: a contact only through an exact root the SOLVER verifies
    assert [r["state"] for r in exact] == ["unresolved"] and exact[0]["reason"] == "clearance_below_min_approach"
    off_grid = lambda t: 1e-6 + 0.3 * (((t - TC).total_seconds() - 1800) / 86400.0) ** 2        # minimum 30 min off a sample
    out = _derive(off_grid)
    assert out[0]["state"] == "unresolved"                                                         # no threshold makes it a contact or near-miss


def test_a_clearance_below_the_minimum_approach_is_unresolved_by_name_never_a_near_miss():
    out = _derive(parabola(0.004, 0.3))
    assert out[0]["state"] == "unresolved" and out[0]["reason"] == "clearance_below_min_approach"
    just_above = _derive(parabola(0.006, 0.3))
    assert just_above[0]["state"] == "near_miss"


def test_a_stretch_clipped_by_the_search_edge_is_unresolved_until_followed_beyond_it():
    lo = TC - timedelta(days=0.5)                                                                   # the window starts mid-stretch
    out = _derive(parabola(0.5, 0.3), lo=lo)
    assert out[0]["clipped"] and out[0]["state"] == "unresolved" and out[0]["reason"] == "clipped_stretch_not_followed"


def test_two_separate_stretches_are_two_results_in_time_order():
    d = lambda t: 0.5 + 0.3 * min(_x(t) ** 2, (_x(t) - 8) ** 2)                          # two minima 8 days apart
    out = _derive(d)
    assert [r["state"] for r in out] == ["near_miss", "near_miss"] and out[0]["t_out"] < out[1]["t_in"]




def test_a_crossing_between_two_samples_is_a_contact_even_though_no_sample_is_zero():
    crossing = lambda t: 0.4 * (_x(t) - 1800 / 86400.0)                                            # zero 30 minutes off the hour grid
    out = _derive(crossing)
    assert [r["state"] for r in out] == ["contact"]                                                # the sign change is the root


def test_a_clearance_the_speed_bound_cannot_prove_is_unresolved_whatever_the_samples_show():
    out = _derive(parabola(0.5, 0.3), vmax_dps=1e6)             # a speed bound that proves nothing
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


def test_a_crossing_dip_hidden_between_two_samples_is_found_by_the_branch_and_bound():
    # base +0.01, with a V dip (slope 1 deg/day, the speed bound) down to -0.01 centred 30 minutes off the hour grid: no sample is negative
    x0 = 1800 / 86400.0
    d = lambda t: 0.01 - 0.02 * max(0.0, 1 - abs(_x(t) - x0) / 0.02)
    a, b = TC - timedelta(hours=3), TC + timedelta(hours=3)
    assert all(d(a + timedelta(hours=k)) > 0 for k in range(7))                                    # an hourly sampler sees no sign change
    res = nm._analyse_stretch(d, a, b, 1.0)
    assert res["rooted"] is True                                                                   # the dip crosses the level


def test_a_narrow_deeper_dip_between_samples_is_the_certified_minimum_not_the_shallow_one_the_samples_show():
    x0 = 1800 / 86400.0
    d = lambda t: min(0.5, 0.48 + abs(_x(t) - x0))                                                  # a flat 0.5 and a dip to 0.48 off the grid
    a, b = TC - timedelta(hours=3), TC + timedelta(hours=3)
    assert min(d(a + timedelta(hours=k)) for k in range(7)) == 0.5                                  # every hourly sample reads 0.5
    res = nm._analyse_stretch(d, a, b, 1.0)
    assert res["rooted"] is False and res["certified"] is True
    assert res["clearance_deg"] == pytest.approx(0.48, abs=2e-3)
    assert abs((res["t_closest"] - (TC + timedelta(minutes=30))).total_seconds()) < 120


def test_a_stretch_with_two_dips_certifies_the_deeper_one():
    x1, x2 = 0.0, 0.25
    d = lambda t: min(0.55 + 0.4 * (_x(t) - x1) ** 2, 0.4 + 6.0 * abs(_x(t) - x2) ** 1)           # a wide dip near 0.55, a sharper one near 0.4
    a, b = TC - timedelta(hours=8), TC + timedelta(hours=14)
    res = nm._analyse_stretch(d, a, b, 8.0)
    assert res["rooted"] is False and res["clearance_deg"] == pytest.approx(0.4, abs=2e-3)
    assert abs((res["t_closest"] - (TC + timedelta(days=0.25))).total_seconds()) < 600


def test_a_speed_bound_that_cannot_exclude_a_lower_value_leaves_the_minimum_uncertified():
    d = parabola(0.5, 0.3)
    res = nm._analyse_stretch(d, TC - timedelta(hours=3), TC + timedelta(hours=3), 1e6)
    assert res["certified"] is False and res["rooted"] is False


# ── the junction field ───────────────────────────────────────────────────────────────────────────────────────────
def test_a_junction_at_t_in_is_included_and_at_t_out_excluded():
    t_in, t_out = utc(2000, 3, 1), utc(2000, 3, 11)
    ev = [("sign_ingress", t_in), ("nakshatra_ingress", t_out), ("dasha_md_ad_boundary", utc(2000, 3, 5))]
    assert nm.junction_field(t_in, t_out, ev, coverage_complete=True) == {
        "kinds": ["dasha_md_ad_boundary", "sign_ingress"], "complete": True}
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
                t_closest=utc(2000, 3, 2), junction=["sign_ingress"], junction_complete=True, ordinal=1, object_id="obj-1")
    base.update(kw)
    return base


def test_a_well_formed_row_is_accepted_and_the_kind_names_proximity_not_strength():
    assert nm.row_problems(_row()) == []
    assert nm.PROXIMITY_NAME == "proximity"
    assert nm.row_problems(_row(closest_state="edge_unplaced", t_closest=None, junction=None, junction_complete=False, t_in=utc(2000, 1, 1)), domain=(utc(2000, 1, 1), utc(2100, 1, 1))) == []


@pytest.mark.parametrize("kw,code", [
    (dict(standing="contact"), "standing_not_near_miss"),
    (dict(score=0.3), "near_miss_scored"),
    (dict(score_reason=None), "score_reason_not_near_miss_unscored"),
    (dict(clearance_deg=0.0), "clearance_not_positive"),
    (dict(clearance_deg=0.004, proximity=0.996), "clearance_below_min_approach"),
    (dict(clearance_deg=1.01, proximity=0.0), "clearance_not_inside_orb"),
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
    a = {"t_in": utc(2001, 1, 1), "t_out": utc(2001, 1, 4), "t_closest": utc(2001, 1, 2)}
    b = {"t_in": utc(2000, 1, 1), "t_out": utc(2000, 1, 4), "t_closest": utc(2000, 1, 2)}
    e1 = {"t_in": utc(2003, 1, 1), "t_out": utc(2003, 1, 4), "t_closest": None}
    e0 = {"t_in": utc(2002, 1, 1), "t_out": utc(2002, 1, 4), "t_closest": None}
    got = nm.assign_ordinals([e1, a, e0, b])
    assert [(o, r) for o, r in got] == [(1, b), (2, a), (3, e0), (4, e1)]
    assert nm.assign_ordinals([b, a, e0, e1]) == got


def test_adding_a_later_occurrence_to_the_full_domain_set_never_renumbers_earlier_ones():
    a = {"t_in": utc(2001, 1, 1), "t_out": utc(2001, 1, 4), "t_closest": utc(2001, 1, 2)}
    b = {"t_in": utc(2000, 1, 1), "t_out": utc(2000, 1, 4), "t_closest": utc(2000, 1, 2)}
    c = {"t_in": utc(2010, 1, 1), "t_out": utc(2010, 1, 4), "t_closest": utc(2010, 1, 2)}
    before = dict((id(r), o) for o, r in nm.assign_ordinals([a, b]))
    after = dict((id(r), o) for o, r in nm.assign_ordinals([a, b, c]))
    assert before[id(a)] == after[id(a)] == 2 and before[id(b)] == after[id(b)] == 1


def test_an_orb_change_is_a_new_object_key():
    k1 = nm.object_key("jupiter", "aspect", "point:259.17", "orb-1.0", "conv-1")
    k2 = nm.object_key("jupiter", "aspect", "point:259.17", "orb-1.5", "conv-1")
    assert k1 != k2 and k1[:3] == k2[:3]


# ── set comparison, coverage, noninterference ────────────────────────────────────────────────────────────────────
def _nm(t_in, t_out, clearance=0.4):
    mid = t_in + (t_out - t_in) / 2
    return {"state": "near_miss", "reason": None, "t_in": t_in, "t_out": t_out, "clearance_deg": clearance, "t_closest": mid,
            "closest_candidates": [(mid - timedelta(minutes=5), mid + timedelta(minutes=5))], "closest_certified": True,
            "distance_at": (lambda t, c=clearance: c)}                    # a flat stand-in geometry: |d| = the clearance everywhere


def _stored(t_in, t_out, clearance=0.4, junction=(), complete=True, closest="mid", ordinal=1):
    mid = t_in + (t_out - t_in) / 2
    return {"t_in": t_in, "t_out": t_out, "clearance_deg": clearance, "closest_state": "placed", "t_closest": mid,
            "junction": None if junction is None else list(junction), "junction_complete": complete, "orb_deg": 1.0, "ordinal": ordinal,
            "object_id": "obj-1"}


NO_JUNCTIONS = ([], True)
ID = dict(expected_orb_deg=1.0, expected_object_id="obj-1")


def test_the_stored_set_must_equal_the_rederived_set_and_the_reported_count():
    cmp = lambda w, st, **kw: nm.compare_sets(w, st, junction_source=NO_JUNCTIONS, **ID, **kw)            # noqa: E731
    w1, w2 = _nm(utc(2000, 3, 1), utc(2000, 3, 4)), _nm(utc(2000, 5, 1), utc(2000, 5, 4))
    s1, s2 = _stored(utc(2000, 3, 1, 0, 0, 1), utc(2000, 3, 4), ordinal=1), _stored(utc(2000, 5, 1), utc(2000, 5, 4), ordinal=2)
    assert cmp([w1, w2], [s1, s2], reported_count=2) == []
    assert cmp([], [], reported_count=0) == []                                                       # a VERIFIED empty
    assert any(x.startswith("near_miss_missing") for x in cmp([w1, w2], [s1]))
    assert any(x.startswith("near_miss_extra") for x in cmp([w1], [s1, s2]))
    assert any(x.startswith("near_miss_reported_not_stored") for x in cmp([w1, w2], [s1, s2], reported_count=3))
    assert any(x.startswith("near_miss_stored_not_reported") for x in cmp([w1, w2], [s1, s2], reported_count=1))
    un = {"state": "unresolved", "reason": "clearance_not_certified", "t_in": utc(2000, 7, 1), "t_out": utc(2000, 7, 3)}
    assert any(x.startswith("near_miss_unresolved") for x in cmp([w1, un], [s1]))


def test_matching_is_one_to_one():
    w1 = _nm(utc(2000, 3, 1), utc(2000, 3, 4))
    w2 = _nm(utc(2000, 3, 1), utc(2000, 3, 4))                                           # a duplicate re-derived stretch
    s = _stored(utc(2000, 3, 1), utc(2000, 3, 4))
    assert any(x.startswith("near_miss_missing") for x in nm.compare_sets([w1, w2], [s], junction_source=NO_JUNCTIONS, **ID))


def test_a_stored_row_with_the_right_interval_but_a_wrong_clearance_or_closest_instant_is_refused():
    w = _nm(utc(2000, 3, 1), utc(2000, 3, 4), clearance=0.5)
    ok = _stored(utc(2000, 3, 1), utc(2000, 3, 4), clearance=0.5)
    assert nm.compare_sets([w], [ok], junction_source=NO_JUNCTIONS, **ID) == []
    assert nm.compare_sets([w], [dict(ok, clearance_deg=0.5 + 0.0009)], junction_source=NO_JUNCTIONS, **ID) == []               # inside the tolerance
    assert [x.split(":")[0] for x in nm.compare_sets([w], [dict(ok, clearance_deg=0.5 + 0.01)], junction_source=NO_JUNCTIONS, **ID)] == ["near_miss_clearance_mismatch"]   # just outside it
    bad_c = nm.compare_sets([w], [dict(ok, clearance_deg=0.05)], junction_source=NO_JUNCTIONS, **ID)                           # the reviewer's 0.05 vs 0.5
    assert [x.split(":")[0] for x in bad_c] == ["near_miss_clearance_mismatch"]
    late = dict(ok, t_closest=ok["t_closest"] + timedelta(hours=11))
    assert [x.split(":")[0] for x in nm.compare_sets([w], [late], junction_source=NO_JUNCTIONS, **ID)] == ["near_miss_t_closest_mismatch"]
    near = dict(ok, t_closest=ok["t_closest"] + timedelta(minutes=4))                                 # inside the candidate interval (+-5 min)
    assert nm.compare_sets([w], [near], junction_source=NO_JUNCTIONS, **ID) == []
    far = dict(ok, t_closest=ok["t_closest"] + timedelta(minutes=9))                                  # outside it: no 600-second blanket tolerance any more
    assert [x.split(":")[0] for x in nm.compare_sets([w], [far], junction_source=NO_JUNCTIONS, **ID)] == ["near_miss_t_closest_mismatch"]
    unplaced = dict(ok, closest_state="edge_unplaced", t_closest=None)
    assert nm.compare_sets([w], [unplaced], junction_source=NO_JUNCTIONS, **ID) == []                                          # row_problems judges the claim


def test_the_stored_junction_must_equal_the_junction_recomputed_from_the_pinned_sources():
    w = _nm(utc(2000, 3, 1), utc(2000, 3, 4))
    events = [("sign_ingress", utc(2000, 3, 2)), ("dasha_md_ad_boundary", utc(2000, 3, 4))]          # the second is AT t_out: excluded
    good = _stored(utc(2000, 3, 1), utc(2000, 3, 4), junction=["sign_ingress"])
    assert nm.compare_sets([w], [good], junction_source=(events, True), **ID) == []
    fabricated = _stored(utc(2000, 3, 1), utc(2000, 3, 4), junction=["dasha_md_ad_boundary"])        # the reviewer's probe: no such event inside
    assert [x.split(":")[0] for x in nm.compare_sets([w], [fabricated], junction_source=(events, True), **ID)] == ["near_miss_junction_mismatch"]
    empty_claimed = _stored(utc(2000, 3, 1), utc(2000, 3, 4), junction=[])                           # an empty list where a junction exists
    assert nm.compare_sets([w], [empty_claimed], junction_source=(events, True), **ID)[0].startswith("near_miss_junction_mismatch")
    unknown = _stored(utc(2000, 3, 1), utc(2000, 3, 4), junction=None, complete=False)                # missing coverage = unknown
    assert nm.compare_sets([w], [unknown], junction_source=(events, False), **ID) == []
    assert nm.compare_sets([w], [good], junction_source=(events, False), **ID)[0].startswith("near_miss_junction_mismatch")


H = (utc(1998, 1, 1).date(), utc(2084, 2, 5).date())


def test_coverage_makes_an_empty_result_verified_only_when_complete_over_the_horizon_with_matching_count():
    ok = {"searched_complete": True, "horizon": H, "count": 0, "resolution_limit_seconds": 60.0}
    assert nm.coverage_problems(ok, 0, horizon=H) == []
    assert nm.coverage_problems(dict(ok, searched_complete=False), 0, horizon=H) == ["near_miss_search_incomplete"]
    assert nm.coverage_problems(dict(ok, searched_complete=None), 0, horizon=H) == ["near_miss_search_incomplete"]
    assert nm.coverage_problems(ok, 2, horizon=H)[0].startswith("near_miss_count_mismatch")
    assert nm.coverage_problems(dict(ok, horizon=(H[0], H[0])), 0, horizon=H)[0].startswith("near_miss_search_horizon_mismatch")


def _outputs():
    return {k: [1, 2, 3] for k in nm.NONINTERFERENCE_KEYS}


def test_noninterference_compares_every_named_output_and_a_missing_key_is_refused():
    on, off = _outputs(), _outputs()
    assert nm.noninterference_problems(on, off) == [] and len(nm.NONINTERFERENCE_KEYS) == 13
    for k in nm.NONINTERFERENCE_KEYS:
        changed = dict(on, **{k: [9]})
        assert nm.noninterference_problems(changed, off) == [f"noninterference_violated: {k}"]
        missing = {x: v for x, v in on.items() if x != k}
        assert nm.noninterference_problems(missing, off) == [f"noninterference_key_missing: {k}"]
    assert {"endpoint_5_t_honesty", "contact_identity_bytes", "coverage_accounting"} <= set(nm.NONINTERFERENCE_KEYS)


# ── amendments of review NDV-FABLE-1 ─────────────────────────────────────────────────────────────────────────────
def test_the_band_is_inclusive_everywhere_and_is_the_one_the_built_band_draws():
    assert nm._in_band(1.0, 1.0) and nm._in_band(-1.0, 1.0) and not nm._in_band(1.0000001, 1.0)
    assert nm.row_problems(_row(clearance_deg=1.0, proximity=0.0)) == []                              # on the edge: inside
    assert any(x.startswith("clearance_not_inside_orb") for x in nm.row_problems(_row(clearance_deg=1.01, proximity=0.0)))


def test_the_derived_stretch_edges_equal_the_built_band_intervals_on_the_same_curve():
    from services.gochara_kernel import contact_reconstruct as cr
    centre = 100.0
    dist = parabola(0.5, 0.3)
    position_at = lambda body, t: (centre + dist(t)) % 360.0                       # the signed distance IS the offset from the level
    built = cr.band_intervals(position_at, BODY, [centre], ORB, LO, HI)
    mine = _derive(dist)
    assert len(built) == len(mine) == 1
    assert abs((built[0][0] - mine[0]["t_in"]).total_seconds()) < 3 and abs((built[0][1] - mine[0]["t_out"]).total_seconds()) < 3
    # and at the edge: a curve whose minimum is exactly the orb on a grid instant is inside for both
    edge = lambda t: 1.0 + 0.3 * _x(t) ** 2
    pos_edge = lambda body, t: (centre + edge(t)) % 360.0
    b = cr.band_intervals(pos_edge, BODY, [centre], ORB, LO, HI)
    m = _derive(edge)
    assert (len(b) > 0) == (len(m) > 0), (b, m)


def test_the_verifiers_own_speed_table_equals_the_kernels_stated_bounds_as_data():
    from services.gochara_kernel import contact_reconstruct as cr
    assert nm.VMAX_DPS == dict(cr.VMAX_DPS)


def test_an_understated_speed_bound_is_refused_and_an_unknown_body_too():
    crossing = lambda t: 0.4 * (_x(t) - 1800 / 86400.0)                              # a real crossing 30 minutes off the hour grid
    with pytest.raises(nm.NearMissError, match="speed_bound_below_table"):
        _derive(crossing, vmax_dps=0.8)       # 20% below Mars' 1.0
    assert [r["state"] for r in _derive(crossing)] == ["contact"]
    assert _derive(parabola(0.5, 0.3), vmax_dps=5.0)[0]["state"] == "near_miss"   # a larger bound is fine
    with pytest.raises(nm.NearMissError, match="unknown_body"):
        _derive(parabola(0.5, 0.3), body="pluto")


def test_a_stretch_across_the_0_360_wrap_is_found_and_measured_correctly():
    for centre in (359.9, 0.05, 180.0):
        out = _derive(parabola(0.5, 0.3), centre=centre)
        assert [r["state"] for r in out] == ["near_miss"], centre
        assert out[0]["clearance_deg"] == pytest.approx(0.5, abs=1e-3)
    out = _derive(lambda t: -(0.5 + 0.3 * _x(t) ** 2), centre=0.1)                                 # approaching from the negative side of the wrap
    assert [r["state"] for r in out] == ["near_miss"] and out[0]["clearance_deg"] == pytest.approx(0.5, abs=1e-3)


def _named(fn, code):
    """the call must raise NearMissError carrying `code`; any other outcome (another exception, no exception) is an assertion failure"""
    try:
        fn()
    except nm.NearMissError as exc:
        assert code in str(exc), str(exc)
    except Exception as exc:                                                    # noqa: BLE001
        raise AssertionError(f"not a named refusal: {type(exc).__name__}: {exc}") from None
    else:
        raise AssertionError(f"no refusal ({code} expected)")


def test_an_empty_window_is_a_named_refusal_not_an_index_error():
    _named(lambda: nm.derive_near_misses(lambda b, t: 100.0, BODY, [100.0], HI, HI, orb_deg=ORB), "window_empty")
    _named(lambda: nm.derive_near_misses(lambda b, t: 100.0, BODY, [100.0], HI, LO, orb_deg=ORB), "window_empty")


def test_a_57_minute_dip_that_bottoms_between_the_hourly_samples_is_found_because_the_stretches_come_from_the_kernels_band():
    from services.gochara_kernel import contact_reconstruct as cr
    x0 = 1800 / 86400.0
    dist = lambda t: 0.98 + abs(_x(t) - x0)                                                       # Mars' bound: in band only for |x - x0| <= 0.02 d
    assert all(dist(LO + timedelta(hours=k)) > ORB for k in range(0, 24 * 30))                      # an hourly sampler never sees it
    position_at = lambda body, t: (CENTRE + dist(t)) % 360.0
    built = cr.band_intervals(position_at, BODY, [CENTRE], ORB, LO, HI)
    mine = _derive(dist)
    assert len(built) == len(mine) == 1
    assert (mine[0]["t_in"], mine[0]["t_out"]) == built[0]                                         # the stretch IS the kernel's
    assert abs((mine[0]["t_out"] - mine[0]["t_in"]).total_seconds() - 57.6 * 60) < 5
    assert mine[0]["state"] == "near_miss" and mine[0]["clearance_deg"] == pytest.approx(0.98, abs=2e-3)



def test_a_row_missing_a_field_is_a_named_refusal_not_a_crash():
    row = _row()
    del row["t_in"]
    assert nm.row_problems(row)[0].startswith("row_field_missing") and "t_in" in nm.row_problems(row)[0]
    assert nm.row_problems({})[0].startswith("row_field_missing")


def test_edge_unplaced_needs_the_domain_and_a_stretch_that_touches_it():
    row = _row(closest_state="edge_unplaced", t_closest=None, junction=None, junction_complete=False)
    domain = (utc(2000, 1, 1), utc(2100, 1, 1))
    assert any(x == "edge_unplaced_unverifiable_without_domain" for x in nm.row_problems(row))
    assert any(x == "edge_unplaced_not_at_domain_edge" for x in nm.row_problems(row, domain=domain))             # a mid-horizon stretch
    assert nm.row_problems(dict(row, t_in=utc(2000, 1, 1)), domain=domain) == []
    assert nm.row_problems(dict(row, t_out=utc(2100, 1, 1), t_in=utc(2099, 12, 1)), domain=domain) == []


def test_proximity_stored_rounded_to_four_decimals_is_accepted_and_a_wrong_one_is_not():
    assert nm.row_problems(_row(clearance_deg=0.3333, orb_deg=1.0, proximity=0.6667)) == []
    assert any(x.startswith("proximity_not_one_minus") for x in nm.row_problems(_row(clearance_deg=0.3333, orb_deg=1.0, proximity=0.67)))


def test_ordinal_ties_follow_a_total_key_and_an_exact_duplicate_is_refused():
    a = {"t_in": utc(2001, 1, 1), "t_out": utc(2001, 1, 5), "t_closest": utc(2001, 1, 2)}
    b = {"t_in": utc(2001, 1, 1), "t_out": utc(2001, 1, 9), "t_closest": utc(2001, 1, 2)}          # same t_closest and t_in, later t_out
    try:
        got_ba, got_ab = nm.assign_ordinals([b, a]), nm.assign_ordinals([a, b])
    except nm.NearMissError as exc:                                  # two DISTINCT stretches must never be called duplicates
        raise AssertionError(f"distinct stretches refused as duplicates: {exc}") from None
    assert got_ba == got_ab == [(1, a), (2, b)]
    with pytest.raises(nm.NearMissError, match="duplicate_near_miss"):
        nm.assign_ordinals([a, dict(a)])
    u1 = {"t_in": utc(2002, 1, 1), "t_out": utc(2002, 1, 5), "t_closest": None}
    with pytest.raises(nm.NearMissError, match="duplicate_near_miss"):
        nm.assign_ordinals([u1, dict(u1)])


def test_a_pd_boundary_is_not_a_junction_kind():
    with pytest.raises(nm.NearMissError, match="junction_kind_unknown"):
        nm.junction_field(utc(2000, 3, 1), utc(2000, 3, 11), [("dasha_pd_boundary", utc(2000, 3, 2))], coverage_complete=True)
    assert nm.JUNCTION_KINDS == {"sign_ingress", "nakshatra_ingress", "dasha_md_ad_boundary"}


def test_stored_decimals_are_accepted_not_a_type_error():
    from decimal import Decimal
    assert nm.row_problems(_row(clearance_deg=Decimal("0.3333"), orb_deg=Decimal("1.0"), proximity=Decimal("0.6667"))) == []
    assert any(x.startswith("proximity_not_one_minus") for x in nm.row_problems(_row(clearance_deg=Decimal("0.3333"), orb_deg=Decimal("1.0"), proximity=Decimal("0.7"))))


def test_a_year_long_slow_body_stretch_is_certified_without_a_sample_blow_up():
    # Saturn: a stretch of 400 days around a 0.3 degree dip; the first pass is capped at MAX_SAMPLES steps
    slow = lambda t: 0.3 + 0.5 * (_x(t) / 200.0) ** 2
    res = nm._analyse_stretch(slow, TC - timedelta(days=200), TC + timedelta(days=200), 0.2)
    assert res["rooted"] is False and res["certified"] is True and res["clearance_deg"] == pytest.approx(0.3, abs=1e-3)


# ── amendments of review VERIFIER-CODEX-1 (3187) ─────────────────────────────────────────────────────────────────────
def test_with_two_nearly_equal_minima_both_times_are_candidates_and_an_unrelated_time_is_refused():
    # the reviewer's curve: a true minimum 0.4998 at +0.5 h (x = 25/48 d from TC) and a near-equal 0.5000 about a day earlier
    d = lambda t: min(1.1, 0.5 + 0.2 * (_x(t) + 0.5) ** 2, 0.4998 + abs(_x(t) - 25 / 48))
    out = _derive(d, lo=TC - timedelta(days=3), hi=TC + timedelta(days=3))
    assert [r["state"] for r in out] == ["near_miss"] and out[0]["closest_certified"] is True
    r = out[0]
    assert r["clearance_deg"] == pytest.approx(0.4998, abs=6e-4)
    assert len(r["closest_candidates"]) == 2                                                     # the value is certified, the TIME is one of two places
    true_t, early_t = TC + timedelta(days=25 / 48), TC - timedelta(days=0.5)
    st = lambda t: dict(_stored(r["t_in"], r["t_out"], clearance=0.4998), t_closest=t, closest_state="placed")            # noqa: E731
    cmp = lambda t: nm.compare_sets([r], [st(t)], junction_source=NO_JUNCTIONS, **ID)                                       # noqa: E731
    assert cmp(true_t) == []                                                                       # the true minimiser is accepted (the old code refused it)
    assert cmp(early_t) == []                                                                      # the near-equal one is within tolerance: a candidate too
    assert [x.split(":")[0] for x in cmp(TC + timedelta(days=2.5))] == ["near_miss_t_closest_mismatch"]                      # nowhere near either


def test_a_single_clear_minimum_has_one_candidate_interval_the_width_of_its_flat_bottom():
    r = _derive(parabola(0.5, 0.3))[0]
    assert len(r["closest_candidates"]) == 1
    lo, hi = r["closest_candidates"][0]
    assert lo <= TC <= hi and lo <= r["t_closest"] <= hi                                              # the true minimiser (TC) is inside
    # values within tol (5e-4 deg) of the minimum lie within sqrt(5e-4 / 0.3) = 0.041 d = about 1 h either side: the interval says so, no more
    assert 1.5 * 3600 <= (hi - lo).total_seconds() <= 5 * 3600


def test_stored_ordinal_orb_and_object_identity_are_bound_to_the_rederived_object():
    w = _nm(utc(2000, 3, 1), utc(2000, 3, 4), clearance=0.5)
    ok = _stored(utc(2000, 3, 1), utc(2000, 3, 4), clearance=0.5)
    assert nm.compare_sets([w], [ok], junction_source=NO_JUNCTIONS, **ID) == []
    assert [x.split(":")[0] for x in nm.compare_sets([w], [dict(ok, ordinal=999)], junction_source=NO_JUNCTIONS, **ID)] == ["near_miss_ordinal_mismatch"]
    assert [x.split(":")[0] for x in nm.compare_sets([w], [dict(ok, orb_deg=5.0, proximity=0.9)], junction_source=NO_JUNCTIONS, **ID)] == ["near_miss_orb_mismatch"]
    assert [x.split(":")[0] for x in nm.compare_sets([w], [dict(ok, object_id="other")], junction_source=NO_JUNCTIONS, **ID)] == ["near_miss_object_mismatch"]
    w2 = _nm(utc(2000, 5, 1), utc(2000, 5, 4), clearance=0.4)                                      # the full-domain ordering is by closest time: w then w2
    s2 = _stored(utc(2000, 5, 1), utc(2000, 5, 4), clearance=0.4, ordinal=2)
    assert nm.compare_sets([w, w2], [ok, s2], junction_source=NO_JUNCTIONS, **ID) == []
    swapped = [dict(ok, ordinal=2), dict(s2, ordinal=1)]
    assert sorted(x.split(":")[0] for x in nm.compare_sets([w, w2], swapped, junction_source=NO_JUNCTIONS, **ID)) == ["near_miss_ordinal_mismatch"] * 2
    with pytest.raises(nm.NearMissError, match="non_finite"):
        nm.compare_sets([w], [ok], junction_source=NO_JUNCTIONS, expected_orb_deg=float("nan"), expected_object_id="obj-1")


def test_decimals_are_normalised_at_the_comparison_boundary_and_non_finite_values_are_refused():
    from decimal import Decimal
    w = _nm(utc(2000, 3, 1), utc(2000, 3, 4), clearance=0.5)
    ok = _stored(utc(2000, 3, 1), utc(2000, 3, 4), clearance=0.5)
    dec = dict(ok, clearance_deg=Decimal("0.5"), orb_deg=Decimal("1.0"))
    assert nm.compare_sets([w], [dec], junction_source=NO_JUNCTIONS, **ID) == []                  # the reviewer's TypeError case
    nan = float("nan")
    starts = lambda problems, code: any(x.startswith(code) for x in problems)                    # noqa: E731
    assert starts(nm.row_problems(_row(proximity=nan)), "non_finite_value")
    assert starts(nm.row_problems(_row(clearance_deg=float("inf"), proximity=0.1)), "non_finite_value")
    assert starts(nm.compare_sets([w], [dict(ok, clearance_deg=nan)], junction_source=NO_JUNCTIONS, **ID), "non_finite_value")
    assert starts(nm.row_problems(_row(t_in=None)), "row_field_missing")                         # present-but-NULL is a missing field, not a TypeError
    assert starts(nm.row_problems(_row(ordinal=None)), "row_field_missing")
    assert any(x.startswith("ordinal_not_a_positive_integer") for x in nm.row_problems(_row(ordinal=0)))


def test_a_non_finite_position_is_geometry_unavailable_never_nothing_found():
    with pytest.raises(nm.NearMissError, match="geometry_unavailable"):
        nm.derive_near_misses(lambda b, t: float("nan"), BODY, [100.0], LO, LO + timedelta(hours=1), orb_deg=ORB)
    with pytest.raises(nm.NearMissError, match="geometry_unavailable"):
        nm.derive_near_misses(lambda b, t: None, BODY, [100.0], LO, LO + timedelta(hours=1), orb_deg=ORB)
    with pytest.raises(nm.NearMissError, match="non_finite"):
        nm.derive_near_misses(lambda b, t: 100.0, BODY, [float("nan")], LO, HI, orb_deg=ORB)
    with pytest.raises(nm.NearMissError, match="non_finite"):
        nm.derive_near_misses(lambda b, t: 100.0, BODY, [100.0], LO, HI, orb_deg=float("inf"))


def test_the_search_carries_the_band_detectors_named_limit_and_is_never_complete_or_verified_empty():
    from services.gochara_kernel import contact_reconstruct as cr
    # the reviewer's 18.9-second in-band dip at Mars' bound: the shared detector finds nothing shorter than its resolution
    d = lambda t: 1 - 0.0001 + (((t - LO).total_seconds() - 21) ** 2 / 86400.0 ** 2 + 0.00001 ** 2) ** 0.5 - 0.00001
    out = _derive(d, lo=LO, hi=LO + timedelta(hours=6))
    assert list(out) == [] and out.resolution_limit_seconds == cr.MIN_EXCURSION_SECONDS == 60
    assert out.complete is False and out.verified_empty is False and "60" in out.named_limit
    full = _derive(parabola(0.5, 0.3))
    assert full.complete is False and full.verified_empty is False
    ok = {"searched_complete": True, "horizon": H, "count": 0, "resolution_limit_seconds": 60.0}
    assert nm.coverage_problems(ok, 0, horizon=H) == []
    assert any(x.startswith("near_miss_search_resolution_unstated") for x in
               nm.coverage_problems({k: v for k, v in ok.items() if k != "resolution_limit_seconds"}, 0, horizon=H))


def test_a_junction_iterator_is_consumed_once_and_serves_every_row():
    a, b = utc(2000, 3, 1), utc(2000, 3, 4)
    assert nm.junction_field(a, b, iter([("sign_ingress", a)]), coverage_complete=True) == {"kinds": ["sign_ingress"], "complete": True}
    w1, w2 = _nm(a, b), _nm(utc(2000, 5, 1), utc(2000, 5, 4))
    s1 = _stored(a, b, junction=["sign_ingress"], ordinal=1)
    s2 = _stored(utc(2000, 5, 1), utc(2000, 5, 4), junction=["sign_ingress"], ordinal=2)
    events = iter([("sign_ingress", a), ("sign_ingress", utc(2000, 5, 2))])
    assert nm.compare_sets([w1, w2], [s1, s2], junction_source=(events, True), **ID) == []         # a one-shot iterator would leave the second row empty


def test_a_certificate_that_would_need_too_much_work_is_uncertified_not_a_silent_blow_up():
    flat = lambda t: 0.5                                                                           # a flat 0.5 degree at the Moon's bound: nothing can be pruned
    res = nm._analyse_stretch(flat, TC, TC + timedelta(days=3), 16.0)
    assert res["certified"] is False and res["reason"] == "work_budget_exhausted" and res["closest_certified"] is False
    assert res["closest_candidates"] == [(TC, TC + timedelta(days=3))]                              # the whole stretch: no time is claimed
    small = nm._analyse_stretch(parabola(0.5, 0.3), TC - timedelta(hours=3), TC + timedelta(hours=3), 1.0, max_evals=5)
    assert small["certified"] is False and small["reason"] == "work_budget_exhausted"


# ── round 2 (VERIFIER-CODEX-2) ───────────────────────────────────────────────────────────────────────────────────────
def test_the_floor_decision_is_made_on_a_refined_certificate_never_on_an_approximate_minimum():
    # the reviewer's case: a true minimum 0.0048 (below the 0.005 floor) must not pass as a near-miss because the coarse search read 0.0051
    x0 = 1800 / 86400.0
    narrow = lambda t: 0.0048 + abs(_x(t) - x0)                                                     # Mars' bound, a V whose tip lies between samples
    out = _derive(narrow)
    assert out and all(r["state"] != "near_miss" for r in out)
    assert out[0]["state"] == "unresolved" and out[0]["reason"] in ("clearance_below_min_approach", "clearance_straddles_min_approach")
    # a minimum just ABOVE the floor is decided near_miss once refined; one just BELOW is unresolved by name
    above = _derive(parabola(0.0052, 0.3))                       # 2e-4 above the floor: the first coarse certificate straddles it, the refined one does not
    below = _derive(parabola(0.00497, 0.3))
    assert [r["state"] for r in above] == ["near_miss"] and above[0]["clearance_deg"] == pytest.approx(0.0052, abs=5e-5)
    assert [r["state"] for r in below] == ["unresolved"] and below[0]["reason"] == "clearance_below_min_approach"
    # too close to the floor for the finest certificate this speed bound allows (about 6e-6 deg at Mars' bound): undecided, by name, never near_miss
    edge = _derive(parabola(0.00503, 0.3))
    assert [r["state"] for r in edge] == ["unresolved"] and edge[0]["reason"] == "clearance_straddles_min_approach"


def test_classify_stretch_names_a_certificate_that_straddles_the_floor():
    c = nm.classify_stretch
    assert c(rooted=False, complete=True, clearance_deg=0.0051, clearance_certified=True, clearance_tol=5e-4) == ("unresolved", "clearance_straddles_min_approach")
    assert c(rooted=False, complete=True, clearance_deg=0.0051, clearance_certified=True, clearance_tol=5e-5) == ("near_miss", None)
    assert c(rooted=False, complete=True, clearance_deg=0.0048, clearance_certified=True, clearance_tol=5e-4) == ("unresolved", "clearance_below_min_approach")


def test_a_placed_row_needs_affirmative_closest_time_evidence_not_any_time_in_the_stretch():
    ok = _stored(utc(2000, 3, 1), utc(2000, 3, 4), clearance=0.4)
    cmp = lambda w: nm.compare_sets([w], [ok], junction_source=NO_JUNCTIONS, **ID)                  # noqa: E731
    base = _nm(utc(2000, 3, 1), utc(2000, 3, 4))
    assert cmp(base) == []
    for bad in (dict(base, closest_candidates=[]), dict(base, closest_candidates=None), {k: v for k, v in base.items() if k != "closest_candidates"},
                dict(base, closest_certified=False), {k: v for k, v in base.items() if k != "closest_certified"}):
        assert [x.split(":")[0] for x in cmp(bad)] == ["near_miss_closest_evidence_missing"], bad
    unplaced = dict(ok, closest_state="edge_unplaced", t_closest=None)
    assert nm.compare_sets([dict(base, closest_certified=False)], [unplaced], junction_source=NO_JUNCTIONS, **ID) == []      # an unplaced row claims no time


def test_a_stored_row_with_a_null_field_is_a_named_refusal_in_the_set_comparison():
    w = _nm(utc(2000, 3, 1), utc(2000, 3, 4))
    ok = _stored(utc(2000, 3, 1), utc(2000, 3, 4))
    for k in ("t_in", "t_out", "clearance_deg", "ordinal", "object_id"):
        try:
            out = nm.compare_sets([w], [dict(ok, **{k: None})], junction_source=NO_JUNCTIONS, **ID)
        except Exception as exc:                                                    # noqa: BLE001
            raise AssertionError(f"a NULL {k} must be a named refusal, not {type(exc).__name__}: {exc}") from None
        assert any(x.startswith("row_field_missing") for x in out), (k, out)


def test_the_band_search_has_a_work_budget_and_names_its_exhaustion():
    calls = [0]

    def counting(b, t):
        calls[0] += 1
        return 100.0 + 0.5 + 0.3 * _x(t) ** 2
    with pytest.raises(nm.NearMissError, match="band_search_work_budget_exhausted"):
        nm.derive_near_misses(counting, BODY, [100.0], LO, HI, orb_deg=ORB, max_position_calls=20)
    assert calls[0] <= 21


# ── round 3 (VERIFIER-CODEX-3) ───────────────────────────────────────────────────────────────────────────────────────
def test_a_stored_closest_time_inside_a_candidate_interval_but_far_from_the_minimum_is_refused():
    # the reviewer's curve: |d| is 0.5 at 12:00 and rises with a sqrt flank; the candidate interval is wide, but 5 minutes off the minimum the
    # separation is already 0.5027 deg
    d = lambda t: min(1.1, 0.5 + (_x(t) ** 2 + 0.000001) ** 0.5 - 0.001)
    r = _derive(d, lo=TC - timedelta(days=3), hi=TC + timedelta(days=3))[0]
    assert r["state"] == "near_miss" and r["closest_certified"] is True
    lo, hi = r["closest_candidates"][0]
    assert lo <= TC - timedelta(minutes=5) <= hi                                      # inside the certified interval...
    stored = lambda t: dict(_stored(r["t_in"], r["t_out"], clearance=0.5), t_closest=t, closest_state="placed")      # noqa: E731
    cmp = lambda t: nm.compare_sets([r], [stored(t)], junction_source=NO_JUNCTIONS, **ID)                           # noqa: E731
    bad = cmp(TC - timedelta(minutes=5, seconds=10))                                  # the reviewer's 11:54:50
    assert [x.split(":")[0] for x in bad] == ["near_miss_t_closest_separation_mismatch"], bad
    assert abs(d(TC - timedelta(minutes=5, seconds=10)) - 0.5) > 0.002                # ...yet 0.0027 deg from the minimum
    assert cmp(TC) == [] and cmp(r["t_closest"]) == []                                # the true minimiser and the certified one are accepted


def test_the_closest_time_check_needs_the_geometry_to_evaluate_the_stored_instant():
    w = _nm(utc(2000, 3, 1), utc(2000, 3, 4))
    ok = _stored(utc(2000, 3, 1), utc(2000, 3, 4), clearance=0.4)
    no_geom = {k: v for k, v in w.items() if k != "distance_at"}
    try:
        out = nm.compare_sets([no_geom], [ok], junction_source=NO_JUNCTIONS, **ID)
    except Exception as exc:                                                    # noqa: BLE001
        raise AssertionError(f"missing geometry must be a named refusal, not {type(exc).__name__}: {exc}") from None
    assert [x.split(":")[0] for x in out] == ["near_miss_closest_evidence_missing"]


def test_a_tolerated_endpoint_shift_cannot_hide_a_junction_because_the_junction_is_recomputed_on_the_rederived_interval():
    d = lambda t: min(1.1, 0.5 + 0.2 * _x(t) ** 2)
    r = _derive(d)[0]
    events = [("dasha_md_ad_boundary", r["t_in"])]                                   # an MD/AD boundary exactly at the re-derived t_in
    shifted = dict(_stored(r["t_in"] + timedelta(seconds=1), r["t_out"], clearance=r["clearance_deg"], junction=[], complete=True),
                   t_closest=r["t_closest"], closest_state="placed")
    out = nm.compare_sets([r], [shifted], junction_source=(events, True), **ID)
    assert [x.split(":")[0] for x in out] == ["near_miss_junction_mismatch"], out
    honest = dict(shifted, t_in=r["t_in"] + timedelta(seconds=1), junction=["dasha_md_ad_boundary"])
    assert nm.compare_sets([r], [honest], junction_source=(events, True), **ID) == []             # the junction the re-derived interval contains
