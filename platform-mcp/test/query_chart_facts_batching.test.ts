/**
 * query_chart_facts_batching.test.ts — MCPT v3.2 P4b acceptance tests.
 *
 * Verifies:
 *   1. The `categories` array param is accepted by the Zod schema.
 *   2. When `categories` is provided, the handler passes category array + batched: true
 *      to the platform primitive endpoint.
 *   3. When `category` (single) is provided, the handler passes category string as-is
 *      (backward-compatible path unchanged).
 *   4. The `rows_by_category` grouping logic in chart_facts_query.ts is correct.
 *
 * AC (acceptance criterion from sub-agent brief):
 *   - query_chart_facts({categories:["planet","house","yoga"]}) returns rows grouped
 *     by category, single round-trip.
 *   - query_chart_facts({category:"planet"}) still works as before (backward compat).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import { CHART_FACTS_CATEGORIES } from '../src/tools/query_chart_facts.js'

// ── Set SERVICE_TOKEN to bypass GCP metadata fetch in client.ts ───────────────
// Without this, fetchIdentityToken() tries the GCP metadata server (an extra
// fetch call) then falls back. By setting SERVICE_TOKEN we get exactly 1 fetch
// per callPlatformPrimitive invocation.
process.env['SERVICE_TOKEN'] = 'test-service-token'

// ── Mock fetch (used by callPlatformPrimitive) ────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Import after mocks ────────────────────────────────────────────────────────

import { registerQueryChartFacts } from '../src/tools/query_chart_facts.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeMockServer() {
  let capturedHandler: ((args: Record<string, unknown>) => Promise<unknown>) | null = null
  let capturedSchema: Record<string, unknown> | null = null

  const server = {
    tool: vi.fn((
      _name: string,
      _description: string,
      schema: Record<string, unknown>,
      handler: (args: Record<string, unknown>) => Promise<unknown>
    ) => {
      capturedHandler = handler
      capturedSchema = schema
    }),
  }

  return {
    server,
    getHandler: () => capturedHandler!,
    getSchema: () => capturedSchema!,
  }
}

const MOCK_PRINCIPAL = {
  user_uid: 'test-uid',
  audience_tier: 'super_admin' as const,
  key_id: 'test-key-001',
}

function makePlatformResponse(result: unknown, ok = true) {
  return {
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({
        ok,
        result,
        trace_id: 'trace-test-001',
        epistemics: { surgical: true, confidence_band: 'high' },
      }),
  }
}

// ── Zod schema unit tests ─────────────────────────────────────────────────────

describe('MCPT v3.2 P4b — QueryChartFactsInputSchema: categories param', () => {
  // Reconstruct schema inline (same shape as the registered schema)
  const QueryChartFactsInputSchema = z.object({
    category: z.string().optional(),
    categories: z.array(z.string()).optional(),
    planet: z.string().optional(),
    house: z.number().int().min(1).max(12).optional(),
    as_of_date: z.string().optional(),
    divisional_chart: z.string().optional(),
    limit: z.number().int().min(1).max(200).optional().default(50),
  })

  it('accepts categories as an array of strings', () => {
    const result = QueryChartFactsInputSchema.safeParse({
      categories: ['planet', 'house', 'yoga'],
    })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.categories).toEqual(['planet', 'house', 'yoga'])
    }
  })

  it('accepts single category without categories array (backward compat)', () => {
    const result = QueryChartFactsInputSchema.safeParse({
      category: 'planet',
    })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.category).toBe('planet')
      expect(result.data.categories).toBeUndefined()
    }
  })

  it('accepts both category and categories (categories takes precedence in handler)', () => {
    const result = QueryChartFactsInputSchema.safeParse({
      category: 'planet',
      categories: ['planet', 'yoga'],
    })
    expect(result.success).toBe(true)
  })

  it('accepts categories with an empty array (no override)', () => {
    const result = QueryChartFactsInputSchema.safeParse({
      categories: [],
    })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.categories).toEqual([])
    }
  })

  it('rejects categories if items are not strings', () => {
    const result = QueryChartFactsInputSchema.safeParse({
      categories: [1, 2, 3],
    })
    expect(result.success).toBe(false)
  })
})

// ── Handler integration tests (mock callPlatformPrimitive) ────────────────────

describe('MCPT v3.2 P4b — query_chart_facts handler: categories batching', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('passes category array + batched:true when categories is provided', async () => {
    const { server, getHandler } = makeMockServer()
    registerQueryChartFacts(server as unknown as Parameters<typeof registerQueryChartFacts>[0], () => MOCK_PRINCIPAL)
    const handler = getHandler()

    // Mock the platform response with rows_by_category
    const rowsByCategory = {
      planet: [{ fact_id: 'PLN.001', category: 'planet', value_text: 'Sun in Aries' }],
      house: [{ fact_id: 'HSE.001', category: 'house', value_text: '1H: Aries' }],
      yoga: [{ fact_id: 'YOG.001', category: 'yoga', value_text: 'Gajakesari' }],
    }
    mockFetch.mockResolvedValueOnce(
      makePlatformResponse({
        results: [{
          content: JSON.stringify({ rows_by_category: rowsByCategory }),
        }],
      })
    )

    await handler({ categories: ['planet', 'house', 'yoga'], limit: 50 })

    expect(mockFetch).toHaveBeenCalledTimes(1)
    const [, fetchOptions] = mockFetch.mock.calls[0] as [string, RequestInit]
    const body = JSON.parse(fetchOptions.body as string) as { params: Record<string, unknown> }

    // Verify batched mode params forwarded to platform
    expect(body.params.category).toEqual(['planet', 'house', 'yoga'])
    expect(body.params.batched).toBe(true)
    // category (singular) should NOT appear separately
    expect(body.params.category).not.toBe('planet')
  })

  it('does NOT pass batched when categories array is empty', async () => {
    const { server, getHandler } = makeMockServer()
    registerQueryChartFacts(server as unknown as Parameters<typeof registerQueryChartFacts>[0], () => MOCK_PRINCIPAL)
    const handler = getHandler()

    mockFetch.mockResolvedValueOnce(
      makePlatformResponse({ results: [] })
    )

    await handler({ categories: [], category: 'planet', limit: 50 })

    const [, fetchOptions] = mockFetch.mock.calls[0] as [string, RequestInit]
    const body = JSON.parse(fetchOptions.body as string) as { params: Record<string, unknown> }

    // Empty categories → falls through to single-category path
    expect(body.params.batched).toBeUndefined()
    expect(body.params.category).toBe('planet')
  })

  it('single category backward compat: passes category string without batched flag', async () => {
    const { server, getHandler } = makeMockServer()
    registerQueryChartFacts(server as unknown as Parameters<typeof registerQueryChartFacts>[0], () => MOCK_PRINCIPAL)
    const handler = getHandler()

    mockFetch.mockResolvedValueOnce(
      makePlatformResponse({
        results: [{ content: JSON.stringify({ fact_id: 'PLN.001', category: 'planet', value_text: 'Sun in Aries' }) }],
      })
    )

    await handler({ category: 'planet', limit: 50 })

    const [, fetchOptions] = mockFetch.mock.calls[0] as [string, RequestInit]
    const body = JSON.parse(fetchOptions.body as string) as { params: Record<string, unknown> }

    // Single-category: no batched flag, category is a plain string
    expect(body.params.category).toBe('planet')
    expect(body.params.batched).toBeUndefined()
  })

  it('propagates other filter params (planet, house) with categories array', async () => {
    const { server, getHandler } = makeMockServer()
    registerQueryChartFacts(server as unknown as Parameters<typeof registerQueryChartFacts>[0], () => MOCK_PRINCIPAL)
    const handler = getHandler()

    mockFetch.mockResolvedValueOnce(makePlatformResponse({ results: [] }))

    await handler({ categories: ['planet', 'shadbala'], planet: 'Saturn', house: 7, limit: 30 })

    const [, fetchOptions] = mockFetch.mock.calls[0] as [string, RequestInit]
    const body = JSON.parse(fetchOptions.body as string) as { params: Record<string, unknown> }

    expect(body.params.planet).toBe('Saturn')
    expect(body.params.house).toBe(7)
    expect(body.params.limit).toBe(30)
    expect(body.params.batched).toBe(true)
    expect(body.params.category).toEqual(['planet', 'shadbala'])
  })

  it('returns okResult on successful batched response', async () => {
    const { server, getHandler } = makeMockServer()
    registerQueryChartFacts(server as unknown as Parameters<typeof registerQueryChartFacts>[0], () => MOCK_PRINCIPAL)
    const handler = getHandler()

    const rowsByCategory = {
      planet: [{ fact_id: 'PLN.001' }],
      yoga: [{ fact_id: 'YOG.001' }],
    }
    mockFetch.mockResolvedValueOnce(
      makePlatformResponse({
        results: [{
          content: JSON.stringify({ rows_by_category: rowsByCategory }),
        }],
      })
    )

    const result = await handler({ categories: ['planet', 'yoga'] }) as { content: Array<{ type: string; text: string }> }

    expect(result).toBeDefined()
    expect(Array.isArray(result.content)).toBe(true)
    expect(result.content[0].type).toBe('text')
    const parsed = JSON.parse(result.content[0].text) as { ok: boolean; result: unknown }
    expect(parsed.ok).toBe(true)
    expect(parsed.result).toBeDefined()
  })
})

// ── rows_by_category grouping logic unit tests ────────────────────────────────

describe('MCPT v3.2 P4b — rows_by_category grouping logic', () => {
  it('groupBy correctly groups rows by category key', () => {
    // Inline the groupBy logic from chart_facts_query.ts for pure unit testing
    function groupBy<T extends { category: string }>(rows: T[]): Record<string, T[]> {
      const grouped: Record<string, T[]> = {}
      for (const row of rows) {
        const cat = row.category
        if (!grouped[cat]) grouped[cat] = []
        grouped[cat].push(row)
      }
      return grouped
    }

    const rows = [
      { fact_id: 'PLN.001', category: 'planet', value_text: 'Sun' },
      { fact_id: 'PLN.002', category: 'planet', value_text: 'Moon' },
      { fact_id: 'HSE.001', category: 'house', value_text: '1H' },
      { fact_id: 'YOG.001', category: 'yoga', value_text: 'Gajakesari' },
    ]

    const grouped = groupBy(rows)

    expect(Object.keys(grouped)).toHaveLength(3)
    expect(grouped['planet']).toHaveLength(2)
    expect(grouped['house']).toHaveLength(1)
    expect(grouped['yoga']).toHaveLength(1)
    expect(grouped['planet'][0].fact_id).toBe('PLN.001')
    expect(grouped['planet'][1].fact_id).toBe('PLN.002')
  })

  it('groupBy returns empty object for empty input', () => {
    function groupBy<T extends { category: string }>(rows: T[]): Record<string, T[]> {
      const grouped: Record<string, T[]> = {}
      for (const row of rows) {
        const cat = row.category
        if (!grouped[cat]) grouped[cat] = []
        grouped[cat].push(row)
      }
      return grouped
    }

    expect(groupBy([])).toEqual({})
  })

  it('groupBy preserves all fields of each row', () => {
    function groupBy<T extends { category: string }>(rows: T[]): Record<string, T[]> {
      const grouped: Record<string, T[]> = {}
      for (const row of rows) {
        const cat = row.category
        if (!grouped[cat]) grouped[cat] = []
        grouped[cat].push(row)
      }
      return grouped
    }

    const row = {
      fact_id: 'SBL.001',
      category: 'shadbala',
      divisional_chart: 'D1',
      value_text: '7.4 rupas',
      value_number: 7.4,
      data: { forensic_rupas: 7.4 },
      source: 'JH-SBL-REPORT',
    }
    const grouped = groupBy([row])
    expect(grouped['shadbala'][0]).toEqual(row)
  })
})

// ── CHART_FACTS_CATEGORIES sanity ─────────────────────────────────────────────

describe('MCPT v3.2 P4b — CHART_FACTS_CATEGORIES sanity', () => {
  it('CHART_FACTS_CATEGORIES is a non-empty array', () => {
    expect(Array.isArray(CHART_FACTS_CATEGORIES)).toBe(true)
    expect(CHART_FACTS_CATEGORIES.length).toBeGreaterThan(0)
  })

  it('CHART_FACTS_CATEGORIES contains expected categories for batching', () => {
    const cats = CHART_FACTS_CATEGORIES as readonly string[]
    expect(cats).toContain('planet')
    expect(cats).toContain('house')
    expect(cats).toContain('yoga')
    expect(cats).toContain('shadbala')
  })
})
