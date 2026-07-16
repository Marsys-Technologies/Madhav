/**
 * WP-S4-fix2 (Gate Ś #8) — yoga_activation_by_dasha ranking fix.
 *
 * Root cause (live evidence, chart 482012f1): the WHERE clause correctly admits
 * undated `kala_activation` rows (activation_start IS NULL) alongside dated ones
 * (W4-loop-1's fix for the original all-zero-results bug), but the ORDER BY ranked
 * purely on `dasha_activation_proximity_score DESC`. An undated row's proximity
 * score always defaults to exactly 0.5 (date_resolver._proximity_score returns 0.5
 * when no peak resolves); the majority of genuinely DATED rows on this chart score
 * BELOW 0.5. So undated rows — carrying a false "above average" 0.5 — systematically
 * crowded real, dated activations out of the top-K page (live symptom: 15/15 rows
 * returned for a 2026-2029 window were ALL undated with the tell-tale flat 0.5).
 *
 * Fix: ORDER BY (activation_start IS NULL) ASC first — dated rows always rank ahead
 * of undated ones — THEN by proximity/salience within each tier. No DB required;
 * `query` is mocked and this test asserts the SQL text itself carries the fix.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('../../../provenance/freshness_notes', () => ({
  deriveDefect001Note: vi.fn().mockResolvedValue({ note: 'stub', orphan_fraction: 0 }),
}))

import { yogaActivationByDashaCapability } from '../register_d8_assess_domain'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('yogaActivationByDashaCapability (yoga_activation_by_dasha) — WP-S4-fix2 ranking', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockQuery.mockResolvedValue({ rows: [] })
  })

  it('ORDER BY ranks dated rows (activation_start IS NOT NULL) ahead of undated rows', async () => {
    await yogaActivationByDashaCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(mockQuery).toHaveBeenCalledTimes(1)
    const sql = mockQuery.mock.calls[0]?.[0] as string
    expect(sql).toContain('ORDER BY (ka.activation_start IS NULL) ASC')
    // The dated-first clause must precede the proximity-score clause, or a flat-0.5
    // undated row would still out-rank a genuinely dated real (often sub-0.5) score.
    const orderByIdx = sql.indexOf('ORDER BY')
    const datedFirstIdx = sql.indexOf('(ka.activation_start IS NULL) ASC')
    const proximityIdx = sql.indexOf('dasha_activation_proximity_score DESC')
    expect(orderByIdx).toBeGreaterThan(-1)
    expect(datedFirstIdx).toBeGreaterThan(orderByIdx)
    expect(proximityIdx).toBeGreaterThan(datedFirstIdx)
  })

  it('WHERE clause still admits undated rows (B.10 — never silently drop reachable data)', async () => {
    await yogaActivationByDashaCapability.handler({ chart_id: CHART_ID }, undefined)
    const sql = mockQuery.mock.calls[0]?.[0] as string
    expect(sql).toContain('ka.activation_start IS NULL OR')
  })

  it('undated_activation_count is still honestly reported when rows return undated', async () => {
    mockQuery.mockResolvedValue({
      rows: [
        { signal_id: 's1', activation_start: null, dasha_alignment_score: 0.5 },
        { signal_id: 's2', activation_start: '2026-08-01', dasha_alignment_score: 0.3 },
      ],
    })
    const result = await yogaActivationByDashaCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['undated_activation_count']).toBe(1)
    expect((content['activated_yogas'] as unknown[]).length).toBe(2)
  })
})
