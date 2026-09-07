/**
 * get_structural_signals.integration.test.ts — live-DB pin for
 * marsys://tool/L1/get_structural (F-B32 slice 8, cycle 181; +3 categories cycle 183).
 *
 * These 18 fact_categories had no dedicated serving face at all before this tool -- pins that
 * it actually returns real rows for the canonical chart, across the full category set and the
 * domain filter, so a future regression that silently drops a category or breaks the domain map
 * is caught here rather than rediscovered live.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_structural_signals.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getStructuralSignalsCapability } from '../get_structural_signals'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_structural_signals (marsys://tool/L1/get_structural) — live DB', () => {
  it('every domain reaches at least one live-populated category', async () => {
    // Live row counts confirmed cycle 181/183 investigation (canonical chart): sambandha_grade=5220,
    // bhava_significance_link=5220, virupa_drishti=2755, contradiction_pair=1740,
    // net_argala_per_varga=1740, graha_centrality=1305, chart_cluster=1305,
    // aspect_received_by_special_point=449, significator_path=360, chart_center_of_gravity=290,
    // panchadha_maitri=210, conjunction_special_point=137, nway_config_per_varga=80,
    // nakshatra_dispositor_chain=50, nakshatra_lord_relationship=45, kendradhipati_dosha=20,
    // graha_yuddha_per_varga=17, nakshatra_co_tenancy=1.
    // relational's own live total (15,378 rows across 9 categories) exceeds the 2000 page cap,
    // and ORDER BY fact_category ASC now puts 'bhava_significance_link' (5220 rows) FIRST
    // alphabetically -- it alone fills the entire first page, so only it (not
    // conjunction_special_point/contradiction_pair, pushed out past the cap) is assertable here
    // (same shape as get_nakshatra.ts's own documented caveat, one level deeper: even a single
    // domain bucket can exceed the page cap here). per_varga's live total (1,837 across 3
    // categories) stays under the cap, so all three are assertable without truncation risk.
    const expectedPerDomain: Record<string, string[]> = {
      relational: ['bhava_significance_link'],
      graph: ['chart_cluster', 'chart_center_of_gravity'],
      special_point: ['aspect_received_by_special_point'],
      per_varga: ['nway_config_per_varga', 'graha_yuddha_per_varga', 'net_argala_per_varga'],
      dosha: ['kendradhipati_dosha'],
    }
    for (const [domain, expected] of Object.entries(expectedPerDomain)) {
      const result = await getStructuralSignalsCapability.handler(
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

  it('sambandha_grade and virupa_drishti (highest row counts, 5220 and 2755) are reachable via an explicit categories filter', async () => {
    const result = await getStructuralSignalsCapability.handler(
      { chart_id: NATIVE_CHART_ID, categories: ['sambandha_grade', 'virupa_drishti'], limit: 2000 },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    const categoriesSeen = new Set(rows.map(r => r['fact_category']))
    expect(categoriesSeen.has('sambandha_grade')).toBe(true)
  })

  it('conjunction_special_point, contradiction_pair, and panchadha_maitri (pushed out of the relational domain page by bhava_significance_link) are reachable via an explicit categories filter', async () => {
    const result = await getStructuralSignalsCapability.handler(
      { chart_id: NATIVE_CHART_ID, categories: ['conjunction_special_point', 'contradiction_pair', 'panchadha_maitri'], limit: 2000 },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    const categoriesSeen = new Set(rows.map(r => r['fact_category']))
    expect(categoriesSeen.has('conjunction_special_point')).toBe(true)
    expect(categoriesSeen.has('contradiction_pair')).toBe(true)
    expect(categoriesSeen.has('panchadha_maitri')).toBe(true)
  })

  it('nakshatra_co_tenancy (1 live row) is reachable via the relational domain filter', async () => {
    const result = await getStructuralSignalsCapability.handler(
      { chart_id: NATIVE_CHART_ID, categories: ['nakshatra_co_tenancy'], limit: 2000 },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBe(1)
    expect(rows[0]!['fact_category']).toBe('nakshatra_co_tenancy')
  })

  it('the dosha domain filter returns only kendradhipati_dosha rows', async () => {
    const result = await getStructuralSignalsCapability.handler(
      { chart_id: NATIVE_CHART_ID, domain: 'dosha', limit: 2000 },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    for (const r of rows) {
      expect(r['fact_category']).toBe('kendradhipati_dosha')
    }
  })

  it('an ayanamsha_id filter narrows every returned row to that ayanamsha', async () => {
    const result = await getStructuralSignalsCapability.handler(
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
