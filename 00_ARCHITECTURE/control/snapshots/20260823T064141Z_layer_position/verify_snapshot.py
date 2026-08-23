#!/usr/bin/env python3
"""M0-T26 — verify the snapshot READS BACK before anything is written.

Four independent assertions:
  V1  snapshot.tsv and snapshot.json agree, row for row, cell for cell.
  V2  restore.sql's VALUES tuples re-parse to exactly the snapshot's (asset_id, layer_index,
      layer_name) — byte-identical, diacritics included.
  V3  the snapshot equals the LIVE table right now (nothing moved between capture and use).
  V4  restore.sql contains no DROP / TRUNCATE / DELETE / ALTER token.
Exit 0 only if all four hold.
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

def unlit(tok):
    tok = tok.strip()
    if tok == 'NULL':
        return None
    assert tok.startswith("'") and tok.endswith("'"), tok
    return tok[1:-1].replace("''", "'")

fail = []
snap = json.loads((HERE / 'snapshot.json').read_text(encoding='utf-8'))
rows = snap['rows']

# V1 -- tsv vs json
tsv = (HERE / 'snapshot.tsv').read_text(encoding='utf-8').splitlines()
hdr, body = tsv[0].split('\t'), tsv[1:]
if len(body) != len(rows):
    fail.append(f'V1 row count tsv={len(body)} json={len(rows)}')
else:
    for line, r in zip(body, rows):
        cells = line.split('\t')
        got = {h: (None if v == '<NULL>' else v) for h, v in zip(hdr, cells)}
        if got != r:
            fail.append(f'V1 mismatch {r["asset_id"]}: tsv={got} json={r}')
print(f'V1 tsv==json over {len(rows)} rows: {"PASS" if not fail else "FAIL"}')

# V2 -- re-parse restore.sql
sqltext = (HERE / 'restore.sql').read_text(encoding='utf-8')
block = sqltext.split('AS (VALUES', 1)[1].split('\n  ), upd AS', 1)[0]
tuples = re.findall(r"\((?:'(?:[^']|'')*'|NULL)\s*,\s*(?:'(?:[^']|'')*'|NULL)\s*,\s*(?:'(?:[^']|'')*'|NULL)\)", block)
parsed = []
for t in tuples:
    toks = re.findall(r"'(?:[^']|'')*'|NULL", t)
    parsed.append({'asset_id': unlit(toks[0]), 'layer_index': unlit(toks[1]), 'layer_name': unlit(toks[2])})
v2fail = []
if len(parsed) != len(rows):
    v2fail.append(f'tuple count {len(parsed)} != {len(rows)}')
else:
    for p, r in zip(parsed, rows):
        if (p['asset_id'], p['layer_index'], p['layer_name']) != (r['asset_id'], r['layer_index'], r['layer_name']):
            v2fail.append(f'{r["asset_id"]}: sql={p} snap={r}')
print(f'V2 restore.sql re-parses to snapshot ({len(parsed)} tuples): {"PASS" if not v2fail else "FAIL"}')
fail += ['V2 ' + m for m in v2fail]

# V3 -- snapshot == live
with psycopg.connect(db_url(), row_factory=dict_row, autocommit=True) as conn:
    c = conn.cursor()
    c.execute("SELECT asset_id, layer, layer_index, layer_name FROM asset_registry ORDER BY asset_id")
    live = c.fetchall()
v3fail = []
if len(live) != len(rows):
    v3fail.append(f'live row count {len(live)} != snapshot {len(rows)}')
else:
    for lv, r in zip(live, rows):
        if {k: lv[k] for k in ('asset_id', 'layer', 'layer_index', 'layer_name')} != r:
            v3fail.append(f'{lv["asset_id"]}: live={dict(lv)} snap={r}')
print(f'V3 snapshot == live table ({len(live)} rows): {"PASS" if not v3fail else "FAIL"}')
fail += ['V3 ' + m for m in v3fail]

# V4 -- no destructive token
bad = [t for t in ('DROP', 'TRUNCATE', 'DELETE', 'ALTER') if re.search(r'\b' + t + r'\b', sqltext, re.I)]
print(f'V4 restore.sql destructive tokens: {bad if bad else "none"} -> {"PASS" if not bad else "FAIL"}')
fail += [f'V4 destructive token {b}' for b in bad]

if fail:
    print('\nSNAPSHOT VERIFICATION FAILED:')
    for f in fail[:20]:
        print('  ' + f)
    sys.exit(1)
print('\nALL FOUR SNAPSHOT ASSERTIONS PASS')
