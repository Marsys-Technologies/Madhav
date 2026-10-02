#!/usr/bin/env python3
"""Asset elevation tracker — any layer, driven by the registry and the gap/certification ledgers.

Generalises kala_brief_tracker.py (L3-only, hardcoded asset list) to every layer. An asset's row is
assembled from four sources, each named per column so a figure can be re-run:

  registry      live asset_registry (read-only)      — identity, target_table, depends_on, status
  production    information_schema + exact count(*)  — does it exist, how big, which contract columns
  brief         the tier-4 instance, if one exists   — brief SHAPE scan, presence only (§2)
  ledgers       asset_gaps.jsonl (the DELTA LEDGER, kind=gap|opportunity) / asset_certs.jsonl — per-GATE certification (§5, §7, §9)

CERTIFICATION IS THE ONLY THING THAT MAKES AN ASSET ELEVATED, and it is read from the certification
ledger alone. The brief scan is completeness, never conformance: a brief that mentions idempotency is
not an asset that is idempotent. The two are reported in separate columns and never summed.

    python3 00_ARCHITECTURE/control/asset_elevation_tracker.py --layer L0 [--env-file <path>]
    python3 00_ARCHITECTURE/control/asset_elevation_tracker.py --layer all --watch
"""
import argparse, collections, datetime, glob, io, json, os, re, subprocess, sys, time

ROOT  = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip() or "."
# R57/P3: ledger/output paths overridable so a sandbox run never reads or writes the production
# control directory (NIKASHA_CONTROL_DIR; ported from harness/tracker_sandbox.py).
CTRL  = os.environ.get("NIKASHA_CONTROL_DIR", os.path.join(ROOT,"00_ARCHITECTURE/control"))
OUT   = os.path.join(CTRL,"asset_elevation_tracker.json")
GAPS  = os.path.join(CTRL,"asset_gaps.jsonl")
CERTS = os.path.join(CTRL,"asset_certs.jsonl")

LAYERS = {
 "L0":{"prefix":"bg_","name":"Brahmagyan","registry_layer":"brahmagyan","scoring":"fidelity",
       "instance":"00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md",  # v3.0 DRAFT_PENDING_ACCEPTANCE — briefs derived from it are pilots (tier-4 §0)
       "briefs":"00_ARCHITECTURE/briefs/nirmana/l0_assets"},
 "L1":{"prefix":"ga_","name":"Gaṇita","registry_layer":"ganita","scoring":"contribution",
       "instance":None,"briefs":"00_ARCHITECTURE/briefs/nirmana/l1_assets"},
 "L2":{"prefix":"bo_","name":"Bodha","registry_layer":"bodha","scoring":"contribution",
       "instance":None,"briefs":"00_ARCHITECTURE/briefs/nirmana/l2_assets"},
 "L3":{"prefix":"ka_","name":"Kāla","registry_layer":"kala","scoring":"contribution",
       "instance":None,"briefs":"00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs"},
 "L4":{"prefix":"ph_","name":"Phala","registry_layer":"phala","scoring":"contribution",
       "instance":None,"briefs":"00_ARCHITECTURE/briefs/nirmana/l4_assets"},
 "L5":{"prefix":"mi_","name":"Mīmāṃsā","registry_layer":"mimamsa","scoring":"contribution",
       "instance":None,"briefs":"00_ARCHITECTURE/briefs/nirmana/l5_assets"},
}

# The certified gates. Nine, not thirty-three. A gate is a CLAIM WITH A DETECTOR THAT COULD RETURN
# FALSE; everything that was merely "addressed in the brief" moved to SHAPE below, which produces no
# certification record because a present section is not a verified claim. See the layer template §5.2.
#
# Ldgr absorbs the former facts/interpretation gate: a ledger entry naming its upstream fact_ids IS
# the separation test, and the separate gate had no detector of its own.
# Narr and Dens are CONDITIONAL — an asset that emits no prose / reaches no served surface disposes
# of them with an explicit N-A record, which counts as satisfied. Disposing is one line; the gate is
# never silently dropped.
GATES = [
 ("Ldgr","derivation ledger",      "always",      "every derived value names the upstream fact_id it reads, and those ids resolve"),
 ("Idem","idempotency",            "always",      "a rebuild replaces its own rows; it never accretes (CLAUDE.md §N.3)"),
 ("Earn","earned signal",          "always",      "every status/grade/PASS has a detector measuring that specific claim (§N.8)"),
 ("Null","honest null",            "always",      "an underivable value is emitted as null, not as a plausible default (§N.7.6)"),
 ("Vocab","vocabulary conformance","always",      "one canonical id per thing, one closed alias set, no free-text synonym"),
 ("Carr","source carriage",        "always",      "what the asset restates from a source matches it; what it computes reproduces a second way; a witness disagreement is carried, not settled — ONE applicable check from CARRIAGE_MENU, run"),
 ("Narr","narration fidelity",     "emits prose", "prose restates cited facts and does not re-derive them (§N.7)"),
 ("Dens","serving density",        "is served",   "confirmed vs catalog-only counted separately; dense layer survives a trim (§N.6)"),
 # NINTH GATE, added 2026-09-26 by native ruling (decision 17). An asset's content is worth nothing if
 # the orchestrator cannot rebuild it on demand, and the property is decidable read-only: registered
 # (@register id matches the registry, BOTH quote styles) · contract (WriterBase; run XOR
 # plan_substeps+run_substep; never commits ctx.db_conn; never writes asset_throughput) · dispatchable
 # target (target_table set, or service/multi-table declared) · DAG resolvable (deps exist, no cycle,
 # declared edges match what it reads) · count/integrity present and able to fail · completion honesty
 # (the build record agrees with the live count — rows_written=0 against a populated table is a status
 # with no measurement behind it). Runtime state comes from ctx.dry_run, never from state='lit' (§N.8).
 # The gate asks whether the rebuild WORKS; making a working rebuild faster or incremental is a tier-4
 # §9 opportunity and never blocks. Fixes go in the asset or the registry, never the frozen orchestrator.
 ("Build","buildability",          "always",      "the orchestrator can dispatch the asset and a triggered rebuild produces the correct result — nine static checks, all read-only (R65: aligned on nine per T4 §4.2; D2 reopen carries the T3 §5.2/changelog half)"),
]

# Pick the ONE that fits what the asset actually does. Running three where one applies is theatre;
# running none is an unearned signal. Where none applies, the Carr record is NO_DETECTOR with a
# reason — an honest null, never a pass.
# RENAMED from DOMAIN_MENU 2026-09-26 (native ruling 11): `Carr` asks whether the asset TRANSMITTED
# faithfully, not whether the astrology is right — that verdict is formed above the data plane. The
# former D4 (seeded negative case — a case the tradition says must NOT fire) is removed: deciding what
# must not fire is a doctrinal act and belongs to the reasoning layer's own artefact.
CARRIAGE_MENU = [
 ("D1","source correspondence",   "the asset restates a cited classical source",      "the restatement against the passage — prerequisites, exceptions, cancellations included"),
 ("D2","witness carriage",        "two admitted authorities cover the same claim",    "the disagreement is carried forward as school disagreement, never averaged or silently resolved"),
 ("D3","independent re-derivation","the value is computable a second way",            "compute it that way and compare within a declared tolerance"),
]
DOMAIN_MENU = CARRIAGE_MENU  # backward-compatible alias for any reader of the JSON key "domain_menu"

# Brief SHAPE — scanned for presence, reported as one boolean per brief, never certified.
# These were T1/T2's sixteen lenses; they describe what a brief CONTAINS, which is not a claim about
# the asset. T3 (inheritance) is a property of the LAYER instance, declared once in its §4.4 and not
# re-litigated per asset. T5 (ladder positions) are status fields read from the registry.
SHAPE = [
 ("identity",        r"\bidentity\b|asset[- ]id|epistemic"),
 ("inputs / DAG",    r"\bDAG\b|upstream|declared input"),
 ("correctness",     r"invariant|correctness"),
 ("data sufficiency",r"data sufficien|coverage|row count"),
 ("consumers",       r"consumer|downstream|reader"),
 ("value / target",  r"latent[- ]value|value extraction|target[- ]state|disposition"),
 ("synergy",         r"OFFERS|DEMANDS|synergy oblig"),
 ("knowledge-time",  r"knowledge[- ]time|F15|F17|DP15a|as_of"),
 ("change packet",   r"may_touch|change packet|files"),
 ("evidence",        r"evidence|proof|detector"),
]

