#!/usr/bin/env python3
"""M0-T21 Phase 0.6b apply. VALUES FIRST (D-24 part 2).
(a) asset_kind := 'service' on the 2 rows whose asset_kind is wrong.
(b) asset_type := 'service' on the 4 rows whose asset_type is wrong.
storage_type: NO CHANGE (all 6 already 'service').
Rolls back and exits non-zero on ANY rowcount other than the measured 2 / 4,
or if any negative control moved, or if the total changed-row set != the six.
"""
import pathlib, re, sys, psycopg
REPO = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')
HERE = pathlib.Path(__file__).resolve().parent
url = next(re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', l).group(1).strip().strip('"\'')
           for l in (REPO/'platform/.env.local').read_text().splitlines() if l.startswith('DATABASE_URL='))
KIND_FIX = ('bg_ephemeris_engine','bg_panchanga')                                   # 2
TYPE_FIX = ('ka_graha_sancara','ka_muhurta_seva','mi_abhilekha','mi_seva')           # 4
SNAP = {tuple(l.split('\t')) for l in (HERE/'snapshot.tsv').read_text().splitlines()[1:]}

conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row, autocommit=False)
try:
    cur = conn.cursor()
    cur.execute("SELECT count(*) n FROM asset_registry")
    n_before = cur.fetchone()['n']
    assert n_before == 128, f"table has {n_before} rows, snapshot has 128 — ABORT"

    cur.execute("""UPDATE asset_registry SET asset_kind='service'
                   WHERE asset_id = ANY(%s) AND asset_kind IS DISTINCT FROM 'service'""", (list(KIND_FIX),))
    n_kind = cur.rowcount
    print(f"(a) asset_kind := 'service' -> UPDATE {n_kind}  (expected 2)")
    if n_kind != 2: raise SystemExit(f"ABORT: asset_kind rowcount {n_kind} != 2")

    cur.execute("""UPDATE asset_registry SET asset_type='service'
                   WHERE asset_id = ANY(%s) AND asset_type IS DISTINCT FROM 'service'""", (list(TYPE_FIX),))
    n_type = cur.rowcount
    print(f"(b) asset_type := 'service' -> UPDATE {n_type}  (expected 4)")
    if n_type != 4: raise SystemExit(f"ABORT: asset_type rowcount {n_type} != 4")

    # ---- in-transaction verification AGAINST THE SNAPSHOT (not against the statement's shape)
    cur.execute("SELECT count(*) n FROM asset_registry")
    if cur.fetchone()['n'] != 128: raise SystemExit("ABORT: row count changed")

    cur.execute("SELECT asset_id,asset_kind,asset_type,storage_type FROM asset_registry ORDER BY asset_id")
    now = {(r['asset_id'],r['asset_kind'],r['asset_type'],r['storage_type']) for r in cur.fetchall()}
    changed_ids = {t[0] for t in (now - SNAP)}
    expected = set(KIND_FIX) | set(TYPE_FIX)
    print(f"    rows differing from snapshot: {len(changed_ids)} -> {sorted(changed_ids)}")
    if changed_ids != expected:
        raise SystemExit(f"ABORT: changed set {sorted(changed_ids)} != intended {sorted(expected)}")
    # no row LOST a correct value: every changed row must differ ONLY by data->service on one column
    snap_by = {t[0]: t for t in SNAP}; now_by = {t[0]: t for t in now}
    for a in changed_ids:
        b, n = snap_by[a], now_by[a]
        diffs = [i for i in range(1,4) if b[i] != n[i]]
        if len(diffs) != 1: raise SystemExit(f"ABORT: {a} changed {len(diffs)} columns")
        i = diffs[0]
        if b[i] != 'data' or n[i] != 'service':
            raise SystemExit(f"ABORT: {a} col{i} {b[i]}->{n[i]} is not data->service")
        print(f"    {a}: {['','asset_kind','asset_type','storage_type'][i]} {b[i]} -> {n[i]}  (one column only)")
    # storage_type untouched on ALL rows
    if any(snap_by[t[0]][3] != t[3] for t in now): raise SystemExit("ABORT: storage_type changed somewhere")
    print("    storage_type unchanged on all 128 rows: OK")
    # C-14 must now be empty
    cur.execute("""SELECT asset_id FROM asset_registry WHERE (asset_kind,asset_type) NOT IN
                   (('data','data'),('artifact','data'),('service','service'),('source','data'))""")
    v = cur.fetchall()
    print(f"    C-14 violations after: {len(v)} (expected 0)")
    if v: raise SystemExit(f"ABORT: C-14 still {v}")
    # all six resolve to service by BOTH columns
    cur.execute("""SELECT asset_id FROM asset_registry WHERE asset_id = ANY(%s)
                   AND NOT (asset_kind='service' AND asset_type='service')""", (list(expected),))
    bad = cur.fetchall()
    if bad: raise SystemExit(f"ABORT: not resolved to service by both columns: {bad}")
    print("    all 6 read asset_kind='service' AND asset_type='service': OK")
    # negative controls unmoved
    for a in ('bo_cdlm_summary','ka_sangam','ph_pramana','lel_events'):
        if now_by[a] != snap_by[a]: raise SystemExit(f"ABORT: negative control {a} moved")
    print("    negative controls (bo_cdlm_summary, ka_sangam, ph_pramana, lel_events) unmoved: OK")
    # artifact cohort intact
    cur.execute("SELECT count(*) n FROM asset_registry WHERE asset_kind='artifact'")
    if cur.fetchone()['n'] != 16: raise SystemExit("ABORT: artifact cohort != 16")
    print("    artifact cohort still 16: OK")

    conn.commit()
    print("\nCOMMITTED.")
except BaseException as e:
    conn.rollback()
    print(f"\nROLLED BACK: {e}", file=sys.stderr)
    conn.close(); sys.exit(1)
conn.close()
