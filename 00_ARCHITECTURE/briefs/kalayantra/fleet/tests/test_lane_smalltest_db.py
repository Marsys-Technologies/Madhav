"""Six REAL P01 dry-run CLIs on a suite-owned, guarded ky_* local database.

The source is this candidate checkout; merged-source admission is tested
separately. No production operation, mock DB, cloud command or Git write.
"""
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import psycopg
import pytest

from test_lane_smalltest import FLEET, ROOT, KINDS, request

# Reuse the existing suite's guarded fixture and migration population. The only
# additional lifecycle is that fixture's ky_* name; it always drops what it owns.
SIDECAR = ROOT / 'platform/python-sidecar'
sys.path.insert(0, str(SIDECAR))
from tests.l3.gochara import test_a53_inventory as base
from tests.l3.gochara.test_c38_teardown_real_db import STUB_DDL
from tests.l3._disposable_db_guard import assert_disposable_connection


@contextlib.contextmanager
def _lane_database(prefix, tag, *, seed=None):
    """The suite's guarded ky_* lane database. With `seed`, the REAL authority migrations (527, 1236, 1379, 1382) are applied before the
    stubs and `seed(conn)` runs between 1236 and 1379 (production's other-chart rows predate 1379's guards), so the 1379 statement-lock
    triggers are live exactly as in production (SR-J2A-N18)."""
    settings = psycopg.conninfo.conninfo_to_dict(base.ADMIN_DSN)
    if settings.get('host') not in ('127.0.0.1', 'localhost') or settings.get('port') != '55433':
        message = 'lane CLI fixture requires explicit loopback cluster port 55433; no other database is contacted'
        if os.environ.get('KALA_REQUIRE_DB') == '1': pytest.fail(message)
        pytest.skip(message)
    previous = base.DB_PREFIX
    base.DB_PREFIX = prefix
    admin = None
    try:
        admin, name, dsn = base.create_am5_database(tag)
        with psycopg.connect(dsn, autocommit=True) as conn:
            assert_disposable_connection(conn, name)
            if seed is not None:
                migrations = ROOT / 'platform/migrations'
                conn.execute('CREATE TABLE public.kala_gochara_windows (chart_id uuid, generation text)')
                conn.execute((ROOT / 'platform/supabase/migrations/527_kala_gochara_generation_authority.sql').read_text())
                conn.execute((migrations / '1236_gochara_authority_refuses_governed_generation.sql').read_text())
                seed(conn)
                with conn.transaction():
                    conn.execute((migrations / '1379_gochara_sealed_authority.sql').read_text())
                    conn.execute((migrations / '1382_gochara_authority_no_truncate.sql').read_text())
            for ddl in STUB_DDL: conn.execute(ddl)
            conn.execute('ALTER TABLE asset_registry ADD COLUMN layer text DEFAULT \'L3\', ADD COLUMN natural_key_partition text')
            conn.execute('ALTER TABLE build_runs ADD COLUMN action text, ADD COLUMN plan jsonb')
            conn.execute('ALTER TABLE build_run_assets ADD COLUMN position integer, ADD COLUMN state text')
            conn.execute('ALTER TABLE asset_throughput ADD COLUMN rows_written integer DEFAULT 0, ADD COLUMN last_error text')
            conn.execute('CREATE UNIQUE INDEX lane_throughput ON asset_throughput(chart_id, asset_id) WHERE chart_id IS NOT NULL')
            import dispatch_v5_small_test_job as dispatch
            from psycopg import sql
            row = dict(asset_id='ka_gochara_v5', **dispatch.EXPECTED_REGISTRY_ROW)
            cols = list(row)
            conn.execute(sql.SQL('INSERT INTO asset_registry ({}) VALUES ({})').format(
                sql.SQL(',').join(map(sql.Identifier, cols)), sql.SQL(',').join(sql.Placeholder() for _ in cols)), list(row.values()))
        yield dict(host='127.0.0.1', port=55433, database=name), dsn
    finally:
        if admin is not None:
            base.drop_am5_database(admin, name)
        base.DB_PREFIX = previous


@pytest.fixture(scope='module')
def lane_db():
    with _lane_database('ky_j1atest_', 'cli') as (target, _dsn):
        yield target


