/**
 * E-S2: gemini-loop.test.ts
 *
 * Verifies the Gemini finish_reason=function_calls agentic loop:
 * - GoogleAdapter.tools() returns mode='finish_reason_function_calls'
 * - isToolUseSignal() correctly identifies Gemini function-call signals
 * - GOOGLE_LOOP_CONFIG is correctly shaped
 */

import { describe, it, expect } from 'vitest'
import { GoogleAdapter } from '../../../src/lib/providers/google/adapter'
import {
  isToolUseSignal,
  GOOGLE_LOOP_CONFIG,
} from '../../../src/lib/synthesis/agentic_loop'

describe('E-S2: GoogleAdapter.tools() — finish_reason_function_calls shape', () => {
  const adapter = new GoogleAdapter()
  const response = adapter.tools({
    toolLoopMode: 'finish_reason_function_calls',
    tools: [
      {
        name: 'query_panchanga',
        description: 'Query panchanga for a date',
        inputSchema: { type: 'object', properties: {} },
      },
    ],
    maxIterations: 8,
  })

  it('returns mode=finish_reason_function_calls', () => {
    expect(response.mode).toBe('finish_reason_function_calls')
  })

  it('returns maxIterations=8', () => {
    expect(response.maxIterations).toBe(8)
  })

  it('providerPayload terminationSignal=finish_reason_function_calls', () => {
    expect(response.providerPayload?.terminationSignal).toBe('finish_reason_function_calls')
  })

  it('providerPayload declares both FUNCTION_CALL and function_calls terminationValues', () => {
    const vals = response.providerPayload?.terminationValues as string[]
    expect(vals).toContain('FUNCTION_CALL')
    expect(vals).toContain('function_calls')
  })

  it('providerPayload declares supportsInterleavedTextTool=true (Gemini 2.5 Pro)', () => {
    expect(response.providerPayload?.supportsInterleavedTextTool).toBe(true)
  })
})

describe('E-S2: isToolUseSignal — Gemini finish_reason_function_calls', () => {
  it('returns true for finish_reason=function_calls (normalized)', () => {
    expect(isToolUseSignal('function_calls', 'finish_reason_function_calls')).toBe(true)
  })

  it('returns true for finish_reason=FUNCTION_CALL (SDK enum)', () => {
    expect(isToolUseSignal('FUNCTION_CALL', 'finish_reason_function_calls')).toBe(true)
  })

  it('returns false for finish_reason=STOP (end-of-turn)', () => {
    expect(isToolUseSignal('STOP', 'finish_reason_function_calls')).toBe(false)
  })

  it('returns false for Anthropic stop_reason=tool_use on Gemini channel', () => {
    expect(isToolUseSignal('tool_use', 'finish_reason_function_calls')).toBe(false)
  })
})

describe('E-S2: GOOGLE_LOOP_CONFIG invariants', () => {
  it('has providerId=google', () => {
    expect(GOOGLE_LOOP_CONFIG.providerId).toBe('google')
  })

  it('terminationSignal=finish_reason_function_calls', () => {
    expect(GOOGLE_LOOP_CONFIG.terminationSignal).toBe('finish_reason_function_calls')
  })

  it('supportsInterleavedTextTool=true', () => {
    expect(GOOGLE_LOOP_CONFIG.supportsInterleavedTextTool).toBe(true)
  })

  it('hasReasoningMiddleware=false (Gemini uses native thinking, not extractReasoningMiddleware)', () => {
    expect(GOOGLE_LOOP_CONFIG.hasReasoningMiddleware).toBe(false)
  })
})
