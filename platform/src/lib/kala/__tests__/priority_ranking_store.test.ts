import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({
  query: (sql: string, params: unknown[]) => queryMock(sql, params),
}))
vi.mock('@/lib/kala/priority_ranking_store', async importOriginal => {
  const actual = await importOriginal<typeof import('@/lib/kala/priority_ranking_store')>()
  return { ...actual, readPriorityRankingRows: vi.fn(actual.readPriorityRankingRows) }
})

import { readPriorityRankingRows, type PriorityRankingRow } from '@/lib/kala/priority_ranking_store'
import { callPriorityRankingCapability } from '@/lib/retrieval/registry/layers/L3_kala/call_service_wrappers'
import { DEFAULT_AYANAMSHA } from '@/lib/retrieval/registry/constants'
import {
  ABSTENTION_MARKER_PATTERNS,
  CATALOG_ONLY_MARKER_PATTERNS,
} from '@/lib/retrieval/signal_glossary'

type Handler = (args: Record<string, unknown>, context?: unknown) => Promise<{
  content: Record<string, unknown>
  is_error?: boolean
}>
const handler = callPriorityRankingCapability.handler as Handler
const request = {
  chart_id: 'fixture-chart',
  ayanamsha_id: 'fixture-variant',
  date_from: '2030-01-01',
  date_to: '2030-04-01',
  domain_filter: null,
  top_k: 20,
}
const served: PriorityRankingRow = {
  signal_id: 'fixture-signal-a',
  signal_headline_text: 'fixture unmapped headline',
  priority_score: 10,
  neutral_dignity_downranked: false,
  abstention_marker_pattern: null,
  catalog_only_marker_pattern: null,
  partition_rank: '1',
  pre_exclusion_rank: '1',
  fixture_extra: { preserved: true },
}
let rows: PriorityRankingRow[]
let events: string[]
let fetchMock: ReturnType<typeof vi.fn>

