/**
 * tool-executor-loop.test.ts — G-S5 server-side integration smoke
 *
 * 3-iteration loop with REAL executeMCPTool invocations.
 * MCP backend mocked at the transport layer (getTool/retrieve).
 *
 * Assertions:
 *   1. Each iteration's tool result string flows back into the next iteration's messages array.
 *   2. Tool input JSON is correctly parsed before dispatch.
 *   3. Loop completes with final answer text after model emits end_turn / stop.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { CapabilityAdapter } from '../../../src/lib/providers/adapter'
import type { ChatRequest, ChatEvent } from '../../../src/lib/providers/types'
import {
  runAgenticLoop,
  ANTHROPIC_LOOP_CONFIG,
} from '../../../src/lib/synthesis/agentic_loop'

// Mock the retrieve/index module so executeMCPTool doesn't hit real DB
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
      query_plan_id: 'smoke-plan-g5',
      query_text: '3-iteration loop smoke',
      query_class: 'factual',
      domains: ['natal'],
      forward_looking: false,
      audience_tier: 'super_admin',
      tools_authorized: ['msr_sql', 'query_panchanga', 'lel_query'],
      history_mode: 'synthesized',
      panel_mode: false,
      expected_output_shape: 'single_answer',
      manifest_fingerprint: 'smoke-fingerprint',
      schema_version: '1.0',
    },
  }
}

function makeRequest(): ChatRequest {
  return {
    messages: [{ role: 'user', content: 'What are the key yogas in my chart?' }],
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
// 3-iteration loop smoke test
// ---------------------------------------------------------------------------

describe('tool-executor-loop — 3-iteration loop with real executeMCPTool', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('3 iterations: iter1=msr_sql tool, iter2=lel_query tool, iter3=final answer', async () => {
    // Iter 1: model requests msr_sql with parsed JSON input
    const iter1Events: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tc-iter1', name: 'msr_sql' },
      { type: 'tool_use_input_delta', id: 'tc-iter1', partialJson: '{"signal_type":' },
      { type: 'tool_use_input_delta', id: 'tc-iter1', partialJson: '["yoga"]}' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]
    // Iter 2: model requests lel_query after receiving msr_sql results
    const iter2Events: ChatEvent[] = [
      { type: 'tool_use_start', id: 'tc-iter2', name: 'lel_query' },
      { type: 'tool_use_input_delta', id: 'tc-iter2', partialJson: '{"limit":5}' },
      { type: 'message_stop', stopReason: 'tool_use' },
    ]
    // Iter 3: model produces final answer — end_turn
    const iter3Events: ChatEvent[] = [
      { type: 'text_delta', text: 'Based on the msr_sql yogas and life events, Saturn in 10H is dominant.' },
      { type: 'message_stop', stopReason: 'end_turn' },
    ]

    // Mock getTool to return different tools by name
    const msrSqlTool = {
      name: 'msr_sql',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({
        results: [
          { content: 'Saturn-Rahu yoga (MSR.042): financial pressure during Saturn periods', significance: 0.9, source_canonical_id: 'MSR.042', confidence: 0.85, result_hash: 'sha256:abc', schema_version: '1.0' },
          { content: 'Neech Bhang Raj yoga (MSR.105): reversal of debilitation', significance: 0.85, source_canonical_id: 'MSR.105', confidence: 0.82, result_hash: 'sha256:def', schema_version: '1.0' },
        ],
      }),
    }
    const lelQueryTool = {
      name: 'lel_query',
      version: '1.0',
      retrieve: vi.fn().mockResolvedValue({
        results: [
          { content: 'LE.001: Born 1984-02-05, Bhubaneswar', significance: 1.0, source_canonical_id: 'LEL.001', confidence: 1.0, result_hash: 'sha256:ghi', schema_version: '1.0' },
        ],
      }),
    }

    vi.mocked(getTool).mockImplementation((name: string) => {
      if (name === 'msr_sql') return msrSqlTool as any
      if (name === 'lel_query') return lelQueryTool as any
      return undefined
    })

    // Capture chat() call args to verify message propagation
    const chatCallArgs: ChatRequest[] = []
    const adapter: CapabilityAdapter = {
      providerId: 'anthropic',
      getManifest: vi.fn(),
      chat: async function* (req: ChatRequest): AsyncIterable<ChatEvent> {
        chatCallArgs.push(req)
        const callIndex = chatCallArgs.length
        if (callIndex === 1) {
          for (const event of iter1Events) yield event
        } else if (callIndex === 2) {
          for (const event of iter2Events) yield event
        } else {
          for (const event of iter3Events) yield event
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

    const ctx = makeCtx()
    const collected = await collectEvents(
      runAgenticLoop(
        adapter,
        makeRequest(),
        (toolCall) => executeMCPTool(toolCall, ctx),
        ANTHROPIC_LOOP_CONFIG,
      ),
    )

    // --- Assertion 1: Loop completes with final answer text after end_turn ---
    const textDeltas = collected.filter(e => e.type === 'text_delta')
    expect(textDeltas).toHaveLength(1)
    const finalText = (textDeltas[0] as { type: 'text_delta'; text: string }).text
    expect(finalText).toContain('Saturn in 10H')

    const stopEvents = collected.filter(e => e.type === 'message_stop')
    const lastStop = stopEvents[stopEvents.length - 1] as { type: 'message_stop'; stopReason: string }
    expect(lastStop.stopReason).toBe('end_turn')

    // --- Assertion 2: Tool input JSON is correctly parsed before dispatch ---
    // msr_sql received signal_type: ['yoga'] (assembled from two partialJson chunks)
    expect(msrSqlTool.retrieve).toHaveBeenCalledTimes(1)
    expect(msrSqlTool.retrieve).toHaveBeenCalledWith(
      ctx.queryPlan,
      { signal_type: ['yoga'] },
    )
    // lel_query received limit: 5
    expect(lelQueryTool.retrieve).toHaveBeenCalledTimes(1)
    expect(lelQueryTool.retrieve).toHaveBeenCalledWith(
      ctx.queryPlan,
      { limit: 5 },
    )

    // --- Assertion 3: Each iteration's tool result flows back into next iteration's messages ---
    // 3 chat() calls (3 iterations)
    expect(chatCallArgs).toHaveLength(3)

    // After iter1 (msr_sql): messages = [user, assistant(tool_use), user(tool_result)]
    const iter2Messages = chatCallArgs[1].messages
    expect(iter2Messages).toHaveLength(3)
    const iter2AssistantTurn = iter2Messages[1]
    expect(iter2AssistantTurn.role).toBe('assistant')
    const iter2AssistantContent = iter2AssistantTurn.content as Array<{ type: string; id: string; name: string }>
    expect(iter2AssistantContent[0].type).toBe('tool_use')
    expect(iter2AssistantContent[0].name).toBe('msr_sql')

    const iter2UserTurn = iter2Messages[2]
    expect(iter2UserTurn.role).toBe('user')
    const iter2UserContent = iter2UserTurn.content as Array<{ type: string; toolUseId: string; content: string }>
    expect(iter2UserContent[0].type).toBe('tool_result')
    // msr_sql result JSON flows back
    const msrResult = JSON.parse(iter2UserContent[0].content)
    expect(msrResult.tool).toBe('msr_sql')
    expect(msrResult.results).toHaveLength(2)
    expect(msrResult.result_count).toBe(2)

    // After iter2 (lel_query): messages = [user, asst(msr_sql), user(msr_result), asst(lel_query), user(lel_result)]
    const iter3Messages = chatCallArgs[2].messages
    expect(iter3Messages).toHaveLength(5)
    const iter3LastUserTurn = iter3Messages[4]
    expect(iter3LastUserTurn.role).toBe('user')
    const iter3LastContent = iter3LastUserTurn.content as Array<{ type: string; content: string }>
    expect(iter3LastContent[0].type).toBe('tool_result')
    const lelResult = JSON.parse(iter3LastContent[0].content)
    expect(lelResult.tool).toBe('lel_query')
    expect(lelResult.results).toHaveLength(1)
  })
})
