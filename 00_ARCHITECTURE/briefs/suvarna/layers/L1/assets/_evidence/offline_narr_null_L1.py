#!/usr/bin/env python3
"""A.L1: main's Null/Narr graders (the same pure graders measure() calls) over the SAVED L1 census records + committed
declarations + DDL-derived column stand-in (E6.1 ddl_c, repo = this lane's worktree). Offline, no DB, no row data
(so Null.blank_rows / counts read INCONCLUSIVE). Indicative, not a measurement."""
import importlib.util, json, os, sys, tempfile, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
LANE = Path(os.environ.get('LANE', HERE.parents[6]))
os.environ['NIKASHA_CONTROL_DIR'] = tempfile.mkdtemp(prefix='al1-')
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(LANE / 'platform/scripts/governance'))
import ddl_c; ddl_c.REPO = str(LANE / 'platform')
import asset_census as new
DDL = ddl_c.build()
CEN = LANE / '00_ARCHITECTURE/briefs/suvarna/layers/census'
d1 = json.load(open(CEN / 'census_L1.json'))['L1']; d2 = json.load(open(CEN / 'after_reader_grant/census_L1.json'))['L1']
a2 = {a['asset_id']: a for a in d2['assets']}
assets = [a2[a['asset_id']] if a['asset_id'] == 'ga_prashna' else a for a in d1['assets']]
decls = new.load_asset_declarations(); tests = new.python_tests(); vocab = new.prose_vocabulary(decls)
res_all = {}
for a in assets:
    aid, tbl = a['asset_id'], a['target_table']
    own = {}
    for t in dict.fromkeys([x for x in [tbl] + list(a.get('count_sql_tables') or []) if x]):
        dd = DDL.get(t)
        own[t] = (sorted(dd) if dd else None, {k: v[0] for k, v in dd.items()} if dd else None, {k: v[1] for k, v in dd.items() if v[1]} if dd else None)
    d = DDL.get(tbl) if tbl else None
    ctx = dict(table=tbl, counts=None, paths=[], written=None, tests=tests, vocabulary=vocab, own=own)
    pf = (decls.get(aid) or {}).get('prose_fields')
    if a['writer_files'] and pf is not None:
        try:
            units, _ = new._delegation_scope(aid, a['writer_files'])
            ctx['paths'] = [u['path'] for u in units]
            ctx['written'] = new.written_columns(units, [tbl] + list(a.get('count_sql_tables') or []))
        except new.Unknown as exc:
            ctx['scope_err'] = str(exc)
    r = new.prose_checks(aid, decls.get(aid), ctx)
    res_all[aid] = {k: dict(v=v['v'], measured=v['measured'][:600], inconclusive=bool(v.get('inconclusive'))) for k, v in r.items()}
    print(aid, {k.split('.')[1]: v['v'] + ('*' if v.get('inconclusive') else '') for k, v in r.items()})
(HERE / 'narr_null_offline_L1.json').write_text(json.dumps(res_all, indent=1))
