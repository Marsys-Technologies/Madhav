#!/usr/bin/env python3
"""M0-T39 I2 snapshot of asset_registry (the only table this task writes).
Dumps full table CSV + a literal-VALUES restore script scoped to estimated_seconds.
Verifies read-back cell-by-cell against a fresh live read."""
import csv, hashlib, json, os, pathlib, sys, datetime
from _db import conn

TS = os.environ.get('SNAP_TS') or datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
ROOT = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')
D = ROOT/'00_ARCHITECTURE/control/snapshots'/f'{TS}_m0t39_asset_registry'
D.mkdir(parents=True, exist_ok=True)

SELECT_FULL = "SELECT * FROM asset_registry ORDER BY asset_id"
SELECT_KEY  = "SELECT asset_id, estimated_seconds FROM asset_registry ORDER BY asset_id"

with conn() as c:
    cur = c.cursor()
    cur.execute("SELECT now() AS now"); taken_at = str(cur.fetchone()['now'])
    cur.execute(SELECT_FULL); full = cur.fetchall()
    cols = list(full[0].keys())
    cur.execute(SELECT_KEY); keyrows = cur.fetchall()

csv_path = D/'asset_registry.csv'
with csv_path.open('w', newline='') as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(cols)
    for r in full:
        w.writerow(['' if r[k] is None else (json.dumps(r[k]) if isinstance(r[k], (dict, list)) else str(r[k])) for k in cols])

def lit(v):
    return 'NULL' if v is None else str(int(v))
restore = D/'restore_estimated_seconds.sql'
vals = ",\n".join(f"  ('{r['asset_id']}', {lit(r['estimated_seconds'])}::int)" for r in keyrows)
restore.write_text(f"""-- M0-T39 I2 restore script — asset_registry.estimated_seconds
-- Snapshot taken_at (db now()): {taken_at}
-- Rows: {len(keyrows)} (every asset_registry row, literal values, NULLs preserved)
-- Restores ONLY the column this task writes. Run inside an explicit transaction.
UPDATE asset_registry r
SET estimated_seconds = v.est
FROM (VALUES
{vals}
) AS v(asset_id, est)
WHERE r.asset_id = v.asset_id
  AND r.estimated_seconds IS DISTINCT FROM v.est;
""")

sha_csv = hashlib.sha256(csv_path.read_bytes()).hexdigest()
sha_res = hashlib.sha256(restore.read_bytes()).hexdigest()

# ---- verification: re-read live and compare cell-by-cell against the CSV we just wrote ----
with conn() as c:
    cur = c.cursor(); cur.execute(SELECT_FULL); live = cur.fetchall()
with csv_path.open() as f:
    rd = list(csv.reader(f)); hdr, body = rd[0], rd[1:]
mismatch = []
if len(body) != len(live) or hdr != cols:
    mismatch.append('shape')
else:
    for lr, br in zip(live, body):
        for i, k in enumerate(cols):
            exp = '' if lr[k] is None else (json.dumps(lr[k]) if isinstance(lr[k], (dict, list)) else str(lr[k]))
            if exp != br[i]:
                mismatch.append(f"{lr['asset_id']}.{k}")
est_null = sum(1 for r in keyrows if r['estimated_seconds'] is None)
man = {
  'task': 'M0-T39', 'agent': 'KARAKA-M0-T39', 'taken_at_db_now': taken_at, 'snapshot_ts': TS,
  'table': 'asset_registry', 'select_full': SELECT_FULL, 'select_key': SELECT_KEY,
  'row_count': len(full), 'column_count': len(cols), 'columns': cols,
  'estimated_seconds_null_count': est_null,
  'estimated_seconds_notnull_count': len(keyrows) - est_null,
  'files': {'asset_registry.csv': {'sha256': sha_csv, 'bytes': csv_path.stat().st_size},
            'restore_estimated_seconds.sql': {'sha256': sha_res, 'bytes': restore.stat().st_size}},
  'verification': {'method': 'full re-read of live asset_registry compared cell-by-cell to the written CSV',
                   'cells_compared': len(live)*len(cols), 'mismatches': len(mismatch),
                   'mismatch_detail': mismatch[:20]},
}
(D/'MANIFEST.json').write_text(json.dumps(man, indent=1))
print(json.dumps({'dir': str(D), 'rows': len(full), 'cells': len(live)*len(cols),
                  'mismatches': len(mismatch), 'est_null': est_null, 'sha_csv': sha_csv[:16]}, indent=1))
sys.exit(1 if mismatch else 0)
