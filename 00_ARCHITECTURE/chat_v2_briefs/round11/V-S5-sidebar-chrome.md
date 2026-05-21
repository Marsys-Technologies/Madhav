---
canonical_id: R11_V_S5
version: 1.0
status: CURRENT
session_id: V-S5
title: Sidebar chrome — 260-280px, light surface, simple list items, hover-reveal hover-bg
depends_on: ["V-S4"]
blocked_on: []
flag: MARSYS_FLAG_R11_CLAUDE_RENDERING
flag_default: false
client_side: "yes — component styling inside .consume-shell, gated by MARSYS_FLAG_R11_CLAUDE_RENDERING"
authored: 2026-05-21
amended: 2026-05-21 — per NATIVE_RULINGS §1: sidebar bg + brand-gold hairlines + brand-cta New Chat button PRESERVED. Only conversation-item shape (padding 8/12, border-radius 8px, hover-bg via existing --sidebar-accent) and sidebar width (~272px) change. The near-ink charcoal sidebar surface is kept.
---

# V-S5 — Sidebar Chrome

## Context

Claude.ai's sidebar is **~260-280px wide**, light surface, with conversation list items at `padding: 8px 12px`, `border-radius: 8px`, hover-bg `#EFE9DE`, active-bg `#E5E0D6`. Title text is 14px sans, single-line truncated.

Chat V2 today uses `.consume-shell` near-ink charcoal sidebar with gold accents. This session adds a `.claude-shell` variant — light surface, minimal chrome — without touching the consume-shell sidebar.

## Files in Scope

- `platform/src/components/consume/ConversationSidebarV2.tsx` — confirm element classes are stable for `.claude-shell` descendant styling.
- `platform/src/app/globals.css` — add `.claude-shell` sidebar token block:
  - `--sidebar: oklch(0.965 0.006 75)` (light surface, slightly off-canvas)
  - `--sidebar-foreground: oklch(0.20 0.006 75)`
  - `--sidebar-accent: oklch(0.94 0.008 75)` (hover bg)
  - `--sidebar-border: oklch(0.91 0.008 75)`
- Conversation list item styling: `padding: 8px 12px`, `border-radius: 8px`, hover `bg-[var(--sidebar-accent)]`, active state slightly darker, title truncated single-line at 14px.
- Sidebar width: `--sidebar-width: 17rem` (~272px) inside `.claude-shell`.

## Files Must NOT Touch

- `.consume-shell` sidebar styling (preserved)
- Sidebar logic (collapse/expand state, conversation CRUD)
- Phase 4C files

## Acceptance Criteria

1. **Light surface tokens:** `.claude-shell --sidebar` and friends are defined per spec.
2. **Width:** sidebar computed width is between 256px and 288px inside `.claude-shell`.
3. **List item shape:** each conversation item has `padding: 8px 12px`, `border-radius: 8px`, hover state lifts to `var(--sidebar-accent)`.
4. **Title truncation:** conversation title is single-line with text-overflow ellipsis.
5. **No regression with flag=false:** `.consume-shell` near-ink sidebar renders identically.
6. **Click-path:** consume route with flag=true → sidebar is a light off-cream column with minimal conversation items.
7. **Parent-context integration test:** mount ConsumeChatV2 with flag=true and a seeded conversation list, assert sidebar bg + item padding + truncation.

## Pre-commit Gates

```bash
grep -n "\.claude-shell {" -A 80 platform/src/app/globals.css | grep -E "--sidebar:|--sidebar-foreground:|--sidebar-accent:|--sidebar-border:"
npx jest --testPathPattern="V-S5|sidebar-chrome|claude-sidebar" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): claude-shell sidebar chrome (light, minimal, ~272px)

.claude-shell repointing of --sidebar* tokens to a light off-cream surface.
Conversation items: 8/12 padding, 8px radius, hover bg. Title truncated.
.consume-shell near-ink sidebar preserved.

Click-path: consume route flag=true → light minimal sidebar.
```

## Decision Log

*(Executor: paste final sidebar width chosen and screenshot of conversation list.)*
