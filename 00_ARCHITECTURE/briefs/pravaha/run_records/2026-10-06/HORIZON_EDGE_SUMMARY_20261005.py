import json, collections, sys
from datetime import datetime, timezone
UTC = timezone.utc
rows = json.load(open("/Users/Dev/pravaha/run/HORIZON_EDGE_STRETCHES_20261005.json"))
D0, D1 = datetime(1998, 1, 1, tzinfo=UTC), datetime(2085, 1, 1, tzinfo=UTC)
def summary(name, H0, H1):
    c = collections.Counter(); detail = collections.defaultdict(list)
    for r in rows:
        A = datetime.fromisoformat(r["A"]); B = datetime.fromisoformat(r["B"])
        if not (A < H1 and B > H0): continue
        cs = [datetime.fromisoformat(x) for x in r["crossings"]]
        in_h = [x for x in cs if H0 <= x < H1]
        dom_s, dom_e = A <= D0, B >= D1
        clip_s, clip_e = (A < H0) or dom_s and H0 <= D0, (B > H1) or dom_e and H1 >= D1
        dom = dom_s or dom_e
        c["stretches overlapping the horizon"] += 1
        key = (r["agent"], r["rel"], r["target"][6:12], A.date().isoformat(), B.date().isoformat())
        if clip_s or clip_e or dom:
            c["CLIPPED at either edge"] += 1
            if clip_s: c["  clipped at start"] += 1
            if clip_e: c["  clipped at end"] += 1
            if dom: c["  touch the builder's DOMAIN edge (crossing beyond it unknowable)"] += 1; detail["domain-clipped"].append(key + (len(cs), len(in_h)))
            elif in_h: c["  exact crossing INSIDE the horizon (case 1)"] += 1; detail["case1"].append(key)
            elif cs: c["  crossing only OUTSIDE the horizon (clipped contact, t_exact None)"] += 1; detail["outside-only"].append(key)
            else: c["  clipped GRAZE, no crossing anywhere (case 2)"] += 1; detail["case2"].append(key)
            if r["cut_inside"]: c["  clipped AND a wrap cut inside the stretch"] += 1
            if r["stations"]: c["  clipped AND a station inside"] += 1
        else:
            c["unclipped"] += 1
            if not cs: c["  unclipped GRAZE"] += 1
            elif r["stations"]: c["  unclipped SEAM (station inside)"] += 1
            else: c["  unclipped plain"] += 1
            if r["cut_inside"]: c["  unclipped with a WRAP CUT crossed inside"] += 1; detail["wrapcut"].append(key)
    print("=====", name, H0.date(), "to", H1.date())
    for k, v in c.items(): print("  ", k, v)
    for k, v in detail.items():
        if k in ("case2", "domain-clipped", "case1", "wrapcut", "outside-only") and len(v) <= 14: print("   DETAIL", k, v)
for name, a, b in [("RUN 1 (all_classes_1y)", (2025,4,17), (2026,4,17)), ("FULL scored horizon", (1998,1,1), (2026,4,17)),
                   ("steward (c): domain horizon", (1998,1,1), (2084,12,31)), ("OWNER RULING 7, start 1998-02-16", (1998,2,16), (2084,2,5)),
                   ("OWNER RULING 7, start = today 2026-10-05", (2026,10,5), (2084,2,5))]:
    summary(name, datetime(*a, tzinfo=UTC), datetime(*b, tzinfo=UTC))
