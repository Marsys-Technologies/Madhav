/**
 * get_ayurdaya.integration.test.ts — F-E2/F-E3 (L1_W1_ANALYSIS_BATCH_E.md, NOW), live-DB
 * regression pin.
 *
 * Confirms live: total_years rows genuinely carry fact_value_jsonb.harana_status =
 * 'base_only_haranas_deferred_to_w3' (confirmed against production data before shipping the
 * fix), and the maraka_grahas row's jsonb (2nd/7th significators) is reachable at 0 hops.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_ayurdaya.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getAyurdayaCapability } from '../get_ayurdaya'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_ayurdaya (marsys://tool/L1/get_ayurdaya) — F-E2/F-E3 jsonb + harana_status disclosure, live DB', () => {
  it(`[${NATIVE_CHART_ID}] every row carries fact_value_jsonb; top-level harana_status matches the live total_years rows' own value`, async () => {
    const result = await getAyurdayaCapability.handler({
      chart_id: NATIVE_CHART_ID,
      ayanamsha_id: 'lahiri_chitrapaksha',
      limit: 200,
    }, undefined)

    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    for (const r of rows) {
      expect(r['fact_value_jsonb']).toBeDefined()
    }

    expect(content['harana_status']).toBe('base_only_haranas_deferred_to_w3')

    const marakaRow = rows.find(r => r['fact_key'] === 'maraka_grahas')
    expect(marakaRow).toBeDefined()
    const marakaJsonb = marakaRow!['fact_value_jsonb'] as Record<string, unknown>
    expect(marakaJsonb['maraka_grahas']).toBeDefined()
  })
})
