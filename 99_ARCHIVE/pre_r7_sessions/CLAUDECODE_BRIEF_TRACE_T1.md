---
session_id: TRACE-T1
title: Query Trace — Data Capture & API
status: COMPLETE
phase: TRACE-T1
executor: Anti-Gravity (Claude Code, claude-sonnet-4-6)
created_date: 2026-05-05
reference_plan: 00_ARCHITECTURE/QUERY_TRACE_REDESIGN_v1_0.md
---

# TRACE-T1 — Query Trace Data Capture & API

## Objective

Land the data model and working API endpoint that powers the reimagined Query Trace UI.
The current trace shows only what executed. After this session, the trace captures:
- What alternatives were considered at each decision point (classify, plan)
- What each retrieval step fetched, kept, and dropped (with reasons)
- The full context assembly story (per-item: rank, status, drop reason, token cost)
- A synthesis quality scorecard
- Baselines for comparing this query against others of the same type

**No UI changes in this session.** This is purely data instrumentation + one new API endpoint.

---

## Scope

```
may_touch:
  - platform/supabase/migrations/            # new migration file only
  - platform/src/lib/pipeline/classify.ts    # emit decision_alternatives to llm_call_log
  - platform/src/lib/pipeline/manifest_planner.ts  # emit plan_alternatives_log rows
  - platform/src/lib/retrieval/             # all retrieval modules: emit kept/dropped items
  - platform/src/lib/context/assembler.ts   # emit context_assembly_log rows
  - platform/src/lib/db/monitoring-write.ts # extend writeLlmCallLog + writeToolExecutionLog
  - platform/src/lib/db/trace/             # CREATE this directory
  - platform/src/app/api/admin/trace/[query_id]/route.ts  # CREATE
  - platform/src/lib/admin/trace_assembler.ts             # CREATE
  - platform/src/lib/admin/baseline_resolver.ts           # CREATE
  - platform/src/__tests__/lib/admin/trace*               # CREATE test files

must_not_touch:
  - platform/src/lib/synthesis/             # synthesis quality scorecard comes from existing checkpoint outputs only
  - platform/src/lib/components/            # no UI this session
  - platform/src/app/(super-admin)/         # no UI this session
  - platform/src/lib/llm/observability/     # do not change OBS-S1 work
  - any existing migration files
  - any existing test files (only create new ones)
```

---

## Task 1 — DB Migration

**New file:** `platform/supabase/migrations/0XX_query_trace_capture.sql`
(Use the next available migration number — check `ls platform/supabase/migrations/` to find it.)

### 1a — Alter `llm_call_log`

```sql
ALTER TABLE llm_call_log
  ADD COLUMN IF NOT EXISTS decision_alternatives JSONB,
  ADD COLUMN IF NOT EXISTS decision_reasoning TEXT,
  ADD COLUMN IF NOT EXISTS prompt_template_id TEXT,
  ADD COLUMN IF NOT EXISTS prompt_template_version TEXT,
  ADD COLUMN IF NOT EXISTS parent_call_id UUID REFERENCES llm_call_log(id);
```

### 1b — Alter `tool_execution_log`

```sql
ALTER TABLE tool_execution_log
  ADD COLUMN IF NOT EXISTS raw_result_count INTEGER,
  ADD COLUMN IF NOT EXISTS kept_result_count INTEGER,
  ADD COLUMN IF NOT EXISTS dropped_items JSONB,
  ADD COLUMN IF NOT EXISTS kept_items JSONB,
  ADD COLUMN IF NOT EXISTS tool_input_payload JSONB,
  ADD COLUMN IF NOT EXISTS tool_output_summary JSONB,
  ADD COLUMN IF NOT EXISTS error_class TEXT DEFAULT 'OK';
```

### 1c — Create `context_assembly_log`

