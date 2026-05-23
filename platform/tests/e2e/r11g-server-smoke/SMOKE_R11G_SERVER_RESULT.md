---
session: G-S5
arc: R11.G
date: 2026-05-23
status: PASS
tests_passed: 13
tests_total: 13
---

# R11.G G-S5 — Server-Side Integration Smoke Results

## Run command

```
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11G/platform && pnpm vitest run tests/e2e/r11g-server-smoke/
```

## Per-test grid

| Test name | File | PASS/FAIL | Notes |
|---|---|---|---|
| 3 iterations: iter1=msr_sql tool, iter2=lel_query tool, iter3=final answer | tool-executor-loop.test.ts | PASS | 3 chat() calls verified; tool input JSON parsed from concatenated partialJson deltas; both tool results (2-result msr_sql + 1-result lel_query) flow into next iteration messages; final end_turn answer verified |
| click gear → data-testid="settings-dropdown-menu" becomes visible | settings-dropdown.test.tsx | PASS | Gear click opens menu |
| click "Claude-style chat" radio → localStorage["marsys.chatShellMode"] = "multi-provider" | settings-dropdown.test.tsx | PASS | localStorage write verified |
| click "Classic Marsys" radio → localStorage["marsys.chatShellMode"] = "classic" | settings-dropdown.test.tsx | PASS | Storage seeded as multi-provider; classic radio click reverts to 'classic' |
| click outside menu → menu closes | settings-dropdown.test.tsx | PASS | mousedown on document.body dismisses menu |
| gear aria-expanded=false initially, true after click, false after outside click | settings-dropdown.test.tsx | PASS | aria state lifecycle verified |
| menu shows "Classic Marsys" and "Claude-style chat" options | settings-dropdown.test.tsx | PASS | Both data-testids and label text present |
| gear button is present when PARITY_ENV_ENABLED is mocked to true | settings-dropdown.test.tsx | PASS | Component renders when env enabled |
| middle iteration tool fails → loop continues → model receives error string → final answer produced | tool-error-recovery.test.ts | PASS | DB connection error → ERROR: string in tool_result → second iteration runs → final text produced; loop never threw |
| loop does NOT abort when tool returns ERROR string — isError=true result propagates cleanly | tool-error-recovery.test.ts | PASS | Unknown tool → ERROR: toolname string propagates cleanly |
| AgenticLoopCapExceeded is thrown only on iteration cap — NOT on tool errors | tool-error-recovery.test.ts | PASS | Persistent tool failure with always-tool_use stop → AgenticLoopCapExceeded at MAX_ITERATIONS (8); error is specifically AgenticLoopCapExceeded, not generic error |
| single iteration with 2 tool calls: both execute, both results feed back into next messages | multi-tool-fan-out.test.ts | PASS | Promise.all execution verified; msr_sql input {signal_type,limit} + panchanga input {date} both parsed and dispatched; 2 tool_use + 2 tool_result in messages; final answer produced |
| one tool fails, other succeeds — both results (success + error) flow back | multi-tool-fan-out.test.ts | PASS | Mixed fan-out: one ERROR string + one valid JSON result both in user turn; loop does not abort |

## Summary

- **Test files:** 4 (tool-executor-loop, tool-error-recovery, multi-tool-fan-out, settings-dropdown)
- **Tests passed:** 13 / 13
- **Tests failed:** 0
- **New failures introduced to root suite:** 0 (10 pre-existing failures confirmed against KNOWN_PRE_EXISTING_FAILURES.md baseline)

## Key verifications

### Iteration counts + tool exec counts

- `tool-executor-loop.test.ts`: 3 iterations, 2 tool executions (msr_sql × 1, lel_query × 1)
- `tool-error-recovery.test.ts` (middle-iter): 2 iterations, 1 tool execution attempt (failed), loop continued
- `tool-error-recovery.test.ts` (cap-breach): MAX_ITERATIONS (8) iterations, 8 tool execution attempts (all failed), AgenticLoopCapExceeded thrown
- `multi-tool-fan-out.test.ts` (2 tools): 2 iterations, 2 tool executions (msr_sql + query_panchanga) in iteration 1 via Promise.all
- `multi-tool-fan-out.test.ts` (mixed): 2 iterations, 2 tool execution attempts (1 fail + 1 success) via Promise.all

### Error-recovery verification

- `executeMCPTool` returns `"ERROR: ..."` string (never throws) for both unknown tools and tool.retrieve() rejections
- `safeExecuteTool` in `agentic_loop.ts` wraps the executor and catches any remaining throws → `isError=true` LoopToolResult
- Neither path aborts the loop; both paths produce a `tool_result` content block that the model receives
- `AgenticLoopCapExceeded` is only raised by `checkIterationCap()`, not by any tool failure path

### vitest.config.ts amendment

Root `vitest.config.ts` exclude updated: replaced `tests/e2e/**` glob with per-suite excludes for Playwright paths, allowing `tests/e2e/r11g-server-smoke/` to run via the standard `pnpm vitest run tests/e2e/r11g-server-smoke/` command. A local `vitest.config.ts` within the smoke directory also exists as a backup for isolated runs.
