---
canonical_id: R11_S_S3
version: 1.0
status: CURRENT
session_id: S-S3
title: Extended-thinking auto-collapse — expand while streaming, collapse on first text_delta
depends_on: ["S-S2"]
blocked_on: []
flag: FLAGLESS
flag_default: —
client_side: "yes — ReasoningProgress heuristic extension"
authored: 2026-05-21
---

# S-S3 — Extended-Thinking Auto-Collapse

## Context

Claude.ai renders extended thinking as a **collapsible panel auto-expanded while streaming**, then **auto-collapses on first text_delta** of the answer block. The current Y-S4 ReasoningProgress component auto-collapses at >2000 tokens, but not on the stage transition from thinking → text.

This session adds the stage-transition auto-collapse heuristic. FLAGLESS per Amendment 3 (additive heuristic on existing component).

## Files in Scope

- `platform/src/components/chat/ReasoningProgress.tsx` — extend the auto-collapse heuristic: collapse when `hasFirstTextDelta === true` AND `wasStreaming === true`. Preserve the >2000-token rule and the manual user toggle.
- `platform/src/lib/chat-v2/useDataParts.ts` — expose `hasFirstTextDelta` derived signal (same one used by S-S1).

## Files Must NOT Touch

- The synthesis prompt (Y-S4 step markers preserved)
- The `### Step:` parsing in stream_adapter
- Phase 4C files

## Acceptance Criteria

1. **Stage-transition collapse:** when `hasFirstTextDelta` flips false→true on a streaming message, ReasoningProgress transitions from expanded → collapsed.
2. **Manual toggle preserved:** if the user has manually collapsed or expanded the panel, the auto-collapse does not override the user's choice within the same message lifetime.
3. **>2000-token rule preserved:** existing Y-S4 behavior unchanged.
4. **Click-path (Amendment 2):** send a synthesis query → reasoning panel expands and shows step timeline while streaming → as soon as the first answer-text-token appears, panel collapses to a single summary line.
5. **Parent-context integration test (Amendment 2):** mount ReasoningProgress within a simulated thread stream that emits reasoning_step events followed by text_delta; assert the panel's collapsed-state flips at the expected event boundary.
6. **A11y:** the panel toggle button retains its existing aria-expanded.

## Pre-commit Gates

```bash
grep -n "hasFirstTextDelta\|first.?text.?delta" platform/src/components/chat/ReasoningProgress.tsx platform/src/lib/chat-v2/useDataParts.ts && echo "PASS"
npx jest --testPathPattern="ReasoningProgress|S-S3|extended-thinking" --passWithNoTests
```

## Commit Template

```
feat(chat-v2): reasoning panel auto-collapse on first text_delta

ReasoningProgress collapses when answer text begins streaming (in addition to the
existing >2000-token rule). User manual toggle preserved. Flagless per §M.16.

Click-path: send query → reasoning expands while streaming → text appears →
reasoning collapses to summary line.
```

## Decision Log

*(Executor: paste sample timing data — at what token count / elapsed-ms does collapse fire on a typical query.)*
