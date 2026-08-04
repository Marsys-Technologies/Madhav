"""W2G — GOCHARA-2.0 arc substrate + contact solver tests.

TDD-first for the W2G writer lane (ṢAḌ-DARŚANA brief §3 W2G, item 19). These
tests were written BEFORE the implementation and each one asserts BOTH ways
where a detector could otherwise pass by always returning the same answer
(CLAUDE.md §N.8 — a status must be earned by a detector that measures the
specific claim).

WHAT IS UNDER TEST — the three load-bearing claims of the 2.0 architecture:

  1. **Monotone-arc decomposition is correct and complete.** A body's century
     of motion decomposes into arcs that are each strictly monotone in
     longitude and span < 360°, split at real stations (derivative roots) and
     at 360° wrap boundaries. Contiguity and coverage are asserted, so a
     silently-dropped arc (which would silently drop real contacts) fails.

  2. **A contact is a bracketed root-find, not a scan.** Because every arc is
     monotone, "when does body B reach degree L" is a bisection inside a
     bracket the arc index already identified — no day-stepping search, and
     therefore no per-call cost that scales with window length.

  3. **The solver issues a CONSTANT number of database reads, independent of
     the number of targets, bodies and primitives.** This is the measured
     design input this lane exists to answer: the v1 sweep's dominant cost is
     ~110-120ms per contact-primitive call from per-call DB chatter
     (`services/gochara_intensity/configuration_activity.py`'s own documented
     finding, re-confirmed by clean A/B measurement 2026-08-04 and recorded in
     SHAD_DARSHANA_STATE.md lane (a)). W2G eliminates it BY CONSTRUCTION, and
     `test_solver_query_count_is_constant_in_target_count` is the detector
     that would go red if a future edit reintroduced a per-target query.

Everything here is offline and deterministic — synthetic ephemeris series with
analytically-known crossings, no database, no network. The live-DB half is the
writer's own test tier.
"""
from __future__ import annotations

import math

import pytest

from services.w2g import (
    ARC_ENGINE_VERSION,
    MonotoneArc,
    ContactEvent,
    build_arcs,
    arcs_covering_degree,
    solve_crossing_jd,
    solve_contact_window,
    find_contacts,
    ContactSolver,
    body_tier,
    materialization_policy,
    TIER_EAGER,
    TIER_CONDITIONAL,
    TIER_LAZY,
    arc_fingerprint,
    class_fingerprint,
)

# ── Synthetic ephemeris series ────────────────────────────────────────────────
#
# `build_arcs` takes exactly what `ephemeris_daily` gives: a knot abscissa
# (noon-UT Julian day) and a WRAPPED tropical longitude per knot. These helpers
# manufacture series whose crossings are known analytically.

JD0 = 2_451_545.0  # J2000.0 noon UT — an arbitrary but real epoch anchor


def _direct_series(n_days: int, deg_per_day: float, lon0: float = 0.0):
    """Uniform prograde motion. Crossing times are exactly linear."""
    jds = [JD0 + float(i) for i in range(n_days)]
    lons = [(lon0 + deg_per_day * i) % 360.0 for i in range(n_days)]
    return jds, lons


def _retrograde_loop_series(n_days: int = 200, lon0: float = 100.0):
    """Prograde -> station -> retrograde -> station -> prograde.

    A smooth sinusoidal modulation on top of a slow drift, so the derivative
    genuinely changes sign twice and the station instants are real roots of the
    fitted spline rather than knot artifacts.
    """
    jds = [JD0 + float(i) for i in range(n_days)]
    lons = []
    for i in range(n_days):
        t = float(i)
        lon = lon0 + 0.20 * t + 6.0 * math.sin(2.0 * math.pi * t / 100.0)
        lons.append(lon % 360.0)
    return jds, lons


# ── 1. Arc decomposition ──────────────────────────────────────────────────────


def test_direct_motion_within_one_revolution_is_a_single_arc():
    jds, lons = _direct_series(200, 1.0, lon0=10.0)  # 10° -> 209°, no wrap
    arcs = build_arcs("Mars", jds, lons)
    assert len(arcs) == 1
    assert arcs[0].direction == 1
    assert arcs[0].start_jd == pytest.approx(jds[0])
    assert arcs[0].end_jd == pytest.approx(jds[-1])


