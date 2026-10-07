"""READ-ONLY, no build: with the real natal longitudes (one read-only SELECT of L1 chart_facts) and the pinned ephemeris, count over 1998-01-01..2026-04-17 the
in-band intervals of the P3/P4 point contacts: plain / with a station inside (seam) / graze (no exact crossing) / partial (some arc piece without a root) / horizon-clipped."""
import sys, os, json, collections
from datetime import datetime, timezone, timedelta
S = "/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/b494bf37-e4fb-4e8f-b5fd-87e2fcc3f095/scratchpad/wt-p1/platform/python-sidecar"
sys.path.insert(0, S); os.chdir(S)
os.environ["SE_EPHE_PATH"] = "/Users/Dev/suvarna-evidence/Se1"
import psycopg
from services.gochara_kernel.chart_context import fetch_chart_context
from services.gochara_kernel import evaluator as ev, contact_certify as cc
from services.gochara_kernel.knots import calc_sidereal_lon
from services.gochara_kernel import rule_registry as gk_rule_registry
from services.gochara_kernel.window_verifier import _ASPECT_ANGLES, _POINT_ORB_DEG
from pipeline.orchestrator.writers import ka_gochara_v5 as w
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
conn = psycopg.connect("", options="-c default_transaction_read_only=on", autocommit=True)
assert conn.execute("SHOW transaction_read_only").fetchone()[0] == "on"
ctx = fetch_chart_context(conn, CHART)
conn.close()
natal = ctx["natal"]; lagna = ctx["lagna_deg"]
print("natal (Title: lon):", {k: round(v, 4) for k, v in natal.items()}, "lagna", lagna, "missing", ctx["operands_missing"])
chart = {"lagna_deg": lagna, "natal": natal}
UTC = timezone.utc
LO, HI = w.DEFAULT_HORIZON
keys = collections.defaultdict(set)
for cls in w.SCORED_CLASSES:
    for path in ("P3", "P4"):
        ver = gk_rule_registry.selected_path_version(cls, path)
        for e in ev.enumerate_edges(cls, path, chart, rule_version=ver):
            if e.transit and e.obj.canonical_target.startswith("point:") and e.relation in ("conjunction", "aspect") and e.agent != "moon":
                keys[(e.agent, e.relation, e.obj.canonical_target)].add((cls, path))
print("distinct (agent, relation, point target) obligations:", len(keys), "| classes with P3/P4 point edges:", len({c for v in keys.values() for c, _ in v}))
JD0 = 2440587.5
def pos(body, t):
    lon, fl = calc_sidereal_lon(body.title(), t.timestamp() / 86400.0 + JD0, os.environ["SE_EPHE_PATH"])
    assert fl & 2
    return lon
pos.cache_key = ("swiss", os.environ["SE_EPHE_PATH"])

import json, bisect
from services.gochara_kernel import contact_reconstruct as cr, arcs as gk_arcs
from services.gochara_kernel.record_store import jd_to_utc
D0, D1 = w.SUBSTRATE_DOMAIN_START, w.SUBSTRATE_DOMAIN_END
idx_cache = {}
def index_for(body):
    if body not in idx_cache:
        ks = w.sample_knots(body, D0.date(), D1.date(), os.environ["SE_EPHE_PATH"])
        idx_cache[body] = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)
    return idx_cache[body]
