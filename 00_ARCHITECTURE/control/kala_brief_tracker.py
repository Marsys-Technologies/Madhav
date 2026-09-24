#!/usr/bin/env python3
"""Kāla (L3) elevation tracker — DAG-ordered lifecycle + brief-criteria coverage.

This is the STRATEGY session's instrument. It does not execute anything: it reads
the repo and the append-only elevation ledger, and reports where each of the 22
assets stands.

    python3 00_ARCHITECTURE/control/kala_brief_tracker.py            # one pass
    python3 00_ARCHITECTURE/control/kala_brief_tracker.py --watch    # rescan every 10s

Outputs kala_brief_tracker.{json,js} next to kala_brief_tracker.html, which polls
the .js and repaints. Nothing here writes to a brief, a table or a database.

Two orderings matter and they are not the same:
  * DAG order (default) — upstream before downstream, so an asset is only elevated
    after everything it depends on is. Source of truth for edges is the ka_* block
    of platform/scripts/seed/asset_registry_seed.ts (asset_registry.depends_on).
  * Registry order — the historical 1..22 numbering of the brief-state table.

A criteria tick means the brief ADDRESSES the criterion (marker detection), never
that it addresses it correctly.
"""
import argparse, collections, datetime, glob, io, json, os, re, subprocess, time

ROOT   = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip() or "."
BR     = os.path.join(ROOT,"00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs")
CTRL   = os.path.join(ROOT,"00_ARCHITECTURE/control")
OUT    = os.path.join(CTRL,"kala_brief_tracker.json")
LEDGER = os.path.join(CTRL,"kala_elevation_ledger.jsonl")
SEED   = os.path.join(ROOT,"platform/scripts/seed/asset_registry_seed.ts")

TIERS = {
 "T1":("Ten analysis lenses",[
   ("A","identity",r"\bidentity\b|asset[- ]id|epistemic"),("B","inputs / DAG",r"\bDAG\b|upstream|declared input"),
   ("C","correctness",r"invariant|correctness"),("D","data sufficiency",r"data sufficien|coverage|row count"),
   ("E","consumers",r"consumer|downstream|reader"),("F","AI / product",r"product|AI|serving question"),
   ("G","efficiency",r"efficienc|cost|latency|hotspot"),("H","reliability",r"reliab|idempoten|timeout|failure"),
   ("I","change packet",r"may_touch|change packet|files"),("J","final evidence",r"evidence|proof|detector")]),
 "T2":("Six elevation lenses",[
   ("Val","value extraction",r"latent[- ]value|value extraction"),("Tgt","target-state design",r"target[- ]state|disposition and target"),
   ("Eff","efficiency w/ quality",r"equivalen|justified no-change|no measured hotspot|cost"),
   ("Syn","synergy obligations",r"OFFERS|DEMANDS|synergy oblig"),
   ("Walk","consumer walkthrough",r"walkthrough|Product §9|end[- ]to[- ]end"),
   ("KTime","knowledge-time",r"knowledge[- ]time|F15|F17|DP15a|as_of")]),
 "T3":("Strategy alignment",[
   ("PD","Product Definition",r"Product Definition|PD v[0-9]|Product §9|PD slice"),("VA","data-plane VA",r"data[- ]plane|DP-SD-|VA §"),
   ("Lyr","layer strategy",r"Strategy §|Kāla Strategy|DP-SD-017|layer contract"),
   ("Bind","synergy binding",r"synergy_binding|SYNERGY_BINDING|binding v[0-9]"),
   ("U/D","upstream / downstream",r"upstream|downstream|L1 authority|§N\.5"),
   ("Srv","serving contract",r"serv(ing|ed) (contract|surface|route)|serve-time|serving path")]),
 "T4":("Discipline gates",[
   ("Fct","facts / interpretation",r"B\.1\b|facts/interpretation|epistemic_class"),
   ("Ldgr","derivation ledger",r"DERIVATION_LEDGER|derivation ledger|constituent_facts|fact_id"),
   ("Idem","idempotency",r"idempoten"),("Earn","earned signal",r"§N\.8|earned[- ]signal|real detector|detector that (can )?fails?"),
   ("Narr","narration fidelity",r"§N\.7|narration"),("Dens","serving density",r"§N\.6|densit|catalog_only|hardFloor"),
   ("Null","honest null",r"honest null|honest absence|honest(ly)? (empty|zero|tier)|null rather than")]),
 "T5":("Two ladders",[
   ("DPL","data-plane ladder",r"PLAN_REVIEWED|PRODUCER_READY|DATA_ACCEPTED"),
   ("CmL","campaign ladder",r"ANALYZED|ENRICHED|QUALIFIED|FROZEN")]),
}