def test_direct_motion_across_a_wrap_splits_at_the_wrap():
    # 350° + 1°/day for 30 days crosses 360 exactly once.
    jds, lons = _direct_series(30, 1.0, lon0=350.0)
    arcs = build_arcs("Mars", jds, lons)
    assert len(arcs) == 2, "a 360-degree wrap must open a new arc"
    assert arcs[0].wrap_index + 1 == arcs[1].wrap_index
    # The split instant is where longitude reaches 360 — 10 days in.
    assert arcs[0].end_jd == pytest.approx(JD0 + 10.0, abs=1e-3)


def test_every_arc_spans_less_than_one_revolution():
    """The property the range-join predicate depends on: an arc covers any
    given degree AT MOST once, so `lo <= L <= hi` is exact."""
    jds, lons = _direct_series(800, 1.0, lon0=0.0)  # ~2.2 revolutions
    arcs = build_arcs("Sun", jds, lons)
    assert len(arcs) >= 3
    for arc in arcs:
        span = abs(arc.end_lon_unwrapped - arc.start_lon_unwrapped)
        assert span <= 360.0 + 1e-6, f"arc {arc.arc_index} spans {span}°"


def test_retrograde_loop_produces_direction_flips_at_real_stations():
    jds, lons = _retrograde_loop_series()
    arcs = build_arcs("Mercury", jds, lons)
    directions = [a.direction for a in arcs]
    assert 1 in directions and -1 in directions, (
        f"a retrograde loop must yield both directions, got {directions}"
    )
    # Directions must alternate at every station boundary — two adjacent arcs
    # with the same direction would mean a spurious split.
    for prev, nxt in zip(arcs, arcs[1:]):
        if prev.wrap_index == nxt.wrap_index:
            assert prev.direction != nxt.direction


def test_arcs_are_contiguous_and_cover_the_whole_epoch():
    jds, lons = _retrograde_loop_series()
    arcs = build_arcs("Mercury", jds, lons)
    assert arcs[0].start_jd == pytest.approx(jds[0])
    assert arcs[-1].end_jd == pytest.approx(jds[-1])
    for prev, nxt in zip(arcs, arcs[1:]):
        assert nxt.start_jd == pytest.approx(prev.end_jd, abs=1e-9), (
            "a gap between arcs is a silently-dropped contact window"
        )


def test_arc_indices_are_dense_and_ordered():
    jds, lons = _retrograde_loop_series()
    arcs = build_arcs("Mercury", jds, lons)
    assert [a.arc_index for a in arcs] == list(range(len(arcs)))


def test_wrapped_bounds_are_inside_the_circle():
    jds, lons = _direct_series(800, 1.0, lon0=0.0)
    for arc in build_arcs("Sun", jds, lons):
        for value in (arc.lon_start_deg, arc.lon_end_deg):
            assert -1e-6 <= value <= 360.0 + 1e-6


def test_too_few_knots_is_an_honest_error_not_a_silent_empty():
    with pytest.raises(ValueError):
        build_arcs("Sun", [JD0, JD0 + 1.0], [0.0, 1.0])


# ── 2. The range-join predicate ───────────────────────────────────────────────


def test_arcs_covering_degree_selects_only_covering_arcs():
    jds, lons = _direct_series(800, 1.0, lon0=0.0)  # 0° -> 799° unwrapped
    arcs = build_arcs("Sun", jds, lons)
    hits = arcs_covering_degree(arcs, 123.0)
    assert hits, "123° is crossed at least twice in 2.2 revolutions"
    for arc in hits:
        lo, hi = sorted((arc.lon_start_deg, arc.lon_end_deg))
        assert lo - 1e-9 <= 123.0 <= hi + 1e-9
    # And the complement: every arc NOT returned must genuinely not cover it.
    for arc in arcs:
        if arc in hits:
            continue
        lo, hi = sorted((arc.lon_start_deg, arc.lon_end_deg))
        assert not (lo <= 123.0 <= hi)


def test_arcs_covering_degree_is_empty_when_the_body_never_reaches_it():
    jds, lons = _direct_series(30, 1.0, lon0=10.0)  # only 10° -> 39°
    arcs = build_arcs("Mars", jds, lons)
    assert arcs_covering_degree(arcs, 200.0) == []


# ── 3. Root-finding ───────────────────────────────────────────────────────────


def test_solve_crossing_recovers_a_known_crossing_instant():
    """Uniform 1°/day from 10°: 123° is reached exactly 113 days in."""
    jds, lons = _direct_series(400, 1.0, lon0=10.0)
    arcs = build_arcs("Mars", jds, lons)
    arc = arcs_covering_degree(arcs, 123.0)[0]
    jd = solve_crossing_jd(arc, 123.0)
    assert jd == pytest.approx(JD0 + 113.0, abs=1e-3)


