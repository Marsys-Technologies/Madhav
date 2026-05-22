---
canonical_id: R11E_E_S8
session_id: E-S8
title: Iteration cap safety — 8-iteration default with clear error on overflow
phase: R11.E
depends_on: [E-S7]
flag: FLAGLESS
client_side: no
authored: 2026-05-22
---

# E-S8 — Iteration Cap Safety

## Context

If the agentic loop hits 8 iterations without natural `stop_reason: end_turn` / `finish_reason: stop`, return a clear error to the client. Prevents runaway loops + cost spirals.

## Files in Scope

- `platform/src/lib/synthesis/agentic_loop.ts` — MAX_ITERATIONS=8 constant; throw `AgenticLoopCapExceeded` error on overflow.
- `platform/src/app/api/chat/consume/route.ts` — translate the error into a user-facing message in the response stream.

## Files MUST NOT Touch

- Other agentic loop logic
- Stream-1 UI files

## Acceptance Criteria

1. MAX_ITERATIONS=8 constant declared.
2. Configurable via env-var `MARSYS_R11E_MAX_ITERATIONS` if needed (optional).
3. On overflow, returns clear error message to client.
4. Test simulates a hypothetical infinite-loop scenario.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -n "MAX_ITERATIONS\|AgenticLoopCapExceeded" src/lib/synthesis/agentic_loop.ts && echo "PASS"
npx jest --testPathPattern="E-S8|iteration-cap" --passWithNoTests
```

## Commit Template

```
feat(synthesis): 8-iteration cap safety for agentic loop (E-S8)
```

## Decision Log

*(Executor: confirm cap value chosen.)*
