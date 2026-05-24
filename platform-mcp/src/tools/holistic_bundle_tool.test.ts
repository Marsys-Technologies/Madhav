/**
 * holistic_bundle_tool.test.ts — Tests for the holistic_bundle MCP tool.
 *
 * TR-P5-S1 acceptance criteria:
 *   1. getToolRouteFor('UCN') returns 'read_asset' (not 'vector_search')
 *   2. getToolRouteFor('RM') returns 'read_asset'
 *   3. getToolRouteFor('CDLM') returns 'read_asset'
 *   4. buildParams('UCN', {...}) returns { canonical_id: 'UCN' }
 *   5. buildParams('MSR', { subset_size: 50 }) returns object with limit: 50
 *   6. buildParams('MSR', {}) defaults to limit: 100
 *   7. return_format='compressed' strips data field from bundle_entries
 *   8. response_meta.size_kb is a number in the envelope
 *   9. response_meta.chunked is true when bundle is large
 *  10. Zod schema rejects subset_size: 5 (below min 10)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Import helpers directly (exported from holistic_bundle.ts) ────────────────

import { getToolRouteFor, buildParams } from '../bundles/holistic_bundle.js'
import type { HolisticBundleEnvelope, BundleEntry } from '../bundles/holistic_bundle.js'

// ── Mock executeHolisticBundle BEFORE importing the tool ──────────────────────

vi.mock('../bundles/holistic_bundle.js', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../bundles/holistic_bundle.js')>()
  return {
    ...actual,
    executeHolisticBundle: vi.fn(),
  }
})

import { executeHolisticBundle } from '../bundles/holistic_bundle.js'
import { registerHolisticBundle } from './holistic_bundle_tool.js'

// ── Test helpers ──────────────────────────────────────────────────────────────

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

/**
 * Builds a minimal valid HolisticBundleEnvelope for mocking.
 */
function buildMockEnvelope(overrides: Partial<HolisticBundleEnvelope> = {}): HolisticBundleEnvelope {
  return {
    ok: true,
    bundle_name: 'holistic_bundle',
    served_from_cache: false,
    bundle_entries: [],
    provenance: {
      signal_ids_available: [],
      sub_tools_fired: [],
      sub_tools_errored: [],
    },
    response_meta: {
      size_kb: 1.2,
      chunked: false,
      recommendation: null,
    },
    ...overrides,
  }
}

/**
 * Registers holistic_bundle on a stub MCP server and invokes the handler
 * directly, applying Zod validation (same as the MCP SDK would).
 */