def test_solve_crossing_works_on_a_retrograde_arc():
    jds, lons = _retrograde_loop_series()
    arcs = build_arcs("Mercury", jds, lons)
    retro = [a for a in arcs if a.direction == -1]
    assert retro, "fixture must contain a retrograde arc"
    arc = retro[0]
    midpoint = 0.5 * (arc.lon_start_deg + arc.lon_end_deg)
    jd = solve_crossing_jd(arc, midpoint)
    assert arc.start_jd <= jd <= arc.end_jd
    assert arc.longitude_at(jd) == pytest.approx(midpoint, abs=1e-3)


def test_solve_crossing_refuses_a_degree_the_arc_does_not_cover():
    jds, lons = _direct_series(30, 1.0, lon0=10.0)
    arc = build_arcs("Mars", jds, lons)[0]
    with pytest.raises(ValueError):
        solve_crossing_jd(arc, 300.0)


def test_contact_window_brackets_the_exact_crossing():
    jds, lons = _direct_series(400, 1.0, lon0=10.0)
    arcs = build_arcs("Mars", jds, lons)
    arc = arcs_covering_degree(arcs, 123.0)[0]
    window = solve_contact_window(arc, 123.0, orb_deg=1.0)
    assert window is not None
    assert window.entry_jd < window.exact_jd < window.exit_jd
    # 1°/day, 1° orb -> entry one day before exact, exit one day after.
    assert window.exact_jd - window.entry_jd == pytest.approx(1.0, abs=1e-2)
    assert window.exit_jd - window.exact_jd == pytest.approx(1.0, abs=1e-2)


def test_contact_window_is_clipped_to_the_arc_and_flagged_when_truncated():
    """A contact whose orb runs off the end of an arc reports a truncated
    edge instead of inventing a crossing outside the arc's own validity."""
    jds, lons = _direct_series(30, 1.0, lon0=10.0)  # 10° -> 39°
    arc = build_arcs("Mars", jds, lons)[0]
    window = solve_contact_window(arc, 39.0, orb_deg=3.0)
    assert window is not None
    assert window.exit_truncated is True
    assert window.entry_truncated is False
    assert window.exit_jd <= arc.end_jd + 1e-9


# ── 4. find_contacts over a whole epoch ───────────────────────────────────────


def test_find_contacts_returns_every_crossing_in_time_order():
    jds, lons = _direct_series(800, 1.0, lon0=0.0)  # 2.2 revolutions
    arcs = build_arcs("Sun", jds, lons)
    events = find_contacts(arcs, target_deg=123.0, orb_deg=1.0)
    assert len(events) == 2, "123° is crossed exactly twice in 799 days at 1°/day"
    assert [e.exact_jd for e in events] == sorted(e.exact_jd for e in events)
    assert events[0].exact_jd == pytest.approx(JD0 + 123.0, abs=1e-3)
    assert events[1].exact_jd == pytest.approx(JD0 + 483.0, abs=1e-3)
    for e in events:
        assert isinstance(e, ContactEvent)
        assert e.body == "Sun"
        assert e.target_deg == 123.0


def test_find_contacts_is_honestly_empty_when_never_reached():
    jds, lons = _direct_series(30, 1.0, lon0=10.0)
    arcs = build_arcs("Mars", jds, lons)
    assert find_contacts(arcs, target_deg=300.0, orb_deg=1.0) == []


def test_find_contacts_counts_retrograde_recrossings_separately():
    """The measured refutation of design §2.3's '1-3x per cycle' multiplier
    (V4, 779,595 events) rests on retro re-crossings being counted as the
    separate contacts they are — not collapsed into one."""
    jds, lons = _retrograde_loop_series()
    arcs = build_arcs("Mercury", jds, lons)
    # Pick a degree inside the retrograde loop's swept band, which the body
    # therefore passes three times (direct, retro, direct).
    # 110 deg sits INSIDE the loop's swept band (the loop turns at ~111.9
    # and ~108.1), so the body passes it three times: direct, retro, direct.
    events = find_contacts(arcs, target_deg=110.0, orb_deg=0.5)
    assert len(events) >= 3, f"expected >=3 re-crossings, got {len(events)}"
    directions = {e.direction for e in events}
    assert directions == {1, -1}


# ── 5. Three-tier materialization (ADJUDICATION-14) ───────────────────────────


def test_tier_a_bodies_are_eager():
    for body in ("Saturn", "Jupiter", "Rahu", "Ketu", "Mars"):
        assert body_tier(body) == TIER_EAGER


def test_tier_b_bodies_are_conditional():
    for body in ("Sun", "Mercury", "Venus"):
        assert body_tier(body) == TIER_CONDITIONAL


