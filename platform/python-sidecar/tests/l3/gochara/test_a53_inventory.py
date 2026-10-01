"""A5.3 — AM-5 search-inventory planner + store against migration 1206 (PR #2867).

Pure planner tests need no database. The store tests run on a throwaway database with the
REAL chain 1081/1152–1157 + 1206 applied verbatim (L1 tables stubbed minimally). 1206's
shapes are not frozen until the Codex verdict — these tests are where a shape change shows.
"""
from __future__ import annotations

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
SEALED = [("P1", "1.0.0"), ("P2", "1.0.0"), ("P3", "1.0.0"), ("P4", "1.0.0"), ("P5", "1.0.0")]
FULL = inv.SearchCapability(position_probe=True, arc_index=True)
P5_EXCL = inv.Exclusion("tier_withheld_by_ruling", "ruling:M20261001T121451-1a8d",
                        "M20261001T121451-1a8d")
H_UNKNOWN_EXCL = inv.Exclusion("inputs_unavailable", "ruling:TEST-H-UNKNOWN", "TEST-H-UNKNOWN")


def _plan(cls="marriage", cap=FULL, **kw):
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
    full = _plan()
    assert {iv.state for iv in full.intervals} == {"searched_complete"}
    no_probe = _plan(cap=inv.SearchCapability(position_probe=False, arc_index=True))
    no_arc = _plan(cap=inv.SearchCapability(position_probe=True, arc_index=False))
    by_ob = lambda plan: {o.ob_id: o for o in plan.obligations}  # noqa: E731
    for plan, relations in ((no_probe, {"residence"}), (no_arc, {"conjunction", "aspect"})):
        obs = by_ob(plan)
        missing = {obs[iv.ob_id].relation for iv in plan.intervals
                   if iv.state == "missing_inputs" and obs[iv.ob_id].transit}
        assert missing == relations
        # an atemporal natal fact is evaluated from L1 whatever the solver set
        assert all(iv.state == "searched_complete" for iv in plan.intervals
                   if not obs[iv.ob_id].transit)


def test_every_interval_spans_the_class_horizon_and_the_relations_are_the_obligations():
    plan = _plan()
    assert all((iv.start, iv.end) == (H0, H1) for iv in plan.intervals)
    assert {iv.ob_id for iv in plan.intervals} == {o.ob_id for o in plan.obligations}
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

@pytest.fixture(scope="module")
def _am5_dsn():
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    try:
        admin = psycopg.connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    name = f"{DB_PREFIX}am5_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    dsn = make_conninfo(ADMIN_DSN, dbname=name)
    try:
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE public.charts (id uuid PRIMARY KEY)")
            cur.execute("CREATE TABLE public._migrations_applied"
                        " (filename text PRIMARY KEY, applied_at timestamptz DEFAULT now())")
            cur.execute("CREATE TABLE public.chart_facts (fact_id text PRIMARY KEY,"
                        " chart_id uuid, fact_category text, fact_subject text, fact_key text,"
                        " fact_value_num double precision, created_at timestamptz DEFAULT now())")
            cur.execute("CREATE TABLE public.chart_dashas (dasha_row_id uuid PRIMARY KEY,"
                        " chart_id uuid, system_id text, level_n int, lord_graha text,"
                        " start_iso timestamptz, end_iso timestamptz,"
                        " computed_at timestamptz DEFAULT now())")
            for fname in MIGRATION_CHAIN + ["1206_gochara_search_inventory_completeness.sql"]:
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
                cur.execute("INSERT INTO public.chart_facts(fact_id, chart_id, fact_category,"
                            " fact_subject, fact_key, fact_value_num)"
                            " VALUES (%s,%s,'graha_position',%s,'longitude_sidereal',%s)",
                            (f"fact-{sname}", CHART_ID, sname, lon))
            cur.execute("INSERT INTO public.chart_dashas(dasha_row_id, chart_id, system_id,"
                        " level_n, lord_graha, start_iso, end_iso) VALUES"
                        " (%s,%s,'vimshottari',1,'Saturn','2020-01-01','2030-01-01')",
                        (str(uuid.UUID(int=1)), CHART_ID))
        conn.close()
        yield dsn
    finally:
        assert name.startswith(DB_PREFIX)
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


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
            consumed_dasha_row_ids=[str(uuid.UUID(int=1))])
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
    plan = _plan()
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
    assert n_ob == n_iv == len(plan.obligations)
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


def test_the_verifier_refuses_what_it_cannot_derive_and_writes_no_row(am5):
    from services.gochara_kernel import inventory_verifier as ver
    store, sky, _ = _boot(am5, "5.7")
    plan = _plan()
    _write(am5, store, sky, "5.7", plan)          # includes P1 and P2
    with pytest.raises(ver.Unverifiable, match="P[12]|p[12]"):
        ver.rederive_inventory_digest(
            am5, chart_id=CHART_ID, generation="5.7", event_class="marriage",
            sealed_paths=SEALED,
            path_exclusions={"p5": {"reason": "tier_withheld_by_ruling",
                                    "basis": "ruling:M20261001T121451-1a8d",
                                    "ruling_ref": "M20261001T121451-1a8d"}})
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
    assert imported <= {"__future__", "hashlib", "typing", "decimal"}, imported


def test_the_seal_check_sees_exactly_what_is_missing_after_the_builder_alone(am5):
    """Builder only (no coverage partition, no verifier): the database's own seal-time
    function must report ONLY those two absences — not a digest, commitment, coverage or
    input fault. (A publication row must be `published` for the manifest-bound checks.)"""
    store, sky, _ = _boot(am5, "5.7")
    plan = _plan()
    _write(am5, store, sky, "5.7", plan)
    with am5.transaction():
        am5.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(am5, CHART_ID, "5.7")
        am5.execute("SELECT public.ka_gochara_lock_global_shared()")
        found = {r[1] for r in am5.execute(
            "SELECT * FROM public.ka_gochara_search_completeness_violations(%s::uuid, '5.7')",
            (CHART_ID,)).fetchall()}
    assert found == {"inventory_without_partition", "verification_missing_or_mismatch"}, found


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
