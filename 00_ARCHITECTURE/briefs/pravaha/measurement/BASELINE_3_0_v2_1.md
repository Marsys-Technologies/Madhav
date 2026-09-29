---
artifact: BASELINE_3_0
canonical_id: BASELINE_3_0
version: "2.1"
status: SCORED
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
protocol: "EVALUATION_PROTOCOL_v2_1.md"
registry: "EVENT_REGISTRY_v2_1.md"
pinned_extract: "baseline_3_0_extract_v1_0.json — sha256 70ba61421915db2ec3fcf3d1a23bc0ad80d43055b0d0bcc656e5a89079ef84ff (914 rows, predicate: kala_gochara_windows where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and generation='3.0', dates converted to IST civil dates) — the SAME pinned extract as the v2.0 re-run, not re-dumped"
scorer: "rerun_3_0_v2_1_scorer.py (deterministic; committed beside this file)"
controls: "random_controls_v1_1.json — seed 482012, matched resolutions, materialised, sha256 05539e8585e99b6493641fa637d6531e5605bf36e62c0aacb1c2f1f4279a5103"
supersedes: "BASELINE_3_0_v2_0.md — retained in full as disclosed history (its registry omitted SPR.D and carried three over-coarse grains; its T-FP estimand and T-rank degeneracy handling were reworked per round-2 review)"
deviation_history: "unchanged: the original '3.0' pass (B4.3) predated the protocol review close; v2.0 and v2.1 re-runs are re-measurements of an already-served generation, not candidate scores."
---

# Baseline '3.0' under protocol v2.1 — re-run from the pinned extract

All figures recomputed from `baseline_3_0_extract_v1_0.json` (sha256 70ba6142…) by
`rerun_3_0_v2_1_scorer.py`; nothing copied from v2_0 or v1_0. Where an earlier figure is
quoted it is labelled *(history)*.

## 1. Registry-derived counts (scorer asserted)

Held-out **47** (30 timing-usable + 17 year-grain); exact-date cohort 5; interval 2
(grandfather 61 d; 2026.01 interval 59 d); month-grain 23. Horizon H = 1998-01-01 →
2026-04-17 = 10,334 days. Dedup unchanged: every '3.0' era class merges to **1 candidate
spanning 1984–2084**; the five zero-width instant classes (separation, business_launch,
career_change, education_milestone, foreign_settlement) remain 1-day instants.

## 2. Endpoint results ('3.0', v2.1 rules)

| endpoint | rule (v2.1 §6) | '3.0' result | verdict |
|---|---|---|---|
| **T-cover** | 47 held-out, overlap per grain (month-grain = any shared day with the calendar month) | **32/47 = 68.1 %**; 15 misses, all named below (SPR.D, restored in v2.1, is a HIT — spiritual_turn is an era class) | sets the served floor: **≥ 32/47** |
| **T-time** | capped median (cap 182 d) over 5 exact events | **182 d** (misses 2: 2008-06-09, 2024-02-16; uncapped hit errors 686, 998, 327 d) — exact cohort unchanged, figure unchanged | FAIL vs 45 d |
| **T-rank** | N ≥ 3 post-dedup, degenerate classes excluded first, floor floor(30/2)+1 = 16 | all 30 timing-usable events sit in degenerate classes (two-horns); eligible **0/30** → **RANK-UNPROVEN** | FAIL — rank-unproven blocks any flip |
| **T-FP** | single estimand: admitted day-fraction adm/H vs per-class budget 3·n_c·90/H | 8 of 9 adverse classes at **99.87 %** vs budgets 2.61–5.23 % → FAIL; separation 0.09 % PASS (zero-width class — degenerate-low, not specific) | FAIL on 8 of 9 |
| **T-honesty** | coverage ≥ 50 % | era classes 99.87 % (degenerate-high); 5 instant classes ≤ 0.12 % (degenerate-low). **Coverage computation manifest absent → T-honesty UNVERIFIABLE as a build property** (Codex R2-M06); the two-horns flags stand as the scorer-side report | flagged |

