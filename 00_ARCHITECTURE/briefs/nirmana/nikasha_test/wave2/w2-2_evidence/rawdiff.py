import json, sys, collections
S = sys.argv[1]
def load(w, L):
    d = json.load(open(f"{S}/census/{w}_{L}.json"))[L]
    return d, {a["asset_id"]: a for a in d["assets"]}
chg = []; text = collections.Counter(); tallies = {}
for L in "L0 L1 L2 L3 L4 L5".split():
    bd, B = load("base", L); hd, H = load("head", L)
    tb = collections.Counter(m["v"] for a in B.values() for m in a["measurements"].values())
    th = collections.Counter(m["v"] for a in H.values() for m in a["measurements"].values())
    tallies[L] = (bd["n_assets"], hd["n_assets"], tb, th)
    for aid in sorted(set(B) | set(H)):
        bm = B.get(aid, {}).get("measurements", {}); hm = H.get(aid, {}).get("measurements", {})
        for crit in sorted(set(bm) | set(hm)):
            b = bm.get(crit, {}).get("v", "<absent>"); h = hm.get(crit, {}).get("v", "<absent>")
            if b == h:
                if bm.get(crit, {}).get("measured") != hm.get(crit, {}).get("measured"):
                    text[(L, crit)] += 1
                continue
            chg.append((L, aid, crit, b, h, bm.get(crit, {}).get("measured", ""), hm.get(crit, {}).get("measured", "")))
for L, (nb, nh, tb, th) in tallies.items():
    print(L, nb, nh, "base", dict(sorted(tb.items())), "\n        head", dict(sorted(th.items())))
print("changes", len(chg))
c = collections.Counter((x[2], x[3], x[4]) for x in chg)
for k, v in sorted(c.items()): print(v, k)
json.dump(chg, open(f"{S}/census/changes.json", "w"), indent=0)
print("text-only", sum(text.values()), dict(sorted(text.items())))
