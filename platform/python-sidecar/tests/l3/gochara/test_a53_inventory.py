"""A5.3 — AM-5 search-inventory planner + store against migration 1206 (PR #2867).

Pure planner tests need no database. The store tests run on a throwaway database with the
REAL chain 1081/1152–1157 + 1206 applied verbatim (L1 tables stubbed minimally). 1206's
shapes are FROZEN at the Codex-accepted v1.2 (#2867 @ffc4b5b05, steward M20261001T233255-baf3) — these
tests are where a shape change shows.
"""
from __future__ import annotations

import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import inventory as inv
from services.gochara_kernel import ledger as gk_ledger
from services.gochara_kernel import record_store as rs
from services.gochara_kernel.inventory_store import InventoryStore, SnapshotUnboundError
from services.gochara_kernel.rule_registry import RuleRegistryStore

from . import test_a53_record_store as base
from .test_a53_record_store import MIGRATIONS, MIGRATION_CHAIN, ADMIN_DSN, DB_PREFIX

UTC = timezone.utc
H0 = datetime(2025, 1, 1, tzinfo=UTC)
H1 = datetime(2025, 3, 1, tzinfo=UTC)
CHART = base.CHART
CHART_ID = base.CHART_ID
FACT_IDS = [f"fact-{n}" for n in ("LAGNA", "SUN", "MOON", "MAR", "MER", "JUP", "VEN",
                                  "SAT", "RAH_MEAN", "KET_MEAN")]
def _dt(y, m, d):
    return datetime(y, m, d, tzinfo=UTC)


def _row(i, level, lord, a, b):
    return inv.DashaRow(str(uuid.UUID(int=i)), level, lord, a, b)


#: parent of each fixture row (an AD nests in its MD, a PD in its AD — §4.0 linkage)
DASHA_PARENT = {1: None, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3}
L0_VEDHA_ROWS = [tuple(r) for r in json.loads(
    (Path(__file__).resolve().parents[1] / "gochara_rules" / "fixtures" / "l0_vedha_rows_2026_10_02.json").read_text())]
PINNED_BUILD = "1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb"      # the frozen §4.0 contract build


# Pinned Vimśottarī rows around the class horizon [2025-01-01, 2025-03-01): each level
# partitions it (the AD row starting before the horizon is clipped, §4.0 half-open).
DASHA = [
    _row(1, 1, "saturn", _dt(2024, 6, 1), _dt(2026, 6, 1)),
    _row(2, 2, "venus", _dt(2024, 12, 1), _dt(2025, 2, 1)),
    _row(3, 2, "sun", _dt(2025, 2, 1), _dt(2025, 4, 1)),
    _row(4, 3, "mars", _dt(2024, 12, 20), _dt(2025, 1, 15)),
    _row(5, 3, "rahu", _dt(2025, 1, 15), _dt(2025, 2, 1)),
    _row(6, 3, "jupiter", _dt(2025, 2, 1), _dt(2025, 3, 20)),
]
DASHA_IDS = [r.row_id for r in DASHA]
SEALED = [("P1", "1.0.0"), ("P2", "1.0.0"), ("P3", "1.0.0"), ("P4", "1.0.0"), ("P5", "1.0.0")]
FULL = inv.SearchCapability(position_probe=True, arc_index=True)
P5_EXCL = inv.Exclusion("tier_withheld_by_ruling", "ruling:M20261001T121451-1a8d",
                        "M20261001T121451-1a8d")
H_UNKNOWN_EXCL = inv.Exclusion("inputs_unavailable", "ruling:TEST-H-UNKNOWN", "TEST-H-UNKNOWN")


def _plan(cls="marriage", cap=FULL, **kw):
    kw.setdefault("dasha_rows", DASHA)
    return inv.plan_class_inventory(
        event_class=cls, chart=CHART, horizon=(H0, H1), sealed_paths=SEALED,
        capability=cap, path_exclusions={"P5": P5_EXCL}, **kw)


# ── planner (pure) ───────────────────────────────────────────────────────────

def test_obligation_bytes_are_arity_nine_lowercase_and_the_ob_id_is_their_uuidv8():
    plan = _plan()
    obs = plan.obligations
    assert obs
    for o in obs:
        b = o.canonical_bytes
        assert b == b.lower() and len(b.split("|")) == 9 and "\n" not in b
        assert b.startswith(f"marriage|{o.path_id.lower()}|1.0.0|")
        assert str(o.ob_id) == str(inv._uuid8_of(b.encode()))
    # distinct paths over shared geometry are distinct obligations (once per path)
    assert len({o.canonical_bytes for o in obs}) == len(obs)


def test_the_pin_partition_is_total_over_the_sealed_registry():
    plan = _plan()
    assert [(p.path_id, p.rule_version) for p in plan.pins] == SEALED
    by = {p.path_id: p for p in plan.pins}
    assert by["P5"].disposition == "excluded"
    assert (by["P5"].exclusion_reason, by["P5"].ruling_ref) == (
        "tier_withheld_by_ruling", "M20261001T121451-1a8d")
    for pid in ("P1", "P2", "P3", "P4"):
        assert by[pid].disposition in ("included", "computed_empty")
        if by[pid].disposition == "included":
            assert by[pid].committed_ob_ids == sorted({o.ob_id for o in by[pid].obligations})
            assert by[pid].committed_ob_ids == sorted(by[pid].committed_ob_ids)


def test_a_provably_empty_path_is_computed_empty_with_a_stated_basis_never_absent():
    # marriage is a gain class: P2's adverse-residence plan is empty by polarity — but its
    # favourable table is not; pick a class/path the derivation proves empty
    for cls in ev.ROW_MEMBERSHIP:
        if cls == "birth_anchor":
            continue
        plan = _plan(cls, h_unknown_exclusion=H_UNKNOWN_EXCL)
        for p in plan.pins:
            if p.disposition == "computed_empty":
                assert p.basis and p.basis.startswith("spec:GOCHARA_DESIGN_SPECS@1.4#")
                assert not p.obligations and p.committed_ob_ids == []
                return
    pytest.skip("no computed_empty path on this chart")