STREAM = {
 "ka_kshetra": ("origin/l3/kshetra-stage3-authorized",
   ["00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_ELEVATION_BRIEF_v1_0.md"]),
 "ka_sangam":  ("origin/sangam/stage3",
   ["00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ELEVATION_BRIEF_v1_0.md",
    "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md"]),
 "ka_gochara": ("origin/l3/gochara-autonomous-wp0-7",
   # the BRIEF v1.2 is SUPERSEDED; the live artifact is the PLAN, whose file is named
   # v2_1 while its frontmatter reads 2.2 (NATIVE_RATIFIED_PLAN). Read the plan only.
   ["00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md"]),
}
ASSETS = [  # registry_n, id, group, source-kind, note
 (1,"ka_kshetra","stream","stream","own packet + ruling sheet"),
 (2,"ka_sangam","stream / spine","stream","brief + algorithm plan"),
 (3,"ka_gochara","family head","stream","owns the served product (N-5)"),
 (4,"ka_gochara_v3_century_materialize","family","inherit:ka_gochara","no standalone brief — row in family plan §2; N-6 hold"),
 (5,"ka_gochara_resonance","family","inherit:ka_gochara","no standalone brief — row in family plan §2"),
 (6,"ka_vedha_gochara","family","inherit:ka_gochara","no standalone brief — row in family plan §2; WP9 stamps owed"),
 (7,"ka_moorti_nirnaya","family / layer","mine","brief overlaps Gochara's live code — needs re-base"),
 (8,"ka_kota_chakra","family / layer","mine",""),
 (9,"ka_tithi_pravesha","frontier","mine",""),
 (10,"ka_yojaka","frontier","mine",""),
 (11,"ka_kalasutra","spine","mine",""),
 (12,"ka_vighnakara","spine","mine",""),
 (13,"ka_kala_darshana","publication","mine",""),
 (14,"ka_jivana_parva","publication","mine",""),
 (15,"ka_bhavishya_lekha","publication","mine","protected claims — outcome reattachment is must_not_touch"),
 (16,"ka_dasha_kala","service","mine","clock authority"),
 (17,"ka_graha_sancara","service","mine",""),
 (18,"ka_muhurta_seva","service","mine",""),
 (19,"ka_tulana","service","mine",""),
 (20,"ka_avadhi","frontier","mine",""),
 (21,"ka_sudarshana_varsha","frontier","mine",""),
 (22,"ka_taranga","spine","mine",""),
]
IDS = {a[1] for a in ASSETS}

def seed_edges():
    """ka_* depends_on, verbatim from the registry seed. Returns (intra, external, extra_ids)."""
    try: s=io.open(SEED,encoding="utf-8").read()
    except OSError: return {},{},[]
    dep={}
    for m in re.finditer(r"asset_id\s*:\s*'(ka_[a-z_0-9]+)'", s):
        seg=s[m.start():m.start()+3000]
        d=re.search(r"depends_on\s*:\s*\[([^\]]*)\]", seg)
        dep[m.group(1)]=re.findall(r"'([a-z_0-9]+)'", d.group(1)) if d else []
    intra={a:[x for x in ds if x in dep] for a,ds in dep.items()}
    ext  ={a:[x for x in ds if x not in dep] for a,ds in dep.items()}
    return intra, ext, sorted(set(dep)-IDS)

def topo(intra):
    """Kahn with deterministic tiebreak. Returns (order, depth, cycle)."""
    nodes=set(intra); indeg={a:len(intra[a]) for a in nodes}
    rev=collections.defaultdict(list)
    for a,ds in intra.items():
        for d in ds: rev[d].append(a)
    q=sorted(a for a in nodes if indeg[a]==0); depth={a:0 for a in q}; order=[]
    while q:
        q.sort(key=lambda x:(depth[x],x)); n=q.pop(0); order.append(n)
        for m in sorted(rev[n]):
            indeg[m]-=1; depth[m]=max(depth.get(m,0),depth[n]+1)
            if indeg[m]==0: q.append(m)
    return order, depth, [a for a in nodes if indeg[a]>0]

