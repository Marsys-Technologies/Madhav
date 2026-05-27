/**
 * query_varshphal.test.ts — Unit tests for the query_varshphal MCP tool.
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
import { registerQueryVarshphal } from './query_varshphal.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

// C2a fix: DB key used by varshaphala table (not Firebase UUID)
const NATIVE_CHART_ID = 'abhisek_mohanty_primary'

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

const mockClientPrincipal: Principal = {
  user_uid: 'test-client',
  audience_tier: 'client',
  key_id: 'test-client-key',
}

function buildVarshphalEnvelope(resultData: unknown) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-varshphal-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'varshphal-bundle-id',
        tool_name: 'query_varshaphala',
        tool_version: '1.0',
        invocation_params: {},
        results: [{
          content: JSON.stringify(resultData),
          source_canonical_id: 'VARSHAPHALA_RAW',
          source_version: '1.0',
          confidence: 0.9,
          significance: 0.75,
        }],
        served_from_cache: false,
        latency_ms: 12,
        result_hash: 'sha256:varshphal-test',
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

async function callQueryVarshphal(
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

  registerQueryVarshphal(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_varshphal handler was not registered')
  return capturedHandler(args)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_varshphal — C2a: NATIVE_CHART_ID fix', () => {
  it('C2a — NATIVE_CHART_ID is the DB key string, not a Firebase UUID', () => {
    expect(NATIVE_CHART_ID).toBe('abhisek_mohanty_primary')
    // Must NOT be a UUID (Firebase UID format)
    expect(NATIVE_CHART_ID).not.toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/)
  })
})

describe('query_varshphal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a non-empty response object for year 2026', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildVarshphalEnvelope({
      year: 2026,
      solar_return_utc: '2026-02-05T05:23:00Z',
      ascendant: { sidereal_lon: 123.4, sign: 'Leo' },
      planets: { Sun: { sidereal_lon: 292.1, sign: 'Capricorn', nakshatra: 'Sravana' } },
      ayanamsha: 'lahiri',
      computed_by: 'pyswisseph',
    }))

    const result = await callQueryVarshphal({ year: 2026 })

    expect(result).toBeDefined()
    const res = result as { content: Array<{ type: string; text: string }> }
    expect(res.content).toBeDefined()
    expect(res.content.length).toBeGreaterThan(0)
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
  })

  it('passes year param to callPlatformPrimitive', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildVarshphalEnvelope({ year: 2026 }))

    await callQueryVarshphal({ year: 2026 })

    expect(mockCall).toHaveBeenCalledTimes(1)
    const [toolName, params] = mockCall.mock.calls[0]
    expect(toolName).toBe('query_varshaphala')
    expect((params as Record<string, unknown>)['year']).toBe(2026)
  })

  it('defaults chart_id to NATIVE_CHART_ID when not provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildVarshphalEnvelope({ year: 2026 }))

    await callQueryVarshphal({ year: 2026 })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['chart_id']).toBe(NATIVE_CHART_ID)
  })

  it('passes custom chart_id when provided', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildVarshphalEnvelope({ year: 2025 }))

    const customChartId = 'custom-chart-uuid-1234'
    await callQueryVarshphal({ year: 2025, chart_id: customChartId })

    const params = mockCall.mock.calls[0][1] as Record<string, unknown>
    expect(params['chart_id']).toBe(customChartId)
  })

  it('returns error result when primitive call fails', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue({
      status: 500,
      envelope: {
        ok: false,
        trace_id: 'fail-001',
        error: { class: 'internal', message: 'DB error' },
      },
    })

    const result = await callQueryVarshphal({ year: 2026 })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  it('client-tier callers reach engine (no tier gate)', async () => {
    // Tier excised (Stream A 3.tier_excision 2026-05-28); query_varshphal
    // no longer 403s a "client"-tier principal — every key sees engine output.
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildVarshphalEnvelope({ year: 2026 }))
    const result = await callQueryVarshphal({ year: 2026 }, mockClientPrincipal)
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  it('succeeds for acharya tier', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildVarshphalEnvelope({ year: 2026 }))

    const acharyaPrincipal: Principal = {
      user_uid: 'acharya-user',
      audience_tier: 'acharya',
      key_id: 'acharya-key',
    }

    const result = await callQueryVarshphal({ year: 2026 }, acharyaPrincipal)
    expect((result as { isError?: boolean }).isError).toBeUndefined()
  })

  // ── Range-mode tests ──────────────────────────────────────────────────────────

  it('range-mode success: returns mode=range and charts array', async () => {
    // audience_tier removed from envelope (Stream A 3.tier_excision 2026-05-28).
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildVarshphalEnvelope({ year: 2025 }))

    const result = await callQueryVarshphal({ year_start: 2025, year_end: 2026 })

    expect(result).toBeDefined()
    const res = result as { content: Array<{ type: string; text: string }> }
    expect(res.content).toBeDefined()
    const parsed = JSON.parse(res.content[0].text)
    expect(parsed.ok).toBe(true)
    expect(parsed.result.mode).toBe('range')
    expect(Array.isArray(parsed.result.charts)).toBe(true)
    expect(parsed.result.charts.length).toBe(2)
    expect(parsed.audience_tier).toBeUndefined()
  })

  it('range-mode 20-year cap: caps at 20 calls for year_start=2000, year_end=2030', async () => {
    const mockCall = vi.mocked(callPlatformPrimitive)
    mockCall.mockResolvedValue(buildVarshphalEnvelope({ year: 2000 }))

    await callQueryVarshphal({ year_start: 2000, year_end: 2030 })

    // 2030 - 2000 = 30 years requested, but cap is 20 (start + 19)
    expect(mockCall).toHaveBeenCalledTimes(20)
  })
})
