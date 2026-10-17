"""J-2a scoped small-test backup: real pg_dump (directory, parallel, snapshot) / pg_restore / SQL measurement, CI only.

Uses the guarded isolated Kāla database fixture (loopback test cluster, never
production). The scope under test is a small synthetic one written to a temp
file, shaped like the real one: a written table, a table written only by a
trigger, an FK parent that is not listed (the runtime closure must add it) and a
table outside the scope that holds rows the archive must NOT contain.
"""
import json
import sys
import uuid
from pathlib import Path

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'platform/scripts'))
import backup_v5_small_test_job as backup

SCHEMA_SQL = """
DROP SCHEMA IF EXISTS p02 CASCADE;
CREATE SCHEMA p02;
CREATE TABLE p02.parent (id serial PRIMARY KEY, label text);
CREATE TABLE p02.written (id serial PRIMARY KEY, parent_id integer REFERENCES p02.parent(id), value text, extra jsonb);
CREATE TABLE p02.audit (id serial PRIMARY KEY, note text);
CREATE TABLE p02.other (id integer, secret text);
CREATE TABLE p02.child_of_written (id integer, written_id integer REFERENCES p02.written(id) ON DELETE SET NULL);
CREATE FUNCTION p02.log_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN INSERT INTO p02.audit (note) VALUES ('changed ' || NEW.id); RETURN NEW; END $$;
CREATE TRIGGER written_audit AFTER UPDATE ON p02.written FOR EACH ROW EXECUTE FUNCTION p02.log_change();
INSERT INTO p02.parent (label) VALUES ('p1'), ('p2');
INSERT INTO p02.written (parent_id, value, extra) VALUES (1, 'original', '{"a":1}'), (2, NULL, NULL), (2, 'dup', NULL);
INSERT INTO p02.audit (note) VALUES ('seed');
INSERT INTO p02.other VALUES (1, 'must-not-be-archived');
"""


def write_scope(path, written=('p02.written', 'p02.audit'), guarded=('p02.child_of_written',)):
    path.write_text(json.dumps({
        'schema': 'ky.smalltest_backup_scope/1', 'name': 'small_test',
        'written': [{'table': t} for t in written], 'context': [],
        'guarded_children': [{'table': t} for t in guarded]}))


@pytest.fixture
def scoped(isolated_kala_db_dsn, tmp_path, monkeypatch):
    settings = psycopg.conninfo.conninfo_to_dict(isolated_kala_db_dsn)
    assert settings['host'] in ('127.0.0.1', 'localhost')
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as conn:
        conn.execute(SCHEMA_SQL)
    scope_file = tmp_path / 'scope.json'
    write_scope(scope_file)
    monkeypatch.setattr(backup, 'SCOPE_FILE', scope_file)
    monkeypatch.setenv('DATABASE_URL', isolated_kala_db_dsn)
    fixed = backup.scratch_settings

    def scratch(name):
        target = fixed(name)
        target.update(port=settings.get('port', '5432'), user=settings['user'], password=settings.get('password', ''))
        return target
    monkeypatch.setattr(backup, 'scratch_settings', scratch)
    return isolated_kala_db_dsn, tmp_path, scope_file


def capture(dsn, tmp_path):
    label = 'p02_' + uuid.uuid4().hex
    folder = tmp_path / label
    return folder, label, backup.snapshot(folder, label, 'small_test')


def assert_target_removed(dsn, label):
    with psycopg.connect(dsn) as conn:
        assert conn.execute('SELECT 1 FROM pg_database WHERE datname = %s', ('ky_restore_' + label,)).fetchone() is None


