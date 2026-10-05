#!/usr/bin/env python3
"""t4_stale_prod.py --pre DIR --maps DIR  (READ-ONLY; production-parameterised copy of rehearsal_final/r2/bin/t4_stale.py)

Connection: the libpq environment of the sourced reader file (PGHOST/PGPORT/PGUSER/PGDATABASE/PGPASSWORD), read-only session forced.
Run as:  ( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; python3 t4_stale_prod.py --pre $EV/W0 --maps <W0 maps dir> )
--pre : folder with pre_build_ids.tsv  (table|build_id|n), pre_cat_facts.tsv (aya|category|n), pre_cat_dashas.tsv (system|aya|level|n),
        pre_cat_divs.tsv (aya|varga|category|n)   -- fields '|' or TAB separated
--maps: folder with chart_facts_map.tsv (fact_id, category, subject, key, aya, formula_id, build_id; COPY text, NULL = \\N)
Prints: survivors with a pre-window build_id per table (EXPECT 0), stored-not-emitted / emitted-not-stored sets, natural keys removed.
Exit 0 iff all four survivor counts are 0 and every stored-not-emitted set is empty; else 1.
"""
import argparse, collections, os, sys
import psycopg
C = '482012f1-710e-4a25-994a-93821f5871aa'
ap = argparse.ArgumentParser(); ap.add_argument('--pre', required=True); ap.add_argument('--maps', required=True); a = ap.parse_args()
def split(l):
    l = l.rstrip('\n'); return l.split('\t') if '\t' in l else l.split('|')
def rows(p): return [split(l) for l in open(p) if l.strip()]
conn = psycopg.connect(options='-c default_transaction_read_only=on'); cur = conn.cursor()
def q(s, *p): cur.execute(s, p); return cur.fetchall()
assert q('select current_setting(%s)', 'transaction_read_only')[0][0] == 'on', 'session is not read-only'
pre_builds = collections.defaultdict(list)
for t, b, n in rows(f'{a.pre}/pre_build_ids.tsv'): pre_builds[t].append(b)
print('pre-state build ids:', {t: len(v) for t, v in pre_builds.items()})
bad = 0; tot = 0
for t in ('chart_facts', 'chart_divisionals', 'chart_dashas', 'chart_vichara'):
    n = q(f'select count(*) from {t} where chart_id=%s and build_id::text = any(%s)', C, pre_builds[t])[0][0]; tot += n
    print(f'  survivors with a pre-window build_id in {t}: {n}')
print('T4 stale survivors (rows carrying a pre-window build_id):', tot); bad += tot
def load(p): return {tuple(r[:-1]) for r in rows(p)}
pre_f, pre_d, pre_v = (load(f'{a.pre}/pre_cat_facts.tsv'), load(f'{a.pre}/pre_cat_dashas.tsv'), load(f'{a.pre}/pre_cat_divs.tsv'))
post_f = {tuple(map(str, r[:2])) for r in q('select ayanamsha_id, fact_category from chart_facts where chart_id=%s group by 1,2', C)}
post_d = {tuple(map(str, r[:3])) for r in q('select system_id, ayanamsha_id, level_n from chart_dashas where chart_id=%s group by 1,2,3', C)}
post_v = {tuple(map(str, r[:3])) for r in q('select ayanamsha_id, varga, fact_category from chart_divisionals where chart_id=%s group by 1,2,3', C)}
for nm, x, y in (('chart_facts (aya,category)', pre_f, post_f), ('chart_dashas (system,aya,level)', pre_d, post_d), ('chart_divisionals (aya,varga,category)', pre_v, post_v)):
    print(f'  {nm}: stored-not-emitted {len(x - y)}  emitted-not-stored {len(y - x)}', sorted(y - x)[:6] if len(y - x) <= 12 else ''); bad += len(x - y)
print('  emitted-not-stored fact categories:', sorted({c for _, c in post_f} - {c for _, c in pre_f}))
pre_keys = set()
for p in rows(f'{a.maps}/chart_facts_map.tsv'): pre_keys.add((p[1], p[2], p[3], p[4], '' if p[5] == '\\N' else p[5]))
post_keys = {tuple('' if x is None else x for x in r) for r in q("select fact_category,fact_subject,fact_key,ayanamsha_id,coalesce(formula_id,'') from chart_facts where chart_id=%s", C)}
removed = pre_keys - post_keys; added = post_keys - pre_keys
print('natural keys removed from re-emitted categories:', len(removed), dict(collections.Counter(k[0] for k in removed)))
print('natural keys added:', len(added), dict(collections.Counter(k[0] for k in added).most_common(8)))
print('T4', 'PASS' if bad == 0 else 'FAIL'); sys.exit(0 if bad == 0 else 1)
