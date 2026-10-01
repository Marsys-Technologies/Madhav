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
# `elevated_assets(ref, repo)` is the ONE place an asset may be called ELEVATED (plan 1.1; Track E brief 8). It is
# a module-level function with no side effects. It reads EVERY input with `git -C <repo> show <sha>:<path>`, where
# <sha> is `ref` resolved once up front: never the working tree, never a database. It RAISES `ElevatedInputError`
# on any unreadable ref/path, any malformed JSONL line or record, and `WatermarkOlderThanLedger` when E5.5's
# invalidation watermark is older than the certification ledger at `ref`; a failure never comes back as an empty
# set (an empty set is only ever the honest answer "nothing is elevated"). The legacy lifecycle()/scan() above is
# NOT this function and is not an authority for ELEVATED (E6.3t switches the tracker's own caller to this one).
#
# An asset is ELEVATED when all four hold, or when it is TERMINALLY dispositioned (retire/consolidate with a reason):
#   (1) every criterion of every core gate its layer requires -- asset_census.CRITERION_REGISTRY entries whose gate
#       is in CELL_GATES and whose `layers` holds the asset's layer, exactly the rows the census rollup counts --
#       has a CURRENT satisfying certificate: PASS (detector not NONE, not inconclusive, not capped, basis absent
#       or 'declaration') or an N/A whose `na.rule_id` is declared in NA_RULE_DECISIONS at `ref` with that
#       `na.decision_id`. A gate with no criterion for the layer is unsatisfied (the rollup reads it NO_DETECTOR);
#   (2) every addition DECLARED for the asset has a current PASS (an addition has no registry rule: no N/A);
#   (3) no open `gap` row on a core gate or declared addition. kind info/opportunity never blocks; a row on a
#       non-gate criterion family (the registry gates outside CELL_GATES: Cost, Count, Complete, Reach...) never
#       blocks (plan D3); an open gap row on ANYTHING ELSE blocks (an unclassifiable row is not proof it is not on
#       a core gate);
#   (4) a disposition is recorded and is not `unresolved`.
#
# ---- INPUT FIELD NAMES (assumed; reconcile with E5.1 nikasha_certify.py / E5.5 on integration) -----------------
# asset_certs.jsonl (E5.1 arch 12.16; first line {"asset":"_schema"}): asset, layer, kind (gate|addition), gate,
#   criterion, criterion_version, detector, verdict, basis, na {rule_id, decision_id, ...}, inconclusive?,
#   evidence {census_run_id}, writer_hashes {repo-relative path: sha256}, writer_hashes_reason, upstream_cert_ids
#   [cert_id], semantic_fingerprint (sha256 or null), cert_key "<asset>|<kind>|<criterion>", generation (1..n in file
#   order per cert_key), cert_id "<cert_key>@<generation>". The current record of a cert_key is its highest generation.
# asset_cert_invalidations.jsonl (E5.5; first line {"asset":"_schema"}): rows of
#   {"record_type":"invalidation","cert_id":"<key>@<gen>","invalidated_by":{"kind":..., "detail":...}}  (a non-empty
#     `invalidated_by`; this is how a semantic-fingerprint / upstream / writer change found by E5.5 reaches the ledger)
#   {"record_type":"watermark","certs_lines":<n>,"certs_sha256":"<sha256>","commit":"<sha>","event_offset":<int>}
#     certs_lines = how many non-blank lines of asset_certs.jsonl (schema line included) E5.5 had evaluated;
#     certs_sha256 = sha256 of those lines, each followed by "\n". The LAST watermark row governs; certs_lines must
#     never decrease. `commit` and `event_offset` are recorded provenance; the decisive comparison is by ledger
#     position, because a commit hash cannot be compared with the ref that contains the file naming it.
#     "Watermark at least the ledger ref" means certs_lines >= the line count of the certificate ledger at `ref`.
# asset_gaps.jsonl (delta ledger; first line {"asset":"_schema"}): asset, gap_id, kind (gap|opportunity|info; absent
#   reads gap), criterion, state (OPEN|IN_PROGRESS|CLOSED|WITHDRAWN; absent reads OPEN), superseded_by. A gap_id's
#   state is its LATEST row; a row folded into another gap_id (superseded_by) is carried by its target, which must
#   exist.
# asset_dispositions.jsonl (recorded dispositions; first line {"asset":"_schema"}): asset, disposition (keep|
#   integrate|enrich|qualify|consolidate|historical|retire|unresolved), reason, additions [declared addition ids].
#   The LATEST row per asset governs. retire/consolidate WITH a non-blank reason is TERMINAL.
# platform/scripts/governance/asset_census.py at `ref`, read as SOURCE (ast, never imported): LAYERS[*].prefix,
#   CRITERION_REGISTRY[*].{gate,layers,detector,revision}, CELL_GATES, NA_RULE_DECISIONS.
#
# "CURRENT" (see certificate_currency): the record is the latest generation of its cert_key; no invalidation row
# names its cert_id; every recorded writer file still hashes to the recorded sha256 at `ref` (a writer file that is
# absent at `ref` is stale, not an error); every upstream cert id is the LATEST generation of its key and is itself
# current and PASS/N/A; a PASS (or measured N/A) carries a semantic fingerprint (the comparison with the live rows is
# E5.5's, delivered as an invalidation row); a gate record's criterion_version equals the registry revision at `ref`.
import ast as _ast, dataclasses as _dc, hashlib as _hashlib, re as _re

