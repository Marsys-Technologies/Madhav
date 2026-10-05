"""SEAM-RULING: the member-geometry check honours the UNION contract (A5.3 brief v1.36), no weaker for a genuine single span.

THE DEFECT (Stream A through the real runner; independent read-only investigation GRAZING_INVESTIGATION_FABLE): the builder stores a P3/P4 point contact per
MONOTONE ARC (`record_store._in_orb_span_around_root`, arcs end at stations). A station inside the 1 degree band with the ray level crossed on both sides is
therefore stored as TWO ABUTTING contacts [entry, S] and [S, exit] sharing the station instant S. `verify_member_geometry` demanded every non-horizon end be an
orb-edge crossing, so at S it found 'still in the geometry just after the stored end' / 'just before the stored start' and the window phase failed
(`window:marriage:P3`). A5.3 brief v1.36 had already ruled: certification compares the UNION of the ledger's contacts; a seam between abutting episodes is not a
boundary of the contact SET (implemented in `contact_certify`, not in the member check). Confirmed by computation: Venus's direct station 1998-02-05 21:28:04 UT
(sidereal 264.638, 0.752 deg from the natal point 265.39) and Mercury's retrograde station 2000-06-23 08:31:23 UT (86.102, 0.712 deg from the ray 85.39).

THE FIX: neighbours are looked up among ALL the generation's stored contacts of one (body, relation, canonical target); a shared instant is a seam only if it is
independently confirmed from the ephemeris as (a) a STATION and (b) INSIDE the geometry on both sides; a seam end gets no outside probe (the inside probe is kept);
a real gap, a non-station split, a partner that is missing, or a genuinely truncated span keeps every outside probe and FAILS.

Synthetic tests (no database, exact curve, mutation-checked) and real-sky tests (the writer's own window phase over 1998-02 and 2000-06 on the real ephemeris)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import window_verifier as wv

from .test_a55_replace_chain import template  # noqa: F401  (the module-scoped migration-chain template the real-sky tests clone)

UTC = timezone.utc
T0 = datetime(2026, 3, 1, tzinfo=UTC)               # the station instant S
DAY = timedelta(days=1)
RAY = 120.0                                          # the point's longitude
EDGE_DAYS = 75 ** 0.5                                # |lambda - RAY| = 1 at +-8.660254 d for lambda = RAY - 0.5 + 0.02 d^2
CHART, GEN, CLS, PATH, VER = "c", "5.0", "marriage", "P3", "1.0.0"


def curve(body, t):                                  # a station at T0 INSIDE the band (0.5 deg below the ray), the ray crossed at +-5 d
    d = (t - T0).total_seconds() / 86400.0
    return (RAY - 0.5 + 0.02 * d * d) % 360.0


def curve_graze(body, t):                            # the same shape but the minimum stays 0.3 deg ABOVE the ray: the ray level is never reached
    d = (t - T0).total_seconds() / 86400.0
    return (RAY + 0.3 + 0.02 * d * d) % 360.0


class _Rows:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return list(self.rows)


class _Conn:
    """members: the contacts the grain's windows use; ledger: ALL stored contacts of the key (the partner need not be a member)."""

    def __init__(self, members, ledger=None):
        self.members, self.ledger = members, ledger if ledger is not None else members

    def execute(self, sql, params=None):
        flat = " ".join(sql.split())
        if flat.startswith("SELECT DISTINCT c.contact_id::text"):
            return _Rows([(cid, "venus", "conjunction", a, b, ex, f"point:{RAY}", T0 - 60 * DAY, T0 + 60 * DAY, 0.00027777778)
                          for cid, a, b, ex in self.members])
        if flat.startswith("SELECT c.contact_id::text, c.t_in, c.t_out"):
            return _Rows([(cid, a, b) for cid, a, b, _ex in self.ledger])
        raise AssertionError(flat[:120])


def _A(): return ("A", T0 - EDGE_DAYS * DAY, T0, T0 - 5 * DAY)       # [entry, S], exact root at -5 d
def _B(): return ("B", T0, T0 + EDGE_DAYS * DAY, T0 + 5 * DAY)       # [S, exit], exact root at +5 d


