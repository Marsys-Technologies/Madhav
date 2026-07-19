---
artifact: D4A_A5_DRY_RUN_RESULTS
version: 1.0
status: DIAGNOSTIC — NOT a DR-12 adjudication
lane: D-4a Lane A-5 ("Harness dry-run", wave gate lane)
run_at: 2026-07-19T03:27:12.938Z
preregistration: artifacts/D-4a/A-5/PREREGISTRATION_v1_0.md (committed BEFORE this run, commit 03b226f7)
raw_receipt: artifacts/D-4a/A-5/dry_run_receipt_v1_0.json (full per-event CurveEventScore + ProperScoreResult data)
---

# D-4a Lane A-5 — Harness Dry-Run Results

> **THESE ARE DIAGNOSTIC SCORES ONLY.** This dry-run is explicitly NOT the DR-12 model
> adjudication ruling (DIS.025) — that determination is reserved for wave D-4b. Do not cite
> the numbers below as a model-comparison verdict. A model scoring worse here is not
> "losing" anything; a model scoring well is not "winning" anything. This run measures;
> it does not adjudicate. Any reading of this table as a peak-model ruling is a violation
> of BRIEF_D4A.md §G item 5 / DIS.025's deferral.

## §1 — Model coverage (pre-registered expectation, PREREGISTRATION_v1_0.md §2)

| model | status | note |
|---|---|---|
| `pratyantar_lord` | **SCORED** | the one real, wired model (`dasha_lord_confluence_v1` proxy) |
| `midpoint_triangle` | **GAP — not scoreable** | `NotImplementedModelError`; no substrate exists in the codebase |
| `transit_kernel` | **GAP — not scoreable** | `NotImplementedModelError`; no ephemeris/transit curve-building code exists anywhere in the repo, independent of the A-0 dasha-serving substrate repair |

Per B.10 (no fabricated computation): the two gaps are reported as gaps, not fabricated scores.
This is a genuine finding for D-4b, not a defect of this lane's run — the DR-12 comparison
the brief anticipates cannot happen until at least one more contender model is implemented.

## §2 — `pratyantar_lord`: per-domain summary (55 scorable events, 5 domain groups)

Primary metric = CRPS (lower better) / skill = 1 − CRPS_model/CRPS_control (positive = model beats control).
Secondary (legacy) metric = hit-rate, ±45d exact / ±75d month_known, top-decile (percentile=0.9).

| domain | n | meanCRPS<br>real | meanCRPS<br>shuffled-ctrl | meanCRPS<br>antiphase-ctrl | skill<br>vs shuffled | skill<br>vs antiphase | hit-rate<br>real | hit-rate<br>shuffled-mean | hit-rate<br>antiphase |
|---|---|---|---|---|---|---|---|---|---|
| general | 24 | 2419.0 | 806.0 | 3219.3 | -2.001 | 0.249 | 1.000 (24/24) | 0.869 | 0.875 |
| health | 6 | 2319.2 | 791.7 | 3595.1 | -1.929 | 0.355 | 1.000 (6/6) | 0.976 | 1.000 |
| marriage | 9 | 2494.7 | 778.5 | 2937.5 | -2.205 | 0.151 | 0.778 (7/9) | 0.952 | 1.000 |
| career | 11 | 2985.5 | 877.4 | 2991.8 | -2.403 | 0.002 | 0.909 (10/11) | 0.870 | 0.909 |
| wealth | 5 | 2765.9 | 838.1 | 3152.3 | -2.300 | 0.123 | 0.400 (2/5) | 0.343 | 0.800 |
| **all domains (weighted)** | **55** | — | — | — | — | — | **0.891** (49/55) | **0.847** | — |

### Headline diagnostic (report, do not adjudicate)

- **Primary (CRPS/skill) and secondary (hit-rate) metrics disagree in direction.** On the
  legacy hit-rate metric, the real model beats or roughly matches its shuffled-birth control
  in 4/5 domains (general, health, career, wealth) and its antiphase control in 3/5. On the
  PRIMARY CRPS metric (DIS.028/DR-15(b)'s ratified primary), the real model is beaten by the
  shuffled-birth control in ALL FIVE domains (skill −1.93 to −2.40 — a large, consistent gap,
  not a borderline one), while it beats the antiphase control in 4/5 (skill +0.00 to +0.35).
- This divergence between the point-in-window hit-rate convention and the mass-concentration
  CRPS convention is itself the kind of measurement this dry-run exists to surface — it is
  reported here as data for D-4b's adjudication, not resolved or explained away by this lane.
- `marriage` is the one domain where even the legacy hit-rate control gap is negative
  (real 0.778 vs shuffled 0.952, vs antiphase 1.000) — the model underperforms both controls
  on both metrics in this domain.

## §3 — Corpus + methodology recap (full detail: PREREGISTRATION_v1_0.md)

- `life_events` rows for chart 482012f1: **62**
- Excluded (birth anchor, synthetic test fixture, 4 superseded correction originals, 1 kill-switched congenital row): **7**
- Scorable corpus: **55**
- Dasha periods loaded (vimshottari, lahiri_chitrapaksha, levels 1-4): **9205**
- Scoring bounds: 1984-02-05 → 2030-12-31
- Params: percentile=0.9, shuffleCount=7, includeSecondaryBattery=true
- No `chain`-shaped events exist in the live corpus (0/55) — DR-13(c)'s chain-scoring path
  (`scoreChain`) is exercised zero times this run. Structural gap, not fabricated (PREREGISTRATION §3.4).
- Domain/event-class resolution reuses `mechanisms.ts`'s live-verified `DOMAIN_LORDS` map
  (T-0/A-3 precedent) because `life_events` has no `event_class` column joining to A-2's
  27-class ontology yet — documented substitute, flagged as a gap for D-4b (PREREGISTRATION §4).

## §4 — Per-event detail

Full per-event `CurveEventScore` (shape, threshold, peak, pass/fail) and `ProperScoreResult`
(CRPS, log-score, eventInRange) for every one of the 55 scored events, for both real and every
control curve, is in the raw receipt: `artifacts/D-4a/A-5/dry_run_receipt_v1_0.json`
(`models[].per_domain[].primary.perEventReal` / `.secondary.real.perEvent`, per domain).
This markdown file is the summary layer; the JSON is the authoritative per-event table.

