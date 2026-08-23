#!/usr/bin/env python3
"""Per-asset measurement: actual rows vs floor (native chart), descriptions, checks.
Writes 00_ARCHITECTURE/control/asset_measurements.json (durable, re-runnable)."""
import json, pathlib, re, sys, datetime
import psycopg
ROOT = pathlib.Path(__file__).resolve().parents[2]
NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
url = next(re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
           for l in (ROOT/'platform/.env.local').read_text().splitlines() if l.startswith('DATABASE_URL='))
out = {}
with psycopg.connect(url, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
    c = conn.cursor()
    c.execute("SET statement_timeout = '45s'")
    c.execute("""SELECT asset_id, english_description, volume_explanation, count_sql, integrity_check_sql,
                        clear_tables, target_floor, target_table, scope, storage_type, provides_apis, health_probe,
                        writer_timeout_seconds, expected_volume_formula
                 FROM asset_registry ORDER BY asset_id""")
    regs = c.fetchall()
    for r in regs:
        a = r['asset_id']
        rec = {k: (v if not isinstance(v, (dict, list)) else json.dumps(v)) for k, v in r.items() if k not in ('count_sql',)}
        rec['actual_rows_native'] = None; rec['count_error'] = None
        sql = r['count_sql']
        if sql:
            try:
                q = sql.replace('%', '%%')
                if '$1' in q:
                    c.execute(q.replace('$1', '%s'), (NATIVE,) * q.count('$1'))
                else:
                    c.execute(q)
                row = c.fetchone()
                rec['actual_rows_native'] = int(list(row.values())[0]) if row else None
            except Exception as e:
                rec['count_error'] = str(e).splitlines()[0][:160]
                try: c.execute("ROLLBACK")
                except Exception: pass
        out[a] = rec
    # per-chart row counts for the two other charts on per_chart assets (cheap: reuse count_sql)
    c.execute("SELECT asset_id, count_sql FROM asset_registry WHERE scope='per_chart' AND count_sql LIKE '%$1%'")
    for r in c.fetchall():
        for cid, key in (('1c826d5a-41cb-4450-b4dc-59d440e5f75a','actual_rows_abhinandan'),
                         ('cb73cd3d-9eba-4220-9902-0de91566e980','actual_rows_chart3')):
            try:
                q2 = r['count_sql'].replace('%', '%%')
                c.execute(q2.replace('$1', '%s'), (cid,) * q2.count('$1')); row = c.fetchone()
                out[r['asset_id']][key] = int(list(row.values())[0]) if row else None
            except Exception as e:
                out[r['asset_id']][key] = None
                try: c.execute("ROLLBACK")
                except Exception: pass
out['_meta'] = {'measured_at': datetime.datetime.utcnow().isoformat()+'Z', 'native_chart': NATIVE}
(ROOT/'00_ARCHITECTURE/control/asset_measurements.json').write_text(json.dumps(out, indent=1, default=str))
n = len(regs); ok = sum(1 for a,v in out.items() if a!='_meta' and v['actual_rows_native'] is not None)
err = [a for a,v in out.items() if a!='_meta' and v['count_error']]
print(f'measured {ok}/{n} counts; errors: {len(err)} -> {err[:10]}')