def _verify(conn, position_at=curve):
    return wv.verify_member_geometry(conn, chart_id=CHART, generation=GEN, event_class=CLS, path_id=PATH, rule_version=VER, position_at=position_at)


# ── the station-in-band pair is ONE contact set ─────────────────────────────────────────────────────────────────────────────

def test_a_station_in_band_pair_of_abutting_contacts_is_accepted():
    assert _verify(_Conn([_A(), _B()])) == {"contacts": 2}


def test_a_member_whose_abutting_partner_is_not_a_member_is_accepted_too():
    assert _verify(_Conn([_A()], ledger=[_A(), _B()])) == {"contacts": 1}


def test_the_pair_is_judged_whole_the_union_ends_keep_their_outside_probes():
    """The seam is exempt; the UNION's outer ends are not: shortening the first contact's start (a truncation) still fails."""
    short_start = ("A", T0 - 6 * DAY, T0, T0 - 5 * DAY)                      # starts 2.66 d after the true entry: still in the geometry just before it
    with pytest.raises(RuntimeError, match=r"contact A: .*still in the geometry just before the stored start"):
        _verify(_Conn([short_start, _B()]))
    short_end = ("B", T0, T0 + 6 * DAY, T0 + 5 * DAY)
    with pytest.raises(RuntimeError, match=r"contact B: .*still in the geometry just after the stored end"):
        _verify(_Conn([_A(), short_end]))


# ── a genuinely truncated span STILL fails; so does everything that is not a seam ───────────────────────────────────────────

def test_a_genuinely_truncated_span_still_fails_when_the_partner_is_missing():
    with pytest.raises(RuntimeError, match=r"contact A: .*still in the geometry just after the stored end"):
        _verify(_Conn([_A()]))                                              # the second arc was never stored: A ends at a station inside the band
    with pytest.raises(RuntimeError, match=r"contact B: .*still in the geometry just before the stored start"):
        _verify(_Conn([_B()]))


def test_a_real_gap_between_the_two_contacts_keeps_both_outside_probes():
    a = ("A", T0 - EDGE_DAYS * DAY, T0 - 2 * DAY, T0 - 5 * DAY)
    b = ("B", T0 + 2 * DAY, T0 + EDGE_DAYS * DAY, T0 + 5 * DAY)
    with pytest.raises(RuntimeError) as exc:
        _verify(_Conn([a, b]))
    assert "contact A: " in str(exc.value) and "just after the stored end" in str(exc.value)
    assert "contact B: " in str(exc.value) and "just before the stored start" in str(exc.value)


def test_a_split_that_is_not_at_a_station_is_not_a_seam_and_is_named():
    a = ("A", T0 - EDGE_DAYS * DAY, T0 + 3 * DAY, T0 - 5 * DAY)             # an arbitrary mid-band split while the body is moving
    b = ("B", T0 + 3 * DAY, T0 + EDGE_DAYS * DAY, T0 + 5 * DAY)
    with pytest.raises(RuntimeError, match=r"not a legitimate seam: venus is not at a station at .*an arc seam exists only where the motion reverses"):
        _verify(_Conn([a, b]))


def test_a_junction_where_the_body_is_outside_the_geometry_on_one_side_is_not_a_seam():
    """Two contacts abutting at a station where the body is NOT inside the band on both sides (here: the station is outside it)."""
    def far(body, t):                                                         # a station 3 deg above the ray: never in the band at all
        d = (t - T0).total_seconds() / 86400.0
        return RAY + 3.0 + 0.02 * d * d
    a = ("A", T0 - 2 * DAY, T0, T0 - 1 * DAY)
    b = ("B", T0, T0 + 2 * DAY, T0 + 1 * DAY)
    with pytest.raises(RuntimeError, match="not a legitimate seam"):
        _verify(_Conn([a, b]), position_at=far)


def test_a_single_contact_is_checked_exactly_as_before():
    """No abutting neighbour anywhere: unchanged behaviour for the ordinary span (entry and exit are orb-edge crossings)."""
    one = ("S", T0 - EDGE_DAYS * DAY, T0 + EDGE_DAYS * DAY, T0 - 5 * DAY)       # one span across the whole in-band stretch (the WP2 'one continuous span' shape)
    assert _verify(_Conn([one])) == {"contacts": 1}
    with pytest.raises(RuntimeError, match="still in the geometry just after the stored end"):
        _verify(_Conn([("S", T0 - EDGE_DAYS * DAY, T0 + 7 * DAY, T0 - 5 * DAY)]))


