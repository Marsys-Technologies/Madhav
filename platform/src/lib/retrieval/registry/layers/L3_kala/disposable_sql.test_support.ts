/** Test-only SQL transport. No Docker/CLI clients, service startup or ambient DSN. */
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
export function disposableSql(script: string): Record<string, unknown>[] {
  const code = `import os,sys,json
import psycopg
from decimal import Decimal
from psycopg.conninfo import conninfo_to_dict
sys.path.insert(0, sys.argv[1])
from tests.l3._disposable_db_guard import validate_disposable_dsn, assert_disposable_connection
dsn=os.environ.get('KALA_VIEW_FIXTURE_DSN') or os.environ.get('KALA_ADMIN_DSN') or os.environ.get('SAMIKSHA_E2E_DATABASE_URL','')
info=conninfo_to_dict(dsn)
endpoint=(info.get('host'),info.get('port'),info.get('dbname'))
import re
suite_owned = (os.environ.get('KALA_VIEW_DB_TESTS') == '1' and endpoint[:2] in {('127.0.0.1','55433'), ('localhost','5432')}
 and re.fullmatch(r'kala_ci_[0-9a-f]{32}', endpoint[2] or ''))
if not suite_owned and endpoint != ('127.0.0.1','55433','ky_cx_k73') and not (os.environ.get('KALA_VIEW_DB_TESTS') == '1' and endpoint == ('localhost','5432','samiksha_e2e')):
 raise RuntimeError('SQL fixtures require the explicit lane or CI disposable loopback DSN')
validate_disposable_dsn(dsn, endpoint[2])
with psycopg.connect(dsn,connect_timeout=3) as conn:
 assert_disposable_connection(conn, endpoint[2])
 with conn.cursor() as cur:
  cur.execute(sys.stdin.read())
  rows=[]
  while True:
   if cur.description:
    cols=[col.name for col in cur.description]
    rows=[dict(zip(cols,row)) for row in cur.fetchall()]
   if not cur.nextset(): break
  conn.rollback()
  print(json.dumps(rows,default=lambda value: float(value) if isinstance(value,Decimal) else str(value)))
`
  return JSON.parse(execFileSync('python3', ['-B', '-c', code,
    fileURLToPath(new URL('../../../../../../python-sidecar/', import.meta.url))], { input: script, encoding: 'utf8', timeout: 15000 }))
}
