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
# T3 sandbox variant: ledger/output paths overridable so a sandbox run never reads or writes
# the production control directory.
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

# The certified gates. Eight, not thirty-three. A gate is a CLAIM WITH A DETECTOR THAT COULD RETURN
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
 ("Build","buildability",          "always",      "the orchestrator can dispatch the asset and a triggered rebuild produces the correct result — six static checks plus a dry-run proof"),
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

def registry(env_file, layer_key):
    """Live asset_registry rows for the layer. Returns (rows, reason_if_unavailable)."""
    dsn=None
    if env_file and os.path.exists(env_file):
        for line in io.open(env_file,encoding="utf-8",errors="replace"):
            if line.strip().startswith("DATABASE_URL="):
                dsn=line.strip().split("=",1)[1].strip().strip('"').strip("'"); break
    dsn = dsn or os.environ.get("DATABASE_URL")
    if not dsn: return {}, "no DATABASE_URL — registry and production columns not read"
    try: import psycopg2
    except ImportError: return {}, "psycopg2 not installed"
    cfg=LAYERS[layer_key]
    try:
        conn=psycopg2.connect(dsn); conn.set_session(readonly=True, autocommit=False); cur=conn.cursor()
        cur.execute("""SELECT asset_id, target_table, storage_type, scope, is_active, catalog_status,
                              has_writer, COALESCE(depends_on,'{}'), count_sql,
                              (integrity_check_sql IS NOT NULL AND length(integrity_check_sql)>0)
                       FROM asset_registry WHERE layer=%s OR asset_id LIKE %s
                       ORDER BY sort_order, asset_id""",(cfg["registry_layer"], cfg["prefix"].replace("_","\\_")+"%"))
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
        return rows, None
    except Exception as e:
        return {}, "registry read failed: %s"%type(e).__name__

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
    # T3 closing semantics: a gap_id's state is its LATEST row (append-only ledger, closure is a
    # later CLOSED row, regression a later OPEN row). Rows without a gap_id are per-row facts.
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
        cfg=LAYERS[lk]; rows,reason=registry(env_file,lk)
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
            instance=cfg["instance"],registry_reason=reason,n_assets=len(assets),assets=assets)
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

if __name__=="__main__": main()
