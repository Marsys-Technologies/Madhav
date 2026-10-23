"""TR DEFECT A — the contact-geometry stage's near-miss reconciliation vs the identity-domain tails disclosed under SR-NEARMISS-DOMAIN-TAIL.

THE DEFECT (qualifying TR on linux/amd64, run 20261023T1655ZT): `verify` DISAGREE `near_miss_reported_but_unstored` for the Saturn aspect to the natal Venus point in
the 3 classes that carry it. That object is one of the two identity-domain tails the near-miss verifier DISCLOSES (SR-NEARMISS-DOMAIN-TAIL): its station lies before
the identity domain opens, the builder's arc index holds only the monotone tail, so the builder stores nothing for it and could not. The verifier's disclosure patch
made `near_miss_verifier.verify_generation` report it, but `certify_geometry`'s reconciliation still demanded a stored row for every graze the certifier reported.
The reconciliation is the wrong side: it must exclude exactly the disclosed set (the same derivation, matched by object id), report it, and keep failing on any other
reported-but-unstored object. The disclosure is REPORT-LEVEL (SR-NEARMISS-DOMAIN-TAIL-AMEND-3): nothing here claims the tail is sealed.

Claims, each with ONE oracle (the single planted reversion that must fail it is named). Curves are analytic parabolas, Saturn-slow, worked by hand; a literal-row
connection (no database). Station and edge: the domain opens D0; |lambda - centre| = C + K d^2 (d = days from the station), the band (1 deg) is left 22 days after it.

  T-1  a reported stretch crossing the domain edge with its station BEFORE the domain is not a problem, and is DISCLOSED in the geometry result with the object id the
       near-miss search holds for it, body, relation, target, dates and a count (revert: `identity_domain_tails` returns [] -> the stage raises `reported_but_unstored`);
  T-2  the same crossing stretch with a station INSIDE the domain still fails by name (revert: `_station_in_span` answers False, i.e. every crossing stretch is a tail);
  T-4  the tail is matched to the graze by the OBJECT'S identity (body, relation, target = one object id), not by the body alone: a second object of the same body
       whose crossing stretch is not a tail, reported before the real tail object, is named alone and the disclosed object id is the tail's
       (revert: match the tail by body only -> the tail object is named instead and the tail is pinned on the wrong object);
  T-5  a tail excuses ONLY the graze it overlaps, one for one: the same object's mid-domain unstored graze (a second station inside the domain) still fails by name
       beside the disclosed tail (revert: a tail excuses every graze of its object, no overlap, no consumption -> nothing raises);
  T-6  one (body, relation, target) key held by two searched objects is refused, not silently pinned to one (revert: drop the uniqueness check -> two tails, no raise);
  T-3  only the disclosed set is excluded: another reported-but-unstored object beside a disclosed tail still fails, and the message names it alone
       (revert: any disclosed tail excuses any unstored graze, not only the one of its own object -> the second object is forgiven)."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import verification_job as vj

UTC = timezone.utc
D0 = datetime(1998, 1, 1, tzinfo=UTC)                            # the identity domain opens (== the horizon start)
DOMAIN = (D0, D0 + timedelta(days=300))
HORIZON = DOMAIN
GEN, CLS = "5.0", "business_launch"
C, ORB = 0.5, 1.0
K = (ORB - C) / 22.0 ** 2
SAT = ("saturn", "conjunction", "point:100.0")                   # the tail object (a slow body: edge speed ~0.03 deg/day)
JUP = ("jupiter", "conjunction", "point:200.0")                  # a second object, whose graze sits inside the domain
OBJ_ID = {SAT: "00000000-0000-0000-0000-00000000a001", JUP: "00000000-0000-0000-0000-00000000a002"}


def _sky(station_saturn: datetime):
    def position_at(body, t):
        if body == "saturn":
            d = (t - station_saturn).total_seconds() / 86400.0
            return (100.0 + C + K * d * d) % 360.0
        d = (t - (D0 + timedelta(days=150))).total_seconds() / 86400.0                  # jupiter: a graze mid-domain, station inside it
        return (200.0 + C + K * d * d) % 360.0
    return position_at


class _Cur:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class Conn:
    """Answers, from literal rows, the certifier's statements and the reconciliation's own."""

    def __init__(self, obligations, searched=None):
        self.obligations = list(obligations)
        self.searched = list(self.obligations if searched is None else searched)

    def execute(self, sql, params=()):
        flat = " ".join(sql.split())
        if "to_regclass" in flat:
            return _Cur([(True,)])
        if "FROM public.ka_gochara_search_inventory" in flat:
            return _Cur([HORIZON])
        if "FROM public.ka_gochara_search_obligation" in flat:
            return _Cur(self.obligations)
        if "FROM public.ka_gochara_contact c" in flat:
            return _Cur([])
        if "FROM public.ka_gochara_near_miss n" in flat:
            return _Cur([])                                                              # the builder stored NO near-miss row at all
        if "FROM public.ka_gochara_near_miss_search s" in flat:
            return _Cur([(OBJ_ID[k], *k, *DOMAIN) for k in self.searched])
        raise AssertionError(flat[:160])


def _geometry(conn, position_at):
    return vj.certify_geometry(conn, chart_id="c", generation=GEN, event_class=CLS, position_at=position_at, horizon=HORIZON)


def test_t1_a_domain_tail_is_not_a_problem_and_is_disclosed_with_its_object_id():
    """Reversion: `identity_domain_tails` returns [] -> the stage raises `near_miss_reported_but_unstored` for the tail."""
    out = _geometry(Conn([SAT]), _sky(D0 - timedelta(days=15)))                          # the station is 15 days before the domain opens
    assert out["identity_domain_tail_count"] == 1 == len(out["identity_domain_tails"]) == len(out["grazes"])
    (t,) = out["identity_domain_tails"]
    assert (t["object_id"], t["body"], t["relation"], t["target"]) == (OBJ_ID[SAT], "saturn", "conjunction", "point:100.0")
    assert t["reason"] == "rootless_stretch_crosses_identity_domain" and t["station_in_domain"] is False
    assert t["t_in"] == D0.isoformat() and D0 + timedelta(days=6) < datetime.fromisoformat(t["t_out"]) < D0 + timedelta(days=8)       # the clipped piece, as the verifier reports it


def test_t2_a_crossing_stretch_with_a_station_inside_the_domain_still_fails_by_name():
    """Reversion: `near_miss_verifier._station_in_span` answers False -> the stretch is disclosed instead of refused and this does not raise."""
    with pytest.raises(RuntimeError, match=r"near_miss_reported_but_unstored: saturn conjunction point:100\.0"):
        _geometry(Conn([SAT]), _sky(D0 + timedelta(days=10)))                            # the station is inside the domain: the builder's arc index sees it, it must have stored it


def test_t3_only_the_disclosed_set_is_excluded_another_unstored_object_still_fails():
    """Reversion: `tail = tails[0] if tails else None` (any disclosed tail excuses any graze) -> the jupiter graze is forgiven and the saturn one fails instead."""
    with pytest.raises(RuntimeError) as exc:
        _geometry(Conn([SAT, JUP]), _sky(D0 - timedelta(days=15)))
    msg = str(exc.value)
    assert "near_miss_reported_but_unstored: jupiter conjunction point:200.0" in msg and "saturn" not in msg


def test_t4_the_tail_is_matched_by_object_identity_not_by_body():
    """Reversion: match the tail to the graze by `body` alone -> the non-tail saturn object is excused by the real tail and the tail object is named instead."""
    from services.gochara_kernel import contact_certify as cc
    sat2 = ("saturn", "conjunction", f"point:{99.5 + K * 17.0 ** 2:.6f}")                 # a second saturn object: its stretch has < 3 in-domain days and a station in the domain -> not a tail
    OBJ_ID[sat2] = "00000000-0000-0000-0000-00000000a003"
    try:
        sky, conn, sink = _sky(D0 - timedelta(days=15)), Conn([sat2, SAT]), []
        cc.certify_contact_geometry(conn, chart_id="c", generation=GEN, event_class=CLS, position_at=sky, graze_sink=sink)
        assert {g["target"] for g in sink} == {sat2[2], SAT[2]}
        order = sorted(sink, key=lambda g: g["target"] != sat2[2])                       # the non-tail object FIRST
        disclosed: list = []
        problems = vj.near_miss_reconcile_problems(conn, chart_id="c", generation=GEN, event_class=CLS, reported=order, horizon=HORIZON, position_at=sky,
                                                   disclosed=disclosed)
    finally:
        OBJ_ID.pop(sat2, None)
    assert len(problems) == 1 and f"near_miss_reported_but_unstored: saturn conjunction {sat2[2]} " in problems[0] and "point:100.0 " not in problems[0]
    assert [(d["object_id"], d["target"]) for d in disclosed] == [(OBJ_ID[SAT], SAT[2])]


def test_t5_a_tail_excuses_only_the_graze_it_overlaps_a_mid_domain_graze_of_the_same_object_still_fails():
    """Reversion: a tail excuses every graze of its object (no overlap test, no consumption) -> this does not raise."""
    period = 200.0                                                                       # a second station at day 200 of the curve (D0 + 185): a mid-domain graze of the SAME object
    amp = 2 * K / (2 * math.pi / period) ** 2
    station = D0 - timedelta(days=15)

    def sky_two_stations(body, t):
        d = (t - station).total_seconds() / 86400.0
        return (100.0 + C + amp * (1 - math.cos(2 * math.pi * d / period))) % 360.0

    with pytest.raises(RuntimeError) as exc:
        _geometry(Conn([SAT]), sky_two_stations)
    msg = str(exc.value)
    assert msg.count("near_miss_reported_but_unstored") == 1 and "near_miss_reported_but_unstored: saturn conjunction point:100.0 [" in msg
    assert f"[{D0.isoformat()}" not in msg                                               # the named graze is the mid-domain one, not the domain-start tail


def test_t6_one_key_held_by_two_searched_objects_is_refused():
    """Reversion: drop the uniqueness check in `identity_domain_tails` -> two tails are computed for one key and nothing raises."""
    conn = Conn([SAT], searched=[SAT, SAT])
    rows = [("00000000-0000-0000-0000-00000000b001", *SAT, *DOMAIN), ("00000000-0000-0000-0000-00000000b002", *SAT, *DOMAIN)]
    conn.execute = lambda sql, params=(), _o=conn.execute: _Cur(rows) if "FROM public.ka_gochara_near_miss_search s" in " ".join(sql.split()) else _o(sql, params)
    with pytest.raises(RuntimeError, match=r"near_miss_tail_ambiguous: saturn conjunction point:100\.0"):
        vj.identity_domain_tails(conn, chart_id="c", generation=GEN, keys={SAT}, position_at=_sky(D0 - timedelta(days=15)), horizon=HORIZON)
