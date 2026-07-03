---
canonical_id: CLAUDECODE_BRIEF_BA_P2_QUERYTIME_RANKING
version: 1.0
status: READY-FOR-EXECUTION — gated on BA-P1 COMPLETE; conductor fills ⟦SLOT⟧ fields before start
created: 2026-07-03
author: Cowork (Beyond-Acharya unified program; substance frozen — conductor fills slots only)
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — phase P2 (the zeroing bench)
slots: ⟦P1_FINAL_TOOL_CENSUS⟧ ⟦P0_BASELINE_TABLE_REF⟧ ⟦HEAD_SHA⟧
common_rules: FROZEN contract §N.2 · ACs [verify-against:] tagged · Ring-1 before merge · degeneracy gate
  on every scoring output · two-chart rule · SESSION_LOG/CURRENT_STATE close · scoring paths LLM-free.
sanity_values: 482012f1 = Aries lagna · Sun Cap H10 Shravana · Moon Aqu H11 P.Bhadrapada · 10th lord
  Saturn · ~12,954 signals/ayanamsha · 90 yogas · ~1,034 contradictions. 1c826d5a ≈12,963 signals ·
  88 yogas. Identical outputs across charts = contamination alarm.
may_touch: ["retrieval registry ranking/composition modules (NEW code paths)", "envelope retrofit sites", "seed-extraction config", "register_d8_assess_domain.ts (assembly only)"]
must_not_touch: ["pipeline writers", "migrations", "stored salience columns / any bodha_* table", "orchestrator/planner/cockpit"]
---

# BRIEF BA-P2 — QUERY-TIME COMPOSITE RANKING + THE PRIOR-TUNING BENCH

**Code anchors:** tool bridge `tool_name_bridge.ts`; registry dispatch `registry_bridge.ts` +
`/api/retrieval/capability/route.ts`; apex `register_d8_assess_domain.ts`. Seeds:
`00_ARCHITECTURE/BEYOND_ACHARYA_W1_JUDGMENT_SEED_PACKAGE_v1_0.md` (priors §1, affinities §5). Golden
questions: `RETRIEVAL_TOOL_BLUEPRINT_v1_0.md` §B5.

## Step 1 — Seed extraction
Extract class-prior table + varga-grain vector + graha×domain + domain×varga affinities from the seed
package into a retrieval-layer runtime config, `prior_version=0.9-prov`. NO migration (the L0 asset lands
in P3A); config schema mirrors the future `brahma_class_priors` row shape exactly.

## Step 2 — The 4-dimensional composite (query time)
`composite = class_prior × topic_relevance × intrinsic_strength × structural_role × temporal_activation`,
percentile-within-class computed on the fly:
- topic_relevance: affinities + bhava-lordship/occupancy from ga_positions/ga_structural.
- intrinsic_strength: REAL shadbala from ga_strength + dignity from ga_condition (never the degenerate
  stored salience).
- structural_role: `COALESCE(pagerank, f(yoga_membership, signature_class))` — pagerank is 100% NULL
  (grounding G-5b); the fallback is REQUIRED.
- temporal_activation: current MD/AD lords direct from chart_dashas (kala bypass — L3 fills in P5A).
`ranking_basis` = {4 sub-scores, composite, priors_version} on EVERY payload.
**Cache:** key (chart_id × domain × priors_version); TTL = MIN(next dasha-boundary from chart_dashas
across active levels, 30d); explicit bust on priors_version bump.

## Step 3 — Envelope retrofit + apex assembly
RetrievalEnvelope on all ⟦P1_FINAL_TOOL_CENSUS⟧ tools (verdict slot null, grounding live, judgment_flags
honest). assess_* assemble the structured verdict SKELETON deterministically: top-k per reasoning-chain
stage (karaka → lord → dispositor → strength → yoga → varga → temporal) + contradiction pairs with both
sides' ranks + activation state + inline citations. No prose.

## Step 4 — P2T: the tuning loop (Ācārya-Pratinidhi drives; config-only iterations)
Run the 10 golden questions → score each with the G10-QT rubric below → adjust priors/affinities →
repeat. Converged when career G10-QT ≥13 AND no question regresses two consecutive iterations. Freeze as
`prior_version=1.0`; write values + full iteration trace into the seed package (version bump) + the
Judgment Ledger.

**G10-QT rubric (/15, pass ≥13):** top-10 contains ≥3 yoga-class signals (3) · a 10th-lord signal (2) ·
a kāraka-congruent signal (2) · ZERO per-varga atomic tallies (2) · no tie-block >3 identical scores (1)
· distribution non-degenerate (2) · every top-10 row cites resolvable facts + a classical source (3).

## Anti-goals
No writes to bodha_* tables; no migrations; do not "fix" stored salience early; do not bake activation
into cached composites beyond the TTL rule; ranking lives in retrieval code + config only.

## Exit gates
- [ ] G10-QT pass on 482012f1 career `[verify-against: prod]` — smoke: `get_signals(482012f1,
      domain=career, limit=10)` → zero `ashtakavarga_bindu_per_varga:*`, ≥3 yoga-class, ranking_basis present
- [ ] latency ≤ +500ms p95 cache-miss / ≤ +50ms cache-hit vs ⟦P0_BASELINE_TABLE_REF⟧ `[verify-against: prod]`
- [ ] prior_version=1.0 frozen + committed; golden-eval score recorded as the standing regression baseline
- [ ] both charts return DISTINCT rankings (contamination check)
