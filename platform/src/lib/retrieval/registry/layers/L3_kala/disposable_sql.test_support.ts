/** Test-only SQL transport. No Docker/CLI clients, service startup or ambient DSN. */
import { execFileSync } from 'node:child_process'
export function disposableSql(script: string): Record<string, unknown>[] {
  const code = `import os,sys,json
import psycopg
from decimal import Decimal
from psycopg.conninfo import conninfo_to_dict
dsn=os.environ.get('KALA_ADMIN_DSN','')
info=conninfo_to_dict(dsn)
if (info.get('host'),info.get('port'),info.get('dbname')) != ('127.0.0.1','55433','ky_cx_k73'):
 raise RuntimeError('SQL fixtures require the explicit disposable loopback ky_cx_k73 DSN')
with psycopg.connect(dsn,connect_timeout=3) as conn:
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
  return JSON.parse(execFileSync('python3', ['-B', '-c', code], { input: script, encoding: 'utf8', timeout: 15000 }))
}
