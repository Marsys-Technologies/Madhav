---
canonical_id: R11C_C_S3
session_id: C-S3
title: Extended-thinking auto-collapse on first text_delta + cross-provider unification
phase: R11.C
depends_on: [C-S2]
flag: FLAGLESS (heuristic extension)
client_side: yes
authored: 2026-05-22
---

# C-S3 — Extended-Thinking Auto-Collapse

## Context

Extend Y-S4's `ReasoningProgress` with auto-collapse triggered when the first text_delta arrives (in addition to existing >2000-token rule). Unify the reasoning surface across Anthropic `thinking` content blocks + Gemini native reasoning UIMessage parts + DeepSeek `<think>` middleware extracted parts (the existing surface already handles all three; this session adds the collapse heuristic).

## Files in Scope

- `platform/src/components/chat/ReasoningProgress.tsx` — add `hasFirstTextDelta` consumer + collapse heuristic.
- `platform/src/lib/chat-v2/useDataParts.ts` — confirm `hasFirstTextDelta` is exposed (added in C-S1).

## Files MUST NOT Touch

- Y-S4 step-marker parsing (preserve)
- Existing >2000-token collapse rule (preserve)
- Provider adapters
- Stream-1 UI files

## Acceptance Criteria

1. When `hasFirstTextDelta` flips false → true, ReasoningProgress transitions from expanded → collapsed.
2. Manual user toggle preserved within the same message lifetime.
3. >2000-token rule preserved.
4. Works for Anthropic + Gemini + DeepSeek paths (existing unified surface).
5. Parent-context test verifies collapse on text_delta event.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -n "hasFirstTextDelta" src/components/chat/ReasoningProgress.tsx && echo "PASS"
npx jest --testPathPattern="ReasoningProgress|C-S3" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): ext-thinking auto-collapse on first text_delta (C-S3)
```

## Decision Log

*(Executor: paste sample timing data per provider.)*
