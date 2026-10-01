#!/usr/bin/env python3
"""Offline Dens re-measure for the 40 L0 assets (A.L0, INDEX section 9.1).

Runs the CURRENT inspector's capability_scan and _grade_dens (platform/scripts/governance/asset_census.py) over the saved census
(layers/census/census_L0.json). Stand-ins for what the live run reads from the database: the populated-column lists recorded in the
saved census (reach.exposed + reach.dark) replace information_schema columns, and the saved count_sql tables define the shared-table
set. It re-measures served-surface attribution exactly as the current scanner does; the tier-column part is approximate.

Usage: python3 dens_remeasure.py <repo-root> [output.json]
"""
import collections, json, sys
root = sys.argv[1] if len(sys.argv) > 1 else '.'
out = sys.argv[2] if len(sys.argv) > 2 else 'dens_remeasure_output.json'
sys.path.insert(0, root + '/platform/scripts/governance')
import os
os.chdir(root)
import asset_census as ac
c = json.load(open('00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json'))['L0']
decl = collections.defaultdict(set)
for a in c['assets']:
    for t in a['count_sql_tables'] + ([a['target_table']] if a['target_table'] else []):
        decl[t].add(a['asset_id'])
shared = frozenset(t for t, w in decl.items() if len(w) > 1)
cols = {a['target_table']: ((a['reach'] or {}).get('exposed') or []) + ((a['reach'] or {}).get('dark') or [])
        for a in c['assets'] if a['target_table']}
res = {}
for a in c['assets']:
    toks = list(dict.fromkeys(([a['target_table']] if a['target_table'] else []) + a['count_sql_tables'] + [a['asset_id']]))
    cap = ac.capability_scan(ac.CAPS_ROOTS, toks, shared=shared, columns=cols, outside_roots=ac.DENS_OUTSIDE_ROOTS)
    g = ac._grade_dens(cap, a['target_table'] or a['asset_id'])
    res[a['asset_id']] = (g['v'], g['measured'][:150])
json.dump(res, open(out, 'w'), indent=1)
print(collections.Counter(v[0] for v in res.values()), 'registry_revision', ac.REGISTRY_REVISION)
