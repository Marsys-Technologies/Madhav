/**
 * query_dasha_periods.test.ts — Unit tests for the query_dasha_periods MCP tool.
 *
 * Session: TR-P7-S1
 *
 * Acceptance criteria:
 *   TC.1 — level param "antar" returns periods (existing baseline behavior).
 *   TC.2 — level "pratyantar" returns periods with sub_periods having shorter
 *           duration_days than the corresponding AD period.
 *   TC.3 — level "sookshma" returns periods with PD sub_periods, each of which
 *           has SD sub_periods with even shorter durations.
 *   TC.4 — level "maha" deduplicates to MD-boundary rows.
 *   TC.5 — computePratyantar produces exactly 9 sub-periods summing ≈ AD duration.
 *   TC.6 — Unknown planet in AD lord falls back gracefully (no crash).
 *   TC.7 — Zod default for level is "antar".
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
import {
  registerQueryDashaPeriods,
  computePratyantar,
  computeSookshma,
  VIMSHOTTARI_YEARS,
} from './query_dasha_periods.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/** A sample AD period spanning ~1 year (365 days). */
const SAMPLE_AD_START = '2025-01-01'
const SAMPLE_AD_END = '2026-01-01'

/** Build an envelope with multiple AD periods for the given level tests. */
function buildDashaEnvelope(periods: unknown[]) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-dasha-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        periods,
        level: 'antar',
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
      trace_id: 'trace-error-001',
      error: { class: 'internal', message: 'DB error', remediation: 'retry' },
    },
  }
}

/** Two sample AD periods within Saturn MD. */
const SAMPLE_PERIODS = [
  {
    md_lord: 'Saturn',
    mahadasha: 'Saturn',
    ad_lord: 'Mercury',
    antardasha: 'Mercury',
    start_date: '2025-01-01',
    end_date: '2027-06-15',
  },
  {
    md_lord: 'Saturn',
    mahadasha: 'Saturn',
    ad_lord: 'Ketu',
    antardasha: 'Ketu',
    start_date: '2027-06-15',
    end_date: '2028-07-15',
  },
]

/**
 * Register query_dasha_periods on a stub MCP server, optionally apply Zod,
 * and invoke the captured handler.
 */
