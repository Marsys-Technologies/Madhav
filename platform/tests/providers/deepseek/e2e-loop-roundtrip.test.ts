/**
 * e2e-loop-roundtrip.test.ts — R11F-B-S5 E2E integration test for DeepSeek
 *
 * Proves that the DeepSeek adapter forwards tools to the DeepSeek API (OpenAI-compat)
 * and that the agentic loop correctly processes tool calls, injects results, and
 * terminates on a final stop signal.
 *
 * Three test cases:
 *   1. Round-trip: tools forwarded → tool_use events → tool result injected → final text
 *   2. Cap:        iteration cap (MAX_ITERATIONS) is respected — AgenticLoopCapExceeded thrown
 *   3. Floor:      B.11 floor context messages are preserved across loop iterations
 *
 * Strategy: vi.hoisted() + vi.mock('openai') to intercept client.chat.completions.create().
 * We spy on mockCreate to verify tools were forwarded in the correct OpenAI-compat format.
 * DeepSeek uses the raw OpenAI SDK — parameters is plain JSON Schema, no jsonSchema() wrapper.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { toolCallStream, finalTextStream, normalStopStream } from './fixtures/tool_use_stream'

// Declare the mock stub BEFORE vi.mock (vi.hoisted ensures it's available at hoist time).
const { mockCreate } = vi.hoisted(() => ({ mockCreate: vi.fn() }))

vi.mock('openai', () => {
  function MockOpenAI() {
    return { chat: { completions: { create: mockCreate } } }
  }
  return { default: MockOpenAI }
})

// server-only guard: stub it before adapter is imported
vi.mock('server-only', () => ({}))

import { DeepSeekAdapter } from '../../../src/lib/providers/deepseek/adapter'
import {
  runAgenticLoop,
  DEEPSEEK_LOOP_CONFIG,
  AgenticLoopCapExceeded,
  MAX_ITERATIONS,
} from '../../../src/lib/synthesis/agentic_loop'
import type { ChatTool, ChatRequest } from '../../../src/lib/providers/types'

// ---------------------------------------------------------------------------
// Shared test fixtures
// ---------------------------------------------------------------------------

const B11_TOOLS: ChatTool[] = [
  {
    name: 'query_signals',
    description: 'Query MSR signals from the Holistic Synthesis layer (B.11 floor)',
    inputSchema: {
      type: 'object',
      properties: {
        signal_id: { type: 'string', description: 'MSR signal identifier' },
      },
      required: ['signal_id'],
    },
  },
]

const BASE_REQUEST: ChatRequest = {
  model: 'deepseek-chat',
  messages: [
    {
      role: 'system',
      content: 'B.11 floor: route through L2.5 Holistic Synthesis before answering.',
    },
    {
      role: 'user',
      content: 'What does Rahu indicate in the chart?',
    },
  ],
  tools: B11_TOOLS,
}

// ---------------------------------------------------------------------------
// Test 1: Round-trip — tools forwarded → tool_use events → result injected → final text
// ---------------------------------------------------------------------------

describe('R11F-B-S5: DeepSeek round-trip — tools forwarded + loop terminates on stop', () => {
  beforeEach(() => {
    mockCreate.mockReset()
  })

  it('forwards tools in OpenAI-compat function format when request.tools is provided', async () => {
    // First call: tool invocation stream; second call: final text stream
    mockCreate
      .mockResolvedValueOnce(toolCallStream())
      .mockResolvedValueOnce(finalTextStream())

    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('Signal MSR.042: Rahu in 12H — isolation themes')

    const events: Array<Record<string, unknown>> = []
    for await (const e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
      events.push(e as Record<string, unknown>)
    }

    // Verify tools were forwarded on the FIRST call to the DeepSeek API
    expect(mockCreate).toHaveBeenCalledTimes(2)
    const firstCallParams = mockCreate.mock.calls[0][0]
    expect(firstCallParams.tools).toBeDefined()
    expect(firstCallParams.tools).toHaveLength(1)
    expect(firstCallParams.tools[0]).toMatchObject({
      type: 'function',
      function: {
        name: 'query_signals',
        description: 'Query MSR signals from the Holistic Synthesis layer (B.11 floor)',
      },
    })
    // DeepSeek uses plain JSON Schema — no jsonSchema() wrapper
    expect(firstCallParams.tools[0].function.parameters).toMatchObject({
      type: 'object',
      properties: { signal_id: { type: 'string' } },
    })
  })

  it('emits tool_use_start, tool_use_input_delta, tool_use_complete from first iteration', async () => {
    mockCreate
      .mockResolvedValueOnce(toolCallStream())
      .mockResolvedValueOnce(finalTextStream())

    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('Signal MSR.042: Rahu data')

    const events: Array<Record<string, unknown>> = []
    for await (const e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
      events.push(e as Record<string, unknown>)
    }

    expect(events.find((e) => e.type === 'tool_use_start')).toMatchObject({
      type: 'tool_use_start',
      id: 'call_ds1',
      name: 'query_signals',
    })
    expect(events.find((e) => e.type === 'tool_use_complete')).toMatchObject({
      type: 'tool_use_complete',
      id: 'call_ds1',
      name: 'query_signals',
      input: { signal_id: 'MSR.042' },
    })
  })

  it('executes the tool executor with the parsed tool input', async () => {
    mockCreate
      .mockResolvedValueOnce(toolCallStream())
      .mockResolvedValueOnce(finalTextStream())

    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('Signal MSR.042: Rahu 12H')

    for await (const _e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
      // drain
    }

    expect(toolExecutor).toHaveBeenCalledOnce()
    expect(toolExecutor).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'call_ds1', name: 'query_signals', input: { signal_id: 'MSR.042' } }),
    )
  })

  it('injects tool result into second-iteration message history', async () => {
    mockCreate
      .mockResolvedValueOnce(toolCallStream())
      .mockResolvedValueOnce(finalTextStream())

    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('Signal MSR.042: Rahu 12H isolation')

    for await (const _e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
      // drain
    }

    // Second call should include the tool result in messages
    const secondCallParams = mockCreate.mock.calls[1][0]
    const msgContents = secondCallParams.messages.map((m: { role: string; content: unknown }) => m.content)
    const resultMsg = msgContents.find((c: unknown) => typeof c === 'string' && c.includes('tool_result'))
    expect(resultMsg).toBeDefined()
  })

  it('emits final text_delta from second iteration after tool result', async () => {
    mockCreate
      .mockResolvedValueOnce(toolCallStream())
      .mockResolvedValueOnce(finalTextStream())

    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('MSR.042 data')

    const events: Array<Record<string, unknown>> = []
    for await (const e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
      events.push(e as Record<string, unknown>)
    }

    const textDeltas = events.filter((e) => e.type === 'text_delta').map((e) => e.text)
    const fullText = textDeltas.join('')
    expect(fullText).toContain('Rahu in the 12th house indicates isolation themes.')
  })

  it('terminates after 2 iterations (tool call + final stop)', async () => {
    mockCreate
      .mockResolvedValueOnce(toolCallStream())
      .mockResolvedValueOnce(finalTextStream())

    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('result')

    for await (const _e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
      // drain
    }

    expect(mockCreate).toHaveBeenCalledTimes(2)
  })
})

// ---------------------------------------------------------------------------
// Test 2: Cap — iteration cap is respected
// ---------------------------------------------------------------------------

describe('R11F-B-S5: iteration cap — AgenticLoopCapExceeded after MAX_ITERATIONS', () => {
  beforeEach(() => {
    mockCreate.mockReset()
    // Always return a tool call stream — the loop never naturally terminates.
    mockCreate.mockImplementation(() => toolCallStream())
  })

  it(`throws AgenticLoopCapExceeded after ${MAX_ITERATIONS} iterations`, async () => {
    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('result')

    async function drainLoop() {
      for await (const _e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
        // drain
      }
    }

    await expect(drainLoop()).rejects.toThrow(AgenticLoopCapExceeded)
  })

  it('does not exceed MAX_ITERATIONS calls to the DeepSeek API', async () => {
    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('result')

    try {
      for await (const _e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
        // drain
      }
    } catch (err) {
      expect(err).toBeInstanceOf(AgenticLoopCapExceeded)
    }

    expect(mockCreate.mock.calls.length).toBeLessThanOrEqual(MAX_ITERATIONS)
  })

  it('error message references MAX_ITERATIONS', async () => {
    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('result')

    try {
      for await (const _e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
        // drain
      }
    } catch (err) {
      expect(err).toBeInstanceOf(AgenticLoopCapExceeded)
      expect((err as AgenticLoopCapExceeded).message).toContain('MAX_ITERATIONS')
    }
  })
})

// ---------------------------------------------------------------------------
// Test 3: B.11 floor context preserved across iterations
// ---------------------------------------------------------------------------

describe('R11F-B-S5: B.11 floor — system prompt preserved across loop iterations', () => {
  beforeEach(() => {
    mockCreate.mockReset()
  })

  it('preserves the B.11 system message in every API call', async () => {
    mockCreate
      .mockResolvedValueOnce(toolCallStream())
      .mockResolvedValueOnce(finalTextStream())

    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('MSR.042 data')

    for await (const _e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
      // drain
    }

    // Both API calls should carry the system prompt
    for (const call of mockCreate.mock.calls) {
      const params = call[0]
      const systemMsg = params.messages.find(
        (m: { role: string; content: string }) =>
          m.role === 'system' && m.content.includes('B.11 floor'),
      )
      expect(systemMsg).toBeDefined()
    }
  })

  it('preserves tools in the second iteration call', async () => {
    mockCreate
      .mockResolvedValueOnce(toolCallStream())
      .mockResolvedValueOnce(finalTextStream())

    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('MSR.042 data')

    for await (const _e of runAgenticLoop(adapter, BASE_REQUEST, toolExecutor, DEEPSEEK_LOOP_CONFIG)) {
      // drain
    }

    // Tools must be forwarded in both iterations (the loop reuses currentRequest)
    const secondCallParams = mockCreate.mock.calls[1][0]
    expect(secondCallParams.tools).toBeDefined()
    expect(secondCallParams.tools).toHaveLength(1)
    expect(secondCallParams.tools[0].function.name).toBe('query_signals')
  })

  it('no tools forwarded when request.tools is empty — clean path', async () => {
    mockCreate.mockResolvedValueOnce(normalStopStream())

    const adapter = new DeepSeekAdapter()
    const toolExecutor = vi.fn().mockResolvedValue('unused')

    const requestWithoutTools: ChatRequest = {
      ...BASE_REQUEST,
      tools: [],
    }

    const events: Array<Record<string, unknown>> = []
    for await (const e of runAgenticLoop(
      adapter,
      requestWithoutTools,
      toolExecutor,
      DEEPSEEK_LOOP_CONFIG,
    )) {
      events.push(e as Record<string, unknown>)
    }

    const callParams = mockCreate.mock.calls[0][0]
    // When tools is empty, streamParams.tools should not be set
    expect(callParams.tools).toBeUndefined()
    expect(toolExecutor).not.toHaveBeenCalled()
    expect(events.find((e) => e.type === 'text_delta')).toMatchObject({
      text: 'Direct answer from B.11 floor context.',
    })
  })

  it('DEEPSEEK_LOOP_CONFIG has hasReasoningMiddleware=true for <think> block preservation', () => {
    // Ensures that across loop iterations, the extractReasoningMiddleware flag is carried.
    // This is a structural invariant — not tested via mock here, but by config shape.
    expect(DEEPSEEK_LOOP_CONFIG.hasReasoningMiddleware).toBe(true)
    expect(DEEPSEEK_LOOP_CONFIG.providerId).toBe('deepseek')
    expect(DEEPSEEK_LOOP_CONFIG.terminationSignal).toBe('finish_reason_tool_calls')
  })
})