def test_unknown_signature_houses_block_by_name_unless_a_ruling_is_given():
    from services.gochara_rules.registry import signature_houses
    unknown = [c for c in ev.ROW_MEMBERSHIP
               if c != "birth_anchor" and signature_houses(c, CHART) is None]
    assert unknown, "the chart must have H-unknown classes"
    cls = unknown[0]
    with pytest.raises(inv.InventoryBlocked, match=cls):
        _plan(cls)
    plan = _plan(cls, h_unknown_exclusion=H_UNKNOWN_EXCL)
    by = {p.path_id: p for p in plan.pins}
    for pid in ("P1", "P3", "P4"):
        assert by[pid].disposition == "excluded"
        assert (by[pid].exclusion_reason, by[pid].ruling_ref) == (
            "inputs_unavailable", "TEST-H-UNKNOWN")
    assert by["P2"].disposition in ("included", "computed_empty")   # not H-dependent


@pytest.mark.parametrize("reason,ruling,ok", [
    ("tier_withheld_by_ruling", None, False), ("disabled_form", None, False),
    ("inputs_unavailable", None, False),
    ("not_applicable_to_class", "R-1", False), ("on_demand_tier", "R-1", False),
    ("tier_withheld_by_ruling", "R-1", True), ("not_applicable_to_class", None, True),
    ("on_demand_tier", None, True), ("bogus", None, False),
])
def test_exclusion_ruling_is_required_iff_the_reason_degrades(reason, ruling, ok):
    if ok:
        inv.Exclusion(reason, "ruling:X", ruling)
    else:
        with pytest.raises(ValueError):
            inv.Exclusion(reason, "ruling:X", ruling)


def test_interval_states_follow_the_search_capability_never_assumed():
    # the build's REAL capability: probe + arc index, but NO aspect-to-span solver (the aspect
    # point's ingress into a house span has none in this slice) — those obligations stay
    # `missing_inputs` (a seal refusal by design), never `searched_complete` on a search nobody ran
    honest = _plan()
    obs_h = {o.ob_id: o for o in honest.obligations}
    missing_h = [iv for iv in honest.intervals if iv.state == "missing_inputs"]
    is_span_aspect = lambda o: o.relation == "aspect" and o.target.startswith("span:")  # noqa: E731
    assert missing_h and all(is_span_aspect(obs_h[iv.ob_id]) for iv in missing_h)
    assert any(is_span_aspect(obs_h[iv.ob_id]) for iv in missing_h)
    assert {iv.state for iv in honest.intervals} == {"searched_complete", "missing_inputs"}
    full = _plan(cap=inv.SearchCapability(position_probe=True, arc_index=True,
                                          aspect_span_solver=True))
    assert {iv.state for iv in full.intervals} == {"searched_complete"}
    no_probe = _plan(cap=inv.SearchCapability(position_probe=False, arc_index=True,
                                              aspect_span_solver=True))
    no_arc = _plan(cap=inv.SearchCapability(position_probe=True, arc_index=False,
                                            aspect_span_solver=True))
    by_ob = lambda plan: {o.ob_id: o for o in plan.obligations}  # noqa: E731
    # no probe: residence is unsearched AND so is aspect-to-span (it derives from the residence
    # spans); the POINT aspects (arc index) are still searched
    kinds = lambda plan: {  # noqa: E731
        (by_ob(plan)[iv.ob_id].relation,
         by_ob(plan)[iv.ob_id].target.split(":")[0])
        for iv in plan.intervals if iv.state == "missing_inputs" and by_ob(plan)[iv.ob_id].transit}
    assert kinds(no_probe) == {("residence", "span"), ("aspect", "span")}
    assert kinds(no_arc) == {("conjunction", "point"), ("aspect", "point")}
    for plan in (no_probe, no_arc):
        obs = by_ob(plan)
        # an atemporal natal fact is evaluated from L1 whatever the solver set
        assert all(iv.state == "searched_complete" for iv in plan.intervals
                   if not obs[iv.ob_id].transit)


def test_every_obligations_intervals_partition_the_class_horizon_exactly():
    plan = _plan()
    by_ob = {}
    for iv in plan.intervals:
        by_ob.setdefault(iv.ob_id, []).append(iv)
    assert set(by_ob) == {o.ob_id for o in plan.obligations}
    for ivs in by_ob.values():
        ivs.sort(key=lambda i: i.start)
        assert ivs[0].start == H0 and ivs[-1].end == H1
        assert all(a.end == b.start for a, b in zip(ivs, ivs[1:]))      # contiguous, disjoint
    assert plan.relations == sorted({o.relation for o in plan.obligations})
    assert "natal_fact" not in plan.relations            # the REAL relations (kgso_relation_ck)


def test_horizon_must_be_whole_second_utc():
    for bad in (datetime(2025, 1, 1), datetime(2025, 1, 1, 0, 0, 0, 5, tzinfo=UTC)):
        with pytest.raises(ValueError):
            inv.plan_class_inventory(
                event_class="marriage", chart=CHART, horizon=(bad, H1),
                sealed_paths=SEALED, capability=FULL,
                path_exclusions={"P5": P5_EXCL})


# ── store (real 1206) ────────────────────────────────────────────────────────