# The closed verdict vocabulary. One spelling each, matching asset_certs.jsonl's own _schema line,
# the layer template §5.3 and the asset template §4/§7. Three surfaces previously spelled these three
# different ways (NO DETECTOR / NO_DETECTOR, N-A / N/A / NA) -- a controlled-vocabulary failure inside
# the machinery that certifies controlled vocabulary.
VERDICTS = {"PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "N/A"}
PASSING_VERDICTS = {"PASS", "N/A"}

REQUIRED_GATES=[k for k,_,_,_ in GATES]

def jsonl(path):
    out=[]; bad=0
    if os.path.exists(path):
        for ln,line in enumerate(io.open(path,encoding="utf-8"),1):
            line=line.strip()
            if not line: continue
            try:
                r=json.loads(line)
                if not str(r.get("asset","")).startswith("_"): r["_line"]=ln; out.append(r)
            except Exception: bad+=1
    return out,bad

# R220 / F6 (nikasha_test/wave1/A_REVIEW.md): the ACTIVE population, the same one asset_census.py
# measures. `dead_flag` is NULL (not false) on every registry row, so the register's literal
# `is_active AND NOT dead_flag` is a NULL trap that matches ZERO rows; `dead_flag IS NOT TRUE` is the
# NULL-safe form. Before F6 this tracker applied no filter at all and counted 129 assets (23 in L3)
# where the census counts 127 (21) -- two retired L3 rows were being tracked as if live.
ACTIVE_PREDICATE = "is_active AND dead_flag IS NOT TRUE"

def registry(env_file, layer_key):
    """Live asset_registry rows for the layer's ACTIVE population (ACTIVE_PREDICATE).
    Returns (rows, reason_if_unavailable, population); population states the registry total and
    names every excluded (inactive/dead) row, so the gap between the two figures is never silent."""
    dsn=None
    if env_file and os.path.exists(env_file):
        for line in io.open(env_file,encoding="utf-8",errors="replace"):
            if line.strip().startswith("DATABASE_URL="):
                dsn=line.strip().split("=",1)[1].strip().strip('"').strip("'"); break
    dsn = dsn or os.environ.get("DATABASE_URL")
    if not dsn: return {}, "no DATABASE_URL — registry and production columns not read", None
    try: import psycopg2
    except ImportError: return {}, "psycopg2 not installed", None
    cfg=LAYERS[layer_key]
    try:
        conn=psycopg2.connect(dsn); conn.set_session(readonly=True, autocommit=False); cur=conn.cursor()
        scope_args=(cfg["registry_layer"], cfg["prefix"].replace("_","\\_")+"%")
        cur.execute("SELECT count(*) FROM asset_registry WHERE (layer=%s OR asset_id LIKE %s)", scope_args)
        registry_total=cur.fetchone()[0]
        cur.execute("SELECT asset_id FROM asset_registry WHERE (layer=%s OR asset_id LIKE %s) "
                    f"AND ({ACTIVE_PREDICATE}) IS NOT TRUE ORDER BY asset_id", scope_args)
        excluded=[r[0] for r in cur.fetchall()]
        cur.execute(f"""SELECT asset_id, target_table, storage_type, scope, is_active, catalog_status,
                              has_writer, COALESCE(depends_on,'{{}}'), count_sql,
                              (integrity_check_sql IS NOT NULL AND length(integrity_check_sql)>0)
                       FROM asset_registry WHERE (layer=%s OR asset_id LIKE %s) AND {ACTIVE_PREDICATE}
                       ORDER BY sort_order, asset_id""", scope_args)
        rows={}
        for r in cur.fetchall():
            rows[r[0]]=dict(target_table=r[1],storage_type=r[2],scope=r[3],is_active=r[4],
                            catalog_status=r[5],has_writer=r[6],depends_on=list(r[7]),
                            count_sql=r[8],integrity_check=r[9])
        # consumers, in-layer and cross-layer, and production presence
        cur.execute("SELECT asset_id, COALESCE(depends_on,'{}') FROM asset_registry")
        allrows=cur.fetchall()
        for aid,row in rows.items():
            row["consumers_in_layer"]=sorted(a for a,d in allrows if aid in d and a.startswith(cfg["prefix"]))
            row["consumers_cross_layer"]=sorted(a for a,d in allrows if aid in d and not a.startswith(cfg["prefix"]))
        tables=[r["target_table"] for r in rows.values() if r["target_table"]]
        if tables:
            cur.execute("""SELECT table_name, count(*) FROM information_schema.columns
                           WHERE table_schema='public' AND table_name = ANY(%s) GROUP BY 1""",(tables,))
            cols=dict(cur.fetchall())
            for row in rows.values():
                t=row["target_table"]
                row["table_exists"]= bool(t) and t in cols
                row["columns"]=cols.get(t)
                row["rows"]=None
                if row["table_exists"]:
                    try:
                        cur.execute('SELECT count(*) FROM public."%s"'%t.replace('"',''))
                        row["rows"]=cur.fetchone()[0]
                    except Exception: pass
        conn.rollback(); cur.close(); conn.close()
        return rows, None, dict(registry_total=registry_total, active=len(rows), excluded_inactive=excluded,
                                predicate=ACTIVE_PREDICATE)
    except Exception as e:
        return {}, "registry read failed: %s"%type(e).__name__, None

def find_brief(layer_key, asset_id):
    cfg=LAYERS[layer_key]; d=os.path.join(ROOT,cfg["briefs"])
    if not os.path.isdir(d): return None
    stem=asset_id[len(cfg["prefix"]):].upper()
    for pat in (f"*{asset_id.upper()}*.md", f"*{stem}*.md", f"*{asset_id}*.md"):
        hits=[h for h in glob.glob(os.path.join(d,pat)) if "REVIEW" not in os.path.basename(h).upper()]
        if hits: return sorted(hits)[0]
    return None

def scan_brief(path):
    if not path or not os.path.exists(path): return None
    s=io.open(path,encoding="utf-8",errors="replace").read()
    cells={lbl:bool(re.search(pat,s,re.I)) for lbl,pat in SHAPE}
    ver=(re.search(r'^version:\s*"?([^"\n]+)',s,re.M) or [None,"—"])[1].strip().strip('"')
    st =(re.search(r'^status:\s*([^\n#]+)',s,re.M) or [None,"—"])[1].strip()
    return dict(path=os.path.relpath(path,ROOT),version=ver,status=st,shape=cells,
                shape_present=sum(cells.values()),shape_total=len(cells),
                shape_complete=all(cells.values()),
                shape_missing=[k for k,v in cells.items() if not v])

def lifecycle(reg, brief, gaps, certs, required):
    """ELEVATED requires certification, never a brief. Nothing else may claim it."""
    # kind=opportunity rows (tier-4 §9) NEVER withhold ELEVATED: "conforms" and "could be better" are two
    # different words. Rows without `kind` are pre-2026-09-26 and read as gaps.
    open_gaps=[g for g in gaps if g.get("state","OPEN").upper() not in ("CLOSED","WITHDRAWN")
               and str(g.get("kind","gap")).lower()!="opportunity"]
    passing={c["criterion"] for c in certs if str(c.get("verdict","")).upper() in PASSING_VERDICTS}
    # An unrecognised verdict string is NOT silently treated as failing -- it is reported, because a
    # typo'd verdict and an honest FAIL are different facts and the closed set exists to keep them so.
    unknown=sorted({str(c.get("verdict","")) for c in certs} - VERDICTS)
    missing=[c for c in required if c not in passing]
    if unknown: return "LEDGER_INVALID", f"verdict(s) outside the closed set: {', '.join(unknown)}"
    if certs and not missing and not open_gaps: return "ELEVATED", "every gate certified or disposed; no open gap"
    if certs and not missing and open_gaps:    return "CERTIFIED_GAPS_OPEN", f"{len(open_gaps)} gap(s) open"
    if certs:                                  return "CERTIFYING", f"{len(required)-len(missing)}/{len(required)} gates certified"
    if open_gaps:                              return "GAPS_REGISTERED", f"{len(open_gaps)} gap(s), no certification yet"
    if brief and "ACCEPT" in (brief["status"] or "").upper(): return "BRIEF_ACCEPTED", "brief accepted; execution not started"
    if brief:                                  return "BRIEF_DRAFT", brief["status"]
    if reg is None:                            return "NOT_IN_REGISTRY", "asset not found in asset_registry"
    return "NO_BRIEF", "registered, no tier-4 brief"

def scan(layer_keys, env_file):
    gaps_all,gbad=jsonl(GAPS); certs_all,cbad=jsonl(CERTS)
    # R57/P3 closing semantics: a gap_id's state is its LATEST row (append-only ledger, closure is
    # a later CLOSED row, regression a later OPEN row). Rows without a gap_id are per-row facts
    # (hand-written, no detector binding, R58) and pass through unchanged. Without this collapse,
    # an appended CLOSED row is additive — the earlier OPEN row for the same gap_id still counts
    # as open, and the tracker's ELEVATED count never moves (ported from harness/tracker_sandbox.py).
    _latest={}; _rest=[]
    for g in gaps_all:
        if g.get("gap_id"): _latest[g["gap_id"]]=g
        else: _rest.append(g)
    gaps_all=_rest+list(_latest.values())
    gap_by=collections.defaultdict(list); cert_by=collections.defaultdict(list)
    for g in gaps_all: gap_by[g.get("asset")].append(g)
    for c in certs_all: cert_by[c.get("asset")].append(c)
    crit=[{"key":k,"label":l,"applies":a,"claim":cl} for k,l,a,cl in GATES]
    required=list(REQUIRED_GATES)
    out={"generated":datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
         "gates":crit,"domain_menu":[{"key":k,"label":l,"applies":a,"check":c} for k,l,a,c in DOMAIN_MENU],"layers":{},"ledger_bad_lines":gbad+cbad,
         "gaps_path":os.path.relpath(GAPS,ROOT),"certs_path":os.path.relpath(CERTS,ROOT)}
    for lk in layer_keys:
        cfg=LAYERS[lk]; rows,reason,population=registry(env_file,lk)
        assets=[]
        for aid in sorted(rows) if rows else []:
            r=rows[aid]; bp=find_brief(lk,aid); b=scan_brief(bp)
            g=gap_by.get(aid,[]); c=cert_by.get(aid,[])
            state,why=lifecycle(r,b,g,c,required)
            assets.append(dict(id=aid,layer=lk,scoring=cfg["scoring"],registry=r,brief=b,
                gaps_open=len([x for x in g if x.get("state","OPEN").upper() not in ("CLOSED","WITHDRAWN")
                               and str(x.get("kind","gap")).lower()!="opportunity"]),
                opps_open=len([x for x in g if x.get("state","OPEN").upper() not in ("CLOSED","WITHDRAWN")
                               and str(x.get("kind","gap")).lower()=="opportunity"]),
                gaps_total=len(g),
                certified=len({x["criterion"] for x in c if str(x.get("verdict","")) in PASSING_VERDICTS}),
                certs_total=len(c),required=len(required),state=state,why=why))
        out["layers"][lk]=dict(name=cfg["name"],prefix=cfg["prefix"],scoring=cfg["scoring"],
            instance=cfg["instance"],registry_reason=reason,n_assets=len(assets),population=population,
            assets=assets)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--layer",default="L0",help="L0..L5 or 'all'")
    ap.add_argument("--env-file",help="file containing DATABASE_URL for the read-only registry/production read")
    ap.add_argument("--watch",action="store_true"); ap.add_argument("--interval",type=int,default=10)
    a=ap.parse_args()
    keys=list(LAYERS) if a.layer.lower()=="all" else [k.strip().upper() for k in a.layer.split(",")]
    for k in keys:
        if k not in LAYERS: sys.exit(f"unknown layer {k}; expected one of {list(LAYERS)} or 'all'")
    while True:
        d=scan(keys,a.env_file); js=json.dumps(d,indent=1,default=str)
        io.open(OUT,"w").write(js)
        io.open(OUT[:-5]+".js","w").write("window.ASSET_DATA="+js+";\nwindow.dispatchEvent(new Event('asset-data'));\n")
        print(f'[{d["generated"]}]')
        for k in keys:
            L=d["layers"][k]
            if L["registry_reason"]: print(f'  {k} {L["name"]}: NOT READ — {L["registry_reason"]}'); continue
            P=L.get("population") or {}
            if P and P.get("registry_total")!=P.get("active"):
                print(f'  {k} population: {P["active"]} active of {P["registry_total"]} registry rows '
                      f'({P["predicate"]}) — excluded (inactive/dead): {", ".join(P["excluded_inactive"])}')
            st=collections.Counter(x["state"] for x in L["assets"])
            print(f'  {k} {L["name"]} ({L["scoring"]}): {L["n_assets"]} assets | '
                  +", ".join(f"{s}={n}" for s,n in sorted(st.items())))
            elev=sum(1 for x in L["assets"] if x["state"]=="ELEVATED")
            print(f'      ELEVATED {elev}/{L["n_assets"]} | open gaps {sum(x["gaps_open"] for x in L["assets"])}'
                  f' | open opportunities {sum(x["opps_open"] for x in L["assets"])}'
                  f' | gates certified {sum(x["certified"] for x in L["assets"])}/{L["n_assets"]*len(d["gates"])}')
        if d["ledger_bad_lines"]: print(f'  !! {d["ledger_bad_lines"]} malformed ledger line(s)')
        if not a.watch: break
        time.sleep(a.interval)


# ═══════════════════════ E6.3 — ELEVATED, exact ═══════════════════════════════════════════════════════════
# `elevated_assets(ref, repo)` is the ONE place an asset may be called ELEVATED (plan 1.1). It is a module-level
# function with no side effects. It reads EVERY input with `git -C <repo> show <sha>:<path>`, where <sha> is `ref`
# resolved once up front: never the working tree, never a database. It RAISES `ElevatedInputError` on any unreadable
# ref/path, any malformed JSONL line or record, a broken hash chain, a registry source it cannot trust, and
# `WatermarkOlderThanLedger` when E5.5's watermark does not cover every certificate at the ref; a failure never comes
# back as an empty set (an empty set is only ever the honest answer "nothing is elevated"). The legacy
# lifecycle()/scan() above is NOT this function and is not an authority for ELEVATED (E6.3t switches the tracker's
# own caller to this one).
#
# THE RULE. An asset is ELEVATED when it is TERMINALLY dispositioned (retire/consolidate WITH a decision id and a reason),
# or when all four hold (`elevated_report` says which, per asset; `elevated_assets` is its key set):
#   (1) every criterion of every core gate its layer requires -- the asset_census.CRITERION_REGISTRY entries whose
#       gate is in CELL_GATES and whose `layers` holds the asset's layer, exactly the rows the census rollup counts --
#       has a CURRENT satisfying certificate: a PASS (detector not NONE, not inconclusive, not capped, `basis` absent,
#       or `declaration` only where the registry defines it: Build.target on a service asset) or an N/A whose
#       `na.rule_id` is declared in NA_RULE_DECISIONS at `ref` with that `na.decision_id`. A gate with no criterion for
#       the layer cannot occur: the pinned registry FLOOR makes the function raise first;
#   (2) every addition DECLARED for the asset has a current PASS (an addition has no registry rule: no N/A);
#   (3) no open `gap` row on a core gate or declared addition: kind info/opportunity never blocks, nor does a row on
#       a non-gate criterion family (Cost, Count, Complete, Reach...: plan D3); an open gap on ANYTHING ELSE blocks;
#   (4) a disposition is recorded and is not `unresolved`.
#
# ---- INPUTS (all under `ref`) ----------------------------------------------------------------------------------
# asset_certs.jsonl is E5.1's ledger AND E5.5's: first line {"asset":"_schema"}, then hash-chained lines (`seq` 1..N
#   over the non-schema lines, `prev_sha256` = sha256 of the previous line's bytes, the schema line's for the first;
#   verified here by a small verifier identical to E5.1's `parse_records`, parity-tested against it). A line is either
#   a CERTIFICATE (cert_key, generation >= 1, cert_id == "<cert_key>@<generation>", verdict: E5.1's `_is_cert_line`) or
#   an EVENT (a `type` in invalidation|watermark|epoch_reset and none of cert_key/cert_id/generation, no certificate
#   `kind`/verdict: E5.1's `_is_event_line`); anything else raises.
#   certificate (kind gate|addition): asset, layer, kind, gate, criterion, criterion_version (int), detector, verdict,
#                     basis, na{rule_id, decision_id}, inconclusive, cross_checked (must be true on every gate record),
#                     evidence.census_run_id, writer_hashes{path: sha256}, writer_hashes_reason, upstream_cert_ids,
#                     semantic_fingerprint, cert_key "<asset>|<kind>|<criterion>", generation (1..n per key). The
#                     current record of a cert_key is its highest generation.
#                     record_version 1 or 2 (absent = 1; anything else raises). v2 (the real writer's output for EVERY record)
#                     carries citation_state (sourced|sourced_ocr_unverified|unsourced|refuted|null; a state only on a citation
#                     gate) and citation_state_caveat (exactly: a citation-gate PASS whose state is not `sourced`, so a null-state
#                     Ldgr.source_presence PASS has caveat true and counts); a v1 record may not carry them (v1 reads as null,
#                     caveat false: the choice E5.1's reader makes). unsourced/refuted PASS lines raise (N-74).
#   invalidation      E5.5: asset, layer, invalidates "<cert_id>" (a certificate on an EARLIER line), reason
#                     [{code,...}], walk >= 1. A repeated invalidation of one certificate is tolerated; the first wins.
#   watermark         E5.5: asset "_ledger", covers_seq (the seq of the last record the evaluation covered, below the
#                     line's own seq), certs_processed and last_cert_id (= the certificates with seq <= covers_seq and
#                     the last of them: each line is CHECKED for truth), commit. The ledger is covered iff a watermark
#                     exists and NO certificate has seq > the LARGEST covers_seq over all watermark lines (E5.5's
#                     rule: a late, smaller, truthful watermark neither helps nor hurts); otherwise
#                     WatermarkOlderThanLedger.
#   epoch_reset       E5.5: asset "_ledger", layer, decision "N-..": the strategist's re-walk-budget reset (no effect here).
# asset_gaps.jsonl (delta ledger): asset (must be a KNOWN asset id, so a malformed or look-alike id raises; the layer-wide pseudo-asset
#   `_layer_all` is skipped), gap_id, kind (gap|
#   opportunity|info; absent reads gap), criterion, state (OPEN|IN_PROGRESS|CLOSED|WITHDRAWN; absent reads OPEN),
#   superseded_by. A gap is keyed (asset, gap_id) and its state is its LATEST row; a row folded into another gap_id
#   (superseded_by, SAME asset, chains resolved, a cycle raises) is carried by the chain's terminal row.
#   A gap's kind and criterion are FIXED at first write (a later row may change only its state); a row that can block (a
#   core-gate row, or a declared addition's) may only be folded into a kind=gap row of a REGISTERED criterion of the same
#   gate (or the same declared addition), and never from OPEN into a CLOSED/WITHDRAWN row; non-gate rows fold freely. A core-gate or
#   declared-addition criterion re-keyed `kind: info` raises.
# asset_dispositions.jsonl: APPEND-ONLY and chained like the certificate ledger (first line {"asset":"_schema"}, then
#   `seq` 1..N and `prev_sha256`, verified by the same chain check). Each line is {asset (a registry asset), disposition
#   (keep|integrate|enrich|qualify|consolidate|historical|retire|unresolved; anything else raises), reason, decision_id
#   (the strategist's decision, N-<n>..., or null: a null reads `unresolved`; a malformed one raises), decided_on
#   (tz-aware ISO), additions (REQUIRED key)}. The LATEST row governs disposition, reason and decision id; the declared
#   additions are the UNION over all of the asset's rows, so a later row without them cannot un-declare one. NOBODY but a
#   strategist-approved PR writes this file (the layer-sheet letters are loaded by such a PR, never inferred here); this
#   module has no writer. A retire/consolidate counts as TERMINAL only with a decision id AND a visible reason.
# platform/scripts/governance/asset_census.py (read as SOURCE with ast, never imported): LAYERS[*].prefix,
#   CRITERION_REGISTRY[*].{gate,layers,detector,revision}, CELL_GATES, NA_RULE_DECISIONS, and the PARTIAL cap rule in
#   `_check_contribution`. The WHOLE module is walked: a second assignment of, a mutation of, an alias of or a dynamic
#   write to any of the four registry names raises (the parser must be able to see the final value).
# platform/scripts/seed/asset_registry_seed.ts (+ LEVEL_MAP.json when present; parsed by generate_level_map.py AS COMMITTED AT `ref`): the asset ids the registry holds and
#   the asset kind (non-authoritative stand-in for the live registry, as in generate_level_map.py).
#
# "CURRENT" (see certificate_currency): the record is the latest generation of its cert_key; a GATE record's declarations_sha256
# equals the sha256 of asset_declarations.json's bytes at `ref` (null = not current; a missing file raises); no invalidation line names
# its cert_id; every recorded writer file still hashes to the recorded sha256 at `ref` (absent at `ref` = stale); every
# upstream cert id is on an earlier line and is itself current and PASS/N/A, and is either the LATEST generation of its
# key or an older generation whose semantic fingerprint equals the latest's (E5.5: a generation bump with identical
# output invalidates nothing downstream); a
# PASS (or measured N/A) carries a semantic fingerprint (comparing it with the live rows is E5.5's job, delivered as an
# invalidation line); a gate record's criterion_version equals the registry revision at `ref`.
import ast as _ast, copy as _copy, dataclasses as _dc, datetime as _dt, hashlib as _hashlib, re as _re, unicodedata as _unicodedata

E63_CONTROL_DIR = "00_ARCHITECTURE/control"
E63_CERTS_PATH = E63_CONTROL_DIR + "/asset_certs.jsonl"
E63_GAPS_PATH = E63_CONTROL_DIR + "/asset_gaps.jsonl"
E63_DISPOSITIONS_PATH = E63_CONTROL_DIR + "/asset_dispositions.jsonl"
E63_LEVEL_MAP_PATH = E63_CONTROL_DIR + "/LEVEL_MAP.json"
E63_CENSUS_PATH = "platform/scripts/governance/asset_census.py"
E63_SEED_PATH = "platform/scripts/seed/asset_registry_seed.ts"
E63_E51_PATH = "platform/scripts/governance/nikasha_certify.py"            # E5.1: the certificate ledger's own validator
E63_DECLARATIONS_PATH = "platform/scripts/governance/asset_declarations.json"   # a gate certificate is bound to its sha256 at `ref`

# FLOOR: how many criteria each core gate must have, per layer, in asset_census.CRITERION_REGISTRY. Pinned from the
# registry at origin/main bf6fe712b (REGISTRY_REVISION 7). A registry edit that REMOVES a core-gate criterion (or a
# `layers=()`) would make ELEVATED easier to reach, so it makes this function raise instead; changing the floor is a
# deliberate, reviewed edit of THIS constant. Carr is pinned as D1/D2/D3 (floor 3) so that the retirement of Carr.detector
# (E6 item (i), REGISTRY_REVISION 8) does not make the function raise; a still-registered Carr.detector is just one more
# required criterion.
E63_PINNED_LAYERS = ("L0", "L1", "L2", "L3", "L4", "L5")
# PINNED CRITERION IDS: every id below must stay a registry criterion of that gate that applies in every pinned layer.
# Captured from the registry at origin/main (REGISTRY_REVISION 7). A count floor alone is not enough (delete one
# criterion, add another: the count holds and a required cert silently disappears), so a removed, renamed, re-gated or
# re-layered pinned id makes the function raise naming it. ADDING a criterion needs no edit (it only adds a requirement);
# changing a pin is a deliberate, reviewed edit of THIS constant. The count floor below stays as a second check.
E63_REQUIRED_CRITERIA = {
    "Ldgr": ("Ldgr.source_presence",),
    "Idem": ("Idem.pattern",),
    "Earn": ("Earn.build_record", "Earn.service_state"),
    "Null": ("Null.blank_rows", "Null.schema_default"),
    "Vocab": ("Vocab.alias", "Vocab.identity"),
    "Carr": ("Carr.D1", "Carr.D2", "Carr.D3"),                      # Carr.detector is retired by #2856: an extra only adds a requirement
    "Narr": ("Narr.agree", "Narr.checkable", "Narr.fidelity_test", "Narr.lint"),
    "Dens": ("Dens.served",),
    "Build": ("Build.completion", "Build.contract", "Build.count_integrity", "Build.dag", "Build.dep_liveness",
              "Build.exercised", "Build.history", "Build.registered", "Build.target"),
}
E63_REQUIRED_FLOOR = {"Ldgr": 1, "Idem": 1, "Earn": 2, "Null": 2, "Vocab": 2, "Carr": 3, "Narr": 4, "Dens": 1, "Build": 9}
# Where the registry defines a PASS BY DECLARATION (mirrors E5.1's nikasha_certify.DECLARATION_BASED; parity-tested):
# criterion -> the asset kinds it applies to. A `basis: declaration` PASS anywhere else is not a PASS.
E63_DECLARATION_BASED = {"Build.target": ("service",)}

E63_VERDICTS = frozenset({"PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "ERRORED", "N/A"})
E63_GAP_KINDS = frozenset({"gap", "opportunity", "info"})
E63_GAP_STATES = frozenset({"OPEN", "IN_PROGRESS", "CLOSED", "WITHDRAWN"})
E63_CLOSED_GAP_STATES = frozenset({"CLOSED", "WITHDRAWN"})
E63_DISPOSITIONS = frozenset({"keep", "integrate", "enrich", "qualify", "consolidate", "historical", "retire",
                              "unresolved"})
E63_TERMINAL_DISPOSITIONS = frozenset({"retire", "consolidate"})
E63_CITATION_BLOCKING = ("unsourced", "refuted")             # the census caps these at NO_DETECTOR (E5.1 CITATION_PASS_REFUSED; guarded)
E63_BASIS_DECLARATION = "declaration"        # the one recognised `basis` (asset_census._check_contribution)
# Layer-wide gap rows attach to no asset (the real ledger holds five, e.g. Build.diagnosability): the one pseudo-asset
# id allowed in the gap ledger besides `_schema`. They never block an asset (no asset carries that id).
E63_PSEUDO_GAP_ASSETS = frozenset({"_layer_all"})
E63_MAX_JSON_DEPTH = 64
E63_EVENT_TYPES = ("invalidation", "watermark", "epoch_reset")     # E5.1's EVENT_TYPES
E63_EVENT_FORBIDDEN = ("cert_key", "cert_id", "generation")          # certificate-only fields an event may not carry
E63_CERT_KINDS = ("gate", "addition")
E63_GUARDED_NAMES = ("CRITERION_REGISTRY", "CELL_GATES", "NA_RULE_DECISIONS", "LAYERS")
E63_MUTATORS = frozenset({"update", "pop", "popitem", "setdefault", "clear", "append", "extend", "insert", "remove",
                          "add", "discard", "sort", "reverse", "__setitem__", "__delitem__", "__ior__"})
E63_DYNAMIC_CALLS = frozenset({"globals", "vars", "setattr", "delattr", "exec", "eval"})

_E63_ASSET = _re.compile(r"[a-z][a-z0-9_]*")
_E63_ADDITION = _re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_E63_SHA256 = _re.compile(r"[0-9a-f]{64}")
_E63_COMMIT = _re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_E63_DECISION = _re.compile(r"N-[0-9]{1,6}[A-Za-z0-9._-]{0,24}")    # E5.5's decision id
_E63_CERT_ID = _re.compile(r"([a-z][a-z0-9_]*)\|(gate|addition)\|([A-Za-z0-9][A-Za-z0-9_.-]*)@([1-9][0-9]*)")


class ElevatedInputError(RuntimeError):
    """An input of `elevated_assets` was unreadable or malformed, so no answer can be given. `code` is a stable slug."""

    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class WatermarkOlderThanLedger(ElevatedInputError):
    """E5.5 has not evaluated every certificate at `ref` (no watermark covers them): the invalidations on file cannot
    be trusted for the newer lines, so the exact function refuses to answer rather than guess."""


def _e63_fail(code, message):
    raise ElevatedInputError(code, message)


def _e63_git(repo, args, what):
    env = {k: v for k, v in os.environ.items()
           if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_PREFIX")}
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, env=env)
    except (OSError, ValueError) as e:
        _e63_fail("git_unavailable", f"{what}: {type(e).__name__}: {e}")
    if r.returncode != 0:
        _e63_fail("unreadable", f"{what}: git exit {r.returncode}: {r.stderr.decode('utf-8', 'replace').strip()[:240]}")
    return r.stdout


def _e63_resolve_ref(ref, repo):
    if not isinstance(ref, str) or not ref or ref != ref.strip() or ref.startswith("-"):
        _e63_fail("bad_ref", f"ref must be a non-blank git ref string, got {ref!r}")
    if repo is None or not str(repo).strip():
        _e63_fail("bad_repo", "repo must be a repository path")
    out = _e63_git(repo, ["rev-parse", "--verify", "--quiet", ref + "^{commit}"], f"resolve ref {ref!r}")
    return out.decode("ascii", "replace").strip()       # git exits non-zero (raised above) unless it resolved a commit


def _e63_show(repo, sha, path):
    return _e63_git(repo, ["show", f"{sha}:{path}"], f"read {path} at {sha[:12]}")


def _e63_exists(repo, sha, path):
    return bool(_e63_git(repo, ["ls-tree", "--name-only", sha, "--", path], f"look for {path} at {sha[:12]}").strip())


def _e63_sha(b):
    return _hashlib.sha256(b).hexdigest()


# ---- strict JSON (the same rules as E5.1's strict_json_loads) -----------------------------------------------------
def _e63_no_dup_keys(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate key {k!r}")
        d[k] = v
    return d


def _e63_no_constant(name):
    raise ValueError(f"non-finite constant {name}")


def _e63_max_depth(text):
    depth = best = 0
    in_str = esc = False
    for ch in text:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "[{":
            depth += 1
            best = max(best, depth)
        elif ch in "]}":
            depth -= 1
    return best


def _e63_strict_loads(text):
    """json.loads that refuses duplicate object keys, NaN/Infinity and nesting deeper than E63_MAX_JSON_DEPTH."""
    if _e63_max_depth(text) > E63_MAX_JSON_DEPTH:
        raise ValueError(f"nesting deeper than {E63_MAX_JSON_DEPTH}")
    try:
        return json.loads(text, object_pairs_hook=_e63_no_dup_keys, parse_constant=_e63_no_constant)
    except RecursionError as e:
        raise ValueError("nesting too deep") from e


def _e63_lines(data, path):
    """[(line number, raw line bytes, object)] for every non-blank line, strictly parsed; the first must be the
    `_schema` row. A torn or unreadable line, a duplicate key, a non-object line: ElevatedInputError."""
    if not data:
        _e63_fail("malformed", f"{path} is empty (no `_schema` row)")
    parts = data.split(b"\n")
    tail = parts[-1]
    raw_lines = parts[:-1] + ([tail] if tail else [])
    rows = []
    for n, raw in enumerate(raw_lines, 1):
        if not raw.strip():
            continue
        try:
            obj = _e63_strict_loads(raw.decode("utf-8"))
        except UnicodeDecodeError as e:
            _e63_fail("malformed", f"{path} line {n} is not valid UTF-8 ({e.reason})")
        except ValueError as e:
            _e63_fail("malformed", f"{path} line {n} is not strict JSON ({e})")
        if not isinstance(obj, dict):
            _e63_fail("malformed", f"{path} line {n} is not a JSON object")
        rows.append((n, raw, obj))
    if not rows or rows[0][2].get("asset") != "_schema":
        _e63_fail("malformed", f"{path}: the first line must be the `_schema` row")
    return rows


def _e63_chain_check(r, where, nrec, prev):
    """E5.1's chain rule, shared by every chained ledger here: seq runs 1..N over the records and prev_sha256 is the
    sha256 of the previous line's bytes (the `_schema` row's for the first)."""
    if not _e63_int(r.get("seq")) or r["seq"] != nrec + 1:
        _e63_fail("malformed", f"{where}: seq is {r.get('seq')!r}, expected {nrec + 1} (seq runs 1..N over the records)")
    if r.get("prev_sha256") != prev:
        _e63_fail("malformed", f"{where}: the hash chain is broken (prev_sha256 is not the sha256 of the previous "
                               "line): an earlier line was edited, deleted or reordered")


def _e63_nonblank(v):
    return isinstance(v, str) and bool(v.strip())


# Characters that render as nothing although they are letters/symbols, not format characters: the Hangul fillers (U+115F,
# U+1160, U+3164, U+FFA0) and the Braille blank (U+2800). A reason made only of these is blank.
_E63_FILLERS = frozenset("\u115f\u1160\u3164\uffa0\u2800")


def _e63_clean(s):
    """What a human reads: NFKC, format/control/private/unassigned characters and invisible fillers dropped, stripped."""
    s = _unicodedata.normalize("NFKC", s)
    return "".join(ch for ch in s if _unicodedata.category(ch) not in ("Cf", "Cc", "Co", "Cn")
                   and ch not in _E63_FILLERS).strip()


def _e63_visible_reason(s):
    """The reason as a human reads it, or "" when nothing readable is left. `_e63_clean` is a denylist, so a reason made of
    other zero-width or mark-only code points (variation selectors, U+034F, Khmer inherent vowels, a lone combining accent,
    U+FFFC, tag characters) would survive it: after cleaning the text must hold at least one letter or digit."""
    cleaned = _e63_clean(s)
    return cleaned if any(ch.isalnum() for ch in cleaned) else ""


def _e63_is_none(detector):
    return isinstance(detector, str) and _e63_clean(detector).upper() == "NONE"


def _e63_relpath_ok(p):
    return (isinstance(p, str) and bool(p) and not p.startswith("/") and "\\" not in p
            and ".." not in p.split("/") and "" not in p.split("/"))


def _e63_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


# ---- the registry, read as source at `ref` -------------------------------------------------------------------------
class _E63Unresolved(Exception):
    pass


def _e63_lit(node, env):
    if isinstance(node, _ast.Constant):
        return node.value
    if isinstance(node, _ast.Tuple):
        return tuple(_e63_lit(e, env) for e in node.elts)
    if isinstance(node, _ast.List):
        return [_e63_lit(e, env) for e in node.elts]
    if isinstance(node, _ast.Set):
        return {_e63_lit(e, env) for e in node.elts}
    if isinstance(node, _ast.Dict):
        if any(k is None for k in node.keys):
            raise _E63Unresolved("dict unpacking")
        return {_e63_lit(k, env): _e63_lit(v, env) for k, v in zip(node.keys, node.values)}
    if isinstance(node, _ast.Name) and node.id in env:
        return env[node.id]
    raise _E63Unresolved(_ast.dump(node)[:80])


def _e63_dictcall(node, wanted, env, what):
    """`dict(k=v, ...)` -> {k: value} for the WANTED keys only; each must be present and evaluable."""
    if not (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name) and node.func.id == "dict"
            and not node.args):
        _e63_fail("registry_unreadable", f"{what} is not a dict(...) call in {E63_CENSUS_PATH}")
    kw = {k.arg: k.value for k in node.keywords if k.arg}
    out = {}
    for key in wanted:
        if key not in kw:
            _e63_fail("registry_unreadable", f"{what} has no `{key}` in {E63_CENSUS_PATH}")
        try:
            out[key] = _e63_lit(kw[key], env)
        except _E63Unresolved as e:
            _e63_fail("registry_unreadable", f"{what}.{key} is not a literal in {E63_CENSUS_PATH} ({e})")
    return out


def _e63_root_name(node):
    while isinstance(node, (_ast.Attribute, _ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, _ast.Name) else None


def _e63_guard_registry_names(tree):
    """Walk the WHOLE module: each guarded registry name is stored exactly once (a module-level assignment) and is
    never mutated, deleted, aliased or written dynamically anywhere, so the literal the parser reads is the value."""
    stores = {n: 0 for n in E63_GUARDED_NAMES}
    for node in _ast.walk(tree):
        bad = None
        if isinstance(node, _ast.Name) and node.id in stores and isinstance(node.ctx, (_ast.Store, _ast.Del)):
            stores[node.id] += 1
            if isinstance(node.ctx, _ast.Del):
                bad = f"`del {node.id}`"
        elif isinstance(node, (_ast.Subscript, _ast.Attribute)) and isinstance(node.ctx, (_ast.Store, _ast.Del)) \
                and _e63_root_name(node) in stores:
            bad = f"a store into {_e63_root_name(node)}"
        elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)) and node.name in stores:
            bad = f"a definition named {node.name}"
        elif isinstance(node, _ast.alias) and (node.asname or node.name.split(".")[0]) in stores:
            bad = f"an import binding {node.asname or node.name}"
        elif isinstance(node, (_ast.Global, _ast.Nonlocal)) and any(n in stores for n in node.names):
            bad = "a global/nonlocal declaration"
        elif isinstance(node, _ast.Call):
            f = node.func
            if isinstance(f, _ast.Attribute) and f.attr in E63_MUTATORS and _e63_root_name(f.value) in stores:
                bad = f"{_e63_root_name(f.value)}.{f.attr}(...)"
            elif isinstance(f, _ast.Name) and f.id in E63_DYNAMIC_CALLS:
                bad = f"a dynamic {f.id}(...) call that could rewrite a registry name"
        elif isinstance(node, (_ast.Assign, _ast.AnnAssign, _ast.NamedExpr)) and isinstance(node.value, _ast.Name) \
                and node.value.id in stores:
            bad = f"an alias of {node.value.id}"
        if bad:
            _e63_fail("registry_unreadable", f"{E63_CENSUS_PATH} contains {bad}: the registry literal the parser reads "
                                             "may not be the value in force")
    top = {st.targets[0].id if isinstance(st, _ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], _ast.Name)
           else getattr(getattr(st, "target", None), "id", None) for st in tree.body
           if isinstance(st, (_ast.Assign, _ast.AnnAssign))}
    for n, c in stores.items():
        if c != 1 or n not in top:
            _e63_fail("registry_unreadable", f"{n} is assigned {c} time(s) in {E63_CENSUS_PATH} (need exactly one "
                                             "module-level assignment)")


def _e63_cap_rule(tree):
    """(prefixes, exact ids) of the criteria `_check_contribution` caps at PARTIAL, read from the `if` that returns
    v=PARTIAL: `crit.startswith("<prefix>")` and `crit == "<id>"` terms. Raises if the pattern is not found."""
    fn = next((n for n in tree.body if isinstance(n, _ast.FunctionDef) and n.name == "_check_contribution"), None)
    if fn is None:
        _e63_fail("registry_unreadable", f"{E63_CENSUS_PATH} has no _check_contribution")
    prefixes, exact = set(), set()
    for node in _ast.walk(fn):
        if not isinstance(node, _ast.If):
            continue
        returns_partial = any(
            isinstance(r, _ast.Return) and isinstance(r.value, _ast.Call) and any(
                k.arg == "v" and isinstance(k.value, _ast.Name) and k.value.id == "PARTIAL" for k in r.value.keywords)
            for r in node.body)
        if not returns_partial:
            continue
        for t in _ast.walk(node.test):
            if isinstance(t, _ast.Call) and isinstance(t.func, _ast.Attribute) and t.func.attr == "startswith" \
                    and isinstance(t.func.value, _ast.Name) and t.func.value.id == "crit" and len(t.args) == 1 \
                    and isinstance(t.args[0], _ast.Constant) and isinstance(t.args[0].value, str):
                prefixes.add(t.args[0].value)
            elif isinstance(t, _ast.Compare) and isinstance(t.left, _ast.Name) and t.left.id == "crit" \
                    and len(t.ops) == 1 and isinstance(t.ops[0], _ast.Eq) and isinstance(t.comparators[0], _ast.Constant) \
                    and isinstance(t.comparators[0].value, str):
                exact.add(t.comparators[0].value)
    if not prefixes and not exact:
        _e63_fail("registry_unreadable", f"no PARTIAL cap rule found in _check_contribution of {E63_CENSUS_PATH}")
    return frozenset(prefixes), frozenset(exact)


@_dc.dataclass(frozen=True)
class RegistryFacts:
    layer_prefix: dict      # "L3" -> "ka_"
    criteria: dict          # "Idem.pattern" -> {gate, layers, detector, revision}
    cell_gates: tuple       # the core gates, in order
    na_rules: dict          # declared N/A rule id -> decision id
    cap_prefixes: frozenset  # a PASS on crit.startswith(p) reads PARTIAL in the census rollup
    cap_exact: frozenset     # ... and on these exact ids

    def required(self, layer):
        """{gate: [criterion, ...]} for the core gates `layer` requires (the rows the census rollup counts)."""
        return {g: sorted(c for c, e in self.criteria.items() if e["gate"] == g and layer in e["layers"])
                for g in self.cell_gates}

    def capped(self, crit):
        return crit in self.cap_exact or any(crit.startswith(p) for p in self.cap_prefixes)

    @property
    def info_families(self):
        return frozenset(e["gate"] for e in self.criteria.values()) - frozenset(self.cell_gates)


def _e63_registry_facts(repo, sha):
    src = _e63_show(repo, sha, E63_CENSUS_PATH)
    try:
        tree = _ast.parse(src.decode("utf-8"), filename=E63_CENSUS_PATH)
    except (SyntaxError, UnicodeDecodeError, ValueError) as e:
        _e63_fail("registry_unreadable", f"{E63_CENSUS_PATH} at {sha[:12]} does not parse ({type(e).__name__})")
    _e63_guard_registry_names(tree)
    env, nodes = {}, {}
    for st in tree.body:
        if isinstance(st, _ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], _ast.Name):
            name, value = st.targets[0].id, st.value
        elif isinstance(st, _ast.AnnAssign) and isinstance(st.target, _ast.Name) and st.value is not None:
            name, value = st.target.id, st.value
        else:
            continue
        nodes[name] = value
        try:
            env[name] = _e63_lit(value, env)
        except _E63Unresolved:
            pass
    for name in ("CELL_GATES", "NA_RULE_DECISIONS"):
        if name not in env:
            _e63_fail("registry_unreadable", f"{name} is not a literal in {E63_CENSUS_PATH}")
    cell_gates, na_rules = env["CELL_GATES"], env["NA_RULE_DECISIONS"]
    if (not isinstance(cell_gates, tuple) or not cell_gates or not all(_e63_nonblank(g) for g in cell_gates)
            or not isinstance(na_rules, dict)
            or not all(_e63_nonblank(k) and _e63_nonblank(v) for k, v in na_rules.items())):
        _e63_fail("registry_unreadable", "CELL_GATES / NA_RULE_DECISIONS have an unexpected shape")
    for name in ("LAYERS", "CRITERION_REGISTRY"):
        if not isinstance(nodes[name], _ast.Dict) or any(k is None for k in nodes[name].keys):
            _e63_fail("registry_unreadable", f"{name} is not a dict literal in {E63_CENSUS_PATH}")
    layer_prefix = {}
    for k, v in zip(nodes["LAYERS"].keys, nodes["LAYERS"].values):
        lk = _e63_lit(k, env)
        layer_prefix[lk] = _e63_dictcall(v, ("prefix",), env, f"LAYERS[{lk!r}]")["prefix"]
    criteria = {}
    for k, v in zip(nodes["CRITERION_REGISTRY"].keys, nodes["CRITERION_REGISTRY"].values):
        ck = _e63_lit(k, env)
        e = _e63_dictcall(v, ("gate", "layers", "detector", "revision"), env, f"CRITERION_REGISTRY[{ck!r}]")
        if (not _e63_nonblank(e["gate"]) or not _e63_nonblank(e["detector"]) or not _e63_int(e["revision"])
                or not isinstance(e["layers"], tuple) or not e["layers"]
                or not all(isinstance(x, str) and x in layer_prefix for x in e["layers"])):
            _e63_fail("registry_unreadable", f"CRITERION_REGISTRY[{ck!r}] has an unexpected shape (layers must be a "
                                             "non-empty tuple of declared layers)")
        criteria[ck] = e
    if not layer_prefix or not all(_e63_nonblank(p) for p in layer_prefix.values()) or not criteria:
        _e63_fail("registry_unreadable", "LAYERS / CRITERION_REGISTRY are empty or malformed")
    cap_prefixes, cap_exact = _e63_cap_rule(tree)
    facts = RegistryFacts(layer_prefix, criteria, cell_gates, na_rules, cap_prefixes, cap_exact)
    _e63_check_floor(facts)
    return facts


