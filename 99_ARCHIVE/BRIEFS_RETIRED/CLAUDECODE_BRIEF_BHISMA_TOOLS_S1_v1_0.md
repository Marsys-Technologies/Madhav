---
title: "BHISMA Phase 1 Round 2 — Structured Tool Execution Logging"
brief_id: BHISMA_TOOLS_S1
version: 1.0
status: COMPLETE
created_date: 2026-05-04
session_id: BHISMA-TOOLS-S1
executor: claude-sonnet-4-6
active_phase: "BHISMA Phase 1 — CI / Hardening"
isolation_tier: BHISMA_ONLY
blocked_by: none
must_complete_before: none
parallel_safe_with: none
---

# BHISMA-TOOLS-S1 — Structured Tool Execution Logging

**Set `status: IN_PROGRESS` at session open. Set `status: COMPLETE` only after ALL acceptance criteria pass.**

---

## §0 Context

The pipeline has two tool execution paths:

1. **Retrieve-tools path** — The route calls `getTool(name)` + `executeWithCache()` for the 15 retrieve tools registered in `/lib/retrieve/index.ts`. These tools already call `writeToolExecutionLog` themselves, keyed on `plan.query_plan_id`.

2. **Synthesis-time AI SDK path** — The route calls `streamText({ tools: buildConsumeTools(...) })`. When Claude decides to call a tool during synthesis, the AI SDK calls that tool's `execute()` function. This path covers the **16 structured tools** in `/lib/tools/structured/` plus `get_birth_data`, `get_planetary_positions`, `get_chart_documents`, and others in `consumeTools`. These tools have no `query_id` in scope and make **zero writes to `tool_execution_log`**.

This means roughly half of all tool executions are invisible in `tool_execution_log` and in the Observatory/monitoring views. The fix is a single `onStepFinish` hook added to the `streamText` call in `route.ts`. No individual tool files need to be modified.

---

## §1 Pre-Work Audit

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Confirm writeToolExecutionLog is NOT already imported in route.ts
grep "writeToolExecutionLog" platform/src/app/api/chat/consume/route.ts

# Confirm onStepFinish is NOT already present in the streamText call
grep "onStepFinish" platform/src/app/api/chat/consume/route.ts

# Confirm the streamText call location (should be around line 797)
grep -n "streamText(" platform/src/app/api/chat/consume/route.ts

# Confirm monitoring-write exports writeToolExecutionLog
grep "export.*writeToolExecutionLog" platform/src/lib/db/monitoring-write.ts
```

All of the above should confirm the gap exists and the fix target is clear.

---

## §2 Scope of Work

### The Fix — Add `onStepFinish` to `streamText` in `route.ts`

**Step 1 — Add import** (find the existing monitoring-write import block at the top of route.ts and add `writeToolExecutionLog`):

The existing import is approximately:
```typescript
import {
  writeLlmCallLog,
  writeQueryPlanLog,
  writeContextAssemblyLog,
} from '@/lib/db/monitoring-write'
```

Change it to:
```typescript
import {
  writeLlmCallLog,
  writeQueryPlanLog,
  writeToolExecutionLog,
  writeContextAssemblyLog,
} from '@/lib/db/monitoring-write'
```

**Step 2 — Add `onStepFinish` callback to the `streamText` call**

The `streamText` call already has `onFinish`. Add `onStepFinish` just before `onFinish`. The callback fires once per LLM step; each step may have zero or more tool calls.

Add this callback — the exact shape of `toolCalls` and `toolResults` in `StepResult` is `Array<{ toolName: string; args: Record<string,unknown> }>` and `Array<{ toolName: string; result: unknown }>` respectively:

```typescript
    onStepFinish: ({ toolCalls, toolResults }) => {
      // Log each tool call that happened during this synthesis step.
      // The retrieve-tools path (executeWithCache) logs itself — this hook
      // only fires for consumeTools (structured tools + chart tools called
      // during streamText). Fire-and-forget: never throw to the caller.
      if (!toolCalls?.length) return
      for (let i = 0; i < toolCalls.length; i++) {
        const tc = toolCalls[i]
        const tr = toolResults?.[i]
        const result = tr?.result
        // Estimate rows_returned: array length if result is an array, else 1.
        const rowsReturned =
          result != null
            ? Array.isArray(result)
              ? result.length
              : 1
            : 0
        void writeToolExecutionLog({
          query_id: queryId,
          tool_name: tc.toolName,
          params_json: tc.args as Record<string, unknown>,
          status: result != null ? 'success' : 'error',
          rows_returned: rowsReturned,
          latency_ms: null,       // not available per-tool from onStepFinish
          token_estimate: null,
          data_asset_id: null,
          error_code: null,
          served_from_cache: false,
          fallback_used: false,
        })
      }
    },
