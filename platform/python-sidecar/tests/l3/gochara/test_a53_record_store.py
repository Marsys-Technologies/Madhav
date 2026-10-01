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
    """position_at: LIBRA_MID inside the (day) ranges, NOT_LIBRA_MID outside
    — consistent with the fixture crossings (into libra at 180°, out at 210°)."""
    def position_at(t: datetime) -> float:
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
                      "truncated_contacts": 0}
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
    from services.gochara_kernel.substrate import (SkyEventStore,
                                                   assign_occurrence_ordinals,
                                                   physical_object_id)
    store = SkyEventStore(conn)
    for level, day in ((180.0, 10), (210.0, 200)):
        poid = physical_object_id(
            body="Saturn", relation_kind="sign_ingress",
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
                build_id="test-build-pg")


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
                      "truncated_contacts": 0}
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
    assert cov == ("marriage", ["residence", "natal_fact"], 11)


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
        " WHERE generation = '5.0'").fetchone()
    assert n[0] == first["records"]
