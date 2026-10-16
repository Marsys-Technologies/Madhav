"""P01 backup/restore evidence: no DB, child programs or credentials are used.

Regression mutations: default mode executes, missing archive validation,
count-only restore, unsafe target, receipt before cleanup, swallowed failures.
"""
import hashlib
import importlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def backup():
    return importlib.import_module('backup_v5_small_test_job')


@pytest.mark.parametrize('operation', ['snapshot', 'restore-verify'])
def test_dryrun_has_no_database_subprocess_or_file_side_effect(backup, operation, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('KY_ROOT', str(tmp_path))
    def forbidden(*a, **kw):
        raise AssertionError('dry-run crossed an execution boundary')
    monkeypatch.setattr(backup, 'snapshot', forbidden)
    monkeypatch.setattr(backup, 'restore_verify', forbidden)
    assert backup.main(['--operation', operation, '--label', 'p01_fixture', '--dry-run']) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan['status'] == 'planned'
    assert plan['backup_taken'] is None and plan['restore_verified'] is None
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('label', ['../escape', 'prod', '', 'a'*41, 'UPPER', '-flag'])
def test_label_refused_before_execution(backup, label):
    with pytest.raises(SystemExit) as e:
        backup._parse_args(['--operation', 'snapshot', '--label', label])
    assert e.value.code == 2


def test_snapshot_and_restore_evidence_are_bound_by_label_and_bytes(backup, tmp_path):
    archive = tmp_path / 'database.dump'
    archive.write_bytes(b'synthetic archive')
    receipt = {'schema': 'ky.smalltest_backup/1', 'status': 'captured', 'label': 'p01_fixture',
               'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
               'measurements': {'tables': {'public.fixture': {'rows': 1, 'sha256': 'a'*64}}, 'sequences': {}},
               'snapshot': 'synthetic-exported-snapshot', 'source': {'database': 'fixture_source'}}
    assert backup.validate_capture(receipt, archive, 'p01_fixture') == receipt['measurements']
    with pytest.raises(backup.BackupRefused, match='label'):
        backup.validate_capture(receipt, archive, 'different_label')
    archive.write_bytes(b'tampered archive')
    with pytest.raises(backup.BackupRefused, match='archive'):
        backup.validate_capture(receipt, archive, 'p01_fixture')


@pytest.mark.parametrize('measurements', [{}, {'tables': {}, 'sequences': {}},
    {'tables': {'public.fixture': {'rows': 1}}, 'sequences': {}},
    {'tables': {'public.fixture': {'rows': -1, 'sha256': 'a'*64}}, 'sequences': {}}])
def test_missing_or_malformed_measurements_refused(backup, tmp_path, measurements):
    archive = tmp_path / 'database.dump'; archive.write_bytes(b'archive')
    receipt = {'schema': 'ky.smalltest_backup/1', 'status': 'captured', 'label': 'p01_fixture',
               'snapshot': 'synthetic', 'source': {'database': 'fixture_source'},
               'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'measurements': measurements}
    with pytest.raises(backup.BackupRefused):
        backup.validate_capture(receipt, archive, 'p01_fixture')


@pytest.mark.parametrize('actual', [
    {'tables': {'public.fixture': {'rows': 1, 'sha256': 'b'*64}}, 'sequences': {}},
    {'tables': {}, 'sequences': {}},
    {'tables': {'public.fixture': {'rows': 2, 'sha256': 'a'*64}}, 'sequences': {}},
    {'tables': {'public.fixture': {'rows': 1, 'sha256': 'a'*64}}, 'sequences': {'public.seq': {'last_value': 2, 'is_called': True}}}])
def test_restore_comparison_refuses_any_content_count_coverage_or_sequence_difference(backup, actual):
    expected = {'tables': {'public.fixture': {'rows': 1, 'sha256': 'a'*64}}, 'sequences': {}}
    with pytest.raises(backup.BackupRefused, match='restore'):
        backup.compare_restore(expected, actual)


def test_equal_restore_is_accepted(backup):
    expected = {'tables': {'public.fixture': {'rows': 1, 'sha256': 'a'*64}}, 'sequences': {}}
    backup.compare_restore(expected, json.loads(json.dumps(expected)))


def test_pg_environment_does_not_inherit_source_into_scratch(backup, monkeypatch):
    monkeypatch.setenv('PGSERVICE', 'synthetic_prod_service')
    monkeypatch.setenv('PGHOST', 'synthetic_remote')
    monkeypatch.setenv('DATABASE_URL', 'synthetic')
    env = backup.client_env(backup.scratch_settings('p01_fixture'))
    assert 'PGSERVICE' not in env and 'DATABASE_URL' not in env
    assert env['PGHOST'] == '127.0.0.1' and env['PGPORT'] == '55433'
    assert env['PGDATABASE'] == 'ky_restore_p01_fixture'


class Result:
    def __init__(self, row):
        self.row = row
    def fetchone(self):
        return self.row


class Connection:
    def __init__(self, *, exists=False, fail_drop=False):
        self.statements = []
        self.exists = exists
        self.fail_drop = fail_drop
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
    def execute(self, query, params=None):
        text = query if isinstance(query, str) else query.as_string(None)
        self.statements.append(text)
        if 'DROP DATABASE' in text and self.fail_drop:
            raise RuntimeError('synthetic cleanup failure')
        if 'pg_export_snapshot' in text:
            return Result(('synthetic_snapshot',))
        if 'current_database()' in text:
            return Result(('fixture_source', '192.0.2.1', 5432))
        if 'pg_database WHERE' in text:
            return Result((1,) if self.exists else None)
        return Result(None)
    def rollback(self):
        self.statements.append('ROLLBACK')


@pytest.fixture
def capture(backup, tmp_path):
    folder = tmp_path / 'p01_fixture'; folder.mkdir()
    archive = folder / 'database.dump'; archive.write_bytes(b'synthetic archive')
    receipt = {'schema': 'ky.smalltest_backup/1', 'status': 'captured', 'label': 'p01_fixture',
               'snapshot': 'synthetic_snapshot', 'source': {'database': 'fixture_source'},
               'script_sha256': backup.sha256(Path(backup.__file__)),
               'archive_sha256': backup.sha256(archive),
               'measurements': {'tables': {'public.fixture': {'rows': 1, 'sha256': 'a'*64}}, 'sequences': {}}}
    (folder / 'capture.json').write_text(json.dumps(receipt))
    return folder, receipt


@pytest.mark.parametrize('failure', ['none', 'changed_content', 'restore_error', 'cleanup_error', 'existing_target'])
def test_actual_restore_workflow_requires_equality_and_successful_cleanup(backup, capture, monkeypatch, failure):
    import psycopg
    folder, receipt = capture
    conn = Connection(exists=failure == 'existing_target', fail_drop=failure == 'cleanup_error')
    connections, programs = [], []
    def connect(*a, **kw):
        connections.append(kw)
        return conn
    def client(argv, settings):
        programs.append(argv)
        if failure == 'restore_error':
            raise backup.BackupRefused('pg_restore failed (synthetic)')
    monkeypatch.setattr(psycopg, 'connect', connect)
    monkeypatch.setattr(backup, 'run_client', client)
    actual = json.loads(json.dumps(receipt['measurements']))
    if failure == 'changed_content':
        actual['tables']['public.fixture']['sha256'] = 'b'*64
    monkeypatch.setattr(backup, 'measurements', lambda c: actual)
    if failure == 'none':
        proof = backup.restore_verify(folder, 'p01_fixture')
        assert proof['restore_verified'] is True and proof['target_removed'] is True
        assert proof['measurements'] == receipt['measurements']
        assert proof['capture_sha256'] == backup.sha256(folder / 'capture.json')
        assert json.loads((folder / 'restore.json').read_text()) == proof
    else:
        with pytest.raises((backup.BackupRefused, RuntimeError)):
            backup.restore_verify(folder, 'p01_fixture')
        assert not (folder / 'restore.json').exists()
    if failure == 'existing_target':
        assert not any('CREATE DATABASE' in q or 'DROP DATABASE' in q for q in conn.statements)
        assert not programs
    else:
        assert any('CREATE DATABASE "ky_restore_p01_fixture"' in q for q in conn.statements)
        assert any('DROP DATABASE "ky_restore_p01_fixture"' in q for q in conn.statements)
        assert programs[0][0] == 'pg_restore' and '--exit-on-error' in programs[0]
    assert all(kw['host'] == kw['hostaddr'] == '127.0.0.1' for kw in connections)


@pytest.mark.parametrize('drift', [False, True])
def test_actual_snapshot_workflow_binds_dump_and_measurements_to_one_readonly_snapshot(backup, tmp_path, monkeypatch, drift):
    import psycopg
    monkeypatch.setenv('DATABASE_URL', '://'.join(['postgresql', 'fixture.invalid/fixture_source']))
    conn = Connection()
    monkeypatch.setattr(psycopg, 'connect', lambda *a, **kw: conn)
    measured = {'tables': {'public.fixture': {'rows': 1, 'sha256': 'a'*64}},
                'sequences': {'public.seq': {'last_value': 1, 'is_called': True}}}
    after = json.loads(json.dumps(measured))
    if drift:
        after['sequences']['public.seq']['last_value'] = 2
    values = iter([measured, after])
    monkeypatch.setattr(backup, 'measurements', lambda c: next(values))
    def client(argv, settings):
        assert argv[0] == 'pg_dump' and '--snapshot=synthetic_snapshot' in argv
        assert '--format=custom' in argv and '--no-owner' in argv and '--no-privileges' in argv
        Path(argv[-1]).write_bytes(b'synthetic archive')
    monkeypatch.setattr(backup, 'run_client', client)
    folder = tmp_path / 'p01_fixture'
    if drift:
        with pytest.raises(backup.BackupRefused, match='changed during capture'):
            backup.snapshot(folder, 'p01_fixture')
        assert not (folder / 'capture.json').exists()
    else:
        proof = backup.snapshot(folder, 'p01_fixture')
        assert proof['measurements'] == measured
        assert proof['archive_sha256'] == backup.sha256(folder / 'database.dump')
        assert proof['backup_taken'] is True and proof['restore_verified'] is None
        assert (folder / 'capture.json').is_file()
    assert conn.statements[0] == 'BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY'


def test_table_fingerprints_measure_real_row_bytes_and_sequence_state(backup):
    # Only the SQL transport is faked; measurement loops/hash framing are real.
    rows = ['{"id":1,"value":"a"}', '{"id":2,"value":null}']
    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def execute(self, query):
            assert 'ORDER BY row_to_json(t)::text COLLATE "C"' in query.as_string(None)
        def __iter__(self): return iter((row,) for row in rows)
    class MeasureConnection:
        def execute(self, query):
            text = query if isinstance(query, str) else query.as_string(None)
            if 'pg_catalog.pg_class' in text:
                return type('Relations', (), {'fetchall': lambda self: [('public', 'fixture', 'r'), ('public', 'seq', 'S')]})()
            if 'pg_largeobject_metadata' in text: return Result((False,))
            if 'last_value' in text: return Result((2, True))
            return Result(None)
        def cursor(self, name): return Cursor()
    expected_digest = hashlib.sha256()
    for row in rows:
        encoded = row.encode('utf-8')
        expected_digest.update(len(encoded).to_bytes(8, 'big') + encoded)
    assert backup.measurements(MeasureConnection()) == {
        'tables': {'public.fixture': {'rows': 2, 'sha256': expected_digest.hexdigest()}},
        'sequences': {'public.seq': {'last_value': 2, 'is_called': True}}}


@pytest.mark.parametrize('service', ['synthetic_redirect', ''])
def test_restore_refuses_inherited_service_before_connecting(backup, capture, monkeypatch, service):
    import psycopg
    folder, _ = capture
    monkeypatch.setenv('PGSERVICE', service)
    monkeypatch.setattr(psycopg, 'connect', lambda *a, **kw: pytest.fail('inherited service reached libpq'))
    with pytest.raises(backup.BackupRefused, match='PGSERVICE'):
        backup.restore_verify(folder, 'p01_fixture')
    assert not (folder / 'restore.json').exists()