def test_the_derived_predicates_agree_with_the_probe_the_junction_check_reuses():
    """`_inside_fn` is the SAME ephemeris-only predicate `_probe_contact` builds (a station-in-band instant is inside; a far instant is not)."""
    inside = wv._inside_fn(curve, "venus", "conjunction", f"point:{RAY}")
    assert inside(T0) and inside(T0 + 8 * DAY) and not inside(T0 + 9 * DAY)
    assert wv._junction_problem(curve, "venus", "conjunction", f"point:{RAY}", T0, 0.00027777778, 60.0) is None


# ── Codex VERIFIER-CODEX-1 amendments to the seam fix ───────────────────────────────────────────────────────────────────────

def test_amendment_1_a_seam_needs_genuinely_shared_endpoints_even_a_half_second_gap_is_a_gap():
    """contact_certify unions touching intervals and keeps every positive gap, so the member check must agree: no tolerance in the shared instant."""
    b_late = ("B", T0 + timedelta(seconds=0.5), T0 + EDGE_DAYS * DAY, T0 + 5 * DAY)
    with pytest.raises(RuntimeError) as exc:
        _verify(_Conn([_A(), b_late]))
    assert "just after the stored end" in str(exc.value) and "just before the stored start" in str(exc.value)
    assert _verify(_Conn([_A(), _B()])) == {"contacts": 2}                                      # exact equality is accepted


def test_amendment_2_continuity_is_proved_across_the_exempted_interval_and_the_junction_itself_is_sampled(monkeypatch):
    """A 4 s excursion OUTSIDE the band centred on the junction (two inside samples at +-60 s, or any grid not containing the junction, would never see it) is
    refused because the junction itself is a sample. Isolated from criteria (a) and (b) so only the continuity proof is under test."""
    def spike(body, t):
        d = (t - T0).total_seconds()
        base = curve(body, t)
        return base + (2.0 if abs(d) <= 2.0 else 0.0)             # a +2 degree excursion for the 4 s around the junction (the grid step is 5 s)
    monkeypatch.setattr(wv.bm, "time_tolerance_seconds", lambda *a, **k: None)
    monkeypatch.setattr(wv, "_station_near", lambda *a, **k: (T0, 0.01))
    why = wv._junction_problem(spike, "venus", "conjunction", f"point:{RAY}", T0, 0.00027777778, 60.0)
    assert why and "continuity across the seam cannot be established" in why and "at the junction itself" in why
    assert wv._junction_problem(curve, "venus", "conjunction", f"point:{RAY}", T0, 0.00027777778, 60.0) is None


def test_amendment_2_the_clearance_bound_is_what_excludes_a_short_excursion(monkeypatch):
    """The proof: every sample must be inside by at least the farthest the body can move between samples (VMAX x step). A junction that is inside by
    LESS than that cannot be shown continuous, even if every sample happens to be inside."""
    def edge(body, t):                                              # sits 0.000001 degrees inside the band edge at the junction
        d = (t - T0).total_seconds() / 86400.0
        return RAY - 1.0 + 0.000001 + 0.02 * d * d
    monkeypatch.setattr(wv.bm, "time_tolerance_seconds", lambda *a, **k: None)
    monkeypatch.setattr(wv, "_station_near", lambda *a, **k: (T0, 0.01))
    why = wv._junction_problem(edge, "venus", "conjunction", f"point:{RAY}", T0, 0.00027777778, 60.0)
    assert why and "less than the" in why and "it can move between samples" in why


