---
artifact: BASELINE_3_0
canonical_id: BASELINE_3_0
version: "2.2"
status: SCORED
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
protocol: "EVALUATION_PROTOCOL_v2_2.md"
registry: "event_registry_v2_2.json (+ EVENT_REGISTRY_v2_2.md review copy)"
pinned_extract: "baseline_3_0_extract_v1_0.json — sha256 70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff (914 rows, predicate: kala_gochara_windows where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and generation='3.0', dates converted to IST civil dates) — the SAME pinned extract as the v2.0/v2.1 re-runs, not re-dumped"
scorer: "rerun_3_0_v2_2_scorer.py (deterministic; committed beside this file)"
result_file: "rerun_result_v2_2.json (machine-readable per-endpoint status; per-event records in rerun_per_event_v2_2.json)"
controls: "random_controls_v1_2.json — seed 482012, ONE frozen experiment (rolling spans at each event's own actual span length), sha256 71372433fe76c6ddffdb5161cb8d5c362acdff9e444f0c83d3cc63eb3b2ff648"
supersedes: "BASELINE_3_0_v2_1.md (sha256 b4c46222…) — retained in full as disclosed history"
deviation_history: "unchanged: the original '3.0' pass (B4.3) predated the protocol review close; v2.0/v2.1/v2.2 are re-measurements of an already-served generation, not candidate scores."
---

# Baseline '3.0' under protocol v2.2 — re-run from the pinned extract

All figures recomputed from `baseline_3_0_extract_v1_0.json` (sha256 70ba6142…) by
`rerun_3_0_v2_2_scorer.py`; nothing copied from v2_1, v2_0 or v1_0. Where an earlier figure
is quoted it is labelled *(history)*.

## 1. Registry-derived counts (machine-checked, source-reconciliation MATCH)

Held-out **47** (32 timing-usable + 15 year-grain); exact-date cohort 5; interval-date **4**
(grandfather 61 d; 2026.01 interval 59 d; 2007–08 sleep disorder 730 d; 2021–22 quarry
730 d); month-grain 23. Horizon H = 1998-01-01 → 2026-04-17 = 10,334 days. The scorer
re-derived every count from `event_registry_v2_2.json` and matched the registry header
(timing 32/32, year 15/15, exact 5/5, interval 4/4) — the §9.2 invariant is satisfied with no
diff to reconcile.

**Dedup (corrected narrative, Codex R2-M07 — printed from the scorer's own merge block):**
v2.1's "70 → 30/29/27" figures were **wrong** (an ad-hoc merge script of mine had a
running-end bug; the scorer's merge was always correct). The true table:

| raw rows → merged candidates | classes |
|---|---|
| 70 → **10** | career_setback, chronic_onset, financial_deception, major_gain, major_loss, parental_event, relocation, spiritual_turn |
| 64 → **10** | psychological_arc |
| 40 → 40 | education_milestone |
| 30 → 30 | business_launch, career_change, separation |
| 30 → **20** | foreign_settlement |
| 10 → 10 | all other 17 classes (incl. the era classes — 10 non-abutting decade candidates over 1984–2084) |

In-year N is what T-rank consumes; these class-merged totals are printed, not asserted.

## 2. Input adapter (R3-P01 — enforced on RAW rows, machine-readable)

Raw valence domain of the pinned extract: **270 gain / 330 loss / 134 mixed / 180 neutral**
— v2.1's claim that adverse rows carry valence `loss` was false (70 parental_event rows are
`mixed`, 10 surgery rows `neutral`; X:6291–6299, 9855–9863) and is corrected in protocol
v2.2 §4.5. The enforced convention is on **si sign**: raw rows with si < 0 = **0** →
`input_adapter.status = PASS` (any violation would have written `INPUT_REJECTED` and stopped
the run before merging).

## 3. Endpoint results ('3.0', v2.2 rules)

