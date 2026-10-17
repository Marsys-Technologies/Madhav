#!/usr/bin/env python3
"""Generic draft-SQL builder + real-PG test harness for CITATION-TEXT curation of the other L0 assets.

For one asset it
  * turns the ledger's `recite` entries (state sourced_fact/sourced_inference with a proposed_citation)
    into guarded UPDATEs of ONE text citation column per table (natural-key match + exact old value),
  * pins, per table, an md5 fingerprint of every non-timestamp column before and after,
  * if the asset's stored integrity_check_sql hashes the changed tables, reseals it (each sha256 literal
    is replaced by the value computed on the replica after the UPDATEs; the stored check must read true),
  * is idempotent (second apply = NOTICE + no-op) and refuses on any drift of the pinned pre-state.

  generic_citation_sql.py gen  <asset> <ledger.json> <snapdir> <out.sql>        (uses pins in <snapdir>/<asset>.pins.json)
  generic_citation_sql.py test <asset> <ledger.json> <snapdir> <sock> <port> <out_dir>

<snapdir> holds `<table>.cols.json`, `<table>.rows.jsonl`, `registry.json` written by dump_tables.py (reader-only).
Never connects to production; the test uses a disposable local server by unix socket."""
import hashlib, json, pathlib, re, subprocess, sys, tempfile

PSQL = "/opt/homebrew/bin/psql"

# asset -> {table: (key columns, citation column)}; registry asset id = asset
SPECS = {
    "bg_dignity_reference": {
        "bg_dignity_reference": (("graha",), "classical_citation"),
        "bg_graha_naisargika_friendship": (("graha", "other_graha"), "classical_citation"),
        "bg_avastha_schemes": (("scheme_name", "state_name"), "classical_citation"),
        "bg_motion_state_thresholds": (("graha", "motion_state"), "classical_citation"),
        "bg_combustion_orbs": (("graha",), "classical_citation"),
    },
    "bg_reference": {
        "reference_planets": (("planet_id",), "source_citation"),
        "reference_signs": (("sign_id",), "source_citation"),
        "reference_houses": (("house_num",), "source_citation"),
        "reference_aspects": (("planet_id", "aspect_house"), "source_citation"),
        "reference_vargas": (("varga_id",), "source_citation"),
        "reference_upagrahas": (("upagraha_id",), "source_citation"),
        "reference_strength_systems": (("strength_id",), "source_citation"),
        "reference_karakas": (("karaka_id",), "source_citation"),
        "reference_constants": (("constant_id",), "source_citation"),
        "reference_glossary": (("term_id",), "classical_citation"),
    },
    "bg_nakshatra": {
        "reference_nakshatra": (("nakshatra_id",), "classical_source"),
        "reference_nakshatra_pada": (("nakshatra_id",), "classical_source"),
        "reference_nakshatra_matrix": ((), "classical_source"),     # family updates through the ledger's row_key_query
    },
    "bg_dasha_systems": {
        "brahma_dasha_systems": (("canonical_id",), "classical_citations", "jsonb"),
        "brahma_ontology": (("entity_class", "canonical_id"), "source_citation", "text"),
    },
    "bg_doshas": {
        "brahma_dosha_catalog": (("canonical_id",), "classical_citations", "jsonb"),
        "brahma_ontology": (("entity_class", "canonical_id"), "source_citation", "text"),
    },
    "bg_prashna_rules": {
        "bg_prashna_lagna_methods": (("method_id",), "classical_citation"),
        "bg_prashna_tajik_yogas": (("yoga_id",), "classical_citation"),
        "bg_prashna_significators": (("question_class",), "classical_citation"),
        "bg_prashna_fructification_rules": (("rule_id",), "classical_citation"),
        "bg_prashna_special_techniques": (("technique_id",), "classical_citation"),
    },
}
# tables that are replicated whole (all tables the asset's stored check reads), besides SPECS tables
EXTRA_TABLES = {
    "bg_reference": ["reference_topic_tags"],
    "bg_dasha_systems": ["reference_dasha_systems"],
    "bg_doshas": ["reference_doshas"],
}
# replicate / fingerprint only the asset's own rows of a shared table
WHERE = {("bg_dasha_systems", "brahma_ontology"): "entity_class='dasha_system'",
         ("bg_doshas", "brahma_ontology"): "entity_class='dosha'"}