def _e63_check_pins(facts):
    for gate, ids in E63_REQUIRED_CRITERIA.items():
        if gate not in facts.cell_gates:
            _e63_fail("registry_below_floor", f"the pinned gate {gate!r} is no longer in CELL_GATES")
        for crit in ids:
            e = facts.criteria.get(crit)
            if e is None:
                _e63_fail("registry_below_floor", f"pinned criterion {crit!r} (gate {gate}) is gone from {E63_CENSUS_PATH}: "
                                                  "removing or renaming a required criterion would make ELEVATED easier; "
                                                  "changing E63_REQUIRED_CRITERIA is a deliberate, reviewed edit")
            if e["gate"] != gate:
                _e63_fail("registry_below_floor", f"pinned criterion {crit!r} moved from gate {gate} to {e['gate']}")
            lost = [L for L in E63_PINNED_LAYERS if L not in e["layers"]]
            if lost:
                _e63_fail("registry_below_floor", f"pinned criterion {crit!r} no longer applies in {lost}")


def _e63_check_floor(facts):
    _e63_check_pins(facts)
    floor = E63_REQUIRED_FLOOR
    stray = sorted(set(floor) - set(facts.cell_gates))
    if stray:
        _e63_fail("registry_below_floor", f"the floor names gate(s) {stray} that CELL_GATES no longer holds")
    for layer in facts.layer_prefix:
        for gate, crits in facts.required(layer).items():
            need = floor.get(gate, 1)
            if len(crits) < need:
                _e63_fail("registry_below_floor", f"{layer}/{gate} requires {len(crits)} criteria in {E63_CENSUS_PATH}, "
                                                  f"below the pinned floor of {need}: removing a core-gate criterion "
                                                  "would make ELEVATED easier, so lowering the floor "
                                                  "(E63_REQUIRED_FLOOR) is a deliberate, reviewed edit")


