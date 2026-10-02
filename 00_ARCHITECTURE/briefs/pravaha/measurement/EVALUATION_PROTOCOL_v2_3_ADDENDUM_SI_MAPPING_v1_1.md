---
artifact: EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING
version: "1.1"
status: "PRE-REGISTRATION — declared before any '4.1' or '5.0' candidate output is inspected; supersedes v1.0"
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 — corrected per Codex round 6 R7
amends: "EVALUATION_PROTOCOL_v2_3 §4 (window identity, ranking) — adds the stored-field mapping and the NULL policy the protocol left silent; changes NO existing rule, threshold, floor, denominator rule or '3.0' figure"
---

# Addendum — the ranking intensity `si`, and what a NULL intensity does

## 1. Mapping (unchanged from v1.0)
**`si := evidence_for`** (the stored `evidence_for` of the merged candidate's highest member, ties per §4.2). `score` is **not** the ranking key.
Reason: `score` is the best single record's factor product, **constrained** by the schema CHECK to [0,1] (1156 `kgew_score_unit_interval_ck`); an exact-contact record with all factors at maximum scores 1.0, so many windows tie at the ceiling — the plateau shape P §8.3 (≥ 50 % identical `si` voids T-rank) and v3.0's defect #24/E5 exist to catch. `evidence_for` is the §2.1 per-channel sum over independent roots, not constrained to [0,1].
**Provenance, stated plainly.** Chosen **after** the '3.0' baseline was seen (BASELINE_3_0_v2_3.md) and **before any candidate output is inspected**. It is a pre-registration, **not blind validation**: the protocol already discloses that its authors have seen the LEL. The absence of '4.1'/'5.0' result files in the repository supports only a repository observation; it cannot prove that no off-repository run occurred.

## 2. Three concepts kept apart (the gap v1.0 left)
| concept | what it is | where defined |
|---|---|---|
| **admission** | a window exists because its prerequisite-satisfied support exists | spec §2.3 / AM-17 — independent of any score |
| **computation coverage** | which (class, year) cells the engine computed | P §6.5 — a statement about *coverage*, not about score qualification |
| **score qualification** | whether a window's `evidence_for` (and peak) is a *known* number | spec §2.1; Codex R1 — `NULL` = unqualified, never 0 |
P §6.5 does **not** say how a merged candidate with a NULL intensity is ranked, and P §9 forbids zero-filling without completing the rule. This addendum completes it.

## 3. NULL policy (conservative, frozen before any candidate inspection)
* **Admission and T-FP burden:** admitted supports **remain in the admission union and in T-FP's admitted-day burden regardless of score qualification.** Unknown necessary-predicate admission is **not** treated as admitted.
* **Known zero** is a numeric value (it ranks, counts and times as 0). **NULL is never a number**: it is not 0, not the minimum, not the mean.
* **Merging, representative selection, candidate counting:** merge by overlap/abutment exactly as §4.2 (supports unaffected by qualification). If the merged candidate's highest-`si` representative **cannot be determined because a contributing intensity is unknown**, **do not invent a numeric `si` or peak**.
* **Ranking, timing, plateau detection:** an affected candidate's ranking and timing result is **unqualified and ineligible to establish a passing endpoint**; it is excluded from the §8.3 same-value grouping and from the percentile arithmetic as unqualified (not as 100, not as 0); the **events are retained** in every denominator (existing event-denominator rules, §6.5 C3 and the worst-rank convention for *eligible misses*, are unchanged) and the **affected candidates are reported by identity**.
* The existing **validity floor** (§6.3: ≥ floor(32/2)+1 eligible events) and all other thresholds are preserved; unqualified candidates reduce eligibility, they do not relax the floor.

## 4. Freeze list — fixed before the first candidate output is inspected
The window/peak rules of AM-17 (maximal connected components; P4 max-min objective; per-root-reduced `evidence_for` objective for other paths; earliest attained maximum; NULL peak when the objective is unqualified) · this qualification policy · the **selected registry versions and the orb state** (ND-ORB-ADMISSION / ND-ORB-SCALE as ruled or "unqualified points") · UTC-to-IST conversion · the merge implementation · stored-value precision · the `1e-9` tie tolerance · candidate-set construction · the scorer and adapter **commits** · the extract hashes · the cohort · thresholds · controls · rerun policy. A change to any of these after a candidate result is a protocol violation and must be disclosed as such.

## 5. What it does not do
It changes no endpoint, bar, tolerance, candidate rule or '3.0' figure (the '3.0' re-run uses its own `si`, unchanged). If a later review prefers `score`, that is a new addendum dated before the run it governs.
