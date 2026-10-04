#!/usr/bin/env python3
"""A.L4/A.L5 read-only evidence collector. Every query is a SELECT through q.sh (suvarna_reader, default_transaction_read_only=on).
Usage: collect.py <layer> <asset_id>... ; writes data/<asset>.json"""
import json, subprocess, sys, datetime, re
C = '482012f1-710e-4a25-994a-93821f5871aa'
Q = '/Users/Dev/suvarna-evidence/A_L4/q.sh'
def q(sql, rows=True):
    r = subprocess.run([Q, sql], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().split('\n')
    if out and out[0].startswith('ERROR'): return {'error': '\n'.join(out)[:400]}
    if not rows: return '\n'.join(out)
    if not out or len(out) < 2: return []
    hdr = out[0].split('|')
    res = []
    for ln in out[1:]:
        if re.match(r'^\(\d+ rows?\)$', ln): continue
        res.append(dict(zip(hdr, ln.split('|'))))
    return res
def jq(sql):
    """single json value via row_to_json / jsonb_agg"""
    r = subprocess.run([Q, "select (" + sql + ")::text"], capture_output=True, text=True)
    lines = r.stdout.strip().split('\n')
    if len(lines) < 2: return {'error': (r.stdout + r.stderr)[:300]}
    return json.loads(lines[1]) if lines[1] not in ('', None) else None
def collect(aid):
    d = {'asset_id': aid, 'collected_utc': datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + 'Z', 'chart': C}
    d['registry'] = jq(f"select to_jsonb(r) from asset_registry r where asset_id='{aid}'")
    d['throughput'] = jq(f"select to_jsonb(t) from asset_throughput t where asset_id='{aid}' and chart_id='{C}'")
    d['runs_summary'] = jq(f"select jsonb_agg(x) from (select state, disposition, count(*) n, max(ended_at) last from build_run_assets where asset_id='{aid}' group by 1,2 order by 1,2) x")
    d['last_runs'] = jq(f"select jsonb_agg(x) from (select b.run_id, b.state, b.disposition, b.started_at, b.ended_at, left(b.error,300) error, b.output_changed, r.chart_id, r.scope from build_run_assets b join build_runs r on r.id=b.run_id where b.asset_id='{aid}' order by b.started_at desc nulls last limit 8) x")
    d['last_runs_canonical'] = jq(f"select jsonb_agg(x) from (select b.run_id, b.state, b.disposition, b.started_at, b.ended_at, left(b.error,300) error, b.output_changed from build_run_assets b join build_runs r on r.id=b.run_id where b.asset_id='{aid}' and r.chart_id='{C}' order by b.started_at desc nulls last limit 8) x")
    csql = (d['registry'] or {}).get('count_sql')
    if csql:
        d['live_count'] = q(csql.replace('$1', f"'{C}'::uuid"), rows=False)
    return d
if __name__ == '__main__':
    for a in sys.argv[1:]:
        d = collect(a)
        json.dump(d, open(f'/Users/Dev/suvarna-evidence/A_L4/data/{a}.json', 'w'), indent=1, default=str)
        print(a, d['throughput'] and (d['throughput']['state'], d['throughput']['rows_written']), d.get('live_count'))
