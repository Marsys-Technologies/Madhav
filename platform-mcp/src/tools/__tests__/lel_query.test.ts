/**
 * __tests__/lel_query.test.ts — SRP-T-2 regression tests for lel_query param translation.
 *
 * Covers:
 *   FIX-5: significance_tier="major" must send significance="major" to platform primitive,
 *          NOT min_significance=0.8 (the old mapping). The platform reads significance as
 *          a string tier ('major'|'moderate'|'minor').
 *
 *   FIX-6: LEL_SOURCE_VERSION constant must equal "1.7" (not "1.6"). The tool description
 *          and source_version annotations must reference the current LEL version.
 *
 * Tests use the same stub-server pattern as the co-located tool tests:
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
import { registerLelQuery, LEL_SOURCE_VERSION, LEL_QUERY_DESCRIPTION } from '../lel_query.js'

// ── Constants ─────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user-srp-t2-lel',
  audience_tier: 'super_admin',
  key_id: 'test-key-srp-t2-lel',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function buildLelEnvelope(events: unknown[] = []) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-srp-t2-lel-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'lel-bundle-srp-t2',
        tool_name: 'lel_query',
        tool_version: '1.0.0',
        invocation_params: {},
        source_version: LEL_SOURCE_VERSION,
        results: events.map(e => ({
          content: JSON.stringify(e),
          source_canonical_id: 'LEL',
          source_version: LEL_SOURCE_VERSION,
          confidence: 0.89,
          significance: 0.85,
        })),
        served_from_cache: false,
        latency_ms: 12,
        result_hash: 'sha256:srp-t2-lel-test',
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
 * Returns {zodError, isZodError: true} on Zod validation failure.
 */
async function callLelQuery(
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

  registerLelQuery(stubServer, () => principal)

  if (!capturedHandler) throw new Error('lel_query handler was not registered on stub server')

  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('lel_query param translation — SRP-T-2 regression suite', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── FIX-5 regression: significance field name ─────────────────────────────────

  describe('FIX-5 regression: significance_tier sends significance string (not min_significance float)', () => {
    it('significance_tier="major" sends significance="major" to platform (not min_significance=0.8)', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({ significance_tier: 'major' })

      expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['significance']).toBe('major')
    })

    it('significance_tier="moderate" sends significance="moderate" to platform (not min_significance=0.5)', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({ significance_tier: 'moderate' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['significance']).toBe('moderate')
    })

    it('significance_tier="minor" sends significance="minor" to platform (not min_significance=0.2)', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({ significance_tier: 'minor' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['significance']).toBe('minor')
    })

    it('FIX-5 regression: min_significance key is NEVER sent to platform when significance_tier is provided', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({ significance_tier: 'major' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['min_significance']).toBeUndefined()
    })

    it('FIX-5 regression: min_significance key is NEVER sent to platform for any significance tier', async () => {
      const tiers = ['major', 'moderate', 'minor'] as const

      for (const tier of tiers) {
        vi.clearAllMocks()
        vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

        await callLelQuery({ significance_tier: tier })

        const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
        expect(params['min_significance']).toBeUndefined()
        expect(typeof params['significance']).toBe('string')
        expect(params['significance']).toBe(tier)
      }
    })

    it('no significance_tier → no significance key sent to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({ category: 'career' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['significance']).toBeUndefined()
      expect(params['min_significance']).toBeUndefined()
    })

    it('Zod rejects invalid significance_tier value ("high" is not in schema)', async () => {
      const result = await callLelQuery({ significance_tier: 'high' })
      expect((result as { isZodError: boolean }).isZodError).toBe(true)
    })

    it('Zod rejects old float significance ("0.8" string is not a valid enum member)', async () => {
      const result = await callLelQuery({ significance_tier: '0.8' })
      expect((result as { isZodError: boolean }).isZodError).toBe(true)
    })
  })

  // ── FIX-6 regression: source_version annotation ───────────────────────────────

  describe('FIX-6 regression: LEL source_version must be "1.7" not "1.6"', () => {
    it('LEL_SOURCE_VERSION exported constant equals "1.7"', () => {
      expect(LEL_SOURCE_VERSION).toBe('1.7')
    })

    it('LEL_SOURCE_VERSION is not the old "1.6" value', () => {
      expect(LEL_SOURCE_VERSION).not.toBe('1.6')
    })

    it('LEL_QUERY_DESCRIPTION references "1.7" in its text', () => {
      expect(LEL_QUERY_DESCRIPTION).toContain('1.7')
    })

    it('LEL_QUERY_DESCRIPTION does not reference the old "1.6" version string', () => {
      expect(LEL_QUERY_DESCRIPTION).not.toContain('1.6')
    })

    it('response from callLelQuery contains "1.7" in the envelope text (source_version annotation)', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope([
        { event_id: 'LEL.E001', date: '2019-02-15', category: 'career', description: 'Job change.' },
      ]))

      const result = await callLelQuery({})

      // The result is an MCP content array: {content: [{type:'text', text:'...json...'}]}
      // Extract the inner JSON text to check source_version annotation
      const mcpResult = result as { content: Array<{ type: string; text: string }> }
      const text = mcpResult.content[0].text
      // The inner JSON contains source_version: "1.7" — search for the value
      expect(text).toContain('1.7')
    })

    it('response does NOT contain old "1.6" version annotation', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope([
        { event_id: 'LEL.E001', date: '2019-02-15', category: 'career', description: 'Job change.' },
      ]))

      const result = await callLelQuery({})

      const mcpResult = result as { content: Array<{ type: string; text: string }> }
      const text = mcpResult.content[0].text
      expect(text).not.toContain('1.6')
    })
  })

  // ── category filter translation ───────────────────────────────────────────────

  describe('category filter translation', () => {
    it('category="career" is passed as category field to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({ category: 'career' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['category']).toBe('career')
    })

    it('category="health" is passed as category field to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({ category: 'health' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['category']).toBe('health')
    })

    it('no category → no category key in platform params', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({})

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['category']).toBeUndefined()
    })

    it('category + significance_tier together are both forwarded correctly', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({ category: 'career', significance_tier: 'major' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['category']).toBe('career')
      expect(params['significance']).toBe('major')
      expect(params['min_significance']).toBeUndefined()
    })
  })

  // ── date_range filter translation ─────────────────────────────────────────────

  describe('date_range filter translation', () => {
    it('date_range {start, end} is forwarded as date_range to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({ date_range: { start: '2015-01-01', end: '2020-12-31' } })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['date_range']).toEqual({ start: '2015-01-01', end: '2020-12-31' })
    })

    it('no date_range → no date_range key in platform params', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildLelEnvelope())

      await callLelQuery({ category: 'spiritual' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['date_range']).toBeUndefined()
    })
  })

  // ── error handling ────────────────────────────────────────────────────────────

  describe('error handling', () => {
    it('returns isError=true when platform primitive call fails', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue({
        status: 500,
        envelope: {
          ok: false,
          trace_id: 'fail-srp-t2-lel-001',
          error: { class: 'internal', message: 'LEL DB read error' },
        },
      })

      const result = await callLelQuery({ category: 'career' })
      expect((result as { isError?: boolean }).isError).toBe(true)
    })

    it('returns isError=true on 403 forbidden response from platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue({
        status: 403,
        envelope: {
          ok: false,
          trace_id: 'fail-srp-t2-lel-403',
          error: { class: 'forbidden', message: 'Insufficient audience tier' },
        },
      })

      const result = await callLelQuery({})
      expect((result as { isError?: boolean }).isError).toBe(true)
    })
  })
})
