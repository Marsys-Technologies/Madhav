---
canonical_id: R11E_E_S0
session_id: E-S0
title: Tool-loop capability check via adapter manifests
phase: R11.E (within R11.CDE composite)
depends_on: [R11D-MERGE]
flag: FLAGLESS
client_side: no
authored: 2026-05-22
---

# E-S0 — Tool-Loop Capability Check

## Context

Verify each manifest declares `adaptiveToolLoop` correctly:
- Anthropic: `'stop_reason'`
- Google: `'finish_reason_function_calls'`
- OpenAI: `'finish_reason_tool_calls'`
- DeepSeek: `'finish_reason_tool_calls'` (OpenAI-compat)
- NVIDIA: `'finish_reason_tool_calls'` (depends on hosted model)

## Files in Scope

- `platform/tests/providers/tool-loop-capability-check.test.ts` (new).

## Acceptance Criteria

1. All 5 manifests report correct adaptiveToolLoop values.
2. Test passes.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
npx jest --testPathPattern="tool-loop-capability-check|E-S0" --passWithNoTests
```

## Commit Template

```
test(providers): tool-loop capability check (E-S0)
```

## Decision Log

*(Executor: paste manifest readouts.)*
