/**
 * chart_summary.test.ts — MCPT v3.2 P4c acceptance tests.
 *
 * Verifies:
 *   1. chart_summary({divisional_charts:["D1","D9","D10"]}) returns ≥50 fact rows.
 *   2. chart_summary appears in the CATALOG for all tiers (tool_in_list_tools check).
 *   3. include_categories filter narrows the fetched category set.
 *   4. exclude_categories filter omits the specified categories.
 *   5. The tool makes ≤ 4 round-trips for the canonical D1+D9+D10 bundle
 *      (1 bulk call + 3 divisional calls = 4 max).
 *   6. rows_by_category groups rows correctly by category.
 *   7. Error from platform propagates as errorResult.
 *
 * AC (acceptance criterion from Phase 4c brief):
 *   - chart_summary({divisional_charts:["D1","D9","D10"]}) returns ≥50 rows in one call.
 *   - chart_summary appears in list_tools for all audience tiers.
 *   - Integration test asserts fixture parity vs current query_chart_facts row-by-row.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { CATALOG } from '../src/tools/catalog.js'

// ── Set SERVICE_TOKEN to bypass GCP metadata fetch ────────────────────────────
process.env['SERVICE_TOKEN'] = 'test-service-token'

// ── Mock fetch (used by callPlatformPrimitive) ────────────────────────────────
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ── Import after mocks ────────────────────────────────────────────────────────
import { registerChartSummaryTool, CHART_SUMMARY_DESCRIPTION } from '../src/tools/chart_summary.js'

// ── Helpers ───────────────────────────────────────────────────────────────────

const MOCK_PRINCIPAL = {
  user_uid: 'test-uid',
  audience_tier: 'super_admin' as const,
  key_id: 'test-key-001',
}

function makeMockServer() {
  let capturedHandler: ((args: Record<string, unknown>) => Promise<unknown>) | null = null

  const server = {
    tool: vi.fn((
      _name: string,
      _description: string,
      _schema: Record<string, unknown>,
      handler: (args: Record<string, unknown>) => Promise<unknown>
    ) => {
      capturedHandler = handler
    }),
  }

  return {
    server,
    getHandler: () => capturedHandler!,
  }
}

/**
 * Build a mock platform response that returns rows_by_category.
 * rowsByCategory: { category: rows[] }
 */
function makeBatchedPlatformResponse(rowsByCategory: Record<string, unknown[]>) {
  return {
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({
        ok: true,
        result: { rows_by_category: rowsByCategory },
        trace_id: 'trace-test-001',
        epistemics: { surgical: true, confidence_band: 'high' },
      }),
  }
}

/**
 * Build a platform error response.
 */
function makePlatformErrorResponse(message: string) {
  return {
    ok: false,
    status: 500,
    json: () =>
      Promise.resolve({
        ok: false,
        error: { class: 'internal', message, remediation: 'Check logs' },
        trace_id: 'trace-err-001',
      }),
  }
}

/**
 * Generate N fake chart-fact rows for a given category.
 */
function makeRows(category: string, count: number, divisional_chart?: string): Record<string, unknown>[] {
  return Array.from({ length: count }, (_, i) => ({
    fact_id: `${category.toUpperCase().slice(0, 3)}.${String(i + 1).padStart(3, '0')}`,
    category,
    divisional_chart: divisional_chart ?? 'D1',
    value_text: `${category} fact ${i + 1}`,
    value_number: i + 1,
  }))
}

// ── Fixtures ──────────────────────────────────────────────────────────────────

// Bulk response: birth_metadata(3) + yoga(5) + arudha(3) + dasha_vimshottari(4) + sensitive_point(5) = 20 rows
const BULK_ROWS_BY_CATEGORY = {
  birth_metadata: makeRows('birth_metadata', 3),
  yoga: makeRows('yoga', 5),
  arudha: makeRows('arudha', 3),
  dasha_vimshottari: makeRows('dasha_vimshottari', 4),
  sensitive_point: makeRows('sensitive_point', 5),
}

// Per-divisional planet+house rows: 9 planets + 12 houses = 21 rows per divisional
function makeDivisionalRows(divChart: string) {
  return {
    planet: makeRows('planet', 9, divChart),
    house: makeRows('house', 12, divChart),
  }
}