async function callQueryDashaPeriods(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
  applyZod = false,
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

  registerQueryDashaPeriods(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_dasha_periods handler was not registered')

  if (applyZod) {
    const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
    const zodSchema = z.object(schemaShape)
    const parsed = zodSchema.safeParse(args)
    if (!parsed.success) return { zodError: parsed.error, isZodError: true }
    return capturedHandler(parsed.data as Record<string, unknown>)
  }

  return capturedHandler(args)
}

/** Parse content[0].text from an MCP result. */
function parseResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Unit tests for pure computation helpers ───────────────────────────────────

describe('computePratyantar (pure)', () => {
  it('TC.5 — produces exactly 9 sub-periods', () => {
    const sub = computePratyantar('Mercury', SAMPLE_AD_START, SAMPLE_AD_END)
    expect(sub).toHaveLength(9)
  })

  it('TC.5 — all sub-periods have positive duration_days', () => {
    const sub = computePratyantar('Mercury', SAMPLE_AD_START, SAMPLE_AD_END)
    sub.forEach(p => {
      expect(p.duration_days).toBeGreaterThan(0)
    })
  })

  it('TC.5 — sub-periods are contiguous (each start = previous end)', () => {
    const sub = computePratyantar('Mercury', SAMPLE_AD_START, SAMPLE_AD_END)
    for (let i = 1; i < sub.length; i++) {
      expect(sub[i].start_date).toBe(sub[i - 1].end_date)
    }
  })

  it('TC.5 — first sub-period starts on AD start date', () => {
    const sub = computePratyantar('Saturn', SAMPLE_AD_START, SAMPLE_AD_END)
    expect(sub[0].start_date).toBe(SAMPLE_AD_START)
  })

  it('TC.5 — last sub-period ends on AD end date', () => {
    const sub = computePratyantar('Saturn', SAMPLE_AD_START, SAMPLE_AD_END)
    expect(sub[sub.length - 1].end_date).toBe(SAMPLE_AD_END)
  })

  it('TC.5 — sum of duration_days ≈ AD duration (within 1 day rounding)', () => {
    const sub = computePratyantar('Jupiter', SAMPLE_AD_START, SAMPLE_AD_END)
    const total = sub.reduce((acc, p) => acc + p.duration_days, 0)
    const adStart = new Date(SAMPLE_AD_START)
    const adEnd = new Date(SAMPLE_AD_END)
    const adDays = Math.round((adEnd.getTime() - adStart.getTime()) / 86_400_000)
    // Allow ±9 days for rounding across 9 periods
    expect(Math.abs(total - adDays)).toBeLessThanOrEqual(9)
  })

  it('TC.6 — unknown lord falls back gracefully (9 sub-periods, no crash)', () => {
    const sub = computePratyantar('UnknownPlanet', SAMPLE_AD_START, SAMPLE_AD_END)
    expect(sub).toHaveLength(9)
    // All known planets should have positive duration (unknown gets 0 ratio → 0ms → 0 days)
    // but should not throw
  })

  it('sub-periods duration proportional to Vimshottari years', () => {
    const sub = computePratyantar('Sun', SAMPLE_AD_START, SAMPLE_AD_END)
    const adStart = new Date(SAMPLE_AD_START)
    const adEnd = new Date(SAMPLE_AD_END)
    const adMs = adEnd.getTime() - adStart.getTime()

    // Venus (20 years) should be about 20/6 ≈ 3.33x longer than Sun (6 years)
    const sunPeriod = sub.find(p => p.planet === 'Sun')
    const venusPeriod = sub.find(p => p.planet === 'Venus')
    expect(sunPeriod).toBeDefined()
    expect(venusPeriod).toBeDefined()

    // Check Venus duration ≈ adDuration * 20/120
    const expectedVenusDays = Math.round(adMs * (VIMSHOTTARI_YEARS['Venus']! / 120) / 86_400_000)
    expect(Math.abs(venusPeriod!.duration_days - expectedVenusDays)).toBeLessThanOrEqual(2)
  })
})

describe('computeSookshma (pure)', () => {
  it('produces 9 sub-periods for a PD period', () => {
    const sub = computeSookshma('Venus', '2025-01-01', '2025-03-01')
    expect(sub).toHaveLength(9)
  })

  it('SD sub-periods are shorter than the PD parent duration', () => {
    const pdStart = '2025-01-01'
    const pdEnd = '2025-04-01'
    const sub = computeSookshma('Jupiter', pdStart, pdEnd)
    const pdMs = new Date(pdEnd).getTime() - new Date(pdStart).getTime()
    const pdDays = Math.round(pdMs / 86_400_000)
    sub.forEach(s => {
      expect(s.duration_days).toBeLessThan(pdDays)
    })
  })
})

// ── MCP handler tests ─────────────────────────────────────────────────────────

describe('query_dasha_periods MCP tool (TR-P7-S1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── TC.1: antar level returns periods (existing baseline) ──────────────────

  it('TC.1 — level "antar" returns non-empty periods', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildDashaEnvelope(SAMPLE_PERIODS))

    const result = await callQueryDashaPeriods({ level: 'antar' })
    const envelope = parseResult(result)

    expect(envelope['ok']).toBe(true)
    const res = envelope['result'] as Record<string, unknown>
    const periods = res['periods'] as unknown[]
    expect(Array.isArray(periods)).toBe(true)
    expect(periods.length).toBeGreaterThan(0)
  })

  // ── TC.2: pratyantar level returns sub_periods shorter than AD ─────────────

  it('TC.2 — level "pratyantar" returns periods with sub_periods', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildDashaEnvelope(SAMPLE_PERIODS))

    const result = await callQueryDashaPeriods({ level: 'pratyantar' })
    const envelope = parseResult(result)

    expect(envelope['ok']).toBe(true)
    const res = envelope['result'] as Record<string, unknown>
    const periods = res['periods'] as Array<Record<string, unknown>>
    expect(periods.length).toBeGreaterThan(0)
    expect(periods[0]['sub_periods']).toBeDefined()
    expect(Array.isArray(periods[0]['sub_periods'])).toBe(true)
  })

  it('TC.2 — PD sub_periods have shorter duration_days than the AD period', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildDashaEnvelope(SAMPLE_PERIODS))

    const result = await callQueryDashaPeriods({ level: 'pratyantar' })
    const envelope = parseResult(result)
    const res = envelope['result'] as Record<string, unknown>
    const periods = res['periods'] as Array<Record<string, unknown>>

    for (const period of periods) {
      const adStart = new Date(String(period['start_date'] ?? period['start']))
      const adEnd = new Date(String(period['end_date'] ?? period['end']))
      const adDays = Math.round((adEnd.getTime() - adStart.getTime()) / 86_400_000)

      const subPeriods = period['sub_periods'] as Array<{ duration_days: number }>
      for (const pd of subPeriods) {
        expect(pd.duration_days).toBeLessThan(adDays)
      }
    }
  })

  // ── TC.3: sookshma level returns periods with nested sub_periods ───────────

  it('TC.3 — level "sookshma" returns periods with PD sub_periods that have SD sub_periods', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildDashaEnvelope(SAMPLE_PERIODS))

    const result = await callQueryDashaPeriods({ level: 'sookshma' })
    const envelope = parseResult(result)

    expect(envelope['ok']).toBe(true)
    const res = envelope['result'] as Record<string, unknown>
    const periods = res['periods'] as Array<Record<string, unknown>>
    expect(periods.length).toBeGreaterThan(0)

    // Each AD period should have PD sub_periods
    const pdList = periods[0]['sub_periods'] as Array<Record<string, unknown>>
    expect(Array.isArray(pdList)).toBe(true)
    expect(pdList.length).toBe(9)

    // Each PD should have SD sub_periods
    const sdList = pdList[0]['sub_periods'] as Array<{ duration_days: number }>
    expect(Array.isArray(sdList)).toBe(true)
    expect(sdList.length).toBe(9)
  })

  it('TC.3 — SD duration_days < PD duration_days < AD duration_days', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildDashaEnvelope(SAMPLE_PERIODS))

    const result = await callQueryDashaPeriods({ level: 'sookshma' })
    const envelope = parseResult(result)
    const res = envelope['result'] as Record<string, unknown>
    const periods = res['periods'] as Array<Record<string, unknown>>

    const adStart = new Date(String(periods[0]['start_date']))
    const adEnd = new Date(String(periods[0]['end_date']))
    const adDays = Math.round((adEnd.getTime() - adStart.getTime()) / 86_400_000)

    const pdList = periods[0]['sub_periods'] as Array<Record<string, unknown>>
    const pdDays = (pdList[0] as { duration_days: number }).duration_days

    const sdList = pdList[0]['sub_periods'] as Array<{ duration_days: number }>
    const sdDays = sdList[0].duration_days

    expect(pdDays).toBeLessThan(adDays)
    expect(sdDays).toBeLessThan(pdDays)
  })

  // ── TC.4: maha level deduplicates ─────────────────────────────────────────

  it('TC.4 — level "maha" collapses multiple AD rows to 1 row per MD lord', async () => {
    // Both SAMPLE_PERIODS have mahadasha="Saturn" → dedup keeps only the first row
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildDashaEnvelope(SAMPLE_PERIODS))

    const result = await callQueryDashaPeriods({ level: 'maha' })
    const envelope = parseResult(result)
    const res = envelope['result'] as Record<string, unknown>
    const periods = res['periods'] as unknown[]

    // 2 AD rows under Saturn MD → dedup to 1
    expect(periods.length).toBe(1)
  })

  // ── TC.7: Zod default level="antar" ───────────────────────────────────────

  it('TC.7 — Zod default for level is "antar"', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildDashaEnvelope(SAMPLE_PERIODS))

    // Call without level param; Zod should default it to "antar"
    const result = await callQueryDashaPeriods({}, mockPrincipal, true)
    const envelope = parseResult(result)

    expect(envelope['ok']).toBe(true)
    const res = envelope['result'] as Record<string, unknown>
    // level "antar" should not add sub_periods
    const periods = res['periods'] as Array<Record<string, unknown>>
    expect(periods[0]['sub_periods']).toBeUndefined()
  })

  // ── Error propagation ──────────────────────────────────────────────────────

  it('returns error result when platform primitive fails', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildErrorEnvelope())

    const result = await callQueryDashaPeriods({ level: 'antar' })
    expect((result as { isError?: boolean }).isError).toBe(true)
  })

  // ── Additional: level annotated in result ─────────────────────────────────

  it('result.level equals the requested level', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildDashaEnvelope(SAMPLE_PERIODS))

    const result = await callQueryDashaPeriods({ level: 'pratyantar' })
    const envelope = parseResult(result)
    const res = envelope['result'] as Record<string, unknown>

    expect(res['level']).toBe('pratyantar')
  })

  // ── Additional: at param is passed through ────────────────────────────────

  it('passes "at" param through to the platform primitive', async () => {
    vi.mocked(callPlatformPrimitive).mockResolvedValue(buildDashaEnvelope(SAMPLE_PERIODS))

    await callQueryDashaPeriods({ at: '2026-05-25', level: 'antar' })

    const [toolName, params] = vi.mocked(callPlatformPrimitive).mock.calls[0]
    expect(toolName).toBe('query_dasha_periods')
    expect((params as Record<string, unknown>)['at']).toBe('2026-05-25')
  })
})