```sql
CREATE TABLE IF NOT EXISTS context_assembly_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id UUID NOT NULL,
  assembly_step_id TEXT NOT NULL,
  item_rank INTEGER NOT NULL,
  source_bundle TEXT NOT NULL,
  source_item_id TEXT NOT NULL,
  layer TEXT NOT NULL,
  token_cost INTEGER NOT NULL,
  relevance_score REAL,
  status TEXT NOT NULL CHECK (status IN ('INCLUDED', 'TRUNCATED', 'DROPPED')),
  drop_reason TEXT CHECK (drop_reason IN ('BUDGET_EXCEEDED', 'DEDUP', 'RELEVANCE_FLOOR') OR drop_reason IS NULL),
  truncated_to_tokens INTEGER,
  cumulative_tokens_at_decision INTEGER,
  budget_at_decision INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_context_assembly_log_query
  ON context_assembly_log(query_id, item_rank);
```

### 1d — Create `synthesis_quality_scorecard`

```sql
CREATE TABLE IF NOT EXISTS synthesis_quality_scorecard (
  query_id UUID PRIMARY KEY,
  citation_density REAL NOT NULL DEFAULT 0,
  whole_chart_coverage JSONB NOT NULL DEFAULT '{}',
  derivation_ledger_compliance REAL NOT NULL DEFAULT 0,
  fabricated_computation_flags JSONB,
  disclosure_tier_verdict TEXT NOT NULL DEFAULT 'UNKNOWN',
  composite_score REAL NOT NULL DEFAULT 0,
  failures JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 1e — Create `plan_alternatives_log`

```sql
CREATE TABLE IF NOT EXISTS plan_alternatives_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id UUID NOT NULL,
  bundle_name TEXT NOT NULL,
  was_selected BOOLEAN NOT NULL,
  rationale TEXT,
  expected_recall_score REAL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_plan_alternatives_log_query
  ON plan_alternatives_log(query_id);
```

### 1f — Materialized view `query_baseline_stats`

First check whether a `query_summary` view or table exists. If it does, adapt the SQL to the actual columns. If it does not exist yet, create a lightweight version reading from `llm_call_log` and `tool_execution_log`. The goal is a materialized view keyed by `query_type` with p50/p95 latency and cost baselines.

```sql
-- Only create this if query_summary (or equivalent) exists.
-- If not, stub it with a view over llm_call_log grouped by call_stage.
-- Adjust column references to match the actual schema.
CREATE MATERIALIZED VIEW IF NOT EXISTS query_baseline_stats AS
SELECT
  'unknown'::TEXT AS query_type,    -- placeholder until query_type column confirmed
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms) AS p50_total_latency_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_total_latency_ms,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY cost_usd)   AS p50_total_cost_usd,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cost_usd)   AS p95_total_cost_usd,
  COUNT(*) AS sample_size
FROM llm_call_log
WHERE created_at > NOW() - INTERVAL '30 days'
  AND cost_usd IS NOT NULL
GROUP BY 1;
```

**Important:** Read the actual `llm_call_log` schema before writing this view. Adapt the column names to what actually exists. Add a comment in the migration noting this is a stub pending full `query_summary` population.

---

## Task 2 — Extend `writeLlmCallLog`

**File:** `platform/src/lib/db/monitoring-write.ts`

Read the existing `writeLlmCallLog` signature. Add the new optional fields to its input type:

```typescript
export interface LlmCallLogEntry {
  // ... existing fields ...
  decision_alternatives?: unknown   // JSONB
  decision_reasoning?: string
  prompt_template_id?: string
  prompt_template_version?: string
  parent_call_id?: string
}
```

Add the same fields to the INSERT statement. Use `?? null` so existing callers are unaffected.

Do the same for `writeToolExecutionLog` — add:
```typescript
export interface ToolExecutionLogEntry {
  // ... existing fields ...
  raw_result_count?: number
  kept_result_count?: number
  dropped_items?: unknown       // JSONB, capped at 200 items
  kept_items?: unknown          // JSONB, capped at 200 items
  tool_input_payload?: unknown  // JSONB
  tool_output_summary?: unknown // JSONB
  error_class?: 'OK' | 'TIMEOUT' | 'AUTH' | 'MALFORMED_RESPONSE' | 'EMPTY'
}
```

**Do not** change any existing callers. Existing callers will continue to work with the new optional fields defaulting to null.

---

## Task 3 — New writer module `context_assembly_writer.ts`

**New file:** `platform/src/lib/db/trace/context_assembly_writer.ts`

```typescript
import type { StorageClient } from '@/lib/storage'

