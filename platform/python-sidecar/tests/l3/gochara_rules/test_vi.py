"""O-VI-* — vedha interval oracles (GOCHARA_DESIGN_SPECS_v1_4 §5).

All intervals half-open [t_in, t_out); the boundary day belongs to the NEXT
(clean) interval (O-VI-2's stated convention).
"""
from __future__ import annotations

from services.gochara_rules.vedha import (
    VedhaInterval, attenuation_at, attenuation_over, carve_vipareeta,
    create_vedha_interval,
)


def _iv(state="active", t_in="2025-01-01T00:00Z", t_out="2025-06-01T00:00Z",
        attenuation=0.5, vi_id="vi-1", obstructor="Mars"):
    return VedhaInterval(vi_id=vi_id, rule_version="1.0.0",
                         primary_contact_id="sha256:primary",
                         obstructor_body=obstructor, vedha_kind="occupation",
                         t_in=t_in, t_out=t_out, state=state,
                         attenuation=attenuation)


# ── O-VI-1 — inactive/cancelled ⇒ 1.0; active ⇒ < 1.0 ───────────────────────
def test_ovi1_state_gated_attenuation():
    inactive = _iv(state="inactive")
    cancelled = _iv(state="cancelled_vipareeta", vi_id="vi-2")
    active = _iv(state="active", vi_id="vi-3")
    t = "2025-02-01T00:00Z"
    assert attenuation_at(t, [inactive])["factor"] == 1.0
    r = attenuation_at(t, [cancelled])
    assert r["factor"] == 1.0
    assert r["rows"][0]["state"] == "cancelled_vipareeta"  # state reported
    # positive control: the ACTIVE row attenuates (< 1.0) — an always-1
    # implementation fails the control
    assert attenuation_at(t, [active])["factor"] < 1.0
    # mutation: attenuating on the inactive row fails
    assert attenuation_at(t, [inactive])["state"] == "clean"


# ── O-VI-2 (literal) — partial overlap; boundary day clean ───────────────────
def test_ovi2_partial_overlap_half_open():
    # primary residence [2025-01-01, 2025-06-01); obstruction covering
    # [2025-01-01, 2025-03-01) only — literal timestamps.
    ob = _iv(t_in="2025-01-01T00:00Z", t_out="2025-03-01T00:00Z")
    segments = attenuation_over(
        ("2025-01-01T00:00Z", "2025-06-01T00:00Z"), [ob])
    assert segments == [
        (("2025-01-01T00:00Z", "2025-03-01T00:00Z"), 0.5),
        (("2025-03-01T00:00Z", "2025-06-01T00:00Z"), 1.0),
    ]
    # the boundary day 2025-03-01 belongs to the CLEAN interval, factor 1.0
    assert attenuation_at("2025-03-01T00:00Z", [ob])["factor"] == 1.0
    assert attenuation_at("2025-02-28T00:00Z", [ob])["factor"] == 0.5
    # mutation: whole-residence attenuation (the N4 collapse) fails
    assert attenuation_at("2025-04-01T00:00Z", [ob])["factor"] == 1.0


# ── O-VI-3 — exception pairs create no interval; Mars control does ───────────
def test_ovi3_exception_pairs():
    # Saturn occupying a Sun-primary's vedha house; Moon occupying a
    # Mercury-primary's ⇒ NO interval (M-8 exceptions)
    assert create_vedha_interval(
        vi_id="v1", rule_version="1.0.0", primary_contact_id="c1",
        primary_body="Sun", obstructor_body="Saturn",
        vedha_kind="occupation", t_in="2025-01-01T00:00Z",
        t_out="2025-02-01T00:00Z", attenuation=0.5) == []
    assert create_vedha_interval(
        vi_id="v2", rule_version="1.0.0", primary_contact_id="c2",
        primary_body="Mercury", obstructor_body="Moon",
        vedha_kind="occupation", t_in="2025-01-01T00:00Z",
        t_out="2025-02-01T00:00Z", attenuation=0.5) == []
    # non-exception control: Mars occupying a Sun-primary's vedha house ⇒ an
    # interval IS created (a never-obstruct implementation fails)
    control = create_vedha_interval(
        vi_id="v3", rule_version="1.0.0", primary_contact_id="c3",
        primary_body="Sun", obstructor_body="Mars", vedha_kind="occupation",
        t_in="2025-01-01T00:00Z", t_out="2025-02-01T00:00Z", attenuation=0.5)
    assert len(control) == 1
    assert control[0].exception == "none"


# ── O-VI-4 (literal) — vipareeta carve-out ───────────────────────────────────
def test_ovi4_vipareeta_carves_subinterval():
    # obstruction [2025-01-01, 2025-06-01); vipareeta row covering
    # [2025-02-15, 2025-03-15) strictly inside — literal timestamps.
    ob = _iv(t_in="2025-01-01T00:00Z", t_out="2025-06-01T00:00Z")
    carved = carve_vipareeta(
        ob, ("2025-02-15T00:00Z", "2025-03-15T00:00Z"))
    by_state = {(iv.t_in, iv.t_out): iv.state for iv in carved}
    # the covered sub-interval [2025-02-15, 2025-03-15) is carved OUT:
    # attenuation outside it, none inside
    assert by_state == {
        ("2025-01-01T00:00Z", "2025-02-15T00:00Z"): "active",
        ("2025-02-15T00:00Z", "2025-03-15T00:00Z"): "cancelled_vipareeta",
        ("2025-03-15T00:00Z", "2025-06-01T00:00Z"): "active",
    }
    cancelled = next(iv for iv in carved if iv.state == "cancelled_vipareeta")
    assert cancelled.attenuation == 1.0
    # mutation: flag-flip cancellation (whole row inactive) fails — active
    # remnants remain and the carved row carries its OWN interval
    assert any(iv.state == "active" for iv in carved)
    assert (cancelled.t_in, cancelled.t_out) == (
        "2025-02-15T00:00Z", "2025-03-15T00:00Z")
    assert attenuation_at("2025-03-01T00:00Z", carved)["factor"] == 1.0
    assert attenuation_at("2025-01-15T00:00Z", carved)["factor"] == 0.5


# ── O-VI-5 — absent overlay coverage ⇒ unavailable, never 1.0 ────────────────
def test_ovi5_absent_overlay_unavailable():
    r = attenuation_at("2025-02-01T00:00Z", None)
    assert r["state"] == "unavailable"
    assert r["factor"] is None
    assert r["coverage"] == {"overlay": "vedha", "computed": False}
    # mutation: default 1.0 on missing overlay fails
    assert r["factor"] != 1.0
