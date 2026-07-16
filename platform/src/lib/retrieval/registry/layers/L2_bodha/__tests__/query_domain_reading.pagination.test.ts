/**
 * query_domain_reading.pagination.test.ts — D-1.5b Lane B-6 (item 2, response budget) unit
 * tests for the question-lens pagination fix on bodha_domain_reading_get. No live DB
 * required — `query` is mocked. All DB-backed collaborators (fetchL1Context,
 * hydrateSignalText, deriveDefect001Note) resolve to their empty/degrade-gracefully paths
 * by keeping every mocked row set empty, so the test stays focused on the pagination wiring.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryDomainReadingCapability } from '../query_domain_reading'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('queryDomainReadingCapability (bodha_domain_reading_get) — lens pagination', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    // Default: every call returns zero rows — computeDiscriminatedSignals bails out early
    // (pool_size 0) rather than reaching into fetchL1Context/applyCompositeRanking, and
    // hydrateSignalText/deriveDefect001Note degrade to their empty paths. Keeps this test
    // scoped to the pagination wiring, not the whole synthesis pipeline.
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('applies LIMIT/OFFSET to the lens query and discloses a genuine total via lens_pagination', async () => {
    // Call order (Promise.all, array-literal order): lensRes, lensCountRes, cdlmRes, discriminated's query.
    mockQuery.mockResolvedValueOnce({ rows: [] })                 // lensRes (page)
    mockQuery.mockResolvedValueOnce({ rows: [{ n: 137 }] })       // lensCountRes (true family size)

    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'career', lens_limit: 25, lens_offset: 10 }, undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const pagination = content['lens_pagination'] as Record<string, unknown>
    expect(pagination['offset']).toBe(10)
    expect(pagination['limit']).toBe(25)
    expect(pagination['total']).toBe(137)
    expect(pagination['more_available']).toBe(true)

    const lensSql = mockQuery.mock.calls[0][0] as string
    expect(lensSql).toMatch(/LIMIT \$\d+ OFFSET \$\d+/)
    const lensParams = mockQuery.mock.calls[0][1] as unknown[]
    expect(lensParams).toContain(25)
    expect(lensParams).toContain(10)
  })

  it('defaults lens_limit to 60 and lens_offset to 0 when omitted', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ n: 0 }] })

    const result = await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'wealth' }, undefined,
    )
    const content = result.content as Record<string, unknown>
    const pagination = content['lens_pagination'] as Record<string, unknown>
    expect(pagination['limit']).toBe(60)
    expect(pagination['offset']).toBe(0)
    expect(pagination['total']).toBe(0)
    expect(pagination['more_available']).toBe(false)
  })

  it('clamps lens_limit to the documented ceiling (200)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ n: 0 }] })

    await queryDomainReadingCapability.handler(
      { chart_id: CHART_ID, domain: 'health', lens_limit: 999 }, undefined,
    )
    const lensParams = mockQuery.mock.calls[0][1] as unknown[]
    expect(lensParams).toContain(200)
  })
})

/**
 * D-1.5b Lane B-7 (Gate B B7_budgets) — per-lens ranked_signals bound. The live defect:
 * bodha_domain_reading_get(domain=wealth) returned 909,221 bytes because each of its 2
 * question lenses carried its FULL relevance family (1,637 rows) inside
 * all_relevant_ranked_jsonb.ranked_signals — a section 2 levels deep that the MCP auto-budget
 * trimmer cannot reach and that Lane B-6's lens_limit (lens FAMILY size) never touched.
 */
