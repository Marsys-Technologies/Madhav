#!/usr/bin/env python3
"""M0-T21 INDEPENDENT re-derivation of the asset_kind/asset_type disagreement set.

Deliberately does NOT reuse any script or JSON from 00_ARCHITECTURE/control/.
Reads the live DB read-only, and re-derives writer presence from the source tree by
ast.parse over @register decorators (not from asset_registry.has_writer).

READ ONLY. SET default_transaction_read_only = on.
"""
import ast, json, pathlib, re, sys
import psycopg

ROOT = pathlib.Path(__file__).resolve().parents[3].parent  # repo root
# snapshots/<ts>_kind_fields/ -> control -> 00_ARCHITECTURE -> repo
ROOT = pathlib.Path(__file__).resolve().parents[4] if (pathlib.Path(__file__).resolve().parents[3].name == '00_ARCHITECTURE') else ROOT
REPO = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')
url = next(re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
           for l in (REPO/'platform/.env.local').read_text().splitlines() if l.startswith('DATABASE_URL='))

# ---- 1. registered writers, from source, via AST ----
registered = {}
for p in (REPO/'platform/python-sidecar').rglob('*.py'):
    if 'dag_edge_guard' in p.name or p.name == 'runner.py':
        pass  # still parse; we only collect decorator string literals on classes/functions
    try:
        tree = ast.parse(p.read_text(), filename=str(p))
    except Exception:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            continue
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == 'register':
                for a in dec.args:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        registered.setdefault(a.value, []).append(f"{p.relative_to(REPO)}:{node.lineno}")

# ---- 2. live registry, read only ----
PERMITTED = {('data','data'), ('artifact','data'), ('service','service'), ('source','data')}
with psycopg.connect(url, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
    c = conn.cursor()
    c.execute("SET default_transaction_read_only = on")
    c.execute("""SELECT asset_id, layer, asset_kind, asset_type, storage_type, catalog_status,
                        is_active, target_table, count_sql IS NOT NULL AS has_count_sql,
                        target_floor, health_probe IS NOT NULL AS has_health_probe,
                        provides_apis IS NOT NULL AS has_provides_apis, service_health,
                        has_writer
                 FROM asset_registry ORDER BY asset_id""")
    rows = c.fetchall()
    c.execute("""SELECT conname, pg_get_constraintdef(oid) AS def FROM pg_constraint
                 WHERE conrelid='asset_registry'::regclass AND contype='c'
                   AND conname IN ('asset_registry_asset_kind_check','asset_registry_asset_type_check',
                                   'asset_registry_storage_type_check','asset_registry_catalog_status_check')
                 ORDER BY conname""")
    cons = c.fetchall()

print(f"total rows: {len(rows)}")
print("\n-- CHECK constraints (verbatim) --")
for k in cons:
    print(f"  {k['conname']}\n    {k['def']}")

print("\n-- triple census --")
from collections import Counter
tri = Counter((r['asset_kind'], r['asset_type'], r['storage_type']) for r in rows)
for t, n in sorted(tri.items()):
    ok = (t[0], t[1]) in PERMITTED
    print(f"  {t[0]:<9} {t[1]:<8} {t[2]:<15} n={n:<4} {'OK' if ok else '<<< INCOHERENT'}")

disagree = [r for r in rows if (r['asset_kind'], r['asset_type']) not in PERMITTED]
print(f"\n-- C-14 disagreements: {len(disagree)} --")

def verdict(r):
    """Independent per-asset verdict from evidence, NOT from either column."""
    ev = []
    score_service = 0; score_data = 0
    if r['storage_type'] == 'service':
        score_service += 1; ev.append("storage_type=service")
    if r['has_health_probe']:
        score_service += 1; ev.append("health_probe NOT NULL (contract §4.10 service-only)")
    if r['has_provides_apis']:
        score_service += 1; ev.append("provides_apis NOT NULL (service-only)")
    if r['service_health'] is not None:
        score_service += 1; ev.append(f"service_health={r['service_health']} (C-16: non-service must be NULL)")
    if r['target_table']:
        score_data += 1; ev.append(f"target_table={r['target_table']} (data-shaped)")
    if r['has_count_sql']:
        score_data += 1; ev.append("count_sql NOT NULL (data-shaped)")
    if r['target_floor'] is not None:
        score_data += 1; ev.append(f"target_floor={r['target_floor']} (data-shaped)")
    regs = registered.get(r['asset_id'])
    ev.append(f"@register: {regs if regs else 'NONE FOUND IN SOURCE'}")
    return ('service' if score_service > score_data else 'data' if score_data > score_service else 'AMBIGUOUS',
            score_service, score_data, ev)

plan = []
for r in disagree:
    v, ss, sd, ev = verdict(r)
    which = None
    if v == 'service':
        if r['asset_kind'] != 'service' and r['asset_type'] == 'service':
            which = 'asset_kind'
        elif r['asset_type'] != 'service' and r['asset_kind'] == 'service':
            which = 'asset_type'
        else:
            which = 'BOTH/UNCLEAR'
    plan.append(dict(asset_id=r['asset_id'], layer=r['layer'], kind=r['asset_kind'],
                     type=r['asset_type'], storage=r['storage_type'], status=r['catalog_status'],
                     verdict=v, service_pts=ss, data_pts=sd, column_to_fix=which, evidence=ev))
    print(f"\n  {r['asset_id']}  [{r['layer']} / {r['catalog_status']}]")
    print(f"    kind={r['asset_kind']} type={r['asset_type']} storage={r['storage_type']}")
    print(f"    VERDICT={v}  (service_pts={ss} data_pts={sd})  FIX COLUMN -> {which}")
    for e in ev:
        print(f"      - {e}")

print("\n-- NEGATIVE CONTROLS (must NOT be in the change set) --")
byid = {r['asset_id']: r for r in rows}
for a in ('bo_cdlm_summary','ka_sangam','ph_pramana','lel_events','ka_dasha_kala','ka_tulana'):
    r = byid.get(a)
    print(f"  {a:<24} kind={r['asset_kind']:<9} type={r['asset_type']:<8} storage={r['storage_type']}")

print("\n-- artifact cohort size (would be destroyed by a naive collapse) --")
print("  artifact rows:", sum(1 for r in rows if r['asset_kind']=='artifact'))
print("  rows with 'service' in any of the 3 columns:",
      sum(1 for r in rows if 'service' in (r['asset_kind'], r['asset_type'], r['storage_type'])))

print("\n-- current totals --")
print("  asset_kind:", dict(Counter(r['asset_kind'] for r in rows)))
print("  asset_type:", dict(Counter(r['asset_type'] for r in rows)))
print("  storage_type:", dict(Counter(r['storage_type'] for r in rows)))

out = pathlib.Path(__file__).parent / 'independent_derivation.json'
out.write_text(json.dumps(dict(total=len(rows), disagreements=plan,
    triples={f"{k[0]}|{k[1]}|{k[2]}": v for k, v in tri.items()},
    kind_totals=dict(Counter(r['asset_kind'] for r in rows)),
    type_totals=dict(Counter(r['asset_type'] for r in rows))), indent=1))
print(f"\nwrote {out}")