beforeEach(() => {
  rows = []
  events = []
  queryMock.mockReset()
  vi.mocked(readPriorityRankingRows).mockClear()
  queryMock.mockImplementation(async (_sql: string, params: unknown[]) => {
    if (params.length === 3) {
      events.push('snapshot')
      return { rows: [{ snapshots: 1, windows: [{ window_id: 'window-a' }, { window_id: 'window-b' }] }] }
    }
    events.push('ranking')
    return { rows }
  })
  vi.stubEnv('PYTHON_SIDECAR_URL', 'https://fixture.invalid')
  vi.stubEnv('PYTHON_SIDECAR_API_KEY', 'fixture-key')
  fetchMock = vi.fn(async (_url: unknown, options: { body: string }) => {
    events.push('comparison')
    const body = JSON.parse(options.body) as Record<string, unknown>
    return {
      ok: true,
      status: 200,
      json: async () => ({
        contract_version: 'k7-4:pareto:v1',
        ordered: ['window-a', 'window-b'],
        front: ['window-a', 'window-b'],
        comparisons: [],
        evidence: { 'window-a': {}, 'window-b': {} },
        rejected: [],
        order_policy: [
          ...(Object.hasOwn(body, 'question_frame') ? ['best_suited'] : []),
          'most_robust', 'strongest', 'nearest',
        ],
        empty_reason: null,
      }),
    }
  })
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

describe('typed Kala ranking read owner', () => {
  it('returns raw rows and preserves seven default-domain bindings', async () => {
    rows = [served]
    expect(await readPriorityRankingRows(request)).toBe(rows)
    expect(queryMock).toHaveBeenCalledTimes(1)
    expect(queryMock.mock.calls[0][1]).toEqual([
      request.chart_id, request.ayanamsha_id, request.date_from, request.date_to,
      ABSTENTION_MARKER_PATTERNS, CATALOG_ONLY_MARKER_PATTERNS, request.top_k,
    ])
    expect(queryMock.mock.calls[0][1][4]).toBe(ABSTENTION_MARKER_PATTERNS)
    expect(queryMock.mock.calls[0][1][5]).toBe(CATALOG_ONLY_MARKER_PATTERNS)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('binds an explicit domain array once ahead of both marker partitions and top K', async () => {
    const domains = ['career', 'career', 'home']
    await readPriorityRankingRows({ ...request, domain_filter: domains, top_k: 1 })
    expect(queryMock.mock.calls[0][1]).toEqual([
      request.chart_id, request.ayanamsha_id, request.date_from, request.date_to,
      domains, ABSTENTION_MARKER_PATTERNS, CATALOG_ONLY_MARKER_PATTERNS, 1,
    ])
    expect(queryMock.mock.calls[0][1][4]).toBe(domains)
  })

  it('preserves empty-domain query shape and bindings as the null-domain case', async () => {
    await readPriorityRankingRows(request)
    await readPriorityRankingRows({ ...request, domain_filter: [] })
    expect(queryMock.mock.calls[1]).toEqual(queryMock.mock.calls[0])
  })

  it('propagates the exact query error for the existing descriptor catch', async () => {
    const failure = new Error('fixture query failure')
    queryMock.mockRejectedValueOnce(failure)
    await expect(readPriorityRankingRows(request)).rejects.toBe(failure)
  })
})

describe('registered ranking descriptor delegates its ranking read', () => {
  it('calls the typed owner once after snapshot/comparison and before serving mapping', async () => {
    rows = [served]
    const result = await handler({ ...request, domain: 'CaReEr', domains: ['ignored'], top_k: '1' })
    expect(result.is_error).toBe(false)
    expect(readPriorityRankingRows).toHaveBeenCalledExactlyOnceWith({
      ...request, domain_filter: ['career'], top_k: 1,
    })
    expect(events).toEqual(['snapshot', 'comparison', 'ranking'])
    expect(queryMock).toHaveBeenCalledTimes(2)
    expect(queryMock.mock.calls[0][1]).toEqual([request.chart_id, ['career'], request.date_to])
    expect(result.content.ordered_windows).toEqual(['window-a'])
    expect(result.content.front_members_omitted).toBe(1)
  })

  it('retains default dates and frame, and literal all on a direct call', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2030-03-04T12:00:00.000Z'))
    await handler({ chart_id: request.chart_id })
    expect(readPriorityRankingRows).toHaveBeenNthCalledWith(1, {
      chart_id: request.chart_id,
      ayanamsha_id: DEFAULT_AYANAMSHA,
      date_from: '2030-03-04',
      date_to: new Date(Date.parse('2030-03-04') + 90 * 86400000).toISOString().split('T')[0],
      domain_filter: null,
      top_k: 20,
    })
    await handler({ ...request, ayanamsha_id: 'all' })
    expect(queryMock.mock.calls[3][1][1]).toBe('all')
  })

  it('keeps domain-array coercion, order and duplicates', async () => {
    await handler({ ...request, domains: ['CaReEr', 123, null, 'CaReEr'] })
    expect(readPriorityRankingRows).toHaveBeenCalledExactlyOnceWith({
      ...request, domain_filter: ['career', '123', 'null', 'career'],
    })
  })

  it('preserves question/preference forwarding and legacy row order, nulls and exclusions', async () => {
    rows = [
      { ...served, neutral_dignity_downranked: true },
      { ...served, signal_id: 'fixture-signal-b', signal_headline_text: null, priority_score: null, catalog_only_marker_pattern: '' },
      { ...served, signal_id: 'fixture-excluded', abstention_marker_pattern: 'fixture-marker', pre_exclusion_rank: '3' },
      { ...served, signal_id: 'fixture-signal-a', signal_headline_text: null },
    ]
    const result = await handler({ ...request, question_frame: { fixture: true }, preference: { nearest: true } })
    const body = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(body.question_frame).toEqual({ fixture: true })
    expect(body.preference).toEqual({ nearest: true })
    const signals = result.content.ranked_signals as Array<Record<string, unknown>>
    expect(signals.map(row => row.signal_id)).toEqual(['fixture-signal-a', 'fixture-signal-b', 'fixture-signal-a'])
    expect(signals[0].fixture_extra).toEqual({ preserved: true })
    expect(signals[1].priority_score).toBeNull()
    expect(signals[1].catalog_only_unverified).toBe(true)
    expect(signals.every(row => row.legacy_scalar === true)).toBe(true)
    expect(signals.every(row => !('partition_rank' in row) && !('pre_exclusion_rank' in row))).toBe(true)
    expect(result.content.signal_id_refs).toEqual(['fixture-signal-a', 'fixture-signal-b'])
    expect(result.content.excluded_internal_marker_count).toBe(1)
    expect(result.content.excluded_internal_markers).toEqual([{
      signal_id: 'fixture-excluded', signal_headline_text: served.signal_headline_text,
      matched_pattern: 'fixture-marker', priority_score: 10, pre_exclusion_rank: 3,
      exclusion_reason: 'internal_computation_abstention_marker',
    }])
    expect(result.content.neutral_dignity_downranked_count).toBe(1)
    expect(result.content.legacy_scalar).toBe(true)
  })

  it.each([
    {},
    { ...request, date_from: '2030-02-30' },
    { ...request, date_to: request.date_from },
    { ...request, date_to: '2029-01-01' },
    { ...request, top_k: 0 },
    { ...request, top_k: 1.5 },
    { ...request, top_k: 101 },
  ])('refuses invalid effective inputs before any read or service call %#', async args => {
    expect((await handler(args)).is_error).toBe(true)
    expect(readPriorityRankingRows).not.toHaveBeenCalled()
    expect(queryMock).not.toHaveBeenCalled()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('does not issue the ranking read after an invalid snapshot', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    expect((await handler(request)).is_error).toBe(true)
    expect(queryMock).toHaveBeenCalledTimes(1)
    expect(fetchMock).not.toHaveBeenCalled()
    expect(readPriorityRankingRows).not.toHaveBeenCalled()
  })

  it('keeps snapshot, comparison and ranking error boundaries', async () => {
    queryMock.mockRejectedValueOnce(new Error('fixture snapshot failure'))
    expect((await handler(request)).content.error).toBe('Error: fixture snapshot failure')
    expect(readPriorityRankingRows).not.toHaveBeenCalled()
    fetchMock.mockRejectedValueOnce(new Error('fixture comparison failure'))
    expect((await handler(request)).content.error).toBe('Error: fixture comparison failure')
    expect(readPriorityRankingRows).not.toHaveBeenCalled()
    queryMock.mockImplementationOnce(async () => ({ rows: [{ snapshots: 1, windows: [{ window_id: 'window-a' }, { window_id: 'window-b' }] }] }))
    queryMock.mockRejectedValueOnce(new Error('fixture ranking failure'))
    expect(await handler(request)).toEqual({
      content: { error: 'Error: fixture ranking failure', chart_id: request.chart_id },
      is_error: true,
    })
  })
})
