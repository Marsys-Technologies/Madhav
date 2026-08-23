#!/usr/bin/env python3
"""M0-T39 — EXECUTE T-5 only: backfill/correct asset_registry.estimated_seconds
from measured build_run_assets medians. D-6 (grant) as corrected by D-12 part 5
(asset_registry.estimated_seconds is in scope) and D-6 condition 4 (measured
telemetry only; no clean telemetry -> NULL).

Every assertion rolls back and exits non-zero. Nothing is committed unless every
number matches the pre-flight expectation computed independently in Python.
"""
import csv, json, pathlib, sys
from _db import conn

SNAP = pathlib.Path(sys.argv[1])
EXP = json.loads((pathlib.Path(__file__).parent/'expectations.json').read_text())
with (SNAP/'asset_registry.csv').open() as f:
    rd = list(csv.reader(f)); cols, snap_rows = rd[0], rd[1:]
snap = {r[cols.index('asset_id')]: r for r in snap_rows}
EST_I = cols.index('estimated_seconds')

T5 = """WITH d AS (
  SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at)) AS secs
  FROM build_run_assets WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL
), s AS (SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs) AS m FROM d GROUP BY asset_id)
UPDATE asset_registry r SET estimated_seconds = ceil(s.m)::int
FROM s WHERE s.asset_id = r.asset_id AND r.estimated_seconds IS DISTINCT FROM ceil(s.m)::int"""

log = {}
fail = []
with conn(autocommit=False) as c:
    cur = c.cursor()
    # re-measure inside the write transaction, immediately before the write
    cur.execute("SELECT count(*) AS n FROM asset_registry"); log['pre_registry_rows'] = cur.fetchone()['n']
    cur.execute("SELECT count(*) AS n FROM asset_registry WHERE estimated_seconds IS NULL"); log['pre_null'] = cur.fetchone()['n']
    cur.execute("SELECT count(*) AS n FROM build_runs WHERE state NOT IN ('completed','failed','stopped')")
    log['nonterminal_runs_at_write'] = cur.fetchone()['n']

    cur.execute(T5); log['rowcount'] = cur.rowcount

    # --- assertions ---
    if log['rowcount'] != EXP['expected_update_rowcount']:
        fail.append(f"rowcount {log['rowcount']} != expected {EXP['expected_update_rowcount']}")
    if log['pre_registry_rows'] != EXP['registry_rows']:
        fail.append('registry row count moved under us')
    if log['pre_null'] != EXP['pre_null_count']:
        fail.append(f"pre NULL count {log['pre_null']} != expected {EXP['pre_null_count']}")
    if log['nonterminal_runs_at_write'] != 0:
        fail.append('a non-terminal build_run exists — telemetry may be moving')

    cur.execute("SELECT count(*) AS n FROM asset_registry WHERE estimated_seconds IS NULL")
    log['post_null'] = cur.fetchone()['n']
    if log['post_null'] != EXP['expected_post_null_count']:
        fail.append(f"post NULL {log['post_null']} != expected {EXP['expected_post_null_count']}")

    cur.execute("SELECT * FROM asset_registry ORDER BY asset_id"); live = cur.fetchall()
    # every value equals the INDEPENDENTLY computed python median; NULLs exactly the no-run set
    wrong_val, other_col_moved, null_wrong = [], [], []
    must_null = set(EXP['must_stay_null']); expv = EXP['expected_values']
    for lr in live:
        a = lr['asset_id']
        if a in must_null:
            if lr['estimated_seconds'] is not None: null_wrong.append(a)
        elif a in expv:
            if lr['estimated_seconds'] != expv[a]: wrong_val.append((a, lr['estimated_seconds'], expv[a]))
        else:
            null_wrong.append(a+':unclassified')
        srow = snap[a]
        for i, k in enumerate(cols):
            if k == 'estimated_seconds': continue
            cur_v = '' if lr[k] is None else (json.dumps(lr[k]) if isinstance(lr[k], (dict, list)) else str(lr[k]))
            if cur_v != srow[i]: other_col_moved.append(f'{a}.{k}')
    log['values_not_matching_independent_median'] = wrong_val
    log['nulls_wrong'] = null_wrong
    log['non_estimated_seconds_cells_changed'] = other_col_moved[:20]
    log['non_estimated_seconds_cells_changed_count'] = len(other_col_moved)
    if wrong_val: fail.append('a written value does not equal the independently computed median')
    if null_wrong: fail.append('NULL set is not exactly the 35 no-run assets')
    if other_col_moved: fail.append('a column other than estimated_seconds changed')

    # discriminators
    disc = []
    for d in EXP['discriminators']:
        got = next(r['estimated_seconds'] for r in live if r['asset_id'] == d['asset_id'])
        disc.append({**d, 'observed_post': got, 'ok': got == d['expected_post']})
    log['discriminators'] = disc
    if not all(d['ok'] for d in disc): fail.append('a discriminator did not land on its expected value')
    # negative controls
    neg = []
    for n in EXP['negative_controls']:
        r = next(x for x in live if x['asset_id'] == n['asset_id'])
        neg.append({'asset_id': n['asset_id'], 'estimated_seconds': r['estimated_seconds'],
                    'target_floor': r['target_floor'], 'writer_timeout_seconds': r['writer_timeout_seconds'],
                    'ok': r['estimated_seconds'] is None and r['target_floor'] == n['target_floor']
                          and r['writer_timeout_seconds'] == n['writer_timeout_seconds']})
    log['negative_controls'] = neg
    if not all(n['ok'] for n in neg): fail.append('a negative control moved')

    if fail:
        c.rollback(); log['committed'] = False; log['fail'] = fail
        print(json.dumps(log, indent=1)); sys.exit(4)
    c.commit(); log['committed'] = True

print(json.dumps(log, indent=1))
