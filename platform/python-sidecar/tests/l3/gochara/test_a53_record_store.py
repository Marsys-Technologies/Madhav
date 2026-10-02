"""A5.3 interval_sweep (2/N) — record store (record_store.py).

Two tiers:

  * fake-store orchestration tests (no DB): coverage-FIRST ordering, the
    named deferral of point solves (3/N), probe-missing honesty (no spans,
    never fabricated), house_from_frame mandatory on computed rows
    (kgrr_evaluated_has_house_ck — anchor unknown ⇒ not minted, named),
    full-domain ordinals with horizon filtering (R3 amendment 1);
  * disposable-PG tests (their own throwaway database; NOT_RUN skip when
    the server is unreachable): the real SQL against the applied migration chain
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
PATH_PREREQS = {
    "P1": [["period_running_at", "1.0.0"], ["natal_bhava_relationship", "1.0.0"],
           ["transit_relation", "1.0.0"]],
    "P2": [["house_from_moon", "1.0.0"]],
    "P3": [["p3_contact_house_or_lord", "1.0.0"]],
    "P4": [["p4_double_transit", "1.0.0"]],
}
PREREQS = PATH_PREREQS["P3"]

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
             and e.obj.canonical_target == "span:7"]
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

    def ensure_object(self, poid):
        self.calls.append(("ensure_object", {"poid": poid}))

    def insert_record(self, **kw):
        self.calls.append(("insert_record", kw))

    def stored_contact_keys(self, *, chart_id, generation):
        keys = set()
        for kind, kw in self.calls:
            if kind in ("insert_contact", "insert_point_contact"):
                poid = kw["poid"]
                keys.add((poid.body, poid.relation_kind, str(poid.uuid)))
        return keys

    def delete_record_grain(self, **kw):
        self.calls.append(("delete_record_grain", kw))
        return {"windows": 0, "records": 0, "contacts": 0}


def _run(store, edges, **over):
    kw = dict(chart_id=CHART_ID, generation="5.0", event_class="marriage",
              path_id="P3", edges=edges, horizon=HORIZON,
              position_at=_probe([(10, 200)]),
              house_for=_house_from_lagna(CHART["lagna_deg"]),
              sky_convention_id=SKY_CID,
              source_fact_ids=["fact-1"], chart=CHART)
    kw.update(over)
    kw.setdefault("prerequisites", PATH_PREREQS[kw["path_id"]])
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
    # AM-4: the Moon is an EPHEMERAL tier — Moon-agent edges are not part of the stored class search
    class_edges = [e for e in class_edges if not (e.transit and e.agent == "moon")]
    residence = [e for e in class_edges if e.transit and e.relation == "residence"]
    natal = [e for e in class_edges if not e.transit]
    assert cov["targets_requested"] == len(class_edges) + 1
    assert cov["targets_resolved"] == len(residence) + len(natal)
    assert cov["state_counts"] == {"resolved": len(residence) + len(natal),
                                   "unavailable": len(class_edges) + 1
                                   - len(residence) - len(natal),
                                   "unqualified": 0}
    assert "aspect-to-span" in cov["unsearched_reason"] and "Moon-agent" in cov["unsearched_reason"]


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
                      "truncated_contacts": 0, "prereq_evaluated": 1,
                      "skipped_natal_p1": 0, "unwritable_testimony": 0,
                      "aspect_span_deferred": 0, "moon_agent_on_demand": 0,
                      "p3_enumeration_defects": 0}
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

# The database tests create their OWN throwaway database on the disposable
# server and drop it afterwards — they never touch a shared scratch database
# (a shared one carried stale rows across convention corrections: the AM-1
# 13d20m fix collided with the old convention's immutable bridge row).
# GOCHARA_A53_ADMIN_DSN names the server's maintenance database; NOT_RUN skip
# when unreachable.
ADMIN_DSN = os.environ.get("GOCHARA_A53_ADMIN_DSN",
                           "postgresql://wp6:local@localhost:55434/postgres")
DB_PREFIX = "a53t_"
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


@pytest.fixture(scope="module")
def _pg_dsn():
    """A fresh database with the gochara-5 migration chain applied verbatim;
    dropped at module end. Refuses to drop anything it did not create."""
    import uuid
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    try:
        admin = psycopg.connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    name = f"{DB_PREFIX}{uuid.uuid4().hex[:10]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    dsn = make_conninfo(ADMIN_DSN, dbname=name)
    try:
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE public.charts (id uuid PRIMARY KEY)")
            cur.execute(
                "CREATE TABLE public._migrations_applied"
                " (filename text PRIMARY KEY, applied_at timestamptz DEFAULT now())")
            for fname in MIGRATION_CHAIN:
                cur.execute((MIGRATIONS / fname).read_text())
                cur.execute("INSERT INTO public._migrations_applied(filename)"
                            " VALUES (%s)", (fname,))
            cur.execute("INSERT INTO public.charts(id) VALUES (%s)", (CHART_ID,))
        conn.close()
        yield dsn
    finally:
        assert name.startswith(DB_PREFIX), name   # never drop what we did not create
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


@pytest.fixture()
def pg(_pg_dsn):
    import psycopg
    conn = psycopg.connect(_pg_dsn, autocommit=True, connect_timeout=3)
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
            body=body.lower(), relation_kind="sign_ingress",   # identity text is lowercase (F-3 §1)
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
                      "truncated_contacts": 0, "prereq_evaluated": 1,
                      "skipped_natal_p1": 0, "unwritable_testimony": 0,
                      "aspect_span_deferred": 0, "moon_agent_on_demand": 0,
                      "p3_enumeration_defects": 0}
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
    # 3/N: with the arc index available the class coverage names the POINT solves as searched.
    # Not every enumerated P3 edge is resolved any more: Moon-agent edges are the EPHEMERAL tier
    # (AM-4) and aspect-to-span edges have no solver in this slice — both named, never claimed.
    all_edges = ev.enumerate_edges("marriage", "P3", CHART)
    stored = [e for e in all_edges if not (e.transit and e.agent == "moon")]
    resolved = [e for e in stored if not (e.transit and e.relation == "aspect"
                                          and e.obj.canonical_target.startswith("span:"))]
    assert 0 < len(resolved) < len(all_edges)
    assert cov == ("marriage", ["residence", "aspect", "conjunction", "natal_fact"],
                   len(resolved))


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
             and e.obj.canonical_target == "span:7"]
    assert len(edges) == 1
    return edges[0]


def _p4_libra_edge(agent: str) -> ev.RecordEdge:
    edges = [e for e in ev.enumerate_edges("marriage", "P4", CHART)
             if e.transit and e.relation == "residence" and e.agent == agent
             and e.obj.canonical_target == "span:7"]
    assert len(edges) == 1
    return edges[0]


def _p1_kwargs(store, edges, rows_by_agent):
    return dict(chart_id=CHART_ID, generation="5.0", event_class="marriage",
                path_id="P1", edges=edges, horizon=HORIZON,
                position_at=_probe([(10, 200)]),
                house_for=_house_from_lagna(CHART["lagna_deg"]),
                sky_convention_id=SKY_CID, source_fact_ids=["fact-1"],
                prerequisites=P1_PREREQS, chart=CHART,
                dasha_rows_for=lambda agent: rows_by_agent.get(agent, []))


def _results(store, predicate):
    return [c["result"] for k, c in store.calls
            if k == "set_prerequisite_result" and c["predicate_id"] == predicate]


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
    assert counts["records"] == 3 and counts["prereq_evaluated"] == 9   # 3 predicates × 3
    calls = [kw for k, kw in store.calls if k == "set_prerequisite_result"]
    assert {c["predicate_id"] for c in calls} == {
        "period_running_at", "natal_bhava_relationship", "transit_relation"}
    assert sorted(_results(store, "period_running_at")) == ["false", "true", "unknown"]
    # ordinals follow the declared membership: 1 = period_running_at
    assert all(c["ordinal"] == 1 for c in calls if c["predicate_id"] == "period_running_at")


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
        return counts, _results(store, "period_running_at")

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
    assert _results(store, "period_running_at") == ["false"]


def test_p1_no_dasha_reader_is_an_explicit_unknown_never_a_silent_null():
    """'Unevaluated' is not 'unknown' (§N.8): with no L1 dasha reader the result is
    STORED as 'unknown', not left NULL."""
    store = FakeStore({"saturn": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    kw = _p1_kwargs(store, [_p1_libra_edge("saturn")], {})
    kw["dasha_rows_for"] = None
    counts = rs.materialise_record_grain(store, **kw)
    assert counts["records"] == 1 and counts["prereq_evaluated"] == 3
    assert _results(store, "period_running_at") == ["unknown"]


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


def _pg_p1_run(conn, dasha_rows, agent="venus"):
    """Seed + coverage + ONE committed P1 grain (`agent` through Libra, ingress day 10)
    with the given L1 dasha rows and the chart. Returns (counts, committed rows)."""
    from services.gochara_kernel.rule_registry import RuleRegistryStore
    RuleRegistryStore(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        _seed_libra_crossings(conn, sky_cid, agent.title())
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    edge = _p1_libra_edge(agent)
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
            sky_convention_id=sky_cid, source_fact_ids=["fact-1"], chart=CHART,
            dasha_rows_for=lambda a: dasha_rows.get(a, []))
    rows = conn.execute(
        "SELECT r.admission_state, p.predicate_id, p.result"
        " FROM public.ka_gochara_relationship_record r"
        " JOIN public.ka_gochara_record_prerequisite p USING (record_id)"
        " WHERE r.generation = %s AND r.path_id = 'P1' AND r.agent = %s ORDER BY p.ordinal",
        (PG_GEN, agent)).fetchall()
    return counts, rows


@pytest.mark.parametrize("agent,dasha_rows,expect_state,expect_period", [
    # Venus OWNS Libra (a scored natal relation) and its contact is stored: the three
    # prerequisites are true ⇒ ADMITTED through the real F5 finalisation
    ("venus", {"venus": [{"start_iso": T0, "end_iso": T0 + 300 * DAY}]}, "admitted", "true"),
    # period not running at the ingress (day 10) ⇒ a false prerequisite ⇒ not_admitted
    ("venus", {"venus": [{"start_iso": T0 + 500 * DAY, "end_iso": T0 + 600 * DAY}]},
     "not_admitted", "false"),
    # no L1 dasha rows ⇒ an explicit unknown, never false ⇒ unqualified
    ("venus", {}, "unqualified", "unknown"),
    # Saturn has NO natal relation to marriage (relation 'none') ⇒ a real false
    ("saturn", {"saturn": [{"start_iso": T0, "end_iso": T0 + 300 * DAY}]},
     "not_admitted", "true"),
])
def test_p1_prerequisite_results_survive_the_real_f5_finalisation(
        pg, agent, dasha_rows, expect_state, expect_period):
    counts, rows = _pg_p1_run(pg, dasha_rows, agent)   # raises at COMMIT if F5 disagrees
    assert counts["records"] == 1 and counts["prereq_evaluated"] == 3
    assert {r[0] for r in rows} == {expect_state}
    by_pred = {r[1]: r[2] for r in rows}
    assert by_pred["period_running_at"] == expect_period
    assert by_pred["transit_relation"] == "true"       # read back from the stored contact
    assert by_pred["natal_bhava_relationship"] == ("true" if agent == "venus" else "false")
    assert "NULL" not in {str(r[2]) for r in rows} and None not in {r[2] for r in rows}


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


# ── AM-3 / §N.3: candidate REPLACEMENT in dependency order ──────────────────

def test_grain_replaces_after_the_coverage_check_and_before_any_insert():
    store = FakeStore({"saturn": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    _run(store, [_libra_edge()])
    kinds = [k for k, _ in store.calls]
    assert kinds.index("stored_coverage_facts_json") < kinds.index("delete_record_grain")
    assert kinds.index("delete_record_grain") < kinds.index("insert_contact")
    assert kinds.index("delete_record_grain") < kinds.index("insert_record")
    (_, kw), = [c for c in store.calls if c[0] == "delete_record_grain"]
    assert (kw["event_class"], kw["path_id"], kw["rule_version"], kw["generation"]) == (
        "marriage", "P3", "1.0.0", "5.0")


def test_grain_with_no_edges_still_replaces_its_stale_rows():
    """An empty grain (e.g. H-unknown class) must still clear what an earlier
    run wrote — a rebuild never leaves the previous generation of rows behind."""
    store = FakeStore({})
    counts = _run(store, [])
    assert counts["records"] == 0
    assert any(k == "delete_record_grain" for k, _ in store.calls)


def test_grain_without_coverage_refuses_with_no_delete():
    store = FakeStore({"saturn": [_crossing(10, 180.0)]}, coverage_present=False)
    with pytest.raises(rs.MissingCoverageError):
        _run(store, [_libra_edge()])
    assert not any(k == "delete_record_grain" for k, _ in store.calls)


class _RecordingConn:
    """Records every statement; answers the sealed-generation probe and the
    contact-id SELECT; reports a rowcount for DELETEs."""

    def __init__(self, sealed=False, contact_ids=("c1", "c2")):
        self.sealed, self.contact_ids = sealed, list(contact_ids)
        self.statements: list[str] = []

    def execute(self, sql, params=None):
        self.statements.append(" ".join(sql.split()))
        conn = self

        class _R:
            rowcount = 1

            def fetchone(self_inner):
                return (conn.sealed,)

            def fetchall(self_inner):
                return [(c,) for c in conn.contact_ids]
        return _R()


def _tables_deleted(conn):
    out = []
    for st in conn.statements:
        if st.startswith("DELETE FROM public."):
            out.append(st.split()[2].removeprefix("public."))
    return out


def test_record_grain_delete_runs_in_fk_dependency_order():
    conn = _RecordingConn()
    rs.RecordStore(conn).delete_record_grain(
        chart_id=CHART_ID, generation="5.0", event_class="marriage",
        path_id="P3", rule_version="1.0.0")
    assert _tables_deleted(conn) == [
        "ka_gochara_eval_window",            # membership cascades with it
        "ka_gochara_relationship_record",    # prerequisites cascade with it
        "ka_gochara_contact"]                # only the contacts no record still uses
    contact_delete = [st for st in conn.statements
                      if st.startswith("DELETE FROM public.ka_gochara_contact")][0]
    assert "NOT EXISTS" in contact_delete and "ka_gochara_relationship_record" in contact_delete


def test_class_chain_delete_ends_with_the_coverage_partition():
    conn = _RecordingConn()
    rs.RecordStore(conn).delete_class_chain(
        chart_id=CHART_ID, generation="5.0", event_class="marriage")
    assert _tables_deleted(conn) == [
        "ka_gochara_eval_window", "ka_gochara_relationship_record",
        "ka_gochara_contact", "kala_gochara_coverage"]


def test_a_sealed_generation_is_refused_before_any_delete():
    for fn, kw in ((rs.RecordStore.delete_record_grain,
                    dict(event_class="marriage", path_id="P3", rule_version="1.0.0")),
                   (rs.RecordStore.delete_class_chain, dict(event_class="marriage"))):
        conn = _RecordingConn(sealed=True)
        with pytest.raises(rs.SealedGenerationError, match="SEALED"):
            fn(rs.RecordStore(conn), chart_id=CHART_ID, generation="5.0", **kw)
        assert _tables_deleted(conn) == []


def test_no_contacts_to_orphan_means_no_contact_delete():
    conn = _RecordingConn(contact_ids=())
    rs.RecordStore(conn).delete_record_grain(
        chart_id=CHART_ID, generation="5.0", event_class="marriage",
        path_id="P3", rule_version="1.0.0")
    assert "ka_gochara_contact" not in _tables_deleted(conn)


# real DB: the rebuild really replaces (own generations 5.3 / 5.4)

def _pg_p3_run(conn, generation, build_id):
    from services.gochara_kernel.rule_registry import RuleRegistryStore
    RuleRegistryStore(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        _seed_libra_crossings(conn, sky_cid, "Saturn")
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    probe = _probe([(10, 200)])
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(
            store, chart_id=CHART_ID, generation=generation, event_class="marriage",
            class_edges=ev.enumerate_edges("marriage", "P3", CHART),
            horizon=HORIZON, position_at=probe, sky_convention_id=sky_cid,
            kala_convention_id=kala_cid, build_id=build_id,
            arc_index_available=False)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        return rs.materialise_record_grain(
            store, chart_id=CHART_ID, generation=generation, event_class="marriage",
            path_id="P3", edges=[_libra_edge()], horizon=HORIZON, position_at=probe,
            house_for=_house_from_lagna(CHART["lagna_deg"]),
            sky_convention_id=sky_cid, source_fact_ids=["fact-1"])


def _row_counts(conn, generation):
    q = lambda t: conn.execute(  # noqa: E731
        f"SELECT count(*) FROM public.{t} WHERE generation = %s",
        (generation,)).fetchone()[0]
    return (q("kala_gochara_coverage"), q("ka_gochara_contact"),
            q("ka_gochara_relationship_record"))


def test_a_rebuild_with_a_new_build_id_replaces_and_never_accretes_or_raises(pg):
    """The previous insert-if-absent coverage byte-check compared build_id, so
    the SECOND orchestrated build (a new build id) died with an
    IdentityCollisionError. A rebuild now replaces the class chain."""
    first = _pg_p3_run(pg, "5.3", build_id="build-one")
    assert _row_counts(pg, "5.3") == (1, 1, 1)
    second = _pg_p3_run(pg, "5.3", build_id="build-two")        # raised before
    assert first == second
    assert _row_counts(pg, "5.3") == (1, 1, 1)                  # replaced, not accreted
    assert pg.execute(
        "SELECT build_id FROM public.kala_gochara_coverage WHERE generation = '5.3'"
    ).fetchone()[0] == "build-two"


def test_a_contact_another_path_still_references_survives_a_grain_replace(pg):
    """P3 and P4 share one physical contact (once geometrically, once per path
    interpretively): replacing the P3 grain must never delete it."""
    from services.gochara_kernel.rule_registry import RuleRegistryStore
    RuleRegistryStore(pg).seed()
    with pg.transaction():
        pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(pg)
        for a in ("Saturn", "Jupiter"):
            _seed_libra_crossings(pg, sky_cid, a)
    store = rs.RecordStore(pg)
    kala_cid = store.ensure_kala_convention()
    probe = _probe([(10, 200)])
    gen = "5.4"
    class_edges = (ev.enumerate_edges("marriage", "P3", CHART)
                   + ev.enumerate_edges("marriage", "P4", CHART))
    with pg.transaction():
        pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(
            store, chart_id=CHART_ID, generation=gen, event_class="marriage",
            class_edges=class_edges, horizon=HORIZON, position_at=probe,
            sky_convention_id=sky_cid, kala_convention_id=kala_cid,
            build_id="b", arc_index_available=False)

    def grain(path, edges):
        with pg.transaction():
            pg.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            return rs.materialise_record_grain(
                store, chart_id=CHART_ID, generation=gen, event_class="marriage",
                path_id=path, edges=edges, horizon=HORIZON, position_at=probe,
                house_for=_house_from_lagna(CHART["lagna_deg"]),
                sky_convention_id=sky_cid, source_fact_ids=["fact-1"])

    sat = [e for e in ev.enumerate_edges("marriage", "P3", CHART)
           if e.transit and e.relation == "residence" and e.agent == "saturn"
           and e.obj.canonical_target == "span:7"]
    sat4 = [e for e in ev.enumerate_edges("marriage", "P4", CHART)
            if e.transit and e.relation == "residence" and e.agent == "saturn"
            and e.obj.canonical_target == "span:7"]
    grain("P3", sat)
    grain("P4", sat4)
    assert _row_counts(pg, gen)[1:] == (1, 2)      # ONE shared contact, two records
    grain("P3", sat)                                # replace P3 only
    assert _row_counts(pg, gen)[1:] == (1, 2)      # the shared contact survived
    paths = [r[0] for r in pg.execute(
        "SELECT path_id FROM public.ka_gochara_relationship_record"
        " WHERE generation = %s ORDER BY path_id", (gen,)).fetchall()]
    assert paths == ["P3", "P4"]


# ── steward rulings 2026-10-02 (B's PREREQUISITE_EVALUATION_ANSWER / AM-11) ────
# every declared prerequisite is EVALUATED — by Stream B's rule logic, read back from
# stored rows where the predicate is a declaration — never hard-coded, never left NULL.

def _moon_house_for(chart):
    moon_idx = int(chart["natal"]["Moon"] // 30)

    def house_for(edge, sign):
        return (SIGNS.index(sign.lower()) - moon_idx) % 12 + 1
    return house_for


def _p2_edge(agent, sign_name):
    edges = [e for e in ev.enumerate_edges("marriage", "P2", CHART)
             if e.transit and e.agent == agent
             and e.obj.canonical_target == f"span:{SIGN_NUM[sign_name]}"]
    assert len(edges) == 1, (agent, sign_name, len(edges))
    return edges[0]


SIGN_NUM = {n: i + 1 for i, n in enumerate(SIGNS)}


def _p2_run(agent, sign_name, **over):
    edge = _p2_edge(agent, sign_name)
    lvl = float(SIGNS.index(sign_name) * 30)
    store = FakeStore({agent: [_crossing(10, lvl), _crossing(200, lvl + 30.0)]})
    probe = lambda b, t: lvl + 15.0 if 10 <= (t - T0) / DAY < 200 else (lvl + 195.0) % 360  # noqa: E731
    kw = dict(chart_id=CHART_ID, generation="5.0", event_class="marriage", path_id="P2",
              edges=[edge], horizon=HORIZON, position_at=probe,
              house_for=_moon_house_for(CHART), sky_convention_id=SKY_CID,
              source_fact_ids=["fact-1"], chart=CHART,
              prerequisites=PATH_PREREQS["P2"])
    kw.update(over)
    counts = rs.materialise_record_grain(store, **kw)
    return store, counts


def test_p2_house_from_moon_is_true_inside_the_cited_set_via_b_favourable_houses():
    # Saturn's cited favourable houses from the Moon are {3, 6, 11}; the Aquarius Moon
    # makes Aries the 3rd (the oracle's written-out count)
    store, counts = _p2_run("saturn", "aries")
    assert counts["records"] == 1 and counts["prereq_evaluated"] == 1
    assert _results(store, "house_from_moon") == ["true"]


def test_p2_house_from_moon_is_false_outside_every_cited_set():
    """P2 only ENUMERATES cited houses, so the false branch is proven by handing an
    enumerated edge a house outside Saturn's cited favourable ∪ adverse set
    ({3, 6, 11} ∪ {12, 8, 1}): the 5th — read back, not asserted."""
    store, counts = _p2_run("saturn", "aries", house_for=lambda e, s: 5)
    assert counts["records"] == 1
    assert _results(store, "house_from_moon") == ["false"]


def test_p2_adverse_houses_are_inside_the_set_for_the_four_cited_malefics():
    store, _ = _p2_run("saturn", "aries", house_for=lambda e, s: 8)     # adverse residence
    assert _results(store, "house_from_moon") == ["true"]
    store, _ = _p2_run("saturn", "aries", house_for=lambda e, s: 9)     # in neither set
    assert _results(store, "house_from_moon") == ["false"]


def test_p2_house_from_moon_is_unknown_without_the_natal_moon_never_false():
    store, _ = _p2_run("saturn", "aries", chart=None)
    assert _results(store, "house_from_moon") == ["unknown"]
    broken = {**CHART, "natal": {k: v for k, v in CHART["natal"].items() if k != "Moon"}}
    store, _ = _p2_run("saturn", "aries", chart=broken)
    assert _results(store, "house_from_moon") == ["unknown"]


def test_p3_membership_is_read_back_against_the_truth_table_and_true_for_enumerated_edges():
    sat = [e for e in ev.enumerate_edges("marriage", "P3", CHART)
           if e.transit and e.relation == "residence" and e.agent == "saturn"
           and e.obj.canonical_target == "span:7"]
    store = FakeStore({"saturn": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    counts = _run(store, sat)
    assert counts["records"] == 1 and counts["p3_enumeration_defects"] == 0
    assert _results(store, "p3_contact_house_or_lord") == ["true"]


def test_p3_a_record_outside_h_union_l_is_a_loudly_reported_enumeration_defect(caplog):
    sat = [e for e in ev.enumerate_edges("marriage", "P3", CHART)
           if e.transit and e.relation == "residence" and e.agent == "saturn"
           and e.obj.canonical_target == "span:7"][0]
    from dataclasses import replace
    bad = replace(sat, object_role="lord")          # a house span claiming the lord role
    store = FakeStore({"saturn": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    with caplog.at_level("ERROR"):
        counts = _run(store, [bad])
    assert _results(store, "p3_contact_house_or_lord") == ["false"]
    assert counts["p3_enumeration_defects"] == 1
    assert any("enumeration defect" in r.message for r in caplog.records)


def test_p3_unknown_h_class_is_unknown_never_false():
    store = FakeStore({"saturn": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    e = [x for x in ev.enumerate_edges("marriage", "P3", CHART)
         if x.transit and x.relation == "residence" and x.agent == "saturn"
         and x.obj.canonical_target == "span:7"][0]
    counts = _run(store, [e], event_class="spiritual_turn")      # H unknown (S:307-312)
    assert counts["records"] == 1
    assert _results(store, "p3_contact_house_or_lord") == ["unknown"]


def test_p3_natal_maraka_testimony_row_has_no_contact_so_the_result_is_an_explicit_unknown():
    mar = [e for e in ev.enumerate_edges("marriage", "P3", CHART) if not e.transit]
    assert mar, "marriage enumerates māraka testimony rows"
    store = FakeStore({})
    counts = _run(store, mar)
    assert counts["natal_records"] == len(mar)
    assert set(_results(store, "p3_contact_house_or_lord")) == {"unknown"}


def test_transit_relation_is_a_read_back_not_a_literal_true():
    """Remove the stored contact from the read-back and the SAME record flips to false:
    the result is computed from stored rows, not asserted by the minting loop."""
    store = FakeStore({"venus": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    store.stored_contact_keys = lambda **kw: set()       # the contact is not stored
    counts = rs.materialise_record_grain(store, **_p1_kwargs(
        store, [_p1_libra_edge("venus")],
        {"venus": [{"start_iso": T0, "end_iso": T0 + 300 * DAY}]}))
    assert counts["records"] == 1
    assert _results(store, "transit_relation") == ["false"]


def test_p1_natal_bhava_relationship_scored_none_and_unknown():
    for agent, want in (("venus", "true"), ("saturn", "false")):
        store = FakeStore({agent: [_crossing(10, 180.0), _crossing(200, 210.0)]})
        rs.materialise_record_grain(store, **_p1_kwargs(
            store, [_p1_libra_edge(agent)], {}))
        assert _results(store, "natal_bhava_relationship") == [want], agent
    # H unknown ⇒ the relation is unknown (never false)
    store = FakeStore({"venus": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    kw = _p1_kwargs(store, [_p1_libra_edge("venus")], {})
    kw["event_class"] = "spiritual_turn"
    rs.materialise_record_grain(store, **kw)
    assert _results(store, "natal_bhava_relationship") == ["unknown"]
    # no chart at all ⇒ unknown
    store = FakeStore({"venus": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    kw = _p1_kwargs(store, [_p1_libra_edge("venus")], {})
    kw["chart"] = None
    rs.materialise_record_grain(store, **kw)
    assert _results(store, "natal_bhava_relationship") == ["unknown"]


def test_p1_testimony_licence_lords_are_not_minted_and_the_count_names_them():
    """A lord whose only natal relation is a testimony kind (non-node dispositorship —
    no clause, no ruling_ref: D3) cannot be written (kgrr_ruling_ck): not minted,
    counted, never silently dropped. Jupiter natal in Taurus ⇒ its dispositor Venus owns
    Libra ∈ H."""
    chart = {**CHART, "natal": {**CHART["natal"], "Jupiter": 45.0}}
    jup = _p1_libra_edge("jupiter")
    store = FakeStore({"jupiter": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    kw = _p1_kwargs(store, [jup], {})
    kw["chart"] = chart
    counts = rs.materialise_record_grain(store, **kw)
    assert counts["records"] == 0 and counts["contacts"] == 0
    assert counts["unwritable_testimony"] == 1


def test_p1_natal_fact_rows_are_not_admission_bearing_records():
    """AM-11 pin (b): P1's natal-fact rows (no contact) are NOT materialised; the count
    names them."""
    natal = [e for e in ev.enumerate_edges("marriage", "P1", CHART) if not e.transit]
    assert natal
    store = FakeStore({"venus": [_crossing(10, 180.0), _crossing(200, 210.0)]})
    kw = _p1_kwargs(store, natal + [_p1_libra_edge("venus")], {})
    counts = rs.materialise_record_grain(store, **kw)
    assert counts["natal_records"] == 0 and counts["skipped_natal_p1"] == len(natal)
    assert counts["records"] == 1
    assert not any(k == "insert_record" and kw_["contact_id"] is None
                   for k, kw_ in store.calls)


# ── F-3 §7: records mint ONLY via evaluator.record_uuid ──────────────────────

def test_the_record_store_refuses_a_non_uuid8_record_id():
    import uuid as _u
    from services.gochara_kernel.record_store import _require_minted_record_uuid
    from services.gochara_kernel import evaluator as ev

    minted = ev.record_uuid({"k": "v"})
    _require_minted_record_uuid(minted)                       # accepted: UUIDv8
    _require_minted_record_uuid(str(minted))                  # accepted: its string form
    with pytest.raises(ValueError, match="record_uuid"):
        _require_minted_record_uuid("sha256:" + "ab" * 32)     # the older RelationshipRecord property
    with pytest.raises(ValueError, match="UUIDv8"):
        _require_minted_record_uuid(_u.uuid4())               # a v4 UUID is not a minted identity
