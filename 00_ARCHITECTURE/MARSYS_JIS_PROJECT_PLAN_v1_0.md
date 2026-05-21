---
artifact: MARSYS_JIS_PROJECT_PLAN_v1_0.md
version: 1.0
status: DRAFT
revision: v1.0 (2026-04-27 initial)
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
authoring_session: Cowork conversation — "Master project plan authoring, post-architecture approval"
purpose: Master project plan that operationalizes MARSYS_JIS_ARCHITECTURE_v1_0.md into ten sequenced phases of executable work. Defines per-phase goals, components, deliverables, dependencies, parallelization, acceptance criteria, rollback paths, and test strategies. This document is the blueprint that per-phase execution briefs (Artifact 3 series) draw against.
governance_status: NOT YET ADOPTED. Awaits native review. Path to adoption: same as architecture document — ND.2 native directive or PHASE_B amendment v1.0.4. Adoption is sequenced: this plan adopts only after the architecture v1.0 it depends on is adopted.
depends_on:
  - MARSYS_JIS_ARCHITECTURE_v1_0.md (APPROVED 2026-04-27; pending formal adoption — this plan operationalizes its component decomposition and phasing preview)
relates_to:
  - PROJECT_ARCHITECTURE_v2_2.md §B Architectural Principles (inherited)
  - MACRO_PLAN_v2_0.md §Cross-cutting workstreams, §Learning Layer (Phase 10 calibration loop substrate aligns with M5)
  - PHASE_B_PLAN_v1_0.md §B.6, §B.7 (this plan's Phases 1, 2, 3, 9 collectively deliver what B.6 and B.7 specify, within the holistic architecture)
authoring_constraints:
  - Q1 resolved: this plan elaborates under PROJECT_ARCHITECTURE; does not subsume.
  - Q2 resolved: aggressive single-phase manifest migration in Phase 1; not multi-phase parallel operation.
  - Q3 resolved: cross-native query class added at Phase 2; per-native namespacing built into Phase 1 from start.
---

# MARSYS-JIS Project Plan v1.0

## §1 — Purpose and Document Hierarchy

This document is the master project plan for building the system specified in `MARSYS_JIS_ARCHITECTURE_v1_0.md`. The architecture document tells you *what* and *why*; this plan tells you *how* and *when* — sequenced into ten phases of executable work, each phase scoped to be deliverable and rollback-able as a unit.

This plan is the second of three planning artifacts. Artifact 1 was the architecture document. Artifact 3 is a series of per-phase execution briefs — one per executable phase, sized for one Claude Code session (or a small bounded sequence), authored against this plan's per-phase specifications. The execution briefs are the documents Claude Code reads and builds against; this plan is the blueprint they draw from.

Three layers of documentation govern execution. The architecture document (Artifact 1) defines stable contracts and component boundaries that change rarely. This plan (Artifact 2) defines the work breakdown that changes occasionally, when phasing learns from execution. Execution briefs (Artifact 3) define per-session scope that changes constantly as phases are completed and the next briefs are authored. Different stability classes belong in different documents.

Throughout this plan, references to component identifiers (`C1.1`, `C2.4`, etc.) point to the architecture document's §4 component specifications. References to stage numbers (`Stage 4.5`, `Stage 7`, etc.) point to the architecture's §5 pipeline. Where this plan references architectural decisions, it cites the architecture's section number for traceability.

## §2 — Phasing Principle

Phases are bounded by **dependency** and **value-delivery**. A phase's outputs are either (a) prerequisites for subsequent phases or (b) end-user-visible value, and ideally both. Each phase produces deliverables that are testable in isolation, deployable behind a feature flag, and reversible if the phase fails verification.

Three rules govern phasing decisions:

**Rule 1 — Sequential dependencies are real.** Some phases must complete before others can start. Phase 1 (Data Plane) cannot start before Phase 0 (Foundation) because the data plane depends on foundation abstractions. Phase 7 (Panel Mode) cannot start before Phase 6 (LLM Checkpoints) because panel mode reuses checkpoint patterns. The dependency graph in §14 captures these.

**Rule 2 — Parallelism is allowed where dependencies are clean.** Phase 4 (Audit & Persistence) and Phase 5 (Interface basic) can run concurrently after Phase 3 (Synthesis) completes — they touch different domains. Phase 9 (Advanced Retrieval) can run concurrently with Phase 6 + Phase 7 work. Native confirmed parallel Claude Code streams are permitted (2026-04-27); §14 names which phases parallelize cleanly.

**Rule 3 — Each phase ends in a known-good state.** No phase leaves the system mid-migration or partially refactored. If a phase's acceptance criteria are not met, the phase rolls back fully; the system returns to the prior phase's known-good state. This rule is what makes the migration path safe even with aggressive choices like Phase 1's hard cutover (Q2 resolved).

Phase numbering reflects sequence intent, not strict ordering — Phase 4 and Phase 5 share the same dependency on Phase 3 and can run concurrently. The numbering helps reasoning about prerequisites.

## §3 — Definition-of-Done Criteria (Universal)

Every phase satisfies these conditions before being declared `COMPLETE`:

**Code-level.** All deliverables in the phase's specification exist in the codebase. All tests in the phase's test strategy pass. No regressions introduced in pre-existing tests. Linting and type-checking pass.

**Documentation-level.** Code changes are documented inline where non-obvious. Schema changes have migration scripts. New components have interface documentation. Architecture document is updated only if the phase surfaced architectural revisions (rare; flagged for native review separately).

**Audit-level.** Per-component telemetry is wired (per architecture §4.6 C6.4). Phase deliverables emit metrics that confirm correctness (e.g., "manifest reads succeed at >99.9%"). Audit trail captures phase-relevant events.

**Operational-level.** Feature flags gate new behavior so the phase can be rolled forward and back without code changes. Migration scripts (where present) have verified rollback paths. Deployment configuration changes are version-controlled.

**Native-acceptance-level.** Native reviews phase output (or designates a reviewer). Phase acceptance criteria are confirmed satisfied. Open implementation questions surfaced during execution are resolved or explicitly deferred.

A phase that fails any of the above stays in `IN_PROGRESS` status until resolved. Partial completions do not graduate.

## §4 — Phase 0: Foundation (D6)

**Goal.** Establish the cross-cutting abstractions that every other phase depends on. This is foundational work with no end-user-visible deliverable; its value is enabling everything else.

**Components touched (architecture §4.6).** C6.1 LLM Provider Abstraction (with OpenAI/GPT integration). C6.2 Schema Registry. C6.3 Configuration Service. C6.4 Telemetry stubs.

**Deliverables.**
- `@ai-sdk/openai` package installed; version compatible with Vercel `ai` SDK in use.
- New OpenAI provider adapter at `platform/src/lib/models/openai.ts` implementing the uniform `streamText` interface.
- `platform/src/lib/models/registry.ts` updated with GPT-5 entry (or current OpenAI flagship at execution time) — capability flags: `tool-use: true`, `prompt-caching` per `@ai-sdk/openai` documentation, `streaming: true`, appropriate `maxOutputTokens`.
- `platform/src/lib/models/resolver.ts` updated with `case 'openai'` resolver branch.
- `platform/src/lib/schemas/` directory with JSON Schema definitions for the six load-bearing types: `QueryPlan`, `Bundle`, `ToolBundle`, `AuditEvent`, `AssetEntry`, `PanelMetadata`. Schemas versioned per architecture §15.
- `platform/src/lib/config/` directory with hot-reloadable Configuration Service. Reads from environment variables with overrides; supports feature flags. Initial flags: `PANEL_MODE_ENABLED` (default off), `MANIFEST_BUILDER_ENABLED` (default off), `LLM_CHECKPOINTS_ENABLED` (default off).
- `platform/src/lib/telemetry/` directory with metric recording stubs. Initial metrics: per-component latency, per-component cost, per-component error rate.
- `.env.example` updated with `OPENAI_API_KEY` requirement and explanatory comment.
- `ModelStylePicker` component (existing) updated to include the GPT-5 entry in its dropdown.

**Dependencies.** None. This is the foundational phase.

**Parallelization within phase.** Three sub-streams can run concurrently: (a) OpenAI provider integration (registry + resolver + adapter + env + UI dropdown); (b) Schema Registry (six schema files + validation utility); (c) Configuration Service + Telemetry stubs. Three Claude Code sessions in parallel, each owning one sub-stream.

**Acceptance criteria.**
- User selects GPT-5 in the model picker, sends a query, receives a streamed response indistinguishable from existing Claude/Gemini/DeepSeek single-model behavior.
- Schema validation passes for at least one example record per schema (`QueryPlan`, `Bundle`, `ToolBundle`, `AuditEvent`).
- Configuration Service exposes feature flags via env override; values changeable without redeploy (hot-reload verified).
- Telemetry records at least one metric for at least one component; metric appears in Cloud Monitoring or equivalent.
- All existing single-model query paths (Claude variants, Gemini variants, DeepSeek variants) continue to work without regression.

**Rollback path.** Revert `package.json` (remove `@ai-sdk/openai`), revert registry/resolver, remove env var, remove schemas/config/telemetry directories. System returns to pre-Phase-0 state. Trivially reversible because Phase 0 is purely additive.

**Test strategy.** Unit tests for the OpenAI adapter (mock provider responses). Integration test for OpenAI end-to-end query (real API call against a test query). Schema validation unit tests. Configuration Service unit tests (env override behavior). Existing-behavior regression suite (all 8 current models still work).

**Estimated Claude Code sessions.** 2-3 sessions. Three parallel sub-streams; ~1 session each plus integration/test session.

**Open implementation questions for execution-time review.** Which OpenAI flagship version to integrate (GPT-5 vs. GPT-5.x — verify against OpenAI's current model list at execution time). Whether OpenAI prompt caching needs explicit cache-control headers or is fully automatic.

## §5 — Phase 1: Data Plane (D1) — Aggressive Manifest Migration

**Goal.** Build the Capability Manifest as the single source of truth for asset discovery; aggressively migrate FILE_REGISTRY + CANONICAL_ARTIFACTS into it (Q2 resolved); bake per-native namespacing into the storage layer from start (Q3 prerequisite); extend the existing ingestion pipeline to emit the manifest atomically with RAG table updates; conduct asset-lifecycle cleanup per the five-category model.

**Components touched (architecture §4.1).** C1.1 Asset Catalog (Capability Manifest). C1.2 Ingestion Pipeline (extends existing). C1.3 Storage Layer (abstraction + per-native namespacing).

**Deliverables.**
- `platform/python-sidecar/rag/manifest_builder.py` — auto-derives base manifest from filesystem walk + frontmatter parsing.
- `00_ARCHITECTURE/manifest_overrides.yaml` — curated overrides file (`preferred_for` per query class, cost weights, exclusions, classification hints).
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — published manifest (auto-derived merged with overrides), fingerprint-rotated on every regeneration.
- `platform/python-sidecar/rag/ingest.py` extended: emit manifest update atomically with RAG table updates. Single-transaction integrity.
- Frontmatter discipline updates across all canonical files: add `expose_to_chat`, `supplements_parent` (where applicable), `native_id` (initially `"abhisek"` for all single-native files; cross-native files get `"universal"`). Existing fields (`version`, `status`, `layer`, `canonical_id`) preserved.
- `99_ARCHIVE/` directory: predecessors >2 generations behind moved here per the five-category model (architecture §7). FORENSIC v6.0, FORENSIC v7 supplement, MSR v1.0/v2.0, CGM v1.0/v2.0, UCN v1.0-v3.0 all move; v8/v3/v9/v4 stay as canonical and v6+1=v7 as recent predecessor where applicable.
- `SOURCES/` subdirectory pattern: source-category files (e.g., `JHORA_TRANSCRIPTION_v8_0_SOURCE.md`) either move to `01_FACTS_LAYER/SOURCES/` or get frontmatter `expose_to_chat: false` and `category: source`.
- `platform/src/lib/storage/` — Storage Layer abstraction with PostgreSQL (Cloud SQL) + GCS + filesystem adapters. Uniform interface per architecture §4.1 C1.3.
- DB schema migrations (Cloud SQL):
  - `messages` table: add `panel_metadata JSONB` column (nullable, default null) — supports Phase 7.
  - All multi-tenant-relevant tables get `native_id VARCHAR(64) NOT NULL DEFAULT 'abhisek'` columns: `messages`, `conversations`, `prediction_ledger`, `audit_log`, `msr_signals` (when MSR ETL lands), `documents`.
  - Composite indices `(native_id, ...)` on tables that will be queried per-native.
- MSR ETL: parse `MSR_v3_0.md`, load 499 signals into a new `msr_signals` PostgreSQL table with typed columns (`signal_id`, `domain`, `planet`, `house`, `nakshatra`, `dasha_lord`, `confidence`, `significance`, `is_forward_looking`, `claim_text`, `classical_basis`, `falsifier`, `native_id`, plus indices). One-time ETL — re-runnable.
- Hard cutover: governance tooling updated.
  - `platform/scripts/governance/drift_detector.py` reads from manifest (replacing CANONICAL_ARTIFACTS reads).
  - `platform/scripts/governance/schema_validator.py` reads from manifest.
  - `platform/scripts/governance/mirror_enforcer.py` reads from manifest (with mirror-pair info merged from manifest.mirror_pairs section).
- `FILE_REGISTRY_v1_11.md` and `CANONICAL_ARTIFACTS_v1_0.md` frontmatter `status` flipped to `SUPERSEDED`. Files retained in place for historical audit; not consulted by tooling.
- New `manifest_validator.py` in governance scripts: parity check against the previous registries (one-time during migration; deprecated after cutover verified).

**Dependencies.** Phase 0 complete (Schema Registry needed for manifest schema; Storage Layer abstraction needs config service).

**Parallelization within phase.** Two streams can run concurrently after foundation work: (a) Manifest building + governance cutover, (b) Storage Layer abstraction + per-native schema migrations + MSR ETL. Lifecycle cleanup (99_ARCHIVE/ moves) gates on the manifest being live (the manifest determines what's CURRENT vs ARCHIVE).

**Acceptance criteria.**
- `CAPABILITY_MANIFEST.json` published with all canonical assets registered correctly. Frontmatter discipline holds: every canonical file has `version`, `status`, `layer`, `expose_to_chat`, `native_id`, plus optional fields where applicable.
- Manifest passes parity check against prior FILE_REGISTRY + CANONICAL_ARTIFACTS contents — every asset previously listed is in the manifest with correct fields.
- 99_ARCHIVE/ contains every predecessor file >2 generations behind. No orphaned predecessors in original locations.
- Governance tooling (drift_detector, schema_validator, mirror_enforcer) passes against the manifest with no regressions versus the prior registry-based runs.
- FILE_REGISTRY + CANONICAL_ARTIFACTS show `SUPERSEDED` status; no live tooling reads from them.
- MSR signals queryable via SQL: test query `SELECT * FROM msr_signals WHERE domain='financial' AND confidence > 0.7 LIMIT 10` returns expected results.
- Per-native schema columns present and populated; queries filtered by `native_id='abhisek'` return only that native's data.
- Storage Layer abstraction usable from Python sidecar (existing code refactored to use it for at least one read path).

**Rollback path.** This is the phase with the highest rollback complexity per Q2's aggressive cutover decision. Rollback procedure:
1. Restore FILE_REGISTRY_v1_11.md and CANONICAL_ARTIFACTS_v1_0.md frontmatter `status` to CURRENT.
2. Revert governance tooling to read from the old registries (revert specific commits).
3. Move predecessors back from 99_ARCHIVE/ if archival caused issues.
4. CAPABILITY_MANIFEST.json stays on disk but is unused; manifest_overrides.yaml stays.
5. DB schema additions stay (they're additive; not regressing); `native_id` columns default to 'abhisek' which works for current single-native deployment.
6. MSR ETL output stays (additive; the table just isn't read yet).

Rollback returns the project to a working pre-Phase-1 state with some additive infrastructure in place (DB columns, ETL output) that's harmless until activated.

**Test strategy.** Manifest schema validation tests. Drift parity tests (manifest vs. old registries — must match). Lifecycle policy tests (verify N=2 generations rule applies correctly). MSR ETL idempotency test (running ETL twice produces same result). Storage Layer abstraction unit tests per backend. Per-native query isolation test (queries filtered by `native_id='abhisek'` return only that native's records). Governance tooling parity tests (drift_detector pre vs. post-cutover should produce identical output for the same corpus state).

**Estimated Claude Code sessions.** 4-5 sessions. Highest-effort phase due to migration scope.

**Open implementation questions for execution-time review.**
- Should the manifest also include explicit `mirror_pairs` section to fully replace CANONICAL_ARTIFACTS' §2 mirror-pair inventory, or are mirror pairs better tracked separately?
- For per-native namespacing, should `native_id` be a full UUID or a human-readable string slug (e.g., 'abhisek')? Recommendation: human-readable for now; UUID later.
- MSR's `falsifier` field is currently embedded prose; should the ETL parse it into structured falsifier records or keep as text?

## §6 — Phase 2: Query Pipeline Basic (D2) — with Cross-Native Class

**Goal.** Build the Router and basic Bundle Composer (rule-only, no Augmenter yet). Build the basic Retrieval Tool Suite (MSR-SQL, Pattern-Register, Resonance/Cluster/Contradiction Registers, Temporal — no Graph Walk yet, no vector search yet, no Reranker yet). Build the Tool-Call Cache. Per Q3 resolved: include cross-native query class in router classification rules from start, with a placeholder `query_msr_aggregate` tool (returns "multi-native not yet deployed" gracefully).

**Components touched (architecture §4.2).** C2.1 Router (Stage 2). C2.2a Rule Composer (no C2.2b Augmenter yet — that's Phase 6). C2.3 Retrieval Tool Suite (subset). C2.5 Tool-Call Cache.

**Deliverables.**
- `platform/src/lib/router/` — Router service implementation.
  - `router.ts` with `classify(query, context) → QueryPlan` interface.
  - Default model: Claude Haiku 4.5 (configurable via C6.3).
  - Eight query classes encoded: factual, interpretive, predictive, cross_domain, discovery, holistic, remedial, **cross_native** (Q3).
  - Router prompt template registered in C3.4 Synthesis Prompt Registry (initial registration).
- `platform/src/lib/bundle/` — Bundle Composer (Rule Composer only).
  - `rule_composer.ts` with `compose(QueryPlan, Manifest) → Bundle` interface.
  - Implements bundle composition rules per architecture §9: floor (FORENSIC + CGM ≈ 40K) + conditional adds based on class.
  - Cross-native bundle composition rule encoded: when `query_class === 'cross_native'`, the bundle is a *meta-bundle* containing aggregate-query placeholders rather than per-native context (since multi-native isn't deployed yet).
- `platform/src/lib/retrieve/` — Retrieval tool implementations for the basic tools:
  - `msr_sql.ts` — `query_msr(filter)` against the `msr_signals` PostgreSQL table populated in Phase 1. Returns 60-100 candidate signals.
  - `pattern_register.ts` — `query_pattern_register(filter)` against the L3.5 PATTERN register.
  - `resonance_register.ts`, `cluster_atlas.ts`, `contradiction_register.ts` — same pattern for the other L3.5 registers.
  - `temporal.ts` — `query_temporal(date_range, type)` calling the existing Python sidecar endpoints for current dasha + transit lookups.
  - `query_msr_aggregate.ts` — placeholder for cross-native aggregate queries; returns `{ status: 'multi_native_not_deployed', message: 'Cross-native queries require multi-native deployment.' }`.
- Each tool implements the uniform `retrieve(QueryPlan) → ToolBundle` interface per architecture §15.
- Tools registered in the Capability Manifest's tool inventory.
- `platform/src/lib/cache/tool_cache.ts` — Request-scoped Tool-Call Cache.
  - `Map<string, Promise<ToolResult>>` keyed on `(tool_name, hash(normalized_params))`.
  - Cleared at request boundary.
  - Audit trail records `served_from_cache: bool` per call.

**Dependencies.** Phase 1 complete (need manifest + storage layer + MSR table populated).

**Parallelization within phase.** High parallelism. Router can be built in one stream; each Retrieval tool can be built in its own stream (six tool streams); Tool Cache can be built in another stream; Rule Composer can be built in another. Up to ten parallel Claude Code sub-streams in principle; practically ~3-4 in parallel works well.

**Acceptance criteria.**
- Router classifies test queries correctly across all 8 classes. Test set: at least 5 queries per class, hand-labeled by native, classifier accuracy ≥80% on the test set.
- Cross-native query class triggers correctly when a query has cross-native intent (test queries: "what patterns are common across charts with my Saturn placement?", "compare my chart to others", etc.).
- Bundle Composer applies rules per architecture §9 correctly. Test: feed a `QueryPlan` with `query_class: 'interpretive'`; verify bundle contains floor + UCN + CDLM + RM, total ~120K tokens.
- MSR-SQL filter returns expected signals. Test query: `domain='financial', confidence ≥ 0.6, significance ≥ 0.6`; expected return: 30-60 candidates from MSR's 499 signals.
- Each L3.5 register tool returns expected records.
- Temporal tool returns current dasha + upcoming windows for a test date.
- `query_msr_aggregate` placeholder returns its standardized "not deployed" response without error.
- Tool Cache demonstrably prevents duplicate execution: integration test with two concurrent identical calls verifies one execution, two cached returns.

**Rollback path.** Feature flag `NEW_QUERY_PIPELINE_ENABLED` (initially false). When false, the existing Consume tab uses its current static-path logic. When true, requests route through the new Router → Bundle Composer → Retrieval pipeline. Rollback = flip flag to false. New code stays on disk but isn't exercised.

**Test strategy.** Per-class router classification tests (8 classes × 5 test queries each = 40 tests). Bundle composition unit tests (one per composition rule). Per-tool retrieval tests (mocked DB + real DB integration variants). Tool Cache deduplication concurrency test. Cross-native placeholder tool test (verifies graceful degradation). Latency benchmarks per tool (validate against architecture §5 latency estimates: MSR-SQL ~150ms, Pattern Register ~30ms, Temporal ~80ms).

**Estimated Claude Code sessions.** 4-5 sessions.

**Open implementation questions for execution-time review.**
- Should the Router's classification prompt include few-shot examples per class, or rely on the model's general reasoning? (Few-shot probably better for rare classes like cross_native.)
- For cross-native query class detection, what linguistic signals are most reliable? (Plurals, comparison phrases, "across" / "common" / "compared")
- Tool Cache TTL — is request-scope sufficient, or do we want some cross-request caching for stable tools? Recommendation: request-scope for v0; revisit at Phase 9.

## §7 — Phase 3: Synthesis Single-Model (D3)

**Goal.** Wire the new pipeline end-to-end for single-model synthesis. Build structural Validator Service. Build Synthesis Orchestrator with Single-Model Strategy. Build Synthesis Prompt Registry. Build Disclosure Tier Filter (super_admin tier active; client + public_redacted as stubs). Replace the existing Consume route's logic with the new pipeline.

**Components touched (architecture §4.3).** C3.1 Validator Service. C3.2 Synthesis Orchestrator (Single-Model Strategy only — Panel Strategy is Phase 7). C3.4 Synthesis Prompt Registry. C3.5 Disclosure Tier Filter. C3.6 Streaming Handler.

**Deliverables.**
- `platform/src/lib/validators/` — Validator Service.
  - `p1_layer_separation.ts` — checks no L1 facts smuggled into L2+ claims.
  - `p2_citation.ts` — checks every L2+ claim's `v6_ids_consumed` field resolves against canonical L1 IDs.
  - `p5_signal_id_resolution.ts` — checks every signal_id mentioned in synthesis resolves against the MSR.
  - `validator_registry.ts` — plug-in registry; `register(validator)`, `runAll(artifact, set)`.
- `platform/src/lib/synthesis/` — Synthesis Orchestrator.
  - `single_model_strategy.ts` — invokes selected model with bundle + tools + system prompt + history; streams response; logs synthesis prompt version.
  - `synthesis_orchestrator.ts` — `synthesize(bundle, mode, model_selection) → stream`; branches on mode (panel-mode branch is a no-op stub until Phase 7).
- `platform/src/lib/prompts/` — Synthesis Prompt Registry.
  - Versioned prompt templates per query class. Initial templates hand-authored.
  - `acharya` / `brief` / `client` style suffixes.
  - `register(template)`, `get(class, tier, strategy) → PromptTemplate`.
- `platform/src/lib/disclosure/` — Disclosure Tier Filter.
  - super_admin tier: pass-through (full content).
  - acharya_reviewer tier: pass-through with methodology disclosure addendum.
  - client tier: stub returning unfiltered content with TODO marker (M6 will implement redaction).
  - public_redacted tier: stub (M10 will implement aggregation).
- `platform/src/app/api/chat/consume/route.ts` refactored: orchestrate the new pipeline (Stage 1 RECEIVE → Stage 2 CLASSIFY → Stage 3+4 DISCOVER+RESOLVE → Stage 5 RETRIEVE → Stage 6 VALIDATE → Stage 7 SYNTHESIZE → stream). Behind `NEW_QUERY_PIPELINE_ENABLED` flag.
- Streaming Handler integration (using existing Vercel `ai` SDK).

**Dependencies.** Phase 2 complete.

**Parallelization within phase.** Validators stream parallel with Synthesis Orchestrator stream parallel with Disclosure Filter stream parallel with Prompt Registry stream. Refactor of `route.ts` is sequential at the end (integrates everything).

**Acceptance criteria.**
- End-to-end query flow works: user types query → Composer sends to Chat API → Router classifies → Bundle Composer composes → Retrieval Tools execute → Validators validate → Synthesizer streams → user sees response.
- Single-model behavior matches existing single-model behavior for a regression suite of test queries (output may differ in specifics due to different bundle composition, but it's still acharya-grade and on-topic).
- Validators pass on well-formed responses; produce `fail` votes on deliberately-broken test cases (e.g., a synthesis output with smuggled L1 facts in L2+ claims fails P1).
- Disclosure filter pass-through works for super_admin tier; stubs return appropriate placeholder responses for other tiers.
- Synthesis prompt version logged correctly into audit-trail-preparing infrastructure (full audit trail comes in Phase 4).

**Rollback path.** Feature flag `NEW_QUERY_PIPELINE_ENABLED` switched off; old static-path Consume logic resumes.

**Test strategy.** End-to-end integration tests (full pipeline against test queries). Validator unit tests (positive + negative cases per validator). Single-model regression suite (existing queries should still produce reasonable answers). Disclosure filter unit tests (per tier). Latency benchmarks (full pipeline ≤ existing single-model latency + 500ms).

**Estimated Claude Code sessions.** 3-4 sessions.

**Open implementation questions for execution-time review.**
- Where does the L2.5 routing instruction in the existing system prompt go? Recommendation: encoded as a default in the prompt registry's interpretive-class template; the bundle composer ensures L2.5 is in the bundle, so the instruction becomes redundant but safe to keep as a backup.
- Should the validator failures halt synthesis or annotate it? Recommendation: structural-fail halts; warn annotates. Per-validator severity configurable in C6.3.

## §8 — Phase 4: Audit and Persistence (D4)

**Goal.** Capture comprehensive audit trail per query. Build outcome-blind Prediction Ledger with pre-stream-write discipline. Scaffold the Calibration Loop component (full implementation at Phase 10 / M5).

**Components touched (architecture §4.4).** C4.1 Audit Trail Service. C4.2 Prediction Ledger. C4.3 Calibration Loop (scaffold only).

**Deliverables.**
- DB schema migrations:
  - `audit_log` table: `event_id UUID PRIMARY KEY`, `timestamp TIMESTAMPTZ`, `conversation_id UUID`, `message_id UUID`, `user_id VARCHAR`, `audience_tier VARCHAR`, `query_plan JSONB`, `manifest_fingerprint VARCHAR(64)`, `bundle_id UUID`, `bundle_hash VARCHAR(64)`, `retrieval_transcripts JSONB`, `validator_votes JSONB`, `synthesis_prompt_version VARCHAR`, `llm_calls JSONB`, `panel_metadata JSONB NULL`, `semantic_gate_result VARCHAR NULL`, `semantic_gate_reason TEXT NULL`, `response_text TEXT`, `total_cost_usd DECIMAL`, `total_latency_ms INTEGER`, `schema_version VARCHAR`, `native_id VARCHAR`. Indices on `(native_id, conversation_id, timestamp)`.
  - `prediction_ledger` table: `prediction_id UUID PRIMARY KEY`, `created_at TIMESTAMPTZ`, `conversation_id UUID`, `message_id UUID`, `panel_turn_id UUID NULL`, `source_type VARCHAR ('panel_member' | 'adjudicator' | 'single_model')`, `source_model_id VARCHAR`, `claim_text TEXT`, `confidence DECIMAL`, `horizon_text TEXT`, `falsifier_text TEXT`, `validated_bundle_hash VARCHAR(64)`, `outcome_resolution VARCHAR NULL ('pending' | 'confirmed' | 'falsified' | 'unresolvable')`, `outcome_resolution_at TIMESTAMPTZ NULL`, `outcome_evidence TEXT NULL`, `native_id VARCHAR`. Indices on `(native_id, outcome_resolution, created_at)`.
- `platform/src/lib/audit/` — Audit Trail Service.
  - `audit_writer.ts` with `write(event)` interface; appends to DB.
  - `audit_reader.ts` with `query(filter)` interface; returns structured records.
  - Audit event capture wired across Stages 2-8 (router output, bundle composition, retrieval transcripts, validator votes, synthesis output, semantic gate result).
- `platform/src/lib/predictions/` — Prediction Ledger.
  - `prediction_logger.ts` with `log(prediction)` interface; pre-stream-write enforcement (writes happen before streaming begins for predictive-class queries).
  - `prediction_query.ts` with `query_unresolved()`, `resolve(prediction_id, outcome)` interfaces.
  - Predictive-claim extraction logic: parses synthesis output, identifies time-indexed claims, logs each as a prediction.
- `platform/src/lib/calibration/` — Calibration Loop scaffold.
  - Module skeleton with no active logic.
  - Stub `consume_audit_events()` and `emit_signal()` interfaces for Phase 10 to implement.
- Audit hooks integrated throughout the pipeline (Stages 2, 3+4, 5, 6, 7, 8).

**Dependencies.** Phase 3 complete (need synthesis to have something to audit).

**Parallelization within phase.** Audit Trail and Prediction Ledger are mostly independent and parallelize cleanly. Schema migrations sequential at start; service implementations parallel; integration sequential at end. Phase 4 itself can run **parallel with Phase 5** (Interface basic) since they touch different domains.

**Acceptance criteria.**
- Every Consume request produces a complete audit-trail event with all expected fields populated.
- Audit query interface returns structured records: `audit_reader.query({ conversation_id })` returns events for that conversation.
- For predictive-class test queries, prediction-ledger entries are written *before* response streaming begins (verifiable by checking row count timing vs. stream first-byte timing).
- For non-predictive test queries, no prediction-ledger entries are written.
- Schema migrations forward and rollback cleanly. Migration test: apply, verify, rollback, verify state matches pre-migration.
- Calibration Loop scaffold compiles and exposes its interfaces (no behavior yet).

**Rollback path.** Audit hooks behind a feature flag `AUDIT_ENABLED` (default on after Phase 4). Schema additions are additive; rollback drops the new tables (or leaves them dormant). Pipeline behavior continues unchanged if hooks are disabled.

**Test strategy.** Audit completeness test (verify every field populated for representative queries). Pre-stream-write timing test (instrument the streaming handler to confirm ledger writes occurred before stream start). Schema migration test (forward + rollback). Audit query interface test. Predictive-claim extraction unit tests (verify regex / classifier correctly identifies time-indexed claims).

**Estimated Claude Code sessions.** 2-3 sessions.

**Open implementation questions for execution-time review.**
- Predictive-claim extraction: regex-based, LLM-based, or hybrid? Recommendation: hybrid — regex for obvious patterns ("by 2027", "within 6 months"), small LLM for nuanced ("a career shift is likely in the coming Saturn period").
- Should the audit_log table partition by `native_id` from start, or use simple indices? Recommendation: indices for now; partition when volume warrants.

## §9 — Phase 5: Interface Basic (D5)

**Goal.** Refactor the Composer for the new pipeline. Build User Settings persistence. Add Progress UX three-state indicator. The Composer's panel checkbox is NOT in this phase (Phase 7); the Audit View is NOT in this phase (Phase 8); placeholder UI elements may appear but are gated by feature flags.

**Components touched (architecture §4.5).** C5.1 Chat API (refactored over D2+D3). C5.2 Composer (extends existing). C5.3 Conversation Renderer (extends existing). C5.5 User Settings. C5.6 Progress UX.

**Deliverables.**
- `platform/src/app/api/chat/consume/route.ts` refactor (continued from Phase 3) — thin orchestration layer over the pipeline.
- `platform/src/components/consume/Composer.tsx` extended:
  - Existing model picker, style picker preserved.
  - Hidden placeholder for panel checkbox (Phase 7 will activate).
  - User settings reading (model + style preferences).
- `platform/src/components/consume/ConversationRenderer.tsx` extended:
  - Streaming display preserved.
  - Hidden placeholder for Audit View affordance (Phase 8 will activate).
- `platform/src/components/settings/` — User Settings UI.
  - Model preference, style preference (existing — confirm preserved).
  - Placeholder for Phase 7 toggles (`degrade_mode_allowed`, `panel_research_mode`) — initially hidden.
- DB schema: `user_preferences` table or extension — `user_id`, `key VARCHAR`, `value JSONB`. Per architecture §4.5 C5.5.
- `platform/src/hooks/useUserSettings.ts` — typed hook for setting access.
- `platform/src/components/consume/ProgressIndicator.tsx` — three-state component.
  - States: "Classifying..." → "Retrieving..." → "Synthesizing..." → streaming.
  - Subscribes to pipeline-stage events (stage events emitted by the orchestrator).

**Dependencies.** Phase 3 complete.

**Parallelization within phase.** Composer + Conversation Renderer + User Settings + Progress Indicator are all separate UI components; can be built in parallel. Chat API refactor is sequential at the end. Phase 5 itself can run **parallel with Phase 4** (Audit & Persistence).

**Acceptance criteria.**
- User opens Consume tab, picks model + style, types query, gets streaming response — full UX cycle works.
- User Settings persist: select model, refresh page, model is still selected.
- Progress indicator transitions through three states correctly during a query.
- No regression on existing Conversation Renderer behavior.
- Hidden placeholders for Phase 7 + 8 affordances are present in DOM but invisible (verify via `data-testid` attributes for test access).

**Rollback path.** Feature flags per UI component (`PANEL_CHECKBOX_VISIBLE`, `AUDIT_VIEW_VISIBLE`). Disable to revert to the pre-Phase-5 UI. Refactored route.ts behavior governed by `NEW_QUERY_PIPELINE_ENABLED`.

**Test strategy.** End-to-end UI tests (Playwright or equivalent). Settings persistence test. UX regression suite (existing queries should still UX correctly). Progress indicator state-transition test.

**Estimated Claude Code sessions.** 3-4 sessions.

**Open implementation questions for execution-time review.**
- Does the User Settings UI live as a modal, a sidebar, or a separate page? Recommendation: sidebar; minimal disruption.
- Should placeholder UI elements be entirely absent from DOM (cleaner) or hidden via CSS (easier to enable)? Recommendation: hidden via CSS for easier Phase 7 + 8 activation.

## §10 — Phase 6: LLM Checkpoints

**Goal.** Add the three accuracy-priority LLM checkpoints established in the 2026-04-27 brainstorm: Bundle Augmenter (Stage 4.5), MSR Reranker (Stage 5.5), Semantic Discipline Gate (Stage 8.5).

**Components touched (architecture §4.2-§4.3).** C2.2b Bundle Augmenter. C2.4 Reranker (replaces significance-weighted sort default). C3.3 Semantic Discipline Gate.

**Deliverables.**
- `platform/src/lib/bundle/bundle_augmenter.ts` — Stage 4.5 implementation.
  - Inputs: rule-composed bundle + QueryPlan + Manifest.
  - Output: augmented bundle (additions, removals, or unchanged).
  - Default model: Claude Haiku 4.5.
  - Augmenter prompt template registered in C3.4 Synthesis Prompt Registry.
  - Behind feature flag `BUNDLE_AUGMENTER_ENABLED`.
- `platform/src/lib/retrieve/reranker.ts` — Stage 5.5 implementation.
  - Inputs: query + 60-100 candidate signals from Tool A MSR-SQL.
  - Output: top 25 ranked by relevance.
  - Replaces the prior significance-weighted sort.
  - Reranker prompt template registered in C3.4.
  - Behind feature flag `MSR_RERANKER_ENABLED`.
- `platform/src/lib/validators/semantic_gate.ts` — Stage 8.5 implementation.
  - Inputs: synthesis output + query class.
  - Output: `pass | fail` with reason.
  - On fail: triggers one revision pass to the synthesizer.
  - Verifies: three interpretations are meaningfully orthogonal; falsifier is specific (for predictive queries).
  - Behind feature flag `SEMANTIC_GATE_ENABLED`.
- Telemetry per checkpoint: did the checkpoint change the output? (Augmenter: did it add/remove assets? Reranker: did it produce different top-25 vs. significance-weighted sort? Semantic gate: did it trigger a revision?). Metrics feed Phase 10 calibration loop.
- Pipeline integration: insert checkpoints at Stages 4.5, 5.5, 8.5.

**Dependencies.** Phase 3 complete (need pipeline working). Phase 0 complete (need C6.3 feature flags + C6.4 telemetry).

**Parallelization within phase.** Three checkpoints are independent; can be built in parallel. Three Claude Code sessions in parallel, each owning one checkpoint.

**Acceptance criteria.**
- All three checkpoints fire for every query when their flags are on.
- Bundle Augmenter: telemetry shows it makes additions on at least 10% of test queries (varies by class).
- MSR Reranker: top-25 differs from significance-weighted sort on at least 30% of test queries (showing it's doing something different).
- Semantic Gate: triggers revision on deliberately-weak synthesis output (test cases with three near-identical interpretations or vague falsifiers); passes well-formed output ≥95% of time.
- Per-checkpoint feature flags work independently.
- No regression on single-model end-to-end behavior when checkpoints are off (verifies flag fallback).

**Rollback path.** Per-checkpoint feature flags off → checkpoints become no-ops → pipeline runs as it did at end of Phase 3.

**Test strategy.** Per-checkpoint unit tests (with mocked LLM responses). Integration tests verifying checkpoints fire at correct stages. A/B-style telemetry comparison: same query with checkpoint on vs. off; verify the audit trail records different paths.

**Estimated Claude Code sessions.** 3 sessions (one per checkpoint).

**Open implementation questions for execution-time review.**
- For the Reranker, start with reranking all 60-100 candidates or only top 50 by significance? Recommendation: top 50 to start; expand to 100 if measured quality requires it.
- Semantic Gate revision logic: how many revision passes maximum before giving up? Recommendation: 1 revision; if still fails, log the failure and stream original output with semantic-gate-failed flag in audit trail.

## §11 — Phase 7: Panel Mode

**Goal.** Build the panel synthesis strategy, with all sub-components, the panel checkbox in the Composer, the user settings toggles for degrade mode and research mode, and the panel-aware progress UX. This phase operationalizes architecture §10.

**Components touched (architecture §4.2-§4.3, §4.5).** C2.6 Bundle Assembler (super-bundle composition). C3.2 Panel Strategy (Panel Resolver, Panel Runner, Anonymizer, Adjudicator integration, Divergence Classifier). C5.2 Composer (panel checkbox). C5.5 User Settings (degrade_mode_allowed, panel_research_mode toggles). C5.6 Progress UX (panel-aware states).

**Deliverables.**
- `platform/src/lib/synthesis/panel/` — Panel Strategy implementation.
  - `panel_resolver.ts` — `resolve(adjudicator_model, slate) → panel_members[]`. Family-level exclusion logic.
  - `panel_runner.ts` — parallel `streamText` invocations with concurrent retry up to N=3 per member, 60s total time budget. Failure handling per architecture §10.2.
  - `anonymizer.ts` — `anonymize(panel_responses[]) → labeled_shuffled[]`. A/B/C labeling, randomized order.
  - `adjudicator.ts` — wraps the Synthesis Orchestrator with adjudicator-specific prompt + super-bundle.
  - `divergence_classifier.ts` — separate small-LLM call extracting and classifying divergences using the five-class taxonomy (including new `DIS.class.extension`).
- `platform/src/lib/bundle/bundle_assembler.ts` — Super-bundle composer (C2.6).
  - `assemble(baseline_bundle, panel_member_extensions[]) → super_bundle`.
  - Deduplicates by content hash.
- DB schema migration: `panel_metadata JSONB` column on `messages` table — already added in Phase 1.
- `platform/src/components/consume/Composer.tsx` extended:
  - Activate panel checkbox (was hidden placeholder in Phase 5).
  - Auto-reset to unchecked after `sendMessage` resolves.
  - Tooltip explaining panel mode.
- `platform/src/components/settings/UserSettings.tsx` extended:
  - Activate `degrade_mode_allowed` toggle.
  - Activate `panel_research_mode` toggle.
  - Persist via Phase 5 user-settings infrastructure.
- `platform/src/components/consume/ProgressIndicator.tsx` extended:
  - Panel-aware states: "Classifying..." → "Retrieving..." → "Running panel..." → "Adjudicator synthesizing..." → streaming.
- `platform/src/lib/synthesis/synthesis_orchestrator.ts` updated: panel-mode branch now calls Panel Strategy instead of being a no-op stub.
- Audit trail integration: `panel_metadata` populated and persisted per architecture §10.2 schema.
- Prediction ledger integration: predictive-class panel queries write 4× ledger entries (3 panel + 1 adjudicator) before streaming.
- Failure handling: hard-halt explicit error message; degrade mode (when opted in) produces 2-of-3 synthesis with `degrade_mode_triggered: true` flag.

**Dependencies.** Phase 3 complete (single-model strategy exists). Phase 4 complete (audit + ledger). Phase 5 complete (UI baseline + settings infrastructure). Phase 6 complete (LLM checkpoint patterns established).

**Parallelization within phase.** Panel sub-components (resolver, runner, anonymizer, adjudicator, classifier) are mostly independent and can be built in parallel. UI changes parallel with backend. ~5 parallel sub-streams. Phase 7 itself can run **parallel with Phase 9** (advanced retrieval) — different surfaces.

**Acceptance criteria.**
- User checks panel box, sends query, panel mode triggers: 3 panel members invoked in parallel, adjudicator synthesizes, divergence classifier extracts divergences, response streams.
- Family-level adjudicator exclusion works for all 4 lab choices: select Claude → panel = GPT+Gemini+DeepSeek; select Gemini → panel = Claude+GPT+DeepSeek; etc.
- Concurrent retry recovers from injected provider failures: deliberately fail one panel member's first call; verify retry fires and succeeds.
- Hard halt (default) on exhausted retries: deliberately fail a panel member 4 times; verify user-facing error message.
- Degrade mode (opt-in): with `degrade_mode_allowed: true`, exhausted retries proceed with 2-of-3 synthesis; `degrade_mode_triggered: true` flagged in audit trail.
- Research mode (opt-in): with `panel_research_mode: true`, panel members receive only system prompt + current user query (no history); audit trail records `history_mode: 'research'`.
- `panel_metadata` persisted correctly per architecture Appendix A schema.
- Predictive panel queries: 4× prediction-ledger entries written pre-stream.
- Tool Cache demonstrably prevents duplicate execution within a panel turn.
- Single-model behavior unchanged when panel checkbox unchecked.

**Rollback path.** Feature flag `PANEL_MODE_ENABLED` off → panel checkbox hidden, panel-mode requests rejected at server; pipeline runs as it did at end of Phase 6.

**Test strategy.** Per-component unit tests for each panel sub-component. End-to-end panel turn integration tests. Failure-handling tests (provider failures, classifier failures, validator failures on panel responses). Family-exclusion logic tests. Degrade-mode integration test. Research-mode integration test. Latency benchmarks (panel turn ≤ 30s on healthy providers).

**Estimated Claude Code sessions.** 5-6 sessions. Highest-effort phase due to scope.

**Open implementation questions for execution-time review.**
- Should the Adjudicator see anonymized retrieval transcripts or model-identified ones? Recommendation: anonymized — the transcripts shouldn't leak which model made which retrieval decision. This requires the anonymization to extend to transcripts not just responses.
- Conversation history for panel members in synthesized history mode (default): does the panel member see the *exact* prior synthesis text, or a summary? Recommendation: exact text — that's what the user sees too; matches the conversation contract.

## §12 — Phase 8: Audit View UI

**Goal.** Surface the comprehensive audit data captured since Phase 4 via the Inspect affordance per assistant message. Single-model audit view + panel-mode audit view. Tier-conditional content rendering.

**Components touched (architecture §4.5).** C5.4 Audit View.

**Deliverables.**
- `platform/src/components/audit/` — Audit View UI components.
  - `AuditViewToggle.tsx` — the Inspect affordance icon on every assistant message.
  - `AuditViewPanel.tsx` — the expandable panel shown on click.
  - `SingleModelAuditRenderer.tsx` — renders single-model audit data: capability snapshot, retrieval bundle summary, validator votes, tool-call transcript, token/latency/cost, semantic-gate result.
  - `PanelModeAuditRenderer.tsx` — renders panel-mode audit data: all of the above for the adjudicator + per-panel-member sub-panels (response text, tool transcript, validator votes, extracted predictions) + divergence list with `DIS.class.*` classifications + anonymization key.
  - `DivergenceListRenderer.tsx` — renders divergences with class color-coding.
  - `ToolTranscriptRenderer.tsx` — renders tool calls with their parameters and result hashes.
- Tier-conditional rendering: `super_admin` tier sees raw content; `acharya_reviewer` tier sees raw + methodology disclosure; `client` tier sees tier-filtered (M6); `public_redacted` tier sees tier-filtered (M10). Today only super_admin tier active; other tier renderers are stubs.
- Audit data fetch: when user clicks Inspect, frontend queries `audit_reader.query({ message_id })` via Chat API → returns audit event → rendered.
- Affordance visibility: `AUDIT_VIEW_VISIBLE` feature flag activates the Inspect button (Phase 5 had it as hidden placeholder).

**Dependencies.** Phase 4 complete (audit trail data exists). Phase 7 complete (panel data exists for panel-mode rendering). Phase 5 complete (UI baseline).

**Parallelization within phase.** Renderer components can be built in parallel (single-model renderer, panel-mode renderer, sub-renderers). UI integration sequential at end. ~3-4 parallel sub-streams.

**Acceptance criteria.**
- Every assistant message has an Inspect button (visible).
- Clicking Inspect opens the audit view panel with correct content.
- Single-model messages show single-model audit content.
- Panel-mode messages show panel-mode audit content with all per-member data + divergences.
- Tier filtering works: super_admin sees raw content; tier-stub renderers (when user is on a future tier) return tier-appropriate placeholder.
- Audit fetch latency ≤ 500ms for typical events.
- Drill-down navigation: clicking a citation navigates to the source asset (when implemented; this might be deferred to a later UI iteration).

**Rollback path.** Feature flag `AUDIT_VIEW_VISIBLE` off → Inspect button hidden; backend audit data continues to be captured (just not surfaced in UI).

**Test strategy.** UI rendering tests for both modes. Tier filter tests. Audit fetch performance test. Accessibility test (keyboard navigation, screen reader compatibility).

**Estimated Claude Code sessions.** 3-4 sessions.

**Open implementation questions for execution-time review.**
- Should the audit view be a modal overlay, a slide-in sidebar, or an expandable inline section? Recommendation: expandable inline (consistent with conversation flow; doesn't disrupt context).
- For panel-mode audit view, should the anonymization key (which model was A, B, C) be revealed by default or behind a "show identities" toggle? Recommendation: hidden by default (preserves the architectural blinding intent for casual viewing), revealed on toggle for power users.

## §13 — Phase 9: Advanced Retrieval

**Goal.** Build out the retrieval surface to its full intended shape: CGM Graph Walk tool, Manifest-Query meta-tool, Vector Search secondary tool. Advanced tools that complete the C2.3 Retrieval Tool Suite.

**Components touched (architecture §4.2).** C2.3 Retrieval Tool Suite expansion.

**Deliverables.**
- `platform/src/lib/retrieve/cgm_graph_walk.ts` — CGM Graph Walk tool.
  - BFS over CGM nodes by edge type filters (`SUPPORTS`, `CONTRADICTS`, `CROSS_LINKS`, etc.).
  - Configurable depth (default 1, max 3).
  - Adaptive seed selection from `QueryPlan.graph_seed_hints`.
  - Returns: connected node IDs + edges traversed.
- `platform/src/lib/retrieve/manifest_query.ts` — Manifest-Query meta-tool.
  - `query_manifest(question_text)` allowing the synthesizer LLM to introspect the catalog.
  - Returns relevant asset entries from the manifest matching the question.
  - Uses small-LLM lookup (or simple keyword search) over the manifest.
- `platform/src/lib/retrieve/vector_search.ts` — Vector Search secondary tool.
  - Voyage-3-large 1024-d embeddings (already populated in Phase 1's RAG tables).
  - pgvector HNSW index queried.
  - Returns: top-K semantically similar passages.
  - Marked as secondary in tool registry — used only when other tools have nothing to match.
- All three tools registered in the Capability Manifest's tool inventory.
- `Vector-Search` and `Graph-Walk` tools added to the Router's tool authorization rules per query class.

**Dependencies.** Phase 1 complete (RAG tables, graph data, embeddings populated). Phase 2 complete (basic retrieval suite established).

**Parallelization within phase.** Three tools are independent; can be built in parallel. Phase 9 itself can run **parallel with Phase 6, 7, 8** — different surfaces.

**Acceptance criteria.**
- CGM Graph Walk returns connected signals from CGM seed nodes for test queries. Test: seed = financial node + career node, depth=1, edge_types=[CROSS_LINKS, SUPPORTS]; verify returned nodes are graph-connected.
- Manifest-Query lets the synthesizer ask "what's available about X" and get relevant assets back. Test: synthesizer-style call with question "Saturn data" returns FORENSIC, MSR (Saturn-related signals), patterns mentioning Saturn, etc.
- Vector Search returns semantically-similar passages. Test: query "wealth and material success" returns chunks mentioning prosperity, abundance, financial gain (even when the literal words don't match).
- All three tools registered in manifest with correct `interface_version`.
- Latency benchmarks: graph walk ≤ 200ms (depth 1), manifest query ≤ 100ms, vector search ≤ 300ms.

**Rollback path.** Per-tool feature flags. Disabled tools simply aren't called by the Router; pipeline degrades gracefully to the basic tool set.

**Test strategy.** Per-tool retrieval tests (real DB integration). Synthesizer-using-tool integration tests (verifying the synthesis output uses tool results correctly). Graph walk correctness test (verify BFS produces expected output for known graph topology). Vector search relevance benchmarks.

**Estimated Claude Code sessions.** 3 sessions.

**Open implementation questions for execution-time review.**
- For the CGM Graph Walk, should depth be QueryPlan-driven (router specifies) or tool-call-driven (synthesizer specifies)? Recommendation: hybrid — router suggests default depth via `QueryPlan.graph_traversal_depth`; synthesizer can override via tool parameter.
- For Vector Search, what's the right top-K default? Recommendation: 10 — small enough to not pollute synthesis context; large enough to surface relevant alternatives the structured tools miss.

## §14 — Phase 10: Calibration Loop Substrate (M5)

**Goal.** Activate the M5 Learning Layer's runtime feedback. Calibration Loop reads from Audit Trail + Prediction Ledger over project history; emits per-component signals back into D2 and D3; provides outcome resolution UI for native to mark prediction outcomes.

**Components touched (architecture §4.4).** C4.3 Calibration Loop full activation.

**Deliverables.**
- `platform/src/lib/calibration/` Calibration Loop full implementation:
  - `audit_consumer.ts` reads audit_log events on schedule.
  - `ledger_consumer.ts` reads prediction_ledger events.
  - `signal_emitter.ts` publishes per-component signals: improved bundle-composition rules, reranker threshold tuning, prompt-version updates, per-model reliability scores per query class.
  - `metric_dashboard.ts` renders calibration metrics (resolution rate, per-model accuracy, divergence-class frequency, etc.).
- `platform/src/components/calibration/OutcomeResolutionUI.tsx` — UI for native to mark prediction outcomes.
  - Lists unresolved predictions (sorted by horizon-elapsed).
  - Native marks each as `confirmed | falsified | unresolvable` with optional evidence text.
  - Updates `prediction_ledger.outcome_resolution`.
- Calibration scheduler: cron-style or event-driven — runs Calibration Loop daily/weekly.
- Per-component telemetry consumers: each component listens for relevant signals (e.g., Bundle Composer listens for new rules; Reranker listens for threshold updates; Prompt Registry listens for prompt-version updates).

**Dependencies.** Phase 4 complete (audit + ledger data exists). Ideally several months of data before activation provides meaningful signal.

**Parallelization within phase.** Limited; this is single-purpose with sequential dependencies between consumer → emitter → consumer-of-signals.

**Acceptance criteria.**
- Calibration Loop runs on schedule, processes audit + ledger.
- Outcome resolution UI lets native mark at least one prediction outcome.
- At least one component receives a signal that changes its behavior (e.g., reranker threshold updated based on observed quality).
- Calibration metrics dashboard displays at least: resolution rate over time, per-model accuracy distribution, divergence-class frequency.

**Rollback path.** Disable Calibration Loop scheduler → no signals emitted → components run with their static configurations.

**Test strategy.** End-to-end calibration loop test (synthetic audit + ledger data, verify signals are emitted correctly). Outcome resolution UI test. Schedule reliability test. Signal application test (verify components correctly apply signals).

**Estimated Claude Code sessions.** 4-5 sessions. Substantial; spans multiple weeks of test data accumulation in practice.

**Open implementation questions for execution-time review.**
- Calibration Loop schedule: daily, weekly, on-demand? Recommendation: weekly default; daily as data volume grows; on-demand always available.
- Should signals automatically update components, or require native approval? Recommendation: autonomous for low-impact (reranker threshold), native-approval-required for high-impact (rule changes, new prompts).

## §15 — Cross-Phase Concerns: Dependency Graph and Parallelization

**Sequential dependencies (must complete before).**
- Phase 0 → Phase 1 (foundation before data plane)
- Phase 1 → Phase 2 (data plane before query pipeline)
- Phase 2 → Phase 3 (query pipeline before synthesis)
- Phase 3 → Phase 4 (synthesis to audit; audit needs synthesis output)
- Phase 3 → Phase 5 (synthesis to interface; interface needs working pipeline)
- Phase 3 → Phase 6 (synthesis to checkpoints; checkpoints extend synthesis)
- Phase 6 → Phase 7 (checkpoints to panel; panel uses checkpoint patterns)
- Phase 4 + Phase 7 → Phase 8 (audit view needs both audit data and panel data)
- Phase 1 + Phase 2 → Phase 9 (advanced retrieval needs data plane and tool suite established)
- Phase 4 → Phase 10 (calibration needs audit + ledger data)

**Parallelization opportunities.**
- Phase 4 + Phase 5 in parallel (after Phase 3) — different domains.
- Phase 6 + Phase 9 partially parallel (both extend the pipeline, but different components).
- Phase 7 + Phase 9 in parallel (different surfaces — synthesis vs. retrieval).
- Phase 8 sequential at end of UI work (depends on Phase 7's data).

**Critical path:** 0 → 1 → 2 → 3 → 6 → 7 → 8 → 10. Approximately 8 phases on the critical path; ~25 sessions estimated end-to-end critical path. With Phases 4, 5, 9 running in parallel where possible, total wall-clock is shortened.

**Native confirmed parallel Claude Code streams permitted (2026-04-27).** When parallelism is exercised, two Claude Code sessions can work concurrently on disjoint phase scopes. The execution-brief authoring (Artifact 3) explicitly identifies which phases share execution time slots when parallel runs are intended.

## §16 — Cross-Phase Concerns: Rollback Strategy

Every phase has a documented rollback path in its individual section. Three universal rollback principles apply across phases:

**Universal feature flagging.** Every new behavior is feature-flag-gated by default. Flipping a flag rolls back the behavior without code changes. Flags persist as configuration; their state is recoverable across deployments.

**Additive-only schema migrations.** No phase removes or modifies existing schema in ways that lose data. New columns, tables, indices are additive. Rollback (if needed) drops the additions; existing data is unaffected.

**Branch-based code rollback.** Each phase's code lives on a feature branch merged at acceptance. If a critical issue is discovered post-merge, the merge can be reverted (git revert) without affecting prior phases' work.

**Phase 1 has the highest rollback complexity** due to the aggressive manifest migration (Q2 resolved). Its rollback procedure is documented in detail in §5; key points: predecessor registry files retained in place with `SUPERSEDED` status (easy to flip back); governance tooling reverts via git; DB schema additions remain (additive, harmless).

## §17 — Cross-Phase Concerns: Test Strategy

Each phase has a test strategy in its individual section. The cross-phase strategy adds:

**Regression suite.** A growing test set of representative queries that exercise the full pipeline. Each phase adds tests; subsequent phases must pass the accumulated suite. By Phase 7, the regression suite covers single-model, panel-mode, all 8 query classes, all 4 audience tiers (where active), all 4 LLM providers.

**Latency budgets.** Per-phase latency targets accumulate. Phase 0 baseline ≤ existing single-model latency. Phase 3 target: ≤ baseline + 500ms (new pipeline overhead). Phase 6 target: ≤ baseline + 800ms (LLM checkpoints). Phase 7 target: ≤ baseline + 1500ms for panel mode (parallel work; not 4× the baseline).

**Cost benchmarks.** Per-phase cost targets per query. Single-model cost should not regress at any phase. Panel-mode cost target: ≤ 4× single-model.

**End-to-end smoke tests.** Per phase, a small set of "golden" queries are run end-to-end and the output (response + audit trail) is compared to a canonical expected shape. Catches integration-level regressions.

**Quality benchmarks (post Phase 7).** Once panel mode is live, run a curated set of acharya-grade queries through both single-model and panel-mode; native or designated reviewer scores quality. Track quality over time as calibration loop matures.

## §18 — Cross-Phase Concerns: Per-Phase Execution Brief Cadence

Execution briefs (Artifact 3) are authored per phase. The cadence:

**Brief authoring.** Cowork authors `EXEC_BRIEF_PHASE_N_v1_0.md` ahead of phase execution, after the prior phase reaches `COMPLETE` status. The brief draws against this plan's per-phase specification, expanding into per-task acceptance criteria for Claude Code execution.

**Brief content.** Per architecture §20 and the prior panel-implementation-brief pattern: trigger phrase, mandatory pre-flight reading, hard-constraint protections, sequenced tasks within the phase (often parallelizable), per-task acceptance criteria, halt points (where applicable), rollback verification, completion criteria.

**Brief size.** Each brief should fit in 1-3 Claude Code sessions for that phase. Phases that estimate 4+ sessions may have their brief split into sub-briefs (e.g., `EXEC_BRIEF_PHASE_1A`, `EXEC_BRIEF_PHASE_1B`).

**Status discipline.** Each brief carries `status: AUTHORED → IN_PROGRESS → COMPLETE` like the prior panel implementation brief. Cowork updates status on phase completion; authors next phase's brief.

**Parallel briefs.** When phases run in parallel (per §15), Cowork authors their briefs in advance so multiple Claude Code sessions can begin concurrently.

## §19 — Risks and Mitigations

**Risk 1: Phase 1 manifest migration introduces data inconsistency.** Aggressive migration (Q2) increases risk vs. parallel operation. **Mitigation:** parity validation script (`manifest_validator.py`) confirms manifest matches predecessor registries before flipping their status; rollback path well-documented; feature-flag-gated cutover allows immediate revert.

**Risk 2: Cross-native query class added at Phase 2 stays unused for extended period (until multi-native deployment), creating dead-code maintenance burden.** **Mitigation:** keep cross-native handling minimal and well-tested; placeholder tools graceful; revisit at multi-native deployment with refactor opportunity.

**Risk 3: LLM checkpoints at Phase 6 add latency and cost without measurable accuracy gain on real queries.** **Mitigation:** A/B telemetry per checkpoint; if measured impact is small on real queries, individual checkpoints can be disabled via feature flag; the architecture supports this gracefully.

**Risk 4: Panel mode at Phase 7 fails frequently due to provider unavailability.** **Mitigation:** concurrent retry with N=3 brings effective per-member success to ~99.99% even on degraded providers; opt-in degrade mode lets users trade fidelity for uptime; audit trail preserves degraded-vs-normal distinction for calibration.

**Risk 5: Native review bottleneck at phase boundaries delays execution.** **Mitigation:** phase reviews are small (acceptance criteria are concrete); review can be lightweight when criteria pass; designated reviewers can be enrolled; parallel phases mean a single review bottleneck doesn't block all work.

**Risk 6: Schema drift between architecture document, this plan, and execution briefs.** **Mitigation:** schemas live in C6.2 Schema Registry (a single source of truth); plan and briefs reference schema names not embedded copies; schema versioning surfaces drift.

**Risk 7: Calibration loop (Phase 10) doesn't produce useful signals due to insufficient data.** **Mitigation:** Phase 10 is sequenced last for this reason; data accumulates from Phase 4 onward; calibration metrics dashboard is informative even with small data; full activation can wait for sufficient data without blocking other phases.

## §20 — Adoption and Next Steps

**Step 1 — Native review of this plan.** Read at your pace. Annotate, push back on phasing or estimates if any. The Q1/Q2/Q3 decisions have been folded in (per architecture v1.0 §19); no further decision needed unless you want to revisit.

**Step 2 — Adoption.** Same path as architecture v1.0: ND.2 native directive or PHASE_B amendment. Adoption gates execution.

**Step 3 — Phase 0 Execution Brief authoring.** Once adopted, Cowork authors `EXEC_BRIEF_PHASE_0_v1_0.md` — the first execution brief, scoped to Phase 0 Foundation work. Trigger phrase, pre-flight reading, deliverables, acceptance criteria, sub-stream assignments. Expected length: similar to the prior `PANEL_IMPLEMENTATION_BRIEF_v1_0.md` template (now SUPERSEDED) but scoped to Phase 0.

**Step 4 — Phase 0 execution.** Native hands the brief to Claude Code; execution proceeds. Native reviews phase output; Cowork authors Phase 1 brief.

**Step 5 — Iterative execution through Phase 10.** Each phase: brief authored, executed, reviewed, next brief authored. M2/B.5 governance/discovery thread resumes in parallel with execution per native's pause/resume direction.

The planning effort completes when this plan is approved. From that point, execution is the sole open thread (with M2/B.5 resumption); planning transitions to maintenance mode (small revisions only, per architecture document discipline).

---

*End of MARSYS_JIS_PROJECT_PLAN_v1_0.md (DRAFT, 2026-04-27). Awaits native review and approval. On adoption, status flips to CURRENT and execution-brief authoring begins. Next concrete artifact: EXEC_BRIEF_PHASE_0_v1_0.md.*
