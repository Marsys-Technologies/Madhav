---
canonical_id: R11C_C_S6
session_id: C-S6
title: Stop button morph + partial-turn DB persistence verified across all 5 providers
phase: R11.C
depends_on: [C-S5]
flag: FLAGLESS (verification + small patch if leaks found)
client_side: yes
authored: 2026-05-22
---

# C-S6 — Stop and Retain Partial

## Context

R6.5 shipped send/stop morph. Verify: (a) morph visible on all 5 stacks, (b) AbortController severs SSE cleanly, (c) partial assistant turn persists to DB. Patch any leak found.

## Files in Scope

- `platform/src/components/chat/Composer.tsx` — verify R6.5 morph (no edits unless leak found).
- `platform/src/components/consume/ConsumeChatV2.tsx` — verify abort handler.
- `platform/src/app/api/chat/consume/route.ts` — verify client-disconnect handling.
- `platform/tests/e2e/chat-v2/stop-and-retain-r11c.spec.ts` (new) — Playwright e2e: send long query → click stop → verify partial in DOM + DB.

## Files MUST NOT Touch

- smooth_stream cadence (C-S2 territory)
- SSE event shape
- Stream-1 UI files

## Acceptance Criteria

1. Send→stop morph visible on all 5 stacks.
2. AbortController abort severs SSE; route logs `client_disconnect`.
3. Partial assistant turn persists to DB (`conversation_messages` row).
4. Page refresh shows partial.
5. e2e test covers the flow on at least Anthropic + Gemini (the two highest-traffic stacks).

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
test -f tests/e2e/chat-v2/stop-and-retain-r11c.spec.ts && echo "PASS"
npx jest --testPathPattern="C-S6|stop.?and.?retain" --passWithNoTests
```

## Commit Template

```
test(chat-v2): verify stop button morph + partial persistence (C-S6)
```

## Decision Log

*(Executor: paste e2e report + any leak fixes.)*