def ledger():
    """Latest event per asset, plus the full trail. Malformed lines are reported, not skipped silently."""
    ev=collections.defaultdict(list); bad=0
    if os.path.exists(LEDGER):
        for ln,line in enumerate(io.open(LEDGER,encoding="utf-8"),1):
            line=line.strip()
            if not line: continue
            try: r=json.loads(line)
            except Exception: bad+=1; continue
            if r.get("asset","").startswith("_"): continue
            r["_line"]=ln; ev[r.get("asset","")].append(r)
    return ev,bad

def git_show(ref,paths):
    out=[]
    for p in paths:
        r=subprocess.run(["git","-C",ROOT,"show",f"{ref}:{p}"],capture_output=True,text=True)
        if r.returncode==0: out.append(r.stdout)
    return "\n".join(out)

def load(aid,kind):
    if kind=="stream":
        ref,ps=STREAM[aid]; return git_show(ref,ps), ref
    if kind.startswith("inherit:"):
        ref,ps=STREAM[kind.split(":",1)[1]]; return git_show(ref,ps), ref+" (inherited)"
    p=os.path.join(BR,f"KA_{aid[3:].upper()}_ELEVATION_BRIEF_v1_0.md")
    return (io.open(p,encoding="utf-8",errors="replace").read(),"this branch") if os.path.exists(p) else ("","MISSING")

def reviews(aid):
    """(count, latest verdict, highest brief version reviewed). REVIEW_<A>_v1_1.md reviewed v1.1."""
    fs=sorted(glob.glob(os.path.join(BR,"reviews",f"REVIEW_{aid.upper()}_v*.md")))
    if not fs: return 0,"—",None
    m=re.search(r"\b(ACCEPT_WITH_CORRECTIONS|REWORK|ACCEPT)\b", io.open(fs[-1],encoding="utf-8").read())
    vs=[]
    for f in fs:
        mv=re.search(r"_v(\d+)_(\d+)\.md$",f)
        if mv: vs.append(f"{mv.group(1)}.{mv.group(2)}")
    return len(fs),(m.group(1) if m else "?"),(max(vs,key=lambda x:tuple(map(int,x.split(".")))) if vs else None)


# ── Read-only production probe (native-authorised 2026-09-24) ────────────────
# Connects ONLY via DATABASE_URL from the environment, or --env-file <path>.
# Never embeds or prints a credential. Every statement is a SELECT; the connection
# is opened read-only and rolled back. If no DSN is available the probe does not
# run and the tracker says so rather than implying a clean result.
CONTRACT_FIELDS = ["t_start","t_end","inclusivity","time_basis","precision_regime","claim_grain",
 "comparable_with","comparability_class","source_qualification","corpus_verifiable",
 "independence_group","declared_current_count","coverage","completeness_state",
 "epistemic_class","operator_role","tier_basis","window_ref"]

def _dsn(env_file=None):
    if env_file and os.path.exists(env_file):
        for line in io.open(env_file,encoding="utf-8",errors="replace"):
            line=line.strip()
            if line.startswith("DATABASE_URL="):
                return line.split("=",1)[1].strip().strip('"').strip("'")
    return os.environ.get("DATABASE_URL")