```

The resulting `streamText` call should have this shape (order: existing options → onStepFinish → onFinish):

```typescript
  const result = streamText({
    model: resolveModel(modelId),
    messages: modelMessages,
    tools: toolsForModel,
    stopWhen: stepCountIs(5),
    maxOutputTokens: modelMeta.maxOutputTokens,
    experimental_transform: smoothStream({ delayInMs: 20, chunking: 'word' }),
    ...(modelMeta.provider === 'nvidia' && { maxRetries: 0 }),
    ...(googleProviderOptions(modelId) && {
      providerOptions: googleProviderOptions(modelId),
    }),
    onStepFinish: ({ toolCalls, toolResults }) => {
      // ... (the block above)
    },
    onFinish: ({ finishReason: reason, providerMetadata, usage }) => {
      // ... (existing, unchanged)
    },
  })
```

### TypeScript type check

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npx tsc --noEmit 2>&1 | grep -E "route\.ts|monitoring-write" | head -20
```

If the `toolCalls[i].args` cast triggers a type error, use `tc.args as Record<string, unknown> | undefined ?? {}` or the exact type that tsc requires. Do NOT loosen the writeToolExecutionLog signature; adjust the cast at the call site.

### Run tests

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npm test 2>&1 | tail -20
```

No test should fail as a result of this change. The existing monitoring-write tests mock the DB client; nothing in the route test mocks `onStepFinish`.

---

## §3 File Scope

### may_touch
```
platform/src/app/api/chat/consume/route.ts    [EDIT — import + onStepFinish callback]
```

### must_not_touch
```
platform/src/lib/tools/structured/**          [zero changes to the 16 tools]
platform/src/lib/retrieve/**                  [already instrumented; do not double-log]
platform/src/lib/db/monitoring-write.ts       [read-only — do NOT change the function signature]
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

- [ ] `writeToolExecutionLog` added to the monitoring-write import in `route.ts`
- [ ] `onStepFinish` callback present in the `streamText` call
- [ ] Callback iterates `toolCalls` and fires `writeToolExecutionLog` for each, using closure `queryId`
- [ ] `latency_ms: null` (not fabricated)
- [ ] `tsc --noEmit` shows no new errors in `route.ts` or `monitoring-write.ts`
- [ ] `npm test` passes (same count as before — no regressions)
- [ ] No changes to any file in `platform/src/lib/tools/structured/` or `platform/src/lib/retrieve/`

---

## §5 Hard Constraints

1. **Do not modify `monitoring-write.ts`** — use the existing `writeToolExecutionLog` signature exactly.
2. **Do not touch retrieve tools** — they already self-log; double-logging would corrupt `tool_execution_log`.
3. **Never fabricate latency** — pass `null` for `latency_ms`; do not calculate wall-clock time per tool (onStepFinish fires once per step, not once per tool).
4. **Fire-and-forget only** — the callback must never throw. The `void writeToolExecutionLog(...)` pattern (already used in retrieve tools) is correct.
5. **Session close:** When all ACs pass, set `status: COMPLETE` in this file's frontmatter.

---

## §6 How to Start

Open a new Antigravity window at `/Users/Dev/Vibe-Coding/Apps/Madhav/` and run:
```
Read CLAUDECODE_BRIEF_BHISMA_TOOLS_S1_v1_0.md and execute it.
```
