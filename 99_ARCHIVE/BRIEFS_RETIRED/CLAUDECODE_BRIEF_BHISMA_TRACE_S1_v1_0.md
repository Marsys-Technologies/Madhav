---
title: "BHISMA Phase 1 Round 3 — W2-TRACE-A Planner Param Threading"
brief_id: BHISMA_TRACE_S1
version: 1.0
status: COMPLETE
created_date: 2026-05-04
session_id: BHISMA-TRACE-S1
executor: claude-sonnet-4-6
active_phase: "BHISMA Phase 1 — CI / Hardening"
isolation_tier: BHISMA_ONLY
blocked_by: none
must_complete_before: none
parallel_safe_with: none
---

# BHISMA-TRACE-S1 — W2-TRACE-A Planner Param Threading

**Set `status: IN_PROGRESS` at session open. Set `status: COMPLETE` only after ALL acceptance criteria pass.**

---

## §0 Context

The LLM-first planner (`LLM_FIRST_PLANNER_ENABLED=true`, default ON since 2026-05-04) emits a `PlanSchema` with per-tool `params` — e.g.:

```json
{ "tool_name": "msr_sql", "params": { "planet": "SATURN", "valence": "negative", "house": 10 }, "priority": 1, ... }
```

These params are designed to narrow the retrieve tool's query (less noise, higher precision output). But they are currently **completely discarded**. The route extracts only tool *names* from `planSchema.tool_calls` and passes the generic `QueryPlan` to `executeWithCache` with no params:

```typescript
queryPlan.tools_authorized = plannerTools   // names only
// ...
const result = await executeWithCache(t, queryPlan, cache)  // no params
```

The retrieve tools already accept an optional second argument:
```typescript
async function retrieve(plan: QueryPlan, params?: Record<string, unknown>)
```
And `RetrievalTool.retrieve` is typed as `retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle>`.

The gap: `executeWithCache` never passes `params` to `tool.retrieve()`. This session fixes that.

**Three files, ~35 lines total. No schema changes, no DB migrations, no tests to write beyond the existing suite.**

---

## §1 Pre-Work Audit

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Confirm executeWithCache does NOT accept plannerParams today
grep -n "plannerParams\|planner_params" platform/src/lib/cache/with_cache.ts

# Confirm the retrieve tools accept params= (should show all with params?)
grep -rn "async function retrieve(plan.*params" platform/src/lib/retrieve/ --include="*.ts" | grep -v test | wc -l

# Confirm route.ts discards params (shows only tool name extraction)
grep -n "plannerTools\|tool_calls.*map\|tools_authorized.*planner" platform/src/app/api/chat/consume/route.ts