PK_OVERRIDE = {"reference_nakshatra_matrix": ("id",)}


SEED_MODULE = {
    "bg_dignity_reference": "platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py (static data, ON CONFLICT DO UPDATE)",
    "bg_reference": "platform/python-sidecar/brahmagyan/l0_reference.py (ON CONFLICT upserts)",
    "bg_nakshatra": "platform/python-sidecar/brahmagyan/l0_nakshatra.py (delete-then-insert of the three tables)",
    "bg_dasha_systems": "platform/python-sidecar/brahmagyan/l0_dasha_systems.py (delete-then-insert; also writes the 20 ontology rows)",
    "bg_prashna_rules": "platform/python-sidecar/brahmagyan/l0_prashna.py (ON CONFLICT upserts)",
}


def dq(s, tag="c"):
    assert f"${tag}$" not in s
    return f"${tag}${s}${tag}$"


def psql(sock, port, db, sql=None, file=None, check=True):
    cmd = [PSQL, "-X", "-q", "-At", "-h", sock, "-p", str(port), "-U", "cur", "-d", db, "-v", "ON_ERROR_STOP=1"]
    cmd += ["-f", file] if file else ["-c", sql]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode:
        raise RuntimeError(p.stderr[-800:])
    return p


def load_cols(snap, table):
    return json.load(open(pathlib.Path(snap) / f"{table}.cols.json"))


def volatile(cols):
    return [c["name"] for c in cols if re.match(r"timestamp", c["type"])]


def spec3(asset, table):
    sp = SPECS[asset][table]
    return (sp[0], sp[1], sp[2] if len(sp) > 2 else "text")


def fingerprint_sql(snap, table, keys, asset=None):
    cols = load_cols(snap, table)
    ex = volatile(cols)
    minus = f" - ARRAY[{','.join(dq(c, 'v') for c in ex)}]::text[]" if ex else ""
    order = ",".join(f"{k}::text COLLATE \"C\"" for k in keys) if keys else "1"
    wh = f" WHERE {WHERE[(asset, table)]}" if asset and (asset, table) in WHERE else ""
    return (f"SELECT md5(COALESCE(string_agg((to_jsonb(t){minus})::text, E'\\n' ORDER BY {order}), '')) FROM {table} t{wh}")


def all_tables(asset):
    return list(SPECS[asset]) + EXTRA_TABLES.get(asset, [])


def pk_of(asset, table):
    if table in PK_OVERRIDE:
        return PK_OVERRIDE[table]
    if table in SPECS[asset]:
        return SPECS[asset][table][0]
    return ()


def jsonb_citation(e, meta):
    """chunk-anchored citation list in the shape brahma_yoga_catalog already uses:
    {"chapter": <corpus chapter = page>, "text_id", "chunk_id": <uuid>, "verse_ref"}; distinct chunks, ledger order."""
    seen, out = set(), []
    for c in e.get("corpus") or []:
        cid = c.get("chunk_id")
        if not cid or cid in seen: continue
        m = meta.get(cid)
        if not m: return None
        seen.add(cid)
        out.append({"chapter": m["chapter"], "text_id": m["text_id"], "chunk_id": m["id"], "verse_ref": m["verse_ref"]})
    return out or None


