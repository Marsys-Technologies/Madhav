#!/usr/bin/env python3
"""M0-T26 PRE-FLIGHT discriminating detector (D-4 condition 3 style).

Run BEFORE the write. Its job is not to say "the plan looks right" -- it is to establish, on the
live PRE-repair state, that each named check can currently FAIL, so that the same check reading
clean afterwards means something (CLAUDE.md N.8: a signal with no code path that could read
false is not a signal).

Six named assets whose correct post-state is known independently of the UPDATE's own CASE:
  ka_gochara_v3_century_materialize  L3 / Kala  -> layer_index ALREADY L3; only the diacritic moves.
                                     Catches a NULL-only backfill that skips normalisation.
  bg_sign_medical                    layer_index is the bare digit '0'.
                                     Catches WHERE ... IS NULL instead of IS DISTINCT FROM.
  bo_arudha                          both NULL. Catches "the backfill did not run".
  ga_vichara                         both NULL and the name carries a diacritic.
                                     Catches encoding loss in transport, distinct from the above.
  bg_reference                       already correct on both. NEGATIVE CONTROL -- must not move.
  ph_pramana                         Phala has zero violations in either class. NEGATIVE CONTROL.

Plus: the asset_id-prefix cross-check (a different column, different mechanism), and the
codepoint pin whose expected values are constants in THIS file, not in the UPDATE.
"""
import json, pathlib, re, sys
import psycopg
from psycopg.rows import dict_row

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PIN = {'Gaṇita': (6, 8), 'Kāla': (4, 5), 'Mīmāṃsā': (7, 12)}
SPOT = {
    'ka_gochara_v3_century_materialize': ('L3', 'Kāla'),
    'bg_sign_medical':                   ('L0', 'Brahmagyan'),
    'bo_arudha':                         ('L2', 'Bodha'),
    'ga_vichara':                        ('L1', 'Gaṇita'),
    'bg_reference':                      ('L0', 'Brahmagyan'),   # negative control
    'ph_pramana':                        ('L4', 'Phala'),        # negative control
}
NEG = {'bg_reference', 'ph_pramana'}

def db_url():
    for l in (ROOT / 'platform/.env.local').read_text().splitlines():
        if l.startswith('DATABASE_URL='):
            return re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
    raise SystemExit('DATABASE_URL not found')

phase = sys.argv[1] if len(sys.argv) > 1 else 'pre'
assert phase in ('pre', 'post')

out = {'phase': phase}
with psycopg.connect(db_url(), row_factory=dict_row, autocommit=True) as conn:
    c = conn.cursor()
    c.execute("SET statement_timeout = '45s'")

    c.execute("SELECT asset_id, layer, layer_index, layer_name FROM asset_registry "
              "WHERE asset_id = ANY(%s) ORDER BY asset_id", (list(SPOT),))
    spot = c.fetchall()
    out['spot_checks'] = [{'asset_id': r['asset_id'], 'layer_index': r['layer_index'],
                           'layer_name': r['layer_name'],
                           'expected_after': list(SPOT[r['asset_id']]),
                           'matches_expected_after':
                               (r['layer_index'], r['layer_name']) == SPOT[r['asset_id']],
                           'role': 'negative_control' if r['asset_id'] in NEG else 'discriminator'}
                          for r in spot]

    # D-1 prefix cross-check (independent column)
    c.execute("""SELECT asset_id, left(asset_id,3) AS prefix, layer, layer_index
                 FROM asset_registry
                 WHERE left(asset_id,3) IN ('bg_','ga_','bo_','ka_','ph_','mi_')
                   AND layer_index IS DISTINCT FROM (CASE left(asset_id,3)
                        WHEN 'bg_' THEN 'L0' WHEN 'ga_' THEN 'L1' WHEN 'bo_' THEN 'L2'
                        WHEN 'ka_' THEN 'L3' WHEN 'ph_' THEN 'L4' WHEN 'mi_' THEN 'L5' END)
                 ORDER BY asset_id""")
    out['prefix_crosscheck_violations'] = [dict(r) for r in c.fetchall()]

    # C-02 / C-03 contract rules, verbatim shape from ASSET_CATALOGUE_CONTRACT section 8
    c.execute("""SELECT asset_id FROM asset_registry
                 WHERE layer_index IS NULL OR layer_index !~ '^L[0-5]$'
                    OR layer_index <> (CASE layer WHEN 'brahmagyan' THEN 'L0' WHEN 'ganita' THEN 'L1'
                          WHEN 'bodha' THEN 'L2' WHEN 'kala' THEN 'L3'
                          WHEN 'phala' THEN 'L4' WHEN 'mimamsa' THEN 'L5' END)
                 ORDER BY asset_id""")
    out['C02_violations'] = [r['asset_id'] for r in c.fetchall()]
    c.execute("""SELECT asset_id FROM asset_registry
                 WHERE layer_name IS DISTINCT FROM
                   (CASE layer WHEN 'brahmagyan' THEN 'Brahmagyan' WHEN 'ganita' THEN 'Gaṇita'
                        WHEN 'bodha' THEN 'Bodha' WHEN 'kala' THEN 'Kāla'
                        WHEN 'phala' THEN 'Phala' WHEN 'mimamsa' THEN 'Mīmāṃsā' END)
                 ORDER BY asset_id""")
    out['C03_violations'] = [r['asset_id'] for r in c.fetchall()]

    # D-4 codepoint pin, measured by the SERVER (length/octet_length), compared to constants here
    c.execute("""SELECT DISTINCT layer_name, length(layer_name) AS chars,
                        octet_length(layer_name) AS bytes
                 FROM asset_registry WHERE layer IN ('ganita','kala','mimamsa')
                   AND layer_name IS NOT NULL ORDER BY 1""")
    obs = [dict(r) for r in c.fetchall()]
    out['codepoint_observed'] = obs
    out['codepoint_pin_expected'] = {k: {'chars': v[0], 'bytes': v[1]} for k, v in PIN.items()}
    out['codepoint_ascii_folded_rows'] = [o for o in obs if o['chars'] == o['bytes']]
    out['codepoint_pin_holds'] = (
        sorted((o['layer_name'], o['chars'], o['bytes']) for o in obs)
        == sorted((k, v[0], v[1]) for k, v in PIN.items()))

    c.execute("SELECT asset_id, layer_index, layer_name FROM asset_registry WHERE asset_id='lel_events'")
    out['lel_events'] = dict(c.fetchone())

(HERE / f'detector_{phase}.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')

print(f'--- detector [{phase}] ---')
for s in out['spot_checks']:
    flag = 'MATCHES-TARGET' if s['matches_expected_after'] else 'DIFFERS-FROM-TARGET'
    print(f"  {s['asset_id']:36s} {str(s['layer_index']):>6s} / {str(s['layer_name']):<11s} "
          f"target {s['expected_after'][0]}/{s['expected_after'][1]:<11s} {flag}  [{s['role']}]")
print(f"  prefix cross-check violations : {len(out['prefix_crosscheck_violations'])} "
      f"{[r['asset_id'] for r in out['prefix_crosscheck_violations']]}")
print(f"  C-02 violations               : {len(out['C02_violations'])}")
print(f"  C-03 violations               : {len(out['C03_violations'])}")
print(f"  codepoint observed            : {[(o['layer_name'], o['chars'], o['bytes']) for o in obs]}")
print(f"  ASCII-folded rows present     : {[o['layer_name'] for o in out['codepoint_ascii_folded_rows']]}")
print(f"  codepoint pin holds exactly   : {out['codepoint_pin_holds']}")
print(f"  lel_events                    : {out['lel_events']}")