def _e63_layer_of(asset, facts, where):
    hits = [lk for lk, p in facts.layer_prefix.items() if asset.startswith(p)]
    if len(hits) != 1:
        _e63_fail("malformed", f"{where}: asset {asset!r} matches {len(hits)} layer prefixes (need exactly one)")
    return hits[0]


_E63_GENERATORS = {}
E63_GENERATOR_PATH = E63_CONTROL_DIR + "/generate_level_map.py"


def _e63_generator(repo, sha):
    """generate_level_map.py AS COMMITTED at `ref` (its strict seed parser is the one place the seed is read): the
    parser is read from the ref like every other input, never from the working tree. It is the repository's own tool
    at the commit being judged; a ref without it raises."""
    key = (str(repo), sha)
    if key not in _E63_GENERATORS:
        import types
        src = _e63_show(repo, sha, E63_GENERATOR_PATH)
        mod = types.ModuleType("generate_level_map_at_ref")
        mod.__file__ = str(os.path.join(str(repo), E63_GENERATOR_PATH))     # only its CLI default reads this
        try:
            exec(compile(src, f"{E63_GENERATOR_PATH}@{sha[:12]}", "exec"), mod.__dict__)
        except Exception as e:                       # noqa: BLE001 - any failure to load the ref's tool is unreadable
            _e63_fail("registry_unreadable", f"{E63_GENERATOR_PATH} at {sha[:12]} cannot be loaded ({type(e).__name__}: {e})")
        _E63_GENERATORS[key] = mod
    return _E63_GENERATORS[key]