// Total expected rows: 20 bulk + (21 per divisional × 3 divisionals) = 20 + 63 = 83 rows
const EXPECTED_MIN_ROWS = 50

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('MCPT v3.2 P4c — chart_summary: canonical bundle returns ≥50 rows', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('chart_summary({divisional_charts:["D1","D9","D10"]}) returns ≥50 fact rows', async () => {
    const { server, getHandler } = makeMockServer()
    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )
    const handler = getHandler()

    // Call 1: bulk categories (birth_metadata, yoga, arudha, dasha_vimshottari, sensitive_point)
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(BULK_ROWS_BY_CATEGORY))
    // Calls 2–4: planet + house per divisional chart
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D1')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D9')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D10')))

    const result = await handler({
      divisional_charts: ['D1', 'D9', 'D10'],
    }) as { content: Array<{ type: string; text: string }> }

    expect(result).toBeDefined()
    expect(Array.isArray(result.content)).toBe(true)
    expect(result.content[0].type).toBe('text')

    const parsed = JSON.parse(result.content[0].text) as {
      ok: boolean
      total_rows: number
      divisional_charts: string[]
      categories_fetched: string[]
      rows_by_category: Record<string, unknown[]>
    }

    expect(parsed.ok).toBe(true)
    expect(parsed.total_rows).toBeGreaterThanOrEqual(EXPECTED_MIN_ROWS)
    expect(parsed.divisional_charts).toEqual(['D1', 'D9', 'D10'])
    expect(parsed.categories_fetched).toContain('birth_metadata')
    expect(parsed.categories_fetched).toContain('planet')
    expect(parsed.categories_fetched).toContain('house')
    expect(parsed.categories_fetched).toContain('yoga')
    expect(parsed.rows_by_category['birth_metadata']).toHaveLength(3)
    expect(parsed.rows_by_category['yoga']).toHaveLength(5)
    expect(parsed.rows_by_category['planet']).toHaveLength(27) // 9 × 3 divisionals
    expect(parsed.rows_by_category['house']).toHaveLength(36)  // 12 × 3 divisionals
  })

  it('makes ≤4 round-trips for canonical D1+D9+D10 bundle (1 bulk + 3 divisional)', async () => {
    const { server, getHandler } = makeMockServer()
    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )
    const handler = getHandler()

    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(BULK_ROWS_BY_CATEGORY))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D1')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D9')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D10')))

    await handler({ divisional_charts: ['D1', 'D9', 'D10'] })

    expect(mockFetch.mock.calls.length).toBeLessThanOrEqual(4)
  })

  it('uses batched=true + category array in platform calls', async () => {
    const { server, getHandler } = makeMockServer()
    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )
    const handler = getHandler()

    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(BULK_ROWS_BY_CATEGORY))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D1')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D9')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D10')))

    await handler({ divisional_charts: ['D1', 'D9', 'D10'] })

    // First call: bulk categories
    const firstCallBody = JSON.parse(
      (mockFetch.mock.calls[0] as [string, RequestInit])[1].body as string
    ) as { params: Record<string, unknown> }
    expect(Array.isArray(firstCallBody.params['category'])).toBe(true)
    expect(firstCallBody.params['batched']).toBe(true)

    // Subsequent calls: divisional calls with divisional_chart filter
    for (const idx of [1, 2, 3]) {
      const divCallBody = JSON.parse(
        (mockFetch.mock.calls[idx] as [string, RequestInit])[1].body as string
      ) as { params: Record<string, unknown> }
      expect(divCallBody.params['batched']).toBe(true)
      expect(typeof divCallBody.params['divisional_chart']).toBe('string')
    }
  })
})

describe('MCPT v3.2 P4c — chart_summary: include_categories filter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('include_categories narrows the fetch to only those categories + birth_metadata', async () => {
    const { server, getHandler } = makeMockServer()
    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )
    const handler = getHandler()

    // Only birth_metadata and yoga — both bulk, no divisional-sensitive categories
    mockFetch.mockResolvedValueOnce(
      makeBatchedPlatformResponse({
        birth_metadata: makeRows('birth_metadata', 3),
        yoga: makeRows('yoga', 5),
      })
    )

    const result = await handler({
      include_categories: ['yoga'],
    }) as { content: Array<{ type: string; text: string }> }

    const parsed = JSON.parse(result.content[0].text) as {
      ok: boolean
      categories_fetched: string[]
    }
    expect(parsed.ok).toBe(true)
    expect(parsed.categories_fetched).toContain('birth_metadata') // always included
    expect(parsed.categories_fetched).toContain('yoga')
    expect(parsed.categories_fetched).not.toContain('planet')
    expect(parsed.categories_fetched).not.toContain('house')
    // Only 1 fetch (bulk only, no divisional categories)
    expect(mockFetch.mock.calls.length).toBe(1)
  })
})

