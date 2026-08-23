#!/usr/bin/env python3
"""M0-T26 (Nirmana Phase 0.5a) — I2 snapshot of asset_registry layer-position columns.

Captures asset_id, layer, layer_index, layer_name for ALL rows (not only the repair set),
so the post-check can prove that nothing outside the intended change set moved.

Writes, into this directory: snapshot.tsv, snapshot.json, restore.sql
Reads DATABASE_URL from platform/.env.local the way measure_assets.py does. Never prints it.
"""
import json, pathlib, re, datetime, hashlib
import psycopg
from psycopg.rows import dict_row

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
COLS = ('asset_id', 'layer', 'layer_index', 'layer_name')

def db_url():
    for l in (ROOT / 'platform/.env.local').read_text().splitlines():
        if l.startswith('DATABASE_URL='):
            return re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
    raise SystemExit('DATABASE_URL not found in platform/.env.local')

def lit(v):
    if v is None:
        return 'NULL'
    return "'" + v.replace("'", "''") + "'"

def main():
    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with psycopg.connect(db_url(), row_factory=dict_row, autocommit=True) as conn:
        c = conn.cursor()
        c.execute("SET statement_timeout = '45s'")
        c.execute("SELECT asset_id, layer, layer_index, layer_name FROM asset_registry ORDER BY asset_id")
        rows = c.fetchall()

    n = len(rows)
    # TSV
    tsv = ['\t'.join(COLS)]
    for r in rows:
        tsv.append('\t'.join('<NULL>' if r[c] is None else r[c] for c in COLS))
    (HERE / 'snapshot.tsv').write_text('\n'.join(tsv) + '\n', encoding='utf-8')

    # JSON
    (HERE / 'snapshot.json').write_text(json.dumps({
        'task': 'M0-T26', 'captured_at_utc': ts, 'table': 'asset_registry',
        'columns': list(COLS), 'row_count': n,
        'rows': [{c: r[c] for c in COLS} for r in rows],
    }, ensure_ascii=False, indent=1), encoding='utf-8')

    # restore.sql — literal VALUES, rowcount-asserted, transactional
    vals = ',\n  '.join(
        '({}, {}, {})'.format(lit(r['asset_id']), lit(r['layer_index']), lit(r['layer_name']))
        for r in rows)
    sql = f"""-- M0-T26 RESTORE — asset_registry layer_index / layer_name
-- Captured {ts} (UTC). Restores EXACTLY the pre-repair values of the two columns
-- this task writes, on all {n} rows. Touches no other column, no other table.
-- Aborts (RAISE EXCEPTION rolls back the whole transaction) unless exactly {n} rows update.
BEGIN;

DO $restore$
DECLARE
  n_updated integer;
BEGIN
  WITH snap(asset_id, layer_index, layer_name) AS (VALUES
  {vals}
  ), upd AS (
    UPDATE asset_registry a
       SET layer_index = s.layer_index,
           layer_name  = s.layer_name
      FROM snap s
     WHERE a.asset_id = s.asset_id
    RETURNING 1
  )
  SELECT count(*) INTO n_updated FROM upd;

  IF n_updated <> {n} THEN
    RAISE EXCEPTION 'M0-T26 restore aborted: updated % rows, expected {n}', n_updated;
  END IF;
  RAISE NOTICE 'M0-T26 restore: % rows restored', n_updated;
END
$restore$;

COMMIT;
"""
    (HERE / 'restore.sql').write_text(sql, encoding='utf-8')

    print(f'snapshot captured: {n} rows')
    for f in ('snapshot.tsv', 'snapshot.json', 'restore.sql'):
        p = HERE / f
        print(f'  {f}: {p.stat().st_size} bytes  sha256={hashlib.sha256(p.read_bytes()).hexdigest()[:16]}')

if __name__ == '__main__':
    main()
