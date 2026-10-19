"""Guarded fixture for binding SQL, without an unrelated sky-substrate build.

Uses the same isolated-database guard/migrations and synthetic L1 inputs as AM5.
This is not the canonical offline fixture or a measuring build acceptance.
"""
from types import SimpleNamespace

import psycopg
import pytest

from pipeline.orchestrator.writers import ContextSpec, SubStep
from pipeline.orchestrator.writers import ka_gochara_v5 as writer
from services.gochara_kernel.rule_registry import RuleRegistryStore
from . import _runner_world as rw
from .conftest import EPHE_PATH
from .test_a53_inventory import apply_near_miss_storage, create_am5_database, drop_am5_database
from .test_c38_teardown_real_db import STUB_DDL


@pytest.fixture
def measuring_world():
    admin, name, dsn = create_am5_database('j3cbinding')
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        rw.apply_orchestrator_schema(conn)
        conn.execute('CREATE TABLE IF NOT EXISTS public.kala_gochara_authority (chart_id uuid PRIMARY KEY, authoritative_generation text)')
        conn.execute((rw.REPO / 'platform/migrations/436_build_substep_progress.sql').read_text())
        rw.seed_registry(conn, {'ka_gochara_v5', 'ga_positions', 'ga_dashas'})
        yield SimpleNamespace(conn=conn, dsn=dsn)
    finally:
        conn.close()
        drop_am5_database(admin, name)


@pytest.fixture
def measuring_teardown_world():
    admin, name, dsn = create_am5_database('j3dreceipt')
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    try:
        for ddl in STUB_DDL:
            conn.execute(ddl)
        apply_near_miss_storage(conn)           # the teardown's closed list covers the migration-1308 generation tables
        import teardown_v5_small_test_job as td
        e = td.EXPECTED_REGISTRY_ROW
        conn.execute('INSERT INTO public.asset_registry VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (writer.ASSET_ID, e['scope'], False, e['has_writer'], e['has_substeps'], e['writer_timeout_seconds'],
             e['depends_on'], e['target_table'], e['count_sql'], e['target_floor'], e['estimated_seconds']))
        RuleRegistryStore(conn).seed()
        w = writer.GocharaV5Writer()
        with conn.transaction():
            w.run_substep(ContextSpec(asset_id=writer.ASSET_ID, build_id='11111111-2222-4333-8444-555555555555', db_conn=conn, dry_run=False,
                config={'chart_id': rw.CHART, 'ephe_path': EPHE_PATH}), SubStep(key=writer.CONVENTION_SUBSTEP, label='convention'))
        yield SimpleNamespace(conn=conn, dsn=dsn, _w=w)
    finally:
        conn.close()
        drop_am5_database(admin, name)