export interface ContextAssemblyItem {
  query_id: string
  assembly_step_id: string
  item_rank: number
  source_bundle: string
  source_item_id: string
  layer: 'preamble' | 'L1' | 'L2_5'
  token_cost: number
  relevance_score?: number
  status: 'INCLUDED' | 'TRUNCATED' | 'DROPPED'
  drop_reason?: 'BUDGET_EXCEEDED' | 'DEDUP' | 'RELEVANCE_FLOOR'
  truncated_to_tokens?: number
  cumulative_tokens_at_decision: number
  budget_at_decision: number
}

/**
 * Fire-and-forget: write context assembly items to context_assembly_log.
 * Errors are swallowed — this must never disrupt the assembly path.
 * Cap at 500 items per call to avoid very large inserts.
 */
export function writeContextAssemblyLog(
  items: ContextAssemblyItem[],
  db: StorageClient,
): void {
  const capped = items.slice(0, 500)
  void (async () => {
    try {
      if (capped.length === 0) return
      const values = capped.map((_, i) => {
        const base = i * 12
        return `($${base+1},$${base+2},$${base+3},$${base+4},$${base+5},$${base+6},$${base+7},$${base+8},$${base+9},$${base+10},$${base+11},$${base+12})`
      }).join(',')
      const params = capped.flatMap(item => [
        item.query_id, item.assembly_step_id, item.item_rank,
        item.source_bundle, item.source_item_id, item.layer,
        item.token_cost, item.relevance_score ?? null, item.status,
        item.drop_reason ?? null, item.cumulative_tokens_at_decision,
        item.budget_at_decision,
      ])
      await db.query(
        `INSERT INTO context_assembly_log
         (query_id, assembly_step_id, item_rank, source_bundle, source_item_id, layer,
          token_cost, relevance_score, status, drop_reason, cumulative_tokens_at_decision,
          budget_at_decision)
         VALUES ${values}
         ON CONFLICT DO NOTHING`,
        params,
      )
    } catch {
      // telemetry errors must not propagate
    }
  })()
}
```

---

## Task 4 — New writer `plan_alternatives_writer.ts`

**New file:** `platform/src/lib/db/trace/plan_alternatives_writer.ts`

```typescript
import type { StorageClient } from '@/lib/storage'

export interface PlanAlternative {
  query_id: string
  bundle_name: string
  was_selected: boolean
  rationale?: string
  expected_recall_score?: number
}

export function writePlanAlternatives(
  alternatives: PlanAlternative[],
  db: StorageClient,
): void {
  void (async () => {
    try {
      if (alternatives.length === 0) return
      const values = alternatives.map((_, i) => {
        const base = i * 5
        return `($${base+1},$${base+2},$${base+3},$${base+4},$${base+5})`
      }).join(',')
      const params = alternatives.flatMap(a => [
        a.query_id, a.bundle_name, a.was_selected,
        a.rationale ?? null, a.expected_recall_score ?? null,
      ])
      await db.query(
        `INSERT INTO plan_alternatives_log
         (query_id, bundle_name, was_selected, rationale, expected_recall_score)
         VALUES ${values}`,
        params,
      )
    } catch {
      // telemetry errors must not propagate
    }
  })()
}
```

---

## Task 5 — Wire logging into the classify path

**File:** `platform/src/lib/pipeline/classify.ts` (read first to understand the structure)

In the classify function, after the LLM returns its classification response, extract the alternatives array (if the LLM returns ranked candidates). Add to the `writeLlmCallLog` call:

```typescript
writeLlmCallLog({
  // ... existing fields ...
  decision_alternatives: classifyResult.candidates ?? null,
  decision_reasoning: classifyResult.reasoning ?? null,
  prompt_template_id: 'classify_v1',
  prompt_template_version: CLASSIFY_PROMPT_VERSION ?? null,
})
```

**Do not** change the classify logic — only augment the logging call. If `classifyResult` does not have a `candidates` array (depends on the actual response shape), add a `TODO` comment noting what field would carry alternatives and leave `decision_alternatives: null` for now.

---

## Task 6 — Wire plan_alternatives_log in manifest_planner

**File:** `platform/src/lib/pipeline/manifest_planner.ts`

The planner already has a success path that calls `writeLlmCallLog`. After that block, add a fire-and-forget call to `writePlanAlternatives`.

Read the planner code to understand what bundle selection information is available in the planner result. The planner prompt (PLANNER_PROMPT v1.6) instructs the LLM to return a plan. Determine whether the raw LLM output contains bundle reasoning.

If the plan result has `included_bundles[]` and `excluded_bundles[]` (or equivalent), emit them:

```typescript
import { writePlanAlternatives } from '@/lib/db/trace/plan_alternatives_writer'
import { getStorageClient } from '@/lib/storage'

