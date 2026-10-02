"""A5.3 — Codex round 9, R9-2 (iii): `verify_p1_anchors` starts from the EXPECTED CONTACT SET.

It used to start from the relationship RECORDS, so a contact with every anchored record omitted was invisible (the
reviewer's fake read returned `{"contacts": 0}` successfully). The expected contacts are now reconstructed from the
ephemeris alone (`contact_reconstruct`) and compared with the ledger both ways, including the zero-output cases."""
from __future__ import annotations

import math
from datetime import timedelta

import pytest

from services.gochara_kernel import contact_reconstruct as cr
from services.gochara_kernel import record_verifier as rv

from .test_a53_inventory import CHART_ID, H0, H1
from .test_a53_p1_anchor import SAT_AD, SUN_AD, SUN_LIBRA, _anchors, _pos, _quiet, _sun_in_libra
from .test_a53_p1_support import GEN, _t, world  # noqa: F401


# ── the reconstruction itself ────────────────────────────────────────────────────────────────────────

def test_the_reconstruction_finds_an_interior_exit_and_reentry_the_endpoint_probes_missed():
    """The reviewer's counterexample, with SMOOTH motion: Mercury inside Libra over [0, 31) days except a dip below the
    sign boundary around day 10. Endpoint probes just inside/outside the support's ends see nothing wrong."""
    lo, hi = _t(1, 1), _t(2, 1)

    def pos(body, t):
        d = (t - lo).total_seconds() / 86400.0
        return 180.5 + 0.2 * d - 4.0 * math.exp(-((d - 10.0) / 1.6) ** 2)
    out = cr.residence_intervals(pos, "mercury", lo, hi)
    libra, virgo = out[6], out[5]
    assert len(libra) == 2 and len(virgo) == 1                      # two Libra intervals around one Virgo excursion
    assert libra[0][0] == lo and libra[1][1] == hi
    assert libra[0][1] == virgo[0][0] and libra[1][0] == virgo[0][1]
    assert timedelta(days=1.5) < virgo[0][1] - virgo[0][0] < timedelta(days=3)


def test_an_excursion_shorter_than_the_sampling_step_is_found_by_the_boundary_aware_refinement():
    """A ~2-hour exit below the boundary — inside one 6-hour step, between two samples that both read `inside`: only
    the refinement (which subdivides any step that could reach a boundary) can see it."""
    lo, hi = _t(1, 1), _t(1, 20)
    t0 = _t(1, 10) + timedelta(hours=5, minutes=17)                  # off the 6-hour grid

    def pos(body, t):
        h = (t - t0).total_seconds() / 3600.0
        return 180.001 + 0.0002 * (t - lo).total_seconds() / 86400.0 - 0.004 * math.exp(-(h / 1.2) ** 2)
    out = cr.residence_intervals(pos, "mercury", lo, hi)
    assert len(out[5]) == 1                                          # one Virgo excursion
    dt = out[5][0][1] - out[5][0][0]
    assert timedelta(minutes=30) < dt < timedelta(hours=4)
    assert len(out[6]) == 2 and out[6][0][1] == out[5][0][0] and out[6][1][0] == out[5][0][1]


def test_an_excursion_shorter_than_the_minimum_is_a_named_limit_not_a_claim():
    """A 20-second flicker below the boundary (shorter than MIN_EXCURSION_SECONDS) may be missed — and the guarantee
    sentence says exactly that instead of claiming it absent."""
    lo, hi = _t(1, 1), _t(1, 5)
    t0 = _t(1, 3) + timedelta(seconds=1234)

    def pos(body, t):
        s = (t - t0).total_seconds()
        return 180.0000002 - (0.0000004 * math.exp(-(s / 6.0) ** 2))
    out = cr.residence_intervals(pos, "mercury", lo, hi)
    assert out[6][0][0] == lo and out[6][-1][1] == hi          # either outcome is allowed under the named limit …
    assert "shorter than 60 s are not excluded" in cr.NAMED_LIMIT   # … and the limit is stated, never silent


def test_the_reconstruction_is_complete_over_every_sign_and_clipped_to_the_horizon():
    lo, hi = _t(1, 1), _t(3, 1)
    out = cr.residence_intervals(lambda b, t: 75.0, "sun", lo, hi)
    assert out[2] == [(lo, hi)] and all(out[i] == [] for i in range(12) if i != 2)


def test_the_guarantee_is_a_sentence_with_its_assumption_and_the_limit_is_named():
    assert cr.GUARANTEE_ASSUMPTION == "smooth_motion_speed_bounded"
    assert "smooth motion" in cr.NAMED_LIMIT and "shorter than 60 s are not excluded" in cr.NAMED_LIMIT
    assert cr.MIN_EXCURSION_SECONDS == 60 and cr.BISECT_SECONDS == 1.0
    assert set(cr.VMAX_DPS) >= {"sun", "moon", "mars", "mercury", "venus", "jupiter", "saturn", "rahu", "ketu"}


