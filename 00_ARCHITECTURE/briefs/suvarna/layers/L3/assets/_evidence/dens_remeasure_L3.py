#!/usr/bin/env python3
"""Offline Dens re-measure for the 21 active L3 assets (A.L3 INDEX 9.1). Same method as the A.L0 script.
Usage: python3 dens_remeasure_L3.py <repo-root> [output.json]"""
import collections, json, sys, os
root = sys.argv[1] if len(sys.argv) > 1 else '.'
out = sys.argv[2] if len(sys.argv) > 2 else 'dens_remeasure_L3_output.json'
sys.path.insert(0, root + '/platform/scripts/governance')
os.chdir(root)
import asset_census as ac
c = json.load(open('00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json'))['L3']
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
    res[a['asset_id']] = (g['v'], g['measured'])
json.dump(res, open(out, 'w'), indent=1, ensure_ascii=False)
print(collections.Counter(v[0] for v in res.values()), 'registry_revision', ac.REGISTRY_REVISION, 'shared', sorted(shared))
