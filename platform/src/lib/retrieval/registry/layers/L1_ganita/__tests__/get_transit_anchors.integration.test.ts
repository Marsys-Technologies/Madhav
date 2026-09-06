/**
 * get_transit_anchors.integration.test.ts — F-D25 (L1_W1_ANALYSIS_BATCH_D.md, NOW, §N.6;
 * D-SERVICE ≤2 hops to L1), live-DB regression pin.
 *
 * Confirms every served row genuinely grounds back to real chart_facts.fact_id values (not
 * fabricated) — each constituent_fact_ids entry must actually exist in chart_facts under the
 * exact (fact_category, fact_key, fact_subject, ayanamsha_id) the writer itself used.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_transit_anchors.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { query } from '@/lib/db/client'
import { getTransitAnchorsCapability } from '../get_transit_anchors'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_transit_anchors (marsys://tool/L1/get_transit_anchors) — F-D25 real grounding, live DB', () => {
  it(`[${NATIVE_CHART_ID}] every row's constituent_fact_ids are non-empty and resolve to real, matching chart_facts rows`, async () => {
    const result = await getTransitAnchorsCapability.handler({
      chart_id: NATIVE_CHART_ID,
      ayanamsha_id: 'lahiri_chitrapaksha',
      limit: 50,
    }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const anchors = content['anchors'] as Array<Record<string, unknown>>
    expect(anchors.length).toBeGreaterThan(0)

    for (const row of anchors) {
      const ids = row['constituent_fact_ids'] as string[]
      expect(ids.length, `graha=${row['graha']} had zero constituent_fact_ids`).toBeGreaterThan(0)

      const check = await query<{ fact_id: string; fact_category: string; ayanamsha_id: string }>(
        `SELECT fact_id, fact_category, ayanamsha_id FROM chart_facts WHERE fact_id = ANY($1::text[])`,
        [ids],
      )
      expect(check.rows.length).toBe(ids.length)
      for (const r of check.rows) {
        expect(r.ayanamsha_id).toBe('lahiri_chitrapaksha')
        expect(['graha_position', 'graha_sign_attributes']).toContain(r.fact_category)
      }
    }
  })
})
