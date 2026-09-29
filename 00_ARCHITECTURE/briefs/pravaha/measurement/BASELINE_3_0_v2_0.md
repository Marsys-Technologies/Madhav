---
artifact: BASELINE_3_0
canonical_id: BASELINE_3_0
version: "2.0"
status: SCORED
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
protocol: "EVALUATION_PROTOCOL_v2_0.md"
registry: "EVENT_REGISTRY_v2_0.md"
pinned_extract: "baseline_3_0_extract_v1_0.json — sha256 70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff (914 rows, predicate: kala_gochara_windows where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and generation='3.0', dates converted to IST civil dates)"
scorer: "rerun_3_0_v2_0_scorer.py (deterministic; committed beside this file)"
controls: "random_controls_v1_0.json — seed 482012, materialised, sha256 ef6ad8a2dc40e0d622ef8ca72100e1fede96f4ce9537d87dbb12d0a1f559a2e6"
supersedes: "BASELINE_3_0_v1_0.md — retained in full as disclosed history (scored under protocol v1.0, before the protocol review closed; its numerators/denominators were wrong per Codex M-02 and its registry mixed status rows with dated onsets)"
deviation_history: "unchanged from v1_0: the original '3.0' pass (B4.3) predated the protocol review close; that measurement stands as history and this v2.0 re-run replaces it as the operative baseline."
---

# Baseline '3.0' under protocol v2.0 — re-run from the pinned extract

All figures recomputed from `baseline_3_0_extract_v1_0.json` by `rerun_3_0_v2_0_scorer.py`;
nothing copied from v1_0. Where a v1_0 figure is quoted for comparison it is labelled
*(v1_0 history)*.

## 1. Registry-derived counts (scorer asserted)

Held-out 46 (27 timing-usable + 19 year-grain); exact-date cohort 5; interval 1; horizon
H = 1998-01-01 → 2026-04-17 = 10,334 days. Dedup merged each class's rows: every '3.0' class
is a chain of abutting decade windows → **1 merged candidate per class spanning 1984–2084**,
except the five zero-width instant classes (separation, business_launch, career_change,
education_milestone, foreign_settlement) whose rows are 1-day instants.

## 2. Endpoint results ('3.0', v2.0 rules)

| endpoint | rule (v2.0 §6) | '3.0' result | verdict |
|---|---|---|---|
| **T-cover** | 46 held-out, containing window per grain | **31/46 = 67.4 %**; 15 misses, all named below | sets the served floor for candidates: **≥ 31/46** |
| **T-time** | capped median (cap 182 d) over 5 exact events | **182 d** (misses 2: 2008-06-09, 2024-02-16; uncapped hit errors 686, 998, 327 d — all cap to 182) | FAIL vs 45 d |
| **T-rank** | N ≥ 3 post-dedup, floor 14 of 27 | **1 of 27** events reach N ≥ 3 (EVT.2024.02.16.01, business_launch, N = 3 instant candidates — a miss, entered at worst-rank 100) → **RANK-UNPROVEN** | FAIL — rank-unproven blocks any flip |
| **T-FP** | per-class budgets 3·n_c·90/H | 8 of 9 adverse classes at burden **99.87 %** vs budgets 2.61–5.23 % → FAIL; separation 0.09 % PASS (zero-width class admits almost nothing — degenerate-low, not specific) | FAIL on 8 of 9 |
| **T-honesty** | coverage ≥ 50 % | era classes 99.87 % base rate (degenerate-high); 5 instant classes ≤ 0.12 % (degenerate-low) | flagged per two-horns |

**Misses (15), named:** EVT.2001.03 (edu), EVT.2003.06 (edu), EVT.2007.06.XX.02 (edu),
EVT.2008.06.09 (career_change), EVT.2011.01 (edu), EVT.2011.06 (edu), EVT.2013.03 (edu),
EVT.2017.03 (career_change), EVT.2019.05 (foreign_settlement), EVT.2022.10 (separation),
EVT.2023.06 (edu), EVT.2023.07 (business_launch), EVT.2024.02.16 (business_launch),
EVT.2000 (edu, year-grain), EVT.2021.XX.XX.02 (edu, year-grain). Pattern: the five zero-width
instant classes (education_milestone, career_change, business_launch, foreign_settlement,
separation) serve only 1-day instants and miss every event in them.

## 3. Degeneracy tests (v2.0 §8)

- **Era-boundary fingerprint:** 210/351 class pairs share identical boundaries = **59.8 %**
  ≥ 50 % → '3.0' is flagged **class-indiscriminate**; T-rank void for it (consistent with the
  rank-unproven result).
- **Two-horns:** 17 gain classes degenerate-high (99.87 %), 5 instant classes degenerate-low
  (≤ 0.12 %). No scored class sits in the 0.5–40 % band except none — every class violates a
  horn.

## 4. Controls

- **Random controls (seed 482012, materialised):** 622/920 control intervals admitted =
  **67.6 %** — indistinguishable from T-cover's 67.4 %. '3.0' covers true events at exactly
  the rate it covers random dates: its coverage carries no information.
- **Negative days:** reflected in the T-FP burdens above (era classes admit 99.87 % of
  negative days).

## 5. Comparison to v1_0 (disclosed history, not operative)

| figure | v1_0 (history) | v2.0 re-run | why it moved |
|---|---|---|---|
| T-cover | 22/36 (Codex M-02 corrected to 21/36) | 31/46 | registry fixed: CURRENT.01 status row removed, MBA enrolment restored, 2026-04-08 excluded, 2026-03-20 remapped to major_gain, year-grain set completed to 19 |
| T-time | median ∞, misses 5/7 | capped median 182 d, misses 2/5 | exact cohort is 5 not 7 (CURRENT.01 and 2026-04-08 removed); cap 182 per single rule |
| T-rank | degenerate N=1, uninformative | rank-unproven (1/27 ≥ N3) | dedup merges era chains to 1 candidate/class |
| T-FP | ≤ 49.87 % bar (from '3.0''s own figure) | per-class budgets 2.61–5.23 %, 8/9 FAIL | bar derived from event density (registry §5) |

## 6. Verdict

Under protocol v2.0, '3.0' fails every co-primary endpoint except the floor it sets for
T-cover (31/46). It is class-indiscriminate, rank-unproven, and its coverage equals its random
control rate. This is the honest served floor against which '4.1' and '5.0' will be measured —
**once the native reports the protocol review closed**. No candidate generation was scored
here or anywhere in B3.6.
