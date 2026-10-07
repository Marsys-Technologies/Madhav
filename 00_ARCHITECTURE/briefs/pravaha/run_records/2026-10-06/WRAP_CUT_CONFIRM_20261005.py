"""READ-ONLY computation (no database): the builder's contact support vs the independent reconstruction for Saturn aspect to point 270.84 (ray level 0.84)."""
import sys, os
from datetime import datetime, timezone
S = "/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/b494bf37-e4fb-4e8f-b5fd-87e2fcc3f095/scratchpad/wt-p1/platform/python-sidecar"
sys.path.insert(0, S); os.chdir(S)
os.environ["SE_EPHE_PATH"] = "/Users/Dev/suvarna-evidence/Se1"
from services.gochara_kernel import contact_certify as cc, arcs as gk_arcs, record_store as rs
from services.gochara_kernel.contacts import find_roots
from services.gochara_kernel.knots import calc_sidereal_lon
from pipeline.orchestrator.writers import ka_gochara_v5 as w
from services.gochara_kernel.record_store import jd_to_utc, POINT_KERNEL_RELATION, POINT_ORB_SOURCE, ORB_TABLE
EPHE = os.environ["SE_EPHE_PATH"]; JD0 = 2440587.5; UTC = timezone.utc
def pos(body, t):
    lon, fl = calc_sidereal_lon(body.title(), t.timestamp() / 86400.0 + JD0, EPHE); assert fl & 2; return lon
pos.cache_key = ("swiss", EPHE)
body, rel, lam = "Saturn", "aspect", float(sys.argv[1]) if len(sys.argv) > 1 else 270.84
ks = w.sample_knots(body, w.SUBSTRATE_DOMAIN_START.date(), w.SUBSTRATE_DOMAIN_END.date(), EPHE)
index = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)
orb = float(ORB_TABLE[POINT_ORB_SOURCE[rel]]["orb_max_deg"])
roots = find_roots(index, body, POINT_KERNEL_RELATION[rel], lam, EPHE, refine=True)
LO, HI = datetime(1997, 12, 1, tzinfo=UTC), datetime(1999, 3, 1, tzinfo=UTC)
want = cc.expected_intervals(pos, body.lower(), rel, f"point:{lam}", LO, HI)
print("orb", orb, "roots in 1997-12..1999-03:", [(jd_to_utc(r.exact_jd).isoformat(), round(r.level_deg, 4)) for r in roots if LO <= jd_to_utc(r.exact_jd) <= HI])
for r in roots:
    t = jd_to_utc(r.exact_jd)
    if not (LO <= t <= HI): continue
    a, b = rs._in_orb_span_around_root(index, r, orb)
    print("BUILDER  support", jd_to_utc(a).isoformat(), "->", jd_to_utc(b).isoformat(), " level", round(r.level_deg, 4), " arc", round(r.arc.start_lon_unwrapped, 4), round(r.arc.end_lon_unwrapped, 4))
for (a, b) in want:
    print("RECONSTR interval", a.isoformat(), "->", b.isoformat())

# ---- PROTOTYPE (scratch only): the same derivation on the root's station-bounded SEGMENT (index.segments) instead of its 360-band arc ----
from types import SimpleNamespace
def span_on_segment(index, root, orb_deg):
    seg = next(s for s in index.segments if s.start_jd - 1e-9 <= root.exact_jd <= s.end_jd + 1e-9)
    return rs._in_orb_span_around_root(index, SimpleNamespace(arc=seg, exact_jd=root.exact_jd, level_deg=root.level_deg), orb_deg)
print("PROTOTYPE (segment) vs reconstruction:")
for r in roots:
    t = jd_to_utc(r.exact_jd)
    if not (LO <= t <= HI): continue
    a, b = span_on_segment(index, r, orb)
    print("  segment support", jd_to_utc(a).isoformat(), "->", jd_to_utc(b).isoformat())
