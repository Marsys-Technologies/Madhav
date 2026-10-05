#!/usr/bin/env python3
"""A.L4 offline rollup: main's asset_census.py (REGISTRY_REVISION as imported) rollup rules applied to a SAVED L4 census
(no DB, no re-measure). Two inputs: the repo's saved 2026-09-30 census and the 2026-10-02 fresh census (inspector 1e5781a, rev 10).
Also re-runs main's Dens.served static scan over the real source tree (no DB)."""
import sys, json, collections, os
from pathlib import Path
LANE = Path(os.environ.get('LANE', '/Users/Dev/suvarna-al4'))
sys.path.insert(0, str(LANE / 'platform/scripts/governance'))
os.chdir(LANE)
import asset_census as ac
inputs = {
  'saved_2026-09-30': LANE / '00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json',
  'fresh_2026-10-02_1e5781a': Path('/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json'),
}
decl = ac.load_asset_declarations(registry_ids=None)
out = dict(registry_revision=ac.REGISTRY_REVISION, registry_fingerprint=ac.registry_fingerprint(), runs={})
for name, p in inputs.items():
    layer = json.load(open(p))['L4']
    facts = {a['asset_id']: ac.facts_for_asset(a, decl) for a in layer['assets']}
    roll = ac.rollup_census(layer, facts)
    # Dens rev static scan
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
        dens[aid] = dict(saved=a['measurements'].get('Dens.served', {}).get('v'), now=g['v'], measured=g['measured'])
    out['runs'][name] = dict(census_generated=layer.get('generated'), census_registry_revision=json.load(open(p)).get('registry_revision') or layer.get('registry_revision'), rollup=roll, dens_static=dens)
Path('/Users/Dev/suvarna-evidence/A_L4/rollup_L4.json').write_text(json.dumps(out, indent=1, default=list))
gates = ['Ldgr','Idem','Earn','Null','Vocab','Carr','Narr','Dens','Build']
for name, r in out['runs'].items():
    print('==', name, 'census', r['census_generated'])
    roll = r['rollup']
    for g in gates:
        c = collections.Counter(roll[k][g]['v'] for k in roll if g in roll[k])
        print(' ', g, dict(c))
    print('  dens static:', dict(collections.Counter(v['now'] for v in r['dens_static'].values())))
