---
artifact: CLAUDECODE_BRIEF_WAVE3_4_RETRIEVAL_AND_BODHA_v1_0.md
canonical_id: WAVE3_4_RETRIEVAL_AND_BODHA_BRIEF
version: 1.0
status: CODE_COMPLETE
authored_by: Cowork (planning) 2026-06-12
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
execution_mode: CONTINUOUS / AUTONOMOUS — phase-by-phase, NO human gate between phases (native directive). Only dependency gates + Tier-3 escalation rails (genuine ambiguity / destructive op / architecture change) pause execution. Native reviews retrospectively via cockpit/Atlas + Smṛti.
governing: MARSYS_CONSOLIDATED_RUNWAY_v1_1 (Waves 0-2 DONE; this is Wave 3 → Wave 4) + L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0 + L2_BODHA_BUILD_CAMPAIGN_v1_0 (§14 map, §13 philosophy) + A10_MSR_SPEC v1.2 (projection model)
data_plane: ALWAYS prod via Cloud SQL proxy
extends: platform/src/lib/retrieval + platform/python-sidecar/pipeline/retrieval (do NOT build a parallel retrieval layer) ; the FROZEN orchestrator (Bodha writers onboard, never extend it)
---

# Wave 3 (Retrievability) + Wave 4 (L2 Bodha) — Phased Continuous Brief v1.0