def probe_db(asset_ids, env_file=None):
    dsn=_dsn(env_file)
    if not dsn:
        return {"ran":False,"reason":"no DATABASE_URL in environment or --env-file; probe not run"}
    try:
        import psycopg2, psycopg2.extras
    except ImportError:
        return {"ran":False,"reason":"psycopg2 not installed; probe not run"}
    out={"ran":True,"tables":{},"applied_max":None,"applied":set()}
    try:
        conn=psycopg2.connect(dsn); conn.set_session(readonly=True, autocommit=False)
        cur=conn.cursor()
        cur.execute("SELECT asset_id, target_table FROM asset_registry WHERE asset_id = ANY(%s)",(list(asset_ids),))
        tmap={a:t for a,t in cur.fetchall()}
        # Query by the registry's own target_table list. An earlier version filtered on
        # LIKE 'kala\_%' and reported ka_gochara_resonance as MISSING when its table is
        # simply named gochara_resonance_map (12 cols, 1595 rows, live) — a naming
        # assumption producing a false negative on a real table.
        wanted=[t for t in tmap.values() if t]
        cur.execute("""SELECT table_name, count(*) FROM information_schema.columns
                       WHERE table_schema='public' AND table_name = ANY(%s) GROUP BY 1""",(wanted,))
        colcount=dict(cur.fetchall())
        cur.execute("""SELECT table_name, column_name FROM information_schema.columns
                       WHERE table_schema='public' AND table_name = ANY(%s)""",(wanted,))
        cols={}
        for t,c in cur.fetchall(): cols.setdefault(t,set()).add(c)
        cur.execute("SELECT filename FROM _migrations_applied WHERE filename ~ '^[0-9]+_'")
        applied={r[0] for r in cur.fetchall()}
        nums=[int(f.split("_",1)[0]) for f in applied]
        out["applied"]=applied; out["applied_max"]=max(nums) if nums else None
        for aid in asset_ids:
            t=tmap.get(aid)
            ent={"target_table":t,"exists":False,"columns":None,"rows":None,
                 "no_table_by_design": t is None,   # service assets store nothing
                 "contract_present":[],"contract_absent":[]}
            if t and t in cols:
                ent["exists"]=True; ent["columns"]=colcount.get(t)
                have=cols[t]
                ent["contract_present"]=[f for f in CONTRACT_FIELDS if f in have]
                ent["contract_absent"] =[f for f in CONTRACT_FIELDS if f not in have]
                try:
                    cur.execute('SELECT count(*) FROM public."%s"'%t.replace('"',''))
                    ent["rows"]=cur.fetchone()[0]
                except Exception:
                    ent["rows"]=None
            out["tables"][aid]=ent
        conn.rollback(); cur.close(); conn.close()
    except Exception as e:
        return {"ran":False,"reason":"probe failed: %s"%type(e).__name__}
    out["applied"]=sorted(out["applied"])
    return out

# Heads whose migrations are LIVE candidates. Scanning all history instead counts
# renumbered predecessors (Saṅgam's 1085-1087 became 1088-1090) as unapplied, which
# inflates the gap with files nobody intends to apply.
LIVE_HEADS=["origin/main","origin/l3/kshetra-stage3-authorized","origin/sangam/stage3",
            "origin/l3/gochara-autonomous-wp0-7","HEAD"]

def intree_migrations():
    """Migration filenames on the current live heads, both directories -> {file: head}."""
    seen={}
    for ref in LIVE_HEADS:
        q=subprocess.run(["git","-C",ROOT,"ls-tree","-r","--name-only",ref,
                          "platform/migrations","platform/supabase/migrations"],
                         capture_output=True,text=True)
        if q.returncode: continue
        for line in q.stdout.splitlines():
            b=os.path.basename(line.strip())
            if b.endswith(".sql") and re.match(r"^\d+_",b): seen.setdefault(b,ref)
    return seen

# lifecycle: what the strategy session may assert from evidence alone
def _vt(v):
    try: return tuple(int(x) for x in str(v).split("."))
    except Exception: return (0,)

OPENING={"brief_started","review_requested","handoff","started"}
SOP_STAGE={"brief_started":"authoring the brief","review_requested":"out for Fable 5.1 review",
 "review_accept":"review ACCEPTED","review_reject":"review REJECTED — back to Opus",
 "brief_authored":"brief drafted, review not yet requested","brief_final":"brief FINAL",
 "handoff":"handed to execution","started":"execution running","completed":"execution reported done",
 "blocked":"execution blocked","verified":"verified","reverted":"reverted"}

def lifecycle(brief_status, nrev, verdict, events, has_brief, brief_ver=None, reviewed_ver=None):
    last = events[-1]["event"] if events else None
    if last=="verified":  return "ELEVATED","the strategy session verified the execution"
    if last=="completed": return "AWAITING_VERIFY","execution reported done; not yet verified here"
    if last=="blocked":   return "BLOCKED", events[-1].get("note","blocked by execution")
    if last in ("started",): return "EXECUTING","execution session is working"
    if last=="handoff":   return "HANDED_OFF","dispatched to execution; not started"
    if last=="reverted":  return "BRIEF_DRAFT","execution reverted"
    if last=="review_reject": return "BRIEF_REJECTED","independent review REJECTED — back to Opus"
    if last=="review_accept": return "BRIEF_FINAL","independent review ACCEPTED"
    if last=="review_requested": return "IN_REVIEW","out for independent Fable 5.1 review"
    if last in ("brief_started","brief_authored"): return "BRIEF_IN_PROGRESS","being authored now"
    if last=="brief_final": return "BRIEF_FINAL","sealed final"
    if not has_brief:     return "BRIEF_ABSENT","no brief artifact found"
    up=(brief_status or "").upper()
    if "APPROVED_FOR_EXECUTION" in up or up.startswith("CLOSED") or "RATIFIED" in up:
        return "BRIEF_FINAL","approved for execution by its own stream"
    if reviewed_ver and brief_ver and _vt(brief_ver)>_vt(reviewed_ver):
        return "BRIEF_AWAITING_REREVIEW",f"v{brief_ver} folds findings from the v{reviewed_ver} review; not re-reviewed"
    if verdict=="REWORK": return "BRIEF_REWORK","latest review returned REWORK"
    if verdict=="ACCEPT_WITH_CORRECTIONS": return "BRIEF_CORRECTIONS","corrections owed from latest review"
    if nrev==0:           return "BRIEF_UNREVIEWED","no independent review on record here"
    if "PROPOSED_FOR_NATIVE_RULING" in (brief_status or ""): return "BRIEF_FINAL","author-final; awaiting ruling"
    return "BRIEF_DRAFT","drafted"

