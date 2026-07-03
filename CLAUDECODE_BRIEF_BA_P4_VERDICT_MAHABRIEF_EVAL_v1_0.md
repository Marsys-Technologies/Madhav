---
canonical_id: CLAUDECODE_BRIEF_BA_P4_VERDICT_MAHABRIEF_EVAL
version: 1.0
status: READY-FOR-EXECUTION — gated on BA-P3B COMPLETE; conductor fills ⟦SLOT⟧s
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program; substance frozen — conductor fills slots only)
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P4 (verdict object · Mahā-Brief · full eval)
slots: ⟦P3B_CLOSE_SHA⟧ ⟦GOLDEN_EVAL_SCORE_AFTER_P3B⟧
common_rules: FROZEN contract · Ring-1/Ring-2 · latency budgets vs P0 baseline · PD-5 (until step 6
  retires it) · deterministic serving (LLM narrates ABOVE the envelope, never inside it).
sanity_values: 38 topics per RETRIEVAL_MODERNIZATION §7; attention budget 70/20/10 from
  brahma_formula_constants; verdict fields per BA_RATIFICATION_GUIDANCE §2.2.
may_touch: ["retrieval composition modules", "mi_darshana writer (insight_units = verdict home)", "NEW synth_chart_brief_get + synth_tail_divergence_get tools", "eval harness", "LiveDependencyGraph.tsx/AssetTable.tsx refactor", "assess_*/get_domain_reading/mimamsa_insight_get serving"]
must_not_touch: ["L1/L2 writers (data frozen post-P3)", "orchestrator", "prior values", "envelope field REMOVALS (additive only)"]
---

# BRIEF BA-P4 — VERDICT OBJECT + MAHĀ-BRIEF + FULL EVAL

**Code anchors:** apex `register_d8_assess_domain.ts`; verdict home `mi_darshana` →
`mimamsa_insight_units` (EXISTS, migration 353); UCD front-matter source `bodha_chart_gestalt` /
`vw_chart_digest`; hardcoded UI maps `LiveDependencyGraph.tsx`, `AssetTable.tsx`, `asset_names.ts`;
golden questions `RETRIEVAL_TOOL_BLUEPRINT_v1_0.md` §B5.

## Step 1 — The verdict object (deterministic assembly)
`content.verdict = {claim, ranked_evidence[], contradictions[{side_a, side_b, weights, resolution,
status}], tradition_concordance (bodha_triangulation), activation_state, ayanamsha_robustness,
confidence?, falsifier?, citations[]}` — assembled by CODE from P3B data; persisted to
mimamsa_insight_units; served through assess_*, get_domain_reading, mimamsa_insight_get.

## Step 2 — Query-time judgment terms + attention budget
Apply at query time (never stored): dasha_activation boost (S-E) · karaka_congruence (A-A) ·
domain×varga affinity (A-D) — all read from brahma_class_priors / brahma_formula_constants. Every
synthesis payload shaped 70/20/10 head/dissent/tail (constant registry-governed, per-query-class tunable).

## Step 3 — The complement pass
NEW `synth_tail_divergence_get(chart, domain)`: synthesis over ONLY the tail (head withheld) → cited
divergence memo; attached as `tail_divergence` on verdicts; embedded at Mahā-Brief deep/complete depths.

## Step 4 — THE MAHĀ-BRIEF
NEW `synth_chart_brief_get(chart_id, depth ∈{standard,deep,complete})`: all 38 topics in reasoning-chain
order; per topic head/dissent/tail-digest + citations + fact_id refs; front matter = orientation digest
(vw_chart_digest) + promise-register summary + contradiction census; back matter = provenance manifest
(grounding score per section). Architecture: generated-on-demand from the per-topic registry core
(server-side batched), CACHED as an artifact keyed (chart × depth × priors_version × data_build_id) —
never a stored table. ≤1M tokens at complete.

## Step 5 — Eval harness FULL
Ācārya-Pratinidhi authors golden answers for ALL query classes Q1–Q9 (blueprint's 10 + period-quality +
undertaking + compatibility-deferred-note), each flagged `lel_overlap` where applicable (eval corpus ∩
learning corpus = ∅). Astro-Examiner blind rubric: 3 independent scorings, median. Harness wired as the
standing per-promotion regression gate.

## Step 6 — PD-5 retirement
Refactor LiveDependencyGraph + AssetTable to registry-driven rendering; retire ASSET_NAMES/ASSET_MAP;
visual check vs the PG baseline screenshot.

## Anti-goals
The LLM never WRITES verdict content — assembly is deterministic; narration sits above the envelope.
Mahā-Brief never becomes a stored table. No envelope field removals. Eval goldens never enter any
calibration/training path.

## Exit gates
- [ ] blind rubric ≥13/15 median on the golden set (INTERPRETATION classes both charts; others as data
      allows pre-P5) `[verify-against: prod]`
- [ ] Mahā-Brief(complete) on 482012f1: all 38 topics present + ranked + cited, ≤1M tokens, cache hit on
      repeat `[verify-against: prod]`
- [ ] tail_divergence non-trivial on ≥1 domain `[verify-against: prod]`
- [ ] UI registry-driven (add a fake registry row in a txn → appears in graph+table → rollback)
      `[verify-against: prod]`
- [ ] latency budgets hold vs P0 baseline `[verify-against: prod]`
