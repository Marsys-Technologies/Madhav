#!/usr/bin/env python3
"""Kāla (L3) brief-elevation tracker — scans all 22 assets against the five-tier criteria.

Writes kala_brief_tracker.json next to kala_brief_tracker.html. Re-run to refresh;
the HTML polls the JSON, so an open browser tab updates without a reload.

    python3 00_ARCHITECTURE/control/kala_brief_tracker.py            # one pass
    python3 00_ARCHITECTURE/control/kala_brief_tracker.py --watch    # rescan every 10s

A tick means the brief ADDRESSES the criterion (marker detection), not that it
addresses it well. This is a coverage tracker, not a quality verdict.
"""
import argparse, datetime, glob, io, json, os, re, subprocess, sys, time

ROOT = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip() or "."
BR   = os.path.join(ROOT,"00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs")
OUT  = os.path.join(ROOT,"00_ARCHITECTURE/control/kala_brief_tracker.json")

TIERS = {
 "T1":("Ten analysis lenses (A–J)",[
   ("A","identity",r"\bidentity\b|asset[- ]id|epistemic"),
   ("B","inputs / DAG",r"\bDAG\b|upstream|declared input"),
   ("C","correctness",r"invariant|correctness"),
   ("D","data sufficiency",r"data sufficien|coverage|row count"),
   ("E","consumers",r"consumer|downstream|reader"),
   ("F","AI / product",r"product|AI|serving question"),
   ("G","efficiency",r"efficienc|cost|latency|hotspot"),
   ("H","reliability",r"reliab|idempoten|timeout|failure"),
   ("I","change packet",r"may_touch|change packet|files"),
   ("J","final evidence",r"evidence|proof|detector")]),
 "T2":("Six elevation lenses",[
   ("Val","value extraction",r"latent[- ]value|value extraction"),
   ("Tgt","target-state design",r"target[- ]state|disposition and target"),
   ("Eff","efficiency w/ quality",r"equivalen|justified no-change|no measured hotspot|cost"),
   ("Syn","synergy obligations",r"OFFERS|DEMANDS|synergy oblig"),
   ("Walk","consumer walkthrough",r"walkthrough|Product §9|end[- ]to[- ]end"),
   ("KTime","knowledge-time",r"knowledge[- ]time|F15|F17|DP15a|as_of")]),
 "T3":("Strategy alignment",[
   ("PD","Product Definition",r"Product Definition|PD v[0-9]|Product §9|PD slice"),
   ("VA","data-plane VA",r"data[- ]plane|DP-SD-|VA §"),
   ("Lyr","layer strategy",r"Strategy §|Kāla Strategy|DP-SD-017|layer contract"),
   ("Bind","synergy binding",r"synergy_binding|SYNERGY_BINDING|binding v[0-9]"),
   ("U/D","upstream / downstream",r"upstream|downstream|L1 authority|§N\.5"),
   ("Srv","serving contract",r"serv(ing|ed) (contract|surface|route)|serve-time|serving path")]),
 "T4":("Discipline gates",[
   ("Fct","facts / interpretation",r"B\.1\b|facts/interpretation|epistemic_class"),
   ("Ldgr","derivation ledger",r"DERIVATION_LEDGER|derivation ledger|constituent_facts|fact_id"),
   ("Idem","idempotency",r"idempoten"),
   ("Earn","earned signal",r"§N\.8|earned[- ]signal|real detector|detector that (can )?fails?"),
   ("Narr","narration fidelity",r"§N\.7|narration"),
   ("Dens","serving density",r"§N\.6|densit|catalog_only|hardFloor"),
   ("Null","honest null",r"honest null|honest absence|honest(ly)? (empty|zero|tier)|null rather than")]),
 "T5":("The two ladders",[
   ("DPL","data-plane ladder",r"PLAN_REVIEWED|PRODUCER_READY|DATA_ACCEPTED"),
   ("CmL","campaign ladder",r"ANALYZED|ENRICHED|QUALIFIED|FROZEN")]),
}

# Stream artifacts live on their own branches; ref -> repo-relative paths, concatenated.
STREAM = {
 "ka_kshetra": ("origin/l3/kshetra-stage3-authorized",
                ["00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_ELEVATION_BRIEF_v1_0.md"]),
 "ka_sangam":  ("origin/sangam/stage3",
                ["00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ELEVATION_BRIEF_v1_0.md",
                 "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md"]),
 "ka_gochara": ("origin/l3/gochara-autonomous-wp0-7",
                ["00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_FAMILY_ELEVATION_BRIEF_v1_2.md",
                 "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md"]),
}
MINE = "%s/KA_{U}_ELEVATION_BRIEF_v1_0.md" % BR

