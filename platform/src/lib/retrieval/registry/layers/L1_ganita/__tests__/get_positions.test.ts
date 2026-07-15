/**
 * get_positions.test.ts — D-1.5b Lane B-6 (CR-50) unit tests for the graha-positions
 * default-ordering fix. No live DB required — `query` is mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getPositionsCapability } from '../get_positions'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('getPositionsCapability (ganita_positions_get) — CR-50', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('defaults to graha_position ONLY (9 grahas + Lagna) — no upagraha/aprakasha interleaving', async () => {
    const result = await getPositionsCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['categories']).toEqual(['graha_position'])
    expect(content['include_upagrahas']).toBe(false)
  })

  it('include_upagrahas=true adds upagraha/aprakasha behind the explicit facet', async () => {
    const result = await getPositionsCapability.handler(
      { chart_id: CHART_ID, include_upagrahas: true }, undefined,
    )
    const content = result.content as Record<string, unknown>
    expect(content['categories']).toEqual(['graha_position', 'upagraha_position', 'aprakasha_position'])
    expect(content['include_upagrahas']).toBe(true)
  })

  it('an explicit `categories` list overrides the CR-50 default entirely', async () => {
    const result = await getPositionsCapability.handler(
      { chart_id: CHART_ID, categories: ['upagraha_position'] }, undefined,
    )
    const content = result.content as Record<string, unknown>
    expect(content['categories']).toEqual(['upagraha_position'])
  })

  it('orders grahas before upagrahas/aprakasha in the SQL even when multiple categories are requested', async () => {
    await getPositionsCapability.handler({ chart_id: CHART_ID, include_upagrahas: true }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toMatch(/CASE fact_category/)
    expect(sql).toMatch(/WHEN 'graha_position' THEN 0/)
    expect(sql).toMatch(/WHEN 'upagraha_position' THEN 1/)
    expect(sql).toMatch(/WHEN 'aprakasha_position' THEN 2/)
  })
})
