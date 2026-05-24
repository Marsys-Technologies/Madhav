---
artifact: BRIEF_R11F-A-S4_v1_0.md
session_id: R11F-A-S4
version: 1.0
phase: A
parallel_safety: false
depends_on: [R11F-A-S3]
estimated_loc_delta: +120
---

# R11F-A-S4 — Anthropic End-to-End Integration Test

## Scope

Write the test that did not exist before this arc: a full adapter → SDK → tool_call →
executor → second-iteration round-trip test for Anthropic. Uses a spy or VCR-recorded
`streamText` that emits a `tool_use` block, executes via a mocked retrieval executor,
feeds the result back, and asserts the second iteration produces text.

This is the canonical test for AC.b (tool_use round-trip works). Once passing, it proves
the full wiring from A-S1 through A-S3 is correct end-to-end.

## Files May Touch

```
platform/tests/providers/anthropic/e2e-loop-roundtrip.test.ts  (new)
platform/tests/providers/anthropic/fixtures/tool_use_stream.ts  (new — mock stream fixture)
```

## Files Must NOT Touch

```
01_FACTS_LAYER/**
025_HOLISTIC_SYNTHESIS/**
platform/src/lib/providers/**   (no implementation changes in this session)
platform/src/app/api/chat/consume/route.ts
CLAUDE.md
deploy.yml
```

## Preconditions

1. A-S3 committed. Baseline vitest passes.
2. `platform/src/lib/providers/anthropic/adapter.ts` now forwards `tools` to `streamText`.
3. `platform/src/lib/synthesis/agentic_loop.ts` has `runAgenticLoop()` (added in F-S1 of
   the precursor arc).

## Implementation

### Step 1 — Design the mock stream fixture

Create `platform/tests/providers/anthropic/fixtures/tool_use_stream.ts`:

```typescript
import { createMockStream } from '../../helpers/stream_helpers'  // adjust path

/**
 * Simulates an Anthropic streamText response that:
 *   Iteration 1: emits tool_call for 'query_ephemeris' with args { date: '1984-02-05' }
 *   Iteration 2: emits text_delta "Saturn is in Scorpio at 5° 18'"
 */
export const anthropicToolUseFixture = {
  iteration1: [
    { type: 'tool-call-streaming-start', toolCallId: 'tc_001', toolName: 'query_ephemeris' },
    { type: 'tool-call-delta', toolCallId: 'tc_001', argsTextDelta: '{"date":' },
    { type: 'tool-call-delta', toolCallId: 'tc_001', argsTextDelta: '"1984-02-05"}' },
    { type: 'tool-call', toolCallId: 'tc_001', toolName: 'query_ephemeris', args: { date: '1984-02-05' } },
    { type: 'finish', finishReason: 'tool-calls', usage: { promptTokens: 100, completionTokens: 30 } },
  ],
  iteration2: [
    { type: 'text-delta', text: 'Saturn is in Scorpio at 5° 18\'' },
    { type: 'finish', finishReason: 'stop', usage: { promptTokens: 200, completionTokens: 40 } },
  ],
}
```

### Step 2 — Write the E2E test

