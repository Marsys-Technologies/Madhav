/**
 * __tests__/query_ephemeris.test.ts — SRP-T-2 regression tests for query_ephemeris param translation.
 *
 * Covers FIX-4: sample_step string enum ("7d", "30d", "1d") must be converted to integer days
 * (7, 30, 1) before calling callPlatformPrimitive. The platform primitive's QueryEphemerisInput
 * reads sample_step as a number; sending "7d" results in NaN comparison ("7d" > 1 is false),
 * so the tool's SAMPLE_STEP_DAYS map performs the conversion.
 *
 * Tests use the same stub-server pattern as the co-located query_ephemeris.test.ts:
 * register the tool on a stub McpServer, capture the handler + schema, simulate Zod validation,
 * then invoke the handler and assert on callPlatformPrimitive call args.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'

// Mock callPlatformPrimitive BEFORE importing the tool
vi.mock('../../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../../client.js'
import { registerQueryEphemeris } from '../query_ephemeris.js'

// ── Constants ─────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user-srp-t2-eph',
  audience_tier: 'super_admin',
  key_id: 'test-key-srp-t2-eph',
}

// A short date range used across most tests
const SHORT_RANGE = { from: '2026-01-01', to: '2026-06-30' }

// ── Helpers ───────────────────────────────────────────────────────────────────

function buildEphemerisEnvelope(positions: unknown[] = []) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-srp-t2-eph-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'ephemeris-bundle-srp-t2',
        tool_name: 'query_ephemeris',
        tool_version: '1.0.0',
        invocation_params: {},
        results: positions.map(p => ({
          content: JSON.stringify(p),
          source_canonical_id: 'EPHEMERIS_DAILY',
          source_version: '1.0',
          confidence: 1.0,
          significance: 0.9,
        })),
        served_from_cache: false,
        latency_ms: 8,
        result_hash: 'sha256:srp-t2-ephemeris-test',
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

/**
 * Register the tool on a stub server, simulate Zod validation, then invoke the handler.
 */
