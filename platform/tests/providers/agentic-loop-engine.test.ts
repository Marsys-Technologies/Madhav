/**
 * agentic-loop-engine.test.ts — Unit tests for runAgenticLoop() (F-S1).
 *
 * Covers:
 *   1. Single iteration (no tool use): mock adapter yields text_delta + message_stop('end_turn')
 *      → loop returns after 1 iter, all events yielded.
 *   2. Two iterations (one tool call): iter 1 yields tool_use_start + message_stop('tool_use'),
 *      iter 2 yields text_delta + message_stop('end_turn') → 2 iters executed, tool events present.
 *   3. Cap exceeded: mock always yields message_stop('tool_use') → throws AgenticLoopCapExceeded
 *      after MAX_ITERATIONS.
 *   4. (R11.G-S1) executeMCPTool with mocked MCP backend → real tool results flow into loop.
 *   5. (R11.G-S1) Tool error recovery → loop continues, model receives error string, no throw.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { CapabilityAdapter } from '../../src/lib/providers/adapter'
import type { ChatRequest, ChatEvent } from '../../src/lib/providers/types'
import {
  runAgenticLoop,
  AgenticLoopCapExceeded,
  ANTHROPIC_LOOP_CONFIG,
  MAX_ITERATIONS,
} from '../../src/lib/synthesis/agentic_loop'

// Mock the retrieve/index module so executeMCPTool doesn't hit real DB
vi.mock('../../src/lib/retrieve/index', () => ({
  getTool: vi.fn(),
  RETRIEVAL_TOOLS: [],
}))

import { getTool } from '../../src/lib/retrieve/index'
import { executeMCPTool } from '../../src/lib/synthesis/mcp_tool_executor'
import type { MCPToolExecutorCtx } from '../../src/lib/synthesis/mcp_tool_executor'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Builds a minimal ChatRequest for test use. */
function makeRequest(): ChatRequest {
  return {
    messages: [{ role: 'user', content: 'Hello' }],
    model: 'claude-sonnet-4-6',
  }
}

/** Builds a minimal MCPToolExecutorCtx for test use. */
function makeCtx(): MCPToolExecutorCtx {
  return {
    queryPlan: {
      query_plan_id: 'test-plan-id',
      query_text: 'test query',
      query_class: 'factual',
      domains: ['natal'],
      forward_looking: false,
      audience_tier: 'super_admin',
      tools_authorized: ['msr_sql', 'query_panchanga'],
      history_mode: 'synthesized',
      panel_mode: false,
      expected_output_shape: 'single_answer',
      manifest_fingerprint: 'test-fingerprint',
      schema_version: '1.0',
    },
  }
}

/**
 * Creates a minimal CapabilityAdapter mock whose chat() method returns
 * the given sequence of events on each successive call.
 *
 * `eventSequences[0]` is yielded on the first chat() call,
 * `eventSequences[1]` on the second, etc.
 */
function makeMockAdapter(eventSequences: ChatEvent[][]): CapabilityAdapter {
  let callIndex = 0

  return {
    providerId: 'anthropic',
    getManifest: vi.fn(),
    chat: async function* (_req: ChatRequest): AsyncIterable<ChatEvent> {
      const events = eventSequences[callIndex] ?? []
      callIndex++
      for (const event of events) {
        yield event
      }
    },
    thinking: vi.fn(),
    cache: vi.fn(),
    tools: vi.fn(),
    webSearch: vi.fn(),
    webFetch: vi.fn(),
    codeExecution: vi.fn(),
    memory: vi.fn(),
    multimodal: vi.fn(),
    imageGeneration: vi.fn(),
    computerUse: vi.fn() as unknown as CapabilityAdapter['computerUse'],
    structuredOutputs: vi.fn(),
  } as unknown as CapabilityAdapter
}

/** Collects all events from an AsyncIterable into an array. */
async function collectEvents(iterable: AsyncIterable<ChatEvent>): Promise<ChatEvent[]> {
  const collected: ChatEvent[] = []
  for await (const event of iterable) {
    collected.push(event)
  }
  return collected
}

// ---------------------------------------------------------------------------
// Test 1: Single iteration — no tool use
// ---------------------------------------------------------------------------

