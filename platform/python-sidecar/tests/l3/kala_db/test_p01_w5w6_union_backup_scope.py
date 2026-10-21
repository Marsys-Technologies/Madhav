"""M-W56-6: the REAL `w5w6_union` scope file captured by the real scoped mechanism (pg_dump directory archive, SQL content measurement), CI only.

Uses the guarded isolated Kāla database fixture (loopback test cluster, never production). The database holds one minimal table per name the reviewed
scope file lists (the real names, not a synthetic scope), because the claim under test is about THAT file: the scoped capture records the union scope's
digest, and its scoped-content digest (SR-BACKUP-VALIDITY-A8) moves when a J-6 head table or a K9 table changes, which is what keeps a backup valid
exactly while the content it describes is unchanged. The production tables' definitions, triggers and foreign keys are not reproduced here; the
capture-time refusals for those (scoped_catalog) are exercised against the real catalog by the other scopes' suite.
"""
import json
import sys
import uuid
from pathlib import Path

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'platform/scripts'))
import backup_v5_small_test_job as backup
import v5_small_test_shared as shared

CHART = '482012f1-710e-4a25-994a-93821f5871aa'
J6_TABLE = 'public.kala_gochara_authority'            # written by head_operation.change_head
K9_TABLE = 'public.kala_layer_candidate_grain'         # written by every K9 writer's grain attestation
K9_WRITER_TABLE = 'public.kala_obstruction'            # written by the last writer of the closed plan


def scope_tables():
    return backup.load_scope(name='w5w6_union')['tables']


@pytest.fixture
def union_db(isolated_kala_db_dsn, monkeypatch):
    settings = psycopg.conninfo.conninfo_to_dict(isolated_kala_db_dsn)
    assert settings['host'] in ('127.0.0.1', 'localhost')
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as conn:
        for table in scope_tables():
            conn.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
        conn.execute("""CREATE TABLE public._migrations_applied (id serial PRIMARY KEY, filename text UNIQUE NOT NULL,
            applied_at timestamptz NOT NULL DEFAULT now(), sha256 text NOT NULL, sql_identity text)""")
        conn.execute("INSERT INTO public._migrations_applied (filename, applied_at, sha256) VALUES ('0001_legacy.sql', '2025-01-01 00:00:00.5+00', 'legacytoken')")
        for table in scope_tables():
            if table != 'public._migrations_applied':
                conn.execute(f'CREATE TABLE {table} (id serial PRIMARY KEY, chart_id uuid, payload text)')
                conn.execute(f"INSERT INTO {table} (chart_id, payload) VALUES ('{CHART}', 'seed')")
    monkeypatch.setenv('DATABASE_URL', isolated_kala_db_dsn)
    return isolated_kala_db_dsn


def capture(tmp_path):
    label = 'w56_' + uuid.uuid4().hex[:20]
    return label, backup.snapshot(tmp_path / label, label, 'w5w6_union')


def fresh_digest(dsn, receipt):
    measured = backup.measure_scope_now(sorted(receipt['measurements']['tables']), sorted(receipt['measurements']['sequences']), dsn)
    return shared.scoped_content_digest(measured)


def test_the_capture_records_the_union_scope_digest_and_archives_exactly_its_tables(union_db, tmp_path):
    label, receipt = capture(tmp_path)
    assert receipt['schema'] == 'ky.smalltest_backup/2' and receipt['backup_taken'] is True
    assert receipt['scope']['name'] == 'w5w6_union'
    assert receipt['scope']['sha256'] == shared.SCOPED_BACKUP_SCOPE_SHA256S['w5w6_union']       # the digest the executor-loaded policy pins
    assert receipt['scope']['tables'] == scope_tables() and receipt['scope']['closure'] == []       # no foreign-key parent had to be added
    assert {J6_TABLE, K9_TABLE, K9_WRITER_TABLE, 'public.kala_layer_head', 'public._migrations_applied'} <= set(receipt['measurements']['tables'])
    listed = backup.archive_tables(tmp_path / label / 'database.dir', backup.scratch_settings(label))
    assert listed['data'] == listed['definitions'] == set(scope_tables())
    assert receipt['scoped_content_digest'] == shared.scoped_content_digest(receipt['measurements'])


@pytest.mark.parametrize('table', [J6_TABLE, K9_TABLE, K9_WRITER_TABLE])
def test_the_scoped_content_digest_moves_when_a_head_table_or_a_k9_table_changes_and_only_then(union_db, tmp_path, table):
    _, receipt = capture(tmp_path)
    assert fresh_digest(union_db, receipt) == receipt['scoped_content_digest']                         # unchanged database: the backup still describes it
    with psycopg.connect(union_db, autocommit=True) as conn:
        conn.execute(f"UPDATE {table} SET payload = 'changed' WHERE id = 1")
    assert fresh_digest(union_db, receipt) != receipt['scoped_content_digest']                         # one changed row of this table: no longer valid
    with psycopg.connect(union_db, autocommit=True) as conn:
        conn.execute(f"UPDATE {table} SET payload = 'seed' WHERE id = 1")
    assert fresh_digest(union_db, receipt) == receipt['scoped_content_digest']                         # restored content: valid again (no clock)


def test_a_table_outside_the_union_scope_does_not_move_the_digest(union_db, tmp_path):
    with psycopg.connect(union_db, autocommit=True) as conn:
        conn.execute("CREATE TABLE public.w56_outside (id serial PRIMARY KEY, payload text)")
        conn.execute("INSERT INTO public.w56_outside (payload) VALUES ('x')")
    _, receipt = capture(tmp_path)
    assert 'public.w56_outside' not in receipt['measurements']['tables']
    with psycopg.connect(union_db, autocommit=True) as conn:
        conn.execute("UPDATE public.w56_outside SET payload = 'y'")
    assert fresh_digest(union_db, receipt) == receipt['scoped_content_digest']
