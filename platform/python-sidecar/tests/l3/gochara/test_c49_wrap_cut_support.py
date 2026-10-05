"""C49 — a 0/360 wrap cut is a representation artefact, never the end of a contact's support (steward WRAP-FIX; Stream B's confirmation in
tracker ref VERIFIER-CODEX-2, evidence WRAP_CUT_EVIDENCE_20261005).

THE DEFECT: `arcs.build_arc_index` stage 2 splits every station-bounded segment at each 360-degree band (so the root SEARCH can be range-joined
by degree) and `record_store._in_orb_span_around_root` took a point contact's support from the root's ARC, so a ray level within one degree of
0/360 had its support stopped at the cut. On the real chart exactly one stretch is wrong (Saturn's aspect to natal Mercury, ray level 0.839,
1998-04-16: the builder started it 30.6 hours late) and both member-geometry verification and full certification reject it.

THE FIX: the span comes from the root's station-bounded SEGMENT (`index.segments`); only a station ends it.

REAL SKY, no mocks of the ephemeris: the pinned .se1 files, the writer's own arc-index construction, the INDEPENDENT reconstruction of the contact
intervals (`contact_certify.expected_intervals`, hourly samples and bisection, no arc index) as the reference. The legacy behaviour is reproduced
by handing the same function an index whose `segments` ARE the arcs (a shim), so every test shows the defect and the fix on identical inputs.
"""
from __future__ import annotations

import functools
import types
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import arcs as gk_arcs
from services.gochara_kernel import contact_certify as cc
from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import record_store as rs
from services.gochara_kernel.knots import calc_sidereal_lon, sample_knots
from services.gochara_kernel.substrate import SUBSTRATE_DOMAIN_END, SUBSTRATE_DOMAIN_START, PhysicalObjectId

from .conftest import EPHE_PATH
from .test_a53_record_store import CHART

UTC = timezone.utc
JD_UNIX = 2440587.5
TOLERANCE_S = 600.0          # an hour-scale defect (30 h) is far outside it; the derived boundary tolerance is minutes at most
FULL = (datetime(1998, 1, 1, tzinfo=UTC), datetime(2026, 4, 17, tzinfo=UTC))
SATURN_ASPECT_TARGET = 270.838758254083       # the real chart's natal Mercury: Saturn's 90-degree aspect ray level is 0.8388


@functools.lru_cache(maxsize=None)
def real_index(body: str):
    ks = sample_knots(body, SUBSTRATE_DOMAIN_START.date(), SUBSTRATE_DOMAIN_END.date(), EPHE_PATH)
    return gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)


def position_at(body: str, t: datetime) -> float:
    lon, retflag = calc_sidereal_lon(body.title(), t.timestamp() / 86400.0 + JD_UNIX, EPHE_PATH)
    assert retflag & 2
    return lon


class legacy_index:
    """The same index but with the ARCS standing in for the segments: `_in_orb_span_around_root` then behaves exactly as it did before the fix."""

    def __init__(self, index):
        self._index = index
        self.segments = index.arcs

    def __getattr__(self, name):
        return getattr(self._index, name)


def point_edge(klass: str, relation: str, lam: float, agent: str):
    edges = [e for e in ev.enumerate_edges(klass, "P3", CHART) if e.transit and e.relation == relation and e.agent == agent]
    assert edges, f"no {relation} edge for {agent} in {klass}/P3"
    e = edges[0]
    obj = PhysicalObjectId(body=agent, relation_kind=relation, canonical_target=f"point:{float(lam)!r}", convention_id=e.obj.convention_id)
    return ev.RecordEdge(**{**e.__dict__, "obj": obj})


def solve(index, edge, horizon=FULL, refine=False):
    return sorted(rs.solve_point_edges([edge], arc_index_for=lambda b: index, horizon=horizon, refine=refine)[id(edge)], key=lambda o: o.t_in)


def reference(edge, horizon):
    return cc.expected_intervals(position_at, edge.agent, edge.relation, edge.obj.canonical_target, *horizon)


def seconds(a: datetime, b: datetime) -> float:
    return abs((a - b).total_seconds())


