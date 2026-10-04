#!/usr/bin/env python3
"""with_app_db.py [--expect-role ROLE] [--selftest] -- COMMAND [ARGS...]

Runs COMMAND with DATABASE_URL set IN-PROCESS. NO credential is ever typed, printed, logged or written to a file.
This is the documented production path of the earlier dispatches (platform/scripts/dispatch_sampurti_*.py: "DATABASE_URL set via
gcloud secrets, never .env.local"; platform/scripts/gochara/flip_authority.py: `gcloud secrets versions access latest
--secret=amjis-pipeline-db-url` with cloud-sql-proxy listening on 127.0.0.1:5433), made non-interactive:
  1. read secret `amjis-pipeline-db-url` (project madhav-astrology) with the operator's own gcloud identity;
  2. rewrite the host part to the standing proxy 127.0.0.1:5433 (a Cloud SQL socket `host=` query parameter is dropped);
  3. log in once, assert current_user == --expect-role (default amjis_app) and print ONLY `with_app_db: role=<name> OK`
     (or `ROLE_MISMATCH got <name> expected <name>`, exit 4, nothing started);
  4. exec COMMAND with DATABASE_URL in its environment only.
Used by: suvarna_level_wave.py (dispatcher), build_fact_identity_index.py (G-IDX, which reads ONLY the DATABASE_URL environment variable).
Exit: 3 secret unreadable / proxy down / login failed; 4 role mismatch; 64 usage; otherwise the exit of COMMAND (exec).
"""
import os, subprocess, sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

SECRET = 'amjis-pipeline-db-url'; PROJECT = 'madhav-astrology'; PROXY = '127.0.0.1:5433'

def rewrite(url):
    u = urlsplit(url.strip())
    if u.scheme not in ('postgres', 'postgresql'): raise ValueError('not a postgres url')
    userinfo = u.netloc.rsplit('@', 1)[0] + '@' if '@' in u.netloc else ''
    q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True) if k != 'host']
    return urlunsplit((u.scheme, userinfo + PROXY, u.path, urlencode(q), ''))

def selftest():
    a = rewrite('postgresql://usr:dummy@/amjis?host=/cloudsql/p:r:i&sslmode=disable')
    b = rewrite('postgres://usr:dummy@10.1.2.3:5432/amjis')
    assert a == 'postgresql://usr:dummy@127.0.0.1:5433/amjis?sslmode=disable', 'case1'
    assert b == 'postgres://usr:dummy@127.0.0.1:5433/amjis', 'case2'
    print('with_app_db selftest PASS (synthetic urls only)')

def main():
    argv = sys.argv[1:]
    if argv[:1] == ['--selftest']: selftest(); return 0
    role = 'amjis_app'
    if argv[:1] == ['--expect-role']:
        if len(argv) < 2: return 64
        role, argv = argv[1], argv[2:]
    if not argv or argv[0] != '--' or len(argv) < 2: print('usage: with_app_db.py [--expect-role R] -- COMMAND ...', file=sys.stderr); return 64
    cmd = argv[1:]
    try:
        r = subprocess.run(['gcloud', 'secrets', 'versions', 'access', 'latest', '--secret=' + SECRET, '--project=' + PROJECT],
                           capture_output=True, text=True, timeout=60)
        if r.returncode: raise RuntimeError('gcloud rc=%d' % r.returncode)
        url = rewrite(r.stdout)
        import psycopg
        with psycopg.connect(url, connect_timeout=10) as c:
            got = c.execute('select current_user').fetchone()[0]
    except Exception as e:                       # class name only: never the message (it could quote the url)
        print('with_app_db: FAIL %s (secret unreadable, proxy 127.0.0.1:5433 down, or login refused)' % type(e).__name__, file=sys.stderr); return 3
    if got != role:
        print('with_app_db: ROLE_MISMATCH got %s expected %s; nothing started' % (got, role), file=sys.stderr); return 4
    print('with_app_db: role=%s OK' % got, file=sys.stderr)
    env = dict(os.environ, DATABASE_URL=url)
    os.execvpe(cmd[0], cmd, env)

if __name__ == '__main__':
    sys.exit(main())
