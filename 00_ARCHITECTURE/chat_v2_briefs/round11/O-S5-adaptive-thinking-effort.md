---
canonical_id: R11_O_S5
version: 1.0
status: CURRENT
session_id: O-S5
title: Adaptive thinking — switch to `thinking.effort` on Opus 4.6+ / Sonnet 4.6+
depends_on: ["O-S4"]
blocked_on: []
flag: FLAGLESS
flag_default: —
client_side: "no — server-side parameter swap"
authored: 2026-05-21
---

# O-S5 — Adaptive Thinking Effort

## Context

Anthropic's extended-thinking docs (current as of 2026): `thinking.budget_tokens` is **deprecated on Opus 4.6 and Sonnet 4.6** — replaced by `thinking.effort` ("adaptive thinking"), which lets the model size its own budget. For Opus 4.7 and newer, `thinking.effort` is the canonical parameter.

If Chat V2's synthesis call currently sets `thinking.budget_tokens` for these models, swap to `thinking.effort`. Idempotent and FLAGLESS per Amendment 3 — server-side parameter swap, no behavior change for older models (which still take budget_tokens).

## Files in Scope

- `platform/src/app/api/chat/consume/route.ts` (or the synthesis client wrapper) — detect model id, branch on it:
  - `opus-4-7`, `opus-4-6`, `sonnet-4-6` → use `thinking: { type: 'enabled', effort: <level> }`
  - older models (haiku-4-5, sonnet-4-5, etc., if any in use) → keep `thinking.budget_tokens`
- `platform/src/lib/synthesis/thinking_config.ts` (new) — single helper `getThinkingConfig(modelId, queryDifficulty)` returning the right param shape.

## Files Must NOT Touch

- Model selection logic (separate concern)
- Synthesis prompt (preservation rule from Amendment 4)
- Phase 4C files

## Acceptance Criteria

1. **Model-branching:** `getThinkingConfig` returns `{ type: 'enabled', effort: <level> }` for the listed adaptive-thinking models and `{ type: 'enabled', budget_tokens: <int> }` for others.
2. **Effort level:** default to `'medium'` (or whatever the docs prescribe as the model-chooses-its-own-budget default); document choice in Decision Log.
3. **Idempotent under load:** running 5 sample queries through the new code path produces same-shape output as before (no behavior regression).
4. **Click-path (Amendment 2 — server behavior):** send a synthesis query on Opus 4.7 → log inspection shows `thinking.effort` was sent (not `budget_tokens`).
5. **Parent-context integration test (Amendment 2):** mock-API test verifies the request body contains the correct `thinking` shape for each listed model.
6. **No flag:** this is a server-side parameter swap with no UX change visible to the user; FLAGLESS per Amendment 3.

## Pre-commit Gates

```bash
test -f platform/src/lib/synthesis/thinking_config.ts && echo "PASS"
grep -n "thinking.effort\|thinking.budget_tokens" platform/src/lib/synthesis/thinking_config.ts platform/src/app/api/chat/consume/route.ts
npx jest --testPathPattern="O-S5|thinking-config|adaptive-thinking" --passWithNoTests
```

## Commit Template

```
feat(synthesis): adaptive thinking.effort on Opus 4.6+ / Sonnet 4.6+ (O-S5)

getThinkingConfig branches on modelId: thinking.effort for adaptive-thinking
models, thinking.budget_tokens for older. Flagless per §M.16 (server-side
parameter swap, no UX change).
```

## Decision Log

*(Executor: paste effort level chosen, model-id branch table, sample request body diff.)*
