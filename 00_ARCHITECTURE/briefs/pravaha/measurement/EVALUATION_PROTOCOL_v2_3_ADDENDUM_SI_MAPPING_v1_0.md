---
artifact: EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING
version: "1.0"
status: "SUPERSEDED by ..._v1_1.md (Codex round 6 R7: NULL behaviour was not supplied by the cited protocol sections; 'clipped' corrected to 'constrained'). The mapping choice itself (si := evidence_for) and its provenance statement stand."
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 — steward ruling M20261002T001617-8321 item (3)
amends: "EVALUATION_PROTOCOL_v2_3 §4 (window identity, ranking) — adds the stored-field mapping the protocol left silent; changes NO existing rule, threshold or figure"
---

# Addendum — which stored field is the ranking intensity `si`

## The gap
Protocol v2.3 §4.3 ranks candidate windows "by **signed intensity, descending**" and §4.5 requires `si` to be stored **non-negative**
for every class; §8.3 voids T-rank for a class-year when ≥ 50 % of its in-year windows share one `si` value. The protocol never says
**which stored window field is `si`**. For the new generations the window table (`ka_gochara_eval_window`, migration 1156) carries both
`score` (REAL, **∈ [0,1]**, NULL = unqualified) and `evidence_for` / `evidence_against` (REAL, finite ≥ 0, unbounded).

## The pre-registered mapping
**`si := evidence_for` (the stored `evidence_for` of the merged candidate's highest member, ties per §4.2).** `score` is **not** used for
ranking. Windows whose `evidence_for` is NULL or whose path is unqualified follow the existing unqualified rules (§6.5 / §9) — nothing new.

## The reason
`score` is the best single record's within-path factor product, clipped to [0,1] by the schema CHECK. Any record at an exact contact with all
factors at their maximum scores **1.0**, so many windows tie at the ceiling — exactly the plateau shape that §8.3's peak-diversity test
(and v3.0's 27-of-41 plateau, defect #24/E5) is built to flag. `evidence_for` is the §2.1 per-channel sum over independent roots and is
not clipped, so it separates windows that `score` cannot. This is a statement about information in the ranking key, not a prediction of
which generation will do better.

## Honest provenance of the choice
It was chosen **after** the '3.0' baseline was seen (BASELINE_3_0_v2_3.md: T-rank VOID, era-boundary fingerprint 59.8 %, T-FP failing on 8/9
adverse classes) and **before any candidate result exists**: at this commit `measurement/` holds the '3.0' re-run files and
`SCORING_RUN_4_1_PLAN_v1_0.md` (a plan) but **no '4.1' or '5.0' result file of any kind**, and no scorer has been run on either generation.
It is therefore a pre-registered choice made with knowledge of '3.0' only; it was not tuned against any candidate output.

## What it does not do
It changes no endpoint, bar, tolerance, candidate rule or '3.0' figure (the '3.0' re-run uses its own `si`, unchanged). If a later review
prefers `score`, that is a new addendum dated before the run it governs; a mapping change **after** a candidate result is a protocol
violation and must be disclosed as such.
