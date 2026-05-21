---
canonical_id: R11_S_S5
version: 1.0
status: CURRENT
session_id: S-S5
title: Stop-and-retain partial — verify stop button morph + partial-turn persistence
depends_on: ["S-S4"]
blocked_on: []
flag: FLAGLESS
flag_default: —
client_side: "yes — verification + small patch if leaks found"
authored: 2026-05-21
---

# S-S5 — Stop and Retain Partial

## Context

Claude.ai's send button morphs to a filled-square stop button while streaming; clicking stop aborts the SSE and **keeps** the partial assistant turn (committed to conversation history). R6.5 shipped single send/stop button morph in Chat V2. This session verifies parity: (a) the morph is visible, (b) abort actually severs the SSE cleanly, (c) the partial assistant text is persisted to DB.

FLAGLESS per Amendment 3 — verification + small patch if a leak is found.

## Files in Scope

- `platform/src/components/chat/Composer.tsx` — verify send/stop button morph (R6.5 work product).
- `platform/src/lib/chat-v2/useChatRuntime` configuration or the `useChat` from `ai` SDK — verify the abort path commits the partial assistant message.
- `platform/src/app/api/chat/consume/route.ts` — verify the route handler tolerates client abort without leaking compute (closes the stream + flushes any pending audit log).
- `platform/tests/e2e/` — Playwright test simulating: send → wait for first text_delta → click stop → assert partial assistant message persists in DOM and DB.

## Files Must NOT Touch

- The smooth_stream cadence (S-S2 territory)
- The SSE event shape
- Phase 4C files

## Acceptance Criteria

1. **Morph visible:** send button visually transitions to stop when `streaming === true`; back to send when `streaming === false`.
2. **Abort severs cleanly:** clicking stop aborts the fetch via `AbortController.abort()` and the route handler logs `client_disconnect` (or equivalent) without throwing.
3. **Partial persists in UI:** the partial assistant turn remains in the message stream after abort (not removed).
4. **Partial persists in DB:** the partial assistant message row exists in `conversation_messages` (or equivalent table) with the text accumulated up to the abort moment.
5. **Continue idiom works:** user can type "please continue" and the next turn continues the partial.
6. **Click-path (Amendment 2):** send long query → text begins streaming → click stop → partial remains → refresh page → partial still there.
7. **Parent-context integration test (Amendment 2):** mount ConsumeChatV2 with a streaming-state assistant message simulator, click the stop button, assert UI state and a fake DB-persist hook is called with the partial text.

## Pre-commit Gates

```bash
grep -n "AbortController\|signal:\|abort()" platform/src/components/chat/Composer.tsx platform/src/components/consume/ConsumeChatV2.tsx
# E2E test wiring
test -f platform/tests/e2e/chat-v2/stop-and-retain.spec.ts && echo "PASS"
npx jest --testPathPattern="S-S5|stop.?and.?retain" --passWithNoTests
```

## Commit Template

```
test(chat-v2): verify stop button morph + partial-turn persistence (S-S5)

Verifies R6.5 send/stop morph, confirms AbortController commits partial assistant
turn to DB, adds Playwright e2e for the flow. Patches any persistence leak found
during verification (see Decision Log).
```

## Decision Log

*(Executor: paste e2e test output, persisted-partial verification, any leak fixes applied.)*