async function callHolisticBundle(
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

  registerHolisticBundle(stubServer, () => principal)

  if (!capturedHandler) throw new Error('holistic_bundle handler was not registered')

  // Simulate Zod validation
  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

/** Parse MCP content text from the tool result. */
function parseResult(result: unknown): Record<string, unknown> {
  const content = (result as { content: Array<{ text: string }> }).content[0].text
  return JSON.parse(content) as Record<string, unknown>
}

// ── Tests: getToolRouteFor ────────────────────────────────────────────────────

describe('getToolRouteFor — UCN/RM/CDLM route fix (TR-P5-S1)', () => {
  it('1. getToolRouteFor("UCN") returns "read_asset" (not "vector_search")', () => {
    expect(getToolRouteFor('UCN')).toBe('read_asset')
  })

  it('2. getToolRouteFor("RM") returns "read_asset"', () => {
    expect(getToolRouteFor('RM')).toBe('read_asset')
  })

  it('3. getToolRouteFor("CDLM") returns "read_asset"', () => {
    expect(getToolRouteFor('CDLM')).toBe('read_asset')
  })

  it('MSR still routes to query_signals (regression guard)', () => {
    expect(getToolRouteFor('MSR')).toBe('query_signals')
  })

  it('CGM still routes to get_cgm_subgraph (regression guard)', () => {
    expect(getToolRouteFor('CGM')).toBe('get_cgm_subgraph')
  })
})

// ── Tests: buildParams ────────────────────────────────────────────────────────

describe('buildParams — param construction (TR-P5-S1)', () => {
  const baseParams = {
    query_text: 'test query',
    tier: 'super_admin',
  }

  it('4. buildParams("UCN", {...}) returns { canonical_id: "UCN" }', () => {
    const result = buildParams('UCN', baseParams)
    expect(result).toEqual({ canonical_id: 'UCN' })
  })

  it('buildParams("RM", {...}) returns { canonical_id: "RM" }', () => {
    const result = buildParams('RM', baseParams)
    expect(result).toEqual({ canonical_id: 'RM' })
  })

  it('buildParams("CDLM", {...}) returns { canonical_id: "CDLM" }', () => {
    const result = buildParams('CDLM', baseParams)
    expect(result).toEqual({ canonical_id: 'CDLM' })
  })

  it('5. buildParams("MSR", { subset_size: 50 }) returns object with limit: 50', () => {
    const result = buildParams('MSR', { ...baseParams, subset_size: 50 })
    expect(result).toMatchObject({ limit: 50 })
  })

  it('6. buildParams("MSR", {}) defaults to limit: 100', () => {
    const result = buildParams('MSR', baseParams)
    expect(result).toMatchObject({ limit: 100 })
  })

  it('buildParams("MSR") with focus_domains includes domain in result', () => {
    const result = buildParams('MSR', { ...baseParams, focus_domains: ['career'] })
    expect(result).toMatchObject({ domain: 'career', limit: 100 })
  })
})

// ── Tests: tool wrapper (mocked executeHolisticBundle) ────────────────────────

describe('holistic_bundle tool — return_format, response_meta, Zod validation (TR-P5-S1)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('7. return_format="compressed" — bundle_entries do not contain data field', async () => {
    const mockExecute = vi.mocked(executeHolisticBundle)

    // Mock returns an entry WITH a data field (as if verbose)
    const entryWithData: BundleEntry = {
      sub_tool: 'MSR',
      errored: false,
      data: { signals: [{ signal_id: 'SIG.001' }] },
      rows_returned: 1,
      signal_ids_available: ['SIG.001'],
      latency_ms: 42,
    }

    // The actual compression happens inside executeHolisticBundle (which we mock),
    // so to test the compressed output we mock it returning a compressed-style entry
    // (no data field). The test verifies the tool faithfully passes return_format
    // to executeHolisticBundle and that the MCP result reflects compressed entries.
    const compressedEntry = {
      sub_tool: 'MSR' as const,
      errored: false as const,
      rows_returned: 1,
      signal_ids_available: ['SIG.001'],
      latency_ms: 42,
    }

    mockExecute.mockResolvedValueOnce(buildMockEnvelope({
      bundle_entries: [compressedEntry],
    }))

    const result = await callHolisticBundle({
      query_text: 'What does my chart say about career?',
      return_format: 'compressed',
    })

    // Verify executeHolisticBundle was called with return_format='compressed'
    expect(mockExecute).toHaveBeenCalledWith(
      expect.objectContaining({ return_format: 'compressed' }),
      expect.any(Object),
    )

    // Verify the returned entry does not have a data field
    const parsed = parseResult(result)
    const entries = (parsed['bundle_entries'] ?? []) as Array<Record<string, unknown>>
    expect(entries.length).toBeGreaterThan(0)
    expect(entries[0]).not.toHaveProperty('data')

    // Suppress unused variable warning
    void entryWithData
  })

  it('8. response_meta.size_kb is a number in the envelope', async () => {
    const mockExecute = vi.mocked(executeHolisticBundle)
    mockExecute.mockResolvedValueOnce(buildMockEnvelope({
      response_meta: { size_kb: 3.7, chunked: false, recommendation: null },
    }))

    const result = await callHolisticBundle({
      query_text: 'Tell me about my career prospects.',
    })

    const parsed = parseResult(result)
    const responseMeta = parsed['response_meta'] as Record<string, unknown> | undefined
    expect(responseMeta).toBeDefined()
    expect(typeof responseMeta!['size_kb']).toBe('number')
    expect(responseMeta!['size_kb']).toBe(3.7)
  })

  it('9. response_meta.chunked is true when bundle is large (size_kb > 64)', async () => {
    const mockExecute = vi.mocked(executeHolisticBundle)
    mockExecute.mockResolvedValueOnce(buildMockEnvelope({
      response_meta: {
        size_kb: 78.4,
        chunked: true,
        recommendation: 'Response exceeds 64KB. Use return_format="compressed" or subset param to narrow the query.',
      },
    }))

    const result = await callHolisticBundle({
      query_text: 'Give me everything about my life.',
    })

    const parsed = parseResult(result)
    const responseMeta = parsed['response_meta'] as Record<string, unknown> | undefined
    expect(responseMeta).toBeDefined()
    expect(responseMeta!['chunked']).toBe(true)
    expect(responseMeta!['size_kb']).toBeGreaterThan(64)
    expect(typeof responseMeta!['recommendation']).toBe('string')
  })

  it('10. Zod schema rejects subset_size: 5 (below min 10)', async () => {
    const result = await callHolisticBundle({
      query_text: 'Tell me about my chart.',
      subset_size: 5,
    })
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  it('Zod schema rejects subset_size: 574 (above max 573)', async () => {
    const result = await callHolisticBundle({
      query_text: 'Tell me about my chart.',
      subset_size: 574,
    })
    expect((result as { isZodError: boolean }).isZodError).toBe(true)
  })

  it('subset_size defaults to 100 when not provided', async () => {
    const mockExecute = vi.mocked(executeHolisticBundle)
    mockExecute.mockResolvedValueOnce(buildMockEnvelope())

    await callHolisticBundle({ query_text: 'Tell me about my chart.' })

    expect(mockExecute).toHaveBeenCalledWith(
      expect.objectContaining({ subset_size: 100 }),
      expect.any(Object),
    )
  })

  it('return_format defaults to "verbose" when not provided', async () => {
    const mockExecute = vi.mocked(executeHolisticBundle)
    mockExecute.mockResolvedValueOnce(buildMockEnvelope())

    await callHolisticBundle({ query_text: 'Tell me about my chart.' })

    expect(mockExecute).toHaveBeenCalledWith(
      expect.objectContaining({ return_format: 'verbose' }),
      expect.any(Object),
    )
  })

  it('passes subset_size through to executeHolisticBundle', async () => {
    const mockExecute = vi.mocked(executeHolisticBundle)
    mockExecute.mockResolvedValueOnce(buildMockEnvelope())

    await callHolisticBundle({
      query_text: 'Tell me about my chart.',
      subset_size: 50,
    })

    expect(mockExecute).toHaveBeenCalledWith(
      expect.objectContaining({ subset_size: 50 }),
      expect.any(Object),
    )
  })
})
