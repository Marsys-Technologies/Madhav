#!/usr/bin/env python3
"""Per-table read-only profile on the canonical chart: columns, non-null counts, small-cardinality value counts, FKs, checks, unique indexes, per-chart row totals."""
import json, sys
from collect import q, jq, C
def profile(t):
    out = {'table': t}
    cols = q(f"select column_name, data_type, is_nullable, column_default from information_schema.columns where table_schema='public' and table_name='{t}' order by ordinal_position")
    out['columns'] = cols
    has_chart = any(c['column_name'] == 'chart_id' for c in cols)
    out['has_chart_id'] = has_chart
    out['rows_by_chart'] = q(f"select chart_id::text, count(*) n from {t} group by 1 order by 2 desc") if has_chart else q(f"select count(*) n from {t}")
    where = f"where chart_id='{C}'" if has_chart else ''
    sel = ', '.join([f"count(\"{c['column_name']}\") as \"{c['column_name']}\"" for c in cols])
    r = q(f"select count(*) as _total, {sel} from {t} {where}")
    out['chart_nonnull'] = r[0] if r and isinstance(r, list) else r
    vc = {}
    for c in cols:
        if c['data_type'] in ('text', 'character varying', 'boolean', 'smallint') and c['column_name'] not in ('source_citation',):
            n = q(f"select count(distinct \"{c['column_name']}\") n from {t} {where}")
            try: nd = int(n[0]['n'])
            except Exception: continue
            if nd <= 14:
                vc[c['column_name']] = q(f"select \"{c['column_name']}\"::text v, count(*) n from {t} {where} group by 1 order by 2 desc")
    out['value_counts'] = vc
    out['constraints'] = q(f"select conname, contype, pg_get_constraintdef(oid) def from pg_constraint where conrelid='public.{t}'::regclass order by contype, conname")
    out['indexes'] = q(f"select indexname, indexdef from pg_indexes where schemaname='public' and tablename='{t}'")
    out['referenced_by'] = q(f"select conrelid::regclass::text tbl, conname, pg_get_constraintdef(oid) def from pg_constraint where confrelid='public.{t}'::regclass")
    return out
if __name__ == '__main__':
    for t in sys.argv[1:]:
        d = profile(t)
        json.dump(d, open(f'/Users/Dev/suvarna-evidence/A_L4/data/table_{t}.json', 'w'), indent=1, default=str)
        print(t, d['chart_nonnull'].get('_total') if isinstance(d['chart_nonnull'], dict) else d['chart_nonnull'])