def union(occs):
    """The stored contacts as a contact SET: a station inside the band leaves two ABUTTING contacts (one per monotone segment), and the independent
    reconstruction reports their union, so the two are compared as sets (contact_certify unions the ledger the same way)."""
    out = []
    for o in sorted(occs, key=lambda o: o.t_in):
        if out and o.t_in <= out[-1][1]:
            out[-1][1] = max(out[-1][1], o.t_out)
            out[-1][2].append(o)
        else:
            out.append([o.t_in, o.t_out, [o]])
    return [(a, b, members) for a, b, members in out]


def match(item, intervals):
    """The independent interval that contains the (merged) interval's midpoint."""
    a, b = (item[0], item[1]) if isinstance(item, tuple) else (item.t_in, item.t_out)
    mid = a + (b - a) / 2
    hits = [iv for iv in intervals if iv[0] <= mid <= iv[1]]
    assert len(hits) == 1, (a, b, hits)
    return hits[0]


# ── Saturn 1998: the real chart's one wrong stretch ──────────────────────────────────────────────────────────────────────────────

def test_saturn_aspect_to_natal_mercury_1998_starts_at_the_physical_time_not_30_hours_late():
    edge = point_edge("career_change", "aspect", SATURN_ASPECT_TARGET, "saturn")
    idx = real_index("Saturn")
    horizon = (datetime(1998, 3, 1, tzinfo=UTC), datetime(1998, 6, 1, tzinfo=UTC))
    (new,), (old,) = solve(idx, edge, horizon), solve(legacy_index(idx), edge, horizon)
    ref = match(new, reference(edge, horizon))
    assert seconds(new.t_in, ref[0]) < TOLERANCE_S and seconds(new.t_out, ref[1]) < TOLERANCE_S, (new.t_in, ref)
    assert (old.t_in - ref[0]) > timedelta(hours=29), (old.t_in, ref[0])                  # the defect: ~30.5 h late on identical inputs
    assert seconds(old.t_out, new.t_out) < 1.0                                           # the END was never cut: only the start was wrong
    assert new.contact.occurrence_ordinal == old.contact.occurrence_ordinal and str(new.contact.contact_id) == str(old.contact.contact_id)


# ── Sun, Mercury, Venus: every occurrence of a level whose band contains the cut, incl. a multi-revolution stationless segment ──────

@pytest.mark.parametrize("body", ["Sun", "Mercury", "Venus"])
def test_every_occurrence_of_a_ray_level_inside_the_cut_band_matches_the_independent_reconstruction(body):
    """Conjunction with a point at 0.3 degrees: the band (-0.7, 1.3) contains the cut. The Sun is the multi-revolution STATIONLESS segment case
    (one segment for decades: its nearest unwrapped level keeps the occurrence right); Mercury and Venus cross the cut direct and retrograde."""
    edge = point_edge("marriage", "conjunction", 0.3, body.lower())
    idx = real_index(body)
    horizon = (FULL[0], datetime(2008, 1, 1, tzinfo=UTC)) if body != "Sun" else (FULL[0], datetime(2012, 1, 1, tzinfo=UTC))
    new, old = solve(idx, edge, horizon), solve(legacy_index(idx), edge, horizon)
    refs = reference(edge, horizon)
    assert len(new) == len(old) >= 3
    assert len(union(new)) == len(refs), (len(union(new)), len(refs))                      # every independent contact, exactly once
    for a, b, _members in union(new):
        ref = match((a, b), refs)
        assert seconds(a, ref[0]) < TOLERANCE_S and seconds(b, ref[1]) < TOLERANCE_S, (body, a, b, ref)
    wrong_before = [(a, b) for a, b, _m in union(old) if seconds(a, match((a, b), refs)[0]) > TOLERANCE_S or seconds(b, match((a, b), refs)[1]) > TOLERANCE_S]
    assert wrong_before, f"{body}: the legacy derivation was expected to be wrong at the cut somewhere in this horizon"


# ── a retrograde segment spanning a cut ──────────────────────────────────────────────────────────────────────────────────────────