def create_am5_database(tag="am5", faithful=False):
    """A throwaway database with the real chain + 1206 applied and the L1 tables stubbed.
    Returns (admin_conn, name, dsn); the caller drops it (refusing non-prefixed names)."""
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    try:
        admin = psycopg.connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        if os.environ.get("GOCHARA_A53_REQUIRE_DB") == "1":      # CI: an unreachable server is a FAILURE, never a skip
            pytest.fail(f"GOCHARA_A53_REQUIRE_DB=1 but the disposable database server is unreachable ({exc})")
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    name = f"{DB_PREFIX}{tag}_{uuid.uuid4().hex[:8]}"
    if faithful:
        # a deployment-faithful mirror (1206-R6 method): the builder / verifier / sealer principals EXIST when the
        # migrations run (so their role-guarded grants apply) and PUBLIC EXECUTE is revoked on every function the
        # migration role creates — exactly what production's bootstrap does
        admin.execute("DO $$ BEGIN"
                      " IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN"
                      "   CREATE ROLE data_plane_builder NOLOGIN; END IF;"
                      " IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier') THEN"
                      "   CREATE ROLE gochara_verifier NOLOGIN; END IF;"
                      " IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_sealer') THEN"
                      "   CREATE ROLE gochara_sealer NOLOGIN; END IF;"
                      " END $$")
    admin.execute(f'CREATE DATABASE "{name}"')
    dsn = make_conninfo(ADMIN_DSN, dbname=name)
    try:
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
        if faithful:
            conn.execute("ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC")
        _populate_am5_database(conn)
        conn.close()
    except BaseException:
        drop_am5_database(admin, name)
        raise
    return admin, name, dsn


def drop_am5_database(admin, name):
    assert name.startswith(DB_PREFIX), name           # never drop what we did not create
    admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    admin.close()