describe('runAgenticLoop — single iteration (no tool use)', () => {
  it('returns after 1 iteration and yields all events', async () => {
    const events: ChatEvent[] = [
      { type: 'text_delta', text: 'Hello, world!' },
      { type: 'usage', inputTokens: 10, outputTokens: 5 },
      { type: 'message_stop', stopReason: 'end_turn' },
    ]

    const adapter = makeMockAdapter([events])
    const toolExecutor = vi.fn().mockResolvedValue('tool output')

    const collected = await collectEvents(
      runAgenticLoop(adapter, makeRequest(), toolExecutor, ANTHROPIC_LOOP_CONFIG),
    )

    // All 3 events must be yielded
    expect(collected).toHaveLength(3)
    expect(collected[0]).toEqual({ type: 'text_delta', text: 'Hello, world!' })
    expect(collected[1]).toEqual({ type: 'usage', inputTokens: 10, outputTokens: 5 })
    expect(collected[2]).toEqual({ type: 'message_stop', stopReason: 'end_turn' })

    // Tool executor must NOT have been called (no tool use)
    expect(toolExecutor).not.toHaveBeenCalled()
  })

  it('handles empty event stream gracefully (no tool_use, no stop reason → 1 iter, no events)', async () => {
    const adapter = makeMockAdapter([[]])
    const toolExecutor = vi.fn()

    const collected = await collectEvents(
      runAgenticLoop(adapter, makeRequest(), toolExecutor, ANTHROPIC_LOOP_CONFIG),
    )

    // Empty sequence, stop reason is null → isToolUseSignal(null, ...) is false → loop exits
    expect(collected).toHaveLength(0)
    expect(toolExecutor).not.toHaveBeenCalled()
  })
})

// ---------------------------------------------------------------------------
// Test 2: Two iterations — one tool call
// ---------------------------------------------------------------------------

describe('runAgenticLoop — two iterations with one tool call', () => {
  it('executes tool, feeds result back, yields events from both iterations', async () => {
    const iter1Events: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tool-1', name: 'get_info' },
      { type: 'tool_use_input_delta', id: 'tool-1', partialJson: '{"key":' },
      { type: 'tool_use_input_delta', id: 'tool-1', partialJson: '"value"}' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]

    const iter2Events: ChatEvent[] = [
      { type: 'text_delta', text: 'Based on the tool result...' },
      { type: 'message_stop', stopReason: 'end_turn' },
    ]

    const adapter = makeMockAdapter([iter1Events, iter2Events])
    const toolExecutor = vi.fn().mockResolvedValue('tool result data')

    const collected = await collectEvents(
      runAgenticLoop(adapter, makeRequest(), toolExecutor, ANTHROPIC_LOOP_CONFIG),
    )

    // All 6 events from both iterations are yielded in order
    expect(collected).toHaveLength(6)

    // Iter 1 events
    expect(collected[0]).toEqual({ type: 'tool_use_start', id: 'tool-1', name: 'get_info' })
    expect(collected[1]).toEqual({ type: 'tool_use_input_delta', id: 'tool-1', partialJson: '{"key":' })
    expect(collected[2]).toEqual({ type: 'tool_use_input_delta', id: 'tool-1', partialJson: '"value"}' })
    expect(collected[3]).toEqual({ type: 'message_stop', stopReason: 'tool_use' })

    // Iter 2 events
    expect(collected[4]).toEqual({ type: 'text_delta', text: 'Based on the tool result...' })
    expect(collected[5]).toEqual({ type: 'message_stop', stopReason: 'end_turn' })

    // Tool executor called once with the assembled tool call
    expect(toolExecutor).toHaveBeenCalledTimes(1)
    expect(toolExecutor).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'tool-1', name: 'get_info', input: { key: 'value' } }),
    )
  })

  it('second chat() call receives the augmented message history (assistant + user turns added)', async () => {
    const iter1Events: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tool-abc', name: 'lookup' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]
    const iter2Events: ChatEvent[] = [
      { type: 'text_delta', text: 'done' },
      { type: 'message_stop', stopReason: 'end_turn' },
    ]

    // Capture chat() arguments
    const chatCallArgs: ChatRequest[] = []
    const adapter: CapabilityAdapter = {
      providerId: 'anthropic',
      getManifest: vi.fn(),
      chat: async function* (req: ChatRequest): AsyncIterable<ChatEvent> {
        chatCallArgs.push(req)
        const events = chatCallArgs.length === 1 ? iter1Events : iter2Events
        for (const event of events) yield event
      },
      thinking: vi.fn(),
      cache: vi.fn(),
      tools: vi.fn(),
      webSearch: vi.fn(),
      webFetch: vi.fn(),
      codeExecution: vi.fn(),
      memory: vi.fn(),
      multimodal: vi.fn(),
      imageGeneration: vi.fn(),
      computerUse: vi.fn() as unknown as CapabilityAdapter['computerUse'],
      structuredOutputs: vi.fn(),
    } as unknown as CapabilityAdapter

    const toolExecutor = vi.fn().mockResolvedValue('lookup result')

    await collectEvents(
      runAgenticLoop(adapter, makeRequest(), toolExecutor, ANTHROPIC_LOOP_CONFIG),
    )

    // chat() must have been called exactly twice
    expect(chatCallArgs).toHaveLength(2)

    // First call: original 1-message history
    expect(chatCallArgs[0].messages).toHaveLength(1)

    // Second call: original + assistant tool-use turn + user tool-result turn = 3 messages
    const secondMessages = chatCallArgs[1].messages
    expect(secondMessages).toHaveLength(3)

    // assistant turn has tool_use content
    const assistantTurn = secondMessages[1]
    expect(assistantTurn.role).toBe('assistant')
    expect(Array.isArray(assistantTurn.content)).toBe(true)
    const assistantContent = assistantTurn.content as Array<{ type: string }>
    expect(assistantContent[0].type).toBe('tool_use')

    // user turn has tool_result content
    const userTurn = secondMessages[2]
    expect(userTurn.role).toBe('user')
    expect(Array.isArray(userTurn.content)).toBe(true)
    const userContent = userTurn.content as Array<{ type: string }>
    expect(userContent[0].type).toBe('tool_result')
  })
})

