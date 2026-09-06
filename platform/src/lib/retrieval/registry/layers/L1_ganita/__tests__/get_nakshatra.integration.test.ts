/**
 * get_nakshatra.integration.test.ts — live-DB pin for marsys://tool/L1/get_nakshatra
 * (F-B18/F-B19, cycle 103).
 *
 * ga_nakshatra had no dedicated serving face at all (ganita_nakshatra_get never existed) --
 * this pins that the new tool actually returns real rows for the canonical chart, across
 * the full category set and the domain filter, so a future regression that silently drops
 * a category or breaks the domain map is caught here rather than rediscovered live.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_nakshatra.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getNakshatraCapability } from '../get_nakshatra'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_nakshatra (marsys://tool/L1/get_nakshatra) — live DB', () => {
  it('every domain reaches at least one live-populated category (total row count exceeds the 2000 page cap, so a flat unfiltered call cannot see them all -- this is the intended reason the domain filter exists)', async () => {
    // Categories confirmed live-populated per domain (cycle 103 investigation);
    // nakshatra_lord_placement/nakshatra_exchange/graha_degree_flags are 0-row on the
    // canonical chart (not a bug -- ga_nakshatra genuinely doesn't emit them for this
    // chart) and are deliberately excluded from this expectation.
    const expectedPerDomain: Record<string, string[]> = {
      identity: ['graha_nakshatra_join', 'graha_pada_join', 'graha_gandanta'],
      kp: ['graha_kp_lords', 'cusp_kp_lords', 'kp_house_significators', 'kp_planet_significations'],
      relational: ['nakshatra_dispositor', 'nakshatra_cogravity', 'nakshatra_conjunction'],
      strength: ['graha_tara_bala'],
      meta: ['nakshatra_statistics', 'nakshatra_cross_ayanamsha'],
    }
    for (const [domain, expected] of Object.entries(expectedPerDomain)) {
      const result = await getNakshatraCapability.handler(
        { chart_id: NATIVE_CHART_ID, domain, limit: 2000 },
        undefined,
      )
      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      const rows = content['rows'] as Array<Record<string, unknown>>
      expect(rows.length, `domain=${domain} returned no rows`).toBeGreaterThan(0)
      const categoriesSeen = new Set(rows.map(r => r['fact_category']))
      for (const category of expected) {
        expect(categoriesSeen.has(category), `domain=${domain}: expected ${category} among served rows`).toBe(true)
      }
    }
  })

  it('the kp domain filter returns only KP-family categories', async () => {
    const result = await getNakshatraCapability.handler(
      { chart_id: NATIVE_CHART_ID, domain: 'kp', limit: 2000 },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    for (const r of rows) {
      expect(['graha_kp_lords', 'cusp_kp_lords', 'kp_house_significators', 'kp_planet_significations'])
        .toContain(r['fact_category'])
    }
  })

  it('an ayanamsha_id filter narrows every returned row to that ayanamsha', async () => {
    const result = await getNakshatraCapability.handler(
      { chart_id: NATIVE_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', limit: 2000 },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    for (const r of rows) {
      expect(r['ayanamsha_id']).toBe('lahiri_chitrapaksha')
    }
  })
})