async function callQueryEphemeris(
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

  registerQueryEphemeris(stubServer, () => principal)

  if (!capturedHandler) throw new Error('query_ephemeris handler was not registered on stub server')

  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_ephemeris param translation — SRP-T-2 regression suite', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── FIX-4 regression: sample_step type conversion ─────────────────────────────

  describe('FIX-4 regression: sample_step string enum → integer days conversion', () => {
    it('sample_step="1d" is converted to integer 1 before reaching platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildEphemerisEnvelope())

      await callQueryEphemeris({ planet: 'Moon', date_range: SHORT_RANGE, sample_step: '1d' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['sample_step']).toBe(1)
      expect(typeof params['sample_step']).toBe('number')
    })

    it('sample_step="7d" is converted to integer 7 before reaching platform (not string "7d")', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildEphemerisEnvelope())

      await callQueryEphemeris({ planet: 'Moon', date_range: SHORT_RANGE, sample_step: '7d' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['sample_step']).toBe(7)
      expect(typeof params['sample_step']).toBe('number')
    })

    it('sample_step="30d" is converted to integer 30 before reaching platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildEphemerisEnvelope())

      await callQueryEphemeris({ planet: 'Saturn', date_range: SHORT_RANGE, sample_step: '30d' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['sample_step']).toBe(30)
      expect(typeof params['sample_step']).toBe('number')
    })

    it('sample_step default (omitted) sends integer 1 to platform — never a string', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildEphemerisEnvelope())

      await callQueryEphemeris({ planet: 'Jupiter', date_range: SHORT_RANGE })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      // Default is "1d" → converts to 1
      expect(params['sample_step']).toBe(1)
      expect(typeof params['sample_step']).toBe('number')
    })

    it('sample_step sent to platform is NEVER a string — all variants produce a number', async () => {
      const steps = ['1d', '7d', '30d'] as const
      const expectedNums = [1, 7, 30]

      for (let i = 0; i < steps.length; i++) {
        vi.clearAllMocks()
        vi.mocked(callPlatformPrimitive).mockResolvedValue(buildEphemerisEnvelope())

        await callQueryEphemeris({
          planet: 'Moon',
          date_range: { from: '2026-01-01', to: '2026-01-31' },
          sample_step: steps[i],
        })

        const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
        expect(typeof params['sample_step']).toBe('number')
        expect(params['sample_step']).toBe(expectedNums[i])
      }
    })

    it('Zod rejects invalid sample_step string (not in enum)', async () => {
      const result = await callQueryEphemeris({
        planet: 'Moon',
        date_range: SHORT_RANGE,
        sample_step: '14d',
      })
      expect((result as { isZodError: boolean }).isZodError).toBe(true)
    })
  })

  // ── date_range translation ────────────────────────────────────────────────────

  describe('date_range {from, to} → start_date/end_date for platform primitive', () => {
    it('date_range.from is mapped to start_date in platform call', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildEphemerisEnvelope())

      await callQueryEphemeris({ planet: 'Jupiter', date_range: { from: '2026-03-01', to: '2026-09-30' } })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['start_date']).toBe('2026-03-01')
    })

    it('date_range.to is mapped to end_date in platform call', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildEphemerisEnvelope())

      await callQueryEphemeris({ planet: 'Jupiter', date_range: { from: '2026-03-01', to: '2026-09-30' } })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['end_date']).toBe('2026-09-30')
    })

    it('date_range object is NOT forwarded directly to platform (no date_range key)', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildEphemerisEnvelope())

      await callQueryEphemeris({ planet: 'Saturn', date_range: SHORT_RANGE })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['date_range']).toBeUndefined()
    })

    it('Zod rejects old schema {start, end} — must use {from, to}', async () => {
      const result = await callQueryEphemeris({
        planet: 'Mars',
        date_range: { start: '2026-01-01', end: '2026-06-30' },
      })
      expect((result as { isZodError: boolean }).isZodError).toBe(true)
    })

    it('date range > 1825 days returns an error envelope (not Zod error)', async () => {
      const result = await callQueryEphemeris({
        planet: 'Saturn',
        date_range: { from: '2020-01-01', to: '2030-01-01' },
      })

      expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
      expect((result as { isError?: boolean }).isError).toBe(true)

      const content = (result as { content: Array<{ type: string; text: string }> }).content
      const parsed = JSON.parse(content[0].text) as Record<string, unknown>
      expect(parsed['ok']).toBe(false)
      expect(parsed['error']).toBe('date_range_too_wide')
    })

    it('reversed date range (from > to) returns date_range_invalid error', async () => {
      const result = await callQueryEphemeris({
        planet: 'Sun',
        date_range: { from: '2026-12-31', to: '2026-01-01' },
      })

      expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
      expect((result as { isError?: boolean }).isError).toBe(true)
      const content = (result as { content: Array<{ type: string; text: string }> }).content
      const parsed = JSON.parse(content[0].text) as Record<string, unknown>
      expect(parsed['error']).toBe('date_range_invalid')
    })
  })

  // ── planet normalization ──────────────────────────────────────────────────────

  describe('planet normalization', () => {
    it('single planet string is forwarded as planet field to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildEphemerisEnvelope())

      await callQueryEphemeris({ planet: 'Saturn', date_range: SHORT_RANGE })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['planet']).toBe('Saturn')
      expect(params['planets']).toBeUndefined()
    })

    it('planet array is forwarded as planets[] field to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildEphemerisEnvelope())

      await callQueryEphemeris({ planet: ['Saturn', 'Jupiter'], date_range: SHORT_RANGE })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['planets']).toEqual(['Saturn', 'Jupiter'])
      expect(params['planet']).toBeUndefined()
    })

    it('Zod rejects invalid planet name (Pluto is not a Jyotish graha)', async () => {
      const result = await callQueryEphemeris({
        planet: 'Pluto',
        date_range: SHORT_RANGE,
      })
      expect((result as { isZodError: boolean }).isZodError).toBe(true)
    })
  })

  // ── error handling ────────────────────────────────────────────────────────────

  describe('error handling', () => {
    it('returns isError=true when platform primitive call fails', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue({
        status: 500,
        envelope: {
          ok: false,
          trace_id: 'fail-srp-t2-eph-001',
          error: { class: 'internal', message: 'Ephemeris DB error' },
        },
      })

      const result = await callQueryEphemeris({ planet: 'Moon', date_range: SHORT_RANGE })
      expect((result as { isError?: boolean }).isError).toBe(true)
    })
  })
})
