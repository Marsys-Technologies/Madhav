#!/usr/bin/env python3
"""Append one event to the Kāla elevation ledger. The ONLY sanctioned writer.

    python3 00_ARCHITECTURE/control/kala_record_event.py \
        --asset ka_sangam --event started --session madhav-xx \
        [--commit <sha>] [--branch <name>] [--evidence <path|url>] \
        [--brief-version 1.5] [--note "..."]

Append-only by construction: opens 'a', writes one line, never rewrites. Refuses an
unknown asset id or event, and refuses 'verified' unless a 'completed' already exists
for that asset — the strategy session verifies execution, not itself.
"""
import argparse, datetime, io, json, os, subprocess, sys

ROOT   = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip() or "."
LEDGER = os.path.join(ROOT,"00_ARCHITECTURE/control/kala_elevation_ledger.jsonl")
EVENTS = {"handoff","started","completed","blocked","verified","reverted"}
ASSETS = {"ka_kshetra","ka_sangam","ka_gochara","ka_gochara_v3_century_materialize",
 "ka_gochara_resonance","ka_vedha_gochara","ka_moorti_nirnaya","ka_kota_chakra",
 "ka_tithi_pravesha","ka_yojaka","ka_kalasutra","ka_vighnakara","ka_kala_darshana",
 "ka_jivana_parva","ka_bhavishya_lekha","ka_dasha_kala","ka_graha_sancara",
 "ka_muhurta_seva","ka_tulana","ka_avadhi","ka_sudarshana_varsha","ka_taranga"}

def existing(asset):
    if not os.path.exists(LEDGER): return []
    out=[]
    for line in io.open(LEDGER,encoding="utf-8"):
        line=line.strip()
        if not line: continue
        try: r=json.loads(line)
        except Exception: continue
        if r.get("asset")==asset: out.append(r)
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--asset",required=True); p.add_argument("--event",required=True)
    p.add_argument("--session",required=True); p.add_argument("--commit"); p.add_argument("--branch")
    p.add_argument("--evidence"); p.add_argument("--brief-version"); p.add_argument("--note")
    a=p.parse_args()
    if a.asset not in ASSETS: sys.exit(f"refused: unknown asset {a.asset!r}")
    if a.event not in EVENTS: sys.exit(f"refused: unknown event {a.event!r} (allowed: {sorted(EVENTS)})")
    prior=[r.get("event") for r in existing(a.asset)]
    if a.event=="verified" and "completed" not in prior:
        sys.exit("refused: cannot verify an asset with no 'completed' event — "
                 "the execution session reports completion, the strategy session verifies it")
    rec={"ts":datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
         "asset":a.asset,"event":a.event,"session":a.session}
    for k,v in (("commit",a.commit),("branch",a.branch),("evidence",a.evidence),
                ("brief_version",a.brief_version),("note",a.note)):
        if v: rec[k]=v
    with io.open(LEDGER,"a",encoding="utf-8") as f:
        f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    print(json.dumps(rec,ensure_ascii=False))
    print(f"appended -> {os.path.relpath(LEDGER,ROOT)} (prior events for this asset: {prior or 'none'})")

if __name__=="__main__": main()
