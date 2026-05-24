/**
 * query_panchanga.test.ts — Regression tests for the query_panchanga MCP tool.
 *
 * Tests the C8 bug fix: the MCP wrapper now passes fields=[...all 11 field groups]
 * to callPlatformPrimitive so the 5 enrichment JSONB columns (special_yogas,
 * choghadiya, hora, inauspicious, auspicious) are included in the response.
 *
 * AC.4: query_panchanga passes all 5 enrichment fields to callPlatformPrimitive.
 * AC.5: both test files pass.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive before importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQueryPanchanga } from './query_panchanga.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildPanchangaEnvelope(resultData: unknown) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-panchanga-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'panchanga-bundle-id',
        tool_name: 'query_panchanga',
        tool_version: '1.0.0',
        invocation_params: {},
        results: [{
          content: JSON.stringify(resultData),
          source_canonical_id: 'PANCHANGA_DAILY',
          source_version: '1.0',
          confidence: 1.0,
          significance: 0.85,
        }],
        served_from_cache: false,
        latency_ms: 8,
        result_hash: 'sha256:panchanga-test',
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

async function callQueryPanchanga(
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

  registerQueryPanchanga(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_panchanga handler was not registered')
  return capturedHandler(args)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_panchanga — C8 enrichment columns fix', () => {
  const ENRICHMENT_FIELDS = ['special_yogas', 'choghadiya', 'hora', 'inauspicious', 'auspicious']
  const BASE_FIELDS = ['tithi', 'vara', 'nakshatra', 'yoga', 'karana', 'sunrise']
  const ALL_FIELDS = [...BASE_FIELDS, ...ENRICHMENT_FIELDS]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('AC.4 — fields param includes "choghadiya" in callPlatformPrimitive call', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildPanchangaEnvelope({
      date: '2026-05-24',
      tithi: 12,
      tithi_name: 'Shukla Dwadashi',
      choghadiya: null,
    }))

    await callQueryPanchanga({ date: '2026-05-24' })

    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCallPlatformPrimitive.mock.calls[0]
    expect(toolName).toBe('query_panchanga')
    expect((params as Record<string, unknown>)['fields']).toContain('choghadiya')
  })

  it('AC.4 — all 5 enrichment columns are in the fields param', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildPanchangaEnvelope({ date: '2026-05-24' }))

    await callQueryPanchanga({ date: '2026-05-24' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    const fields = params['fields'] as string[]
    for (const enrichField of ENRICHMENT_FIELDS) {
      expect(fields).toContain(enrichField)
    }
  })

  it('AC.4 — all 6 base columns are also in the fields param', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildPanchangaEnvelope({ date: '2026-05-24' }))

    await callQueryPanchanga({ date: '2026-05-24' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    const fields = params['fields'] as string[]
    for (const baseField of BASE_FIELDS) {
      expect(fields).toContain(baseField)
    }
  })

  it('AC.4 — fields param contains all 11 field groups total', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildPanchangaEnvelope({ date: '2026-05-24' }))

    await callQueryPanchanga({ date: '2026-05-24' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    const fields = params['fields'] as string[]
    expect(fields.length).toBe(ALL_FIELDS.length)
  })

  it('date param is forwarded to callPlatformPrimitive', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildPanchangaEnvelope({ date: '1984-02-05' }))

    await callQueryPanchanga({ date: '1984-02-05' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['date']).toBe('1984-02-05')
  })

  it('observer param is forwarded when provided', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildPanchangaEnvelope({ date: '2026-05-24' }))

    await callQueryPanchanga({
      date: '2026-05-24',
      observer: { lat: 28.6, lon: 77.2 },
    })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['observer']).toEqual({ lat: 28.6, lon: 77.2 })
  })

  it('observer param is absent when not provided', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildPanchangaEnvelope({ date: '2026-05-24' }))

    await callQueryPanchanga({ date: '2026-05-24' })

    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['observer']).toBeUndefined()
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

    const result = await callQueryPanchanga({ date: '2026-05-24' })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  it('returns ok result when primitive call succeeds', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildPanchangaEnvelope({
      date: '2026-05-24',
      tithi_name: 'Shukla Dwadashi',
      choghadiya: [{ window: 'Amrit', start: '06:00', end: '07:30' }],
      hora: [{ planet: 'Sun', start: '06:00', end: '07:00' }],
      inauspicious: { rahu_kalam: { start: '16:30', end: '18:00' } },
      auspicious: { abhijit: { start: '11:48', end: '12:36' } },
      special_yogas: [{ name: 'Amrit Siddhi', active: true }],
    }))

    const result = await callQueryPanchanga({ date: '2026-05-24' })
    expect((result as { isError?: boolean }).isError).toBeUndefined()
    const res = result as { content: Array<{ type: string; text: string }> }
    expect(res.content).toBeDefined()
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
  })
})
