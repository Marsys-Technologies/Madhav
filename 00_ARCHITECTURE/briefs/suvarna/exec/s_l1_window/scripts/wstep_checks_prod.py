#!/usr/bin/env python3
"""wstep_checks_prod.py RUN_P RUN_17 --log LOGFILE [--log LOGFILE ...] [--receipts-pre FILE]   (READ-ONLY; production copy of r2/bin/wstep_checks.py)

Per-asset W-step checks for the 18 ga_* lanes. Connection: the libpq environment of the sourced reader file, read-only session forced:
  ( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; python3 wstep_checks_prod.py $RUN_P $RUN_17 --log $EV/W3/job_X.log --log $EV/W3/job_Y.log )
 C1 asset_throughput 'lit' and last_error NULL        C2 build_run_assets complete/build in the S-L1 run, run 'completed'
 C3 ALL stored rows of the asset's footprint carry ONE build_id == its run id
 C4 the newest receipt is 'proven' and bound to the run id (and newer than --receipts-pre, the W0 pre_receipts_ga.tsv, when given)
 C5 rows the writer reported in the job log ('asset <id> complete - N rows') == rows stored
 Global (plain SQL, ALL vargas): zero longitude_sidereal graha rows; zero degree_in_sign rows in ANY varga; 0 floored special_lagna.
Prints one JSON line per asset, then the global counts and `WSTEP PASS|FAIL`. Exit 0 iff 18/18 ok and the global counts are 0.
"""
import argparse, json, re, sys
import psycopg
C = '482012f1-710e-4a25-994a-93821f5871aa'
ap = argparse.ArgumentParser(); ap.add_argument('run_p'); ap.add_argument('run_17'); ap.add_argument('--log', action='append', default=[]); ap.add_argument('--receipts-pre'); a = ap.parse_args()
A17 = 'ga_ayurdaya ga_condition ga_dashas ga_medical ga_nakshatra ga_panchanga ga_sade_sati ga_sensitive ga_sensitive_degree ga_strength ga_structural ga_tajaka ga_transit_anchors ga_vargas ga_vastu ga_vichara ga_yoga'.split()
RUN = {'ga_positions': a.run_p, **{x: a.run_17 for x in A17}}
log = ''.join(open(p, errors='replace').read() for p in a.log)
reported = {m.group(1): int(m.group(2)) for m in re.finditer(r'asset (ga_\w+) complete \W+ (\d+) rows', log)}
pre_rec = {}
if a.receipts_pre:
    for l in open(a.receipts_pre):
        p = l.rstrip('\n').split('|')
        if len(p) >= 2 and p[1]: pre_rec[p[0]] = p[1]
conn = psycopg.connect(options='-c default_transaction_read_only=on'); cur = conn.cursor()
def q(s, *p): cur.execute(s, p); return cur.fetchall()
assert q('select current_setting(%s)', 'transaction_read_only')[0][0] == 'on', 'session is not read-only'
reg = {r[0]: r[1] for r in q("select asset_id, target_table from asset_registry where asset_id like 'ga\\_%%'")}
okall = True
for x in sorted(RUN):
    row = {'asset': x, 'run': RUN[x][:8]}
    st = q('select state, last_error from asset_throughput where asset_id=%s and chart_id=%s', x, C); row['C1'] = bool(st) and st[0][0] == 'lit' and st[0][1] is None
    ra = q('select r.state, b.state, b.disposition from build_run_assets b join build_runs r on r.id=b.run_id where b.run_id=%s and b.asset_id=%s', RUN[x], x)
    row['C2'] = bool(ra) and ra[0] == ('completed', 'complete', 'build')
    stored = 0; builds = set(); nobid = False
    cats = [r[0] for r in q('select fact_category from fact_category_ownership where owning_asset_id=%s', x)]
    if cats:
        for n, b in q('select count(*), build_id::text from chart_facts where chart_id=%s and fact_category = any(%s) group by 2', C, cats): stored += n; builds.add(b)
    t = reg.get(x)
    if t and t != 'chart_facts':
        has = q("select count(*) from information_schema.columns where table_schema='public' and table_name=%s and column_name='build_id'", t)[0][0]
        if has:
            for n, b in q(f'select count(*), build_id::text from {t} where chart_id=%s group by 2', C): stored += n; builds.add(b)
        else:
            nobid = True; stored += q(f'select count(*) from {t} where chart_id=%s', C)[0][0]
    row.update(stored=stored, reported=reported.get(x), builds=sorted(b[:8] for b in builds), no_build_id_col=nobid)
    row['C3'] = builds == {RUN[x]} or (nobid and not builds and stored > 0)
    rc = q('select receipt_state, observed_at::text, build_id::text from asset_provenance_receipts where asset_id=%s and chart_id=%s order by observed_at desc limit 1', x, C)
    row['C4'] = bool(rc) and rc[0][0] == 'proven' and rc[0][2] == RUN[x] and (x not in pre_rec or rc[0][1] > pre_rec[x])
    row['C5'] = row['reported'] == stored
    row['ok'] = all(row[k] for k in ('C1', 'C2', 'C3', 'C4', 'C5')); okall &= row['ok']; print(json.dumps(row))
z1 = q("select count(*) from chart_facts where chart_id=%s and fact_category='graha_position' and fact_key='longitude_sidereal' and fact_value_num=0", C)[0][0]
z2 = q("select varga, count(*) from chart_divisionals where chart_id=%s and fact_category='varga_position' and fact_key='degree_in_sign' and fact_value_num=0 group by 1 order by 1", C)
sp = q("select count(*) from chart_facts where chart_id=%s and fact_category='special_lagna' and verification_pass_status='floored'", C)[0][0]
print('zero graha longitude_sidereal rows:', z1, '| zero degree_in_sign rows in ANY varga:', z2, '| floored special_lagna:', sp)
good = okall and z1 == 0 and not z2 and sp == 0
print('WSTEP', 'PASS' if good else 'FAIL'); sys.exit(0 if good else 1)
