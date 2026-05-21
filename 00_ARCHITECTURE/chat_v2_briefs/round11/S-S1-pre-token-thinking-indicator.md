---
canonical_id: R11_S_S1
version: 1.0
status: CURRENT
session_id: S-S1
title: Pre-token thinking indicator — animated dot label with elapsed counter before first text_delta
depends_on: []
blocked_on: []
flag: FLAGLESS
flag_default: —
client_side: "yes — additive UI"
authored: 2026-05-21
---

# S-S1 — Pre-Token Thinking Indicator

## Context

Claude.ai shows a small animated dot / shimmer label under the user's message in the ~200-800ms window between "send" and the first token streaming. For extended-thinking models it morphs into "Thinking…" with an elapsed-time counter ("Thought for 12s").

Chat V2 has R8.A streaming-dots and a ReasoningProgress component, but does NOT have a unified pre-token indicator that bridges "request sent" → "first text_delta" with an elapsed counter.

This session is FLAGLESS per Amendment 3 — purely additive UI inside the existing thread surface, no event-shape change.

## Files in Scope

- `platform/src/components/chat/PreTokenIndicator.tsx` (new) — small component that renders an animated dot label + elapsed-seconds counter starting at request-send, hidden once the first text_delta is received.
- `platform/src/components/chat/AssistantMessage.tsx` — mount `<PreTokenIndicator />` at the top of an in-flight assistant message before any text or reasoning blocks have streamed.
- `platform/src/lib/chat-v2/useDataParts.ts` (or equivalent) — expose a derived signal `hasFirstTextDelta` per message so the indicator knows when to unmount.

## Files Must NOT Touch

- The SSE event shape in `route.ts`
- The smooth_stream.ts buffering
- ReasoningProgress (S-S3 owns that)
- Phase 4C files

## Acceptance Criteria

1. **Mount discipline:** indicator mounts when an assistant message slot exists with `status: streaming` AND `hasFirstTextDelta === false`; unmounts on first text_delta.
2. **Animated dot:** dots animate via the existing `@keyframes chat-dot` in globals.css (already defined) — no new keyframes.
3. **Elapsed counter:** for messages where reasoning/thinking parts are present, label reads "Thinking… {N}s" where N updates every second; without reasoning, label reads simply "…".
4. **Click-path (Amendment 2):** send a synthesis query → animated dots appear under the user's message → after ~1-3s the dots disappear and the assistant text begins streaming.
5. **Parent-context integration test (Amendment 2):** mount ConsumeChatV2 with a seeded in-flight assistant message (no text_delta yet) and assert `PreTokenIndicator` is present; advance the stream state to simulate first text_delta and assert it unmounts.
6. **A11y:** indicator has `role="status" aria-live="polite"` so screen readers announce "Thinking" once.

## Pre-commit Gates

```bash
test -f platform/src/components/chat/PreTokenIndicator.tsx && echo "PASS: file exists"
grep -n "PreTokenIndicator" platform/src/components/chat/AssistantMessage.tsx && echo "PASS: mounted"
npx jest --testPathPattern="PreTokenIndicator|S-S1" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): pre-token thinking indicator with elapsed counter

PreTokenIndicator mounts while assistant message is streaming and no text_delta
has arrived; shows animated dots + "Thinking… Ns" counter when reasoning is
present. Unmounts on first text_delta. Flagless per §M.16 (additive UI).

Click-path: send query → dots → text begins → dots disappear.
```

## Decision Log

*(Executor: paste typical wait-time observed before first text_delta on a sample query.)*
