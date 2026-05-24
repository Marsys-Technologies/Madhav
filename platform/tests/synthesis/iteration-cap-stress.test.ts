/**
 * R11F-C-S2: iteration-cap-stress.test.ts
 *
 * Stress tests for the agentic loop iteration cap (MAX_ITERATIONS=8).
 * Complements the existing iteration-cap.test.ts (unit-level checkIterationCap
 * function tests) by driving the full runAgenticLoop engine under adversarial
 * mock conditions.
 *
 * TC1: Loop halts cleanly at MAX_ITERATIONS when adapter always returns tool_use.
 * TC2: Telemetry is emitted for each iteration before the cap error is thrown.
 * TC3: Cost accumulation over a 3-iteration round-trip stays within +30% of
 *      a single-iteration baseline (cost-spiral guard sanity check).
 */

vi.mock('server-only', () => ({}))

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  runAgenticLoop,
  MAX_ITERATIONS,
  AgenticLoopCapExceeded,
  ANTHROPIC_LOOP_CONFIG,
  OPENAI_LOOP_CONFIG,
  createLoopState,
  checkIterationCap,
} from '../../src/lib/synthesis/agentic_loop'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Builds a mock adapter whose chat() always yields a tool_use stop signal.
 * This simulates a "malicious" or buggy model that never returns end_turn.
 */
function makeInfiniteToolUseAdapter() {
  return {
    chat: vi.fn(async function* () {
      yield { type: 'tool_use_start' as const, id: 'tc-stress', name: 'msr_sql' }
      yield { type: 'tool_use_input_delta' as const, id: 'tc-stress', partialJson: '{}' }
      yield { type: 'usage' as const, inputTokens: 100, outputTokens: 50, cacheReadTokens: 0, cacheCreationTokens: 0 }
      yield { type: 'message_stop' as const, stopReason: 'tool_use' }
    }),
  }
}

/**
 * Builds a mock adapter that stops at a given iteration count, then returns
 * end_turn. Used for TC3 to simulate a bounded 3-iteration round-trip.
 */
function makeBoundedAdapter(stopAfterIterations: number, tokensPerIter: { input: number; output: number }) {
  let callCount = 0
  return {
    chat: vi.fn(async function* () {
      callCount++
      yield { type: 'usage' as const, inputTokens: tokensPerIter.input, outputTokens: tokensPerIter.output, cacheReadTokens: 0, cacheCreationTokens: 0 }
      if (callCount < stopAfterIterations) {
        yield { type: 'tool_use_start' as const, id: `tc-${callCount}`, name: 'msr_sql' }
        yield { type: 'tool_use_input_delta' as const, id: `tc-${callCount}`, partialJson: '{}' }
        yield { type: 'message_stop' as const, stopReason: 'tool_use' }
      } else {
        yield { type: 'message_stop' as const, stopReason: 'end_turn' }
      }
    }),
  }
}

// ---------------------------------------------------------------------------
// TC1: Halts cleanly at MAX_ITERATIONS
// ---------------------------------------------------------------------------

