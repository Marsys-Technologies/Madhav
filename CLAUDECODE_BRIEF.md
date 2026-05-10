---
artifact: CLAUDECODE_BRIEF.md
status: COMPLETE
session_id: Pipeline-Transform-S1
phase: Pipeline-Transformation-Phases-2-3-4
executor: claude-code-extension (anti-gravity VS Code)
authored_by: Cowork (Abhisek session 2026-05-11)
authored_on: 2026-05-11
acceptance_criteria_count: 24
supersedes: GANGA-MOPUP-S1 (PARTIAL_COMPLETE 2026-05-07)
---

# MARSYS-JIS Pipeline Transformation — Phases 2, 3, 4

## §0 — HOW TO READ THIS BRIEF

This file is the governing scope for this Claude Code session. Read it in full
before touching any file. Every code change, every deletion, every flag removal
must be traceable to an acceptance criterion (AC) listed in §6.

When ALL 24 acceptance criteria are GREEN, set `status: COMPLETE` in this
file's frontmatter and stop.

Do not emit SESSION_OPEN or SESSION_CLOSE artifacts. No governance handshake
is required for this headless execution session.

---

## §1 — CONTEXT (read, do not re-derive)

**Phase 1 is COMPLETE (2026-05-11).** Two files were delivered by a Cowork session:

1. `platform/src/lib/pipeline/types.ts` — **PipelinePlan** Zod schema.
   Single authoritative contract for the pipeline. Contains:
   - `QueryClassEnum` — unified 8-class enum
     (`factual|interpretive|predictive|cross_domain|discovery|holistic|remedial|cross_native`)
   - `AssetBundleItemSchema` — per-document spec (asset_id, priority, reason)
   - `ToolCallItemSchema` — retrieval tool call spec
   - `PipelinePlanSchema` — the full Zod schema (all fields labelled PLANNER OUTPUT
     or ROUTE STAMP)
   - `PipelinePlanInputJsonSchema` — hand-crafted JSONSchema7 for NIM compatibility
   - `PipelinePlannerError` — no-silent-fallback error class

2. `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` — Updated planner prompt v2.0.
   8-class enum (was 6), `asset_bundle[]` output (new), `synthesis_guidance` output
   (new), rules R1–R20 preserved, rules R21–R26 added, 11 few-shots, 6-criterion rubric.

The structural problems being solved in Phases 2–4:

- **P1** `classify()` runs unconditionally — 2nd LLM call even when planner succeeds
- **P2** PlanSchema (6-class) + QueryPlan (8-class) merged at runtime in route.ts
- **P3** Circuit breaker swallows planner failures → silent fallback, no audit trail
- **P4** `rule_composer.compose()` runs regardless of planner output
- **P5** Four planner variants exist; only one (manifest_planner) is wired
- **P6/P8** 6-class vs 8-class query_class enum produces incoherent merged output
- **P7** `context_assembler.ts` adds a hidden 3rd LLM pre-synthesis call

**Target after Phase 4:** Exactly **2 LLM calls per request** (planner + synthesis).
Zero silent fallbacks. One schema (PipelinePlan). One linear pipeline path.

---

## §2 — MANDATORY READING BEFORE WRITING ANY CODE

Read these files in order before touching anything. Do not skip any.

```
platform/src/lib/pipeline/types.ts                         (Phase 1 — your new contract)
platform/src/lib/pipeline/manifest_planner.ts              (rename target → pipeline_planner.ts)
platform/src/lib/pipeline/planner_context_builder.ts       (keep as-is)
platform/src/lib/pipeline/budget_arbiter.ts                (keep as-is)
platform/src/lib/pipeline/planner_circuit_breaker.ts       (DELETE in Phase 4)
platform/src/lib/bundle/rule_composer.ts                   (DELETE in Phase 4)
platform/src/lib/bundle/composition_rules.ts               (DELETE in Phase 4)
platform/src/lib/bundle/manifest_reader.ts                 (keep as-is)
platform/src/lib/router/router.ts                          (DELETE in Phase 4)
platform/src/lib/router/prompt.ts                          (DELETE in Phase 4)
platform/src/lib/router/planner.ts                         (DELETE in Phase 4 — orphaned)
platform/src/lib/synthesis/context_assembler.ts            (DELETE in Phase 4)
platform/src/lib/synthesis/single_model_strategy.ts        (read to understand synthesize() signature)
platform/src/lib/synthesis/index.ts                        (read createOrchestrator() signature)
platform/src/lib/config/feature_flags.ts                   (prune in Phase 4)
platform/src/app/api/chat/consume/route.ts                 (REWRITE in Phase 3)
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                   (read artifacts[] for asset_id→path mapping)
00_ARCHITECTURE/GCS_LAYOUT_v1_0.md                         (read before implementing bundle_hydrator)
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md                     (Phase 1 output — new prompt path)
```

