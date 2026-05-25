/**
 * query_signal_state.test.ts — Unit tests for the query_signal_state MCP tool wrapper.
 *
 * Verifies:
 *   - Tool registers without throwing
 *   - Handler returns {content: [{type: 'text'}]} on success
 *   - Handler returns isError: true when primitive returns status >= 400
 *   - date param is mapped to query_date in forwarded params
 *   - end_date param is forwarded correctly
 *   - state_filter is mapped to states[] array in forwarded params
 *   - chart_id is forwarded as UUID
 *   - limit param defaults to 50 when omitted
 *   - Response content is parseable JSON with ok: true
 *   - isError: true when envelope.ok is false (even with status 200)
 *   - Tool name forwarded to callPlatformPrimitive is exactly 'query_signal_state'
 *   - principal is forwarded to callPlatformPrimitive
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive before importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQuerySignalState } from './query_signal_state.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildSuccessEnvelope(results: unknown[] = []) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-signal-state-001',
      audience_tier: 'super_admin' as const,
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'signal-state-bundle-id',
        tool_name: 'query_signal_state',
        tool_version: '1.0.0',
        invocation_params: {},
        results: results.map(r => ({
          content: JSON.stringify(r),
          source_canonical_id: 'SIGNAL_STATES',
          source_version: '1.0',
          confidence: 0.85,
        })),
        served_from_cache: false,
        latency_ms: 8,
        result_hash: 'sha256:signal-state-test',
        schema_version: '1.0',
      },
      citations: [],
      plan: null,
      predictions_logged: [],
      synthesis_audit: null,
      suggested_followups: [],
      warnings: [],
    },
  }
}

function buildErrorEnvelope() {
  return {
    status: 500,
    envelope: {
      ok: false,
      trace_id: 'trace-signal-state-err',
      error: { class: 'internal', message: 'signal_states query failed' },
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callQuerySignalState(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null
  let capturedSchema: Record<string, unknown> | null = null

  const stubServer = {
    tool: (
      _name: string,
      _description: unknown,
      schema: Record<string, unknown>,
      handler: (input: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedHandler = handler
      capturedSchema = schema
    },
  } as unknown as McpServer

  registerQuerySignalState(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_signal_state handler was not registered')

  // Simulate Zod validation as the MCP SDK would perform
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)

  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// Helper: parse text content from MCP result
function parseResultContent(result: unknown): unknown {
  const r = result as { content?: Array<{ type: string; text: string }>; isError?: boolean }
  if (!r.content?.[0]?.text) return null
  return JSON.parse(r.content[0].text)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_signal_state — MCP tool wrapper', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1: tool registers without throwing
  it('AC.1 — registers without throwing', () => {
    const stubServer = {
      tool: vi.fn(),
    } as unknown as McpServer

    expect(() => registerQuerySignalState(stubServer, () => mockPrincipal)).not.toThrow()
    expect((stubServer.tool as ReturnType<typeof vi.fn>)).toHaveBeenCalledOnce()
    const [toolName] = (stubServer.tool as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(toolName).toBe('query_signal_state')
  })

  // AC.2: success path returns {content: [{type: 'text'}]}
  it('AC.2 — success path returns content with type text', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([
      { signal_id: 'SIG.MSR.001', query_date: '2026-05-25', state: 'lit', confidence: 0.9 },
    ]))

    const result = await callQuerySignalState({})

    const r = result as { content?: Array<{ type: string; text: string }> }
    expect(r.content).toBeDefined()
    expect(r.content![0].type).toBe('text')
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // AC.3: error path returns isError: true when status >= 400
  it('AC.3 — returns isError: true when primitive returns status >= 400', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callQuerySignalState({})

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.4: date param is mapped to query_date in forwarded params
  it('AC.4 — date param is mapped to query_date for API compatibility', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQuerySignalState({ date: '2026-05-25' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['query_date']).toBe('2026-05-25')
    expect('date' in params).toBe(false)
  })

  // AC.5: end_date is forwarded correctly
  it('AC.5 — end_date is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQuerySignalState({ date: '2026-05-01', end_date: '2026-05-31' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['query_date']).toBe('2026-05-01')
    expect(params['end_date']).toBe('2026-05-31')
  })

  // AC.6: state_filter 'lit' maps to states: ['lit']
  it('AC.6 — state_filter is mapped to states array', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQuerySignalState({ state_filter: 'lit' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['states']).toEqual(['lit'])
    expect('state_filter' in params).toBe(false)
  })

  // AC.7: state_filter 'ripening' maps to states: ['ripening']
  it('AC.7 — state_filter ripening maps to states array', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQuerySignalState({ state_filter: 'ripening' })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['states']).toEqual(['ripening'])
  })

  // AC.8: chart_id is forwarded as UUID
  it('AC.8 — chart_id UUID is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    // Must be a valid v4 UUID (Zod uuid() validates version/variant bits)
    const chartId = '550e8400-e29b-41d4-a716-446655440000'
    await callQuerySignalState({ chart_id: chartId })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['chart_id']).toBe(chartId)
  })

  // AC.9: invalid UUID is rejected by Zod schema
  it('AC.9 — invalid chart_id UUID is rejected by Zod schema', async () => {
    const result = await callQuerySignalState({ chart_id: 'not-a-uuid' })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.10: limit defaults to 50 when omitted
  it('AC.10 — limit defaults to 50 when not provided', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQuerySignalState({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(50)
  })

  it('AC.10b — explicit limit is forwarded correctly', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQuerySignalState({ limit: 100 })

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(100)
  })

  // AC.11: response content is parseable JSON with ok: true
  it('AC.11 — response content is parseable JSON with ok: true', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const result = await callQuerySignalState({})
    const parsed = parseResultContent(result) as { ok?: boolean }
    expect(parsed?.ok).toBe(true)
  })

  // AC.12: isError: true when envelope.ok is false (even with status 200)
  it('AC.12 — isError: true when envelope.ok is false regardless of status', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue({
      status: 200,
      envelope: { ok: false, trace_id: 'trace-x', error: { class: 'zero_rows', message: 'signal_states empty' } },
    })

    const result = await callQuerySignalState({})
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // AC.13: tool name forwarded to callPlatformPrimitive is exactly 'query_signal_state'
  it('AC.13 — callPlatformPrimitive is called with tool name query_signal_state', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQuerySignalState({ date: '2026-05-25' })

    expect(vi.mocked(callPlatformPrimitive).mock.calls[0][0]).toBe('query_signal_state')
  })

  // AC.14: principal is passed through to callPlatformPrimitive
  it('AC.14 — principal is forwarded to callPlatformPrimitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    const customPrincipal: Principal = {
      user_uid: 'acharya-user',
      audience_tier: 'acharya',
      key_id: 'acharya-key',
    }

    await callQuerySignalState({}, customPrincipal)

    const passedPrincipal = vi.mocked(callPlatformPrimitive).mock.calls[0][2] as Principal
    expect(passedPrincipal.user_uid).toBe('acharya-user')
    expect(passedPrincipal.audience_tier).toBe('acharya')
  })

  // AC.15: invalid state_filter value is rejected by Zod schema
  it('AC.15 — invalid state_filter value is rejected by Zod schema', async () => {
    const result = await callQuerySignalState({ state_filter: 'active' })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.16: limit > 200 is rejected by Zod schema
  it('AC.16 — limit > 200 is rejected by Zod schema', async () => {
    const result = await callQuerySignalState({ limit: 201 })
    expect((result as { isZodError?: boolean }).isZodError).toBe(true)
  })

  // AC.17: state_filter omitted means no states key in forwarded params
  it('AC.17 — state_filter omitted means states key absent from forwarded params', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSuccessEnvelope([]))

    await callQuerySignalState({})

    const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
    expect('states' in params).toBe(false)
  })
})
