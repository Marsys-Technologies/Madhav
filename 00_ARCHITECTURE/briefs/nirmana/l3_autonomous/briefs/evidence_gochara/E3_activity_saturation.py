# READ-ONLY evidence script. No DB, no network, no writes. Needs: swisseph, numpy, scipy.
# Run from anywhere:  python <this file>
import sys, collections
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[6] / "platform" / "python-sidecar"))  # worktree root
import numpy as np, swisseph as swe
from services.gochara_v3.tests.test_speedup import _build_context_for_benchmark
from services.gochara_v3 import engine as E
ctx = _build_context_for_benchmark("marriage")[0]
targets = list(ctx.resonance_targets)
print("weights:", ctx.weight_by_target_ref)
start = swe.julday(2026, 1, 1, 12.0)
sent = [s for s in E._gather_sentences_no_db(swe, ctx, targets, start, start + 90.0) if s.primitive in E._ACTIVITY_PRIMITIVES]
by = collections.Counter((s.primitive, s.transit_planet) for s in sent)
print(f"\n{len(sent)} activity sentences in 90 d for {len(targets)} targets. By primitive:")
for prim, n in collections.Counter(s.primitive for s in sent).most_common(): print(f"   {prim:26s} {n}")
print("By transit body:")
for pl, n in collections.Counter(s.transit_planet for s in sent).most_common(): print(f"   {str(pl):10s} {n}")
zero = sum(1 for s in sent if (s.detail.get('orb_strength') == 0 or s.detail.get('orb_strength') == 0.0))
print("sentences with orb_strength == 0 (anti-point phantoms):", zero)

def activity_at(jd, keep):
    ss = [s for s in E._gather_sentences_no_db(swe, ctx, targets, jd - 5.0, jd + 5.0) if keep(s)]
    a, _, _ = E._compute_activity_v3(ss, ctx.weight_by_target_ref); return a, len([s for s in ss if s.primitive in E._ACTIVITY_PRIMITIVES])
SLOW = {"Saturn", "Jupiter", "Rahu", "Ketu"}
print("\n date        all-bodies(act, n)     no-Moon(act, n)      slow-only(act, n)")
for k in range(0, 90, 9):
    jd = start + k
    a = activity_at(jd, lambda s: True); b = activity_at(jd, lambda s: s.transit_planet != "Moon"); c = activity_at(jd, lambda s: s.transit_planet in SLOW)
    y, m, d, _ = swe.revjul(jd)
    print(f" {y}-{m:02d}-{d:02d}   {a[0]:.6f} ({a[1]:3d})      {b[0]:.6f} ({b[1]:3d})     {c[0]:.6f} ({c[1]:3d})")