Also run this before starting — get the full import dependency graph:
```bash
cd platform && grep -r "manifest_planner\|PlanSchema\|PlannerError\|rule_composer\|compose\b\|classify\b\|plannerCircuit\|contextAssembler\|CONTEXT_ASSEMBLY\|LLM_FIRST_PLANNER" src --include="*.ts" -l
```

---

## §3 — PHASE 2: Create pipeline_planner.ts + bundle_hydrator.ts

### 3A. Create pipeline_planner.ts (rename + rewire of manifest_planner.ts)

Copy `platform/src/lib/pipeline/manifest_planner.ts` to
`platform/src/lib/pipeline/pipeline_planner.ts`.
Apply the following surgical changes to the NEW file only. Do NOT delete
manifest_planner.ts yet (that happens in Phase 4).

**Change 1 — Add import from ./types at the top:**
```ts
import {
  PipelinePlanSchema,
  PipelinePlanInputJsonSchema,
  PipelinePlannerError,
  type PipelinePlan,
} from './types'
```

**Change 2 — Remove legacy type declarations** (no longer needed; now in types.ts):
Delete the following from the new file:
- `export interface PlanSchema { ... }` block
- `export class PlannerError extends Error { ... }` block
- `export const PlanSchemaZod = z.object({ ... })` block
- `const PlanInputJsonSchema: JSONSchema7 = { ... }` block
Remove `import type { JSONSchema7 } from 'json-schema'` if it's now unused.

**Change 3 — Update prompt file path** in `getSystemPrompt()`:
Change `'PLANNER_PROMPT_v1_0.md'` → `'PLANNER_PROMPT_v2_0.md'`

**Change 4 — Rename public entrypoint:**
Rename `export async function callLlmPlanner(` → `export async function callPipelinePlanner(`
Update return type: `Promise<PlanSchema>` → `Promise<PipelinePlan>`

**Change 5 — Swap Zod schema in safeParse:**
Replace `PlanSchemaZod.safeParse(submitCall.input)` → `PipelinePlanSchema.safeParse(submitCall.input)`

**Change 6 — Swap JSON schema in tool() call:**
Replace `jsonSchema<PlanSchema>(PlanInputJsonSchema)` → `jsonSchema<PipelinePlan>(PipelinePlanInputJsonSchema)`

**Change 7 — Swap error class:**
Replace every `throw new PlannerError(` → `throw new PipelinePlannerError(`
Replace every `new PlannerError(` → `new PipelinePlannerError(`

**Change 8 — Fix typed references to parsed.data:**
`parsed.data` is now typed as `PipelinePlan`. Any trace payload that references
`parsed.data.query_class` or `parsed.data.tool_calls` continues to work because
PipelinePlan has both fields. No logic changes needed — just verify no type errors.

**Change 9 — Keep unchanged:** All retry logic, telemetry, observatory observability,
`writeLlmCallLog`, `writePlanAlternatives`, `buildPlannerContext`, manifest loading,
`googleProviderOptions` spread, `maxTokens: 2048`. These are correct.

**Change 10 — Add backward-compat aliases at the bottom** (removed in Phase 4):
```ts
// Backward-compat — route.ts still references callLlmPlanner until Phase 3.
// DELETE these three lines in Phase 4 Step 5C.
export { callPipelinePlanner as callLlmPlanner }
export { PipelinePlannerError as PlannerError }
export type { PipelinePlan as PlanSchema }
```

**AC-P2-1:** `pipeline_planner.ts` exists; exports `callPipelinePlanner` returning
`Promise<PipelinePlan>`; `npx tsc --noEmit` in platform/ produces zero new errors
in `src/` non-test files compared to the pre-Phase-2 baseline.

---

### 3B. Create bundle_hydrator.ts

Create `platform/src/lib/bundle/bundle_hydrator.ts`.

**Before writing a single line, read:**
1. `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md` — understand the L1/, L2_5/, L3/ prefix scheme
2. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — find the `artifacts` array; each entry
   has at minimum `canonical_id` and `path`. Determine whether there is also a
   `gcs_path` field or whether you derive the GCS URI from `path` + layout rules.
3. `platform/src/lib/bundle/manifest_reader.ts` — understand what type `loadManifest()`
   returns. Use the exact same type in bundle_hydrator.
4. `platform/src/lib/storage/index.ts` (or wherever `getStorageClient` is exported) —
   understand the read API. Use the identical pattern used in `manifest_planner.ts`
   or `manifest_reader.ts` for GCS reads.
5. `platform/src/lib/synthesis/single_model_strategy.ts` (search for `bundle.mandatory_context`)
   — understand the exact shape of `mandatory_context` items that `synthesize()` expects.
   The `HydratedBundle` you return MUST have a `mandatory_context` field that matches
   this shape, so Phase 3 can pass `bundle` directly to `orchestrator.synthesize()`.
6. `platform/src/lib/bundle/rule_composer.ts` — understand the shape of what `compose()`
   currently returns. Your `HydratedBundle` must be assignment-compatible with the
   `bundle` type that `synthesize()` accepts.

