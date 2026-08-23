#!/usr/bin/env python3
"""M0-T26 RESTORE DRILL -- prove restore.sql BY EXECUTION, without persisting it.

Executes the body of restore.sql inside one transaction, asserts the table then equals
snapshot.json cell for cell on all 128 rows, and ROLLS BACK. Nothing is committed: the
repaired state is left in place, and postcheck.py is re-run afterwards to prove that.

This is what separates "the restore file was authored and parses" from "the restore file
was executed and produced the snapshot state". Only the two columns this task writes are
touched, on rows already in the snapshot -- the same scope as the repair itself.
"""
import json, pathlib, re, sys
import psycopg
from psycopg.rows import dict_row

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]

def db_url():
    for l in (ROOT / 'platform/.env.local').read_text().splitlines():
        if l.startswith('DATABASE_URL='):
            return re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
    raise SystemExit('DATABASE_URL not found')

snap = {r['asset_id']: r for r in json.loads((HERE / 'snapshot.json').read_text(encoding='utf-8'))['rows']}
sqltext = (HERE / 'restore.sql').read_text(encoding='utf-8')
body = sqltext.split('BEGIN;', 1)[1].rsplit('COMMIT;', 1)[0]      # strip the outer txn control
assert 'DO $restore$' in body

diffs = []
with psycopg.connect(db_url(), row_factory=dict_row, autocommit=False) as conn:
    c = conn.cursor()
    c.execute("SET statement_timeout = '45s'")
    c.execute(body)
    for n in conn.notices if hasattr(conn, 'notices') else []:
        print('  notice:', n.strip())
    c.execute("SELECT asset_id, layer, layer_index, layer_name FROM asset_registry ORDER BY asset_id")
    live = {r['asset_id']: r for r in c.fetchall()}
    for aid in sorted(set(snap) | set(live)):
        s, l = snap.get(aid), live.get(aid)
        if s is None or l is None or {k: l[k] for k in s} != s:
            diffs.append((aid, s, None if l is None else dict(l)))
    conn.rollback()

print(f'restore executed in-transaction; rows compared: {len(snap)}; cells differing from snapshot: {len(diffs)}')
for d in diffs[:10]:
    print('  ', d)
print('TRANSACTION ROLLED BACK -- the repaired state is unchanged.')
json.dump({'rows_compared': len(snap), 'diffs': diffs, 'committed': False},
          open(HERE / 'restore_drill.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
sys.exit(1 if diffs else 0)
