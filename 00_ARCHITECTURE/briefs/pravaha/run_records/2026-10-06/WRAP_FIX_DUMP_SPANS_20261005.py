"""READ-ONLY, no database: for every real-chart point obligation (targets from the saved stretch list), the builder's per-root support spans over the whole
substrate domain with the _in_orb_span_around_root of the checkout given as argv[1]; written to argv[2]."""
import sys, os, json
S = sys.argv[1]; OUT = sys.argv[2]
sys.path.insert(0, S); os.chdir(S)
os.environ["SE_EPHE_PATH"] = "/Users/Dev/suvarna-evidence/Se1"
from services.gochara_kernel import arcs as gk_arcs, record_store as rs
from services.gochara_kernel.contacts import find_roots
from services.gochara_kernel.record_store import POINT_KERNEL_RELATION, POINT_ORB_SOURCE, ORB_TABLE
from pipeline.orchestrator.writers import ka_gochara_v5 as w
rows = json.load(open("/Users/Dev/pravaha/run/HORIZON_EDGE_STRETCHES_20261005.json"))
keys = sorted({(r["agent"], r["rel"], r["target"]) for r in rows})
cache = {}
def index_for(body):
    if body not in cache:
        ks = w.sample_knots(body, w.SUBSTRATE_DOMAIN_START.date(), w.SUBSTRATE_DOMAIN_END.date(), os.environ["SE_EPHE_PATH"])
        cache[body] = gk_arcs.build_arc_index(body, ks.knot_jds, ks.longitudes_deg)
    return cache[body]
out = []
for agent, rel, target in keys:
    lam = float(target.split(":", 1)[1]); body = agent.title(); idx = index_for(body)
    orb = float(ORB_TABLE[POINT_ORB_SOURCE[rel]]["orb_max_deg"])
    for r in find_roots(idx, body, POINT_KERNEL_RELATION[rel], lam, os.environ["SE_EPHE_PATH"], refine=True):
        a, b = rs._in_orb_span_around_root(idx, r, orb)
        out.append([agent, rel, target, repr(r.exact_jd), repr(a), repr(b), r.arc.start_jd, r.arc.end_jd])
json.dump(out, open(OUT, "w"))
print("roots", len(out), "obligations", len(keys))
