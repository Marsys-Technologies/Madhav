#!/usr/bin/env python3
"""Verify the M0-T21 snapshot reads back: checksums, TSV<->JSON agreement,
restore.sql VALUES parse-back, and full agreement with the live DB. READ ONLY."""
import hashlib, json, pathlib, re, sys, psycopg
HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')
fail = []

# 1 checksums
for line in (HERE/'SHA256SUMS').read_text().splitlines():
    h, name = line.split('  ');  p = HERE/name
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != h: fail.append(f"checksum mismatch {name}")
print(f"[1] checksums: {len(open(HERE/'SHA256SUMS').read().splitlines())} files verified")

# 2 tsv <-> json
tsv = [l.split('\t') for l in (HERE/'snapshot.tsv').read_text().splitlines()]
hdr, tsv_rows = tsv[0], tsv[1:]
js = json.loads((HERE/'snapshot.json').read_text())
if hdr != js['columns']: fail.append("header mismatch")
tsv_set = {tuple(r) for r in tsv_rows}
js_set = {tuple(r[c] for c in js['columns']) for r in js['rows']}
if tsv_set != js_set: fail.append(f"tsv/json differ: {tsv_set ^ js_set}")
print(f"[2] tsv({len(tsv_rows)}) == json({len(js['rows'])}): {tsv_set == js_set}")

# 3 restore.sql VALUES parse back to the same 128 tuples
sql = (HERE/'restore.sql').read_text()
parsed = set(re.findall(r"\('([^']*)','([^']*)','([^']*)','([^']*)'\)", sql))
if parsed != tsv_set: fail.append(f"restore.sql VALUES != snapshot ({len(parsed)} vs {len(tsv_set)})")
print(f"[3] restore.sql VALUES parse-back: {len(parsed)} tuples, identical to snapshot: {parsed == tsv_set}")
for tok in ('DROP ','TRUNCATE','DELETE FROM','ALTER TABLE'):
    if tok in sql.upper(): fail.append(f"restore.sql contains {tok}")
print(f"[3b] restore.sql contains no DROP/TRUNCATE/DELETE/ALTER: {'ok' if not fail else 'SEE FAILURES'}")

# 4 live DB agreement
url = next(re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
           for l in (REPO/'platform/.env.local').read_text().splitlines() if l.startswith('DATABASE_URL='))
with psycopg.connect(url, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
    cur = conn.cursor(); cur.execute("SET default_transaction_read_only = on")
    cur.execute("SELECT asset_id,asset_kind,asset_type,storage_type FROM asset_registry ORDER BY asset_id")
    live = {(r['asset_id'],r['asset_kind'],r['asset_type'],r['storage_type']) for r in cur.fetchall()}
if live != tsv_set:
    fail.append(f"snapshot != live DB; sym-diff={live ^ tsv_set}")
print(f"[4] live DB has {len(live)} rows; snapshot matches live exactly: {live == tsv_set}")

print()
if fail:
    print("SNAPSHOT VERIFICATION FAILED:"); [print("  -", f) for f in fail]; sys.exit(1)
print("SNAPSHOT VERIFICATION PASSED — snapshot is readable, self-consistent, and equals live state.")
print("HONEST SCOPE: restore.sql is AUTHORED AND PARSE-VERIFIED, NOT PROVEN-BY-EXECUTION.")
print("  Executing it is itself a write and is outside M0-T21's granted scope.")
