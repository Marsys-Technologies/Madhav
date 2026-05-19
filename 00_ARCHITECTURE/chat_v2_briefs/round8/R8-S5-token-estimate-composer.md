---
canonical_id: CHAT_V2_R8_S5_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R8
session_id: R8-S5
owner: chat-v2/round8-capabilities worktree
branch: chat-v2/round8-capabilities
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR8
flag_namespace: MARSYS_FLAG_R8_TOKENS
authored: 2026-05-20
depends_on: []
---

## Context

R8-S5 adds a live token count display and context-window percentage indicator to `Composer.tsx`. The feature gives the user real-time visibility into how much of the synthesis context window their current input consumes, with progressive colour coding and a persistent warning chip as they approach saturation.

The tokenizer (`gpt-tokenizer`) is a production dependency but must be loaded lazily via dynamic `import()` inside a `useEffect` so it never enters the initial server-rendered JS bundle and does not trigger `window is not defined` errors during SSR. Until the tokenizer has resolved, the UI shows a placeholder string `— tokens`.

Debouncing governs re-computation: 200 ms after the user stops typing for inputs up to 50 000 characters; 500 ms for longer inputs.

`contextWindowTokens` is sourced from `stackPicker().synthesisContextWindow`. If that value is absent or zero, fall back to `128000`.

The feature is gated by the flag namespace `MARSYS_FLAG_R8_TOKENS`; the flag guard must wrap both the token-count computation and the rendered UI elements so the composer renders identically to its pre-R8-S5 state when the flag is off.

---

## Files in scope

| Path | Change |
|------|--------|
| `platform/src/components/chat/Composer.tsx` | Primary implementation: lazy tokenizer load, debounced encode, token/pct state, rendered indicator + warning chip |
| `platform/package.json` | Add `gpt-tokenizer` as a production dependency |
| `platform/src/lib/feature_flags.ts` | Register `MARSYS_FLAG_R8_TOKENS` boolean flag with default `false` |
| `platform/src/hooks/useTokenCount.ts` | (New) Encapsulate lazy-load + debounced encode logic; keeps Composer.tsx diff minimal |
| `platform/tests/unit/useTokenCount.test.ts` | (New) Unit tests for hook: placeholder before load, correct count after load, debounce timing, 50k-char threshold |

---

## Files must not touch

- `platform/src/components/chat/ConsumeChatV2.tsx` — no layout changes permitted in this session
- `platform/src/components/chat/MessageList.tsx` — out of scope
- `platform/src/app/api/**` — server routes are not modified
- `platform/src/lib/pipeline/**` — query pipeline untouched
- `00_ARCHITECTURE/**` (except this brief itself, already written) — no governance artifact edits
- `platform/src/components/consume/**` — consume-layer components are read-only for this session
- Any file not listed in **Files in scope** above

---

## Acceptance criteria

**AC-1 Live token count**
Typing in the composer updates the token count display within 200 ms of the user pausing (keystroke debounce). The displayed value matches `encode(inputValue).length` from `gpt-tokenizer`.

**AC-2 Percentage indicator**
`pctUsed` renders as `Math.round(tokenCount / contextWindowTokens * 100)` where `contextWindowTokens` = `stackPicker().synthesisContextWindow ?? 128000`. Both values appear in the indicator: `{tokenCount} tokens · {pctUsed}%`.

**AC-3 Colour threshold — amber**
At `pctUsed >= 75` the indicator text transitions from `text-zinc-500` to `text-amber-400`. The element gains `title="Approaching context limit"` (native tooltip).

**AC-4 Colour threshold — red + chip**
At `pctUsed >= 95` the indicator transitions to `text-red-400`. A persistent warning chip appears below the composer: `"Context nearly full — consider starting a new conversation"`. The chip must remain visible (not dismissed by typing) until `pctUsed` drops below 95.

**AC-5 SSR safety**
Running `next build` or `next start` produces zero occurrences of `window is not defined` in server logs attributable to `gpt-tokenizer`. The dynamic import must be guarded by `typeof window !== 'undefined'` inside `useEffect`.

**AC-6 Placeholder before load**
Until the tokenizer module has resolved, the indicator renders the literal string `— tokens` (em dash, not hyphen). No flash of 0 or NaN is permitted.

**AC-7 Lazy bundle inclusion**
`next build` bundle analysis (`.next/analyze/` or `@next/bundle-analyzer` output) confirms `gpt-tokenizer` is NOT present in the initial page JS chunks. It appears only in a dynamically-loaded chunk. If bundle analysis tooling is not yet wired, provide a manual verification step in the commit message body.

**AC-8 Long-input debounce**
For `inputValue.length > 50000`, the debounce delay is 500 ms, not 200 ms. Unit test must exercise this branch.

**AC-9 Flag gate**
When `MARSYS_FLAG_R8_TOKENS` is `false` (default), the composer renders with no token indicator, no warning chip, and no tokenizer import is triggered. The feature is fully absent from the rendered output.

**AC-10 TypeScript clean**
`tsc --noEmit` exits 0. No `any` escapes introduced in the new hook or composer changes. `gpt-tokenizer` types must be satisfied (install `@types/gpt-tokenizer` if the package does not ship its own declarations, or author a minimal `.d.ts` shim under `platform/src/types/`).

---

## Pre-commit gates

Run each of the following and confirm exit 0 before committing. Paste the exit codes in the commit message body.

```bash
# 1. TypeScript
cd platform && npx tsc --noEmit

# 2. Unit tests (hook + any existing Composer tests)
cd platform && npx jest --testPathPattern="useTokenCount|Composer" --passWithNoTests

# 3. Lint
cd platform && npx eslint src/components/chat/Composer.tsx src/hooks/useTokenCount.ts

# 4. Next.js build (SSR safety + bundle)
cd platform && npx next build 2>&1 | grep -i "window is not defined" && echo "SSR FAIL" || echo "SSR OK"
```

If any gate fails, the commit must not be made. Fix and re-run all four gates.

---

## Commit message template

```
feat(composer): R8-S5 live token count + context-window % indicator

- Add `gpt-tokenizer` as production dep (lazy dynamic import, SSR-safe)
- New `useTokenCount` hook: debounced encode (200ms / 500ms >50k chars),
  placeholder until module loads
- Composer renders `{tokenCount} tokens · {pctUsed}%` below textarea
- Colour thresholds: zinc-500 (default) → amber-400 (≥75%) → red-400 (≥95%)
- Persistent warning chip at ≥95%: "Context nearly full — consider starting
  a new conversation"
- All UI gated behind MARSYS_FLAG_R8_TOKENS (default false)
- Pre-commit gates: tsc=0, jest=0, eslint=0, SSR=OK

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
