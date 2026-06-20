---
artifact: L2_BODHA_RETRIEVAL_STRATEGY_v1_0.md
canonical_id: L2_BODHA_RETRIEVAL_STRATEGY
version: 1.0
status: GOVERNING (the retrieval layer for L2 Bodha — binds every L2_bodha tool + the serve/composition layer)
authored_by: Cowork 2026-06-19
purpose: >
  The governing strategy for how the LLM RETRIEVES from the 9-asset L2 Bodha layer (the second pillar). Lands two
  cross-cutting principles held out of the per-asset briefs: F1 (spine-organized, reference-don't-repeat
  composition — the cross-asset de-duplication) and the LEL toggle propagation (lel_enabled + lel_origin
  exclusion). Plus the layer-resolution contract (L2→L1→L0) + the canonical L2_bodha tool set + the coverage gate.
governing_inputs:
  - L2_BODHA_STRATEGIC_FINDINGS_TRACKER_v1_0.md (F1 de-dup + F3 layer-resolution)
  - LEL_TOGGLE_GOVERNING_PRINCIPLE_v1_0.md (lel_enabled + lel_origin)
  - reference: platform/src/lib/retrieval/registry (3 primitive types; 4 adapters; NO tier gating) + the coverage gate
---

# L2 Bodha — Retrieval Strategy v1.0

## §1 — The principle: completeness is worthless if the LLM can't reach it efficiently
The retrieval layer is the SECOND pillar. It is built ON the existing registry (3 primitive types: tools/resources/
prompts; 4 adapters; no tier gating) — never a parallel one. Each asset's tools are specified in its brief; THIS
doc governs the CROSS-ASSET concerns that no single brief owns.

## §2 — F1: SPINE-ORGANIZED, REFERENCE-DON'T-REPEAT composition (the cross-asset de-dup)
**The risk:** one question touches multiple asset tools (msr + cdlm + ucd + lens + cgm + rm); the SAME fact
surfaces through all of them → lands at the LLM N× = token bloat AND weighting distortion (a fact seen 5× looks 5×
important — re-introducing, via retrieval, the double-counting we banned in the data).
**The nuance:** the N perspectives are COMPLEMENTARY (msr=what it is, cdlm=what it links, cgm=position, ucd=defining,
rm=remedy); only the shared IDENTITY is redundant. The signal is the SPINE; the assets are ANNOTATIONS on it.
**The rule — emit each fact ONCE with its perspectives ATTACHED:** "Jupiter–Venus conjunction [msr: salience 0.81]
[cdlm: links career↔wealth] [cgm: central hub] [ucd: chart-defining] [rm: …]" — NOT five separate dumps. Enabled
cheaply because every asset already references by `signal_id` / `constituent_fact_ids` (capture-once-reference-many)
— the data KNOWS it's the same signal; retrieval must EXPLOIT it.
**Three mechanisms:**
1. **Lens/digest as the PRIMARY query surface + natural de-duplicator** — bo_drishti (lens) + bo_samvada (gestalt)
   return ONE entry per signal with all asset-perspectives merged. The LLM queries THESE first, not five raw asset tools.
2. **Hydration return shape** — raw asset tools return REFERENCES (signal_ids + that asset's delta); the
   composition layer resolves each unique signal_id ONCE and merges the per-asset deltas (a join collapsing on the key).
3. **The "reference, don't repeat" contract** — when an answer touches a signal through multiple tools, the
   composition emits the signal once + lists the perspectives. **B6 tests this** ("same fact_id appearing N× in one
   answer = FAIL").

## §3 — THE LEL TOGGLE in retrieval (lel_enabled + lel_origin exclusion)
Per LEL_TOGGLE_GOVERNING_PRINCIPLE — every L2_bodha tool + the composition/serve layer carries this:
- Every tool accepts **`lel_enabled: true|false`** (default FALSE — deterministic).
- **OFF:** EXCLUDE every `lel_origin`-tagged element (the hard provenance filter, transitive); return PURE
  DETERMINISTIC values (which always exist alongside). The return must be assertable as ZERO lel_origin elements.
- **ON:** JOIN the LEL calibration overlay (additive); return calibrated values; the return STATES that LEL is applied.
- The provenance in every return names the MODE (deterministic vs LEL-calibrated) so the LLM is transparent.

## §4 — LAYER-RESOLUTION (F3 — the LLM uses all three layers; L2 points DOWN)
L2 is a layer of MEANING + REFERENCE; it does NOT re-store raw values. So retrieval RESOLVES DOWN the layers:
- "what does it MEAN / how strong / what links / what's buried" → **L2_bodha** tools.
- "the EXACT longitude / shadbala NUMBER / dasha DATES" → **L1_ganita** tools (get_strength, get_positions, …).
- "what the CLASSICAL text SAYS / catalog definition" → **L0_brahmagyan** tools (query_classical_texts, query_yoga_catalog, …).
An MSR signal's `constituent_facts_array` resolves to the L1 fact (precise value); its `classical_sources_jsonb`
resolves to the L0 citation. The composition can HYDRATE a signal across layers (L2 meaning + L1 value + L0
citation) in one assembled answer. (All 3 retrieval layers EXIST — verified.)

## §5 — The canonical L2_bodha tool set (per the asset briefs — the cross-reference)
bo_laksana: query_msr / semantic. bo_sangati: query_domain_evidence + cell/rollup. bo_karanajala/bimba: node/edge/
motif/path fetch + the RECURSIVE-TRAVERSAL primitive + query_cross_subsystem + semantic/topology. bo_samskara:
query_signals_semantic + query_signal_to_classical (the bridge). bo_upaya: query_remedies + query_resonance_targets
+ query_remedy_program + query_remedies_for_problem. bo_samvada: query_ucd (the orientation/first-call) + query_zoom.
bo_drishti: query_lens. bo_anveshana: query_discoveries + query_anomalies (+ the "tell me something I don't know"
signature tool). bo_pramana_mapa: query_scorecard + query_self_assessment.
**The orientation pattern:** the LLM's FIRST call is query_ucd (the gestalt, de-duplicated, with discovery-lead);
it THEN drills via query_zoom / lens / domain-evidence — targeted, not five scattershot asset calls.

## §6 — The coverage gate (extended)
The existing coverage_gate (syntactic) is extended so: every bodha_* table reachable; every `source_subsystem`
reachable; the cross-subsystem edges reachable; the discoveries reachable. B6 (semantic) sits ABOVE it. NO tier gating.

---
*End of L2_BODHA_RETRIEVAL_STRATEGY v1.0. The second pillar: F1 spine-organized reference-don't-repeat composition
(each fact once, perspectives attached — the lens/digest as primary surface + hydration + the contract B6 tests);
the LEL toggle (lel_enabled + transitive lel_origin exclusion — OFF returns provably-deterministic, ON joins the
overlay); layer-resolution (L2 meaning → L1 value → L0 citation, hydrated in one answer); the canonical L2_bodha
tool set with query_ucd as the de-duplicated orientation first-call; the extended coverage gate beneath B6.
Completeness is worthless without efficient access — this is how the LLM reaches it.*