def test_amendment_4_a_slow_body_that_never_reverses_is_not_a_station():
    """Low speed alone (boundary_match's criterion) is not a reversal: a monotone inflection with zero speed at the junction is refused."""
    def inflection(body, t):
        d = (t - T0).total_seconds() / 86400.0
        return RAY + 0.0002 * d ** 3                                 # speed 0 at the junction, increasing on both sides, no reversal
    a = ("A", T0 - 17.0 * DAY, T0, T0)
    b = ("B", T0, T0 + 17.0 * DAY, T0)
    assert wv.bm.time_tolerance_seconds(inflection, "venus", T0, 0.00027777778) is None          # criterion (a) alone WOULD accept it
    with pytest.raises(RuntimeError, match=r"no reversal of venus's motion is bracketed within 6 h"):
        _verify(_Conn([a, b]), position_at=inflection)


def test_amendment_4_the_junction_must_sit_at_the_located_station_to_the_stated_accuracy():
    """A split hours away from the true station is refused; a split minutes away (indistinguishable from the station at the stated 1 arcsecond) is accepted."""
    for hours, ok in ((6.0, False), (0.25, True)):
        j = T0 + timedelta(hours=hours)
        a = ("A", T0 - EDGE_DAYS * DAY, j, T0 - 5 * DAY)
        b = ("B", j, T0 + EDGE_DAYS * DAY, T0 + 5 * DAY)
        if ok:
            assert _verify(_Conn([a, b])) == {"contacts": 2}
        else:
            with pytest.raises(RuntimeError, match="not a legitimate seam"):
                _verify(_Conn([a, b]))


def test_amendment_4_the_station_distance_bound_alone_refuses_a_far_junction(monkeypatch):
    """Isolated from the low-speed criterion: with (a) bypassed, a junction 4 h from the located station (inside the 6 h search window, beyond the roughly 2.9 h
    at which this curve is still at the station's longitude to 1 arcsecond) is refused by the angular-accuracy bound; one 5 minutes away is accepted."""
    monkeypatch.setattr(wv.bm, "time_tolerance_seconds", lambda *a, **k: None)
    why = wv._junction_problem(curve, "venus", "conjunction", f"point:{RAY}", T0 + timedelta(hours=4), 0.00027777778, 60.0)
    assert why and "farther than the" in why and "at which the body is still at the station's longitude to the stated accuracy" in why
    assert wv._junction_problem(curve, "venus", "conjunction", f"point:{RAY}", T0 + timedelta(minutes=5), 0.00027777778, 60.0) is None


def test_the_seam_exemption_is_only_for_point_contacts():
    why = wv._junction_problem(curve, "venus", "residence", "span:5", T0, 0.00027777778, 60.0)
    assert why and "seams are exempt only for point contacts" in why


# ── the aside: a no-exact graze ─────────────────────────────────────────────────────────────────────────────────────────────

def test_the_certifier_would_report_a_graze_as_omitted_because_it_reconstructs_the_whole_band():
    """Aside to the SEAM-RULING (characterisation, not a fix): the builder mints a point contact only around an EXACT ROOT of the ray level
    (`solve_point_edges` -> `find_roots`), so a graze (band entered, ray level never reached) yields no contact; `contact_certify` reconstructs every in-band
    interval, so it reports that interval as 'not in the ledger'. The two disagree on a graze; a real one has not been exhibited on this chart (see the report)."""
    from services.gochara_kernel import contact_certify as cc
    lo, hi = T0 - 30 * DAY, T0 + 30 * DAY
    want = cc.expected_intervals(curve_graze, "venus", "conjunction", f"point:{RAY}", lo, hi)
    assert len(want) == 1                                                       # the in-band stretch exists (|lambda - ray| <= 1 around the minimum)
    problems = cc.compare_contact_sets(curve_graze, "venus", "conjunction", f"point:{RAY}", want, [], lo, hi)
    assert problems and "is not in the ledger" in problems[0]


# ── the real sky: the writer's own window phase and the verification job, over the real stations ───────────────────────────

H_VENUS = (datetime(1998, 1, 20, tzinfo=UTC), datetime(1998, 2, 25, tzinfo=UTC))      # Venus direct station 1998-02-05 21:28:04 UT, 0.752 deg from 265.39
H_MERCURY = (datetime(2000, 6, 1, tzinfo=UTC), datetime(2000, 7, 20, tzinfo=UTC))     # Mercury retrograde station 2000-06-23 08:31:23 UT, 0.712 deg from 85.39
STATIONS = {"venus": (H_VENUS, datetime(1998, 2, 5, 21, 28, 4, tzinfo=UTC), "conjunction"),
            "mercury": (H_MERCURY, datetime(2000, 6, 23, 8, 31, 23, tzinfo=UTC), "aspect")}


