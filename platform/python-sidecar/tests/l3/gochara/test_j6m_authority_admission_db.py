"""J-6m admission/retention SQL oracles; no sky computation or production action.

Uses the A5.3 guarded, disposable database with the real migration chain. The
publication/seal rows below are synthetic *admission metadata*, including corrupt
pairs. Their setup bypasses seal insertion guards deliberately: this suite tests
which existing seals authority admission accepts, not whether sealing is earned.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import uuid

import psycopg
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb
import pytest

from .test_a53_inventory import ADMIN_DSN, CHART_ID, create_am5_database, drop_am5_database

ROOT = Path(__file__).resolve().parents[5]
MIGRATIONS = ROOT / 'platform/migrations'
FOLLOWUP = '1382_gochara_authority_no_truncate.sql'


def _authority_database(*, apply_followup=True, tag='j6m'):
    admin, name, dsn = create_am5_database(tag)
    conn = None
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        # Real 527 DDL, including its legacy window discriminator; no handwritten
        # authority-table replacement. 527 owns its own legacy transaction.
        conn.execute('CREATE TABLE public.kala_gochara_windows (chart_id uuid)')
        conn.execute((ROOT / 'platform/supabase/migrations/527_kala_gochara_generation_authority.sql').read_text())
        conn.execute((MIGRATIONS / '1236_gochara_authority_refuses_governed_generation.sql').read_text())
        conn.execute("INSERT INTO public.kala_gochara_convention"
                     " (convention_id,zodiac,ayanamsha,sidereal_method,node_model,node_source,epoch_convention,"
                     " time_scale,house_system,ephemeris_mode,method_version)"
                     " VALUES ('j6m-metadata-only','fixture','fixture','fixture','fixture','fixture','fixture',"
                     " 'fixture','fixture','fixture','fixture')")
        # Seed adversarial metadata before the migration; this is not a seal-flow
        # acceptance test and makes no claim of computed or verified chart data.
        with conn.transaction():
            conn.execute('ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER USER')
            cases = [
                (CHART_ID, '5.0', 'published', {}, 'match'),
                (CHART_ID, '5.1', 'published', {}, None),
                (CHART_ID, '5.2', 'candidate', {}, 'match'),
                (CHART_ID, '5.3', 'published', {}, 'mismatch'),
                (CHART_ID, '5.4', 'published', {'stored_scope': 'test_slice'}, 'match'),
                (CHART_ID, '5.5', 'published', {'test_slice': False}, 'match'),
                (CHART_ID, '10.0', 'published', {}, 'match'),
            ]
            for chart, gen, status, vector, seal in cases:
                manifest = uuid.uuid4()
                conn.execute("INSERT INTO public.kala_gochara_publication"
                             " (manifest_id,chart_id,generation,writer_asset_id,convention_id,input_generation_vector,"
                             " ephemeris_backend,horizon,row_counts,content_digest,status)"
                             " VALUES (%s,%s,%s,'ka_gochara_v5','j6m-metadata-only',%s,'{}',"
                             " tstzrange('2025-01-01 UTC','2025-02-01 UTC','[)'),'{}','fixture',%s)",
                             (manifest, chart, gen, Jsonb(vector), status))
                if seal:
                    conn.execute('INSERT INTO public.ka_gochara_generation_seal(chart_id,generation,manifest_id)'
                                 ' VALUES (%s,%s,%s)', (chart, gen, manifest if seal == 'match' else uuid.uuid4()))
            conn.execute('ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER USER')
        conn.execute("INSERT INTO public.kala_gochara_authority(chart_id,authoritative_generation,flipped_by,evidence_ref)"
                     " VALUES (%s,'3.0','fixture','previous-head')", (CHART_ID,))
        before = conn.execute('TABLE public.kala_gochara_authority').fetchall()
        with conn.transaction():
            conn.execute((MIGRATIONS / '1379_gochara_sealed_authority.sql').read_text())
            # Optional only so the same behavioral oracle runs on the revert
            # copy (1379 alone), exposing TRUNCATE's actual effect rather than
            # failing on a missing file. The static suite requires the file.
            if apply_followup and (MIGRATIONS / FOLLOWUP).exists():
                conn.execute((MIGRATIONS / FOLLOWUP).read_text())
        assert conn.execute('TABLE public.kala_gochara_authority').fetchall() == before
        yield conn
    finally:
        if conn is not None:
            conn.close()
        drop_am5_database(admin, name)


@pytest.fixture(scope='module')
def authority_db():
    yield from _authority_database()


@pytest.fixture
def runner_db():
    # Use the same guarded lifecycle and real predecessor chain, but let the
    # actual TypeScript runner own 1382's transaction and ledger insertion.
    yield from _authority_database(apply_followup=False, tag='j6mr1')


@pytest.fixture
def db(authority_db):
    with authority_db.transaction(force_rollback=True):
        yield authority_db


def _head(conn):
    return conn.execute('SELECT authoritative_generation FROM public.kala_gochara_authority WHERE chart_id=%s',
                        (CHART_ID,)).fetchone()[0]


def _set(conn, generation):
    conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s WHERE chart_id=%s',
                 (generation, CHART_ID))


@pytest.mark.parametrize('mode', ['origin', 'replica'])
@pytest.mark.parametrize('generation', ['5.0', '10.0'])
def test_matching_published_non_slice_seal_admitted_and_explicit_previous_head_restored(db, mode, generation):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    _set(db, generation)
    assert _head(db) == generation
    _set(db, '3.0')
    assert _head(db) == '3.0'


@pytest.mark.parametrize('mode', ['origin', 'replica'])
@pytest.mark.parametrize('generation', ['5.1', '5.2', '5.3', '5.4', '5.5', '5.9'])
def test_unsealed_unpublished_mismatched_slice_and_missing_seals_refused(db, mode, generation):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    with pytest.raises(psycopg.errors.CheckViolation, match='governed head requires'):
        with db.transaction():
            _set(db, generation)
    assert _head(db) == '3.0'


@pytest.mark.parametrize('mode', ['origin', 'replica'])
def test_insert_also_requires_matching_seal(db, mode):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    db.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,))
    with pytest.raises(psycopg.errors.CheckViolation):
        with db.transaction():
            db.execute("INSERT INTO public.kala_gochara_authority(chart_id,authoritative_generation) VALUES (%s,'5.1')",
                       (CHART_ID,))
    db.execute("INSERT INTO public.kala_gochara_authority(chart_id,authoritative_generation) VALUES (%s,'5.0')",
               (CHART_ID,))
    assert _head(db) == '5.0'


@pytest.mark.parametrize('mode', ['origin', 'replica'])
def test_fresh_authority_insert_holds_chart_lock_until_transaction_ends(authority_db, mode):
    # M08: removing INSERT from the row guard must lose serialization here.
    # Unlike the admission test above, commit DELETE before starting INSERT:
    # its statement lock must not mask a missing INSERT lock.
    conn = authority_db
    previous = conn.execute('SELECT chart_id,authoritative_generation,flipped_at,flipped_by,evidence_ref'
                            ' FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,)).fetchone()
    assert previous is not None and previous[1] == '3.0'
    conn.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,))
    # Pin the family key independently of the helper under test (1153:453).
    lock_sql = "SELECT pg_try_advisory_xact_lock(hashtext('gochara5:chart:' || %s)::bigint)"
    try:
        # ConnectionInfo.dsn omits passwords; retain the guarded fixture's CI
        # authentication while selecting only its disposable database.
        observer_dsn = make_conninfo(ADMIN_DSN, dbname=conn.info.dbname)
        with psycopg.connect(observer_dsn, autocommit=True, connect_timeout=3) as observer:
            assert observer.execute(lock_sql, (CHART_ID,)).fetchone() == (True,)
            with conn.transaction(force_rollback=True):
                conn.execute(f"SET LOCAL session_replication_role = '{mode}'")
                conn.execute("INSERT INTO public.kala_gochara_authority(chart_id,authoritative_generation)"
                             " VALUES (%s,'5.0')", (CHART_ID,))
                assert _head(conn) == '5.0'
                assert observer.execute(lock_sql, (CHART_ID,)).fetchone() == (False,)
            assert observer.execute(lock_sql, (CHART_ID,)).fetchone() == (True,)
    finally:
        conn.execute('INSERT INTO public.kala_gochara_authority'
                     ' (chart_id,authoritative_generation,flipped_at,flipped_by,evidence_ref)'
                     ' VALUES (%s,%s,%s,%s,%s)', previous)


@pytest.mark.parametrize('mode', ['origin', 'replica'])
@pytest.mark.parametrize('mutation', [
    "DELETE FROM public.ka_gochara_generation_seal WHERE chart_id=%s AND generation='5.0'",
    "UPDATE public.ka_gochara_generation_seal SET manifest_id='00000000-0000-0000-0000-000000000001'"
    " WHERE chart_id=%s AND generation='5.0'",
])
def test_authoritative_seal_cannot_be_removed_or_replaced(db, mode, mutation):
    # M07: an origin-only seal write guard permits replica DELETE/UPDATE.
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    _set(db, '5.0')
    seal_sql = "SELECT * FROM public.ka_gochara_generation_seal WHERE chart_id=%s AND generation='5.0'"
    before = db.execute(seal_sql, (CHART_ID,)).fetchone()
    assert before is not None
    assert db.execute("SELECT public.ka_gochara_authority_admissible(%s,'5.0')",
                      (CHART_ID,)).fetchone() == (True,)
    with pytest.raises(psycopg.errors.RaiseException, match='ka_gochara_generation_seal is permanent'):
        with db.transaction():
            db.execute(mutation, (CHART_ID,))
    assert db.execute(seal_sql, (CHART_ID,)).fetchone() == before
    assert _head(db) == '5.0'
    assert db.execute("SELECT public.ka_gochara_authority_admissible(%s,'5.0')",
                      (CHART_ID,)).fetchone() == (True,)


@pytest.mark.parametrize('mode', ['origin', 'replica'])
def test_delete_cannot_silently_restore_implicit_legacy_default(db, mode):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    _set(db, '5.0')
    with pytest.raises(psycopg.errors.CheckViolation, match='explicit retained previous head'):
        with db.transaction():
            db.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,))
    assert _head(db) == '5.0'


@pytest.mark.parametrize('mode', ['origin', 'replica'])
@pytest.mark.parametrize('generation', ['5.0', '3.0', None])
def test_truncate_cannot_silently_restore_implicit_legacy_default(db, mode, generation):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    if generation is None:
        db.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,))
    else:
        _set(db, generation)
    before = db.execute('TABLE public.kala_gochara_authority').fetchall()
    with pytest.raises(psycopg.errors.RaiseException, match='TRUNCATE refused on kala_gochara_authority'):
        with db.transaction():
            db.execute('TRUNCATE public.kala_gochara_authority')
    assert db.execute('TABLE public.kala_gochara_authority').fetchall() == before


@pytest.mark.parametrize('mode', ['origin', 'replica'])
@pytest.mark.parametrize('sql', [
    "UPDATE public.kala_gochara_publication SET status='rolled_back' WHERE generation='5.0'",
    "UPDATE public.kala_gochara_publication SET input_generation_vector='{}'::jsonb || '{\"test_slice\":true}'::jsonb WHERE generation='5.0'",
    "DELETE FROM public.kala_gochara_publication WHERE generation='5.0'",
])
def test_authoritative_manifest_cannot_be_withdrawn_or_replaced(db, mode, sql):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    _set(db, '5.0')
    with pytest.raises(psycopg.errors.CheckViolation, match='authoritative manifest is immutable|sealed boundary'):
        with db.transaction():
            db.execute(sql)
    assert _head(db) == '5.0'


def test_catalog_readback_names_validated_constraint_and_always_trigger(db):
    name, validated, definition = db.execute(
        "SELECT conname,convalidated,pg_get_constraintdef(oid) FROM pg_constraint"
        " WHERE conrelid='public.kala_gochara_authority'::regclass AND conname='kga_sealed_authority_ck'").fetchone()
    assert name == 'kga_sealed_authority_ck' and validated
    assert 'ka_gochara_authority_admissible(chart_id, authoritative_generation)' in definition
    assert db.execute("SELECT tgenabled FROM pg_trigger WHERE tgrelid='public.kala_gochara_authority'::regclass"
                      " AND tgname='kala_gochara_authority_no_truncate'").fetchone() == ('A',)


def test_followup_refuses_missing_sealed_constraint_before_creating_trigger(db):
    with pytest.raises(psycopg.errors.RaiseException, match='1382 preflight'):
        with db.transaction():
            db.execute('DROP TRIGGER kala_gochara_authority_no_truncate ON public.kala_gochara_authority')
            db.execute('ALTER TABLE public.kala_gochara_authority DROP CONSTRAINT kga_sealed_authority_ck')
            db.execute((MIGRATIONS / FOLLOWUP).read_text())
    # Savepoint rollback preserves the previously validated deployment.
    assert db.execute("SELECT tgenabled FROM pg_trigger WHERE tgrelid='public.kala_gochara_authority'::regclass"
                      " AND tgname='kala_gochara_authority_no_truncate'").fetchone() == ('A',)


def _guard(conn):
    return conn.execute(
        "SELECT oid,tgenabled,tgtype,tgnargs,tgqual,pg_get_triggerdef(oid),"
        " tgfoid='public.ka_gochara_refuse_truncate()'::regprocedure AS correct_function"
        " FROM pg_trigger WHERE tgrelid='public.kala_gochara_authority'::regclass"
        " AND tgname='kala_gochara_authority_no_truncate' AND NOT tgisinternal").fetchone()


def _assert_guard(conn):
    guard = _guard(conn)
    assert guard is not None
    assert guard[1:5] == ('A', 34, 0, None)
    assert guard[6] is True
    return guard


def _authority_rows(conn):
    return conn.execute('SELECT * FROM public.kala_gochara_authority ORDER BY chart_id').fetchall()


def _runner(conn, directory, *, dry_run=False, protected=True):
    """Run the imported production runner, never its CLI or an external DB.

    Only the existing guarded fixture's explicit connection parameters cross
    stdin. Child errors expose a class/code, never a DSN or database error text.
    CI has platform/node_modules; a local job may supply read-only dependencies.
    """
    settings = psycopg.conninfo.conninfo_to_dict(make_conninfo(ADMIN_DSN, dbname=conn.info.dbname))
    assert settings['host'] in ('127.0.0.1', 'localhost', '::1')
    assert conn.info.dbname.startswith('a53t_')
    config = {key: settings[key] for key in ('host', 'port', 'user', 'password') if key in settings}
    config['database'] = conn.info.dbname
    address = conn.execute('SELECT inet_server_addr()::text').fetchone()[0]
    modules = Path(os.environ.get('J6M_R1_NODE_MODULES', ROOT / 'platform/node_modules'))
    registration = modules / 'tsx/dist/cjs/index.cjs'
    assert registration.is_file(), 'npm ci is required for the real migration-runner proof'
    javascript = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {Client} = require('pg');
const {runMigrations} = require(process.argv[1]);
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const client = new Client({...input.config, connectionTimeoutMillis: 3000});
(async () => {
  try {
    await client.connect();
    const probe = await client.query('SELECT current_database() AS db, inet_server_addr()::text AS address');
    assert.equal(probe.rows[0].db, input.config.database);
    assert.equal(probe.rows[0].address, input.address);
    const options = {dryRun: input.dryRun, disclosures: new Map(), renumberDisclosures: new Map()};
    if (input.protected) options.only = new Set([input.filename]);
    const ran = await runMigrations(client, [input.directory], options);
    console.log('J6M_R1_RESULT=' + JSON.stringify({ran}));
  } catch (error) {
    console.log('J6M_R1_RESULT=' + JSON.stringify({error: error.constructor.name, code: error.code ?? null}));
  } finally {
    await client.end();
  }
})().catch(() => { process.exitCode = 1; });
"""
    child = subprocess.run(
        ['node', '--require', str(registration), '--eval', javascript, str(ROOT / 'platform/scripts/migrate.ts')],
        input=json.dumps({'config': config, 'address': address, 'directory': str(directory),
                          'dryRun': dry_run, 'protected': protected, 'filename': FOLLOWUP}),
        env={**os.environ, 'NODE_ENV': 'test', 'TSX_DISABLE_CACHE': '1',
             'MIGRATE_APPLY_PROTECTED': ''},
        cwd=ROOT / 'platform', capture_output=True, text=True, timeout=30)
    assert child.returncode == 0, 'migration-runner harness failed (child error text withheld)'
    records = [line.removeprefix('J6M_R1_RESULT=') for line in child.stdout.splitlines()
               if line.startswith('J6M_R1_RESULT=')]
    assert len(records) == 1, 'migration-runner harness returned no unique result'
    return json.loads(records[0])


