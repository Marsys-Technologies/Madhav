/**
 * E-S3: openai-loop.test.ts
 *
 * Verifies the OpenAI finish_reason=tool_calls agentic loop:
 * - OpenAIAdapter.tools() returns mode='finish_reason_tool_calls'
 * - isToolUseSignal() correctly identifies OpenAI tool-call signals
 * - Responses API preference is documented in providerPayload
 */

import { describe, it, expect } from 'vitest'
import { OpenAIAdapter } from '../../../src/lib/providers/openai/adapter'
import {
  isToolUseSignal,
  OPENAI_LOOP_CONFIG,
} from '../../../src/lib/synthesis/agentic_loop'

describe('E-S3: OpenAIAdapter.tools() — finish_reason_tool_calls shape', () => {
  const adapter = new OpenAIAdapter()
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

  it('returns mode=finish_reason_tool_calls', () => {
    expect(response.mode).toBe('finish_reason_tool_calls')
  })

  it('returns maxIterations=8', () => {
    expect(response.maxIterations).toBe(8)
  })

  it('providerPayload terminationSignal=finish_reason_tool_calls', () => {
    expect(response.providerPayload?.terminationSignal).toBe('finish_reason_tool_calls')
  })

  it('providerPayload terminationValue=tool_calls', () => {
    expect(response.providerPayload?.terminationValue).toBe('tool_calls')
  })

  it('providerPayload documents Responses API preference flag', () => {
    // preferResponsesApi=false until R11.F wires it
    expect('preferResponsesApi' in (response.providerPayload ?? {})).toBe(true)
  })

  it('providerPayload requireStreamOptions=true for usage tracking', () => {
    expect(response.providerPayload?.requireStreamOptions).toBe(true)
  })
})

describe('E-S3: isToolUseSignal — OpenAI finish_reason_tool_calls', () => {
  it('returns true for finish_reason=tool_calls', () => {
    expect(isToolUseSignal('tool_calls', 'finish_reason_tool_calls')).toBe(true)
  })

  it('returns false for finish_reason=stop (end-of-turn)', () => {
    expect(isToolUseSignal('stop', 'finish_reason_tool_calls')).toBe(false)
  })

  it('returns false for finish_reason=length (truncated)', () => {
    expect(isToolUseSignal('length', 'finish_reason_tool_calls')).toBe(false)
  })

  it('does not match Anthropic stop_reason=tool_use', () => {
    expect(isToolUseSignal('tool_use', 'finish_reason_tool_calls')).toBe(false)
  })

  it('does not match Gemini function_calls', () => {
    expect(isToolUseSignal('function_calls', 'finish_reason_tool_calls')).toBe(false)
  })
})

describe('E-S3: OPENAI_LOOP_CONFIG invariants', () => {
  it('has providerId=openai', () => {
    expect(OPENAI_LOOP_CONFIG.providerId).toBe('openai')
  })

  it('terminationSignal=finish_reason_tool_calls', () => {
    expect(OPENAI_LOOP_CONFIG.terminationSignal).toBe('finish_reason_tool_calls')
  })

  it('supportsInterleavedTextTool=false (Chat Completions does not interleave)', () => {
    expect(OPENAI_LOOP_CONFIG.supportsInterleavedTextTool).toBe(false)
  })

  it('hasReasoningMiddleware=false', () => {
    expect(OPENAI_LOOP_CONFIG.hasReasoningMiddleware).toBe(false)
  })
})
