#!/usr/bin/env python3
"""M0-T26 — re-derive the repair sets from THREE independent sources and require agreement.

Nothing here is inherited from DERIVED_FIELD_REPAIR_PROPOSAL_v1_0.md. The proposal's figures
(21 / 20) are re-measured, and any disagreement is reported rather than reconciled.

Source A  the live `layer` column  -> the contract map (this IS the repair rule).
Source B  the asset_id prefix      -> CLAUDE.md N.1 (bg_/ga_/bo_/ka_/ph_/mi_), a DIFFERENT
                                      column written by a different mechanism (migration 224).
Source C  asset_registry_seed.ts read AS TEXT (D-13: never imported) -> its layerNames /
                                      layerIndices maps plus any per-asset explicit override.
                                      This is the seed-durability premise of the task.

Codepoint pins are constants stated HERE, taken from CLAUDE.md N.1 / the catalogue contract --
not from the seed and not from the UPDATE, so an encoding loss anywhere cannot hide.
"""
import json, pathlib, re, sys
import psycopg
from psycopg.rows import dict_row

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SEED = ROOT / 'platform/scripts/seed/asset_registry_seed.ts'

# --- constants pinned here, by codepoint, from CLAUDE.md N.1 -------------------------------
NAME_BY_LAYER = {
    'brahmagyan': 'Brahmagyan',
    'ganita':     'Gaṇita',        # G a U+1E47 i t a          -> 6 chars / 8 bytes
    'bodha':      'Bodha',
    'kala':       'Kāla',          # K U+0101 l a              -> 4 chars / 5 bytes
    'phala':      'Phala',
    'mimamsa':    'Mīmāṃsā',  # M U+012B m U+0101 U+1E43 s U+0101 -> 7 / 12
}
INDEX_BY_LAYER = {'brahmagyan': 'L0', 'ganita': 'L1', 'bodha': 'L2',
                  'kala': 'L3', 'phala': 'L4', 'mimamsa': 'L5'}
INDEX_BY_PREFIX = {'bg_': 'L0', 'ga_': 'L1', 'bo_': 'L2', 'ka_': 'L3', 'ph_': 'L4', 'mi_': 'L5'}
NAME_BY_PREFIX = {p: NAME_BY_LAYER[l] for p, l in
                  zip(INDEX_BY_PREFIX, ['brahmagyan', 'ganita', 'bodha', 'kala', 'phala', 'mimamsa'])}
CODEPOINT_PIN = {'Gaṇita': (6, 8), 'Kāla': (4, 5), 'Mīmāṃsā': (7, 12)}
HELD = {'lel_events'}          # D-23: not mechanically derivable; stays NULL

def db_url():
    for l in (ROOT / 'platform/.env.local').read_text().splitlines():
        if l.startswith('DATABASE_URL='):
            return re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
    raise SystemExit('DATABASE_URL not found')

# --- Source C: parse the seed as text ------------------------------------------------------
def parse_seed():
    src = SEED.read_text(encoding='utf-8')
    seg = src[src.index('const layerNames'):src.index('const assetType')]
    names, idxs = {}, {}
    for k, v in re.findall(r"(\w+):\s*'((?:[^'\\]|\\.)*)'", seg):
        if k in INDEX_BY_LAYER:
            (idxs if re.fullmatch(r'L[0-5]', v) else names)[k] = v
    # per-asset entries: asset_id, and any explicit layer / layer_name / layer_index override
    entries = {}
    # (?<![A-Za-z_]) so `downstream_asset_id:` does not match; first occurrence wins.
    for m in re.finditer(r"(?<![A-Za-z_])asset_id:\s*'([a-z0-9_]+)'", src):
        aid = m.group(1)
        chunk = src[m.start(): m.start() + 4000]
        # stop at the start of the next asset_id entry
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
    return names, idxs, entries

seed_names, seed_idxs, seed_entries = parse_seed()

with psycopg.connect(db_url(), row_factory=dict_row, autocommit=True) as conn:
    c = conn.cursor()
    c.execute("SELECT asset_id, layer, layer_index, layer_name FROM asset_registry ORDER BY asset_id")
    live = c.fetchall()

report = {'live_rows': len(live), 'seed_entries': len(seed_entries),
          'seed_layerNames': seed_names, 'seed_layerIndices': seed_idxs}

# seed map must be byte-identical to the pinned constants
report['seed_map_matches_pin'] = (seed_names == NAME_BY_LAYER and seed_idxs == INDEX_BY_LAYER)

