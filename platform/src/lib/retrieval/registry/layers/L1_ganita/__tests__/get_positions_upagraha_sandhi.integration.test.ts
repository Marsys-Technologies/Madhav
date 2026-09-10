/**
 * get_positions_upagraha_sandhi.integration.test.ts — live-DB pin for F-B32's
 * sun_derived_upagraha/sandhi_flag fix (cycle 184).
 *
 * Both categories had zero serving path anywhere before this fix, deliberately deferred across
 * cycles 181-183 pending a careful pass on this specific file (frame-rebasing math, CR-50
 * discipline). This pins the two live behaviors that make the split correct: sun_derived_
 * upagraha genuinely carries house_d1 (so it belongs in the include_upagrahas bundle and the
 * frame facet applies to it), while sandhi_flag genuinely does not (so it stays categories-only
 * opt-in, never bundled).
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_positions_upagraha_sandhi.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getPositionsCapability } from '../get_positions'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('get_positions — sun_derived_upagraha/sandhi_flag (F-B32, cycle 184) — live DB', () => {
  it('include_upagrahas=true surfaces real sun_derived_upagraha rows (KALA_SUN/MRITYU_SUN/YAMAGHANTAKA/ARTHA_PRAHARA)', async () => {
    const result = await getPositionsCapability.handler(
      { chart_id: NATIVE_CHART_ID, include_upagrahas: true, ayanamsha_id: 'lahiri_chitrapaksha' },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    expect(rows.length).toBeGreaterThan(0)
    const sunUpagrahaRows = rows.filter(r => r['fact_category'] === 'sun_derived_upagraha')
    expect(sunUpagrahaRows.length).toBeGreaterThan(0)
    const subjectsSeen = new Set(sunUpagrahaRows.map(r => r['fact_subject']))
    for (const expected of ['KALA_SUN', 'MRITYU_SUN', 'YAMAGHANTAKA', 'ARTHA_PRAHARA']) {
      expect(subjectsSeen.has(expected), `expected ${expected} among sun_derived_upagraha rows`).toBe(true)
    }
  })

  it('the frame facet re-bases sun_derived_upagraha house_d1 rows, not just graha/upagraha_position', async () => {
    const result = await getPositionsCapability.handler(
      { chart_id: NATIVE_CHART_ID, categories: ['sun_derived_upagraha'], frame: 'chandra', ayanamsha_id: 'lahiri_chitrapaksha' },
      undefined,
    )
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    const rows = content['rows'] as Array<Record<string, unknown>>
    const houseRows = rows.filter(r => r['fact_key'] === 'house_d1')
    expect(houseRows.length).toBeGreaterThan(0)
    for (const r of houseRows) {
      expect(r['house_from_frame']).toBeDefined()
    }
  })

  it('sandhi_flag is reachable via an explicit categories filter but NOT included by include_upagrahas', async () => {
    const explicit = await getPositionsCapability.handler(
      { chart_id: NATIVE_CHART_ID, categories: ['sandhi_flag'], ayanamsha_id: 'lahiri_chitrapaksha' },
      undefined,
    )
    expect(explicit.is_error).toBe(false)
    const explicitContent = explicit.content as Record<string, unknown>
    const explicitRows = explicitContent['rows'] as Array<Record<string, unknown>>
    expect(explicitRows.length).toBeGreaterThan(0)
    for (const r of explicitRows) {
      expect(r['fact_category']).toBe('sandhi_flag')
    }

    const bundled = await getPositionsCapability.handler(
      { chart_id: NATIVE_CHART_ID, include_upagrahas: true, ayanamsha_id: 'lahiri_chitrapaksha' },
      undefined,
    )
    const bundledContent = bundled.content as Record<string, unknown>
    const bundledRows = bundledContent['rows'] as Array<Record<string, unknown>>
    expect(bundledRows.some(r => r['fact_category'] === 'sandhi_flag')).toBe(false)
  })
})
