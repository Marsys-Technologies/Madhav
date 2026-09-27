#!/usr/bin/env python3
"""Per-asset verdict diff base (9baaa307b) vs head, grouped by cause."""
import json, sys, collections
S = sys.argv[1]
def load(p, L):
    d = json.load(open(p))[L]
    return d, {a["asset_id"]: a for a in d["assets"]}
def cause(crit, b, h, hm):
    if b == "<absent-asset>": return "R224: asset newly measured (lel_events)"
    if crit == "Build.completion":
        if "empty: live=0" in hm and h == "FAIL": return f"R52 non-emptiness ({b}->FAIL)"
        if "is not a completed build" in hm: return f"R42 completed-state guard ({b}->FAIL)"
        if "reads no table" in hm: return f"R42 constant count_sql ({b}->NO_DETECTOR)"
        if "disagrees with" in hm: return f"R42 rows_written vs live compared ({b}->FAIL)"
        if b == "ERRORED": return f"R231 chart bound: measured ({b}->{h})"
        if b == "N/A" and h == "N/A": return "text only (R222 N/A reason restated)"
        if "no build record" in hm: return f"R231 chart-scoped build record ({b}->{h})"
    if crit == "Count.floor":
        if b == "<absent>" and "no floor to breach" in hm: return "R48 declared floor=0 -> N/A (was absent)"
        if b == "<absent>" and h in ("PASS","FAIL"): return f"R231+R56 floor now measured (absent->{h})"
        if b == "<absent>": return f"R48/R56 declared floor now graded (absent->{h})"
        if b == "PASS" and h == "N/A": return "R48 floor=0 vacuous PASS -> N/A"
    if crit in ("Build.contract", "Idem.pattern") and h == "NO_DETECTOR" and b == "N/A": return "R222 N2 unrecognised writer (N/A->NO_DETECTOR)"
    if crit == "Complete.depth" and h == "NO_DETECTOR": return f"R222 N5 empty table ({b}->NO_DETECTOR)"
    if crit == "Vocab.identity" and h == "NO_DETECTOR": return f"R222 N5 identity on empty table ({b}->NO_DETECTOR)"
    if crit == "Dens.served" and h == "NO_DETECTOR": return "R222 N3"
    return f"UNEXPLAINED {crit} {b}->{h}"
out = collections.defaultdict(list); text_only = collections.Counter(); tallies = {}
for L in "L0 L1 L2 L3 L4 L5".split():
    bd, B = load(f"{S}/census/base_{L}.json", L); hd, H = load(f"{S}/census/head_{L}.json", L)
    tb = collections.Counter(m["v"] for a in B.values() for m in a["measurements"].values())
    th = collections.Counter(m["v"] for a in H.values() for m in a["measurements"].values())
    tallies[L] = (bd["n_assets"], hd["n_assets"], dict(tb), dict(th))
    for aid in sorted(set(B) | set(H)):
        bm = B.get(aid, {}).get("measurements", {}); hm = H.get(aid, {}).get("measurements", {})
        for crit in sorted(set(bm) | set(hm)):
            b = bm.get(crit, {}).get("v", "<absent>") if aid in B else "<absent-asset>"
            h = hm.get(crit, {}).get("v", "<absent>") if aid in H else "<absent-asset>"
            if b == h:
                if bm.get(crit, {}).get("measured") != hm.get(crit, {}).get("measured"):
                    text_only[(L, crit)] += 1
                continue
            c = cause(crit, b, h, hm.get(crit, {}).get("measured", ""))
            out[c].append(f"{L} {aid} {crit}: {b} -> {h} | {hm.get(crit, {}).get('measured', '')[:150]}")
for L, (nb, nh, tb, th) in tallies.items():
    print(f"{L}: assets {nb} -> {nh}\n   base {dict(sorted(tb.items()))}\n   head {dict(sorted(th.items()))}")
print()
for c in sorted(out):
    print(f"### {c}: {len(out[c])}")
    for x in out[c]: print("   ", x)
print("\n### text-only changes (verdict unchanged):", dict(text_only))
