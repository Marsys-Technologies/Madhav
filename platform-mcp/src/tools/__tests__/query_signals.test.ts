/**
 * __tests__/query_signals.test.ts — SRP-T-2 regression tests for query_signals param translation.
 *
 * Covers FIX-3: valence vocabulary updated from old ("positive"/"negative") to DB vocabulary
 * ("benefic"/"malefic"/"context-dependent"). Tests that the Zod schema enforces the new
 * vocabulary and that each valid valence value is correctly forwarded to callPlatformPrimitive
 * as a single-element array.
 *
 * Tests use the same stub-server pattern as the co-located query_signals.test.ts:
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
import { registerQuerySignals } from '../query_signals.js'

// ── Constants ─────────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user-srp-t2',
  audience_tier: 'super_admin',
  key_id: 'test-key-srp-t2',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function buildSignalsEnvelope(signals: unknown[] = []) {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-srp-t2-signals-001',
      audience_tier: 'super_admin',
      epistemics: { surgical: true, confidence_band: 'high', horizon_days: null, falsifier: null },
      result: {
        tool_bundle_id: 'signals-bundle-srp-t2',
        tool_name: 'query_signals',
        tool_version: '1.0.0',
        invocation_params: {},
        results: signals.map(s => ({
          content: JSON.stringify(s),
          source_canonical_id: 'MSR',
          source_version: '5.0',
          confidence: 0.85,
          significance: 0.8,
        })),
        served_from_cache: false,
        latency_ms: 10,
        result_hash: 'sha256:srp-t2-signals-test',
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
 * Returns {zodError, isZodError: true} on Zod validation failure,
 * or the MCP result object on handler invocation.
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

  if (!capturedHandler) throw new Error('query_signals handler was not registered on stub server')

  // Simulate the Zod validation the MCP SDK performs before invoking the handler
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('query_signals param translation — SRP-T-2 regression suite', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ── FIX-3 regression: valence vocabulary ─────────────────────────────────────

  describe('FIX-3 regression: valence vocabulary (benefic/malefic/context-dependent)', () => {
    it('valence="benefic" is accepted by Zod schema and forwarded as ["benefic"] to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ valence: 'benefic' })

      expect(callPlatformPrimitive).toHaveBeenCalledTimes(1)
      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['valence']).toEqual(['benefic'])
    })

    it('valence="malefic" is accepted by Zod schema and forwarded as ["malefic"] to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ valence: 'malefic' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['valence']).toEqual(['malefic'])
    })

    it('valence="context-dependent" is accepted by Zod schema and forwarded as ["context-dependent"] to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ valence: 'context-dependent' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['valence']).toEqual(['context-dependent'])
    })

    it('old vocabulary "positive" is REJECTED by Zod schema (FIX-3 regression guard)', async () => {
      const result = await callQuerySignals({ valence: 'positive' })
      expect((result as { isZodError: boolean }).isZodError).toBe(true)
    })

    it('old vocabulary "negative" is REJECTED by Zod schema (FIX-3 regression guard)', async () => {
      const result = await callQuerySignals({ valence: 'negative' })
      expect((result as { isZodError: boolean }).isZodError).toBe(true)
    })

    it('invalid valence string "lucky" is REJECTED by Zod schema', async () => {
      const result = await callQuerySignals({ valence: 'lucky' })
      expect((result as { isZodError: boolean }).isZodError).toBe(true)
    })

    it('no valence arg → no valence key sent to platform (undefined, not empty array)', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ planet: 'Sun' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['valence']).toBeUndefined()
    })

    it('valence is always forwarded as an array to platform (not a bare string)', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ valence: 'malefic' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(Array.isArray(params['valence'])).toBe(true)
      expect(typeof params['valence']).not.toBe('string')
    })
  })

  // ── domain filter translation ─────────────────────────────────────────────────

  describe('domain filter translation', () => {
    it('domain="career" is passed as domain field to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ domain: 'career' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['domain']).toBe('career')
    })

    it('domains=["health","spiritual"] is passed as domains array to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ domains: ['health', 'spiritual'] })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['domains']).toEqual(['health', 'spiritual'])
    })
  })

  // ── planet filter translation ─────────────────────────────────────────────────

  describe('planet filter translation', () => {
    it('planet="Saturn" is passed as planet field to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ planet: 'Saturn' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['planet']).toBe('Saturn')
    })

    it('planet="Moon" with forward_looking=true both reach platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ planet: 'Moon', forward_looking: true })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['planet']).toBe('Moon')
      expect(params['forward_looking']).toBe(true)
    })
  })

  // ── forward_looking translation ───────────────────────────────────────────────

  describe('forward_looking filter translation', () => {
    it('forward_looking=true is forwarded to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ forward_looking: true })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['forward_looking']).toBe(true)
    })

    it('forward_looking=false is forwarded to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ forward_looking: false })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['forward_looking']).toBe(false)
    })
  })

  // ── limit default ─────────────────────────────────────────────────────────────

  describe('limit default', () => {
    it('limit defaults to 50 when not explicitly provided', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ domain: 'career' })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['limit']).toBe(50)
    })

    it('explicit limit=100 is forwarded to platform', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue(buildSignalsEnvelope())

      await callQuerySignals({ limit: 100 })

      const params = vi.mocked(callPlatformPrimitive).mock.calls[0][1] as Record<string, unknown>
      expect(params['limit']).toBe(100)
    })
  })

  // ── error handling ────────────────────────────────────────────────────────────

  describe('error handling', () => {
    it('returns isError=true when platform primitive call fails', async () => {
      vi.mocked(callPlatformPrimitive).mockResolvedValue({
        status: 500,
        envelope: {
          ok: false,
          trace_id: 'fail-srp-t2-001',
          error: { class: 'internal', message: 'DB connection error' },
        },
      })

      const result = await callQuerySignals({ domain: 'career', forward_looking: true })
      expect((result as { isError?: boolean }).isError).toBe(true)
    })
  })
})
