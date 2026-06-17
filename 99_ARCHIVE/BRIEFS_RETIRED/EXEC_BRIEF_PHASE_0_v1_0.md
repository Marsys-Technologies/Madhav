---
artifact: EXEC_BRIEF_PHASE_0_v1_0.md
status: COMPLETE
completed_on: 2026-04-27
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
status_history:
  - timestamp: 2026-04-27
    status: IN_PROGRESS_STREAM_A_B_C
    note: Claude Code (Sonnet 4.6) claimed all three streams simultaneously; executed in parallel via subagents.
  - timestamp: 2026-04-27
    status: COMPLETE
    note: All streams complete. 26 tests pass across 6 test files. 0 TypeScript errors in new code. must_not_touch verified clean (pre-existing M2/B.5 modifications untouched). Stream A used gpt-4.1 (confirmed from @ai-sdk/openai@3.0.53 known model list). Stream B upgraded ajv to v8 for Draft 2020-12 support. Stream C: all feature flags default false.
executor_target: Claude Code (Anti-Gravity / VS Code extension; NOT the CLI)
trigger_phrase: "Read EXEC_BRIEF_PHASE_0_v1_0.md and execute it."
phase_number: 0
phase_name: Foundation (Domain D6)
purpose: Executor brief for Phase 0 of the MARSYS-JIS Project Plan. Builds the foundational cross-cutting abstractions (LLM Provider Abstraction with OpenAI integration, Schema Registry, Configuration Service, Telemetry stubs) that every subsequent phase depends on. Three parallelizable sub-streams.
depends_on:
  - 00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md (APPROVED 2026-04-27 — the architectural source of truth; Phase 0 builds Domain D6 components per §4.6)
  - 00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md (APPROVED 2026-04-27 — Phase 0 specification at §4)
  - CLAUDE.md (project orientation)
parallel_stream_warning: |
  The M2/B.5 governance/discovery/retrieval thread is PAUSED per native direction (2026-04-27)
  until this planning effort completes execution. Recent B.5/B.6 work has produced files in
  platform/python-sidecar/ and 035_DISCOVERY_LAYER/ — these are paused-stream artifacts and
  MUST NOT be touched by Phase 0 work. Phase 0 is purely additive in the platform/src/lib/
  area and does not require any modification to the paused stream's surfaces.
chosen_path: Aggressive (Q1/Q2/Q3 resolved per native 2026-04-27). Phase 0 itself is risk-free
  (purely additive); the aggressive choices materialize at Phase 1 + Phase 2.
---

# EXECUTION BRIEF — Phase 0: Foundation (Domain D6)

## §0 — Trigger and Execution Model

Native triggers this brief by saying to a Claude Code session: **"Read EXEC_BRIEF_PHASE_0_v1_0.md and execute it."**

On trigger, Claude Code MUST:
1. Read this entire brief end-to-end before any other action.
2. Read the mandatory pre-flight artifacts in §2 in the order specified.
3. Read the relevant codebase files in §2 to understand current state.
4. Acknowledge readiness and propose the sub-stream sequence the session will execute (one of A/B/C in series, or parallel coordination if multiple sessions are active).
5. Execute the chosen sub-stream(s) per the specifications in §5/§6/§7.
6. On completion of all assigned sub-streams: run integration verification per §8; flip this brief's `status` to `COMPLETE`; notify native.

**Status transitions.** AUTHORED (initial) → IN_PROGRESS_STREAM_A | IN_PROGRESS_STREAM_B | IN_PROGRESS_STREAM_C (one or more streams active; record which streams this session owns in `status_history` field) → STREAMS_COMPLETE_PENDING_INTEGRATION → COMPLETE. Each transition writes a `status_history` entry with timestamp and one-line note.

**Multi-session coordination.** Native confirmed parallel Claude Code streams permitted (2026-04-27). If multiple sessions are active concurrently, each session claims one or more sub-streams. Claims are recorded in `status_history`. No two sessions own the same sub-stream simultaneously.

## §1 — Mission

