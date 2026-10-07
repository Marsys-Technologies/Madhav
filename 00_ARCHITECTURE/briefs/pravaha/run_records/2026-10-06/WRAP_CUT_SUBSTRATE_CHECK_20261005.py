"""READ-ONLY (no database): the sky-event substrate's boundary roots (the input of the production residence spans) vs independent sampling, per body, 1998-2085:
completeness (every sampled sign/aspect-boundary change contains a root), validity (the Swiss longitude at each root is at its level), uniqueness (no twins), reported separately for the 0/360 wrap level and every other level."""
import sys, os, collections
from datetime import datetime, timezone, timedelta
S = "/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/b494bf37-e4fb-4e8f-b5fd-87e2fcc3f095/scratchpad/wt-p1/platform/python-sidecar"
sys.path.insert(0, S); os.chdir(S)
os.environ["SE_EPHE_PATH"] = "/Users/Dev/suvarna-evidence/Se1"
from services.gochara_kernel import arcs as gk_arcs, contacts as gk_contacts, substrate as sub
from services.gochara_kernel.knots import calc_sidereal_lon, sample_knots
EPHE = os.environ["SE_EPHE_PATH"]; JD0 = 2440587.5
def lon(body, jd):
    l, fl = calc_sidereal_lon(body, jd, EPHE); assert fl & 2; return l
bodies = sys.argv[1:] or list(sub.SUBSTRATE_BODIES)
j0 = sub.SUBSTRATE_DOMAIN_START.timestamp() / 86400.0 + JD0; j1 = sub.SUBSTRATE_DOMAIN_END.timestamp() / 86400.0 + JD0
for body in bodies:
    ks = sample_knots(body, sub.SUBSTRATE_DOMAIN_START.date(), sub.SUBSTRATE_DOMAIN_END.date(), EPHE)
    idx = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)
    roots = []
    for rel in sub.DB_EVENT_KIND:
        roots += [(rel, r) for r in gk_contacts.find_boundary_roots(idx, body, rel, EPHE, refine=True)]
    levels = sorted({round(r.level_deg % 360.0, 6) for _, r in roots})
    st = collections.Counter()
    # validity + twins
    byl = collections.defaultdict(list)
    for rel, r in roots:
        L = r.level_deg % 360.0; byl[(rel, round(L, 6))].append(r.exact_jd)
        d = ((lon(body, r.exact_jd) - L + 180) % 360) - 180
        if abs(d) > 1e-4: st["invalid_root_" + ("wrap" if L == 0 else "other")] += 1
    for k, v in byl.items():
        v.sort()
        for a, b in zip(v, v[1:]):
            if b - a < 1.0: st["twin_" + ("wrap" if k[1] == 0 else "other")] += 1
    # completeness by sampling every 6 h, per distinct level
    step = 0.25; n = int((j1 - j0) / step)
    prev = lon(body, j0); allroots = sorted(r.exact_jd for _, r in roots)
    import bisect
    lv_all = sorted({r.level_deg % 360.0 for _, r in roots})
    for i in range(1, n + 1):
        t = j0 + i * step; cur = lon(body, t); dlt = ((cur - prev + 180) % 360) - 180
        for L in lv_all:
            a = ((prev - L + 180) % 360) - 180; b = ((cur - L + 180) % 360) - 180
            if (a < 0 <= b) or (b < 0 <= a):
                if abs(a) > 90 or abs(b) > 90: continue
                k = bisect.bisect_left(allroots, t - step - 1e-6)
                found = k < len(allroots) and allroots[k] <= t + 1e-6
                st["crossings_" + ("wrap" if L == 0 else "other")] += 1
                if not found: st["MISSED_" + ("wrap" if L == 0 else "other")] += 1
        prev = cur
    print(body, "levels", len(levels), "roots", len(roots), dict(st), flush=True)
