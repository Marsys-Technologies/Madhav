---
canonical_id: R11C_C_S1
session_id: C-S1
title: Pre-token thinking indicator — "Thinking… Ns" affordance pre-first-text-delta
phase: R11.C
depends_on: [C-S0]
flag: FLAGLESS (additive UI)
client_side: yes
authored: 2026-05-22
---

# C-S1 — Pre-Token Thinking Indicator

## Context

Render a small animated dot + elapsed counter ("Thinking… 7s") under the user's message during the gap between send and first text_delta. For thinking-capable models (Anthropic/Gemini/DeepSeek) the label is "Thinking… Ns"; for non-thinking models, just an animated dot.

## Files in Scope

- `platform/src/components/chat/PreTokenIndicator.tsx` (new) — small component reading the per-message stream state.
- `platform/src/components/chat/AssistantMessage.tsx` — mount the indicator at the top of an in-flight message before first text_delta.
- `platform/src/lib/chat-v2/useDataParts.ts` — expose `hasFirstTextDelta` per message.

## Files MUST NOT Touch

- Stream-1 visual rendering (R11.B doesn't change first-text-delta detection)
- Provider adapters
- Phase 4C

## Acceptance Criteria

1. PreTokenIndicator renders for in-flight messages with `hasFirstTextDelta === false`.
2. For thinking-capable models, label shows "Thinking… {N}s" with N updating each second.
3. Unmounts on first text_delta.
4. A11y: `role="status" aria-live="polite"`.
5. Click-path documented.
6. Parent-context test asserts render + unmount.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
test -f src/components/chat/PreTokenIndicator.tsx && echo "PASS"
grep -n "PreTokenIndicator" src/components/chat/AssistantMessage.tsx && echo "PASS"
npx jest --testPathPattern="PreTokenIndicator|C-S1" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): pre-token thinking indicator (C-S1)
```

## Decision Log

*(Executor: typical wait-time pre-first-delta per provider.)*