**Implementation:**

```ts
// platform/src/lib/bundle/bundle_hydrator.ts
//
// Resolves plan.asset_bundle[] to canonical document content for the synthesis
// context window. Replaces rule_composer.ts + composition_rules.ts (deleted Phase 4).
//
// Floor assets FORENSIC and CGM are enforced even if absent from plan.asset_bundle.
// A non-floor asset that fails to load is skipped with a warning.
// A floor asset that fails to load throws (fatal).
```

The exported interface:
```ts
export interface HydratedAsset {
  asset_id: string
  content: string
  priority: 1 | 2 | 3
  byte_count: number
}

export interface HydratedBundle {
  assets: HydratedAsset[]
  total_bytes: number
  floor_enforced: boolean
  // mandatory_context must match the shape synthesize() expects for bundle.mandatory_context.
  // Read single_model_strategy.ts to get the exact type before declaring this.
  mandatory_context: <exact type from single_model_strategy.ts>
}

export async function hydrateBundle(
  plan: PipelinePlan,
  manifest: <type returned by loadManifest()>,
): Promise<HydratedBundle>
```

**Floor asset IDs:** `['FORENSIC', 'CGM']`

**hydrateBundle algorithm:**
1. Build effective asset list from `plan.asset_bundle ?? []`
2. For each floor asset ID: if absent from list, prepend `{ asset_id, priority: 1, reason: 'floor asset enforced by hydrator' }`; set `floor_enforced = true`
3. Sort by priority ascending (p1 first)
4. For each item in effective list:
   a. Find manifest entry where `canonical_id === item.asset_id`
   b. If not found: warn + skip (do NOT throw for non-floor)
   c. Derive GCS path from manifest entry (read GCS_LAYOUT first)
   d. Fetch content using getStorageClient()
   e. If floor asset fetch fails: throw; if non-floor: warn + skip
5. Build `mandatory_context` from fetched assets (match `rule_composer` output shape)
6. Return HydratedBundle

**AC-P2-2:** `bundle_hydrator.ts` exists; exports `hydrateBundle`; zero new TS errors in src/.

**AC-P2-3:** Unit test at `platform/src/__tests__/lib/bundle/bundle_hydrator.test.ts`:
- Floor enforcement: plan with empty asset_bundle → FORENSIC + CGM added, floor_enforced=true
- Unknown asset_id: warn logged, asset skipped, no throw
- HydratedBundle.mandatory_context is array and length equals number of successfully loaded assets
All tests pass.

---

## §4 — PHASE 3: route.ts single-path rewrite

**Read the full current route.ts before writing a single line.**

This phase rewrites `platform/src/app/api/chat/consume/route.ts` to use one
linear path: planner → hydrate → retrieve → synthesize. Zero flags, zero
circuit breaker, zero context assembler, zero classify().

### 4A. Import changes at top of route.ts

**REMOVE these imports** (all come from files being deleted in Phase 4):
```ts
import { classify } from '@/lib/router/router'
import { callLlmPlanner, PlannerError, type PlanSchema } from '@/lib/pipeline/manifest_planner'
import { plannerCircuit, PlannerCircuitOpenError } from '@/lib/pipeline/planner_circuit_breaker'
import { compose } from '@/lib/bundle/rule_composer'
import {
  contextAssembler,
  CONTEXT_ASSEMBLY_TOKEN_THRESHOLD,
  estimateBundleTokens,
} from '@/lib/synthesis/context_assembler'
import type { ContextBundle } from '@/lib/synthesis/types'
```

**ADD these imports:**
```ts
import { callPipelinePlanner, PipelinePlannerError } from '@/lib/pipeline/pipeline_planner'
import { hydrateBundle } from '@/lib/bundle/bundle_hydrator'
import type { PipelinePlan } from '@/lib/pipeline/types'
```

Also remove `writeContextAssemblyLog` from the monitoring-write import **only if**
it is not referenced anywhere outside the context_assembler block being deleted.
Check with grep first.

**Keep all other imports unchanged.**

### 4B. Replace the dual-planning block with a single planner call

The block to replace starts approximately at:
```ts
const plannerHistory = messages ...
const preAllocatedQueryId = crypto.randomUUID()
let planSchema: PlanSchema | null = null
...
if (configService.getFlag('LLM_FIRST_PLANNER_ENABLED')) {
```
and ends approximately at:
```ts
const plannerParamsMap = new Map<string, Record<string, unknown>>(
  planSchema?.tool_calls.map(tc => [tc.tool_name, tc.params]) ?? []
)
```

**IMPORTANT: Declare `let stepSeq = 0` and `const nextSeq = () => ++stepSeq`
BEFORE this block, exactly as they currently exist. Do not move them.**

Replace the entire dual-planning block with:

