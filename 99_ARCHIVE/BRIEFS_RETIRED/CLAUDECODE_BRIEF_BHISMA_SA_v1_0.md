---
title: "BHISMA Wave 2 — Session S-A: UQE Completion + MON Instrumentation"
brief_id: BHISMA_SA
version: 1.0
status: COMPLETE
created_date: 2026-05-03
session_id: BHISMA-W2-S-A
executor: claude-opus-4-6
active_phase: "BHISMA Wave 2 — Stream UQE + Stream MON"
isolation_tier: BHISMA_ONLY
parallel_safe_with: BHISMA_SB
must_complete_before: BHISMA_SC
---

# BHISMA Wave 2 — Session S-A
## UQE Completion + MON Instrumentation

**Set `status: IN_PROGRESS` at session open. Set `status: COMPLETE` only after ALL acceptance criteria pass.**

---

## §0 Context

BHISMA Wave 2 (`00_ARCHITECTURE/BHISMA_WAVE2_PLAN_v1_1.md`, CURRENT) is the Universal Query Engine + Observability sprint for the MARSYS-JIS platform. Wave 1 (commit 03770d2) is closed. Wave 2 has 58 tasks across 5 streams.

This session (S-A) covers **Stream UQE** (bug fixes + 3 missing files) and **Stream MON** (emission point instrumentation). Session S-B runs in parallel (zero file overlap guaranteed) covering SCHEMA + EVAL.

**You are NOT to open, read, or modify any files belonging to:**
- MARSYS-JIS M-phase work (anything in `025_HOLISTIC_SYNTHESIS/`, `01_FACTS_LAYER/`, `06_LEARNING_LAYER/`)
- Ustad/Phase-O Observatory (`/Users/Dev/Vibe-Coding/Apps/Ustad/` or any Ustad path)
- BHISMA_SB scope files (see §3 must_not_touch)

---

## §1 Mandatory Pre-Work

**Before any code changes**, run the following audit commands to confirm current state:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform

# Confirm the 3 missing files are still absent
ls src/lib/pipeline/universal_query_engine.ts 2>&1
ls src/lib/audit/citation_validator.ts 2>&1
ls src/lib/query_investigation.ts 2>&1

# Confirm B2W-1 bug location
grep -n "canonical_id" src/lib/tools/remedial_codex_query.ts | head -20

# Confirm temperature is unset
grep -n "temperature" src/lib/synthesis/single_model_strategy.ts | head -20

# Confirm step_seq collision
grep -n "step_seq" src/lib/trace/emitter.ts | head -20

# Current test count baseline
npx tsc --noEmit 2>&1 | tail -5
npx vitest run --reporter=verbose 2>&1 | tail -20
```

Record findings before proceeding.

---

## §2 Scope of Work (Ordered by dependency)

### BLOCK 1 — Independent Bug Fixes (no blockers, do first)

#### Task UQE-1: Fix remedial_codex_query SQL (B2W-1)
**File:** `platform/src/lib/tools/remedial_codex_query.ts`
**Root cause:** Column "canonical_id" does not exist in remedial_codex table post-migration.
**Fix:** Inspect the actual schema by checking `platform/supabase/migrations/` (latest migration that touches remedial_codex or similar table) and update the column reference to match the actual schema column name.
**Acceptance:** `SELECT` returns ≥1 row when tested with a known remedial query (e.g., "Ketu remedial measures"). Citation count ≥ 1 post-synthesis.

#### Task UQE-2: Set Synthesis Temperature Logic (B2W-5)
**File:** `platform/src/lib/synthesis/single_model_strategy.ts`
**Root cause:** Temperature unset → model defaults to non-zero → non-deterministic responses.
**Fix:**
```typescript
// Add temperature assignment based on query type before synthesis call
const temperature = queryPlan?.query_intent_summary?.includes('exploratory') ? 0.3 : 0.0;
// Pass temperature in the generateText / streamText call options
```
Set `temperature: 0` for deterministic queries (factual, remedial, interpretive single-answer).
Set `temperature: 0.3` for exploratory/holistic queries.
The temperature value must be visible in the emitted `synthesis_done` trace step (add to the payload).
**Acceptance:** Byte-identical input produces byte-identical output across 5 test loops. Temperature appears in trace.

#### Task UQE-7: Domain-Only Fallback for MSR/Registers (B2W-2, B2W-3)
**Files:**
- `platform/src/lib/tools/msr_sql.ts`
- `platform/src/lib/tools/pattern_register.ts`
- `platform/src/lib/tools/contradiction_register.ts`
- `platform/src/lib/tools/resonance_register.ts`

**Root cause:** `compose_bundle` emits `planets=[], houses=null` → `WHERE planet = ANY($planets)` returns zero rows.
**Fix:** Add a domain-only fallback path in each tool:
```typescript
// If planets array is empty AND houses is null/empty, fall back to domain-only query
// Example for msr_sql:
if (!params.planets?.length && !params.houses?.length) {
  // Query by domain only: WHERE signal_domain = $domain
  // Return up to 20 signals ordered by relevance_score DESC
}
```
Apply the same pattern to all four tools.
**Acceptance:** Each register/tool returns ≥1 row when called with `planets=[], houses=null` on a test domain ("remedial", "career", "health").

#### Task UQE-9: Fix Trace Step Sequence Collisions (B2W-7)
**File:** `platform/src/lib/trace/emitter.ts`
**Root cause:** `context_assembly` and `vector_search` both emit `step_seq=9`; synthesis orphaned at seq 11.
**Fix:** Implement atomic step sequence increment:
```typescript
// Replace static step_seq assignment with:
private stepSeqCounter = new Map<string, number>(); // keyed by query_id

