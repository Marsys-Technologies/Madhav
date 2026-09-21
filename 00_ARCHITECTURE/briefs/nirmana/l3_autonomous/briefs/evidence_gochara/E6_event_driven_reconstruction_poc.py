# READ-ONLY evidence script. No DB, no network, no writes. Needs: swisseph, numpy, scipy.
"""Proof of concept for Stage E1: gather the event list ONCE for a span, then reconstruct the
engine's activity(t) in closed form at every instant, and compare against the real engine
evaluated point-by-point (the way interval_solver calls it today)."""
import sys, time, bisect, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[6] / "platform" / "python-sidecar"))
import numpy as np, swisseph as swe
from services.gochara_v3.tests.test_speedup import _build_context_for_benchmark
from services.gochara_v3 import engine as E
from services.gochara_v3.engine import evaluate_lambda_vector

ctx = _build_context_for_benchmark("marriage")[0]; targets = list(ctx.resonance_targets)
start = swe.julday(2026, 1, 1, 12.0); SPAN = 180.0; W = 5.0
grid = np.arange(start, start + SPAN, 0.5)

t0 = time.perf_counter()
ref = np.array([float(evaluate_lambda_vector(swe, ctx, np.array([float(j)]), v1_parity_mode=False)[0].x_t) for j in grid])
t_engine = time.perf_counter() - t0

t0 = time.perf_counter()
sent = [s for s in E._gather_sentences_no_db(swe, ctx, targets, float(grid[0]) - W, float(grid[-1]) + W)]
sent.sort(key=lambda s: s.event_jd); jds = [s.event_jd for s in sent]
t_gather = time.perf_counter() - t0
t0 = time.perf_counter()
rec = []
for j in grid:
    lo, hi = bisect.bisect_left(jds, j - W), bisect.bisect_right(jds, j + W)
    a, _, _ = E._compute_activity_v3(sent[lo:hi], ctx.weight_by_target_ref); rec.append(a)
rec = np.array(rec); t_closed = time.perf_counter() - t0

diff = np.abs(ref - rec)
print(f"instants compared: {len(grid)} over {SPAN:.0f} d ({len(targets)} targets, {len(sent)} events)")
print(f"max |engine - reconstruction| = {diff.max():.3e};  instants differing by > 1e-9: {(diff > 1e-9).sum()}")
bad = np.nonzero(diff > 1e-9)[0]
for i in bad[:5]:
    near = min(abs(abs(grid[i] - e) - W) for e in jds)
    print(f"   differs at grid[{i}]  engine={ref[i]:.8f} recon={rec[i]:.8f}   distance of this instant from an event+/-{W:.0f}d edge: {near:.4f} d")
print(f"\nwall: engine point-by-point {t_engine:.2f}s | one gather {t_gather:.2f}s + closed form {t_closed:.3f}s  => {t_engine/(t_gather+t_closed):.1f}x on this span")
print(f"per-instant cost: engine {1000*t_engine/len(grid):.1f} ms vs closed form {1000*t_closed/len(grid):.3f} ms  ({t_engine/len(grid)/(t_closed/len(grid)):.0f}x per instant once events are known)")
print("NOTE: the gather here still uses the legacy day-stepping scan. The arc kernel replaces that gather; E1 shows it solves each contact to ~1 arcsec.")