Create `platform/tests/providers/anthropic/e2e-loop-roundtrip.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AnthropicCapabilityAdapter } from '@/lib/providers/anthropic/adapter'
import { runAgenticLoop } from '@/lib/synthesis/agentic_loop'
import { anthropicToolUseFixture } from './fixtures/tool_use_stream'

// Mock the Vercel AI SDK streamText
vi.mock('ai', async (importOriginal) => {
  const actual = await importOriginal<typeof import('ai')>()
  return { ...actual, streamText: vi.fn() }
})

describe('Anthropic adapter E2E loop round-trip', () => {
  let adapter: AnthropicCapabilityAdapter
  let streamTextMock: ReturnType<typeof vi.fn>

  beforeEach(async () => {
    const { streamText } = await import('ai')
    streamTextMock = streamText as ReturnType<typeof vi.fn>
    adapter = new AnthropicCapabilityAdapter()
  })

  it('executes tool_use block, injects result, and produces text on second iteration', async () => {
    let callCount = 0
    streamTextMock.mockImplementation(() => ({
      fullStream: (async function* () {
        const parts = callCount === 0
          ? anthropicToolUseFixture.iteration1
          : anthropicToolUseFixture.iteration2
        callCount++
        for (const part of parts) yield part
      })(),
    }))

    const mockExecutor = vi.fn().mockResolvedValue(
      JSON.stringify({ planets: [{ name: 'Saturn', sign: 'Scorpio', degree: 5.3 }] })
    )

    const request = {
      model: 'claude-sonnet-4-6',
      messages: [{ role: 'user' as const, content: 'Where was Saturn on my birth date?' }],
      tools: [{ name: 'query_ephemeris', description: 'Query ephemeris', inputSchema: { type: 'object' as const, properties: { date: { type: 'string' } } } }],
      toolsConfig: { toolChoice: 'auto' as const, tools: [] },
    }

    const config = { maxIterations: 8, provider: 'anthropic' as const }
    const events: Array<{ type: string }> = []

    for await (const event of runAgenticLoop(adapter, request, mockExecutor, config)) {
      events.push(event)
    }

    // Assert tool was called
    expect(mockExecutor).toHaveBeenCalledOnce()
    expect(mockExecutor).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'query_ephemeris', input: { date: '1984-02-05' } })
    )

    // Assert second iteration produced text
    const textEvents = events.filter(e => e.type === 'text_delta')
    expect(textEvents.length).toBeGreaterThan(0)

    // Assert streamText was called twice (2 iterations)
    expect(streamTextMock).toHaveBeenCalledTimes(2)

    // Assert tools were passed in BOTH calls
    expect(streamTextMock.mock.calls[0][0].tools).toBeDefined()
    expect(streamTextMock.mock.calls[1][0].tools).toBeDefined()
  })

  it('halts at MAX_ITERATIONS if model keeps calling tools', async () => {
    // Mock streamText to always return tool_use (never stop)
    streamTextMock.mockImplementation(() => ({
      fullStream: (async function* () {
        yield* anthropicToolUseFixture.iteration1
      })(),
    }))

    const mockExecutor = vi.fn().mockResolvedValue('result')
    const config = { maxIterations: 3, provider: 'anthropic' as const }
    const events: Array<{ type: string }> = []

    try {
      for await (const event of runAgenticLoop(adapter, {
        model: 'claude-sonnet-4-6',
        messages: [{ role: 'user' as const, content: 'test' }],
        tools: [{ name: 'query_ephemeris', description: 'test', inputSchema: { type: 'object' as const, properties: {} } }],
      }, mockExecutor, config)) {
        events.push(event)
      }
      expect.fail('Should have thrown AgenticLoopCapExceeded')
    } catch (err) {
      expect((err as Error).name).toBe('AgenticLoopCapExceeded')
    }
    expect(mockExecutor).toHaveBeenCalledTimes(3)
  })

  it('passes B.11 floor context through to first iteration', async () => {
    streamTextMock.mockImplementation(() => ({
      fullStream: (async function* () {
        yield* anthropicToolUseFixture.iteration2  // returns text immediately
      })(),
    }))

    const floorContextMarker = '<!-- FLOOR:MSR_573_SIGNALS -->'
    const request = {
      model: 'claude-sonnet-4-6',
      messages: [
        { role: 'system' as const, content: floorContextMarker },
        { role: 'user' as const, content: 'test' },
      ],
      tools: [],
    }

    for await (const _ of runAgenticLoop(adapter, request, vi.fn(), { maxIterations: 8, provider: 'anthropic' as const })) {
      // drain
    }

    // Assert floor context was in the first streamText call
    const firstCallMessages = streamTextMock.mock.calls[0][0].messages
    const allContent = JSON.stringify(firstCallMessages)
    expect(allContent).toContain(floorContextMarker)
  })
})
```

### Step 3 — Verify test runs

```bash
cd platform && npx vitest run tests/providers/anthropic/e2e-loop-roundtrip.test.ts --no-coverage
```

Fix any import paths or mock shapes until all 3 tests pass.

## Acceptance Tests

```bash
# AC.a: E2E test file exists
ls platform/tests/providers/anthropic/e2e-loop-roundtrip.test.ts
# expected: file present

# AC.b: all 3 test cases pass
cd platform && npx vitest run tests/providers/anthropic/e2e-loop-roundtrip.test.ts --no-coverage 2>&1 | tail -10
# expected: 3 tests pass, 0 failures

# AC.c: iteration cap test proves at-most-N guarantee
# (verified by AC.b above — "halts at MAX_ITERATIONS" test)

# AC.d: full vitest
cd platform && npx vitest run --no-coverage 2>&1 | tail -5
# expected: no failures
```

## Deliverable Artifacts

- `platform/tests/providers/anthropic/e2e-loop-roundtrip.test.ts` (new — 3 test cases)
- `platform/tests/providers/anthropic/fixtures/tool_use_stream.ts` (new)
- Commit: `test(r11f-a-s4): anthropic E2E loop round-trip — tool_use, cap, floor context`

## Rollback Steps

```bash
git revert HEAD  # removes test files only; no production code changes
```
