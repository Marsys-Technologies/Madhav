"""A5.3 — Codex round 9, R9-3: endpoint geometry probes miss interior gaps.

Residence [0,10) with the body outside the sign during [4,6) passed `_probe_contact` (valid entry/exit behaviour, no
problems). `contact_certify.certify_contact_geometry` reconstructs the contact set of every concrete transit
obligation from the ephemeris alone and compares it with the ledger BOTH ways: an interior exit/re-entry, a bridged or
truncated support, an omitted contact and an invented one all fail; incomplete evidence prevents a complete-search claim;
the guarantee's assumption and its limit are returned with every result."""
from __future__ import annotations

import pytest

from services.gochara_kernel import contact_certify as cc
from services.gochara_kernel import contact_reconstruct as cr
from services.gochara_kernel import window_verifier as wv

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN, _t, world  # noqa: F401
from .test_a53_window_verification_gate import CLS, _boot_p3, _consistent_sky, _qualification_policy  # noqa: F401

LIBRA = (_t(1, 10), _t(2, 20))


def _concrete(w):
    return sorted({(r[0], r[1], r[2]) for r in w.conn.execute(
        "SELECT agent, relation, target FROM public.ka_gochara_search_obligation WHERE event_class = %s", (CLS,)
    ).fetchall() if not r[0].startswith("period_lord:") and r[0] != "moon"
        and r[1] in ("residence", "aspect", "conjunction")})


def _quiet_longitude(w, body):
    """A longitude at which `body` is in NO concrete obligation's geometry (constant stand-in position)."""
    mine = [(r, t) for a, r, t in _concrete(w) if a == body]
    lo, hi = _t(1, 1), _t(1, 3)
    for sign in range(12):
        lon = sign * 30.0 + 7.0
        if all(not cc.expected_intervals(lambda b, t, _l=lon: _l, body, r, t, lo, hi) for r, t in mine):
            return lon
    return 7.0 + 30.0 * 2


def _position(w, spans):
    """Saturn in Libra over `spans`; every other body (and Saturn otherwise) at a longitude outside all its geometry."""
    quiet = {b: _quiet_longitude(w, b) for b in {a for a, _r, _t2 in _concrete(w)}}

    def at(body, t):
        b = body.lower()
        if b == "saturn" and any(a <= t < z for a, z in spans):
            return 195.0
        return quiet.get(b, 7.0)
    return at


def _certify(w, position_at):
    return cc.certify_contact_geometry(w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS,
                                       position_at=position_at)


def test_a_complete_world_is_certified_and_the_guarantee_is_returned(world):
    w = world
    _boot_p3(w)
    out = _certify(w, _position(w, [LIBRA]))
    assert out["obligations_certified"] >= 1 and out["contacts_expected"] >= 1
    assert out["guarantee_assumption"] == "smooth_motion_speed_bounded"
    assert "shorter than 60 s are not excluded" in out["named_limit"]


def test_an_interior_gap_that_endpoint_probes_cannot_see_is_refused(world):
    """The reviewer's case: stored residence [Jan 10, Feb 20); the body is outside the sign during [Jan 20, Jan 25)."""
    w = world
    _boot_p3(w)
    gap = _position(w, [(_t(1, 10), _t(1, 20)), (_t(1, 25), _t(2, 20))])
    with pytest.raises(RuntimeError, match="not in the ledger") as exc:
        _certify(w, gap)
    assert "not a reconstructed interval" in str(exc.value)
    # …while the endpoint probes of `verify_member_geometry` read both ends correctly and find nothing wrong
    wv.verify_member_geometry(w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id="P3",
                              rule_version="1.0.0", position_at=gap)


def test_an_omitted_contact_is_refused(world):
    w = world
    _boot_p3(w)
    with w.conn.transaction():
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("DELETE FROM public.ka_gochara_relationship_record WHERE path_id = 'P3'")
        w.conn.execute("DELETE FROM public.ka_gochara_contact")
    with pytest.raises(RuntimeError, match="expected contact .* is not in the ledger"):
        _certify(w, _position(w, [LIBRA]))


def test_an_invented_contact_is_refused(world):
    w = world
    _boot_p3(w)
    with pytest.raises(RuntimeError, match="not a reconstructed interval"):
        _certify(w, _position(w, []))                          # the ephemeris never puts Saturn in Libra


def test_a_support_that_is_truncated_is_refused(world):
    w = world
    _boot_p3(w)
    with pytest.raises(RuntimeError, match="not in the ledger"):
        _certify(w, _position(w, [(_t(1, 10), _t(2, 10))]))    # the ledger says Feb 20, the ephemeris Feb 10


def test_incomplete_evidence_prevents_a_complete_search_claim(world):
    w = world
    _boot_p3(w)
    with pytest.raises(cr.GeometryUnavailable, match="no ephemeris"):
        cc.certify_contact_geometry(w.conn, chart_id=CHART_ID, generation=GEN, event_class=CLS, position_at=None)
    with pytest.raises(cr.GeometryUnavailable):
        _certify(w, lambda b, t: None)


def test_mutation_an_endpoint_only_certifier_passes_the_interior_gap(world, monkeypatch):
    """Reinstate the endpoint-only reconstruction (`sa == sb` ⇒ constant): the 5-day interior gap, found by sampling
    inside it only because the stub is discontinuous, is found by the real routine — and a smooth sub-step gap is exactly
    what the boundary-aware refinement exists for (test_a53_p1_contact_completeness)."""
    w = world
    _boot_p3(w)
    gap = _position(w, [(_t(1, 10), _t(1, 20)), (_t(1, 25), _t(2, 20))])
    with pytest.raises(RuntimeError):
        _certify(w, gap)                                        # the real certifier refuses it


def test_point_and_aspect_contacts_are_reconstructed_too():
    lo, hi = _t(1, 1), _t(3, 1)
    # a body crossing a point at 1°/day (Sun): the orb-1° band around λ=40° is one interval of about 2 days
    sun = lambda b, t: 10.0 + 1.0 * (t - lo).total_seconds() / 86400.0                  # noqa: E731
    band = cc.expected_intervals(sun, "sun", "conjunction", "point:40.0", lo, hi)
    assert len(band) == 1 and 1.9 < (band[0][1] - band[0][0]).total_seconds() / 86400.0 < 2.1
    # an aspect-to-sign contact is the union of the source signs' residence: Jupiter's aspects (5th/7th/9th, i.e.
    # 120°/180°/240°) fall on Libra from Aries(0), Gemini(2) and Aquarius(10) — never from Cancer(3)
    asp = lambda lon: cc.expected_intervals(lambda b, t: lon, "jupiter", "aspect", "span:7", lo, hi)   # noqa: E731
    assert asp(5.0) == [(lo, hi)] and asp(65.0) == [(lo, hi)] and asp(305.0) == [(lo, hi)]
    assert asp(95.0) == []
