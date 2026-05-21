---
canonical_id: R11_V_S1
version: 1.0
status: CURRENT
session_id: V-S1
title: Claude typography stack — serif body + sans chrome inside `.claude-shell`
depends_on: []
blocked_on: []
amended: 2026-05-21 — Open Item #1 LOCKED per NATIVE_RULINGS §1: do NOT introduce a separate `.claude-shell` class; instead EXTEND the existing `.consume-shell` block in globals.css with serif body + sans chrome + mono code rules. Marsys palette preserved.
flag: MARSYS_FLAG_R11_CLAUDE_RENDERING
flag_default: false
client_side: "yes — NEXT_PUBLIC, mounted as a class on ConsumeChat root"
authored: 2026-05-21
---

# V-S1 — Claude Typography Stack

## Context

Chat V2 today renders with `--font-sans: var(--font-sans)` (Geist Sans) on the consume route. Claude.ai's chat surface uses a **system serif stack** for assistant body + headings (`ui-serif, Georgia, "Iowan Old Style", "Source Serif Pro", serif`) at ~16px / line-height 1.65 / weight 400, with a sans stack for chrome (sidebar, buttons, labels) and a monospace stack for code blocks.

This session introduces a new shell-scope class `.claude-shell` that re-points typography tokens to the Claude-style serif body + sans chrome + mono code pattern. It does NOT touch the existing `.consume-shell` brand surface — both classes can coexist. Mounting `.claude-shell` on the ConsumeChat root is gated by `MARSYS_FLAG_R11_CLAUDE_RENDERING` (NEXT_PUBLIC, default false).

## Files in Scope

- `platform/src/app/globals.css` — add `.claude-shell { ... }` block with `--font-sans` re-pointed to a sans system stack (chrome), introduce `--font-body-serif` for assistant body, set body element `font-family` inside `.claude-shell` to the serif stack.
- `platform/src/components/consume/ConsumeChatV2.tsx` — read `process.env.NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING`, conditionally add `claude-shell` class to the root container (alongside or in place of `consume-shell` per the native's ruling in master-plan Open Item #1).
- `platform/src/lib/feature_flags.ts` — register `MARSYS_FLAG_R11_CLAUDE_RENDERING` flag (default false).
- `.github/workflows/deploy.yml` — add `NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING` to the `--build-arg` block (Amendment 1 HARD GATE).
- `platform/tests/components/consume/ConsumeChatV2-claude-shell.test.tsx` (new) — mount-verification: with the flag stub'd true, `claude-shell` class appears on root; with flag stub'd false, it does not.

## Files Must NOT Touch

- `.consume-shell` block in globals.css (preserved as opt-in alternative)
- Any /build, /admin, /observatory, /aiops styling — scope is consume route only
- The `--brand-*` tokens (V-S2 owns the palette decision)
- Phase 4C files

## Acceptance Criteria

1. **Flag is client-side with deploy.yml coverage (Amendment 1):** `NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING` appears in both `feature_flags.ts` and `deploy.yml --build-arg`. Coverage check from master plan §Amendment 5 passes for this flag.
2. **`.claude-shell` class defined:** globals.css contains `.claude-shell { --font-sans: <sans system stack>; --font-body-serif: <serif system stack>; }` plus `.claude-shell body, .claude-shell main, .claude-shell .message-body { font-family: var(--font-body-serif); }` (or equivalent selector covering assistant message content).
3. **Mount conditional:** ConsumeChatV2 root carries `claude-shell` class iff `process.env.NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING === 'true'`. With flag false, root has `consume-shell` only (no behavior change).
4. **Click-path (Amendment 2):** With flag=true and the consume route open, the assistant message body renders in a serif typeface and sidebar/buttons remain sans. Document in commit body.
5. **Parent-context integration test (Amendment 2):** Test mounts `<ConsumeChatV2 />` with the AssistantRuntimeProvider context simulated, with `NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING` stub'd both ways, asserts root class membership and at least one descendant `font-family` computed-style includes "serif" when flag=true.
6. **No fonts/`@font-face` introduced:** Serif/sans/mono stacks must be system stacks only — no `@import url(...font.css)` or `@font-face` declarations. (Latency budget; license simplicity.)
7. **No regression with flag=false:** Existing `.consume-shell` surface renders byte-identical to pre-R11. Confirmed via Playwright snapshot diff if available, else manual.

## Pre-commit Gates

```bash
# Flag registered + deploy.yml coverage
grep -n "MARSYS_FLAG_R11_CLAUDE_RENDERING" platform/src/lib/feature_flags.ts && echo "PASS: registered"
grep -n "NEXT_PUBLIC_MARSYS_FLAG_R11_CLAUDE_RENDERING" .github/workflows/deploy.yml && echo "PASS: deploy.yml"

# No new @font-face / font CDN imports
grep -rn "@font-face\|fonts.googleapis\|fonts.gstatic" platform/src/app/globals.css | grep -v "^[^:]*:[[:space:]]*//\|^[^:]*:[[:space:]]*/\*" && echo "FAIL: new font import" || echo "PASS: system stacks only"

# Integration test
npx jest --testPathPattern="claude-shell|ConsumeChatV2-claude" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): introduce .claude-shell typography stack (serif body + sans chrome)

Adds .claude-shell class with system-serif body and system-sans chrome,
mounted on ConsumeChatV2 root behind MARSYS_FLAG_R11_CLAUDE_RENDERING=false
(NEXT_PUBLIC; deploy.yml --build-arg added).

.consume-shell preserved as default. No web fonts introduced; system stacks only.

Click-path: consume route with flag=true → assistant messages render serif.
```

## Decision Log

*(Executor: paste resolution of Open Native-Input Item #1 here before commit. Paste the final font-family value for `--font-body-serif`. Paste before/after screenshots if available.)*