@pytest.fixture()
def rworld(template):
    from .test_a55_replace_chain import _World
    w = _World(template)
    try:
        yield w
    finally:
        w.close()


def _chain(w, horizon, cls="marriage", full=True):
    """The writer's own substeps. `full=False` skips the P1 grain and `verify:` for a horizon the stubbed L1's daśā rows do not cover (the stub-L1 limit the
    existing suites record: P1's period-running support cannot be derived there); the window phase (P2, P3, P4), where the defect lived, is run either way."""
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    w.step(writer_mod.MANIFEST_SUBSTEP, horizon)
    w.step(writer_mod.SNAPSHOT_SUBSTEP, horizon)
    w.step(f"inventory:{cls}", horizon)
    w.step(f"coverage:{cls}", horizon)
    for p in writer_mod.RECORD_PATHS:
        if full or p != "P1":
            w.step(f"record:{cls}:{p}", horizon)
    for p in writer_mod.WINDOW_PATHS:
        if full or p != "P1":
            w.step(f"window:{cls}:{p}", horizon)      # window:marriage:P3 used to FAIL here: 'member geometry verification failed'
    if full:
        w.step(f"verify:{cls}", horizon)


def _pair(w, body, relation):
    from .test_a55_replace_chain import GEN
    return w.conn.execute(
        "SELECT c.contact_id::text, c.t_in, c.t_out FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o"
        " ON o.physical_object_id = c.physical_object_id WHERE c.generation = %s AND c.body = %s AND c.relation_kind = %s"
        " AND o.canonical_target LIKE 'point:%%' ORDER BY c.t_in", (GEN, body, relation)).fetchall()


@pytest.mark.parametrize("body", ["venus", "mercury"])
def test_the_real_station_pair_is_stored_as_two_abutting_contacts_and_the_whole_marriage_chain_now_completes(rworld, body):
    """Computation behind the ruling: the stored point contacts of the body are TWO rows sharing one instant, that instant is the Swiss station, and
    the writer's window phase, its in-build verify and the verification job's member-geometry stage all accept it."""
    horizon, station, relation = STATIONS[body]
    _chain(rworld, horizon, full=(body == "venus"))        # Venus 1998: the WHOLE chain incl. P1 and verify:; Mercury 2000: no P1 (stub-L1 daśā)
    rows = _pair(rworld, body, relation)
    assert len(rows) == 2 and rows[0][2] == rows[1][1], rows                                        # two abutting contacts sharing the station instant
    assert abs((rows[0][2] - station).total_seconds()) < 30.0, (rows[0][2], station)                 # and it IS the station (a flat extremum: the instant is conditioned to seconds)
    from services.gochara_kernel import window_verifier as wvm
    from .test_p1_exclusion_h_unknown import _position_at
    from .test_a55_replace_chain import CHART_ID, GEN
    for path in ("P3",):
        out = wvm.verify_member_geometry(rworld.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", path_id=path,
                                         rule_version="1.0.0", position_at=_position_at)
        assert out["contacts"] >= 2
    if body == "venus":                                  # the verification JOB's per-class entry point (member_geometry P3 included) on the same real-sky world
        from .test_p1_exclusion_h_unknown import _verify
        report = _verify(rworld, "marriage")
        assert report.get("status") != "UNVERIFIED" and "windows" in report, report


def test_on_the_real_sky_a_truncated_station_pair_still_fails(rworld):
    """Delete the second arc's contact: the first now ends at a station INSIDE the band with nothing abutting it; the check must still fail."""
    from services.gochara_kernel import window_verifier as wvm
    from .test_p1_exclusion_h_unknown import _position_at
    from .test_a55_replace_chain import CHART_ID, GEN
    horizon, _station, relation = STATIONS["venus"]
    _chain(rworld, horizon)
    rows = _pair(rworld, "venus", relation)
    assert len(rows) == 2
    with rworld.conn.transaction():
        rworld.conn.execute("SET LOCAL session_replication_role = replica")
        rworld.conn.execute("DELETE FROM public.ka_gochara_contact WHERE generation = %s AND contact_id::text = %s", (GEN, rows[1][0]))
    with pytest.raises(RuntimeError, match=r"member geometry verification failed marriage/P3.*still in the geometry just after the stored end"):
        wvm.verify_member_geometry(rworld.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", path_id="P3",
                                   rule_version="1.0.0", position_at=_position_at)


