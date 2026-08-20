/**
 * get_strength_f60_total_count.test.ts — F-60 regression.
 *
 * Defect (campaign ledger F-60, evidence_summary): `get_strength.ts` reported
 * `total: servedRows.length` — a false, post-cap, post-filter PAGE LENGTH masquerading
 * as a true row count — while a silent `Math.min(limit, 2000)` cap could additionally
 * truncate what that page contained without ever disclosing that a cap was hit. A
 * caller reading `total` had no way to tell "this is everything" from "this is a
 * fragment of something much bigger".
 *
 * Fix: a dedicated `total_available` field, populated by a COUNT(*) query that shares
 * the exact same WHERE predicate as the SELECT (chart_id/categories/ayanamsha_id/
 * graha_key) but is computed independent of `limit`/`offset`/the 2000-row cap/the
 * `all:false` counterfactual-row filter — plus an explicit `limit_capped` disclosure
 * whenever the caller's requested limit exceeded the hard cap.
 *
 * Every assertion below reads a field (`total_available`, `limit_capped`,
 * `requested_limit`) that did not exist on the pre-fix response at all — so this test
 * genuinely fails (TypeError-adjacent `undefined` comparisons) against the pre-fix
 * handler, not just against a changed value of an existing field.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
// A true row count much larger than any page this test requests — the number the fix
// must surface via `total_available` regardless of how few rows the SELECT itself pages
// back. Chosen independently of any generated row array so the test cannot pass by
// accident (e.g. by the fix silently reading `rows.length` under a new field name).
const TRUE_TOTAL_COUNT = 4321

function makeSelectRows(n: number): Record<string, unknown>[] {
  return Array.from({ length: n }, (_, i) => ({
    fact_id: `strength_${i}`, fact_category: 'graha_shadbala_total', fact_subject: 'SU',
    ayanamsha_id: 'lahiri_chitrapaksha', fact_key: 'total', fact_value_num: 400,
    fact_value_text: null, fact_value_jsonb: null, unit: null,
    verification_pass_status: 'pass', citation_ref: 'c',
  }))
}

async function getCapabilityHandler() {
  await import('../../catalog')
  const { getCapability } = await import('../../index')
  const cap = getCapability('marsys://tool/L1/get_strength')
  if (!cap) throw new Error('get_strength capability not registered')
  return cap.handler as (args: Record<string, unknown>, ctx?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
}

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockImplementation(async (sql: string) => {
    // address_resolver.ts's resolveFrameSign — single-subject lookup (frame:'lagna').
    if (/fact_category = \$3\s+AND fact_subject = \$4/.test(sql)) return { rows: [] }
    // get_strength.ts's own multi-graha signRes lookup — return no sign rows so the
    // `all:false` counterfactual filter is a no-op and doesn't interfere with this test's
    // row-count assertions (out of scope for F-60; covered by the MC-014 test file).
    if (/fact_category = 'graha_position'/.test(sql)) return { rows: [] }
    // The dedicated F-60 COUNT(*) query — MUST be checked before the generic SELECT
    // branch below, since both contain "FROM chart_facts".
    if (/SELECT COUNT\(\*\)/.test(sql)) return { rows: [{ total_count: TRUE_TOTAL_COUNT }] }
    if (/FROM chart_facts/.test(sql)) return { rows: makeSelectRows(3) }
    return { rows: [] }
  })
})

describe('get_strength — F-60: total_available is the true pre-cap row count, not the served page length', () => {
  it('reports total_available independently of the (much smaller) served page — and it differs from `total`', async () => {
    const handler = await getCapabilityHandler()
    const res = await handler({ chart_id: CHART_ID, limit: 3, offset: 0 })

    expect(res.is_error).toBeFalsy()
    const rows = res.content['rows'] as unknown[]
    expect(rows).toHaveLength(3)

    // The old defect: `total` was `servedRows.length` — i.e. always equal to the page.
    expect(res.content['total']).toBe(3)
    // The fix: a genuinely distinct, independently-sourced true count.
    expect(res.content['total_available']).toBe(TRUE_TOTAL_COUNT)
    expect(res.content['total_available']).not.toBe(res.content['total'])
  })

  it('the COUNT(*) query shares the filter but carries no LIMIT/OFFSET params', async () => {
    const handler = await getCapabilityHandler()
    await handler({ chart_id: CHART_ID, limit: 3, offset: 200 })

    const countCall = mockQuery.mock.calls.find((call: unknown[]) => /SELECT COUNT\(\*\)/.test(call[0] as string))
    expect(countCall).toBeDefined()
    const [countSql, countParams] = countCall as [string, unknown[]]
    expect(countSql).not.toMatch(/LIMIT/)
    expect(countSql).not.toMatch(/OFFSET/)
    // chart_id + categories only (no limit/offset values leaked into the count params).
    expect(countParams[0]).toBe(CHART_ID)
    expect(countParams).not.toContain(200)
  })

  it('discloses an explicit cap when the requested limit exceeds the 2000-row hard cap', async () => {
    const handler = await getCapabilityHandler()
    const res = await handler({ chart_id: CHART_ID, limit: 5000, offset: 0 })

    expect(res.content['limit_capped']).toBe(true)
    expect(res.content['requested_limit']).toBe(5000)
    expect(res.content['limit']).toBe(2000)
    expect(typeof res.content['note_limit_cap']).toBe('string')

    // The SELECT itself must actually have been issued with the capped limit (2000), not
    // the raw requested 5000 — the disclosure has to describe what really happened.
    const selectCall = mockQuery.mock.calls.find((call: unknown[]) => {
      const sql = call[0] as string
      return /FROM chart_facts/.test(sql) && !/SELECT COUNT\(\*\)/.test(sql)
    })
    expect(selectCall).toBeDefined()
    const [, selectParams] = selectCall as [string, unknown[]]
    expect(selectParams).toContain(2000)
    expect(selectParams).not.toContain(5000)
  })

  it('does not disclose a cap when the requested limit is within the hard cap', async () => {
    const handler = await getCapabilityHandler()
    const res = await handler({ chart_id: CHART_ID, limit: 100, offset: 0 })

    expect(res.content['limit_capped']).toBeUndefined()
    expect(res.content['requested_limit']).toBeUndefined()
    expect(res.content['limit']).toBe(100)
  })
})
