"""Real-PostgreSQL proof: a SHADOW-ONLY ROW CANNOT SATISFY a registry check after the wrapper returns (integration).

Same environment as ``test_l2_wrapper_real_pg.py`` (``L2_WRAPPER_REALPG_ADMIN_URL`` / ``L2_WRAPPER_REALPG_BUILDER_URL``, production role
model, session = ``data_plane_builder``). The bind-time shadows are owned by ``data_plane_l2_owner`` and unreadable by the builder in the
production ACLs (a separate finding), so the shadow in this test is a builder-owned temp table with the protected table's name: the same
name-resolution situation (``pg_temp`` first), reproduced without needing the missing grant.
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
from bodha_writers.data_plane_contracts import l2_producer  # noqa: E402
from pipeline.orchestrator.writers import ContextSpec  # noqa: E402

from .test_l2_wrapper_real_pg import CHART, _builder_txn_with_l1_head, fixtures_committed  # noqa: E402,F401


@pytest.fixture(autouse=True)
def _data_plane_build_path_on(monkeypatch):
    """N-165: the data-plane build path is OFF by default; this integration proof exercises the dormant machinery."""
    monkeypatch.setattr("ga_writers.data_plane_contracts.DATA_PLANE_BUILD_PATH_ENABLED", True)


CHECK = "SELECT EXISTS (SELECT 1 FROM bodha_msr_signals WHERE chart_id = %s AND signal_type_class = 'shadow_only_probe')"
MSR_INSERT = """INSERT INTO public.bodha_msr_signals(signal_id,chart_id,ayanamsha_id,build_id,signal_type_id,signal_type_class,
  signal_tradition,fact_kind,source_l1_asset,source_subsystem,configuration_jsonb,constituent_facts_array,deterministic_strength,
  verification_certainty,computed_salience,salience_formula_version,domains_affected_array,domain_salience_jsonb,active_duration_class,
  verification_pass_status,citation_ref,citation_human,computed_at,engine_version)
  VALUES(%s,%s,'lahiri_chitrapaksha',%s,'probe','real_row_probe','fixture','fixture','ga_positions','fixture','{}',ARRAY['fixture'],1,1,1,
  'fixture',ARRAY['fixture'],'{}','fixture','single','fixture','fixture',now(),'fixture')"""


def test_shadow_only_row_satisfies_the_check_until_the_wrapper_resets_resolution(fixtures_committed):
    with psycopg.connect(BUILDER) as conn:
        cur = conn.cursor()
        cur.execute("CREATE TEMP TABLE bodha_msr_signals ON COMMIT DROP AS SELECT * FROM public.bodha_msr_signals WITH NO DATA")
        cur.execute("INSERT INTO pg_temp.bodha_msr_signals(signal_id,chart_id,signal_type_class) VALUES (%s,%s,'shadow_only_probe')", (str(uuid.uuid4()), CHART))
        assert cur.execute(CHECK, (CHART,)).fetchone()[0] is True, "premise: the unqualified check reads the shadow row"
        dpc._resolve_unqualified_names_to_real_tables(ContextSpec(asset_id="x", build_id="b", db_conn=conn, config={}))
        assert cur.execute(CHECK, (CHART,)).fetchone()[0] is False, "after the reset a row that exists only in the shadow no longer satisfies the check"
        assert cur.execute("SELECT count(*) FROM pg_temp.bodha_msr_signals").fetchone()[0] == 1, "the shadow itself is untouched"
        conn.rollback()
        # SET LOCAL: transaction-local, the session default is back after the rollback
        assert conn.execute("SHOW search_path").fetchone()[0] != "public, pg_temp"


def test_real_wrapper_leaves_unqualified_names_on_the_real_table(fixtures_committed):
    """Through the REAL wrapper (bind, open, body, complete) as the production builder: the row the writer wrote is what an unqualified
    statement sees afterwards (before the fix it saw the empty bind-time shadow)."""
    class Probe:
        asset_id = "bo_sudarshana"

        def run(self, ctx):
            ctx.db_conn.execute(MSR_INSERT, (str(uuid.uuid4()), ctx.config["chart_id"], ctx.build_id))
            return type("R", (), {"rows_inserted": 1, "rows_updated": 0, "rows_skipped": 0, "notes": ""})()

    Wrapped = l2_producer("bo_sudarshana")(Probe)
    with psycopg.connect(BUILDER) as conn:
        run = _builder_txn_with_l1_head(conn)
        ctx = ContextSpec(asset_id="bo_sudarshana", build_id=run, db_conn=conn, config={"chart_id": CHART, "birth_params": {}})
        Wrapped().run(ctx)
        seen = conn.execute("SELECT count(*) FROM bodha_msr_signals WHERE chart_id=%s AND signal_type_class='real_row_probe'", (CHART,)).fetchone()[0]
        real = conn.execute("SELECT count(*) FROM public.bodha_msr_signals WHERE chart_id=%s AND signal_type_class='real_row_probe'", (CHART,)).fetchone()[0]
        assert (seen, real) == (1, 1)
        conn.rollback()


RESOLVES_TO_TEMP = "SELECT c.relnamespace = pg_my_temp_schema() FROM pg_class c WHERE c.oid = %s::regclass"


def test_second_wrapped_call_in_one_transaction_binds_and_reads_the_shadows_again(fixtures_committed):
    """Two contracted calls on ONE connection/transaction (a light writer's deferred-commit transaction): the first ends with the
    name-resolution reset, so without a reset at ENTRY the second call's body would resolve the protected names to the REAL tables while its
    own bind just created fresh shadows. The body records which schema ``chart_facts`` resolves to: the shadow (the temp schema) both times.
    ``regclass`` resolution needs no privilege on the table, so this runs under today's ACLs."""
    seen: list[tuple[str, bool]] = []

    class Probe:
        asset_id = "bo_sudarshana"

        def run(self, ctx):
            seen.append(("chart_facts", ctx.db_conn.execute(RESOLVES_TO_TEMP, ("chart_facts",)).fetchone()[0]))
            if len(seen) == 1:  # the second call re-enters the SAME content-addressed generation: a replay, it writes nothing
                ctx.db_conn.execute(MSR_INSERT, (str(uuid.uuid4()), ctx.config["chart_id"], ctx.build_id))
            return type("R", (), {"rows_inserted": 1, "rows_updated": 0, "rows_skipped": 0, "notes": ""})()

    Wrapped = l2_producer("bo_sudarshana")(Probe)
    with psycopg.connect(BUILDER) as conn:
        run = _builder_txn_with_l1_head(conn)
        ctx = ContextSpec(asset_id="bo_sudarshana", build_id=run, db_conn=conn, config={"chart_id": CHART, "birth_params": {}})
        Wrapped().run(ctx)
        assert conn.execute("SHOW search_path").fetchone()[0] == "public, pg_temp", "premise: the first call ended with the reset"
        assert conn.execute(RESOLVES_TO_TEMP, ("chart_facts",)).fetchone()[0] is False
        Wrapped().run(ctx)
        assert conn.execute("SHOW search_path").fetchone()[0] == "public, pg_temp"
        conn.rollback()
    assert seen == [("chart_facts", True), ("chart_facts", True)], seen


def test_true_bind_shadows_are_still_alive_but_unqualified_reads_hit_the_real_table_after_the_wrapper_returns(fixtures_committed):
    """The shadows here are the REAL ones ``bind_l2_exact_inputs`` created (owned by ``data_plane_l2_owner``), not a builder-owned stand-in.
    After the wrapper returns they still exist in this transaction's temp schema, yet an unqualified read must not touch them: under the
    production ACLs reading one raises ``permission denied`` (and with a grant it would return the shadow's rows), so a successful read of the
    real count proves name resolution went to ``public``. Reviewer probe: /Users/Dev/suvarna-evidence/S_L1/rv3008/probe_real_shadow.py."""
    class Probe:
        asset_id = "bo_sudarshana"

        def run(self, ctx):
            ctx.db_conn.execute(MSR_INSERT, (str(uuid.uuid4()), ctx.config["chart_id"], ctx.build_id))
            return type("R", (), {"rows_inserted": 1, "rows_updated": 0, "rows_skipped": 0, "notes": ""})()

    Wrapped = l2_producer("bo_sudarshana")(Probe)
    with psycopg.connect(BUILDER) as conn:
        run = _builder_txn_with_l1_head(conn)
        ctx = ContextSpec(asset_id="bo_sudarshana", build_id=run, db_conn=conn, config={"chart_id": CHART, "birth_params": {}})
        Wrapped().run(ctx)
        owners = conn.execute(
            "SELECT pg_get_userbyid(c.relowner) FROM pg_class c WHERE c.relnamespace = pg_my_temp_schema() AND c.relname = 'chart_facts'").fetchall()
        assert owners == [("data_plane_l2_owner",)], f"premise: the true bind shadow of chart_facts is alive and not builder-owned: {owners}"
        unqualified = conn.execute("SELECT count(*) FROM chart_facts WHERE chart_id = %s", (CHART,)).fetchone()[0]
        real = conn.execute("SELECT count(*) FROM public.chart_facts WHERE chart_id = %s", (CHART,)).fetchone()[0]
        assert unqualified == real and real >= 1, (unqualified, real)
        conn.rollback()