E63_CONTROL_DIR = "00_ARCHITECTURE/control"
E63_CERTS_PATH = E63_CONTROL_DIR + "/asset_certs.jsonl"
E63_GAPS_PATH = E63_CONTROL_DIR + "/asset_gaps.jsonl"
E63_INVALIDATIONS_PATH = E63_CONTROL_DIR + "/asset_cert_invalidations.jsonl"
E63_DISPOSITIONS_PATH = E63_CONTROL_DIR + "/asset_dispositions.jsonl"
E63_CENSUS_PATH = "platform/scripts/governance/asset_census.py"

E63_VERDICTS = frozenset({"PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "ERRORED", "N/A"})
E63_GAP_KINDS = frozenset({"gap", "opportunity", "info"})
E63_GAP_STATES = frozenset({"OPEN", "IN_PROGRESS", "CLOSED", "WITHDRAWN"})
E63_CLOSED_GAP_STATES = frozenset({"CLOSED", "WITHDRAWN"})
E63_DISPOSITIONS = frozenset({"keep", "integrate", "enrich", "qualify", "consolidate", "historical", "retire",
                              "unresolved"})
E63_TERMINAL_DISPOSITIONS = frozenset({"retire", "consolidate"})
E63_BASIS_DECLARATION = "declaration"        # the one recognised `basis` (asset_census._check_contribution)

_E63_ASSET = _re.compile(r"[a-z][a-z0-9_]*")
_E63_ADDITION = _re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_E63_SHA256 = _re.compile(r"[0-9a-f]{64}")
_E63_COMMIT = _re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_E63_CERT_ID = _re.compile(r"([a-z][a-z0-9_]*)\|(gate|addition)\|([A-Za-z0-9][A-Za-z0-9_.-]*)@([1-9][0-9]*)")


class ElevatedInputError(RuntimeError):
    """An input of `elevated_assets` was unreadable or malformed, so no answer can be given. `code` is a stable slug."""

    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class WatermarkOlderThanLedger(ElevatedInputError):
    """E5.5 has evaluated fewer certificate-ledger lines than the ledger at `ref` holds: the invalidations on file
    cannot be trusted for the newer lines, so the exact function refuses to answer rather than guess."""


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


def _e63_jsonl(data, path, require_schema=True):
    """[(physical line number, raw text, object)] for every non-blank line; the first must be the `_schema` row."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        _e63_fail("malformed", f"{path} is not valid UTF-8 ({e.reason})")
    rows = []
    for n, raw in enumerate(text.split("\n"), 1):
        raw = raw.rstrip("\r")
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as e:
            _e63_fail("malformed", f"{path} line {n} is not JSON ({e.msg})")
        if not isinstance(obj, dict):
            _e63_fail("malformed", f"{path} line {n} is not a JSON object")
        rows.append((n, raw, obj))
    if require_schema and (not rows or rows[0][2].get("asset") != "_schema"):
        _e63_fail("malformed", f"{path}: the first line must be the `_schema` row")
    return rows


def _e63_nonblank(v):
    return isinstance(v, str) and bool(v.strip())


def _e63_relpath_ok(p):
    return (isinstance(p, str) and bool(p) and not p.startswith("/") and "\\" not in p
            and ".." not in p.split("/") and "" not in p.split("/"))


# ---- the registry, read as source at `ref` ---------------------------------------------------------------------
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


@_dc.dataclass(frozen=True)
class RegistryFacts:
    layer_prefix: dict      # "L3" -> "ka_"
    criteria: dict          # "Idem.pattern" -> {gate, layers, detector, revision}
    cell_gates: tuple       # the core gates, in order
    na_rules: dict          # declared N/A rule id -> decision id

    def required(self, layer):
        """{gate: [criterion, ...]} for the core gates `layer` requires (the rows the census rollup counts)."""
        return {g: sorted(c for c, e in self.criteria.items() if e["gate"] == g and layer in e["layers"])
                for g in self.cell_gates}

    @property
    def info_families(self):
        return frozenset(e["gate"] for e in self.criteria.values()) - frozenset(self.cell_gates)


def _e63_registry_facts(repo, sha):
    src = _e63_show(repo, sha, E63_CENSUS_PATH)
    try:
        tree = _ast.parse(src.decode("utf-8"), filename=E63_CENSUS_PATH)
    except (SyntaxError, UnicodeDecodeError, ValueError) as e:
        _e63_fail("registry_unreadable", f"{E63_CENSUS_PATH} at {sha[:12]} does not parse ({type(e).__name__})")
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
    for needed in ("LAYERS", "CRITERION_REGISTRY", "CELL_GATES", "NA_RULE_DECISIONS"):
        if needed not in nodes:
            _e63_fail("registry_unreadable", f"{E63_CENSUS_PATH} at {sha[:12]} defines no {needed}")
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
        if (not _e63_nonblank(e["gate"]) or not _e63_nonblank(e["detector"]) or isinstance(e["revision"], bool)
                or not isinstance(e["revision"], int) or not isinstance(e["layers"], tuple)
                or not all(isinstance(x, str) for x in e["layers"])):
            _e63_fail("registry_unreadable", f"CRITERION_REGISTRY[{ck!r}] has an unexpected shape")
        criteria[ck] = e
    if not layer_prefix or not all(_e63_nonblank(p) for p in layer_prefix.values()) or not criteria:
        _e63_fail("registry_unreadable", "LAYERS / CRITERION_REGISTRY are empty or malformed")
    return RegistryFacts(layer_prefix, criteria, cell_gates, na_rules)


def _e63_layer_of(asset, facts, where):
    hits = [lk for lk, p in facts.layer_prefix.items() if asset.startswith(p)]
    if len(hits) != 1:
        _e63_fail("malformed", f"{where}: asset {asset!r} matches {len(hits)} layer prefixes (need exactly one)")
    return hits[0]


# ---- the four ledgers --------------------------------------------------------------------------------------------
def _e63_parse_certs(data, facts):
    """(records by cert_key in generation order, nonblank lines). Strict: any record this reader cannot trust raises."""
    rows = _e63_jsonl(data, E63_CERTS_PATH)
    by_key = {}
    for n, _raw, r in rows[1:]:
        where = f"{E63_CERTS_PATH} line {n}"
        asset, kind, crit, verdict = r.get("asset"), r.get("kind"), r.get("criterion"), r.get("verdict")
        gen = r.get("generation")
        if not (isinstance(asset, str) and _E63_ASSET.fullmatch(asset)):
            _e63_fail("malformed", f"{where}: bad asset {asset!r}")
        if kind not in ("gate", "addition") or not _e63_nonblank(crit):
            _e63_fail("malformed", f"{where}: kind must be gate|addition and criterion non-blank")
        if verdict not in E63_VERDICTS:
            _e63_fail("malformed", f"{where}: verdict {verdict!r} is outside {sorted(E63_VERDICTS)}")
        if isinstance(gen, bool) or not isinstance(gen, int) or gen < 1:
            _e63_fail("malformed", f"{where}: generation must be an int >= 1")
        key = f"{asset}|{kind}|{crit}"
        if r.get("cert_key") != key or r.get("cert_id") != f"{key}@{gen}":
            _e63_fail("malformed", f"{where}: cert_key/cert_id do not match asset|kind|criterion@generation")
        layer = r.get("layer")
        if layer not in facts.layer_prefix or _e63_layer_of(asset, facts, where) != layer:
            _e63_fail("malformed", f"{where}: layer {layer!r} does not match asset {asset!r}")
        if not _e63_nonblank(r.get("detector")):
            _e63_fail("malformed", f"{where}: detector is required (NONE is spelled NONE)")
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
        if kind == "gate" and crit in facts.criteria and r.get("gate") != facts.criteria[crit]["gate"]:
            _e63_fail("malformed", f"{where}: {crit} belongs to gate {facts.criteria[crit]['gate']!r}, not {r.get('gate')!r}")
        by_key.setdefault(key, []).append(r)
    for key, recs in by_key.items():
        if [x["generation"] for x in recs] != list(range(1, len(recs) + 1)):
            _e63_fail("malformed", f"{E63_CERTS_PATH}: {key}: generations are not 1..{len(recs)} in file order")
    return by_key, [raw for _n, raw, _o in rows]


def _e63_parse_invalidations(data):
    rows = _e63_jsonl(data, E63_INVALIDATIONS_PATH)
    invalidated, watermark = {}, None
    for n, _raw, r in rows[1:]:
        where = f"{E63_INVALIDATIONS_PATH} line {n}"
        rt = r.get("record_type")
        if rt == "invalidation":
            cid, by = r.get("cert_id"), r.get("invalidated_by")
            if not (isinstance(cid, str) and _E63_CERT_ID.fullmatch(cid)):
                _e63_fail("malformed", f"{where}: invalidation cert_id {cid!r} is not a cert id")
            if not (_e63_nonblank(by) or (isinstance(by, dict) and by and _e63_nonblank(by.get("kind")))):
                _e63_fail("malformed", f"{where}: invalidated_by must be a non-blank string or an object with a `kind`")
            invalidated[cid] = by
        elif rt == "watermark":
            nl, sh, off, cm = r.get("certs_lines"), r.get("certs_sha256"), r.get("event_offset"), r.get("commit")
            if (isinstance(nl, bool) or not isinstance(nl, int) or nl < 1
                    or not (isinstance(sh, str) and _E63_SHA256.fullmatch(sh))
                    or (off is not None and (isinstance(off, bool) or not isinstance(off, int) or off < 0))
                    or (cm is not None and not (isinstance(cm, str) and _E63_COMMIT.fullmatch(cm)))):
                _e63_fail("malformed", f"{where}: watermark needs certs_lines >= 1 and certs_sha256 (+ optional commit/event_offset)")
            if watermark is not None and nl < watermark["certs_lines"]:
                _e63_fail("malformed", f"{where}: the watermark went backwards ({nl} < {watermark['certs_lines']})")
            watermark = r
        else:
            _e63_fail("malformed", f"{where}: record_type must be invalidation|watermark, got {rt!r}")
    if watermark is None:
        _e63_fail("watermark_missing", f"{E63_INVALIDATIONS_PATH} carries no watermark row: nothing says up to where "
                                       "invalidations have been evaluated")
    return invalidated, watermark


def _e63_check_watermark(watermark, cert_lines):
    have = len(cert_lines)
    if watermark["certs_lines"] < have:
        raise WatermarkOlderThanLedger(
            "watermark_older", f"the invalidation watermark covers {watermark['certs_lines']} certificate-ledger "
                               f"lines but the ledger at the ref holds {have}")
    if watermark["certs_lines"] > have:
        _e63_fail("watermark_ahead", f"the watermark claims {watermark['certs_lines']} certificate-ledger lines but "
                                     f"the ledger at the ref holds {have} (truncated or rewritten ledger)")
    digest = _hashlib.sha256("".join(ln + "\n" for ln in cert_lines[:have]).encode("utf-8")).hexdigest()
    if digest != watermark["certs_sha256"]:
        _e63_fail("watermark_mismatch", "the certificate ledger's content no longer matches the watermark's sha256 "
                                        "(the append-only ledger was rewritten)")


def _e63_parse_gaps(data):
    """The EFFECTIVE gap rows: latest row per gap_id; rows with no gap_id stand alone; folded rows removed."""
    rows = _e63_jsonl(data, E63_GAPS_PATH)
    latest, loose, all_ids = {}, [], set()
    for n, _raw, r in rows[1:]:
        where = f"{E63_GAPS_PATH} line {n}"
        if not _e63_nonblank(r.get("asset")):
            _e63_fail("malformed", f"{where}: asset is required")
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
        eff = dict(asset=r["asset"], kind=kind, state=state, criterion=crit, gap_id=gid, superseded_by=sup, line=n)
        if gid:
            all_ids.add(gid)
            latest[gid] = eff
        else:
            loose.append(eff)
    out = []
    for g in loose + list(latest.values()):
        if g["superseded_by"]:
            if g["superseded_by"] not in all_ids:
                _e63_fail("malformed", f"{E63_GAPS_PATH} line {g['line']}: superseded_by {g['superseded_by']!r} names no gap_id")
            continue                      # folded: its identity is carried by the target row
        out.append(g)
    return out


def _e63_parse_dispositions(data, facts):
    rows = _e63_jsonl(data, E63_DISPOSITIONS_PATH)
    latest = {}
    for n, _raw, r in rows[1:]:
        where = f"{E63_DISPOSITIONS_PATH} line {n}"
        asset, disp = r.get("asset"), r.get("disposition")
        if not (isinstance(asset, str) and _E63_ASSET.fullmatch(asset)):
            _e63_fail("malformed", f"{where}: bad asset {asset!r}")
        _e63_layer_of(asset, facts, where)
        if disp not in E63_DISPOSITIONS:
            _e63_fail("malformed", f"{where}: disposition {disp!r} is outside {sorted(E63_DISPOSITIONS)}")
        if r.get("reason") is not None and not isinstance(r.get("reason"), str):
            _e63_fail("malformed", f"{where}: reason must be text")
        adds = r.get("additions", [])
        if (not isinstance(adds, list) or any(not isinstance(a, str) or not _E63_ADDITION.fullmatch(a)
                                              or a in facts.criteria for a in adds)
                or len(set(adds)) != len(adds)):
            _e63_fail("malformed", f"{where}: additions must be unique addition ids that do not shadow a registered criterion")
        latest[asset] = dict(disposition=disp, reason=(r.get("reason") or "").strip(), additions=tuple(adds))
    return latest


# ---- currency ----------------------------------------------------------------------------------------------------
class LedgerState:
    """What `is_current` reads: the certificate ledger at one resolved commit, with E5.5's invalidations."""

    def __init__(self, repo, sha, facts, by_key, invalidated):
        self.repo, self.sha, self.facts = repo, sha, facts
        self.by_key, self.invalidated = by_key, invalidated
        self._hash_cache, self._cur_cache, self._visiting = {}, {}, []

    def writer_sha256(self, path):
        """sha256 of `path` at the ledger commit, or None when the file is absent there."""
        if path not in self._hash_cache:
            try:
                self._hash_cache[path] = _hashlib.sha256(_e63_show(self.repo, self.sha, path)).hexdigest()
            except ElevatedInputError:
                self._hash_cache[path] = None
        return self._hash_cache[path]


def certificate_currency(rec, state):
    """(True, None) when `rec` is CURRENT, else (False, why). Raises ElevatedInputError on an upstream cycle."""
    cid = rec["cert_id"]
    if cid in state._cur_cache:
        return state._cur_cache[cid]
    if cid in state._visiting:
        _e63_fail("malformed", f"upstream certificate cycle through {cid}")
    state._visiting.append(cid)
    try:
        res = _e63_currency(rec, state)
    finally:
        state._visiting.pop()
    state._cur_cache[cid] = res
    return res


def is_current(rec, state):
    return certificate_currency(rec, state)[0]


def _e63_currency(rec, state):
    latest = state.by_key[rec["cert_key"]][-1]
    if rec["generation"] != latest["generation"]:
        return False, f"generation {rec['generation']} is not the latest ({latest['generation']})"
    if rec["cert_id"] in state.invalidated:
        return False, "invalidated by E5.5"
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
        if ugen != len(urecs):
            return False, f"upstream {uid} has a newer generation ({len(urecs)})"
        up = urecs[-1]
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
    basis = rec.get("basis")
    if basis is not None and basis != E63_BASIS_DECLARATION:
        return False
    v, crit = rec["verdict"], rec["criterion"]
    if v == "PASS":
        if rec["detector"].upper() == "NONE" or (
                not addition and state.facts.criteria.get(crit, {}).get("detector", "").upper() == "NONE"):
            return False            # detector NONE never reaches PASS (the record's own, or the registry's)
        if not addition and (crit.startswith("Null.") or crit == "Narr.fidelity_test"):
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


def _e63_asset_state(asset, state, disp, gaps):
    """(elevated?, terminal?) for one asset."""
    d = disp.get(asset)
    if d is not None and d["disposition"] in E63_TERMINAL_DISPOSITIONS and d["reason"]:
        return True, True                                                     # TERMINAL
    if d is None or d["disposition"] == "unresolved":                          # (4)
        return False, False
    layer = _e63_layer_of(asset, state.facts, f"asset {asset}")
    for gate, crits in state.facts.required(layer).items():                    # (1)
        if not crits:
            return False, False
        for c in crits:
            rec = (state.by_key.get(f"{asset}|gate|{c}") or [None])[-1]
            if rec is None or not _e63_satisfies(rec, state, addition=False):
                return False, False
    for a in d["additions"]:                                                   # (2)
        rec = (state.by_key.get(f"{asset}|addition|{a}") or [None])[-1]
        if rec is None or not _e63_satisfies(rec, state, addition=True):
            return False, False
    if any(_e63_gap_blocks(g, d["additions"], state.facts.info_families) for g in gaps.get(asset, ())):   # (3)
        return False, False
    return True, False


def elevated_assets(ref: str, repo: str) -> set:
    """The asset ids ELEVATED (plan 1.1) or terminally dispositioned, as of the ledgers committed at `ref`.

    Reads only `git -C repo show <ref>:<path>`; never the working tree or a database; no side effects. Raises
    ElevatedInputError (WatermarkOlderThanLedger for a stale E5.5 watermark) on any unreadable or malformed input.
    """
    sha = _e63_resolve_ref(ref, repo)
    facts = _e63_registry_facts(repo, sha)
    by_key, cert_lines = _e63_parse_certs(_e63_show(repo, sha, E63_CERTS_PATH), facts)
    invalidated, watermark = _e63_parse_invalidations(_e63_show(repo, sha, E63_INVALIDATIONS_PATH))
    _e63_check_watermark(watermark, cert_lines)
    gap_rows = _e63_parse_gaps(_e63_show(repo, sha, E63_GAPS_PATH))
    disp = _e63_parse_dispositions(_e63_show(repo, sha, E63_DISPOSITIONS_PATH), facts)
    for cid in invalidated:
        m = _E63_CERT_ID.fullmatch(cid)
        if f"{m.group(1)}|{m.group(2)}|{m.group(3)}" not in by_key:
            _e63_fail("malformed", f"{E63_INVALIDATIONS_PATH}: invalidation names {cid}, which is not in the certificate ledger")
    gaps = {}
    for g in gap_rows:
        gaps.setdefault(g["asset"], []).append(g)
    state = LedgerState(repo, sha, facts, by_key, invalidated)
    population = {k.split("|", 1)[0] for k in by_key} | set(disp)
    return {a for a in sorted(population) if _e63_asset_state(a, state, disp, gaps)[0]}


if __name__=="__main__": main()
