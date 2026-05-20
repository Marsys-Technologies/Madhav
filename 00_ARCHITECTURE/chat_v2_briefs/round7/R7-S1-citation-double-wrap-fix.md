---
canonical_id: CHAT_V2_R7_S1_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R7
session_id: R7-S1
owner: chat-v2/round7-polish worktree
branch: chat-v2/round7-polish
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR7
flag_namespace: MARSYS_FLAG_R7_CITATION
authored: 2026-05-20
depends_on: []
---

## Context

`preprocessCitations` in `ConsumeChatV2.tsx` (lines 207–228) runs three sequential
replacement passes on assistant text:

1. Strip `‹sanskrit›` markup.
2. Collapse `(→ SIG.MSR.NNN, ...)` wrappers into backtick-wrapped `CITE:N:SIG.MSR.NNN`
   badge markers.
3. Replace bare `SIG.MSR.NNN` with badge markers.

**The bug:** step 3's regex `/SIG\.MSR\.\d{3}(?!\d)/g` has no awareness of text that was
already badged by step 2.  Because step 2 emits strings of the form

```
`CITE:1:SIG.MSR.001`
```

the bare-SIG pattern in step 3 matches `SIG.MSR.001` inside that string and re-wraps it,
producing:

```
`CITE:1:`CITE:1:SIG.MSR.001``
```

This double-nesting breaks the downstream `MarkdownContent` citation renderer — it sees a
malformed marker and either drops the citation or renders raw backtick text to the user.

**Fix (lookbehind approach — preferred):** add a negative lookbehind on step 3's regex so
it skips any `SIG.MSR.NNN` that is immediately preceded by the `CITE:N:` prefix:

```ts
// Before
result = result.replace(/SIG\.MSR\.\d{3}(?!\d)/g, badge)

// After
result = result.replace(/(?<!CITE:\d+:)SIG\.MSR\.\d{3}(?!\d)/g, badge)
```

V8+ runtimes (Node ≥ 10, all modern browsers) support ES2018 lookbehinds; no polyfill is
needed.  The Cloud Run image (`node:20-alpine`) satisfies this requirement.

**Also required:** export `preprocessCitations` (or a thin named re-export wrapper) so the
unit-test file can import it without reaching into module internals.  A barrel re-export at
the bottom of the function block is sufficient:

```ts
export { preprocessCitations }
```

---

## Files in scope

| File | Change |
|---|---|
| `platform/src/components/consume/ConsumeChatV2.tsx` | Add negative lookbehind to step 3 regex (line 225); add `export { preprocessCitations }` |
| `platform/src/components/consume/__tests__/preprocessCitations.test.ts` | New file — four unit tests covering the fixed behaviour |

The `__tests__/` directory may need to be created if it does not yet exist under
`platform/src/components/consume/`.

---

## Files must not touch

- `platform/src/components/consume/ConsumeChat.tsx` — wrapper re-export only; no logic
  changes.
- `platform/src/components/chat/Composer.tsx` — out of scope; LOCKED per `platform/AGENTS.md`.
- Any file under `00_ARCHITECTURE/` other than this brief itself.
- `platform/src/lib/pipeline/` — pipeline layer; out of R7 scope.
- `platform/src/app/` route files.
- Any `*.md` governance artifact not part of this brief's session close.
- `platform/tests/e2e/` — end-to-end specs; integration work deferred to R7-S2+.

---

## Acceptance criteria

### AC-1 — No double-wrap on arrow-wrapped signals

Given assistant text `(→ SIG.MSR.042)`, `preprocessCitations` returns a `processedText`
that contains exactly one backtick-wrapped badge for `SIG.MSR.042` and zero occurrences of
nested backtick pairs (i.e. `` `CITE:N:`CITE`` does not appear anywhere in the output).

### AC-2 — Bare signal still resolves to a single badge

Given assistant text `SIG.MSR.001 is active`, the output contains exactly one badge
`` `CITE:1:SIG.MSR.001` `` and `count` is 1.

### AC-3 — Mixed paragraph — correct badge count, no duplication

Given text `(→ SIG.MSR.001, SIG.MSR.002) and also SIG.MSR.003 plus bare SIG.MSR.001`
(where `SIG.MSR.001` appears once via arrow-wrap and once bare):

- `count` is 3 (three unique signals).
- `SIG.MSR.001` badge appears exactly twice in the output (arrow position + bare position),
  both bearing the same index (e.g. `CITE:1`).
- No double-wrap nesting is present.

### AC-4 — Pre-badged string is left unchanged

Given text that already contains `` `CITE:1:SIG.MSR.001` `` (simulating a string that has
already passed through `preprocessCitations` once, e.g. via streaming re-render), the
function does not re-badge the contained signal ID; the output is byte-identical to the
input for that token.

### AC-5 — Export is importable

The unit test file imports `preprocessCitations` via a named import:

```ts
import { preprocessCitations } from '../ConsumeChatV2'
```

and the import resolves without TypeScript error (verified by `tsc --noEmit`).

### AC-6 — No regressions in existing Chat V2 smoke surface

The `(→ SIG.MSR.NNN)` arrow-badge rendering visible in the UI continues to produce single
inline badges — confirmed by manual smoke or by existing round-6 walkthrough spec if the
env vars are available.

---

## Pre-commit gates

Run these from the `platform/` directory before committing.  All must pass (exit 0).

```bash
# 1. TypeScript — no type errors introduced
npx tsc --noEmit

# 2. Unit tests — new + existing must be green
npx jest src/components/consume/__tests__/preprocessCitations.test.ts --passWithNoTests=false

# 3. Lint — no new ESLint errors in changed files
npx eslint src/components/consume/ConsumeChatV2.tsx \
           src/components/consume/__tests__/preprocessCitations.test.ts \
  --max-warnings=0

# 4. Build — production bundle must compile cleanly
npx next build 2>&1 | tail -20
```

Gate 4 (build) may be deferred to CI if local build time is prohibitive, but gates 1–3
must pass locally before the commit is authored.

---

## Commit message template

```
fix(chat-v2): prevent double-wrap of already-badged SIG IDs in preprocessCitations

Add negative lookbehind (?<!CITE:\d+:) to the bare-SIG regex in step 3 of
preprocessCitations so signals already wrapped by the arrow-collapse pass (step 2)
are not re-processed, eliminating the `CITE:N:`CITE:N:SIG.MSR.NNN`` nesting bug.

Also exports preprocessCitations as a named export to enable direct unit testing.

New test file: platform/src/components/consume/__tests__/preprocessCitations.test.ts
- AC-1: arrow-wrapped signal produces single badge
- AC-2: bare signal produces single badge
- AC-3: mixed paragraph — correct count, no duplication
- AC-4: pre-badged input is left unchanged

Fixes: double-wrap regression introduced when step-2 output feeds step-3 regex.
Round: R7-S1
Brief: 00_ARCHITECTURE/chat_v2_briefs/round7/R7-S1-citation-double-wrap-fix.md

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
