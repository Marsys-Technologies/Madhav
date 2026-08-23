#!/usr/bin/env python3
"""M0-T26 SEED-DURABILITY RE-PROJECTION for layer_index / layer_name -- measured, not inherited.

The premise this task was unblocked on (SEED_DURABILITY_REGISTER section 3.5) is that on every
divergent cell the SEED holds the CLEAN value, so a re-seed REPAIRS these columns rather than
reverting them. That premise was measured BEFORE the repair. This re-measures it AFTER.

Method (D-13: the seed is READ AS TEXT, never imported):
  - parse the per-asset ASSETS entries for asset_id / layer / explicit layer_name / layer_index
  - apply the seed's own derivation, verbatim from :3269-3270
        layerName  = asset.layer_name  ?? layerNames[asset.layer]  ?? asset.layer
        layerIndex = asset.layer_index ?? layerIndices[asset.layer] ?? null
  - both columns are in the ON CONFLICT DO UPDATE SET list (= EXCLUDED, unconditional), so the
    projected value IS what a re-seed writes
  - compare against the live post-repair value
"""
import json, pathlib, re, sys
import psycopg
from psycopg.rows import dict_row

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SEED = ROOT / 'platform/scripts/seed/asset_registry_seed.ts'

def db_url():
    for l in (ROOT / 'platform/.env.local').read_text().splitlines():
        if l.startswith('DATABASE_URL='):
            return re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
    raise SystemExit('DATABASE_URL not found')

src = SEED.read_text(encoding='utf-8')
seg = src[src.index('const layerNames'):src.index('const assetType')]
names, idxs = {}, {}
for k, v in re.findall(r"(\w+):\s*'((?:[^'\\]|\\.)*)'", seg):
    (idxs if re.fullmatch(r'L[0-5]', v) else names)[k] = v

# confirm both columns really are unconditionally overwritten on conflict
onconf = src[src.index('ON CONFLICT (asset_id) DO UPDATE SET'):][:4000]
guarded = {c: bool(re.search(c + r'\s*=\s*CASE', onconf)) for c in ('layer_name', 'layer_index')}
inlist = {c: bool(re.search(c + r'\s*=\s*EXCLUDED\.' + c, onconf)) for c in ('layer_name', 'layer_index')}

entries = {}
# (?<![A-Za-z_]) so `downstream_asset_id:` does not match; first occurrence wins.
for m in re.finditer(r"(?<![A-Za-z_])asset_id:\s*'([a-z0-9_]+)'", src):
    aid = m.group(1)
    chunk = src[m.start(): m.start() + 6000]
    nxt = re.search(r"asset_id:\s*'[a-z0-9_]+'", chunk[10:])
    if nxt:
        chunk = chunk[:10 + nxt.start()]
    e = {}
    for key in ('layer', 'layer_name', 'layer_index'):
        mm = re.search(key + r":\s*'((?:[^'\\]|\\.)*)'", chunk)
        if mm:
            e[key] = mm.group(1)
    if aid not in entries:
        entries[aid] = e

with psycopg.connect(db_url(), row_factory=dict_row, autocommit=True) as conn:
    c = conn.cursor()
    c.execute("SELECT asset_id, layer, layer_index, layer_name FROM asset_registry ORDER BY asset_id")
    live = c.fetchall()

div = []
for r in live:
    aid = r['asset_id']
    e = entries.get(aid)
    if e is None:
        continue                      # unreachable by a re-seed: not an INSERT and not an UPDATE
    lyr = e.get('layer')
    s_name = e.get('layer_name') or names.get(lyr) or lyr
    s_idx = e.get('layer_index') or idxs.get(lyr)
    for col, sv in (('layer_index', s_idx), ('layer_name', s_name)):
        if r[col] != sv:
            div.append({'asset_id': aid, 'column': col, 'live': r[col], 'reseed_writes': sv,
                        'direction': ('seed fills a live NULL' if r[col] is None else
                                      'seed NULLs a live value' if sv is None else
                                      'both non-null, differ')})

out = {'live_rows': len(live), 'seed_entries': len(entries),
       'columns_in_do_update_as_EXCLUDED': inlist, 'columns_CASE_guarded': guarded,
       'rows_not_in_seed': sorted(set(r['asset_id'] for r in live) - set(entries)),
       'divergent_cells_after_repair': div,
       'divergent_layer_index': sum(1 for d in div if d['column'] == 'layer_index'),
       'divergent_layer_name': sum(1 for d in div if d['column'] == 'layer_name')}
(HERE / 'durability_after_repair.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')

print(f"seed writes both cols unconditionally (= EXCLUDED): {inlist}   CASE-guarded: {guarded}")
print(f"rows with no seed entry (unreachable by re-seed)  : {out['rows_not_in_seed']}")
print(f"divergent cells AFTER repair -> layer_index {out['divergent_layer_index']}"
      f"  layer_name {out['divergent_layer_name']}   (register measured 21 / 20 BEFORE)")
for d in div:
    print(f"   {d['asset_id']}.{d['column']}: live={d['live']!r}  re-seed writes {d['reseed_writes']!r}  [{d['direction']}]")
