---
canonical_id: R11_O_S3
version: 1.0
status: CURRENT
session_id: O-S3
title: Agentic tool-use loop — `stop_reason` keyed while-loop with interleaved text+tool blocks
depends_on: ["O-S2"]
blocked_on: []
flag: MARSYS_FLAG_R11_AGENTIC_TOOL_LOOP
flag_default: false
client_side: "no — server-side loop topology"
authored: 2026-05-21
---

# O-S3 — Agentic Tool-Use Loop

## Context

Anthropic's documented agentic loop is a `while` keyed on `stop_reason`. The model returns `stop_reason: "tool_use"` with one or more `tool_use` blocks; the client executes each, returns `tool_result` blocks; the model is called again. Multi-step is native. The model can interleave text + tool calls inside a single assistant message.

This session audits Chat V2's existing tool-use loop in `/api/chat/consume/route.ts` (and the planner code path) and aligns it to the documented topology where it diverges. **High-risk session** — behavior-changing. Default false until verified.

## Files in Scope

- `platform/src/app/api/chat/consume/route.ts` — audit the current tool-call dispatch. Document in Decision Log.
- `platform/src/lib/synthesis/agentic_loop.ts` (new or extracted) — implement the canonical loop:
  ```
  while (response.stop_reason === 'tool_use') {
    const toolBlocks = response.content.filter(b => b.type === 'tool_use');
    const toolResults = await Promise.all(toolBlocks.map(execute));
    messages.push({ role: 'assistant', content: response.content });
    messages.push({ role: 'user', content: toolResults });
    response = await anthropic.messages.create({...});
  }
  ```
- `platform/src/lib/feature_flags.ts` — register `MARSYS_FLAG_R11_AGENTIC_TOOL_LOOP` (default false, server-side).
- `platform/tests/` — integration test verifying multi-step tool dispatch under flag=true.

## Files Must NOT Touch

- Tool implementations themselves (registered tools in `lib/retrieve/`)
- The smooth_stream cadence
- Phase 4C files

## Acceptance Criteria

1. **Audit recorded:** current loop topology documented in Decision Log.
2. **Canonical loop implemented:** with flag=true, the route handler dispatches tools in the `stop_reason`-keyed pattern above. Max iteration cap of 8 (documented; configurable).
3. **Interleaved text+tool support:** if Claude returns a response with both `text` and `tool_use` blocks, the text is streamed to the client BEFORE the tool dispatch begins; the tool result completes; then the next iteration's text begins.
4. **Token accounting:** each iteration's `usage` is summed; total Observatory cost emit reflects the total.
5. **Iteration cap safety:** with flag=true, if the loop hits 8 iterations without `stop_reason === 'end_turn'`, an error is returned with a clear message.
6. **Click-path (Amendment 2 — server behavior, but verify via UI):** send a query requiring multiple tool calls in sequence (e.g., panchang followed by signal lookup) → UI shows the tool cards in order → final synthesis appears.
7. **Parent-context integration test (Amendment 2):** end-to-end test sending a multi-tool query and asserting both tool dispatches fired and synthesis text was returned.
8. **Flag guard:** with flag=false, the current single-shot or partial-loop behavior is preserved.

## Pre-commit Gates

```bash
grep -rn "NEXT_PUBLIC.*AGENTIC_TOOL_LOOP" platform/src --include="*.ts*" && echo "FAIL" || echo "PASS"
grep -n "stop_reason.*tool_use\|while.*tool_use" platform/src/lib/synthesis/agentic_loop.ts platform/src/app/api/chat/consume/route.ts
npx jest --testPathPattern="O-S3|agentic-loop|tool-loop" --passWithNoTests
```

## Commit Template

```
feat(synthesis): agentic tool-use loop keyed on stop_reason (O-S3)

Implements canonical while-loop on stop_reason === 'tool_use' with interleaved
text+tool support, 8-iteration cap, total-usage rollup. Guarded by
MARSYS_FLAG_R11_AGENTIC_TOOL_LOOP=false (server-side; no NEXT_PUBLIC).

Audit of current topology in Decision Log.
```

## Decision Log

*(Executor: paste current loop topology, iteration cap chosen, sample multi-tool query trace.)*
