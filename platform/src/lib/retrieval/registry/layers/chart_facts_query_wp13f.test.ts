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

// D-1.5b Gate B (CR-18 / B_shadbala_ratio) — ayanamsha-INVARIANT facts surface alongside the
// requested ayanamsha. `required_rupa` (graha_shadbala_total) is stored under
// ayanamsha_id='INVARIANT' (a fixed BPHS constant), while `ratio`/`rupa` are per-ayanamsha.
// Filtering strictly on `ayanamsha_id = $2` dropped required_rupa from the pivot (0/9), failing
// Gate B, which requires each shadbala row to carry BOTH ratio AND required_rupa.
describe('D-1.5b Gate B — INVARIANT-scoped facts (required_rupa) surface with the requested ayanamsha', () => {
  it('the WHERE clause includes INVARIANT alongside the bound ayanamsha (main + count)', async () => {
    const handler = await getCapabilityHandler()
    wire(1, [])
    await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows' })
    // $2 is still the caller's ayanamsha, and INVARIANT is unioned in for ayanamsha-independent facts.
    expect(mainCall()!.sql).toMatch(/ayanamsha_id IN \(\$2, 'INVARIANT'\)/)
    expect(countCall()!.sql).toMatch(/ayanamsha_id IN \(\$2, 'INVARIANT'\)/)
    expect(mainCall()!.params[1]).toBe(AYANAMSHA)
  })

  it('pivots an INVARIANT required_rupa into the SAME wide row as the per-ayanamsha ratio/rupa for a graha', async () => {
    const handler = await getCapabilityHandler()
    // Simulate the DB returning, for subject SUN in graha_shadbala_total: the per-ayanamsha
    // `ratio` + `rupa` rows AND the INVARIANT `required_rupa` row (now reachable via the widened
    // WHERE). All three share fact_subject='SUN', so the pivot must collapse them into one row.
    const rows = [
      { fact_id: 'r', fact_category: 'graha_shadbala_total', fact_subject: 'SUN', fact_key: 'ratio', fact_value_num: 1.694, fact_value_text: null, fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c' },
      { fact_id: 'u', fact_category: 'graha_shadbala_total', fact_subject: 'SUN', fact_key: 'rupa', fact_value_num: 8.47, fact_value_text: null, fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c' },
      { fact_id: 'q', fact_category: 'graha_shadbala_total', fact_subject: 'SUN', fact_key: 'required_rupa', fact_value_num: 5, fact_value_text: null, fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c' },
    ]
    wire(1, rows)
    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'pivoted', category: 'graha_shadbala_total' })

    const facts = res.content['facts'] as Array<Record<string, unknown>>
    const sun = facts.find(f => f['fact_subject'] === 'SUN')
    expect(sun).toBeDefined()
    // Both the per-ayanamsha ratio AND the INVARIANT required_rupa must be present on the row.
    expect(sun!['ratio']).toBe(1.694)
    expect(sun!['required_rupa']).toBe(5)
    expect(sun!['rupa']).toBe(8.47)
    // required_rupa carries its own fact_id for §N.5 back-reference.
    expect((sun!['fact_ids'] as Record<string, string>)['required_rupa']).toBe('q')
  })
})
