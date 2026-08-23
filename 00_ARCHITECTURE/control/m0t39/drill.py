#!/usr/bin/env python3
"""M0-T39 restore drill (D-28 part 2 standing requirement).

Inside ONE transaction that is ALWAYS rolled back:
  1. apply the T-5 UPDATE (the real mutation)  -> proves the table can move
  2. apply restore_estimated_seconds.sql       -> proves the restore actually restores
  3. compare every asset_registry cell to the snapshot CSV
  4. ROLLBACK (never commit)
Then re-run the pre-flight post-rollback so the drill's net effect is provably zero.
"""
import csv, json, pathlib, sys, subprocess
from _db import conn

SNAP = pathlib.Path(sys.argv[1])
CSV = SNAP/'asset_registry.csv'
RESTORE = (SNAP/'restore_estimated_seconds.sql').read_text()

T5 = """WITH d AS (
  SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at)) AS secs
  FROM build_run_assets WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL
), s AS (SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs) AS m FROM d GROUP BY asset_id)
UPDATE asset_registry r SET estimated_seconds = ceil(s.m)::int
FROM s WHERE s.asset_id = r.asset_id AND r.estimated_seconds IS DISTINCT FROM ceil(s.m)::int"""

with CSV.open() as f:
    rd = list(csv.reader(f)); cols, snap_rows = rd[0], rd[1:]

res = {}
with conn(autocommit=False) as c:
    cur = c.cursor()
    cur.execute(T5); res['mutation_rowcount'] = cur.rowcount
    cur.execute("SELECT count(*) AS n FROM asset_registry WHERE estimated_seconds IS NULL")
    res['null_count_after_mutation'] = cur.fetchone()['n']
    cur.execute(RESTORE); res['restore_rowcount'] = cur.rowcount
    cur.execute("SELECT * FROM asset_registry ORDER BY asset_id"); live = cur.fetchall()
    mismatch = []
    if len(live) != len(snap_rows) or list(live[0].keys()) != cols:
        mismatch.append('shape')
    else:
        for lr, sr in zip(live, snap_rows):
            for i, k in enumerate(cols):
                exp = '' if lr[k] is None else (json.dumps(lr[k]) if isinstance(lr[k], (dict, list)) else str(lr[k]))
                if exp != sr[i]:
                    mismatch.append(f"{lr['asset_id']}.{k}")
    res['cells_compared'] = len(live)*len(cols)
    res['cells_differing_from_snapshot_after_restore'] = len(mismatch)
    res['mismatch_detail'] = mismatch[:20]
    c.rollback(); res['rolled_back'] = True

with conn() as c:
    cur = c.cursor()
    cur.execute("SELECT count(*) AS n FROM asset_registry WHERE estimated_seconds IS NULL")
    res['null_count_post_rollback'] = cur.fetchone()['n']
print(json.dumps(res, indent=1))
p = subprocess.run([sys.executable, 'preflight.py'], capture_output=True, text=True)
print('--- preflight re-run post-rollback (exit %d) ---' % p.returncode)
print(p.stdout[-1200:])
ok = (res['mutation_rowcount'] == 93 and res['restore_rowcount'] == 93
      and res['cells_differing_from_snapshot_after_restore'] == 0
      and res['null_count_after_mutation'] == 35 and res['null_count_post_rollback'] == 119
      and p.returncode == 0)
print('DRILL', 'OK' if ok else 'FAIL')
sys.exit(0 if ok else 3)
