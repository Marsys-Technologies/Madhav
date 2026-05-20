---
canonical_id: R10_Y_S4
version: 1.0
status: CURRENT
session_id: Y-S4
title: Reasoning step labels — left-margin timeline in synthesis responses
depends_on: [Y-S3]
blocked_on: []
flag: MARSYS_FLAG_R10_REASONING_STEPS
flag_default: true
client_side: "no — synthesis prompt + server adapter; ReasoningProgress component is client-side but rendered from server-emitted events"
authored: 2026-05-20
---

# Y-S4 — Reasoning Step Labels

## Context

The synthesis pipeline produces a multi-phase reasoning trace (signal assembly, cross-domain linking, interpretation, etc.) before emitting the final response. Currently this trace is invisible or collapsed into the existing `ReasoningProgress` accordion. This session surfaces the reasoning phases as a named left-margin timeline: each phase emits a `### Step: <label>` marker in the synthesis prompt, the adapter parses it to a `reasoning_step` SSE event, and `ReasoningProgress` renders a vertical timeline with step labels and tick marks.

**CRITICAL PRESERVATION RULE (from CLAUDE.md §E R7 + amendment):** The synthesis prompt (`synthesis_prompt_v2` or equivalent) contains R7-S2's footnote citation instruction block. This block MUST be preserved verbatim when the prompt is edited. Do not rewrite, reorder, or paraphrase the footnote instruction block. Only ADD the `### Step:` marker instructions after the existing prompt structure.

**Amendment 1:** Flag is effectively server-side (read in synthesis route to gate the `### Step:` markers in the prompt). The `ReasoningProgress` component on the client side reads `reasoning_step` events from the stream — it is always-present code, gated by whether the events arrive. No `NEXT_PUBLIC_` prefix needed. No deploy.yml build-arg required.

**Amendment 3:** FLAGGED — changes synthesis prompt structure; want gated rollout.

**Amendment 2:** Visible component (ReasoningProgress timeline) → click-path and parent-context test required.

## Files in Scope

- `platform/src/lib/synthesis/synthesis_prompt_v2.ts` (or equivalent prompt file) — ADD `### Step: <label>` markers at phase boundaries; PRESERVE R7-S2 footnote block
- `platform/src/lib/streaming/stream_adapter.ts` (or equivalent) — parse `### Step: <label>` lines to `{ type: 'reasoning_step', label: string }` SSE events
- `platform/src/components/chat-v2/messages/ReasoningProgress.tsx` — render `reasoning_step` events as a vertical timeline with step labels (replaces or extends current accordion)
- `platform/src/lib/feature_flags.ts` — add `MARSYS_FLAG_R10_REASONING_STEPS` (default `true`)
- `platform/tests/` — integration test

## Files Must NOT Touch

- The R7-S2 footnote instruction block in the synthesis prompt (preservation rule above)
- `platform/src/components/chat-v2/messages/MarkdownContent.tsx`
- Phase 4C files
- `.github/workflows/deploy.yml` (server-side flag)

## Acceptance Criteria

1. **R7-S2 footnote block preserved:** After editing the synthesis prompt, executor diffs the footnote citation instruction block before and after: `git diff platform/src/lib/synthesis/synthesis_prompt_v2.ts | grep -A5 -B5 footnote`. The block content must be identical to its pre-edit state. Document in Decision Log.
2. **Flag is server-side (Amendment 1 confirmation):** `MARSYS_FLAG_R10_REASONING_STEPS` does NOT appear with a `NEXT_PUBLIC_` prefix anywhere. Executor confirms via grep.
3. **click-path (Amendment 2):** User path: Chat V2 → send a synthesis query → the reasoning/thinking accordion opens → a vertical timeline appears showing step labels (e.g., "Signal Assembly", "Cross-Domain Linking", "Interpretation", "Response") with tick marks as each phase completes → final response renders below. Document in commit body.
4. **`### Step:` parsing:** Adapter identifies lines matching `/^### Step: (.+)$/` in the synthesis stream and emits `{ type: 'reasoning_step', label: string, timestamp: number }`. These events arrive before the text content of that step.
5. **Timeline rendering:** `ReasoningProgress` renders a left-margin vertical timeline. Each step is a labeled tick: pending steps in gray, active step with a pulsing indicator, completed steps with a checkmark. The component is additive — it does not replace existing ReasoningProgress content if any.
6. **Flag guard:** When flag=false, `### Step:` markers are not added to the prompt and `reasoning_step` events are not emitted. Existing behavior is preserved.
7. **Parent-context integration test (Amendment 2):** At least one test mounts `ReasoningProgress` within the message stream context (providing simulated `reasoning_step` events) and asserts: (a) step labels render in order, (b) active step has pulsing indicator, (c) completed step has checkmark. Leaf test alone does NOT satisfy this AC.

## Pre-commit Gates

```bash
# Verify R7-S2 footnote block unchanged (executor runs manually before commit)
# git diff platform/src/lib/synthesis/synthesis_prompt_v2.ts | grep -C3 footnote

# Flag is server-side only
grep -rn "NEXT_PUBLIC.*REASONING_STEPS" platform/src --include="*.ts*" && echo "FAIL: NEXT_PUBLIC found" || echo "PASS: no NEXT_PUBLIC"

# Verify ### Step: parsing in adapter
grep -n "reasoning_step\|### Step" platform/src/lib/streaming/stream_adapter.ts && echo "PASS" || echo "FAIL"

npx jest --testPathPattern="ReasoningProgress|reasoning.*step|step.*label" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): reasoning step labels — left-margin timeline in synthesis

synthesis_prompt_v2 emits ### Step: <label> markers at phase boundaries
(R7-S2 footnote block preserved verbatim). Adapter parses to reasoning_step
events. ReasoningProgress renders vertical left-margin timeline with
active/completed indicators. Guarded by MARSYS_FLAG_R10_REASONING_STEPS=true
(server-side; no NEXT_PUBLIC, no deploy.yml build-arg).

Click-path: synthesis query → reasoning accordion → step timeline → response.
```

## Decision Log

*(Executor: paste git diff of footnote block here to confirm preservation. Record step label set chosen.)*