def _runner_directory(tmp_path):
    directory = tmp_path / 'migrations'
    directory.mkdir()
    (directory / FOLLOWUP).write_bytes((MIGRATIONS / FOLLOWUP).read_bytes())
    return directory


@pytest.mark.parametrize('dry_run', [False, True])
def test_runner_defers_unapplied_1382_outside_protected_window(runner_db, tmp_path, dry_run):
    conn = runner_db
    before = _authority_rows(conn)
    assert _runner(conn, _runner_directory(tmp_path), dry_run=dry_run, protected=False) == {'ran': []}
    assert _guard(conn) is None
    assert conn.execute('SELECT count(*) FROM public._migrations_applied WHERE filename=%s',
                        (FOLLOWUP,)).fetchone() == (0,)
    assert _authority_rows(conn) == before


def test_runner_failed_1382_preflight_rolls_back_without_ledger(runner_db, tmp_path):
    conn = runner_db
    conn.execute('ALTER TABLE public.kala_gochara_authority DROP CONSTRAINT kga_sealed_authority_ck')
    before = _authority_rows(conn)
    assert _runner(conn, _runner_directory(tmp_path)) == {'error': 'DatabaseError', 'code': 'P0001'}
    assert _guard(conn) is None and _authority_rows(conn) == before
    assert conn.execute('SELECT count(*) FROM public._migrations_applied WHERE filename=%s',
                        (FOLLOWUP,)).fetchone() == (0,)


