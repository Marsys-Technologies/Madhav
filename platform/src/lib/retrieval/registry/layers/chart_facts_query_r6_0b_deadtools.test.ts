/**
 * chart_facts_query_r6_0b_deadtools.test.ts — R6 lane 0b-deadtools regression pins.
 *
 * V-8: `query_chart_facts` (marsys://tool/L1/chart_facts_query) silently ignored `offset` —
 *   page 2 === page 1 for both shape="rows" and shape="pivoted". Fixed by reading `offset`
 *   from args, widening the raw-row fetch cap to cover `offset + limit`, and slicing at
 *   `[offset, offset+limit)` instead of `[0, limit)`.
 *
 * P-6: `sign` + `divisional_chart` together always returned 0 rows — the sign filter bound
 *   to chart_facts's OWN fact_key='sign' rows, which only exist for D1-scoped categories;
 *   no divisional-chart subject (e.g. "D9_JUP") ever carries a fact_key='sign' row in
 *   chart_facts (the real per-varga sign lives in `chart_divisionals`). Fixed by resolving
 *   the sign match against chart_divisionals when divisional_chart is present, then
 *   translating matched grahas into chart_facts's divisional fact_subject codes.
 *
 * Mocks `@/lib/db/client`'s `query()` (the capability's only I/O) and asserts on the real
 * registered capability handler pulled from the registry — not a reimplementation.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'

beforeEach(() => {
  mockQuery.mockReset()
})

async function getCapabilityHandler() {
  // Triggers registration of chart_facts_query (and every other layer capability) against
  // the mocked db client, matching how the real primitives route loads the registry.
  await import('../catalog')
  const { getCapability } = await import('../index')
  const cap = getCapability('marsys://tool/L1/chart_facts_query')
  if (!cap) throw new Error('chart_facts_query capability not registered')
  return cap.handler as (args: Record<string, unknown>, ctx?: unknown) => Promise<{ content: unknown; is_error?: boolean }>
}

describe('chart_facts_query — R6 0b-deadtools (V-8) offset pagination fix', () => {
  it('shape="rows": offset=0 and offset=5 (limit=5) return DIFFERENT rows from the same underlying set — page 2 !== page 1', async () => {
    const handler = await getCapabilityHandler()
    const allRows = Array.from({ length: 20 }, (_, i) => ({
      fact_id: `f${i}`, fact_category: 'graha_position', fact_subject: `SUBJ${i}`,
      fact_key: 'sign', fact_value_num: null, fact_value_text: 'Aries',
      fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c',
    }))
    mockQuery.mockResolvedValue({ rows: allRows })

    const page1 = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', limit: 5, offset: 0 })
    const page2 = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', limit: 5, offset: 5 })

    const rows1 = (page1.content as { rows: Array<{ fact_id: string }> }).rows
    const rows2 = (page2.content as { rows: Array<{ fact_id: string }> }).rows
    expect(rows1.map(r => r.fact_id)).toEqual(['f0', 'f1', 'f2', 'f3', 'f4'])
    expect(rows2.map(r => r.fact_id)).toEqual(['f5', 'f6', 'f7', 'f8', 'f9'])
    expect(rows1).not.toEqual(rows2)
  })

  it('the raw-row fetch cap grows with offset (previously fixed at limit*20 regardless of offset)', async () => {
    const handler = await getCapabilityHandler()
    mockQuery.mockResolvedValue({ rows: [] })

    await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', limit: 10, offset: 100 })

    const [, params] = mockQuery.mock.calls[0] as [string, unknown[]]
    const rowCap = params[params.length - 1] as number
    // (offset + limit) * 20 = (100 + 10) * 20 = 2200 — must exceed the old limit*20=200 cap.
    expect(rowCap).toBeGreaterThanOrEqual(2200)
  })
})

describe('chart_facts_query — R6 0b-deadtools (P-6) divisional sign filter fix', () => {
  it('divisional_chart + sign resolves against chart_divisionals, not chart_facts fact_key=sign', async () => {
    const handler = await getCapabilityHandler()
    const calls: Array<{ sql: string; params: unknown[] }> = []
    mockQuery.mockImplementation(async (sql: string, params: unknown[]) => {
      calls.push({ sql, params })
      if (sql.includes('FROM chart_divisionals')) {
        return { rows: [{ graha: 'Jupiter' }] }
      }
      return { rows: [] }
    })

    await handler({
      chart_id: CHART_ID, ayanamsha_id: AYANAMSHA,
      divisional_chart: 'D9', sign: 'Gemini', shape: 'rows',
    })

    const divisionalsCall = calls.find(c => c.sql.includes('FROM chart_divisionals'))
    expect(divisionalsCall).toBeDefined()
    expect(divisionalsCall!.params).toEqual([CHART_ID, AYANAMSHA, 'D9', 'Gemini'])

    // The main chart_facts query must filter on the TRANSLATED fact_subject code
    // ("D9_JUP"), never on a fact_key='sign' subquery scoped to chart_facts alone.
    const mainCall = calls.find(c => c.sql.includes('FROM chart_facts') && !c.sql.includes('chart_divisionals'))
    expect(mainCall).toBeDefined()
    expect(mainCall!.sql).not.toMatch(/fact_key\s*=\s*\$\d+\s+AND\s+fact_value_text ILIKE/)
    expect(mainCall!.params).toContainEqual(['D9_JUP'])
  })

  it('no chart_divisionals match for the varga/sign combo returns 0 rows honestly (no fabricated fallback)', async () => {
    const handler = await getCapabilityHandler()
    mockQuery.mockImplementation(async (sql: string) => {
      if (sql.includes('FROM chart_divisionals')) return { rows: [] } // no graha in that sign
      return { rows: [{ fact_id: 'should-not-appear', fact_category: 'x', fact_subject: 'D9_JUP', fact_key: 'k', fact_value_text: 'v', fact_value_num: null, fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c' }] }
    })

    const result = await handler({
      chart_id: CHART_ID, ayanamsha_id: AYANAMSHA,
      divisional_chart: 'D9', sign: 'Capricorn', shape: 'rows',
    })

    // The second mockQuery call (main fetch) is invoked with an empty ANY() array — real
    // Postgres would return 0 rows for that; our mock can't enforce that semantic, so this
    // test instead pins the CONTRACT: the empty-match array is what's sent, not silently
    // widened to "match everything" or defaulted to the D1 bare-sign subquery.
    const mainCallArgs = mockQuery.mock.calls.find(([sql]) => (sql as string).includes('FROM chart_facts') && !(sql as string).includes('chart_divisionals'))!
    const mainParams = mainCallArgs[1] as unknown[]
    expect(mainParams).toContainEqual([])
    void result
  })
})
