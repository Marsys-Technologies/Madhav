---
canonical_id: R11B_B_S2
session_id: B-S2
title: User-bubble dimensions — Claude shape constants, Marsys speech-tail preserved
phase: R11.B — Look-and-Feel
depends_on: [B-S1]
flag: MARSYS_FLAG_R11B_LOOK_AND_FEEL (same as B-S1) AND useMultiProviderParity() hook
client_side: yes
authored: 2026-05-22
---

# B-S2 — User-Bubble Dimensions

## Context

Adopt Claude's user-bubble shape constants (`border-radius: 1rem`, `max-width: 80%`, `padding: 12px 14px`, right-aligned) while preserving the existing Marsys glassmorphic dark bubble with gold-tinted hairline + speech-tail pseudo-element (`.v2-user-bubble::after`).

## Files in Scope

- `platform/src/components/chat/UserMessage.tsx` — gate on flag + hook; when active, apply `v2-user-bubble--r11b-shape` class.
- `platform/src/app/globals.css` — `.consume-shell.r11b-active .v2-user-bubble` rules: border-radius 1rem, max-width 80%, padding 12/14, margin-left auto. Speech-tail `::after` preserved verbatim.
- Tests.

## Files MUST NOT Touch

- The existing `.v2-user-bubble::after` speech-tail pseudo-element (preserve)
- Gold hairline border styling (preserve)
- `.consume-shell` palette tokens
- Provider adapters
- Phase 4C files

## Acceptance Criteria

1. With flag+hook both true: user bubble renders with `border-radius: 1rem`, `max-width: 80%`, `padding: 12px 14px`, right-aligned.
2. Speech-tail `::after` pseudo-element unchanged in either state.
3. Gold-tinted border `rgba(var(--brand-gold-rgb), 0.18)` unchanged.
4. With either gate false: existing user bubble renders byte-identical.
5. Click-path: send a message under active state → right-aligned ~16px rounded bubble with gold speech-tail.
6. Parent-context test asserts computed `border-radius`, `max-width`, `padding`.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform
grep -n "v2-user-bubble--r11b-shape\|r11b-active .v2-user-bubble" src/components/chat/UserMessage.tsx src/app/globals.css && echo "PASS"
npx jest --testPathPattern="UserMessage|B-S2|user-bubble" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): user-bubble Claude shape constants (B-S2)

UserMessage inside .consume-shell.r11b-active adopts border-radius 1rem,
max-width 80%, padding 12/14, right-align. Marsys speech-tail + gold border
preserved verbatim.
```

## Decision Log

*(Executor: paste before/after screenshots.)*