def _populate_am5_database(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE public.charts (id uuid PRIMARY KEY)")
        cur.execute("CREATE TABLE public._migrations_applied"
                    " (filename text PRIMARY KEY, applied_at timestamptz DEFAULT now())")
        cur.execute("CREATE TABLE public.chart_facts (fact_id text PRIMARY KEY,"
                    " chart_id uuid, ayanamsha_id text, fact_category text, fact_subject text,"
                    " fact_key text,"
                    " fact_value_num double precision, created_at timestamptz DEFAULT now())")
        cur.execute("CREATE TABLE public.chart_dashas (dasha_row_id uuid PRIMARY KEY,"
                    " chart_id uuid, ayanamsha_id text, system_id text, level_n int,"
                    " parent_row_id uuid, lord_graha text, start_iso timestamptz,"
                    " end_iso timestamptz, build_id uuid, verification_pass_status text,"
                    " computed_at timestamptz DEFAULT now())")
        # L0 reference the input vector binds (P2's cited vedha rows, AM-18): the real table's shape
        cur.execute("CREATE TABLE public.bg_transit_rules (id SERIAL PRIMARY KEY, rule_type TEXT NOT NULL"
                    " CHECK (rule_type IN ('favourable','unfavourable','vedha')), graha TEXT NOT NULL,"
                    " primary_house INTEGER NOT NULL, vedha_house INTEGER, phala TEXT NOT NULL,"
                    " classical_citation TEXT NOT NULL, rule_notes TEXT,"
                    " UNIQUE (graha, rule_type, primary_house))")
        # the VALIDATED 42-row authority exhibit (36 cited classical + 6 L0-flagged UNSOURCED node rows, read
        # read-only from production 2026-10-02 — Stream B's literal fixture), exactly what the pair loader consumes
        for graha, house, vedha, citation, rule_type in L0_VEDHA_ROWS:
            cur.execute("INSERT INTO public.bg_transit_rules (rule_type, graha, primary_house, vedha_house,"
                        " phala, classical_citation) VALUES (%s, %s, %s, %s, 'x', %s)",
                        (rule_type, graha, house, vedha, citation))
        for fname in MIGRATION_CHAIN + ["1206_gochara_search_inventory_completeness.sql",
                                        "1240_gochara_window_verification_gate.sql"]:
            cur.execute((MIGRATIONS / fname).read_text())
            cur.execute("INSERT INTO public._migrations_applied(filename) VALUES (%s)",
                        (fname,))
        cur.execute("INSERT INTO public.charts(id) VALUES (%s)", (CHART_ID,))
        subj = {"LAGNA": CHART["lagna_deg"], "SUN": CHART["natal"]["Sun"],
                "MOON": CHART["natal"]["Moon"], "MAR": CHART["natal"]["Mars"],
                "MER": CHART["natal"]["Mercury"], "JUP": CHART["natal"]["Jupiter"],
                "VEN": CHART["natal"]["Venus"], "SAT": CHART["natal"]["Saturn"],
                "RAH_MEAN": CHART["natal"]["Rahu"], "KET_MEAN": CHART["natal"]["Ketu"]}
        for sname, lon in subj.items():
            cur.execute("INSERT INTO public.chart_facts(fact_id, chart_id, ayanamsha_id,"
                        " fact_category, fact_subject, fact_key, fact_value_num)"
                        " VALUES (%s,%s,'lahiri_chitrapaksha','graha_position',%s,"
                        " 'longitude_sidereal',%s)",
                        (f"fact-{sname}", CHART_ID, sname, lon))
        for r in DASHA:
            parent = DASHA_PARENT[int(uuid.UUID(r.row_id).int)]
            cur.execute("INSERT INTO public.chart_dashas(dasha_row_id, chart_id,"
                        " ayanamsha_id, system_id, level_n, parent_row_id, lord_graha,"
                        " start_iso, end_iso, build_id, verification_pass_status)"
                        " VALUES (%s,%s,'lahiri_chitrapaksha','vimshottari',%s,%s,%s,%s,%s,"
                        " %s,'two_pass_verified')",
                        (r.row_id, CHART_ID, r.level,
                         None if parent is None else str(uuid.UUID(int=parent)),
                         r.lord.title(), r.start, r.end, PINNED_BUILD))


@pytest.fixture(scope="module")
def _am5_dsn():
    admin, name, dsn = create_am5_database("am5")
    try:
        yield dsn
    finally:
        drop_am5_database(admin, name)


@pytest.fixture()
def am5(_am5_dsn):
    import psycopg
    conn = psycopg.connect(_am5_dsn, autocommit=True, connect_timeout=3)
    yield conn
    conn.close()


def _boot(conn, generation, vector=None):
    """Registry sealed, sky + legacy convention bridged, a CANDIDATE manifest whose
    horizon is the inventory horizon. Returns (store, sky_cid, kala_cid)."""
    RuleRegistryStore(conn).seed()
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky = base._sky_convention_id(conn)
        kala = rs.RecordStore(conn).ensure_kala_convention()
        rs.RecordStore(conn).ensure_bridge(kala, sky)
        gk_ledger.publish_candidate(
            conn, CHART_ID, generation, kala, vector or {"rule_registry": "r1"},
            {"backend": "swieph"}, f"[{H0.isoformat()},{H1.isoformat()})",
            writer_asset_id="ka_gochara_v5")
    return InventoryStore(conn), sky, kala


def _write(conn, store, sky, generation, plan):
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        store.delete_generation_inventory(CHART_ID, generation)
        digest = store.insert_snapshot(
            chart_id=CHART_ID, generation=generation, convention_id=sky,
            consumed_fact_ids=FACT_IDS,
            consumed_dasha_row_ids=DASHA_IDS)
        out = store.write_class_inventory(
            chart_id=CHART_ID, generation=generation, plan=plan, input_digest=digest)
    return digest, out


def test_the_registry_seals_are_the_pin_partition_the_planner_must_cover(am5):
    store, _sky, _ = _boot(am5, "5.7")
    with am5.transaction():
        am5.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        assert store.sealed_rule_paths() == SEALED


def test_a_planned_class_is_stored_finalised_and_the_digests_are_the_dbs(am5):
    store, sky, _ = _boot(am5, "5.7")
    plan = _plan(cap=inv.SearchCapability(position_probe=True, arc_index=True,
                                          aspect_span_solver=True))
    digest, out = _write(am5, store, sky, "5.7", plan)
    assert out["obligations"] == len(plan.obligations) and out["pins"] == 5
    row = am5.execute(
        "SELECT inventory_digest, ledger_digest, finalized_at IS NOT NULL, input_digest"
        " FROM public.ka_gochara_search_inventory WHERE generation = '5.7'").fetchone()
    assert row[0] == out["inventory_digest"] and row[1] == out["ledger_digest"]
    assert row[2] is True and row[3] == digest
    n_ob = am5.execute("SELECT count(*) FROM public.ka_gochara_search_obligation"
                       " WHERE generation = '5.7'").fetchone()[0]
    n_iv = am5.execute("SELECT count(*) FROM public.ka_gochara_search_interval"
                       " WHERE generation = '5.7' AND state = 'searched_complete'").fetchone()[0]
    assert n_ob == len(plan.obligations)
    assert n_iv == sum(1 for i in plan.intervals if i.state == "searched_complete")
    facts = store.finalised_class_facts(CHART_ID, "5.7", "marriage")
    assert facts["relations"] == plan.relations and facts["missing_inputs"] == 0
    assert facts["horizon"] == (H0, H1)


def test_a_rebuild_replaces_the_whole_chain_and_never_accretes(am5):
    store, sky, _ = _boot(am5, "5.7")
    first = _plan()
    _write(am5, store, sky, "5.7", first)
    second = _plan(cap=inv.SearchCapability(position_probe=False, arc_index=True))
    _, out = _write(am5, store, sky, "5.7", second)
    assert am5.execute("SELECT count(*) FROM public.ka_gochara_search_obligation"
                       " WHERE generation = '5.7'").fetchone()[0] == len(second.obligations)
    assert am5.execute("SELECT count(*) FROM public.ka_gochara_search_interval"
                       " WHERE generation = '5.7' AND state = 'missing_inputs'"
                       ).fetchone()[0] > 0
    assert out["inventory_digest"] != am5.execute(
        "SELECT public.ka_gochara_search_inventory_digest(%s::uuid,'5.7','nonexistent')",
        (CHART_ID,)).fetchone()[0]


def test_the_snapshot_needs_the_manifest_it_is_bound_to(am5):
    RuleRegistryStore(am5).seed()
    with am5.transaction():
        am5.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky = base._sky_convention_id(am5)
        with pytest.raises(SnapshotUnboundError):
            InventoryStore(am5).insert_snapshot(
                chart_id=CHART_ID, generation="5.8", convention_id=sky,
                consumed_fact_ids=[], consumed_dasha_row_ids=[])


def test_the_snapshot_vector_is_the_manifests_never_invented(am5):
    store, sky, _ = _boot(am5, "5.7", vector={"rule_registry": "zzz"})
    plan = _plan()
    _write(am5, store, sky, "5.7", plan)
    stored = am5.execute("SELECT input_generation_vector FROM"
                         " public.ka_gochara_search_input_snapshot"
                         " WHERE generation = '5.7'").fetchone()[0]
    assert stored == {"rule_registry": "zzz"}


def test_the_independent_verifier_reproduces_the_builders_and_the_dbs_digest(am5):
    """The verifier shares no code with the builder: for P3 + P4 + the P5 exclusion its
    from-the-spec derivation must land on the DB's own inventory digest. A mismatch here
    means the two readings of the doctrine DISAGREE — the whole point of the second path."""
    from services.gochara_kernel import inventory_verifier as ver
    paths = [("P3", "1.0.0"), ("P4", "1.0.0"), ("P5", "1.0.0")]
    store, sky, _ = _boot(am5, "5.7")
    for cls in ("marriage", "bereavement", "career_entry", "separation"):
        plan = inv.plan_class_inventory(
            event_class=cls, chart=CHART, horizon=(H0, H1), sealed_paths=paths,
            capability=FULL, path_exclusions={"P5": P5_EXCL})
        _write(am5, store, sky, "5.7", plan)
        db_digest = am5.execute(
            "SELECT inventory_digest FROM public.ka_gochara_search_inventory"
            " WHERE generation = '5.7' AND event_class = %s", (cls,)).fetchone()[0]
        out = ver.rederive_inventory_digest(
            am5, chart_id=CHART_ID, generation="5.7", event_class=cls, sealed_paths=paths,
            path_exclusions={"p5": {"reason": "tier_withheld_by_ruling",
                                    "basis": "ruling:M20261001T121451-1a8d",
                                    "ruling_ref": "M20261001T121451-1a8d"}})
        assert out["obligations"] == sorted(o.canonical_bytes for o in plan.obligations), cls
        assert out["digest"] == db_digest, cls


def test_the_verifier_derives_every_included_p1_to_p4_pin_including_p2_and_matches_the_stored_digest(am5):
    """R8-4: the included-P2 inventory derivation exists — the independent verifier reproduces the stored digest
    of a plan that includes P1, P2, P3 and P4 (P5 held)."""
    from services.gochara_kernel import inventory_verifier as ver
    store, sky, _ = _boot(am5, "5.7")
    plan = _plan()
    assert {p.path_id for p in plan.pins if p.disposition == "included"} == {"P1", "P2", "P3", "P4"}
    _write(am5, store, sky, "5.7", plan)
    res = ver.rederive_inventory_digest(
        am5, chart_id=CHART_ID, generation="5.7", event_class="marriage", sealed_paths=SEALED,
        path_exclusions={"p5": {"reason": "tier_withheld_by_ruling", "basis": "ruling:M20261001T121451-1a8d",
                                "ruling_ref": "M20261001T121451-1a8d"}})
    assert res["digest"] == store.finalised_class_facts(CHART_ID, "5.7", "marriage")["inventory_digest"]


def test_the_verifier_refuses_what_it_cannot_derive_and_writes_no_row(am5):
    from services.gochara_kernel import inventory_verifier as ver
    store, sky, _ = _boot(am5, "5.8")
    plan = inv.plan_class_inventory(event_class="marriage", chart=CHART, horizon=(H0, H1), sealed_paths=SEALED,
                                    capability=FULL, dasha_rows=DASHA, path_exclusions={})   # P5 INCLUDED
    assert "P5" in {p.path_id for p in plan.pins if p.disposition == "included"}
    _write(am5, store, sky, "5.8", plan)
    with pytest.raises(ver.Unverifiable, match="p5"):
        ver.rederive_inventory_digest(
            am5, chart_id=CHART_ID, generation="5.8", event_class="marriage", sealed_paths=SEALED,
            path_exclusions={})
    assert am5.execute("SELECT count(*) FROM public.ka_gochara_search_inventory_verification"
                       ).fetchone()[0] == 0


def test_a_verification_row_that_differs_from_the_stored_digest_blocks_the_seal(am5):
    from services.gochara_kernel import inventory_verifier as ver
    paths = [("P3", "1.0.0"), ("P4", "1.0.0"), ("P5", "1.0.0")]
    store, sky, _ = _boot(am5, "5.9")
    plan = inv.plan_class_inventory(
        event_class="marriage", chart=CHART, horizon=(H0, H1), sealed_paths=paths,
        capability=FULL, path_exclusions={"P5": P5_EXCL})
    _write(am5, store, sky, "5.9", plan)
    with am5.transaction():
        am5.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        am5.execute("SELECT public.ka_gochara_lock_global_shared()")
        ver.write_verification(am5, chart_id=CHART_ID, generation="5.9",
                               event_class="marriage", rederived_digest="0" * 64)
        gk_ledger.publish(am5, CHART_ID, "5.9")
        found = {r[1] for r in am5.execute(
            "SELECT * FROM public.ka_gochara_search_completeness_violations(%s::uuid,'5.9')",
            (CHART_ID,)).fetchall()}
    assert "verification_missing_or_mismatch" in found


def test_the_verifier_imports_nothing_from_the_builder():
    import ast
    src = (Path(__file__).resolve().parents[3] / "services" / "gochara_kernel"
           / "inventory_verifier.py").read_text()
    imported = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom):
            imported.add((node.module or "") if node.level == 0 else "." * node.level + (node.module or ""))
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    forbidden = ("evaluator", "inventory", "inventory_store", "substrate", "targets",
                 "record_store", "gochara_rules", "gochara_kernel")
    bad = {m for m in imported if any(f in m.replace("inventory_verifier", "") for f in forbidden)}
    assert not bad, f"the verifier must be independent of the builder: {bad}"
    # stdlib only (the aspect-to-span re-derivation needs `datetime.timedelta`)
    assert imported <= {"__future__", "hashlib", "typing", "decimal", "datetime"}, imported


