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
