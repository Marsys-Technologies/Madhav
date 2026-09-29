import json, sys, collections
b = json.load(open(sys.argv[1])); h = json.load(open(sys.argv[2]))
def flat(c):
    return {(L, a["asset_id"], k): v for L, d in c.items() for a in d["assets"] for k, v in a["measurements"].items()}
fb, fh = flat(b), flat(h)
print("verdicts base", len(fb), "head", len(fh), "keys equal:", set(fb) == set(fh))
vchg = [(k, fb[k]["v"], fh[k]["v"]) for k in fb if k in fh and fb[k]["v"] != fh[k]["v"]]
tchg = [k for k in fb if k in fh and fb[k]["v"] == fh[k]["v"] and fb[k]["measured"] != fh[k]["measured"]]
print("verdict changes:", len(vchg), collections.Counter((k[2], x, y) for k, x, y in vchg))
print("text-only changes:", len(tchg), collections.Counter(k[2] for k in tchg))
fav = [(k, x, y) for k, x, y in vchg if y in ("PASS", "N/A")]
print("favourable (->PASS/N/A):", len(fav))
for k, x, y in sorted(vchg): print("  ", k[0], k[1], k[2], x, "->", y)
# text-only change breakdown outside Idem/Reach
for k in tchg:
    if k[2] not in ("Idem.pattern", "Reach.fields"):
        print("  TEXT", k, "|", fb[k]["measured"][:120], "=>", fh[k]["measured"][:120])
