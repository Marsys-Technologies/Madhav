# READ-ONLY evidence script. No DB, no network, no writes. Needs: swisseph, numpy, scipy.
# Run from anywhere:  python <this file>
import sys, time, collections
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[6] / "platform" / "python-sidecar"))  # worktree root
import numpy as np, swisseph as swe
from services.gochara_v3.tests.test_speedup import _build_context_for_benchmark
from services.gochara_v3.engine import evaluate_lambda_vector
from services.gochara_v3 import engine as E

_r = _build_context_for_benchmark("marriage"); ctx = _r[0] if isinstance(_r, tuple) else _r
print("targets:", len(ctx.resonance_targets), [ (t.target_type, t.target_ref, t.target_longitude_deg) for t in ctx.resonance_targets][:8])

start = swe.julday(2026, 1, 1, 12.0)
# --- per-evaluation cost, measured the way interval_solver calls it: one-element arrays ---
ts = []
for k in range(12):
    jd = start + 7.0 * k
    t0 = time.perf_counter(); evaluate_lambda_vector(swe, ctx, np.array([jd]), v1_parity_mode=False); ts.append(time.perf_counter() - t0)
print("per-eval seconds (weekly grid, as the solver calls it):", [round(x, 3) for x in ts], "median", round(float(np.median(ts)), 3))
ts2 = []
for k in range(8):
    jd = start + 3.1415 + 0.37 * k          # off-grid instants, like bisection/dense/refine probes
    t0 = time.perf_counter(); evaluate_lambda_vector(swe, ctx, np.array([jd]), v1_parity_mode=False); ts2.append(time.perf_counter() - t0)
print("per-eval seconds (off-grid probes):", [round(x, 3) for x in ts2], "median", round(float(np.median(ts2)), 3))

# --- shape of the ACTIVITY term on a fine grid: is it piecewise-constant with edges at event_jd +/- 5d? ---
grid = np.arange(start, start + 90.0, 0.25)
acts, lams, taras = [], [], []
for jd in grid:
    r = evaluate_lambda_vector(swe, ctx, np.array([float(jd)]), v1_parity_mode=False)[0]
    d = r.x_t_detail or {}
    acts.append(round(float(r.x_t), 10)); lams.append(round(float(r.raw_lambda), 10)); taras.append(d.get("tara_modifier"))
acts = np.array(acts); lams = np.array(lams)
chg = np.nonzero(np.diff(acts) != 0)[0]
print(f"\nactivity over 90 d @0.25 d: {len(grid)} samples, {len(set(acts))} DISTINCT values, {len(chg)} change points")
print("distinct activity values:", sorted(set(acts))[:12])
# collect the event list the engine itself sees, and predict the change points from it
targets = list(ctx.resonance_targets)
sent = E._gather_sentences_no_db(swe, ctx, targets, float(grid[0]) - 5.0, float(grid[-1]) + 5.0)
ev = sorted(set(round(s.event_jd, 4) for s in sent if s.primitive in E._ACTIVITY_PRIMITIVES))
pred = sorted([e - 5.0 for e in ev] + [e + 5.0 for e in ev])
pred = [p for p in pred if grid[0] <= p <= grid[-1]]
obs = [float(grid[i] + 0.125) for i in chg]   # midpoint of the 0.25 d cell where the value changed
unmatched = [o for o in obs if min(abs(o - p) for p in pred) > 0.25] if pred else obs
print(f"events in span: {len(ev)}; predicted breakpoints (event_jd +/- 5.0): {len(pred)}; observed change points: {len(obs)}; observed NOT within 0.25 d of a predicted breakpoint: {len(unmatched)}")
print("lambda distinct values:", len(set(lams)), " tara distinct:", sorted(set(t for t in taras if t is not None)))
perm = [round(float(evaluate_lambda_vector(swe, ctx, np.array([float(j)]))[0].permission), 10) for j in grid[::8]]
print("permission distinct values over span:", sorted(set(perm)))