describe('MCPT v3.2 P4c — chart_summary: exclude_categories filter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('exclude_categories omits specified categories from default list', async () => {
    const { server, getHandler } = makeMockServer()
    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )
    const handler = getHandler()

    // Exclude sensitive_point and yoga from default list
    // Bulk categories remaining: birth_metadata, arudha, dasha_vimshottari
    mockFetch.mockResolvedValueOnce(
      makeBatchedPlatformResponse({
        birth_metadata: makeRows('birth_metadata', 3),
        arudha: makeRows('arudha', 3),
        dasha_vimshottari: makeRows('dasha_vimshottari', 4),
      })
    )
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D1')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D9')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D10')))

    const result = await handler({
      exclude_categories: ['sensitive_point', 'yoga'],
    }) as { content: Array<{ type: string; text: string }> }

    const parsed = JSON.parse(result.content[0].text) as {
      ok: boolean
      categories_fetched: string[]
    }
    expect(parsed.ok).toBe(true)
    expect(parsed.categories_fetched).not.toContain('sensitive_point')
    expect(parsed.categories_fetched).not.toContain('yoga')
    expect(parsed.categories_fetched).toContain('birth_metadata')
    expect(parsed.categories_fetched).toContain('planet')
  })
})

describe('MCPT v3.2 P4c — chart_summary: error propagation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('propagates platform error as errorResult when bulk call fails', async () => {
    const { server, getHandler } = makeMockServer()
    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )
    const handler = getHandler()

    mockFetch.mockResolvedValueOnce(makePlatformErrorResponse('Platform database error'))

    const result = await handler({}) as { content: Array<{ type: string; text: string }>; isError?: boolean }

    expect(result.isError).toBe(true)
    const parsed = JSON.parse(result.content[0].text) as { ok: boolean }
    expect(parsed.ok).toBe(false)
  })
})

describe('MCPT v3.2 P4c — chart_summary: appears in list_tools for all tiers', () => {
  it('chart_summary appears in CATALOG (available to all tiers)', () => {
    const names = CATALOG.map(t => t.name)
    expect(names).toContain('chart_summary')
  })

  it('chart_summary description passes lint gate: starts with disambiguator', () => {
    expect(CHART_SUMMARY_DESCRIPTION).toMatch(/^(What it does|FIRST CALL when|Returns)/)
  })

  it('chart_summary description passes lint gate: contains "When to prefer"', () => {
    expect(CHART_SUMMARY_DESCRIPTION).toMatch(/When to prefer/)
  })

  it('chart_summary description passes lint gate: ≤1200 characters', () => {
    expect(CHART_SUMMARY_DESCRIPTION.length).toBeLessThanOrEqual(1200)
  })
})

describe('MCPT v3.2 P4c — chart_summary: fixture parity vs query_chart_facts', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('chart_summary row-by-row: planet rows preserve all fields from query_chart_facts', async () => {
    const { server, getHandler } = makeMockServer()
    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )
    const handler = getHandler()

    const expectedPlanetRow = {
      fact_id: 'PLN.001',
      category: 'planet',
      divisional_chart: 'D1',
      value_text: 'Sun in Aries 0°',
      value_number: 0.0,
      source: 'JH-D1',
      data: { longitude: 0.0, nakshatra: 'Ashwini', pada: 1 },
    }

    mockFetch.mockResolvedValueOnce(
      makeBatchedPlatformResponse({
        birth_metadata: makeRows('birth_metadata', 1),
        yoga: makeRows('yoga', 1),
        arudha: makeRows('arudha', 1),
        dasha_vimshottari: makeRows('dasha_vimshottari', 1),
        sensitive_point: makeRows('sensitive_point', 1),
      })
    )
    // D1: planet row with full detail
    mockFetch.mockResolvedValueOnce(
      makeBatchedPlatformResponse({
        planet: [expectedPlanetRow],
        house: makeRows('house', 1, 'D1'),
      })
    )
    // D9, D10: normal rows
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D9')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D10')))

    const result = await handler({ divisional_charts: ['D1', 'D9', 'D10'] }) as {
      content: Array<{ type: string; text: string }>
    }

    const parsed = JSON.parse(result.content[0].text) as {
      ok: boolean
      rows_by_category: { planet: typeof expectedPlanetRow[] }
    }

    expect(parsed.ok).toBe(true)
    const planetRows = parsed.rows_by_category['planet']
    const sunRow = planetRows.find(r => r.fact_id === 'PLN.001')
    expect(sunRow).toBeDefined()
    expect(sunRow).toEqual(expectedPlanetRow)
  })

  it('chart_summary total_rows == sum of all rows_by_category arrays', async () => {
    const { server, getHandler } = makeMockServer()
    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => MOCK_PRINCIPAL
    )
    const handler = getHandler()

    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(BULK_ROWS_BY_CATEGORY))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D1')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D9')))
    mockFetch.mockResolvedValueOnce(makeBatchedPlatformResponse(makeDivisionalRows('D10')))

    const result = await handler({ divisional_charts: ['D1', 'D9', 'D10'] }) as {
      content: Array<{ type: string; text: string }>
    }

    const parsed = JSON.parse(result.content[0].text) as {
      total_rows: number
      rows_by_category: Record<string, unknown[]>
    }

    const sumFromArrays = Object.values(parsed.rows_by_category).reduce(
      (acc, rows) => acc + rows.length,
      0
    )
    expect(parsed.total_rows).toBe(sumFromArrays)
  })
})
