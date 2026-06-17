---
title: "BHISMA Phase 2 — Planner Fix: DeepSeek toolChoice / model-ID mismatch"
brief_id: BHISMA_PF_S1
version: 1.0
status: OPEN
created_date: 2026-05-04
session_id: BHISMA-PF-S1
executor: claude-sonnet-4-6
active_phase: "BHISMA Phase 2 — E2E / Planner Quality"
isolation_tier: BHISMA_ONLY
blocked_by: none
must_complete_before: BHISMA-PROMPT-S2
parallel_safe_with: none
---

# BHISMA-PF-S1 — DeepSeek Planner Model-ID Fix

**Set `status: IN_PROGRESS` at session open. Set `status: COMPLETE` only after ALL acceptance criteria pass.**

---

## §0 Context — the bug

`manifest_planner.ts` calls `generateText` with a `submit_plan` tool and
`toolChoice: 'required'` to force the model into structured-output mode (this
approach was originally required for NIM compatibility; it is correct).

The planner model for the DeepSeek stack resolves to `deepseek-v4-flash` (via
`FAMILY_WORKER['deepseek']` and `STACK_ROUTING.deepseek.planner_fast.primary`).

**`deepseek-v4-flash` is not a recognised model ID on the DeepSeek API.**
The API silently maps unrecognised IDs to `deepseek-reasoner` (the R1 / thinking
model). `deepseek-reasoner` explicitly rejects `toolChoice` with:

```
"deepseek-reasoner does not support this tool_choice"
```

Result: 100% planner failure rate on the DeepSeek stack since 2026-05-04.
`plan_json` is NULL on every `query_plan_log` row. The LLM-first planner has
never successfully fired in production.

The correct DeepSeek API model ID for the non-thinking model is `deepseek-chat`
(which the DeepSeek API now routes to its V4 Flash / non-thinking backend).
`deepseek-chat` is already in the model registry and supports `tool_choice`.

Evidence from E2E observation (`query_plan_log` + `llm_call_log`):
- 2 queries, both on DeepSeek stack (synthesis = deepseek-v4-pro)
- Both planner calls: model=deepseek-v4-flash, error="deepseek-reasoner does not support this tool_choice", latency_ms=862/410
- Both fell back to deterministic classify() — plan_json=NULL on every row

---

## §1 Pre-Work Audit

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Confirm FAMILY_WORKER['deepseek'] is currently deepseek-v4-flash
grep -n "FAMILY_WORKER" platform/src/lib/models/registry.ts | grep deepseek

# Confirm STACK_ROUTING.deepseek uses deepseek-v4-flash for planner/worker
grep -n "deepseek-v4-flash" platform/src/lib/models/registry.ts

# Confirm deepseek-chat is present in the registry (it should be)
grep -n "'deepseek-chat'" platform/src/lib/models/registry.ts

