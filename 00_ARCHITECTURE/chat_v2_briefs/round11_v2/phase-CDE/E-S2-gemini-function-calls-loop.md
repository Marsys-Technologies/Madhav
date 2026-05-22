---
canonical_id: R11E_E_S2
session_id: E-S2
title: Gemini agentic loop — while (finish_reason === 'function_calls')
phase: R11.E
depends_on: [E-S1]
flag: MARSYS_FLAG_R11E_GEMINI_LOOP (server-side, default false — HIGH risk)
client_side: no
authored: 2026-05-22
---

# E-S2 — Gemini function_calls Loop

## Context

Adapt the agentic loop from E-S1 to Gemini's `finish_reason === 'function_calls'` termination signal. Reuse `agentic_loop.ts` engine; Google adapter feeds Gemini-specific iteration.

## Files in Scope

- `platform/src/lib/providers/google/adapter.ts` — `tools()` returns Gemini-specific loop config.
- `platform/src/lib/synthesis/agentic_loop.ts` — extend with provider-pluggable termination check.
- `platform/src/app/api/chat/consume/route.ts` — dispatch via loop when Gemini active + flag=true.
- `platform/src/lib/config/feature_flags.ts` — register flag.

## Files MUST NOT Touch

- Anthropic loop path (E-S1 territory)
- Stream-1 UI files

## Acceptance Criteria

1. With flag=true + Gemini active: loop iterates on `finish_reason === 'function_calls'`.
2. With flag=false: single-shot preserved.
3. Integration test: multi-tool query on Gemini.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -n "finish_reason.*function_calls" src/lib/providers/google/adapter.ts src/lib/synthesis/agentic_loop.ts && echo "PASS"
npx jest --testPathPattern="E-S2|gemini.*loop" --passWithNoTests
```

## Commit Template

```
feat(synthesis): Gemini function_calls agentic loop (E-S2, HIGH RISK)
```

## Decision Log

*(Executor: paste sample Gemini multi-tool trace.)*
