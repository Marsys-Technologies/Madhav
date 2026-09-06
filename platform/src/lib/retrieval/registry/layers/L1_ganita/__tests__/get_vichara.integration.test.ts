/**
 * get_vichara.integration.test.ts — F-D11 (L1_W1_ANALYSIS_BATCH_D.md, NOW, §N.7 pt.2),
 * live-DB regression pin.
 *
 * The ORDER BY was `vichara_family, domain NULLS FIRST, subject` alone — a non-total order.
 * Confirmed live: 1,595 `valence_pass` rows/ayanamsha share this exact sort key per subject
 * (SAT/MAR/JUP each 1,595-way tied on the canonical chart), so LIMIT/OFFSET pagination
 * across them was undefined/unstable order. Pins that repeated identical calls now return
 * byte-identical row order.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_vichara.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getVicharaCapability } from '../get_vichara'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_vichara (marsys://tool/L1/get_vichara) — F-D11 total-order pagination, live DB', () => {
  it(`[${NATIVE_CHART_ID}] repeated identical calls into the known SAT valence_pass tie group return byte-identical row order`, async () => {
    const call = () => getVicharaCapability.handler({
      chart_id: NATIVE_CHART_ID,
      family: 'valence_pass',
      subject: 'SAT',
      limit: 200,
    }, undefined)

    const [first, second, third] = await Promise.all([call(), call(), call()])
    expect(first.is_error).toBe(false)

    const idsOf = (r: typeof first) => ((r.content as Record<string, unknown>)['rows'] as Array<Record<string, unknown>>).map(row => row['id'])
    const firstIds = idsOf(first)
    expect(firstIds.length).toBeGreaterThan(0)
    expect(idsOf(second)).toEqual(firstIds)
    expect(idsOf(third)).toEqual(firstIds)
  })
})
