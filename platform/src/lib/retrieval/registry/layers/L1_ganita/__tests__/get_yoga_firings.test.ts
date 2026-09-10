/**
 * get_yoga_firings.test.ts — F-D1/F-D2 (L1_W1_ANALYSIS_BATCH_D.md).
 *
 * F-D1: classical citations exist for all firing yogas in
 * brahma_yoga_catalog.classical_citations (233/233 populated) but this
 * surface never joined them — citation_ref/citation_human on ga_yoga_firings
 * are deliberately the strength-derivation citation, not the classical one.
 *
 * F-D2: density_contract.paginated=true with no offset input and
 * MAX_LIMIT=50 against more live rows made rows beyond the first page
 * permanently unreachable.
 *
 * No live DB required — `query` is mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getYogaFiringsCapability } from '../get_yoga_firings'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('getYogaFiringsCapability — F-D1 classical citation join', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('joins brahma_yoga_catalog and selects catalog_classical_citations', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })

    await getYogaFiringsCapability.handler({ chart_id: CHART_ID }, undefined)

    const rowsSql = mockQuery.mock.calls[0][0] as string
    expect(rowsSql).toMatch(/LEFT JOIN brahma_yoga_catalog c ON c\.canonical_id = f\.yoga_canonical_id/)
    expect(rowsSql).toMatch(/c\.classical_citations AS catalog_classical_citations/)
  })

  it('reports catalog_classical_citations distinctly from citation_ref in provenance', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [{
        id: 1, yoga_canonical_id: 'ruchaka', citation_ref: 'ga_yoga.strength:ruchaka:...',
        catalog_classical_citations: [{ chapter: 75, text_id: 'bphs' }],
      }],
    })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })

    const result = await getYogaFiringsCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows[0]['catalog_classical_citations']).toEqual([{ chapter: 75, text_id: 'bphs' }])
    expect(rows[0]['citation_ref']).toBe('ga_yoga.strength:ruchaka:...')
    const provenance = content['provenance'] as Record<string, unknown>
    expect(provenance['tables']).toContain('brahma_yoga_catalog')
  })
})

describe('getYogaFiringsCapability — F-D2 offset paging', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('defaults offset to 0 and binds it as the final query parameter', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })

    await getYogaFiringsCapability.handler({ chart_id: CHART_ID }, undefined)

    const rowsSql = mockQuery.mock.calls[0][0] as string
    const rowsParams = mockQuery.mock.calls[0][1] as unknown[]
    expect(rowsSql).toMatch(/OFFSET \$\d+/)
    expect(rowsParams[rowsParams.length - 1]).toBe(0)
  })

  it('passes an explicit offset through to the query and the echoed filters', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '63' }] })

    const result = await getYogaFiringsCapability.handler({ chart_id: CHART_ID, offset: 50 }, undefined)

    const rowsParams = mockQuery.mock.calls[0][1] as unknown[]
    expect(rowsParams[rowsParams.length - 1]).toBe(50)

    const content = result.content as Record<string, unknown>
    const filters = content['filters'] as Record<string, unknown>
    expect(filters['offset']).toBe(50)
  })

  it('the F-D2 regression: rows 51-63 are reachable via offset=50, not silently dropped', async () => {
    // 13 rows on page 2 of a 63-row total (limit defaults to 50).
    const page2 = Array.from({ length: 13 }, (_, i) => ({ id: 51 + i }))
    mockQuery.mockResolvedValueOnce({ rows: page2 })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '63' }] })

    const result = await getYogaFiringsCapability.handler({ chart_id: CHART_ID, offset: 50 }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(13)
    expect(content['total_matching']).toBe(63)
    expect(content['more_available']).toBe(false)  // 63 > 50 + 13 is false — this page is the last
  })

  it('more_available accounts for offset, not just the current page size', async () => {
    const page1 = Array.from({ length: 50 }, (_, i) => ({ id: i }))
    mockQuery.mockResolvedValueOnce({ rows: page1 })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '63' }] })

    const result = await getYogaFiringsCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['more_available']).toBe(true)  // 63 > 0 + 50
  })
})
