"""P01: actual logical capture/restore/count/content/sequence proof, CI only.

Uses the existing guarded isolated Kāla database fixture. The operation's
scratch endpoint is redirected only to that same guarded loopback CI service;
no production target, Docker lifecycle or external connection is used here.
"""
import json
import sys
import uuid
from pathlib import Path

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'platform/scripts'))
import backup_v5_small_test_job as backup


@pytest.fixture
def captured(isolated_kala_db_dsn, tmp_path, monkeypatch):
    settings = psycopg.conninfo.conninfo_to_dict(isolated_kala_db_dsn)
    assert settings['host'] in ('127.0.0.1', 'localhost')
    # The fixture has already checked the actual server, not just its URL.
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as conn:
        conn.execute('CREATE SCHEMA IF NOT EXISTS p01_fixture')
        conn.execute('DROP TABLE IF EXISTS p01_fixture.children')
        conn.execute('DROP TABLE IF EXISTS p01_fixture.rows')
        conn.execute('CREATE TABLE p01_fixture.rows (id serial PRIMARY KEY, value text, extra jsonb)')
        conn.execute("INSERT INTO p01_fixture.rows (value, extra) VALUES ('original', '{\"a\":1}'), (NULL, NULL)")
        conn.execute('CREATE TABLE p01_fixture.children (id integer REFERENCES p01_fixture.rows(id))')
        conn.execute('INSERT INTO p01_fixture.children VALUES (1)')
    label = 'p01_' + uuid.uuid4().hex
    folder = tmp_path / label
    monkeypatch.setenv('DATABASE_URL', isolated_kala_db_dsn)
    fixed_scratch = backup.scratch_settings
    def scratch(name):
        target = fixed_scratch(name)
        target.update(port=settings.get('port', '5432'), user=settings['user'], password=settings.get('password', ''))
        return target
    monkeypatch.setattr(backup, 'scratch_settings', scratch)
    proof = backup.snapshot(folder, label)
    assert proof['backup_taken'] is True and proof['restore_verified'] is None
    assert proof['measurements']['tables']['p01_fixture.rows']['rows'] == 2
    assert proof['measurements']['sequences']['p01_fixture.rows_id_seq']['last_value'] == 2
    return folder, label, proof, isolated_kala_db_dsn


def assert_target_removed(source, label):
    with psycopg.connect(source) as conn:
        assert conn.execute('SELECT 1 FROM pg_database WHERE datname = %s', ('ky_restore_' + label,)).fetchone() is None


def test_complete_archive_restores_with_every_count_hash_and_sequence_equal(captured):
    folder, label, capture, source = captured
    proof = backup.restore_verify(folder, label)
    assert proof['measurements'] == capture['measurements']
    assert proof['restore_verified'] is True and proof['target_removed'] is True
    assert json.loads((folder / 'restore.json').read_text()) == proof
    assert_target_removed(source, label)


def test_equal_row_count_changed_content_refuses_real_restore(captured, monkeypatch):
    folder, label, _, source = captured
    restore_client = backup.run_client
    def altered(argv, settings):
        restore_client(argv, settings)
        assert argv[0] == 'pg_restore'
        with psycopg.connect(**settings, autocommit=True) as target:
            target.execute("UPDATE p01_fixture.rows SET value = 'changed' WHERE id = 1")
    monkeypatch.setattr(backup, 'run_client', altered)
    with pytest.raises(backup.BackupRefused, match='restore row counts/content hashes/sequence state'):
        backup.restore_verify(folder, label)
    assert not (folder / 'restore.json').exists()
    assert_target_removed(source, label)


@pytest.mark.parametrize('operation', ['snapshot', 'restore-verify'])
def test_failed_client_cannot_earn_success_after_writing_real_archive_or_restored_data(
        captured, tmp_path, monkeypatch, capsys, operation):
    """Real source, dump, restore and measurements; inject only client exit 1.

    Even fully usable bytes/data cannot turn a failed client into an earned
    backup/restore signal. Keeping run_client real detects its guard's removal.
    """
    folder, label, _, source = captured
    root = tmp_path / 'executor'
    if operation == 'snapshot':
        label = 'p01_' + uuid.uuid4().hex
    target = root / 'run/ops/backups' / label
    target.parent.mkdir(parents=True)
    if operation == 'restore-verify':
        folder.rename(target)
    monkeypatch.setenv('KY_ROOT', str(root))
    real_run = backup.subprocess.run
    clients = []
    def failed_exit(argv, **kwargs):
        assert argv[0] == ('pg_dump' if operation == 'snapshot' else 'pg_restore')
        result = real_run(argv, **kwargs)
        assert result.returncode == 0, 'the real local client must complete before exit injection'
        if operation == 'snapshot':
            assert Path(argv[-1]).stat().st_size > 0
        clients.append(argv[0])
        result.returncode = 1
        return result
    monkeypatch.setattr(backup.subprocess, 'run', failed_exit)
    assert backup.main(['--operation', operation, '--label', label, '--execute']) == 1
    output = capsys.readouterr()
    assert not output.out and 'failed (exit 1' in output.err
    assert len(clients) == 1
    assert not (target / ('capture.json' if operation == 'snapshot' else 'restore.json')).exists()
    assert_target_removed(source, label)


@pytest.mark.parametrize('invalid', ['missing', 'schema', 'status', 'snapshot', 'source', 'sequence',
                                   'source_database_missing', 'source_database_type', 'source_database_empty',
                                   'source_missing_endpoint', 'source_port_type', 'snapshot_type'])
def test_invalid_capture_never_emits_restore_success_or_creates_a_target(
        captured, tmp_path, monkeypatch, capsys, invalid):
    folder, label, receipt, source = captured
    root = tmp_path / 'executor'
    target = root / 'run/ops/backups' / label
    target.parent.mkdir(parents=True)
    folder.rename(target)
    path = target / 'capture.json'
    if invalid == 'missing':
        path.unlink()
    else:
        if invalid == 'sequence':
            receipt['measurements']['sequences']['p01_fixture.rows_id_seq']['is_called'] = 1
        elif invalid == 'source_database_missing':
            receipt['source'].pop('database')
        elif invalid == 'source_database_type':
            receipt['source']['database'] = 42
        elif invalid == 'source_database_empty':
            receipt['source']['database'] = ''
        elif invalid == 'source_missing_endpoint':
            receipt['source'].pop('address')
        elif invalid == 'source_port_type':
            receipt['source']['port'] = True
        elif invalid == 'snapshot_type':
            receipt['snapshot'] = ['not an exported snapshot identifier']
        else:
            receipt[invalid] = None
        path.write_text(json.dumps(receipt))
    monkeypatch.setenv('KY_ROOT', str(root))
    connections = []
    real_connect = psycopg.connect
    def connect(*args, **kwargs):
        connections.append(True)
        return real_connect(*args, **kwargs)
    monkeypatch.setattr(psycopg, 'connect', connect)
    assert backup.main(['--operation', 'restore-verify', '--label', label, '--execute']) == 1
    output = capsys.readouterr()
    assert not output.out and 'backup ' in output.err
    assert not (target / 'restore.json').exists()
    assert not connections, 'invalid capture must be refused before any restore connection'
    assert_target_removed(source, label)
