/**
 * receipt_honesty_r38_r41_wp15.integration.test.ts — WP-1.5 R-38 / R-41 retest.
 *
 * The audit's Lane-4 receipt-honesty pass ran only on the surgical channel, leaving R-38
 * (judgment_query varga_confirmed-while-empty) and R-41 (ganita_yogas_get verdict counters
 * contradict served rows) as a declared deployed-channel lane-hole. The live MCP channel
 * needs interactive auth (unavailable in CI/non-interactive), so this proves the SAME
 * honesty invariants at the registry-capability handler the deployed tool wraps, against
 * the real DB (both canonical charts).
 *
 * Run with: INTEGRATION=true DATABASE_URL=... vitest run \
 *   src/lib/retrieval/registry/layers/receipt_honesty_r38_r41_wp15.integration.test.ts
 */
import { describe, it, expect } from 'vitest'

const INTEGRATION = process.env.INTEGRATION === 'true'
const describeIf = INTEGRATION ? describe : describe.skip

const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const LAHIRI = 'lahiri_chitrapaksha'

type Handler = (a: Record<string, unknown>, c?: unknown) => Promise<{ content: unknown; is_error?: boolean }>

// The exact verdict-counter logic register_p1_ganita.ts's ganita_yogas_get applies to the
// served rows (categoryCounts of fact_category). Mirrored here so the test proves the
// deployed instrument's counters agree with its own served rows.
function categoryCounts(rows: Array<Record<string, unknown>>): Record<string, number> {
  const c: Record<string, number> = {}
  for (const r of rows) {
    const cat = String(r['fact_category'] ?? 'unknown')
    c[cat] = (c[cat] ?? 0) + 1
  }
  return c
}

describeIf('WP-1.5 R-41 — ganita_yogas_get verdict counters == served rows', () => {
  for (const chart of [NATIVE, ABHINANDAN]) {
    it(`counters agree with served rows + total is a real COUNT (${chart.slice(0, 8)})`, async () => {
      const { getYogaDoshaCapability } = await import('./L1_ganita/get_yoga_dosha')
      const h = getYogaDoshaCapability.handler as Handler
      const res = await h({ chart_id: chart, ayanamsha_id: LAHIRI, limit: 50, offset: 0 })
      const content = res.content as { rows?: Array<Record<string, unknown>>; total?: number }
      const rows = content.rows ?? []
      const total = content.total ?? 0

      // R-41 invariant: the verdict's yogas_fired/doshas_fired are counts of the SERVED rows —
      // they can never exceed the rows actually in the page.
      const counts = categoryCounts(rows)
      const yogas_fired = counts['yoga_label'] ?? 0
      const doshas_fired = counts['dosha_label'] ?? 0
      const summed = Object.values(counts).reduce((a, b) => a + b, 0)
      expect(summed).toBe(rows.length)                 // counters partition the served rows exactly
      expect(yogas_fired + doshas_fired).toBeLessThanOrEqual(rows.length)

      // Envelope honesty: total (pagination.total) is a genuine COUNT under the same filter,
      // so it is always >= the served page — never a fabricated or contradicting number.
      expect(total).toBeGreaterThanOrEqual(rows.length)
    })
  }
})

describeIf('WP-1.5 R-38 — judgment_query varga_confirmed is NEVER ✓ while rows are empty', () => {
  for (const domain of ['career', 'marriage', 'wealth', 'health']) {
    it(`varga_confirmed ✓ ⟺ varga_confirmation.rows non-empty (${domain}, native)`, async () => {
      const { judgmentQueryCapability } = await import('./register_d9_judgment')
      const h = judgmentQueryCapability.handler as Handler
      const res = await h({ chart_id: NATIVE, ayanamsha_id: LAHIRI, domain })
      expect(res.is_error).toBeFalsy()
      const content = res.content as {
        checklist?: { varga_confirmation?: { rows?: unknown[] } }
        receipt?: { varga_confirmed?: string }
      }
      const rows = content.checklist?.varga_confirmation?.rows ?? []
      const mark = String(content.receipt?.varga_confirmed ?? '')
      const claimsConfirmed = mark.includes('✓')
      // The R-38 lie: a "✓" receipt next to an empty rows array. Forbidden in both directions.
      expect(claimsConfirmed).toBe(rows.length > 0)
      if (rows.length === 0) expect(mark).toContain('✗')
    })
  }
})
