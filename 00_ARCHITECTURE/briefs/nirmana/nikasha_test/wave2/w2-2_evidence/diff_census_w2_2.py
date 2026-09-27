#!/usr/bin/env python3
"""W2-2 Proof 2: per-asset verdict diff, 931dbc479 (base) vs HEAD, grouped by cause; text-only changes by cause."""
import json, sys, collections
S = sys.argv[1]
FAV = ("PASS", "N/A")
def load(w, L):
    d = json.load(open(f"{S}/census/{w}_{L}.json"))[L]
    return d, {a["asset_id"]: a for a in d["assets"]}
def cause(crit, b, h, hm):
    if crit == "Build.registered" and b == "FAIL" and h == "PASS": return "R43 writer recognised (constant / package / shim import) — FAIL->PASS"
    if crit == "Build.contract" and b == "NO_DETECTOR": return f"R43 writer recognised, contract scan now runs — NO_DETECTOR->{h}"
    if crit == "Idem.pattern" and b == "NO_DETECTOR": return f"R43 writer recognised, idempotency scan now runs — NO_DETECTOR->{h}"
    if crit == "Build.dep_liveness" and h == "PARTIAL" and "stale" in hm: return f"R45 chart-scoped liveness, stale dependency — {b}->PARTIAL"
    if crit == "Build.target" and b == "N/A" and h == "PASS": return "R53 target-less writer graded on the engine's produced-table rule — N/A->PASS"
    if crit == "Dens.served" and h == "NO_DETECTOR" and "comments only" in hm: return f"R51 comment-only attribution — {b}->NO_DETECTOR"
    if crit == "Dens.served" and b == "PASS" and h == "FAIL": return "R51 module attribution by code (the only declaring module named the table in a comment) — PASS->FAIL"
    return f"UNEXPLAINED {crit} {b}->{h}"
def tcause(L, crit, bm, hm):
    if crit in ("Earn.build_record", "Cost.baseline"): return "D6 item 2: NO_DETECTOR text now names the linked attempt"
    if crit == "Build.dep_liveness": return "R45: text names the chart scope measured"
    if crit == "Build.history": return "R49 latest dated error / R233+R50 exact tallies"
    if crit == "Build.exercised": return "R233: executed count now newline-safe (was undercounted)"
    if crit == "Dens.served": return "R51: module list attributed by code"
    if crit == "Vocab.alias": return "R54: measured fraction stated"
    if crit in ("Build.completion", "Count.floor"): return "R46: bo_samvada counted by its view"
    return "OTHER"
out = collections.defaultdict(list); text = collections.defaultdict(collections.Counter); tallies = {}; fav = []
for L in "L0 L1 L2 L3 L4 L5".split():
    bd, B = load("base", L); hd, H = load("head", L)
    tb = collections.Counter(m["v"] for a in B.values() for m in a["measurements"].values())
    th = collections.Counter(m["v"] for a in H.values() for m in a["measurements"].values())
    tallies[L] = (bd["n_assets"], hd["n_assets"], tb, th)
    for aid in sorted(set(B) | set(H)):
        bm = B.get(aid, {}).get("measurements", {}); hm = H.get(aid, {}).get("measurements", {})
        for crit in sorted(set(bm) | set(hm)):
            b = bm.get(crit, {}).get("v", "<absent>"); h = hm.get(crit, {}).get("v", "<absent>")
            bt = bm.get(crit, {}).get("measured", ""); ht = hm.get(crit, {}).get("measured", "")
            if b == h:
                if bt != ht: text[tcause(L, crit, bt, ht)][(L, crit)] += 1
                continue
            c = cause(crit, b, h, ht)
            out[c].append(f"{L} {aid} {crit}: {b} -> {h} | {ht[:170]}")
            if h in FAV and b not in FAV: fav.append(f"{L} {aid} {crit}: {b} -> {h} | {ht[:170]}")
            if h in FAV and b in FAV: fav.append(f"(closable->closable) {L} {aid} {crit}: {b} -> {h} | {ht[:170]}")
def s(c): return " ".join(f"{k}={c.get(k,0)}" for k in ("PASS","N/A","FAIL","PARTIAL","NO_DETECTOR","ERRORED","NOT_GENERIC"))
for L, (nb, nh, tb, th) in tallies.items():
    print(f"{L}: assets {nb} -> {nh}\n   931dbc479 {s(tb)}\n   HEAD      {s(th)}")
print(f"\nVERDICT CHANGES: {sum(len(v) for v in out.values())}; UNEXPLAINED: {sum(len(v) for k, v in out.items() if k.startswith('UNEXPLAINED'))}\n")
for c in sorted(out):
    print(f"### {c}: {len(out[c])}")
    for x in out[c]: print("   ", x)
print(f"\n### FAVOURABLE flips (-> PASS or N/A): {len(fav)}")
for x in fav: print("   ", x)
print(f"\n### text-only changes (verdict unchanged): {sum(sum(c.values()) for c in text.values())}")
for k, c in sorted(text.items()): print(f"   {k}: {sum(c.values())}  {dict(sorted(c.items()))}")
