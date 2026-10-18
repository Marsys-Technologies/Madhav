"""J-GOCHARA-TIMEOUT pre-build: actual registry SQL, no production value approval.

The authentic *historical* baseline is replayed from immutable migrations, never
presented as the current production row. TEST_APPROVED is a deliberately artificial
one-second increase for SQL mechanics; it is not a proposed policy or timeout.
"""
import asyncio
from pathlib import Path

import psycopg
import pytest

PLATFORM = Path(__file__).resolve().parents[4]
TEMPLATE = PLATFORM / "scripts/sql/ka_gochara_v3_century_materialize_timeout.sql.in"
TARGET = "ka_gochara_v3_century_materialize"
BASELINE_FILES = [
    "167_asset_registry.sql", "202_asset_registry_service_support.sql",
    "223_orchestrator_rebuild_probe_dag.sql", "342_asset_registry_writer_flags.sql",
    "417_asset_registry_writer_timeout_seconds.sql",
    "560_ka_gochara_v3_century_materialize_seed.sql", "562_gochara_v3_dag_integration.sql",
]
HISTORICAL_BASELINE = 3600  # real migration 560, NOT a live-registry measurement
TEST_APPROVED = HISTORICAL_BASELINE + 1  # test data only, never policy


def prepared_sql(expected=HISTORICAL_BASELINE, approved=TEST_APPROVED):
    return TEMPLATE.read_text().replace("__EXPECTED_TIMEOUT_SECONDS__", str(expected)).replace(
        "__APPROVED_TIMEOUT_SECONDS__", str(approved))