// After the existing writeLlmCallLog block in the success path:
{
  const obsDb = getStorageClient()
  const alternatives: PlanAlternative[] = [
    ...(planResult.included_bundles ?? []).map(b => ({
      query_id: queryId ?? nativeId,
      bundle_name: b.name ?? b,
      was_selected: true,
      rationale: b.rationale ?? null,
      expected_recall_score: b.expected_recall ?? null,
    })),
    ...(planResult.excluded_bundles ?? []).map(b => ({
      query_id: queryId ?? nativeId,
      bundle_name: b.name ?? b,
      was_selected: false,
      rationale: b.rationale ?? null,
    })),
  ]
  writePlanAlternatives(alternatives, obsDb)
}
```

If the plan result does not have this structure, add a `TODO` comment and skip for now. Do not break the planner.

---

## Task 7 — Wire kept/dropped items in retrieval modules

**Read the files under `platform/src/lib/retrieval/`** (or wherever SQL/GCS/vector retrieval happens — grep for `writeToolExecutionLog` to find the relevant files).

For each retrieval tool call that already calls `writeToolExecutionLog`, augment the call with:

```typescript
writeToolExecutionLog({
  // ... existing fields ...
  raw_result_count: rawResults.length,
  kept_result_count: keptResults.length,
  dropped_items: droppedResults.slice(0, 200).map(item => ({
    item_id: item.id ?? item.signal_id ?? item.chunk_id,
    score: item.score ?? item.relevance_score ?? null,
    drop_reason: item.drop_reason ?? 'BELOW_THRESHOLD',
  })),
  kept_items: keptResults.slice(0, 200).map(item => ({
    item_id: item.id ?? item.signal_id ?? item.chunk_id,
    score: item.score ?? item.relevance_score ?? null,
    contribution_tokens: item.token_count ?? null,
  })),
  tool_input_payload: {
    // bundle-specific — include SQL string for sql tools, URIs for GCS, query text for vector
  },
  error_class: 'OK',
})
```

**Only augment existing `writeToolExecutionLog` calls — do not add new ones.** If a retrieval module doesn't call `writeToolExecutionLog`, add a `TODO` comment and move on. The goal is to capture data where the hook already exists, not to add hooks to untouched code.

---

## Task 8 — Wire context_assembly_log in assembler

**File:** `platform/src/lib/context/assembler.ts` (read first)

After context assembly is complete, emit a fire-and-forget batch write. At the end of the assembly function, collect the assembly manifest (which items were included, truncated, dropped) and call `writeContextAssemblyLog`.

The assembler already tracks what went into context. Adapt the collection to the `ContextAssemblyItem` shape. Key fields:
- `status`: `INCLUDED` if fully included, `TRUNCATED` if the item was included but its text was cut, `DROPPED` if it was pruned.
- `drop_reason`: `BUDGET_EXCEEDED` if budget was exhausted, `DEDUP` if the item was a duplicate of a higher-priority item, `RELEVANCE_FLOOR` if below the relevance threshold.
- `cumulative_tokens_at_decision`: running total of tokens committed when this item was evaluated.
- `budget_at_decision`: the budget ceiling at the time this item was evaluated.

If the assembler does not currently track these fields, add minimal instrumentation to collect them during the assembly loop. **Do not change the assembly algorithm** — only observe and record.

---

## Task 9 — Trace API endpoint + assembler

### 9a — Trace assembler

**New file:** `platform/src/lib/admin/trace_assembler.ts`

This module queries all the new tables (plus existing `llm_call_log`, `tool_execution_log`, `audit_logs`) for a given `query_id` and assembles the full trace document.

```typescript
export interface TraceDocument {
  query: {
    id: string
    text: string | null
    type: string | null
    confidence: number | null
    total_ms: number | null
    total_cost_usd: number | null
    health: 'HEALTHY' | 'DEGRADED' | 'FAILED' | 'UNKNOWN'
  }
  classify: {
    input: unknown
    alternatives: Array<{ type: string; confidence: number; rationale: string | null }>
    decision_reasoning: string | null
    latency_ms: number | null
    tokens: { input: number; output: number }
  } | null
  plan: {
    included_bundles: Array<{ name: string; rationale: string | null; expected_recall: number | null }>
    excluded_bundles: Array<{ name: string; rationale: string | null }>
    plan_json: unknown
    latency_ms: number | null
  } | null
  fetches: Array<{
    bundle: string
    step_order: number
    raw_count: number
    kept_count: number
    dropped_items: Array<{ item_id: string; score: number | null; drop_reason: string }>
    kept_items: Array<{ item_id: string; score: number | null; contribution_tokens: number | null }>
    latency_ms: number | null
    error_class: string
  }>
  context_assembly: {
    items: Array<{
      rank: number
      source_bundle: string
      source_item_id: string
      layer: string
      token_cost: number
      relevance_score: number | null
      status: 'INCLUDED' | 'TRUNCATED' | 'DROPPED'
      drop_reason: string | null
      cumulative_tokens: number
      budget: number
    }>
    token_ledger: {
      total: number
      budget: number
      preamble: number
      L1: number
      L2_5: number
      dropped_count: number
      truncated_count: number
    }
  } | null
  synthesis: {
    model: string | null
    input_tokens: number | null
    output_tokens: number | null
    latency_ms: number | null
    scorecard: unknown | null
  } | null
  baselines: {
    p50_total_latency_ms: number | null
    p95_total_latency_ms: number | null
    p50_total_cost_usd: number | null
    p95_total_cost_usd: number | null
    sample_size: number
  } | null
  anomalies: Array<{
    stage: string
    severity: 'ERROR' | 'WARNING' | 'INFO'
    message: string
    step_id: string | null
  }>
  partial: boolean
}

