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
                t_closest=utc(2000, 3, 2), junction=["sign_ingress"], junction_complete=True)
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
    return {"state": "near_miss", "reason": None, "t_in": t_in, "t_out": t_out, "clearance_deg": clearance, "t_closest": t_in + (t_out - t_in) / 2}


def _stored(t_in, t_out, clearance=0.4, junction=(), complete=True, closest="mid"):
    mid = t_in + (t_out - t_in) / 2
    return {"t_in": t_in, "t_out": t_out, "clearance_deg": clearance, "closest_state": "placed", "t_closest": mid,
            "junction": None if junction is None else list(junction), "junction_complete": complete}


NO_JUNCTIONS = ([], True)


def test_the_stored_set_must_equal_the_rederived_set_and_the_reported_count():
    cmp = lambda w, st, **kw: nm.compare_sets(w, st, junction_source=NO_JUNCTIONS, **kw)            # noqa: E731
    w1, w2 = _nm(utc(2000, 3, 1), utc(2000, 3, 4)), _nm(utc(2000, 5, 1), utc(2000, 5, 4))
    s1, s2 = _stored(utc(2000, 3, 1, 0, 0, 1), utc(2000, 3, 4)), _stored(utc(2000, 5, 1), utc(2000, 5, 4))
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
    assert any(x.startswith("near_miss_missing") for x in nm.compare_sets([w1, w2], [s], junction_source=NO_JUNCTIONS))


def test_a_stored_row_with_the_right_interval_but_a_wrong_clearance_or_closest_instant_is_refused():
    w = _nm(utc(2000, 3, 1), utc(2000, 3, 4), clearance=0.5)
    ok = _stored(utc(2000, 3, 1), utc(2000, 3, 4), clearance=0.5)
    assert nm.compare_sets([w], [ok], junction_source=NO_JUNCTIONS) == []
    assert nm.compare_sets([w], [dict(ok, clearance_deg=0.5 + 0.0009)], junction_source=NO_JUNCTIONS) == []               # inside the tolerance
    assert [x.split(":")[0] for x in nm.compare_sets([w], [dict(ok, clearance_deg=0.5 + 0.01)], junction_source=NO_JUNCTIONS)] == ["near_miss_clearance_mismatch"]   # just outside it
    bad_c = nm.compare_sets([w], [dict(ok, clearance_deg=0.05)], junction_source=NO_JUNCTIONS)                           # the reviewer's 0.05 vs 0.5
    assert [x.split(":")[0] for x in bad_c] == ["near_miss_clearance_mismatch"]
    late = dict(ok, t_closest=ok["t_closest"] + timedelta(hours=11))
    assert [x.split(":")[0] for x in nm.compare_sets([w], [late], junction_source=NO_JUNCTIONS)] == ["near_miss_t_closest_mismatch"]
    near = dict(ok, t_closest=ok["t_closest"] + timedelta(minutes=9))
    assert nm.compare_sets([w], [near], junction_source=NO_JUNCTIONS) == []
    unplaced = dict(ok, closest_state="edge_unplaced", t_closest=None)
    assert nm.compare_sets([w], [unplaced], junction_source=NO_JUNCTIONS) == []                                          # row_problems judges the claim


def test_the_stored_junction_must_equal_the_junction_recomputed_from_the_pinned_sources():
    w = _nm(utc(2000, 3, 1), utc(2000, 3, 4))
    events = [("sign_ingress", utc(2000, 3, 2)), ("dasha_md_ad_boundary", utc(2000, 3, 4))]          # the second is AT t_out: excluded
    good = _stored(utc(2000, 3, 1), utc(2000, 3, 4), junction=["sign_ingress"])
    assert nm.compare_sets([w], [good], junction_source=(events, True)) == []
    fabricated = _stored(utc(2000, 3, 1), utc(2000, 3, 4), junction=["dasha_md_ad_boundary"])        # the reviewer's probe: no such event inside
    assert [x.split(":")[0] for x in nm.compare_sets([w], [fabricated], junction_source=(events, True))] == ["near_miss_junction_mismatch"]
    empty_claimed = _stored(utc(2000, 3, 1), utc(2000, 3, 4), junction=[])                           # an empty list where a junction exists
    assert nm.compare_sets([w], [empty_claimed], junction_source=(events, True))[0].startswith("near_miss_junction_mismatch")
    unknown = _stored(utc(2000, 3, 1), utc(2000, 3, 4), junction=None, complete=False)                # missing coverage = unknown
    assert nm.compare_sets([w], [unknown], junction_source=(events, False)) == []
    assert nm.compare_sets([w], [good], junction_source=(events, False))[0].startswith("near_miss_junction_mismatch")


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
