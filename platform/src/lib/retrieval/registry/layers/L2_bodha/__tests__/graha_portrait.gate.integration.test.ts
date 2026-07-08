/**
 * @integration-test
 *
 * graha_portrait.gate.integration.test.ts — R5 W3 GATE MEASUREMENT (live DB).
 * ==============================================================================
 * The W3 lane gate: "graha_portrait('Saturn') produces a genuinely populated
 * portrait — not hollow/null fields" (design §28.2), on BOTH canonical charts
 * (native 482012f1, Abhinandan 1c826d5a). This is the graha_portrait analog of
 * P3's original defect (a tool that LOOKED like it returned data but every field
 * was null/[]) — asserted directly against the real capability handler, ONE call
 * per chart, no mocking.
 *
 * Gated on DB_AVAILABLE (same pattern as traverse_chart_graph.gate.integration.test.ts
 * / address_resolver.integration.test.ts). Run:
 *   DATABASE_URL=postgresql://user:pass@host:port/db vitest run --testPathPattern=graha_portrait.gate
 */

import { describe, it, expect } from 'vitest'
import { grahaPortraitCapability } from '../graha_portrait'

const DB_AVAILABLE = !!(process.env.DB_URL || process.env.DATABASE_URL)
const maybeDescribe = DB_AVAILABLE ? describe : describe.skip

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const BOTH_CHARTS = [
  ['native', NATIVE_CHART_ID],
  ['Abhinandan', ABHINANDAN_CHART_ID],
] as const

maybeDescribe('graha_portrait — W3 gate: Saturn portrait, ONE call, genuinely populated, live DB', () => {
  for (const [label, chartId] of BOTH_CHARTS) {
    it(`${label} chart (${chartId}): Saturn portrait is populated, not hollow`, async () => {
      const t0 = performance.now()
      const result = await grahaPortraitCapability.handler(
        { chart_id: chartId, graha: 'Saturn' },
        undefined,
      )
      const elapsedMs = performance.now() - t0
      console.log(`[GATE] ${label} chart Saturn portrait — latency ${elapsedMs.toFixed(1)}ms`)

      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>

      // Identity resolved correctly.
      expect(content['graha']).toBe('Saturn')
      expect(content['graha_code']).toBe('SAT')

      // ── position: sign/house/nakshatra/pada facts for Saturn, not empty ──
      const position = content['position'] as Record<string, unknown>
      expect((position['rows'] as unknown[]).length).toBeGreaterThan(0)

      // ── dignity: at least the 4 operative vargas (D1/D9/D10/D60) present ──
      const dignity = content['dignity'] as Record<string, unknown>
      expect((dignity['operative_varga_rows'] as unknown[]).length).toBeGreaterThanOrEqual(4)
      expect((dignity['all_varga_rows'] as unknown[]).length).toBeGreaterThan(4)

      // ── functional_nature: benefic/malefic/yoga-karaka classification present ──
      const functionalNature = content['functional_nature'] as Record<string, unknown>
      expect((functionalNature['rows'] as unknown[]).length).toBeGreaterThan(0)

      // ── strength: shadbala decomposition rows present (the get_strength fix) ──
      const strength = content['strength'] as Record<string, unknown>
      expect((strength['rows'] as unknown[]).length).toBeGreaterThan(0)

      // ── avasthas: baladi/jagrad/etc rows present ──
      const avasthas = content['avasthas'] as Record<string, unknown>
      expect((avasthas['rows'] as unknown[]).length).toBeGreaterThan(0)

      // ── yogas: section present with an honest note; parivartana count is a number ──
      const yogas = content['yogas'] as Record<string, unknown>
      expect(typeof yogas['note']).toBe('string')
      expect(typeof yogas['parivartana_count']).toBe('number')

      // ── dashas: Saturn Mahadasha period(s) across the lifetime ──
      const dashas = content['dashas'] as Record<string, unknown>
      expect((dashas['rows'] as unknown[]).length).toBeGreaterThan(0)

      // ── cgm_neighborhood: real graph traversal ran (about-resolution present) ──
      const cgm = content['cgm_neighborhood'] as Record<string, unknown>
      expect(cgm['about_resolution']).toBeTruthy()

      // ── completeness receipt: every requested section resolved (no error rows) ──
      const completeness = content['completeness'] as Record<string, string>
      for (const [section, status] of Object.entries(completeness)) {
        expect(status, `section "${section}" should not error`).not.toBe('error')
      }
      expect(content['errors']).toBeUndefined()

      console.log(`[GATE] ${label} chart — completeness:`, completeness)
    }, 30_000)
  }
})
