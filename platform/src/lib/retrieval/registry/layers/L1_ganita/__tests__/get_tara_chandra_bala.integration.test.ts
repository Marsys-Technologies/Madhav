/**
 * get_tara_chandra_bala.integration.test.ts — F-B28 (L1_W1_ANALYSIS_BATCH_B.md, MUST,
 * §N.6 items 3 & 4), live-DB regression pin.
 *
 * Same defect class as get_panchanga.ts's own F-B28 fix: `total` reported the PAGE size,
 * not the true matching count. Pins the real fix with a deliberately small limit to force
 * genuine truncation (the canonical chart has 195 rows across both categories — comfortably
 * under the 200 default, so this test uses limit=50 to actually exercise truncation).
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_tara_chandra_bala.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getTaraChanndraBalaCapability } from '../get_tara_chandra_bala'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_tara_chandra_bala (marsys://tool/L1/get_tara_chandra_bala) — F-B28 real total_matching, live DB', () => {
  it(`[${NATIVE_CHART_ID}] a small limit genuinely truncates — more_available must be true, not silently hidden`, async () => {
    const result = await getTaraChanndraBalaCapability.handler({ chart_id: NATIVE_CHART_ID, limit: 50 }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as unknown[]

    expect(rows.length).toBe(50)
    expect(content['total_matching']).toBeGreaterThan(50)
    expect(content['more_available']).toBe(true)
  })

  it(`[${NATIVE_CHART_ID}] the default limit=200 reaches the true total (195 rows) with more_available:false`, async () => {
    const result = await getTaraChanndraBalaCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as unknown[]
    expect(rows.length).toBe(content['total_matching'])
    expect(content['more_available']).toBe(false)
  })
})
