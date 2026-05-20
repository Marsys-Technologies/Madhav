---
canonical_id: R10_X_S7
version: 1.0
status: CURRENT
session_id: X-S7
title: Font-size control — Aa+/Aa- in chat header
depends_on: [X-S6]
blocked_on: []
flag: FLAGLESS
flag_default: ~
client_side: "yes — settings-driven CSS variable, no backend"
authored: 2026-05-20
---

# X-S7 — Font-Size Control

## Context

Users reading long astrological synthesis responses benefit from being able to adjust the chat text size. This session adds Aa+/Aa− controls in the Chat V2 header that cycle through four text scales. The current scale is stored in `useChatPreferences` and applied as a CSS custom property (`--text-scale`) on the chat root element.

**Amendment 3:** FLAGLESS — settings-driven preference, no behavior change, no backend impact.

**Amendment 2:** Visible component (Aa+/Aa− buttons in header) → click-path and parent-context test required.

## Files in Scope

- `platform/src/hooks/chat-v2/useChatPreferences.ts` — add `textScale` field with enum `{0.875, 1.0, 1.125, 1.25}`, persisted to localStorage
- `platform/src/components/chat-v2/header/ChatHeader.tsx` (or equivalent) — add Aa+/Aa− buttons
- `platform/src/components/chat-v2/messages/MarkdownContent.tsx` — apply `font-size: calc(1rem * var(--text-scale, 1))` on prose text
- Chat root component (ConsumeChat V2 or layout wrapper) — apply `--text-scale` CSS var from preference
- `platform/tests/` — integration test

## Files Must NOT Touch

- Server-side files
- Phase 4C files
- `.github/workflows/deploy.yml`

## Acceptance Criteria

1. **click-path (Amendment 2):** User path: Chat V2 → header → click "Aa+" → message text grows by one step → click again → grows to max → further clicks no-op → click "Aa−" → shrinks one step. Document in commit body.
2. **Four scales:** `0.875` (small), `1.0` (default), `1.125` (large), `1.25` (xlarge). Cycling past max/min clamps (no wrap-around).
3. **CSS variable:** `--text-scale` is set on the chat root (or `:root` scoped to chat) from the current preference value. `MarkdownContent` prose uses `font-size: calc(1rem * var(--text-scale, 1))`.
4. **Persistence:** `textScale` is stored in `useChatPreferences` localStorage namespace. Survives page refresh.
5. **Default:** 1.0 (no change from current behavior for users who never touch the control).
6. **Accessibility:** Aa+ button aria-label `"Increase text size"`, Aa− `"Decrease text size"`. At max scale Aa+ is visually disabled (`aria-disabled="true"`); at min scale Aa− similarly.
7. **Parent-context integration test (Amendment 2):** At least one test mounts `ChatHeader` within `ChatPrefsCtxProvider` (real context, not injected props) and asserts: (a) clicking Aa+ increments textScale in context, (b) `MarkdownContent` rendered within the same tree reflects updated CSS var. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
npx jest --testPathPattern="textScale|fontScale|ChatHeader|font-size|Aa" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): Aa+/Aa− font-size control in header

useChatPreferences gains textScale (0.875/1.0/1.125/1.25), persisted to
localStorage. --text-scale CSS var on chat root; MarkdownContent prose
flexes via calc. Aa+/Aa− buttons in header with aria labels. Flagless
per §M.16.

Click-path: header → Aa+ → text grows → Aa− → shrinks.
```

## Decision Log

*(Executor: record any decisions or deviations here at close.)*
