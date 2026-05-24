/**
 * query_jaimini_chara_dasha.test.ts — Unit tests for the query_jaimini_chara_dasha MCP tool.
 *
 * Session: TR-P7-S2
 *
 * Acceptance criteria:
 *   T1 — query_jaimini_chara_dasha({date: "2026-06-01"}) returns active_rashi_dasha.rashi (non-empty string)
 *   T2 — query_jaimini_chara_dasha({include_sub_periods: true}) returns full_periods with length 12
 *   T3 — each period in full_periods has rashi, start_date, end_date
 *   T4 — total duration of full_periods ≈ 120 years (43800 days ± 365 days tolerance)
 *   T5 — sidecar error → errorResult with ok: false
 *   T6 — Zod schema accepts optional date and include_sub_periods
 *   T7 — full mode also returns active_rashi_dasha and active_antar_dasha
 *   T8 — empty active_rashi_dasha from sidecar → error response
 *
 * NOTE: callPlatformPrimitive is vi.mocked — tests pass without sidecar connectivity.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock callPlatformPrimitive BEFORE importing the tool ──────────────────────

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerQueryJaiminiCharaDasha } from './query_jaimini_chara_dasha.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Build a sidecar active-dasha response envelope.
 * Wraps in a ToolBundle-style structure as returned by callPlatformPrimitive.
 */
function buildActiveDashaEnvelope(activeDasha: {
  rashi: string
  sign_lord: string
  start_date: string
  end_date: string
}, antarDasha?: {
  rashi: string
  sign_lord: string
  start_date: string
  end_date: string
} | null, queryDate?: string) {
  const inner = {
    ok: true,
    query_date: queryDate ?? '2026-06-01',
    birth_date: '1984-02-05',
    active_rashi_dasha: activeDasha,
    active_antar_dasha: antarDasha ?? null,
    algorithm: 'jaimini_chara_dasha',
    source: 'native_fallback_longitudes',
  }

  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-jcd-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true },
      result: {
        tool_bundle_id: 'jcd-bundle-id',
        tool_name: 'jaimini_chara_dasha',
        results: [
          {
            content: JSON.stringify(inner),
            source_canonical_id: 'FORENSIC',
            confidence: 1.0,
          },
        ],
        served_from_cache: false,
        latency_ms: 5,
      },
      citations: [],
      plan: null,
      predictions_logged: [],
    },
  }
}

/**
 * Build a sidecar full-periods response envelope.
 * The periods array has exactly 12 entries — one per rashi.
 */
function buildFullPeriodsEnvelope(periods: Array<{
  rashi: string
  sign_lord: string
  years: number
  start_date: string
  end_date: string
}>) {
  const inner = {
    ok: true,
    birth_date: '1984-02-05',
    total_years: periods.reduce((sum, p) => sum + p.years, 0),
    period_count: periods.length,
    periods,
    algorithm: 'jaimini_chara_dasha',
    source: 'native_fallback_longitudes',
  }

  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-jcdf-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true },
      result: {
        tool_bundle_id: 'jcdf-bundle-id',
        tool_name: 'jaimini_chara_dasha_full',
        results: [
          {
            content: JSON.stringify(inner),
            source_canonical_id: 'FORENSIC',
            confidence: 1.0,
          },
        ],
        served_from_cache: false,
        latency_ms: 8,
      },
      citations: [],
      plan: null,
      predictions_logged: [],
    },
  }
}

/** Build a 404/500 error envelope. */
function buildErrorEnvelope(statusCode = 503, message = 'Sidecar unavailable') {
  return {
    status: statusCode,
    envelope: {
      ok: false,
      trace_id: 'trace-err-001',
      error: { class: 'internal', message, remediation: 'retry' },
    },
  }
}

/**
 * Register the tool on a stub server and invoke with Zod validation.
 * Pattern mirrors other tool tests in this codebase.
 */
