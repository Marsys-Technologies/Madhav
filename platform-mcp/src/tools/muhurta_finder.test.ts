/**
 * muhurta_finder.test.ts — Unit tests for the muhurta_finder MCP tool.
 *
 * TR-P4-S2 AC: all 3 test files must pass.
 * Mocks callPlatformPrimitive to verify params, error handling, and response shape.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive before importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerMuhurtaFinder } from './muhurta_finder.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildMuhurtaEnvelope(windows: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-muhurta-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'muhurta-bundle-id',
        tool_name: 'query_muhurat',
        tool_version: '1.0.0',
        invocation_params: {},
        results: [{
          content: JSON.stringify({
            ok: true,
            windows,
            count: windows.length,
            event: 'vyapara',
            supported_events: ['vivah', 'griha_pravesh', 'vyapara', 'yatra', 'property_purchase', 'mantra_initiation'],
          }),
          source_canonical_id: 'PANCHANGA_DAILY',
          source_version: '1.0',
          confidence: 1.0,
          significance: 0.85,
        }],
        served_from_cache: false,
        latency_ms: 20,
        result_hash: 'sha256:muhurta-test',
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

const SAMPLE_WINDOWS = [
  {
    event: 'vyapara',
    start_utc: '2026-06-04T00:45:00Z',
    end_utc: '2026-06-04T03:00:00Z',
    star_rating: 5,
    score: 0.89,
    breakdown: { tithi: 0.9, vara: 1.0, nakshatra: 0.85, yoga: 0.9, tara_bala: 0.95 },
  },
]

async function callMuhurtaFinder(
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

  registerMuhurtaFinder(stubServer, () => principal)

  if (!capturedHandler) throw new Error('muhurta_finder handler was not registered')
  return capturedHandler(args)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('muhurta_finder', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('passes activity_type as event param to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      date_from: '2026-06-01',
      date_to: '2026-06-30',
      activity_type: 'vyapara',
    })

    expect(mockCall).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCall.mock.calls[0]
    expect(toolName).toBe('query_muhurat')
    expect((params as Record<string, unknown>)['event']).toBe('vyapara')
  })

  it('passes date_from and date_to to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      date_from: '2026-06-01',
      date_to: '2026-06-20',
      activity_type: 'yatra',
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['date_from']).toBe('2026-06-01')
    expect(params['date_to']).toBe('2026-06-20')
  })

  it('defaults chart_id to NATIVE_CHART_ID when not provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      date_from: '2026-06-01',
      date_to: '2026-06-15',
      activity_type: 'griha_pravesh',
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['chart_id']).toBe(NATIVE_CHART_ID)
  })

  it('passes custom chart_id when provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    const customId = 'custom-chart-uuid-9999'
    await callMuhurtaFinder({
      date_from: '2026-06-01',
      date_to: '2026-06-10',
      activity_type: 'vivah',
      chart_id: customId,
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['chart_id']).toBe(customId)
  })

  it('passes top_n to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      date_from: '2026-06-01',
      date_to: '2026-06-20',
      activity_type: 'vyapara',
      top_n: 5,
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['top_n']).toBe(5)
  })

  it('returns error result when date_from is after date_to', async () => {
    const result = await callMuhurtaFinder({
      date_from: '2026-06-30',
      date_to: '2026-06-01',
      activity_type: 'vyapara',
    })

    expect((result as { isError?: boolean }).isError).toBe(true)
    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(false)
    expect(parsed.error.class).toBe('validation')
  })

  it('returns error result when date range exceeds 30 days', async () => {
    const result = await callMuhurtaFinder({
      date_from: '2026-06-01',
      date_to: '2026-08-01', // 61 days
      activity_type: 'vyapara',
    })

    expect((result as { isError?: boolean }).isError).toBe(true)
    const res = result as { content: Array<{ type: string; text: string }> }
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(false)
    expect(parsed.error.message).toMatch(/30-day/)
  })

  it('returns error result when primitive call fails', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue({
      status: 500,
      envelope: {
        ok: false,
        trace_id: 'fail-001',
        error: { class: 'internal', message: 'Sidecar engine error' },
      },
    })

    const result = await callMuhurtaFinder({
      date_from: '2026-06-01',
      date_to: '2026-06-10',
      activity_type: 'vyapara',
    })

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  it('returns ok result when primitive call succeeds', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    const result = await callMuhurtaFinder({
      date_from: '2026-06-01',
      date_to: '2026-06-30',
      activity_type: 'vyapara',
    })

    expect((result as { isError?: boolean }).isError).toBeUndefined()
    const res = result as { content: Array<{ type: string; text: string }> }
    expect(res.content).toBeDefined()
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
  })
})
