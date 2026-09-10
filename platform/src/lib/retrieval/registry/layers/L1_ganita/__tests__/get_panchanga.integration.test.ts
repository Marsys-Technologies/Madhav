/**
 * get_panchanga.integration.test.ts — F-B28 (L1_W1_ANALYSIS_BATCH_B.md, MUST, §N.6 items
 * 3 & 4), live-DB regression pin.
 *
 * `total` used to report the PAGE size (result.rows.length), not the true matching count —
 * a truncated answer was indistinguishable from a complete one. This is not a hypothetical:
 * the canonical chart genuinely has 221 panchanga_* rows against the 200-row default limit,
 * so the pre-fix response silently reported `total: 200` looking complete while 21 rows were
 * truncated. Pins the real fix: total_matching reflects the TRUE count, more_available is
 * honestly true whenever the page is short.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_panchanga.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getPanchangaCapability } from '../get_panchanga'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_panchanga (marsys://tool/L1/get_panchanga) — F-B28 real total_matching, live DB', () => {
  it(`[${NATIVE_CHART_ID}] default limit=200 genuinely truncates the real 221-row set — more_available must be true, not silently hidden`, async () => {
    const result = await getPanchangaCapability.handler({ chart_id: NATIVE_CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as unknown[]

    expect(rows.length).toBe(200) // the default LIMIT actually caps the page
    expect(content['total_matching']).toBeGreaterThan(200) // the TRUE count, not the page size
    expect(content['more_available']).toBe(true)
  })

  it(`[${NATIVE_CHART_ID}] a large-enough limit reaches the true total with more_available:false`, async () => {
    const result = await getPanchangaCapability.handler({ chart_id: NATIVE_CHART_ID, limit: 1000 }, undefined)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as unknown[]
    expect(rows.length).toBe(content['total_matching'])
    expect(content['more_available']).toBe(false)
  })
})
