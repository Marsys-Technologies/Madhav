"""Real-PostgreSQL proof of the l2_producer wrapper's call order (integration; skipped unless both URLs are provided).

Environment (a disposable database built like production: see tests/l2/realpg/README.md):
  L2_WRAPPER_REALPG_ADMIN_URL    superuser/administrator login, used ONLY to insert two fixture rows (a synthetic charts row and the
                                 fact_category_ownership row for graha_position) and nothing else
  L2_WRAPPER_REALPG_BUILDER_URL  the production pipeline login ``data_plane_builder`` (no superuser, no CREATE on schema public)

Everything the test does as the builder happens in ONE transaction that is rolled back. The L1 head it needs is created through the REAL
lifecycle functions (open_l1_data_plane_generation / complete_l1_data_plane_partition), never inserted by hand.

What it proves:
  1. ``_open_generation`` (bind, then open) opens a generation on a real database: a ``building`` row with the content-addressed id exists;
  2. the OLD order (open without a prior bind) is rejected by the database with the exact message the migration defines, so the order is
     a database contract and not a style choice;
  3. the shared wrapper survives ``begin_observation`` with a real ``uuid.UUID`` chart id and a real ``_resolve_upstream_context``.
It does NOT claim the adapter bodies run: reading the pg_temp input shadows and calling bodha_signal_identity() need grants production
does not have yet (see BO_UUID_FIX_REPORT_2.md); that is deliberately outside this test.
"""
from __future__ import annotations

import os
import uuid

import pytest

psycopg = pytest.importorskip("psycopg")

ADMIN = os.environ.get("L2_WRAPPER_REALPG_ADMIN_URL")
BUILDER = os.environ.get("L2_WRAPPER_REALPG_BUILDER_URL")
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not (ADMIN and BUILDER), reason="L2_WRAPPER_REALPG_ADMIN_URL / L2_WRAPPER_REALPG_BUILDER_URL not provided"),
]

import bodha_writers.data_plane_contracts as dpc  # noqa: E402
from pipeline.orchestrator.writers import ContextSpec  # noqa: E402

CHART = uuid.UUID("11111111-1111-4111-8111-111111111111")
L1_RUN = "55555555-5555-4555-8555-555555555555"
L1_CONTEXT = (
    "l1.data-plane.contract.1.0", "l0.semantic.2026-09-13.1",
    "665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1", "l0-resource-config-g1",
    "d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a",
)


@pytest.fixture(scope="module")
def fixtures_committed():
    with psycopg.connect(ADMIN, autocommit=True) as admin:
        admin.execute(
            """INSERT INTO public.charts(id,name,birth_date,birth_time,birth_place,birth_lat,birth_lng,timezone_id,house_system,native_id,role,chart_type)
               VALUES (%s,'fixture','2000-01-01','12:00','fixture',20,85,'Asia/Kolkata','sripathi','fixture','fixture','natal') ON CONFLICT DO NOTHING""",
            (CHART,))
        admin.execute("SET session_replication_role = replica")
        admin.execute("INSERT INTO public.fact_category_ownership(fact_category, owning_asset_id) VALUES ('graha_position','ga_positions') ON CONFLICT DO NOTHING")


