/**
 * E-S1: anthropic-loop.test.ts
 *
 * Verifies the Anthropic stop_reason agentic loop implementation:
 * - AnthropicAdapter.tools() returns a ToolsResponse with mode='stop_reason'
 * - agentic_loop.ts declares the correct termination check
 * - isToolUseSignal() correctly identifies Anthropic tool-use signals
 * - checkIterationCap() throws AgenticLoopCapExceeded at MAX_ITERATIONS
 */

import { describe, it, expect } from 'vitest'
import { AnthropicAdapter } from '../../../src/lib/providers/anthropic/adapter'
import {
  isToolUseSignal,
  checkIterationCap,
  createLoopState,
  accumulateUsage,
  AgenticLoopCapExceeded,
  MAX_ITERATIONS,
  ANTHROPIC_LOOP_CONFIG,
} from '../../../src/lib/synthesis/agentic_loop'

// ---------------------------------------------------------------------------
// Anthropic adapter tools() method
// ---------------------------------------------------------------------------

describe('E-S1: AnthropicAdapter.tools() — ToolsResponse shape', () => {
  const adapter = new AnthropicAdapter()
  const response = adapter.tools({
    toolLoopMode: 'stop_reason',
    tools: [
      {
        name: 'query_chart_facts',
        description: 'Query the astrological chart',
        inputSchema: { type: 'object', properties: {} },
      },
    ],
    maxIterations: 8,
  })

  it('returns mode=stop_reason', () => {
    expect(response.mode).toBe('stop_reason')
  })

  it('returns correct maxIterations', () => {
    expect(response.maxIterations).toBe(8)
  })

  it('returns the tools array unchanged', () => {
    expect(response.tools).toHaveLength(1)
    expect(response.tools[0].name).toBe('query_chart_facts')
  })

  it('providerPayload declares terminationSignal=stop_reason', () => {
    expect(response.providerPayload?.terminationSignal).toBe('stop_reason')
  })

  it('providerPayload declares terminationValue=tool_use', () => {
    expect(response.providerPayload?.terminationValue).toBe('tool_use')
  })

  it('providerPayload declares supportsInterleavedTextTool=true', () => {
    expect(response.providerPayload?.supportsInterleavedTextTool).toBe(true)
  })

  it('defaults to 8 iterations when maxIterations not provided', () => {
    const r = adapter.tools({ toolLoopMode: 'stop_reason', tools: [] })
    expect(r.maxIterations).toBe(8)
  })
})

// ---------------------------------------------------------------------------
// isToolUseSignal — Anthropic
// ---------------------------------------------------------------------------

describe('E-S1: isToolUseSignal — Anthropic stop_reason', () => {
  it('returns true when stop_reason === tool_use', () => {
    expect(isToolUseSignal('tool_use', 'stop_reason')).toBe(true)
  })

  it('returns false when stop_reason === end_turn', () => {
    expect(isToolUseSignal('end_turn', 'stop_reason')).toBe(false)
  })

  it('returns false when stop_reason === max_tokens', () => {
    expect(isToolUseSignal('max_tokens', 'stop_reason')).toBe(false)
  })

  it('returns false for null/undefined', () => {
    expect(isToolUseSignal(null, 'stop_reason')).toBe(false)
    expect(isToolUseSignal(undefined, 'stop_reason')).toBe(false)
  })

  it('does not match finish_reason signals on stop_reason channel', () => {
    expect(isToolUseSignal('tool_calls', 'stop_reason')).toBe(false)
    expect(isToolUseSignal('function_calls', 'stop_reason')).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// Iteration cap safety (E-S8 prerequisite — verified here for Anthropic)
// ---------------------------------------------------------------------------

describe('E-S1: iteration cap — AgenticLoopCapExceeded at MAX_ITERATIONS', () => {
  it(`MAX_ITERATIONS is ${MAX_ITERATIONS}`, () => {
    expect(MAX_ITERATIONS).toBe(8)
  })

  it('throws AgenticLoopCapExceeded when iterations reach cap', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    // Simulate MAX_ITERATIONS iterations
    for (let i = 0; i < MAX_ITERATIONS; i++) {
      state.iterations++
    }
    expect(() => checkIterationCap(state)).toThrow(AgenticLoopCapExceeded)
  })

  it('does not throw before the cap', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    state.iterations = MAX_ITERATIONS - 1
    expect(() => checkIterationCap(state)).not.toThrow()
  })

  it('error message references MAX_ITERATIONS', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    state.iterations = MAX_ITERATIONS
    try {
      checkIterationCap(state)
    } catch (err) {
      expect(err).toBeInstanceOf(AgenticLoopCapExceeded)
      expect((err as AgenticLoopCapExceeded).message).toContain('MAX_ITERATIONS')
    }
  })
})

// ---------------------------------------------------------------------------
// Usage accumulation across loop iterations
// ---------------------------------------------------------------------------

describe('E-S1: usage accumulation — sum across iterations', () => {
  it('accumulates token usage across iterations', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    accumulateUsage(state, { inputTokens: 1000, outputTokens: 200 })
    accumulateUsage(state, { inputTokens: 500, outputTokens: 100, cacheReadTokens: 800 })
    expect(state.totalInputTokens).toBe(1500)
    expect(state.totalOutputTokens).toBe(300)
    expect(state.totalCacheReadTokens).toBe(800)
  })
})