## §0 — How to run this brief
ONE brief, TWO waves, EIGHT phases (R1–R3 then B1–B5). Implement **phase-by-phase, continuously** —
finish a phase, verify it against prod, proceed to the next WITHOUT waiting for human sign-off. Stop
only on a real dependency miss or a Tier-3 event (destructive op, genuine ambiguity, needed
architecture change → raise to native). Each phase has its own acceptance; the whole thing is one
PR-able arc (or a PR per phase if cleaner — your call, just don't gate on the native between them).

**Inherited non-negotiables (apply to every phase):** deterministic-first; no audience tier
([[feedback-no-audience-tier]]); no silent drops (errors shown/flagged, never hidden); per-chart
isolation by chart_id; real fact_id references (never mock); FROZEN orchestrator contract (Bodha
writers are `@register('bo_*')` WriterBase, run on ctx.db_conn, never commit, no asset_throughput
writes); count_sql is data-truth (§N.4). Floors aspirational (target_floor = achieved after build).

---
# WAVE 3 — RETRIEVABILITY LAYER (the 2nd pillar)
Goal: every relevant stored deterministic fact is reachable by the LLM through tools. The data-
integrity audit found legacy tools exposed ~30% of stored categories; close that to ~100%. Build ON
the existing retrieval layer (platform/src/lib/retrieval + python-sidecar/pipeline/retrieval) + the
canonical tool registry (3 primitive types: tools/resources/prompts; 4 adapters; NO tier gating —
[[reference-retrieval-layer-architecture]]).

## PHASE R1 — Coverage map + the missing-tool inventory
- Enumerate every stored category the LLM should reach: ALL chart_facts fact_categories (positions,
  strength/shadbala, ashtakavarga, bhava-bala, panchanga, aspects [all per-varga], yoga/dosha labels,
  argala, dispositors, sade-sati, varshaphal, sensitive points, the 8 new GA8 relationship families)
  + L0 (brahma_yoga_catalog, brahma_dosha_catalog, brahma_remedy_corpus, classical_text_chunks,
  sutravali_rules) + L2 bodha_* (once Wave 4 lands).
- Diff against the tools that exist. Produce the gap list (category → has-tool? / NOT-covered).
- Acceptance: a committed coverage matrix; every NOT-covered category named.

## PHASE R2 — Build the missing retrieval tools (close the gap to ~100%)
- Add the tools R1 found missing. Principles: each tool is registry-defined (data-driven, not
  hardcoded per-category); chart-scoped ($1=chart_id) for per-chart, unfiltered for global; returns
  rows + the strength/salience + epistemic-tier columns (so the LLM can SAY "low-confidence" — don't
  strip tier); **NO weak-tail truncation** — paginate, never `LIMIT N`-drop (the project keeps the
  whole distribution; serve-time ranks, never drops at retrieval). Expose the L0 corpus too (yoga/
  dosha/remedy/text catalogs) so the LLM can cite classical sources.
- Acceptance [verify-against: prod]: every category from R1 now has a working tool returning real
  rows for the native; weak/low-strength rows ARE returned (spot-check a low-salience signal is
  reachable); L0 catalog queryable.

## PHASE R3 — Planner/routing coverage + retrieval-completeness CI gate
- Ensure the planner/router can reach every tool (no category orphaned because the planner never
  calls its tool). Add a **retrieval-completeness contract test**: every chart_facts.fact_category +
  every bodha_* table MUST have ≥1 tool, or CI flags it — turns Pillar 2 into a regression gate.
- Acceptance: the CI gate exists + passes; a deliberately-unexposed category fails it (proving it works).

---
# WAVE 4 — L2 BODHA (the destination)
Build the synthesis layer as a PURE PROJECTION over the now-complete ga_structural — NOT a re-firing
engine (A10 v1.2; L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION). bo_laksana inherits L1's fired
relationships by fact_id and adds population-level significance (rank/convergence/contradiction/
domain-salience). Then the rest of the Bodha DAG. Tables per L2_BODHA_BUILD_CAMPAIGN §14; design per
§13 (convergence + contradiction first-class; graph built deepest; every judgment a versioned formula).

## PHASE B1 — bo_laksana (MSR) as projection (the root)
- `@register('bo_laksana')` WriterBase. For each L1 structural fact (ga_structural relationship +
  its intrinsic strength) → ONE MSR signal row in `bodha_msr_signals`: reference the L1 fact_id in
  `constituent_facts_array` (inherit L1's value, NEVER re-derive/re-fire), attach the salience
  decomposition via `salience_formula_v1` (the versioned pure fn already in bodha_writers/formulas.py)
  + domain tagging + epistemic tier carried from L1 (two_pass_verified vs documented_approximation).
  NO predicate registry (G52 retired); NO threshold drop (every firing → a row, strength is a column).
  Heavy writer → plan_substeps (per-ayanamsha and/or per signal-class). Build the 3 MVs (A10 §11).
- Acceptance [verify-against: prod]: bodha_msr_signals populated for the native; every signal's
  constituent_facts_array resolves to real chart_facts rows (the anti-drift spine — zero unresolved);
  no re-firing (signal count tracks ga_structural fact count, not a predicate catalog); FORENSIC-
  anchored signals inherit L1 values (Muntha = Libra/7H/Venus, not re-derived); two-pass; weak tail present.

## PHASE B2 — the fan-out (parallel on bo_laksana)
- `bo_bimba` (CGM nodes) + `bo_karanajala` (CGM edges/sub_graphs/motifs/paths + owns bodha_contradictions),
  `bo_sangati` (CDLM cells/rollups/clusters + bodha_convergence — convergence-density-per-domain via
  convergence_formula_v1), `bo_samskara` (embeddings, 1:1 with MSR signals). All project/aggregate
  from bo_laksana; all populate their §14 tables; graph built DEEPEST (final-dispositor convergence,
  centrality via centrality_formula_v1, significator path-analysis per §13.1). bo_samvada = UCD/
  Option-A (read-side join vw_chart_digest + query_ucd; NOT a per-chart writer).
- Acceptance: each fan-out asset's §14 tables populated; convergence + contradiction are first-class
  rows (not just columns); CGM graph metrics present; embeddings 1:1 with MSR.

## PHASE B3 — bo_upaya (RM) — dependents
- `@register('bo_upaya')` (depends_on bo_laksana + bo_sangati). All 6 bodha_rm_* tables via
  resonance_score_v1; remedies labelled from brahma_remedy_corpus (L0), grounded not invented.
- Acceptance: 6 RM tables populated; every remedy carries a classical citation; resonance scored deterministically.

## PHASE B4 — bo_pramana_mapa + UCD read surface
- `bo_pramana_mapa` global synthesis_quality_scorecard. Build the UCD read surface (vw_chart_digest
  view + query_ucd tool) per A14 — the join of the chart_summary rows, NOT a writer.
- Acceptance: scorecard populated; query_ucd returns the unified digest for the native.

## PHASE B5 — orchestrator build + cockpit verify + L2 seal
- Run the whole layer via the orchestrator (`POST /api/cockpit/runs scope=layer/bodha`, native chart).
  Cockpit/Atlas: 8 bo_ assets lit, counts true (summed count_sql per §14), all via the orchestrator path.
- Reconcile registry (the §14 map: each bo_ row → its real tables + summed count_sql; flip DRAFT→CURRENT).
- Seal: author L2_BODHA_CLOSE with validated state + the L3 Kāla onboarding contract.
- Acceptance: layer builds from one orchestrator run in DAG order; FORENSIC 7/7; no silent drops;
  Atlas shows all Bodha assets lit with real sample rows + astrological notes; L2_BODHA_CLOSE written.

---
## §FINAL — Acceptance for the whole arc
- [ ] Wave 3: ~100% of stored categories (L0 + L1 + L2) reachable by ≥1 retrieval tool; weak tail retrievable; CI completeness gate live.
- [ ] Wave 4: all 8 bo_ assets lit; bo_laksana is a projection (constituent_facts resolve, no re-fire); convergence/contradiction first-class; graph deepest; UCD read surface live; L2 sealed with L3 onboarding contract.
- [ ] Whole arc ran continuously phase-by-phase — no human gate fired (only dep gates / Tier-3 rails).
- [ ] Cockpit/Atlas reflect the new state truthfully (count_sql reconcile); migration numbers fresh (no collisions); seed-apply hardening held (post-apply readback passed).

## §OUT OF SCOPE
L3 Kāla / dasha-temporal (next layer, post-L2-seal); any GA8 re-amendment (ga_structural complete);
re-opening settled architecture. Do NOT reintroduce the predicate-firing model or G52.

---
*End of WAVE3_4_RETRIEVAL_AND_BODHA v1.0. One brief, continuous phase-by-phase: R1 coverage map → R2
build missing tools → R3 planner+CI gate (retrievability ~100%) → B1 bo_laksana projection → B2 fan-out
(convergence/contradiction first-class, graph deepest) → B3 bo_upaya → B4 pramana+UCD → B5 orchestrate
+ seal. No human gates between phases; dependency gates + Tier-3 rails only. bo_laksana PROJECTS L1,
never re-fires. The two founding pillars (completeness done; retrievability + synthesis here) close.*
