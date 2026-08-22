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

// ── F-159: ayanamsha_frame_sensitivity passes through get_positions unchanged ────────────────
// The primitive itself (positive/negative/missing-data) is exhaustively unit-tested against
// resolveFrameSign/resolveFrameReferenceSign directly in address_resolver.test.ts — this test
// only pins that get_positions.ts's frame:'chandra' branch is a faithful, additive pass-through
// of whatever resolveFrameReferenceSign returns, per the finding's "one choke point, then
// propagate" design (no re-derivation here).
describe('getPositionsCapability — F-159 ayanamsha_frame_sensitivity pass-through', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('surfaces ayanamsha_frame_sensitivity in the response when frame="chandra" and the cross-ayanamsha read fires', async () => {
    // Row 1: the default graha_position page (one house_d1 row so the frame re-base path runs).
    mockQuery.mockResolvedValueOnce({
      rows: [{ ayanamsha_id: 'lahiri_chitrapaksha', fact_subject: 'MAR', fact_key: 'house_d1', fact_value_num: '7' }],
    })
    // Row 2: resolveFrameReferenceSign's single-ayanamsha MOON sign lookup (chandra frame).
    mockQuery.mockResolvedValueOnce({ rows: [{ fact_id: 'f1', fact_value_text: 'Pisces' }] })
    // Row 3: computeChandraFrameSensitivity's cross-ayanamsha MOON sign widened read — one
    // divergent ayanamsha, exercising the fire case end-to-end through this consumer.
    mockQuery.mockResolvedValueOnce({
      rows: [
        { ayanamsha_id: 'krishnamurti', fact_value_text: 'Pisces' },
        { ayanamsha_id: 'lahiri_chitrapaksha', fact_value_text: 'Pisces' },
        { ayanamsha_id: 'raman', fact_value_text: 'Pisces' },
        { ayanamsha_id: 'surya_siddhanta_classical', fact_value_text: 'Aquarius' },
        { ayanamsha_id: 'true_chitra', fact_value_text: 'Pisces' },
      ],
    })
    // Row 4: the un-paginated `sign` lookup get_positions.ts issues to re-base house_from_frame.
    mockQuery.mockResolvedValueOnce({
      rows: [{ ayanamsha_id: 'lahiri_chitrapaksha', fact_subject: 'MAR', fact_value_text: 'Libra' }],
    })

    const result = await getPositionsCapability.handler({ chart_id: CHART_ID, frame: 'chandra' }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const sensitivity = content['ayanamsha_frame_sensitivity'] as Record<string, unknown>
    expect(sensitivity).toBeTruthy()
    expect(sensitivity['frame_sensitivity_class']).toBe('ayanamsha_sensitive')
  })

  it('never surfaces ayanamsha_frame_sensitivity for the default (lagna) frame', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const result = await getPositionsCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect('ayanamsha_frame_sensitivity' in content).toBe(false)
  })
})
