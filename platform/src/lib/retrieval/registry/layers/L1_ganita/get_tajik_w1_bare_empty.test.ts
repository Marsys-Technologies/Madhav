/**
 * get_tajik_w1_bare_empty.test.ts — SATYA-ŚEṢA W1 sibling-sweep regression pin.
 *
 * get_tajik has no free-text/guessable filter (its 3 fact_categories are fixed), so a bare
 * empty here gets an honest `empty_reason` disclosure — never a resolver_suggestion (there is
 * no term to resolve). See SATYA_SHESHA_BRIEF_v1_0.md §2 W1 ("sweep sibling query-shaped
 * L1/L2 tools for the same bare-empty shape").
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

beforeEach(() => {
  mockQuery.mockReset()
})

async function getCapabilityHandler() {
  await import('../../catalog')
  const { getCapability } = await import('../../index')
  const cap = getCapability('marsys://tool/L1/get_tajik')
  if (!cap) throw new Error('get_tajik capability not registered')
  return cap.handler as (args: Record<string, unknown>, ctx?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
}

describe('get_tajik — SATYA-ŚEṢA W1: bare empty carries empty_reason', () => {
  it('zero hadda-lord facts AND zero varsha-year-lord rows -> empty_reason disclosed', async () => {
    const handler = await getCapabilityHandler()
    mockQuery.mockResolvedValue({ rows: [] }) // COUNT(*) AS n rows are empty too -> n undefined -> 0

    const res = await handler({ chart_id: CHART_ID })

    expect(res.is_error).toBeFalsy()
    expect(res.content['total']).toBe(0)
    expect(res.content['empty_reason']).toBeDefined()
    expect(String(res.content['empty_reason'])).toMatch(new RegExp(CHART_ID))
  })

  it('real rows present -> no empty_reason', async () => {
    const handler = await getCapabilityHandler()
    mockQuery.mockImplementation(async (sql: string) => {
      if (/COUNT\(\*\)::int AS n FROM chart_facts/.test(sql)) return { rows: [{ n: 1 }] }
      if (/COUNT\(\*\)::int AS n FROM l1_tajik_varsha_year_lords/.test(sql)) return { rows: [{ n: 0 }] }
      if (/FROM chart_facts/.test(sql)) {
        return { rows: [{ fact_id: 'f0', fact_category: 'tajik_hadda_lord', ayanamsha_id: 'lahiri_chitrapaksha', fact_key: 'hadda_lord', fact_value_text: 'Venus', fact_value_num: null, fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c' }] }
      }
      return { rows: [] }
    })

    const res = await handler({ chart_id: CHART_ID, include_varsha: false })

    expect(res.content['total']).toBe(1)
    expect(res.content['empty_reason']).toBeUndefined()
  })
})