li_repair, ln_repair, disagreements, no_seed_entry, held_rows = [], [], [], [], []
for r in live:
    aid, layer = r['asset_id'], r['layer']
    a_idx, a_name = INDEX_BY_LAYER.get(layer), NAME_BY_LAYER.get(layer)
    pref = aid[:3]
    b_idx = INDEX_BY_PREFIX.get(pref)
    b_name = NAME_BY_PREFIX.get(pref)
    e = seed_entries.get(aid)
    if e is None:
        no_seed_entry.append(aid)
        c_idx = c_name = None
    else:
        seed_layer = e.get('layer', layer)
        c_idx = e.get('layer_index', seed_idxs.get(seed_layer))
        c_name = e.get('layer_name', seed_names.get(seed_layer))
    # cross-source agreement (prefix source only where a prefix is recognised)
    srcs_idx = [x for x in (a_idx, b_idx, c_idx) if x is not None]
    srcs_name = [x for x in (a_name, b_name, c_name) if x is not None]
    if len(set(srcs_idx)) > 1 or len(set(srcs_name)) > 1:
        disagreements.append({'asset_id': aid, 'layer': layer, 'prefix': pref,
                              'idx': {'layer': a_idx, 'prefix': b_idx, 'seed': c_idx},
                              'name': {'layer': a_name, 'prefix': b_name, 'seed': c_name}})
    if aid in HELD:
        held_rows.append({'asset_id': aid, 'layer': layer,
                          'layer_index_now': r['layer_index'], 'layer_name_now': r['layer_name']})
        continue
    if r['layer_index'] != a_idx:
        li_repair.append({'asset_id': aid, 'layer': layer, 'now': r['layer_index'], 'to': a_idx,
                          'defect': 'NULL' if r['layer_index'] is None else
                                    ('MALFORMED' if not re.fullmatch(r'L[0-5]', r['layer_index']) else 'MISMATCH'),
                          'seed_holds': c_idx})
    if r['layer_name'] != a_name:
        ln_repair.append({'asset_id': aid, 'layer': layer, 'now': r['layer_name'], 'to': a_name,
                          'defect': 'NULL' if r['layer_name'] is None else 'WRONG_SPELLING',
                          'seed_holds': c_name})

report.update({
    'layer_index_repair_count': len(li_repair),
    'layer_name_repair_count': len(ln_repair),
    'layer_index_repair': li_repair,
    'layer_name_repair': ln_repair,
    'held_rows': held_rows,
    'cross_source_disagreements': disagreements,
    'assets_with_no_seed_entry': no_seed_entry,
})
# defect-class tallies
for key, s in (('layer_index', li_repair), ('layer_name', ln_repair)):
    tal = {}
    for x in s:
        tal[x['defect']] = tal.get(x['defect'], 0) + 1
    report[key + '_defect_classes'] = tal
# durability premise: does the seed hold the CLEAN value on every repair cell?
report['seed_holds_clean_layer_index'] = sum(1 for x in li_repair if x['seed_holds'] == x['to'])
report['seed_holds_clean_layer_name'] = sum(1 for x in ln_repair if x['seed_holds'] == x['to'])
# codepoint pin on the constants themselves
report['codepoint_pin'] = {k: {'expect_chars': v[0], 'expect_bytes': v[1],
                               'actual_chars': len(k), 'actual_bytes': len(k.encode('utf-8')),
                               'ok': (len(k), len(k.encode('utf-8'))) == v}
                           for k, v in CODEPOINT_PIN.items()}

OUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else 'independent_derivation.json')
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'wrote {OUT.name}')

print(f"live rows                     : {report['live_rows']}")
print(f"seed map == pinned constants  : {report['seed_map_matches_pin']}")
print(f"layer_index repair set        : {report['layer_index_repair_count']}  {report['layer_index_defect_classes']}")
print(f"layer_name  repair set        : {report['layer_name_repair_count']}  {report['layer_name_defect_classes']}")
print(f"held (never written)          : {[h['asset_id'] for h in held_rows]}")
print(f"cross-source disagreements    : {len(disagreements)}  {[d['asset_id'] for d in disagreements]}")
print(f"assets with NO seed entry     : {len(no_seed_entry)}  {no_seed_entry}")
print(f"seed holds CLEAN on repair set: layer_index {report['seed_holds_clean_layer_index']}/{len(li_repair)}"
      f"  layer_name {report['seed_holds_clean_layer_name']}/{len(ln_repair)}")
print(f"codepoint pin                 : {all(v['ok'] for v in report['codepoint_pin'].values())}")
