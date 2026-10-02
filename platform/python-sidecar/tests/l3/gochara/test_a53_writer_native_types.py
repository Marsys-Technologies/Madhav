"""A5.3 writerbase_conformance — the writer chain with the RUNNER'S NATIVE TYPES.

The A2.5 review (ASTRA A1) found a writer green on tuple rows and string chart ids that crashed on
the governed runner's real inputs: `chart_id` arrives as a `uuid.UUID` and `ctx.db_conn` is a
psycopg `dict_row` connection. The same chain as `test_a53_am5_writer.py` is driven here with
exactly those two types, end to end through the writer's own substeps on a throwaway database.
"""
from __future__ import annotations

import uuid

import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel.rule_registry import RuleRegistryStore

from .test_a53_inventory import CHART_ID, H0, H1, create_am5_database, drop_am5_database

GEN = writer_mod.GENERATION


@pytest.fixture()
def native(monkeypatch, tmp_path):
    import psycopg
    from psycopg.rows import dict_row
    admin, name, dsn = create_am5_database("am5n")
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3, row_factory=dict_row)
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", lambda body, jd, ephe: (10.0, 2))
    RuleRegistryStore(conn).seed()
    w = writer_mod.GocharaV5Writer()
    from .test_a53_am5_writer import make_ephe
    ephe = make_ephe(tmp_path)

    def step(key):
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-native", db_conn=conn,
                          config={"chart_id": uuid.UUID(CHART_ID), "horizon": (H0, H1), "ephe_path": ephe},
                          dry_run=False)
        with conn.transaction():
            return w.run_substep(ctx, SubStep(key=key, label=key))
    try:
        yield step, conn, w
    finally:
        conn.close()
        drop_am5_database(admin, name)


def test_the_pinned_chart_guard_accepts_the_runners_uuid_for_the_pinned_chart_and_refuses_others():
    writer_mod._require_pinned_chart(uuid.UUID(writer_mod.PINNED_CHART_ID))      # the runner's type
    writer_mod._require_pinned_chart(writer_mod.PINNED_CHART_ID)                # the CLI's type
    with pytest.raises(writer_mod.ChartRefusal):
        writer_mod._require_pinned_chart(uuid.UUID("00000000-0000-4000-8000-0000000000b2"))
    with pytest.raises(writer_mod.ChartRefusal):
        writer_mod._require_pinned_chart("00000000-0000-4000-8000-0000000000b2")


def test_the_am5_chain_runs_with_a_uuid_chart_and_a_dict_row_connection(native):
    step, conn, w = native
    step(writer_mod.CONVENTION_SUBSTEP)
    assert "candidate manifest" in step(writer_mod.MANIFEST_SUBSTEP).notes
    snap = step(writer_mod.SNAPSHOT_SUBSTEP)
    assert "6 daśā rows" in snap.notes and "10 L1 facts" in snap.notes
    inv = step("inventory:marriage")
    assert "obligations" in inv.notes
    assert step("coverage:marriage").rows_inserted == 1
    ver = step("verify:marriage")
    assert ver is not None
    n = conn.execute(
        "SELECT count(*) AS n FROM public.ka_gochara_search_inventory WHERE generation = %s",
        (GEN,)).fetchone()["n"]
    assert n == 1


def test_the_rules_convention_and_record_substeps_run_with_native_types(native):
    """The remaining non-geometry substep kinds, same two native types. (The Swiss-backed body
    substeps are exercised by the writer's own suite; this proves the row-shape/UUID seam for the
    rules, convention, manifest, snapshot, inventory, coverage, record and verify kinds.)"""
    step, conn, w = native
    assert "seeded + sealed" in step(writer_mod.RULES_SUBSTEP).notes     # the fixture seeded: idempotent reuse
    step(writer_mod.CONVENTION_SUBSTEP)
    step(writer_mod.MANIFEST_SUBSTEP)
    step(writer_mod.SNAPSHOT_SUBSTEP)
    step("inventory:marriage")
    step("coverage:marriage")
    rec = step("record:marriage:P3")
    assert rec is not None and rec.asset_id == writer_mod.ASSET_ID
    assert step("verify:marriage") is not None


def test_plan_substeps_and_run_with_native_types_and_dry_run_writes_nothing(native):
    step, conn, w = native
    ctx = writer_mod.ContextSpec(
        asset_id=writer_mod.ASSET_ID, build_id="b-native-dry", db_conn=conn,
        config={"chart_id": uuid.UUID(CHART_ID), "horizon": (H0, H1)}, dry_run=True)
    plan = w.plan_substeps(ctx)
    assert plan and plan[0].key == writer_mod.RULES_SUBSTEP
    before = conn.execute("SELECT count(*) AS n FROM public.ka_gochara_search_inventory").fetchone()["n"]
    for st in plan[:6]:
        res = w.run_substep(ctx, st)
        assert "dry_run" in res.notes and res.rows_inserted == 0
    assert conn.execute("SELECT count(*) AS n FROM public.ka_gochara_search_inventory"
                        ).fetchone()["n"] == before
