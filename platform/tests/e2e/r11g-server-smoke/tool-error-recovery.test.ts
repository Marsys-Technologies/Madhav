/**
 * tool-error-recovery.test.ts — G-S5 server-side integration smoke
 *
 * Middle iteration's tool returns "ERROR: <msg>" string.
 * Loop must continue; model receives error string and reacts.
 * AgenticLoopCapExceeded thrown only on iteration cap — NOT on tool error.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { CapabilityAdapter } from '../../../src/lib/providers/adapter'
import type { ChatRequest, ChatEvent } from '../../../src/lib/providers/types'
import {
  runAgenticLoop,
  AgenticLoopCapExceeded,
  ANTHROPIC_LOOP_CONFIG,
  MAX_ITERATIONS,
} from '../../../src/lib/synthesis/agentic_loop'

// Mock the retrieve/index module
// D7 Step 4: mock getToolByName from tool_name_bridge (lib/retrieve/index RETIRED)
vi.mock('../../../src/lib/retrieval/registry/tool_name_bridge', async (importOriginal) => {
  const real = await importOriginal() as Record<string, unknown>
  return { ...real, getToolByName: vi.fn() }
})

import { getToolByName as getTool } from '../../../src/lib/retrieval/registry/tool_name_bridge'
import { executeMCPTool } from '../../../src/lib/synthesis/mcp_tool_executor'
import type { MCPToolExecutorCtx } from '../../../src/lib/synthesis/mcp_tool_executor'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeCtx(): MCPToolExecutorCtx {
  return {
    queryPlan: {
      query_plan_id: 'smoke-error-recovery',
      query_text: 'error recovery smoke',
      query_class: 'factual',
      domains: ['natal'],
      forward_looking: false,
      audience_tier: 'super_admin',
      tools_authorized: ['msr_sql'],
      history_mode: 'synthesized',
      panel_mode: false,
      expected_output_shape: 'single_answer',
      manifest_fingerprint: 'smoke-err-fingerprint',
      schema_version: '1.0',
    },
  }
}

function makeRequest(): ChatRequest {
  return {
    messages: [{ role: 'user', content: 'What is the status of my chart?' }],
    model: 'claude-sonnet-4-6',
  }
}

async function collectEvents(iterable: AsyncIterable<ChatEvent>): Promise<ChatEvent[]> {
  const collected: ChatEvent[] = []
  for await (const event of iterable) {
    collected.push(event)
  }
  return collected
}

// ---------------------------------------------------------------------------
// Error recovery tests
// ---------------------------------------------------------------------------

describe('tool-error-recovery — middle iteration ERROR string loops continue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('middle iteration tool fails → loop continues → model receives error string → final answer produced', async () => {
    // Iter 1: model requests msr_sql tool (will fail)
    const iter1Events: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tc-err-mid', name: 'msr_sql' },
      { type: 'tool_use_input_delta', id: 'tc-err-mid', partialJson: '{"signal_type":["yoga"]}' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]
    // Iter 2: model reacts to error, produces final answer
    const iter2Events: ChatEvent[] = [
      { type: 'text_delta', text: 'I encountered a retrieval error but can still provide context from my training.' },
      { type: 'message_stop', stopReason: 'end_turn' },
    ]

    // Tool raises an exception → executeMCPTool returns "ERROR: ..." string
    const failingTool = {
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockRejectedValue(new Error('DB connection refused: timeout after 30s')),
    }
    vi.mocked(getTool).mockReturnValue(failingTool as any)

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
    let threw = false
    const collected: ChatEvent[] = []

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

    // Loop must NOT abort on tool error
    expect(threw).toBe(false)

    // Both iterations ran (5 events: 3 from iter1 + 2 from iter2)
    expect(collected).toHaveLength(5)

    // 2 chat() calls
    expect(chatCallArgs).toHaveLength(2)

    // Second call includes the ERROR string in tool_result
    const iter2Messages = chatCallArgs[1].messages
    // messages: [original_user, assistant(tool_use), user(tool_result)]
    expect(iter2Messages).toHaveLength(3)

    const userTurn = iter2Messages[2]
    expect(userTurn.role).toBe('user')
    const userContent = userTurn.content as Array<{ type: string; content: string }>
    expect(userContent[0].type).toBe('tool_result')

    // ERROR string was passed to the model (not thrown)
    expect(userContent[0].content).toMatch(/^ERROR:/)
    expect(userContent[0].content).toContain('DB connection refused')

    // Final answer was produced
    const textDelta = collected.find(e => e.type === 'text_delta') as { type: 'text_delta'; text: string } | undefined
    expect(textDelta).toBeDefined()
    expect(textDelta?.text).toContain('retrieval error')
  })

  it('loop does NOT abort when tool returns ERROR string — isError=true result propagates cleanly', async () => {
    // Iter 1: tool lookup fails (unknown tool → ERROR string from executeMCPTool itself)
    const iter1Events: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tc-unknown', name: 'totally_nonexistent_tool' },
      { type: 'tool_use_input_delta', id: 'tc-unknown', partialJson: '{}' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]
    // Iter 2: model continues after error
    const iter2Events: ChatEvent[] = [
      { type: 'text_delta', text: 'The tool was unavailable. Here is what I know.' },
      { type: 'message_stop', stopReason: 'end_turn' },
    ]

    // getTool returns undefined → ERROR string
    vi.mocked(getTool).mockReturnValue(undefined)

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
    let threw = false
    const collected: ChatEvent[] = []
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
    expect(collected).toHaveLength(5)

    // Error string from unknown tool is in the user's tool_result turn
    const secondMessages = chatCallArgs[1].messages
    const userContent = secondMessages[2].content as Array<{ type: string; content: string }>
    expect(userContent[0].content).toMatch(/^ERROR:/)
    expect(userContent[0].content).toContain('totally_nonexistent_tool')
  })

  it('AgenticLoopCapExceeded is thrown only on iteration cap — NOT on tool errors', async () => {
    // Every iteration: tool fails, but model keeps requesting tools (cap breach)
    const singleIterEvents: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tc-persistent-err', name: 'msr_sql' },
      { type: 'tool_use_input_delta', id: 'tc-persistent-err', partialJson: '{}' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]

    const alwaysFailingTool = {
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockRejectedValue(new Error('persistent tool failure — never recovers')),
    }
    vi.mocked(getTool).mockReturnValue(alwaysFailingTool as any)

    const sequences = Array.from({ length: MAX_ITERATIONS + 2 }, () => [...singleIterEvents])
    let callIndex = 0
    const adapter: CapabilityAdapter = {
      providerId: 'anthropic',
      getManifest: vi.fn(),
      chat: async function* (_req: ChatRequest): AsyncIterable<ChatEvent> {
        const events = sequences[callIndex] ?? []
        callIndex++
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

    // Must throw AgenticLoopCapExceeded — not any other error
    let caughtError: unknown = null
    try {
      await collectEvents(
        runAgenticLoop(
          adapter,
          makeRequest(),
          (toolCall) => executeMCPTool(toolCall, ctx),
          ANTHROPIC_LOOP_CONFIG,
        ),
      )
    } catch (err) {
      caughtError = err
    }

    expect(caughtError).not.toBeNull()
    expect(caughtError).toBeInstanceOf(AgenticLoopCapExceeded)
    const loopErr = caughtError as AgenticLoopCapExceeded
    expect(loopErr.iterations).toBe(MAX_ITERATIONS)
    expect(loopErr.name).toBe('AgenticLoopCapExceeded')
  })
})
