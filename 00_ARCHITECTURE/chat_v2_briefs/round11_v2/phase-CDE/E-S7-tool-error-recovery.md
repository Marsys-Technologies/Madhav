---
canonical_id: R11E_E_S7
session_id: E-S7
title: Tool error recovery — model sees error result, retries or pivots
phase: R11.E
depends_on: [E-S6]
flag: FLAGLESS
client_side: no
authored: 2026-05-22
---

# E-S7 — Tool Error Recovery

## Context

When a tool execution fails (timeout, error, no result), the agentic loop returns the error to the model as a tool_result. The model decides to retry the tool with different args or pivot to a different tool. Loop continues.

## Files in Scope

- `platform/src/lib/synthesis/agentic_loop.ts` — error capture + propagation as tool_result content.
- `platform/tests/synthesis/tool-error-recovery.test.ts` (new).

## Files MUST NOT Touch

- Tool implementations (preserve)
- Stream-1 UI files

## Acceptance Criteria

1. Tool execution failure returns error as tool_result to the model.
2. Loop continues for up to iteration cap.
3. Final response references the error gracefully (model knows the tool failed).
4. Test simulates a failing tool + verifies graceful recovery.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
npx jest --testPathPattern="E-S7|tool-error-recovery" --passWithNoTests
```

## Commit Template

```
feat(synthesis): tool error recovery in agentic loop (E-S7)
```

## Decision Log

*(Executor: paste sample failing-tool trace.)*