```ts
// ── Single-path LLM-first planner ─────────────────────────────────────────
// No flag guard. No circuit breaker. No classify() fallback.
// PipelinePlannerError → HTTP 422 (caller must retry or degrade gracefully).
const plannerHistory = messages
  .filter(m => m.role === 'user' || m.role === 'assistant')
  .slice(-2)
  .map(m => ({
    role: m.role as 'user' | 'assistant',
    content: extractText(m.parts ?? []),
  }))
  .filter(m => m.content.length > 0)

const preAllocatedQueryId = crypto.randomUUID()
const plannerModelId = STACK_ROUTING[selectedStack].planner_fast.primary
const plannerFallbackModelId = STACK_ROUTING[selectedStack].planner_fast.fallback
const plannerStartedAt = Date.now()

let plan: PipelinePlan
try {
  plan = await callPipelinePlanner(
    queryText,
    plannerHistory,
    plannerModelId,
    chartId,
    (event) => traceEmitter.emitStep(event),
    preAllocatedQueryId,
    plannerFallbackModelId,
  )
} catch (err) {
  if (err instanceof PipelinePlannerError) {
    return NextResponse.json(
      { error: 'planner_failed', message: err.message },
      { status: 422 }
    )
  }
  throw err
}
const plannerLatencyMs = Date.now() - plannerStartedAt

// Stamp route-controlled fields — never LLM output
plan.query_plan_id = preAllocatedQueryId
plan.query_text = queryText
plan.audience_tier = isSuperAdmin ? 'super_admin' : 'client'
plan.manifest_fingerprint = manifest.fingerprint
plan.schema_version = '2.0'
plan.planning_model_id = plannerModelId
plan.planning_latency_ms = plannerLatencyMs

const queryId = preAllocatedQueryId

// Budget arbitration
const arbitrated = arbitrateBudgets(
  plan.tool_calls.map(tc => ({
    tool_name: tc.tool_name,
    priority: tc.priority,
    token_budget: tc.token_budget,
  })),
  {
    synthesis_model_max_context: modelMeta.maxInputTokens ?? 128_000,
    system_prompt_reserve: 800,
    synthesis_guidance_reserve: plan.synthesis_guidance ? 200 : 0,
    safety_margin: 0.85,
    min_tokens_per_tool: 200,
  },
)
for (let i = 0; i < plan.tool_calls.length; i++) {
  plan.tool_calls[i].token_budget = arbitrated[i].token_budget
}

// Derive toolsAuthorized from plan (replaces queryPlan.tools_authorized)
const toolsAuthorized = Array.from(new Set(plan.tool_calls.map(tc => tc.tool_name)))

// B.11 Whole-Chart-Read enforcement — at least one L2.5 tool required
const L2_5_TOOLS = ['msr_sql', 'query_msr_aggregate', 'pattern_register',
  'resonance_register', 'cluster_atlas', 'contradiction_register', 'cgm_graph_walk']
if (!toolsAuthorized.some(t => L2_5_TOOLS.includes(t))) {
  plan.tool_calls.push(
    { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1, reason: 'B.11 floor enforcement' },
    { tool_name: 'cgm_graph_walk', params: {}, token_budget: 400, priority: 2, reason: 'B.11 floor enforcement' },
  )
  toolsAuthorized.push('msr_sql', 'cgm_graph_walk')
  console.log('[consume:v3] B.11 enforcement: added msr_sql + cgm_graph_walk')
}

// Audit log
void writeQueryPlanLog({
  query_id: queryId,
  conversation_id: finalConversationId ?? null,
  chart_id: chartId ?? null,
  planner_model_id: plannerModelId,
  query_text: queryText,
  query_class: plan.query_class,
  tool_count: plan.tool_calls.length,
  plan_json: plan as unknown as Record<string, unknown>,
  parsing_success: true,
  parse_error: null,
  fallback_used: false,
  planner_latency_ms: plannerLatencyMs,
})

// Emit plan step (step_name: 'classify' preserved for trace UI backward compat)
const classifyStart = plannerStartedAt
traceEmitter.emitStep({
  event: 'step_done',
  query_id: queryId,
  step: {
    query_id: queryId,
    conversation_id: finalConversationId,
    step_seq: nextSeq(),
    step_name: 'classify',
    step_type: 'llm',
    status: 'done',
    started_at: new Date(classifyStart).toISOString(),
    completed_at: new Date().toISOString(),
    latency_ms: plannerLatencyMs,
    data_summary: {
      result: plan.query_class,
      query_class: plan.query_class,
      confidence: 1.0,
      planning_confidence: 1.0,
    },
    payload: {
      query_plan: {
        query_class: plan.query_class,
        tools_authorized: toolsAuthorized,
        tool_calls: plan.tool_calls,
        query_intent_summary: plan.query_intent_summary,
        synthesis_guidance: plan.synthesis_guidance,
        planning_model_id: plan.planning_model_id,
        planning_latency_ms: plan.planning_latency_ms,
      },
      tool_calls: plan.tool_calls,
    },
  },
})

// Planner params map for retrieval layer
const plannerParamsMap = new Map<string, Record<string, unknown>>(
  plan.tool_calls.map(tc => [tc.tool_name, tc.params])
)
```

