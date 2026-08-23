#!/usr/bin/env python3
"""M0-T39 post-check — fresh connection, compared against the SNAPSHOT and against the
independently-computed expectations, not against the shape of the statement."""
import csv, json, pathlib, sys
from _db import conn
SNAP = pathlib.Path(sys.argv[1])
EXP = json.loads((pathlib.Path(__file__).parent/'expectations.json').read_text())
with (SNAP/'asset_registry.csv').open() as f:
    rd = list(csv.reader(f)); cols, rows = rd[0], rd[1:]
snap = {r[cols.index('asset_id')]: r for r in rows}
EST_I = cols.index('estimated_seconds')
with conn() as c:
    cur = c.cursor(); cur.execute("SELECT * FROM asset_registry ORDER BY asset_id"); live = cur.fetchall()
    cur.execute("SELECT count(*) AS n FROM asset_registry WHERE estimated_seconds IS NULL"); post_null = cur.fetchone()['n']
    cur.execute("SELECT count(*) AS n FROM asset_throughput"); at_rows = cur.fetchone()['n']
    cur.execute("SELECT state, count(*) AS n FROM asset_throughput GROUP BY state ORDER BY state"); at_states = cur.fetchall()
    cur.execute("""SELECT count(*) AS n FROM asset_throughput WHERE state IN ('dormant','building')
                   AND (last_built_at IS NULL OR last_built_at < now() - interval '24 hours')"""); orphans = cur.fetchone()['n']
    cur.execute("""SELECT count(*) AS n FROM build_run_assets a JOIN build_runs r ON r.id=a.run_id
                   WHERE a.state='queued' AND r.state IN ('completed','failed','stopped')"""); t3 = cur.fetchone()['n']
    cur.execute("""SELECT count(*) AS n FROM build_runs WHERE ended_at IS NULL AND state IN ('completed','failed','stopped')"""); t4 = cur.fetchone()['n']
changed, other, nulls = [], [], []
must_null, expv = set(EXP['must_stay_null']), EXP['expected_values']
for lr in live:
    a = lr['asset_id']; s = snap[a]
    for i, k in enumerate(cols):
        cur_v = '' if lr[k] is None else (json.dumps(lr[k]) if isinstance(lr[k], (dict, list)) else str(lr[k]))
        if cur_v != s[i]:
            (changed if k == 'estimated_seconds' else other).append(f'{a}.{k}')
    if a in must_null and lr['estimated_seconds'] is not None: nulls.append(a)
    if a in expv and lr['estimated_seconds'] != expv[a]: nulls.append(a+':value')
r = {'cells_compared': len(live)*len(cols),
     'estimated_seconds_cells_changed_vs_snapshot': len(changed),
     'other_cells_changed_vs_snapshot': len(other), 'other_detail': other[:20],
     'post_null_estimated_seconds': post_null, 'expected_post_null': EXP['expected_post_null_count'],
     'values_disagreeing_with_independent_median': nulls,
     'UNTOUCHED_asset_throughput_rows': at_rows,
     'UNTOUCHED_asset_throughput_states': {x['state']: x['n'] for x in at_states},
     'UNTOUCHED_orphan_rows_still_present': orphans,
     'UNTOUCHED_t3_queued_under_terminal_runs': t3,
     'UNTOUCHED_t4_terminal_runs_no_ended_at': t4}
print(json.dumps(r, indent=1))
ok = (len(changed) == 93 and len(other) == 0 and post_null == 35 and not nulls
      and at_rows == 267 and orphans == 3 and t3 == 1477 and t4 == 31)
print('POSTCHECK', 'OK' if ok else 'FAIL'); sys.exit(0 if ok else 5)