def test_moon_is_lazy_only_and_never_eager():
    """ADJUDICATION-14: 'Tier C (Moon) lazy-only, never materialized
    full-span.' The Moon is 76.1% of the measured 779,595 contact events."""
    assert body_tier("Moon") == TIER_LAZY
    policy = materialization_policy("Moon")
    assert policy.eager is False
    assert policy.full_span is False
    assert policy.reason


def test_every_daily_body_has_a_tier():
    bodies = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
              "Saturn", "Rahu", "Ketu")
    for body in bodies:
        assert body_tier(body) in (TIER_EAGER, TIER_CONDITIONAL, TIER_LAZY)


def test_unknown_body_is_an_error_not_a_default_tier():
    """§N.7 item 6 — an honest failure beats a plausible-sounding default."""
    with pytest.raises(KeyError):
        body_tier("Chiron")


# ── 6. Delta-aware invalidation (W2G design amendment 2) ──────────────────────


def test_arc_fingerprint_changes_with_the_substrate_and_not_otherwise():
    base = arc_fingerprint(body="Saturn", epoch_start_jd=JD0, epoch_end_jd=JD0 + 1000,
                           knot_count=1000, engine_version=ARC_ENGINE_VERSION)
    same = arc_fingerprint(body="Saturn", epoch_start_jd=JD0, epoch_end_jd=JD0 + 1000,
                           knot_count=1000, engine_version=ARC_ENGINE_VERSION)
    assert base == same
    other_body = arc_fingerprint(body="Jupiter", epoch_start_jd=JD0, epoch_end_jd=JD0 + 1000,
                                 knot_count=1000, engine_version=ARC_ENGINE_VERSION)
    assert base != other_body
    longer = arc_fingerprint(body="Saturn", epoch_start_jd=JD0, epoch_end_jd=JD0 + 2000,
                             knot_count=2000, engine_version=ARC_ENGINE_VERSION)
    assert base != longer


def test_one_class_grammar_change_invalidates_only_that_class():
    """The exact shape of item 9's real one-class addition: adding or changing
    ONE event_class's grammar must not force every other already-computed
    class to recompute."""
    arcs_fp = {"Saturn": "a" * 16, "Jupiter": "b" * 16}
    before = {
        cls: class_fingerprint(event_class=cls, grammar_version="g1",
                               target_refs=("t1", "t2"), bodies=("Saturn", "Jupiter"),
                               arc_fingerprints=arcs_fp)
        for cls in ("marriage", "career_advancement", "health_adverse")
    }
    after = dict(before)
    after["health_adverse"] = class_fingerprint(
        event_class="health_adverse", grammar_version="g2",
        target_refs=("t1", "t2"), bodies=("Saturn", "Jupiter"),
        arc_fingerprints=arcs_fp,
    )
    changed = {k for k in before if before[k] != after[k]}
    assert changed == {"health_adverse"}


def test_a_substrate_rebuild_invalidates_every_class_that_reads_it():
    """The other direction — delta-awareness must not become blindness."""
    before = class_fingerprint(event_class="marriage", grammar_version="g1",
                               target_refs=("t1",), bodies=("Saturn",),
                               arc_fingerprints={"Saturn": "a" * 16})
    after = class_fingerprint(event_class="marriage", grammar_version="g1",
                              target_refs=("t1",), bodies=("Saturn",),
                              arc_fingerprints={"Saturn": "z" * 16})
    assert before != after


def test_target_set_change_invalidates_the_class():
    before = class_fingerprint(event_class="marriage", grammar_version="g1",
                               target_refs=("t1",), bodies=("Saturn",),
                               arc_fingerprints={"Saturn": "a" * 16})
    after = class_fingerprint(event_class="marriage", grammar_version="g1",
                              target_refs=("t1", "t2"), bodies=("Saturn",),
                              arc_fingerprints={"Saturn": "a" * 16})
    assert before != after


def test_class_fingerprint_is_order_independent_in_its_sets():
    a = class_fingerprint(event_class="marriage", grammar_version="g1",
                          target_refs=("t2", "t1"), bodies=("Jupiter", "Saturn"),
                          arc_fingerprints={"Saturn": "a" * 16, "Jupiter": "b" * 16})
    b = class_fingerprint(event_class="marriage", grammar_version="g1",
                          target_refs=("t1", "t2"), bodies=("Saturn", "Jupiter"),
                          arc_fingerprints={"Jupiter": "b" * 16, "Saturn": "a" * 16})
    assert a == b, "row order out of the database must not change a fingerprint"