# ── amendment 3: the registered writer cannot emit OVERLAPPING point contacts ──────────────────────────────────────────────

def test_amendment_3_point_contacts_of_a_retrograde_loop_abut_at_stations_and_never_overlap_on_the_real_sky():
    """Codex reproduced overlapping episodes with the Saturn fixture of A5.3 v1.36 (Oct 2025 to Jan 2026) failing the member check. The REGISTERED writer's point
    contacts cannot overlap: `solve_point_edges` mints one contact per EXACT ROOT of the ray level, each bounded by that root's own MONOTONE ARC
    (`record_store._in_orb_span_around_root`: a station closes the span; arcs partition time), and two roots of the same level lie in different arcs, so their spans
    are disjoint and touch at most at the station that separates the arcs; roots of different aspect rays are at least 60 degrees apart (more than twice the 1 degree
    orb). The overlapping episodes of v1.36 came from the earlier per-branch `episodes.in_orb_intervals` solver, which the writer no longer calls for point
    contacts (E8-2, 2026-10-01). This pins it on Saturn's real 2025 loop, for a level near the station (two roots) and one inside the loop (three roots)."""
    from datetime import date
    from services.gochara_kernel import arcs as gk_arcs
    from services.gochara_kernel import record_store as rs
    from services.gochara_kernel.contacts import find_roots
    from services.gochara_kernel.knots import calc_sidereal_lon, sample_knots
    from .conftest import EPHE_PATH, assert_real_ephemeris
    assert_real_ephemeris()
    ks = sample_knots("Saturn", date(2025, 3, 1), date(2026, 3, 1), EPHE_PATH)
    index = gk_arcs.build_arc_index("Saturn", ks.knot_jds, ks.longitudes_deg)
    jd0 = 2440587.5
    lons = [(datetime(2025, 11, 1, tzinfo=UTC) + timedelta(hours=h), None) for h in range(0, 24 * 60, 6)]
    vals = [(t, calc_sidereal_lon("Saturn", t.timestamp() / 86400.0 + jd0, EPHE_PATH)[0]) for t, _ in lons]
    station_min = min(v for _t, v in vals)                         # the retrograde -> direct station (Nov 28 2025) is the minimum of this stretch
    peak = max(calc_sidereal_lon("Saturn", (datetime(2025, 7, 13, tzinfo=UTC)).timestamp() / 86400.0 + jd0, EPHE_PATH)[0], station_min)
    for label, level, want_roots in (("a level 0.5 deg above the station: the loop's two crossings abut at the station", station_min + 0.5, 3),
                                     ("a level inside the loop: three crossings", (station_min + peak) / 2.0, 3)):
        roots = find_roots(index, "Saturn", rs.POINT_KERNEL_RELATION["conjunction"], level % 360.0, EPHE_PATH, refine=True)
        assert len(roots) == want_roots, (label, [r.exact_jd for r in roots])      # (the first is the direct pass of spring 2025, far from the loop)
        spans = sorted(rs._in_orb_span_around_root(index, r, 1.0) for r in roots)
        for (a0, b0), (a1, b1) in zip(spans, spans[1:]):
            assert b0 <= a1 + 1e-9, (label, "OVERLAP", (a0, b0), (a1, b1))                   # never overlapping
            assert a1 - b0 <= 1e-6 or a1 > b0, (label, "touch or gap", b0, a1)                # and a touch is exact (a shared station), never a sliver of overlap
        touching = [(b0, a1) for (a0, b0), (a1, b1) in zip(spans, spans[1:]) if abs(a1 - b0) <= 1e-9]
        if level == station_min + 0.5:
            assert len(touching) == 1                                                        # the retrograde and the later direct crossing abut at the station
