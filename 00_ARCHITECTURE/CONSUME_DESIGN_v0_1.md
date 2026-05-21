---
artifact: CONSUME_DESIGN_v0_1.md
version: 0.1
status: SUPERSEDED (2026-04-27 — content absorbed and refined into MARSYS_JIS_ARCHITECTURE_v1_0.md; retained in place for historical audit and provenance)
revision: v0.1 (2026-04-26 initial) → extended same-session 2026-04-26 with §11 Layer Anatomy + §12 Algorithm Walkthrough + §13 Layer Epistemology
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-26
authoring_session: Cowork conversation — "Consume staleness gap → adaptive design → layer anatomy + algorithm"
purpose: Architectural design for the Consume customer-facing inference layer, framed as adaptive synthesis over the evolving corpus asset universe.
governance_status: NOT YET ADOPTED. Awaits native review. Path to adoption is either (a) ND.2 native directive that binds B.6 to honor it, or (b) PHASE_B_PLAN_v1_0.md amendment to v1.0.4 with explicit B.6 / B.7 deliverables.
relates_to:
  - PHASE_B_PLAN_v1_0.md §B.6 (Hybrid Retrieval), §B.7 (Synthesis Router)
  - MACRO_PLAN_v2_0.md §B.6 line 714 ("thin query UI consumes retrieval library")
  - PROJECT_ARCHITECTURE_v2_2.md §B Architectural Principles, §H.4 Whole-Chart-Read
  - 06_LEARNING_LAYER (prediction ledger, calibration, learned prompts — M3+ consumers)
  - MACRO_PLAN_v2_0.md §Ethical Framework (disclosure tiers, four audiences)
seeds:
  - User observation: "consume must leverage whatever assets are available, structurally."
  - Forensic finding: today's consume-tools.ts hardcodes L2.5 cgm reads, ignores RAG corpus + graph + future capabilities.
---

# CONSUME DESIGN v0.1 — Adaptive Inference Layer

## §1 — Purpose

Consume is the customer-facing inference surface — the chat interface where the native (and any other authorized audience under §6) actually interrogates the corpus. Today's implementation (`platform/src/lib/claude/consume-tools.ts`, `platform/src/app/api/chat/consume/route.ts`) is statically bound: it fetches a single hardcoded layer document (L2.5 "cgm") via `get_layer_document` and reasons over that frozen snapshot. As the corpus enriches phase-by-phase, the chat does not see the enrichment. The "true check" of enrichment — whether richer corpus produces richer answers — cannot be run.

This design replaces static binding with **adaptive consumption**: Consume reads a capability manifest at query time, discovers which assets are CURRENT, and dispatches to whichever assets best serve the query class. As new assets come online (B.5 discovery registers, B.6 hybrid retriever, B.7 synthesis router, M3 learning feedback, M5 temporal engines), Consume code does not change — only the manifest changes, and tool dispatch routes accordingly.

## §2 — Core Principle

**Consume is a function of the current corpus state, not a snapshot of an earlier state.**

Three corollaries follow.

The first is **asset agnosticism**: Consume does not hardcode any specific asset path, version, or capability. It receives a query, classifies it, asks the manifest "what is currently available that serves this query class?", and dispatches accordingly. Removing an asset (e.g., deprecating a stale L3 report) means flipping its manifest entry to `available: false` — Consume routes around it without code change.

The second is **graceful upgrade**: when a richer asset becomes available alongside a lesser one (e.g., hybrid retriever lands while static layer documents still exist), the manifest's `preferred_for` field tells Consume to prefer the richer one for the query classes it serves. The lesser asset remains as fallback. This makes phase transitions non-breaking.

The third is **falsifiable consumption**: every response carries an audit trail naming exactly which manifest version was active, which assets were consulted, and which P-validators passed. If the chat says something wrong, the audit trail makes the diagnosis auditable. This is the precondition for the corpus's "true check."

## §3 — The Asset Universe

Consume reads from ten asset families, each evolving on its own cadence. Each has a stable asset-family ID. New families enter the universe as the macro plan progresses.

The currently-live families (consultable today, with the corpus state at 2026-04-26):