def test_runner_ledger_failure_rolls_back_1382_ddl_and_preserves_rows(runner_db, tmp_path):
    conn = runner_db
    # Refuse only this fixture's ledger insertion AFTER 1382's DDL succeeded.
    # Without the runner-owned transaction the trigger would remain installed
    # without an applied record and subsequent runner attempts would fail 42710.
    conn.execute("CREATE FUNCTION public.j6mr1_refuse_ledger() RETURNS trigger LANGUAGE plpgsql AS $$"
                 " BEGIN IF NEW.filename = '1382_gochara_authority_no_truncate.sql' THEN"
                 " RAISE EXCEPTION 'fixture ledger refusal'; END IF; RETURN NEW; END $$")
    conn.execute('CREATE TRIGGER j6mr1_refuse_ledger BEFORE INSERT ON public._migrations_applied'
                 ' FOR EACH ROW EXECUTE FUNCTION public.j6mr1_refuse_ledger()')
    before = _authority_rows(conn)
    assert _runner(conn, _runner_directory(tmp_path)) == {'error': 'DatabaseError', 'code': 'P0001'}
    assert _guard(conn) is None and _authority_rows(conn) == before
    assert conn.execute('SELECT count(*) FROM public._migrations_applied WHERE filename=%s',
                        (FOLLOWUP,)).fetchone() == (0,)


