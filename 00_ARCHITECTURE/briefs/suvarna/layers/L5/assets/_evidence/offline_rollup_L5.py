#!/usr/bin/env python3
"""A.L5 offline rollup: main's asset_census.py (REGISTRY_REVISION 16) rollup rules applied to the SAVED L5 census
(census_L5.json as of 2026-09-30, inspector 2a78ec64d). Not a re-measure; no DB. Also re-runs main's Dens.served
static scan over the real source tree (no DB). Run with cwd = a checkout of main. Adapted from the A.L1 script."""
import sys, json, collections, os
from pathlib import Path
LANE = Path(os.environ.get('LANE', '/Users/Dev/suvarna-al5'))
sys.path.insert(0, str(LANE / 'platform/scripts/governance'))
import asset_census as ac
CEN = LANE / '00_ARCHITECTURE/briefs/suvarna/layers/census'
d1 = json.load(open(CEN / 'census_L5.json'))['L5']
d2 = d1
# census1 plus the one differing asset (ga_prashna) from the post-grant rerun; verify nothing else differs
a1 = {a['asset_id']: a for a in d1['assets']}; a2 = {a['asset_id']: a for a in d2['assets']}
diff = [k for k in a1 if json.dumps(a1[k], sort_keys=True) != json.dumps(a2[k], sort_keys=True)]
print('assets differing census1 vs rerun:', diff)
layer = dict(d1); layer['assets'] = [a2[k] if k in diff else a1[k] for k in a1]
decl = ac.load_asset_declarations(registry_ids=None)
facts = {a['asset_id']: ac.facts_for_asset(a, decl) for a in layer['assets']}
roll = ac.rollup_census(layer, facts)
out = dict(registry_revision=ac.REGISTRY_REVISION, registry_fingerprint=ac.registry_fingerprint(), rollup=roll)
# Dens rev-4 static scan over the real source tree
decl_t = collections.defaultdict(set)
for a in layer['assets']:
    for t in ([a['target_table']] if a['target_table'] else []) + list(a['count_sql_tables'] or []):
        decl_t[t].add(a['asset_id'])
shared = frozenset(t for t, w in decl_t.items() if len(w) > 1)
cols = {}
for a in layer['assets']:
    r = a.get('reach')
    if a['target_table'] and r: cols[a['target_table']] = list(r['exposed']) + list(r['dark'])
dens = {}
for a in layer['assets']:
    aid = a['asset_id']; tbl = a['target_table']
    toks = list(dict.fromkeys([t for t in ([tbl] if tbl else []) + list(a['count_sql_tables'] or []) + [aid] if t]))
    cap = ac.capability_scan(ac.CAPS_ROOTS, toks, shared=shared, columns=cols, outside_roots=ac.DENS_OUTSIDE_ROOTS)
    g = ac._grade_dens(cap, tbl or aid)
    dens[aid] = dict(before=a['measurements'].get('Dens.served', {}).get('v'), after=g['v'], measured=g['measured'])
out['dens_rev4_static'] = dens
Path('/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json').write_text(json.dumps(out, indent=1, default=list))
gates = ['Ldgr','Idem','Earn','Null','Vocab','Carr','Narr','Dens','Build']
for g in gates:
    c = collections.Counter(roll[k][g]['v'] for k in roll if g in roll[k])
    print(g, dict(c))
print('dens rev4:', dict(collections.Counter(v['after'] for v in dens.values())))
for k, v in dens.items(): print(' ', k, v['before'], '->', v['after'])
