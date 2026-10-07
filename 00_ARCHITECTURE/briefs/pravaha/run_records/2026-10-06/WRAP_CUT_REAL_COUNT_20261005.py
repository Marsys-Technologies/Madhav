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

from services.gochara_kernel import arcs as gk_arcs, record_store as rs
from services.gochara_kernel.contacts import find_roots
from services.gochara_kernel.record_store import jd_to_utc, POINT_KERNEL_RELATION, POINT_ORB_SOURCE, ORB_TABLE
idx_cache = {}
def index_for(body):
    if body not in idx_cache:
        ks = w.sample_knots(body, w.SUBSTRATE_DOMAIN_START.date(), w.SUBSTRATE_DOMAIN_END.date(), os.environ["SE_EPHE_PATH"])
        idx_cache[body] = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)
    return idx_cache[body]
tot = collections.Counter(); rows = []
for (agent, rel, target), users in sorted(keys.items()):
    lam = float(target.split(":", 1)[1]); body = agent.title()
    angles = (0.0,) if rel == "conjunction" else _ASPECT_ANGLES[agent]
    levels = [(lam - a) % 360.0 for a in angles]; orb = _POINT_ORB_DEG[rel]
    near_cut = [lv for lv in levels if min(lv, 360.0 - lv) < orb]          # ray level whose band [lv-orb, lv+orb] contains 0/360
    idx = index_for(body); borb = float(ORB_TABLE[POINT_ORB_SOURCE[rel]]["orb_max_deg"])
    roots = find_roots(idx, body, POINT_KERNEL_RELATION[rel], lam, os.environ["SE_EPHE_PATH"], refine=True)
    built = []
    for r in roots:
        a, b = rs._in_orb_span_around_root(idx, r, borb)
        A, B = max(jd_to_utc(a), LO), min(jd_to_utc(b), HI)
        if A < B: built.append([A, B, r])
    built.sort(key=lambda x: x[0]); merged = []
    for A, B, r in built:
        if merged and abs((A - merged[-1][1]).total_seconds()) < 2: merged[-1][1] = max(merged[-1][1], B)
        else: merged.append([A, B, r])
    want = cc.expected_intervals(pos, agent, rel, target, LO, HI)
    for (a, b) in want:
        if a <= LO or b >= HI: tot["clipped (skipped)"] += 1; continue
        # the builder span overlapping this interval
        ov = [m for m in merged if m[0] < b and m[1] > a]
        # does an arc cut (a multiple of 360 in the unwrapped longitude) lie strictly inside [a, b]?
        ja, jb = a.timestamp() / 86400.0 + JD0, b.timestamp() / 86400.0 + JD0
        ua, ub = idx.evaluate(ja), idx.evaluate(jb)
        cut_inside = int(max(ua, ub) // 360.0) > int(min(ua, ub) // 360.0) or (min(ua, ub) % 360.0 == 0.0)
        # the cut must be crossed while the body is in the band: at the stretch's start or end the body is at the band edge (orb from the ray)
        touches = bool(near_cut)
        if not ov: tot["NO BUILDER SPAN (graze/none)"] += 1; kind = "none"; ds = de = None
        else:
            ds = (ov[0][0] - a).total_seconds(); de = (ov[-1][1] - b).total_seconds()
            kind = "late/early >30min" if (abs(ds) > 1800 or abs(de) > 1800) else "ok"
        tot["stretches"] += 1; tot["touch wrap cut (ray band contains 0/360): " + str(touches)] += 1
        tot["cut crossed inside stretch: " + str(cut_inside)] += 1
        tot["builder vs independent: " + kind] += 1
        if touches or cut_inside or kind not in ("ok",): rows.append((agent, rel, target, [round(l, 3) for l in near_cut], a.isoformat()[:16], b.isoformat()[:16], touches, cut_inside, kind, None if ds is None else round(ds / 3600, 1), None if de is None else round(de / 3600, 1)))
for k, v in sorted(tot.items()): print("COUNT", k, v)
for r in rows: print("ROW", r)
