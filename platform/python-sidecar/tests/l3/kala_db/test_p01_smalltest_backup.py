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
