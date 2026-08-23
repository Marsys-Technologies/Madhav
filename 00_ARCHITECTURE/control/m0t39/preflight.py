#!/usr/bin/env python3
"""M0-T39 pre-flight discriminating detector for T-5 (estimated_seconds backfill).

Computes every asset's median run duration INDEPENDENTLY in Python from raw
build_run_assets durations, so 'the repair succeeded' is checked against a
separately-derived expectation rather than against the same SQL that wrote it.
Emits expectations.json consumed by execute.py and postcheck.py.
"""
import json, math, statistics, sys, pathlib, datetime
from _db import conn

OUT = pathlib.Path(__file__).parent/'expectations.json'

RAW = """SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at))::float8 AS secs
FROM build_run_assets
WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL"""

with conn() as c:
    cur = c.cursor()
    cur.execute("SELECT now() AS now"); now = str(cur.fetchone()['now'])
    cur.execute(RAW); raw = cur.fetchall()
    cur.execute("SELECT asset_id, estimated_seconds, target_floor, writer_timeout_seconds FROM asset_registry ORDER BY asset_id")
    reg = {r['asset_id']: r for r in cur.fetchall()}
    # the SQL the repair will use, run read-only, so the two derivations can be compared
    cur.execute("""WITH d AS (SELECT asset_id, EXTRACT(EPOCH FROM (ended_at-started_at)) AS secs
      FROM build_run_assets WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL)
      SELECT asset_id, ceil(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs))::int AS est
      FROM d GROUP BY asset_id ORDER BY asset_id""")
    sqlmed = {r['asset_id']: r['est'] for r in cur.fetchall()}

by = {}
for r in raw:
    by.setdefault(r['asset_id'], []).append(r['secs'])

# independent median (statistics.median == PERCENTILE_CONT(0.5): interpolated / mean of two middles)
py_est = {a: int(math.ceil(statistics.median(v))) for a, v in by.items()}

in_registry = {a: e for a, e in py_est.items() if a in reg}
not_in_registry = sorted(a for a in py_est if a not in reg)

# cross-check the two independent derivations, restricted to registry assets
disagree = sorted(a for a in in_registry if sqlmed.get(a) != in_registry[a])

expected_changed = sorted(a for a, e in in_registry.items() if reg[a]['estimated_seconds'] != e)
no_run = sorted(a for a in reg if a not in py_est)
unchanged_measurable = sorted(a for a, e in in_registry.items() if reg[a]['estimated_seconds'] == e)

# --- discriminators: named rows whose correct post-value is known independently ---
disc_ids = ['ga_dashas','ga_panchanga','ga_vargas','ga_sensitive','bo_laksana_rerank','mi_sankalpa']
disc = []
for a in disc_ids:
    if a in in_registry:
        disc.append({'asset_id': a, 'pre': reg[a]['estimated_seconds'], 'expected_post': in_registry[a],
                     'n_runs': len(by[a]), 'differs_pre': reg[a]['estimated_seconds'] != in_registry[a]})
# negative controls: must be NULL before AND after, and unrelated columns must not move
neg = [{'asset_id': a, 'estimated_seconds': reg[a]['estimated_seconds'],
        'target_floor': reg[a]['target_floor'], 'writer_timeout_seconds': reg[a]['writer_timeout_seconds']}
       for a in no_run[:5]]

exp = {
 'computed_at_db_now': now,
 'method': 'python statistics.median over raw build_run_assets complete-run durations, ceil()',
 'registry_rows': len(reg),
 'assets_with_completed_runs_total': len(py_est),
 'assets_with_completed_runs_in_registry': len(in_registry),
 'assets_with_runs_not_in_registry': not_in_registry,
 'registry_assets_with_no_completed_run': len(no_run),
 'expected_update_rowcount': len(expected_changed),
 'expected_changed_assets': expected_changed,
 'expected_unchanged_measurable': unchanged_measurable,
 'must_stay_null': no_run,
 'python_vs_sql_disagreements': disagree,
 'expected_values': in_registry,
 'discriminators': disc,
 'negative_controls': neg,
 'pre_null_count': sum(1 for a in reg if reg[a]['estimated_seconds'] is None),
 'expected_post_null_count': len(no_run),
}
OUT.write_text(json.dumps(exp, indent=1))

print(json.dumps({k: exp[k] for k in ['computed_at_db_now','registry_rows','assets_with_completed_runs_total',
  'assets_with_completed_runs_in_registry','assets_with_runs_not_in_registry','registry_assets_with_no_completed_run',
  'expected_update_rowcount','python_vs_sql_disagreements','pre_null_count','expected_post_null_count']}, indent=1))
print('discriminators:'); [print('  ', json.dumps(d)) for d in disc]
print('negative_controls (first 5 of %d must-stay-NULL):' % len(no_run)); [print('  ', json.dumps(n)) for n in neg]

fail = []
if disagree: fail.append(f'python and SQL medians disagree on {disagree}')
if not all(d['differs_pre'] for d in disc if d['asset_id'] != 'mi_sankalpa'):
    fail.append('a discriminator does not differ pre-write — detector could not have failed')
if any(n['estimated_seconds'] is not None for n in neg): fail.append('negative control not NULL pre-write')
if fail:
    print('PREFLIGHT FAIL:', fail); sys.exit(2)
print('PREFLIGHT OK')