- **`L1_FACTS`** — `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` + `LIFE_EVENT_LOG_v1_2.md`. Immutable canonical chart + 36 events with Swiss-Ephemeris-populated chart_states.
- **`L2_5_HOLISTIC`** — `025_HOLISTIC_SYNTHESIS/{CGM, MSR, UCN, CDLM, RM}`. CGM v9.0 (post-B.3.5), MSR v3.0 (499 signals), UCN v4.0/4.1, CDLM v1.1/1.2, RM v2.0/2.1.
- **`L3_REPORTS`** — `03_DOMAIN_REPORTS/REPORT_*.md`. 9 v1.1 + Financial v2.1.
- **`RAG_CORPUS`** — Cloud SQL `rag_chunks` (993 rows), `rag_embeddings` (977 rows). Chunked, layer-tagged, type-tagged.
- **`RAG_GRAPH`** — Cloud SQL `rag_graph_nodes` (1752), `rag_graph_edges` (3911 — including SUPPORTS post-Exec_7; CONTRADICTS persisting at Exec_8 close).

The future families (declared but not yet consultable):

- **`DISCOVERY_REGISTERS`** — patterns, resonances, contradictions, clusters. B.5 deliverable.
- **`HYBRID_RETRIEVER`** — vector + BM25 + graph-walk + RRF + Voyage rerank + layer-balance. B.6 deliverable (`platform/python-sidecar/rag/retrieve.py` + `platform/src/lib/rag/retrieveClient.ts`).
- **`SYNTHESIS_ROUTER`** — query classifier producing a QueryPlan. B.7 deliverable (`router.py`).
- **`LEARNING_FEEDBACK`** — calibrated signal weights, learned graph edge weights, optimized prompts, prediction-outcome history. M3 deliverable. Learning Layer subsystem.
- **`TEMPORAL_ENGINES`** — dasha periods, transits, time-indexed prediction surfaces. M5 deliverable.

Each asset family carries a stable interface that Consume calls. The asset's internal implementation can evolve (e.g., RAG_GRAPH gains new edge types) without Consume changing — the interface absorbs evolution.

## §4 — The Eight-Stage Pipeline

A query traverses eight stages. Stages 1–2 are deterministic; stages 3–5 read the manifest; stages 6–8 enforce discipline.

**01 RECEIVE.** Ingest the query, the audience tier (from auth context — `super_admin`, `client`, `acharya_reviewer`, or anonymous public per §6), and session context (chart_id, conversation history). Reject malformed inputs with structured errors.

**02 CLASSIFY.** Route the query through a classifier producing a `QueryPlan`: query class (`factual` | `interpretive` | `predictive` | `remedial` | `cross_domain`), required asset families, required validators, expected output shape (single-answer | three-interpretation | time-indexed-prediction). Pre-B.7, this is a lightweight LLM classifier; post-B.7, it is the canonical Synthesis Router. The interface is identical so the swap is non-breaking.

**03 DISCOVER.** Read the capability manifest (`00_ARCHITECTURE/CAPABILITY_MANIFEST.json` or equivalent runtime location). Filter to families marked `available: true` and matching the query class's required asset list. Surface a "capability snapshot" — the exact list of assets that *will* be consulted, recorded for the audit trail at stage 08.

**04 RESOLVE.** Translate the QueryPlan + capability snapshot into a concrete asset-call plan: for each required family, which specific tool to invoke and with what parameters. Apply `preferred_for` rules — e.g., when both `RAG_CORPUS` (vector search) and `HYBRID_RETRIEVER` are available, prefer the latter for `interpretive` queries.

**05 RETRIEVE.** Execute the asset-call plan in parallel where possible. Each asset family exposes a uniform `retrieve(query_plan) -> RetrievalBundle` interface. Bundles carry chunks, citations, provenance (which version of which asset), and confidence indicators. P3 (Whole-Chart-Read) enforcement begins here: every bundle MUST include L2_5_HOLISTIC content regardless of the query's surface domain — this is non-negotiable per `PROJECT_ARCHITECTURE §H.4` / B.11.

