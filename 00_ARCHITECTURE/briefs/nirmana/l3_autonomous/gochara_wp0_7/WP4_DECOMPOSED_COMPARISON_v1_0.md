---
artifact: WP4_DECOMPOSED_COMPARISON
version: "1.0"
status: WP4_COMPLETE
date: 2026-09-23
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §4 WP4 (decomposed comparison);
          WP3b_CLASSIFICATION.md (delta classes A-1/A-2/A-4/A-5/A-6/B-4);
          WP1_CONTRACTS.md §1.2, §3.1; WP6_LEDGER.md §6 (scale pricing)
branch: l3/gochara-autonomous-wp0-7 @ /Users/Dev/madhav-l3/gochara-wp0-7
evidence_class: producer prototype evidence — synthetic curves, synthetic chart ids,
  disposable WP6 database; no production service was modified for this work package
---

# WP4 — Decomposed comparison: legacy vs kernel, measured on one synthetic workload

All numbers below are **measured** by `platform/python-sidecar/tests/l3/gochara/test_wp4_decomposed.py`
(10 tests, all passing in the 96-test suite) on workload **WP4-SYNTH-1**. Nothing is estimated.
Where a comparison against a historical production figure appears, the workloads differ and the
document says so — it is a scale reading, never a like-for-like claim (E-001).

## 1. Workload declaration (WP4-SYNTH-1)

- Horizon: JD(2024-01-01 12:00 UT) → JD(2026-01-01 12:00 UT), 731.0 days.
- Bodies: synthetic cubics in u = (jd − T0)/365.25, reproduced exactly by the spline (`refine=False`):
  - Saturn: `280 + 8u − 6u² + 0.8u³` (one station at +289.34 d)
  - Jupiter: `40 + 30u − 4u² + 0.4u³` (monotone)
- Knots: padded daily-noon 2023-07-01 → 2026-07-01 (1097 knots/body). Padding is required —
  knots exactly on the horizon hide the pre-horizon orb entry and suppress the truncation flag.
- Targets: conjunction at 281.0° (Saturn) and 55.0° (Jupiter); drishti legs for both bodies.
- Chart id `00000000-0000-4000-8000-0000000004aa` (synthetic, non-person, PB-7).
- Ephemeris: **synthetic curves only**; `swisseph` is used solely for `swe.julday` calendar math.

### Episode census (measured)

| leg | exact episodes | notes |
|---|---|---|
| Saturn conjunction 281.0° | 2 | t_exact = +50.8716 d (t_in = +0.0 d, `truncated_at_horizon='start'`); t_exact = +563.4154 d (clean) |
| Jupiter conjunction 55.0° | 1 | t_exact = +195.8804 d |
| Saturn drishti_contact | 0 | honest zero — levels outside traveled band |
| Jupiter drishti_contact | 0 | honest zero — levels outside traveled band |
| sub-horizon [t1−2d, t1+30d] (Saturn conj.) | 1 | `truncated_at_horizon='both'` |

Anchor speeds at t_exact: Saturn 0.0174544 / 0.0131414 deg/d, Jupiter 0.0713342 deg/d.

### Anchor equivalence (no delta)

At every exact crossing both sides agree: legacy `legacy_activity_at` and the kernel projection
both give λ = 0.8 at t_exact on both conjunction legs. The decomposed comparison therefore starts
from a verified shared anchor; every delta below is off-anchor behavior.

## 2. Delta table — each delta classified against WP3b_CLASSIFICATION.md

