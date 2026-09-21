# READ-ONLY evidence script. No DB, no network, no writes. Needs: swisseph, numpy, scipy.
# Run from anywhere:  python <this file>
import sys, time
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[6] / "platform" / "python-sidecar"))  # worktree root
import swisseph as swe
from services.gochara_v3.tests.test_speedup import _build_context_for_benchmark
from services.gochara_v3.interval_solver import find_threshold_crossings
from services.gochara_v3.threshold import ThresholdConfig
ctx = _build_context_for_benchmark("marriage")[0]
cfg = ThresholdConfig(percentile_used=0.0, lambda_thresh=0.0, implied_density=0.0, base_rate_cited=0.0,
                      age_band_used="band_41_60", density_flag="ok", fallback_used=False, sample_count=0)   # exactly the writer's config (:1938-1947)
a, b = swe.julday(2026,1,1,12.0), swe.julday(2027,1,1,12.0)
t0 = time.perf_counter(); iv, js, ls = find_threshold_crossings(swe, ctx, a, b, cfg, coarse_step_days=7.0, return_series=True); dt = time.perf_counter()-t0
print(f"1-year range, writer's threshold config: {len(iv)} interval(s); coarse samples={len(js)}; wall={dt:.1f}s")
for i in iv: print("  enter", "%d-%02d-%02d"%swe.revjul(i.enter_jd)[:3], " exit", "%d-%02d-%02d"%swe.revjul(i.exit_jd)[:3], " (range start/end:", "%d-%02d-%02d"%swe.revjul(a)[:3], "/", "%d-%02d-%02d"%swe.revjul(js[-1])[:3], ")")
print("lambda min/max over series:", float(ls.min()), float(ls.max()), "-> every sample satisfies lambda >= 0.0, including lambda == 0")