def test_scoped_archive_holds_exactly_scope_plus_fk_parents_and_restores_equal(scoped):
    dsn, tmp_path, _ = scoped
    folder, label, receipt = capture(dsn, tmp_path)
    assert receipt['schema'] == 'ky.smalltest_backup/2' and receipt['backup_taken'] is True
    assert receipt['restore_verified'] is None
    # the unlisted FK parent is added by the runtime closure; the unrelated table is not archived
    assert receipt['scope']['tables'] == ['p02.audit', 'p02.parent', 'p02.written']
    assert receipt['scope']['closure'] == ['p02.parent']
    assert 'p02.other' not in receipt['measurements']['tables'] and 'p02.child_of_written' not in receipt['scope']['tables']
    assert backup.archive_data_tables(folder / 'database.dir', backup.scratch_settings(label)) == set(receipt['scope']['tables'])
    assert receipt['scope']['sequences'] == ['p02.audit_id_seq', 'p02.parent_id_seq', 'p02.written_id_seq']
    assert (folder / 'database.dir').is_dir() and not (folder / 'database.dump').exists()
    proof = backup.restore_verify(folder, label, 'small_test')
    assert proof['restore_verified'] is True and proof['target_removed'] is True and proof['scoped'] is True
    assert proof['measurements'] == receipt['measurements']
    assert proof['scope_sha256'] == receipt['scope']['sha256'] and proof['validity'] == receipt['validity']
    assert json.loads((folder / 'restore.json').read_text()) == proof
    assert_target_removed(dsn, label)


def test_equal_row_count_changed_content_refuses_scoped_restore(scoped, monkeypatch):
    dsn, tmp_path, _ = scoped
    folder, label, _ = capture(dsn, tmp_path)
    real = backup.run_client

    def altered(argv, settings, timeout=14400):
        real(argv, settings, timeout)
        assert argv[0] == 'pg_restore'
        with psycopg.connect(**settings, autocommit=True) as target:
            target.execute("ALTER TABLE p02.written DISABLE TRIGGER ALL")
            target.execute("UPDATE p02.written SET value = 'changed' WHERE id = 1")
    monkeypatch.setattr(backup, 'run_client', altered)
    with pytest.raises(backup.BackupRefused, match='restore row counts/content hashes/sequence state'):
        backup.restore_verify(folder, label, 'small_test')
    assert not (folder / 'restore.json').exists()
    assert_target_removed(dsn, label)


def test_sql_measurement_is_order_independent_and_sensitive_to_every_row_change(scoped):
    dsn, _, _ = scoped
    tables = ['p02.written']

    def measure(*statements):
        with psycopg.connect(dsn, autocommit=True) as conn:
            for s in statements:
                conn.execute(s)
            conn.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
            out = backup.scoped_measurements(conn, tables, [])['tables']['p02.written']
            conn.rollback()
            return out
    from psycopg import sql
    with psycopg.connect(dsn) as conn:
        statement = backup._row_aggregate_sql(sql.Identifier('p02', 'written')).as_string(conn).upper()
    assert 'ORDER BY' not in statement and statement.count('SELECT') >= 1 and 'ONLY' in statement   # no sort, no row stream
    base = measure()
    assert base['rows'] == 3
    # physical reordering is not a change
    assert measure('ALTER TABLE p02.written DISABLE TRIGGER ALL', 'UPDATE p02.written SET value = value') == base
    changed = measure("UPDATE p02.written SET value = 'x' WHERE id = 1")
    assert changed['rows'] == 3 and changed['sha256'] != base['sha256']
    duplicated = measure("INSERT INTO p02.written (parent_id, value, extra) VALUES (2, 'x', NULL)")
    assert duplicated['rows'] == 4 and duplicated['sha256'] not in (base['sha256'], changed['sha256'])


@pytest.mark.parametrize('fault', ['trigger_outside_scope', 'table_missing', 'unreviewed_cascade', 'over_budget'])
def test_scope_the_database_cannot_honour_is_refused_before_any_dump(scoped, monkeypatch, fault):
    dsn, tmp_path, scope_file = scoped
    dumps = []
    monkeypatch.setattr(backup, 'run_client', lambda *a, **k: dumps.append(a))
    reason = {'trigger_outside_scope': 'trigger on a scoped table writes outside the scope',
              'table_missing': 'scope table missing on source',
              'unreviewed_cascade': 'reaches an unreviewed table',
              'over_budget': 'over the .* 30-minute budget'}[fault]
    if fault == 'trigger_outside_scope':
        write_scope(scope_file, written=('p02.written',))          # the trigger writes p02.audit
    elif fault == 'table_missing':
        write_scope(scope_file, written=('p02.written', 'p02.audit', 'p02.nonexistent'))
    elif fault == 'unreviewed_cascade':
        write_scope(scope_file, guarded=())                         # child_of_written is neither archived nor guarded
    else:
        monkeypatch.setattr(backup, 'SCOPED_DATA_BUDGET_BYTES', 1)
    with pytest.raises(backup.BackupRefused, match=reason):
        backup.snapshot(tmp_path / ('p02_' + uuid.uuid4().hex), 'p02_refused', 'small_test')
    assert not dumps


