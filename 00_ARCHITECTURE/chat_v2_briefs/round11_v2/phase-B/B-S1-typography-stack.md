---
canonical_id: R11B_B_S1
session_id: B-S1
title: Claude typography stack — serif body + sans chrome + mono code inside .consume-shell
phase: R11.B — Look-and-Feel
depends_on: [B-S0]
flag: MARSYS_FLAG_R11B_LOOK_AND_FEEL (umbrella for B-S1..B-S7) AND useMultiProviderParity() hook
client_side: "yes — NEXT_PUBLIC + user-pref hook"
authored: 2026-05-22
---

# B-S1 — Claude Typography Stack

## Context

Marsys palette stays (per NATIVE_RULINGS §1). Inside `.consume-shell`, body + assistant messages adopt Claude's system-serif stack (`ui-serif, Georgia, "Iowan Old Style", "Source Serif Pro", serif`). Sidebar + buttons + labels stay sans (system-sans stack). Code blocks use system-mono.

Gated by: `MARSYS_FLAG_R11B_LOOK_AND_FEEL` env-var (NEXT_PUBLIC, default false) AND `useMultiProviderParity()` hook (from A-S11). Both must be true for the new typography to apply.

## Files in Scope

- `platform/src/app/globals.css` — add typography rules inside the existing `.consume-shell` block:
  - `--font-body-serif` token
  - `.consume-shell.r11b-active body, .consume-shell.r11b-active .message-body { font-family: var(--font-body-serif); }`
  - Code-block treatment with system-mono stack
- `platform/src/components/consume/ConsumeChatV2.tsx` — when `useMultiProviderParity()` returns true AND `MARSYS_FLAG_R11B_LOOK_AND_FEEL=true`, add `r11b-active` class to the consume-shell root.
- `platform/src/lib/config/feature_flags.ts` — register `MARSYS_FLAG_R11B_LOOK_AND_FEEL` (default false, NEXT_PUBLIC).
- `.github/workflows/deploy.yml` — add `NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL` build-arg.
- Tests.

## Files MUST NOT Touch

- `.consume-shell` palette tokens (palette stays — only typography changes)
- `--brand-*` tokens
- Phase 4C files
- Provider adapters (R11.CDE stream territory)

## Acceptance Criteria

1. `MARSYS_FLAG_R11B_LOOK_AND_FEEL` registered in feature_flags + deploy.yml (Amendment 1).
2. `.consume-shell.r11b-active body` font-family is the system-serif stack.
3. Sidebar + buttons inside `.consume-shell.r11b-active` remain sans.
4. Code blocks inside assistant messages render in system-mono.
5. Hook + env-var both gate: with flag=false OR hook=false, classic typography (Geist) renders.
6. No `@font-face` or CDN font imports introduced.
7. Click-path: env=true + toggle on → assistant messages render in serif.
8. Parent-context test asserts class membership + computed font-family.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform
grep -n "MARSYS_FLAG_R11B_LOOK_AND_FEEL" src/lib/config/feature_flags.ts && echo "PASS"
grep -n "NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL" ../.github/workflows/deploy.yml && echo "PASS"
grep -n "r11b-active" src/app/globals.css && echo "PASS"
grep -rn "@font-face\|fonts.googleapis" src/app/globals.css | grep -v "^[^:]*:\s*\(//\|/\*\)" && echo "FAIL: new font import" || echo "PASS"
npx jest --testPathPattern="typography|B-S1" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): claude typography stack inside .consume-shell (B-S1)

System-serif body inside .consume-shell.r11b-active; sans chrome + mono code
stacks. Marsys palette unchanged. Gated by MARSYS_FLAG_R11B_LOOK_AND_FEEL
(NEXT_PUBLIC, default false) + useMultiProviderParity() hook from A-S11.
```

## Decision Log

*(Executor: paste final font-family value chosen; before/after screenshot.)*
