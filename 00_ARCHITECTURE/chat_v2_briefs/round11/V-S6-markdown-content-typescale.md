---
canonical_id: R11_V_S6
version: 1.0
status: CURRENT
session_id: V-S6
title: Markdown content typescale — serif headings, 16px body, 1.65 line-height inside `.claude-shell`
depends_on: ["V-S5"]
blocked_on: []
flag: MARSYS_FLAG_R11_CLAUDE_RENDERING
flag_default: false
client_side: "yes — MarkdownContent styling inside .consume-shell, gated by MARSYS_FLAG_R11_CLAUDE_RENDERING"
authored: 2026-05-21
amended: 2026-05-21 — per NATIVE_RULINGS §1: `.claude-shell` references mean "inside .consume-shell, gated by the flag". Marsys palette stays. Code-block `bg: var(--card)` resolves to the existing `.consume-shell` --card token, NOT a Claude-cream value.
---

# V-S6 — Markdown Content Typescale

## Context

Claude.ai assistant messages render markdown at: body 16px / line-height ~1.65 / weight 400, serif. Headings: h1 28-30px, h2 22-24px, h3 18-19px, all serif weight 600 with slight negative tracking on h1. Inline code: monospace ~13px with subtle bg. Code blocks: monospace ~14px with `bg: var(--card)` (one shade above canvas).

This session brings `MarkdownContent` inside `.claude-shell` to this typescale.

## Files in Scope

- `platform/src/components/chat/MarkdownContent.tsx` — add `.claude-shell` descendant CSS-module or className rules for `h1, h2, h3, h4, p, ul, ol, pre, code` matching the typescale above. Use `var(--font-body-serif)` for body + headings, `var(--font-mono)` for code.
- `platform/src/app/globals.css` — optionally add a `.claude-shell .markdown-content { ... }` block consolidating the rules. Use existing `bt-display/bt-heading/bt-body` patterns as reference but DO NOT reuse those classes (they belong to build-portal).

## Files Must NOT Touch

- Build-portal typography classes (`.bt-*`) — preserved
- Mermaid block styling, InteractiveTable styling (separate components)
- NumberedCitation styling (separate brief if needed)
- Phase 4C files

## Acceptance Criteria

1. **Body:** `.claude-shell .markdown-content p` (or equivalent) has `font-size: 1rem`, `line-height: 1.65`, `font-family: var(--font-body-serif)`.
2. **Headings:** h1 28-30px / weight 600 / letter-spacing -0.01em; h2 22-24px / 600; h3 18-19px / 600. All `var(--font-body-serif)`.
3. **Code:** inline code `var(--font-mono)` at ~0.875em with subtle bg; pre+code block at ~14px / line-height 1.5, `bg: var(--card)`, padding 12-16px, border-radius 8px.
4. **Lists:** `ul/ol` use the body typescale, list-style preserved.
5. **No regression with flag=false:** existing markdown rendering identical.
6. **Click-path:** consume route flag=true → assistant response renders in serif with the heading hierarchy above; code blocks render in mono.
7. **Parent-context integration test:** mount MarkdownContent with a seeded message containing h1/h2/h3/p/code/pre, flag=true, assert computed `font-family` and `font-size` on each element.

## Pre-commit Gates

```bash
grep -n "\.claude-shell.*markdown\|MarkdownContent.*claude-shell" platform/src/app/globals.css platform/src/components/chat/MarkdownContent.tsx
npx jest --testPathPattern="V-S6|markdown-content-typescale" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): claude-shell markdown typescale (serif body+headings, mono code)

MarkdownContent inside .claude-shell: 1rem body / 1.65 leading / serif, h1-h3
scaled 28/22/18 weight 600, monospace code at 0.875em inline + 14px block.
.consume-shell rendering preserved.

Click-path: consume route flag=true → assistant message renders with editorial
serif feel.
```

## Decision Log

*(Executor: paste before/after of a sample synthesis response with headings + code.)*
