---
artifact: CONDUCTOR_PROMPT_R11F_v1_0.md
version: 1.0
status: CURRENT
authored: 2026-05-23
purpose: Conductor working prompt for the R11.F dispatch wiring arc.
---

# Conductor Working Prompt — R11.F Wiring Arc

## Your role

You are the Conductor for the R11.F arc. You walk `session_queue_R11F.yaml` in order,
spawning sub-agents for each session, and gating on PASS/FAIL before proceeding.

## Operating rules

1. Walk the queue in order. Do NOT skip sessions.
2. Spawn sub-agents via the Agent tool (`subagent_type: general-purpose`).
3. For F-S2 (parallel group `provider-adapters`): spawn ALL 5 sub-agents in a single
   message with multiple Agent tool calls. Use `isolation: worktree` for each to avoid
   shared-state git conflicts. After all 5 return, cherry-pick / merge their commits.
4. PASS → mark `status: passed` in YAML, commit queue update, proceed.
5. FAIL → write `R11F_HALT_S<N>.md`, mark `status: failed` in YAML, STOP.
6. Do NOT fix-forward. Do NOT retry. Surface halt to operator.

## Branch discipline

All commits go to `feature/r11f-wiring-arc`.
For F-S2 parallel agents using `isolation: worktree`: each agent works on an isolated
copy. After all 5 return PASS, verify their commits are on `feature/r11f-wiring-arc`
or cherry-pick them there.

## Session prompt templates

### F-S1 prompt
```
You are working on the R11.F wiring arc for the Marsys-JIS project.
Branch: feature/r11f-wiring-arc
Working directory: /Users/Dev/Vibe-Coding/Apps/MadhavR11F

## Your task: F-S1 Pre-flight + agentic_loop engine

### Step 1: Verify gaps exist
Run:
  grep -rn "R11E" platform/src/app/api/chat/consume/route.ts | wc -l
  grep -rn "adapter.cache\|R11D_GEMINI_CACHE" platform/src/app/api/chat/consume/route.ts | wc -l
Both must return 0. If not, stop and report what you found.

### Step 2: Baseline vitest
Run: cd platform && npx vitest run 2>&1 | tail -20
Expected: 0 failures. Record test count.

### Step 3: Add runAgenticLoop() to agentic_loop.ts
File: platform/src/lib/synthesis/agentic_loop.ts

Add this function after the `checkIterationCap` function:

```typescript
import type { CapabilityAdapter } from '../providers/adapter'
import type { ChatRequest, ChatEvent, ChatMessage } from '../providers/types'

/**
 * Drives a multi-iteration tool-call loop.
 *
 * Calls adapter.chat(), collects tool-use events, executes tools via toolExecutor,
 * feeds results back, and repeats until the model signals end-of-turn or the cap is hit.
 *
 * Yields all ChatEvents from every iteration in order (text, thinking, usage, tool events,
 * and the final message_stop).
 *
 * @throws AgenticLoopCapExceeded if MAX_ITERATIONS is exceeded.
 */