| endpoint | rule (v2.2 §6) | '3.0' result | verdict |
|---|---|---|---|
| **T-cover** | 47 held-out, overlap per grain | **32/47 = 68.1 %**; 15 misses, all named below. The two re-grained interval rows (2007–08 chronic_onset, 2021–22 property_acquisition) are HITs, as they were at year-grain | sets the served floor: **≥ 32/47** |
| **T-time** | capped median (cap 182 d) over 5 exact events | **182 d** (misses 2: 2008-06-09, 2024-02-16; uncapped hit errors 686, 998, **333** d) | FAIL vs 45 d |
| **T-rank** | N ≥ 3 post-dedup, degeneracy exclusions first, floor floor(32/2)+1 = 17; machine-readable void | era-fingerprint **59.8 %** ≥ 50 % ⇒ `t_rank.status = "VOID"` in `rerun_result_v2_2.json` — **no rank median is emitted as a result**. (A diagnostic-only median over timing-usable events with N ≥ 1 computes to **0.0** — labelled `diagnostic_only`; it demonstrates exactly why the void must be enforced in code: against '3.0''s single in-year candidate per class, every hit ranks first and a printed median would look perfect.) Eligible 0/32 | FAIL — rank void; rank-unproven blocks any flip |
| **T-FP** | admitted day-fraction adm/H vs per-class budget 3·n_c·90/H | 8 of 9 adverse classes at **99.87 %** vs budgets 2.61–5.23 % → FAIL; separation 0.09 % PASS (degenerate-low, not specific) | FAIL on 8 of 9 |
| **T-honesty** | coverage ≥ 50 % + manifest | Coverage computation manifest absent → `t_honesty.status = "UNVERIFIABLE"` (build requirement for future generations); two-horns flags stand as the scorer-side report | flagged |

**T-time uncapped-error note (source-reconciliation disclosure):** v2.1 printed the third
uncapped hit error as 327 d; v2.2 prints **333 d**. The difference is the v2.2 §4.2
merge-representative rule (ties → earliest peak), now in prose: major_gain's merged
2024–2034 candidate carries several si = 0.55 rows; the earliest tied peak (2025-04-21) is
6 days before the first-in-window-order peak v2.1 used (2025-04-27). The capped median
(182 d) is unaffected. Recorded here per the §9.2 invariant — the side that changed is the
declared rule, not a bug on either side.

**Misses (15), named:** EVT.2001.03 (edu), EVT.2003.06 (edu), EVT.2007.06.XX.02 (edu),
EVT.2008.06.09 (career_change), EVT.2011.01 (edu), EVT.2011.06 (edu), EVT.2013.03 (edu),
EVT.2017.03 (career_change), EVT.2019.05 (foreign_settlement), EVT.2022.10 (separation),
EVT.2023.06 (edu), EVT.2023.07 (business_launch), EVT.2024.02.16 (business_launch),
EVT.2000 (edu, year-grain), EVT.2021.XX.XX.02 (edu, year-grain). Identical set to v2.1.

**Instant-class statement (the B3.7 packet question, settled):** the five instant classes
(education_milestone, career_change, business_launch, foreign_settlement, separation) miss
**15 of their 16** held-out events; EVT.2004.XX.XX.02 (CMU offer, year-grain) is a HIT. This
is **'3.0''s behaviour, not a scorer artefact**: the scorer does evaluate instant classes —
their merged candidates exist (40/30/30/20/30 per the dedup table) but carry base rates of
0.09–0.12 % (degenerate-low), so their windows almost never overlap an event span. The
scorer's instant handling is the same overlap test applied to every other class
(`rerun_3_0_v2_2_scorer.py` `hit()`); there is no special-case path to artefact.

## 4. Degeneracy tests (v2.2 §8 — run before any endpoint)

- **Era-boundary fingerprint:** 210/351 class pairs share identical boundaries = **59.8 %**
  ≥ 50 % → '3.0' flagged **class-indiscriminate**; T-rank VOID (machine-readable, §6.3).
- **Two-horns, all 27 classes including birth_anchor:** **22 degenerate-high (99.87 %),
  5 degenerate-low (≤ 0.12 %), 0 in-band** (gain subset: 14 high / 4 low / 0 ok).
- **Peak-diversity (§8.3, 1e-9 tolerance — the ONE tie tolerance of §4.3):** computed per
  class-year before rank; moot for '3.0' — the generation-wide void already applied.

## 5. Controls

- **Random controls (seed 482012, ONE frozen experiment, materialised v1_2):** rolling spans
  at each event's own actual span length in days (actual calendar months 28–31 d, actual
  years 365/366 d, intervals at their own lengths incl. the two new 730 d rows); domain
  `randrange(0, H−span+1)` inclusive; any-shared-day overlap; unweighted. Result: **638/940
  = 67.9 %** of control intervals admitted — no observed separation from T-cover's 68.1 % in
  this diagnostic. (v2.1's controls read 645/940 = 68.6 % *(history)*; the 7-draw difference
  comes from the two re-grained events drawing at 730 d instead of 365/366 d — the seed and
  every other span are unchanged.)
- **Adverse-day burden:** reflected in the T-FP figures above (era classes admit 99.87 % of
  all observed days, so any masking choice leaves the verdict unchanged).

## 6. Comparison to earlier runs (history, not operative)

| figure | v2_0 (history) | v2.1 (history) | v2.2 re-run | why it moved |
|---|---|---|---|---|
| registry | 46 held-out, floor 15 | 47, floor 16 | **47, floor 17** | SPR.D restored (v2.1); two multi-year rows as 730-d intervals (v2.2) |
| T-cover | 31/46 | 32/47 | **32/47** | unchanged — both re-grained rows were and remain hits |
| T-time | 182 d, 2/5 | 182 d, 2/5 | **182 d, 2/5** | exact cohort unchanged; one uncapped hit error 327 → 333 via the declared tie rule |
| T-rank | 1/27 → rank-unproven | 0/30 → rank-unproven | **VOID (machine-readable), 0/32** | generation-wide void now enforced in code (R2-M03) |
| T-FP | 99.87 % burden, 8/9 FAIL | 8/9 FAIL | **8/9 FAIL** | estimand unchanged; budgets unchanged (n_c stable) |
| controls | 67.6 % | 68.6 % | **67.9 %** | two events draw at 730 d (registry change, same seed) |

## 7. Verdict

Under protocol v2.2, '3.0' fails every co-primary endpoint except the floor it sets for
T-cover (**≥ 32/47**). It is class-indiscriminate, its T-rank is VOID with 0/32 eligible
events, and its coverage shows no observed separation from its random control rate in this
diagnostic. This is the honest served floor against which '4.1' and '5.0' will be measured —
**once the native closes D-PROTO** (which now gates scoring only, not J1). No candidate
generation was scored here or anywhere in B4.5.