# Confirm manifest_planner uses toolChoice: 'required' (this is correct — do NOT change)
grep -n "toolChoice" platform/src/lib/pipeline/manifest_planner.ts
```

---

## §2 Scope of Work

### File 1 — `platform/src/lib/models/registry.ts`

Four targeted changes. No other file needs to change.

#### Change 1 — FAMILY_WORKER: deepseek entry

**Before:**
```typescript
deepseek:  'deepseek-v4-flash',                // tier=mid     $0.14/$0.28  (was deepseek-chat)
```

**After:**
```typescript
deepseek:  'deepseek-chat',                    // non-thinking, supports tool_choice; deepseek-v4-flash is not a valid API model ID
```

#### Change 2 — STACK_ROUTING.deepseek.planner_fast

**Before:**
```typescript
planner_fast: {
  primary:  'deepseek-v4-flash',                        // $0.14/$0.28, fast JSON
  fallback: 'deepseek-v4-pro',                          // fallback with thinking=false
},
```

**After:**
```typescript
planner_fast: {
  primary:  'deepseek-chat',                            // non-thinking, supports toolChoice — deepseek-v4-flash is not a valid API ID
  fallback: 'deepseek-v4-pro',                          // fallback (note: v4-pro maps to thinking mode on API; planner retry path)
},
```

#### Change 3 — STACK_ROUTING.deepseek.context_assembly

**Before:**
```typescript
context_assembly: {
  primary:  'deepseek-v4-flash',                        // 1M ctx, cheapest option
  fallback: 'deepseek-v4-pro',                          // 1M ctx, thinking=false
},
```

**After:**
```typescript
context_assembly: {
  primary:  'deepseek-chat',                            // non-thinking, correct API ID
  fallback: 'deepseek-v4-pro',                          // 1M ctx fallback
},
```

#### Change 4 — STACK_ROUTING.deepseek.worker

**Before:**
```typescript
worker: {
  primary:  'deepseek-v4-flash',                        // $0.14/$0.28, minimal latency
  fallback: 'deepseek-v4-pro',                          // fallback
},
```

**After:**
```typescript
worker: {
  primary:  'deepseek-chat',                            // non-thinking, correct API ID
  fallback: 'deepseek-v4-pro',                          // fallback
},
```

#### Change 5 — deepseek-chat model entry: remove "deprecated" framing

The `deepseek-chat` entry currently reads:
```typescript
hint: '⚠ Deprecated alias → V4 Flash. Will stop working 2026-07-24.',
```

This is now incorrect — `deepseek-chat` is the **active planner model**. Update:

**Before:**
```typescript
{
  id: 'deepseek-chat',
  provider: 'deepseek',
  tier: 'mid',
  label: 'DeepSeek V3 (deprecated)',
  hint: '⚠ Deprecated alias → V4 Flash. Will stop working 2026-07-24.',
  speedTier: 'balanced',
  maxOutputTokens: 8_192,
  capabilities: ['tool-use'],
  role: 'both',
  costPer1MInput: 0.14,   // now routes to V4 Flash pricing
  costPer1MOutput: 0.28,
},
```

**After:**
```typescript
{
  id: 'deepseek-chat',
  provider: 'deepseek',
  tier: 'mid',
  label: 'DeepSeek Chat (V4 Flash)',
  hint: 'DeepSeek planner + worker — non-thinking, supports tool_choice. API alias for V4 Flash non-thinking.',
  speedTier: 'fast',
  maxOutputTokens: 8_192,
  capabilities: ['tool-use'],
  role: 'both',
  costPer1MInput: 0.14,
  costPer1MOutput: 0.28,
},
```

#### Change 6 — deepseek-v4-flash model entry: mark as invalid API ID

Update the `deepseek-v4-flash` entry to make clear it is NOT a valid DeepSeek API
model name (so future sessions don't re-introduce the bug):

Find the `deepseek-v4-flash` model entry and change its `hint` and `label`:

**Before:**
```typescript
{
  id: 'deepseek-v4-flash',
  ...
  label: 'DeepSeek V4 Flash',
  hint: 'DeepSeek Stack planner/worker — 1M context, $0.14 input',
```

**After:**
```typescript
{
  id: 'deepseek-v4-flash',
  ...
  label: 'DeepSeek V4 Flash [internal label only]',
  hint: '⚠ Not a valid DeepSeek API model ID — API maps this to deepseek-reasoner which rejects toolChoice. Use deepseek-chat for planner/worker calls. Retain entry for future if DeepSeek publishes this ID officially.',
```

---

## §3 File Scope

### may_touch
```
platform/src/lib/models/registry.ts    [EDIT — 6 targeted changes, all within this file]
```

### must_not_touch
```
platform/src/lib/pipeline/manifest_planner.ts   [toolChoice:'required' is CORRECT — do NOT change]
platform/src/lib/models/resolver.ts             [no changes needed]
platform/src/lib/pipeline/planner_circuit_breaker.ts
platform/src/app/api/chat/consume/route.ts
platform/src/lib/cache/with_cache.ts
platform/src/lib/synthesis/single_model_strategy.ts
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

- [ ] `FAMILY_WORKER['deepseek']` is `'deepseek-chat'`
- [ ] `STACK_ROUTING.deepseek.planner_fast.primary` is `'deepseek-chat'`
- [ ] `STACK_ROUTING.deepseek.context_assembly.primary` is `'deepseek-chat'`
- [ ] `STACK_ROUTING.deepseek.worker.primary` is `'deepseek-chat'`
- [ ] `deepseek-chat` model entry label and hint no longer say "deprecated"
- [ ] `deepseek-v4-flash` model entry hint warns it is not a valid API ID
- [ ] `grep deepseek-v4-flash platform/src/lib/models/registry.ts` shows it only in the MODELS array definition and the `deepseek-v4-flash` routing entries are gone
- [ ] `tsc --noEmit` — no new errors
- [ ] `npm test` — same pass count as before (no regressions)
- [ ] No changes to `manifest_planner.ts` — `toolChoice: 'required'` remains

---

## §5 Hard Constraints

1. **Do NOT change `manifest_planner.ts`** — `toolChoice: 'required'` is the correct approach for NIM compat. The bug is the wrong model ID, not the calling convention.
2. **Do NOT rename `deepseek-reasoner`** — it is a deprecated alias retained for backward compat with persisted model IDs. Leave it as-is.
3. **Do NOT touch synthesis routing** — `STACK_ROUTING.deepseek.synthesis.primary = 'deepseek-v4-pro'` works in production (confirmed by E2E logs). Do not change it.
4. **Backward-compatible only** — `deepseek-chat` is already in the registry; no new model entries are required. The registry change is purely routing-table updates.
5. **Session close:** When all ACs pass, set `status: COMPLETE` in this file's frontmatter.

---

## §6 Why This Doesn't Affect Other Stacks

- **Anthropic stack**: planner uses `claude-haiku-4-5` → `toolChoice` fully supported ✅
- **Gemini stack**: planner uses `gemini-2.5-flash-lite` → `toolChoice` fully supported ✅
- **GPT stack**: planner uses `gpt-4.1-mini` → `toolChoice` fully supported ✅
- **NIM stack**: planner uses `nvidia/llama-3.3-nemotron-super-49b-v1` → NIM uses the hand-crafted `PlanInputJsonSchema` to avoid `response_format` rejection ✅
- **DeepSeek stack**: planner uses `deepseek-v4-flash` → **maps to deepseek-reasoner on API → rejects toolChoice** ❌ ← THIS FIX

---

## §7 How to Start

Open a new Antigravity window at `/Users/Dev/Vibe-Coding/Apps/Madhav/` and run:
```
Read CLAUDECODE_BRIEF_BHISMA_PF_S1_v1_0.md and execute it.
```
