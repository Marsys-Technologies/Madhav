/**
 * chart_facts_query_w1_bare_empty.test.ts — SATYA-ŚEṢA W1 regression pins.
 *
 * SATYA_SHESHA_BRIEF_v1_0.md §2 W1 / UAT-DARPANA S4-03: `ganita_chart_facts_get(keyword=
 * "gulika")` returned a bare `{facts: [], total: 0}` with no signal that GULIKA is served
 * under category `sensitive_point_gulika_mandi`. Fixed by adding `empty_reason` (what was
 * searched, over what universe) and `resolver_suggestion` (the concept-resolver's honest
 * pointer, same two-pass logic `concept_locate` uses) to every bare-empty response.
 *
 * Mocks `@/lib/db/client`'s `query()` (the capability's + the resolver's only I/O) and asserts
 * on the real registered capability handler pulled from the registry — matching the sibling
 * WP-1.3(f)/R6-0b-deadtools/D2-hora regression files in this directory.
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

describe('chart_facts_query — SATYA-ŚEṢA W1: bare empty carries empty_reason + resolver_suggestion', () => {
  it('the verbatim S4-03 recipe (keyword="gulika") returns a pointer to sensitive_point_gulika_mandi, not a bare empty', async () => {
    const handler = await getCapabilityHandler()
    mockQuery.mockImplementation(async (sql: string) => {
      // Both the main fetch and the disclosed-pagination COUNT return nothing — GULIKA is not
      // reachable via the `keyword` filter (it only ILIKEs fact_key/fact_value_text, never
      // fact_category). The live-category fallback query (SELECT DISTINCT fact_category) is
      // never reached because "gulika" resolves on PASS 1 (the seed alias table) — no DB round
      // trip needed for the resolver itself.
      if (/COUNT\(/i.test(sql)) return { rows: [{ total: 0 }] }
      return { rows: [] }
    })

    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'pivoted', keyword: 'gulika' })

    expect(res.is_error).toBeFalsy()
    expect(res.content['total']).toBe(0)
    expect(res.content['facts']).toEqual([])
    // The bare empty is no longer bare.
    expect(res.content['empty_reason']).toBeDefined()
    expect(String(res.content['empty_reason'])).toMatch(/keyword="gulika"/)
    const suggestion = res.content['resolver_suggestion'] as Record<string, unknown>
    expect(suggestion).toBeDefined()
    expect(suggestion).not.toBeNull()
    expect(suggestion['resolved']).toBe(true)
    expect(suggestion['fact_categories']).toContain('sensitive_point_gulika_mandi')
  })

  it('a genuine resolver MISS (no alias, no live category match) reports resolver_suggestion: null — never a fabricated pointer', async () => {
    const handler = await getCapabilityHandler()
    mockQuery.mockImplementation(async (sql: string) => {
      if (/COUNT\(/i.test(sql)) return { rows: [{ total: 0 }] }
      return { rows: [] } // live fact_category fallback also finds nothing
    })

    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', keyword: 'zzz_totally_unknown_term_zzz' })

    expect(res.content['total']).toBe(0)
    expect(res.content['resolver_suggestion']).toBeNull()
    expect(res.content['resolver_suggestion_note']).toBeDefined()
    expect(String(res.content['resolver_suggestion_note'])).toMatch(/resolver MISS/)
  })

  it('a populated query is unaffected — no empty_reason/resolver_suggestion fields when rows are actually served', async () => {
    const handler = await getCapabilityHandler()
    mockQuery.mockImplementation(async (sql: string) => {
      if (/COUNT\(/i.test(sql)) return { rows: [{ total: 1 }] }
      return {
        rows: [{
          fact_id: 'f0', fact_category: 'graha_position', fact_subject: 'SUN',
          fact_key: 'sign', fact_value_num: null, fact_value_text: 'Capricorn',
          fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c',
        }],
      }
    })

    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', planet: 'Sun' })

    expect(res.content['total']).toBe(1)
    expect(res.content['empty_reason']).toBeUndefined()
    expect(res.content['resolver_suggestion']).toBeUndefined()
  })

  it('empty_reason names the actual filters applied (category + sign compound example)', async () => {
    const handler = await getCapabilityHandler()
    mockQuery.mockImplementation(async (sql: string) => {
      if (/COUNT\(/i.test(sql)) return { rows: [{ total: 0 }] }
      return { rows: [] }
    })

    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', category: 'yoga_label', sign: 'Aries' })

    const reason = String(res.content['empty_reason'])
    expect(reason).toMatch(/category="yoga_label"/)
    expect(reason).toMatch(/sign="Aries"/)
    expect(reason).toMatch(new RegExp(CHART_ID))
  })

  it('no free-text term available (only structural filters) reports resolver_suggestion: null with an explanatory note, no DB round trip for resolution', async () => {
    const handler = await getCapabilityHandler()
    mockQuery.mockImplementation(async (sql: string) => {
      if (/COUNT\(/i.test(sql)) return { rows: [{ total: 0 }] }
      return { rows: [] }
    })

    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: AYANAMSHA, shape: 'rows', house: 7 })

    expect(res.content['resolver_suggestion']).toBeNull()
    expect(String(res.content['resolver_suggestion_note'])).toMatch(/No free-text term/)
  })
})