### 4C. Replace compose() with hydrateBundle()

Replace:
```ts
const composeStart = Date.now()
const bundle = await compose(queryPlan)
traceEmitter.emitStep({ ... step_name: 'compose_bundle' ... })
```

with:
```ts
const composeStart = Date.now()
const bundle = await hydrateBundle(plan, manifest)
traceEmitter.emitStep({
  event: 'step_done',
  query_id: queryId,
  step: {
    query_id: queryId,
    conversation_id: finalConversationId,
    step_seq: nextSeq(),
    step_name: 'compose_bundle',
    step_type: 'deterministic',
    status: 'done',
    started_at: new Date(composeStart).toISOString(),
    completed_at: new Date().toISOString(),
    latency_ms: Date.now() - composeStart,
    data_summary: {
      result: `${bundle.assets.length} assets · ${toolsAuthorized.length} tools`,
      floor_enforced: bundle.floor_enforced,
    },
    payload: {},
  },
})
```

### 4D. Update tool execution loop

The loop currently reads `queryPlan.tools_authorized`. Replace every
`queryPlan.tools_authorized` reference in the loop with `toolsAuthorized`.

The `executeWithCache(t, queryPlan, cache, plannerParamsMap.get(toolName))`
call currently passes `queryPlan` as the second argument. Before replacing it
with `plan`, read `platform/src/lib/retrieve/index.ts` and at least two
retrieval tools to understand which fields the second argument provides. If
any field present on `QueryPlan` is missing from `PipelinePlan`, add it to
`PipelinePlan` in types.ts before proceeding (do not break retrieval tools).
Replace `queryPlan` → `plan` in the executeWithCache call once confirmed safe.

### 4E. Update bundle validation call

Replace `runAll(bundle, 'bundle', { query_plan: queryPlan, ... })` with
`runAll(bundle, 'bundle', { query_plan: plan, ... })`.

### 4F. Remove the context_assembler block

Remove the entire block:
```ts
const effectiveContextAssembly =
  configService.getFlag('CONTEXT_ASSEMBLY_ENABLED') && selectedStack !== 'nim'
let assembledBundle: ContextBundle | null = null
let synthesisToolResults: ToolBundle[] = validToolResults
const totalToolTokens = estimateBundleTokens(validToolResults)
const belowThreshold = totalToolTokens < CONTEXT_ASSEMBLY_TOKEN_THRESHOLD
if (effectiveContextAssembly && !belowThreshold) {
  ...
  assembledBundle = await contextAssembler(...)
  synthesisToolResults = assembledBundle.tool_bundles
} else if (effectiveContextAssembly && belowThreshold) {
  ...
}
```

Replace with:
```ts
const synthesisToolResults = validToolResults
```

(No context assembly. synthesis_guidance from the plan serves this role.)

### 4G. Update synthesis orchestrator call

Replace `query_plan: queryPlan` → `query_plan: plan` in `orchestrator.synthesize(...)`.

For `synthesis_guidance`: read whether `orchestrator.synthesize()` has a
`synthesis_guidance` parameter. If yes, add `synthesis_guidance: plan.synthesis_guidance`.
If no, append `plan.synthesis_guidance` to the system prompt inside
`consumeSystemPrompt(...)` or pass it as a new field. The simplest approach:
if the synthesize() signature does not support it, add `synthesis_guidance?:
string` to the synthesize() input type in `platform/src/lib/synthesis/index.ts`
and thread it through to `single_model_strategy.ts` where the system prompt is
assembled. Then append it as a separator + guidance block:
```ts
const guidance = plan.synthesis_guidance
  ? `\n\n---\n\nSYNTHESIS GUIDANCE (from planner):\n${plan.synthesis_guidance}`
  : ''
// append `guidance` to the system prompt string
```

### 4H. Update audit consumer

Replace `query_plan: queryPlan` → `query_plan: plan` in `createAuditConsumer({...})`.

Also replace `bundle` in the audit consumer call if it references the old bundle
shape — use the HydratedBundle from Phase 2.

### 4I. Update citation gate

Replace `queryPlan.query_class` → `plan.query_class` in `validateCitations(...)`.
Replace `assembledBundle?.tool_bundles ?? validToolResults` → `validToolResults`
(no more assembledBundle). Replace `bundle` if it's referenced — use HydratedBundle.

### 4J. Update message metadata

In `toUIMessageStreamResponse → messageMetadata`:
- `planner_active: planSchema !== null && !plannerFallbackUsed` → `planner_active: true`
- `planning_model_id: plannerModelIdUsed ?? null` → `planning_model_id: plannerModelId`
- `planning_latency_ms: plannerLatencyMs ?? null` → `planning_latency_ms: plannerLatencyMs`
- Remove `context_assembler_model_id` and `context_assembler_latency_ms` from the
  metadata object (or set to null if the client reads them).

