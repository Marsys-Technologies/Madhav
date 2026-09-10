/**
 * get_vastu_directions.test.ts — F-E11 (L1_W1_ANALYSIS_BATCH_E.md, "highest-
 * leverage item in the batch"): the per-chart weakened/strengthened directions
 * (ga_vastu_planet_direction_map) and the 24-row classical per-direction
 * remedies (bg_vastu_direction_remedials, L0) were never joined -- the
 * instrument held both halves of "your East is afflicted, here is the
 * classical remedy" with no surface putting them together.
 *
 * No live DB required — `query` is mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getVastuDirectionsCapability } from '../get_vastu_directions'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('getVastuDirectionsCapability — F-E11 classical remedy join', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('LEFT JOIN LATERALs bg_vastu_direction_remedials on the row’s own direction', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })

    await getVastuDirectionsCapability.handler({ chart_id: CHART_ID }, undefined)

    const rowsSql = mockQuery.mock.calls[0][0] as string
    expect(rowsSql).toMatch(/LEFT JOIN LATERAL/)
    expect(rowsSql).toMatch(/FROM bg_vastu_direction_remedials/)
    expect(rowsSql).toMatch(/WHERE direction = m\.direction/)
  })

  it('serves direction_remedies as an array of {remedy_type, remedy_description, classical_citation}', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [{
        id: 1, graha: 'Sun', direction: 'East', direction_impact: 'weakened',
        direction_remedies: [
          { remedy_type: 'color', remedy_description: 'White or saffron', classical_citation: 'Brihat Samhita Ch.53' },
          { remedy_type: 'symbol', remedy_description: 'Sun symbol', classical_citation: 'Mayamata Ch.6' },
        ],
      }],
    })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })

    const result = await getVastuDirectionsCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    const remedies = rows[0]['direction_remedies'] as Array<Record<string, unknown>>
    expect(remedies).toHaveLength(2)
    expect(remedies[0]).toMatchObject({ remedy_type: 'color' })
    const provenance = content['provenance'] as Record<string, unknown>
    expect(provenance['tables']).toContain('bg_vastu_direction_remedials')
  })

  it('a direction with no catalog remedy serves an empty array, never a missing field', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [{ id: 2, graha: 'Rahu', direction: 'Southwest', direction_remedies: [] }],
    })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })

    const result = await getVastuDirectionsCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows[0]['direction_remedies']).toEqual([])
  })

  it('the SQL coalesces a NULL aggregate to an empty JSON array, not NULL', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })

    await getVastuDirectionsCapability.handler({ chart_id: CHART_ID }, undefined)
    const rowsSql = mockQuery.mock.calls[0][0] as string
    expect(rowsSql).toMatch(/COALESCE\(r\.direction_remedies, '\[\]'::jsonb\)/)
  })

  it('still filters on chart_id and other params, qualified against the joined query', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })

    await getVastuDirectionsCapability.handler({ chart_id: CHART_ID, direction: 'East' }, undefined)
    const rowsSql = mockQuery.mock.calls[0][0] as string
    const rowsParams = mockQuery.mock.calls[0][1] as unknown[]
    expect(rowsSql).toMatch(/m\.chart_id = \$1/)
    expect(rowsSql).toMatch(/m\.direction = \$2/)
    expect(rowsParams).toEqual([CHART_ID, 'East', 50])
  })
})