export async function assembleTrace(
  queryId: string,
  db: StorageClient,
): Promise<TraceDocument> {
  // Fetch all relevant rows in parallel. For rows that don't exist (pre-instrumentation),
  // gracefully return nulls. Set partial=true if any expected section is missing.
  // ...
}
```

Implement `assembleTrace` by running parallel queries to all relevant tables. Derive `health` from: if any fetch `error_class !== 'OK'` → DEGRADED; if synthesis scorecard `composite_score < 0.5` → DEGRADED; if any step has `error_class` that isn't OK and it was supposed to contribute → FAILED; otherwise HEALTHY.

Derive `anomalies` with these initial detectors:
1. Plan latency > 2× p50 for query type → WARNING `Plan latency ${plan_ms}ms (${ratio}× p50)`
2. Any fetch with `error_class !== 'OK'` → ERROR `${bundle} fetch failed: ${error_class}`
3. Any fetch with `kept_count === 0` → WARNING `${bundle} returned 0 items`
4. Context assembly `dropped_count / (dropped_count + included_count) > 0.3` → WARNING `Context assembly dropped >30% of candidates (budget pressure)`
5. Synthesis `citation_density < 0.5` (from scorecard) → WARNING `Synthesis citation density low`

### 9b — API route

**New file:** `platform/src/app/api/admin/trace/[query_id]/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { getServerUserWithProfile } from '@/lib/auth/access-control'
import { getStorageClient } from '@/lib/storage'
import { assembleTrace } from '@/lib/admin/trace_assembler'

