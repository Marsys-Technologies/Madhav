/**
 * get_sade_sati.integration.test.ts — F-D20 (L1_W1_ANALYSIS_BATCH_D.md, NOW, §N.7 pt.2),
 * live-DB regression pin.
 *
 * The ORDER BY was `fact_category, ayanamsha_id, fact_key` alone — a non-total order.
 * Confirmed live: 48 rows share this exact sort key for several (category, ayanamsha, key)
 * combinations on the canonical chart (e.g. sade_sati_phase_quarter/krishnamurti/
 * quarter_end_iso), so LIMIT/OFFSET pagination across them (particularly the all:true full
 * sweep) was undefined/unstable order. Pins that repeated identical calls now return
 * byte-identical row order.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_sade_sati.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getSadeSatiCapability } from '../get_sade_sati'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_sade_sati (marsys://tool/L1/get_sade_sati) — F-D20 total-order pagination, live DB', () => {
  it(`[${NATIVE_CHART_ID}] all:true repeated identical calls into the known tie group return byte-identical row order`, async () => {
    const call = () => getSadeSatiCapability.handler({
      chart_id: NATIVE_CHART_ID,
      all: true,
      categories: ['sade_sati_phase_quarter'],
      ayanamsha_id: 'krishnamurti',
      limit: 200,
    }, undefined)

    const [first, second, third] = await Promise.all([call(), call(), call()])
    expect(first.is_error).toBe(false)

    const idsOf = (r: typeof first) => ((r.content as Record<string, unknown>)['rows'] as Array<Record<string, unknown>>).map(row => row['fact_id'])
    const firstIds = idsOf(first)
    expect(firstIds.length).toBeGreaterThan(0)
    expect(idsOf(second)).toEqual(firstIds)
    expect(idsOf(third)).toEqual(firstIds)
  })
})
