"""A5.3 — the AM-5 chain driven THROUGH THE WRITER's own substeps against migration 1206 on a
throwaway database: manifest → snapshot → inventory → coverage (aligned to the inventory) →
verify. Only the Swiss probe is faked; the planner, store, verifier, coverage writer, the
orchestrator-shaped transaction-per-substep and every SQL guard are production code."""
from __future__ import annotations

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import ledger as gk_ledger  # noqa: F401
from services.gochara_kernel.rule_registry import RuleRegistryStore

from . import test_a53_inventory as base
from .test_a53_inventory import (CHART_ID, H0, H1, create_am5_database,
                                 drop_am5_database)

GEN = writer_mod.GENERATION


@pytest.fixture()
def am5():
    """A FRESH database per test: the writer's generation label is fixed ('5.0') and one
    test publishes it."""
    import psycopg
    admin, name, dsn = create_am5_database("am5w")
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        yield conn
    finally:
        conn.close()
        drop_am5_database(admin, name)


@pytest.fixture()
def run(am5, monkeypatch):
    """One substep = one transaction, like the orchestrator; Swiss probe faked."""
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
    RuleRegistryStore(am5).seed()
    w = writer_mod.GocharaV5Writer()

    def step(key):
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-1", db_conn=am5,
                          config={"chart_id": CHART_ID, "horizon": (H0, H1)}, dry_run=False)
        with am5.transaction():
            return w.run_substep(ctx, SubStep(key=key, label=key))
    return step, am5


def _violations(conn):
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        conn.execute("SELECT public.ka_gochara_lock_global_shared()")
        return conn.execute(
            "SELECT event_class, violation FROM"
            " public.ka_gochara_search_completeness_violations(%s::uuid, %s)",
            (CHART_ID, GEN)).fetchall()


def test_the_chain_runs_through_the_writer_and_the_partition_aligns_with_the_inventory(run):
    step, conn = run
    step(writer_mod.CONVENTION_SUBSTEP)
    assert "candidate manifest" in step(writer_mod.MANIFEST_SUBSTEP).notes
    snap = step(writer_mod.SNAPSHOT_SUBSTEP)
    assert "6 daśā rows" in snap.notes and "10 L1 facts" in snap.notes
    inv = step("inventory:marriage")
    assert "obligations" in inv.notes and "P5:excluded" in inv.notes
    cov = step("coverage:marriage")
    assert cov.rows_inserted == 1
    # the partition is the SUMMARY of the stored inventory: same horizon, same relations
    part = conn.execute(
        "SELECT lower(completed_horizon), upper(completed_horizon), relations_searched"
        " FROM public.kala_gochara_coverage WHERE generation = %s"
        " AND partition_kind = 'event_class' AND partition_key = 'marriage'", (GEN,)).fetchone()
    facts = conn.execute(
        "SELECT lower(horizon), upper(horizon) FROM public.ka_gochara_search_inventory"
        " WHERE generation = %s AND event_class = 'marriage'", (GEN,)).fetchone()
    rels = [r[0] for r in conn.execute(
        "SELECT DISTINCT relation FROM public.ka_gochara_search_obligation"
        " WHERE generation = %s AND event_class = 'marriage' ORDER BY 1", (GEN,)).fetchall()]
    assert (part[0], part[1]) == facts and part[2] == rels
    assert "natal_fact" not in part[2]


def test_the_seal_check_then_reports_only_what_is_genuinely_unfinished(run):
    """After inventory + aligned coverage, `partition_overclaims` and every digest/commitment/
    input violation are GONE; what remains is the verifier's refusal for P2 (it cannot
    derive it yet) and the other 25 classes with no inventory."""
    step, conn = run
    for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP,
              writer_mod.SNAPSHOT_SUBSTEP, "inventory:marriage", "coverage:marriage"):
        step(k)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        gk_ledger.publish(conn, CHART_ID, GEN)
    found = {v for _c, v in _violations(conn)}
    assert "partition_overclaims" not in found
    assert not found & {"committed_set_mismatch", "inventory_digest_mismatch",
                        "obligation_uncovered", "missing_inputs_present",
                        "input_snapshot_drift", "input_snapshot_mismatch",
                        "input_vector_mismatch", "horizon_manifest_mismatch",
                        "registry_unaccounted_path", "inventory_not_finalised"}, found
    assert "verification_missing_or_mismatch" in found      # not verified yet


def test_the_verifier_refuses_a_class_with_a_path_it_cannot_derive_and_the_note_says_so(run):
    step, _ = run
    for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP,
              writer_mod.SNAPSHOT_SUBSTEP, "inventory:marriage"):
        step(k)
    res = step("verify:marriage")
    assert res.rows_inserted == 0 and "UNVERIFIED" in res.notes
    assert "P2" in res.notes or "p2" in res.notes


def test_an_h_unknown_class_plans_under_the_standing_ruling(run):
    step, conn = run
    for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP,
              writer_mod.SNAPSHOT_SUBSTEP):
        step(k)
    res = step("inventory:spiritual_turn")
    assert "P1:excluded" in res.notes and "P3:excluded" in res.notes and "P4:excluded" in res.notes
    rows = conn.execute(
        "SELECT path_id, exclusion_reason, ruling_ref FROM public.ka_gochara_search_path_pin"
        " WHERE generation = %s AND event_class = 'spiritual_turn' AND disposition = 'excluded'"
        " ORDER BY path_id", (GEN,)).fetchall()
    assert rows == [("P1", "inputs_unavailable", "ST-H-UNKNOWN-20261002"),
                    ("P3", "inputs_unavailable", "ST-H-UNKNOWN-20261002"),
                    ("P4", "inputs_unavailable", "ST-H-UNKNOWN-20261002"),
                    ("P5", "tier_withheld_by_ruling", "ST-P5-HOLD-20261001")]


def test_coverage_refuses_when_the_inventory_has_not_run(run):
    step, _ = run
    for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP,
              writer_mod.SNAPSHOT_SUBSTEP):
        step(k)
    res = step("coverage:marriage")
    assert res.rows_inserted == 0 and "no finalised search inventory" in res.notes


def test_a_rebuild_replaces_the_whole_chain_including_the_snapshot(run):
    step, conn = run
    for k in (writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP,
              writer_mod.SNAPSHOT_SUBSTEP, "inventory:marriage", "coverage:marriage"):
        step(k)
    before = conn.execute("SELECT count(*) FROM public.ka_gochara_search_obligation"
                          " WHERE generation = %s", (GEN,)).fetchone()[0]
    for k in (writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP,
              "inventory:marriage", "coverage:marriage"):
        step(k)                                  # the second build: no raise, no accretion
    assert conn.execute("SELECT count(*) FROM public.ka_gochara_search_obligation"
                        " WHERE generation = %s", (GEN,)).fetchone()[0] == before
