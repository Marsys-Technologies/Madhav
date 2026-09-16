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
    start_iso: `2000-01-0${id.charCodeAt(0) - 96}T00:00:00.000Z`,
  }
}

function args(overrides: Record<string, unknown> = {}) {
  return {
    chart_id: CHART_ID,
    limit: 2,
    fields: 'all',
    window_start: '2000-01-01',
    window_end: '2100-01-01',
    ...overrides,
  }
}

function mockBuildPages(state: {
  activeBuild: string | null
  availableBuilds: Set<string>
  rowsByBuild: Record<string, readonly Record<string, unknown>[]>
}) {
  const pageCalls: Array<{ params: readonly unknown[]; sql: string }> = []
  queryMock.mockImplementation((sql: string, params: unknown[] = []) => {
    if (typeof sql !== 'string') return Promise.resolve({ rows: [] })
    if (sql.includes('FROM build_runs')) return Promise.resolve({ rows: state.activeBuild ? [{ build_id: state.activeBuild }] : [] })
    if (sql.includes('snapshot_available')) return Promise.resolve({ rows: state.availableBuilds.has(String(params[1])) ? [{ snapshot_available: true }] : [] })
    if (sql.startsWith('SELECT * FROM chart_dashas')) {
      const buildId = String(params.at(-1))
      const offset = Number(params[2])
      const fetchLimit = Number(params[1])
      pageCalls.push({ sql, params })
      return Promise.resolve({ rows: (state.rowsByBuild[buildId] ?? []).slice(offset, offset + fetchLimit) })
    }
    if (sql.startsWith('SELECT MAX(level_n)')) return Promise.resolve({ rows: [{ max_level: 3 }] })
    throw new Error(`unexpected query: ${sql}`)
  })
  return { pageCalls }
}

describe('get_dashas build-pinned cursor pagination', () => {
  beforeEach(() => queryMock.mockReset())

  it('pins first, middle, and final pages to one completed build without duplicate progression', async () => {
    const state = {
      activeBuild: 'build-a',
      availableBuilds: new Set(['build-a']),
      rowsByBuild: { 'build-a': [dasha('a'), dasha('b'), dasha('c'), dasha('d'), dasha('e')] },
    }
    const database = mockBuildPages(state)

    const first = (await getDashasCapability.handler(args(), undefined)).content as Record<string, unknown>
    const middle = (await getDashasCapability.handler(args({ page_cursor: first.next_page_cursor }), undefined)).content as Record<string, unknown>
    const final = (await getDashasCapability.handler(args({ page_cursor: middle.next_page_cursor }), undefined)).content as Record<string, unknown>
    const served = [first, middle, final].flatMap((content) => (content.rows as Array<Record<string, unknown>>).map((row) => row.dasha_row_id))

    expect(served).toEqual(['a', 'b', 'c', 'd', 'e'])
    expect(new Set(served).size).toBe(served.length)
    expect([first.more_available, middle.more_available, final.more_available]).toEqual([true, true, false])
    expect([first.next_offset, middle.next_offset, final.next_offset]).toEqual([2, 4, null])
    expect([first.next_page_cursor, middle.next_page_cursor, final.next_page_cursor]).toEqual([expect.any(String), expect.any(String), null])
    expect(database.pageCalls.map((call) => [call.params[2], call.params.at(-1)])).toEqual([[0, 'build-a'], [2, 'build-a'], [4, 'build-a']])
    expect(database.pageCalls.every((call) => call.sql.includes('build_id'))).toBe(true)
  })

  it('marks a first-page empty filter as exhausted only after confirming the active build snapshot', async () => {
    mockBuildPages({ activeBuild: 'build-a', availableBuilds: new Set(['build-a']), rowsByBuild: { 'build-a': [] } })

    const result = await getDashasCapability.handler(args(), undefined)

    expect(result).toMatchObject({
      is_error: false,
      content: { build_id: 'build-a', rows: [], total: 0, more_available: false, next_page_cursor: null },
    })
  })

  it('rejects fractional and huge finite pagination before issuing SQL, while safely flooring usable values', async () => {
    mockBuildPages({ activeBuild: 'build-a', availableBuilds: new Set(['build-a']), rowsByBuild: { 'build-a': [dasha('a')] } })

    for (const invalid of [{ limit: 0.5 }, { limit: Number.POSITIVE_INFINITY }, { offset: 1_000_001 }]) {
      queryMock.mockClear()
      const result = await getDashasCapability.handler(args(invalid), undefined)
      expect(result).toMatchObject({ is_error: true, content: { code: 'invalid_pagination', restart_required: true } })
      expect(queryMock).not.toHaveBeenCalled()
    }

    const result = await getDashasCapability.handler(args({ limit: 3.9, offset: 1.9 }), undefined)
    expect(result).toMatchObject({ is_error: true, content: { code: 'page_cursor_required', restart_required: true } })
    expect(queryMock).not.toHaveBeenCalled()

    const firstPageResult = await getDashasCapability.handler(args({ limit: 3.9 }), undefined)
    expect(firstPageResult.is_error).toBe(false)
    const pageCall = queryMock.mock.calls.find(([sql]) => String(sql).startsWith('SELECT * FROM chart_dashas'))!
    expect(pageCall[1]).toEqual(expect.arrayContaining([CHART_ID, 4, 0]))
  })

  it('denies a cursor replay when a query filter changes instead of serving another family', async () => {
    const state = {
      activeBuild: 'build-a', availableBuilds: new Set(['build-a']),
      rowsByBuild: { 'build-a': [dasha('a'), dasha('b'), dasha('c')] },
    }
    const database = mockBuildPages(state)
    const first = (await getDashasCapability.handler(args(), undefined)).content as Record<string, unknown>
    const result = await getDashasCapability.handler(args({ system: 'yogini', page_cursor: first.next_page_cursor }), undefined)

    expect(result).toMatchObject({ is_error: true, content: { code: 'page_cursor_filter_mismatch', restart_required: true } })
    expect(database.pageCalls).toHaveLength(1)
  })

  it('requires restart rather than falsely exhausting after a completed-build transition or missing pinned snapshot', async () => {
    const state = {
      activeBuild: 'build-a', availableBuilds: new Set(['build-a']),
      rowsByBuild: { 'build-a': [dasha('a'), dasha('b'), dasha('c')], 'build-b': [dasha('x')] },
    }
    const database = mockBuildPages(state)
    const first = (await getDashasCapability.handler(args(), undefined)).content as Record<string, unknown>

    state.activeBuild = 'build-b'
    const rebuilt = await getDashasCapability.handler(args({ page_cursor: first.next_page_cursor }), undefined)
    expect(rebuilt).toMatchObject({ is_error: true, content: { code: 'page_cursor_build_changed', restart_required: true } })
    expect(database.pageCalls).toHaveLength(1)

    state.activeBuild = 'build-a'
    state.availableBuilds.delete('build-a')
    const unavailable = await getDashasCapability.handler(args({ page_cursor: first.next_page_cursor }), undefined)
    expect(unavailable).toMatchObject({ is_error: true, content: { code: 'page_cursor_snapshot_unavailable', restart_required: true } })
    expect(database.pageCalls).toHaveLength(1)
  })
})
