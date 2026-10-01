#!/usr/bin/env python3
"""Direct and transitive dependents of the 23 L2 assets from the seed `depends_on` (which carries migration 1210 for new rows), next to the
saved census blocking_radius (pre-1210) (A.L2, INDEX section 6). Static; no DB.

Usage: python3 closure.py <repo-root> [output.json]
"""
import collections, json, re, sys
root = sys.argv[1] if len(sys.argv) > 1 else '.'
out = sys.argv[2] if len(sys.argv) > 2 else 'closure_L2.json'
src = open(root + '/platform/scripts/seed/asset_registry_seed.ts').read().split('export const COEFFICIENTS')[0]
pos = [(m.start(), m.group(1)) for m in re.finditer(r"asset_id:\s*'([a-z0-9_]+)'", src)]
deps = {}
for i, (p, a) in enumerate(pos):
    blk = src[p:(pos[i + 1][0] if i + 1 < len(pos) else len(src))]
    m = re.search(r"depends_on:\s*\[(.*?)\]", blk, re.S)
    deps[a] = re.findall(r"'([a-z0-9_]+)'", re.sub(r"//[^\n]*", "", m.group(1))) if m else []
cen = {}
for L in ['L0', 'L1', 'L2', 'L3', 'L4', 'L5']:
    d = json.load(open(f'{root}/00_ARCHITECTURE/briefs/suvarna/layers/census/census_{L}.json'))[L]
    for a in d['assets']:
        cen[a['asset_id']] = (a['blocking_radius']['direct'], a['blocking_radius']['transitive'])
rev = collections.defaultdict(set)
for a, ds in deps.items():
    for d in ds:
        rev[d].add(a)
res = {}
for a in sorted(k for k in deps if k.startswith('bo_')):
    seen, st = set(), list(rev[a])
    while st:
        x = st.pop()
        if x not in seen:
            seen.add(x); st += list(rev[x])
    res[a] = dict(census=cen.get(a), post=(len(rev[a]), len(seen)), direct=sorted(rev[a]), trans=sorted(seen), deps=deps[a])
json.dump(res, open(out, 'w'), indent=1)
for a, v in res.items():
    print(a, 'census', v['census'], 'seed-derived', v['post'])