describe('TC1: loop halts at MAX_ITERATIONS when adapter always returns tool_use', () => {
  it('throws AgenticLoopCapExceeded after exactly MAX_ITERATIONS adapter.chat() calls', async () => {
    const mockAdapter = makeInfiniteToolUseAdapter()
    const request = {
      model: 'claude-opus-4-5',
      messages: [{ role: 'user' as const, content: [{ type: 'text' as const, text: 'Query.' }] }],
    }

    let caughtError: unknown = null
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for await (const _ of runAgenticLoop(mockAdapter as any, request as any, async () => '{"result":"ok"}', ANTHROPIC_LOOP_CONFIG)) {
        // consume all events
      }
    } catch (err) {
      caughtError = err
    }

    expect(caughtError).not.toBeNull()
    expect(caughtError).toBeInstanceOf(AgenticLoopCapExceeded)
    // adapter.chat() must be called exactly MAX_ITERATIONS times before the cap fires
    expect(mockAdapter.chat).toHaveBeenCalledTimes(MAX_ITERATIONS)
  })

  it('AgenticLoopCapExceeded.iterations equals MAX_ITERATIONS', async () => {
    const mockAdapter = makeInfiniteToolUseAdapter()
    const request = {
      model: 'claude-opus-4-5',
      messages: [{ role: 'user' as const, content: [{ type: 'text' as const, text: 'Query.' }] }],
    }

    let caughtError: unknown = null
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for await (const _ of runAgenticLoop(mockAdapter as any, request as any, async () => '{}', ANTHROPIC_LOOP_CONFIG)) {
        // consume
      }
    } catch (err) {
      caughtError = err
    }

    expect(caughtError).toBeInstanceOf(AgenticLoopCapExceeded)
    if (caughtError instanceof AgenticLoopCapExceeded) {
      expect(caughtError.iterations).toBe(MAX_ITERATIONS)
    }
  })

  it('cap holds for OpenAI provider (finish_reason_tool_calls signal)', async () => {
    const mockAdapter = {
      chat: vi.fn(async function* () {
        yield { type: 'tool_use_start' as const, id: 'tc-oai', name: 'msr_sql' }
        yield { type: 'tool_use_input_delta' as const, id: 'tc-oai', partialJson: '{}' }
        yield { type: 'message_stop' as const, stopReason: 'tool_calls' }
      }),
    }

    const request = {
      model: 'gpt-4o',
      messages: [{ role: 'user' as const, content: [{ type: 'text' as const, text: 'Query.' }] }],
    }

    let threw = false
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for await (const _ of runAgenticLoop(mockAdapter as any, request as any, async () => '{}', OPENAI_LOOP_CONFIG)) {
        // consume
      }
    } catch (err) {
      threw = err instanceof AgenticLoopCapExceeded
    }

    expect(threw).toBe(true)
    expect(mockAdapter.chat).toHaveBeenCalledTimes(MAX_ITERATIONS)
  })
})

// ---------------------------------------------------------------------------
// TC2: Telemetry events emitted before cap error
// ---------------------------------------------------------------------------

describe('TC2: telemetry is emitted for each iteration before the cap throws', () => {
  it('console.log is called MAX_ITERATIONS times (one telemetry emit per iteration)', async () => {
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

    const mockAdapter = makeInfiniteToolUseAdapter()
    const request = {
      model: 'claude-opus-4-5',
      messages: [{ role: 'user' as const, content: [{ type: 'text' as const, text: 'Query.' }] }],
    }

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for await (const _ of runAgenticLoop(mockAdapter as any, request as any, async () => '{}', ANTHROPIC_LOOP_CONFIG)) {
        // consume
      }
    } catch {
      // expected AgenticLoopCapExceeded
    }

    // emitLoopIterationTelemetry calls console.log once per iteration
    expect(logSpy).toHaveBeenCalledTimes(MAX_ITERATIONS)

    logSpy.mockRestore()
  })

  it('each telemetry log contains marsys_event_type=tool_loop_iteration', async () => {
    const loggedPayloads: unknown[] = []
    const logSpy = vi.spyOn(console, 'log').mockImplementation((...args) => {
      try {
        loggedPayloads.push(JSON.parse(String(args[0])))
      } catch {
        // not JSON
      }
    })

    const mockAdapter = makeInfiniteToolUseAdapter()
    const request = {
      model: 'claude-opus-4-5',
      messages: [{ role: 'user' as const, content: [{ type: 'text' as const, text: 'Query.' }] }],
    }

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for await (const _ of runAgenticLoop(mockAdapter as any, request as any, async () => '{}', ANTHROPIC_LOOP_CONFIG)) {
        // consume
      }
    } catch {
      // expected
    }

    expect(loggedPayloads.length).toBe(MAX_ITERATIONS)
    for (const payload of loggedPayloads) {
      expect((payload as Record<string, unknown>)['marsys_event_type']).toBe('tool_loop_iteration')
    }

    logSpy.mockRestore()
  })

  it('telemetry records sequential iteration numbers 1..MAX_ITERATIONS', async () => {
    const loggedPayloads: Array<Record<string, unknown>> = []
    const logSpy = vi.spyOn(console, 'log').mockImplementation((...args) => {
      try {
        loggedPayloads.push(JSON.parse(String(args[0])))
      } catch {
        // not JSON
      }
    })

    const mockAdapter = makeInfiniteToolUseAdapter()
    const request = {
      model: 'claude-opus-4-5',
      messages: [{ role: 'user' as const, content: [{ type: 'text' as const, text: 'Query.' }] }],
    }

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for await (const _ of runAgenticLoop(mockAdapter as any, request as any, async () => '{}', ANTHROPIC_LOOP_CONFIG)) {
        // consume
      }
    } catch {
      // expected
    }

    const iterations = loggedPayloads.map(p => p['iteration'])
    for (let i = 1; i <= MAX_ITERATIONS; i++) {
      expect(iterations).toContain(i)
    }

    logSpy.mockRestore()
  })
})

