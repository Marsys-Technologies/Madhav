---
canonical_id: R11_V_S2
version: 1.1
status: CURRENT
session_id: V-S2
title: User-bubble dimensions — Claude shape constants, Marsys glassmorphic speech-tail preserved
depends_on: ["V-S1"]
blocked_on: []
flag: MARSYS_FLAG_R11_CLAUDE_RENDERING
flag_default: false
client_side: "yes — UserMessage component inside .consume-shell"
authored: 2026-05-21
amended: 2026-05-21 — rescoped per NATIVE_RULINGS §1 (Marsys palette stays; no .claude-shell palette tokens needed; this session now adjusts user-bubble shape constants only)
---

# V-S2 — User-Bubble Dimensions (Claude Shape, Marsys Skin)

## Context

**Rescope per `NATIVE_RULINGS_v1_0.md §1`:** the Marsys palette is preserved.
This session NO LONGER introduces `.claude-shell` palette tokens (the original
v1.0 scope). Instead it adjusts the user-message bubble to Claude's exact shape
constants (`border-radius: 1rem`, `max-width: 80%`, `padding: 12px 14px`,
right-aligned) while preserving the existing Marsys glassmorphic dark bubble
with gold-tinted hairline border and right-pointing speech-tail pseudo-element
(`.v2-user-bubble::after`).

The goal: a user bubble that visually reads as "Marsys" (gold + ink + speech-tail)
but with Claude's ergonomic dimensions.

## Files in Scope

- `platform/src/components/chat/UserMessage.tsx` — gate the rendering on
  `process.env.NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING`. When flag=true,
  apply Claude shape constants via a new class `v2-user-bubble--claude-shape`
  (or equivalent). When flag=false, current behavior unchanged.
- `platform/src/app/globals.css` — add a `.v2-user-bubble.v2-user-bubble--claude-shape` block:
  - `border-radius: 1rem;`
  - `max-width: 80%;`
  - `padding: 12px 14px;`
  - `margin-left: auto;` (right-align)
  - Speech-tail `::after` pseudo-element preserved verbatim — same `top: 12px`, `right: -7px` offsets, same `border-left: 7px solid oklch(0.24 0.012 80)` color.
- `platform/tests/components/chat/UserMessage-claude-shape.test.tsx` (new) — parent-context test asserting bubble computed styles match the constants above when flag=true.

## Files Must NOT Touch

- `.consume-shell` palette tokens (Marsys gold/charcoal stays)
- Phase 4C files
- Any other chat component

## Acceptance Criteria

1. **Flag client-side + deploy.yml (Amendment 1):** flag handled by V-S1 — V-S2 just reads it; no new flag introduced. Coverage check at R11-MERGE.
2. **Shape constants applied when flag=true:** `border-radius: 1rem` (~16px), `max-width: 80%`, `padding: 12px 14px`, right-aligned.
3. **Speech-tail preserved:** `.v2-user-bubble::after` pseudo-element renders unchanged in both flag states. Color matches the bubble background `oklch(0.24 0.012 80)`.
4. **Gold hairline preserved:** `border: 1px solid rgba(var(--brand-gold-rgb), 0.18)` unchanged.
5. **Click-path (Amendment 2):** with flag=true, send a message — your bubble appears right-aligned, ~16px rounded corners, 80% max-width, with the gold-tinted speech-tail pointing right at the canvas. Document in commit body.
6. **Parent-context integration test (Amendment 2):** mount `<UserMessage>` inside a simulated `ConsumeChatV2` context with flag=true, assert computed `border-radius`, `max-width`, `padding` match constants; assert `::after` pseudo-element is present.
7. **No regression with flag=false:** existing user bubble renders byte-identical.

## Pre-commit Gates

```bash
grep -n "v2-user-bubble--claude-shape\|NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING" platform/src/components/chat/UserMessage.tsx platform/src/app/globals.css
npx jest --testPathPattern="UserMessage|V-S2|claude-shape" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): user-bubble dimensions to Claude shape (V-S2)

UserMessage adopts border-radius 1rem, max-width 80%, padding 12/14 inside
.consume-shell when MARSYS_FLAG_R11_CLAUDE_RENDERING=true. Marsys glassmorphic
speech-tail + gold hairline preserved verbatim.

Click-path: send a message with flag=true → right-aligned ~16px-rounded bubble
with gold speech-tail.
```

## Decision Log

*(Executor: paste a screenshot of a user bubble under both flag states.)*