@pytest.fixture(scope="module")
def baseline(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as conn:
        for filename in BASELINE_FILES:
            conn.execute((PLATFORM / "supabase/migrations" / filename).read_text())
    return isolated_kala_db_dsn


@pytest.fixture
def registry(baseline):
    with psycopg.connect(baseline) as conn:
        # Future columns must also be protected without a hand-maintained list.
        conn.execute("ALTER TABLE public.asset_registry ADD COLUMN future_contract jsonb")
        conn.execute("UPDATE public.asset_registry SET future_contract = '{\"retain\": [1, null]}'")
        for asset, timeout in [("ka_gochara", HISTORICAL_BASELINE),
                               ("ka_gochara_v3_century_materialize_alias", HISTORICAL_BASELINE + 2)]:
            conn.execute("""INSERT INTO public.asset_registry
                SELECT (jsonb_populate_record(NULL::public.asset_registry,
                to_jsonb(r) || jsonb_build_object('asset_id', %s::text,
                'writer_timeout_seconds', %s::int))).*
                FROM public.asset_registry r WHERE asset_id = %s""", (asset, timeout, TARGET))
        assert conn.execute("SELECT writer_timeout_seconds FROM public.asset_registry WHERE asset_id=%s",
                            (TARGET,)).fetchone()[0] == HISTORICAL_BASELINE
        yield conn
        conn.rollback()


def snapshot(conn):
    # Independent readback compares serialized whole rows, including unknown columns.
    return dict(conn.execute("SELECT asset_id, row_to_json(r)::text FROM public.asset_registry r ORDER BY asset_id").fetchall())


def test_updates_exact_target_column_and_is_idempotent(registry):
    before = snapshot(registry)
    registry.execute(prepared_sql())
    target = registry.execute("SELECT writer_timeout_seconds FROM public.asset_registry WHERE asset_id=%s", (TARGET,)).fetchone()[0]
    assert target == TEST_APPROVED
    after = snapshot(registry)
    assert after[TARGET] == before[TARGET].replace(
        f'"writer_timeout_seconds":{HISTORICAL_BASELINE}', f'"writer_timeout_seconds":{TEST_APPROVED}')
    assert {k: v for k, v in after.items() if k != TARGET} == {k: v for k, v in before.items() if k != TARGET}
    registry.execute(prepared_sql())
    assert snapshot(registry) == after


@pytest.fixture
def committed_neighbour(baseline):
    # The normal registry fixture's rows/DDL are uncommitted and invisible to
    # a second session. Publish only this test's distinct competing-write row.
    neighbour = TARGET + "_competing_writer"
    with psycopg.connect(baseline, autocommit=True) as conn:
        conn.execute("""INSERT INTO public.asset_registry
            SELECT (jsonb_populate_record(NULL::public.asset_registry,
            to_jsonb(r) || jsonb_build_object('asset_id', %s::text))).*
            FROM public.asset_registry r WHERE asset_id = %s""", (neighbour, TARGET))
        try:
            yield baseline, neighbour
        finally:
            conn.execute("DELETE FROM public.asset_registry WHERE asset_id = %s", (neighbour,))


def test_competing_registry_writer_waits_until_transaction_ends(committed_neighbour):
    """Removing the table lock must let this different-row write escape."""
    baseline, neighbour = committed_neighbour

    async def compete():
        options = "-c statement_timeout=5000 -c lock_timeout=4000"
        async with (
            await psycopg.AsyncConnection.connect(baseline, connect_timeout=3, options=options) as migration,
            await psycopg.AsyncConnection.connect(baseline, connect_timeout=3, options=options) as competitor,
        ):
            await migration.execute(prepared_sql())
            # A write to TARGET would also wait on UPDATE's ordinary row lock,
            # masking removal of the full-registry snapshot protection.
            writer = asyncio.create_task(competitor.execute("""UPDATE public.asset_registry
                SET writer_timeout_seconds = writer_timeout_seconds + 1
                WHERE asset_id = %s RETURNING writer_timeout_seconds""", (neighbour,)))
            try:
                deadline = asyncio.get_running_loop().time() + 2
                while True:
                    cursor = await migration.execute(
                        "SELECT pg_blocking_pids(%s)", (competitor.info.backend_pid,))
                    blockers = (await cursor.fetchone())[0]
                    if migration.info.backend_pid in blockers:
                        break
                    assert not writer.done(), "competing registry write escaped the migration transaction"
                    assert asyncio.get_running_loop().time() < deadline, "writer did not reach the registry lock"
                    await asyncio.sleep(0.01)
                assert not writer.done()
                await migration.rollback()
                cursor = await asyncio.wait_for(writer, timeout=6)
                assert await cursor.fetchone() == (HISTORICAL_BASELINE + 1,)
                cursor = await competitor.execute(
                    "SELECT writer_timeout_seconds FROM public.asset_registry WHERE asset_id = %s", (TARGET,))
                assert await cursor.fetchone() == (HISTORICAL_BASELINE,)
            finally:
                # Release the blocker even on assertion failure, then drain the
                # bounded write before rolling it back; no task/row survives.
                await migration.rollback()
                try:
                    await asyncio.wait_for(writer, timeout=6)
                finally:
                    await competitor.rollback()

    asyncio.run(compete())


@pytest.mark.parametrize("state", ["missing", "alias-only", "stale", "null"])
def test_refuses_missing_alias_or_stale_baseline(registry, state):
    if state in ("missing", "alias-only"):
        registry.execute("DELETE FROM public.asset_registry WHERE asset_id=%s", (TARGET,))
        if state == "missing":
            registry.execute("DELETE FROM public.asset_registry WHERE asset_id LIKE '%alias'")
    elif state == "null":
        registry.execute("ALTER TABLE public.asset_registry ALTER COLUMN writer_timeout_seconds DROP NOT NULL")
        registry.execute("UPDATE public.asset_registry SET writer_timeout_seconds=NULL WHERE asset_id=%s", (TARGET,))
    else:
        registry.execute("UPDATE public.asset_registry SET writer_timeout_seconds=writer_timeout_seconds+2 WHERE asset_id=%s", (TARGET,))
    before = snapshot(registry)
    with pytest.raises(psycopg.Error, match="missing target|stale baseline"):
        with registry.transaction():
            registry.execute(prepared_sql())
    assert snapshot(registry) == before


@pytest.mark.parametrize("expected,approved", [(0, 1), (-1, 1), (3600, 0), (3600, 3599), (3600, 3600)])
def test_refuses_invalid_or_non_increasing_parameters(registry, expected, approved):
    before = snapshot(registry)
    with pytest.raises(psycopg.Error, match="invalid timeout parameters"):
        with registry.transaction():
            registry.execute(prepared_sql(expected, approved))
    assert snapshot(registry) == before


def test_unbound_template_cannot_execute(registry):
    with pytest.raises(psycopg.Error):
        with registry.transaction():
            registry.execute(TEMPLATE.read_text())


def test_uses_public_registry_despite_search_path_shadow(registry):
    registry.execute("CREATE TEMP TABLE asset_registry (LIKE public.asset_registry INCLUDING ALL)")
    registry.execute("INSERT INTO pg_temp.asset_registry SELECT * FROM public.asset_registry")
    registry.execute(prepared_sql())
    assert registry.execute("SELECT writer_timeout_seconds FROM public.asset_registry WHERE asset_id=%s", (TARGET,)).fetchone()[0] == TEST_APPROVED
    assert registry.execute("SELECT writer_timeout_seconds FROM pg_temp.asset_registry WHERE asset_id=%s", (TARGET,)).fetchone()[0] == HISTORICAL_BASELINE


@pytest.mark.parametrize("mutation", ["wrong-row", "wrong-table", "extra-column", "unconstrained", "no-update"])
def test_independent_readback_rejects_update_mutations(registry, mutation):
    sql = prepared_sql()
    update = "UPDATE public.asset_registry\n       SET writer_timeout_seconds = approved_timeout\n     WHERE asset_id = 'ka_gochara_v3_century_materialize'\n       AND writer_timeout_seconds = expected_timeout;"
    assert update in sql
    replacement = {
        "wrong-row": update.replace(TARGET, "ka_gochara"),
        "wrong-table": update.replace("public.asset_registry", "pg_temp.asset_registry"),
        "extra-column": update.replace("= approved_timeout", "= approved_timeout, is_active = false"),
        "unconstrained": "UPDATE public.asset_registry SET writer_timeout_seconds = approved_timeout;",
        "no-update": "NULL;",
    }[mutation]
    registry.execute("CREATE TEMP TABLE asset_registry (LIKE public.asset_registry INCLUDING ALL)")
    registry.execute("INSERT INTO pg_temp.asset_registry SELECT * FROM public.asset_registry")
    before = snapshot(registry)
    with pytest.raises(psycopg.Error, match="registry readback mismatch"):
        with registry.transaction():
            registry.execute(sql.replace(update, replacement))
    assert snapshot(registry) == before


def test_readback_detects_trigger_side_effect_and_rolls_back(registry):
    registry.execute("""CREATE FUNCTION public.timeout_test_side_effect() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN NEW.english_description := 'changed by trigger'; RETURN NEW; END $$;
      CREATE TRIGGER timeout_side_effect BEFORE UPDATE ON public.asset_registry
      FOR EACH ROW EXECUTE FUNCTION public.timeout_test_side_effect();""")
    before = snapshot(registry)
    with pytest.raises(psycopg.Error, match="registry readback mismatch"):
        with registry.transaction():
            registry.execute(prepared_sql())
    assert snapshot(registry) == before


def test_caller_rollback_owns_the_update(registry):
    before = snapshot(registry)
    with pytest.raises(psycopg.Error, match="division by zero"):
        with registry.transaction():
            registry.execute(prepared_sql())
            registry.execute("SELECT 1 / 0")
    assert snapshot(registry) == before


def test_template_stays_unbound_and_outside_runner_discovery():
    text = TEMPLATE.read_text()
    assert "__EXPECTED_TIMEOUT_SECONDS__" in text
    assert "__APPROVED_TIMEOUT_SECONDS__" in text
    assert TEMPLATE.suffix == ".in"
    for directory in [PLATFORM / "migrations", PLATFORM / "supabase/migrations"]:
        assert not list(directory.glob("*_ka_gochara_v3_century_materialize_timeout.sql")), (
            "Numeric migration requires independent measured approval and a fresh guard number; "
            "replace this preparation guard when that separately reviewed migration is authorized")
