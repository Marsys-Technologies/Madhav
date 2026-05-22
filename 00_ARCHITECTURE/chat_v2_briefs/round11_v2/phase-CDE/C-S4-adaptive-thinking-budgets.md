---
canonical_id: R11C_C_S4
session_id: C-S4
title: Adaptive thinking budgets per provider — thinking.effort / thinkingBudget / polyfill
phase: R11.C
depends_on: [C-S3]
flag: FLAGLESS (server-side parameter selection)
client_side: "no — adapter-level config helpers"
authored: 2026-05-22
---

# C-S4 — Adaptive Thinking Budgets

## Context

Each provider's adapter `thinking()` method returns the right config for that provider:
- Anthropic: `{ type: 'enabled', effort: 'medium' }` for Opus 4.6+/Sonnet 4.6+; `{ type: 'enabled', budget_tokens: N }` for older.
- Gemini: keep existing `thinkingBudget: 24576` from registry.ts (preserve verbatim).
- DeepSeek R1: `{ thinking: true }` toggle.
- OpenAI: polyfill via system-prompt CoT nudge (since o-series removed from codebase). OR leave thinking unsupported and rely on hide-and-hint.
- NVIDIA: depends on hosted model; conservative default null (capability hint shows "Switch to Anthropic/Gemini for adaptive thinking").

## Files in Scope

- `platform/src/lib/providers/anthropic/adapter.ts` — implement `thinking()` method with effort branching.
- `platform/src/lib/providers/google/adapter.ts` — implement `thinking()` returning the existing thinkingBudget.
- `platform/src/lib/providers/openai/adapter.ts` — implement `thinking()` either as null (hide-and-hint) or CoT polyfill — executor decides + documents.
- `platform/src/lib/providers/deepseek/adapter.ts` — implement `thinking()` with toggle.
- `platform/src/lib/providers/nvidia/adapter.ts` — implement `thinking()` returning null.
- `platform/src/lib/synthesis/thinking_config.ts` (new or extended) — helper that dispatches via active provider's adapter.

## Files MUST NOT Touch

- `registry.ts` thinkingBudget value (preserve)
- Existing reasoning extraction middleware
- Stream-1 UI files

## Acceptance Criteria

1. Each adapter's `thinking()` method returns the right shape for its provider.
2. Existing Gemini path preserved (24576 budget).
3. Existing DeepSeek `<think>` extraction preserved.
4. No regression on any provider.
5. Tests verify per-provider request shape.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
for p in anthropic google openai deepseek nvidia; do
  grep -n "thinking:" src/lib/providers/$p/adapter.ts && echo "PASS: $p thinking method"
done
npx jest --testPathPattern="thinking-config|C-S4|adaptive-thinking" --passWithNoTests
```

## Commit Template

```
feat(providers): adaptive thinking budgets per provider (C-S4)
```

## Decision Log

*(Executor: paste per-provider thinking config + sample request bodies.)*
