---
canonical_id: R11E_E_S5
session_id: E-S5
title: NVIDIA NIM agentic loop — hosted-model dependent
phase: R11.E
depends_on: [E-S4]
flag: MARSYS_FLAG_R11E_NVIDIA_LOOP (server-side, default false)
client_side: no
authored: 2026-05-22
---

# E-S5 — NVIDIA Loop

## Context

NVIDIA NIM hosts many open-weight models; tool-loop support depends on the active model. For models that support OpenAI-compatible tool calls, reuse E-S3's pattern. For models that don't, the adapter throws `CapabilityUnsupportedError` and the dispatcher surfaces a hide-and-hint.

## Files in Scope

- `platform/src/lib/providers/nvidia/adapter.ts` — `tools()` returns loop config when active model supports; throws otherwise.
- `platform/src/lib/synthesis/agentic_loop.ts` — verify NVIDIA path.

## Files MUST NOT Touch

- `NVIDIA_PLANNER_ENABLED` planner routing (preserve)
- Other providers' loop paths

## Acceptance Criteria

1. For models supporting OpenAI-compat tools: loop iterates correctly.
2. For other models: CapabilityUnsupportedError thrown; UI surfaces hint.
3. Existing NVIDIA planner path preserved.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -n "NVIDIA_PLANNER_ENABLED" src/lib/providers/nvidia/adapter.ts || echo "INFO: planner routing lives elsewhere"
npx jest --testPathPattern="E-S5|nvidia.*loop" --passWithNoTests
```

## Commit Template

```
feat(synthesis): NVIDIA NIM agentic loop (E-S5)
```

## Decision Log

*(Executor: document which hosted models support tools; paste sample trace.)*