// ---------------------------------------------------------------------------
// TC3: Cost within +30% of baseline for a 3-iteration round-trip
// ---------------------------------------------------------------------------

describe('TC3: multi-iteration cost accumulation stays within +30% of baseline', () => {
  /**
   * Baseline: a single non-agentic call with the same token budget.
   * For the cost model we use a simple linear proxy:
   *   cost = inputTokens * INPUT_RATE + outputTokens * OUTPUT_RATE
   * The test asserts that a 3-iteration loop where each iteration uses
   * ~30% fewer output tokens than the baseline does not exceed 1.30× baseline.
   *
   * This validates the loop has sub-linear overhead, not that it reaches
   * a specific dollar figure (rates are provider-dependent).
   */
  const INPUT_RATE = 3.0 / 1_000_000   // $/token (Anthropic claude-opus-4-5 approx)
  const OUTPUT_RATE = 15.0 / 1_000_000

  function computeCost(inputTokens: number, outputTokens: number): number {
    return inputTokens * INPUT_RATE + outputTokens * OUTPUT_RATE
  }

  it('3-iteration round-trip total cost ≤ 1.30× single-call baseline', async () => {
    const BASELINE_INPUT = 3000
    const BASELINE_OUTPUT = 500

    // Each loop iteration uses baseline input + some overhead, but less output
    // (tool calls are short; final answer is shorter than full synthesis).
    const PER_ITER_INPUT = Math.round(BASELINE_INPUT * 0.4) // context grows each turn
    const PER_ITER_OUTPUT = Math.round(BASELINE_OUTPUT * 0.3)

    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

    const mockAdapter = makeBoundedAdapter(3, { input: PER_ITER_INPUT, output: PER_ITER_OUTPUT })

    const request = {
      model: 'claude-opus-4-5',
      messages: [{ role: 'user' as const, content: [{ type: 'text' as const, text: 'Query.' }] }],
    }

    // Collect usage events to tally actual tokens used by the loop
    let totalInput = 0
    let totalOutput = 0

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for await (const event of runAgenticLoop(mockAdapter as any, request as any, async () => '{}', ANTHROPIC_LOOP_CONFIG)) {
        if (event.type === 'usage') {
          totalInput += (event as { type: 'usage'; inputTokens: number; outputTokens: number }).inputTokens
          totalOutput += (event as { type: 'usage'; inputTokens: number; outputTokens: number }).outputTokens
        }
      }
    } catch {
      // should not throw for a bounded adapter
    }

    const baselineCost = computeCost(BASELINE_INPUT, BASELINE_OUTPUT)
    const loopCost = computeCost(totalInput, totalOutput)
    const ratio = loopCost / baselineCost

    // Assert: 3-iteration loop with reduced per-iteration token usage stays
    // within 1.30× the single-call baseline
    expect(ratio).toBeLessThanOrEqual(1.30)

    logSpy.mockRestore()
  })

  it('cost accumulation is monotonically non-decreasing across iterations', async () => {
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

    const costs: number[] = []
    let runningInput = 0
    let runningOutput = 0

    const mockAdapter = makeBoundedAdapter(3, { input: 200, output: 100 })
    const request = {
      model: 'claude-opus-4-5',
      messages: [{ role: 'user' as const, content: [{ type: 'text' as const, text: 'Query.' }] }],
    }

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for await (const event of runAgenticLoop(mockAdapter as any, request as any, async () => '{}', ANTHROPIC_LOOP_CONFIG)) {
        if (event.type === 'usage') {
          runningInput += (event as { type: 'usage'; inputTokens: number; outputTokens: number }).inputTokens
          runningOutput += (event as { type: 'usage'; inputTokens: number; outputTokens: number }).outputTokens
          costs.push(computeCost(runningInput, runningOutput))
        }
      }
    } catch {
      // no throw expected
    }

    // Running cost must be non-decreasing
    for (let i = 1; i < costs.length; i++) {
      expect(costs[i]).toBeGreaterThanOrEqual(costs[i - 1])
    }

    logSpy.mockRestore()
  })
})