# Confirm single_model_strategy wraps tools without params
grep -n "executeWithCache" platform/src/lib/synthesis/single_model_strategy.ts
```

---

## §2 Scope of Work

### File 1 — `platform/src/lib/cache/with_cache.ts`

Add `plannerParams` as an optional fourth argument. Pass it through to `tool.retrieve()`. Include it in the cache key so that the same tool called with different planner params gets separate cache entries (correctness > hit rate here).

**Before:**
```typescript
export async function executeWithCache(
  tool: RetrievalTool,
  plan: QueryPlan,
  cache?: RequestScopedToolCache,
): Promise<ToolBundle> {
  if (!cache) {
    return await tool.retrieve(plan)
  }

  const params: Record<string, unknown> = {
    query_class: plan.query_class,
    domains: [...(plan.domains ?? [])].sort(),
    planets: [...(plan.planets ?? [])].sort(),
    forward_looking: plan.forward_looking,
    dasha_context_required: plan.dasha_context_required ?? false,
  }

  const existing = cache.getPromise(tool.name, params)
  if (existing) {
    const cached = await existing
    return { ...cached, served_from_cache: true }
  }

  const promise = tool.retrieve(plan)
  cache.put(tool.name, params, promise)
  return await promise
}
```

**After:**
```typescript
export async function executeWithCache(
  tool: RetrievalTool,
  plan: QueryPlan,
  cache?: RequestScopedToolCache,
  plannerParams?: Record<string, unknown>,
): Promise<ToolBundle> {
  if (!cache) {
    return await tool.retrieve(plan, plannerParams)
  }

  const cacheKey: Record<string, unknown> = {
    query_class: plan.query_class,
    domains: [...(plan.domains ?? [])].sort(),
    planets: [...(plan.planets ?? [])].sort(),
    forward_looking: plan.forward_looking,
    dasha_context_required: plan.dasha_context_required ?? false,
    // Include planner params in cache key so different param sets don't alias.
    // Sort keys for determinism.
    ...(plannerParams && Object.keys(plannerParams).length > 0
      ? { planner_params: Object.fromEntries(Object.entries(plannerParams).sort()) }
      : {}),
  }

  const existing = cache.getPromise(tool.name, cacheKey)
  if (existing) {
    const cached = await existing
    return { ...cached, served_from_cache: true }
  }

  const promise = tool.retrieve(plan, plannerParams)
  cache.put(tool.name, cacheKey, promise)
  return await promise
}
```

### File 2 — `platform/src/app/api/chat/consume/route.ts`

After the budget arbitration block that sets `queryPlan.tools_authorized`, build a params map from `planSchema.tool_calls`. Then pass per-tool params to `executeWithCache`.

**Step 2a — build the params map** (add immediately after `queryPlan.tools_authorized = plannerTools`):

```typescript
// W2-TRACE-A: map from tool_name → planner-supplied params.
// When the LLM planner is active, these narrow the retrieve call
// (e.g. msr_sql gets { planet:'SATURN', valence:'negative' }).
// When planSchema is null (classify() fallback), map is empty and
// executeWithCache receives undefined — no behaviour change.
const plannerParamsMap = new Map<string, Record<string, unknown>>(
  planSchema?.tool_calls.map(tc => [tc.tool_name, tc.params]) ?? []
)
```

Place this immediately after:
```typescript
queryPlan.tools_authorized = plannerTools
```

**Step 2b — pass params to executeWithCache** in the tool execution loop. Find this line:
```typescript
const result = await executeWithCache(t, queryPlan, cache)
```
Change it to:
```typescript
const result = await executeWithCache(t, queryPlan, cache, plannerParamsMap.get(toolName))
```

### File 3 — `platform/src/lib/synthesis/single_model_strategy.ts`

In the wrapped-tools loop (around lines 214–229), pass planner params from `query_plan.tool_calls` if present.

The `query_plan` received by `synthesize()` may be a `RichQueryPlan` (which has `tool_calls: ToolCallSpec[]`). It's already typed as the retrieve-layer `QueryPlan` in this file's scope, so cast it safely.

**Before** (inside the `for (const toolName of query_plan.tools_authorized)` loop):
```typescript
execute: async () => {
  const t = getTool(toolName)
  if (!t) return { error: `Tool ${toolName} not found` }
  const toolBundle = await executeWithCache(t, query_plan, cache)
  return { results: toolBundle.results, tool_name: toolName }
},
```

**After:**
```typescript
execute: async () => {
  const t = getTool(toolName)
  if (!t) return { error: `Tool ${toolName} not found` }
  // W2-TRACE-A: thread planner-supplied params if the plan carries them.
  const richToolCalls = (query_plan as { tool_calls?: Array<{ tool_name: string; params: Record<string, unknown> }> }).tool_calls ?? []
  const plannerParams = richToolCalls.find(tc => tc.tool_name === toolName)?.params
  const toolBundle = await executeWithCache(t, query_plan, cache, plannerParams)
  return { results: toolBundle.results, tool_name: toolName }
},
```

---

## §3 File Scope

### may_touch
```
platform/src/lib/cache/with_cache.ts                   [EDIT — add plannerParams arg]
platform/src/app/api/chat/consume/route.ts             [EDIT — build params map + pass to executeWithCache]
platform/src/lib/synthesis/single_model_strategy.ts   [EDIT — read params from RichQueryPlan, pass to executeWithCache]
```

### must_not_touch
```
platform/src/lib/retrieve/**                [retrieve tools already accept params= correctly]
platform/src/lib/router/**
platform/src/lib/cache/tool_cache.ts        [cache storage internals unchanged]
platform/tests/**
00_ARCHITECTURE/**
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
CLAUDE.md
.github/**
/Users/Dev/Vibe-Coding/Apps/Ustad/**
```

---

## §4 Acceptance Criteria

- [ ] `executeWithCache` signature has `plannerParams?: Record<string, unknown>` as 4th arg
- [ ] `tool.retrieve(plan, plannerParams)` called (not `tool.retrieve(plan)`)
- [ ] Cache key includes planner params when non-empty
- [ ] `plannerParamsMap` built from `planSchema?.tool_calls` in route.ts (empty when planSchema is null → no behaviour change on fallback path)
- [ ] `executeWithCache` in route.ts passes `plannerParamsMap.get(toolName)` (undefined when tool not in map)
- [ ] `single_model_strategy.ts` reads `tool_calls` from query_plan and passes params to `executeWithCache`
- [ ] `tsc --noEmit` — no new errors in any of the 3 touched files
- [ ] `npm test` passes — same pass count as before (no regressions)
- [ ] When `planSchema` is null (fallback path), `plannerParamsMap` is an empty Map; all `plannerParamsMap.get(...)` calls return `undefined` → behaviour identical to pre-patch

---

## §5 Hard Constraints

1. **Do not modify retrieve tool implementations** — they already handle `params?` correctly. This session only threads params *into* them from the call sites.
2. **Do not add a new QueryPlan field** — use the cast `(query_plan as { tool_calls?: ... })` for the single_model_strategy access. The router types already have `RichQueryPlan` with `tool_calls` — but modifying the retrieve-layer `QueryPlan` type is out of scope.
3. **Backward-compatible only** — every new argument is optional. When planSchema is absent, behaviour is byte-identical to the pre-patch state.
4. **Session close:** When all ACs pass, set `status: COMPLETE` in this file's frontmatter.

---

## §6 How to Start

Open a new Antigravity window at `/Users/Dev/Vibe-Coding/Apps/Madhav/` and run:
```
Read CLAUDECODE_BRIEF_BHISMA_TRACE_S1_v1_0.md and execute it.
```
