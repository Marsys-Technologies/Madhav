---
canonical_id: R11B_B_S5
session_id: B-S5
title: Sidebar chrome — Claude-compact conversation items, Marsys dark surface preserved
phase: R11.B — Look-and-Feel
depends_on: [B-S4]
flag: MARSYS_FLAG_R11B_LOOK_AND_FEEL + hook
client_side: yes
authored: 2026-05-22
---

# B-S5 — Sidebar Chrome

## Context

Conversation list items adopt Claude's compact shape (`padding: 8px 12px`, `border-radius: 8px`, hover-bg via existing `--sidebar-accent`). The near-ink charcoal sidebar surface + gold-hairline borders + `.brand-cta` New Chat button are preserved verbatim per NATIVE_RULINGS §1.

## Files in Scope

- `platform/src/components/consume/ConversationSidebarV2.tsx` — gate item styling on flag + hook.
- `platform/src/app/globals.css` — `.consume-shell.r11b-active .conversation-list-item` rules.
- Sidebar width: `--sidebar-width: ~17rem` under active state.

## Files MUST NOT Touch

- Sidebar surface bg (near-ink charcoal stays)
- Gold-hairline borders
- `.brand-cta` New Chat button
- Sidebar CRUD logic (R8-S4 pin/archive/folders preserved)
- Provider adapters
- Phase 4C files

## Acceptance Criteria

1. Under active state: conversation items have `padding: 8px 12px`, `border-radius: 8px`, hover-bg.
2. Sidebar width 256-288px range.
3. Conversation title single-line truncated with ellipsis.
4. Gold-hairline borders + dark surface + New Chat button unchanged.
5. R8 features (pin/archive/folders/FTS search) work in both states.
6. No regression with either gate false.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform
grep -n "r11b-active.*conversation\|claude-sidebar" src/components/consume/ConversationSidebarV2.tsx src/app/globals.css && echo "PASS"
npx jest --testPathPattern="ConversationSidebar|B-S5|sidebar-chrome" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): claude-compact sidebar items (B-S5)

Conversation items inside .consume-shell.r11b-active: 8/12 padding, 8px radius,
hover-bg. Marsys near-ink sidebar + gold hairlines + .brand-cta New Chat
preserved.
```

## Decision Log

*(Executor: paste sidebar screenshot with conversation list under active state.)*