def test_sequence_moving_during_the_dump_refuses_capture(scoped, monkeypatch):
    dsn, tmp_path, _ = scoped
    real = backup.run_client

    def moving(argv, settings, timeout=14400):
        real(argv, settings, timeout)
        with psycopg.connect(dsn, autocommit=True) as other:
            other.execute("SELECT nextval('p02.audit_id_seq')")
    monkeypatch.setattr(backup, 'run_client', moving)
    folder = tmp_path / 'p02_drift'
    with pytest.raises(backup.BackupRefused, match='sequence state changed during capture'):
        backup.snapshot(folder, 'p02_drift', 'small_test')
    assert not (folder / 'capture.json').exists()


def test_dump_that_leaks_out_of_scope_data_refuses_capture(scoped, monkeypatch):
    dsn, tmp_path, _ = scoped
    real = backup.run_client

    def leaky(argv, settings, timeout=14400):
        real([a for a in argv if not a.startswith('--exclude-table-data')], settings, timeout)
    monkeypatch.setattr(backup, 'run_client', leaky)
    with pytest.raises(backup.BackupRefused, match='archive data entries differ from the scope'):
        backup.snapshot(tmp_path / 'p02_leak', 'p02_leak', 'small_test')
    assert not (tmp_path / 'p02_leak' / 'capture.json').exists()


@pytest.mark.parametrize('operation', ['snapshot', 'restore-verify'])
def test_failed_client_cannot_earn_scoped_success_after_writing_a_real_archive(scoped, tmp_path, monkeypatch, capsys, operation):
    dsn, _, _ = scoped
    root = tmp_path / 'executor'
    label = 'p02_' + uuid.uuid4().hex
    target = root / 'run/ops/backups' / label
    target.parent.mkdir(parents=True)
    monkeypatch.setenv('KY_ROOT', str(root))
    if operation == 'restore-verify':
        backup.snapshot(target, label, 'small_test')
    real_run = backup.subprocess.run
    clients = []

    def failed_exit(argv, **kwargs):
        result = real_run(argv, **kwargs)
        if argv[1:2] == ['--list']:
            return result
        assert result.returncode == 0, 'the real local client must complete before exit injection'
        clients.append(argv[0])
        result.returncode = 1
        return result
    monkeypatch.setattr(backup.subprocess, 'run', failed_exit)
    assert backup.main(['--operation', operation, '--label', label, '--scope', 'small_test', '--execute']) == 1
    output = capsys.readouterr()
    assert not output.out and 'failed (exit 1' in output.err
    assert clients == ['pg_dump' if operation == 'snapshot' else 'pg_restore']
    assert not (target / ('capture.json' if operation == 'snapshot' else 'restore.json')).exists()
    assert_target_removed(dsn, label)


def test_tampered_archive_file_is_refused_before_any_restore_connection(scoped, monkeypatch):
    dsn, tmp_path, _ = scoped
    folder, label, _ = capture(dsn, tmp_path)
    victim = sorted((folder / 'database.dir').glob('*.dat.gz'))[0]
    victim.write_bytes(victim.read_bytes() + b'x')
    connections = []
    real = psycopg.connect
    monkeypatch.setattr(psycopg, 'connect', lambda *a, **k: connections.append(1) or real(*a, **k))
    with pytest.raises(backup.BackupRefused, match='file hashes differ'):
        backup.restore_verify(folder, label, 'small_test')
    assert not connections and not (folder / 'restore.json').exists()
