# READ-ONLY evidence script. No DB, no network, no writes. Needs: swisseph, numpy, scipy.
# Run from anywhere:  python <this file>
import sys, time
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[6] / "platform" / "python-sidecar"))  # worktree root
import numpy as np, swisseph as swe
from services.gochara_v3.tests.test_speedup import _build_context_for_benchmark
from services.gochara_v3 import engine as E
from services.gochara_grammar import primitives as P
from services.gochara_grammar import sarvatobhadra as SBC
ctx = _build_context_for_benchmark("marriage")[0]
targets = list(ctx.resonance_targets); start = swe.julday(2027, 3, 1, 12.0)
names = ["degree_contact","drishti_contact","sign_ingress","nakshatra_ingress_tara","station_retro_loop","eclipse_degree","kakshya_cell_crossing","gochara_vedha_pair"]
tot = {}
for n in names:
    fn = getattr(P, n); t0 = time.perf_counter(); cnt = 0
    for k in range(6):
        jd = start + 7.0 * k + 0.123
        for t in targets:
            try:
                out = fn(swe, ctx.chart_id, t, jd - 5, jd + 5, conn=None) if n in ("kakshya_cell_crossing","gochara_vedha_pair") else fn(swe, ctx.chart_id, t, jd - 5, jd + 5)
                cnt += len(out)
            except Exception as e: cnt = f"ERR {e}"
    tot[n] = (time.perf_counter() - t0) / 6, cnt
t0 = time.perf_counter()
for k in range(6):
    jd = start + 7.0 * k + 0.123
    for t in targets: SBC.find_sarvatobhadra_vedha_states(swe, ctx.chart_id, t, jd - 5, jd + 5, conn=None)
tot["sarvatobhadra_vedha (computed, then excluded from activity)"] = (time.perf_counter() - t0) / 6, "-"
s = sum(v[0] for v in tot.values())
print(f"per-evaluation search cost by primitive ({len(targets)} targets), total {s*1000:.1f} ms:")
for n, (sec, cnt) in sorted(tot.items(), key=lambda kv: -kv[1][0]): print(f"  {n:62s} {sec*1000:7.2f} ms  {100*sec/s:5.1f}%   sentences/6 evals: {cnt}")
