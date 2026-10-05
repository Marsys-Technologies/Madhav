"""A5.3 — window members' contact spans verified against the EPHEMERIS itself (Codex round 8, R8-4).

`verify_member_support` compared a record's support with the builder-written contact span; that is not independent.
`verify_member_geometry` probes the ephemeris just inside and just outside each end of every member's contact span
(a sign for residence, the dṛṣṭi-source signs for aspect-to-span, an orb band around each ray level for point
relations), using only the Swiss longitude probe — no arc index, substrate or solver.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import window_verifier as wv
from services.gochara_kernel.convention import ORB_TABLE, drishti_angles

UTC = timezone.utc
T = lambda d: datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=d)            # noqa: E731


def _line(a_day, b_day, inside, outside):
    """A body at `inside`° during [a, b) and `outside`° otherwise."""
    return lambda body, t: inside if T(a_day) <= t < T(b_day) else outside


def _probe(position_at, relation, target, t_in, t_out, open_start=False, open_end=False, body="saturn"):
    return wv._probe_contact(position_at, body, relation, target, T(t_in), T(t_out), open_start, open_end, 1.0)


def test_the_verifiers_geometry_constants_equal_the_kernels_and_are_its_own():
    assert wv._POINT_ORB_DEG["conjunction"] == ORB_TABLE["orb_conj_slow"]["orb_max_deg"]
    assert wv._POINT_ORB_DEG["aspect"] == ORB_TABLE["orb_drishti_slow"]["orb_max_deg"]
    for body in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        assert wv._ASPECT_ANGLES[body.lower()] == tuple(drishti_angles(body)), body
    import ast
    import inspect
    imported = {n.module for n in ast.walk(ast.parse(inspect.getsource(wv))) if isinstance(n, ast.ImportFrom)}
    assert not any(m and ("window_sweep" in m or "window_store" in m or "convention" in m or "arcs" in m)
                   for m in imported)


# ── residence (a sign) ──────────────────────────────────────────────────────────────────────────────────────

def test_a_residence_span_that_is_the_physical_one_passes_at_both_ends():
    pos = _line(10, 50, 195.0, 15.0)                                   # Libra [day 10, day 50)
    assert _probe(pos, "residence", "span:7", 10, 50) == []


def test_a_residence_span_that_starts_late_ends_early_or_overruns_is_caught():
    pos = _line(10, 50, 195.0, 15.0)
    late_start = _probe(pos, "residence", "span:7", 12, 50)             # stored start is 2 days after the ingress
    assert any("still in the geometry just before the stored start" in p for p in late_start)
    early_start = _probe(pos, "residence", "span:7", 8, 50)             # stored start precedes the ingress
    assert any("not in the geometry just inside the stored start" in p for p in early_start)
    overrun = _probe(pos, "residence", "span:7", 10, 60)
    assert any("not in the geometry just inside the stored end" in p for p in overrun)
    short = _probe(pos, "residence", "span:7", 10, 40)
    assert any("still in the geometry just after the stored end" in p for p in short)


def test_a_span_truncated_at_the_horizon_is_probed_inside_only():
    pos = _line(-20, 90, 195.0, 15.0)                                   # the body is in Libra through the horizon
    assert _probe(pos, "residence", "span:7", 0, 60, open_start=True, open_end=True) == []
    # an end that is NOT a horizon edge must still be a real exit
    assert _probe(pos, "residence", "span:7", 0, 60, open_start=True, open_end=False) != []


# ── aspect-to-span and point relations ─────────────────────────────────────────────────────────────────────

def test_aspect_to_span_is_probed_from_the_source_signs():
    # Saturn's dṛṣṭi angles 60/180/270: it aspects Libra (sign 7) from sign 7-2=5 (Leo), 1 (Aries), 7-9→10 (Capricorn)
    pos = _line(10, 50, 130.0, 15.0)                                    # Leo [day 10, 50): the 3rd-house aspect
    assert _probe(pos, "aspect", "span:7", 10, 50) == []
    assert _probe(pos, "aspect", "span:7", 12, 50) != []


def test_a_point_conjunction_is_probed_against_the_orb_band_and_a_wrong_span_is_caught():
    lam = 100.0

    def pos(body, t):                                                   # crosses the 1° orb band [99, 101] on day 20..40
        return 99.0 + (t - T(20)).total_seconds() / 86400.0 * 0.1 if T(0) <= t < T(60) else 0.0
    # in the band on day 20 + (≤ 20 days)
    inside_from, inside_to = 20, 40
    assert _probe(pos, "conjunction", f"point:{lam}", inside_from, inside_to) == []
    assert _probe(pos, "conjunction", f"point:{lam}", 25, inside_to) != []


def test_an_aspect_to_a_point_uses_each_ray_level_and_never_a_foreign_one():
    lam = 100.0
    ray_level = (lam - 90.0) % 360.0                                    # Mars's 4th-house ray: body at target−90°

    def pos(body, t):
        return ray_level if T(10) <= t < T(30) else 0.0
    assert _probe(pos, "aspect", f"point:{lam}", 10, 30, body="mars") == []
    assert _probe(pos, "aspect", f"point:{lam}", 10, 35, body="mars") != []
    wrong_way = (lam + 90.0) % 360.0                                    # the aspect falls FORWARD: target − angle only

    def foreign(body, t):
        return wrong_way if T(10) <= t < T(30) else 0.0
    assert _probe(foreign, "aspect", f"point:{lam}", 10, 30, body="mars") != []


def test_a_relation_without_independent_geometry_is_named_not_passed():
    assert _probe(lambda b, t: 0.0, "return", "point:10.0", 1, 5)[0].endswith("no independent geometry for this relation")


# ── on the real schema through the writer ───────────────────────────────────────────────────────────────────

from .test_a53_window_verification_gate import (SPANS, _boot_p3, _consistent_sky, _t, world)  # noqa: E402,F401


def test_the_window_phase_verifies_the_contact_geometry_and_refuses_a_span_the_sky_does_not_support(world):
    w = world
    _boot_p3(w)
    ok = w.step("window:marriage:P3")
    assert "reproduced all 1 window(s) exactly" in ok.notes                  # the truth matches the stored span
    SPANS["saturn"] = [(_t(1, 15), _t(2, 20))]                               # the sky says the ingress is 5 days later
    with pytest.raises(RuntimeError, match="member geometry verification failed marriage/P3.*not in the geometry "
                                           "just inside the stored start"):
        w.step("window:marriage:P3")


def test_the_geometry_result_counts_the_contacts_it_probed(world):
    w = world
    _boot_p3(w)
    out = wv.verify_member_geometry(
        w.conn, chart_id="482012f1-710e-4a25-994a-93821f5871aa", generation="5.0",
        event_class="marriage", path_id="P3", rule_version="1.0.0",
        position_at=lambda body, t: 195.0 if SPANS["saturn"][0][0] <= t < SPANS["saturn"][0][1] else 15.0)
    assert out == {"contacts": 0}                                            # no window exists yet: no members
    w.step("window:marriage:P3")
    out = wv.verify_member_geometry(
        w.conn, chart_id="482012f1-710e-4a25-994a-93821f5871aa", generation="5.0", event_class="marriage",
        path_id="P3", rule_version="1.0.0",
        position_at=lambda body, t: 195.0 if SPANS["saturn"][0][0] <= t < SPANS["saturn"][0][1] else 15.0)
    assert out == {"contacts": 1}


def test_a_stored_start_later_than_the_ingress_is_caught_only_because_the_start_is_not_a_horizon_edge(world):
    w = world
    _boot_p3(w)
    SPANS["saturn"] = [(_t(1, 5), _t(2, 20))]                                # the body was already in Libra on Jan 5
    with pytest.raises(RuntimeError, match="still in the geometry just before the stored start"):
        w.step("window:marriage:P3")