### 4K. Pre-allocate seq numbers correctly

Read the current UQE-9 comment in route.ts. The old code pre-allocated
`contextAssemblySeq` and `synthesisSeq`. After removing context assembly:
- Remove `contextAssemblySeq` pre-allocation
- Keep `synthesisSeq` pre-allocation for the synthesis step
- Update `orchestrator.synthesize({ context_assembly_seq, synthesis_seq, ... })` —
  remove `context_assembly_seq` if it's only used by the assembler.
  Keep `synthesis_seq`.

**AC-P3-1:** `npx tsc --noEmit` — zero errors in src/ non-test files.

**AC-P3-2:** `npm run build` from `platform/` completes without errors.
(If build requires env vars, use: `SKIP_ENV_VALIDATION=1 npm run build`)

**AC-P3-3:** `head -100 platform/src/app/api/chat/consume/route.ts | grep "from "` —
zero imports from `router/router`, `manifest_planner`, `planner_circuit_breaker`,
`rule_composer`, or `context_assembler`.

**AC-P3-4:** `grep -c "classify(\|plannerCircuit\|compose(\|contextAssembler(\|LLM_FIRST_PLANNER_ENABLED\|CONTEXT_ASSEMBLY_ENABLED\|PlanSchema\|PlannerError\b" platform/src/app/api/chat/consume/route.ts`
returns 0.

**AC-P3-5:** `stepSeq` and `nextSeq` declared before the planner block; all trace
steps use `nextSeq()`.

**AC-P3-6:** route.ts calls `callPipelinePlanner()` with no fallback;
`PipelinePlannerError` catches → `NextResponse.json({ error: 'planner_failed' }, { status: 422 })`.

**AC-P3-7:** `compose(` absent from route.ts; `hydrateBundle(plan, manifest)` present.

**AC-P3-8:** `plan.synthesis_guidance` is threaded to the synthesis orchestrator
(either as a named param or appended to the system prompt).

**AC-P3-9:** Tool execution loop reads `toolsAuthorized` (derived from plan.tool_calls).

**AC-P3-10:** `grep "slice(-5)" platform/src/app/api/chat/consume/route.ts` returns
the synthesis history window line (unchanged — 2-turn window preserved).

---

## §5 — PHASE 4: Delete legacy files + prune flags

Do Phase 4 **only after AC-P3-1 and AC-P3-2 are GREEN.**

### 5A. Verify zero consumers before each deletion

For each file target, run:
```bash
grep -r "<basename_without_extension>" platform/src --include="*.ts" -l
```
If any remaining file imports the target, fix that import first. Only delete
after confirming zero remaining consumers.

### 5B. DELETE these files

```
platform/src/lib/router/router.ts
platform/src/lib/router/prompt.ts
platform/src/lib/router/planner.ts          (orphaned — was never wired into route.ts)
platform/src/lib/pipeline/planner_circuit_breaker.ts
platform/src/lib/pipeline/manifest_planner.ts
platform/src/lib/bundle/rule_composer.ts
platform/src/lib/bundle/composition_rules.ts
platform/src/lib/synthesis/context_assembler.ts
```

Also check and delete if no non-route consumers remain:
```
platform/src/lib/router/errors.ts           (only used by router.ts)
platform/src/lib/pipeline/per_tool_planner.ts
```

For `platform/src/lib/pipeline/universal_query_engine.ts`: if it contains
algorithmic logic worth preserving, move to `99_ARCHIVE/`; otherwise delete.

### 5C. Remove backward-compat aliases from pipeline_planner.ts

Remove these three lines added in Phase 2, Step 10:
```ts
export { callPipelinePlanner as callLlmPlanner }
export { PipelinePlannerError as PlannerError }
export type { PipelinePlan as PlanSchema }
```

### 5D. Prune feature_flags.ts

In `platform/src/lib/config/feature_flags.ts`, remove:
- `LLM_FIRST_PLANNER_ENABLED` from the flag union type and from `DEFAULT_FLAGS`
- `CONTEXT_ASSEMBLY_ENABLED` from the flag union type and from `DEFAULT_FLAGS`

### 5E. Prune registry.ts

In `platform/src/lib/models/registry.ts`: remove `context_assembly` from
`STACK_ROUTING` **only if** it is not referenced anywhere outside the deleted
files. Check with grep first. If any remaining file reads
`STACK_ROUTING[stack].context_assembly`, leave it.

### 5F. Update PLANNER_PROMPT_v1_0.md

Edit `00_ARCHITECTURE/PLANNER_PROMPT_v1_0.md` frontmatter:
```yaml
status: SUPERSEDED
superseded_by: PLANNER_PROMPT_v2_0.md
superseded_on: 2026-05-11
```

### 5G. Update CAPABILITY_MANIFEST.json

If `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` references `manifest_planner.ts`
anywhere, update it to `pipeline_planner.ts`.

### 5H. Remove @deprecated aliases from types.ts