| # | delta (measured) | class (WP3b) | fix owner |
|---|---|---|---|
| 1 | **Step-vs-graduated activity.** At t_exact+4 d on the Saturn leg: legacy λ = 0.80000000 (boxcar), kernel λ = 0.74414599 (graduated, speed 0.017454 deg/d). Δ = 0.05585401. | A-2 (F-08), ACCIDENTAL BUG | WP5 H-2 family; M-1 method call decides the replacement decay |
| 2 | **Exception → 0.0 → certified active.** `eval_single_legacy` swallows a failed evaluation to 0.0; with `lambda_thresh = 0.0` and the `>=` predicate the failed JD is certified **active**. Fixed side: WP5 `EvaluationFailure` + kernel `completeness_state` (row state in the test: `qualified`). | A-1 (F-08), ACCIDENTAL BUG | WP5 H-2 (fixed side implemented, commit 59bebe7dc) |
| 3 | **Overlay absent → unknown-as-clear.** Legacy `quality_gates = 1.0` when no vedha overlay overlaps; kernel projection reports `state='unavailable'` (honest null per WP2 oracle contract). | A-6 (F-11), ACCIDENTAL BUG | WP5 H-family (honest-null overlay states) |
| 4 | **Era window declared over unmeasured range.** On the 30-day sub-horizon, legacy `find_threshold_crossings` reports `enter_jd` clamped to the sweep start with no crossing measured there; the kernel marks the same episode `truncated_at_horizon='both'`. | A-4 (F-10/H-3), ACCIDENTAL BUG | WP5 H-3 (fixed side implemented) |
| 5 | **Peak-cap truncation + plateau tie-break.** Legacy `retain_candidates` keeps 3 of 5 peaks (2 dropped pre-persistence); `find_local_maxima` admits a plateau once, at its first point. Kernel `peaks.admit_peaks` persists all admitted peaks (serve-time trim only) and admits all 3 tied maxima at rank 1. | A-5 (F-10/H-5) + B-4, ACCIDENTAL BUG / DELIBERATE-legacy | WP5 H-5 (admission cap-free; trim at serve time, never re-rank) |

No unclassified divergence was observed on this workload; had one appeared, the campaign stop
condition would have fired.

### Contact-id stability (B-family, no delta)

The 3 exact contact ids are byte-identical when the horizon is recomputed as one span vs split at
2025-01-01 vs shifted +10 d (no exact crossing within 1 min of the split). Partition-scoped,
minute-floored ids are stable under re-partition, by design (WP1 §1.2).

## 3. Timing (measured, WP4-SYNTH-1; seconds)

| metric | value |
|---|---|
| prepare (cold) | 0.001112 |
| search (cold / warm) | 0.000619 / 0.000617 |
| query kernel (cold / warm) | 0.000386 / 0.000414 |
| query legacy (cold / warm) | 0.000208 / 0.000229 |
| end-to-end kernel (cold) | 0.002117 |
| end-to-end legacy | 0.000751 |
| legacy resolution hierarchy | 0.000543 |
| era windows / search cells / query points | 1 / 4 / 105 |
| λ_thresh used | 0.0 |

**Scale reading (not a comparison):** the best recorded completed run of the *full century
production workload* is 58.2 min — an externally recorded figure for a different workload.
WP4-SYNTH-1 is ~10³ knots × 2 bodies over 2 years; the century run is orders of magnitude larger.
These numbers establish only that both sides are measurable and cheap at prototype scale (E-001).

## 4. Ledger pricing (measured on the disposable WP6 database)

| metric | value |
|---|---|
| write_contacts (3 rows, this workload) | 0.002242 s |
| write_coverage (2 partitions) | 0.001408 s |
| serve-shaped range read (warm) | 0.000505 s |
| rows left behind | 0 (`clear_generation` verified) |

Index-scale pricing is WP6's, measured at 200k rows (WP6_LEDGER.md §6): load 9.9 s
(~20k rows/s), warm serve reads ~0.07 ms, 293.9 MiB total. This section prices the write path at
this workload's own row count; the scale claim lives in WP6.

## 5. Reproduce

```
cd platform/python-sidecar
../../.venv/bin/python -m pytest tests/l3/gochara/test_wp4_decomposed.py -q -s
```

Prints `WP4_DELTA …` lines (one per classified delta), `WP4_MEASURED {json}` (timing), and
`WP4_LEDGER_MEASURED {json}` (ledger pricing). The ledger test skips NOT_RUN if the disposable
database `postgresql://wp6:disposable@localhost:55433/wp6` is unreachable.
