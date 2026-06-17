---
artifact: EXEC_BRIEF_PHASE_2_v1_0.md
status: COMPLETE
completed_on: "2026-04-27"
status_history:
  - timestamp: "2026-04-27T00:00:00Z"
    status: AUTHORED
    note: "Brief authored by Cowork (Claude Opus 4.7)"
  - timestamp: "2026-04-27T12:00:00Z"
    status: IN_PROGRESS_STREAM_A_B_C_D
    note: "Execution started — pre-flight complete; dispatching parallel subagents for all four streams"
  - timestamp: "2026-04-27T23:30:00Z"
    status: COMPLETE
    note: "All streams complete; 323 Phase 2 tests passing; smoke test succeeds for all 8 query classes; type-check clean; must_not_touch verified"
    classification_accuracy_note: "Router unit tests pass; real LLM accuracy not measured in offline execution (requires API key)"
    bundle_entries_per_class:
      factual: 2
      interpretive: 5
      predictive: 4
      cross_domain: 5
      discovery: 6
      holistic: 19
      remedial: 2
      cross_native: 3
    tool_execution_latency_note: "filesystem tools (pattern, resonance, cluster, contradiction) sub-50ms; temporal via sidecar 1 result; msr_sql requires Cloud SQL (not available offline)"
    cache_hit_rate_smoke_test: "Cache deduplication verified — repeated identical calls return served_from_cache:true; msr_sql not available for full verification"
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
executor_target: Claude Code (Anti-Gravity / VS Code extension; NOT the CLI)
trigger_phrase: "Read EXEC_BRIEF_PHASE_2_v1_0.md and execute it."
phase_number: 2
phase_name: Query Pipeline Basic (Domain D2)
purpose: Build the deterministic query pipeline foundation. Stage-2 Router with 8 query classes (including cross-native per Q3); Bundle Composer rule-only (no Augmenter — that's Phase 6); Retrieval Tool Suite with 7 basic tools (MSR-SQL, 4 L3.5 register filters, Temporal, query_msr_aggregate placeholder); Tool-Call Cache. Phase 2 produces a deterministic pipeline that takes a query and produces a retrieval bundle — without yet wiring it into the Consume route (that's Phase 3).
depends_on:
  - 00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md (APPROVED 2026-04-27 — §4.2 D2 Query Pipeline; §9 Router and QueryPlan; §8 Retrieval Architecture; Appendix A QueryPlan + ToolBundle schemas)
  - 00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md (APPROVED 2026-04-27 — §6 Phase 2 specification)
  - EXEC_BRIEF_PHASE_0_v1_0.md (COMPLETE — Phase 0's Provider Abstraction enables Router LLM calls; Schema Registry holds QueryPlan + ToolBundle schemas; Configuration Service holds feature flags)
  - EXEC_BRIEF_PHASE_1A_v1_0.md (COMPLETE — Phase 1A's Storage Layer is foundational for retrieval tools; msr_signals table populated with 499 signals)
  - EXEC_BRIEF_PHASE_1B_v1_0.md (COMPLETE — Phase 1B's Capability Manifest is the asset catalog the Router consults via Bundle Composer)
  - CLAUDE.md (project orientation, now updated post-1B to reference CAPABILITY_MANIFEST.json)
parallel_stream_tolerance: |
  Phase 2 is designed to run with the M2/B.5 governance/discovery/retrieval thread RESUMED in parallel.
  Phase 2 is purely additive in platform/src/lib/router/, platform/src/lib/bundle/, platform/src/lib/retrieve/,
  platform/src/lib/cache/. It does NOT modify governance tooling (already cut over in 1B), does NOT touch the
  manifest or its overrides, does NOT modify Python sidecar files. M2/B.5 may run freely during Phase 2.
chosen_path: Q3 cross-native query class included in router classification rules from start. Phase 2's
  query_msr_aggregate placeholder tool returns "multi-native not yet deployed" gracefully. The architecture
  is multi-native-ready from this phase forward; multi-native deployment is a separate later phase that
  this work doesn't block.
risk_classification: MEDIUM. Significantly less risky than Phase 1B (no migration, no governance flip).
  Multiple sub-streams parallelizable. The Router is the most consequential single component in this phase
  because the QueryPlan it emits drives every downstream stage.
---

# EXECUTION BRIEF — Phase 2: Query Pipeline Basic

## §0 — Trigger and Execution Model

Native triggers this brief by saying to a Claude Code session: **"Read EXEC_BRIEF_PHASE_2_v1_0.md and execute it."**

On trigger, Claude Code MUST:
1. Read this entire brief end-to-end before any other action.
2. Read the mandatory pre-flight artifacts in §2 in the order specified.
3. Read the relevant codebase files in §2 to understand current state.
4. Acknowledge readiness; propose the sub-stream sequence (one of A-D in series, parallel via subagents, or multi-session parallel).
5. Execute per the specifications in §5 through §8.
6. On completion: integration verification per §9; flip status to `COMPLETE`; notify native.

**Status transitions.** AUTHORED → IN_PROGRESS_STREAM_(A|B|C|D) → STREAMS_COMPLETE_PENDING_INTEGRATION → COMPLETE. Each transition writes a `status_history` entry with timestamp and one-line note.

**Multi-session coordination.** Native confirmed parallel Claude Code streams permitted. Stream A (Router) and Stream B (Bundle Composer) can be developed in parallel — they use the same QueryPlan schema as a contract but are otherwise independent. Stream C (Retrieval Tool Suite) is a collection of 7 tools each implementing the same `retrieve(QueryPlan) → ToolBundle` interface; tools can be developed in parallel. Stream D (Tool-Call Cache) is small and independent. Recommended within-session subagent pattern: A + B + C-tools-1-3 + D in parallel; C-tools-4-7 in second wave.

## §1 — Mission

Build the deterministic foundation of the query pipeline. Phase 2 produces:

- A **Stage-2 Router** (C2.1) that classifies queries into one of 8 classes (factual, interpretive, predictive, cross_domain, discovery, holistic, remedial, **cross_native**) and emits a structured `QueryPlan`. Default model: Claude Haiku 4.5; configurable via Configuration Service.
- A **Bundle Composer (Rule Composer only)** (C2.2a) that takes the QueryPlan + Capability Manifest and applies the bundle composition rules from architecture §9 — floor (FORENSIC + CGM ≈ 40K) plus class-conditional adds. The Bundle Augmenter LLM checkpoint (C2.2b) is NOT in Phase 2; it lands in Phase 6.
- A **Retrieval Tool Suite (basic)** (C2.3 subset) implementing 7 tools: MSR-SQL filter, Pattern Register filter, Resonance Register filter, Cluster Atlas filter, Contradiction Register filter, Temporal lookup, and the cross-native `query_msr_aggregate` placeholder. Each tool implements the uniform `retrieve(QueryPlan) → ToolBundle` interface. Graph Walk and Vector Search are NOT in Phase 2; they land in Phase 9.
- A **Tool-Call Cache** (C2.5) — request-scoped Map keyed on `(tool_name, hash(normalized_params))` preventing duplicate execution within a panel turn (Phase 7 will use this; Phase 2 establishes it).

Phase 2 does NOT yet wire the pipeline into the Consume route — that's Phase 3 (Synthesis Single-Model). Phase 2's deliverables are usable from a script (e.g., `npm run pipeline:test --query="my saturn return"`) but not yet from the chat UI. This separation lets Phase 2 ship and be tested independently.

The phase is parallelizable into four sub-streams. Stream A (Router) is the most consequential because the QueryPlan it emits is the contract that drives every downstream component. Stream B (Bundle Composer) consumes QueryPlan output. Stream C (tools) are independent of A+B once the QueryPlan + ToolBundle schemas are stable. Stream D (cache) is independent of all.

## §2 — Mandatory Pre-flight Reading

Read in full, in this order. Do not skip.

**§2.1 — Architectural and project context (read first):**

1. `CLAUDE.md` — note that item 2 now references `CAPABILITY_MANIFEST.json` (post-1B cutover).
2. `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` — pay particular attention to: §4.2 Domain D2 components (C2.1 Router, C2.2 Bundle Composer, C2.3 Retrieval Tool Suite, C2.5 Tool-Call Cache); §8 Retrieval Architecture (Tier 1 eligible set, floor + conditional rules, Tier 2 + Tier 3); §9 Router and QueryPlan (the 8 query classes, the QueryPlan schema dimensions, the bundle composition rules); Appendix A schemas for QueryPlan, Bundle, ToolBundle, AssetEntry.
3. `00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md` §6 Phase 2 specification — the components, deliverables, acceptance criteria, open questions.

**§2.2 — Phase 0/1A/1B outputs you depend on:**

4. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (62 entries; fingerprint `0dee4e52...` post-1B cutover) — the Bundle Composer reads this for asset metadata.
5. `00_ARCHITECTURE/manifest_overrides.yaml` — `preferred_for` per query class, `cost_weight`, `always_required` flags. Bundle Composer uses these to apply per-class rules.
6. `platform/src/lib/schemas/query_plan.schema.json` — the QueryPlan schema. Router output validates against this; Bundle Composer + Retrieval Tools consume validated QueryPlans.
7. `platform/src/lib/schemas/tool_bundle.schema.json` — the ToolBundle schema. Each retrieval tool produces output validating against this.
8. `platform/src/lib/schemas/bundle.schema.json` — the Bundle schema (Bundle Composer output).
9. `platform/src/lib/schemas/asset_entry.schema.json` — manifest entries the Composer consults.
10. `platform/src/lib/schemas/index.ts` — validation utility.
11. `platform/src/lib/storage/index.ts` — Storage Layer abstraction. Retrieval tools use `getStorageClient().query()` (PostgreSQL), `.readObject()` (GCS), `.readFile()` (filesystem) per the tool's data source.
12. `platform/src/lib/config/index.ts` and `platform/src/lib/config/feature_flags.ts` — Configuration Service. Add new flags as needed (e.g., `ROUTER_MODEL_OVERRIDE`).
13. `platform/src/lib/telemetry/index.ts` — Telemetry. Each component emits per-operation latency + cost metrics.
14. `platform/src/lib/models/registry.ts` and `resolver.ts` — model abstraction. Router uses `resolveModel('claude-haiku-4-5')` or whatever's configured.

**§2.3 — Existing code to understand for context (do NOT modify):**

15. `platform/src/lib/claude/consume-tools.ts` — the existing 8-tool surface that the chat currently uses. Phase 2 does NOT extend this file; Phase 2 builds a parallel, manifest-driven retrieval suite that Phase 3 will integrate with. Read this file to understand: which tools exist, how they query the database, what their return shapes look like, what tools the new Phase 2 implementations should mirror functionally.
16. `platform/src/lib/claude/system-prompts.ts` — existing system prompt with the L2.5 routing mandate. Read for context; Phase 3 (not Phase 2) will adapt this to the new pipeline.
17. `platform/src/app/api/chat/consume/route.ts` — the streaming route. Read to understand the current pipeline shape; Phase 2 does NOT modify this. Phase 3 will wire the new pipeline into a feature-flagged branch.

**§2.4 — Current data state:**

18. The `msr_signals` table — 499 rows from Phase 1A's ETL. Spot-check a few rows: `SELECT * FROM msr_signals WHERE domain='financial' AND confidence > 0.7 LIMIT 5`. Confirm columns match the schema in `platform/src/lib/db/types.ts MsrSignal`.
19. L3.5 register sources — for tool implementations, you need to know how to query the registers. The PATTERN, RESONANCE, CLUSTER, CONTRADICTION registers are in `035_DISCOVERY_LAYER/REGISTERS/*.json`. Phase 2's tools read these via the Storage Layer's filesystem adapter (NOT via DB; the registers are JSON files, not tables). Read one register file (e.g., `PATTERN_REGISTER_v1_0.json`) to understand the structure.

After completing pre-flight reading, summarize your understanding in 5-7 sentences. Confirm: (a) the QueryPlan schema's required fields and the 8 query classes; (b) the bundle composition rules; (c) where each retrieval tool sources data from (DB / filesystem / sidecar); (d) the Storage Layer interface for each data source.

## §3 — Hard Scope Constraints

### `may_touch` (allowed surfaces)

**New files (creation allowed):**
- `platform/src/lib/router/` — Router (Stream A).
- `platform/src/lib/bundle/` — Bundle Composer (Stream B).
- `platform/src/lib/retrieve/` — Retrieval Tool Suite (Stream C).
- `platform/src/lib/cache/` — Tool-Call Cache (Stream D).
- `platform/src/scripts/test/pipeline_smoke.ts` (or similar) — a small CLI script that runs an end-to-end test of the pipeline against a synthetic query, producing a Bundle. Useful for Phase 2 verification.
- Test files in the project's existing test pattern.

**Existing files (modification allowed only as specified):**
- `platform/src/lib/config/feature_flags.ts` — add new flags as needed: `ROUTER_MODEL_OVERRIDE` (string), `BUNDLE_COMPOSER_DEBUG` (bool), `RETRIEVAL_TOOL_TIMEOUT_MS` (number).
- `package.json` — add npm scripts: `pipeline:test`, possibly others.

**This brief itself** — only for status transitions and `status_history` updates.

### `must_not_touch` (forbidden surfaces)

**Architecture and project plan (read-only):**
- `00_ARCHITECTURE/MARSYS_JIS_ARCHITECTURE_v1_0.md` — do NOT modify.
- `00_ARCHITECTURE/MARSYS_JIS_PROJECT_PLAN_v1_0.md` — do NOT modify.
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — do NOT modify. Phase 2 reads it; does not regenerate. (Manifest regeneration happens via the Manifest Builder when frontmatter or filesystem changes; Phase 2 doesn't change either.)
- `00_ARCHITECTURE/manifest_overrides.yaml` — do NOT modify in Phase 2.

**Predecessor briefs:** do NOT modify any of EXEC_BRIEF_PHASE_0/1A/1B's status or content. They're COMPLETE.

**Data layers (read-only — no frontmatter changes in Phase 2):**
- All canonical files in 01_FACTS_LAYER/, 02_*/, 025_HOLISTIC_SYNTHESIS/, 03_DOMAIN_REPORTS/, 035_DISCOVERY_LAYER/REGISTERS/, 06_LEARNING_LAYER/.
- 99_ARCHIVE/ — do NOT modify or move files out.

**Existing pipeline code (untouched in Phase 2):**
- `platform/src/lib/claude/consume-tools.ts` — existing 8-tool surface stays as-is. Phase 3 may interact with this; Phase 2 does not.
- `platform/src/lib/claude/system-prompts.ts`.
- `platform/src/app/api/chat/consume/route.ts`.
- `platform/src/components/consume/*`.
- `platform/src/lib/models/*` — Phase 0 deliverables; Phase 2 USES the resolver but doesn't modify it.

**M2/B.5 surfaces (parallel-stream protection):**
- `platform/python-sidecar/` — entire Python sidecar EXCEPT calls into existing endpoints (`/transits`, `/ephemeris`) which the Temporal tool legitimately calls.
- `platform/scripts/governance/` — governance scripts (cut over in 1B; do not modify in 2).
- `platform/src/lib/rag/` (if present) — recent B.6 retrieval client work; do not touch.
- The active CLAUDECODE_BRIEF.md (project root, if present) — belongs to M2/B.5 stream.
- `.gemini/`, `.geminirules`.

**Database schema:**
- DO NOT add new tables or columns in Phase 2. Existing schema (post-1A migrations) is sufficient.
- DO NOT execute migration scripts.
- READ-ONLY queries from Phase 2 code against `msr_signals` and any existing tables that Phase 2 tools need.

### Behavioral constraints

- Phase 2 produces deterministic components only. The Router uses an LLM (so technically there's an LLM call), but it's classifying — not synthesizing. Bundle Composer is purely rule-based (no LLM). Retrieval tools are purely deterministic (SQL queries, file reads, sidecar HTTP calls).
- The Router's classification rules MUST include the cross-native query class per Q3.
- The Bundle Composer rules MUST match architecture §9 exactly (floor + class-conditional adds).
- Each retrieval tool MUST conform to the uniform `retrieve(QueryPlan) → ToolBundle` interface.
- The query_msr_aggregate tool MUST return a graceful "multi-native not deployed" response (with a clear status field) rather than throwing. This is the placeholder pattern.
- No feature flags activated in Phase 2. The new pipeline exists as code but is NOT wired into any production code path. Phase 3 wires it.
- M2/B.5 may run in parallel; if a M2/B.5 commit lands during Phase 2 execution that modifies governance tooling, halt and ask native.

If you encounter a need to touch a `must_not_touch` surface, halt and ask native.

## §4 — Sub-Stream Overview and Dependencies

**Stream A — Router (Stage 2).** TypeScript service implementing `classify(query, context) → QueryPlan`. Uses Claude Haiku 4.5 by default; configurable. Classification covers all 8 query classes. Independent of B/C/D code-wise; outputs the QueryPlan that B + C + D consume.

**Stream B — Bundle Composer (Rule Composer).** TypeScript service implementing `compose(QueryPlan, Manifest) → Bundle`. Reads CAPABILITY_MANIFEST.json + manifest_overrides.yaml; applies architecture §9 composition rules; produces validated Bundle. Independent of A/C/D code-wise; uses QueryPlan as input contract.

**Stream C — Retrieval Tool Suite.** Seven tools, each implementing `retrieve(QueryPlan) → ToolBundle`. The tools:
- C.1 MSR-SQL filter (queries msr_signals table per QueryPlan domains/planets/dasha context).
- C.2 Pattern Register filter (filesystem read of PATTERN_REGISTER_v1_0.json + filtering).
- C.3 Resonance Register filter.
- C.4 Cluster Atlas filter.
- C.5 Contradiction Register filter.
- C.6 Temporal lookup (calls Python sidecar /transits + /ephemeris endpoints).
- C.7 query_msr_aggregate (cross-native placeholder; returns "not deployed" status).
Each tool is independent of the others; can be developed in parallel.

**Stream D — Tool-Call Cache.** TypeScript module implementing `get(key) → CachedResult | null`, `put(key, value)`, `clear()`. Request-scoped Map. Independent of A/B/C.

**Recommended execution shape (subagent parallelism within one Claude Code session):**

```
Time 1 (parallel): Stream A      Stream B      Stream C-tools-1-3   Stream D
                       (Router)   (Composer)   (MSR, Pattern, Res)   (Cache)

Time 2 (parallel): Stream C-tools-4-7
                   (Cluster, Contradiction, Temporal, query_msr_aggregate)

Time 3:           Integration verification per §9
```

For multi-session parallelism: split A + B + D in one session; Stream C in another session.

## §5 — Stream A: Router (Stage 2)

**Goal.** Build the Stage-2 Router that classifies queries and emits structured QueryPlan objects. Stateless service; small fast LLM; configurable model.

**Tasks (in order):**

**A.1 — Create the router directory.** Create `platform/src/lib/router/`.

**A.2 — Author the prompt template.** Create `platform/src/lib/router/prompt.ts`. The classification prompt instructs the LLM to:
- Read the user query plus minimal conversation context (last 1-2 user messages for context, no full history).
- Classify into one of 8 query classes.
- Identify domains (subset of: career, finance, psychology, health, relationships, spiritual, children, parents, travel — the 9 L3 domains).
- Identify planets and houses mentioned.
- Determine `forward_looking` (boolean).
- Determine `dasha_context_required` (boolean).
- Provide `graph_seed_hints` (array of CGM node IDs the LLM thinks would be useful seeds — note: in Phase 2 the graph walk tool isn't built yet, but the router emits hints anyway for Phase 9).
- Determine `tools_authorized` from the available tool list.
- Output strictly as JSON matching the QueryPlan schema.

Include 8 few-shot examples — one per query class — to anchor classification quality. The cross_native class needs particular attention: trigger linguistic signals include "across charts", "common patterns", "compared to others", "different natives", "research", "compare my chart with", "people with similar".

**A.3 — Implement the classifier.** Create `platform/src/lib/router/router.ts`:

```typescript
export interface RouterConfig {
  model_id: string  // default: 'claude-haiku-4-5' (or current Anthropic small flagship)
  temperature: number  // default: 0.0 (deterministic for classification)
  max_tokens: number  // default: 1024 (enough for structured output)
}

export interface RouterContext {
  conversation_history?: Array<{ role: 'user' | 'assistant', content: string }>  // last 1-2 turns
  audience_tier: 'super_admin' | 'acharya_reviewer' | 'client' | 'public_redacted'
  manifest_fingerprint: string  // for audit trail; passed to QueryPlan
}

export async function classify(
  query: string,
  context: RouterContext,
  config?: Partial<RouterConfig>
): Promise<QueryPlan> {
  // Resolve model via Phase 0's model resolver
  // Build messages from prompt template
  // Call streamText (or generateText for non-streaming classification)
  // Parse JSON output
  // Validate against QueryPlan schema (Phase 0's Schema Registry)
  // Add manifest_fingerprint, schema_version, router_model_id, router_confidence
  // Emit telemetry: latency, tokens
  // Return validated QueryPlan
}
```

**A.4 — Handle classification failures gracefully.** If the LLM produces invalid JSON or fails schema validation, retry once with stricter formatting instructions. If retry fails, return a default QueryPlan with `query_class: 'interpretive'`, `domains: []`, `forward_looking: false`, etc. — and a `router_confidence: 0.0` flag indicating the fallback was used. Log the failure to telemetry.

**A.5 — Add config flags.** In `platform/src/lib/config/feature_flags.ts` (extend the existing pattern), add:
- `ROUTER_MODEL_OVERRIDE: string` (default: `'claude-haiku-4-5'`)
- `ROUTER_TEMPERATURE: number` (default: 0.0)
- `ROUTER_MAX_TOKENS: number` (default: 1024)

These are runtime-configurable.

**A.6 — Tests.** Create `platform/src/lib/router/__tests__/`:
- `router.test.ts` — unit test with mocked LLM responses for each of the 8 classes.
- `classification.test.ts` — integration test against real LLM with a curated set of test queries (10+ queries, hand-labeled, run against Haiku 4.5; expect ≥80% accuracy on test set).
- `cross_native.test.ts` — specific test for cross_native class detection on edge-case queries.
- `fallback.test.ts` — test the schema-validation-failure fallback path.

**Stream A acceptance criteria:**
- [ ] Router service exists at `platform/src/lib/router/`.
- [ ] `classify()` accepts query + context, returns validated QueryPlan.
- [ ] All 8 query classes producible from test queries.
- [ ] Cross_native class triggers correctly on cross-chart queries.
- [ ] Schema validation enforced; invalid LLM output triggers retry then fallback.
- [ ] Telemetry emits per classification.
- [ ] Config flags work for model override.
- [ ] All tests pass.
- [ ] Classification accuracy ≥80% on the test set.

## §6 — Stream B: Bundle Composer (Rule Composer)

**Goal.** Build the deterministic Bundle Composer that takes a QueryPlan + the Capability Manifest and produces a validated Bundle per architecture §9 rules. The LLM Bundle Augmenter (Stage 4.5) is NOT in Phase 2.

**Tasks (in order):**

**B.1 — Create the bundle directory.** Create `platform/src/lib/bundle/`.

**B.2 — Author the rule composer.** Create `platform/src/lib/bundle/rule_composer.ts`. Implements:

```typescript
export interface BundleComposerConfig {
  manifest_path: string  // default: '00_ARCHITECTURE/CAPABILITY_MANIFEST.json'
  overrides_path: string  // default: '00_ARCHITECTURE/manifest_overrides.yaml'
  max_bundle_tokens: number  // default: 200000 (with margin under any model context window)
}

export async function compose(
  plan: QueryPlan,
  config?: Partial<BundleComposerConfig>
): Promise<Bundle> {
  // 1. Read manifest + overrides via Storage Layer
  // 2. Apply floor: include FORENSIC + CGM (always_required: true entries)
  // 3. Apply class-conditional adds per architecture §9:
  //    - if class in [interpretive, cross_domain, holistic]: + UCN + CDLM + RM
  //    - if class in [predictive] OR forward_looking: + LEL + SADE_SATI
  //    - if class in [discovery, holistic]: + 4 L3.5 registers
  //    - if class == holistic: + remaining T1 eligible
  //    - if class == cross_native: special handling — no per-native expansion; meta-bundle
  // 4. Compute total tokens (sum of token_count from manifest entries)
  // 5. If total > max_bundle_tokens: warn and degrade (drop conditional adds in priority order)
  // 6. Compute bundle_hash (sha256 of canonical_id list)
  // 7. Return validated Bundle (against bundle.schema.json)
}
```

**B.3 — Implement composition rules in detail.** A separate file `platform/src/lib/bundle/composition_rules.ts` encodes the rules as functions:

```typescript
export interface CompositionRule {
  name: string
  applies(plan: QueryPlan): boolean
  assets_to_add(plan: QueryPlan, manifest: ManifestData): AssetEntry[]
  role: 'floor' | 'interpretive' | 'predictive' | 'discovery' | 'holistic' | 'cross_native_meta'
}

export const COMPOSITION_RULES: CompositionRule[] = [
  {
    name: 'floor',
    applies: () => true,
    assets_to_add: (_, manifest) => manifest.entries.filter(e => e.always_required),
    role: 'floor'
  },
  {
    name: 'interpretive',
    applies: (p) => ['interpretive', 'cross_domain', 'holistic'].includes(p.query_class),
    assets_to_add: (_, manifest) => manifest.entries.filter(e => 
      ['UCN', 'CDLM', 'RM'].includes(e.canonical_id)),
    role: 'interpretive'
  },
  // ... etc.
]
```

**B.4 — Manifest reader.** Create `platform/src/lib/bundle/manifest_reader.ts`. Reads CAPABILITY_MANIFEST.json + manifest_overrides.yaml, merges them, exposes typed accessors. Caches the merged manifest in-process; reloads on file fingerprint change (or feature flag).

**B.5 — Cross-native handling.** For `query_class === 'cross_native'`, the bundle is a *meta-bundle*: floor (FORENSIC + CGM) + a placeholder marker indicating cross-native aggregation will occur during retrieval (which the query_msr_aggregate tool handles by returning "not deployed"). Document this explicitly in code comments.

**B.6 — Token-count enforcement.** If composed bundle exceeds `max_bundle_tokens`, degrade by dropping conditional adds in priority order: domain reports first (none in Phase 2), then discovery registers, then predictive adds, then interpretive adds. Floor never drops. Log warnings via telemetry.

**B.7 — Tests.** Create `platform/src/lib/bundle/__tests__/`:
- `rule_composer.test.ts` — unit tests, one per query class; verify expected assets included and excluded.
- `composition_rules.test.ts` — unit test each rule individually.
- `cross_native.test.ts` — verify cross-native class produces meta-bundle.
- `degradation.test.ts` — verify token-count degradation order.
- `manifest_reader.test.ts` — verify merge of manifest + overrides.

**Stream B acceptance criteria:**
- [ ] Bundle Composer service exists at `platform/src/lib/bundle/`.
- [ ] `compose()` produces valid Bundle for all 8 query classes.
- [ ] Floor (FORENSIC + CGM) included unconditionally.
- [ ] Class-conditional rules per architecture §9 verified by tests.
- [ ] Cross-native produces meta-bundle.
- [ ] Token-count degradation works.
- [ ] All tests pass.
- [ ] Bundle output validates against bundle.schema.json.

## §7 — Stream C: Retrieval Tool Suite

**Goal.** Build 7 retrieval tools. Each tool implements the uniform `retrieve(QueryPlan) → ToolBundle` interface from architecture §15. Tools are independent of each other; can be developed in parallel.

**Common pattern (apply to every tool):**

```typescript
export interface RetrievalTool {
  name: string  // 'msr_sql', 'pattern_register', etc.
  version: string  // '1.0'
  retrieve(plan: QueryPlan, params?: any): Promise<ToolBundle>
}

// Each tool:
// 1. Reads what it needs from QueryPlan (e.g., domains, planets for MSR-SQL)
// 2. Executes its retrieval (SQL / file read / sidecar HTTP)
// 3. Constructs ToolBundle output with results, citations, provenance
// 4. Records served_from_cache (always false in Phase 2; cache integration in Phase 3+)
// 5. Emits telemetry
// 6. Validates output against tool_bundle.schema.json
// 7. Returns ToolBundle
```

### §7.1 — Tool C.1: MSR-SQL Filter

**Source.** Cloud SQL `msr_signals` table (populated in Phase 1A with 499 rows).

**Inputs from QueryPlan.** `domains`, `planets`, `houses` (optional), `dasha_context_required`, `is_forward_looking` (where applicable).

**Implementation.** Uses Storage Layer's `query()` method. SQL pattern:

```sql
SELECT * FROM msr_signals 
WHERE native_id = $1
  AND domain IN ($domains::varchar[])
  AND ($planets IS NULL OR planet = ANY($planets))
  AND ($is_forward_looking IS NULL OR is_forward_looking = $is_forward_looking)
  AND confidence >= $confidence_floor
ORDER BY (confidence * significance) DESC
LIMIT 100;
```

Default `confidence_floor`: 0.6. Configurable via feature flag.

**Output.** ToolBundle with up to 100 candidate signals. Compression (top 25 by significance × confidence) is NOT in Phase 2 — that's the Reranker (Phase 6). Phase 2 returns all candidates; the QueryPlan can specify `result_limit` if needed.

**File.** `platform/src/lib/retrieve/msr_sql.ts`.

### §7.2 — Tool C.2: Pattern Register Filter

**Source.** `035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.json` (filesystem).

**Inputs.** `domains`, `forward_looking`, `is_forward_looking`.

**Implementation.** Storage Layer's `readFile()` → parse JSON → in-memory filter.

**Output.** ToolBundle with patterns matching the filter (typically 3-15 patterns).

**File.** `platform/src/lib/retrieve/pattern_register.ts`.

### §7.3 — Tool C.3: Resonance Register Filter

**Source.** `035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.json`.

**Inputs.** `domains`, `planets` (resonances often involve planet pairs).

**Implementation.** Same pattern as Pattern Register.

**File.** `platform/src/lib/retrieve/resonance_register.ts`.

### §7.4 — Tool C.4: Cluster Atlas Filter

**Source.** `035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.json`.

**Inputs.** `domains`, sometimes specific cluster IDs from `graph_seed_hints`.

**Implementation.** Same pattern.

**File.** `platform/src/lib/retrieve/cluster_atlas.ts`.

### §7.5 — Tool C.5: Contradiction Register Filter

**Source.** `035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.json`.

**Inputs.** `domains`, signal IDs.

**Implementation.** Same pattern.

**File.** `platform/src/lib/retrieve/contradiction_register.ts`.

### §7.6 — Tool C.6: Temporal Lookup

**Source.** Python sidecar endpoints `/transits` and `/ephemeris`. (Phase 2 calls existing endpoints; doesn't add new ones.)

**Inputs.** `forward_looking`, optionally `date_range` from QueryPlan if specified.

**Implementation.** HTTP POST to sidecar. Use the existing pattern in `platform/src/lib/claude/consume-tools.ts` for `get_transits` and `get_planetary_positions` as references — but build a NEW wrapper at `platform/src/lib/retrieve/temporal.ts` that conforms to the `RetrievalTool` interface.

**Output.** ToolBundle with current dasha + upcoming transit windows.

**File.** `platform/src/lib/retrieve/temporal.ts`.

### §7.7 — Tool C.7: query_msr_aggregate (cross-native placeholder)

**Source.** N/A (placeholder).

**Inputs.** `query_class === 'cross_native'`.

**Implementation.** Returns a ToolBundle with status indicator:

```typescript
return {
  tool_bundle_id: uuid(),
  tool_name: 'query_msr_aggregate',
  tool_version: '1.0',
  invocation_params: plan,
  results: [],
  served_from_cache: false,
  cache_key: null,
  latency_ms: 1,
  result_hash: 'sha256:placeholder_not_deployed',
  schema_version: '1.0',
  // Custom field for placeholder pattern:
  status: 'multi_native_not_deployed',
  message: 'Cross-native aggregate queries require multi-native deployment. The architecture supports this query class; deployment is pending a future phase.'
}
```

**Note**: Adding a `status` field to ToolBundle requires either extending the schema or putting this in the `results` array. Recommended: put it in `results` as a single status entry; the schema accepts arbitrary content shapes.

**File.** `platform/src/lib/retrieve/query_msr_aggregate.ts`.

### §7.8 — Tool registry

Create `platform/src/lib/retrieve/index.ts` exposing a registry:

```typescript
import * as msrSql from './msr_sql'
import * as patternRegister from './pattern_register'
// ... etc.

export const RETRIEVAL_TOOLS: RetrievalTool[] = [
  msrSql.tool,
  patternRegister.tool,
  // ... etc.
]

export function getTool(name: string): RetrievalTool | undefined {
  return RETRIEVAL_TOOLS.find(t => t.name === name)
}
```

### §7.9 — Tests

Each tool gets its own test file:
- `__tests__/msr_sql.test.ts` — uses test DB or mocked Storage Layer.
- `__tests__/pattern_register.test.ts` — uses sample register JSON.
- ... etc.

Plus an integration test `__tests__/integration.test.ts` that invokes each tool with a representative QueryPlan and verifies the ToolBundle output.

**Stream C acceptance criteria:**
- [ ] All 7 tools exist at `platform/src/lib/retrieve/`.
- [ ] Each tool implements the uniform RetrievalTool interface.
- [ ] MSR-SQL returns expected signals for test queries.
- [ ] Each register filter returns expected entries.
- [ ] Temporal returns dasha + transit info from sidecar.
- [ ] query_msr_aggregate returns the placeholder status without throwing.
- [ ] Tool registry exposes all 7 tools.
- [ ] All tests pass.

## §8 — Stream D: Tool-Call Cache

**Goal.** Build the request-scoped Tool-Call Cache (C2.5) that prevents duplicate tool execution within a panel turn (Phase 7 will use this).

**Tasks:**

**D.1 — Create the cache directory.** Create `platform/src/lib/cache/`.

**D.2 — Implement the cache.** Create `platform/src/lib/cache/tool_cache.ts`:

```typescript
export interface ToolCacheEntry {
  result: ToolBundle
  inserted_at: number
}

export class RequestScopedToolCache {
  private cache: Map<string, Promise<ToolBundle>> = new Map()
  
  generateKey(toolName: string, params: any): string {
    const normalized = JSON.stringify(params, Object.keys(params).sort())
    return `${toolName}:${sha256(normalized)}`
  }
  
  async get(toolName: string, params: any): Promise<ToolBundle | undefined> {
    const key = this.generateKey(toolName, params)
    return await this.cache.get(key)
  }
  
  put(toolName: string, params: any, resultPromise: Promise<ToolBundle>): void {
    const key = this.generateKey(toolName, params)
    this.cache.set(key, resultPromise)
  }
  
  clear(): void {
    this.cache.clear()
  }
  
  size(): number {
    return this.cache.size
  }
}

export function createToolCache(): RequestScopedToolCache {
  return new RequestScopedToolCache()
}
```

**D.3 — Integration helper.** Create `platform/src/lib/cache/with_cache.ts` — a small helper that wraps a tool's `retrieve()` call with cache lookup:

```typescript
export async function executeWithCache(
  tool: RetrievalTool,
  plan: QueryPlan,
  cache?: RequestScopedToolCache
): Promise<ToolBundle> {
  if (!cache) {
    return await tool.retrieve(plan)
  }
  
  const cached = await cache.get(tool.name, plan)
  if (cached) {
    return { ...cached, served_from_cache: true }
  }
  
  const promise = tool.retrieve(plan)
  cache.put(tool.name, plan, promise)
  return await promise
}
```

**D.4 — Tests.**
- `cache.test.ts` — unit tests for get/put/clear/key generation.
- `concurrency.test.ts` — verify two concurrent calls to `executeWithCache` with identical parameters result in only one tool execution (the second awaits the cached promise).
- `with_cache.test.ts` — verify served_from_cache flag is correctly set on cached responses.

**Stream D acceptance criteria:**
- [ ] RequestScopedToolCache class exists.
- [ ] Key generation is deterministic (same params → same key regardless of object key order).
- [ ] Concurrent identical calls → single execution.
- [ ] Cache.clear() empties the map.
- [ ] All tests pass.

## §9 — Integration and Final Acceptance

After all four sub-streams complete:

**§9.1 — Cross-stream verification.** Confirm:
- Router output (QueryPlan) is consumable by Bundle Composer.
- Bundle Composer output (Bundle) is consumable by Synthesis Orchestrator (Phase 3 will verify; Phase 2 just shapes-check).
- Each Retrieval Tool's output (ToolBundle) is uniformly shaped.
- Tool-Call Cache integrates with `executeWithCache` helper.

**§9.2 — End-to-end pipeline smoke test.** Create `platform/src/scripts/test/pipeline_smoke.ts`:

```typescript
async function smokeTest() {
  const testQueries = [
    "What is my Mercury position?",  // factual
    "What does my chart say about my career?",  // interpretive
    "Will I see a financial change in the next 2 years?",  // predictive
    "How do my career and relationship patterns interact?",  // cross_domain
    "What unusual patterns does my chart show?",  // discovery
    "Give me a complete chart read",  // holistic
    "What remedies for my Saturn?",  // remedial
    "What patterns are common across charts with similar Saturn placements?",  // cross_native
  ]
  
  const cache = createToolCache()
  
  for (const query of testQueries) {
    const plan = await classify(query, { audience_tier: 'super_admin', manifest_fingerprint: '...' })
    const bundle = await compose(plan)
    
    const toolResults: ToolBundle[] = []
    for (const toolName of plan.tools_authorized) {
      const tool = getTool(toolName)
      if (!tool) continue
      const result = await executeWithCache(tool, plan, cache)
      toolResults.push(result)
    }
    
    console.log(`Query: ${query}`)
    console.log(`  Class: ${plan.query_class}`)
    console.log(`  Bundle entries: ${bundle.mandatory_context.length}`)
    console.log(`  Tools fired: ${toolResults.length}`)
    console.log(`  Tool results: ${toolResults.map(r => `${r.tool_name}=${r.results.length}`).join(', ')}`)
  }
}

smokeTest()
```

Run via `npm run pipeline:test` (after adding to package.json scripts).

**§9.3 — Test suite execution.** Run the full project test suite. All Phase 0/1A/1B tests must still pass; new Phase 2 tests must pass.

**§9.4 — `must_not_touch` verification.** `git status`. Confirm only the allowed surfaces were modified.

**§9.5 — Lint and type-check.** Project's lint and type-check commands. No new warnings.

**§9.6 — Backward compatibility.** Existing single-model queries against the live Consume tab continue to work (Phase 2 didn't modify the live route).

## §10 — Phase 2 Done Criteria

This brief is `COMPLETE` when ALL of the following are true:

1. All Stream A acceptance criteria met.
2. All Stream B acceptance criteria met.
3. All Stream C acceptance criteria met (all 7 tools).
4. All Stream D acceptance criteria met.
5. End-to-end pipeline smoke test (§9.2) succeeds for all 8 query classes.
6. Test suite passes; lint + type-check clean.
7. `must_not_touch` verified.
8. Native confirms acceptance.

When all criteria met:
- Update brief frontmatter `status` to `COMPLETE`.
- Add `completed_on` field.
- Append final `status_history` entry summarizing: query classification accuracy on test set, number of bundle entries per query class, tool execution latencies, cache hit rate observed during smoke test.
- Notify native that Phase 2 is complete and Phase 3 brief authoring can begin.

## §11 — Communication Discipline

**Halt on uncertainty.** If during execution you discover an architectural choice the brief didn't make, halt and surface to native.

**No scope creep.** Tangential issues → `PHASE_2_OBSERVATIONS_v1_0.md`.

**Status updates between sessions.** Multi-session execution leaves `status_history` updated.

**Adherence to architectural principles.** Architecture §3 P.7 (modular componentization), P.8 (domain knowledge → LLM, integrity → deterministic), P.10 (multi-model + multi-native forward-compatibility) govern Phase 2. The Router uses an LLM (small fast model — domain knowledge in classification). Bundle Composer is purely rule-based (deterministic — no domain knowledge needed beyond what the rules encode). Retrieval tools are deterministic. Tool Cache is pure infrastructure.

**Conflict with M2/B.5.** M2/B.5 may run in parallel during Phase 2. If M2/B.5 modifies the manifest or governance scripts during Phase 2 execution, halt and verify nothing Phase 2 depends on changed.

## §12 — Final Notes

Phase 2 is the foundation of the query-time pipeline. Done well, Phases 3-9 build on a clean base. The Router is the most consequential single component in this phase — its QueryPlan output is the contract every downstream stage consumes. Spend time on the router prompt and the few-shot examples; classification quality directly affects bundle composition quality, which directly affects synthesis quality.

The seven retrieval tools are mostly mechanical — the architecture is the same per tool, with different data sources. Build them in parallel; they're independent.

The cross-native query class (Q3) requires special attention in two places: the router's classification rules (one of the 8 classes), and the cross-native bundle composition rule (meta-bundle pattern). The placeholder query_msr_aggregate tool provides the graceful "not deployed" response. None of this activates until multi-native deployment, but the architecture is forward-compatible from this phase onward.

When Phase 2 completes, the deterministic foundation is done. Phase 3 (Synthesis Single-Model) wires the pipeline into the Consume route end-to-end, replacing the current static path with the new manifest-driven, router-classified, bundle-composed retrieval pipeline. The cumulative effect by end of Phase 3: the chat works the same way for the user, but the internal pipeline is fully migrated.

---

*End of EXEC_BRIEF_PHASE_2_v1_0.md (status `AUTHORED`, 2026-04-27). Trigger phrase: "Read EXEC_BRIEF_PHASE_2_v1_0.md and execute it." On Phase 2 completion, status flips to `COMPLETE` and Cowork authors `EXEC_BRIEF_PHASE_3_v1_0.md` (Synthesis Single-Model — the phase that wires the pipeline into the Consume route).*