# ── 7. THE KEYSTONE: constant query count ─────────────────────────────────────


class _CountingArcSource:
    """An arc source that records every read it is asked to perform."""

    def __init__(self, arcs_by_body: dict[str, list[MonotoneArc]]):
        self._arcs = arcs_by_body
        self.calls: list[tuple[str, ...]] = []

    def load(self, bodies):
        bodies = tuple(bodies)
        self.calls.append(bodies)
        return {b: self._arcs.get(b, []) for b in bodies}


def _solver_fixture(n_bodies: int = 3):
    arcs_by_body = {}
    for i, body in enumerate(("Saturn", "Jupiter", "Mars", "Venus", "Sun")[:n_bodies]):
        jds, lons = _direct_series(800, 0.5 + 0.25 * i, lon0=float(10 * i))
        arcs_by_body[body] = build_arcs(body, jds, lons)
    return arcs_by_body


def test_solver_query_count_is_constant_in_target_count():
    """THE measured design input, encoded as a detector.

    v1 pays ~110-120ms per (target x primitive x window) contact-primitive
    call because each one re-enters the DB. W2G's solver reads the arc
    substrate ONCE and then does pure CPU root-finding, so the read count must
    not move when the target count grows by 40x.
    """
    arcs_by_body = _solver_fixture()
    bodies = tuple(arcs_by_body)

    src_small = _CountingArcSource(arcs_by_body)
    ContactSolver(src_small).solve(bodies=bodies, target_degs=[12.0], orb_deg=1.0)

    src_big = _CountingArcSource(arcs_by_body)
    many = [float(d) for d in range(0, 360, 9)]  # 40 targets
    result = ContactSolver(src_big).solve(bodies=bodies, target_degs=many, orb_deg=1.0)

    assert len(src_small.calls) == 1
    assert len(src_big.calls) == len(src_small.calls), (
        f"read count scaled with targets: {len(src_small.calls)} -> {len(src_big.calls)}"
    )
    assert result, "the 40-target solve must actually find contacts"


def test_solver_query_count_is_constant_in_body_count():
    small = _CountingArcSource(_solver_fixture(1))
    ContactSolver(small).solve(bodies=("Saturn",), target_degs=[12.0], orb_deg=1.0)

    big_fixture = _solver_fixture(5)
    big = _CountingArcSource(big_fixture)
    ContactSolver(big).solve(bodies=tuple(big_fixture), target_degs=[12.0], orb_deg=1.0)

    assert len(small.calls) == len(big.calls) == 1


def test_solver_results_do_not_depend_on_how_many_reads_it_took():
    """Equivalence between the batched solve and per-target solves — the
    optimization must be an optimization, not a semantic change."""
    arcs_by_body = _solver_fixture()
    bodies = tuple(arcs_by_body)
    targets = [30.0, 120.0, 250.0]

    batched = ContactSolver(_CountingArcSource(arcs_by_body)).solve(
        bodies=bodies, target_degs=targets, orb_deg=1.0
    )
    one_at_a_time: list[ContactEvent] = []
    for t in targets:
        one_at_a_time.extend(
            ContactSolver(_CountingArcSource(arcs_by_body)).solve(
                bodies=bodies, target_degs=[t], orb_deg=1.0
            )
        )

    key = lambda e: (e.body, e.target_deg, round(e.exact_jd, 6))  # noqa: E731
    assert sorted(map(key, batched)) == sorted(map(key, one_at_a_time))


def test_solver_honours_the_lazy_tier_by_default():
    """The Moon must not be materialized full-span unless asked for
    explicitly — ADJUDICATION-14 Tier C."""
    jds_m, lons_m = _direct_series(400, 13.0, lon0=0.0)
    jds_s, lons_s = _direct_series(400, 0.03, lon0=0.0)
    arcs_by_body = {
        "Moon": build_arcs("Moon", jds_m, lons_m),
        "Saturn": build_arcs("Saturn", jds_s, lons_s),
    }

    src = _CountingArcSource(arcs_by_body)
    events = ContactSolver(src).solve(
        bodies=("Saturn", "Moon"), target_degs=[5.0], orb_deg=1.0
    )
    assert all(e.body != "Moon" for e in events), (
        "the Moon is Tier C — full-span materialization is forbidden by default"
    )

    src2 = _CountingArcSource(arcs_by_body)
    lazy = ContactSolver(src2).solve(
        bodies=("Moon",), target_degs=[5.0], orb_deg=1.0, include_lazy=True
    )
    assert lazy, "an explicit lazy drill-down must still be able to reach the Moon"
