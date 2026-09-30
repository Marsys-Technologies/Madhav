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
