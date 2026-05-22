---
canonical_id: R11E_E_S4
session_id: E-S4
title: DeepSeek agentic loop — OpenAI-compatible finish_reason
phase: R11.E
depends_on: [E-S3]
flag: MARSYS_FLAG_R11E_DEEPSEEK_LOOP (server-side, default false)
client_side: no
authored: 2026-05-22
---

# E-S4 — DeepSeek Loop

## Context

DeepSeek uses OpenAI-compatible function calling. Reuse E-S3's pattern. Preserve `<think>` middleware throughout (the loop must continue passing reasoning blocks through the unified surface).

## Files in Scope

- `platform/src/lib/providers/deepseek/adapter.ts` — `tools()` returns DeepSeek loop config.
- `platform/src/lib/synthesis/agentic_loop.ts` — verify reasoning-block pass-through.

## Files MUST NOT Touch

- `extractReasoningMiddleware` (preserve)
- Other providers' loop paths

## Acceptance Criteria

1. DeepSeek loop iterates correctly with flag=true.
2. `<think>` blocks still extracted and surfaced as reasoning parts even during loop iterations.
3. Integration test.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -n "extractReasoningMiddleware\|<think>" src/lib/providers/deepseek/adapter.ts && echo "PASS"
npx jest --testPathPattern="E-S4|deepseek.*loop" --passWithNoTests
```

## Commit Template

```
feat(synthesis): DeepSeek agentic loop with reasoning preservation (E-S4)
```

## Decision Log

*(Executor: paste sample trace showing <think> blocks preserved.)*