@pytest.mark.parametrize('dry_run', [False, True])
@pytest.mark.parametrize('protected', [False, True])
def test_runner_applies_once_then_hash_matching_repeat_preserves_guard_and_ledger(
        runner_db, tmp_path, dry_run, protected):
    conn = runner_db
    directory = _runner_directory(tmp_path)
    before = _authority_rows(conn)
    assert _guard(conn) is None
    assert _runner(conn, directory) == {'ran': [FOLLOWUP]}
    guard = _assert_guard(conn)
    ledger_sql = 'SELECT * FROM public._migrations_applied WHERE filename=%s'
    ledger = conn.execute(ledger_sql, (FOLLOWUP,)).fetchall()
    assert len(ledger) == 1
    assert conn.execute('SELECT sha256 FROM public._migrations_applied WHERE filename=%s',
                        (FOLLOWUP,)).fetchone() == (hashlib.sha256((directory / FOLLOWUP).read_bytes()).hexdigest(),)
    assert _runner(conn, directory, dry_run=dry_run, protected=protected) == {'ran': []}
    assert _assert_guard(conn) == guard  # Includes OID: no drop/recreate disguised as a skip.
    assert conn.execute(ledger_sql, (FOLLOWUP,)).fetchall() == ledger
    assert _authority_rows(conn) == before
    for mode in ('origin', 'replica'):
        with pytest.raises(psycopg.errors.RaiseException, match='TRUNCATE refused on kala_gochara_authority'):
            with conn.transaction():
                conn.execute(f'SET LOCAL session_replication_role = {mode}')
                conn.execute('TRUNCATE public.kala_gochara_authority')
    assert _authority_rows(conn) == before


