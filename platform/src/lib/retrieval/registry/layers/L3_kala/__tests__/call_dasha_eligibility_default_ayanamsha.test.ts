/**
 * call_dasha_eligibility_default_ayanamsha.test.ts — N1-A DEFECT-2 regression.
 *
 * call_dasha_eligibility (ka_dasha_kala) used to default `ayanamsha_id` to the literal
 * `'lahiri'` while every other ayanamsha-bearing handler in this file (call_ephemeris_at_t,
 * call_priority_ranking) defaults to the project canonical `DEFAULT_AYANAMSHA` constant
 * (`'lahiri_chitrapaksha'`, `platform/src/lib/retrieval/registry/constants.ts`). Since
 * `chart_dashas` rows are stored under `lahiri_chitrapaksha`, a caller omitting
 * `ayanamsha_id` silently got zero rows instead of an error. Proves the fixed default
 * resolves to the canonical value and is what actually reaches the SQL query params.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (sql: string, params: unknown[]) => queryMock(sql, params) }))

vi.mock('@/lib/ganita/dasha_eligibility_store', async importOriginal => {
  const actual = await importOriginal<typeof import('@/lib/ganita/dasha_eligibility_store')>()
  return { ...actual, readDashaEligibilityWindows: vi.fn(actual.readDashaEligibilityWindows) }
})

import { applyAyanamshaContractForCapability } from '@/lib/retrieval/chart_facts_helpers'
import { readDashaEligibilityWindows } from '@/lib/ganita/dasha_eligibility_store'
import { callDashaEligibilityCapability } from '../call_service_wrappers'
import { DEFAULT_AYANAMSHA } from '../../../constants'

type Handler = (a: Record<string, unknown>, c?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
const handler = callDashaEligibilityCapability.handler as Handler

describe('call_dasha_eligibility — default ayanamsha_id', () => {
  beforeEach(() => {
    vi.mocked(readDashaEligibilityWindows).mockClear()
    queryMock.mockReset()
    queryMock.mockResolvedValue({ rows: [] })
  })

  it('defaults to the canonical DEFAULT_AYANAMSHA, not the literal "lahiri"', async () => {
    expect(DEFAULT_AYANAMSHA).toBe('lahiri_chitrapaksha')

    const result = await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa' }, undefined)

    expect(result.is_error).toBeFalsy()
    expect(result.content['ayanamsha_id']).toBe(DEFAULT_AYANAMSHA)

    expect(queryMock).toHaveBeenCalled()
    const [, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(params[1]).toBe(DEFAULT_AYANAMSHA)
  })

  it('still honors an explicit ayanamsha_id override', async () => {
    const result = await handler(
      { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', ayanamsha_id: 'raman' },
      undefined,
    )
    expect(result.content['ayanamsha_id']).toBe('raman')
    const [, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(params[1]).toBe('raman')
  })
})


describe('call_dasha_eligibility — typed store boundary', () => {
  const args = {
    chart_id: 'fixture-chart',
    ayanamsha_id: 'fixture-variant',
    date_from: '2030-01-01',
    date_to: '2030-12-31',
  }

  beforeEach(() => {
    vi.mocked(readDashaEligibilityWindows).mockClear()
    queryMock.mockReset()
    queryMock.mockResolvedValue({ rows: [] })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('delegates once to the owner with all effective inputs and one query', async () => {
    await handler({ ...args, target_lords: ['SUN', 'MOON'] })
    expect(readDashaEligibilityWindows).toHaveBeenCalledExactlyOnceWith({
      ...args,
      target_lords: ['SUN', 'MOON'],
    })
    expect(queryMock).toHaveBeenCalledTimes(1)
    expect(queryMock.mock.calls[0][1]).toEqual([
      args.chart_id, args.ayanamsha_id, args.date_from, args.date_to, 'SUN', 'MOON',
    ])
  })

  it('retains the exact SQL frame, inclusive overlap, ordering and row cap', async () => {
    await handler(args)
    const [sql, params] = queryMock.mock.calls[0]
    expect(sql).toBe(`SELECT
           dasha_row_id, system_id, level_n,
           lord_graha, lord_sign, parent_row_id,
           to_char(start_date, 'YYYY-MM-DD') AS start_date,
           to_char(end_date, 'YYYY-MM-DD')   AS end_date,
           start_iso, end_iso,
           kp_sublevel, kp_sub_lord
         FROM chart_dashas
         WHERE chart_id = $1 AND ayanamsha_id = $2
           AND end_date >= $3 AND start_date <= $4
           ${''}
         ORDER BY start_date, system_id, level_n
         LIMIT 400`)
    expect(params).toEqual([args.chart_id, args.ayanamsha_id, args.date_from, args.date_to])
  })

  it('binds every optional lord in order including duplicates and SQL-looking text', async () => {
    const target_lords = ['MOON', "fixture' OR TRUE --", 'MOON']
    await handler({ ...args, target_lords })
    const [sql, params] = queryMock.mock.calls[0]
    expect(sql).toContain('AND lord_graha IN ($5, $6, $7)')
    expect(sql).not.toContain(target_lords[1])
    expect(params).toEqual([
      args.chart_id, args.ayanamsha_id, args.date_from, args.date_to, ...target_lords,
    ])
  })

  it('preserves normalized all defaulting and direct raw all binding separately', async () => {
    const normalized = applyAyanamshaContractForCapability(callDashaEligibilityCapability, {
      chart_id: args.chart_id, ayanamsha_id: 'all',
    })
    expect(normalized).toEqual({ chart_id: args.chart_id, ayanamsha_scope: 'all' })
    await handler(normalized)
    expect(queryMock.mock.calls[0][1][1]).toBe(DEFAULT_AYANAMSHA)
    await handler({ ...args, ayanamsha_id: 'all' })
    expect(queryMock.mock.calls[1][1][1]).toBe('all')
    expect(readDashaEligibilityWindows).toHaveBeenNthCalledWith(2, {
      ...args, ayanamsha_id: 'all', target_lords: [],
    })
  })

  it('preserves helper-normalized aliases and direct literal aliases separately', async () => {
    const normalized = applyAyanamshaContractForCapability(callDashaEligibilityCapability, {
      ...args, ayanamsha_id: 'LAHIRI',
    })
    await handler(normalized)
    expect(queryMock.mock.calls[0][1][1]).toBe(DEFAULT_AYANAMSHA)
    await handler({ ...args, ayanamsha_id: 'lahiri' })
    expect(queryMock.mock.calls[1][1][1]).toBe('lahiri')
  })

  it('passes nullable stored instants through without conversion', async () => {
    const rows = [{
      dasha_row_id: 'fixture-null-instants', system_id: 'fixture-system', level_n: 1,
      lord_graha: 'SUN', lord_sign: null, parent_row_id: null,
      start_date: '2030-01-01', end_date: '2030-12-31',
      start_iso: null, end_iso: null, kp_sublevel: null, kp_sub_lord: null,
    }]
    queryMock.mockResolvedValueOnce({ rows })
    const result = await handler(args)
    expect(result.content.dasha_windows).toBe(rows)
    expect(result.content.cross_system_windows).toEqual([
      { ...rows[0], system_agreement_count: 1, agreeing_systems: ['fixture-system'] },
    ])
  })

  it('retains empty-lord all semantics without a fifth bind', async () => {
    const result = await handler({ ...args, target_lords: [] })
    expect(result.content.target_lords).toBe('all')
    expect(queryMock.mock.calls[0][0]).not.toContain('lord_graha IN')
    expect(queryMock.mock.calls[0][1]).toHaveLength(4)
  })

  it('keeps chart validation before owner or query access', async () => {
    expect(await handler({})).toEqual({
      content: { error: 'chart_id is required' }, is_error: true,
    })
    expect(readDashaEligibilityWindows).not.toHaveBeenCalled()
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('computes omitted date inputs at the existing handler boundary', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2030-03-04T12:00:00.000Z'))
    const date_to = new Date(Date.now() + 3 * 365 * 86400000).toISOString().split('T')[0]
    const result = await handler({ chart_id: args.chart_id })
    expect(readDashaEligibilityWindows).toHaveBeenCalledExactlyOnceWith({
      chart_id: args.chart_id,
      ayanamsha_id: DEFAULT_AYANAMSHA,
      date_from: '2030-03-04',
      date_to,
      target_lords: [],
    })
    expect(result.content.date_from).toBe('2030-03-04')
    expect(result.content.date_to).toBe(date_to)
  })

  it('preserves raw row identity, DATE text, timestamp strings and stable agreement mapping', async () => {
    const first = {
      dasha_row_id: 'fixture-row-a', system_id: 'zeta', level_n: 2,
      lord_graha: 'SUN', lord_sign: null, parent_row_id: null,
      start_date: '2030-01-01', end_date: '2030-02-01',
      start_iso: '2030-01-01T00:00:00+05:30', end_iso: '2030-02-01T00:00:00+05:30',
      kp_sublevel: null, kp_sub_lord: null,
    }
    const rows = [
      first,
      { ...first, dasha_row_id: 'fixture-row-b', system_id: 'alpha' },
      { ...first, dasha_row_id: 'fixture-row-c', system_id: 'alpha' },
      { ...first, dasha_row_id: 'fixture-row-d', start_date: '2030-02-02' },
      { ...first, dasha_row_id: 'fixture-row-e', start_date: '2030-03-03' },
    ]
    queryMock.mockResolvedValueOnce({ rows })
    const result = await handler(args)
    expect(result.content.dasha_windows).toBe(rows)
    expect(result.content.count).toBe(5)
    expect(result.content.high_agreement_count).toBe(1)
    expect(result.content.cross_system_windows).toEqual([
      { ...first, system_agreement_count: 2, agreeing_systems: ['alpha', 'zeta'] },
      { ...rows[3], system_agreement_count: 1, agreeing_systems: ['zeta'] },
      { ...rows[4], system_agreement_count: 1, agreeing_systems: ['zeta'] },
    ])
    expect(first.start_date).toBe('2030-01-01')
    expect(first.start_iso).toBe('2030-01-01T00:00:00+05:30')
  })

  it('preserves the existing empty result and error mapping', async () => {
    const empty = await handler(args)
    expect(empty.content.dasha_windows).toEqual([])
    expect(empty.content.cross_system_windows).toEqual([])
    expect(empty.content.count).toBe(0)
    expect(empty.is_error).toBe(false)
    queryMock.mockRejectedValueOnce(new Error('fixture-query-failure'))
    expect(await handler(args)).toEqual({
      content: { error: 'Error: fixture-query-failure', chart_id: args.chart_id },
      is_error: true,
    })
  })

  it('allows direct typed owner reads without registration or output transformation', async () => {
    const rows = [{ fixture: 'untransformed-row' }]
    queryMock.mockResolvedValueOnce({ rows })
    expect(await readDashaEligibilityWindows({ ...args, target_lords: [] })).toBe(rows)
    expect(queryMock).toHaveBeenCalledTimes(1)
  })
})
