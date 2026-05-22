---
canonical_id: R11B_B_S6
session_id: B-S6
title: Markdown content typescale — serif h1-h3, 16px body / 1.65 leading, mono code
phase: R11.B — Look-and-Feel
depends_on: [B-S5]
flag: MARSYS_FLAG_R11B_LOOK_AND_FEEL + hook
client_side: yes
authored: 2026-05-22
---

# B-S6 — Markdown Content Typescale

## Context

`MarkdownContent` under active state adopts Claude's typescale: body 16px / line-height 1.65, h1 28-30px / weight 600, h2 22-24px / 600, h3 18-19px / 600. Code blocks at ~14px mono with `bg: var(--card)` (resolves to existing `.consume-shell` card token, NOT a Claude-cream value).

## Files in Scope

- `platform/src/components/chat/MarkdownContent.tsx` — add `.consume-shell.r11b-active .markdown-content` descendant rules for h1-h4, p, ul, ol, pre, code, blockquote.
- `platform/src/app/globals.css` — optionally consolidate the rules in a `.consume-shell.r11b-active .markdown-content { ... }` block.

## Files MUST NOT Touch

- Build-portal typography (`.bt-*` classes)
- MermaidBlock, InteractiveTable styling (separate components)
- NumberedCitation styling (B-S7 territory)
- Provider adapters
- Phase 4C files

## Acceptance Criteria

1. Under active state: body `font-size: 1rem`, `line-height: 1.65`, serif.
2. h1 28-30px / 600 / letter-spacing -0.01em.
3. h2 22-24px / 600.
4. h3 18-19px / 600.
5. Code blocks: ~14px mono, padding 12-16px, border-radius 8px, `bg: var(--card)`.
6. Inline code: mono at 0.875em with subtle bg.
7. Lists + blockquotes use body typescale.
8. No regression with either gate false.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform
grep -n "r11b-active.*markdown\|MarkdownContent.*r11b" src/app/globals.css src/components/chat/MarkdownContent.tsx && echo "PASS"
npx jest --testPathPattern="MarkdownContent|B-S6|markdown-typescale" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): claude markdown typescale (B-S6)

MarkdownContent inside .consume-shell.r11b-active: 1rem body / 1.65 leading,
serif h1-h3 28/22/18 weight 600, mono code at 0.875em inline + 14px block.
Marsys palette preserved (code bg uses existing --card token).
```

## Decision Log

*(Executor: paste sample synthesis response with headings + code under active state.)*