# ── Native ruling, 2026-09-24 ────────────────────────────────────────────────
# "Let's consider L0, L1, and L2 all assets to be elevated as per the current revision,
#  let's make that assumption and proceed."
# This is an ASSUMPTION the native authorised to unblock the campaign, NOT a measured fact.
# Measured, under the current frozen definition t3-2026-09-11-8b884eac, bg_*=0/40 frozen,
# ga_*=0/19, bo_*=8/22 (prior freezes are scoped to superseded revisions and do not carry).
# The tracker therefore gates only on intra-L3 ancestors and states the assumption on its face.
ASSUME_UPSTREAM_LAYERS_ELEVATED = True
UPSTREAM_ASSUMPTION = ("Native ruling 2026-09-24: L0/L1/L2 assets are ASSUMED elevated under the "
  "current revision so L3 can proceed. Measured state under the frozen definition "
  "t3-2026-09-11-8b884eac is bg_ 0/40, ga_ 0/19, bo_ 8/22 frozen — the assumption is a "
  "decision to proceed, not a verification, and any L3 result inherits it.")

READY_FOR_HANDOFF={"BRIEF_FINAL"}
DONE={"ELEVATED"}

def scan(env_file=None, do_probe=True):
    intra,ext,extra = seed_edges()
    db = probe_db([a[1] for a in ASSETS], env_file) if do_probe else {"ran":False,"reason":"disabled"}
    order,depth,cycle = topo(intra) if intra else ([],{},[])
    dag_rank={a:i for i,a in enumerate([x for x in order if x in IDS],1)}
    ev,bad = ledger()
    crit=[{"tier":t,"tier_name":tn,"key":k,"label":l}
          for t,(tn,items) in TIERS.items() for k,l,_ in items]
    assets=[]
    for n,aid,group,kind,note in ASSETS:
        text,origin=load(aid,kind)
        ver=(re.search(r'^version:\s*"?([^"\n]+)',text,re.M) or [None,"—"])[1].strip().strip('"')
        sts=[x.strip() for x in re.findall(r'^status:\s*([^\n#]+)',text,re.M)]
        live=[x for x in sts if "SUPERSEDED" not in x.upper()]
        st=(live or sts or ["—"])[0]
        cells={}
        for t,(tn,items) in TIERS.items():
            for k,l,pat in items:
                hit=bool(re.search(pat,text,re.I))
                if t=="T1":
                    m=re.search(r"^\|\s*"+re.escape(k)+r"\s+[^|]*\|(.*)$",text,re.M)
                    ans=m.group(1).strip().strip("|").strip() if m else ""
                    hit=hit or (len(ans)>12 and ans not in {"—","-","n/a","·"})
                cells[k]=hit
        nrev,verd,rver=reviews(aid)
        if kind=="stream" or kind.startswith("inherit:"):
            nrev,verd,rver=-1,"external",None   # Astra / Kimi, not stored in this tree
        state,why=lifecycle(st,nrev,verd,ev.get(aid,[]),bool(text),ver,rver)
        assets.append({"n":n,"id":aid,"group":group,"kind":kind,"note":note,"origin":origin,
            "ver":ver,"status":st,"reviews":nrev,"verdict":verd,"reviewed_ver":rver,"cells":cells,
            "score":sum(cells.values()),"total":len(cells),
            "dag":dag_rank.get(aid,999),"depth":depth.get(aid,0),
            "deps":intra.get(aid,[]),"ext_deps":ext.get(aid,[]),
            "db": db.get("tables",{}).get(aid),
            "state":state,"why":why,"events":ev.get(aid,[]),
            "active": bool(ev.get(aid)) and ev[aid][-1]["event"] in OPENING,
            "sop_stage": SOP_STAGE.get(ev[aid][-1]["event"]) if ev.get(aid) else None,
            "last_event_ts": ev[aid][-1]["ts"] if ev.get(aid) else None})
    by={a["id"]:a for a in assets}
    for a in assets:
        blockers=[d for d in a["deps"] if d in by and by[d]["state"] not in DONE]
        a["blocked_by"]=blockers
        a["ready"]= (a["state"] in READY_FOR_HANDOFF) and not blockers
        a["next"]= ("hand off to execution" if a["ready"] else
                    "finish brief" if a["state"].startswith("BRIEF") and not blockers else
                    "verify execution" if a["state"]=="AWAITING_VERIFY" else
                    "wait on "+", ".join(blockers) if blockers else "—")
    assets.sort(key=lambda a:(a["dag"],a["n"]))
    cov={c["key"]:sum(1 for a in assets if a["cells"][c["key"]]) for c in crit}
    unapplied=[]
    if db.get("ran"):
        ap=set(db.get("applied") or [])
        for fn,head in sorted(intree_migrations().items()):
            if fn not in ap: unapplied.append({"file":fn,"head":head.replace("origin/","")})
    now=[{"id":a["id"],"stage":a["sop_stage"],"since":a["last_event_ts"],"dag":a["dag"]}
         for a in assets if a["active"]]
    return {"generated":datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "now_processing":now,"upstream_assumption":UPSTREAM_ASSUMPTION,
        "criteria":crit,"assets":assets,"coverage":cov,"n_assets":len(assets),
        "db":{k:v for k,v in db.items() if k!="tables"},
        "unapplied_migrations":unapplied,"unapplied_count":len(unapplied),
        "cycle":cycle,"untracked_ka_assets":extra,"ledger_bad_lines":bad,
        "ledger_path":os.path.relpath(LEDGER,ROOT),
        "states":collections.Counter(a["state"] for a in assets)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--watch",action="store_true")
    ap.add_argument("--interval",type=int,default=10)
    ap.add_argument("--env-file",help="file containing DATABASE_URL=... for the read-only probe")
    ap.add_argument("--no-db",action="store_true",help="skip the production probe")
    a=ap.parse_args()
    while True:
        d=scan(a.env_file, not a.no_db); js=json.dumps(d,indent=1,default=str)
        io.open(OUT,"w").write(js)
        io.open(OUT[:-5]+".js","w").write("window.KALA_DATA="+js+";\nwindow.dispatchEvent(new Event('kala-data'));\n")
        np_=d.get("now_processing") or []
        print("  NOW PROCESSING: "+(", ".join(f'{x["id"]} ({x["stage"]})' for x in np_) if np_ else "nothing in flight"))
        rdy=[x["id"] for x in d["assets"] if x["ready"]]
        print(f'[{d["generated"]}] {d["n_assets"]} assets | states: '
              +", ".join(f"{k}={v}" for k,v in sorted(d["states"].items())))
        print(f'  ready for handoff (DAG-unblocked): {", ".join(rdy) if rdy else "none"}')
        if d["cycle"]: print("  !! DAG CYCLE:",d["cycle"])
        if d["untracked_ka_assets"]: print("  !! ka_* in seed but untracked:",d["untracked_ka_assets"])
        if d["db"].get("ran"):
            dbs=[x.get("db") or {} for x in d["assets"]]
            svc=sum(1 for x in dbs if x.get("no_table_by_design"))
            dep=sum(1 for x in dbs if x.get("exists"))
            miss=[x["id"] for x in d["assets"] if (x.get("db") or {}) and not (x["db"] or {}).get("exists")
                  and not (x["db"] or {}).get("no_table_by_design")]
            print(f'  prod probe: {dep} tables live, {svc} service assets (no table by design)'
                  +(f', MISSING: {", ".join(miss)}' if miss else ', none missing'))
            print(f'  migrations: applied max {d["db"].get("applied_max")}, '
                  f'{d["unapplied_count"]} on live heads not applied')
        else:
            print(f'  prod probe: NOT RUN — {d["db"].get("reason")}')
        if d["ledger_bad_lines"]: print(f'  !! {d["ledger_bad_lines"]} malformed ledger line(s)')
        if not a.watch: break
        time.sleep(a.interval)

if __name__=="__main__": main()
