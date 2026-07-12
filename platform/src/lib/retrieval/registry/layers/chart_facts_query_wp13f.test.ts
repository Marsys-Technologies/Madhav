/**
 * chart_facts_query_wp13f.test.ts — WP-1.3(f) / LCA-3, LCA-3-EXT regression pins.
 *
 * Covers the four query_chart_facts remediations:
 *   1. fact_subject filter actually FILTERS (compiles a fact_subject = ANY predicate;
 *      composes with category). LCA-3.
 *   2. Invalid / unrecognized category -> honest empty (0 rows), never the full-chart dump.
 *      LCA-3.
 *   3. Disclosed pagination: `total` (true count over the whole matching set) + `more_available`
 *      reflect the real subject/row count, not just this page. LCA-3-EXT.
 *   4. ayanamsha_id is honored by the handler (queried in the WHERE clause) — the primary tool's
 *      6-ayanamsha reachability fix lives at the MCP bridge (see registry_bridge ayanamsha test);
 *      here we pin that the handler queries exactly the ayanamsha it is handed.
 *
 * Mocks `@/lib/db/client`'s `query()` (the capability's only I/O) and asserts on the real
 * registered capability handler pulled from the registry — matching the sibling deadtools test.
 *
 * The handler issues a main row fetch and a separate COUNT query (for the disclosed total).
 * Tests key on the SQL text (COUNT(...) vs ORDER BY ...) rather than call index so they stay
 * robust to call ordering and added intermediate queries.
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
  await import('../catalog')
  const { getCapability } = await import('../index')
  const cap = getCapability('marsys://tool/L1/chart_facts_query')
  if (!cap) throw new Error('chart_facts_query capability not registered')
  return cap.handler as (args: Record<string, unknown>, ctx?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
}

type QCall = { sql: string; params: unknown[] }
function callsOf(): QCall[] {
  return mockQuery.mock.calls.map(([sql, params]) => ({ sql: String(sql), params: (params ?? []) as unknown[] }))
}
function countCall(): QCall | undefined { return callsOf().find(c => /COUNT\(/i.test(c.sql)) }
function mainCall(): QCall | undefined { return callsOf().find(c => /ORDER BY/i.test(c.sql)) }

/** Wires the mock so the COUNT query returns `total` and every other query returns `rows`. */
function wire(total: number, rows: Array<Record<string, unknown>>) {
  mockQuery.mockImplementation((sql: string) => {
    if (/COUNT\(/i.test(sql)) return Promise.resolve({ rows: [{ total }] })
    return Promise.resolve({ rows })
  })
}

describe('WP-1.3(f) LCA-3 — fact_subject filter actually filters', () => {
  it('compiles a fact_subject = ANY predicate with the supplied subjects', async () => {
    const handler = await getCapabilityHandler()
    wire(1, [{
      fact_id: 'f0', fact_category: 'graha_position', fact_subject: 'LAGNA',
      fact_key: 'sign', fact_value_num: null, fact_value_text: 'Aries',
      fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c',
    }])

    await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', fact_subject: 'LAGNA' })

    const main = mainCall()
    expect(main).toBeDefined()
    expect(main!.sql).toMatch(/fact_subject = ANY/)
    // The supplied subject list is bound as a parameter (not interpolated) — proves it filters.
    expect(main!.params).toContainEqual(['LAGNA'])
  })

  it('splits a comma-list into multiple subjects', async () => {
    const handler = await getCapabilityHandler()
    wire(2, [])
    await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', fact_subject: 'SUN, MOON' })
    expect(mainCall()!.params).toContainEqual(['SUN', 'MOON'])
  })
})

describe('WP-1.3(f) LCA-3 — invalid category is honest-empty, never a dump', () => {
  it('unrecognized category compiles a fact_category = ANY filter and returns 0 rows (no error dump)', async () => {
    const handler = await getCapabilityHandler()
    wire(0, []) // DB returns nothing for a category that does not exist
    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', category: 'bogus_invalid' })

    expect(res.is_error).toBeFalsy()
    // The filter was actually applied (the whole point — not ignored + full dump).
    expect(mainCall()!.sql).toMatch(/fact_category = ANY/)
    expect(mainCall()!.params).toContainEqual(['bogus_invalid'])
    // Honest empty.
    expect(res.content['rows']).toEqual([])
    expect(res.content['returned_count']).toBe(0)
    expect(res.content['total']).toBe(0)
    expect(res.content['more_available']).toBe(false)
  })
})

describe('WP-1.3(f) LCA-3-EXT — disclosed pagination with a real total', () => {
  it('shape="rows": total is the true count and more_available=true when rows remain past the page', async () => {
    const handler = await getCapabilityHandler()
    const page = Array.from({ length: 100 }, (_, i) => ({
      fact_id: `f${i}`, fact_category: 'graha_position', fact_subject: `SUBJ${i}`,
      fact_key: 'sign', fact_value_num: null, fact_value_text: 'Aries',
      fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c',
    }))
    wire(5566, page) // 5,566 matching rows total; this page served 100
    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', limit: 100, offset: 0 })

    expect(res.content['total']).toBe(5566)
    expect(res.content['returned_count']).toBe(100)
    expect(res.content['more_available']).toBe(true)
    expect(countCall()).toBeDefined()
    expect(countCall()!.sql).toMatch(/COUNT\(\*\)/i) // rows-shape counts raw rows
  })

  it('shape="pivoted": total counts DISTINCT subjects and more_available=false when the page covers them all', async () => {
    const handler = await getCapabilityHandler()
    const rows = [
      { fact_id: 'a', fact_category: 'yoga_label', fact_subject: 'YOGA_1', fact_key: 'name', fact_value_num: null, fact_value_text: 'Gajakesari', fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c' },
      { fact_id: 'b', fact_category: 'yoga_label', fact_subject: 'YOGA_2', fact_key: 'name', fact_value_num: null, fact_value_text: 'Budhaditya', fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c' },
    ]
    wire(2, rows) // 2 distinct subjects, both served on this page
    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'pivoted', limit: 100, offset: 0 })

    expect(res.content['total']).toBe(2)
    expect(res.content['returned_count']).toBe(2)
    expect(res.content['more_available']).toBe(false)
    expect(countCall()!.sql).toMatch(/COUNT\(DISTINCT fact_subject\)/i) // pivoted counts subjects
  })

  it('more_available=true when offset+page < total (pivoted mid-page)', async () => {
    const handler = await getCapabilityHandler()
    const rows = Array.from({ length: 50 }, (_, i) => ({
      fact_id: `s${i}`, fact_category: 'yoga_label', fact_subject: `Y${i}`, fact_key: 'name',
      fact_value_num: null, fact_value_text: 'X', fact_value_jsonb: null, unit: null,
      verification_pass_status: 'pass', citation_ref: 'c',
    }))
    wire(5566, rows)
    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'pivoted', limit: 50, offset: 0 })
    expect(res.content['total']).toBe(5566)
    expect(res.content['more_available']).toBe(true)
  })
})

describe('WP-1.3(f) — handler honors the ayanamsha it is handed', () => {
  it('queries the exact ayanamsha_id in the WHERE clause (true_chitra, not lahiri)', async () => {
    const handler = await getCapabilityHandler()
    wire(1, [])
    await handler({ chart_id: CHART_ID, ayanamsha_id: 'true_chitra', shape: 'rows' })
    // $2 is the ayanamsha bind on both the count and the main query.
    expect(mainCall()!.params[1]).toBe('true_chitra')
    expect(countCall()!.params[1]).toBe('true_chitra')
  })
})