ASSETS = [
 (1,"ka_kshetra","stream","stream","Kṣetra stream — own packet + ruling sheet"),
 (2,"ka_sangam","stream","stream","Saṅgam stream — brief + algorithm plan"),
 (3,"ka_gochara","family head","stream","Gochara family head — brief + family plan"),
 (4,"ka_gochara_v3_century_materialize","family","inherit:ka_gochara","no standalone brief — row in family plan §2"),
 (5,"ka_gochara_resonance","family","inherit:ka_gochara","no standalone brief — row in family plan §2"),
 (6,"ka_vedha_gochara","family","inherit:ka_gochara","no standalone brief — row in family plan §2"),
 (7,"ka_moorti_nirnaya","family + layer","mine","overlaps Gochara family — ingress-instant grading built there"),
 (8,"ka_kota_chakra","family + layer","mine",""),
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

def git_show(ref, paths):
    parts=[]
    for p in paths:
        r=subprocess.run(["git","-C",ROOT,"show",f"{ref}:{p}"],capture_output=True,text=True)
        if r.returncode==0: parts.append(r.stdout)
    return "\n".join(parts)

def load(aid, kind):
    if kind=="stream":
        ref,paths=STREAM[aid]; return git_show(ref,paths), f"{ref}"
    if kind.startswith("inherit:"):
        src=kind.split(":",1)[1]; ref,paths=STREAM[src]
        return git_show(ref,paths), f"{ref} (inherited)"
    p=MINE.replace("{U}", aid[3:].upper())
    if os.path.exists(p): return io.open(p,encoding="utf-8",errors="replace").read(), "this branch"
    return "", "MISSING"

def reviews(aid):
    fs=sorted(glob.glob(os.path.join(BR,"reviews",f"REVIEW_{aid.upper()}_v*.md")))
    if not fs: return 0,"—"
    m=re.search(r"\b(ACCEPT_WITH_CORRECTIONS|REWORK|ACCEPT)\b", io.open(fs[-1],encoding="utf-8").read())
    return len(fs), (m.group(1) if m else "?")

def scan():
    crit=[]
    for t,(tname,items) in TIERS.items():
        for k,label,_ in items: crit.append({"tier":t,"tier_name":tname,"key":k,"label":label})
    assets=[]
    for n,aid,group,kind,note in ASSETS:
        text,origin=load(aid,kind)
        ver=(re.search(r'^version:\s*"?([^"\n]+)',text,re.M) or [None,"—"])[1].strip().strip('"')
        st =(re.search(r'^status:\s*([^\n#]+)',text,re.M) or [None,"—"])[1].strip()
        cells={}
        for t,(tname,items) in TIERS.items():
            for k,label,pat in items:
                hit=bool(re.search(pat,text,re.I))
                if t=="T1":
                    m=re.search(r"^\|\s*"+re.escape(k)+r"\s+[^|]*\|(.*)$",text,re.M)
                    ans=m.group(1).strip().strip("|").strip() if m else ""
                    hit = hit or (len(ans)>12 and ans not in {"—","-","n/a","·"})
                cells[k]=hit
        nrev,verd=reviews(aid)
        if kind=="stream" or kind.startswith("inherit:"):
            # stream reviews are external (Astra / Kimi K3) and are not stored in this tree;
            # reporting 0 here would read as "unreviewed", which is false.
            verd="external"; nrev=-1
        assets.append({"n":n,"id":aid,"group":group,"kind":kind,"note":note,"origin":origin,
            "ver":ver,"status":st,"reviews":nrev,"verdict":verd,"cells":cells,
            "score":sum(cells.values()),"total":len(cells),"found":bool(text)})
    cov={c["key"]:sum(1 for a in assets if a["cells"][c["key"]]) for c in crit}
    return {"generated":datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "criteria":crit,"assets":assets,"coverage":cov,"n_assets":len(assets)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--watch",action="store_true"); ap.add_argument("--interval",type=int,default=10)
    a=ap.parse_args()
    while True:
        d=scan(); js=json.dumps(d,indent=1)
        io.open(OUT,"w").write(js)
        # also emit a .js so the page works from file:// where fetch() is blocked
        io.open(OUT[:-5]+".js","w").write("window.KALA_DATA="+js+";\nwindow.dispatchEvent(new Event('kala-data'));\n")
        gaps=sorted(((v,k) for k,v in d["coverage"].items()))[:4]
        print(f'[{d["generated"]}] {d["n_assets"]} assets scanned -> {OUT}')
        print("  weakest columns: "+", ".join(f"{k} {v}/{d['n_assets']}" for v,k in gaps))
        if not a.watch: break
        time.sleep(a.interval)

if __name__=="__main__": main()
