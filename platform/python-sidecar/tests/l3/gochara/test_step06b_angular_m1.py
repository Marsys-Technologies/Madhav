"""A5.4 angular_m1 — proof battery for the N1 repair of step06b's M-1 kernel.

Sealed doctrine FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0, finding N1:
step06b_windows_projection.py scored the M-1 `linear_no_box` activity as a
TIME triangle over [t_in, t_exact, t_out]. The ruled kernel (D-RQ2) is
ANGULAR: activity(t) = 1 − min(|Δλ(t)|/orb, 1), where Δλ(t) is the
shortest-arc separation between the transiting body's longitude at t and the
contact's target longitude — the algebra engine.py's _compute_activity_v3
applies under activity_shape='linear_no_box' (engine.py:1147-1155).

Every test here is pure arithmetic: the ephemeris accessor is injected as
(body, jd) -> longitude, so no Swiss calls and no DB. Each test would FAIL
against the removed time-triangle `linear_no_box_decay` (the mutation check
in test_quadratic_body_diverges_from_time_triangle makes the divergence
explicit with a stated epsilon).
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from .test_step06b_windows_projection import (  # noqa: E402
    WRITER_PATH, _ctx, _open_gates)

UTC = timezone.utc


def _load_writer():
    spec = importlib.util.spec_from_file_location(
        "step06b_windows_projection_a54", WRITER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


w = _load_writer()

ORB = 5.0
TARGET = 100.0
T_EXACT = 2460100.0  # arbitrary JD anchor; no calendar semantics needed


def _time_triangle(t_jd, t_in, t_exact, t_out):
    """The REMOVED defective kernel, re-stated here verbatim (from the
    pre-repair step06b_windows_projection.py:209-228) so the mutation checks
    below quantify the divergence against it."""
    if t_jd <= t_in or t_jd >= t_out:
        return 0.0
    if t_jd <= t_exact:
        return (t_jd - t_in) / (t_exact - t_in)
    return (t_out - t_jd) / (t_out - t_exact)


def _contact(cid, t_in, t_exact, t_out, *, target=TARGET, orb=ORB,
             body="Syn"):
    return {
        "contact_id": cid, "body": body, "relation": "conjunction",
        "target_type": "karaka", "target_ref": "Venus",
        "target_longitude_deg": target, "orb_max_deg": orb,
        "completeness_state": "applied",
        "_primitive": "degree_contact",
        "_target_lon_deg": target, "_orb_deg": orb,
        "_t_in_jd": t_in, "_t_exact_jd": t_exact, "_t_out_jd": t_out,
    }


def _activity_at(contacts, pos_fn, t_jd, weights=None):
    """Evaluate ONLY the activity term (isolate the kernel from promise /
    permission / gates)."""
    ctx = _ctx(weights_by_ref=weights or {"Venus": 1.0})
    evaluate = w.make_eval_fn(ctx, contacts, _open_gates,
                              planet_pos_fn=pos_fn)
    return evaluate(t_jd)["activity"]


def _shortest_arc(lon, target):
    return abs(((lon - target + 180.0) % 360.0) - 180.0)


# ── 1. non-constant angular speed (quadratic body) ───────────────────────────

# λ(t) = λ0 + v0·Δt + a·Δt², anchored so λ(t_exact) = TARGET.
V0 = 0.02        # °/day at t_exact (slow body)
ACC = 0.004      # °/day² — speed roughly triples over +10 days


def _quad_lon(t):
    dt = t - T_EXACT
    return (TARGET + V0 * dt + ACC * dt * dt) % 360.0


def _quad_pos(body, jd):
    return _quad_lon(jd)


def test_quadratic_body_matches_angular_formula_exactly():
    contact = _contact("q1", T_EXACT - 20.0, T_EXACT, T_EXACT + 20.0)
    for dt in (-15.0, -7.5, -1.0, 0.0, 1.0, 7.5, 15.0):
        t = T_EXACT + dt
        expected = 1.0 - min(_shortest_arc(_quad_lon(t), TARGET) / ORB, 1.0)
        got = _activity_at([contact], _quad_pos, t)
        assert got == pytest.approx(expected, abs=1e-12), (dt, got, expected)
        # and the value is the pure kernel itself (weight 1.0 => noisy-OR
        # over one sentence is the identity)
        assert got == pytest.approx(
            w.angular_orb_decay(_quad_lon(t), TARGET, ORB), abs=1e-15)


def test_quadratic_body_diverges_from_time_triangle():
    """Mutation check: at instants where angular speed departs from the
    span-average, the old time triangle and the angular kernel disagree by
    more than epsilon — the pre-repair code cannot produce these numbers."""
    t_in, t_out = T_EXACT - 20.0, T_EXACT + 20.0
    contact = _contact("q1", t_in, T_EXACT, t_out)
    epsilon = 0.05  # activity units — an order above float noise
    diverged = 0
    for dt in (-18.0, -12.0, -6.0, 6.0, 12.0, 18.0):
        t = T_EXACT + dt
        angular = _activity_at([contact], _quad_pos, t)
        triangle = _time_triangle(t, t_in, T_EXACT, t_out)
        if abs(angular - triangle) > epsilon:
            diverged += 1
        # late approach: the body accelerates toward the target, so it is
        # angularly CLOSER than the time triangle assumes
        if dt > 0:
            assert angular > triangle
    assert diverged >= 4, "kernel is not distinguishable from the triangle"


# ── 2. station-like dwell ────────────────────────────────────────────────────

# λ(t) = TARGET − k·(t − t_s)² with t_s = t_exact: the body is parked AT the
# target at the station (speed → 0), so angular activity stays at 1.0 for
# days while the time triangle falls linearly to 0.5 at +10 days.
K_STAT = 0.002  # °/day² — |Δλ| = 0.2° at ±10 days


def _stat_lon(t):
    dt = t - T_EXACT
    return (TARGET - K_STAT * dt * dt) % 360.0


def _stat_pos(body, jd):
    return _stat_lon(jd)


def test_station_like_dwell_keeps_activity_high():
    t_in, t_out = T_EXACT - 20.0, T_EXACT + 20.0
    contact = _contact("s1", t_in, T_EXACT, t_out)
    bound = 1.0 - (K_STAT * 100.0) / ORB  # 0.96 at |Δt| = 10 days
    for dt in (-10.0, -5.0, -1.0, 0.0, 1.0, 5.0, 10.0):
        t = T_EXACT + dt
        angular = _activity_at([contact], _stat_pos, t)
        expected = 1.0 - min(_shortest_arc(_stat_lon(t), TARGET) / ORB, 1.0)
        assert angular == pytest.approx(expected, abs=1e-12)
        assert angular >= bound - 1e-12
        # the time triangle would have decayed to <= 0.75 here — the
        # divergence the N1 finding names ("parked near the boundary")
        if abs(dt) >= 5.0:
            triangle = _time_triangle(t, t_in, T_EXACT, t_out)
            assert angular - triangle > 0.2


# ── 3. 0°-seam continuity ────────────────────────────────────────────────────

SEAM_TARGET = 359.5


def _seam_lon(t):
    # constant 1°/day through the seam: λ(t_exact) = 0.0
    return (1.0 * (t - T_EXACT)) % 360.0


def _seam_pos(body, jd):
    return _seam_lon(jd)


def test_shortest_arc_across_zero_seam_is_continuous():
    contact = _contact("z1", T_EXACT - 5.0, T_EXACT, T_EXACT + 5.0,
                       target=SEAM_TARGET)
    prev = None
    # half-day steps across the seam: separation crosses 359.5 -> 0 -> 0.5
    # with no jump; activity is exactly 1 − |Δλ|/orb at every instant.
    for i in range(-8, 9):
        t = T_EXACT + i * 0.5
        expected = 1.0 - min(_shortest_arc(_seam_lon(t), SEAM_TARGET) / ORB, 1.0)
        got = _activity_at([contact], _seam_pos, t)
        assert got == pytest.approx(expected, abs=1e-12)
        if prev is not None:
            assert abs(got - prev) <= 0.5 / ORB + 1e-9  # Lipschitz, no seam jump
        prev = got
    # sanity: the seam is actually crossed inside the sampled range
    assert _seam_lon(T_EXACT - 0.25) > 359.0
    assert _seam_lon(T_EXACT + 0.25) < 1.0
    # peak (shortest separation 0.5°, not a wrap artifact of 359°)
    assert _activity_at([contact], _seam_pos, T_EXACT) == pytest.approx(
        1.0 - 0.5 / ORB)


# ── 4. honesty guards ────────────────────────────────────────────────────────


def test_missing_target_longitude_aborts():
    """A contact without target_longitude_deg cannot be angularly scored;
    the run aborts (no F-08 swallow, no fabricated fallback)."""
    contact = _contact("m1", T_EXACT - 10.0, T_EXACT, T_EXACT + 10.0)
    del contact["_target_lon_deg"]
    contact["target_longitude_deg"] = None
    ctx = _ctx()
    evaluate = w.make_eval_fn(ctx, [contact], _open_gates,
                              planet_pos_fn=_quad_pos)
    with pytest.raises(ValueError, match="target_longitude_deg"):
        evaluate(T_EXACT)


def test_orb_max_deg_falls_back_to_5deg():
    contact = _contact("f1", T_EXACT - 10.0, T_EXACT, T_EXACT + 10.0)
    contact["_orb_deg"] = None
    contact["orb_max_deg"] = None
    # 4° off target: at the 5.0° fallback orb this is 0.2; at any other orb
    # it would differ — pins the fallback value.
    pos = lambda body, jd: (TARGET + 4.0) % 360.0  # noqa: E731
    assert _activity_at([contact], pos, T_EXACT) == pytest.approx(0.2)
    assert w.ORB_MAX_DEG_FALLBACK == 5.0


def test_clamp_zero_beyond_orb_and_eval_never_negative():
    contact = _contact("c1", T_EXACT - 10.0, T_EXACT, T_EXACT + 10.0)
    pos = lambda body, jd: (TARGET + 179.9) % 360.0  # noqa: E731
    assert w.angular_orb_decay(pos("Syn", T_EXACT), TARGET, ORB) == 0.0
    assert _activity_at([contact], pos, T_EXACT) == 0.0


# ── 5. ASTRA_REVIEW_A5_4 P1-1: aspect geometry + episode support + roots ─────
#
# The reviewer's executable probes: "Saturn's third aspect: target 100°,
# body 40°. Mars's fourth: target 100°, body 10°. Jupiter's ninth: target
# 100.31°, body 220.31°. All three exact-contact probes returned activity 0,
# rather than 1." and "two weight-0.5 conjunction records, 100 days apart,
# both contribute at the first episode: activity 0.75, rather than 0.5."


def _drishti(cid, aspect_deg, target, body_lon, *, t_exact=T_EXACT,
             body="Syn", target_ref="Venus"):
    c = _contact(cid, t_exact - 20.0, t_exact, t_exact + 20.0,
                 target=target, body=body)
    c.update({"relation": "drishti_contact", "_primitive": "drishti_contact",
              "aspect_deg": aspect_deg, "_aspect_deg": aspect_deg,
              "target_ref": target_ref})
    return c, (lambda b, jd: body_lon)


@pytest.mark.parametrize("label,aspect_deg,target,body_lon", [
    ("Saturn 3rd", 60.0, 100.0, 40.0),
    ("Mars 4th", 90.0, 100.0, 10.0),
    ("Jupiter 9th", 240.0, 100.31, 220.31),
    ("Saturn 10th (O-AD-4)", 270.0, 0.0, 90.0),
    ("Mars 8th (O-AD-2)", 210.0, 0.0, 150.0),
])
def test_exact_special_aspect_scores_one(label, aspect_deg, target, body_lon):
    """body = (target − angle) mod 360 ⇒ the aspect point sits ON the target
    ⇒ activity 1.0. Mutation caught: the pre-repair kernel read Δλ from the
    bare body longitude (|body − target| ≥ 60° ⇒ 0.0)."""
    c, pos = _drishti("a1", aspect_deg, target, body_lon)
    got = _activity_at([c], pos, T_EXACT)
    assert got == pytest.approx(1.0, abs=1e-12), label
    # the pre-repair value on the same fixture, for contrast (the mutation)
    assert w.angular_orb_decay(body_lon, target, ORB) == 0.0, label


def test_mirrored_aspect_direction_is_rejected():
    """The shipped mirror (#13: `target + angle`) would put Saturn's 3rd at
    body = target + 60 = 160°. That body scores 0 — the forward count is the
    only geometry the kernel honours (§6.2 inv 6, O-AD-3)."""
    c, pos = _drishti("m1", 60.0, 100.0, 160.0)
    assert _activity_at([c], pos, T_EXACT) == 0.0
    # and the forward body (40°) scores 1.0 on the same contact
    assert _activity_at([c], lambda b, jd: 40.0, T_EXACT) == pytest.approx(1.0)


def test_partial_aspect_orb_uses_aspect_point_not_body():
    """2° off the aspect point at a 5° orb ⇒ 0.6 exactly (1 − 2/5)."""
    c, pos = _drishti("p1", 90.0, 100.0, 12.0)  # aspect point 102°
    assert _activity_at([c], pos, T_EXACT) == pytest.approx(0.6)


def test_conjunction_ignores_zero_aspect_deg():
    """A non-dṛṣṭi contact carries aspect_deg 0 (ledger): the aspect point
    IS the body — the pre-existing conjunction battery above is unchanged."""
    c = _contact("c0", T_EXACT - 20.0, T_EXACT, T_EXACT + 20.0)
    c["_aspect_deg"] = 0.0
    assert _activity_at([c], lambda b, jd: TARGET, T_EXACT) == pytest.approx(1.0)


def test_separated_passes_do_not_stack_at_the_first_episode():
    """Two weight-0.5 conjunction records of ONE body over ONE target, 100
    days apart (a direct pass and a later re-crossing = two contacts, two
    occurrence ordinals). The body is parked on the target, so angularly
    both would score 1.0 at every instant. At the first episode only the
    first contact supports ⇒ 0.5. Mutation caught: without episode support
    both contribute ⇒ 1 − 0.5·0.5 = 0.75 (the reviewer's probe)."""
    c1 = _contact("pass1", T_EXACT - 10.0, T_EXACT, T_EXACT + 10.0)
    c2 = _contact("pass2", T_EXACT + 90.0, T_EXACT + 100.0, T_EXACT + 110.0)
    parked = lambda b, jd: TARGET  # noqa: E731
    got = _activity_at([c1, c2], parked, T_EXACT, weights={"Venus": 0.5})
    assert got == pytest.approx(0.5)
    assert got != pytest.approx(0.75)
    # between the passes: NEITHER episode supports ⇒ absent, not 1.0
    assert _activity_at([c1, c2], parked, T_EXACT + 50.0,
                        weights={"Venus": 0.5}) == 0.0
    # at the second pass only the second contributes
    assert _activity_at([c1, c2], parked, T_EXACT + 100.0,
                        weights={"Venus": 0.5}) == pytest.approx(0.5)


def test_contact_outside_its_episode_is_absent_even_when_in_orb():
    c = _contact("e1", T_EXACT - 10.0, T_EXACT, T_EXACT + 10.0)
    parked = lambda b, jd: TARGET  # noqa: E731
    assert _activity_at([c], parked, T_EXACT - 10.0001) == 0.0
    assert _activity_at([c], parked, T_EXACT + 10.0001) == 0.0
    assert _activity_at([c], parked, T_EXACT - 10.0) == pytest.approx(1.0)  # closed edge
    assert w.contact_supports(c, T_EXACT + 10.0) is True
    assert w.contact_supports(c, T_EXACT + 10.0001) is False


def test_role_aliases_of_one_physical_root_contribute_once():
    """7L Venus and kāraka Venus are two ledger contacts (two target_refs)
    on ONE physical crossing (same body, relation, aspect, target
    longitude, t_exact ⇒ same independence_group). §2.1: max per root, never
    noisy-OR across aliases. Mutation caught: 1 − 0.5·0.5 = 0.75."""
    c1 = _contact("alias-karaka", T_EXACT - 10.0, T_EXACT, T_EXACT + 10.0)
    c2 = dict(c1, contact_id="alias-lord", target_ref="7L", target_type="lord")
    for grp in ("ig-shared", None):  # ledger group, and the local fallback
        for c in (c1, c2):
            c["_independence_group"] = grp
        got = _activity_at([c1, c2], lambda b, jd: TARGET, T_EXACT,
                           weights={"Venus": 0.5, "7L": 0.5})
        assert got == pytest.approx(0.5), grp
    # per-root MAX: unequal alias weights keep the larger, once
    got = _activity_at([c1, c2], lambda b, jd: TARGET, T_EXACT,
                       weights={"Venus": 0.3, "7L": 0.5})
    assert got == pytest.approx(0.5)


def test_distinct_physical_roots_still_combine():
    """Positive control for the reduction: two bodies on two targets are two
    roots ⇒ the pinned noisy-OR combines them (0.75)."""
    c1 = _contact("r-sat", T_EXACT - 10.0, T_EXACT, T_EXACT + 10.0,
                  body="Saturn", target=100.0)
    c2 = _contact("r-jup", T_EXACT - 10.0, T_EXACT, T_EXACT + 10.0,
                  body="Jupiter", target=200.0)
    c2["target_ref"] = "Jupiter"
    pos = lambda b, jd: {"Saturn": 100.0, "Jupiter": 200.0}[b]  # noqa: E731
    got = _activity_at([c1, c2], pos, T_EXACT,
                       weights={"Venus": 0.5, "Jupiter": 0.5})
    assert got == pytest.approx(0.75)


def test_fetch_contacts_reads_aspect_deg_and_independence_group():
    """The ledger read must carry the two columns the kernel now needs;
    a SELECT that omits them re-introduces the bare-body defect silently."""
    import inspect
    src = inspect.getsource(w.fetch_contacts)
    assert "aspect_deg" in src and "independence_group" in src