describe('queryDomainReadingCapability (bodha_domain_reading_get) — per-lens ranked_signals budget (B-7)', () => {
  // Build a lens whose ranked_signals family is `n` rows, mirroring the live shape
  // ({ ranked_signals: [...], total_count }) each row carrying a realistic text payload.
  const bigLens = (question_type: string, n: number) => ({
    lens_id: `lens_${question_type}`,
    question_type,
    template_element_ids_jsonb: [],
    all_relevant_ranked_jsonb: {
      total_count: n,
      ranked_signals: Array.from({ length: n }, (_v, i) => ({
        signal_id: `sig_${question_type}_${i}`,
        computed_salience: 0.5,
        // ~200 bytes of filler per row, approximating a stored ranked_signal row.
        summary_stub: 'x'.repeat(180),
      })),
    },
    lens_template_version: 'v1',
    points_only_assertion: null,
    verification_pass_status: 'pass',
    computed_at: '2026-07-16T00:00:00Z',
  })

  const runWealth = async (args: Record<string, unknown>) => {
    // Call order (Promise.all): lensRes, lensCountRes, cdlmRes, computeDiscriminatedSignals' query.
    mockQuery.mockReset()
    mockQuery.mockResolvedValueOnce({ rows: [bigLens('wealth', 1637), bigLens('property', 1637)] }) // lensRes
    mockQuery.mockResolvedValueOnce({ rows: [{ n: 2 }] })   // lensCountRes
    mockQuery.mockResolvedValueOnce({ rows: [] })            // cdlmRes
    mockQuery.mockResolvedValue({ rows: [] })                // discriminated + hydration + defect001
    return queryDomainReadingCapability.handler({ chart_id: CHART_ID, domain: 'wealth', ...args }, undefined)
  }

  it('bounds each lens to 25 ranked_signals by default and discloses the true family size', async () => {
    const result = await runWealth({})
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const lenses = content['question_lenses'] as Array<Record<string, unknown>>
    expect(lenses).toHaveLength(2)
    for (const lens of lenses) {
      const arj = lens['all_relevant_ranked_jsonb'] as Record<string, unknown>
      const ranked = arj['ranked_signals'] as unknown[]
      expect(ranked.length).toBe(25)              // capped
      expect(lens['ranked_signals_total']).toBe(1637)  // true family size disclosed
      expect(lens['ranked_signals_capped']).toBe(true)
      expect(arj['total_count']).toBe(1637)
    }
    expect(content['ranked_signals_per_lens_cap']).toBe(25)
  })

  it('the DEFAULT response is bounded well under the ~100KB Gate B budget', async () => {
    const result = await runWealth({})
    const bytes = Buffer.byteLength(JSON.stringify(result.content), 'utf8')
    // Pre-fix this same content serialized to 909,221 bytes live. Assert an order-of-
    // magnitude cut and a hard ceiling comfortably under the ~100KB (102,400B) gate.
    expect(bytes).toBeLessThan(100 * 1024)
  })

  it('clamps max_signals_per_lens to its ceiling (100) and honors an explicit value', async () => {
    const r1 = await runWealth({ max_signals_per_lens: 50 })
    const l1 = (r1.content as Record<string, unknown>)['question_lenses'] as Array<Record<string, unknown>>
    expect(((l1[0]['all_relevant_ranked_jsonb'] as Record<string, unknown>)['ranked_signals'] as unknown[]).length).toBe(50)

    const r2 = await runWealth({ max_signals_per_lens: 999 })
    const l2 = (r2.content as Record<string, unknown>)['question_lenses'] as Array<Record<string, unknown>>
    expect(((l2[0]['all_relevant_ranked_jsonb'] as Record<string, unknown>)['ranked_signals'] as unknown[]).length).toBe(100)
  })

  it('response_format=full raises the per-lens cap to 200', async () => {
    const result = await runWealth({ response_format: 'full' })
    const lenses = (result.content as Record<string, unknown>)['question_lenses'] as Array<Record<string, unknown>>
    const ranked = (lenses[0]['all_relevant_ranked_jsonb'] as Record<string, unknown>)['ranked_signals'] as unknown[]
    expect(ranked.length).toBe(200)
    expect((result.content as Record<string, unknown>)['ranked_signals_per_lens_cap']).toBe(200)
  })
})
