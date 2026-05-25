/**
 * query_signals.test.ts — Regression tests for the query_signals MCP tool.
 *
 * Tests the C4 bug fix: the wrapper now correctly translates forward_looking,
 * min_confidence, valence, temporal_activation, and domains[] into the
 * toolParams passed to callPlatformPrimitive.
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
import { registerQuerySignals } from './query_signals.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildSignalsEnvelope(signals: unknown[]) {
  const toolBundle = {
    tool_bundle_id: 'signals-bundle-id',
    tool_name: 'query_signals',
    tool_version: '1.0.0',
    invocation_params: {},
    results: signals.map(s => ({
      content: JSON.stringify(s),
      source_canonical_id: 'MSR',
      source_version: '3.0',
      confidence: 0.85,
      significance: 0.8,
    })),
    served_from_cache: false,
    latency_ms: 10,
    result_hash: 'sha256:signals-test',
    schema_version: '1.0',
  }

  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-signals-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: toolBundle,
      citations: [],
      plan: null,
      predictions_logged: [],
      synthesis_audit: null,
      suggested_followups: [],
      warnings: [],
    },
  }
}

/**
 * Extract and call the registered handler from the stub server.
 * Simulates Zod validation the MCP SDK would perform.
 */
async function callQuerySignals(
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

  registerQuerySignals(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_signals handler was not registered')

  // Simulate Zod validation as the MCP SDK would perform
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)

  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_signals — C4 filter enforcement fix', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // AC.1 + AC.2: forward_looking=true is forwarded to callPlatformPrimitive
  it('AC.2 — forward_looking=true is included in toolParams passed to primitive', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSignalsEnvelope([
      { signal_id: 'SIG.MSR.234', domain: 'career', claim_text: 'Professional rise in Rahu MD.' },
    ]))

    await callQuerySignals({
      domain: 'career',
      forward_looking: true,
    })

    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCallPlatformPrimitive.mock.calls[0]
    expect(toolName).toBe('query_signals')
    expect((params as Record<string, unknown>)['forward_looking']).toBe(true)
  })

  // AC.1 + AC.2: min_confidence=0.9 is forwarded
  it('AC.2 — min_confidence=0.9 is included in toolParams as both min_confidence and confidence_floor', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSignalsEnvelope([]))

    await callQuerySignals({
      min_confidence: 0.9,
    })

    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['min_confidence']).toBe(0.9)
    // confidence_floor is the alias the primitive reads for explicit floor override
    expect(params['confidence_floor']).toBe(0.9)
  })

  // AC.1 + AC.2: both forward_looking and min_confidence forwarded together
  it('AC.2 — forward_looking=true AND min_confidence=0.9 are both included in toolParams', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSignalsEnvelope([]))

    await callQuerySignals({
      forward_looking: true,
      min_confidence: 0.9,
      domain: 'career',
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['forward_looking']).toBe(true)
    expect(params['min_confidence']).toBe(0.9)
    expect(params['domain']).toBe('career')
  })

  // AC.1: valence is forwarded as an array (primitive expects string[])
  // FIX-3: valence enum uses DB vocabulary: 'benefic'/'malefic'/'context-dependent'
  it('AC.1 — valence="benefic" is forwarded to toolParams as ["benefic"]', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSignalsEnvelope([]))

    await callQuerySignals({ valence: 'benefic' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['valence']).toEqual(['benefic'])
  })

  it('AC.1 — valence="malefic" is forwarded to toolParams as ["malefic"]', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSignalsEnvelope([]))

    await callQuerySignals({ valence: 'malefic' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['valence']).toEqual(['malefic'])
  })

  it('AC.1 — valence="context-dependent" is forwarded to toolParams as ["context-dependent"]', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSignalsEnvelope([]))

    await callQuerySignals({ valence: 'context-dependent' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['valence']).toEqual(['context-dependent'])
  })

  it('Zod rejects old valence vocabulary ("positive") — schema now uses DB vocabulary', async () => {
    const result = await callQuerySignals({ valence: 'positive' })
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  it('Zod rejects invalid valence value', async () => {
    const result = await callQuerySignals({ valence: 'lucky' })
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  // AC.1: temporal_activation is forwarded as an array
  it('AC.1 — temporal_activation="dasha_tied" is forwarded to toolParams as ["dasha_tied"]', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSignalsEnvelope([]))

    await callQuerySignals({ temporal_activation: 'dasha_tied' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['temporal_activation']).toEqual(['dasha_tied'])
  })

  it('Zod rejects invalid temporal_activation value', async () => {
    const result = await callQuerySignals({ temporal_activation: 'random' })
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  // AC.1: domains[] is forwarded
  it('AC.1 — domains=["career","health"] is forwarded to toolParams', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSignalsEnvelope([]))

    await callQuerySignals({ domains: ['career', 'health'] })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['domains']).toEqual(['career', 'health'])
  })

  // Default chart_id fallback: when no chart_id provided, the primitive is still called
  // (chart_id is not in query_signals schema — it uses native_id in the primitive)
  it('default chart_id: callPlatformPrimitive is called even without chart_id', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSignalsEnvelope([]))

    await callQuerySignals({ domain: 'spiritual' })

    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName] = mockCallPlatformPrimitive.mock.calls[0]
    expect(toolName).toBe('query_signals')
  })

  // limit has a default of 50
  it('limit defaults to 50 when not provided', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildSignalsEnvelope([]))

    await callQuerySignals({ domain: 'career' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['limit']).toBe(50)
  })

  it('returns error result when primitive call fails', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue({
      status: 500,
      envelope: {
        ok: false,
        trace_id: 'fail-001',
        error: { class: 'internal', message: 'DB error' },
      },
    })

    const result = await callQuerySignals({ domain: 'career', forward_looking: true })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })
})
