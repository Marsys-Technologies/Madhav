"""J4B rehearsal regressions; live runs use the suite-owned guarded cluster.

The safety probe deliberately uses a recording psql: reverting the lifecycle
must never let an old DROP ROLE reach an existing cluster principal.
"""
from pathlib import Path
import os
import subprocess
import sys
import pytest

REPO = Path(__file__).resolve().parents[3]
HERE = REPO / 'platform/scripts/gochara/rehearsal'
sys.path.insert(0, str(REPO / 'platform/scripts/governance/__tests__'))
from _gochara_readback_pg import disposable_pg  # noqa: F401


@pytest.mark.parametrize('missing', ['', 'data_plane_schema_owner'])
def test_existing_roles_are_never_dropped_even_on_fixture_failure(tmp_path, missing):
    shim = tmp_path / 'psql'
    log = tmp_path / 'psql.log'
    shim.write_text('''#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
commands = [args[i+1] for i,a in enumerate(args[:-1]) if a == '-c']
sql = '\\n'.join(commands) if commands else sys.stdin.read()
with open(os.environ['REHEARSAL_SQL_LOG'], 'a') as f: f.write(sql + '\\n')
if 'REASSIGN OWNED' in sql or 'DROP OWNED' in sql or ('DROP ROLE' in sql and sql.strip() != 'DROP ROLE ' + os.environ['MISSING_ROLE']):
    sys.exit(71)  # fail closed; never forward a destructive historical command
if 'inet_server_addr' in sql: print('127.0.0.1')
elif 'pg_database' in sql: print('0')
elif 'pg_roles' in sql:
    if not os.environ['MISSING_ROLE'] or ("rolname='" + os.environ['MISSING_ROLE'] + "'") not in sql: print('1')  # every canonical role predates this fixture
elif 'DROP SCHEMA' in sql: sys.exit(70)  # inject failure after the resource setup
''')
    shim.chmod(0o755)
    env = {k:v for k,v in os.environ.items() if not k.startswith('PG')}
    env.update(PATH=str(tmp_path) + os.pathsep + env['PATH'], PGHOST='127.0.0.1', PGPORT='55433',
               REPO=str(REPO), REHEARSAL_SQL_LOG=str(log), MISSING_ROLE=missing)
    proc = subprocess.run(['bash', str(HERE / 'run_window_rehearsal.sh')], env=env,
                          capture_output=True, text=True, timeout=30)
    commands = log.read_text()
    protected_commands = commands.replace('CREATE ROLE ' + missing + ' NOLOGIN', '').replace('DROP ROLE ' + missing, '') if missing else commands
    assert not any(x in protected_commands for x in ('DROP ROLE', 'REASSIGN OWNED', 'DROP OWNED', 'CREATE ROLE')), commands
    if missing:
        assert 'CREATE ROLE ' + missing in commands and 'DROP ROLE ' + missing in commands
    assert proc.returncode == 70, proc.stdout + proc.stderr
    assert 'DROP DATABASE' in commands, 'failed fixture must clean its own database'


@pytest.mark.parametrize('today', ['0', '1'])
def test_current_window_rehearsal(disposable_pg, tmp_path, today):
    """Real runner + real 1378; synthetic prereqs, full sitting release gates."""
    cl = disposable_pg
    # Preserve existing cluster role identities/attributes through success AND cleanup.
    before = cl.psql('SELECT oid,rolname,rolcanlogin,rolinherit,rolconnlimit FROM pg_roles ORDER BY oid')
    env = {k:v for k,v in os.environ.items() if not k.startswith('PG')}
    env.update(cl.env())
    env.pop('PGSERVICEFILE', None)
    env.update(REPO=str(REPO), TODAY=today, STRICT='1', REHEARSAL_OUT=str(tmp_path / 'evidence'))
    proc = subprocess.run(['bash', str(HERE / 'run_window_rehearsal.sh')], env=env,
                          cwd=REPO, capture_output=True, text=True, timeout=240)
    (tmp_path / 'rehearsal.log').write_text(proc.stdout + proc.stderr)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert '0 failed, 0 finding(s)' in proc.stdout
    assert 'PASS R2-registry-1243 ' in proc.stdout
    assert 'PASS R3-revoke-1302 ' in proc.stdout
    assert '1378 ACL closure' in proc.stdout
    assert (tmp_path / 'evidence/pre-window/R2-registry-1243-file.out').read_text().count('source_unavailable') == 2
    assert cl.psql('SELECT oid,rolname,rolcanlogin,rolinherit,rolconnlimit FROM pg_roles ORDER BY oid') == before