// ---------------------------------------------------------------------------
// Test 3: Cap exceeded
// ---------------------------------------------------------------------------

describe('runAgenticLoop — iteration cap exceeded', () => {
  it('throws AgenticLoopCapExceeded after MAX_ITERATIONS when model always returns tool_use', async () => {
    // Every iteration yields a tool-use start + tool_use stop reason
    const singleIterEvents: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tool-x', name: 'noop' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]

    // Provide enough event sequences to cover MAX_ITERATIONS calls
    const sequences = Array.from({ length: MAX_ITERATIONS + 2 }, () => [...singleIterEvents])
    const adapter = makeMockAdapter(sequences)
    const toolExecutor = vi.fn().mockResolvedValue('result')

    await expect(async () => {
      await collectEvents(
        runAgenticLoop(adapter, makeRequest(), toolExecutor, ANTHROPIC_LOOP_CONFIG),
      )
    }).rejects.toThrow(AgenticLoopCapExceeded)
  })

  it('AgenticLoopCapExceeded carries the correct iteration count', async () => {
    const singleIterEvents: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tool-y', name: 'noop' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]

    const sequences = Array.from({ length: MAX_ITERATIONS + 2 }, () => [...singleIterEvents])
    const adapter = makeMockAdapter(sequences)
    const toolExecutor = vi.fn().mockResolvedValue('result')

    let caughtError: AgenticLoopCapExceeded | null = null
    try {
      await collectEvents(
        runAgenticLoop(adapter, makeRequest(), toolExecutor, ANTHROPIC_LOOP_CONFIG),
      )
    } catch (err) {
      if (err instanceof AgenticLoopCapExceeded) {
        caughtError = err
      }
    }

    expect(caughtError).not.toBeNull()
    expect(caughtError?.iterations).toBe(MAX_ITERATIONS)
    expect(caughtError?.name).toBe('AgenticLoopCapExceeded')
  })

  it('respects custom maxIterations in config', async () => {
    const customConfig = { ...ANTHROPIC_LOOP_CONFIG, maxIterations: 3 }
    const singleIterEvents: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tool-z', name: 'noop' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]
    const sequences = Array.from({ length: 10 }, () => [...singleIterEvents])
    const adapter = makeMockAdapter(sequences)
    const toolExecutor = vi.fn().mockResolvedValue('result')

    let caughtError: AgenticLoopCapExceeded | null = null
    try {
      await collectEvents(runAgenticLoop(adapter, makeRequest(), toolExecutor, customConfig))
    } catch (err) {
      if (err instanceof AgenticLoopCapExceeded) {
        caughtError = err
      }
    }

    expect(caughtError).not.toBeNull()
    expect(caughtError?.iterations).toBe(3)
  })
})

// ---------------------------------------------------------------------------
// Test 4: executeMCPTool — real tool results flow back (R11.G-S1, AC.G1.3)
// ---------------------------------------------------------------------------