def test_the_seal_check_sees_exactly_what_is_missing_after_the_builder_alone(am5):
    """Builder only (no coverage partition, no verifier): the database's own seal-time
    function must report ONLY those two absences — not a digest, commitment, coverage or
    input fault. (A publication row must be `published` for the manifest-bound checks.)"""
    store, sky, _ = _boot(am5, "5.7")
    plan = _plan(cap=inv.SearchCapability(position_probe=True, arc_index=True,
                                          aspect_span_solver=True))
    _write(am5, store, sky, "5.7", plan)
    with am5.transaction():
        am5.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(am5, CHART_ID, "5.7")
        am5.execute("SELECT public.ka_gochara_lock_global_shared()")
        found = {r[1] for r in am5.execute(
            "SELECT * FROM public.ka_gochara_search_completeness_violations(%s::uuid, '5.7')",
            (CHART_ID,)).fetchall()}
    assert found == {"inventory_without_partition", "verification_missing_or_mismatch"}, found


def test_an_unsolved_aspect_to_span_search_blocks_the_seal_by_name(am5):
    """The honest capability (no aspect-to-span solver) leaves those obligations
    `missing_inputs`; the database's seal-time function reports it — the generation cannot seal
    on a search that was never run (CLAUDE.md §N.8)."""
    store, sky, _ = _boot(am5, "5.89")
    _write(am5, store, sky, "5.89", _plan())            # the writer's real capability
    with am5.transaction():
        am5.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(am5, CHART_ID, "5.89")
        am5.execute("SELECT public.ka_gochara_lock_global_shared()")
        found = {r[1] for r in am5.execute(
            "SELECT * FROM public.ka_gochara_search_completeness_violations(%s::uuid, '5.89')",
            (CHART_ID,)).fetchall()}
    assert "missing_inputs_present" in found, found


