#!/usr/bin/env python3
"""M0-T26 APPLY -- asset_registry.layer_index / layer_name, mechanical backfill.

Authority: DECISIONS.jsonl D-4 (mechanical, derivable-only, non-derivable left NULL,
pre-flight discriminating detector) and D-23 (lel_events HELD -- the SOURCE question is R5's).

Scope: two columns, on the asset_ids re-derived by derive_independent.py. No other column,
no other table, no DDL, no migration, no build.

Rowcount assertion: exactly 20 layer_index rows and 19 layer_name rows. Any other number
ROLLS BACK and exits non-zero. The asset_id list is passed EXPLICITLY (= ANY(%s)) rather than
left to a WHERE predicate, so the statement cannot widen if the derivation is wrong; the
IS DISTINCT FROM guard is kept as well, which makes a re-run report 0/0.

The values written are the layer->lexicon map of CLAUDE.md N.1, bound as PARAMETERS (never
interpolated into SQL text), so the diacritics travel as Python str -> psycopg UTF-8 and
cannot be normalised by SQL-text transport.
"""
import json, pathlib, re, sys
import psycopg
from psycopg.rows import dict_row

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXPECT_LI, EXPECT_LN = 20, 19

NAME_BY_LAYER = {'brahmagyan': 'Brahmagyan', 'ganita': 'Gaṇita', 'bodha': 'Bodha',
                 'kala': 'Kāla', 'phala': 'Phala', 'mimamsa': 'Mīmāṃsā'}
INDEX_BY_LAYER = {'brahmagyan': 'L0', 'ganita': 'L1', 'bodha': 'L2',
                  'kala': 'L3', 'phala': 'L4', 'mimamsa': 'L5'}

def db_url():
    for l in (ROOT / 'platform/.env.local').read_text().splitlines():
        if l.startswith('DATABASE_URL='):
            return re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
    raise SystemExit('DATABASE_URL not found')

der = json.loads((HERE / 'independent_derivation.json').read_text(encoding='utf-8'))
li_ids = [x['asset_id'] for x in der['layer_index_repair']]
ln_ids = [x['asset_id'] for x in der['layer_name_repair']]
assert 'lel_events' not in li_ids and 'lel_events' not in ln_ids, 'lel_events must be HELD (D-23)'
assert der['cross_source_disagreements'] == [], 'cross-source disagreement -- do not write'
assert der['seed_map_matches_pin'], 'seed map differs from pinned lexicon -- do not write'

pairs_idx = [(k, v) for k, v in INDEX_BY_LAYER.items()]
pairs_nam = [(k, v) for k, v in NAME_BY_LAYER.items()]

with psycopg.connect(db_url(), row_factory=dict_row, autocommit=False) as conn:
    c = conn.cursor()
    c.execute("SET statement_timeout = '45s'")

    c.execute("""
        UPDATE asset_registry a SET layer_index = m.idx
          FROM (VALUES %s) AS m(lyr, idx)
         WHERE a.layer = m.lyr
           AND a.asset_id = ANY(%%s)
           AND a.layer_index IS DISTINCT FROM m.idx
    """ % ','.join(['(%s,%s)'] * len(pairs_idx)),
        [v for p in pairs_idx for v in p] + [li_ids])
    n_li = c.rowcount

    c.execute("""
        UPDATE asset_registry a SET layer_name = m.lyr_name
          FROM (VALUES %s) AS m(lyr, lyr_name)
         WHERE a.layer = m.lyr
           AND a.asset_id = ANY(%%s)
           AND a.layer_name IS DISTINCT FROM m.lyr_name
    """ % ','.join(['(%s,%s)'] * len(pairs_nam)),
        [v for p in pairs_nam for v in p] + [ln_ids])
    n_ln = c.rowcount

    print(f'layer_index rows updated : {n_li}  (expected {EXPECT_LI})')
    print(f'layer_name  rows updated : {n_ln}  (expected {EXPECT_LN})')

    if (n_li, n_ln) != (EXPECT_LI, EXPECT_LN):
        conn.rollback()
        print('ROWCOUNT ASSERTION FAILED -- ROLLED BACK, nothing written.')
        sys.exit(2)

    # in-transaction sanity: lel_events untouched, and the codepoint pin holds on the new state
    c.execute("SELECT layer_index, layer_name FROM asset_registry WHERE asset_id='lel_events'")
    lel = c.fetchone()
    if lel['layer_index'] is not None or lel['layer_name'] is not None:
        conn.rollback()
        print(f'lel_events NO LONGER NULL ({lel}) -- ROLLED BACK.')
        sys.exit(3)

    c.execute("""SELECT DISTINCT layer_name, length(layer_name) AS chars,
                        octet_length(layer_name) AS bytes
                 FROM asset_registry WHERE layer IN ('ganita','kala','mimamsa')
                   AND layer_name IS NOT NULL ORDER BY 1""")
    obs = sorted((r['layer_name'], r['chars'], r['bytes']) for r in c.fetchall())
    pin = sorted([('Gaṇita', 6, 8), ('Kāla', 4, 5), ('Mīmāṃsā', 7, 12)])
    if obs != pin:
        conn.rollback()
        print(f'CODEPOINT PIN FAILED in-transaction: {obs} != {pin} -- ROLLED BACK.')
        sys.exit(4)

    conn.commit()
    print('COMMITTED. lel_events still NULL/NULL; codepoint pin holds in-transaction:', obs)
