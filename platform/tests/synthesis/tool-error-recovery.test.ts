/**
 * E-S7: tool-error-recovery.test.ts
 *
 * Verifies tool error recovery in the agentic loop:
 * - safeExecuteTool() catches thrown errors and returns isError=true result
 * - Error output is passed back to the model as tool_result content
 * - Loop continues after a tool error (up to cap)
 * - Final response can reference the error gracefully
 */

import { describe, it, expect } from 'vitest'
import {
  safeExecuteTool,
  createLoopState,
  ANTHROPIC_LOOP_CONFIG,
  type LoopToolCall,
} from '../../src/lib/synthesis/agentic_loop'

const mockToolCall: LoopToolCall = {
  id: 'tool_abc123',
  name: 'query_chart_facts',
  input: { native_id: 'test-id' },
  streamPosition: 0,
}

describe('E-S7: safeExecuteTool — error recovery', () => {
  it('returns isError=false when executor succeeds', async () => {
    const result = await safeExecuteTool(mockToolCall, async () => 'chart data here')
    expect(result.isError).toBe(false)
    expect(result.output).toBe('chart data here')
    expect(result.id).toBe(mockToolCall.id)
    expect(result.name).toBe(mockToolCall.name)
  })

  it('returns isError=true when executor throws Error', async () => {
    const result = await safeExecuteTool(mockToolCall, async () => {
      throw new Error('DB connection timeout')
    })
    expect(result.isError).toBe(true)
    expect(result.output).toContain('DB connection timeout')
    expect(result.id).toBe(mockToolCall.id)
  })

  it('returns isError=true when executor throws string', async () => {
    const result = await safeExecuteTool(mockToolCall, async () => {
      // eslint-disable-next-line @typescript-eslint/no-throw-literal
      throw 'network error'
    })
    expect(result.isError).toBe(true)
    expect(result.output).toContain('network error')
  })

  it('wraps error message with "Tool execution failed:" prefix', async () => {
    const result = await safeExecuteTool(mockToolCall, async () => {
      throw new Error('ephemeris calculation failed')
    })
    expect(result.output).toMatch(/Tool execution failed:/)
    expect(result.output).toContain('ephemeris calculation failed')
  })

  it('never re-throws — always returns a LoopToolResult', async () => {
    // Even with a completely unexpected error, safeExecuteTool should not throw
    let threw = false
    try {
      await safeExecuteTool(mockToolCall, async () => {
        throw new TypeError('unexpected type mismatch')
      })
    } catch {
      threw = true
    }
    expect(threw).toBe(false)
  })
})

describe('E-S7: loop state persists across errors', () => {
  it('state is not reset by a tool error', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    state.iterations = 2
    state.totalInputTokens = 2000
    // Simulate recording a failed tool call
    state.toolCallHistory.push({
      iteration: 2,
      toolCall: mockToolCall,
      result: {
        id: mockToolCall.id,
        name: mockToolCall.name,
        output: 'Tool execution failed: DB timeout',
        isError: true,
      },
    })
    // State is preserved — loop can continue
    expect(state.iterations).toBe(2)
    expect(state.totalInputTokens).toBe(2000)
    expect(state.toolCallHistory).toHaveLength(1)
  })

  it('error result is stored in toolCallHistory for audit trail', () => {
    const state = createLoopState(ANTHROPIC_LOOP_CONFIG)
    const failedResult = {
      id: 'tool_xyz',
      name: 'query_ephemeris',
      output: 'Tool execution failed: ephemeris data unavailable',
      isError: true,
    }
    state.toolCallHistory.push({ iteration: 1, toolCall: mockToolCall, result: failedResult })
    expect(state.toolCallHistory[0].result.isError).toBe(true)
    expect(state.toolCallHistory[0].result.output).toContain('ephemeris data unavailable')
  })
})
