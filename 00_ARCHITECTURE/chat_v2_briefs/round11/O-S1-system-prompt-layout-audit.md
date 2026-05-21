---
canonical_id: R11_O_S1
version: 1.0
status: CURRENT
session_id: O-S1
title: System-prompt layout audit — align to Anthropic cache layout (tools → system → messages)
depends_on: ["S-S5"]
blocked_on: []
flag: MARSYS_FLAG_R11_PROMPT_LAYOUT_V2
flag_default: false
client_side: "no — server-side prompt assembly"
authored: 2026-05-21
---

# O-S1 — System-Prompt Layout Audit

## Context

Anthropic's prompt-caching docs prescribe the assembly order **tools → system → messages**, with `cache_control` breakpoints placed at the end of each. The current Marsys synthesis prompt assembly order in `/api/chat/consume/route.ts` and `lib/synthesis/` is unknown without an audit — this session audits, documents, and (if non-conforming) re-orders behind a flag.

**Hard preservation rule (Amendment 4):** The R7-S2 footnote citation instruction block AND the Y-S4 `### Step: <label>` step-marker instructions must be preserved byte-identical when the prompt is re-arranged. They may move within the prompt but not be edited.

## Files in Scope

- `platform/src/lib/synthesis/synthesis_prompt_v2.ts` (or equivalent — audit confirms file location) — audit existing structure, document current order in this brief's Decision Log.
- `platform/src/app/api/chat/consume/route.ts` — audit how prompt + tools + messages are passed to the Anthropic Messages API call.
- `platform/src/lib/synthesis/prompt_assembler.ts` (new or existing) — if a new layout V2 is needed, implement it here behind `MARSYS_FLAG_R11_PROMPT_LAYOUT_V2`.
- `platform/src/lib/feature_flags.ts` — register the flag (default false, server-side).
- `platform/tests/` — snapshot test of the assembled prompt with the flag both ways.

## Files Must NOT Touch

- The R7-S2 footnote block text (preservation rule)
- The Y-S4 step-marker text (preservation rule)
- `.github/workflows/deploy.yml` (server-side flag)
- Phase 4C files

## Acceptance Criteria

1. **Audit recorded:** Decision Log contains the current prompt assembly order (line ranges + section labels).
2. **V2 layout assembled:** with flag=true, the request to the Anthropic API has `tools` parameter populated, `system` parameter populated, and `messages` array in this exact order — matching Anthropic's documented cache layout.
3. **R7-S2 footnote block preserved (Amendment 4):** `git diff platform/src/lib/synthesis/synthesis_prompt_v2.ts | grep -C5 footnote` shows the block byte-identical. Document the diff in Decision Log.
4. **Y-S4 step-marker block preserved (Amendment 4):** `git diff … | grep -C5 "### Step"` shows the marker instruction block byte-identical.
5. **Snapshot test:** asserts that with flag=true the assembled API payload matches the V2 layout shape.
6. **Flag guard:** with flag=false, behavior is exactly current — including byte-identical request body.
7. **No regression in synthesis quality:** executor runs 3 sample synthesis queries with flag=true and confirms output quality is on par or better (subjective; document in Decision Log).

## Pre-commit Gates

```bash
# Server-side only
grep -rn "NEXT_PUBLIC.*PROMPT_LAYOUT_V2" platform/src --include="*.ts*" && echo "FAIL: NEXT_PUBLIC" || echo "PASS: server-side"

# Preservation verification (executor runs manually)
# git diff platform/src/lib/synthesis/synthesis_prompt_v2.ts | grep -C5 "footnote\|### Step"

npx jest --testPathPattern="O-S1|prompt-layout|prompt-assembler" --passWithNoTests
```

## Commit Template

```
feat(synthesis): system-prompt layout v2 — align to Anthropic cache layout (O-S1)

Restructures prompt assembly to tools → system → messages order. R7-S2 footnote
block and Y-S4 step-marker block preserved byte-identical. Guarded by
MARSYS_FLAG_R11_PROMPT_LAYOUT_V2=false (server-side; no NEXT_PUBLIC).

Current layout audited; diff in Decision Log.
```

## Decision Log

*(Executor: paste current prompt structure, target V2 structure, diff of preserved blocks confirming byte-identity, 3 sample synthesis outputs.)*