describe('executeMCPTool — real tool results via mocked MCP backend (AC.G1.3)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns serialised JSON when tool succeeds', async () => {
    const mockTool = {
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({
        results: [
          { content: 'Signal MSR.001: Saturn in 10H', significance: 0.9, source_canonical_id: 'MSR.001', confidence: 0.85, result_hash: 'sha256:abc', schema_version: '1.0' },
        ],
      }),
    }
    vi.mocked(getTool).mockReturnValue(mockTool as any)

    const ctx = makeCtx()
    const toolCall = { id: 'tc-1', name: 'msr_sql', input: { signal_type: ['yoga'] } }
    const result = await executeMCPTool(toolCall, ctx)

    expect(result).not.toMatch(/^ERROR:/)
    const parsed = JSON.parse(result)
    expect(parsed.tool).toBe('msr_sql')
    expect(parsed.results).toHaveLength(1)
    expect(parsed.result_count).toBe(1)
    expect(mockTool.retrieve).toHaveBeenCalledWith(ctx.queryPlan, { signal_type: ['yoga'] })
  })

  it('returns ERROR string when tool is not registered (AC.G1.4)', async () => {
    vi.mocked(getTool).mockReturnValue(undefined)

    const ctx = makeCtx()
    const toolCall = { id: 'tc-2', name: 'nonexistent_tool', input: {} }
    const result = await executeMCPTool(toolCall, ctx)

    expect(result).toMatch(/^ERROR:/)
    expect(result).toContain('nonexistent_tool')
  })

  it('returns ERROR string (not throw) when tool.retrieve() rejects (AC.G1.4)', async () => {
    const mockTool = {
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockRejectedValue(new Error('DB connection failed')),
    }
    vi.mocked(getTool).mockReturnValue(mockTool as any)

    const ctx = makeCtx()
    const toolCall = { id: 'tc-3', name: 'msr_sql', input: {} }
    const result = await executeMCPTool(toolCall, ctx)

    expect(result).toMatch(/^ERROR:/)
    expect(result).toContain('DB connection failed')
  })

  it('real executeMCPTool flows into runAgenticLoop — results appear in next iteration messages', async () => {
    // Iter 1: model requests msr_sql tool
    const iter1Events: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tc-loop-1', name: 'msr_sql' },
      { type: 'tool_use_input_delta', id: 'tc-loop-1', partialJson: '{"signal_type":["yoga"]}' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]
    // Iter 2: model produces final answer
    const iter2Events: ChatEvent[] = [
      { type: 'text_delta', text: 'Based on msr_sql results, Saturn is strong.' },
      { type: 'message_stop', stopReason: 'end_turn' },
    ]

    const mockTool = {
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({
        results: [{ content: 'Saturn 10H yoga active', significance: 0.9, source_canonical_id: 'MSR.001', confidence: 0.85, result_hash: 'sha256:abc', schema_version: '1.0' }],
      }),
    }
    vi.mocked(getTool).mockReturnValue(mockTool as any)

    const chatCallArgs: ChatRequest[] = []
    const adapter: CapabilityAdapter = {
      providerId: 'anthropic',
      getManifest: vi.fn(),
      chat: async function* (req: ChatRequest): AsyncIterable<ChatEvent> {
        chatCallArgs.push(req)
        const events = chatCallArgs.length === 1 ? iter1Events : iter2Events
        for (const event of events) yield event
      },
      thinking: vi.fn(),
      cache: vi.fn(),
      tools: vi.fn(),
      webSearch: vi.fn(),
      webFetch: vi.fn(),
      codeExecution: vi.fn(),
      memory: vi.fn(),
      multimodal: vi.fn(),
      imageGeneration: vi.fn(),
      computerUse: vi.fn() as unknown as CapabilityAdapter['computerUse'],
      structuredOutputs: vi.fn(),
    } as unknown as CapabilityAdapter

    const ctx = makeCtx()
    const collected: ChatEvent[] = []
    for await (const event of runAgenticLoop(
      adapter,
      makeRequest(),
      (toolCall) => executeMCPTool(toolCall, ctx),
      ANTHROPIC_LOOP_CONFIG,
    )) {
      collected.push(event)
    }

    // Both iterations' events yielded
    expect(collected).toHaveLength(5)
    // msr_sql tool was called
    expect(mockTool.retrieve).toHaveBeenCalledTimes(1)
    // Second chat() call has 3 messages (original + assistant tool-use + user tool-result)
    expect(chatCallArgs).toHaveLength(2)
    const secondMessages = chatCallArgs[1].messages
    expect(secondMessages).toHaveLength(3)
    // user tool-result turn carries the JSON output from executeMCPTool
    const userTurn = secondMessages[2]
    expect(userTurn.role).toBe('user')
    const userContent = userTurn.content as Array<{ type: string; content: string }>
    expect(userContent[0].type).toBe('tool_result')
    const toolResultContent = userContent[0].content
    expect(toolResultContent).toContain('msr_sql')
    expect(toolResultContent).toContain('Saturn 10H yoga active')
  })
})

