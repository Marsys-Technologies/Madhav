---
artifact: BRIEF_R11F-B-S5_v1_0.md
session_id: R11F-B-S5
version: 1.0
phase: B
parallel_safety: false
depends_on: [R11F-B-S1, R11F-B-S3]
estimated_loc_delta: +80
---

# R11F-B-S5 — DeepSeek + NVIDIA: Verify/Fix Tool Forwarding + Combined Smoke

## Scope

The precursor arc (F-S2) added tool-event emission to DeepSeek and NVIDIA adapters, but
tool forwarding to the AI SDK was not confirmed. This session:

1. Verifies or patches `deepseek/adapter.ts` tool forwarding (OpenAI-compat wire format).
2. Verifies or patches `nvidia/adapter.ts` tool forwarding (OpenAI NIM compat).
3. Investigates whether NVIDIA NIM's chosen model supports function calling; documents
   the outcome; marks the NVIDIA loop flag N/A in `feature_flags.ts` if not supported.
4. Adds E2E integration tests for DeepSeek and NVIDIA (or NVIDIA-skip doc if N/A).
5. Runs visual smoke for both providers via Chrome MCP.
6. **DeepSeek R1 limitation**: documents whether tool calls survive interleaving with
   reasoning blocks (`<think>...</think>`) — full fix deferred to R11.G if not.

## Files May Touch

```
platform/src/lib/providers/deepseek/adapter.ts
platform/src/lib/providers/nvidia/adapter.ts
platform/src/lib/config/feature_flags.ts   (NVIDIA N/A annotation if needed)
platform/tests/providers/deepseek-tool-events.test.ts
platform/tests/providers/nvidia-tool-events.test.ts
platform/tests/providers/deepseek/e2e-loop-roundtrip.test.ts  (new)
platform/tests/providers/nvidia/e2e-loop-roundtrip.test.ts    (new, or SKIP_REASON.md)
```

## Files Must NOT Touch

```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
platform/src/lib/providers/anthropic/**
platform/src/lib/providers/google/**
platform/src/lib/providers/openai/**
platform/src/app/api/chat/consume/route.ts
CLAUDE.md
deploy.yml
```

## Implementation

### Step 1 — DeepSeek adapter audit

Read `deepseek/adapter.ts`. DeepSeek is OpenAI-compatible at the wire level. Apply the
same tool forwarding as B-S3 (OpenAI):

```typescript
if (request.tools && request.tools.length > 0) {
  streamParams.tools = request.tools.map(tool => ({
    type: 'function' as const,
    function: { name: tool.name, description: tool.description ?? '', parameters: jsonSchema(tool.inputSchema ?? { type: 'object', properties: {} }) },
  }))
}
if (request.toolsConfig?.toolChoice) streamParams.toolChoice = request.toolsConfig.toolChoice
```

#### DeepSeek R1 thinking-block caveat

If the chosen DeepSeek model is R1 (reasoning model), test whether tool_call events arrive
correctly when the model also emits `<think>` blocks. Inspect the stream fixture from
`deepseek-tool-events.test.ts` — does it interleave thinking parts with tool parts?

Document finding in a comment in the test file:
```
// NOTE: DeepSeek R1 interleaves <think> blocks with tool_call events.
// The adapter currently yields thinking_delta events before tool_use_start.
// Full reasoning+tool interleaving is R11.G scope; tool calls still work
// if the model uses standard format without extended reasoning blocks.
```

### Step 2 — NVIDIA NIM adapter audit

Read `nvidia/adapter.ts`. NVIDIA NIM exposes OpenAI-compatible endpoints but function
calling support depends on the deployed model (e.g., `meta/llama-3.1-70b-instruct` supports
tools; `meta/llama-3.2-1b-instruct` may not).

**Decision tree:**

**Case A — Model supports function calling:**
Apply same tool forwarding as B-S3. Write E2E test. Set NVIDIA loop as supported.

**Case B — Model does NOT support function calling:**
- Add a comment to `feature_flags.ts` on the `R11E_NVIDIA_LOOP` line:
  ```typescript
  R11E_NVIDIA_LOOP: false,  // N/A — NIM model does not support function calling; see R11F-B-S5
  ```
- Create `tests/providers/nvidia/SKIP_REASON.md` documenting the NIM model name and
  capability limitation.
- Do NOT add `MARSYS_FLAG_R11E_NVIDIA_LOOP` to `deploy.yml` in C-S3.

### Step 3 — E2E tests

Write `tests/providers/deepseek/e2e-loop-roundtrip.test.ts` (3 cases, same structure as A-S4).

Write `tests/providers/nvidia/e2e-loop-roundtrip.test.ts` if Case A, or create
`SKIP_REASON.md` if Case B.

### Step 4 — Visual smoke (DeepSeek)

Navigate to `/consume` with DeepSeek provider selected. Send the dasha query. Screenshot.

Save:
```
00_ARCHITECTURE/chat_v2_briefs/round11f/visual_evidence/deepseek/
  smoke_01_response.png
  smoke_02_tool_flow.png
```

### Step 5 — Visual smoke (NVIDIA)

Case A: Same procedure. Save to `visual_evidence/nvidia/`.
Case B: Save a screenshot of the settings showing NVIDIA provider selected and a text
response (no tool-flow timeline expected). Document as "NVIDIA function calling: N/A".

## Acceptance Tests

```bash
# AC.a: DeepSeek tools forwarding
grep -n "streamParams.tools" platform/src/lib/providers/deepseek/adapter.ts
# expected: >= 1 match

# AC.b: DeepSeek E2E test passes
cd platform && npx vitest run tests/providers/deepseek/e2e-loop-roundtrip.test.ts --no-coverage 2>&1 | tail -5
# expected: 3 tests pass

# AC.c: NVIDIA outcome documented
ls platform/tests/providers/nvidia/e2e-loop-roundtrip.test.ts 2>/dev/null || ls platform/tests/providers/nvidia/SKIP_REASON.md
# expected: one of the two files present

# AC.d: full vitest
cd platform && npx vitest run --no-coverage 2>&1 | tail -5
# expected: no failures
```

## Deliverable Artifacts

- Patched `deepseek/adapter.ts` (tool forwarding)
- Patched or annotated `nvidia/adapter.ts` (tool forwarding or N/A comment)
- `tests/providers/deepseek/e2e-loop-roundtrip.test.ts` (new)
- `tests/providers/nvidia/e2e-loop-roundtrip.test.ts` OR `SKIP_REASON.md` (new)
- `visual_evidence/deepseek/` screenshots
- `visual_evidence/nvidia/` screenshots (with N/A note if Case B)
- Commit: `fix(r11f-b-s5): deepseek+nvidia adapter tool forwarding + smoke evidence`

## Rollback Steps

```bash
git revert HEAD
```