nextStepSeq(queryId: string): number {
  const current = this.stepSeqCounter.get(queryId) ?? 0;
  this.stepSeqCounter.set(queryId, current + 1);
  return current + 1;
}
// Clear counter when query completes (on 'done' event)
```
For parallel steps (e.g., tool calls that fire in parallel), emit them with incrementing sequential seqs in the order they _start_, not the order they resolve.
**Acceptance:** `step_seq` is unique within `query_id` across 100+ test queries. No duplicates.

---

### BLOCK 2 — New Files (create in order)

#### Task UQE-3-REVISED: Create citation_validator.ts (B2W-6, Gap G10)
**File to create:** `platform/src/lib/audit/citation_validator.ts`
**Also update:** `platform/src/lib/audit/validator.ts`, `platform/src/lib/config/feature_flags.ts`

**Purpose:** Two-layer citation gate replacing the simple count heuristic.

**Layer 1 (existence):** Count `SIG.MSR.NNN` patterns in synthesis output (current heuristic). Returns `total_citations: number`.

**Layer 2 (cross-reference):** For each citation ID found in Layer 1, verify it actually exists in the assembled context JSONB. Returns `verified_citations: number`.

**Gate logic:**
```typescript
export type CitationValidationResult =
  | { status: 'PASS';  verified_citations: number; total_citations: number }
  | { status: 'WARN';  message: 'training_data_leak'; total_citations: number; verified_citations: 0 }
  | { status: 'ERROR'; message: 'zero_grounded_citations_prescriptive'; query_class: string }

export function validateCitations(
  synthesisOutput: string,
  assembledContext: Record<string, unknown>,
  queryClass: string,
  isPrescriptive: boolean
): CitationValidationResult {
  // Layer 1
  const totalCitations = (synthesisOutput.match(/SIG\.MSR\.\d{3}/g) ?? []).length;
  // Layer 2
  const verifiedCitations = countVerifiedInContext(
    synthesisOutput.match(/SIG\.MSR\.\d{3}/g) ?? [],
    assembledContext
  );
  // Gate logic per spec
  if (verifiedCitations >= 1) return { status: 'PASS', verified_citations: verifiedCitations, total_citations: totalCitations };
  if (totalCitations > 0 && verifiedCitations === 0) return { status: 'WARN', message: 'training_data_leak', total_citations: totalCitations, verified_citations: 0 };
  if (isPrescriptive && verifiedCitations === 0 && totalCitations === 0) return { status: 'ERROR', message: 'zero_grounded_citations_prescriptive', query_class: queryClass };
  return { status: 'PASS', verified_citations: 0, total_citations: 0 }; // non-prescriptive, zero citations allowed
}
```

**Feature flag to add to `feature_flags.ts`:**
```typescript
export const CITATION_GATE_OVERRIDE = getBoolFlag('MARSYS_FLAG_CITATION_GATE_OVERRIDE', false);
```

**Wire into validator.ts:** Call `validateCitations` after synthesis; if `status === 'ERROR'` and `!CITATION_GATE_OVERRIDE`, throw `PipelineError`.

**Write unit tests:** `platform/tests/audit/citation_validator.test.ts`
- Test: known-good remedial query → PASS with verified_citations ≥ 1
- Test: fabricated citations not in context → WARN (training_data_leak)
- Test: zero citations + prescriptive → ERROR
- Test: zero citations + non-prescriptive → PASS
- Test: CITATION_GATE_OVERRIDE=true suppresses ERROR

#### Task UQE-6: Remove Class-Based Tool Authorization (B2W-4)
**File:** `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
**Root cause:** `vector_search` excluded from `tools_authorized` for `query_class=remedial`.
**Fix:** Remove any `tools_authorized` or `class_gating` field that restricts which tools are available per query class. All tools should be available to the planner regardless of class. The planner (not the class gate) decides which tools to invoke.
**Note:** Do NOT delete `CAPABILITY_MANIFEST.json`. Only remove the class-based restriction fields. Leave all other metadata intact.
**Acceptance:** `vector_search` included in tool set for remedial queries; no class-based exclusion in manifest.

