/**
 * muhurta_finder.test.ts — Unit tests for the muhurta_finder MCP tool.
 *
 * C4a tests: enum restriction, alias resolution (travel → yatra), error handling.
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
import { registerMuhurtaFinder, SIDECAR_EVENTS, EVENT_ALIAS } from './muhurta_finder.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

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
        tool_name: 'muhurta_finder',
        tool_version: '1.0.0',
        invocation_params: {},
        results: [{
          content: JSON.stringify({
            ok: true,
            windows,
            count: windows.length,
            event: 'vyapara',
            supported_events: Array.from(SIDECAR_EVENTS),
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

  // C4a: canonical sidecar event values pass through unchanged
  it('passes canonical event value (vyapara) directly to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      event: 'vyapara',
      date_from: '2026-06-01',
      date_to: '2026-06-30',
    })

    expect(mockCall).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCall.mock.calls[0]
    expect(toolName).toBe('muhurta_finder')
    expect((params as Record<string, unknown>)['event']).toBe('vyapara')
  })

  // C4a: alias resolution — travel → yatra
  it('resolves alias travel → yatra before dispatch', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      event: 'travel',
      date_from: '2026-06-01',
      date_to: '2026-06-30',
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['event']).toBe('yatra')
  })

  // C4a: alias resolution — marriage → vivah
  it('resolves alias marriage → vivah before dispatch', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      event: 'marriage',
      date_from: '2026-06-01',
      date_to: '2026-06-30',
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['event']).toBe('vivah')
  })

  // C4a: alias resolution — business_start → vyapara
  it('resolves alias business_start → vyapara before dispatch', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      event: 'business_start',
      date_from: '2026-06-01',
      date_to: '2026-06-30',
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['event']).toBe('vyapara')
  })

  // C4a: alias resolution — vehicle_purchase → property_purchase
  it('resolves alias vehicle_purchase → property_purchase before dispatch', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      event: 'vehicle_purchase',
      date_from: '2026-06-01',
      date_to: '2026-06-30',
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['event']).toBe('property_purchase')
  })

  it('passes date_from and date_to to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      event: 'yatra',
      date_from: '2026-06-01',
      date_to: '2026-06-20',
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['date_from']).toBe('2026-06-01')
    expect(params['date_to']).toBe('2026-06-20')
  })

  it('passes top_n to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    await callMuhurtaFinder({
      event: 'vyapara',
      date_from: '2026-06-01',
      date_to: '2026-06-20',
      top_n: 5,
    })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['top_n']).toBe(5)
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
      event: 'vyapara',
      date_from: '2026-06-01',
      date_to: '2026-06-10',
    })

    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  it('returns ok result when primitive call succeeds', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildMuhurtaEnvelope(SAMPLE_WINDOWS))

    const result = await callMuhurtaFinder({
      event: 'vyapara',
      date_from: '2026-06-01',
      date_to: '2026-06-30',
    })

    expect((result as { isError?: boolean }).isError).toBeUndefined()
    const res = result as { content: Array<{ type: string; text: string }> }
    expect(res.content).toBeDefined()
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
  })

  // C4a: SIDECAR_EVENTS and EVENT_ALIAS exports are correct
  it('SIDECAR_EVENTS contains 6 canonical values', () => {
    expect(SIDECAR_EVENTS).toContain('vivah')
    expect(SIDECAR_EVENTS).toContain('griha_pravesh')
    expect(SIDECAR_EVENTS).toContain('vyapara')
    expect(SIDECAR_EVENTS).toContain('yatra')
    expect(SIDECAR_EVENTS).toContain('property_purchase')
    expect(SIDECAR_EVENTS).toContain('mantra_initiation')
    expect(SIDECAR_EVENTS.length).toBe(6)
  })

  it('EVENT_ALIAS maps travel → yatra', () => {
    expect(EVENT_ALIAS['travel']).toBe('yatra')
  })

  it('EVENT_ALIAS maps marriage → vivah', () => {
    expect(EVENT_ALIAS['marriage']).toBe('vivah')
  })

  it('EVENT_ALIAS maps house_entry → griha_pravesh', () => {
    expect(EVENT_ALIAS['house_entry']).toBe('griha_pravesh')
  })

  it('EVENT_ALIAS maps business_start → vyapara', () => {
    expect(EVENT_ALIAS['business_start']).toBe('vyapara')
  })

  it('EVENT_ALIAS maps vehicle_purchase → property_purchase', () => {
    expect(EVENT_ALIAS['vehicle_purchase']).toBe('property_purchase')
  })
})
