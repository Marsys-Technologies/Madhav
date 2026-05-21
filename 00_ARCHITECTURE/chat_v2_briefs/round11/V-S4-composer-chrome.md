---
canonical_id: R11_V_S4
version: 1.0
status: CURRENT
session_id: V-S4
title: Composer chrome — rounded shape, no shadow, fades into canvas, filled-circle send
depends_on: ["V-S3"]
blocked_on: []
flag: MARSYS_FLAG_R11_CLAUDE_RENDERING
flag_default: false
client_side: "yes — component styling inside .consume-shell, gated by MARSYS_FLAG_R11_CLAUDE_RENDERING"
authored: 2026-05-21
amended: 2026-05-21 — per NATIVE_RULINGS §1+§2: changes happen inside `.consume-shell` gated by the flag; `--accent` stays `var(--brand-gold)` (NOT coral). `.brand-cta` gold-gradient send button preserved verbatim; only border-radius + box-shadow + bg adopted to Claude minimal shape.
---

# V-S4 — Composer Chrome

## Context

Claude.ai's composer is sticky-bottom, `border-radius: ~20-24px`, single thin border, NO drop shadow, bg matches canvas (it "fades into the page"). Send button is a small filled circle (~32-36px), coral bg, white arrow. Stop button is the same shape with a filled-square glyph.

Chat V2's `Composer` is in `platform/src/components/chat/Composer.tsx`; `.consume-composer-card:focus-within` currently produces a gold ring + faint gold halo. This session adds a `.claude-shell .consume-composer-card` variant matching Claude's minimal aesthetic.

## Files in Scope

- `platform/src/components/chat/Composer.tsx` — confirm element classes are stable enough to be styled via `.claude-shell .consume-composer-card` descendant rules.
- `platform/src/app/globals.css` — add `.claude-shell .consume-composer-card { ... }` block:
  - `background: var(--background)` (fades into canvas)
  - `border-radius: 1.5rem` (~24px)
  - `border: 1px solid var(--border)`
  - `box-shadow: none`
  - `&:focus-within { border-color: var(--accent); box-shadow: none; }`
- Send/stop button styling — small filled circle (~32px), `background: var(--accent)`, white icon. Use the same `var(--accent)` chosen in V-S2.

## Files Must NOT Touch

- `.consume-shell` composer styling (preserved)
- `.brand-cta` block (preserves login/admin CTA visuals)
- Phase 4C files

## Acceptance Criteria

1. **Shape inside `.claude-shell`:** composer card has `border-radius >= 1.25rem` and `box-shadow: none`. Border is 1px solid `var(--border)`.
2. **Bg fades:** composer `background` computed style equals page `background` computed style inside `.claude-shell`.
3. **Send/stop button:** circular shape (border-radius >= 50%), `var(--accent)` filled, ~32-36px diameter.
4. **Sticky-bottom preserved:** existing `ThreadPrimitive.ViewportFooter` (or equivalent) sticky positioning is not altered.
5. **No regression with flag=false:** existing composer renders identically.
6. **Click-path:** consume route with flag=true → composer reads as a minimal rounded textarea that blends with the cream canvas; send button is a small filled coral/gold circle.
7. **Parent-context integration test:** mount Composer inside ConsumeChatV2 with flag=true, assert computed `border-radius`, `box-shadow`, and `background` of the composer card and the button shape.

## Pre-commit Gates

```bash
grep -n "\.claude-shell.*consume-composer-card\|claude-shell.*Composer" platform/src/app/globals.css platform/src/components/chat/Composer.tsx
npx jest --testPathPattern="V-S4|composer-chrome|claude-composer" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): claude-shell composer chrome (rounded, shadowless, fades-in)

Composer inside .claude-shell: 1.5rem border-radius, no box-shadow, bg matches
canvas, focus-within colors the border via --accent. Send/stop button: small
filled circle with --accent bg.

.consume-shell composer styling preserved. Same flag (V-S1).

Click-path: consume route with flag=true → minimal composer below cream column.
```

## Decision Log

*(Executor: paste send-button diameter chosen and the accent value used.)*
