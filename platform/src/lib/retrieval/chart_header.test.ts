/**
 * chart_header.test.ts — W3-L1 (GT-47 / W-9) fail-loud contract unit tests.
 * No live DB required — `query` is mocked (same convention as
 * registry/layers/L1_ganita/__tests__/get_positions.test.ts).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import {
  fetchChartHeader,
  fetchChartHeaderResolution,
  CHART_HEADER_UNRESOLVED_FLAG,
} from './chart_header'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('fetchChartHeaderResolution — W3-L1 fail-loud contract', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('resolves normally: real fields, empty flags', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ name: 'Abhisek Mohanty' }] })
      .mockResolvedValueOnce({
        rows: [
          { fact_subject: 'LAGNA', fact_key: 'sign', fact_value_text: 'Aries', fact_value_num: null },
          { fact_subject: 'LAGNA', fact_key: 'longitude_sidereal', fact_value_text: null, fact_value_num: '12.43' },
          { fact_subject: 'MOON', fact_key: 'sign', fact_value_text: 'Aquarius', fact_value_num: null },
          { fact_subject: 'SUN', fact_key: 'sign', fact_value_text: 'Capricorn', fact_value_num: null },
        ],
      })
      .mockResolvedValueOnce({
        rows: [
          { lord_graha: 'Mercury', level_n: 1 },
          { lord_graha: 'Saturn', level_n: 2 },
        ],
      })

    const resolution = await fetchChartHeaderResolution(CHART_ID, 'lahiri_chitrapaksha', '2026-07-20')

    expect(resolution.flags).toEqual([])
    expect(resolution.header).toEqual({
      chart_id_short: CHART_ID.slice(0, 8),
      name: 'Abhisek Mohanty',
      lagna_sign: 'Aries',
      lagna_deg: 12.43,
      moon_sign: 'Aquarius',
      sun_sign: 'Capricorn',
      ayanamsha: 'lahiri_chitrapaksha',
      current_maha_antar: 'Mercury MD / Saturn AD',
    })
  })

  it('DB error during resolution: fields stay null, but the failure is flagged (not silent)', async () => {
    mockQuery.mockRejectedValue(new Error('connection terminated'))

    const resolution = await fetchChartHeaderResolution(
      CHART_ID, 'lahiri_chitrapaksha', '2026-07-21', // distinct as_of_date avoids the 60s cache from the prior test
    )

    expect(resolution.flags).toEqual([CHART_HEADER_UNRESOLVED_FLAG])
    expect(resolution.header.chart_id_short).toBe(CHART_ID.slice(0, 8))
    expect(resolution.header.name).toBeNull()
    expect(resolution.header.lagna_sign).toBeNull()
    expect(resolution.header.moon_sign).toBeNull()
    expect(resolution.header.sun_sign).toBeNull()
    expect(resolution.header.current_maha_antar).toBeNull()
  })

  it('fetchChartHeader (backward-compatible wrapper) still returns just the header on failure', async () => {
    mockQuery.mockRejectedValue(new Error('connection terminated'))

    const header = await fetchChartHeader(CHART_ID, 'lahiri_chitrapaksha', '2026-07-22')

    expect(header.lagna_sign).toBeNull()
    expect(header.chart_id_short).toBe(CHART_ID.slice(0, 8))
  })

  it('CHART_HEADER_UNRESOLVED_FLAG is the stable, plain-string flag name (pre-closed-enum)', () => {
    expect(CHART_HEADER_UNRESOLVED_FLAG).toBe('chart_header_unresolved')
  })
})