rows = []
HOUR = timedelta(hours=1)
for (agent, rel, target), users in sorted(keys.items()):
    lam = float(target.split(":", 1)[1]); angles = (0.0,) if rel == "conjunction" else _ASPECT_ANGLES[agent]
    levels = [(lam - a) % 360.0 for a in angles]; orb = _POINT_ORB_DEG[rel]
    idx = index_for(agent.title())
    for (A, B) in cr.band_intervals(pos, agent, levels, orb, D0, D1):
        n = max(3, int((B - A).total_seconds() // 3600) + 2)
        ts = [A + (B - A) * k / (n - 1) for k in range(n)]; ls = [pos(agent, t) for t in ts]
        best = min(levels, key=lambda lv: min(abs(((x - lv + 180) % 360) - 180) for x in ls))
        d = [((x - best + 180) % 360) - 180 for x in ls]
        cross = []
        for i in range(n - 1):
            if (d[i] < 0 <= d[i + 1]) or (d[i + 1] < 0 <= d[i]) or d[i] == 0:
                lo_t, hi_t = ts[i], ts[i + 1]
                f_lo = d[i]
                for _ in range(40):
                    mid = lo_t + (hi_t - lo_t) / 2; fm = ((pos(agent, mid) - best + 180) % 360) - 180
                    if (fm < 0) == (f_lo < 0): lo_t, f_lo = mid, fm
                    else: hi_t = mid
                cross.append((lo_t + (hi_t - lo_t) / 2).isoformat())
        v = [((ls[i + 1] - ls[i] + 180) % 360) - 180 for i in range(n - 1)]
        stations = sum(1 for i in range(len(v) - 1) if (v[i] > 0) != (v[i + 1] > 0))
        ja, jb = A.timestamp() / 86400.0 + JD0, B.timestamp() / 86400.0 + JD0
        ua, ub = idx.evaluate(ja), idx.evaluate(jb)
        cut_inside = int(max(ua, ub) // 360.0) > int(min(ua, ub) // 360.0)
        touches_cut = min(best, 360.0 - best) < orb
        rows.append(dict(agent=agent, rel=rel, target=target, A=A.isoformat(), B=B.isoformat(), crossings=cross, stations=stations, cut_inside=cut_inside, touches_cut=touches_cut, level=round(best, 4)))
json.dump(rows, open("/Users/Dev/pravaha/run/HORIZON_EDGE_STRETCHES_20261005.json", "w"))
print("stretches over the domain:", len(rows))
UTC_ = timezone.utc
def horizon_summary(name, H0, H1):
    c = collections.Counter(); detail = collections.defaultdict(list)
    for r in rows:
        A = datetime.fromisoformat(r["A"]); B = datetime.fromisoformat(r["B"])
        if not (A < H1 and B > H0): continue
        cs = [datetime.fromisoformat(x) for x in r["crossings"]]
        in_h = [x for x in cs if H0 <= x < H1]
        clip_s = A < H0; clip_e = B > H1
        dom = A <= D0 or B >= D1
        c["stretches overlapping the horizon"] += 1
        key = (r["agent"], r["rel"], r["target"][6:12], A.date().isoformat(), B.date().isoformat())
        if clip_s or clip_e:
            c["CLIPPED at either edge"] += 1
            c["  clipped at start" ] += 1 if clip_s else 0; c["  clipped at end"] += 1 if clip_e else 0
            if dom: c["  of which touch the builder's DOMAIN edge (crossing beyond it unknowable)"] += 1; detail["domain-clipped"].append(key)
            elif in_h: c["  clipped, exact crossing INSIDE the horizon (case 1)"] += 1; detail["case1"].append(key)
            elif cs: c["  clipped, crossing only OUTSIDE the horizon (clipped contact, t_exact None)"] += 1; detail["outside-only"].append(key)
            else: c["  clipped GRAZE (no crossing anywhere) (case 2)"] += 1; detail["case2"].append(key)
            if r["cut_inside"]: c["  clipped AND a wrap cut inside the stretch"] += 1
            if r["stations"]: c["  clipped AND a station inside"] += 1
        else:
            c["unclipped"] += 1
            if not cs: c["  unclipped GRAZE"] += 1
            elif r["stations"]: c["  unclipped SEAM (station inside the stretch)"] += 1
            else: c["  unclipped plain"] += 1
            if r["cut_inside"]: c["  unclipped with a WRAP CUT crossed inside"] += 1; detail["wrapcut"].append(key)
    print("=====", name, H0.date(), "to", H1.date())
    for k, v in c.items(): print("  ", k, v)
    for k, v in detail.items():
        if k in ("case2", "domain-clipped", "case1", "wrapcut") and len(v) <= 12: print("   DETAIL", k, v)
horizon_summary("RUN 1 (all_classes_1y)", datetime(2025, 4, 17, tzinfo=UTC_), datetime(2026, 4, 17, tzinfo=UTC_))
horizon_summary("FULL scored horizon", LO, HI)
horizon_summary("FULL domain horizon", datetime(1998, 1, 1, tzinfo=UTC_), datetime(2084, 12, 31, tzinfo=UTC_))
