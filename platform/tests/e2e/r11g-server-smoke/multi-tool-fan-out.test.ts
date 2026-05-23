/**
 * multi-tool-fan-out.test.ts — G-S5 server-side integration smoke
 *
 * Single iteration with 2 simultaneous tool calls.
 * Both execute via Promise.all. Both results feed back.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { CapabilityAdapter } from '../../../src/lib/providers/adapter'
import type { ChatRequest, ChatEvent } from '../../../src/lib/providers/types'
import {
  runAgenticLoop,
  ANTHROPIC_LOOP_CONFIG,
} from '../../../src/lib/synthesis/agentic_loop'

// Mock the retrieve/index module
vi.mock('../../../src/lib/retrieve/index', () => ({
  getTool: vi.fn(),
  RETRIEVAL_TOOLS: [],
}))

import { getTool } from '../../../src/lib/retrieve/index'
import { executeMCPTool } from '../../../src/lib/synthesis/mcp_tool_executor'
import type { MCPToolExecutorCtx } from '../../../src/lib/synthesis/mcp_tool_executor'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeCtx(): MCPToolExecutorCtx {
  return {
    queryPlan: {
      query_plan_id: 'smoke-fan-out',
      query_text: 'multi-tool fan-out smoke',
      query_class: 'factual',
      domains: ['natal', 'temporal'],
      forward_looking: false,
      audience_tier: 'super_admin',
      tools_authorized: ['msr_sql', 'query_panchanga'],
      history_mode: 'synthesized',
      panel_mode: false,
      expected_output_shape: 'single_answer',
      manifest_fingerprint: 'smoke-fanout-fingerprint',
      schema_version: '1.0',
    },
  }
}

function makeRequest(): ChatRequest {
  return {
    messages: [{ role: 'user', content: 'Give me both yoga signals and today\'s panchanga.' }],
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
// Multi-tool fan-out tests
// ---------------------------------------------------------------------------

describe('multi-tool-fan-out — 2 simultaneous tool calls in one iteration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('single iteration with 2 tool calls: both execute, both results feed back into next messages', async () => {
    // Iter 1: model emits 2 tool_use_start events (fan-out)
    const iter1Events: ChatEvent[] = [
      // First tool: msr_sql
      { type: 'tool_use_start', id: 'tc-fanout-1', name: 'msr_sql' },
      { type: 'tool_use_input_delta', id: 'tc-fanout-1', partialJson: '{"signal_type":["yoga"],"limit":3}' },
      // Second tool: query_panchanga
      { type: 'tool_use_start', id: 'tc-fanout-2', name: 'query_panchanga' },
      { type: 'tool_use_input_delta', id: 'tc-fanout-2', partialJson: '{"date":"2026-05-23"}' },
      // Both tools stop at same time
      { type: 'message_stop', stopReason: 'tool_use' },
    ]
    // Iter 2: model produces final answer incorporating both results
    const iter2Events: ChatEvent[] = [
      { type: 'text_delta', text: 'Based on MSR yogas and panchanga: auspicious day with strong Saturn yoga.' },
      { type: 'message_stop', stopReason: 'end_turn' },
    ]

    // Mock tools
    const msrSqlTool = {
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({
        results: [
          { content: 'Saturn-Venus yoga (MSR.042): financial abundance', significance: 0.88, source_canonical_id: 'MSR.042', confidence: 0.85, result_hash: 'sha256:a1', schema_version: '1.0' },
          { content: 'Jupiter-Moon yoga (MSR.103): emotional intelligence', significance: 0.76, source_canonical_id: 'MSR.103', confidence: 0.80, result_hash: 'sha256:a2', schema_version: '1.0' },
        ],
      }),
    }
    const panchangaTool = {
      name: 'query_panchanga',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({
        results: [
          { content: 'Tithi: Shukla Panchami | Vara: Shukravara | Nakshatra: Pushya | Yoga: Siddha', significance: 1.0, source_canonical_id: 'PANCHANGA.2026-05-23', confidence: 0.99, result_hash: 'sha256:b1', schema_version: '1.0' },
        ],
      }),
    }

    vi.mocked(getTool).mockImplementation((name: string) => {
      if (name === 'msr_sql') return msrSqlTool as any
      if (name === 'query_panchanga') return panchangaTool as any
      return undefined
    })

    // Track execution order (both should be called)
    const executionOrder: string[] = []
    const originalMsrRetrieve = msrSqlTool.retrieve
    msrSqlTool.retrieve = vi.fn().mockImplementation(async (...args: unknown[]) => {
      executionOrder.push('msr_sql')
      return originalMsrRetrieve(...(args as Parameters<typeof originalMsrRetrieve>))
    })
    const originalPanchangaRetrieve = panchangaTool.retrieve
    panchangaTool.retrieve = vi.fn().mockImplementation(async (...args: unknown[]) => {
      executionOrder.push('query_panchanga')
      return originalPanchangaRetrieve(...(args as Parameters<typeof originalPanchangaRetrieve>))
    })

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
    const collected = await collectEvents(
      runAgenticLoop(
        adapter,
        makeRequest(),
        (toolCall) => executeMCPTool(toolCall, ctx),
        ANTHROPIC_LOOP_CONFIG,
      ),
    )

    // --- Both tools executed ---
    expect(executionOrder).toContain('msr_sql')
    expect(executionOrder).toContain('query_panchanga')
    expect(executionOrder).toHaveLength(2)

    // --- Both tool inputs correctly parsed and dispatched ---
    expect(msrSqlTool.retrieve).toHaveBeenCalledWith(
      ctx.queryPlan,
      { signal_type: ['yoga'], limit: 3 },
    )
    expect(panchangaTool.retrieve).toHaveBeenCalledWith(
      ctx.queryPlan,
      { date: '2026-05-23' },
    )

    // --- 2 chat() calls (2 iterations) ---
    expect(chatCallArgs).toHaveLength(2)

    // --- Both results flow back into next iteration's messages ---
    // iter2 messages: [original_user, assistant(2 tool_use), user(2 tool_results)]
    const iter2Messages = chatCallArgs[1].messages
    expect(iter2Messages).toHaveLength(3)

    // assistant turn has 2 tool_use content items
    const assistantTurn = iter2Messages[1]
    expect(assistantTurn.role).toBe('assistant')
    const assistantContent = assistantTurn.content as Array<{ type: string; id: string; name: string }>
    expect(Array.isArray(assistantContent)).toBe(true)
    expect(assistantContent).toHaveLength(2)
    expect(assistantContent[0].type).toBe('tool_use')
    expect(assistantContent[0].name).toBe('msr_sql')
    expect(assistantContent[1].type).toBe('tool_use')
    expect(assistantContent[1].name).toBe('query_panchanga')

    // user turn has 2 tool_result content items
    const userTurn = iter2Messages[2]
    expect(userTurn.role).toBe('user')
    const userContent = userTurn.content as Array<{ type: string; toolUseId: string; content: string }>
    expect(Array.isArray(userContent)).toBe(true)
    expect(userContent).toHaveLength(2)
    expect(userContent[0].type).toBe('tool_result')
    expect(userContent[1].type).toBe('tool_result')

    // msr_sql result present
    const msrResult = JSON.parse(userContent[0].content)
    expect(msrResult.tool).toBe('msr_sql')
    expect(msrResult.results).toHaveLength(2)

    // panchanga result present
    const panchangaResult = JSON.parse(userContent[1].content)
    expect(panchangaResult.tool).toBe('query_panchanga')
    expect(panchangaResult.results).toHaveLength(1)
    expect(panchangaResult.results[0].content).toContain('Pushya')

    // --- Final answer incorporates both results ---
    const textDelta = collected.find(e => e.type === 'text_delta') as { type: 'text_delta'; text: string } | undefined
    expect(textDelta).toBeDefined()
    expect(textDelta?.text).toContain('auspicious day')
  })

  it('one tool fails, other succeeds — both results (success + error) flow back', async () => {
    // Iter 1: two tools, one will fail
    const iter1Events: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tc-mix-1', name: 'msr_sql' },
      { type: 'tool_use_input_delta', id: 'tc-mix-1', partialJson: '{}' },
      { type: 'tool_use_start', id: 'tc-mix-2', name: 'query_panchanga' },
      { type: 'tool_use_input_delta', id: 'tc-mix-2', partialJson: '{"date":"2026-05-23"}' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]
    const iter2Events: ChatEvent[] = [
      { type: 'text_delta', text: 'Partial data available despite retrieval error.' },
      { type: 'message_stop', stopReason: 'end_turn' },
    ]

    const msrSqlTool = {
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockRejectedValue(new Error('msr_sql timeout')),
    }
    const panchangaTool = {
      name: 'query_panchanga',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({
        results: [
          { content: 'Tithi: Shukla Panchami', significance: 1.0, source_canonical_id: 'PANCHANGA.X', confidence: 0.99, result_hash: 'sha256:c1', schema_version: '1.0' },
        ],
      }),
    }

    vi.mocked(getTool).mockImplementation((name: string) => {
      if (name === 'msr_sql') return msrSqlTool as any
      if (name === 'query_panchanga') return panchangaTool as any
      return undefined
    })

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

    // Loop must NOT throw even when one of two tools fails
    expect(threw).toBe(false)
    expect(chatCallArgs).toHaveLength(2)

    const iter2Messages = chatCallArgs[1].messages
    const userContent = iter2Messages[2].content as Array<{ type: string; content: string }>
    expect(userContent).toHaveLength(2)

    // One is error, one is success — both feed back
    const contents = userContent.map(u => u.content)
    const hasError = contents.some(c => c.startsWith('ERROR:'))
    const hasSuccess = contents.some(c => {
      try { const p = JSON.parse(c); return p.tool === 'query_panchanga' } catch { return false }
    })
    expect(hasError).toBe(true)
    expect(hasSuccess).toBe(true)
  })
})
