---
canonical_id: R11B_B_S4
session_id: B-S4
title: Composer chrome — Claude-minimal shape, Marsys gold focus + brand-cta send retained
phase: R11.B — Look-and-Feel
depends_on: [B-S3]
flag: MARSYS_FLAG_R11B_LOOK_AND_FEEL + hook
client_side: yes
authored: 2026-05-22
---

# B-S4 — Composer Chrome

## Context

Composer adopts Claude's minimal rounded shape (border-radius ~1.5rem, no box-shadow, fades into canvas) but retains Marsys gold focus border + the `.brand-cta` gold-gradient send button per NATIVE_RULINGS §2.

## Files in Scope

- `platform/src/components/chat/Composer.tsx` — gate styling on flag + hook.
- `platform/src/app/globals.css` — `.consume-shell.r11b-active .consume-composer-card` block: rounded 1.5rem, no shadow, bg matches canvas, focus-within border uses `var(--brand-gold)`.
- Send button: keep existing `.brand-cta` styling. Stop button: square glyph, same gold accent.

## Files MUST NOT Touch

- `.brand-cta` block (preserves login/admin gold CTA visuals)
- The existing send/stop button morph from R6.5
- Slash menu / token count / attachments behavior (R8 features preserved)
- Provider adapters
- Phase 4C files

## Acceptance Criteria

1. Composer card under active state: `border-radius >= 1.25rem`, `box-shadow: none`, bg matches canvas.
2. Focus-within border uses `var(--brand-gold)`.
3. Send button retains `.brand-cta` gold gradient.
4. Sticky-bottom positioning preserved.
5. R8 affordances (slash, tokens, attachments) work in both states.
6. No regression with either gate false.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform
grep -n "r11b-active .*consume-composer-card\|claude-composer" src/app/globals.css src/components/chat/Composer.tsx && echo "PASS"
npx jest --testPathPattern="Composer|B-S4|composer-chrome" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): claude-minimal composer chrome (B-S4)

Composer inside .consume-shell.r11b-active: 1.5rem radius, no shadow, bg
matches canvas, gold focus border. .brand-cta send button preserved.
```

## Decision Log

*(Executor: paste before/after composer screenshots.)*
