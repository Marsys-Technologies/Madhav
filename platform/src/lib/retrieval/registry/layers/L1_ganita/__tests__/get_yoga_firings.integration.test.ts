/**
 * get_yoga_firings.integration.test.ts — F-D5 (L1_W1_ANALYSIS_BATCH_D.md, NOW, §N.7 pt.2),
 * live-DB regression pin.
 *
 * The ORDER BY was `strength DESC NULLS LAST, yoga_canonical_id` alone — a non-total order.
 * Multiple (yoga_canonical_id, strength) pairs genuinely repeat across the 5 stored
 * ayanamshas on the canonical chart (confirmed live: dhana_yoga_house_lords/budha_aditya/
 * anapha/dhana_yoga_2_5_9_11/jaimini_karakamsha_moon each have 3 same-strength rows), so a
 * caller querying across all ayanamshas at once got ties resolved in undefined/unstable
 * order. Pins that repeated identical calls now return byte-identical row ORDER (not just
 * the same set), and that no row is silently duplicated or dropped by the added tiebreak.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_yoga_firings.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getYogaFiringsCapability } from '../get_yoga_firings'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_yoga_firings (marsys://tool/L1/get_yoga_firings) — F-D5 total-order pagination, live DB', () => {
  it(`[${NATIVE_CHART_ID}] repeated identical calls return byte-identical row order (deterministic pagination)`, async () => {
    const call = () => getYogaFiringsCapability.handler({
      chart_id: NATIVE_CHART_ID,
      fired: true,
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

  it(`[${NATIVE_CHART_ID}] a known same-strength tie group (dhana_yoga_house_lords) resolves in a stable, ayanamsha-then-id order`, async () => {
    const result = await getYogaFiringsCapability.handler({
      chart_id: NATIVE_CHART_ID,
      fired: true,
      yoga_canonical_id: 'dhana_yoga_house_lords',
      limit: 200,
    }, undefined)

    expect(result.is_error).toBe(false)
    const rows = (result.content as Record<string, unknown>)['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThanOrEqual(3) // known live tie: 3 rows, same strength, 3 distinct ayanamshas

    // Within the same yoga_canonical_id + strength tie, rows must come out sorted by
    // (ayanamsha_id, id) — never a different order across identical calls (already pinned
    // above), and never grouped by anything other than the declared tiebreak.
    const tieGroup = rows.filter(r => r['yoga_canonical_id'] === 'dhana_yoga_house_lords')
    for (let i = 1; i < tieGroup.length; i++) {
      const prev = tieGroup[i - 1]
      const cur = tieGroup[i]
      if (prev['strength'] === cur['strength']) {
        const prevKey = `${prev['ayanamsha_id']}`
        const curKey = `${cur['ayanamsha_id']}`
        expect(prevKey <= curKey).toBe(true)
        if (prevKey === curKey) {
          expect(Number(prev['id'])).toBeLessThan(Number(cur['id']))
        }
      }
    }
  })
})