def test_a_sealed_generation_is_refused_before_any_delete():
    class Conn:
        def __init__(self):
            self.sql = []

        def execute(self, sql, params=None):
            self.sql.append(sql)

            class R:
                rowcount = 0

                def fetchone(self_):
                    return (True,)
            return R()

    c = Conn()
    with pytest.raises(rs.SealedGenerationError, match="SEALED"):
        InventoryStore(c).delete_generation_inventory(CHART_ID, "5.0")
    assert not any(s.startswith("DELETE") for s in c.sql)


# ── P1 under the AM-11 role-token form ───────────────────────────────────────

def _p1_obs(plan):
    (p1,) = [p for p in plan.pins if p.path_id == "P1"]
    return p1, list(p1.obligations)


def test_p1_obligation_agents_are_the_role_tokens_and_records_keep_concrete_grahas():
    plan = _plan()
    p1, obs = _p1_obs(plan)
    assert p1.disposition == "included"
    roles = [o for o in obs if o.agent.startswith("period_lord:")]
    delivery = [o for o in obs if not o.agent.startswith("period_lord:")]
    assert {o.agent for o in roles} == {"period_lord:md", "period_lord:ad", "period_lord:pd"}
    assert {o.relation for o in obs} == {"residence"}              # P1's transit geometry
    assert not any(not o.transit for o in obs)                       # natal rows: not obligations
    for p in plan.pins:                                              # every other path: concrete
        if p.path_id != "P1":
            assert not any(o.agent.startswith("period_lord:") for o in p.obligations)
    shapes = {(o.relation, o.object_role, o.target) for o in roles}
    assert len(roles) == 3 * len(shapes)                             # the same geometry per role
    # XX.38 (steward M…053914): the Sun/Jupiter DELIVERY searches are concrete-agent obligations — written out
    # literally here (sign numbers: Aries 1 … Pisces 12), not derived from the code under test
    assert {(o.agent, o.target) for o in delivery} == (
        {("sun", f"span:{n}") for n in (1, 2, 4, 6, 7, 8, 10, 12)}
        | {("jupiter", f"span:{n}") for n in (1, 2, 6, 7, 10, 12)})
    assert all(o.object_role == "period_lord" and o.frame == "dasha_lord" for o in delivery)


def test_the_xx38_delivery_obligations_cover_the_whole_horizon_not_a_period_cut():
    plan = _plan()
    _p1, obs = _p1_obs(plan)
    for o in (x for x in obs if not x.agent.startswith("period_lord:")):
        ivs = [(iv.start, iv.end) for iv in plan.intervals if iv.ob_id == o.ob_id]
        assert ivs == [(H0, H1)], (o.agent, o.target)


def test_p1_intervals_are_cut_at_the_pinned_dasha_rows_with_the_resolved_agent():
    plan = _plan()
    _p1, obs = _p1_obs(plan)

    def cuts(role):
        ob = next(o for o in obs if o.agent == f"period_lord:{role}")
        return [(iv.start, iv.end, iv.detail["resolved_agent"], iv.detail["dasha_row_id"],
                 iv.state) for iv in sorted(plan.intervals, key=lambda i: i.start)
                if iv.ob_id == ob.ob_id]

    assert cuts("md") == [(H0, H1, "saturn", str(uuid.UUID(int=1)), "searched_complete")]
    assert cuts("ad") == [
        (H0, _dt(2025, 2, 1), "venus", str(uuid.UUID(int=2)), "searched_complete"),
        (_dt(2025, 2, 1), H1, "sun", str(uuid.UUID(int=3)), "searched_complete")]
    assert cuts("pd") == [
        (H0, _dt(2025, 1, 15), "mars", str(uuid.UUID(int=4)), "searched_complete"),
        (_dt(2025, 1, 15), _dt(2025, 2, 1), "rahu", str(uuid.UUID(int=5)), "searched_complete"),
        (_dt(2025, 2, 1), H1, "jupiter", str(uuid.UUID(int=6)), "searched_complete")]


def test_a_dasha_gap_is_a_missing_inputs_interval_never_silently_covered():
    rows = [r for r in DASHA if r.row_id != str(uuid.UUID(int=5))]
    plan = _plan(dasha_rows=rows)
    _p1, obs = _p1_obs(plan)
    pd = next(o for o in obs if o.agent == "period_lord:pd")
    gaps = [iv for iv in plan.intervals if iv.ob_id == pd.ob_id and iv.state == "missing_inputs"]
    assert [(g.start, g.end) for g in gaps] == [(_dt(2025, 1, 15), _dt(2025, 2, 1))]
    assert gaps[0].detail == {"resolved_agent": None, "dasha_row_id": None}


def test_p1_without_the_pinned_rows_or_with_a_subsecond_boundary_is_blocked_by_name():
    with pytest.raises(inv.InventoryBlocked, match="P1"):
        _plan(dasha_rows=None)
    # a fractional boundary INSIDE the horizon (the AD change on 2025-02-01); one before it
    # is clipped away and never reaches 1206's whole-second CHECK
    frac = [r if r.row_id != DASHA[2].row_id else inv.DashaRow(
        r.row_id, r.level, r.lord, datetime(2025, 2, 1, 0, 0, 0, 500, tzinfo=UTC), r.end)
        for r in DASHA]
    with pytest.raises(inv.InventoryBlocked, match="whole-second"):
        _plan(dasha_rows=frac)