def _e63_registry_assets(repo, sha):
    """{asset_id: asset_kind or None} the registry holds at `ref`: the seed's ASSETS, plus LEVEL_MAP.json's levels
    when that file is committed (the frozen map of the live registry)."""
    gen = _e63_generator(repo, sha)
    try:
        rows = gen.parse_seed_text(_e63_show(repo, sha, E63_SEED_PATH).decode("utf-8"))
    except (gen.LevelMapError, UnicodeDecodeError) as e:
        _e63_fail("registry_unreadable", f"{E63_SEED_PATH} at {sha[:12]} cannot be read as the registry seed ({e})")
    out = {}
    for r in rows:
        if not _E63_ASSET.fullmatch(r["asset_id"]) or r["asset_id"] in out:
            _e63_fail("registry_unreadable", f"{E63_SEED_PATH}: bad or duplicate asset id {r['asset_id']!r}")
        out[r["asset_id"]] = r["asset_kind"]
    if _e63_exists(repo, sha, E63_LEVEL_MAP_PATH):
        try:
            lm = _e63_strict_loads(_e63_show(repo, sha, E63_LEVEL_MAP_PATH).decode("utf-8"))
            levels = lm["levels"]
            assert isinstance(levels, dict) and all(isinstance(k, str) and _E63_ASSET.fullmatch(k) for k in levels)
        except (ValueError, KeyError, TypeError, AssertionError, UnicodeDecodeError) as e:
            _e63_fail("malformed", f"{E63_LEVEL_MAP_PATH} at {sha[:12]} is not a level map ({type(e).__name__})")
        for k in levels:
            out.setdefault(k, None)
    if not out:
        _e63_fail("registry_unreadable", "the registry holds no asset")
    return out


# ---- the certificate ledger (E5.1 records + E5.5 invalidation and watermark lines) ---------------------------------
@_dc.dataclass
class _Ledger:
    by_key: dict            # cert_key -> [certificate records] in generation order
    pos: dict               # cert_id -> seq of its line
    invalidated: dict       # invalidated cert_id -> its (first) invalidation event
    last_covers: int | None  # the largest covers_seq over all watermark lines (None: no watermark line)
    unevaluated: int        # certificates with seq > the last watermark's covers_seq


def _e63_is_cert_line(r):
    key, gen = r.get("cert_key"), r.get("generation")
    return (isinstance(key, str) and _e63_int(gen) and gen >= 1 and r.get("cert_id") == f"{key}@{gen}"
            and isinstance(r.get("verdict"), str))


def _e63_is_event_line(r):
    t = r.get("type")
    if not isinstance(t, str) or t in E63_CERT_KINDS:
        return False                                 # (an unknown type is refused by the dispatch in _e63_parse_certs)
    if any(k in r for k in E63_EVENT_FORBIDDEN):
        return False
    return not (r.get("kind") in E63_CERT_KINDS or (isinstance(r.get("verdict"), str) and r["verdict"] in E63_VERDICTS))