Build the foundational cross-cutting abstractions specified in `MARSYS_JIS_ARCHITECTURE_v1_0.md §4.6 Domain D6` and operationalized in `MARSYS_JIS_PROJECT_PLAN_v1_0.md §4 Phase 0`. These four components are dependencies for every subsequent phase:

- **C6.1 LLM Provider Abstraction** with OpenAI/GPT integration added (the existing abstraction wraps Anthropic, Google, DeepSeek; this phase adds OpenAI).
- **C6.2 Schema Registry** holding the JSON schema definitions for the six load-bearing types: QueryPlan, Bundle, ToolBundle, AuditEvent, AssetEntry, PanelMetadata.
- **C6.3 Configuration Service** providing hot-reloadable feature flags and component configuration.
- **C6.4 Telemetry stubs** for per-component metric recording (full telemetry implementation comes later; Phase 0 lays scaffolding).

Phase 0 is purely additive. No existing code paths regress. No data is migrated. The only user-visible change is GPT-5 (or current OpenAI flagship) appearing in the model picker — and even that is gated to ensure existing models continue to work identically.

The phase is parallelizable into three independent sub-streams (A, B, C). One Claude Code session can execute all three serially; multiple sessions can take one each in parallel.

## §2 — Mandatory Pre-flight Reading

Read in full, in this order. Do not skip. Note your understanding of each before proceeding.

**§2.1 — Architectural and project context (read first):**