def test_the_standing_rulings_are_the_exclusions_the_planner_is_given():
    paths, h_unknown = inv.standing_exclusions()
    assert paths["P5"].reason == "tier_withheld_by_ruling"
    assert paths["P5"].ruling_ref == "ST-P5-HOLD-20261001"
    assert paths["P5"].basis == "ruling:ST-P5-HOLD-20261001"
    assert (h_unknown.reason, h_unknown.ruling_ref) == ("inputs_unavailable",
                                                        "ST-H-UNKNOWN-20261002")
    from services.gochara_rules.registry import signature_houses
    unknown = [c for c in ev.ROW_MEMBERSHIP
               if c != "birth_anchor" and signature_houses(c, CHART) is None]
    for cls in unknown:       # the ruling covers P1/P3/P4 ONLY — P2 still plans
        plan = inv.plan_class_inventory(
            event_class=cls, chart=CHART, horizon=(H0, H1), sealed_paths=SEALED,
            capability=FULL, path_exclusions=paths, h_unknown_exclusion=h_unknown,
            dasha_rows=DASHA)
        by = {p.path_id: p for p in plan.pins}
        assert {pid for pid, p in by.items() if p.disposition == "excluded"} == {
            "P1", "P3", "P4", "P5"}, cls
        assert by["P2"].disposition in ("included", "computed_empty")


def test_role_token_interval_detail_is_stored_verbatim(am5):
    store, sky, _ = _boot(am5, "5.11")
    _write(am5, store, sky, "5.11", _plan())
    rows = am5.execute(
        "SELECT i.detail FROM public.ka_gochara_search_interval i"
        " JOIN public.ka_gochara_search_obligation o USING (chart_id, generation, event_class, ob_id)"
        " WHERE i.generation = '5.11' AND o.agent = 'period_lord:ad'").fetchall()
    assert {r[0]["resolved_agent"] for r in rows} == {"venus", "sun"}


def test_the_verifier_reproduces_the_inventory_and_ledger_digests_with_p1_role_tokens(am5):
    """P1 under the role-token form, from-the-spec: the verifier's inventory digest equals
    the DB's AND its re-derived LEDGER digest (cuts + resolved agents from the snapshot's
    consumed daśā rows) equals the stored one — the only independent check on the cuts."""
    from services.gochara_kernel import inventory_verifier as ver
    paths = [("P1", "1.0.0"), ("P3", "1.0.0"), ("P4", "1.0.0"), ("P5", "1.0.0")]
    ruled = {"p5": {"reason": "tier_withheld_by_ruling", "basis": "ruling:ST-P5-HOLD-20261001",
                    "ruling_ref": "ST-P5-HOLD-20261001"}}
    store, sky, _ = _boot(am5, "5.12")
    p5, hu = inv.standing_exclusions()
    for cls in ("marriage", "bereavement", "separation"):
        plan = inv.plan_class_inventory(
            event_class=cls, chart=CHART, horizon=(H0, H1), sealed_paths=paths,
            capability=FULL, path_exclusions=p5, h_unknown_exclusion=hu, dasha_rows=DASHA)
        _write(am5, store, sky, "5.12", plan)
        db_inv, db_led = am5.execute(
            "SELECT inventory_digest, ledger_digest FROM public.ka_gochara_search_inventory"
            " WHERE generation = '5.12' AND event_class = %s", (cls,)).fetchone()
        out = ver.rederive_inventory_digest(
            am5, chart_id=CHART_ID, generation="5.12", event_class=cls, sealed_paths=paths,
            path_exclusions=ruled)
        assert out["obligations"] == sorted(o.canonical_bytes for o in plan.obligations), cls
        assert out["digest"] == db_inv, cls
        led = ver.rederive_ledger_digest(
            am5, chart_id=CHART_ID, generation="5.12", event_class=cls,
            obligations=out["obligations"],
            capability={"position_probe": True, "arc_index": True})
        assert led == db_led, cls


def test_the_verifier_ledger_check_catches_a_wrong_cut_that_sql_cannot(am5):
    """SQL recomputes the ledger digest from the stored rows, so a wrongly-CUT but
    internally consistent ledger passes every SQL check. The verifier's own derivation
    does not."""
    from services.gochara_kernel import inventory_verifier as ver
    paths = [("P1", "1.0.0"), ("P5", "1.0.0")]
    store, sky, _ = _boot(am5, "5.13")
    p5, hu = inv.standing_exclusions()
    plan = inv.plan_class_inventory(
        event_class="marriage", chart=CHART, horizon=(H0, H1), sealed_paths=paths,
        capability=FULL, path_exclusions=p5, h_unknown_exclusion=hu,
        dasha_rows=[r for r in DASHA if r.level != 2] + [
            _row(2, 2, "venus", _dt(2024, 12, 1), _dt(2025, 4, 1))])   # AD cut at the wrong place
    _write(am5, store, sky, "5.13", plan)
    db_led = am5.execute("SELECT ledger_digest FROM public.ka_gochara_search_inventory"
                         " WHERE generation = '5.13'").fetchone()[0]
    assert db_led      # SQL is satisfied: it only recomputes what was stored
    out = ver.rederive_inventory_digest(
        am5, chart_id=CHART_ID, generation="5.13", event_class="marriage", sealed_paths=paths,
        path_exclusions={"p5": {"reason": "tier_withheld_by_ruling",
                                "basis": "ruling:ST-P5-HOLD-20261001",
                                "ruling_ref": "ST-P5-HOLD-20261001"}})
    # the snapshot consumed the (wrong) row ids the builder was handed in `_write` — the
    # verifier re-derives from the REAL pinned rows in chart_dashas, which disagree
    real = ver.rederive_ledger_digest(
        am5, chart_id=CHART_ID, generation="5.13", event_class="marriage",
        obligations=out["obligations"], capability={"position_probe": True, "arc_index": True})
    assert real != db_led


# ── the accepted 1206 v1.1/v1.2 contract points this writer depends on ───────

