import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import { fetchKpCuspChain, fetchSensitiveDegreeFirings } from '../reading_checklist'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const BUILD_ID = '11111111-1111-4111-8111-111111111111'

beforeEach(() => queryMock.mockReset())

describe('reading-checklist selected-build fence', () => {
  it('fences sensitive-degree facts to the judgment build', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{
      fact_id: 'active-sensitive', fact_subject: 'MAR', fact_key: 'pushkara',
      fact_value_text: 'pushkara', fact_value_jsonb: { fired: true },
    }] })

    const result = await fetchSensitiveDegreeFirings(CHART_ID, AYANAMSHA, BUILD_ID)

    expect(result.fact_ids).toEqual(['active-sensitive'])
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain('build_id = $4::text')
    expect(params).toEqual([
      CHART_ID, AYANAMSHA, ['pushkara', 'gandanta', 'mrityu_bhaga', 'kartari'], BUILD_ID,
    ])
  })

  it('threads build_id through the KP child and never accepts another generation', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })

    const result = await fetchKpCuspChain(CHART_ID, AYANAMSHA, [2, 11], BUILD_ID)

    expect(result.cusps).toEqual([])
    const [sql, params] = queryMock.mock.calls[0]!
    expect(String(sql)).toContain('build_id = $4::text')
    expect(params).toEqual([
      CHART_ID,
      AYANAMSHA,
      ['cusp_kp_lords', 'kp_cuspal_significators', 'bhava_cusps', 'kp_ruling_planets_natal'],
      BUILD_ID,
    ])
  })
})