#### Task UQE-5 / UQE-4a / UQE-4b: Create universal_query_engine.ts
**File to create:** `platform/src/lib/pipeline/universal_query_engine.ts`

**Purpose:** Central orchestrator that replaces `classify + compose + plan_per_tool`. All queries route through this engine when `LLM_FIRST_PLANNER_ENABLED=true`.

**Dependencies already exist (verify before writing):**
- `platform/src/lib/pipeline/manifest_planner.ts` — exists ✓
- `platform/src/lib/pipeline/manifest_compressor.ts` — exists ✓
- `platform/src/lib/pipeline/budget_arbiter.ts` — exists ✓
- `platform/src/lib/pipeline/planner_circuit_breaker.ts` — exists ✓
- `platform/src/lib/pipeline/planner_context_builder.ts` — exists ✓
- `platform/src/lib/trace/emitter.ts` — exists ✓

**Key interfaces (from Wave 2 plan §3, UQE-4a):**
```typescript
interface CompressedManifestEntry {
  t: string;          // tool_name
  d: string;          // description ≤15 words
  p: string[];        // param names only
  c: 'low'|'med'|'hi'; // token_cost_tier
  a: string;          // data_asset_id
}

interface BudgetArbiterConfig {
  synthesis_model_max_context: number;
  system_prompt_reserve: number;
  synthesis_guidance_reserve: number;
  safety_margin: number; // 0.85
}

interface PlanningStartEvent {
  event: 'planning_start';
  query_id: string;
  planner_model_id: string;
  manifest_tool_count: number;
}

interface PlanningDoneEvent {
  event: 'planning_done';
  query_id: string;
  tool_count_planned: number;
  tools_selected: string[];
  query_intent_summary: string;
  planner_latency_ms: number;
}
```

**`UniversalQueryEngine` class signature:**
```typescript
export class UniversalQueryEngine {
  constructor(
    private manifPlanner: ManifestPlanner,
    private circuitBreaker: PlannerCircuitBreaker,
    private budgetArbiter: BudgetArbiter,
    private contextBuilder: PlannerContextBuilder,
    private emitter: TraceEmitter
  ) {}

  async plan(
    query: string,
    queryId: string,
    conversationHistory: ConversationTurn[],
    synthesisModelId: string
  ): Promise<UniversalToolCallSpec[]> {
    // 1. Emit planning_start SSE event
    // 2. Build planner context (contextBuilder.build, max 5K tokens)
    // 3. Compress manifest (manifCompressor.compress)
    // 4. Call circuit-breaker-wrapped planner
    // 5. Arbitrate budgets (budgetArbiter.arbitrate)
    // 6. Emit planning_done SSE event
    // 7. Return tool specs
  }
}
```

**Implement the full class body following the above pattern.** Wire into the routing layer so that when `LLM_FIRST_PLANNER_ENABLED=true`, the router calls `universalQueryEngine.plan()` instead of `classify + compose`.

**Write unit tests:** `platform/tests/pipeline/universal_query_engine.test.ts`
- Test: planning_start emitted before LLM call
- Test: planning_done emitted after plan validated
- Test: budget arbitration applied (total_tokens ≤ model_max × 0.85)
- Test: circuit breaker open → fallback plan returned
- Test: empty history → no summarization call

---

### BLOCK 3 — MON Instrumentation (after Block 2 stable)

#### Task MON-5: Instrument LLM Call Logging
**Files to update:**
- `platform/src/lib/pipeline/manifest_planner.ts`
- `platform/src/lib/synthesis/single_model_strategy.ts`
- `platform/src/lib/tools/title_generator.ts` (if exists; skip if absent)
- `platform/src/lib/pipeline/planner_context_builder.ts`

**What to emit at each call site:**
```typescript
// After each LLM call, write to llm_call_log:
await db.query(`
  INSERT INTO llm_call_log
    (query_id, call_stage, model_id, input_tokens, output_tokens, reasoning_tokens,
     latency_ms, cost_usd, fallback_used, created_at)
  VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