def _retrograde_segment_spanning_a_cut(index):
    for seg in index.segments:
        if seg.direction == -1:
            lo, hi = sorted((seg.start_lon_unwrapped, seg.end_lon_unwrapped))
            k = int(lo // 360.0) + 1
            if 360.0 * k < hi - 0.05 and 360.0 * k > lo + 0.05:
                return seg
    return None


@pytest.mark.parametrize("body", ["Mercury", "Venus", "Mars"])
def test_a_retrograde_segment_that_spans_a_cut_is_supported_across_it(body):
    idx = real_index(body)
    seg = _retrograde_segment_spanning_a_cut(idx)
    if seg is None:
        pytest.skip(f"{body}: no retrograde segment spans a 0/360 cut in 1998-2085")
    from services.gochara_kernel.substrate import jd_to_utc
    t0, t1 = jd_to_utc(seg.start_jd), jd_to_utc(seg.end_jd)
    if t0 >= FULL[1]:
        pytest.skip(f"{body}: the spanning retrograde segment is after the reference horizon")
    horizon = (max(FULL[0], t0 - timedelta(days=40)), min(FULL[1], t1 + timedelta(days=40)))
    edge = point_edge("marriage", "conjunction", 0.0, body.lower())
    new, old = solve(idx, edge, horizon), solve(legacy_index(idx), edge, horizon)
    refs = reference(edge, horizon)
    in_segment = [o for o in new if o.t_exact is not None and seg.start_jd <= (o.t_exact.timestamp() / 86400.0 + JD_UNIX) <= seg.end_jd]
    assert in_segment, f"{body}: no contact of the 0-degree level falls on the spanning retrograde segment"
    for a, b, _members in union(new):
        ref = match((a, b), refs)
        assert seconds(a, ref[0]) < TOLERANCE_S and seconds(b, ref[1]) < TOLERANCE_S, (body, a, b, ref)
    assert any(seconds(a, match((a, b), refs)[0]) > TOLERANCE_S or seconds(b, match((a, b), refs)[1]) > TOLERANCE_S for a, b, _m in union(old))


# ── a station inside the band still ends the span ───────────────────────────────────────────────────────────────────────────────

def _station_within_one_degree_of_a_cut(index):
    from services.gochara_kernel.substrate import jd_to_utc
    out = []
    for jd in index.stations:
        lon = index.evaluate(jd) % 360.0
        off = lon if lon < 180.0 else lon - 360.0           # signed distance to the cut
        if abs(off) < 1.0 and FULL[0] < jd_to_utc(jd) < FULL[1] - timedelta(days=60):
            out.append((jd, off))
    return out


@pytest.mark.parametrize("body", ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"])
def test_a_span_that_meets_a_station_inside_a_cut_band_ends_at_the_station_not_at_the_cut(body):
    idx = real_index(body)
    candidates = _station_within_one_degree_of_a_cut(idx)
    if not candidates:
        pytest.skip(f"{body}: no station within one degree of a 0/360 cut in 1998-2026")
    from services.gochara_kernel.substrate import jd_to_utc
    checked = 0
    for jd, off in candidates:
        t_s = jd_to_utc(jd)
        lam = (off / 2.0) % 360.0                                  # the band (lam-1, lam+1) contains BOTH the cut and the station
        edge = point_edge("marriage", "conjunction", lam, body.lower())
        horizon = (t_s - timedelta(days=90), t_s + timedelta(days=90))
        new = solve(idx, edge, horizon)
        refs = reference(edge, horizon)
        touching = [o for o in new if min(seconds(o.t_in, t_s), seconds(o.t_out, t_s)) < 3600.0 * 6]
        for a, b, _members in union(new):
            ref = match((a, b), refs)
            assert seconds(a, ref[0]) < TOLERANCE_S * 3 and seconds(b, ref[1]) < TOLERANCE_S * 3, (body, off, a, b, ref)
        if touching:
            checked += 1
            # the support ends AT the station (within the angular tolerance expressed in time near a station), never at the cut
            assert any(min(seconds(o.t_in, t_s), seconds(o.t_out, t_s)) < 3600.0 * 6 for o in touching)
    assert checked >= 1, f"{body}: no contact ended at a station inside a cut band in the candidates {candidates}"


# ── ids, ordinals and every non-wrap span are unchanged ─────────────────────────────────────────────────────────────────────────────

def test_ids_ordinals_and_every_non_wrap_span_are_unchanged_for_the_whole_chart():
    """For every (body, relation, natal point) of the stub chart (the real chart's natal longitudes) over the whole horizon: the contacts' ids and
    ordinals are identical before and after, and a span differs ONLY where the ray band contains the 0/360 cut."""
    differing, total = [], 0
    for body in ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        idx = real_index(body)
        for relation in ("conjunction", "aspect"):
            for lam in sorted(CHART["natal"].values()):
                try:
                    edge = point_edge("career_change", relation, lam, body.lower())
                except AssertionError:
                    continue
                new, old = solve(idx, edge), solve(legacy_index(idx), edge)
                assert [str(o.contact.contact_id) for o in new] == [str(o.contact.contact_id) for o in old]
                assert [o.contact.occurrence_ordinal for o in new] == [o.contact.occurrence_ordinal for o in old]
                total += len(new)
                for n, o in zip(new, old):
                    if (n.t_in, n.t_out) != (o.t_in, o.t_out):
                        differing.append((body, relation, lam, n.t_exact))
                        level = n.level_deg
                        assert min(level, 360.0 - level) < 1.0 - 1e-9, (body, relation, lam, level)   # ONLY where the band STRICTLY contains the cut
    assert total > 500 and len(differing) >= 1, (total, differing)
    assert ("saturn", "aspect") in {(b.lower(), r) for b, r, _l, _t in differing}


# ── a fresh build before and after, on the stub chart, through the writer's own substeps ──────────────────────────────────────────────────

from .test_a55_replace_chain import _World, template  # noqa: E402,F401


def _contacts(world):
    return {r[0]: (r[1], r[2]) for r in world.conn.execute(
        "SELECT contact_id::text, t_in, t_out FROM public.ka_gochara_contact WHERE generation = '5.0'").fetchall()}


def test_a_fresh_build_before_and_after_has_the_same_contact_ids_and_only_the_wrap_contact_differs(template, monkeypatch):
    """career_change P3 over 1998 on the stub chart (natal Mercury 270.84: Saturn's aspect to it is the real chart's wrap case). Built twice by the
    writer's real substeps, once with the arc-only derivation (the shim) and once with the fix: the SAME contact ids, and exactly the wrap
    contact's start differs, by the 30.6 hours Stream B measured."""
    horizon = (datetime(1998, 1, 1, tzinfo=UTC), datetime(1998, 12, 31, tzinfo=UTC))
    fixed = rs._in_orb_span_around_root
    built = {}
    for name, span in (("before", lambda index, root, orb: fixed(legacy_index(index), root, orb)), ("after", fixed)):
        monkeypatch.setattr(rs, "_in_orb_span_around_root", span)
        world = _World(template)
        try:
            world.build(horizon, classes=("career_change",), paths=("P3",))
            built[name] = _contacts(world)
        finally:
            world.close()
    before, after = built["before"], built["after"]
    assert len(before) > 20 and set(before) == set(after), (len(before), len(after))              # the same contacts, the same ids
    changed = {cid: (before[cid], after[cid]) for cid in before if before[cid] != after[cid]}
    assert len(changed) == 1, changed
    (old, new), = changed.values()
    assert old[1] == new[1] and (old[0] - new[0]) > timedelta(hours=29), (old, new)               # only the START moved, by about 30.6 hours


# ── a band that merely TOUCHES the cut is unchanged, bit for bit (Codex WRAP-CODEX-1) ──────────────────────────────────────────────────

@pytest.mark.parametrize("body", ["Sun", "Saturn", "Rahu", "Ketu"])
@pytest.mark.parametrize("level", [1.0, 359.0])
def test_a_band_whose_edge_lies_exactly_on_the_cut_keeps_the_arc_derived_span_bit_for_bit(body, level):
    """Conjunction at level 1 (band 0 to 2) or 359 (band 358 to 360): the band touches the cut but lies wholly inside its arc, so EVERY occurrence over
    the whole horizon is exactly (==) what the arc-only derivation gives. The first version of the fix re-solved the endpoint here and moved every
    occurrence by seconds."""
    idx = real_index(body)
    try:
        edge = point_edge("marriage", "conjunction", level, body.lower())
    except AssertionError:
        pytest.skip(f"{body}: no conjunction edge in marriage/P3")
    domain = (SUBSTRATE_DOMAIN_START, SUBSTRATE_DOMAIN_END)            # the whole 87-year domain: the slow bodies cross a level only a few times
    new, old = solve(idx, edge, domain), solve(legacy_index(idx), edge, domain)
    assert len(new) == len(old) >= (80 if body == "Sun" else 1), (body, level, len(new))
    for n, o in zip(new, old):
        assert (n.t_in, n.t_out) == (o.t_in, o.t_out), (body, level, n.t_exact, n.t_in - o.t_in, n.t_out - o.t_out)
