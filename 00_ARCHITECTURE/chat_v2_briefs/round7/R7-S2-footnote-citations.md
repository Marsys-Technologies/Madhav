---
canonical_id: CHAT_V2_R7_S2_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R7
session_id: R7-S2
owner: chat-v2/round7-polish worktree
branch: chat-v2/round7-polish
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR7
flag_namespace: MARSYS_FLAG_R7_CITATION
authored: 2026-05-20
depends_on: [R7-S1]
---

## Context

This is R7-S2 (R6.2 fix-forward). The synthesis pipeline currently instructs the LLM to emit inline `(→ SIG.MSR.NNN)` markers inside generated prose. Those markers are not GFM-compliant and bypass the `MarkdownContent` component's structured citation flow — they render as raw text rather than styled badge elements, and they couple the prose irreversibly to MSR signal IDs that the reader never asked to see in-line.

The fix is a two-part change:

1. **Synthesis prompt** — replace the `(→ SIG.MSR.NNN)` instruction with GFM footnote syntax: `[^1]` inline + a trailing footnote block mapping each index to its canonical signal ID (`[^1]: SIG.MSR.NNN`). The LLM continues to ground every interpretive claim in a signal ID; the IDs are now in a structured footnote block instead of polluting prose.

2. **MarkdownContent.tsx** — add `footnoteReference` and `footnoteDefinition` to the existing `components` map so the markdown renderer handles GFM footnotes. `footnoteReference` renders as a small superscript badge (styled to match the existing CITE badge). `footnoteDefinition` renders invisibly (sr-only / display:none) because the canonical citation data flows through data parts, not through the footnote block itself; the footnote block is kept in the LLM output only as a machine-readable anchor and as defence-in-depth for prompt drift.

`preprocessCitations` is retained unchanged as a secondary defence layer for prompt drift; it is not the primary rendering path after this session.

The test suite gains a case asserting that `[^1]` in a markdown string produces a badge-class element in the rendered output.

## Files in scope

- `platform/src/lib/synthesis/prompts/synthesis_prompt_v2.ts`
  — Locate the block that instructs the LLM on citation style (search for `SIG.MSR` or `→ SIG`). Replace the inline-marker instruction with a GFM footnote instruction. Exact replacement target must be confirmed by reading the file first. Keep the "do not emit raw SIG IDs in prose" rule verbatim; only the emission format changes.

- `platform/src/components/chat/MarkdownContent.tsx`
  — Already imports and uses a `components` prop map for react-markdown / streamdown. Add two entries:
    - `footnoteReference`: renders as `<sup><span className="inline-flex items-center rounded px-1 text-xs font-medium bg-amber-500/20 text-amber-400">{node.identifier}</span></sup>` (or equivalent — match the exact class tokens of the existing CITE badge).
    - `footnoteDefinition`: renders as `<span className="sr-only" />` (invisible; data flows via data parts).

- `platform/src/components/chat/__tests__/streamdown_render.test.ts` (or the nearest equivalent test file for MarkdownContent / streamdown rendering — confirm exact path before editing)
  — Add one test: given a markdown string containing `[^1]` and a footnote definition `[^1]: SIG.MSR.042`, assert the rendered output contains an element with the badge class tokens (`bg-amber-500/20`, `text-amber-400`) and the text `1`.

## Files must not touch

- `platform/src/lib/synthesis/prompts/synthesis_prompt_v1.ts` (legacy, read-only for reference only)
- `platform/src/components/chat/ConsumeChatV2.tsx` (active, separate workstream — R7-S1 owns this)
- `platform/src/components/chat/ConsumeChat.tsx`
- `platform/src/lib/synthesis/preprocessCitations.ts` (retain unchanged — defence-in-depth)
- `platform/src/components/consume/ConsumeChatV2.tsx`
- `00_ARCHITECTURE/**` except this file
- `01_FACTS_LAYER/**`
- `025_HOLISTIC_SYNTHESIS/**`
- `06_LEARNING_LAYER/**`
- Any file not listed under "Files in scope" above

## Acceptance criteria

AC.R7S2.1 — Synthesis prompt no longer contains any instruction to emit `→ SIG.MSR.NNN` or `(→ SIG.` style inline markers. The only citation instruction present is the GFM footnote form (`[^N]` inline + trailing `[^N]: SIG.MSR.NNN` block).

AC.R7S2.2 — `MarkdownContent.tsx` components map contains a `footnoteReference` entry that renders a `<sup>` element wrapping a `<span>` with at minimum `bg-amber-500/20` and `text-amber-400` in its className.

AC.R7S2.3 — `MarkdownContent.tsx` components map contains a `footnoteDefinition` entry that renders with `sr-only` or equivalent `display:none` so the raw footnote block is not visible to the reader.

AC.R7S2.4 — `preprocessCitations` is present in its file unchanged (no lines added, removed, or altered).

AC.R7S2.5 — The new unit test exists, runs, and passes: markdown input `"text[^1]\n\n[^1]: SIG.MSR.042"` produces a rendered element matching the badge class tokens.

AC.R7S2.6 — `pnpm tsc --noEmit` exits 0 across the platform package.

AC.R7S2.7 — `pnpm lint` exits 0 across the platform package (no new ESLint errors introduced).

AC.R7S2.8 — The changed test file's full suite (`pnpm test -- --testPathPattern=streamdown_render`) exits 0.

## Pre-commit gates

Run these commands in order inside the `platform/` directory before committing. All must exit 0.

```bash
# 1. Type-check
pnpm tsc --noEmit

# 2. Lint
pnpm lint

# 3. Unit tests (citation/render subset)
pnpm test -- --testPathPattern=streamdown_render

# 4. Full test suite (non-interactive)
pnpm test --passWithNoTests
```

If any gate fails, fix before committing. Do not skip or suppress errors with inline ignores unless a pre-existing suppression already exists in the file for an unrelated rule.

## Commit message template

```
feat(chat-v2/r7-s2): switch synthesis citations to GFM footnotes + footnoteReference badge

- synthesis_prompt_v2.ts: replace (→ SIG.MSR.NNN) inline marker instruction
  with [^N] footnote syntax; footnote block maps index → canonical signal ID
- MarkdownContent.tsx: add footnoteReference (amber superscript badge) +
  footnoteDefinition (sr-only) to components map
- streamdown_render.test.ts: assert [^1] markdown renders as badge element
- preprocessCitations.ts unchanged (defence-in-depth for prompt drift)

Closes R6.2 fix-forward (CHAT_V2_R7_S2_BRIEF v1.0)
```
