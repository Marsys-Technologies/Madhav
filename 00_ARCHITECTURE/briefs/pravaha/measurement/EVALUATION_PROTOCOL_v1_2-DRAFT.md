---
artifact: EVALUATION_PROTOCOL
canonical_id: EVALUATION_PROTOCOL
version: "1.2-DRAFT"
status: DRAFT_FOR_REVIEW
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
supersedes: "EVALUATION_PROTOCOL_v1_1.md (retained) — v1.2 is a DRAFT, filed for the protocol review; it takes force only when the native's review closes"
amendment_disclosure: >
  Written AFTER the '3.0' scoring pass (B4.3) and BEFORE any '4.1'/'5.0' scoring, on the steward's
  four instructions of 2026-09-29. What was seen before this draft: the full '3.0' baseline. No
  candidate generation has been scored or inspected. B4.3's own deviation (scored before the
  protocol review closed) is disclosed in BASELINE_3_0_v1_0.md and stands as a measurement under
  an unreviewed protocol; nothing further is scored until the native reports the review is done.
---

# Evaluation protocol v1.2 (DRAFT) — deltas on v1.1, per the steward's four instructions

## 1. T-rank restored as a threshold (steward item 2 — replace, don't drop)

The campaign's core defect is flat, unrankable peaks (E5's plateaus); a generation that never
ranks must not pass. Rule:

- **T-rank (co-primary, threshold):** over held-out events with **N ≥ 3 candidate windows** of
  the event's class in the event's year, the median rank percentile of the true window must be
  **≤ 25**.
- **Validity floor:** at least **12** timing-usable held-out events must reach N ≥ 3 for the
  test to be computable. Derivation: the partition holds 23 timing-usable held-out events
  (exact + month-exact, dev cases excluded); 12 is the bare majority — below it a median would
  speak for a minority of the set. A generation reaching N ≥ 3 on fewer than 12 events is
  **rank-unproven**, and rank-unproven **blocks the flip** regardless of the other endpoints:
  the flat-peak defect is exactly what the elevation exists to cure, so "cannot tell whether it
  ranks" is a failing answer, not a neutral one.
- The degeneracy tests of v1.1 §B stand unchanged: class-indiscriminate or plateau classes
  contribute no N to the floor.

## 2. T-FP derived from event density (steward item 3 — not from '3.0''s figure)

Derivation, stated so it can be challenged: the held-out partition carries **8 adverse-class
events** (bereavement 2009.06 · financial_deception 2025.05 · career_setback 2016 · separation
2022.10 and 2026-04-17 · illness_acute 2021.01 · surgery 2007.06 · chronic_onset 2007) over the
scored horizon of 1998-01-01 → 2026-12-31 = 10,587 days. A system that admitted a 90-day window
per true adverse event and nothing else would show an admitted day-fraction of
8 × 90 / 10,587 ≈ **6.8 %**. The bar is set at three times that ideal:

- **T-FP (co-primary):** per adverse class, the negative-year admitted day-fraction must be
  **≤ 20 %** (≈ 3 × the 6.8 % ideal density). A class failing this admits adverse events at
  more than triple the rate the chart's own history could justify. Gain classes keep v1.1's
  0.5 % ≤ base rate ≤ 40 % two-horns rule.

## 3. T-time as a single exact rule (steward item 4)

- **T-time (co-primary):** over the **7 exact-date held-out events** (1998-02-16, 2007-06-10,
  2008-06-09, 2024-02-16, 2026-03-20, 2026-04-08, 2026-04-17), the **median timing error ≤ 45
  days**, where an event with no containing window is scored at the capped miss value of **182
  days** and enters the median like any other value. One rule; no separate miss-count clause
  (the v1.1 "misses ≤ 5 of 7" and "≥ 4 of 7 within 45 d" formulations are withdrawn — the
  capped-miss median subsumes them: '3.0''s five misses at 182 d alone would push its median to
  182 d, failing, as it should).

## 4. Endpoint summary under v1.2

All four are co-primary and necessary: **T-cover** (≥ 22 of 36 with a containing window, every
miss named) · **T-time** (single rule, §3) · **T-FP** (§2) · **T-rank** (§1, with the
rank-unproven flip-block). T-honesty and the v1.1 degeneracy tests stand. The flip
recommendation (D-FLIP) requires all four plus the A5.7 engineering gates.
