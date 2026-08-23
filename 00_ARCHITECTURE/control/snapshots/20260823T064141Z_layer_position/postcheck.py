#!/usr/bin/env python3
"""M0-T26 POST-CHECK -- verified against the SNAPSHOT, not against the statement's shape.

P1  Diff live vs snapshot cell by cell. The set of (asset_id, column) cells that MOVED must
    equal exactly the re-derived repair set: 20 layer_index + 19 layer_name.
P2  No row that already held a CORRECT value changed (that is P1's complement, asserted
    explicitly because it is the failure the rowcount alone cannot see).
P3  Every moved cell landed on the value derive_independent.py computed -- and on the value the
    seed holds (the durability premise).
P4  lel_events still NULL / NULL.
P5  `layer` (the derivation INPUT) is byte-identical to the snapshot on all rows -- proof the
    repair did not move its own input.
P6  Contract rules C-02 / C-03: exactly 1 violation each, and it must be lel_events.
P7  Codepoint pin (constants stated in preflight.py) holds on the applied rows.
"""
import json, pathlib, re, sys
import psycopg
from psycopg.rows import dict_row

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]

def db_url():
    for l in (ROOT / 'platform/.env.local').read_text().splitlines():
        if l.startswith('DATABASE_URL='):
            return re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
    raise SystemExit('DATABASE_URL not found')

snap = {r['asset_id']: r for r in json.loads((HERE / 'snapshot.json').read_text(encoding='utf-8'))['rows']}
der = json.loads((HERE / 'independent_derivation.json').read_text(encoding='utf-8'))
want = {}
for col, key in (('layer_index', 'layer_index_repair'), ('layer_name', 'layer_name_repair')):
    for x in der[key]:
        want[(x['asset_id'], col)] = (x['to'], x['seed_holds'])

with psycopg.connect(db_url(), row_factory=dict_row, autocommit=True) as conn:
    c = conn.cursor()
    c.execute("SELECT asset_id, layer, layer_index, layer_name FROM asset_registry ORDER BY asset_id")
    live = {r['asset_id']: r for r in c.fetchall()}
    c.execute("""SELECT asset_id FROM asset_registry
                 WHERE layer_index IS NULL OR layer_index !~ '^L[0-5]$'
                    OR layer_index <> (CASE layer WHEN 'brahmagyan' THEN 'L0' WHEN 'ganita' THEN 'L1'
                          WHEN 'bodha' THEN 'L2' WHEN 'kala' THEN 'L3'
                          WHEN 'phala' THEN 'L4' WHEN 'mimamsa' THEN 'L5' END) ORDER BY 1""")
    c02 = [r['asset_id'] for r in c.fetchall()]
    c.execute("""SELECT asset_id FROM asset_registry WHERE layer_name IS DISTINCT FROM
                   (CASE layer WHEN 'brahmagyan' THEN 'Brahmagyan' WHEN 'ganita' THEN 'Gaṇita'
                        WHEN 'bodha' THEN 'Bodha' WHEN 'kala' THEN 'Kāla'
                        WHEN 'phala' THEN 'Phala' WHEN 'mimamsa' THEN 'Mīmāṃsā' END) ORDER BY 1""")
    c03 = [r['asset_id'] for r in c.fetchall()]
    c.execute("""SELECT DISTINCT layer_name, length(layer_name) AS chars,
                        octet_length(layer_name) AS bytes
                 FROM asset_registry WHERE layer IN ('ganita','kala','mimamsa')
                   AND layer_name IS NOT NULL ORDER BY 1""")
    obs = sorted((r['layer_name'], r['chars'], r['bytes']) for r in c.fetchall())

fails, moved = [], {}
if set(live) != set(snap):
    fails.append(f'row set changed: +{set(live)-set(snap)} -{set(snap)-set(live)}')
for aid in sorted(set(live) & set(snap)):
    for col in ('layer_index', 'layer_name'):
        if live[aid][col] != snap[aid][col]:
            moved[(aid, col)] = (snap[aid][col], live[aid][col])
    if live[aid]['layer'] != snap[aid]['layer']:                                    # P5
        fails.append(f'P5 layer moved on {aid}: {snap[aid]["layer"]} -> {live[aid]["layer"]}')

extra = set(moved) - set(want)
missing = set(want) - set(moved)
if extra:
    fails.append(f'P1/P2 cells moved that should not have: {sorted(extra)}')
if missing:
    fails.append(f'P1 cells that should have moved did not: {sorted(missing)}')
for k, (to, seed) in want.items():                                                  # P3
    if k in moved and moved[k][1] != to:
        fails.append(f'P3 {k} landed {moved[k][1]!r}, expected {to!r}')
    if k in moved and moved[k][1] != seed:
        fails.append(f'P3 {k} landed {moved[k][1]!r}, seed holds {seed!r} (durability)')

lel = live['lel_events']
if lel['layer_index'] is not None or lel['layer_name'] is not None:                  # P4
    fails.append(f'P4 lel_events no longer NULL: {dict(lel)}')

if c02 != ['lel_events']:
    fails.append(f'P6 C-02 violations = {c02}, expected exactly [lel_events]')
if c03 != ['lel_events']:
    fails.append(f'P6 C-03 violations = {c03}, expected exactly [lel_events]')

pin = sorted([('Gaṇita', 6, 8), ('Kāla', 4, 5), ('Mīmāṃsā', 7, 12)])
if obs != pin:
    fails.append(f'P7 codepoint pin: observed {obs}, expected {pin}')

n_li = sum(1 for k in moved if k[1] == 'layer_index')
n_ln = sum(1 for k in moved if k[1] == 'layer_name')
print(f'P1 cells moved            : layer_index {n_li} / layer_name {n_ln}'
      f'  (re-derived target {len(der["layer_index_repair"])} / {len(der["layer_name_repair"])})')
print(f'P2 unintended cells moved : {len(extra)}')
print(f'P3 landed on derived value AND on the seed value: {len(want) - sum(1 for f in fails if f.startswith("P3"))}/{len(want)}')
print(f'P4 lel_events             : layer_index={lel["layer_index"]!r} layer_name={lel["layer_name"]!r}')
print(f'P5 `layer` column moved   : {sum(1 for f in fails if f.startswith("P5"))} rows')
print(f'P6 C-02 / C-03 violations : {c02} / {c03}')
print(f'P7 codepoint observed     : {obs}  -> {"PASS" if obs == pin else "FAIL"}')

json.dump({'moved': {f'{a}.{c}': v for (a, c), v in moved.items()},
           'C02_violations': c02, 'C03_violations': c03, 'codepoint_observed': obs,
           'lel_events': dict(lel), 'failures': fails},
          open(HERE / 'postcheck.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

if fails:
    print('\nPOST-CHECK FAILURES:')
    for f in fails[:20]:
        print('  ' + f)
    sys.exit(1)
print('\nALL POST-CHECK ASSERTIONS HOLD (observation, not certification -- I16)')