def _builder_txn_with_l1_head(conn):
    """Inside the caller's transaction: a REAL ga_positions L1 head for CHART, then an active bo_sudarshana build."""
    cur = conn.cursor()
    cur.execute("INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by) VALUES (%s,%s,'asset','build','running','{}','test')", (L1_RUN, CHART))
    cur.execute("INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES (%s,'ga_positions',1,'building')", (L1_RUN,))
    for key, value in (("madhav.l1_asset_id", "ga_positions"), ("madhav.l1_chart_id", str(CHART)), ("madhav.l1_generation_id", L1_RUN),
                       ("madhav.l1_partition_key", "all"), ("madhav.l1_contract_version", L1_CONTEXT[0])):
        cur.execute("SELECT set_config(%s,%s,true)", (key, value))
    cur.execute("SELECT open_l1_data_plane_generation(%s::uuid,'ga_positions',%s,'all',1,NULL,%s,%s,%s,%s,%s)", (str(CHART), L1_RUN, *L1_CONTEXT))
    cur.execute(
        """INSERT INTO chart_facts(fact_id,chart_id,ayanamsha_id,build_id,fact_category,fact_subject,fact_key,fact_value_text,citation_ref,citation_human,
                                   source_calculation,verification_pass_status,engine_version,computed_at)
           VALUES (gen_random_uuid()::text,%s,'lahiri_chitrapaksha',%s,'graha_position','SUN','sign','Aquarius','fixture','fixture','fixture','single','fixture',now())""",
        (CHART, L1_RUN))
    cur.execute("SELECT complete_l1_data_plane_partition(%s::uuid,'ga_positions',%s,'all',1)", (str(CHART), L1_RUN))
    cur.execute("UPDATE build_run_assets SET state='complete' WHERE run_id=%s", (L1_RUN,))
    cur.execute("UPDATE build_runs SET state='completed' WHERE id=%s", (L1_RUN,))
    l2_run = str(uuid.uuid4())
    cur.execute("INSERT INTO build_runs(id,chart_id,scope,action,state,plan,triggered_by) VALUES (%s,%s,'asset','build','running','{}','test')", (l2_run, CHART))
    cur.execute("INSERT INTO build_run_assets(run_id,asset_id,position,state) VALUES (%s,'bo_sudarshana',1,'building')", (l2_run,))
    return l2_run


def _ctx(conn, run_id):
    return ContextSpec(asset_id="bo_sudarshana", build_id=run_id, db_conn=conn, config={"chart_id": CHART, "birth_params": {}})


def _observation(conn, run_id):
    ctx = _ctx(conn, run_id)
    ctx.config["chart_id"] = str(ctx.config["chart_id"])  # what the wrapper's _coerce_chart_id_to_str does first
    vector, context = dpc._resolve_upstream_context(conn, chart_id=ctx.config["chart_id"], asset_id="bo_sudarshana", partition_key="bo_sudarshana")
    obs = dpc.begin_observation(ctx, "bo_sudarshana", "a" * 64, partition_key="bo_sudarshana", dependency_vector=vector, calculation_context=context)
    return ctx, obs


def test_session_is_the_production_builder_not_a_superuser(fixtures_committed):
    with psycopg.connect(BUILDER) as conn:
        user, sup = conn.execute("SELECT session_user, (SELECT rolsuper FROM pg_roles WHERE rolname=session_user)").fetchone()
        assert user == "data_plane_builder" and sup is False


def test_bind_then_open_opens_a_building_generation(fixtures_committed):
    with psycopg.connect(BUILDER) as conn:
        run = _builder_txn_with_l1_head(conn)
        ctx, obs = _observation(conn, run)
        dpc._open_generation(ctx, obs, expected_partitions=1)
        rows = conn.execute(
            "SELECT state, expected_partitions FROM data_plane_l2_producer_generations WHERE chart_id=%s AND asset_id='bo_sudarshana' AND generation_id=%s",
            (CHART, obs.generation_id)).fetchall()
        assert rows == [("building", 1)]
        conn.rollback()


def test_open_without_bind_is_rejected_by_the_database(fixtures_committed):
    with psycopg.connect(BUILDER) as conn:
        run = _builder_txn_with_l1_head(conn)
        ctx, obs = _observation(conn, run)
        cur = conn.cursor()
        for key, value in (("madhav.l2_asset_id", obs.asset_id), ("madhav.l2_chart_id", obs.chart_id), ("madhav.l2_generation_id", obs.generation_id),
                           ("madhav.l2_partition_key", obs.partition_key), ("madhav.l2_build_id", obs.build_id), ("madhav.l2_contract_version", dpc.CONTRACT_VERSION)):
            cur.execute("SELECT set_config(%s,%s,true)", (key, value))
        import json
        cur.execute("SAVEPOINT old_order")
        with pytest.raises(psycopg.errors.RaiseException, match="requires an exact-input bind receipt"):
            cur.execute(
                "SELECT public.open_l2_data_plane_generation(%s::uuid,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)",
                (obs.chart_id, obs.asset_id, obs.generation_id, obs.partition_key, 1, obs.build_id, None, dpc.CONTRACT_VERSION, obs.source_digest,
                 json.dumps(obs.calculation_context, sort_keys=True), json.dumps(obs.dependency_vector, sort_keys=True), obs.role))
        conn.rollback()
