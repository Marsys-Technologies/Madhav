import { beforeEach, describe, expect, it, vi } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))

import { getDashasCapability } from '../get_dashas'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function dasha(id: string) {
  return {
    dasha_row_id: id,
    system_id: 'vimshottari',
    ayanamsha_id: 'lahiri_chitrapaksha',
    start_date: '2000-01-01',
    start_iso: '2000-01-01T00:00:00.000Z',
  }
}

function mockPage(rows: readonly Record<string, unknown>[]) {
  queryMock.mockImplementation((sql: string) => {
    if (typeof sql !== 'string') return Promise.resolve({ rows: [] })
    if (sql.startsWith('SELECT * FROM chart_dashas')) return Promise.resolve({ rows })
    if (sql.startsWith('SELECT MAX(level_n)')) return Promise.resolve({ rows: [{ max_level: 3 }] })
    throw new Error(`unexpected query: ${sql}`)
  })
}

function args(overrides: Record<string, unknown> = {}) {
  return {
    chart_id: CHART_ID,
    limit: 2,
    offset: 0,
    fields: 'all',
    window_start: '2000-01-01',
    window_end: '2100-01-01',
    ...overrides,
  }
}

describe('get_dashas truthful offset pagination', () => {
  beforeEach(() => queryMock.mockReset())

  it('fetches one extra row, returns only the requested page, and discloses its continuation', async () => {
    mockPage([dasha('a'), dasha('b'), dasha('c')])

    const result = await getDashasCapability.handler(args(), undefined)
    const content = result.content as Record<string, unknown>

    expect(result.is_error).toBe(false)
    expect((content.rows as Array<Record<string, unknown>>).map((row) => row.dasha_row_id)).toEqual(['a', 'b'])
    expect(content).toMatchObject({ total: 2, more_available: true, next_offset: 2 })
    const [pageSql, pageParams] = queryMock.mock.calls[0]!
    expect(pageSql).toContain('ORDER BY system_id ASC, ayanamsha_id ASC, start_date ASC, level_n ASC, start_iso ASC, dasha_row_id ASC LIMIT $2 OFFSET $3')
    expect(pageParams).toEqual(expect.arrayContaining([CHART_ID, 3, 0]))
    expect(queryMock.mock.calls.every(([sql]) => typeof sql === 'string')).toBe(true)
    expect(queryMock.mock.calls.some(([sql]) => String(sql).includes('COUNT('))).toBe(false)
  })

  it('uses a stable continuation without duplicate progression through middle and final pages', async () => {
    const pages = [
      [dasha('a'), dasha('b'), dasha('c')],
      [dasha('c'), dasha('d'), dasha('e')],
      [dasha('e')],
    ]
    let call = 0
    queryMock.mockImplementation((sql: string) => {
      if (typeof sql !== 'string') return Promise.resolve({ rows: [] })
      if (sql.startsWith('SELECT * FROM chart_dashas')) return Promise.resolve({ rows: pages[call++] })
      if (sql.startsWith('SELECT MAX(level_n)')) return Promise.resolve({ rows: [{ max_level: 3 }] })
      throw new Error(`unexpected query: ${sql}`)
    })

    const first = (await getDashasCapability.handler(args({ offset: 0 }), undefined)).content as Record<string, unknown>
    const middle = (await getDashasCapability.handler(args({ offset: 2 }), undefined)).content as Record<string, unknown>
    const final = (await getDashasCapability.handler(args({ offset: 4 }), undefined)).content as Record<string, unknown>
    const served = [first, middle, final].flatMap((content) => (content.rows as Array<Record<string, unknown>>).map((row) => row.dasha_row_id))

    expect(served).toEqual(['a', 'b', 'c', 'd', 'e'])
    expect(new Set(served).size).toBe(served.length)
    expect([first.next_offset, middle.next_offset, final.next_offset]).toEqual([2, 4, null])
    expect([first.more_available, middle.more_available, final.more_available]).toEqual([true, true, false])
  })

  it('normalizes invalid, nonfinite, and fractional pagination arguments safely', async () => {
    for (const [limit, offset, expectedFetchLimit, expectedOffset] of [
      [Number.NaN, Number.NaN, 201, 0],
      [Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY, 201, 0],
      [-1, -5, 201, 0],
      [3.9, 1.9, 4, 1],
      [5000, 2, 1001, 2],
    ]) {
      mockPage([])
      await getDashasCapability.handler(args({ limit, offset }), undefined)
      expect(queryMock.mock.calls[0]![1]).toEqual(expect.arrayContaining([CHART_ID, expectedFetchLimit, expectedOffset]))
      queryMock.mockReset()
    }
  })

  it('marks an empty page as exhausted without a continuation', async () => {
    mockPage([])

    const result = await getDashasCapability.handler(args({ offset: 50 }), undefined)

    expect(result.content).toMatchObject({ rows: [], total: 0, more_available: false, next_offset: null })
  })
})
