/**
 * get_transit_anchors.test.ts — F-D25 (L1_W1_ANALYSIS_BATCH_D.md, NOW, §N.6; D-SERVICE ≤2
 * hops to L1) unit tests. No live DB required — `query` is mocked.
 *
 * Before this fix: no density_contract, no empty_reason, and grounds_to.l1_fact_ids: false
 * despite the writer genuinely deriving every served value from specific chart_facts rows
 * (graha_position/graha_sign_attributes, fact_key sign/longitude_sidereal/nakshatra). The fix
 * re-runs the writer's own filter at serve time (not fabricated) to attach real
 * constituent_fact_ids to each row, and grounds_to.l1_fact_ids is now genuinely true.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getTransitAnchorsCapability } from '../get_transit_anchors'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('getTransitAnchorsCapability (ganita_transit_anchors_get)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('declares grounds_to.l1_fact_ids: true and a density_contract (F-D25)', () => {
    expect(getTransitAnchorsCapability.grounds_to).toEqual({ l1_fact_ids: true })
    expect(getTransitAnchorsCapability.density_contract).toBeDefined()
    expect(getTransitAnchorsCapability.density_contract?.empty_reason).toBe(true)
  })

  it('attaches real constituent_fact_ids resolved from chart_facts, keyed by (ayanamsha_id, subject code)', async () => {
    const anchorRows = [
      { id: '1', chart_id: CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', graha: 'sun', natal_sign: 'capricorn', natal_house_from_moon: 12, natal_degree_absolute: 284.5 },
      { id: '2', chart_id: CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', graha: 'rahu', natal_sign: 'aquarius', natal_house_from_moon: 1, natal_degree_absolute: 310.2 },
    ]
    mockQuery.mockResolvedValueOnce({ rows: anchorRows }) // anchors query
    mockQuery.mockResolvedValueOnce({
      rows: [
        { ayanamsha_id: 'lahiri_chitrapaksha', fact_subject: 'SUN', fact_id: 'f-sun-sign' },
        { ayanamsha_id: 'lahiri_chitrapaksha', fact_subject: 'SUN', fact_id: 'f-sun-long' },
        { ayanamsha_id: 'lahiri_chitrapaksha', fact_subject: 'RAH_MEAN', fact_id: 'f-rahu-sign' },
      ],
    }) // fact_ids query

    const result = await getTransitAnchorsCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const anchors = content['anchors'] as Array<Record<string, unknown>>

    const sunRow = anchors.find(a => a['graha'] === 'sun')!
    expect(sunRow['constituent_fact_ids']).toEqual(['f-sun-sign', 'f-sun-long'])
    const rahuRow = anchors.find(a => a['graha'] === 'rahu')!
    expect(rahuRow['constituent_fact_ids']).toEqual(['f-rahu-sign'])

    // The second query's fact_category/fact_key params must be the writer's own filter.
    const factQueryParams = mockQuery.mock.calls[1][1] as unknown[]
    expect(factQueryParams).toEqual([
      CHART_ID,
      ['lahiri_chitrapaksha'],
      ['graha_position', 'graha_sign_attributes'],
      ['sign', 'longitude_sidereal', 'nakshatra'],
    ])
  })

  it('does not issue the fact_ids lookup query when zero anchor rows are returned', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await getTransitAnchorsCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it('reports empty_reason with the applied filters named when genuinely zero rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await getTransitAnchorsCapability.handler({ chart_id: CHART_ID, ayanamsha_id: 'raman', graha: 'mars' }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(String(content['empty_reason'])).toMatch(/raman/)
    expect(String(content['empty_reason'])).toMatch(/mars/)
    expect(content['total']).toBe(0)
  })

  it('leaves constituent_fact_ids empty (not crashing) for a row whose graha string is unrecognized', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ id: '1', chart_id: CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', graha: 'not_a_graha' }] })
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await getTransitAnchorsCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const anchors = content['anchors'] as Array<Record<string, unknown>>
    expect(anchors[0]['constituent_fact_ids']).toEqual([])
  })
})