def updates_from_ledger(asset, ledger_path, snap):
    L = json.load(open(ledger_path))
    L = L if isinstance(L, list) else [e for v in L.values() for e in v]
    live = {}
    for table in SPECS[asset]:
        live[table] = [json.loads(l) for l in open(pathlib.Path(snap) / f"{table}.rows.jsonl")]
    meta_p = pathlib.Path(snap) / "chunk_meta.json"
    meta = json.load(open(meta_p)) if meta_p.exists() else {}
    ups, skipped = {}, []

    def add(t, item):
        ups.setdefault(t, []).append(item)

    def text_update(t, keyvals, new, rk):
        keys, cite, _ = spec3(asset, t)
        kv = {k: str(keyvals[k]) for k in keys}
        match = [r for r in live[t] if all(str(r[k]) == kv[k] for k in keys)]
        if not match:
            skipped.append((t, rk, "no live row for key")); return
        olds = {r[cite] for r in match}
        if len(olds) != 1:
            skipped.append((t, rk, "rows under the key carry different citations")); return
        old = olds.pop()
        if old is None or old == new:
            skipped.append((t, rk, "old is NULL or unchanged")); return
        add(t, dict(key=kv, old=old, new=new, n=len(match)))

    def jsonb_update(t, keyvals, e, rk):
        keys, cite, _ = spec3(asset, t)
        kv = {k: str(keyvals[k]) for k in keys}
        match = [r for r in live[t] if all(str(r[k]) == kv[k] for k in keys)]
        newv = jsonb_citation(e, meta)
        if len(match) != 1 or newv is None:
            skipped.append((t, rk, "jsonb: no unique live row / chunk uuid unresolved")); return
        old = match[0][cite]
        if old == newv:
            skipped.append((t, rk, "unchanged")); return
        add(t, dict(key=kv, old=json.dumps(old, sort_keys=True, ensure_ascii=False), new=json.dumps(newv, sort_keys=True, ensure_ascii=False), n=1, jsonb=True))

    for e in L:
        if not (e.get("state") in ("sourced_fact", "sourced_inference") and e.get("proposed_action") == "recite" and e.get("proposed_citation")):
            continue
        rk = e["row_key"]
        t = e.get("table")
        if asset == "bg_doshas":          # one ledger entry per dosha: catalog (jsonb) + ontology (text)
            cid = rk.get("canonical_id")
            jsonb_update("brahma_dosha_catalog", {"canonical_id": cid}, e, rk)
            text_update("brahma_ontology", {"entity_class": "dosha", "canonical_id": cid}, e["proposed_citation"].strip(), rk)
            continue
        if t not in SPECS[asset]:
            skipped.append((t, rk, "table not in generic spec")); continue
        keys, cite, kind = spec3(asset, t)
        if not keys:                      # family mode: the ledger's regenerating id query
            q = (e.get("row_key_query") or "").strip().rstrip(";")
            q = re.sub(r"\s+order by id\s*$", "", q, flags=re.I)
            if not q or not e.get("current_citation"):
                skipped.append((t, rk, "family without query / old citation")); continue
            add(t, dict(query=q, old=e["current_citation"].strip(), new=e["proposed_citation"].strip(), n=int(e["row_count"]), key=rk))
            continue
        if not all(k in rk for k in keys):
            why = ("family-level entry: one proposed citation spans several rows whose support differs; not applied row by row"
                   if e.get("row_keys") else "key columns missing in ledger row_key")
            skipped.append((t, rk, why)); continue
        if kind == "jsonb":
            jsonb_update(t, rk, e, rk)
        else:
            text_update(t, rk, e["proposed_citation"].strip(), rk)
    return ups, skipped