@pytest.mark.parametrize('dry_run', [False, True])
@pytest.mark.parametrize('protected', [False, True])
def test_runner_refuses_changed_1382_bytes_even_for_preview_and_routine_skip(
        runner_db, tmp_path, dry_run, protected):
    conn = runner_db
    directory = _runner_directory(tmp_path)
    assert _runner(conn, directory) == {'ran': [FOLLOWUP]}
    guard, rows = _assert_guard(conn), _authority_rows(conn)
    ledger = conn.execute('SELECT * FROM public._migrations_applied WHERE filename=%s', (FOLLOWUP,)).fetchall()
    with (directory / FOLLOWUP).open('a') as changed:
        changed.write('\n-- same SQL identity, changed immutable bytes\n')
    assert _runner(conn, directory, dry_run=dry_run, protected=protected) == {
        'error': 'MigrationHashMismatchError', 'code': None}
    assert _assert_guard(conn) == guard and _authority_rows(conn) == rows
    assert conn.execute('SELECT * FROM public._migrations_applied WHERE filename=%s', (FOLLOWUP,)).fetchall() == ledger


@pytest.mark.parametrize('generation', ['3.0', '5.0'])
@pytest.mark.parametrize('mode', ['origin', 'replica'])
def test_raw_1382_replay_is_42710_and_preserves_exact_rows_and_always_guard(db, generation, mode):
    db.execute(f'SET LOCAL session_replication_role = {mode}')
    _set(db, generation)
    before, guard = _authority_rows(db), _assert_guard(db)
    with pytest.raises(psycopg.errors.DuplicateObject) as refused:
        with db.transaction():
            db.execute((MIGRATIONS / FOLLOWUP).read_text())
    assert refused.value.sqlstate == '42710'
    assert _authority_rows(db) == before and _assert_guard(db) == guard
    with pytest.raises(psycopg.errors.RaiseException, match='TRUNCATE refused on kala_gochara_authority'):
        with db.transaction():
            db.execute('TRUNCATE public.kala_gochara_authority')
    assert _authority_rows(db) == before


def test_runner_skip_does_not_replace_required_catalog_readback(runner_db, tmp_path):
    conn = runner_db
    directory = _runner_directory(tmp_path)
    assert _runner(conn, directory) == {'ran': [FOLLOWUP]}
    with conn.transaction(force_rollback=True):
        conn.execute('ALTER TABLE public.kala_gochara_authority DISABLE TRIGGER kala_gochara_authority_no_truncate')
        # The runner checks the committed ledger, not live catalog drift. The
        # separate readback must reject this state even after a successful skip.
        assert _runner(conn, directory) == {'ran': []}
        with pytest.raises(AssertionError):
            _assert_guard(conn)
    _assert_guard(conn)