def _e63_check_cert(r, n, facts):
    where = f"{E63_CERTS_PATH} line {n}"
    asset, kind, crit, verdict = r.get("asset"), r.get("kind"), r.get("criterion"), r.get("verdict")
    if kind not in E63_CERT_KINDS:
        _e63_fail("malformed", f"{where}: a certificate of kind {kind!r}")
    if not (isinstance(asset, str) and _E63_ASSET.fullmatch(asset)):
        _e63_fail("malformed", f"{where}: bad asset {asset!r}")
    if not _e63_nonblank(crit):
        _e63_fail("malformed", f"{where}: criterion must be non-blank")
    if verdict not in E63_VERDICTS:
        _e63_fail("malformed", f"{where}: verdict {verdict!r} is outside {sorted(E63_VERDICTS)}")
    if r["cert_key"] != f"{asset}|{kind}|{crit}":
        _e63_fail("malformed", f"{where}: cert_key does not match asset|kind|criterion")
    layer = r.get("layer")
    if not isinstance(layer, str) or layer not in facts.layer_prefix or _e63_layer_of(asset, facts, where) != layer:
        _e63_fail("malformed", f"{where}: layer {layer!r} does not match asset {asset!r}")
    if not _e63_nonblank(r.get("detector")):
        _e63_fail("malformed", f"{where}: detector is required (NONE is spelled NONE)")
    if not _e63_int(r.get("criterion_version")) or r["criterion_version"] < 1:
        _e63_fail("malformed", f"{where}: criterion_version must be an int >= 1")
    ev = r.get("evidence")
    if not isinstance(ev, dict) or not _e63_nonblank(ev.get("census_run_id")):
        _e63_fail("malformed", f"{where}: evidence.census_run_id is required (a record with no run id is not a record)")
    wh = r.get("writer_hashes", {})
    if not isinstance(wh, dict) or any(not _e63_relpath_ok(p) or not isinstance(h, str)
                                       or not _E63_SHA256.fullmatch(h) for p, h in wh.items()):
        _e63_fail("malformed", f"{where}: writer_hashes must map repo-relative paths to lower-case sha256")
    ups = r.get("upstream_cert_ids", [])
    if not isinstance(ups, list) or any(not isinstance(u, str) or not _E63_CERT_ID.fullmatch(u) for u in ups):
        _e63_fail("malformed", f"{where}: upstream_cert_ids must be a list of cert ids")
    fp = r.get("semantic_fingerprint")
    if fp is not None and not (isinstance(fp, str) and _E63_SHA256.fullmatch(fp)):
        _e63_fail("malformed", f"{where}: semantic_fingerprint must be 64 lower-case hex or null")
    if r.get("na") is not None and not isinstance(r.get("na"), dict):
        _e63_fail("malformed", f"{where}: na must be an object or null")
    if kind == "gate":
        if r.get("cross_checked") is not True:
            _e63_fail("malformed", f"{where}: a gate record must carry cross_checked: true (the writer reads its verdict "
                                   "from the census; a record without that was not written by it)")
        if crit in facts.criteria and r.get("gate") != facts.criteria[crit]["gate"]:
            _e63_fail("malformed", f"{where}: {crit} belongs to gate {facts.criteria[crit]['gate']!r}, not {r.get('gate')!r}")


def _e63_check_invalidation(r, n, cert_pos, facts):
    where = f"{E63_CERTS_PATH} line {n}"
    t = r.get("invalidates")
    if not isinstance(t, str) or t not in cert_pos:
        _e63_fail("malformed", f"{where}: invalidates {t!r}, which is not a certificate on an earlier line")
    target = cert_pos[t]
    reason = r.get("reason")
    if r.get("asset") != target["asset"] or r.get("layer") != target.get("layer") or r.get("layer") not in facts.layer_prefix:
        _e63_fail("malformed", f"{where}: the invalidation does not agree with the certificate it invalidates")
    if (not _e63_int(r.get("walk")) or r["walk"] < 1 or not isinstance(reason, list) or not reason
            or not all(isinstance(x, dict) and _e63_nonblank(x.get("code")) for x in reason)):
        _e63_fail("malformed", f"{where}: an invalidation needs walk >= 1 and a non-empty reason list")


def _e63_check_epoch_reset(r, n, facts):
    d = r.get("decision")
    if (r.get("asset") != "_ledger" or r.get("layer") not in facts.layer_prefix or not isinstance(d, str)
            or not _E63_DECISION.fullmatch(d)):
        _e63_fail("malformed", f"{E63_CERTS_PATH} line {n}: malformed epoch_reset (asset _ledger, a layer, a decision id N-xx)")


def _e63_check_watermark(r, n, certs):
    where = f"{E63_CERTS_PATH} line {n}"
    cov, ep, last = r.get("covers_seq"), r.get("certs_processed"), r.get("last_cert_id")
    if (r.get("asset") != "_ledger" or not _e63_nonblank(r.get("commit")) or not _e63_int(cov) or not _e63_int(ep)):
        _e63_fail("malformed", f"{where}: malformed watermark line")
    if cov < 0 or cov >= n:
        _e63_fail("watermark_mismatch", f"{where}: covers_seq {cov} is outside 0..{n - 1}")
    covered = [c for c in certs if c["seq"] <= cov]
    want_last = covered[-1]["cert_id"] if covered else None
    if ep != len(covered) or last != want_last:
        _e63_fail("watermark_mismatch", f"{where}: the watermark claims {ep} certificate(s) ending {last!r} up to seq "
                                        f"{cov} but the ledger holds {len(covered)} ending {want_last!r}")


_E63_E51_DRIVER = r'''
import json, sys
sys.path.insert(0, ".")
import nikasha_certify as nc
data = sys.stdin.buffer.read()
const = {k: list(getattr(nc, k)) for k in ("CITATION_PASS_REFUSED",)}
const["DECLARATIONS_RELPATH"] = nc.DECLARATIONS_RELPATH
try:
    records = nc.parse_records(data)
    print(json.dumps({"ok": True, "constants": const, "records": records}))
except nc.CertificationRefused as e:
    print(json.dumps({"ok": False, "code": e.code, "message": e.message, "constants": const}))
'''

# In-process memo of E5.1's verdict, keyed by EVERYTHING the verdict depends on (see _e63_e51_validate). A hit replays the very
# verdict (accepted records, or the refusal) that the validator produced for exactly these bytes and this validator text.
_E63_E51_CACHE = {}
_E63_E51_CACHE_MAX = 16


def _e63_e51_key(sha, data, nc_src, census_src):
    return (sha, _e63_sha(data), _e63_sha(nc_src), _e63_sha(census_src), _e63_sha(_E63_E51_DRIVER.encode("utf-8")))