def update_sql(asset, ups):
    stmts = []
    for t, items in ups.items():
        keys, cite, kind = spec3(asset, t)
        cast = "::jsonb" if kind == "jsonb" else ""
        if not keys:
            for i in items:
                stmts.append((t, i["n"], f"UPDATE {t} t SET {cite} = {dq(i['new'])}\n    WHERE t.id IN ({i['query']}) AND t.{cite} = {dq(i['old'])}"))
            continue
        vcols = ", ".join(list(keys) + ["old_c", "new_c"])
        vals = ",\n      ".join("(" + ", ".join([dq(i["key"][k]) for k in keys] + [dq(i["old"]), dq(i["new"])]) + ")" for i in items)
        cond = " AND ".join(f"t.{k}::text = v.{k}" for k in keys)
        stmts.append((t, sum(i["n"] for i in items),
                      f"UPDATE {t} t SET {cite} = v.new_c{cast}\n    FROM (VALUES\n      {vals}\n    ) AS v({vcols})\n    WHERE {cond} AND t.{cite}{'::jsonb' if cast else ''} = v.old_c{cast}"))
    return stmts


HEX64 = re.compile(r"'([0-9a-f]{64}|[0-9a-f]{32})'")


def hash_subselects(check_sql):
    """For each sha256 literal in a stored integrity check, return (hex, scalar_sql) where scalar_sql is the
    enclosing parenthesised sub-select with the `= 'hex'` comparison removed (so it returns the hash text)."""
    out = []
    for m in HEX64.finditer(check_sql):
        # walk left to the '(' that opens the enclosing sub-select
        depth, i = 0, m.start() - 1
        while i >= 0:
            ch = check_sql[i]
            if ch == ")": depth += 1
            elif ch == "(":
                if depth == 0: break
                depth -= 1
            i -= 1
        # walk right to the matching ')'
        depth, j = 0, m.end()
        while j < len(check_sql):
            ch = check_sql[j]
            if ch == "(": depth += 1
            elif ch == ")":
                if depth == 0: break
                depth -= 1
            j += 1
        inner = check_sql[i:j + 1]
        scalar = re.sub(r"=\s*'" + m.group(1) + "'", "", inner)
        out.append((m.group(1), scalar))
    return out


