# READ-ONLY evidence script. Diagnoses the 41/360 instants where E6's reconstruction differs from the engine.
import sys, bisect, pathlib, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[6] / "platform" / "python-sidecar"))
import numpy as np, swisseph as swe
from services.gochara_v3.tests.test_speedup import _build_context_for_benchmark
from services.gochara_v3 import engine as E
ctx = _build_context_for_benchmark("marriage")[0]; targets = list(ctx.resonance_targets)
start = swe.julday(2026, 1, 1, 12.0); W = 5.0
glob = sorted(E._gather_sentences_no_db(swe, ctx, targets, start - W, start + 180 + W), key=lambda s: s.event_jd)
def key(s): return (s.primitive, s.transit_planet, s.target_ref, round(s.event_jd, 3))
cause = collections.Counter(); shown = 0
for i in (1, 22, 23, 30, 31, 40, 41, 60, 61):
    t = start + 0.5 * i
    loc = E._gather_sentences_no_db(swe, ctx, targets, t - W, t + W)
    sub = [s for s in glob if t - W <= s.event_jd <= t + W]
    a, b = {key(s): s for s in loc}, {key(s): s for s in sub}
    only_loc, only_glob = set(a) - set(b), set(b) - set(a)
    for k in only_loc | only_glob:
        s = a.get(k) or b.get(k); edge = min(abs(s.event_jd - (t - W)), abs(s.event_jd - (t + W)))
        side = "engine-window-only" if k in only_loc else "global-list-only"
        cause[(side, s.primitive, "within 1 scan step of window edge" if edge <= 1.0 else "interior")] += 1
        if shown < 6:
            print(f"t=grid[{i}] {side:20s} {s.primitive:22s} {str(s.transit_planet):8s} event at t{s.event_jd - t:+.4f} d  orb_strength={s.detail.get('orb_strength')}"); shown += 1
print("\ncauses:"); [print("  ", k, n) for k, n in cause.most_common()]
