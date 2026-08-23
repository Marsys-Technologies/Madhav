#!/usr/bin/env python3
"""M0-T21 POST-CHECK. Diffs live state against the pre-write snapshot, row by row.
Verifies against the SNAPSHOT, not against the UPDATE statement's shape. READ ONLY."""
import json, pathlib, re, sys, psycopg
HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')
url = next(re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
           for l in (REPO/'platform/.env.local').read_text().splitlines() if l.startswith('DATABASE_URL='))
before = {r['asset_id']: r for r in json.loads((HERE/'snapshot.json').read_text())['rows']}
EXPECT = {'bg_ephemeris_engine':'asset_kind','bg_panchanga':'asset_kind',
          'ka_graha_sancara':'asset_type','ka_muhurta_seva':'asset_type',
          'mi_abhilekha':'asset_type','mi_seva':'asset_type'}
fail = []
with psycopg.connect(url, row_factory=psycopg.rows.dict_row, autocommit=True) as conn:
    cur = conn.cursor(); cur.execute("SET default_transaction_read_only = on")
    cur.execute("SELECT asset_id,asset_kind,asset_type,storage_type FROM asset_registry ORDER BY asset_id")
    after = {r['asset_id']: r for r in cur.fetchall()}

    print(f"[A] row count  before={len(before)}  after={len(after)}")
    if set(before) != set(after): fail.append("asset_id set changed")

    print("\n[B] EVERY row diffed against the snapshot:")
    moved = {}
    for a in sorted(before):
        d = [c for c in ('asset_kind','asset_type','storage_type') if before[a][c] != after[a][c]]
        if d: moved[a] = d
    print(f"    rows that moved: {len(moved)}")
    for a, d in sorted(moved.items()):
        for c in d:
            print(f"      {a:<22} {c:<13} {before[a][c]!r} -> {after[a][c]!r}")
    if set(moved) != set(EXPECT): fail.append(f"moved set {sorted(moved)} != intended {sorted(EXPECT)}")
    print(f"    moved set == the six intended: {set(moved)==set(EXPECT)}")

    print("\n[C] each moved row changed exactly ONE column, and it is the intended one:")
    for a, d in sorted(moved.items()):
        ok = (len(d) == 1 and d[0] == EXPECT[a] and before[a][d[0]]=='data' and after[a][d[0]]=='service')
        print(f"      {a:<22} cols={d} intended={EXPECT[a]:<11} {'OK' if ok else 'FAIL'}")
        if not ok: fail.append(f"{a} unexpected change {d}")

    print("\n[D] NO ROW LOST A CORRECT VALUE — no 'service' was overwritten by 'data' anywhere:")
    regressions = [(a,c) for a in before for c in ('asset_kind','asset_type','storage_type')
                   if before[a][c]=='service' and after[a][c]!='service']
    print(f"      service->non-service regressions: {len(regressions)} {regressions}")
    if regressions: fail.append(f"REGRESSION {regressions}")
    artifact_lost = [a for a in before if before[a]['asset_kind']=='artifact' and after[a]['asset_kind']!='artifact']
    print(f"      artifact classifications lost: {len(artifact_lost)} {artifact_lost}")
    if artifact_lost: fail.append("artifact lost")

    print("\n[E] THE TRAP NEGATIVE CONTROL — the two rows a literal 'asset_kind is authoritative'")
    print("    repair rule would have corrupted to data/data:")
    for a in ('bg_ephemeris_engine','bg_panchanga'):
        r = after[a]; ok = r['asset_kind']=='service' and r['asset_type']=='service'
        print(f"      {a:<22} kind={r['asset_kind']:<8} type={r['asset_type']:<8} "
              f"(snapshot was kind={before[a]['asset_kind']}/type={before[a]['asset_type']}) {'OK' if ok else 'TRAP SPRUNG'}")
        if not ok: fail.append(f"TRAP: {a}")
    print("    mirror case (asset_kind was already right):")
    for a in ('ka_graha_sancara',):
        r = after[a]; ok = r['asset_kind']=='service' and r['asset_type']=='service'
        print(f"      {a:<22} kind={r['asset_kind']:<8} type={r['asset_type']:<8} {'OK' if ok else 'FAIL'}")
        if not ok: fail.append(f"mirror {a}")

    print("\n[F] untouched controls:")
    for a in ('bo_cdlm_summary','ka_sangam','ph_pramana','lel_events','ka_dasha_kala','ka_tulana'):
        same = before[a]==dict(after[a])
        print(f"      {a:<22} kind={after[a]['asset_kind']:<9} type={after[a]['asset_type']:<8} unchanged={same}")
        if not same: fail.append(f"control {a} moved")

    print("\n[G] contract C-14 (verbatim from ASSET_CATALOGUE_CONTRACT §8):")
    cur.execute("""SELECT asset_id, asset_kind, asset_type FROM asset_registry
                   WHERE (asset_kind, asset_type) NOT IN
                   (('data','data'),('artifact','data'),('service','service'),('source','data'))""")
    v = cur.fetchall(); print(f"      violations: {len(v)} {v}")
    if v: fail.append("C-14 nonzero")

    print("\n[H] three-column closure — EXPECT exactly 8 rows, all three columns 'service':")
    cur.execute("""SELECT asset_id, asset_kind, asset_type, storage_type FROM asset_registry
                   WHERE 'service' IN (asset_kind, asset_type, storage_type) ORDER BY asset_id""")
    cl = cur.fetchall()
    for r in cl:
        print(f"      {r['asset_id']:<22} {r['asset_kind']:<8} {r['asset_type']:<8} {r['storage_type']}")
    allsvc = all(r['asset_kind']=='service' and r['asset_type']=='service' and r['storage_type']=='service' for r in cl)
    print(f"      count={len(cl)} (expect 8), all three columns 'service' on every row: {allsvc}")
    if len(cl)!=8 or not allsvc: fail.append("closure")

    print("\n[I] totals:")
    for col, exp in (('asset_kind',{'data':104,'artifact':16,'service':8}), ('asset_type',{'data':120,'service':8})):
        cur.execute(f"SELECT {col} k, count(*) n FROM asset_registry GROUP BY 1 ORDER BY 1")
        got = {r['k']: r['n'] for r in cur.fetchall()}
        print(f"      {col}: {got}   expected {exp}   {'OK' if got==exp else 'MISMATCH'}")
        if got != exp: fail.append(f"{col} totals {got}")
    cur.execute("SELECT storage_type k, count(*) n FROM asset_registry GROUP BY 1 ORDER BY 1")
    print(f"      storage_type: {{{', '.join(repr(r['k'])+': '+str(r['n']) for r in cur.fetchall())}}} (must be unchanged)")

    print("\n[J] CHECK constraints unchanged (no DDL was performed):")
    cur.execute("""SELECT conname, pg_get_constraintdef(oid) d FROM pg_constraint
                   WHERE conrelid='asset_registry'::regclass AND conname IN
                   ('asset_registry_asset_kind_check','asset_registry_catalog_status_check') ORDER BY 1""")
    for r in cur.fetchall(): print(f"      {r['conname']}: {r['d']}")

print()
if fail:
    print("POST-CHECK FAILURES:"); [print("  -", f) for f in fail]; sys.exit(1)
print("POST-CHECK: all assertions above returned their expected values.")
print("This is an observation, not a certification (I16/H7). PARIKSAKA verifies.")
