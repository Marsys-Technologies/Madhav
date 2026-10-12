#!/usr/bin/env python3
"""Offline Dens.served (rev 4) re-scan of the 23 L2 assets with the CURRENT inspector's capability_scan and _grade_dens (A.L2, INDEX section 1).

Stand-ins for what the live run reads from the database: the populated-column lists recorded in the saved census (reach.exposed + reach.dark)
replace information_schema columns, and the shared-table set is the set of target tables owned by more than one L2 asset. The attribution of
served surfaces is exactly the current scanner's; the tier-column part is approximate. Not a census.

Usage: python3 dens_remeasure.py <repo-root>
"""
import collections, json, os, sys
root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
os.chdir(root)
sys.path.insert(0, 'platform/scripts/governance')
import asset_census as ac
b = json.load(open('00_ARCHITECTURE/briefs/suvarna/layers/census/after_reader_grant/census_L2.json'))['L2']
cols = {}
for a in b['assets']:
    r = a['reach']
    cols.setdefault(a['target_table'], sorted(set(r.get('exposed', [])) | set(r.get('dark', []))))
owners = collections.defaultdict(list)
for a in b['assets']:
    owners[a['target_table']].append(a['asset_id'])
shared = {t for t, v in owners.items() if len(v) > 1}
for a in b['assets']:
    aid, tbl = a['asset_id'], a['target_table']
    dtoks = list(dict.fromkeys([t for t in ([tbl] if tbl else []) + list(a['count_sql_tables']) + [aid] if t]))
    cap = ac.capability_scan(ac.CAPS_ROOTS, dtoks, shared=shared, columns=cols, outside_roots=ac.DENS_OUTSIDE_ROOTS)
    g = ac._grade_dens(cap, tbl or aid)
    print(aid, '| saved:', a['measurements']['Dens.served']['v'], '| offline rev4:', g['v'], '|', g['measured'][:300])
