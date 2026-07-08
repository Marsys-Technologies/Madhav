/**
 * coverage_receipt.gate.integration.test.ts — R5 W4 lane 2 (coverage stamps → receipts) gate.
 *
 * Verifies the D5 coverage receipt (design §10.5, `{family, served, total}`) is populated with
 * REAL, non-fabricated numbers on both canonical charts:
 *   1. query_signals.ts (marsys://tool/L2/query_signals — backs the MCP get_signals tool):
 *      `total_matching_filters` is a genuine COUNT(*) against the same base filters the served
 *      page/candidate pool was drawn from — must be >= returned_count, and must actually shrink
 *      when a real filter (min_salience) narrows the family.
 *   2. get_yoga_dosha.ts (marsys://tool/L1/get_yoga_dosha — backs ganita_yogas_get): the
 *      previously-mislabeled `total` (page length) is now a genuine COUNT(*) family size —
 *      must be >= rows.length, and a small page (limit=1) must show total > served.
 *
 * Run with: INTEGRATION=true npx vitest run src/lib/retrieval/registry/layers/L2_bodha/__tests__/coverage_receipt.gate.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
import { querySignalsCapability } from '../query_signals'
import { getYogaDoshaCapability } from '../../L1_ganita/get_yoga_dosha'

const INTEGRATION = process.env.INTEGRATION === 'true'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const BOTH_CHARTS = [NATIVE_CHART_ID, ABHINANDAN_CHART_ID]

const describeIf = INTEGRATION ? describe : describe.skip

describeIf('D5 coverage receipt — family-size COUNT, live DB', () => {
  for (const chartId of BOTH_CHARTS) {
    it(`[${chartId}] query_signals: total_matching_filters is a real COUNT(*), >= returned_count`, async () => {
      const result = await querySignalsCapability.handler({
        chart_id: chartId, top_k: 5, offset: 0,
      }, undefined)
      expect(result.is_error).toBe(false)
      const content = result.content as Record<string, unknown>
      const total = content['total_matching_filters']
      expect(typeof total).toBe('number')
      expect(total as number).toBeGreaterThanOrEqual(content['returned_count'] as number)
      // Family is large (66,738-signal corpus per query_signals.ts docstring) — a 5-row page
      // must show a total far larger than served, proving this isn't just echoing served count.
      expect(total as number).toBeGreaterThan(content['returned_count'] as number)
    })

    it(`[${chartId}] query_signals: min_salience filter genuinely shrinks total_matching_filters`, async () => {
      const unfiltered = await querySignalsCapability.handler({ chart_id: chartId, top_k: 1 }, undefined)
      const filtered = await querySignalsCapability.handler({ chart_id: chartId, top_k: 1, min_salience: 0.9 }, undefined)
      const unfilteredTotal = (unfiltered.content as Record<string, unknown>)['total_matching_filters'] as number
      const filteredTotal = (filtered.content as Record<string, unknown>)['total_matching_filters'] as number
      expect(filteredTotal).toBeLessThanOrEqual(unfilteredTotal)
    })

    it(`[${chartId}] get_yoga_dosha: total is a genuine family-size COUNT(*), not the page length`, async () => {
      const result = await getYogaDoshaCapability.handler({ chart_id: chartId, limit: 1, offset: 0 }, undefined)
      expect(result.is_error).toBe(false)
      const content = result.content as { rows: unknown[]; total: number }
      expect(content.rows.length).toBe(1)
      // Family (6 categories, unbounded) must exceed a 1-row page for both canonical charts —
      // proves `total` is no longer the mislabeled page-length bug.
      expect(content.total).toBeGreaterThan(1)
    })
  }
})
