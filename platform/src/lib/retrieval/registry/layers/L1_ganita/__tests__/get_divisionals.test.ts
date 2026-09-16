/**
 * get_divisionals.test.ts — Task D1 receipt-grade offset pagination.
 *
 * The production change these tests protect: returning a page-sized `total`
 * (or no continuation marker) can cause Inquiry to close while matching rows
 * remain. The handler must use its server-observed limit-plus-one result to
 * expose whether another page exists.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getDivisionalsCapability } from '../get_divisionals'
import { getCatalog } from '../../../catalog'
import { compileCapabilityKnowledge } from '../../../knowledge/compiler'
import { deriveInquiryPaginationReceipt } from '@/lib/vidhi/inquiry/pagination'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function row(id: string) {
  return { id, varga: 'D9', ayanamsha_id: 'lahiri', graha: 'Sun', fact_category: 'varga_position', fact_key: id }
}

function contentOf(result: Awaited<ReturnType<typeof getDivisionalsCapability.handler>>) {
  return result.content as Record<string, unknown>
}

function divisionalBinding() {
  const snapshot = compileCapabilityKnowledge(getCatalog(), '2026-09-16T20:40:27.000Z')
  const binding = snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.get_divisionals')
    ?.bindings.find((candidate) => candidate.relation === 'primary')
  if (!binding) throw new Error('missing reviewed divisional binding')
  return binding
}

describe('getDivisionalsCapability — Task D1 receipt-grade pagination', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('marks an initial full page as partial from a server-observed extra row', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row('first'), row('second'), row('third')] })

    const result = await getDivisionalsCapability.handler({ chart_id: CHART_ID, limit: 2 }, undefined)
    const content = contentOf(result)

    expect(result.is_error).toBe(false)
    expect(content['rows']).toEqual([row('first'), row('second')])
    expect(content['more_available']).toBe(true)
    expect(content).not.toHaveProperty('total')
    expect(mockQuery).toHaveBeenCalledTimes(1)
    expect(mockQuery.mock.calls[0]).toEqual(expect.arrayContaining([
      expect.stringMatching(/ORDER BY varga, ayanamsha_id, graha, fact_category, fact_key/),
      [CHART_ID, 3, 0],
    ]))
  })

  it('marks a final short page as exhausted without inventing a total', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row('last')] })

    const result = await getDivisionalsCapability.handler({ chart_id: CHART_ID, limit: 2 }, undefined)
    const content = contentOf(result)

    expect(result.is_error).toBe(false)
    expect(content['rows']).toEqual([row('last')])
    expect(content['more_available']).toBe(false)
    expect(content['next_offset']).toBeNull()
    expect(content).not.toHaveProperty('total')
  })

  it('reports an empty filtered page as exhausted using the same parameterized query', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })

    const result = await getDivisionalsCapability.handler(
      { chart_id: CHART_ID, varga: 'D60', graha: 'Moon', limit: 2 },
      undefined,
    )
    const content = contentOf(result)
    const [sql, params] = mockQuery.mock.calls[0] as [string, unknown[]]

    expect(result.is_error).toBe(false)
    expect(content['rows']).toEqual([])
    expect(content['more_available']).toBe(false)
    expect(sql).toContain('varga = $4')
    expect(sql).toContain('graha = $5')
    expect(params).toEqual([CHART_ID, 3, 0, 'D60', 'Moon'])
  })

  it('keeps the requested offset while probing one row beyond the page', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row('fifth'), row('sixth'), row('seventh')] })

    const result = await getDivisionalsCapability.handler(
      { chart_id: CHART_ID, offset: 4, limit: 2 },
      undefined,
    )
    const content = contentOf(result)

    expect(result.is_error).toBe(false)
    expect(content['rows']).toEqual([row('fifth'), row('sixth')])
    expect(content['more_available']).toBe(true)
    expect(mockQuery.mock.calls[0][1]).toEqual([CHART_ID, 3, 4])
  })

  it('uses the server default page size for an omitted-limit continuation receipt', async () => {
    mockQuery.mockResolvedValueOnce({ rows: Array.from({ length: 301 }, (_, index) => row(`default-${index}`)) })

    const args = { chart_id: CHART_ID }
    const result = await getDivisionalsCapability.handler(args, undefined)

    expect(contentOf(result)['next_offset']).toBe(300)
    expect(deriveInquiryPaginationReceipt(divisionalBinding(), result, args))
      .toEqual({ semantics: 'offset', exhausted: false, next: 300 })
  })

  it('uses the server-clamped page size for an oversized-limit continuation receipt', async () => {
    mockQuery.mockResolvedValueOnce({ rows: Array.from({ length: 2001 }, (_, index) => row(`clamped-${index}`)) })

    const args = { chart_id: CHART_ID, offset: 100, limit: 5000 }
    const result = await getDivisionalsCapability.handler(args, undefined)

    expect(contentOf(result)['next_offset']).toBe(2100)
    expect(deriveInquiryPaginationReceipt(divisionalBinding(), result, args))
      .toEqual({ semantics: 'offset', exhausted: false, next: 2100 })
  })

  it('normalizes a zero limit to a progressing one-row continuation', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row('zero-first'), row('zero-second')] })

    const args = { chart_id: CHART_ID, limit: 0 }
    const result = await getDivisionalsCapability.handler(args, undefined)

    expect(mockQuery.mock.calls[0][1]).toEqual([CHART_ID, 2, 0])
    expect(contentOf(result)['rows']).toEqual([row('zero-first')])
    expect(contentOf(result)['next_offset']).toBe(1)
    expect(deriveInquiryPaginationReceipt(divisionalBinding(), result, args))
      .toEqual({ semantics: 'offset', exhausted: false, next: 1 })
  })

  it('normalizes a negative limit to a progressing one-row continuation', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row('negative-first'), row('negative-second')] })

    const args = { chart_id: CHART_ID, offset: 4, limit: -10 }
    const result = await getDivisionalsCapability.handler(args, undefined)

    expect(mockQuery.mock.calls[0][1]).toEqual([CHART_ID, 2, 4])
    expect(contentOf(result)['rows']).toEqual([row('negative-first')])
    expect(contentOf(result)['next_offset']).toBe(5)
    expect(deriveInquiryPaginationReceipt(divisionalBinding(), result, args))
      .toEqual({ semantics: 'offset', exhausted: false, next: 5 })
  })

  it.each([
    ['NaN', Number.NaN],
    ['Infinity', Number.POSITIVE_INFINITY],
  ])('uses the default page size for a non-finite %s limit', async (_label, limit) => {
    mockQuery.mockResolvedValueOnce({ rows: Array.from({ length: 301 }, (_, index) => row(`non-finite-${index}`)) })

    const args = { chart_id: CHART_ID, limit }
    const result = await getDivisionalsCapability.handler(args, undefined)

    expect(mockQuery.mock.calls[0][1]).toEqual([CHART_ID, 301, 0])
    expect(contentOf(result)['rows']).toHaveLength(300)
    expect(contentOf(result)['next_offset']).toBe(300)
    expect(deriveInquiryPaginationReceipt(divisionalBinding(), result, args))
      .toEqual({ semantics: 'offset', exhausted: false, next: 300 })
  })
})
