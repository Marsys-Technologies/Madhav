---
canonical_id: R11B_B_S3
session_id: B-S3
title: Bubble-less assistant + 768px centered column + hover-reveal action bar
phase: R11.B — Look-and-Feel
depends_on: [B-S2]
flag: MARSYS_FLAG_R11B_LOOK_AND_FEEL (same) AND useMultiProviderParity() hook
client_side: yes
authored: 2026-05-22
---

# B-S3 — Message-Container Shape

## Context

Adopt Claude's signature asymmetric pattern: assistant messages bubble-less (text directly on canvas); message stream pinned to 768px (`48rem`) centered column; action bar (copy/retry/branch) reveals on hover only.

## Files in Scope

- `platform/src/components/chat/AssistantMessage.tsx` — under active state, remove card chrome (no bg, no border, no padding at message level).
- `platform/src/components/consume/ConsumeChatV2.tsx` — under active state, pin message-stream column to `max-width: 48rem` centered; `gap-6` to `gap-8` between messages.
- `platform/src/components/chat/MessageActionBar.tsx` — under active state, default `opacity-0`; `group-hover:opacity-100` + `focus-within:opacity-100`.
- `platform/src/app/globals.css` — supporting rules inside `.consume-shell.r11b-active`.
- Tests.

## Files MUST NOT Touch

- `.consume-shell` palette
- `v2-user-bubble` (B-S2 territory)
- Provider adapters
- Phase 4C files

## Acceptance Criteria

1. Under active state: assistant element has no background, no border, no inline padding at message level.
2. Message stream column `max-width: 48rem` centered horizontally.
3. Gap between message turns ~24-32px (`gap-6` or `gap-8`).
4. Action bar reveals on parent hover or keyboard focus.
5. Sacred components inside the column (PerMessageDetailsDrawer attach points) untouched.
6. No regression with either gate false.
7. Click-path: open consume → flag+hook active → see asymmetric layout.
8. Parent-context test: assert assistant has no background-color + column computed max-width = 768px.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform
grep -n "r11b-active.*AssistantMessage\|claude-shape\|max-width.*48rem" src/components/chat/AssistantMessage.tsx src/components/consume/ConsumeChatV2.tsx src/app/globals.css
npx jest --testPathPattern="AssistantMessage|message-container|B-S3" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): asymmetric message containers + 768px column (B-S3)

Bubble-less assistant; 768px centered column; hover-reveal action bar — all
inside .consume-shell.r11b-active. Marsys palette preserved.
```

## Decision Log

*(Executor: paste 3-message exchange screenshot under active state.)*
