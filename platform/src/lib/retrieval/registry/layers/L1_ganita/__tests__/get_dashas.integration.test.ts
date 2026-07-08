/**
 * get_dashas.integration.test.ts — live-DB regression pin for marsys://tool/L1/get_dashas'
 * "current-dasha" gate (R5 W1 dasha_query lane, Ring-1 verifier finding + JL-010).
 *
 * The verifier found the tool's own description omitted that `ayanamsha_id` must be
 * explicitly supplied for the ≤1KB current-dasha gate — chart_dashas carries 5 ayanamshas
 * and get_dashas.ts applies NO server-side default for this one facet (unlike system/level/
 * window), so a caller who omits it silently gets one row PER AYANAMSHA (5 rows, ~3.2KB,
 * 3x over budget). This test pins the ≤1KB number using the COMPLETE correct facet set
 * (system=vimshottari, level=1, as_of_date=<today>, ayanamsha_id=lahiri_chitrapaksha) on
 * both canonical charts, and pins the documented failure mode (omitting ayanamsha_id busts
 * the gate) so a future regression in either the handler or its own tool description is
 * caught here rather than rediscovered live.
 *
 * Run with: INTEGRATION=true vitest run src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_dashas.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { getDashasCapability } from '../get_dashas'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const BOTH_CHARTS = [NATIVE_CHART_ID, ABHINANDAN_CHART_ID]

const describeIf = INTEGRATION ? describe : describe.skip

const today = new Date().toISOString().slice(0, 10)

describeIf('get_dashas (marsys://tool/L1/get_dashas) — current-dasha gate, live DB', () => {
  for (const chartId of BOTH_CHARTS) {
    it(`[${chartId}] COMPLETE facet set (system=vimshottari, level=1, as_of_date=${today}, ayanamsha_id=lahiri_chitrapaksha) is ONE row, <=1KB`, async () => {
      const result = await getDashasCapability.handler({
        chart_id: chartId,
        system: 'vimshottari',
        level: 1,
        as_of_date: today,
        ayanamsha_id: 'lahiri_chitrapaksha',
      }, undefined)

      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      const rows = content['rows'] as Array<Record<string, unknown>>

      // Exactly one currently-active Mahadasha for one ayanamsha.
      expect(rows.length).toBe(1)
      expect(rows[0]['ayanamsha_id']).toBe('lahiri_chitrapaksha')
      expect(rows[0]['level_n']).toBe(1)

      const bytes = Buffer.byteLength(JSON.stringify(content), 'utf8')
      expect(bytes, `current-dasha payload was ${bytes} bytes`).toBeLessThanOrEqual(1024)
    })

    it(`[${chartId}] REGRESSION: omitting ayanamsha_id silently returns one row PER AYANAMSHA and busts the gate (pins the documented failure mode)`, async () => {
      const result = await getDashasCapability.handler({
        chart_id: chartId,
        system: 'vimshottari',
        level: 1,
        as_of_date: today,
        // ayanamsha_id intentionally omitted
      }, undefined)

      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      const rows = content['rows'] as Array<Record<string, unknown>>

      // All 5 ayanamshas come back unfiltered — this is the exact silent-unfiltered defect
      // the tool description now warns about; if this ever drops to 1, the description's
      // warning (and this test) need to be revisited, not silently left stale.
      expect(rows.length).toBeGreaterThan(1)
      const distinctAyanamshas = new Set(rows.map(r => r['ayanamsha_id']))
      expect(distinctAyanamshas.size).toBeGreaterThan(1)

      const bytes = Buffer.byteLength(JSON.stringify(content), 'utf8')
      expect(bytes, `unfiltered payload was ${bytes} bytes — expected to bust the 1KB gate`).toBeGreaterThan(1024)
    })
  }
})