def build_sql(asset, ups, snap, pins, registry):
    """pins: {'pre': {table: md5}, 'post': {table: md5}, 'reseal': {old_hex: new_hex}}"""
    stmts = update_sql(asset, ups)
    reg = registry[asset]
    check = reg["integrity_check_sql"] or ""
    ic_md5 = hashlib.md5(check.encode()).hexdigest()
    reseal = pins.get("reseal", {})
    total = sum(n for _, n, _ in stmts)
    tabs = list(pins["pre"])
    decl = "\n".join(f"  fp_{i} text;" for i, _ in enumerate(tabs))
    pre_ck = "\n".join(
        f"  EXECUTE {dq(fingerprint_sql(snap, t, pk_of(asset, t), asset), 'q')} INTO fp_{i};\n"
        f"  IF fp_{i} IS DISTINCT FROM '{pins['pre'][t]}' THEN RAISE EXCEPTION 'curation refuses: {t} is not the pinned pre-state (%)', fp_{i}; END IF;"
        for i, t in enumerate(tabs))
    already = " AND ".join(f"fp_{i} = '{pins['post'][t]}'" for i, t in enumerate(tabs))
    fp_all = "\n".join(f"  EXECUTE {dq(fingerprint_sql(snap, t, pk_of(asset, t), asset), 'q')} INTO fp_{i};" for i, t in enumerate(tabs))
    post_ck = "\n".join(
        f"  IF fp_{i} IS DISTINCT FROM '{pins['post'][t]}' THEN RAISE EXCEPTION 'curation post-flight: {t} content fingerprint mismatch (%)', fp_{i}; END IF;"
        for i, t in enumerate(tabs))
    upd = "\n".join(
        f"  {sql};\n  GET DIAGNOSTICS n = ROW_COUNT;\n  IF n <> {cnt} THEN RAISE EXCEPTION 'curation expected {cnt} {t} rows, updated %', n; END IF;"
        for t, cnt, sql in stmts)
    if reseal:
        rep = "integrity_check_sql"
        for o, n in reseal.items():
            rep = f"replace({rep}, '{o}', '{n}')"
        reseal_already = " AND ".join(f"position('{n}' IN ic) > 0" for n in reseal.values())
        reseal_block = f"""
  -- reseal the stored integrity contract (its sha256 covers the changed tables)
  UPDATE asset_registry SET integrity_check_sql = {rep} WHERE asset_id = '{asset}';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'curation expected 1 registry row, updated %', n; END IF;"""
        ic_guard = f"""
  IF md5(ic) IS DISTINCT FROM '{ic_md5}' THEN RAISE EXCEPTION 'curation refuses: registry integrity_check_sql is not the pinned pre-state text (md5 mismatch)'; END IF;"""
        already_ic = f"\n    IF NOT ({reseal_already}) THEN RAISE EXCEPTION 'curation refuses: tables are at the curated content but the registry contract is not resealed'; END IF;"
    else:
        reseal_block, ic_guard, already_ic = "", "", ""
    return f"""-- =============================================================================
-- DRAFT_NEEDS_NUMBER_l0_{asset}_citation_curation.sql      (HELD DRAFT: NOT APPLIED, NOT A MIGRATION)
-- Lane: curation-lane (Exec Suvarna), branch suvarna/land/TI-curation-001, N-101 curation of {asset}.
-- SS allocates the migration number (block 1200-1299).  Citation TEXT only: {total} rows across {len(stmts)} table(s);
-- no value, key or other column changes.  Every proposed citation is chunk-level (corpus chunk id + page + printed
-- sloka) and each row's FACT/INFERENCE class and supporting quote are in the ledger
-- (assets/{asset}_ledger.json); rows the held text CONTRADICTS are not touched (acharya batch).
-- GUARDS  per-table md5 fingerprint of every non-timestamp column must equal the pinned pre-state; every UPDATE
--         matches natural key AND exact old citation and must hit the exact expected row count; post-state
--         fingerprints are pinned; {'the stored integrity_check_sql is pinned by md5 and resealed (each sha256/md5 literal replaced by the value computed on the test replica after the UPDATEs); it must read true afterwards' if reseal else 'the asset integrity check does not hash these columns (no reseal needed)'};
--         idempotent: a second apply is a NOTICE + no-op.
-- Seed parity (NOT patched here; follow-up after SS review and PR #2984): {SEED_MODULE.get(asset, 'the writer')}
--         must carry the same citations or the next L0 rebuild reverts them; editing it also stales
--         nirmana-writer-digests.json (a #2984 file).
-- =============================================================================

DO $curation$
DECLARE
  n integer;
  ic text;
  ok boolean;
{decl}
BEGIN
  SELECT integrity_check_sql INTO ic FROM asset_registry WHERE asset_id = '{asset}' FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'curation refuses: asset_registry row {asset} not found'; END IF;
{fp_all}
  IF {already} THEN{already_ic}
    RAISE NOTICE 'curation already applied: no-op';
    RETURN;
  END IF;
{pre_ck}{ic_guard}

{upd}

  -- post-flight
{fp_all}
{post_ck}
{reseal_block}
  SELECT integrity_check_sql INTO ic FROM asset_registry WHERE asset_id = '{asset}';
  IF ic IS NOT NULL THEN
    EXECUTE ic INTO ok;
    IF ok IS NOT TRUE THEN RAISE EXCEPTION 'curation post-flight: {asset} stored integrity_check_sql reads false'; END IF;
  END IF;
END
$curation$;
"""


