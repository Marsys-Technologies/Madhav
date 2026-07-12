/**
 * wp13e_temporal_date_honoring.test.ts — WP-1.3(e) serving-half contract tests
 * ============================================================================
 * get_temporal_windows / kala_windows_get route through query_temporal_activation.
 * This lane's serving-half deliverable:
 *   1. honor date params — range (date_from/date_to) AND point-in-time (as_of);
 *   2. ECHO the applied filter explicitly (date_filter object, always present);
 *   3. honest empty with a DISCLOSED reason — distinguish "no windows in range"
 *      from R-45 "awaiting WP-2.1 activation-date population" (PENDING-W3).
 *
 * The writer half (populating activation_start/activation_end) is WP-2.1 (W2);
 * these tests lock the serving contract so timing questions work once dates land.
 *
 * DB is mocked (vi.mock('@/lib/db/client')) — assertions are against the SQL/params
 * actually built and the response envelope, not live rows. [verify-against: prod]
 * for real row-count behavior (documented in the WP-1.3(e) report).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

import { queryTemporalActivationCapability } from '../layers/L3_kala/query_temporal_activation'

const CHART_ID = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'

const DATED_ROW = {
  id: 'act-1',
  signal_id: 'sig-1',
  ayanamsha_id: 'lahiri_chitrapaksha',
  signature_class: 'x',
  activation_start: '2020-01-01',
  activation_end: '2021-01-01',
  activation_peak_date: '2020-06-01',
  orb_strength: 0.9,
}

beforeEach(() => {
  queryMock.mockReset()
})

describe('WP-1.3(e) — as_of point-in-time honored', () => {
  it('builds a point-in-time clause (start<=as_of AND end>=as_of) and echoes it', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [DATED_ROW] }) // activation query
      .mockResolvedValueOnce({ rows: [] })          // predicates query
    const res = await queryTemporalActivationCapability.handler(
      { chart_id: CHART_ID, as_of: '2020-06-15' }, undefined,
    )
    const [sql, params] = queryMock.mock.calls[0] as [string, unknown[]]
    // param bound ::date so boundary instants match at calendar-date granularity
    expect(sql).toMatch(/activation_start <= \$\d+::date/)
    expect(sql).toMatch(/activation_end >= \$\d+::date/)
    expect(params).toContain('2020-06-15')

    const content = (res as { content: Record<string, unknown> }).content
    const df = content['date_filter'] as Record<string, unknown>
    expect(df['mode']).toBe('point_in_time')
    expect(df['as_of']).toBe('2020-06-15')
    expect(df['honored']).toBe(true)
  })
})

describe('WP-1.3(e) — range date params honored + echoed', () => {
  it('applies range overlap clauses and echoes an explicit date_filter (mode=range)', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [DATED_ROW] })
      .mockResolvedValueOnce({ rows: [] })
    const res = await queryTemporalActivationCapability.handler(
      { chart_id: CHART_ID, date_from: '2019-01-01', date_to: '2022-01-01' }, undefined,
    )
    const [sql, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toMatch(/activation_end >= \$/)
    expect(sql).toMatch(/activation_start <= \$/)
    expect(params).toContain('2019-01-01')
    expect(params).toContain('2022-01-01')

    const content = (res as { content: Record<string, unknown> }).content
    const df = content['date_filter'] as Record<string, unknown>
    expect(df['mode']).toBe('range')
    expect(df['date_from']).toBe('2019-01-01')
    expect(df['date_to']).toBe('2022-01-01')
    expect(df['range_defaulted']).toBe(false)
  })

  it('flags range_defaulted=true when neither date_from/date_to nor as_of is passed', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [DATED_ROW] })
      .mockResolvedValueOnce({ rows: [] })
    const res = await queryTemporalActivationCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = (res as { content: Record<string, unknown> }).content
    const df = content['date_filter'] as Record<string, unknown>
    expect(df['range_defaulted']).toBe(true)
  })
})

describe('WP-1.3(e) — date columns serialized as YYYY-MM-DD (no TZ shift)', () => {
  it('SELECTs the three date columns through to_char(..., YYYY-MM-DD), not raw', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [DATED_ROW] })
      .mockResolvedValueOnce({ rows: [] })
    await queryTemporalActivationCapability.handler({ chart_id: CHART_ID }, undefined)
    const [sql] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toMatch(/to_char\(activation_start,\s*'YYYY-MM-DD'\)\s+AS activation_start/)
    expect(sql).toMatch(/to_char\(activation_end,\s*'YYYY-MM-DD'\)\s+AS activation_end/)
    expect(sql).toMatch(/to_char\(activation_peak_date,\s*'YYYY-MM-DD'\)\s+AS activation_peak_date/)
    // no bare "activation_start," projection that would let node-pg parse a JS Date
    expect(sql).not.toMatch(/SELECT[^)]*\bactivation_start,\s*activation_end,\s*activation_peak_date\b/)
  })
})

describe('WP-1.3(e) — honest empty with disclosed reason', () => {
  it('R-45 / PENDING-W3: rows exist but none dated → awaiting_activation_dates reason', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [] }) // activation query → empty
      .mockResolvedValueOnce({ rows: [{ total: 13364, dated: 0 }] }) // disclosure count
    const res = await queryTemporalActivationCapability.handler(
      { chart_id: CHART_ID, date_from: '2026-01-01', date_to: '2027-01-01' }, undefined,
    )
    const content = (res as { content: Record<string, unknown> }).content
    expect(content['activation_count']).toBe(0)
    expect(content['awaiting_activation_dates']).toBe(true)
    const reason = content['empty_reason'] as string
    expect(reason).toMatch(/PENDING-W3/)
    expect(reason).toMatch(/WP-2\.1/)
    expect(reason).toMatch(/13364/)
  })

  it('genuine out-of-window: dated rows exist but none overlap → widen-window reason', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ total: 13369, dated: 84 }] })
    const res = await queryTemporalActivationCapability.handler(
      { chart_id: CHART_ID, date_from: '1900-01-01', date_to: '1901-01-01' }, undefined,
    )
    const content = (res as { content: Record<string, unknown> }).content
    expect(content['awaiting_activation_dates']).toBe(false)
    const reason = content['empty_reason'] as string
    expect(reason).toMatch(/84/)
    expect(reason).not.toMatch(/PENDING-W3/)
  })

  it('no rows at all for chart/ayanamsha → not-built reason', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ total: 0, dated: 0 }] })
    const res = await queryTemporalActivationCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = (res as { content: Record<string, unknown> }).content
    const reason = content['empty_reason'] as string
    expect(reason).toMatch(/No activation rows/)
    expect(content['awaiting_activation_dates']).toBe(false)
  })

  it('non-empty result → empty_reason is null, no disclosure count query', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [DATED_ROW] })
      .mockResolvedValueOnce({ rows: [] }) // predicates
    const res = await queryTemporalActivationCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = (res as { content: Record<string, unknown> }).content
    expect(content['empty_reason']).toBeNull()
    expect(content['awaiting_activation_dates']).toBe(false)
    // exactly 2 queries: activation + predicates (no disclosure count)
    expect(queryMock.mock.calls.length).toBe(2)
  })
})