export async function GET(
  _req: NextRequest,
  { params }: { params: { query_id: string } },
) {
  const ctx = await getServerUserWithProfile()
  if (!ctx) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  if (ctx.profile.role !== 'super_admin') return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  if (ctx.profile.status !== 'active') return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const db = getStorageClient()
  const trace = await assembleTrace(params.query_id, db)
  return NextResponse.json(trace)
}
```

---

## Task 10 — TypeScript check

```bash
cd platform && npx tsc --noEmit 2>&1 | tail -30
```

Zero new errors in files you touched.

---

## Task 11 — Tests

```bash
cd platform && npx vitest run \
  src/__tests__/lib/admin/ \
  src/__tests__/lib/db/trace/ \
  --reporter=verbose 2>&1 | tail -60
```

Write tests covering:
1. `writeContextAssemblyLog` — happy path (batch insert), empty array (no-op), DB error (swallowed).
2. `writePlanAlternatives` — happy path, empty array.
3. `assembleTrace` — with full data (all tables populated), with partial data (pre-instrumentation query returns `partial: true`), with non-existent query_id (returns null for all sections, `partial: true`).
4. Anomaly detectors — each of the 5 detectors, with a mocked trace document.
5. API route — 401 (unauthenticated), 403 (non-super_admin), 200 with mocked assembler.

Minimum 20 tests.

---

## Acceptance Criteria

| AC | Check |
|---|---|
| AC.T1.1 | Migration applies cleanly (`supabase db reset` or equivalent test cycle passes) |
| AC.T1.2 | `context_assembly_log`, `synthesis_quality_scorecard`, `plan_alternatives_log` tables exist with correct schema |
| AC.T1.3 | `llm_call_log` and `tool_execution_log` have all new columns (nullable, backward-compatible) |
| AC.T1.4 | `query_baseline_stats` materialized view populates (even if sample_size = 0 on fresh DB) |
| AC.T1.5 | `writeContextAssemblyLog` is fire-and-forget, never throws, caps at 500 items |
| AC.T1.6 | `GET /api/admin/trace/:query_id` returns 403 for non-super_admin callers |
| AC.T1.7 | `GET /api/admin/trace/:query_id` returns the full `TraceDocument` shape for any valid query_id |
| AC.T1.8 | `partial: true` returned when `context_assembly_log` has no rows for the query |
| AC.T1.9 | All 5 anomaly detectors produce a callout when their condition is met |
| AC.T1.10 | `tsc --noEmit` exits clean (or only pre-existing unrelated errors) |
| AC.T1.11 | ≥ 20 tests pass |

---

## Priority order (if context runs short)

1. Must ship: Tasks 1, 2, 9 (migration + writer extension + API endpoint — the load-bearing items)
2. Should ship: Tasks 3, 4, 7, 8 (writer modules + retrieval/assembler hooks)
3. Nice to have: Tasks 5, 6 (classify/planner decision_alternatives logging)
4. Always run: Tasks 10, 11 (tsc + tests)

---

## Do NOT do

- Do not modify any synthesis prompt, planner prompt, or classification logic
- Do not change the assembly algorithm — only instrument it
- Do not modify existing `writeToolExecutionLog` call sites beyond adding the new optional fields
- Do not touch any UI component or page
- Do not change OBS-S1 observability code (`lib/llm/observability/`)

---

## How to start

Open the Madhav project (`/Users/Dev/Vibe-Coding/Apps/Madhav/`) in Anti-Gravity.
Run: **"Read CLAUDECODE_BRIEF_TRACE_T1.md and execute it."**