Remove from the bottom of `platform/src/lib/pipeline/types.ts`:
```ts
/** @deprecated Use PipelinePlan. */
export type UnifiedQueryPlan = PipelinePlan
/** @deprecated Use PipelinePlannerError. */
export { PipelinePlannerError as UnifiedPlannerError }
```

**AC-P4-1:** `npx tsc --noEmit` — zero errors in src/ non-test files post-deletion.

**AC-P4-2:** `npm run build` — completes post-deletion.

**AC-P4-3:** `grep -r "router/router\|manifest_planner\|planner_circuit_breaker\|rule_composer\|composition_rules\|context_assembler\|router/planner\|router/prompt" platform/src --include="*.ts"` returns empty.

**AC-P4-4:** `grep -r "LLM_FIRST_PLANNER_ENABLED\|CONTEXT_ASSEMBLY_ENABLED" platform/src --include="*.ts"` returns empty.

**AC-P4-5:** `grep "PLANNER_PROMPT" platform/src/lib/pipeline/pipeline_planner.ts` shows `v2_0` only.

**AC-P4-6:** `grep "status:" 00_ARCHITECTURE/PLANNER_PROMPT_v1_0.md` shows `SUPERSEDED`.

**AC-P4-7:** Backward-compat aliases absent from `pipeline_planner.ts`.

**AC-P4-8:** `@deprecated` aliases absent from `types.ts`.

---

## §6 — ACCEPTANCE CRITERIA (complete checklist — 24 items)

Mark each PASS or FAIL. All 24 must be PASS before claiming session complete.

### Phase 2 (3 criteria)
- [ ] **AC-P2-1** `pipeline_planner.ts` exists; exports `callPipelinePlanner` returning `Promise<PipelinePlan>`; zero new TS errors in src/ vs pre-Phase-2 baseline
- [ ] **AC-P2-2** `bundle_hydrator.ts` exists; exports `hydrateBundle`; zero new TS errors in src/
- [ ] **AC-P2-3** `bundle_hydrator.test.ts`: floor enforcement + unknown-asset-skip + shape check — all pass

### Phase 3 (10 criteria)
- [ ] **AC-P3-1** `npx tsc --noEmit` — zero errors in src/ non-test files
- [ ] **AC-P3-2** `npm run build` — completes without errors
- [ ] **AC-P3-3** route.ts imports: no `router/router`, `manifest_planner`, `planner_circuit_breaker`, `rule_composer`, `context_assembler`
- [ ] **AC-P3-4** route.ts grep: zero occurrences of `classify(`, `plannerCircuit`, `compose(`, `contextAssembler(`, `LLM_FIRST_PLANNER_ENABLED`, `CONTEXT_ASSEMBLY_ENABLED`, `PlanSchema`
- [ ] **AC-P3-5** `stepSeq`/`nextSeq` declared before planner block; all trace steps use `nextSeq()`
- [ ] **AC-P3-6** `PipelinePlannerError` → HTTP 422; no silent fallback
- [ ] **AC-P3-7** `hydrateBundle(plan, manifest)` called where `compose(queryPlan)` was
- [ ] **AC-P3-8** `plan.synthesis_guidance` threaded to synthesis orchestrator
- [ ] **AC-P3-9** Tool loop reads `toolsAuthorized` (from `plan.tool_calls`)
- [ ] **AC-P3-10** Synthesis history: `.slice(-5).slice(0,-1)` unchanged (2-turn window)

### Phase 4 (8 criteria)
- [ ] **AC-P4-1** `npx tsc --noEmit` — zero errors in src/ post-deletion
- [ ] **AC-P4-2** `npm run build` — completes post-deletion
- [ ] **AC-P4-3** No deleted file appears in any remaining import
- [ ] **AC-P4-4** `LLM_FIRST_PLANNER_ENABLED` and `CONTEXT_ASSEMBLY_ENABLED` absent from all src/
- [ ] **AC-P4-5** `pipeline_planner.ts` reads `PLANNER_PROMPT_v2_0.md` only
- [ ] **AC-P4-6** `PLANNER_PROMPT_v1_0.md` has `status: SUPERSEDED`
- [ ] **AC-P4-7** Backward-compat aliases removed from `pipeline_planner.ts`
- [ ] **AC-P4-8** `@deprecated` aliases removed from `types.ts`

### LLM call count invariant (primary goal — 3 criteria)
- [ ] **AC-INV-1** `grep -c "await generate" platform/src/app/api/chat/consume/route.ts` returns **0** — route.ts makes zero direct LLM calls; both are inside `pipeline_planner.ts` and the synthesis orchestrator
- [ ] **AC-INV-2** `grep -c "callPipelinePlanner\|synthesize(" platform/src/app/api/chat/consume/route.ts` returns **2** exactly — one planner call, one synthesis call
- [ ] **AC-INV-3** No `configService.getFlag(` call in route.ts refers to `LLM_FIRST_PLANNER_ENABLED` or `CONTEXT_ASSEMBLY_ENABLED`

