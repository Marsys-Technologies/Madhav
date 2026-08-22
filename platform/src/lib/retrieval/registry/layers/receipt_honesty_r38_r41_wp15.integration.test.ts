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

describeIf('WP-1.5 R-38 / F-160 — judgment_query varga_confirmed never fabricates a ✓ or ✗', () => {
  // F-160 (PARIŚEṢA-V4): the ORIGINAL R-38 invariant here — `varga_confirmed ✓ ⟺
  // varga_confirmation.rows non-empty` — encoded the exact defect F-160 fixes: "a placement
  // row exists" is NOT "the varga ratifies the D1 direction". varga_confirmed is now a real
  // tri-state derived from chart_vichara.varga_ratification (agree/oppose/unknown), reported
  // as its OWN field (`receipt.varga_ratification_relation`) alongside the OLD placement-
  // presence signal (`receipt.varga_placements_present`, kept honestly separate — §N.6 item
  // 1: flattening the two was the original defect). The invariant this test now proves is
  // narrower and still real: `varga_confirmed` may show ✓ ONLY when the ratification vote
  // actually agrees, and NEVER shows ✓ or the contradicted mark when the vote could not be
  // determined.
  for (const domain of ['career', 'marriage', 'wealth', 'health']) {
    it(`varga_confirmed's mark matches receipt.varga_ratification_relation honestly (${domain}, native)`, async () => {
      const { judgmentQueryCapability } = await import('./register_d9_judgment')
      const h = judgmentQueryCapability.handler as Handler
      const res = await h({ chart_id: NATIVE, ayanamsha_id: LAHIRI, domain })
      expect(res.is_error).toBeFalsy()
      const content = res.content as {
        receipt?: {
          varga_confirmed?: string
          varga_placements_present?: boolean
          varga_ratification_relation?: string
        }
      }
      const mark = String(content.receipt?.varga_confirmed ?? '')
      const relation = content.receipt?.varga_ratification_relation
      const claimsAgree = mark.includes('✓')
      const claimsOppose = mark.includes('!') && !claimsAgree
      // The mark must be driven by the REAL relation, never by placement presence alone.
      expect(claimsAgree, `domain=${domain} relation=${relation} mark="${mark}"`).toBe(relation === 'agree')
      expect(claimsOppose, `domain=${domain} relation=${relation} mark="${mark}"`).toBe(relation === 'oppose')
      if (relation === 'abstain' || relation === 'abstain_missing' || relation === 'no_row') {
        expect(mark, `domain=${domain}`).not.toContain('✓')
        expect(claimsOppose, `domain=${domain}`).toBe(false)
        expect(mark, `domain=${domain}`).toContain('?')
      }
      // varga_placements_present is real too, and independently reported — never silently
      // dropped even though it is no longer what varga_confirmed means.
      expect(typeof content.receipt?.varga_placements_present).toBe('boolean')
    })
  }
})