`, [queryId, stage, modelId, inputTokens, outputTokens, reasoningTokens, latencyMs, costUsd, fallbackUsed]);
```

For `single_model_strategy.ts`, if `model_id === 'deepseek-reasoner'`:
```typescript
// Extract reasoning tokens from stream
const thinkBlocks = extractThinkBlocks(rawStream); // already exists
const reasoningTokens = Math.ceil(thinkBlocks.join('').length / 4);
```

**Acceptance:** `llm_call_log` has one row per LLM call; `reasoning_tokens` non-null for deepseek-reasoner calls.

#### Task MON-6: Create query_investigation.ts + Emit query_plan_log
**File to create:** `platform/src/lib/query_investigation.ts`

**Purpose:** Helper module used by `manifest_planner.ts` to write the planner output to `query_plan_log`.

```typescript
export interface QueryPlanRecord {
  query_id: string;
  raw_plan_json: Record<string, unknown>;
  tool_count: number;
  planning_confidence: number | null;
  fallback_used: boolean;
  parsing_success: boolean;
  parse_error: string | null;
  planner_model_id: string;
  planner_latency_ms: number;
}

export async function writeQueryPlanLog(
  db: DatabaseClient,
  record: QueryPlanRecord
): Promise<void> {
  await db.query(`
    INSERT INTO query_plan_log
      (query_id, raw_plan_json, tool_count, planning_confidence,
       fallback_used, parsing_success, parse_error, planner_model_id,
       planner_latency_ms, created_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
  `, [...]);
}
```

**Wire into `manifest_planner.ts`:** Import and call `writeQueryPlanLog` after plan JSON is validated (or after fallback is triggered with `parsing_success=false`).

**Write unit tests:** `platform/tests/query_investigation.test.ts`
- Test: successful plan → `parsing_success=true`, `fallback_used=false`
- Test: parse failure → `parsing_success=false`, `parse_error` non-null
- Test: fallback triggered → `fallback_used=true`

#### Task MON-7: Instrument Tool Execution Logging
**Files:** All tool implementation files. Find them with:
```bash
ls platform/src/lib/tools/*.ts
```
Add at the end of each tool's main function (after result is obtained):
```typescript
await db.query(`
  INSERT INTO tool_execution_log
    (query_id, tool_name, params_json, execution_status, rows_returned,
     latency_ms, data_asset_id, error_code, created_at)
  VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
`, [queryId, toolName, JSON.stringify(params), status, rowCount, latencyMs, dataAssetId, errorCode ?? null]);
```
Set `execution_status = 'zero_rows'` when result is empty; `'error'` on exception; `'ok'` otherwise.

#### Task MON-8: Instrument context_assembly_log
**File:** `platform/src/lib/pipeline/context_assembly.ts`
After assembling context, emit:
```typescript
await db.query(`
  INSERT INTO context_assembly_log
    (query_id, l1_tokens, l2_signal_tokens, l2_pattern_tokens,
     l4_tokens, vector_tokens, cgm_tokens, total_tokens,
     citation_count, b3_compliant, created_at)
  VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
`, [...perLayerCounts, citationCount, b3Compliant]);
```
After synthesis completes (back in orchestrator), update `citation_count` field via a separate UPDATE call.

---

## §3 File Scope

### may_touch
```
platform/src/lib/tools/remedial_codex_query.ts
platform/src/lib/tools/msr_sql.ts
platform/src/lib/tools/pattern_register.ts
platform/src/lib/tools/contradiction_register.ts
platform/src/lib/tools/resonance_register.ts
platform/src/lib/synthesis/single_model_strategy.ts
platform/src/lib/trace/emitter.ts
platform/src/lib/pipeline/manifest_planner.ts
platform/src/lib/pipeline/manifest_compressor.ts
platform/src/lib/pipeline/budget_arbiter.ts
platform/src/lib/pipeline/planner_circuit_breaker.ts
platform/src/lib/pipeline/planner_context_builder.ts
platform/src/lib/pipeline/context_assembly.ts
platform/src/lib/audit/validator.ts
platform/src/lib/config/feature_flags.ts
00_ARCHITECTURE/CAPABILITY_MANIFEST.json
platform/src/lib/pipeline/universal_query_engine.ts          [NEW]
platform/src/lib/audit/citation_validator.ts                 [NEW]
platform/src/lib/query_investigation.ts                      [NEW]
platform/tests/pipeline/universal_query_engine.test.ts       [NEW]
platform/tests/audit/citation_validator.test.ts              [NEW]
platform/tests/query_investigation.test.ts                   [NEW]
```

### must_not_touch
```
# MARSYS-JIS research files
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
06_LEARNING_LAYER/**
00_ARCHITECTURE/BHISMA_PLAN_v1_0.md
00_ARCHITECTURE/BHISMA_WAVE2_PLAN_v1_1.md

# BHISMA S-B scope (parallel session — do not touch)
platform/tests/eval/**
platform/scripts/eval/**
00_ARCHITECTURE/RETENTION_POLICY_v1_0.md
platform/.github/**

# Ustad project (hard boundary)
/Users/Dev/Vibe-Coding/Apps/Ustad/**

# Governance files (read-only)
00_ARCHITECTURE/CURRENT_STATE_v1_0.md
00_ARCHITECTURE/SESSION_LOG.md
CLAUDE.md
```

---

## §4 Acceptance Criteria (ALL must pass before COMPLETE)

### Bug Fixes
- [ ] **B2W-1:** `remedial_codex_query` SELECT returns ≥1 row for a known remedial query (test inline, not requiring live DB)
- [ ] **B2W-2 / B2W-3:** Domain fallback returns ≥1 row when `planets=[], houses=null` for domains "remedial", "career", "health"
- [ ] **B2W-4:** CAPABILITY_MANIFEST.json has no class-based `tools_authorized` restriction; `vector_search` available to all classes
- [ ] **B2W-5:** Temperature = 0 for single_answer; temperature = 0.3 for exploratory; temperature visible in synthesis_done trace payload
- [ ] **B2W-6:** `citation_validator.ts` exists; unit tests PASS (4 scenarios); wire-in to `validator.ts` confirmed
- [ ] **B2W-7:** `step_seq` unique within `query_id`; no duplicate seqs in `emitter.ts` (verified by unit test or grep)

### New Files
- [ ] `platform/src/lib/pipeline/universal_query_engine.ts` exists; exports `UniversalQueryEngine` class; unit tests PASS
- [ ] `platform/src/lib/audit/citation_validator.ts` exists; exports `validateCitations`; unit tests PASS
- [ ] `platform/src/lib/query_investigation.ts` exists; exports `writeQueryPlanLog`; unit tests PASS

### MON Instrumentation
- [ ] `manifest_planner.ts` emits to `llm_call_log` (verified by grep for INSERT into llm_call_log)
- [ ] `single_model_strategy.ts` emits to `llm_call_log`; includes `reasoning_tokens` extraction for deepseek-reasoner
- [ ] All tool files emit to `tool_execution_log`; `zero_rows` status set correctly
- [ ] `context_assembly.ts` emits to `context_assembly_log`; per-layer token fields populated

### Quality Gates
- [ ] `npx tsc --noEmit` exits 0 (no TypeScript errors in NEW files; pre-existing errors may remain but must not increase)
- [ ] `npx vitest run` — all NEW test files pass; no pre-existing test regressions introduced by this session's changes
- [ ] No imports of Ustad/MARSYS-JIS paths in any touched file

---

## §5 Hard Constraints

1. **DB writes use the existing database client pattern** — do not introduce a new DB client library. Use whatever client pattern exists in `context_assembly.ts` or `manifest_planner.ts` as the reference.
2. **`LLM_FIRST_PLANNER_ENABLED` stays OFF** — this session does NOT flip the feature flag. The gate flip is a native decision pending S-B recall/precision report.
3. **No fabricated column names** — before any SQL INSERT, verify the target table exists by checking `platform/migrations/` (files 032–036 contain the schema). If a column name is uncertain, grep migrations to confirm.
4. **Error handling is loud** — per ADR-3, all DB write failures must log (console.error) but NOT throw (to avoid contaminating the synthesis pipeline). Wrap all monitoring inserts in try/catch with error log.
5. **B.10 discipline** — this session touches pipeline/monitoring code only. Do not derive or invent astrological values.
6. **Session close:** When all ACs pass, set `status: COMPLETE` in this file's frontmatter.

---

## §6 How to Start

Open a new Antigravity (Claude Code) window at `/Users/Dev/Vibe-Coding/Apps/Madhav/` and run:

```
Read CLAUDECODE_BRIEF_BHISMA_SA_v1_0.md and execute it.
```

The session should read this brief, set status to IN_PROGRESS, then proceed through §1 (pre-work audit), §2 Block 1 (independent fixes), §2 Block 2 (new files), §2 Block 3 (MON instrumentation), verify all §4 acceptance criteria, and set status to COMPLETE.
