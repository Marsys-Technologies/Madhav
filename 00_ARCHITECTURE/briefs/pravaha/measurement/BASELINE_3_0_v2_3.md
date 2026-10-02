---
artifact: BASELINE_3_0
canonical_id: BASELINE_3_0
version: "2.3"
status: SCORED
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
decision: "D-PROTO_DECISION_v1_0.md (ACCEPT_WITH_CONDITIONS) — §6 conditions 1–5 landed together in this re-run; per-condition Verify evidence in EVALUATION_PROTOCOL_v2_3.md §11"
protocol: "EVALUATION_PROTOCOL_v2_3.md"
registry: "event_registry_v2_3.json (+ EVENT_REGISTRY_v2_3.md review copy)"
pinned_extract: "baseline_3_0_extract_v1_0.json — sha256 70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff (914 rows, predicate: kala_gochara_windows where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and generation='3.0', dates converted to IST civil dates) — the SAME pinned extract as the v2.0–v2.2 re-runs, not re-dumped; the v2_3 scorer COMPUTED this hash at load time and would have aborted with INPUT_REJECTED on any mismatch (condition 4)"
scorer: "rerun_3_0_v2_3_scorer.py (deterministic; committed beside this file)"
result_file: "rerun_result_v2_3.json (machine-readable per-endpoint status; per-event records in rerun_per_event_v2_3.json)"
controls: "random_controls_v1_3.json — seed 482012, ONE frozen experiment (rolling spans at each event's own actual span length), sha256 eea40fe8ba743a15291c8ec885b1f9dc0c5591a03ebf8bfb70cbefe414f6cb94"
supersedes: "BASELINE_3_0_v2_2.md (sha256 0ec1ce47…) — retained in full as disclosed history"
deviation_history: "unchanged: the original '3.0' pass (B4.3) predated the protocol review close; v2.0–v2.3 are re-measurements of an already-served generation, not candidate scores."
---

# Baseline '3.0' under protocol v2.3 — re-run from the pinned extract

All figures recomputed from `baseline_3_0_extract_v1_0.json` (sha256 70ba6142…) by
`rerun_3_0_v2_3_scorer.py`; nothing copied from v2_2 or earlier. The v2.3 run exists to
land D-PROTO conditions 1–5; **every '3.0' figure is unchanged from v2.2** — verified per
figure below and in the result JSON diff.

## 1. Registry-derived counts (machine-checked, source-reconciliation MATCH)

Held-out **47** (32 timing-usable + 15 year-grain); exact-date cohort 5; interval-date **4**
(grandfather 61 d; 2026.01 interval 59 d; 2007–08 sleep disorder **731 d (leap year 2008)**;
2021–22 quarry 730 d). Horizon H = 1998-01-01 → 2026-04-17 = 10,334 days. Registry v2_3
carries the three D-PROTO condition-5 mapping_reason clauses (2012 residual year
uncertainty; 2010 family-level windfall; 2022-10 concurrent-relationship → separation
deliberate mapping) plus the 731-d correction; no counts moved. Scorer re-derived every
count and matched the registry header (timing 32/32, year 15/15, exact 5/5, interval 4/4).

**Dedup table (scorer merge block, unchanged from v2.2):**

| raw rows → merged candidates | classes |
|---|---|
| 70 → **10** | career_setback, chronic_onset, financial_deception, major_gain, major_loss, parental_event, relocation, spiritual_turn |
| 64 → **10** | psychological_arc |
| 40 → 40 | education_milestone |
| 30 → 30 | business_launch, career_change, separation |
| 30 → **20** | foreign_settlement |
| 10 → 10 | all other 17 classes |

## 2. Input adapter (unchanged from v2.2)

Raw valence domain: **270 gain / 330 loss / 134 mixed / 180 neutral**; enforced convention
on si sign (raw rows with si < 0 = **0** → `input_adapter.status = PASS`). The v2_3 scorer
additionally **validates the 27-class list on input** (condition 4): any unknown class in
the extract or registry would abort the run with `INPUT_REJECTED`; none occurred.

## 3. Endpoint results ('3.0', v2.3 rules) — figures unmoved

| endpoint | rule (v2.3 §6) | '3.0' result | verdict |
|---|---|---|---|
| **T-cover** | 47 held-out, overlap per grain, candidate set per §4.6 | **32/47 = 68.1 %**; the SAME 15 misses as v2.2 (named in §3a) | sets the served floor: **≥ 32/47** |
| **T-time** | capped median (cap 182 d) over 5 exact events, misses reported separately | **182 d** (misses 2: 2008-06-09, 2024-02-16; uncapped hit errors 686, 998, **333** d) | FAIL vs 45 d |
| **T-rank** | candidate set = §4.6 merged in-mask windows; N ≥ 3 post-dedup, degeneracy exclusions first, floor 17; void machine-readable | era-fingerprint **59.8 %** ≥ 50 % ⇒ `t_rank.status = "VOID"` — no rank median emitted as a result (diagnostic-only median 0.0, labelled). Eligible **0/32** | FAIL — rank void |
| **T-FP** | adverse classes: admitted day-fraction vs per-class budget 3·n_c·90/H | **8 of 9 adverse classes at 99.87 % → FAIL; separation 0.09 % PASS** (degenerate-low, not specific) — **identical to v2.2** | FAIL on 8 of 9 |
| **T-FP gain band (NEW, condition 1)** | each of the 17 non-adverse non-anchor classes must pass its own budget; `t_fp_overall.pass` requires EVERY adverse AND gain entry | **all 17 gain classes FAIL the band** (13 at 99.87 % incl. psychological_arc; 4 at ≤ 0.12 %: business_launch, career_change, education_milestone, foreign_settlement — degenerate-low is a fail, not a pass); `t_fp_overall.pass = false` | enforced, FAIL |
| **T-honesty (condition 3)** | coverage ≥ 50 % + manifest; UNVERIFIABLE now carries consequences §6.5 | `t_honesty.pass = false` with consequence string (blocks candidate flip until manifest ships; non-gating for the baseline) | flagged |

