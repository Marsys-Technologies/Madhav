"""A5.3 interval_sweep (2/N) — record store (record_store.py).

Two tiers:

  * fake-store orchestration tests (no DB): coverage-FIRST ordering, the
    named deferral of point solves (3/N), probe-missing honesty (no spans,
    never fabricated), house_from_frame mandatory on computed rows
    (kgrr_evaluated_has_house_ck — anchor unknown ⇒ not minted, named),
    full-domain ordinals with horizon filtering (R3 amendment 1);
  * disposable-PG tests (GOCHARA_REMAINDER_DSN; NOT_RUN skip when
    unreachable): the real SQL against the applied migration chain
    (1081 + 1152–1157) — coverage row, contact chain, kgrr rows, CHECK
    conformance, and pin-4 idempotent re-run.

The grain under test is P3/marriage's saturn residence in libra (the 7th
signature house from the fixture's aries lagna — enumerate_edges is pure,
so the chart is a dict; no chart_facts needed at this tier).
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.gochara_kernel import evaluator as ev  # noqa: E402
from services.gochara_kernel import record_store as rs  # noqa: E402

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
DAY = timedelta(days=1)
HORIZON = (T0, T0 + 400 * DAY)
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
SKY_CID = "sha256:" + "ab" * 32
PREREQS = [["p4_double_transit", "1.0.0"]]

CHART = {
    "lagna_deg": 12.43,
    "natal": {
        "Sun": 291.96, "Moon": 327.06, "Mars": 198.52, "Mercury": 270.84,
        "Jupiter": 148.87, "Venus": 265.39, "Saturn": 356.74,
        "Rahu": 21.34, "Ketu": 201.34,
    },
}
SIGNS = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
         "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
LIBRA_MID = 195.0
NOT_LIBRA_MID = 15.0


def _libra_edge() -> ev.RecordEdge:
    edges = [e for e in ev.enumerate_edges("marriage", "P3", CHART)
             if e.transit and e.relation == "residence" and e.agent == "saturn"
             and e.obj.canonical_target == "span:libra"]
    assert len(edges) == 1
    return edges[0]


def _house_from_lagna(lagna_deg: float):
    lagna_idx = int(lagna_deg // 30)

    def house_for(edge: ev.RecordEdge, sign: str) -> int:
        return (SIGNS.index(sign.lower()) - lagna_idx) % 12 + 1
    return house_for


def _crossing(day: float, level: float) -> rs.CrossingInfo:
    return rs.CrossingInfo(t=T0 + day * DAY, level_deg=level,
                           solver_method="swiss_refined",
                           delta_lambda=2.0 / 3600.0, delta_t=1e-9,
                           precision_regime="swiss_bisect_tol_1e-9d")


def _probe(ranges: list[tuple[float, float]]):
    """position_at(body, t): LIBRA_MID inside the (day) ranges, NOT_LIBRA_MID
    outside — consistent with the fixture crossings (into libra at 180°, out
    at 210°)."""
    def position_at(body: str, t: datetime) -> float:
        d = (t - T0) / DAY
        return LIBRA_MID if any(a <= d < b for a, b in ranges) else NOT_LIBRA_MID
    return position_at


class FakeStore:
    """Records every call; crossings are injected per body; the stored
    coverage partition is present by default (the coverage substep ran)."""

    def __init__(self, crossings: dict[str, list[rs.CrossingInfo]],
                 coverage_present: bool = True):
        self._crossings = crossings
        self._coverage = coverage_present
        self.calls: list[tuple[str, dict]] = []

    def fetch_crossings(self, body, convention_id):
        self.calls.append(("fetch_crossings", {"body": body}))
        return list(self._crossings.get(body, []))

    def write_coverage(self, **kw):
        self.calls.append(("write_coverage", kw))

    def ensure_bridge(self, kala, sky):
        self.calls.append(("ensure_bridge", {"kala": kala, "sky": sky}))

    def stored_coverage_facts_json(self, *, chart_id, generation, event_class):
        self.calls.append(("stored_coverage_facts_json",
                           {"event_class": event_class}))
        if not self._coverage:
            raise rs.MissingCoverageError(event_class)
        return '{"convention_id": "sha256:kala"}'

    def insert_contact(self, **kw):
        self.calls.append(("insert_contact", kw))

    def insert_point_contact(self, **kw):
        self.calls.append(("insert_point_contact", kw))

    def set_prerequisite_result(self, **kw):
        self.calls.append(("set_prerequisite_result", kw))

    def insert_record(self, **kw):
        self.calls.append(("insert_record", kw))


def _run(store, edges, **over):
    kw = dict(chart_id=CHART_ID, generation="5.0", event_class="marriage",
              path_id="P3", edges=edges, horizon=HORIZON,
              position_at=_probe([(10, 200)]),
              house_for=_house_from_lagna(CHART["lagna_deg"]),
              sky_convention_id=SKY_CID,
              source_fact_ids=["fact-1"], prerequisites=PREREQS)
    kw.update(over)
    return rs.materialise_record_grain(store, **kw)


def _run_coverage(store, class_edges, **over):
    kw = dict(chart_id=CHART_ID, generation="5.0", event_class="marriage",
              class_edges=class_edges, horizon=HORIZON,
              position_at=_probe([(10, 200)]),
              sky_convention_id=SKY_CID, kala_convention_id="sha256:kala",
              build_id="test-build")
    kw.update(over)
    return rs.write_class_coverage(store, **kw)


# ── class coverage substep (fake store) ───────────────────────────────────

def test_class_coverage_names_the_search_and_the_deferrals():
    store = FakeStore({"saturn": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    class_edges = ev.enumerate_edges("marriage", "P3", CHART)
    point_edge = ev.RecordEdge(**{**_libra_edge().__dict__,
                                  "relation": "conjunction"})
    _run_coverage(store, class_edges + [point_edge])
    kinds = [k for k, _ in store.calls]
    assert kinds[0] == "fetch_crossings"   # resolution restatement read
    assert "ensure_bridge" in kinds and kinds.index("ensure_bridge") < kinds.index("write_coverage")
    cov = [kw for k, kw in store.calls if k == "write_coverage"][0]
    assert cov["relations_searched"] == ["residence", "natal_fact"]
    assert cov["resolution"] == pytest.approx(2.0)  # N7 restatement, arcsec
    assert rs.DEFERRAL_POINT_SOLVE in cov["unsearched_reason"]
    # edge-level counts over the FULL class enumeration: the residence +
    # natal edges searched, the conjunction edge unavailable
    residence = [e for e in class_edges if e.transit and e.relation == "residence"]
    natal = [e for e in class_edges if not e.transit]
    assert cov["targets_requested"] == len(class_edges) + 1
    assert cov["targets_resolved"] == len(residence) + len(natal)
    assert cov["state_counts"] == {"resolved": len(residence) + len(natal),
                                   "unavailable": len(class_edges) + 1
                                   - len(residence) - len(natal),
                                   "unqualified": 0}


def test_class_coverage_missing_probe_is_a_named_non_claim():
    store = FakeStore({"saturn": [_crossing(10, 180.0)]})
    _run_coverage(store, [_libra_edge()], position_at=None)
    cov = [kw for k, kw in store.calls if k == "write_coverage"][0]
    assert "position_probe" in cov["unavailable_inputs"]
    assert "resolution" in cov["unavailable_inputs"]  # 0.0 is a non-claim
    assert cov["relations_searched"] == []
    assert cov["targets_resolved"] == 0


# ── record grain (fake store) ─────────────────────────────────────────────

def test_grain_binds_the_stored_class_partition():
    store = FakeStore({"saturn": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    counts = _run(store, [_libra_edge()])
    kinds = [k for k, _ in store.calls]
    assert kinds[0] == "fetch_crossings"
    assert "write_coverage" not in kinds  # the coverage substep owns that row
    assert "stored_coverage_facts_json" in kinds
    assert counts == {"contacts": 1, "records": 1, "natal_records": 0,
                      "truncated_contacts": 0, "prereq_evaluated": 0}
    rec = [kw for k, kw in store.calls if k == "insert_record"][0]
    assert rec["coverage_key"] == "marriage"  # the frozen F7 key convention


def test_grain_without_class_coverage_refuses():
    store = FakeStore({"saturn": [_crossing(10, 180.0)]}, coverage_present=False)
    with pytest.raises(rs.MissingCoverageError):
        _run(store, [_libra_edge()])
    assert not any(k == "insert_record" for k, _ in store.calls)


def test_point_solve_edges_mint_nothing():
    edge = ev.RecordEdge(**{**_libra_edge().__dict__, "relation": "conjunction"})
    store = FakeStore({"saturn": [_crossing(10, 180.0)]})
    counts = _run(store, [edge])
    assert counts["contacts"] == 0 and counts["records"] == 0
    assert not any(k == "insert_contact" for k, _ in store.calls)


def test_missing_probe_derives_nothing():
    store = FakeStore({"saturn": [_crossing(10, 180.0)]})
    counts = _run(store, [_libra_edge()], position_at=None)
    assert counts["contacts"] == 0
    assert not any(k == "insert_contact" for k, _ in store.calls)


def test_unknown_frame_anchor_is_not_minted():
    store = FakeStore({"saturn": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    counts = _run(store, [_libra_edge()], house_for=lambda e, s: None)
    assert counts["records"] == 0
    assert not any(k == "insert_record" for k, _ in store.calls)


def test_full_domain_ordinals_survive_horizon_filtering():
    """Three libra entries across the domain; the horizon keeps only the
    second — its ordinal stays 2 (R3: a clipped partition never renumbers)."""
    crossings = [
        _crossing(-500, 180.0), _crossing(-300, 210.0),    # span 1 (pre-horizon)
        _crossing(10, 180.0), _crossing(200, 210.0),       # span 2 (in horizon)
        _crossing(500, 180.0), _crossing(700, 210.0),      # span 3 (post-horizon)
    ]
    store = FakeStore({"saturn": crossings})
    counts = _run(store, [_libra_edge()],
                  position_at=_probe([(-500, -300), (10, 200), (500, 700)]))
    assert counts["contacts"] == 1
    contact = [kw for k, kw in store.calls if k == "insert_contact"][0]
    assert contact["contact"].occurrence_ordinal == 2
    record = [kw for k, kw in store.calls if k == "insert_record"][0]
    assert record["house_from_frame"] == 7  # libra is the 7th from aries
    assert record["support_state"] == "computed"
    assert record["precision"]["solver_method"] == "swiss_refined"


def test_natal_fact_mints_uncomputed_with_null_contact():
    natal = [e for e in ev.enumerate_edges("marriage", "P3", CHART)
             if not e.transit]
    assert len(natal) == 2  # P3 marriage: lord + occupant natal facts
    store = FakeStore({})
    counts = _run(store, natal)
    assert counts["natal_records"] == 2
    rec = [kw for k, kw in store.calls if k == "insert_record"][0]
    assert rec["contact_id"] is None and rec["precision"] is None
    assert rec["support_state"] == "uncomputed"
    assert rec["support_intervals"] == []


# ── disposable PG (real SQL; NOT_RUN when unreachable) ────────────────────

DSN = os.environ.get("GOCHARA_A53_DSN",
                     "postgresql://wp6:local@localhost:55434/a53")
MIGRATIONS = Path(__file__).resolve().parents[4] / "migrations"
MIGRATION_CHAIN = [
    "1081_nirmana_l3_gochara_ledger_coverage_publication.sql",
    "1152_kala_gochara_contacts_t_exact_nullable_truncated.sql",
    "1153_gochara_sky_event_substrate.sql",
    "1154_gochara_rule_path_registry.sql",
    "1155_gochara_relationship_record.sql",
    "1156_gochara_eval_window.sql",
    "1157_gochara_av_polarity_declaration.sql",
]


@pytest.fixture()
def pg():
    """The disposable remainder DB with the gochara-5 migration chain applied
    verbatim (idempotent: the _migrations_applied ledger stub gates re-run).
    No cleanup of the insert-only tables — every identity is deterministic,
    so a re-run is exactly the idempotency the writer guarantees."""
    psycopg = pytest.importorskip("psycopg")
    try:
        conn = psycopg.connect(DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable remainder database unreachable ({exc})")
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS public.charts (id uuid PRIMARY KEY)")
        cur.execute(
            "CREATE TABLE IF NOT EXISTS public._migrations_applied"
            " (filename text PRIMARY KEY, applied_at timestamptz DEFAULT now())")
        for name in MIGRATION_CHAIN:
            prefix = name.split("_", 1)[0] + "_"
            applied = cur.execute(
                "SELECT 1 FROM public._migrations_applied"
                " WHERE starts_with(filename, %s) LIMIT 1", (prefix,),
            ).fetchone()
            if not applied:
                # the ledger stub may be younger than an earlier rehearsal —
                # probe a marker object before re-applying (1152 is NOT
                # re-runnable: ADD CONSTRAINT without IF NOT EXISTS)
                marker = {
                    "1081": "SELECT to_regclass('public.kala_gochara_coverage')",
                    "1152": "SELECT conname FROM pg_constraint"
                            " WHERE conname = 'kgc_t_exact_iff_exact_crossing'",
                }.get(prefix.rstrip("_"))
                if marker is not None:
                    applied = cur.execute(marker).fetchone()
                    if applied and applied[0]:
                        cur.execute(
                            "INSERT INTO public._migrations_applied(filename)"
                            " VALUES (%s) ON CONFLICT DO NOTHING", (name,))
                        continue
                    applied = None
            if applied:
                continue
            cur.execute((MIGRATIONS / name).read_text())
            cur.execute(
                "INSERT INTO public._migrations_applied(filename) VALUES (%s)"
                " ON CONFLICT DO NOTHING", (name,))
        cur.execute("INSERT INTO public.charts(id) VALUES (%s)"
                    " ON CONFLICT DO NOTHING", (CHART_ID,))
    yield conn
    conn.close()


def _seed_saturn_crossings(conn, sky_cid: str):
    """Two sign_ingress sky events for Saturn under the real substrate
    convention: into libra (180°) on day 10, out to scorpio (210°) on day 200."""
    _seed_libra_crossings(conn, sky_cid, "Saturn")


def _seed_libra_crossings(conn, sky_cid: str, body: str):
    """Libra residence [day 10, day 200) for `body` as two sign_ingress sky
    events (insert-if-absent; deterministic identities)."""
    from services.gochara_kernel.substrate import (SkyEventStore,
                                                   assign_occurrence_ordinals,
                                                   physical_object_id)
    store = SkyEventStore(conn)
    for level, day in ((180.0, 10), (210.0, 200)):
        poid = physical_object_id(
            body=body, relation_kind="sign_ingress",
            canonical_target=f"point:{level!r}", convention_id=sky_cid)
        store.insert_physical_object(poid)
        (contact,) = assign_occurrence_ordinals(
            physical_object_id=poid, t_exact_list=[T0 + day * DAY])
        store.insert_event(
            contact, event_kind="sign_ingress", longitude=level,
            solver_method="swiss_refined", delta_lambda=2.0 / 3600.0,
            delta_t=1e-9, precision_regime="swiss_bisect_tol_1e-9d",
            coverage={"truncated": False})


def _grain_kwargs(store, sky_cid):
    return dict(chart_id=CHART_ID, generation="5.0", event_class="marriage",
                path_id="P3", edges=[_libra_edge()], horizon=HORIZON,
                position_at=_probe([(10, 200)]),
                house_for=_house_from_lagna(CHART["lagna_deg"]),
                sky_convention_id=sky_cid,
                source_fact_ids=["fact-1"])
    # prerequisites None ⇒ the grain reads the path's DECLARED membership
    # from the seeded registry (F5)


def _coverage_kwargs(store, kala_cid, sky_cid):
    return dict(chart_id=CHART_ID, generation="5.0", event_class="marriage",
                class_edges=ev.enumerate_edges("marriage", "P3", CHART),
                horizon=HORIZON, position_at=_probe([(10, 200)]),
                sky_convention_id=sky_cid, kala_convention_id=kala_cid,
                build_id="test-build-pg", arc_index_available=True)


def _sky_convention_id(conn) -> str:
    """Register the real substrate convention (pin 3, idempotent under the
    caller's chart lock) and return its id."""
    from services.gochara_kernel.substrate import SkyEventStore
    return SkyEventStore(conn).register_convention()


def test_grain_end_to_end_on_disposable_pg(pg):
    conn = pg
    # rule catalogue first (its own grain; the registry write guards take
    # the global family key themselves — never mixed with the chart key)
    from services.gochara_kernel.rule_registry import RuleRegistryStore
    RuleRegistryStore(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        _seed_saturn_crossings(conn, sky_cid)
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(store, **_coverage_kwargs(store, kala_cid, sky_cid))
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(store, **_grain_kwargs(store, sky_cid))
    assert counts == {"contacts": 1, "records": 1, "natal_records": 0,
                      "truncated_contacts": 0, "prereq_evaluated": 0}
    row = conn.execute(
        "SELECT temporal_support_state, temporal_support_grain,"
        " house_from_frame, admission_state, outcome_valence_for_native"
        " FROM public.ka_gochara_relationship_record"
        " WHERE generation = '5.0'").fetchone()
    assert row == ("computed", "span", 7, "unqualified", "unqualified")
    contact = conn.execute(
        "SELECT solver_method, coverage->>'truncated', t_exact IS NOT NULL"
        " FROM public.ka_gochara_contact WHERE generation = '5.0'").fetchone()
    assert contact == ("swiss_refined", "false", True)
    cov = conn.execute(
        "SELECT partition_key, relations_searched, targets_resolved"
        " FROM public.kala_gochara_coverage"
        " WHERE generation = '5.0' AND partition_kind = 'event_class'").fetchone()
    # 3/N: with the arc index available the class coverage names the point
    # solves as searched — every one of the 34 P3 edges is resolved
    assert cov == ("marriage", ["residence", "aspect", "conjunction",
                                "natal_fact"], 34)


def test_grain_rerun_is_idempotent(pg):
    conn = pg
    from services.gochara_kernel.rule_registry import RuleRegistryStore
    RuleRegistryStore(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        _seed_saturn_crossings(conn, sky_cid)
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(store, **_coverage_kwargs(store, kala_cid, sky_cid))
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        first = rs.materialise_record_grain(store, **_grain_kwargs(store, sky_cid))
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        second = rs.materialise_record_grain(store, **_grain_kwargs(store, sky_cid))
    assert first == second
    n = conn.execute(
        "SELECT count(*) FROM public.ka_gochara_relationship_record"
        # scoped to this grain's relation — the shared disposable DB also
        # carries the point-solve PG test's rows
        " WHERE generation = '5.0' AND relation = 'residence'").fetchone()
    assert n[0] == first["records"]


# ── 3/N: point solves (conjunction/aspect on point:<λ>) ─────────────────────
#
# Synthetic arc indexes (linear/piecewise curves reproduced exactly by the
# cubic, refine=False — the spline-stage root IS the exact root) drive the
# REAL solve_point_edges + grain; one disposable-PG test refines against
# checksum-pinned Swiss for the full CHECK chain.

J0 = T0.timestamp() / 86400.0 + 2440587.5


def _index(body, curve, lo=-200, hi=800):
    from services.gochara_kernel import arcs as gk_arcs
    jds = [float(J0 + i) for i in range(lo, hi)]
    lons = [curve(jd) % 360.0 for jd in jds]
    return gk_arcs.build_arc_index(body, jds, lons, tolerance_arcsec=1e-7)


def _point_edge(relation="conjunction", lam=200.0, agent="sun"):
    from services.gochara_kernel.substrate import PhysicalObjectId
    edges = [e for e in ev.enumerate_edges("marriage", "P3", CHART)
             if e.transit and e.relation == relation and e.agent == agent]
    assert edges, f"no {relation} edge for {agent} in marriage/P3"
    e = edges[0]
    obj = PhysicalObjectId(
        body=agent, relation_kind=relation,
        canonical_target=f"point:{float(lam)!r}",
        convention_id=e.obj.convention_id)
    return ev.RecordEdge(**{**e.__dict__, "obj": obj})


def test_point_conjunction_solved_and_minted_full_chain():
    edge = _point_edge("conjunction", 200.0, "sun")
    # Sun at 100° at T0, +1°/day → crosses 200° at T0+100d; in-orb ±1°.
    idx = _index("Sun", lambda jd: (jd - J0) + 100.0)
    store = FakeStore({})
    counts = _run(store, [edge], arc_index_for=lambda b: idx, refine=False)
    assert counts["contacts"] == 1 and counts["records"] == 1
    (occ,) = [kw["occ"] for k, kw in store.calls if k == "insert_point_contact"]
    assert occ.contact.occurrence_ordinal == 1
    assert abs((occ.t_exact - (T0 + 100 * DAY)).total_seconds()) < 120
    assert abs((occ.t_in - (T0 + 99 * DAY)).total_seconds()) < 120
    assert abs((occ.t_out - (T0 + 101 * DAY)).total_seconds()) < 120
    assert occ.truncated is False and occ.solver_method == "arc_index_bracket"
    rec = [kw for k, kw in store.calls if k == "insert_record"][0]
    assert rec["contact_id"] == str(occ.contact.contact_id)
    assert rec["support_state"] == "computed"
    assert rec["support_intervals"][0].startswith("[")
    assert rec["house_from_frame"] == 7


def test_point_aspect_levels_are_target_minus_angle():
    """Aspect direction (the A2.1 O-AD rule) at the record layer: Mars's
    aspects on a 0° target occur with the body at (target − angle) —
    270°/180°/150° for the 4th/7th/8th — never the mirrored level."""
    edge = _point_edge("aspect", 0.0, "mars")
    idx = _index("Mars", lambda jd: (jd - J0) * 0.5, lo=0, hi=700)  # < 1 revolution
    occs = rs.solve_point_edges(
        [edge], arc_index_for=lambda b: idx,
        horizon=(T0, T0 + 650 * DAY), refine=False)[id(edge)]
    exacts = sorted(o.t_exact for o in occs)
    expect = [T0 + 300 * DAY, T0 + 360 * DAY, T0 + 540 * DAY]  # 150/180/270°
    assert len(exacts) == 3
    for got, want in zip(exacts, expect):
        assert abs((got - want).total_seconds()) < 240
    assert [o.contact.occurrence_ordinal for o in
            sorted(occs, key=lambda o: o.t_exact)] == [1, 2, 3]
    # mutation detector: mirrored levels (target + angle: 90°/210°→ at
    # +180d/+420d) carry NO occurrence
    for bad in (T0 + 180 * DAY, T0 + 420 * DAY):
        assert all(abs((t - bad).total_seconds()) > 3600 for t in exacts)


def test_point_retrograde_recrossing_ordinals():
    """O-RX-1 at the writer: a direct pass, a retrograde re-crossing and the
    re-return are ordinals 1, 2, 3 of ONE physical object."""
    edge = _point_edge("conjunction", 200.0, "jupiter")

    def curve(jd):
        d = jd - J0
        if d <= 210:
            return d
        if d <= 225:
            return 210.0 - (d - 210)
        return 195.0 + (d - 225)

    idx = _index("Jupiter", curve, lo=0)
    occs = rs.solve_point_edges(
        [edge], arc_index_for=lambda b: idx, horizon=HORIZON,
        refine=False)[id(edge)]
    assert len(occs) == 3
    ordered = sorted(occs, key=lambda o: o.t_exact)
    assert [o.contact.occurrence_ordinal for o in ordered] == [1, 2, 3]
    assert len({o.contact.physical_object_id for o in occs}) == 1
    for occ, day in zip(ordered, (200, 220, 230)):
        assert abs((occ.t_exact - (T0 + day * DAY)).total_seconds()) < 240
    # distinct contact ids, one object (NK-2)
    assert len({str(o.contact.contact_id) for o in occs}) == 3


def test_point_exact_beyond_horizon_end_kept_truncated():
    """N3/Tier-0-G at a point contact: exact centre 0.5d beyond the horizon
    end, in-orb interval overlapping → the truncated span is KEPT (t_exact
    NULL, clipped_truncated, t_out = the horizon end); a contact touching
    only the excluded end instant itself is NOT one."""
    edge = _point_edge("conjunction", 200.0, "venus")
    idx = _index("Venus", lambda jd: (jd - J0) - 200.5, hi=700)
    occs = rs.solve_point_edges(
        [edge], arc_index_for=lambda b: idx, horizon=HORIZON,
        refine=False)[id(edge)]
    # the body also crosses 200° (mod 360) at +40.5d — that one is exact
    assert len(occs) == 2
    first, occ = sorted(occs, key=lambda o: o.t_in)
    assert first.t_exact is not None and first.contact.occurrence_ordinal == 1
    assert occ.t_exact is None and occ.truncated is True
    assert occ.contact.occurrence_ordinal == 2
    assert occ.solver_method == "clipped_truncated"
    assert occ.t_out == HORIZON[1]
    assert abs((occ.t_in - (T0 + 399.5 * DAY)).total_seconds()) < 240
    assert occ.delta_lambda is None and occ.delta_t is None

    # control: exact at T0+401d on a no-wrap index → in-orb [400, 402]
    # touches only the excluded end → no occurrence at all
    idx2 = _index("Venus", lambda jd: (jd - J0) - 201.0, lo=300, hi=500)
    edge2 = _point_edge("conjunction", 200.0, "venus")
    occs2 = rs.solve_point_edges(
        [edge2], arc_index_for=lambda b: idx2, horizon=HORIZON,
        refine=False)
    assert occs2 == {}


def test_point_edges_unsolved_without_arc_index():
    edge = _point_edge("conjunction", 200.0, "sun")
    store = FakeStore({})
    counts = _run(store, [edge], arc_index_for=None)
    assert counts["contacts"] == 0 and counts["records"] == 0
    assert not any(k == "insert_point_contact" for k, _ in store.calls)


def test_class_coverage_point_solves_searched_with_arc_index():
    store = FakeStore({})
    class_edges = ev.enumerate_edges("marriage", "P3", CHART)
    assert any(e.transit and e.relation in rs.POINT_KERNEL_RELATION
               for e in class_edges)
    _run_coverage(store, class_edges, arc_index_available=True)
    cov = [kw for k, kw in store.calls if k == "write_coverage"][0]
    assert "conjunction" in cov["relations_searched"]
    assert "aspect" in cov["relations_searched"]
    assert rs.DEFERRAL_POINT_SOLVE not in (cov["unsearched_reason"] or "")
    assert cov["resolution"] >= rs.POINT_SOLVE_INDEX_TOLERANCE_ARCSEC


# ── disposable PG: the real SQL chain with a Swiss-refined solve ────────────

def test_point_grain_end_to_end_on_disposable_pg(pg):
    conn = pg
    from tests.l3.gochara import conftest as _c
    if _c._PROBLEMS:
        pytest.skip(f"NOT_RUN: .se1 ephemeris files: {_c._PROBLEMS}")
    from services.gochara_kernel import arcs as gk_arcs
    from services.gochara_kernel.knots import sample_knots
    from services.gochara_kernel.substrate import (SUBSTRATE_DOMAIN_END,
                                                   SUBSTRATE_DOMAIN_START)
    edge = _point_edge("conjunction", 200.0, "sun")
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    kw = _coverage_kwargs(store, kala_cid, sky_cid)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(store, **kw)

    ks = sample_knots("Sun", SUBSTRATE_DOMAIN_START.date(),
                      SUBSTRATE_DOMAIN_END.date(), _c.EPHE_PATH)
    idx = gk_arcs.build_arc_index("Sun", ks.knot_jds, ks.longitudes_deg)
    gkw = _grain_kwargs(store, sky_cid)
    gkw.update(edges=[edge], arc_index_for=lambda b: idx,
               ephe_path=_c.EPHE_PATH, refine=True)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(store, **gkw)
    assert counts["contacts"] >= 1 and counts["records"] == counts["contacts"]
    rows = conn.execute(
        "SELECT occurrence_ordinal, t_in, t_out, t_exact, solver_method,"
        " delta_lambda, delta_t, precision_regime, coverage"
        " FROM public.ka_gochara_contact"
        " WHERE generation = '5.0' AND relation_kind = 'conjunction'"
        " ORDER BY occurrence_ordinal").fetchall()
    assert len(rows) == counts["contacts"]
    for ordinal, t_in, t_out, t_exact, solver, dl, dt, regime, cov in rows:
        assert solver == "swiss_refined" and cov["truncated"] is False
        assert t_in < t_exact < t_out          # kgc_time_order/span_order
        assert dl is not None and dt is not None and regime
        assert HORIZON[0] <= t_exact < HORIZON[1]
    recs = conn.execute(
        "SELECT contact_id, house_from_frame, temporal_support_state,"
        " temporal_support_intervals FROM public.ka_gochara_relationship_record"
        " WHERE generation = '5.0' AND relation = 'conjunction'").fetchall()
    assert len(recs) == counts["contacts"]
    assert all(r[1] == 7 and r[2] == "computed" and r[3] for r in recs)
    # R3: ordinals are FULL-DOMAIN — the Sun crosses 200° once a year from
    # the 1998-01-01 domain start, so the single in-horizon (2026)
    # occurrence is ordinal 29, never renumbered to 1 by the horizon filter
    assert [r[0] for r in rows] == [29]
    # pin-4 idempotent rerun: same identities, byte checks pass, no dupes
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts2 = rs.materialise_record_grain(store, **gkw)
    assert counts2 == counts
    n = conn.execute(
        "SELECT count(*) FROM public.ka_gochara_contact"
        " WHERE generation = '5.0' AND relation_kind = 'conjunction'"
    ).fetchone()[0]
    assert n == counts["contacts"]


# ── 3/N part 3: prerequisite result evaluation (design v1.0 item 5) ─────────
#
# period_running_at (P1, per occurrence against the §4.0 vimshottari rows)
# and p4_double_transit (P4, Jupiter/Saturn support overlap) are evaluated at
# materialisation through the 1155 result_only UPDATE path; everything else
# stays NULL (not evaluated ⇒ unknown ⇒ unqualified at COMMIT, F5).

P1_PREREQS = [["period_running_at", "1.0.0"],
              ["natal_bhava_relationship", "1.0.0"],
              ["transit_relation", "1.0.0"]]
P4_PREREQS = [["p4_double_transit", "1.0.0"]]


def _p1_libra_edge(agent: str) -> ev.RecordEdge:
    edges = [e for e in ev.enumerate_edges("marriage", "P1", CHART)
             if e.transit and e.relation == "residence" and e.agent == agent
             and e.obj.canonical_target == "span:libra"]
    assert len(edges) == 1
    return edges[0]


def _p4_libra_edge(agent: str) -> ev.RecordEdge:
    edges = [e for e in ev.enumerate_edges("marriage", "P4", CHART)
             if e.transit and e.relation == "residence" and e.agent == agent
             and e.obj.canonical_target == "span:libra"]
    assert len(edges) == 1
    return edges[0]


def _p1_kwargs(store, edges, rows_by_agent):
    return dict(chart_id=CHART_ID, generation="5.0", event_class="marriage",
                path_id="P1", edges=edges, horizon=HORIZON,
                position_at=_probe([(10, 200)]),
                house_for=_house_from_lagna(CHART["lagna_deg"]),
                sky_convention_id=SKY_CID, source_fact_ids=["fact-1"],
                prerequisites=P1_PREREQS,
                dasha_rows_for=lambda agent: rows_by_agent.get(agent, []))


def test_p1_period_running_at_true_false_unknown():
    edges = [_p1_libra_edge(a) for a in ("saturn", "jupiter", "venus")]
    crossings = {a: [_crossing(10, 180.0), _crossing(200, 210.0)]
                 for a in ("saturn", "jupiter", "venus")}
    store = FakeStore(crossings)
    counts = rs.materialise_record_grain(store, **_p1_kwargs(
        store, edges,
        {"saturn": [{"start_iso": T0, "end_iso": T0 + 300 * DAY}],      # running at the ingress
         "jupiter": [{"start_iso": T0 + 500 * DAY, "end_iso": T0 + 600 * DAY}],  # not running
         "venus": []}))                                                 # no L1 rows → unknown
    assert counts["records"] == 3 and counts["prereq_evaluated"] == 3
    calls = [kw for k, kw in store.calls if k == "set_prerequisite_result"]
    assert len(calls) == 3
    by_predicate = {c["predicate_id"] for c in calls}
    assert by_predicate == {"period_running_at"}  # the named scope only
    results = sorted(c["result"] for c in calls)
    assert results == ["false", "true", "unknown"]
    # ordinal 1 = period_running_at in the declared membership
    assert all(c["ordinal"] == 1 for c in calls)


def test_p1_period_running_at_domain_start_truncated_uses_observed_span_start():
    """Spans are derived over the FULL substrate domain (R3), so the only
    truncated span (t_exact None) is one already in the sign at the domain
    start: it has no observed ingress, so the occurrence instant is the
    observed span start (flagged v1.5 binding). Dasha row covering that start
    ⇒ true; a row that does not ⇒ false (never silently the exact-less 'unknown'
    — rows exist, the question is answerable)."""
    edge = _p1_libra_edge("saturn")
    domain_start_rel_days = (rs.SUBSTRATE_DOMAIN_START - T0) / DAY   # negative

    def run(row):
        store = FakeStore({"saturn": [_crossing(200, 210.0)]})   # only the EXIT
        kw = _p1_kwargs(store, [edge], {"saturn": [row]})
        kw["position_at"] = _probe([(domain_start_rel_days - 1, 200)])
        counts = rs.materialise_record_grain(store, **kw)
        calls = [c for k, c in store.calls if k == "set_prerequisite_result"]
        return counts, [c["result"] for c in calls]

    covers = {"start_iso": rs.SUBSTRATE_DOMAIN_START - 10 * DAY,
              "end_iso": rs.SUBSTRATE_DOMAIN_START + 10 * DAY}
    misses = {"start_iso": T0 - 10 * DAY, "end_iso": T0 + 10 * DAY}
    counts, results = run(covers)
    assert counts["records"] == 1 and counts["truncated_contacts"] == 1
    assert results == ["true"]
    counts, results = run(misses)
    assert counts["truncated_contacts"] == 1 and results == ["false"]


def test_p1_period_running_at_ingress_before_horizon_uses_the_exact_ingress():
    """An ingress BEFORE the horizon is not truncated under the full-domain
    derivation: its exact instant is known, and period_running_at is judged at
    THAT instant — not at the clipped horizon start."""
    edge = _p1_libra_edge("saturn")
    store = FakeStore({"saturn": [_crossing(-500, 180.0),
                                  _crossing(200, 210.0)]})
    kw = _p1_kwargs(
        store, [edge],
        # running at the horizon start, NOT at the ingress 500 d earlier
        {"saturn": [{"start_iso": T0 - 10 * DAY, "end_iso": T0 + 10 * DAY}]})
    kw["position_at"] = _probe([(-500, 200)])
    counts = rs.materialise_record_grain(store, **kw)
    assert counts["records"] == 1 and counts["truncated_contacts"] == 0
    calls = [c for k, c in store.calls if k == "set_prerequisite_result"]
    assert [c["result"] for c in calls] == ["false"]


def test_p1_no_dasha_reader_no_evaluation():
    store = FakeStore({"saturn": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    kw = _p1_kwargs(store, [_p1_libra_edge("saturn")], {})
    kw["dasha_rows_for"] = None
    counts = rs.materialise_record_grain(store, **kw)
    assert counts["records"] == 1 and counts["prereq_evaluated"] == 0
    assert not any(k == "set_prerequisite_result" for k, _ in store.calls)


def test_p4_double_transit_overlap_true_and_false():
    jup, sat = _p4_libra_edge("jupiter"), _p4_libra_edge("saturn")

    def run(saturn_crossings):
        store = FakeStore({
            "jupiter": [_crossing(10, 180.0), _crossing(200, 210.0)],
            "saturn": saturn_crossings})
        return store, rs.materialise_record_grain(
            store, chart_id=CHART_ID, generation="5.0",
            event_class="marriage", path_id="P4", edges=[jup, sat],
            horizon=HORIZON, position_at=_probe([(10, 200), (100, 300),
                                                 (500, 700)]),
            house_for=_house_from_lagna(CHART["lagna_deg"]),
            sky_convention_id=SKY_CID, source_fact_ids=["fact-1"],
            prerequisites=P4_PREREQS)

    # overlapping: jupiter in libra [10,200), saturn [100,300) → both true
    store, counts = run([_crossing(100, 180.0), _crossing(300, 210.0)])
    assert counts["records"] == 2 and counts["prereq_evaluated"] == 2
    calls = [kw for k, kw in store.calls if k == "set_prerequisite_result"]
    assert sorted(c["result"] for c in calls) == ["true", "true"]

    # non-overlapping: saturn's libra residence [500,700) is entirely
    # outside the horizon (minted nothing) — jupiter's record: the other
    # planet WAS searched, no overlap ⇒ false (never unknown)
    store, counts = run([_crossing(500, 180.0), _crossing(700, 210.0)])
    assert counts["records"] == 1 and counts["prereq_evaluated"] == 1
    calls = [kw for k, kw in store.calls if k == "set_prerequisite_result"]
    assert [c["result"] for c in calls] == ["false"]


# ── 3/N part 3b: the prerequisite results through the REAL F5 finalisation ──
#
# The fake-store tests above prove the evaluation's values; only the real DB
# proves the COMMIT-time F5 check (1155): a record's admission_state must equal
# the state derived from its prerequisite results (any false ⇒ not_admitted;
# else any unknown/unevaluated ⇒ unqualified; else admitted). Own generation
# ('5.1') so these rows never mix into the '5.0' rows the tests above select.

PG_GEN = "5.1"


def _pg_p1_run(conn, dasha_rows):
    """Seed + coverage + ONE committed P1 grain (Saturn through Libra, ingress
    day 10) with the given L1 dasha rows. Returns (counts, committed_records)."""
    from services.gochara_kernel.rule_registry import RuleRegistryStore
    RuleRegistryStore(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        _seed_saturn_crossings(conn, sky_cid)
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    edge = _p1_libra_edge("saturn")
    probe = _probe([(10, 200)])
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(
            store, chart_id=CHART_ID, generation=PG_GEN, event_class="marriage",
            class_edges=ev.enumerate_edges("marriage", "P1", CHART),
            horizon=HORIZON, position_at=probe, sky_convention_id=sky_cid,
            kala_convention_id=kala_cid, build_id="test-build-pg",
            arc_index_available=False)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(
            store, chart_id=CHART_ID, generation=PG_GEN, event_class="marriage",
            path_id="P1", edges=[edge], horizon=HORIZON, position_at=probe,
            house_for=_house_from_lagna(CHART["lagna_deg"]),
            sky_convention_id=sky_cid, source_fact_ids=["fact-1"],
            dasha_rows_for=lambda agent: dasha_rows.get(agent, []))
    rows = conn.execute(
        "SELECT r.admission_state, p.predicate_id, p.result"
        " FROM public.ka_gochara_relationship_record r"
        " JOIN public.ka_gochara_record_prerequisite p USING (record_id)"
        " WHERE r.generation = %s AND r.path_id = 'P1' ORDER BY p.ordinal",
        (PG_GEN,)).fetchall()
    return counts, rows


@pytest.mark.parametrize("dasha_rows,expect_state,expect_result", [
    # period not running at the ingress (day 10) ⇒ a false prerequisite ⇒ not_admitted
    ({"saturn": [{"start_iso": T0 + 500 * DAY, "end_iso": T0 + 600 * DAY}]},
     "not_admitted", "false"),
    # running ⇒ true, but the other declared prerequisites stay unevaluated ⇒ unqualified
    ({"saturn": [{"start_iso": T0, "end_iso": T0 + 300 * DAY}]},
     "unqualified", "true"),
    # no L1 rows ⇒ unknown, never false ⇒ unqualified
    ({}, "unqualified", "unknown"),
])
def test_p1_prerequisite_results_survive_the_real_f5_finalisation(
        pg, dasha_rows, expect_state, expect_result):
    counts, rows = _pg_p1_run(pg, dasha_rows)    # raises at COMMIT if F5 disagrees
    assert counts["records"] == 1 and counts["prereq_evaluated"] == 1
    assert {r[0] for r in rows} == {expect_state}
    by_pred = {r[1]: r[2] for r in rows}
    assert by_pred["period_running_at"] == expect_result


PG_GEN_P4 = "5.2"


def _pg_p4_run(conn, agents):
    """ONE committed P4 grain over the Libra-residence edges of `agents`
    (each in Libra [day 10, day 200)); returns the committed
    (admission_state, predicate_id, result) rows."""
    from services.gochara_kernel.rule_registry import RuleRegistryStore
    RuleRegistryStore(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        for a in ("Saturn", "Jupiter"):
            _seed_libra_crossings(conn, sky_cid, a)
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    edges = [_p4_libra_edge(a) for a in agents]
    probe = _probe([(10, 200)])
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(
            store, chart_id=CHART_ID, generation=PG_GEN_P4, event_class="marriage",
            class_edges=ev.enumerate_edges("marriage", "P4", CHART),
            horizon=HORIZON, position_at=probe, sky_convention_id=sky_cid,
            kala_convention_id=kala_cid, build_id="test-build-pg",
            arc_index_available=False)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(
            store, chart_id=CHART_ID, generation=PG_GEN_P4, event_class="marriage",
            path_id="P4", edges=edges, horizon=HORIZON, position_at=probe,
            house_for=_house_from_lagna(CHART["lagna_deg"]),
            sky_convention_id=sky_cid, source_fact_ids=["fact-1"])
    rows = conn.execute(
        "SELECT r.agent, r.admission_state, p.predicate_id, p.result"
        " FROM public.ka_gochara_relationship_record r"
        " JOIN public.ka_gochara_record_prerequisite p USING (record_id)"
        " WHERE r.generation = %s AND r.path_id = 'P4' ORDER BY r.agent",
        (PG_GEN_P4,)).fetchall()
    return counts, rows


def test_p4_double_transit_true_is_admitted_through_the_real_f5_finalisation(pg):
    counts, rows = _pg_p4_run(pg, ["jupiter", "saturn"])
    assert counts["records"] == 2 and counts["prereq_evaluated"] == 2
    # P4's ONLY prerequisite is p4_double_transit: overlap ⇒ true ⇒ all results
    # true ⇒ the one place a record legitimately reaches 'admitted'
    assert rows == [("jupiter", "admitted", "p4_double_transit", "true"),
                    ("saturn", "admitted", "p4_double_transit", "true")]


def test_p4_other_planet_not_searched_is_unknown_and_unqualified(pg):
    counts, rows = _pg_p4_run(pg, ["saturn"])        # Jupiter's edge not in the grain
    assert counts["records"] == 1
    assert [(r[1], r[3]) for r in rows if r[0] == "saturn"] == [("unqualified", "unknown")]