**06 VALIDATE.** Run the P-validator stack against the assembled bundle and the synthesis-time intent. Today (B.4 close): P1 (layer separation), P2 (citation discipline), P5 (signal-ID resolution), P6 (UCN-vs-L3 consistency, partial). Coming online: P3 (whole-chart-read enforcement on bundle), P4 (no-fabrication on synthesis output), P7 (three-interpretation), P8 (falsifier presence on time-indexed claims), P9 (audit trail completeness). Each validator votes pass | warn | fail. A `fail` halts; a `warn` annotates.

**07 SYNTHESIZE.** The LLM (Claude) composes the answer using the validated bundle as the *only* substrate. System prompt enforces: cite L1 fact_ids inline; mark interpretive claims with confidence; surface cross-domain signals from CDLM where present; never invent numerical chart values (B.10).

**08 DISCIPLINE.** Apply the four discipline gates before the response leaves Consume.

The first gate, **three-interpretation (P7)**, applies to any interpretive query: the response carries three readings — literal/textual, conventional, and edge-case — with their relative weights. Predictive queries pass through this gate as scenarios.

The second gate, **falsifier (P8)**, applies to any time-indexed claim: the response names what observable would falsify the claim within the named horizon.

The third gate, **audit trail (P9)**, writes a ledger event to `06_LEARNING_LAYER/LEDGER/` capturing: query, capability snapshot, retrieval bundle hash, validator votes, synthesis prompt version, response. For predictive claims, the ledger also writes a prediction record to `prediction_ledger.py` BEFORE the response is streamed (Learning Layer rule #4: outcome-blind prediction logging is sacrosanct).

The fourth gate, **disclosure filter**, applies §6 audience-tier rules. The same answer may be redacted, calibration-banded, or removed entirely depending on who asked.

## §5 — The Capability Manifest

The manifest is a small, declarative JSON that Consume reads at boot (and optionally per-query for hot reload). It is the SINGLE point of coordination between corpus evolution and Consume's behavior.

A representative shape:

```json
{
  "manifest_version": "0.4",
  "as_of_phase": "M2.B.4_complete",
  "as_of_date": "2026-04-26",
  "fingerprint": "sha256:...",
  "assets": {
    "L1_FACTS": {
      "available": true,
      "version": "v8.0",
      "tool_binding": "get_l1_facts",
      "preferred_for": ["factual"],
      "interface_version": "1.0"
    },
    "L2_5_HOLISTIC": {
      "available": true,
      "version": "v9.0",
      "tool_binding": "get_holistic_synthesis",
      "preferred_for": ["interpretive", "cross_domain"],
      "always_required": true,
      "interface_version": "1.0"
    },
    "RAG_GRAPH": {
      "available": true,
      "version": "B.4_close",
      "node_count": 1752,
      "edge_count": 3911,
      "tool_binding": "graph_walk",
      "preferred_for": ["cross_domain"],
      "interface_version": "1.0"
    },
    "HYBRID_RETRIEVER": {
      "available": false,
      "expected_phase": "B.6",
      "expected_session": "Madhav_M2A_Exec_12",
      "preferred_for": ["interpretive", "predictive"],
      "interface_version": "1.0"
    },
    "TEMPORAL_ENGINES": {
      "available": false,
      "expected_phase": "M5",
      "preferred_for": ["predictive"],
      "interface_version": "1.0"
    }
  },
  "validators_active": ["P1", "P2", "P5", "P6_partial"],
  "validators_planned": {"P3": "B.7", "P4": "B.6", "P7": "B.5", "P8": "B.5", "P9": "B.5+"},
  "audience_tiers_supported": ["super_admin", "acharya_reviewer"],
  "audience_tiers_planned": {"client": "M6", "public_redacted": "M10"}
}
```

The manifest is generated at every phase close as part of session-close hygiene. Cowork authors the manifest update; Claude Code applies it; `schema_validator.py` verifies it. The manifest's fingerprint rotates on every change, and Consume logs the active fingerprint into every audit trail (so a response can be reconstructed deterministically given the manifest at query time).

The manifest's `interface_version` per asset is the contract guarantee: as long as the interface_version is stable, Consume keeps working. Breaking changes bump interface_version and trigger a Consume-side adaptation session.

## §6 — Disclosure Tiers (Ethical Framework Binding)

Per `MACRO_PLAN_v2_0.md §3.5` Ethical Framework, four audiences each consume responses under distinct disclosure protocols.

**Native (super_admin).** Full responses. All three interpretations. Falsifiers named. Confidence bands explicit. Internal language permitted. This is the default tier today.

**Acharya reviewer.** Same as native, plus methodology disclosure (which validators ran, which asset families were consulted). For peer review of the instrument's reasoning, not the native's chart.

**Client (consenting third party, M6+).** Their own chart only. Redacted internal terminology. Calibration bands mandatory on predictive claims. No fate-adjacent assertions; only probabilistic guidance with named falsifiers. Chart-cohort comparison disallowed without cross-consent.

**Public redacted (post-M10 research tier).** No individual chart attribution. Aggregated cohort findings only. Calibration bands required. Subject to the §3.9.B publication review gate.

The disclosure filter at stage 08 is the enforcement point. The response composer inside stage 07 is audience-tier-aware and conditions language accordingly; the filter is the belt-and-suspenders check.

## §7 — Validator Stack Detail

The P-validators are the discipline binding. Consume invokes them at stage 06 and again at stage 08 (post-synthesis). Their evolution is part of the manifest.

P1 (`p1_layer_separation.py`) — already live since B.1. Asserts no L1 facts mixed into L2+ claims, no L2+ derivations posing as L1.
P2 (`p2_citation.py`) — already live since B.1. Asserts every L2+ claim's `v6_ids_consumed` field resolves against canonical L1 IDs.
P3 (`p3_whole_chart_read.py`) — B.7 scope. Asserts retrieval bundle includes L2.5 holistic content. Today this is enforced by manifest's `always_required: true` flag plus a stage-05 hard requirement.
P4 (`p4_no_fabrication.py`) — B.6 scope. Asserts no numerical chart values appear in synthesis output that are not in the bundle.
P5 (`p5_signal_id_resolution.py`) — already live since B.1. Asserts every signal_id in synthesis resolves against MSR.
P6 (`p6_uvc_consistency.py`) — partial impl at Exec_8. UCN-vs-L3 conflict scan as candidate-CONTRADICTS surface. Full validator at B.5.
P7 (`p7_three_interpretation.py`) — B.5 Task 0 scope. Asserts interpretive queries return three readings.
P8 (`p8_falsifier.py`) — B.5 Task 0 scope. Asserts time-indexed claims carry named falsifiers.
P9 (`p9_audit_trail.py`) — B.5+ scope. Asserts every artifact's ledger event chain resolves.

The Consume design assumes validators will be added incrementally. Each validator's manifest entry says `available_at_phase: X`. Consume's stage 06 runs whichever set is active at the manifest's `as_of_phase`.

## §8 — Migration Path / Version Tiers

**v0 (today).** Static `get_layer_document` fetch of L2.5 cgm. No retriever. Hardcoded bindings. No manifest.

**v1.0 (post-B.6, ~Madhav_M2A_Exec_12).** First retriever-backed cut. Capability manifest exists. Stages 03–05 wired. `consume-tools.ts` rewritten to call `retrieveClient.ts`. Static document path remains as fallback for asset families without a retriever yet (L1, L3 reports).

**v1.1 (post-B.7).** Synthesis router replaces lightweight classifier in stage 02. P3 + P4 active. Three-interpretation gate (P7) active for interpretive queries.

**v2.0 (post-M3).** Learning feedback consumed. Calibrated signal weights re-rank retrieval bundles. Learned prompts replace static synthesis prompt where calibrated.

**v3.0 (post-M5).** Temporal engines available. Time-indexed predictive queries dispatch to dasha + transit calculation, with falsifier (P8) enforced. Prediction ledger fully wired.

**v4.0 (post-M10).** Public-redacted disclosure tier active. Cross-cohort discovery substrate consultable for aggregate-only queries.

The critical architectural commitment: **between v0 → v4.0, the user-facing chat UI does not change, and the model-facing tool interface evolves only by additive extension**. Internals migrate; the chat keeps working through every phase boundary because the manifest absorbs the change.

## §9 — Open Questions Awaiting Native Decision

The first concerns where the manifest lives. Two candidate locations: `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (governance-layer artifact, mirror-pair candidate) or `platform/src/lib/rag/manifest.json` (code-side artifact). The former binds it to governance discipline (versioning, fingerprint, mirror enforcement); the latter is closer to where Consume reads it. Recommendation: governance-layer, with a code-side cached copy validated against governance master at boot.

The second concerns the v0 → v1.0 transition. Should `consume-tools.ts` be rewritten in a single B.6 session, or should the manifest be introduced first (v0.5) with the existing tools registering as static-doc tools, and then the retriever tool added at v1.0? The phased approach is safer; the single-session approach is faster. Recommendation: phased, with v0.5 landing in B.6 prep and v1.0 closing B.6.

The third concerns audience-tier authentication. Today the portal has Firebase Auth + role check. The four-tier model in §6 requires extending the role machinery. Recommendation: defer to M6 when client tier is needed; today's super_admin gate is adequate for native + acharya_reviewer (manual reviewer accounts).

The fourth concerns the prediction-ledger interim home. Per `MACRO_PLAN §Cross-cutting workstreams`, time-indexed predictions log to LEL (`01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`'s prediction subsection) until B.5 / Step 11 scaffolds `06_LEARNING_LAYER/PREDICTION_LEDGER/`. Consume v0.5 must respect this interim home; v1.0+ migrates to the canonical ledger.

The fifth — and most important — is governance: **does this design get adopted as ND.2 (a binding native directive on B.6) or as a PHASE_B_PLAN amendment v1.0.4?** ND.2 is lighter and faster; the amendment is more durable. Recommendation: ND.2 first, with the requirement that B.6's brief authoring session promotes the directive's content into the plan.

## §10 — Adoption Path (proposed)

If this design is acceptable to the native, the proposed path is:

The first step is the native's review of this document, with annotations and corrections.

The second step is authoring **ND.2** in `00_ARCHITECTURE/NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` binding B.6 (and forward) to honor the design — in particular, requiring that B.6 deliver: the capability manifest, the retriever-backed Consume tools, the manifest-aware tool dispatch, and the Validator Stack hooks. This is a small, fast amendment.

The third step is a Cowork session that authors the **B.6 brief** (`CLAUDECODE_BRIEF_M2A_Exec_12.md` or the appropriate session ID) with ND.2's content fully expanded into per-task acceptance criteria. Claude Code then executes B.6 against that brief.

The fourth step, post-B.6, is Cowork ratifying the design as adopted (status `CURRENT`) and converting any deltas-from-design back into either further ND directives or a PHASE_B_PLAN amendment.

This sequence respects the project's discipline: design-before-build, governance-binds-execution, executor-honors-brief, ratification-after-fact.

---

## §11 — Layer Anatomy (asset universe in detail)

The chat consults a layered corpus. Each layer has its own canonical files, its own role, and its own derivation relationship to the layers below it. Understanding what each layer holds is prerequisite to understanding the algorithm in §12.

### L1 — Facts (foundation · multi-file · citation root)

L1 is foundational and immutable. It contains the only primitive observations in the system. Every claim made anywhere in the corpus, at any layer, traces back to specific L1 fact IDs.

Primary canonical files: `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (the chart — planetary positions, divisional charts, dasha periods, yogas) and `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (36 lived events with Swiss-Ephemeris-populated chart_states).

Supplementary canonical files: `JHORA_TRANSCRIPTION_v8_0_SOURCE.md` (Jagannatha Hora transcription source), `EVENT_CHART_STATES_v1_0.md` (chart states for events), `FORENSIC_DATA_v8_0_SUPPLEMENT.md`, `SADE_SATI_CYCLES_ALL.md`, `EXTERNAL_COMPUTATION_SPEC_v2_0.md`.

Role: source of truth. L1 is never bypassed. It is the citation root for every L2+ claim per Citation Discipline (B.2).

### L2.5 — Holistic Synthesis (5 files · always required)

L2.5 contains the interpretive frameworks *about* the chart. These are *reading instruments*, not narratives — they tell the chat *how to interpret* L1, not *what to say*.

Canonical files (5 distinct artifacts, each with a specific role): `CGM_v9_0.md` — Central Generative Model (the unified causal-generative model of how this specific chart works). `MSR_v3_0.md` — Master Signal Registry (499 catalogued signals — the project's pattern vocabulary). `UCN_v4_0.md` — Unified Causal Network (signal → outcome causal pathways). `CDLM_v1_1.md` — Cross-Domain Linkage Matrix (cross-references between domains). `RM_v2_0.md` — Resonance Matrix (signal reinforcement scoring).

Role: always-required pre-flight for any non-trivial query. The Whole-Chart-Read principle (B.11) makes L2.5 mandatory because without it the chat reads L1 without the lens that turns observation into meaning.

### L3 — Domain Reports (9 files · narrative crystallizations)

L3 is the acharya-grade narrative layer. Nine reports, one per domain.

Current canonical files: `REPORT_CAREER_DHARMA_v1_1.md`, `REPORT_HEALTH_LONGEVITY_v1_1.md`, `REPORT_RELATIONSHIPS_v1_1.md`, `REPORT_FINANCIAL_v2_1.md`, `REPORT_PARENTS_v1_1.md`, `REPORT_CHILDREN_v1_1.md`, `REPORT_TRAVEL_v1_1.md`, `REPORT_PSYCHOLOGY_MIND_v1_1.md`, `REPORT_SPIRITUAL_v1_1.md`. Plus `CROSS_REPORT_COHERENCE_AUDIT_v1_0.md` for inter-report consistency.

Role: pre-computed interpretive paths per domain. L3 is a *crystallization* — it saves the chat from reconstructing common readings from L1+L2.5 every time. The chat still cites L1 underneath; L3 is a shortcut, not a source.

### L3.5 — Discovery Layer (multi-file directory · cross-corpus meta-content)

L3.5 holds patterns + resonances + contradictions + clusters that emerge across the corpus, plus the graph that connects them.

Canonical artifacts: `REGISTERS/PATTERN_REGISTER_v1_0.{json,md}` (just landed in B.5), `REGISTERS/INDEX.json`, `cgm_supports_edges_manifest_v1_0.json`, `cgm_contradicts_edges_manifest_v1_0.json`, `QUERY_TAXONOMY/DECISION_SUPPORT_PLAYBOOK_v1_0.md`, `QUERY_TAXONOMY/SESSION_PROTOCOL_QUESTION_TAXONOMY_v1_0.md`. Plus discovery prompts under `PROMPTS/{claude,gemini}/` and their two-pass response artifacts.

Role: meta-content. Observations *about* the chart-corpus that no single L1+L2.5 reading would produce, but which fall out when the corpus is treated as a connected graph. CONTRADICTION-PROBE queries route here primarily.

### L4 — Remedial Codex (2 files · prescriptive)

L4 answers a different question than L1–L3.5: not "what is" but "what to do."

Canonical files: `REMEDIAL_CODEX_v2_0_PART1.md` and `REMEDIAL_CODEX_v2_0_PART2.md` (paginated single document).

Role: prescriptive remedies — gemstones, mantras, behavioral, dietary, timing windows — given specific L1+L2.5 conditions. L4 is downstream of everything; it cites L1 conditions and L2.5 frameworks.

### L5 — Temporal Engines (3 files + ephemeris · time-projection)

L5 forward-projects L1+L2.5 through dasha and transit math.

Canonical files: `LIFETIME_TIMELINE_v1_0.md` (lifetime dasha + transit timeline), `HEATMAP_VARSHPHAL_v1_0.md` (varshphal annual heatmap), `RED_TEAM_PHASE5_v1_0.md` (red-team artifact for L5). Plus the Python sidecar with Swiss Ephemeris for runtime ephemeris queries.

Role: time-indexed prediction surface. *Without L1, L5 has nothing to project. Without L2.5, L5 produces dates with no interpretation.* L5 operates on L1+L2.5; it does not replace them.

### L6 — Learning Layer (multi-file · meta-feedback · scaffold live, full live M3+)

L6 holds the feedback substrate — calibrated weights, learned prompts, outcome ledgers.

Current files: `PREDICTION_LEDGER/prediction_ledger.jsonl` (outcome-blind prediction log — sacrosanct per Learning Layer rule #4), `LEDGER/two_pass_events.jsonl` (two-pass discovery events), `PROMPT_REGISTRY/INDEX.json`, `SCHEMAS/{prediction, two_pass_events, pattern}_schema_v0_1.json`, plus subdirectories for `SIGNAL_WEIGHT_CALIBRATION/`, `GRAPH_EDGE_WEIGHT_LEARNING/`, `EMBEDDING_SPACE_ADAPTATION/`, `PROMPT_OPTIMIZATION/` (mostly scaffold today; full implementations land at M3+).

Role: meta-feedback. L6 adjusts *how* the chat reads L1–L5 over time. It never replaces lower layers; it tunes the reading.

### Transversal projection — RAG Corpus + RAG Graph (Cloud SQL, not a layer)

The RAG corpus and graph are not a "layer" in the L-sense. They are a *structured projection* of L1+L2.5+L3 content into chunked, vector-embedded, graph-walkable form for query-time retrieval.

Cloud SQL tables: `rag_chunks` (993), `rag_embeddings` (977 · Voyage-3-large 1024-d), `rag_graph_nodes` (1752), `rag_graph_edges` (3911 · CITES, MENTIONS, AFFECTS_DOMAIN, CROSS_LINKS, SUPPORTS, CONTRADICTS).

Role: query-time retrieval surface. Same content as the layer files, different access pattern. For semantic-similar passage lookup, vector search beats full-file read. For cross-domain cross-references, graph walk beats reading multiple reports. For exact narrative quotation, full-file read beats chunked retrieval. The chat picks the access pattern that fits the query.

## §12 — Algorithm Walkthrough (concrete query example)

The eight-step pipeline from §4 is abstract. Here is what it looks like for a real query.

**Query:** *"Will my Saturn return next year impact my career?"*

**Step 1 — Receive & Classify.** Class: PREDICTIVE × CROSS-DOMAIN (Saturn return touches career but also psychology, health, dharma). Audience tier: super_admin (native).

**Step 2 — Whole-Chart-Read pre-flight.** Load `CGM_v9_0.md` (full file — narrative). Surface Saturn-related signals from `MSR_v3_0.md` (filter by signal-text matches Saturn). Check `UCN_v4_0.md` Saturn pathway sections. Scan `CDLM_v1_1.md` for Saturn cross-domain links. Score `RM_v2_0.md` Saturn-resonance. Bundle holds the L2.5 substrate.

**Step 3 — Resolve layers per QueryPlan.** Per the matrix in §11 figure: L1 ★, L2.5 ★ (already loaded in step 2), L3 ●● (multiple — CAREER_DHARMA primary, PSYCHOLOGY_MIND + HEALTH_LONGEVITY secondary because Saturn cross-links there), L3.5 ● (graph-walk from Saturn node to find connected patterns + any CONTRADICTS edges that would qualify the prediction), L5 ★ (mandatory for predictive — `LIFETIME_TIMELINE_v1_0.md` + transit math for the Saturn return date), L6 ● (prediction ledger entry).

**Step 4 — Retrieve in parallel.** L1: find natal Saturn position from `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` plus relevant LEL events showing past Saturn-related episodes. L3 reports: full file reads (narrative-grade). L3.5: graph-walk from the Saturn-position node, depth 2, including SUPPORTS and CONTRADICTS edges. L5: file read of `LIFETIME_TIMELINE_v1_0.md` for the dasha context + Python sidecar call to the ephemeris for the exact Saturn return date. RAG corpus: semantic search for "Saturn return" passages across the corpus to pick up subtle cross-references.

**Step 5 — Validate (P1–P9).** P1 layer separation — confirm no L1 facts smuggled into L2+ claims in the bundle. P2 citation discipline — confirm every interpretive snippet cites resolvable L1 fact_ids. P3 whole-chart-read — confirm L2.5 is in the bundle (yes, from step 2). P5 signal_id resolution — confirm every MSR signal_id surfaced resolves in MSR. P6 UCN-vs-L3 consistency partial scan. P7 prepares to require three interpretations. P8 prepares to require falsifier. P9 prepares the audit-trail event template.

**Step 6 — Synthesize.** Compose answer. Cite natal Saturn's L1 fact_id inline ("your natal Saturn at [position] [F.087]"). Name the CGM section that explains Saturn's role in this chart. Quote the CAREER_DHARMA report's Saturn passage. Surface the CDLM cross-link from career to psychology/health for the Saturn return window. Lay out the dasha context (from L5 timeline) and the transit math (Saturn return date ±tolerance). Apply confidence bands.

**Step 7 — Discipline gates (P7 + P8).** Generate three interpretations of the career impact (literal: "career disruption likely"; conventional: "Saturn returns are tests of vocational maturity"; edge-case: "this Saturn return follows two strong-Saturn dasha periods so the test may compound"). Name the falsifier ("prediction is wrong if no significant career-domain disruption signal manifests within ±6 months of [named window]"). Apply disclosure filter (super_admin tier — full response permitted).

**Step 8 — Ledger & stream.** Write the audit-trail event to `06_LEARNING_LAYER/LEDGER/two_pass_events.jsonl` with bundle hash, validator votes, prompt version, and manifest fingerprint. Write the prediction record to `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl` *before* streaming — outcome-blind logging is sacrosanct per Learning Layer rule #4. Then stream the response to the chat UI.

One query. Six layers consulted. Every claim cited. Falsifier named. Prediction ledger written. This is acharya-grade at the chat layer.

## §13 — Layer Epistemology (the why behind the routing)

The most important question native asked: *"Do we need L1 if we have L5?"* The answer is no, and the reasoning generalizes.

**Higher layers crystallize, project, or prescribe over lower layers — they never subsume them.** Every layer has a distinct epistemic role:

L1 is *observation* — what the chart shows.
L2.5 is *framework* — how to read what the chart shows.
L3 is *narrative* — pre-computed interpretive paths per domain.
L3.5 is *meta-observation* — patterns about the chart-corpus visible only at scale.
L4 is *prescription* — what to do given what we observe and how we read it.
L5 is *projection* — what the observation+framework imply forward in time.
L6 is *meta-feedback* — how the reading itself should be tuned given outcomes.

L5 is *L1+L2.5 unfolded forward in time*. Strip L1 and L5 has nothing to project; strip L2.5 and L5 produces dates with no meaning. The same logic holds upward: L4 strips meaningless without L1 conditions and L2.5 frameworks; L3 strips meaningless without L1 chart and L2.5 lens; L3.5 strips meaningless without the L1+L2.5+L3 substrate to find patterns within.

The principle in one line: **the chat's authority comes from grounding, and grounding comes from L1 always being in the citation chain.** A chat answer that quotes only L3 narrative is a generic-LLM answer dressed in domain language. A chat answer that traces every claim to L1 fact_ids — through whichever combination of L2.5 / L3 / L3.5 / L4 / L5 the query class requires — is acharya-grade.

This is also what makes the chat's outputs falsifiable. An answer with citation chains is auditable. An answer without is unfalsifiable, which is the same as untestable, which is the same as not-real-knowledge for this project's purposes.

## §14 — Implications for ND.2

The layer anatomy and algorithm walkthrough sharpen what ND.2 must require of B.6 (and forward). Three concrete obligations.

The first is **layer-aware tool decomposition**. The B.6 retriever cannot be a single "search the corpus" function. It must expose layer-specific entry points — `retrieve_from_l1`, `retrieve_from_l25`, `retrieve_from_l3`, `graph_walk_l35`, `temporal_project_l5` — so that Step 3 of the algorithm can resolve layers explicitly. The hybrid retriever is one of these tools, not the only one.

The second is **citation-chain enforcement at synthesis time**. The synthesis prompt at Step 6 must require inline L1 fact_id citation for every interpretive claim. P2 validates this; P4 (no fabrication) blocks any claim whose citation does not resolve. Both validators must be wired into Consume's pipeline at v1.0 (B.6 close), not deferred.

The third is **prediction-ledger pre-stream write**. For any PREDICTIVE-class query, the ledger write at Step 8 must complete before the response streams. This is not optional. Outcome-blind prediction logging is the Learning Layer's foundation — if we ever stream a prediction without ledgering it first, we contaminate the very dataset that calibrates the system.

These three obligations, plus the manifest discipline from §5, are what ND.2 should bind B.6's executor brief to deliver.

---

*End of CONSUME_DESIGN_v0_1.md extended (DRAFT_PROPOSAL, 2026-04-26 same-session). Awaits native review. Next concrete artifact: ND.2 draft text.*