1. `CLAUDE.md` (project root) — project orientation, governance principles, current execution position.
2. `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` — the architectural source of truth. Pay particular attention to: §3 Architectural Principles (especially P.7 modular componentization and P.10 multi-model forward-compatibility); §4.6 Domain D6 (the four components Phase 0 builds); §15 Interface Contracts (the six load-bearing contracts; Phase 0 establishes the schemas for them); §17 Migration from Current State (Phase 0's place in the sequence).
3. `00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md` — the master project plan. Read §3 universal definition-of-done and §4 Phase 0 specification in full. §15 dependency graph for context.

**§2.2 — Current code state (read to understand what you're modifying):**

4. `platform/src/lib/models/registry.ts` — existing model registry. Understand the registry schema (capability flags, provider field, model entries).
5. `platform/src/lib/models/resolver.ts` — existing model resolver. Understand the switch-based provider dispatch.
6. `platform/src/lib/models/anthropic.ts`, `google.ts`, `deepseek.ts` (or equivalent files for the existing providers) — exemplars for how to structure the new OpenAI adapter.
7. `platform/src/components/consume/ModelStylePicker.tsx` — existing model dropdown UI. Locate where the model list is consumed; understand how to add a new entry.
8. `platform/src/app/api/chat/consume/route.ts` — main streaming route. Note that Phase 0 does NOT modify this route; you read it only to confirm the new OpenAI model integration will be picked up automatically by the existing route.

**§2.3 — Configuration and environment:**

9. `.env.example` (or equivalent in `platform/`) — existing env-var documentation pattern. Phase 0 adds `OPENAI_API_KEY` to this file.
10. Any existing TypeScript path-alias or import patterns the project uses (`tsconfig.json`, etc.) — match them in new files.

**§2.4 — What NOT to read for execution intent:**

The four predecessor documents (`CONSUME_DESIGN_v0_1.md`, `PANEL_SYNTHESIS_ADDENDUM_v0_1.md`, `MARSYS_JIS_Architecture_Review_Brief.docx`, `PANEL_IMPLEMENTATION_BRIEF_v1_0.md`) are SUPERSEDED. Their content has been absorbed into the architecture document. Reading them for execution intent is unnecessary and may produce stale instructions; the architecture document is the single source of truth.

After completing pre-flight reading, summarize your understanding in 4-6 sentences before proceeding to sub-stream execution. This confirms the design landed correctly.

## §3 — Hard Scope Constraints

### `may_touch` (allowed surfaces)

- `platform/src/lib/models/openai.ts` — NEW file (Stream A).
- `platform/src/lib/models/registry.ts` — modify to add the OpenAI entry (Stream A).
- `platform/src/lib/models/resolver.ts` — modify to add the OpenAI provider case (Stream A).
- `platform/src/lib/schemas/` — NEW directory (Stream B).
- `platform/src/lib/config/` — NEW directory (Stream C).
- `platform/src/lib/telemetry/` — NEW directory (Stream C).
- `platform/src/components/consume/ModelStylePicker.tsx` — modify to surface the new model in the dropdown (Stream A).
- `package.json` — add `@ai-sdk/openai` dependency (Stream A).
- `package-lock.json` (or `pnpm-lock.yaml` / `yarn.lock` per the project's package manager) — auto-updated by package install.
- `.env.example` (or equivalent) — add `OPENAI_API_KEY` documentation (Stream A).
- This brief itself — only for status transitions and `status_history` updates.
- New test files in the project's existing test directory pattern (Streams A, B, C — for unit + integration tests of new components).

### `must_not_touch` (forbidden surfaces — parallel-stream protection)

The M2/B.5 thread is PAUSED but its files remain on disk. DO NOT modify, rename, or delete any of these:

**Governance and architecture (read-only):**
- `00_ARCHITECTURE/` — entire directory. Architecture and Project Plan documents are read-only context for Phase 0; you do NOT update them.
- `CLAUDECODE_BRIEF.md` (project root, if present) — belongs to the M2/B.5 stream; do not touch.
- The four superseded predecessor documents (`CONSUME_DESIGN_v0_1.md`, `PANEL_SYNTHESIS_ADDENDUM_v0_1.md`, `PANEL_IMPLEMENTATION_BRIEF_v1_0.md`, plus the `.docx` retrieval brief) — leave their `SUPERSEDED` status as-is.

**Data layers (read-only):**
- `01_FACTS_LAYER/` — L1 facts.
- `02_*` (any directory starting with 02) — L2 analysis.
- `025_HOLISTIC_SYNTHESIS/` — L2.5 holistic.
- `03_DOMAIN_REPORTS/` — L3 reports.
- `035_DISCOVERY_LAYER/` — L3.5 discovery (active surface for the paused M2/B.5 stream).
- `04_REMEDIAL_CODEX/` (if present) — L4.
- `05_TEMPORAL_ENGINES/` (if present) — L5.
- `06_LEARNING_LAYER/` — L6 learning. Includes prediction ledger and pattern register; the M2/B.5 stream may have been actively writing here. DO NOT touch.

**Paused-stream code surfaces:**
- `platform/python-sidecar/` — entire Python sidecar including `rag/`, `chunkers/`, recent B.5/B.6 deliverables. DO NOT modify any file under this directory. Phase 0 does not require any Python sidecar changes.
- `platform/scripts/governance/` — drift_detector, schema_validator, mirror_enforcer. Belongs to governance tooling; do not touch.
- `platform/src/lib/rag/` (if present) — recent B.6 retrieval client work. Do not touch in Phase 0.
- `platform/src/lib/claude/consume-tools.ts` — existing 8-tool surface. Phase 0 does not extend this; new tools come in Phase 2.
- `platform/src/lib/claude/system-prompts.ts` — existing system prompt. Phase 0 does not modify this.
- The `.gemini/` directory and `.geminirules` — Gemini-side mirror surfaces.

**Database and runtime:**
- DO NOT execute any migration scripts in Phase 0. Phase 0 is code-only; no schema changes.
- DO NOT modify any existing pipeline files (consume/route.ts, consume-tools.ts) beyond the strictly-needed additions in Stream A.

**Behavioral constraints:**
- Existing single-model behavior MUST NOT regress. All 8 currently-supported models (3 Claude variants + 3 Gemini variants + 2 DeepSeek variants) must continue to work identically.
- Adding the OpenAI provider must not change the resolution logic for any existing provider.
- The new schemas, config service, and telemetry stubs are scaffolding only — they must not be wired into any production code path in Phase 0. Wiring happens in subsequent phases as those phases land.

If you encounter a situation where Phase 0 work seems to require touching a `must_not_touch` surface, halt and ask native. Do not proceed under any interpretation that loosens these constraints.

## §4 — Sub-Stream Overview

Three sub-streams run in Phase 0. They are independent and can run in any order or in parallel.

**Stream A — OpenAI Provider Integration.** Adds GPT-5 (or current OpenAI flagship) as a usable single-model option. End-state: user selects GPT-5 in the dropdown, sends a query, gets a streamed response identical in shape to existing Claude/Gemini/DeepSeek queries.

**Stream B — Schema Registry.** Builds the JSON Schema definitions for the six load-bearing types. End-state: schemas live at `platform/src/lib/schemas/`; a validation utility lets other code validate records against them; TypeScript types derived from the schemas are exported.

**Stream C — Configuration Service + Telemetry stubs.** Builds the hot-reloadable Configuration Service and the Telemetry recording API. End-state: feature flags can be defined and queried; flag values can be overridden via environment variables; metrics can be recorded by any component.

Each stream's specification follows. Within a stream, tasks should generally be executed in the order listed.

## §5 — Stream A: OpenAI Provider Integration

**Goal.** Add OpenAI/GPT as a fully-functional single-model provider, matching the patterns used by the existing Anthropic / Google / DeepSeek providers.

**Tasks (in order):**

**A.1 — Install package.** Add `@ai-sdk/openai` to `package.json` dependencies. Use the latest stable version compatible with the existing Vercel `ai` SDK version in the project. Run the project's package manager to install (`npm install`, `pnpm install`, or `yarn install` per project convention).

**A.2 — Create the adapter.** Create `platform/src/lib/models/openai.ts`. Match the structure of `anthropic.ts`, `google.ts`, or `deepseek.ts` (whichever exists; use the most recent one as a template). The adapter exports a function that takes a model ID and returns a `LanguageModel` instance compatible with the Vercel `ai` SDK's `streamText`.

```typescript
// Example shape (match existing pattern)
import { openai } from '@ai-sdk/openai'

export function getOpenAIModel(modelId: string) {
  return openai(modelId)
}
```

**A.3 — Determine the OpenAI flagship model ID.** At execution time, verify the current OpenAI flagship via the `@ai-sdk/openai` documentation. As of 2026, this is likely `gpt-5` or `gpt-5.x`. Use the exact model ID string the SDK supports. If multiple flagship-tier models are available (e.g., `gpt-5` and `gpt-5-mini`), include only the flagship-tier `gpt-5` for now; smaller variants can be added later.

**A.4 — Update the registry.** Modify `platform/src/lib/models/registry.ts` to add the new model entry. Match the schema of existing entries. Capability flags:
- `provider: 'openai'`
- `tool-use: true` (GPT-5 supports tool use)
- `prompt-caching: true` if OpenAI's automatic prompt caching is supported by the SDK; `false` otherwise. Verify against `@ai-sdk/openai` documentation. Note: OpenAI's prompt caching is automatic and does not require explicit cache-control headers, unlike Anthropic.
- `streaming: true`
- `maxOutputTokens`: per the model's documentation; reasonable default is 16384 unless the spec says otherwise.
- `displayName`: 'GPT-5' or whatever the flagship's marketing name is.

**A.5 — Update the resolver.** Modify `platform/src/lib/models/resolver.ts` to add a `case 'openai'` branch that calls `getOpenAIModel(meta.id)`. Match the pattern of existing cases. The exhaustiveness check (`_exhaustive: never`) at the end of the switch should now include 'openai' in the union.

**A.6 — Update environment variable documentation.** Add `OPENAI_API_KEY` to `.env.example` (or the equivalent file the project uses for env documentation) with a comment:

```
# OpenAI API key for GPT-5 access (Phase 0 of MARSYS-JIS architecture)
# Required if any user selects GPT-5 in the model picker.
OPENAI_API_KEY=sk-...
```

If the project uses a separate environment-variable-documentation file or a Cloud Run secret-manager pattern, follow that instead of literal `.env.example`.

**A.7 — Update the model picker UI.** Modify `platform/src/components/consume/ModelStylePicker.tsx` (or whatever the equivalent dropdown component is named) to include the new GPT-5 entry. Match the existing dropdown pattern — likely an array of model entries with `id`, `displayName`, `provider` fields, with appropriate icon or label.

**A.8 — End-to-end verification.** With `OPENAI_API_KEY` set in the development environment, manually verify:
- GPT-5 appears in the model picker.
- Selecting GPT-5 and sending a simple query returns a streamed response.
- The response renders correctly in the conversation panel.
- Multi-turn conversations work (model receives history correctly).
- Tool-use works (if you can write a quick test that triggers a tool call).

**A.9 — Regression check.** Verify all 8 existing model selections still work end-to-end. Run a quick query against each existing model (Claude Haiku, Sonnet, Opus; Gemini variants; DeepSeek variants).

**Stream A acceptance criteria:**
- [ ] `@ai-sdk/openai` installed; lockfile updated.
- [ ] `platform/src/lib/models/openai.ts` created and exports the adapter.
- [ ] Registry contains the new GPT-5 entry with correct capability flags.
- [ ] Resolver handles `openai` provider without errors; exhaustiveness check passes.
- [ ] `OPENAI_API_KEY` documented as a required env var.
- [ ] ModelStylePicker shows the new model option.
- [ ] End-to-end query with GPT-5 works (streaming, multi-turn, tool-use).
- [ ] Existing Claude/Gemini/DeepSeek model selections continue to work without regression.
- [ ] No file in `must_not_touch` was modified.

**Stream A test files to create:**
- `platform/src/lib/models/__tests__/openai.test.ts` — unit test for the adapter (mocked SDK).
- `platform/src/lib/models/__tests__/registry.test.ts` — verify the new entry is present and has correct fields.
- `platform/src/lib/models/__tests__/resolver.test.ts` — verify `openai` case resolves correctly.

## §6 — Stream B: Schema Registry

**Goal.** Define the JSON Schema definitions for the six load-bearing types specified in `MARSYS_JIS_ARCHITECTURE_v1_0.md §15` and detailed in Appendix A of that document. Provide a validation utility and TypeScript types derived from the schemas.

**Tasks (in order):**

**B.1 — Create the schemas directory.** Create `platform/src/lib/schemas/` as a new directory.

**B.2 — Author the six JSON Schema files.** Use JSON Schema Draft 2020-12 (or whatever version the project's existing schemas in `06_LEARNING_LAYER/SCHEMAS/` use, for consistency). DO NOT modify the existing schemas in `06_LEARNING_LAYER/SCHEMAS/` (they belong to the paused stream); the new schemas live in `platform/src/lib/schemas/`.

Required files (one schema per file):

- `platform/src/lib/schemas/asset_entry.schema.json` — see Architecture Appendix A AssetEntry. Required fields: `canonical_id`, `path`, `version`, `status`, `layer`, `expose_to_chat`, `representations`, `interface_version`, `fingerprint`, `native_id`. Optional: `preferred_for`, `always_required`, `tool_binding`, `cost_weight`, `supplements_parent`.

- `platform/src/lib/schemas/query_plan.schema.json` — see Architecture Appendix A QueryPlan. Required fields: `query_plan_id`, `query_text`, `query_class` (enum of 8 values: factual, interpretive, predictive, cross_domain, discovery, holistic, remedial, cross_native), `domains`, `forward_looking`, `audience_tier`, `tools_authorized`, `history_mode`, `panel_mode`, `expected_output_shape`, `manifest_fingerprint`, `schema_version`. Optional: `planets`, `houses`, `dasha_context_required`, `graph_seed_hints`, `graph_traversal_depth`, `bundle_directives`, `adjudicator_model_id`, `router_confidence`, `router_model_id`.

- `platform/src/lib/schemas/bundle.schema.json` — see Architecture Appendix A Bundle. Required: `bundle_id`, `query_plan_reference`, `manifest_fingerprint`, `mandatory_context`, `total_tokens`, `bundle_hash`, `schema_version`. Optional: `retrieved_context`.

- `platform/src/lib/schemas/tool_bundle.schema.json` — see Architecture Appendix A ToolBundle. Required: `tool_bundle_id`, `tool_name`, `tool_version`, `invocation_params`, `results`, `served_from_cache`, `latency_ms`, `result_hash`, `schema_version`. Optional: `cache_key`.

- `platform/src/lib/schemas/audit_event.schema.json` — see Architecture Appendix A AuditEvent. Comprehensive schema; required fields are extensive — refer to the architecture document Appendix A for the full list. Schema version `"1.0"`.

- `platform/src/lib/schemas/panel_metadata.schema.json` — see Architecture §10 panel mode and Appendix A PanelMetadata. Required nested structures: `panel_composition`, `merged_super_bundle`, `panel_responses`, `anonymization`, `adjudicator_synthesis`, `divergence_classification`. Plus `panel_total_cost_estimate_usd`, `panel_total_latency_ms`.

For each schema:
- Include a top-level `$id` field with a stable URI (e.g., `"https://marsys-jis/schemas/query_plan.schema.json"`).
- Include `title` and `description` at top level.
- Include `version` field at top level (`"1.0"`).
- Use `$ref` for shared sub-types (e.g., audience_tier enum) if they're shared across schemas.

**B.3 — Create the validation utility.** Create `platform/src/lib/schemas/index.ts` with:
- TypeScript type exports derived from the JSON schemas (use a tool like `json-schema-to-typescript` if convenient, or hand-author the types matching the schemas).
- A validation function: `validate<T>(schemaName: string, data: unknown): { valid: boolean, errors?: ValidationError[], data?: T }`.
- Use a JSON Schema validation library compatible with the project (e.g., `ajv`). Add the dependency to `package.json` if not already present.
- A `getSchema(name: string): JSONSchema` function for runtime schema retrieval.

**B.4 — Create the schema index.** A simple `platform/src/lib/schemas/manifest.json` listing all six schemas with their version numbers, paths, and one-line descriptions. This is the registry's own catalog of schemas.

**B.5 — Write unit tests.** Test files at `platform/src/lib/schemas/__tests__/`:
- `validation.test.ts` — for each of the six schemas, write at least one valid example record (passes validation) and one invalid example (fails validation with informative error).
- `types.test.ts` — verify TypeScript types are usable (compile-time test; use a small example assigning a value to each type).

**Stream B acceptance criteria:**
- [ ] All six schema files exist at `platform/src/lib/schemas/` with correct content per architecture Appendix A.
- [ ] Schema validation utility works: `validate('query_plan', exampleQueryPlan)` returns `{ valid: true }` for valid examples and `{ valid: false, errors: [...] }` for invalid.
- [ ] TypeScript types derived from schemas are usable in other code.
- [ ] Schema index `manifest.json` lists all six schemas.
- [ ] All unit tests pass.
- [ ] No file in `must_not_touch` was modified (especially `06_LEARNING_LAYER/SCHEMAS/` — those are different schemas owned by the paused stream).

**Note on schema scope.** Phase 0 creates the schema *definitions* and validation infrastructure. The schemas are not yet wired into any production code path; that wiring happens in Phases 2-7 as those phases use the relevant schema for runtime validation.

## §7 — Stream C: Configuration Service and Telemetry Stubs

**Goal.** Build the hot-reloadable Configuration Service for feature flags and component configuration, plus the Telemetry stub API for per-component metric recording.

**Tasks (in order):**

**C.1 — Create the config directory.** Create `platform/src/lib/config/`.

**C.2 — Define feature-flag types and registry.** Create `platform/src/lib/config/feature_flags.ts`:
```typescript
export type FeatureFlag = 
  | 'PANEL_MODE_ENABLED'
  | 'MANIFEST_BUILDER_ENABLED'
  | 'LLM_CHECKPOINTS_ENABLED'
  | 'BUNDLE_AUGMENTER_ENABLED'
  | 'MSR_RERANKER_ENABLED'
  | 'SEMANTIC_GATE_ENABLED'
  | 'NEW_QUERY_PIPELINE_ENABLED'
  | 'AUDIT_ENABLED'
  | 'AUDIT_VIEW_VISIBLE'
  | 'PANEL_CHECKBOX_VISIBLE'

export const DEFAULT_FLAGS: Record<FeatureFlag, boolean> = {
  PANEL_MODE_ENABLED: false,
  MANIFEST_BUILDER_ENABLED: false,
  LLM_CHECKPOINTS_ENABLED: false,
  BUNDLE_AUGMENTER_ENABLED: false,
  MSR_RERANKER_ENABLED: false,
  SEMANTIC_GATE_ENABLED: false,
  NEW_QUERY_PIPELINE_ENABLED: false,
  AUDIT_ENABLED: false,
  AUDIT_VIEW_VISIBLE: false,
  PANEL_CHECKBOX_VISIBLE: false,
}
```

All Phase 0+ feature flags listed; all default to `false` so Phase 0's foundation work doesn't accidentally activate any pipeline behavior.

**C.3 — Implement the Configuration Service.** Create `platform/src/lib/config/index.ts`:

```typescript
export interface ConfigService {
  getFlag(name: FeatureFlag): boolean
  setFlag(name: FeatureFlag, value: boolean): void  // dev-only; production uses env override
  getValue<T>(key: string, defaultValue: T): T
  subscribe(callback: (key: string, value: unknown) => void): () => void
}
```

Implementation:
- Reads default flag values from `DEFAULT_FLAGS`.
- Overrides via environment variables: `MARSYS_FLAG_PANEL_MODE_ENABLED=true` etc.
- Supports hot-reload via filesystem watch in development (optional; can be deferred to a later phase if complex).
- Pub-sub for `subscribe()` to notify when flag changes.
- Singleton pattern so all components share the same config.

**C.4 — Create the telemetry directory.** Create `platform/src/lib/telemetry/`.

**C.5 — Implement the Telemetry stubs.** Create `platform/src/lib/telemetry/index.ts`:

```typescript
export interface TelemetryService {
  recordMetric(componentId: string, metricName: string, value: number, tags?: Record<string, string>): void
  recordLatency(componentId: string, operation: string, latencyMs: number): void
  recordCost(componentId: string, model: string, inputTokens: number, outputTokens: number, costUsd: number): void
  recordError(componentId: string, errorType: string, error: Error): void
}
```

Phase 0 implementation: log to console (dev) or to a structured log destination if the project has one. Real metric export to Cloud Monitoring (or equivalent) is a later-phase concern; Phase 0 just establishes the API.

**C.6 — Define metric types.** Create `platform/src/lib/telemetry/metrics.ts` with constants for the metric names used throughout the system:

```typescript
export const Metrics = {
  COMPONENT_LATENCY_MS: 'component.latency_ms',
  COMPONENT_COST_USD: 'component.cost_usd',
  COMPONENT_ERROR_RATE: 'component.error_rate',
  LLM_INPUT_TOKENS: 'llm.input_tokens',
  LLM_OUTPUT_TOKENS: 'llm.output_tokens',
  CACHE_HIT_RATE: 'cache.hit_rate',
  // ... add others as components land
} as const
```

**C.7 — Write unit tests.**
- `platform/src/lib/config/__tests__/index.test.ts` — verify env-var override works, defaults work, `subscribe()` fires on changes.
- `platform/src/lib/telemetry/__tests__/index.test.ts` — verify `recordMetric()` produces a structured log/output.

**Stream C acceptance criteria:**
- [ ] Config service exposes feature flags via `getFlag()`.
- [ ] Default flag values match the Phase 0 spec (all `false`).
- [ ] Environment variable override works: setting `MARSYS_FLAG_PANEL_MODE_ENABLED=true` makes `getFlag('PANEL_MODE_ENABLED')` return true.
- [ ] Subscribe/unsubscribe pattern works (hot-reload).
- [ ] Telemetry service exposes `recordMetric()`, `recordLatency()`, `recordCost()`, `recordError()`.
- [ ] At least one metric appears in the structured log when `recordMetric()` is called.
- [ ] All unit tests pass.

## §8 — Integration and Final Acceptance

After all three sub-streams are complete, run integration verification:

**§8.1 — Cross-stream import test.** Verify that the new components can import from each other where appropriate. For example, `platform/src/lib/config/index.ts` should be importable from any other lib file. The Telemetry service should be importable. The schemas should be importable.

**§8.2 — End-to-end smoke test.** With `NEW_QUERY_PIPELINE_ENABLED` flag still `false` (the default), verify:
- The Consume tab loads.
- All 9 model options (Claude × 3, Gemini × 3, DeepSeek × 2, GPT × 1) appear in the picker.
- Selecting any model and sending a query produces a streamed response (using the EXISTING pipeline; the new pipeline isn't wired yet).
- No error appears in the browser console or server logs.

**§8.3 — Test suite execution.** Run the full project test suite. All tests must pass:
- New unit tests added by Streams A, B, C.
- All pre-existing tests.

**§8.4 — Lint and type-check.** Run the project's linting and type-checking commands. No new warnings or errors.

**§8.5 — Documentation check.** Verify any inline documentation added to new files is clear and useful. Component-level docstrings on the new lib directories' index files describe what each component is and how to use it.

**§8.6 — `must_not_touch` verification.** Run `git status` (or equivalent) and confirm no file in the `must_not_touch` list of §3 has been modified. If any unintended modifications exist, revert them.

## §9 — Phase 0 Done Criteria

This brief is `COMPLETE` when ALL of the following are true:

1. All Stream A acceptance criteria met.
2. All Stream B acceptance criteria met.
3. All Stream C acceptance criteria met.
4. All §8 integration verification steps passed.
5. `git status` shows no modifications to `must_not_touch` surfaces.
6. The project builds without warnings.
7. Native (or designated reviewer) confirms acceptance.

When all criteria met:
- Update this brief's frontmatter `status` field from current state to `COMPLETE`.
- Add `completed_on` field with the current date.
- Append a `status_history` final entry summarizing what was accomplished.
- Notify native that Phase 0 is complete and Phase 1 brief authoring can begin.

## §10 — Communication Discipline

**Halt on uncertainty.** If during execution you discover an architectural choice the brief didn't make, do NOT improvise. Halt, surface the question to the native, and wait for direction. Do not silently make architectural decisions outside the brief.

**No scope creep.** If you find a tangentially related issue (a bug in single-model behavior, an opportunity to refactor a related module, a typo elsewhere), note it in a new file `PHASE_0_OBSERVATIONS_v1_0.md` for native review. Do not fix it as part of this brief.

**Status updates between sessions.** If execution spans multiple sessions, each session-end leaves the brief's `status_history` field updated with what was accomplished, what's next, and any blockers surfaced. The next session resumes from the exact state indicated.

**Multi-session coordination.** If multiple sessions are running in parallel (per the user's enabling of parallel streams), each session claims one or more of the three sub-streams. Claims are recorded in `status_history`. No two sessions own the same sub-stream.

**Adherence to architectural principles.** The architecture document's §3 Principles govern all implementation decisions. In particular: P.7 modular componentization with stable interfaces (don't create cross-component coupling); P.8 domain knowledge → LLM, integrity/lookup/persistence → deterministic (relevant for telemetry stubs — they're pure infrastructure, no LLM); P.10 multi-model and multi-native forward-compatibility (the OpenAI integration must work for any future native, even though only Abhisek's chart is deployed today).

## §11 — Final Notes

Phase 0 is foundational. The components built here have no end-user-visible value (except the OpenAI integration), but they are dependencies for every subsequent phase. Build them carefully — the patterns established here propagate.

The schemas in particular merit attention: they are the contracts between components. A schema authored badly in Phase 0 will be a load-bearing pain point for years. Spend the time to get them right; refer to the architecture document Appendix A and §15 in detail.

The Configuration Service's feature-flag pattern is what enables the entire migration to be reversible. Every subsequent phase will add flags here. Keep the pattern simple and discoverable.

When Phase 0 completes, native will review and either approve (Phase 1 brief authored next) or request revisions. Phase 1 is where the migration scope grows substantially (capability manifest, per-native namespacing, MSR ETL, governance cutover) — having a solid foundation matters.

---

*End of EXEC_BRIEF_PHASE_0_v1_0.md (status `AUTHORED`, 2026-04-27). Trigger phrase: "Read EXEC_BRIEF_PHASE_0_v1_0.md and execute it." On Phase 0 completion, status flips to `COMPLETE` and Cowork authors `EXEC_BRIEF_PHASE_1_v1_0.md`.*