# --------------------------------------------------------------------------------------------
def create_replica(sock, port, db, asset, snap):
    psql(sock, port, "postgres", f"DROP DATABASE IF EXISTS {db}")
    # production sorts with glibc en_US.UTF8 (punctuation ignored at the first level); the stored checks use a bare
    # ORDER BY, so the replica uses ICU 'en-US-u-ka-shifted'.  The G0 fidelity check (stored check reads true) is the proof.
    psql(sock, port, "postgres", f"CREATE DATABASE {db} TEMPLATE template0 ENCODING 'UTF8' LOCALE_PROVIDER icu ICU_LOCALE 'en-US-u-ka-shifted' LC_COLLATE 'C' LC_CTYPE 'C'")
    sql = ["DROP TABLE IF EXISTS asset_registry;",
           "CREATE TABLE asset_registry (asset_id text PRIMARY KEY, integrity_check_sql text, english_description text, target_floor bigint);"]
    for t in all_tables(asset):
        cols = load_cols(snap, t)
        sql.append(f"DROP TABLE IF EXISTS {t};")
        sql.append(f"CREATE TABLE {t} (" + ", ".join(f'"{c["name"]}" {c["type"]}' for c in cols) + ");")
        rows = [json.loads(l) for l in open(pathlib.Path(snap) / f"{t}.rows.jsonl")]
        for i in range(0, len(rows), 400):
            chunk = json.dumps(rows[i:i + 400], ensure_ascii=False)
            sql.append(f"INSERT INTO {t} SELECT * FROM json_populate_recordset(NULL::{t}, {dq(chunk, 'j')}::json);")
    reg = json.load(open(pathlib.Path(snap) / "registry.json"))[asset]
    sql.append(f"INSERT INTO asset_registry VALUES ({dq(asset)}, {dq(reg['integrity_check_sql']) if reg['integrity_check_sql'] else 'NULL'}, "
               f"{dq(reg.get('english_description') or '')}, {reg.get('target_floor') or 0});")
    f = pathlib.Path(tempfile.mkdtemp()) / "replica.sql"
    f.write_text("\n".join(sql), encoding="utf8")
    psql(sock, port, db, file=str(f))


def table_state(sock, port, db, asset):
    out = {}
    for t in all_tables(asset):
        out[t] = [json.loads(x) for x in psql(sock, port, db, f"select row_to_json(t)::text from {t} t order by 1").stdout.splitlines() if x]
    out["_ic"] = psql(sock, port, db, f"select integrity_check_sql from asset_registry where asset_id='{asset}'").stdout
    return out


def diff_cols(a, b, asset):
    d = []
    for t in all_tables(asset):
        ra = {json.dumps(r, sort_keys=True) for r in a[t]}
        rb = {json.dumps(r, sort_keys=True) for r in b[t]}
        for s in ra ^ rb:
            pass
        # per-row diff by index of sorted unique serialisation is brittle; compare multiset of changed columns
        A = sorted(a[t], key=lambda r: json.dumps(r, sort_keys=True)); B = sorted(b[t], key=lambda r: json.dumps(r, sort_keys=True))
    return d


def run_check(sock, port, db, asset):
    ic = psql(sock, port, db, f"select integrity_check_sql from asset_registry where asset_id='{asset}'").stdout
    if not ic.strip(): return None
    return psql(sock, port, db, ic).stdout.strip()


