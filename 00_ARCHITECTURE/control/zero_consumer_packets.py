#!/usr/bin/env python3
"""M0-T6 (0.8c) — evidence packet inputs for every asset with no detected serving consumer.

Read-only. Adds, per zero-serving asset: registry prose, live row shape and count on the
native chart / the singleton, and the DB-side facts a disposition decision would need.
Writes 00_ARCHITECTURE/control/zero_consumer_evidence.json. DECIDES NOTHING (G1 is
ADHIKĀRIN's).
"""
import json, pathlib, re, datetime
import psycopg

ROOT = pathlib.Path(__file__).resolve().parents[2]
NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
MAP = json.loads((ROOT / '00_ARCHITECTURE/control/CONSUMER_MAP.json').read_text())

url = next(re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
           for l in (ROOT / 'platform/.env.local').read_text().splitlines()
           if l.startswith('DATABASE_URL='))

targets = sorted(a for a, v in MAP['assets'].items()
                 if v['evidence_class'] != 'serving_consumer_detected'
                 and v['evidence_class'] != 'serving_consumer_detected_via_code_module')

out = {}
with psycopg.connect(url, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
    c = conn.cursor()
    c.execute("SET statement_timeout = '60s'")
    for a in targets:
        v = MAP['assets'][a]
        c.execute("""SELECT english_description, volume_explanation, count_sql, size_sql,
                            integrity_check_sql, target_floor, depends_on, clear_tables,
                            health_probe, provides_apis, has_substeps, estimated_seconds,
                            service_health, last_invoked_at
                     FROM asset_registry WHERE asset_id = %s""", (a,))
        reg = c.fetchone()
        rec = {'registry': {k: (str(x) if isinstance(x, (datetime.datetime,)) else x)
                            for k, x in reg.items()}}
        # who declares this asset as a dependency
        c.execute("SELECT asset_id FROM asset_registry WHERE %s = ANY(depends_on) ORDER BY 1", (a,))
        rec['declared_downstream_dependents'] = [r['asset_id'] for r in c.fetchall()]
        # throughput
        c.execute("""SELECT chart_id::text, state, rows_written, last_built_at::text, last_error
                     FROM asset_throughput WHERE asset_id = %s ORDER BY last_built_at DESC""", (a,))
        rec['asset_throughput_rows'] = c.fetchall()
        # live table shape
        rec['tables'] = {}
        for t in v['tables_scanned']:
            info = {}
            # pg_attribute covers ordinary tables, views AND materialized views;
            # information_schema.columns silently omits matviews (a real false-negative trap).
            c.execute("""SELECT a.attname AS column_name,
                                format_type(a.atttypid, a.atttypmod) AS data_type,
                                cl.relkind
                         FROM pg_class cl
                         JOIN pg_namespace n ON n.oid = cl.relnamespace
                         JOIN pg_attribute a ON a.attrelid = cl.oid
                         WHERE n.nspname='public' AND cl.relname=%s
                           AND a.attnum > 0 AND NOT a.attisdropped
                         ORDER BY a.attnum""", (t,))
            cols = c.fetchall()
            info['columns'] = [f"{r['column_name']}:{r['data_type']}" for r in cols]
            info['exists'] = bool(cols)
            info['relkind'] = ({'r': 'table', 'v': 'view', 'm': 'materialized view',
                                'p': 'partitioned table', 'f': 'foreign table'}
                               .get(cols[0]['relkind']) if cols else None)
            if cols:
                try:
                    c.execute(f'SELECT count(*) AS n FROM public."{t}"')
                    info['total_rows'] = c.fetchone()['n']
                except Exception as e:
                    info['total_rows'] = None
                    info['count_error'] = str(e).splitlines()[0][:160]
                if any(r['column_name'] == 'chart_id' for r in cols):
                    try:
                        c.execute(f'SELECT count(*) AS n FROM public."{t}" WHERE chart_id = %s', (NATIVE,))
                        info['rows_on_native_chart'] = c.fetchone()['n']
                    except Exception as e:
                        info['rows_on_native_chart'] = None
                        info['native_count_error'] = str(e).splitlines()[0][:160]
                else:
                    info['rows_on_native_chart'] = 'n/a — table is not chart-scoped'
            rec['tables'][t] = info
        # registry count_sql as the registry itself defines it
        if reg['count_sql']:
            try:
                q = reg['count_sql'].replace('%', '%%')
                if '$1' in q:
                    c.execute(q.replace('$1', '%s'), (NATIVE,) * q.count('$1'))
                else:
                    c.execute(q)
                row = c.fetchone()
                rec['registry_count_sql_result'] = int(list(row.values())[0]) if row else None
            except Exception as e:
                rec['registry_count_sql_result'] = None
                rec['registry_count_sql_error'] = str(e).splitlines()[0][:200]
        out[a] = rec

(ROOT / '00_ARCHITECTURE/control/zero_consumer_evidence.json').write_text(
    json.dumps({'_meta': {'generated_at': datetime.datetime.now(datetime.timezone.utc)
                          .isoformat().replace('+00:00', 'Z'),
                          'native_chart': NATIVE,
                          'source_map': '00_ARCHITECTURE/control/CONSUMER_MAP.json',
                          'assets': len(out),
                          'certifies': 'nothing; no disposition proposed or taken (G1 is ADHIKARIN)'},
                'assets': out}, indent=1, default=str))
print(f'packets for {len(out)} assets:', ', '.join(targets))