def test_the_live_input_digests_are_chart_keyed_and_the_dasha_ids_are_uuids(am5):
    """1206 v1.1 R4: rows are keyed by (chart, id) — the chart is the first argument — and the
    snapshot's `consumed_dasha_row_ids` is uuid[]. A digest asked for ANOTHER chart sees none of
    this chart's rows (every id MISSING), so it differs."""
    store, sky, _ = _boot(am5, "5.80")
    _write(am5, store, sky, "5.80", _plan())
    snap = am5.execute(
        "SELECT consumed_dasha_row_ids, l1_facts_digest, dasha_digest FROM"
        " public.ka_gochara_search_input_snapshot WHERE generation = '5.80'").fetchone()
    assert [str(x) for x in snap[0]] == sorted(DASHA_IDS)            # uuid[] round trip
    other = str(uuid.UUID(int=0xDEAD))
    assert am5.execute("SELECT public.ka_gochara_search_l1_facts_digest(%s::uuid, %s::text[])",
                       (CHART_ID, sorted(FACT_IDS))).fetchone()[0] == snap[1]
    assert am5.execute("SELECT public.ka_gochara_search_l1_facts_digest(%s::uuid, %s::text[])",
                       (other, sorted(FACT_IDS))).fetchone()[0] != snap[1]
    assert am5.execute("SELECT public.ka_gochara_search_dasha_digest(%s::uuid, %s::uuid[])",
                       (other, sorted(DASHA_IDS))).fetchone()[0] != snap[2]


def test_an_empty_ledger_is_input_bound_and_the_verifier_derives_the_same_preimage(am5):
    """1206 v1.1: the ledger_digest preimage starts with `input=<input_digest>`, so even a class
    with NO obligations has a digest that changes with the snapshot — and the independent verifier
    derives that exact preimage (an EMPTY ledger included)."""
    import hashlib
    from services.gochara_kernel import inventory_verifier as ver
    store, sky, _ = _boot(am5, "5.81")
    empty = inv.ClassInventory(event_class="marriage", horizon=(H0, H1), pins=(), intervals=())
    digest, out = _write(am5, store, sky, "5.81", empty)
    expected = hashlib.sha256(f"input={digest}".encode()).hexdigest()
    assert out["ledger_digest"] == expected
    assert ver.rederive_ledger_digest(
        am5, chart_id=CHART_ID, generation="5.81", event_class="marriage",
        obligations=[], capability={"position_probe": True, "arc_index": True}) == expected
    # input-bound: a different snapshot (a different fact set) changes the empty ledger's digest
    with am5.transaction():
        am5.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        store.delete_generation_inventory(CHART_ID, "5.81")
        digest2 = store.insert_snapshot(
            chart_id=CHART_ID, generation="5.81", convention_id=sky,
            consumed_fact_ids=FACT_IDS[:-1], consumed_dasha_row_ids=DASHA_IDS)
        out2 = store.write_class_inventory(
            chart_id=CHART_ID, generation="5.81", plan=empty, input_digest=digest2)
    assert digest2 != digest and out2["ledger_digest"] != out["ledger_digest"]


def test_a_snapshot_not_bound_to_the_publications_bridged_convention_is_refused(am5):
    """1206 v1.1 R2: the snapshot's sky convention must be the one the publication's legacy
    convention is bridged to (immutable 1:1 bridge) — anything else is refused by the database."""
    import psycopg
    store, sky, _ = _boot(am5, "5.82")
    with pytest.raises(psycopg.errors.RaiseException, match="R2"):
        with am5.transaction():
            am5.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
            store.delete_generation_inventory(CHART_ID, "5.82")
            store.insert_snapshot(
                chart_id=CHART_ID, generation="5.82", convention_id="sha256:" + "ab" * 32,
                consumed_fact_ids=FACT_IDS, consumed_dasha_row_ids=DASHA_IDS)


# ── no record ahead of the inventory (steward M…053914) ──────────────────────────────────────────────

@pytest.mark.parametrize("cls", ["marriage", "bereavement", "career_entry", "illness_acute"])
def test_every_p1_transit_record_edge_is_obliged_by_the_inventory(cls):
    """Every P1 transit edge the writer can mint a record for is covered by an inventory obligation: an OWN-form edge
    (agent = anchor lord) by the role-token obligation of its anchor level on the same geometry; an XX.38 edge
    (agent != anchor lord) by a CONCRETE-agent obligation on the same geometry. Before this, the XX.38 searches were
    carried by records the inventory never obliged."""
    from services.gochara_kernel import evaluator as ev
    plan = _plan(cls)
    (p1,) = [p for p in plan.pins if p.path_id == "P1"]
    if p1.disposition != "included":
        pytest.skip(f"{cls}: P1 is {p1.disposition} (H unknown)")
    have = {(o.agent, o.relation, o.target, o.frame, o.person) for o in p1.obligations}
    for e in ev.enumerate_edges(cls, "P1", CHART):
        if not e.transit:
            continue
        frame = e.frame_kind if e.frame_arg is None else f"{e.frame_kind}:{e.frame_arg}"
        agent = f"period_lord:{e.period_anchor_level}" if e.agent == e.period_anchor_lord else e.agent
        assert (agent, e.relation, e.obj.canonical_target, frame, e.affected_person) in have, (
            e.agent, e.period_anchor_lord, e.period_anchor_level, e.obj.canonical_target)


def test_mutation_a_planner_without_the_delivery_obligations_leaves_records_ahead_of_the_inventory(monkeypatch):
    """The same property fails when the XX.38 obligations are dropped — reinstating the defect."""
    from services.gochara_kernel import evaluator as ev
    real = inv._plan_p1

    def without_delivery(*a, **k):
        obs, ivs = real(*a, **k)
        keep = [o for o in obs if o.agent.startswith("period_lord:")]
        ids = {o.ob_id for o in keep}
        return tuple(keep), [i for i in ivs if i.ob_id in ids]
    monkeypatch.setattr(inv, "_plan_p1", without_delivery)
    plan = _plan("marriage")
    (p1,) = [p for p in plan.pins if p.path_id == "P1"]
    have = {(o.agent, o.target) for o in p1.obligations}
    missing = [e for e in ev.enumerate_edges("marriage", "P1", CHART)
               if e.transit and e.agent != e.period_anchor_lord and (e.agent, e.obj.canonical_target) not in have]
    assert missing, "the mutant must leave XX.38 edges unobliged"
