/**
 * query_sky_calendar — L0-W2 NOW item 14 substrate reader.
 * Covers the interval-filter semantics and the honest-empty/disclaimer discipline,
 * mirroring query_muhurta_lattice.test.ts's coverage shape for its sibling capability.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { querySkyCalendarCapability } from '../query_sky_calendar'

const START = '2026-08-05T00:00:00Z'
const END = '2026-08-06T00:00:00Z'

function row(over: Record<string, unknown> = {}) {
  return {
    event_type: 'ingress',
    primary_body: 'Jupiter',
    secondary_body: null,
    event_datetime_utc: '2026-08-05T12:00:00Z',
    sign: 'Gemini',
    nakshatra: 'Mrigashira',
    longitude_deg: 60.0,
    speed_dps: 0.08,
    detail: { target_sign: 'Gemini' },
    ayanamsha_key: 'lahiri',
    sampling_method: 'pyswisseph_bisection',
    source_citation: 'pyswisseph DE441 (Swiss Ephemeris); Lahiri ayanamsha',
    ...over,
  }
}

describe('querySkyCalendarCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('filters on event_datetime_utc >= start AND < end, param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row()] })
    await querySkyCalendarCapability.handler({ start_utc: START, end_utc: END }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('event_datetime_utc >= $1')
    expect(sql).toContain('event_datetime_utc < $2')
    expect(sql).toContain('FROM bg_sky_events')
    expect(params[0]).toBe(START)
    expect(params[1]).toBe(END)
  })

  it('counts rows per event_type', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [row(), row({ event_type: 'station', primary_body: 'Mars' }), row({ event_type: 'station', primary_body: 'Saturn' })],
    })
    const result = await querySkyCalendarCapability.handler({ start_utc: START, end_utc: END }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(3)
    expect(content['event_type_counts']).toEqual({ ingress: 1, station: 2 })
  })

  it('carries an honest empty_reason naming the rolling-horizon cause', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await querySkyCalendarCapability.handler({ start_utc: START, end_utc: END }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('rolling forward horizon')
  })

  it('rejects a missing/unparseable interval and an inverted one, without touching the DB', async () => {
    for (const args of [
      {},
      { start_utc: 'not-a-date', end_utc: END },
      { start_utc: END, end_utc: START },
    ]) {
      const result = await querySkyCalendarCapability.handler(args as Record<string, unknown>, undefined)
      expect(result.is_error).toBe(true)
    }
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('rejects an unknown event_type rather than silently returning everything', async () => {
    const result = await querySkyCalendarCapability.handler(
      { start_utc: START, end_utc: END, event_type: 'not_a_type' }, undefined,
    )
    expect(result.is_error).toBe(true)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('accepts all five event families', async () => {
    for (const type of ['ingress', 'station', 'eclipse_solar', 'eclipse_lunar', 'double_transit']) {
      mockQuery.mockResolvedValueOnce({ rows: [] })
      const result = await querySkyCalendarCapability.handler(
        { start_utc: START, end_utc: END, event_type: type }, undefined,
      )
      expect(result.is_error).toBe(false)
    }
    expect(mockQuery).toHaveBeenCalledTimes(5)
  })

  it('filters on primary_body when supplied', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row()] })
    await querySkyCalendarCapability.handler({ start_utc: START, end_utc: END, primary_body: 'Jupiter' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('primary_body = $3')
    expect(params).toContain('Jupiter')
  })

  it('caps limit and reports truncation honestly', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row(), row({ primary_body: 'Saturn' })] })
    const result = await querySkyCalendarCapability.handler(
      { start_utc: START, end_utc: END, limit: 2 }, undefined,
    )
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(params[params.length - 1]).toBe(2)
    expect((result.content as Record<string, unknown>)['truncated']).toBe(true)
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await querySkyCalendarCapability.handler({ start_utc: START, end_utc: END }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id, and no native identifiers in the description', () => {
    expect(querySkyCalendarCapability.scope).toBe('global')
    expect(querySkyCalendarCapability.required_inputs).not.toContain('chart_id')
    expect(querySkyCalendarCapability.description).not.toContain('Bhubaneswar')
    expect(querySkyCalendarCapability.description).not.toMatch(/\b\d{1,3}(?:,\d{3}){1,2}\b/)
  })

  it('disclaimer disclaims chart-contact interpretation, matching the writer\'s own scope boundary', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [row()] })
    const result = await querySkyCalendarCapability.handler({ start_utc: START, end_utc: END }, undefined)
    expect(String((result.content as Record<string, unknown>)['disclaimer'])).toContain('chart-scoped question')
  })
})