def _e63_e51_run(sha, data, nc_src, census_src):
    """Run E5.1's validator (the ref's own nikasha_certify.py + asset_census.py, written to a temporary directory) in a
    subprocess on the ledger bytes. -> the validator's answer: {"ok", "constants", "records" | "code"/"message"}. Anything but
    an answer (cannot run, no output) raises and is never cached."""
    import shutil
    import tempfile
    d = tempfile.mkdtemp(prefix="e63_e51_")
    try:
        with open(os.path.join(d, "nikasha_certify.py"), "wb") as f:
            f.write(nc_src)
        with open(os.path.join(d, "asset_census.py"), "wb") as f:
            f.write(census_src)
        try:
            r = subprocess.run([sys.executable, "-c", _E63_E51_DRIVER], input=data, capture_output=True, cwd=d, timeout=120,
                               env={k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONSTARTUP")})
        except (OSError, subprocess.SubprocessError) as e:
            _e63_fail("registry_unreadable", f"E5.1's validator at {sha[:12]} could not be run ({type(e).__name__}: {e})")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    try:
        out = json.loads(r.stdout.decode("utf-8").strip().splitlines()[-1])
        out["constants"]
        out["ok"]
    except (ValueError, IndexError, KeyError, TypeError, UnicodeDecodeError):
        _e63_fail("registry_unreadable", f"E5.1's validator at {sha[:12]} did not answer ({r.stderr.decode('utf-8', 'replace')[-200:]})")
    if out["ok"] is True and not isinstance(out.get("records"), list):
        _e63_fail("registry_unreadable", f"E5.1's validator at {sha[:12]} accepted the ledger but returned no records")
    return out


def _e63_e51_validate(repo, sha, data):
    """E5.1's OWN validator, loaded from the same ref, is the single definition of what a certificate ledger is: the chain,
    seq, generations, record_version, citation_state / caveat and the declarations binding are read ONLY there (this reader
    holds no copy of those rules). -> the validator's records (every certificate and event line in file order, citation and
    declarations fields normalised as E5.1 reads them); a ledger E5.1 refuses raises here (`malformed`). A ref without the
    validator, or a validator that cannot run or does not answer, raises (fail closed). The validator's constants this reader
    still relies on (CITATION_PASS_REFUSED, DECLARATIONS_RELPATH) must equal the reader's own: a mismatch raises.

    CACHE (per process). The verdict is a pure function of (the validator's text, the ledger bytes), so it is memoised under
    (ref sha, sha256(ledger bytes), sha256(nikasha_certify.py at the ref), sha256(asset_census.py at the ref), sha256(driver)).
    The validator files and the ledger are READ and HASHED on every call (a ref without them raises before any lookup); a
    changed ledger byte, a changed validator file or another ref is a different key, so it re-runs the validator. A refusal is
    cached AS a refusal (replayed as the same ElevatedInputError), never as an acceptance; a run that gave no answer is not
    cached. Records are returned as a deep copy, and the constants check runs on every call, hit or miss."""
    nc_src = _e63_show(repo, sha, E63_E51_PATH)
    census_src = _e63_show(repo, sha, E63_CENSUS_PATH)
    key = _e63_e51_key(sha, data, nc_src, census_src)
    out = _E63_E51_CACHE.get(key)
    if out is None:
        out = _e63_e51_run(sha, data, nc_src, census_src)
        while len(_E63_E51_CACHE) >= _E63_E51_CACHE_MAX:
            _E63_E51_CACHE.pop(next(iter(_E63_E51_CACHE)))
        _E63_E51_CACHE[key] = out
    const = out["constants"]
    mine = {"CITATION_PASS_REFUSED": list(E63_CITATION_BLOCKING), "DECLARATIONS_RELPATH": E63_DECLARATIONS_PATH}
    if const != mine:
        diff = sorted(k for k in mine if mine[k] != const.get(k))
        _e63_fail("registry_unreadable", f"E5.1 at {sha[:12]} and this reader disagree on {diff}: a rule one side changed "
                                         "(edit the E63_* constants deliberately to match)")
    if not out["ok"]:
        _e63_fail("malformed", f"{E63_CERTS_PATH}: E5.1's own reader refuses this ledger ({out['code']}): {out['message']}")
    return _copy.deepcopy(out["records"])


def _e63_parse_certs(records, facts):
    """-> _Ledger, from the records E5.1's validator accepted (chain, seq, generations, citation and declarations fields are
    already settled there). Added here: the generic certificate field checks against the registry, E5.5's event shapes and
    a truthful watermark; anything else raises."""
    led = _Ledger(by_key={}, pos={}, invalidated={}, last_covers=None, unevaluated=0)
    certs, cert_by_id = [], {}
    for r in records:
        n = r["seq"]
        where = f"{E63_CERTS_PATH} record {n}"
        is_cert = "type" not in r and _e63_is_cert_line(r)       # a line that names a `type` is an event or invalid
        if not is_cert and not _e63_is_event_line(r):
            _e63_fail("malformed", f"{where}: not a record this reader can trust (a certificate needs cert_key/"
                                   "generation/cert_id/verdict; any other line needs a `type` in "
                                   f"{E63_EVENT_TYPES} and no certificate field)")
        if is_cert:
            _e63_check_cert(r, n, facts)
            led.pos[r["cert_id"]] = r["seq"]
            cert_by_id[r["cert_id"]] = r
            led.by_key.setdefault(r["cert_key"], []).append(r)
            certs.append(r)
        elif r["type"] == "invalidation":
            _e63_check_invalidation(r, n, cert_by_id, facts)
            led.invalidated.setdefault(r["invalidates"], r)
        elif r["type"] == "watermark":
            _e63_check_watermark(r, r["seq"], certs)
            led.last_covers = max(led.last_covers or 0, r["covers_seq"])      # E5.5: the furthest evaluation counts
        elif r["type"] == "epoch_reset":
            _e63_check_epoch_reset(r, n, facts)
        else:
            _e63_fail("malformed", f"{where}: unknown event type {r['type']!r}")
    cov = led.last_covers if led.last_covers is not None else 0
    led.unevaluated = sum(1 for c in certs if c["seq"] > cov)
    return led


# ---- gaps and dispositions -----------------------------------------------------------------------------------------
def _e63_parse_gaps(data, known, facts, additions):
    """The EFFECTIVE gap rows. Keyed (asset, gap_id): the latest row wins; a row with no gap_id stands alone; a row
    folded by `superseded_by` (same asset, chains resolved, a cycle or a dangling target raises) is carried by the
    chain's terminal row."""
    rows = _e63_lines(data, E63_GAPS_PATH)
    latest, loose, first = {}, [], {}
    for n, _raw, r in rows[1:]:
        where = f"{E63_GAPS_PATH} line {n}"
        asset = r.get("asset")
        if isinstance(asset, str) and asset in E63_PSEUDO_GAP_ASSETS:
            continue
        if not isinstance(asset, str) or asset not in known:
            _e63_fail("malformed", f"{where}: asset {asset!r} is not a known asset (certificates, dispositions or the "
                                   "registry; this also rejects malformed ids and look-alikes of real ones): a gap "
                                   "on it would be silently ignored")
        kind = r.get("kind", "gap")
        state = str(r.get("state", "OPEN")).upper()
        if kind not in E63_GAP_KINDS:
            _e63_fail("malformed", f"{where}: kind {kind!r} is outside {sorted(E63_GAP_KINDS)}")
        if state not in E63_GAP_STATES:
            _e63_fail("malformed", f"{where}: state {r.get('state')!r} is outside {sorted(E63_GAP_STATES)}")
        crit = r.get("criterion", "")
        if not isinstance(crit, str):
            _e63_fail("malformed", f"{where}: criterion must be text")
        gid, sup = r.get("gap_id"), r.get("superseded_by")
        if (gid is not None and not _e63_nonblank(gid)) or (sup is not None and not _e63_nonblank(sup)):
            _e63_fail("malformed", f"{where}: gap_id / superseded_by must be non-blank text when present")
        eff = dict(asset=asset, kind=kind, state=state, criterion=crit, gap_id=gid, superseded_by=sup, line=n)
        if gid:
            # a gap's identity is (asset, gap_id, criterion, kind) as FIRST written: a later row may change its state,
            # never what it is about or whether it blocks (re-keying an open core-gate gap to `opportunity` or to a
            # non-gate family would make it vanish)
            f = first.setdefault((asset, gid), (kind, crit, n))
            if (kind, crit) != f[:2]:
                _e63_fail("malformed", f"{where}: gap {gid!r} of {asset} was first written as kind {f[0]!r}, criterion "
                                       f"{f[1]!r} (line {f[2]}) and may not change to kind {kind!r}, criterion {crit!r}")
            latest[(asset, gid)] = eff
        else:
            loose.append(eff)
    out = []
    for g in loose + list(latest.values()):
        if not g["superseded_by"]:
            out.append(g)
            continue
        seen, cur = {(g["asset"], g["gap_id"])}, g
        while cur["superseded_by"]:
            nxt = (cur["asset"], cur["superseded_by"])
            if nxt in seen:
                _e63_fail("malformed", f"{E63_GAPS_PATH} line {g['line']}: superseded_by forms a cycle at {nxt[1]!r}")
            if nxt not in latest:
                _e63_fail("malformed", f"{E63_GAPS_PATH} line {g['line']}: superseded_by {cur['superseded_by']!r} names "
                                       f"no gap_id of asset {g['asset']}")
            seen.add(nxt)
            tgt = latest[nxt]
            adds = additions.get(cur["asset"], ())
            origin_can_block = (cur["criterion"].split(".", 1)[0] not in facts.info_families
                                or any(cur["criterion"] == a or cur["criterion"].startswith(a + ".") for a in adds))
            if origin_can_block:
                same_family = tgt["criterion"].split(".", 1)[0] == cur["criterion"].split(".", 1)[0]
                same_addition = any(cur["criterion"] == a or cur["criterion"].startswith(a + ".") for a in adds) and any(
                    tgt["criterion"] == a or tgt["criterion"].startswith(a + ".") for a in adds)
                registered = tgt["criterion"] in facts.criteria
                # the real ledger folds a renamed criterion within ONE gate (Vocab.rule1.alias -> Vocab.alias, R79) and
                # non-gate rows among themselves (Complete.depth -> Completeness.*); a fold of a row that CAN block (a
                # core-gate row or a declared addition's) must land on a kind=gap row of a REGISTERED criterion of the
                # same gate (or the same declared addition), never another gate, an opportunity or an unregistered id
                if (tgt["kind"] != "gap" or cur["kind"] != "gap" or not ((same_family and registered) or same_addition)):
                    _e63_fail("malformed", f"{E63_GAPS_PATH} line {cur['line']}: a gap that can block may only be folded "
                                           f"into a kind=gap row of a registered criterion of the same gate or of the "
                                           f"same declared addition ({cur['criterion']!r} -> {tgt['criterion']!r}, "
                                           f"{cur['kind']} -> {tgt['kind']})")
            cur = tgt
        if g["state"] not in E63_CLOSED_GAP_STATES and cur["state"] in E63_CLOSED_GAP_STATES and (
                g["criterion"].split(".", 1)[0] not in facts.info_families
                or any(g["criterion"] == a or g["criterion"].startswith(a + ".") for a in additions.get(g["asset"], ()))):
            _e63_fail("malformed", f"{E63_GAPS_PATH} line {g['line']}: an OPEN gap that can block was folded into a "
                                   f"{cur['state']} row ({cur['gap_id']!r}): its open state must not vanish by folding")
        # folded: the terminal row (a member of `latest`) is counted on its own
    return out


def _e63_parse_dispositions(data, facts, registry):
    """asset -> {disposition (as written), effective (`unresolved` unless the line carries a decision id), reason,
    decision_id, additions (the UNION over every row)}. Chained exactly like the certificate ledger (`seq`,
    `prev_sha256`); a line is {asset, disposition, reason, decision_id, decided_on, additions}. The LATEST row governs
    the disposition; a row without a decision id (null) reads `unresolved`; a malformed decision id raises."""
    rows = _e63_lines(data, E63_DISPOSITIONS_PATH)
    latest, adds = {}, {}
    prev, nrec = _e63_sha(rows[0][1]), 0
    for n, raw, r in rows[1:]:
        where = f"{E63_DISPOSITIONS_PATH} line {n}"
        if r.get("asset") == "_schema":
            _e63_fail("malformed", f"{where}: a second `_schema` row")
        _e63_chain_check(r, where, nrec, prev)
        prev, nrec = _e63_sha(raw), nrec + 1
        asset, disp = r.get("asset"), r.get("disposition")
        if not (isinstance(asset, str) and _E63_ASSET.fullmatch(asset)):
            _e63_fail("malformed", f"{where}: bad asset {asset!r}")
        _e63_layer_of(asset, facts, where)
        if asset not in registry:
            _e63_fail("malformed", f"{where}: asset {asset!r} is not in the registry")
        if disp not in E63_DISPOSITIONS:
            _e63_fail("malformed", f"{where}: disposition {disp!r} is outside {sorted(E63_DISPOSITIONS)}")
        if r.get("reason") is not None and not isinstance(r.get("reason"), str):
            _e63_fail("malformed", f"{where}: reason must be text")
        for key in ("decision_id", "decided_on", "additions"):
            if key not in r:
                _e63_fail("malformed", f"{where}: `{key}` is required on every row (decision_id may be null: that reads "
                                       "`unresolved`; an empty additions list is the honest 'none declared')")
        dec = r["decision_id"]
        if dec is not None and not (isinstance(dec, str) and _E63_DECISION.fullmatch(dec)):
            _e63_fail("malformed", f"{where}: decision_id {dec!r} is not a decision id (N-<n>...) or null")
        try:
            aware = isinstance(r["decided_on"], str) and _dt.datetime.fromisoformat(r["decided_on"]).tzinfo is not None
        except ValueError:
            aware = False
        if not aware:
            _e63_fail("malformed", f"{where}: decided_on must be a timezone-aware ISO-8601 timestamp")
        a = r["additions"]
        if (not isinstance(a, list) or any(not isinstance(x, str) or not _E63_ADDITION.fullmatch(x)
                                           or x in facts.criteria for x in a) or len(set(a)) != len(a)):
            _e63_fail("malformed", f"{where}: additions must be unique addition ids that do not shadow a registered criterion")
        adds.setdefault(asset, set()).update(a)
        latest[asset] = dict(disposition=disp, effective=disp if dec is not None else "unresolved",
                             reason=_e63_visible_reason(r.get("reason") or ""), decision_id=dec)
    return {a: dict(d, additions=tuple(sorted(adds[a]))) for a, d in latest.items()}


# ---- currency ----------------------------------------------------------------------------------------------------
class LedgerState:
    """What `is_current` reads: the certificate ledger at one resolved commit, with E5.5's invalidations."""

    def __init__(self, repo, sha, facts, by_key, invalidated, pos=None, kinds=None):
        self.repo, self.sha, self.facts = repo, sha, facts
        self.by_key, self.invalidated = by_key, invalidated
        self.pos = pos if pos is not None else {r["cert_id"]: i for i, rs in enumerate(by_key.values()) for r in rs}
        self.kinds = kinds or {}
        self._hash_cache, self._cur_cache, self._decl = {}, {}, None

    @property
    def declarations_sha256(self):
        """sha256 of the BYTES of asset_declarations.json at the ledger commit (E5.1's definition: the blob at the ref).
        An unreadable file raises: no certificate can be judged current without it (fail closed)."""
        if self._decl is None:
            self._decl = _e63_sha(_e63_show(self.repo, self.sha, E63_DECLARATIONS_PATH))
        return self._decl

    def writer_sha256(self, path):
        """sha256 of `path` at the ledger commit, or None when the file is absent there."""
        if path not in self._hash_cache:
            try:
                self._hash_cache[path] = _hashlib.sha256(_e63_show(self.repo, self.sha, path)).hexdigest()
            except ElevatedInputError:
                self._hash_cache[path] = None
        return self._hash_cache[path]


def certificate_currency(rec, state):
    """(True, None) when `rec` is CURRENT, else (False, why). An upstream must sit on an EARLIER line, so the citation
    graph is acyclic by construction and the recursion terminates."""
    cid = rec["cert_id"]
    if cid not in state._cur_cache:
        state._cur_cache[cid] = _e63_currency(rec, state)
    return state._cur_cache[cid]


def is_current(rec, state):
    return certificate_currency(rec, state)[0]


def _e63_currency(rec, state):
    latest = state.by_key[rec["cert_key"]][-1]
    if rec["generation"] != latest["generation"]:
        return False, f"generation {rec['generation']} is not the latest ({latest['generation']})"
    if rec["cert_id"] in state.invalidated:
        return False, "invalidated by E5.5"
    if rec["kind"] == "gate" and rec["declarations_sha256"] != state.declarations_sha256:
        if rec["declarations_sha256"] is None:
            return False, "the gate certificate is not bound to a declarations file (legacy or unbound)"
        return False, "certified against declarations that are not the ones at the ref"
    for path, recorded in rec.get("writer_hashes", {}).items():
        if state.writer_sha256(path) != recorded:
            return False, f"writer file {path} no longer hashes to the certified sha256"
    measured = rec["verdict"] == "PASS" or (rec["verdict"] == "N/A" and (rec.get("na") or {}).get("basis") == "measured_cause")
    if measured and rec.get("semantic_fingerprint") is None:
        return False, "a measured verdict carries no semantic fingerprint, so a row change could never invalidate it"
    if measured and not rec.get("writer_hashes") and not _e63_nonblank(rec.get("writer_hashes_reason")):
        return False, "no writer hashes and no stated reason for having none"
    if rec["kind"] == "gate" and rec["criterion"] in state.facts.criteria:
        if rec.get("criterion_version") != state.facts.criteria[rec["criterion"]]["revision"]:
            return False, "the criterion's registry revision moved since this was measured"
    for uid in rec.get("upstream_cert_ids", []):
        m = _E63_CERT_ID.fullmatch(uid)
        ukey, ugen = f"{m.group(1)}|{m.group(2)}|{m.group(3)}", int(m.group(4))
        urecs = state.by_key.get(ukey)
        if not urecs or ugen > len(urecs):
            _e63_fail("malformed", f"{rec['cert_id']}: upstream {uid} is not in the certificate ledger")
        if state.pos[uid] >= state.pos[rec["cert_id"]]:
            _e63_fail("malformed", f"{rec['cert_id']}: upstream {uid} is not on an earlier line")
        up = urecs[-1]
        if ugen != len(urecs):
            cited = urecs[ugen - 1]
            # E5.5: a generation bump with the SAME semantic fingerprint leaves the dependant's premise unchanged
            if cited.get("semantic_fingerprint") is None or cited.get("semantic_fingerprint") != up.get("semantic_fingerprint"):
                return False, f"upstream {uid} has a newer generation ({len(urecs)}) with different output"
        ok, why = certificate_currency(up, state)
        if not ok:
            return False, f"upstream {uid} is not current ({why})"
        if up["verdict"] not in ("PASS", "N/A"):
            return False, f"upstream {uid} reads {up['verdict']}"
    return True, None


def _e63_satisfies(rec, state, addition):
    """Does this latest record count as a current PASS (or a registry-computed N/A, gates only)?"""
    if not is_current(rec, state):
        return False
    if rec.get("inconclusive"):
        return False
    v, crit = rec["verdict"], rec["criterion"]
    basis = rec.get("basis")
    if basis is not None:
        kinds = E63_DECLARATION_BASED.get(crit)
        if (basis != E63_BASIS_DECLARATION or addition or kinds is None
                or state.kinds.get(rec["asset"]) not in kinds):
            return False             # an unrecognised basis, or `declaration` where the registry does not define it
    if v == "PASS":
        if _e63_is_none(rec["detector"]) or (
                not addition and _e63_is_none(state.facts.criteria.get(crit, {}).get("detector", ""))):
            return False            # detector NONE never reaches PASS (the record's own, or the registry's)
        if not addition and state.facts.capped(crit):
            return False            # capped at PARTIAL by the census rollup (Null: never PASS alone)
        return True
    if v == "N/A" and not addition:
        na = rec.get("na") or {}
        rid = na.get("rule_id")
        return (isinstance(rid, str) and rid.startswith(crit + "#") and _e63_nonblank(na.get("decision_id"))
                and state.facts.na_rules.get(rid) == na["decision_id"])
    return False


def _e63_gap_blocks(g, additions, info_families):
    if g["kind"] != "gap" or g["state"] in E63_CLOSED_GAP_STATES:
        return False
    crit = g["criterion"]
    if any(crit == a or crit.startswith(a + ".") for a in additions):
        return True
    return crit.split(".", 1)[0] not in info_families


def _e63_stale_declaration_cells(state, asset=None):
    """The LATEST gate certificates (of `asset`, or of every asset) whose declarations_sha256 is not the one at the ref:
    [{asset, criterion, cert_id, recorded_sha256, recorded_version, at_ref_sha256, reason}] with reason "unbound" (null:
    legacy, v1 or pre-binding) or "stale" (certified against other declarations)."""
    out = []
    for key in sorted(state.by_key):
        rec = state.by_key[key][-1]
        if rec["kind"] != "gate" or (asset is not None and rec["asset"] != asset):
            continue
        if rec["declarations_sha256"] != state.declarations_sha256:
            out.append(dict(asset=rec["asset"], criterion=rec["criterion"], cert_id=rec["cert_id"],
                            recorded_sha256=rec["declarations_sha256"], recorded_version=rec["declarations_version"],
                            at_ref_sha256=state.declarations_sha256,
                            reason="unbound" if rec["declarations_sha256"] is None else "stale"))
    return out


def _e63_asset_report(asset, state, disp, gaps):
    """None when the asset is not elevated, else HOW it is: {basis: "terminal_disposition" | "measured",
    declaration_based_pass_cells, ruled_na_cells, citation_states, citation_caveat, declarations_current,
    stale_declaration_cells, terminal}."""
    d = disp.get(asset)
    if d is not None and d["effective"] in E63_TERMINAL_DISPOSITIONS and d["reason"]:       # TERMINAL (decision id + reason)
        return dict(basis="terminal_disposition", declaration_based_pass_cells=0, ruled_na_cells=[],
                    citation_states={}, citation_caveat=False, declarations_current=True, stale_declaration_cells=[],
                    terminal=dict(disposition=d["effective"], reason=d["reason"], decision_id=d["decision_id"]))
    if d is None or d["effective"] == "unresolved":                                          # (4)
        return None
    layer = _e63_layer_of(asset, state.facts, f"asset {asset}")
    declared, ruled, cit_states, caveat = 0, [], {}, False
    for gate, crits in state.facts.required(layer).items():                                  # (1) (the floor: crits != [])
        for c in crits:
            rec = (state.by_key.get(f"{asset}|gate|{c}") or [None])[-1]
            if rec is None or not _e63_satisfies(rec, state, addition=False):
                return None
            if rec["verdict"] == "N/A":
                ruled.append(dict(criterion=c, rule_id=rec["na"]["rule_id"], decision_id=rec["na"]["decision_id"]))
            else:
                if rec.get("basis") == E63_BASIS_DECLARATION:
                    declared += 1
                if rec["citation_state"] is not None:          # (the reader allows a state only on a citation gate)
                    cit_states[c] = rec["citation_state"]
                caveat = caveat or rec["citation_state_caveat"] is True
    for a in d["additions"]:                                                                 # (2)
        rec = (state.by_key.get(f"{asset}|addition|{a}") or [None])[-1]
        if rec is None or not _e63_satisfies(rec, state, addition=True):
            return None
    if any(_e63_gap_blocks(g, d["additions"], state.facts.info_families) for g in gaps.get(asset, ())):   # (3)
        return None
    stale = _e63_stale_declaration_cells(state, asset)          # an elevated asset's REQUIRED cells are current; others may not be
    return dict(basis="measured", declaration_based_pass_cells=declared, ruled_na_cells=ruled,
                citation_states=dict(sorted(cit_states.items())), citation_caveat=caveat,
                declarations_current=not stale, stale_declaration_cells=stale, terminal=None)


def _e63_check_info_rekeys(gap_rows, disp, facts):
    """A core-gate (or declared-addition) gap re-keyed `kind: info` would stop blocking: raise instead."""
    for g in gap_rows:
        if g["kind"] != "info":
            continue
        adds = disp.get(g["asset"], {}).get("additions", ())
        if g["criterion"].split(".", 1)[0] in facts.cell_gates or any(
                g["criterion"] == a or g["criterion"].startswith(a + ".") for a in adds):
            _e63_fail("malformed", f"{E63_GAPS_PATH} line {g['line']}: {g['criterion']!r} is a core-gate or declared-"
                                   "addition criterion, which may not be re-keyed to kind: info")


def _e63_load(ref, repo):
    """Everything both public functions read, once: (ledger state, dispositions, gaps by asset, population)."""
    sha = _e63_resolve_ref(ref, repo)
    facts = _e63_registry_facts(repo, sha)
    registry = _e63_registry_assets(repo, sha)
    records = _e63_e51_validate(repo, sha, _e63_show(repo, sha, E63_CERTS_PATH))     # E5.1's validator, same ref, has the word
    led = _e63_parse_certs(records, facts)
    if led.last_covers is None:
        _e63_fail("watermark_missing", "the certificate ledger carries no watermark line: E5.5 has never evaluated it")
    if led.unevaluated:
        raise WatermarkOlderThanLedger("watermark_older", f"{led.unevaluated} certificate record(s) follow the last "
                                                          "watermark: E5.5 has not evaluated them")
    disp = _e63_parse_dispositions(_e63_show(repo, sha, E63_DISPOSITIONS_PATH), facts, registry)
    known = set(registry) | set(disp) | {k.split("|", 1)[0] for k in led.by_key}
    gap_rows = _e63_parse_gaps(_e63_show(repo, sha, E63_GAPS_PATH), known, facts, {a: d["additions"] for a, d in disp.items()})
    _e63_check_info_rekeys(gap_rows, disp, facts)
    gaps = {}
    for g in gap_rows:
        gaps.setdefault(g["asset"], []).append(g)
    state = LedgerState(repo, sha, facts, led.by_key, led.invalidated, led.pos, registry)
    state.declarations_sha256                      # a missing declarations file at the ref raises, whatever the ledger holds
    return state, disp, gaps, {k.split("|", 1)[0] for k in led.by_key} | set(disp)


def elevated_report(ref: str, repo: str) -> dict:
    """Which assets are ELEVATED and HOW, as of the ledgers committed at `ref`: {asset: {basis, ...}}.

    basis "measured": every core gate (and declared addition) by a current measured PASS or a ruled N/A;
    `declaration_based_pass_cells` counts the PASS-by-declaration cells among them and `ruled_na_cells` lists the N/A
    cells with their rule and decision ids. basis "terminal_disposition": retire/consolidate, honoured only when its line
    carries a decision id and a visible reason (`terminal` = {disposition, reason, decision_id}). The two are never
    summed into one flat figure by this function: a dashboard shows "elevated by measurement" and "closed by
    retirement" separately.

    DECLARATIONS BINDING (N-74 add-on). A gate certificate is CURRENT only if its `declarations_sha256` equals the sha256 of
    the bytes of platform/scripts/governance/asset_declarations.json AT `ref` (E5.1's definition); a null or absent one (v1,
    pre-binding, legacy) is not current; an addition carries none and is judged as before; a missing declarations file at
    the ref raises. `declarations_current` is false and `stale_declaration_cells` lists the asset's latest gate
    certificates bound to other declarations (informational for an elevated asset: its required cells are current by
    construction); `stale_declaration_cells(ref, repo)` lists them for every asset.

    CITATION STATE (N-74). E5.1 record_version 2 carries `citation_state` (sourced | sourced_ocr_unverified | unsourced |
    refuted; null when not declared or not applicable; v1 records read as null, caveat false). `citation_states` maps
    the asset's Carr.D1 / Ldgr.source_presence PASS cells that carry a non-null state to it; `citation_caveat` is true when
    ANY of its PASS cells carries the writer's `citation_state_caveat` (a citation-criterion PASS whose state is not
    `sourced`: that includes `sourced_ocr_unverified` AND a null-state Ldgr.source_presence PASS, which still counts), so
    a dashboard can show "ELEVATED on OCR-only or undeclared citations" on its own. A cell whose state is `unsourced` or
    `refuted` is never a PASS (the census caps it at NO_DETECTOR; a PASS line carrying one raises as a bad ledger);
    `citation_blocked_cells` lists such current cells.

    Reads only `git -C repo show <ref>:<path>`; never the working tree or a database; no side effects. Raises
    ElevatedInputError (WatermarkOlderThanLedger when E5.5's watermark does not cover every certificate) on any
    unreadable or malformed input. One bad record anywhere (even a superseded generation) makes both functions raise: fail
    closed, as E5.1's reader does.
    """
    state, disp, gaps, population = _e63_load(ref, repo)
    out = {}
    for a in sorted(population):
        rep_ = _e63_asset_report(a, state, disp, gaps)
        if rep_ is not None:
            out[a] = rep_
    return out


def stale_declaration_cells(ref: str, repo: str) -> list:
    """Every LATEST gate certificate that is not current because of the declarations binding (SS N-74 add-on):
    [{asset, criterion, cert_id, recorded_sha256, recorded_version, at_ref_sha256, reason}], reason "stale" (certified
    against declarations other than asset_declarations.json at `ref`) or "unbound" (null sha: v1, pre-binding or legacy
    records). Such a cell is never current, so its asset is simply absent from `elevated_report`; this is how a dashboard
    shows "certified against old declarations". Same inputs, same raises (a missing declarations file raises)."""
    state, _disp, _gaps, _pop = _e63_load(ref, repo)
    return _e63_stale_declaration_cells(state)


def citation_blocked_cells(ref: str, repo: str) -> list:
    """The current certificates whose citation state is `unsourced` or `refuted` (N-74): [{asset, criterion, cert_id,
    verdict, citation_state}]. The census caps such a cell at NO_DETECTOR (E5.1 refuses a PASS carrying one), so this is
    how a withheld ELEVATED is explained: the asset is simply absent from `elevated_report`, and this says why. Same
    inputs, same raises."""
    state, _disp, _gaps, _pop = _e63_load(ref, repo)
    out = []
    for key in sorted(state.by_key):
        rec = state.by_key[key][-1]
        if rec.get("citation_state") in E63_CITATION_BLOCKING and is_current(rec, state):
            out.append(dict(asset=rec["asset"], criterion=rec["criterion"], cert_id=rec["cert_id"],
                            verdict=rec["verdict"], citation_state=rec["citation_state"]))
    return out


def elevated_assets(ref: str, repo: str) -> set:
    """The asset ids ELEVATED (plan 1.1) or terminally dispositioned: exactly the keys of `elevated_report` (one
    implementation, so the two cannot disagree). Same inputs, same raises."""
    return set(elevated_report(ref, repo))


if __name__=="__main__": main()
