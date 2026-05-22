---
canonical_id: R11E_E_S9
session_id: E-S9
title: Tool-loop observability — per-iteration usage in Observatory
phase: R11.E
depends_on: [E-S8]
flag: FLAGLESS
client_side: no
authored: 2026-05-22
---

# E-S9 — Tool-Loop Observability

## Context

Per-iteration `usage` (input + output tokens, plus cache + reasoning + thoughts) emitted to Observatory for each loop iteration. Total cost is the sum across iterations.

## Files in Scope

- `platform/src/lib/synthesis/agentic_loop.ts` — emit per-iteration telemetry.
- `platform/src/lib/observatory/tool_loop_metrics.ts` (new) — aggregation queries.
- `platform/src/components/observatory/ToolLoopMetricsTile.tsx` (new) — dashboard tile.

## Files MUST NOT Touch

- Provider adapters (just consume their telemetry)
- Stream-1 UI files

## Acceptance Criteria

1. Per-iteration usage records emitted.
2. Observatory tile shows: iterations per turn × provider × per-day.
3. Cost-per-turn breakdown by iteration.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
test -f src/lib/observatory/tool_loop_metrics.ts && echo "PASS"
test -f src/components/observatory/ToolLoopMetricsTile.tsx && echo "PASS"
npx jest --testPathPattern="E-S9|tool_loop_metrics" --passWithNoTests
```

## Commit Template

```
feat(observatory): tool-loop iteration telemetry + dashboard tile (E-S9)
```

## Decision Log

*(Executor: paste tile screenshot.)*