### 3a. Misses (15), named — identical set to v2.1/v2.2

EVT.2001.03 (edu), EVT.2003.06 (edu), EVT.2007.06.XX.02 (edu), EVT.2008.06.09
(career_change), EVT.2011.01 (edu), EVT.2011.06 (edu), EVT.2013.03 (edu), EVT.2017.03
(career_change), EVT.2019.05 (foreign_settlement), EVT.2022.10 (separation), EVT.2023.06
(edu), EVT.2023.07 (business_launch), EVT.2024.02.16 (business_launch), EVT.2000 (edu,
year-grain), EVT.2021.XX.XX.02 (edu, year-grain).

**Candidate-set rule (condition 2) — disclosed effects:** the §4.6 merged-window set
(hits, N, and ranks computed against ONE set, mask-clipped) changes two edge behaviours
probed before landing: the lone chronic_onset window inside a multi-year event span now
counts as a hit for that event (no such case exists in the held-out cohort — coverage
unmoved), and fully-post-mask windows no longer inflate N (no in-mask window of any scored
class is affected). Neither moves any '3.0' figure; both are documented with probe output
in protocol §11.

## 4. Degeneracy tests (unchanged results)

- Era-boundary fingerprint: **59.8 %** → class-indiscriminate; T-rank VOID.
- Two-horns, 27 classes: **22 degenerate-high (99.87 %), 5 degenerate-low, 0 in-band**
  (gain subset 14 high / 4 low / 0 ok — these are the rows condition 1 now enforces
  individually in §6.4).
- Peak-diversity (§8.3): v2_3 computes it with the **same sorted-gap 1e-9 predicate** the
  ranking code uses (single tie tolerance, §4.3); moot for '3.0' under the void.

## 5. Controls

- **Random controls (seed 482012, ONE frozen experiment, materialised v1_3, sha256
  eea40fe8…):** same experiment as v1_2 — **all 940 draws byte-identical** (spans, hit
  counts: verified NONE differ, see protocol §11 condition-5 evidence). Result: **638/940
  = 67.9 %** — no observed separation from T-cover's 68.1 % in this diagnostic.
- **Adverse-day burden:** reflected in T-FP above.

## 6. Comparison to earlier runs (history, not operative)

| figure | v2.2 | v2.3 re-run | moved? |
|---|---|---|---|
| registry | 47 held-out, floor 17 | **47, floor 17** | no (mapping_reason clauses + 731-d wording only) |
| T-cover | 32/47 | **32/47, same 15 misses** | no |
| T-time | 182 d, 2/5; 686/998/333 | **182 d, 2/5; 686/998/333** | no |
| T-rank | VOID, 0/32 | **VOID, 0/32** | no |
| T-FP adverse | 8/9 FAIL | **8/9 FAIL** | no |
| T-FP gain band | not enforced | **17/17 FAIL; overall FAIL** | new enforcement (condition 1) |
| T-honesty | UNVERIFIABLE | **pass=false + consequences** | consequence wiring (condition 3) |
| controls | 638/940 | **638/940, byte-identical draws** | no |

## 7. D-PROTO conditions

All five §6 conditions of D-PROTO_DECISION_v1_0 are landed together in protocol v2.3,
scorer v2_3, and this re-run. The per-condition Verify evidence (probes, mutation test,
hash measurement, controls byte-identity) is in **EVALUATION_PROTOCOL_v2_3.md §11** and is
not restated here. Steward verification of the conditions (B4.6) is pending; nothing in
this file marks it.

## 8. Verdict

Under protocol v2.3, '3.0' fails every co-primary endpoint except the floor it sets for
T-cover (**≥ 32/47**). It is class-indiscriminate, its T-rank is VOID with 0/32 eligible
events, all 17 gain classes now fail their individual T-FP budgets alongside 8 of 9 adverse
classes, and its coverage shows no observed separation from its random control rate in this
diagnostic. This remains the honest served floor against which '4.1' and '5.0' will be
measured. No candidate generation was scored here or anywhere in B4.5b.

## 9. Erratum (2026-10-02) — what the extract pin pins
`baseline_3_0_extract_v1_0.json` sha256 `70ba6142…` pins the extract's **content** (914 rows). It is **not** a reproducible byte order: the file's row order among rows tied on `(event_class, ws)` was database-defined (the dump query ordered by `(event_class, ws)` only). A fresh read-only re-dump of production `'3.0'` with a total `ORDER BY` has the **identical row multiset** (914 rows) and different bytes (sha256 `b9ec4e4b…`; 24 row positions differ); scoring is order-invariant (the §4.2 merge sorts), and the candidate adapter + scorer reproduce every figure above from **both** files. No figure in this record changed; the extract is **not re-pinned** (steward ruling M20261002T042015-7bff). Candidate extracts are produced by a total-order command and sealed by bytes in the Stage-2 freeze (SI addendum v1.3/v1.4 §5).
