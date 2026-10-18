"""J4OPS SQL executes on the suite's guarded fixture, never a second server.

Fixture grants below are test setup, not an allocated/production migration.
These tests measure ACL capture/read-only enforcement, not a window qualification.
The existing sidecar tests/ CI discovery collects this file automatically.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from .test_a53_inventory import create_am5_database, drop_am5_database

ROOT = Path(__file__).resolve().parents[5]
BUNDLE = ROOT / 'platform/scripts/j4ops'
SPEC = importlib.util.spec_from_file_location('j4ops_readback_db', BUNDLE / 'readback.py')
rb = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rb)


@pytest.fixture(scope='module')
def database():
    psycopg = pytest.importorskip('psycopg')
    admin, name, dsn = create_am5_database(tag='j4ops', faithful=True)
    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            yield conn, name
    finally:
        drop_am5_database(admin, name)


def environment(conn):
    # Never put a DSN on argv or print it. The local cluster is trust-auth (no password);
    # the CI service container requires its throwaway password, passed via the environment only.
    env = dict(os.environ, PGHOST=conn.info.host, PGPORT=str(conn.info.port),
               PGDATABASE=conn.info.dbname, PGUSER=conn.info.user)
    if conn.info.password:
        env['PGPASSWORD'] = conn.info.password
    return env


def run_capture(conn, name, phase='provision'):
    return rb.capture(phase, name, environ=environment(conn))


def test_grant_only_1378_fixture_lacks_l1_reads_and_capture_reports_it(database):
    conn, name = database
    identity, cells, _ = run_capture(conn, name)
    assert identity['transaction_read_only'] == 'on'
    assert len(cells) == 36
    missing = rb.grant_problems(cells)
    assert len(missing) == 4
    assert all('SELECT' in problem and ('chart_facts' in problem or 'chart_dashas' in problem) for problem in missing)


def test_fixture_positive_reads_and_column_level_negative_writes(database):
    conn, name = database
    conn.execute('GRANT SELECT ON public.chart_facts, public.chart_dashas TO gochara_verifier, gochara_sealer')
    try:
        _, cells, _ = run_capture(conn, name)
        assert rb.grant_problems(cells) == []
        conn.execute('GRANT UPDATE (fact_subject) ON public.chart_facts TO gochara_verifier')
        try:
            _, cells, _ = run_capture(conn, name)
            assert rb.grant_problems(cells) == ['gochara_verifier chart_facts UPDATE differs']
        finally:
            conn.execute('REVOKE UPDATE (fact_subject) ON public.chart_facts FROM gochara_verifier')
        conn.execute('GRANT INSERT (chart_id) ON public.ka_gochara_eval_window_verification TO data_plane_builder')
        try:
            _, cells, _ = run_capture(conn, name)
            assert rb.grant_problems(cells) == ['data_plane_builder ka_gochara_eval_window_verification INSERT differs']
        finally:
            conn.execute('REVOKE INSERT (chart_id) ON public.ka_gochara_eval_window_verification FROM data_plane_builder')
    finally:
        conn.execute('REVOKE SELECT ON public.chart_facts, public.chart_dashas FROM gochara_verifier, gochara_sealer')


def test_actual_readonly_session_refuses_dml_cte_without_changing_facts(database, monkeypatch):
    conn, name = database
    before = conn.execute('SELECT count(*) FROM public.chart_facts').fetchone()[0]
    assert before > 0
    monkeypatch.setattr(rb, 'sql_bytes', lambda _: b'WITH removed AS (DELETE FROM public.chart_facts RETURNING fact_id) SELECT count(*) FROM removed;')
    with pytest.raises(ValueError, match='SQL failed'):
        run_capture(conn, name)
    assert conn.execute('SELECT count(*) FROM public.chart_facts').fetchone()[0] == before


def test_actual_second_window_sql_captures_catalogue_without_qualifying_fixture(database):
    conn, name = database
    identity, capture, _ = run_capture(conn, name, phase='second-window')
    rb.check_identity(identity, name)
    assert set(capture) == {'server_major', 'ledger', 'functions', 'triggers', 'dormant_writes', 'app_schema_create'}
    assert capture['functions'] and capture['triggers']
    assert all('ka_gochara_' in f['signature'] for f in capture['functions'])
    # No expected second-window state is fabricated from this fixture.


def test_cli_records_self_hash_and_verifiable_manifest_and_refuses_overwrite(database, tmp_path):
    conn, name = database
    output = tmp_path / 'readback'
    cmd = [sys.executable, '-B', str(BUNDLE / 'readback.py'), '--phase', 'provision',
           '--expect-db', name, '--out', str(output), '--runner-sha256',
           hashlib.sha256((BUNDLE / 'readback.py').read_bytes()).hexdigest()]
    result = subprocess.run(cmd, capture_output=True, text=True, env=environment(conn))
    assert result.returncode == 1, result.stderr  # four genuinely missing grants
    record = json.loads(result.stdout)
    assert record['status'] == 'READBACK_MISMATCH'
    assert record['operation_completed'] is False
    for line in (output / 'MANIFEST.sha256').read_text().splitlines():
        expected, filename = line.split('  ', 1)
        assert hashlib.sha256((output / filename).read_bytes()).hexdigest() == expected
    again = subprocess.run(cmd, capture_output=True, text=True, env=environment(conn))
    assert again.returncode == 2
    assert not again.stdout
