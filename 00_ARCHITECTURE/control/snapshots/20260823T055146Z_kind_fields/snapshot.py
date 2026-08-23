#!/usr/bin/env python3
"""M0-T21 I2 snapshot: asset_id, asset_kind, asset_type, storage_type for ALL rows.
Emits snapshot.tsv, snapshot.json, restore.sql (literal VALUES), MANIFEST.md, SHA256SUMS.
READ ONLY against the DB."""
import hashlib, json, pathlib, re, datetime, psycopg
HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')
url = next(re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
           for l in (REPO/'platform/.env.local').read_text().splitlines() if l.startswith('DATABASE_URL='))
COLS = ('asset_id','asset_kind','asset_type','storage_type')
with psycopg.connect(url, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
    cur = conn.cursor(); cur.execute("SET default_transaction_read_only = on")
    cur.execute(f"SELECT {','.join(COLS)} FROM asset_registry ORDER BY asset_id")
    rows = cur.fetchall()
    cur.execute("SELECT count(*) n FROM asset_registry"); total = cur.fetchone()['n']
assert len(rows) == total, f"row mismatch {len(rows)} != {total}"
for r in rows:
    for c in COLS:
        assert r[c] is not None, f"unexpected NULL in {c} for {r['asset_id']}"
        assert '\t' not in r[c] and "'" not in r[c], f"unsafe char in {r['asset_id']}.{c}"

(HERE/'snapshot.tsv').write_text('\t'.join(COLS)+'\n' + ''.join('\t'.join(r[c] for c in COLS)+'\n' for r in rows))
(HERE/'snapshot.json').write_text(json.dumps({'captured_at_utc': datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z'),
    'table':'asset_registry','columns':list(COLS),'row_count':len(rows),
    'rows':[{c:r[c] for c in COLS} for r in rows]}, indent=1))

vals = ',\n  '.join("('{}','{}','{}','{}')".format(*[r[c] for c in COLS]) for r in rows)
(HERE/'restore.sql').write_text(f"""-- M0-T21 RESTORE SCRIPT — asset_registry kind fields, {len(rows)} rows, literal VALUES.
-- Captured {datetime.datetime.now(datetime.UTC).isoformat()}. Restores asset_kind/asset_type/storage_type ONLY.
-- Touches NO other column, NO other table, NO DDL. Run inside the BEGIN/COMMIT as written.
-- Rowcount assertion: the DO block raises and aborts unless exactly {len(rows)} rows are restored.
BEGIN;

CREATE TEMP TABLE _m0t21_restore(asset_id text PRIMARY KEY, asset_kind text, asset_type text, storage_type text) ON COMMIT DROP;
INSERT INTO _m0t21_restore(asset_id, asset_kind, asset_type, storage_type) VALUES
  {vals};

DO $$
DECLARE n_src int; n_upd int; n_missing int;
BEGIN
  SELECT count(*) INTO n_src FROM _m0t21_restore;
  IF n_src <> {len(rows)} THEN RAISE EXCEPTION 'restore source has %, expected {len(rows)}', n_src; END IF;
  SELECT count(*) INTO n_missing FROM _m0t21_restore s
    WHERE NOT EXISTS (SELECT 1 FROM asset_registry a WHERE a.asset_id = s.asset_id);
  IF n_missing <> 0 THEN RAISE EXCEPTION 'restore: % snapshot asset_ids no longer exist in asset_registry', n_missing; END IF;
  UPDATE asset_registry a
     SET asset_kind = s.asset_kind, asset_type = s.asset_type, storage_type = s.storage_type
    FROM _m0t21_restore s WHERE a.asset_id = s.asset_id;
  GET DIAGNOSTICS n_upd = ROW_COUNT;
  IF n_upd <> {len(rows)} THEN RAISE EXCEPTION 'restore updated % rows, expected {len(rows)}', n_upd; END IF;
  RAISE NOTICE 'restore: % rows restored', n_upd;
END $$;

-- Post-restore verification (must return 0):
--   SELECT count(*) FROM asset_registry a JOIN _m0t21_restore s USING (asset_id)
--   WHERE (a.asset_kind,a.asset_type,a.storage_type) IS DISTINCT FROM (s.asset_kind,s.asset_type,s.storage_type);
COMMIT;
""")

sums = []
for f in sorted(HERE.glob('*')):
    if f.name == 'SHA256SUMS' or f.is_dir(): continue
    sums.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}")
(HERE/'SHA256SUMS').write_text('\n'.join(sums)+'\n')
print(f"snapshot: {len(rows)} rows -> snapshot.tsv / snapshot.json / restore.sql")
print('\n'.join(sums))
