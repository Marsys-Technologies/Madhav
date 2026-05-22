---
canonical_id: R11E_E_S6
session_id: E-S6
title: Interleaved text + tool block streaming — Claude 4.x + Gemini 2.5 patterns
phase: R11.E
depends_on: [E-S5]
flag: FLAGLESS (handled via per-provider loop config)
client_side: yes (UI rendering verifies ordering)
authored: 2026-05-22
---

# E-S6 — Interleaved Text + Tool

## Context

Claude 4.x + Gemini 2.5 can emit text BEFORE a tool call within a single assistant turn. The unified ChatEvent stream must honor that ordering so the UI renders text-then-card-then-text correctly. ToolCallCard rendering from C-S5 expects stream-order; verify the order survives loop iterations.

## Files in Scope

- `platform/src/lib/synthesis/agentic_loop.ts` — verify interleaved ordering preserved.
- `platform/src/lib/chat-v2/useDataParts.ts` — confirm stream-position ordering.
- `platform/tests/synthesis/interleaved-text-tool.test.ts` (new) — assert ordering.

## Files MUST NOT Touch

- ToolCallCard rendering (C-S5)
- Stream-1 UI files

## Acceptance Criteria

1. Multi-tool Anthropic response with interleaved text + tool_use blocks renders DOM children in source order.
2. Same for Gemini interleaved response.
3. Test passes for both.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
npx jest --testPathPattern="E-S6|interleaved" --passWithNoTests
```

## Commit Template

```
feat(synthesis): interleaved text+tool stream-order verified (E-S6)
```

## Decision Log

*(Executor: paste test report showing ordering preserved.)*