def test_asset(asset, ledger, snap, sock, port, outdir):
    snap = pathlib.Path(snap)
    registry = json.load(open(snap / "registry.json"))
    log = []
    L = lambda m: (print(m), log.append(m))
    ups, skipped = updates_from_ledger(asset, ledger, snap)
    if not ups:
        L(f"{asset}: no recite updates; nothing to draft"); return None
    n_upd = sum(i["n"] for v in ups.values() for i in v)
    create_replica(sock, port, "g0", asset, snap)
    base = run_check(sock, port, "g0", asset)
    assert base in (None, "t"), f"replica fidelity: stored check reads {base!r}"
    L(f"G0 PASS replica fidelity ({asset}): stored integrity check reads {base}")
    tabs = all_tables(asset)
    pre = {t: psql(sock, port, "g0", fingerprint_sql(snap, t, pk_of(asset, t), asset)).stdout.strip() for t in tabs}
    # probe: apply updates in a rolled-back txn, read post fingerprints and the post sha256 sub-selects
    stm = update_sql(asset, ups)
    check = registry[asset]["integrity_check_sql"] or ""
    subs = hash_subselects(check)
    probe = "BEGIN;\n" + "\n".join(f"{s};" for _, _, s in stm) + "\n"
    probe += "".join(f"SELECT 'F|{t}|'||({fingerprint_sql(snap, t, pk_of(asset, t), asset)});\n" for t in tabs)
    probe += "".join(f"SELECT 'H|{i}|'||({sc});\n" for i, (_, sc) in enumerate(subs))
    probe += "ROLLBACK;"
    out = psql(sock, port, "g0", probe).stdout
    post = {m.group(1): m.group(2) for m in re.finditer(r"F\|([^|]+)\|([0-9a-f]{32})", out)}
    newhex = {int(m.group(1)): m.group(2) for m in re.finditer(r"H\|(\d+)\|([0-9a-f]{32,64})", out)}
    reseal = {}
    for i, (old, _) in enumerate(subs):
        if newhex.get(i) and newhex[i] != old: reseal[old] = newhex[i]
    assert {t: psql(sock, port, "g0", fingerprint_sql(snap, t, pk_of(asset, t), asset)).stdout.strip() for t in tabs} == pre
    pins = {"pre": pre, "post": post, "reseal": reseal}
    json.dump(pins, open(snap / f"{asset}.pins.json", "w"), indent=1)
    sql = build_sql(asset, ups, snap, pins, registry)
    out_sql = pathlib.Path(outdir) / f"DRAFT_NEEDS_NUMBER_l0_{asset}_citation_curation.sql"
    out_sql.write_text(sql, encoding="utf8")
    L(f"G1 PASS probe (rolled back): {n_upd} rows over {len(ups)} table(s); {len(reseal)} hash literal(s) to reseal; {len(skipped)} ledger recite entries not drafted")
    # apply once
    create_replica(sock, port, "g1", asset, snap)
    before = table_state(sock, port, "g1", asset)
    psql(sock, port, "g1", file=str(out_sql))
    after = table_state(sock, port, "g1", asset)
    changed = 0
    for t in tabs:
        assert len(before[t]) == len(after[t])
        keys, cite = spec3(asset, t)[:2] if t in SPECS[asset] else ((), None)
        nc = lambda r: json.dumps({c: v for c, v in r.items() if c != cite}, sort_keys=True)
        sb = sorted(before[t], key=lambda r: (nc(r), json.dumps(r.get(cite), sort_keys=True)))
        sa = sorted(after[t], key=lambda r: (nc(r), json.dumps(r.get(cite), sort_keys=True)))
        for rb, ra in zip(sb, sa):
            assert nc(rb) == nc(ra), (t, "a non-citation column changed")
            if rb != ra:
                changed += 1
    for t in EXTRA_TABLES.get(asset, []):
        assert before[t] == after[t], t
    assert changed == n_upd, (changed, n_upd)
    assert run_check(sock, port, "g1", asset) in (None, "t")
    if reseal: assert after["_ic"] != before["_ic"]
    L(f"G2 PASS apply once: exactly {changed} citation cells changed (only the citation column of the keyed rows); no other column of any replicated table differs; stored integrity check reads {run_check(sock, port, 'g1', asset)}")
    p = psql(sock, port, "g1", file=str(out_sql))
    assert "already applied" in p.stderr
    assert table_state(sock, port, "g1", asset) == after
    L("G3 PASS idempotent: second apply = NOTICE 'already applied: no-op', nothing changed")
    # guard on old values: mutate (a) a to-be-updated citation, (b) another column of a replicated table, (c) the registry text
    t0 = next((t for t in ups if SPECS[asset][t][0] and not ups[t][0].get('jsonb')), next(iter(ups))); keys0, cite0, kind0 = spec3(asset, t0); k0 = ups[t0][0]["key"]
    if not keys0:                         # family-only asset: address the family through its id query
        k0 = None
    other_cols = [c["name"] for c in load_cols(snap, t0) if c["name"] not in keys0 and c["name"] != cite0 and c["type"] == "text"]
    wh = (" AND ".join(f"{k}::text = {dq(v)}" for k, v in k0.items()) if k0 else f"id IN ({ups[t0][0]['query']})")
    muts = {"old citation altered": f"UPDATE {t0} SET {cite0} = {cite0} || ' ' WHERE " + wh}
    if other_cols and k0:
        muts["another column altered"] = f"UPDATE {t0} SET {other_cols[0]} = COALESCE({other_cols[0]}, '') || '.' WHERE " + " AND ".join(f"{k}::text = {dq(v)}" for k, v in k0.items())
    if reseal:
        muts["registry contract drifted"] = f"UPDATE asset_registry SET integrity_check_sql = integrity_check_sql || ' ' WHERE asset_id='{asset}'"
    for i, (name, mut) in enumerate(muts.items()):
        db = f"g4_{i}"
        create_replica(sock, port, db, asset, snap)
        psql(sock, port, db, mut)
        pre_s = table_state(sock, port, db, asset)
        pr = psql(sock, port, db, file=str(out_sql), check=False)
        assert pr.returncode != 0 and "curation refuses" in pr.stderr, (name, pr.stderr[-300:])
        assert table_state(sock, port, db, asset) == pre_s
        L(f"G4 PASS guard refuses on '{name}' and changed nothing")
        psql(sock, port, "postgres", f"DROP DATABASE IF EXISTS {db}")
    if reseal:
        create_replica(sock, port, "g5", asset, snap)
        psql(sock, port, "g5", ";\n".join(s for _, _, s in stm) + ";")
        assert run_check(sock, port, "g5", asset) == "f"
        L("G5 PASS the reseal is necessary: the citation UPDATEs alone make the stored integrity check read f")
        psql(sock, port, "postgres", "DROP DATABASE IF EXISTS g5")
    # pin mutation
    create_replica(sock, port, "g6", asset, snap)
    first = ups[t0][0]
    mut_sql = out_sql.read_text(encoding="utf8").replace(first["new"], first["new"] + " X", 1)
    assert mut_sql != out_sql.read_text(encoding="utf8")
    mf = pathlib.Path(tempfile.mkdtemp()) / "mut.sql"; mf.write_text(mut_sql, encoding="utf8")
    pre_s = table_state(sock, port, "g6", asset)
    pr = psql(sock, port, "g6", file=str(mf), check=False)
    assert pr.returncode != 0 and "post-flight" in pr.stderr, pr.stderr[-300:]
    assert table_state(sock, port, "g6", asset) == pre_s
    L("G6 PASS mutation: an altered new citation in the draft is caught by the pinned post-state fingerprint (nothing applied)")
    for db in ("g0", "g1", "g6"):
        psql(sock, port, "postgres", f"DROP DATABASE IF EXISTS {db}")
    (pathlib.Path(outdir) / f"PG_TEST_EVIDENCE_{asset}.txt").write_text(
        f"Real-PostgreSQL test of {out_sql.name} (disposable local PG 15, unix socket); tools/generic_citation_sql.py\n\n" + "\n".join(log) +
        "\n\nNot drafted (ledger recite entries without a safe automatic UPDATE):\n" + "\n".join(f"  {t} {rk} -- {why}" for t, rk, why in skipped) + "\n", encoding="utf8")
    return dict(rows=n_upd, tables=len(ups), reseal=len(reseal), skipped=len(skipped))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "test":
        asset, ledger, snap, sock, port, outdir = sys.argv[2:8]
        print(test_asset(asset, ledger, snap, sock, port, outdir))
    else:
        sys.exit("usage: see module docstring")
