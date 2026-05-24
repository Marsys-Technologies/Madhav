/**
 * query_divisional_chart.test.ts — Unit tests for the query_divisional_chart MCP tool.
 *
 * TR-P4-S1 AC.4: all 3 test files must pass.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive before importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQueryDivisionalChart } from './query_divisional_chart.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildDivisionalEnvelope(rows: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-divisional-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'divisional-bundle-id',
        tool_name: 'divisional_query',
        tool_version: '1.0',
        invocation_params: {},
        results: rows.map(row => ({
          content: JSON.stringify(row),
          source_canonical_id: 'FORENSIC',
          source_version: '8.0',
          confidence: 1.0,
          significance: 0.85,
        })),
        served_from_cache: false,
        latency_ms: 10,
        result_hash: 'sha256:divisional-test',
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

async function callQueryDivisionalChart(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null

  const stubServer = {
    tool: (
      _name: string,
      _description: unknown,
      _schema: unknown,
      handler: (input: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedHandler = handler
    },
  } as unknown as McpServer

  registerQueryDivisionalChart(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_divisional_chart handler was not registered')
  return capturedHandler(args)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_divisional_chart', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns non-empty response for D9 division', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildDivisionalEnvelope([
      { fact_id: 'D9_Sun_1', category: 'planet', varga: 'D9', value_text: 'Sun in Aries', placement: { planet: 'Sun', sign: 'Aries', house: 1 } },
      { fact_id: 'D9_Moon_7', category: 'planet', varga: 'D9', value_text: 'Moon in Libra', placement: { planet: 'Moon', sign: 'Libra', house: 7 } },
    ]))

    const result = await callQueryDivisionalChart({ division: 'D9' })

    expect(result).toBeDefined()
    const res = result as { content: Array<{ type: string; text: string }> }
    expect(res.content).toBeDefined()
    expect(res.content.length).toBeGreaterThan(0)
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
  })

  it('passes varga param as the division value to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildDivisionalEnvelope([]))

    await callQueryDivisionalChart({ division: 'D9' })

    expect(mockCall).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCall.mock.calls[0]
    expect(toolName).toBe('divisional_query')
    expect((params as Record<string, unknown>)['varga']).toBe('D9')
  })

  it('defaults chart_id to NATIVE_CHART_ID when not provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildDivisionalEnvelope([]))

    await callQueryDivisionalChart({ division: 'D10' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['chart_id']).toBe(NATIVE_CHART_ID)
  })

  it('passes planet filter when provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildDivisionalEnvelope([]))

    await callQueryDivisionalChart({ division: 'D9', planet: 'Saturn' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['planet']).toBe('Saturn')
  })

  it('passes house filter when provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildDivisionalEnvelope([]))

    await callQueryDivisionalChart({ division: 'D9', house: 7 })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['house']).toBe(7)
  })

  it('omits planet and house from params when not provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildDivisionalEnvelope([]))

    await callQueryDivisionalChart({ division: 'D60' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['planet']).toBeUndefined()
    expect(params['house']).toBeUndefined()
  })

  it('returns error result when primitive call fails', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue({
      status: 500,
      envelope: {
        ok: false,
        trace_id: 'fail-002',
        error: { class: 'internal', message: 'DB error' },
      },
    })

    const result = await callQueryDivisionalChart({ division: 'D9' })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  it('handles D1 (Rasi) division correctly', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildDivisionalEnvelope([
      { fact_id: 'D1_Mars_8', category: 'planet', varga: 'D1', value_text: 'Mars in 8th', placement: { planet: 'Mars', house: 8 } },
    ]))

    await callQueryDivisionalChart({ division: 'D1' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['varga']).toBe('D1')
  })

  it('handles D60 (Shashtiamsha) division correctly', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildDivisionalEnvelope([]))

    await callQueryDivisionalChart({ division: 'D60' })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['varga']).toBe('D60')
  })
})
