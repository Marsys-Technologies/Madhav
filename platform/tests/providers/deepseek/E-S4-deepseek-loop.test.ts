/**
 * E-S4: deepseek-loop.test.ts
 *
 * Verifies the DeepSeek agentic loop with reasoning preservation:
 * - DeepSeekAdapter.tools() returns mode='finish_reason_tool_calls'
 * - providerPayload declares extractReasoningMiddleware=true
 * - DEEPSEEK_LOOP_CONFIG has hasReasoningMiddleware=true
 */

import { describe, it, expect } from 'vitest'
import { DeepSeekAdapter } from '../../../src/lib/providers/deepseek/adapter'
import {
  DEEPSEEK_LOOP_CONFIG,
} from '../../../src/lib/synthesis/agentic_loop'

describe('E-S4: DeepSeekAdapter.tools() — reasoning preservation', () => {
  const adapter = new DeepSeekAdapter()
  const response = adapter.tools({
    toolLoopMode: 'finish_reason_tool_calls',
    tools: [
      {
        name: 'query_chart_facts',
        description: 'Query chart facts',
        inputSchema: { type: 'object', properties: {} },
      },
    ],
    maxIterations: 8,
  })

  it('returns mode=finish_reason_tool_calls (OpenAI-compat)', () => {
    expect(response.mode).toBe('finish_reason_tool_calls')
  })

  it('returns maxIterations=8', () => {
    expect(response.maxIterations).toBe(8)
  })

  it('providerPayload declares extractReasoningMiddleware=true', () => {
    expect(response.providerPayload?.extractReasoningMiddleware).toBe(true)
  })

  it('providerPayload terminationValue=tool_calls (same as OpenAI)', () => {
    expect(response.providerPayload?.terminationValue).toBe('tool_calls')
  })

  it('providerPayload supportsInterleavedTextTool=false', () => {
    expect(response.providerPayload?.supportsInterleavedTextTool).toBe(false)
  })
})

describe('E-S4: DEEPSEEK_LOOP_CONFIG — reasoning middleware flag', () => {
  it('providerId=deepseek', () => {
    expect(DEEPSEEK_LOOP_CONFIG.providerId).toBe('deepseek')
  })

  it('terminationSignal=finish_reason_tool_calls', () => {
    expect(DEEPSEEK_LOOP_CONFIG.terminationSignal).toBe('finish_reason_tool_calls')
  })

  it('hasReasoningMiddleware=true (extractReasoningMiddleware preserves <think> blocks)', () => {
    expect(DEEPSEEK_LOOP_CONFIG.hasReasoningMiddleware).toBe(true)
  })

  it('supportsInterleavedTextTool=false', () => {
    expect(DEEPSEEK_LOOP_CONFIG.supportsInterleavedTextTool).toBe(false)
  })
})

describe('E-S4: DeepSeek adapter still has extractReasoningMiddleware reference', () => {
  // The existing thinking() method must still signal extractReasoningMiddleware=true
  it('thinking() method has extractReasoningMiddleware in providerPayload', () => {
    const adapter = new DeepSeekAdapter()
    const thinking = adapter.thinking({
      extendedThinkingMode: 'inline_blocks',
    })
    expect(thinking.providerPayload?.extractReasoningMiddleware).toBe(true)
  })
})