@pytest.mark.parametrize('kind', KINDS + ('readback_sql',))
def test_real_lane_cli_and_independent_readback(lane_db, tmp_path, kind):
    import executor as ex
    req = request(kind); req['lane_target'] = lane_db
    if kind == 'readback_sql': req.update(requested_by='v1', args={})
    env = ex.lane_child_env(req, tmp_path)
    # Neither child needs a credential, a file containing one or cloud identity.
    env['PYTHONPATH'] = str(SIDECAR)
    result = subprocess.run([sys.executable, str(FLEET / 'lane_smalltest.py'), '--dry-run',
        '--lane-target', json.dumps(lane_db)], env=env, cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    proofs = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{"after_sha256"')]
    assert len(proofs) == 1
    proof = proofs[0]
    assert proof['status'] == 'DRY_RUN_VERIFIED' and proof['unchanged'] is True
    assert proof['readback']['database'] == lane_db['database']
    assert proof['before_sha256'] == proof['after_sha256']
    assert proof['request_sha256'] == ex.request_digest(req)
    assert proof['launched'] is False and proof['backup_taken'] is None and proof['restore_verified'] is None
    assert not list(tmp_path.rglob('*.dump')) and not list(tmp_path.rglob('*claim*'))


def test_readback_uses_a_real_read_only_session(lane_db, monkeypatch):
    import lane_smalltest as adapter
    req = request('readback_sql'); req['lane_target'] = lane_db
    original = adapter.backup.measurements
    def try_write(conn):
        assert conn.read_only is True
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute('CREATE TABLE lane_must_not_write(id int)')
        conn.rollback()
        return original(conn)
    monkeypatch.setattr(adapter.backup, 'measurements', try_write)
    assert adapter.observe(req)['database'] == lane_db['database']


def test_executor_export_six_receipts_and_final_independent_readback(lane_db, tmp_path, monkeypatch):
    """Real export/CLI/receipts; only candidate Git-object lookup is overlaid.

    This candidate is uncommitted by job policy. The transport double overlays
    these exact candidate files onto a read-only Git archive of HEAD. It never
    writes an object, branch, index, worktree, approval or campaign marker.
    """
    import hashlib
    import tarfile
    from types import SimpleNamespace
    from test_lane_smalltest import load
    ex = load('executor')
    monkeypatch.setattr(ex, 'GIT', ROOT)
    monkeypatch.setattr(ex, 'PY', sys.executable)
    monkeypatch.setattr(ex, 'REC', tmp_path / 'receipts'); ex.REC.mkdir()
    monkeypatch.setattr(ex, 'TMP', tmp_path / 'exports'); ex.TMP.mkdir()
    monkeypatch.setattr(ex, 'log', lambda *a: None)
    monkeypatch.setattr(ex, 'seen', lambda _: False)
    read_git = ex.git
    reviewed = read_git('rev-parse', 'HEAD').stdout.strip()
    def candidate_git(*args, **kwargs):
        if args[0] == 'cat-file':
            return SimpleNamespace(returncode=0 if (ROOT / args[2].split(':', 1)[1]).is_file() else 1)
        if args[0] == 'show':
            return SimpleNamespace(returncode=0, stdout=(ROOT / args[1].split(':', 1)[1]).read_text())
        return read_git(*args, **kwargs)
    monkeypatch.setattr(ex, 'git', candidate_git)
    real_run = subprocess.run
    overlays = [FLEET / 'executor.py', FLEET / 'executor_ops.json', FLEET / 'lane_smalltest.py',
                ROOT / 'platform/scripts/v5_small_test_shared.py', ROOT / 'platform/scripts/teardown_v5_small_test_job.py']
    def export_candidate(argv, **kwargs):
        if argv[0] == 'git' and 'archive' in argv:
            result = real_run(argv, **kwargs)
            assert result.returncode == 0
            kwargs['stdout'].flush()
            with tarfile.open(kwargs['stdout'].name, mode='a') as bundle:
                for path in overlays: bundle.add(path, arcname=str(path.relative_to(ROOT)))
            return result
        return real_run(argv, **kwargs)
    monkeypatch.setattr(ex.subprocess, 'run', export_candidate)
    table = json.loads((FLEET / 'executor_ops.json').read_text())['ops']
    refs = []
    inputs = tmp_path / 'requests'; inputs.mkdir()
    (tmp_path / 'candidate-overlay.json').write_text(json.dumps(dict(candidate_overlay=True, base_revision=reviewed, qualified_on_main=False)))
    for kind in KINDS:
        req = request(kind); req.update(lane_target=lane_db, reviewed_commit=reviewed)
        assert ex.validate(req, table, {'none': True}) is None
        (inputs / (kind + '.json')).write_text(json.dumps(req, sort_keys=True, separators=(',', ':')) + '\n')
        rc, output = ex.execute(req, table[kind]); assert rc == 0, output
        ex.receipt(req, 'COMPLETED', rc=rc, out=output)
        path = ex.REC / (req['operation_id'] + '.json'); body = path.read_bytes(); record = json.loads(body)
        assert record['status'] == 'COMPLETED' and 'launch' not in record and 'teardown' not in record
        refs.append(dict(name=path.name, sha256=hashlib.sha256(body).hexdigest()))
    req = request('readback_sql'); req.update(lane_target=lane_db, reviewed_commit=reviewed,
        requested_by='v1', args={}, lane_receipts=refs)
    assert ex.validate(req, table, {'none': True}) is None
    (inputs / 'readback_sql.json').write_text(json.dumps(req, sort_keys=True, separators=(',', ':')) + '\n')
    rc, output = ex.execute(req, table['readback_sql']); assert rc == 0, output
    ex.receipt(req, 'COMPLETED', rc=rc, out=output)
    final = json.loads((ex.REC / (req['operation_id'] + '.json')).read_text())
    assert final['status'] == 'COMPLETED' and len(final['lane']['qualification']) == 6
    assert {entry['kind'] for entry in final['lane']['qualification']} == set(KINDS)
    assert final['request_id'] == req['request_id'] and len(final['evidence_sha256']) == 64
    assert not list(ex.TMP.iterdir()), 'all private source exports must be removed'


CANONICAL = '482012f1-710e-4a25-994a-93821f5871aa'
FOREIGN = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'     # the non-canonical chart production holds in both tables (readback 20261017T060309Z)


def _seed_production_shape(conn):
    """What production holds and ky_b1 did not: kala_gochara_publication has the canonical 4.0 rolled_back row AND a second, non-canonical
    chart's 4.0 candidate; kala_gochara_authority holds one non-canonical chart (and the canonical 3.0 head)."""
    conn.execute("INSERT INTO public.kala_gochara_convention (convention_id,zodiac,ayanamsha,sidereal_method,node_model,node_source,"
                 "epoch_convention,time_scale,house_system,ephemeris_mode,method_version)"
                 " VALUES ('n18-fixture','f','f','f','f','f','f','f','f','f','f')")
    for chart, status, digest in ((CANONICAL, 'rolled_back', 'sha256:fixture'), (FOREIGN, 'candidate', 'sha256:unpublished-candidate')):
        conn.execute("INSERT INTO public.kala_gochara_publication (chart_id,generation,writer_asset_id,convention_id,"
                     "input_generation_vector,ephemeris_backend,horizon,row_counts,content_digest,status)"
                     " VALUES (%s,'4.0','ka_gochara','n18-fixture','{}','{}',tstzrange('2025-01-01 UTC','2025-02-01 UTC','[)'),'{}',%s,%s)",
                     (chart, digest, status))
    for chart in (CANONICAL, FOREIGN):
        conn.execute("INSERT INTO public.kala_gochara_authority (chart_id,authoritative_generation,flipped_at,flipped_by,evidence_ref)"
                     " VALUES (%s,'3.0','2025-01-01 UTC','fixture','retained-head')", (chart,))


def _foreign_rows(dsn):
    with psycopg.connect(dsn) as conn:
        return (conn.execute('SELECT chart_id::text, generation, status, content_digest FROM public.kala_gochara_publication ORDER BY 1,2').fetchall(),
                conn.execute('SELECT chart_id::text, authoritative_generation FROM public.kala_gochara_authority ORDER BY 1').fetchall())


@pytest.fixture(scope='module')
def lane_db_production_shape():
    with _lane_database('ky_n18test_', 'cli', seed=_seed_production_shape) as (target, dsn):
        yield target, dsn


def test_n18_fixture_reproduces_the_production_hazard(lane_db_production_shape):
    """Detector for the claim below: a zero-row DELETE on the manifest table, bound to the canonical chart, DOES raise P0001 here.
    Without this the next test could pass on a database that never had the hazard (CLAUDE.md N.8)."""
    _target, dsn = lane_db_production_shape
    with psycopg.connect(dsn) as conn:
        conn.execute('SELECT public.ka_gochara_lock_chart(%s::uuid)', (CANONICAL,))
        with pytest.raises(psycopg.errors.RaiseException) as raised:
            conn.execute("DELETE FROM public.kala_gochara_publication WHERE chart_id=%s AND generation='5.0'", (CANONICAL,))
        assert raised.value.sqlstate == 'P0001'
        conn.rollback()


def test_n18_empty_teardown_dry_run_with_another_charts_rows_present_passes_and_changes_nothing(lane_db_production_shape, tmp_path):
    """SR-J2A-N18 (A): the EMPTY dry run proves absence by SELECT and issues no DELETE on a table whose scoped count is 0, so another
    chart's manifest/authority rows (statement-level triggers lock every chart present) can no longer fail it with P0001."""
    import executor as ex
    import teardown_v5_small_test_job as td
    target, dsn = lane_db_production_shape
    before = _foreign_rows(dsn)
    assert sorted(row[0] for row in before[0]) == sorted([CANONICAL, FOREIGN]) and FOREIGN in [row[0] for row in before[1]]
    req = request('smalltest_teardown_dryrun'); req['lane_target'] = target
    env = ex.lane_child_env(req, tmp_path)
    env['PYTHONPATH'] = str(SIDECAR)
    result = subprocess.run([sys.executable, str(FLEET / 'lane_smalltest.py'), '--dry-run',
        '--lane-target', json.dumps(target)], env=env, cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    proof = json.loads([line for line in result.stdout.splitlines() if line.startswith('{"after_sha256"')][0])
    assert proof['status'] == 'DRY_RUN_VERIFIED' and proof['unchanged'] is True and proof['before_sha256'] == proof['after_sha256']
    teardown = json.loads(result.stdout.split('teardown_proof\t')[1].splitlines()[0])
    assert teardown['status'] == 'ROLLED_BACK' and teardown['rollback_confirmed'] is True
    # every table of the deletion scope was measured empty and skipped, in scope order; nothing was deleted from
    assert teardown['skipped_empty_tables'] == [name for name, *_ in td._scope_statements([])]
    assert _foreign_rows(dsn) == before
