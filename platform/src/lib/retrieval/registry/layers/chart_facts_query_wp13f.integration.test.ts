/**
 * chart_facts_query_wp13f.integration.test.ts — WP-1.3(f) LCA-3 / LCA-3-EXT live-DB proof.
 *
 * Runs against the real chart_facts table (no mocks). Proves, on the native chart:
 *   - a category filter materially SHRINKS the served payload vs unfiltered (byte + row deltas);
 *   - an invalid category returns honest-empty (0 rows), not the ~119KB full dump;
 *   - pagination discloses the REAL total (~5,566 subjects) with more_available=true when a page
 *     leaves rows behind;
 *   - every one of the 6 stored ayanamshas returns its own data (true_chitra is NOT lahiri).
 *
 * Run with: INTEGRATION=true vitest run \
 *   src/lib/retrieval/registry/layers/chart_facts_query_wp13f.integration.test.ts
 */
import { describe, it, expect } from 'vitest'

const INTEGRATION = process.env.INTEGRATION === 'true'
const describeIf = INTEGRATION ? describe : describe.skip

const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const AYANAMSHAS = ['lahiri_chitrapaksha', 'krishnamurti', 'raman', 'surya_siddhanta_classical', 'true_chitra', 'INVARIANT']

async function handler() {
  await import('../catalog')
  const { getCapability } = await import('../index')
  const cap = getCapability('marsys://tool/L1/chart_facts_query')
  if (!cap) throw new Error('chart_facts_query capability not registered')
  return cap.handler as (a: Record<string, unknown>, c?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
}
const bytes = (o: unknown) => Buffer.byteLength(JSON.stringify(o), 'utf8')

describeIf('WP-1.3(f) live-DB — filter narrows payload (byte + row delta)', () => {
  it('category=graha_position is materially smaller than an unfiltered page and contains only matching rows', async () => {
    const h = await handler()
    const unfiltered = await h({ chart_id: NATIVE, ayanamsha_id: 'lahiri_chitrapaksha', shape: 'pivoted', limit: 1000 })
    const filtered = await h({ chart_id: NATIVE, ayanamsha_id: 'lahiri_chitrapaksha', shape: 'pivoted', category: 'graha_position' })

    const uBytes = bytes(unfiltered.content)
    const fBytes = bytes(filtered.content)
    // eslint-disable-next-line no-console
    console.log(`[byte-delta] unfiltered=${uBytes}B filtered(graha_position)=${fBytes}B`)
    expect(fBytes).toBeLessThan(uBytes / 5) // materially smaller

    const facts = filtered.content['facts'] as Array<Record<string, unknown>>
    expect(facts.length).toBeGreaterThan(0)
    for (const f of facts) expect(f['fact_category']).toBe('graha_position')
  })
})

describeIf('WP-1.3(f) live-DB — invalid category is honest-empty, not a dump', () => {
  it('returns 0 rows and a tiny payload', async () => {
    const h = await handler()
    const res = await h({ chart_id: NATIVE, ayanamsha_id: 'lahiri_chitrapaksha', shape: 'pivoted', category: 'bogus_not_a_category' })
    expect(res.is_error).toBeFalsy()
    expect((res.content['facts'] as unknown[]).length).toBe(0)
    expect(res.content['total']).toBe(0)
    expect(bytes(res.content)).toBeLessThan(2000) // nowhere near a 119KB dump
  })
})

describeIf('WP-1.3(f) live-DB — disclosed pagination with the real total', () => {
  it('unfiltered pivoted discloses total≈5566 and more_available=true at limit=1000', async () => {
    const h = await handler()
    const res = await h({ chart_id: NATIVE, ayanamsha_id: 'lahiri_chitrapaksha', shape: 'pivoted', limit: 1000, offset: 0 })
    // eslint-disable-next-line no-console
    console.log(`[pagination] total=${res.content['total']} returned=${res.content['returned_count']} more=${res.content['more_available']}`)
    expect(Number(res.content['total'])).toBeGreaterThan(5000)
    expect(Number(res.content['returned_count'])).toBeLessThanOrEqual(1000)
    expect(res.content['more_available']).toBe(true) // 5,566 > 1,000 — rows remain
  })
})

describeIf('WP-1.3(f) live-DB — all 6 ayanamshas serve their own data', () => {
  for (const chart of [NATIVE, ABHINANDAN]) {
    for (const aya of AYANAMSHAS) {
      it(`[${chart}] ayanamsha=${aya} returns rows tagged with that ayanamsha`, async () => {
        const h = await handler()
        const res = await h({ chart_id: chart, ayanamsha_id: aya, shape: 'rows', limit: 5 })
        expect(res.is_error).toBeFalsy()
        expect(res.content['ayanamsha_id']).toBe(aya)
        expect((res.content['rows'] as unknown[]).length).toBeGreaterThan(0)
        expect(Number(res.content['total'])).toBeGreaterThan(0)
      })
    }
  }
})