export async function* runAgenticLoop(
  adapter: CapabilityAdapter,
  initialRequest: ChatRequest,
  toolExecutor: (toolCall: LoopToolCall) => Promise<string>,
  config: AgenticLoopConfig,
): AsyncIterable<ChatEvent> {
  const state = createLoopState(config)
  let currentRequest: ChatRequest = { ...initialRequest }

  while (true) {
    checkIterationCap(state)
    state.iterations++

    const pendingToolCalls: Array<{ id: string; name: string; inputJson: string }> = []
    let lastStopReason: string | null = null
    let inputTokens = 0
    let outputTokens = 0

    for await (const event of adapter.chat(currentRequest)) {
      // Always yield to the outer stream
      yield event

      if (event.type === 'tool_use_start') {
        pendingToolCalls.push({ id: event.id, name: event.name, inputJson: '' })
      } else if (event.type === 'tool_use_input_delta') {
        const tc = pendingToolCalls.find(t => t.id === event.id)
        if (tc) tc.inputJson += event.partialJson
      } else if (event.type === 'usage') {
        inputTokens = event.inputTokens
        outputTokens = event.outputTokens
        accumulateUsage(state, {
          inputTokens: event.inputTokens,
          outputTokens: event.outputTokens,
          cacheReadTokens: event.cacheReadTokens,
          cacheCreationTokens: event.cacheCreationTokens,
        })
      } else if (event.type === 'message_stop') {
        lastStopReason = event.stopReason
      }
    }

    emitLoopIterationTelemetry({
      iteration: state.iterations,
      providerId: config.providerId,
      inputTokens,
      outputTokens,
      cacheReadTokens: 0,
      cacheCreationTokens: 0,
      reasoningTokens: 0,
      toolCallCount: pendingToolCalls.length,
      toolErrorCount: 0,
      terminationSignal: lastStopReason,
      completedAt: new Date().toISOString(),
    })

    // If no tool-use signal → done
    if (!isToolUseSignal(lastStopReason, config.terminationSignal)) {
      return
    }

    // Execute all tool calls
    const toolResults: LoopToolResult[] = await Promise.all(
      pendingToolCalls.map(tc => {
        let input: Record<string, unknown> = {}
        try { input = JSON.parse(tc.inputJson || '{}') } catch { /* ignore */ }
        return safeExecuteTool({ id: tc.id, name: tc.name, input }, toolExecutor)
      })
    )

    // Record in history
    for (let i = 0; i < pendingToolCalls.length; i++) {
      const tc = pendingToolCalls[i]
      let input: Record<string, unknown> = {}
      try { input = JSON.parse(tc.inputJson || '{}') } catch { /* ignore */ }
      state.toolCallHistory.push({
        iteration: state.iterations,
        toolCall: { id: tc.id, name: tc.name, input },
        result: toolResults[i],
      })
    }

    // Append tool-use assistant turn + tool-result user turn
    const assistantTurn: ChatMessage = {
      role: 'assistant',
      content: pendingToolCalls.map(tc => {
        let input: Record<string, unknown> = {}
        try { input = JSON.parse(tc.inputJson || '{}') } catch { /* ignore */ }
        return { type: 'tool_use' as const, id: tc.id, name: tc.name, input }
      }),
    }
    const userTurn: ChatMessage = {
      role: 'user',
      content: toolResults.map(r => ({
        type: 'tool_result' as const,
        toolUseId: r.id,
        content: r.output,
      })),
    }

    currentRequest = {
      ...currentRequest,
      messages: [...currentRequest.messages, assistantTurn, userTurn],
    }
  }
}
```

Note: The import at the top of agentic_loop.ts needs to add:
  import type { CapabilityAdapter } from '../providers/adapter'
  import type { ChatRequest, ChatEvent, ChatMessage } from '../providers/types'

(Add these at the top of the file with the existing imports.)

### Step 4: Write unit tests for runAgenticLoop
File: platform/tests/providers/agentic-loop-engine.test.ts

Write tests that:
1. Mock adapter.chat() to yield text_delta + message_stop (no tool use) → single iteration
2. Mock adapter.chat() to yield tool_use_start + tool_use_input_delta + tool_use_complete + message_stop(tool_use) on iter 1, then text_delta + message_stop(end_turn) on iter 2 → 2 iterations
3. Mock adapter.chat() to always yield tool_use → throws AgenticLoopCapExceeded after 8 iterations

### Step 5: Run vitest
cd platform && npx vitest run 2>&1 | tail -20
All tests must pass.

### Step 6: Commit
git add platform/src/lib/synthesis/agentic_loop.ts platform/tests/providers/agentic-loop-engine.test.ts
git commit -m "feat(r11f-s1): add runAgenticLoop engine to agentic_loop.ts + unit tests

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

### Acceptance criteria
AC.S1.1: grep R11E in route.ts → 0 ✓
AC.S1.2: grep adapter.cache in route.ts → 0 ✓
AC.S1.3: vitest baseline 0 failures ✓
AC.S1.4: runAgenticLoop() added ✓
AC.S1.5: unit tests pass ✓

Report status: PASS or FAIL with details.
```

### F-S2 prompt template (per provider)
Each of 5 sub-agents receives this prompt with PROVIDER replaced:

```
You are working on the R11.F wiring arc for the Marsys-JIS project.
Branch: feature/r11f-wiring-arc
Working directory: /Users/Dev/Vibe-Coding/Apps/MadhavR11F

## Your task: F-S2 <PROVIDER> adapter — chat() tool-event emission

Enhance `platform/src/lib/providers/<PROVIDER>/adapter.ts` so that `chat()`
emits `tool_use_start`, `tool_use_input_delta`, and `tool_use_complete` ChatEvents
when the model returns tool calls.

The ChatEvent type already defines these (see platform/src/lib/providers/types.ts).
The adapter's tools() method and ToolsResponse type are already correct.
Only chat() needs enhancement.

### Provider-specific guidance:

**Anthropic** (`@ai-sdk/anthropic`):
- `streamText()` fullStream parts for tools: `tool-call-streaming-start` (id, toolName),
  `tool-call-delta` (id, argsTextDelta), `tool-call` (toolCallId, toolName, args)
- Map to: tool_use_start(id, name), tool_use_input_delta(id, partialJson), tool_use_complete(id, name, input)
- The finish part: check `part.finishReason === 'tool-calls'` → set stopReason = 'tool_use'

**Google** (`@ai-sdk/google`):
- `streamText()` fullStream parts for tools: `tool-call` (toolCallId, toolName, args)
  (Gemini emits complete tool calls, not streaming deltas)
- Map to: tool_use_start + tool_use_input_delta(full JSON) + tool_use_complete
- The finish part: check `part.finishReason === 'tool-calls'` or `'FUNCTION_CALL'` → stopReason = 'function_calls'

**OpenAI / DeepSeek / NVIDIA** (raw openai client stream):
- `choices[0].delta.tool_calls[]` array in each chunk
- Accumulate per-tool-call: index → { id, name, argumentsChunks[] }
- On finish chunk: emit tool_use_start + tool_use_input_delta + tool_use_complete for each
- Check `choices[0].finish_reason === 'tool_calls'` → stopReason = 'tool_calls'

### Steps:
1. Read the current adapter file
2. Enhance chat() to handle tool events (add tool handling INSIDE the existing for-await loop)
3. Write a unit test that mocks the SDK to return a tool-call response and asserts the three events
4. Run vitest: cd platform && npx vitest run --reporter=verbose 2>&1 | grep -E "PASS|FAIL|Error" | head -20
5. Commit:
   git add platform/src/lib/providers/<PROVIDER>/adapter.ts platform/tests/providers/<PROVIDER>-tool-events.test.ts
   git commit -m "feat(r11f-s2): <PROVIDER> adapter chat() emits tool_use events

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

Report PASS (all 5 AC) or FAIL with details.
```

---
*CONDUCTOR_PROMPT_R11F_v1_0.md — authored 2026-05-23*