// ---------------------------------------------------------------------------
// Test 5: Tool error recovery — loop continues, no abort (R11.G-S1, AC.G1.4)
// ---------------------------------------------------------------------------

describe('executeMCPTool — tool error recovery in loop (AC.G1.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('middle iteration tool returns ERROR string → loop continues, model receives error, loop does NOT throw', async () => {
    // Iter 1: model requests a tool that will fail
    const iter1Events: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tc-err-1', name: 'msr_sql' },
      { type: 'tool_use_input_delta', id: 'tc-err-1', partialJson: '{}' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]
    // Iter 2: model reacts to error and produces final answer
    const iter2Events: ChatEvent[] = [
      { type: 'text_delta', text: 'I encountered an error but can still answer.' },
      { type: 'message_stop', stopReason: 'end_turn' },
    ]

    // Tool fails with an exception
    const mockTool = {
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockRejectedValue(new Error('Simulated DB failure')),
    }
    vi.mocked(getTool).mockReturnValue(mockTool as any)

    const chatCallArgs: ChatRequest[] = []
    const adapter: CapabilityAdapter = {
      providerId: 'anthropic',
      getManifest: vi.fn(),
      chat: async function* (req: ChatRequest): AsyncIterable<ChatEvent> {
        chatCallArgs.push(req)
        const events = chatCallArgs.length === 1 ? iter1Events : iter2Events
        for (const event of events) yield event
      },
      thinking: vi.fn(),
      cache: vi.fn(),
      tools: vi.fn(),
      webSearch: vi.fn(),
      webFetch: vi.fn(),
      codeExecution: vi.fn(),
      memory: vi.fn(),
      multimodal: vi.fn(),
      imageGeneration: vi.fn(),
      computerUse: vi.fn() as unknown as CapabilityAdapter['computerUse'],
      structuredOutputs: vi.fn(),
    } as unknown as CapabilityAdapter

    const ctx = makeCtx()
    const collected: ChatEvent[] = []

    // Must NOT throw — loop completes naturally after error recovery
    let threw = false
    try {
      for await (const event of runAgenticLoop(
        adapter,
        makeRequest(),
        (toolCall) => executeMCPTool(toolCall, ctx),
        ANTHROPIC_LOOP_CONFIG,
      )) {
        collected.push(event)
      }
    } catch {
      threw = true
    }
    expect(threw).toBe(false)

    // Both iterations ran — 5 events total
    expect(collected).toHaveLength(5)
    expect(chatCallArgs).toHaveLength(2)

    // The second chat() call received the error string in the tool_result
    const secondMessages = chatCallArgs[1].messages
    const userTurn = secondMessages[2]
    const userContent = userTurn.content as Array<{ type: string; content: string }>
    expect(userContent[0].type).toBe('tool_result')
    // Error message was passed through to the model
    expect(userContent[0].content).toMatch(/ERROR:.*Simulated DB failure/)
  })

  it('AgenticLoopCapExceeded is thrown only on cap breach — not on tool errors', async () => {
    // Every iteration: one tool call that fails; model always requests another tool (tool_use stop)
    const singleIterEvents: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tc-cap', name: 'msr_sql' },
      { type: 'tool_use_input_delta', id: 'tc-cap', partialJson: '{}' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]

    const mockTool = {
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockRejectedValue(new Error('persistent failure')),
    }
    vi.mocked(getTool).mockReturnValue(mockTool as any)

    const sequences = Array.from({ length: MAX_ITERATIONS + 2 }, () => [...singleIterEvents])
    const adapter = makeMockAdapter(sequences)
    const ctx = makeCtx()

    await expect(async () => {
      await collectEvents(
        runAgenticLoop(
          adapter,
          makeRequest(),
          (toolCall) => executeMCPTool(toolCall, ctx),
          ANTHROPIC_LOOP_CONFIG,
        ),
      )
    }).rejects.toThrow(AgenticLoopCapExceeded)
  })
})