**Misses (15), named:** EVT.2001.03 (edu), EVT.2003.06 (edu), EVT.2007.06.XX.02 (edu),
EVT.2008.06.09 (career_change), EVT.2011.01 (edu), EVT.2011.06 (edu), EVT.2013.03 (edu),
EVT.2017.03 (career_change), EVT.2019.05 (foreign_settlement), EVT.2022.10 (separation),
EVT.2023.06 (edu), EVT.2023.07 (business_launch), EVT.2024.02.16 (business_launch),
EVT.2000 (edu, year-grain), EVT.2021.XX.XX.02 (edu, year-grain).

Instant-class statement, corrected (Kimi NK-11): the five zero-width instant classes miss
**15 of their 16** held-out events — **EVT.2004.XX.XX.02 (education_milestone, year-grain,
CMU offer) is a HIT** (a 1-day instant falls inside 2004). The v2.0 narrative's "miss every
event in them" was wrong by one.

## 3. Degeneracy tests (v2.1 §8 — run before any endpoint; exclusions feed T-rank)

- **Era-boundary fingerprint:** 210/351 class pairs share identical boundaries = **59.8 %**
  ≥ 50 % → '3.0' flagged **class-indiscriminate**; T-rank void for it (consistent with the
  rank-unproven result).
- **Two-horns, recounted over all 27 classes including birth_anchor (Codex R2-M07):**
  **22 degenerate-high (99.87 %), 5 degenerate-low (≤ 0.12 %), 0 in-band.** The v2.0
  narrative's "17 gain classes degenerate-high" counted the gain subset only; the corrected
  all-class tally is 22/5/0.
- **Peak-diversity (restored, v1.1 §B.1 wording):** computed per class-year before rank;
  moot for '3.0' — every timing-usable event was already excluded by two-horns.

## 4. Controls

- **Random controls (seed 482012, matched resolutions, materialised v1_1):** 645/940 control
  intervals admitted = **68.6 %** — no observed separation from T-cover's 68.1 % in this
  diagnostic (phrasing corrected per Codex R2-M07: the re-run does not establish "exactly
  equal"; it observes no separation at this resolution). Interval events were drawn at
  interval span (grandfather 61 d, 2026.01 59 d) with `randrange(0, H−span+1)` (off-by-one
  fixed per Codex R2-M05).
- **Adverse-day burden:** reflected in the T-FP figures above (era classes admit 99.87 % of
  all observed days, so any masking choice leaves the verdict unchanged).

## 5. Comparison to earlier runs (history, not operative)

| figure | v1_0 (history) | v2_0 (history) | v2.1 re-run | why it moved |
|---|---|---|---|---|
| T-cover | 21–22/36 | 31/46 | **32/47** | SPR.D restored (a hit); three rows regrained timing-usable; month-grain = calendar-month overlap |
| T-time | median ∞, 5/7 | 182 d, 2/5 | **182 d, 2/5** | exact cohort unchanged |
| T-rank | degenerate N=1 | 1/27 → rank-unproven | **0/30 → rank-unproven** | degeneracy exclusions now run before rank (Codex R2-M03); floor restated to 16 of 30 |
| T-FP | ≤ 49.87 % bar | 99.87 % burden, 8/9 FAIL | **99.87 % = adm/H, 8/9 FAIL** | estimand unified: burden and budget share denominator H (Codex R2-M02) |
| controls | — | 67.6 % (v1_0, 365-day draws for all year events) | **68.6 %** (matched resolutions) | interval-length draws; randrange inclusive fix |

## 6. Verdict

Under protocol v2.1, '3.0' fails every co-primary endpoint except the floor it sets for
T-cover (**≥ 32/47**). It is class-indiscriminate, rank-unproven (0/30 after degeneracy
exclusions), and its coverage shows no observed separation from its random control rate in
this diagnostic. This is the honest served floor against which '4.1' and '5.0' will be
measured — **once the native closes D-PROTO**. No candidate generation was scored here or
anywhere in B3.8.