async function callQueryJaiminiCharaDasha(
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

  registerQueryJaiminiCharaDasha(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_jaimini_chara_dasha handler was not registered')

  // Simulate Zod validation as the MCP SDK would
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

/** Parse the MCP content text from an okResult / errorResult. */
function parseContent(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Sample data ───────────────────────────────────────────────────────────────

const SAMPLE_ACTIVE_RASHI = {
  rashi: 'Scorpio',
  sign_lord: 'Mars',
  start_date: '2022-05-15',
  end_date: '2031-05-14',
}

const SAMPLE_ACTIVE_ANTAR = {
  rashi: 'Capricorn',
  sign_lord: 'Saturn',
  start_date: '2025-01-01',
  end_date: '2026-12-31',
}

// 12 rashis in forward zodiac order starting from Taurus (native Lagna)
// Each with a non-trivial year count summing to 120.
const SAMPLE_FULL_PERIODS = (() => {
  const rashis = [
    { rashi: 'Taurus',      sign_lord: 'Venus',   years: 8 },
    { rashi: 'Gemini',      sign_lord: 'Mercury', years: 10 },
    { rashi: 'Cancer',      sign_lord: 'Moon',    years: 6 },
    { rashi: 'Leo',         sign_lord: 'Sun',     years: 12 },
    { rashi: 'Virgo',       sign_lord: 'Mercury', years: 11 },
    { rashi: 'Libra',       sign_lord: 'Venus',   years: 9 },
    { rashi: 'Scorpio',     sign_lord: 'Mars',    years: 9 },
    { rashi: 'Sagittarius', sign_lord: 'Jupiter', years: 11 },
    { rashi: 'Capricorn',   sign_lord: 'Saturn',  years: 12 },
    { rashi: 'Aquarius',    sign_lord: 'Saturn',  years: 12 },
    { rashi: 'Pisces',      sign_lord: 'Jupiter', years: 11 },
    { rashi: 'Aries',       sign_lord: 'Mars',    years: 9 },
  ]

  // Build start/end dates from 1984-02-05 (native birth date)
  let current = new Date('1984-02-05')
  return rashis.map(r => {
    const startDate = current.toISOString().split('T')[0]
    const days = Math.round(r.years * 365.25)
    const end = new Date(current)
    end.setDate(end.getDate() + days - 1)
    const endDate = end.toISOString().split('T')[0]
    current = new Date(end)
    current.setDate(current.getDate() + 1)
    return {
      rashi: r.rashi,
      sign_lord: r.sign_lord,
      years: r.years,
      start_date: startDate,
      end_date: endDate,
    }
  })
})()

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_jaimini_chara_dasha (TR-P7-S2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── T1: active dasha for a specific date ────────────────────────────────────

  it('T1 — returns active_rashi_dasha.rashi as a non-empty string for date=2026-06-01', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildActiveDashaEnvelope(SAMPLE_ACTIVE_RASHI, SAMPLE_ACTIVE_ANTAR, '2026-06-01'))

    const result = await callQueryJaiminiCharaDasha({ date: '2026-06-01' })

    expect((result as { isError?: boolean }).isError).toBeFalsy()
    const parsed = parseContent(result)

    expect(parsed['ok']).toBe(true)

    const activeDasha = parsed['active_rashi_dasha'] as { rashi?: string }
    expect(typeof activeDasha?.rashi).toBe('string')
    expect(activeDasha.rashi.length).toBeGreaterThan(0)
  })

  // ── T2: full_periods has length 12 ──────────────────────────────────────────

  it('T2 — include_sub_periods=true returns full_periods array with exactly 12 entries', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    // First call: full periods
    mock.mockResolvedValueOnce(buildFullPeriodsEnvelope(SAMPLE_FULL_PERIODS))
    // Second call: active dasha (for query_date within full result)
    mock.mockResolvedValueOnce(buildActiveDashaEnvelope(SAMPLE_ACTIVE_RASHI, SAMPLE_ACTIVE_ANTAR))

    const result = await callQueryJaiminiCharaDasha({ include_sub_periods: true })

    expect((result as { isError?: boolean }).isError).toBeFalsy()
    const parsed = parseContent(result)

    expect(parsed['ok']).toBe(true)

    const fullPeriods = parsed['full_periods'] as unknown[]
    expect(Array.isArray(fullPeriods)).toBe(true)
    expect(fullPeriods.length).toBe(12)
  })

  // ── T3: each period has rashi, start_date, end_date ─────────────────────────

  it('T3 — each period in full_periods has rashi, start_date, end_date', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildFullPeriodsEnvelope(SAMPLE_FULL_PERIODS))
    mock.mockResolvedValueOnce(buildActiveDashaEnvelope(SAMPLE_ACTIVE_RASHI, null))

    const result = await callQueryJaiminiCharaDasha({ include_sub_periods: true })
    const parsed = parseContent(result)

    const fullPeriods = parsed['full_periods'] as Array<Record<string, unknown>>
    expect(fullPeriods.length).toBe(12)

    for (const period of fullPeriods) {
      expect(typeof period['rashi']).toBe('string')
      expect((period['rashi'] as string).length).toBeGreaterThan(0)

      expect(typeof period['start_date']).toBe('string')
      expect((period['start_date'] as string)).toMatch(/^\d{4}-\d{2}-\d{2}$/)

      expect(typeof period['end_date']).toBe('string')
      expect((period['end_date'] as string)).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    }
  })

  // ── T4: total duration ≈ 120 years (43800 ± 365 days) ──────────────────────

  it('T4 — total duration of full_periods is approximately 120 years (43800 ± 365 days)', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildFullPeriodsEnvelope(SAMPLE_FULL_PERIODS))
    mock.mockResolvedValueOnce(buildActiveDashaEnvelope(SAMPLE_ACTIVE_RASHI, null))

    const result = await callQueryJaiminiCharaDasha({ include_sub_periods: true })
    const parsed = parseContent(result)

    const fullPeriods = parsed['full_periods'] as Array<Record<string, string>>
    expect(fullPeriods.length).toBe(12)

    // Compute total days
    let totalDays = 0
    for (const period of fullPeriods) {
      const start = new Date(period['start_date']).getTime()
      const end = new Date(period['end_date']).getTime()
      totalDays += Math.round((end - start) / (1000 * 60 * 60 * 24)) + 1
    }

    // 120 years * 365.25 = 43830 days. Allow ± 365 days tolerance.
    const TARGET_DAYS = 43800
    const TOLERANCE = 365
    expect(totalDays).toBeGreaterThan(TARGET_DAYS - TOLERANCE)
    expect(totalDays).toBeLessThan(TARGET_DAYS + TOLERANCE)
  })

  // ── T5: sidecar error → errorResult ─────────────────────────────────────────

  it('T5 — sidecar HTTP error returns errorResult with ok: false', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildErrorEnvelope(503, 'Sidecar unavailable'))

    const result = await callQueryJaiminiCharaDasha({ date: '2026-06-01' })

    expect((result as { isError: boolean }).isError).toBe(true)
    const parsed = parseContent(result)
    expect(parsed['ok']).toBe(false)
    expect(parsed['error']).toBe('sidecar_error')
  })

  // ── T6: Zod accepts optional fields ─────────────────────────────────────────

  it('T6 — Zod schema accepts empty args (all fields optional)', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildActiveDashaEnvelope(SAMPLE_ACTIVE_RASHI, null))

    const result = await callQueryJaiminiCharaDasha({})

    // Should not be a Zod error
    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
    const parsed = parseContent(result)
    expect(parsed['ok']).toBe(true)
  })

  // ── T7: full mode returns active_rashi_dasha and active_antar_dasha ─────────

  it('T7 — full mode also returns active_rashi_dasha and active_antar_dasha fields', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    // First call: full periods
    mock.mockResolvedValueOnce(buildFullPeriodsEnvelope(SAMPLE_FULL_PERIODS))
    // Second call: active dasha
    mock.mockResolvedValueOnce(buildActiveDashaEnvelope(SAMPLE_ACTIVE_RASHI, SAMPLE_ACTIVE_ANTAR, '2026-06-01'))

    const result = await callQueryJaiminiCharaDasha({
      include_sub_periods: true,
      date: '2026-06-01',
    })

    const parsed = parseContent(result)
    expect(parsed['ok']).toBe(true)

    // Must have both full_periods AND active dasha fields
    expect(Array.isArray(parsed['full_periods'])).toBe(true)
    expect(parsed['active_rashi_dasha']).toBeDefined()
    const activeDasha = parsed['active_rashi_dasha'] as { rashi?: string }
    expect(typeof activeDasha.rashi).toBe('string')
  })

  // ── T8: sidecar returns empty/invalid active_rashi_dasha → error ────────────

  it('T8 — sidecar response with missing active_rashi_dasha returns errorResult', async () => {
    const mock = vi.mocked(callPlatformPrimitive)

    // Return an envelope where inner data has ok:true but no active_rashi_dasha
    const emptyInner = {
      ok: true,
      query_date: '2026-06-01',
      active_rashi_dasha: null,
      active_antar_dasha: null,
    }
    mock.mockResolvedValueOnce({
      status: 200,
      envelope: {
        ok: true,
        trace_id: 'trace-empty-001',
        result: {
          results: [{ content: JSON.stringify(emptyInner) }],
        },
      },
    })

    const result = await callQueryJaiminiCharaDasha({ date: '2026-06-01' })

    expect((result as { isError: boolean }).isError).toBe(true)
    const parsed = parseContent(result)
    expect(parsed['ok']).toBe(false)
    expect(parsed['error']).toBe('active_dasha_not_found')
  })

  // ── Additional: algorithm field is present ────────────────────────────────────

  it('algorithm field is "jaimini_chara_dasha" in response', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildActiveDashaEnvelope(SAMPLE_ACTIVE_RASHI, null, '2026-06-01'))

    const result = await callQueryJaiminiCharaDasha({ date: '2026-06-01' })
    const parsed = parseContent(result)

    expect(parsed['algorithm']).toBe('jaimini_chara_dasha')
  })

  // ── Additional: full_periods sidecar error when include_sub_periods=true ─────

  it('full mode sidecar error returns errorResult with ok:false', async () => {
    const mock = vi.mocked(callPlatformPrimitive)
    mock.mockResolvedValueOnce(buildErrorEnvelope(500, 'internal error'))

    const result = await callQueryJaiminiCharaDasha({ include_sub_periods: true })

    expect((result as { isError: boolean }).isError).toBe(true)
    const parsed = parseContent(result)
    expect(parsed['ok']).toBe(false)
    expect(parsed['error']).toBe('sidecar_error')
  })
})
