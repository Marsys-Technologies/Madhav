"""READ-ONLY, no database: (1) the distance of every point-contact ray level from exactly 0/360; (2) for every real-chart in-band stretch that contains a station, the body's distance from the ray level AT the station."""
import sys, os, json
S = "/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/b494bf37-e4fb-4e8f-b5fd-87e2fcc3f095/scratchpad/wt-p1/platform/python-sidecar"
sys.path.insert(0, S); os.chdir(S)
os.environ["SE_EPHE_PATH"] = "/Users/Dev/suvarna-evidence/Se1"
from datetime import datetime, timezone, timedelta
from services.gochara_kernel.knots import calc_sidereal_lon
from services.gochara_kernel.window_verifier import _ASPECT_ANGLES
UTC = timezone.utc; JD0 = 2440587.5
def pos(b, t):
    l, f = calc_sidereal_lon(b.title(), t.timestamp() / 86400 + JD0, os.environ["SE_EPHE_PATH"]); assert f & 2; return l
rows = json.load(open("/Users/Dev/pravaha/run/HORIZON_EDGE_STRETCHES_20261005.json"))
keys = sorted({(r["agent"], r["rel"], r["target"]) for r in rows})
levels = []
for agent, rel, target in keys:
    lam = float(target.split(":", 1)[1]); angles = (0.0,) if rel == "conjunction" else _ASPECT_ANGLES[agent]
    levels += [min((lam - a) % 360.0, 360.0 - (lam - a) % 360.0) for a in angles]
print("ray levels:", len(levels), "| smallest distance of any ray level from exactly 0/360:", round(min(levels), 4), "| levels within 1e-6 of 0/360:", sum(1 for l in levels if l < 1e-6))
def vel(agent, t, h=600):
    a = pos(agent, t - timedelta(seconds=h)); b = pos(agent, t + timedelta(seconds=h)); return (((b - a + 180) % 360) - 180) / (2 * h)
out = []
for r in rows:
    if not r["stations"]: continue
    agent = r["agent"]; A = datetime.fromisoformat(r["A"]); B = datetime.fromisoformat(r["B"]); level = r["level"]
    n = int((B - A).total_seconds() // 3600) + 2; ts = [A + (B - A) * k / (n - 1) for k in range(n)]
    vs = [vel(agent, t) for t in ts]
    for i in range(len(vs) - 1):
        if (vs[i] > 0) != (vs[i + 1] > 0):
            lo, hi, vlo = ts[i], ts[i + 1], vs[i]
            for _ in range(40):
                mid = lo + (hi - lo) / 2; vm = vel(agent, mid)
                if (vm > 0) == (vlo > 0): lo, vlo = mid, vm
                else: hi = mid
            ts_ = lo + (hi - lo) / 2
            d = abs(((pos(agent, ts_) - level + 180) % 360) - 180)
            out.append((d, agent, r["rel"], r["target"][6:14], ts_.isoformat()[:16]))
out.sort()
print("stations inside in-band stretches:", len(out))
print("closest approach to the ray level AT a station: smallest 8:")
for o in out[:8]: print("  %.5f deg" % o[0], o[1:])
for thr in (2.8e-4, 1e-3, 1e-2, 0.05):
    print("  stations within %.4g deg of the ray level: %d" % (thr, sum(1 for o in out if o[0] < thr)))