---

## §7 — MAY TOUCH / MUST NOT TOUCH

### may_touch
```
platform/src/lib/pipeline/manifest_planner.ts        (source for copy — do not modify)
platform/src/lib/pipeline/pipeline_planner.ts         (CREATE Phase 2)
platform/src/lib/pipeline/types.ts                    (minor field additions only if retrieval tools need them)
platform/src/lib/bundle/bundle_hydrator.ts            (CREATE Phase 2)
platform/src/lib/bundle/rule_composer.ts              (DELETE Phase 4)
platform/src/lib/bundle/composition_rules.ts          (DELETE Phase 4)
platform/src/lib/router/router.ts                     (DELETE Phase 4)
platform/src/lib/router/prompt.ts                     (DELETE Phase 4)
platform/src/lib/router/planner.ts                    (DELETE Phase 4)
platform/src/lib/router/errors.ts                     (DELETE Phase 4 if no other consumers)
platform/src/lib/pipeline/planner_circuit_breaker.ts  (DELETE Phase 4)
platform/src/lib/synthesis/context_assembler.ts       (DELETE Phase 4)
platform/src/lib/pipeline/per_tool_planner.ts         (DELETE Phase 4 if no other consumers)
platform/src/lib/pipeline/universal_query_engine.ts   (move/delete Phase 4)
platform/src/lib/config/feature_flags.ts              (prune Phase 4)
platform/src/lib/models/registry.ts                   (remove context_assembly slot Phase 4 — if safe)
platform/src/app/api/chat/consume/route.ts            (REWRITE Phase 3)
platform/src/lib/synthesis/index.ts                   (add synthesis_guidance param if needed Phase 3)
00_ARCHITECTURE/PLANNER_PROMPT_v1_0.md                (frontmatter status update only)
00_ARCHITECTURE/CAPABILITY_MANIFEST.json              (manifest_planner reference update only)
platform/src/__tests__/lib/bundle/bundle_hydrator.test.ts  (CREATE Phase 2)
```

### must_not_touch
```
platform/src/lib/pipeline/planner_context_builder.ts  (correct — keep as-is)
platform/src/lib/pipeline/budget_arbiter.ts            (correct — keep as-is)
platform/src/lib/pipeline/manifest_compressor.ts       (correct — keep as-is)
platform/src/lib/bundle/manifest_reader.ts             (correct — keep as-is)
platform/src/lib/synthesis/single_model_strategy.ts    (read-only; only modify if
                                                         synthesis_guidance threading
                                                         absolutely requires it)
platform/src/lib/validators/**
platform/src/lib/audit/**
platform/src/lib/retrieve/**                           (unless a field is missing from
                                                         PipelinePlan — then amend types.ts first)
platform/src/lib/trace/**
platform/src/lib/db/**
platform/src/lib/llm/**
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
00_ARCHITECTURE/CURRENT_STATE_v1_0.md
00_ARCHITECTURE/SESSION_LOG.md
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md
```

---

## §8 — KNOWN OUT-OF-SCOPE ISSUES

Do NOT fix these in this session:

1. **DeepSeek PF-S1 blocker** — `deepseek-chat` alias → `deepseek-v4-flash` production
   issue. Deferred.
2. **Anthropic maxInputTokens unregistered** — ~200K actual but unverified.
   Deferred.
3. **11 pre-existing test-file TypeScript errors** — in `__tests__/` and `tests/`
   directories only. Do not fix. Do not let them block ACs (AC checks are
   `src/` non-test files only).
4. **30-query golden-set eval** — planner eval against PLANNER_PROMPT_v2_0 deferred
   to next session after this one ships.
5. **Pre-existing dirty working-tree files** — uncommitted changes in observatory,
   panel, and StackBreakdownCards files from prior sessions. Do not commit them;
   do not touch them.

---

## §9 — COMPLETION SEQUENCE

When all 24 ACs are PASS:

1. **Set `status: COMPLETE`** in this file's frontmatter.

2. **Update `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2:**
   - `last_session_id: Pipeline-Transform-S1`
   - Note Pipeline Transformation Phases 2–4 complete.
   - `next_session: Planner-Eval-S1` (golden-set re-run with PLANNER_PROMPT_v2_0)

3. **Append to `00_ARCHITECTURE/SESSION_LOG.md`:**
   ```
   | Pipeline-Transform-S1 | 2026-05-11 | Pipeline Transformation Phases 2–4 COMPLETE.
     route.ts: 2 LLM calls. 9 legacy files deleted. PipelinePlan is the single contract. |
   ```

4. **Print the final AC checklist** with PASS/FAIL for each of the 24 items
   and the three INV items.

---

*CLAUDECODE_BRIEF.md · Pipeline-Transform-S1 · 2026-05-11*
*24 acceptance criteria across Phases 2, 3, 4 of the LLM-first planner transformation*
*Supersedes GANGA-MOPUP-S1 (PARTIAL_COMPLETE 2026-05-07)*
