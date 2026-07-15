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