def test_an_undeterminable_position_makes_the_geometry_unavailable_not_empty():
    with pytest.raises(cr.GeometryUnavailable):
        cr.residence_intervals(lambda b, t: None, "sun", _t(1, 1), _t(1, 5))


# ── the verifier starts from the expected contacts ───────────────────────────────────────────────────

def test_a_contact_carrying_only_two_of_its_readings_fails(world):
    w = world
    _sun_in_libra(w)
    w.conn.execute("DELETE FROM public.ka_gochara_relationship_record WHERE (period_anchor_lord, period_anchor_level)"
                   " NOT IN (('sun','ad'), ('saturn','ad'))")          # keep the two readings the fixture materialised
    # the fixture materialised (Sun AD) + (Saturn AD) only: the Sun's own MD/PD readings of the SAME contact are missing
    with pytest.raises(RuntimeError, match="anchors stored"):
        _anchors(w)


def test_a_fully_anchored_contact_passes(world):
    w = world
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 20)), ("saturn", 2, _t(1, 20), _t(2, 5))])
    w.boot()
    w.seed("sun", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    w.grain("sun", lambda t: _t(1, 10) <= t < _t(2, 20), anchors=[SUN_AD, SAT_AD, ("sun", "md"), ("sun", "pd")])
    out = _anchors(w)
    assert out["contacts"] >= 1 and out["guarantee_assumption"] == cr.GUARANTEE_ASSUMPTION
    assert "not excluded" in out["named_limit"]


def _fully_anchored(w):
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 20)), ("saturn", 2, _t(1, 20), _t(2, 5))])
    w.boot()
    w.seed("sun", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    w.grain("sun", lambda t: _t(1, 10) <= t < _t(2, 20), anchors=[SUN_AD, SAT_AD, ("sun", "md"), ("sun", "pd")])
    assert _anchors(w)["contacts"] >= 1


def test_a_contact_with_every_anchored_record_omitted_is_caught(world):
    """The contact row exists, every record on it is gone — the old verifier started from records and passed."""
    w = world
    _fully_anchored(w)
    w.conn.execute("DELETE FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'")
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_contact").fetchone()[0] >= 1
    with pytest.raises(RuntimeError, match=r"anchors stored \[\] != derived"):
        _anchors(w)


def test_a_contact_the_ledger_never_wrote_is_caught(world):
    """Zero output: the geometry says the Sun is in Libra, nothing was materialised at all."""
    w = world
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 20))])
    w.boot()
    with pytest.raises(RuntimeError, match="is not in the ledger"):
        _anchors(w)


def test_a_class_with_no_contacts_and_no_records_passes_the_zero_case(world):
    """Every body in a P1-quiet sign: no contacts expected, none stored, no records — a VALID empty output."""
    w = world
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 20))])
    w.boot()
    assert _anchors(w, position_at=_pos({}))["contacts"] == 0


def test_an_interior_gap_the_support_bridges_is_caught(world):
    """Stored: Sun in Libra [Jan 10, Feb 20). Ephemeris: out of Libra during [Jan 20, Jan 25) (a 5-day exit the
    endpoint probes cannot see). The reconstructed contacts are two; the ledger holds one bridging both."""
    w = world
    _fully_anchored(w)
    gap = _pos({"sun": [(_t(1, 10), _t(1, 20)), (_t(1, 25), _t(2, 20))]})
    with pytest.raises(RuntimeError, match="is not in the ledger"):
        _anchors(w, position_at=gap)


def test_an_invented_contact_is_caught(world):
    """Records on a contact the ephemeris does not reconstruct (the Sun was NOT in Libra then)."""
    w = world
    _fully_anchored(w)
    with pytest.raises(RuntimeError, match="carries P1 records but is not a reconstructed"):
        _anchors(w, position_at=_pos({}))


def test_without_an_ephemeris_there_is_no_complete_claim(world):
    w = world
    _fully_anchored(w)
    with pytest.raises(cr.GeometryUnavailable, match="no ephemeris"):
        rv.verify_p1_anchors(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", position_at=None)
    with pytest.raises(cr.GeometryUnavailable):
        _anchors(w, position_at=lambda b, t: None)


def test_mutation_a_record_started_verifier_passes_the_omitted_contact(world, monkeypatch):
    """Reinstate the pre-R9-2 behaviour (compare only the contacts that carry records): the omission passes."""
    w = world
    _fully_anchored(w)
    w.conn.execute("DELETE FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'")

    def records_only(conn, *, chart_id, generation, event_class, position_at):
        n = conn.execute("SELECT count(DISTINCT contact_id) FROM public.ka_gochara_relationship_record"
                         " WHERE path_id = 'P1' AND contact_id IS NOT NULL").fetchone()[0]
        return {"contacts": n}
    monkeypatch.setattr(rv, "verify_p1_anchors", records_only)
    assert rv.verify_p1_anchors(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage",
                                position_at=SUN_LIBRA) == {"contacts": 0}          # the defect the reviewer reproduced
