/**
 * formula_pins_readers.test.ts — BEHAVIOUR of the three chart_facts reader surfaces that serve the
 * seven multi-formula categories (chart_facts_query, get_karakas, get_sensitive_points): the row
 * reduction is deterministic and canonical-first, the ORDER BY is TOTAL, and Mrityu (no canonical
 * formula) yields an honest null headline. The served-text additions (formula_id / formula_role /
 * variants / policy fields) are pinned separately in formula_pins_tool_text.test.ts.
 *
 * Source: INVESTIGATION_L1_DUPLICATE_KEYS_v1_0.md (PR #2861) + SS decision 2026-10-01.
 * Mocks `@/lib/db/client`'s query() (the handlers' only I/O). The mock hands the handler its rows in
 * an ADVERSARIAL arrival order (variant first, and the reverse), because the pre-fix winner was
 * whichever row happened to arrive last/first.
 */
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { DK_KN, DK_PA, MR_BPHS, MR_SAR, MR_TAJ, PLAIN, SK_KN, YOGI_ALT, YOGI_BPHS, type Row } from './formula_pins_fixtures'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYA = 'lahiri_chitrapaksha'

// The catalog import registers every capability (cold start is several seconds).
beforeAll(async () => {
  await import('../../catalog')
}, 120_000)

beforeEach(() => {
  mockQuery.mockReset()
})

type Qc = { sql: string; params: unknown[] }
const calls = (): Qc[] => mockQuery.mock.calls.map(([sql, params]) => ({ sql: String(sql), params: (params ?? []) as unknown[] }))
const mainCall = (): Qc => {
  const c = calls().find(x => /ORDER BY/i.test(x.sql) && !/COUNT\(/i.test(x.sql))
  expect(c).toBeDefined()
  return c!
}
function wire(rows: Row[], total = rows.length) {
  mockQuery.mockImplementation((sql: string) =>
    /COUNT\(/i.test(sql) ? Promise.resolve({ rows: [{ total }] }) : Promise.resolve({ rows }),
  )
}

async function chartFactsQuery(args: Row) {
  const { getCapability } = await import('../../index')
  const cap = getCapability('marsys://tool/L1/chart_facts_query')
  if (!cap) throw new Error('chart_facts_query not registered')
  return (cap.handler as (a: Row, c?: unknown) => Promise<{ content: Row; is_error?: boolean }>)({ chart_id: CHART_ID, ayanamsha_id: AYA, ...args })
}
async function getKarakas(args: Row = {}) {
  const { getKarakasCapability } = await import('../L1_ganita/get_karakas')
  return (getKarakasCapability.handler as (a: Row, c?: unknown) => Promise<{ content: Row; is_error?: boolean }>)({ chart_id: CHART_ID, ...args })
}
async function getSensitivePoints(args: Row = {}) {
  const { getSensitivePointsCapability } = await import('../L1_ganita/get_sensitive_points')
  return (getSensitivePointsCapability.handler as (a: Row, c?: unknown) => Promise<{ content: Row; is_error?: boolean }>)({ chart_id: CHART_ID, ...args })
}

describe('chart_facts_query — pivoted: the canonical formula is the headline whatever the arrival order', () => {
  for (const [label, order] of [
    ['variant arrives first', [YOGI_ALT, YOGI_BPHS]],
    ['canonical arrives first', [YOGI_BPHS, YOGI_ALT]],
  ] as const) {
    it(`Yogi: headline is bphs_93_20's longitude, never alt_96_40's (${label})`, async () => {
      wire([...order])
      const row = ((await chartFactsQuery({ category: 'esoteric_point_yogi' })).content['facts'] as Row[])[0]!
      expect(row['longitude_sidereal']).toBe(352.351180718121) // NOT alt_96_40's 355.68 (the old last-wins value)
      expect((row['fact_ids'] as Row)['longitude_sidereal']).toBe('1ab369a4dca61235')
    })
  }

  for (const [label, order] of [['parashari first', [DK_PA, DK_KN]], ['kn_rao first', [DK_KN, DK_PA]]] as const) {
    it(`chara karaka: Darakaraka headline is the kn_rao school's Jupiter, not parashari's Mercury (${label})`, async () => {
      wire([...order])
      const row = ((await chartFactsQuery({ category: 'karaka_chara_position' })).content['facts'] as Row[])[0]!
      expect(row['assigned_graha']).toBe('Jupiter')
      expect((row['fact_ids'] as Row)['assigned_graha']).toBe('130f96d334c42797')
    })
  }

  for (const order of [[MR_TAJ, MR_BPHS, MR_SAR], [MR_BPHS, MR_SAR, MR_TAJ]]) {
    it(`Mrityu has NO canonical formula: the headline is null, never one of the three (${order[0]!['formula_id']} first)`, async () => {
      wire([...order])
      const row = ((await chartFactsQuery({ category: 'esoteric_point_mrityu' })).content['facts'] as Row[])[0]!
      expect(row['longitude_sidereal']).toBeNull()
      expect((row['fact_ids'] as Row)['longitude_sidereal']).toBeUndefined()
    })
  }

  it('a single-formula row (Strikaraka exists only under kn_rao) is served as its canonical value', async () => {
    wire([SK_KN])
    const row = ((await chartFactsQuery({ category: 'karaka_chara_position' })).content['facts'] as Row[])[0]!
    expect(row['assigned_graha']).toBe('Mercury')
  })

  it('ordinary rows (NULL formula_id) are served exactly as before', async () => {
    wire([PLAIN])
    const row = ((await chartFactsQuery({ category: 'graha_position' })).content['facts'] as Row[])[0]!
    expect(row['nakshatra']).toBe('Ashwini')
    expect((row['fact_ids'] as Row)['nakshatra']).toBe('plain-1')
  })

  it('grounding still cites every served variant fact_id (nothing served is ungrounded)', async () => {
    wire([YOGI_ALT, YOGI_BPHS])
    const g = JSON.stringify((await chartFactsQuery({ category: 'esoteric_point_yogi' })).content['grounding'])
    expect(g).toContain('1ab369a4dca61235')
    expect(g).toContain('8ed0713d195cc400')
  })

  it('SQL: the ORDER BY is TOTAL and canonical-first (… key, canonical rank, formula_id, fact_id = the PK)', async () => {
    wire([PLAIN])
    await chartFactsQuery({ category: 'graha_position' })
    const { sql } = mainCall()
    expect(sql).toMatch(/ORDER BY fact_subject, fact_category, fact_key, CASE [\s\S]+ END, formula_id, fact_id LIMIT/)
    expect(sql).toContain("WHEN fact_category = 'esoteric_point_yogi' AND formula_id = 'bphs_93_20' THEN 0")
    expect(sql).toContain("WHEN fact_category = 'karaka_chara_position' AND formula_id = 'kn_rao_rahu_included' THEN 0")
    expect(sql).toMatch(/SELECT[\s\S]*\bformula_id\b[\s\S]*FROM chart_facts/) // formula_id is read, so the pivot can pick
  })
})

describe('get_karakas — total canonical-first ORDER BY', () => {
  it('SQL: ORDER BY is total (… key, subject, canonical-first rank, formula_id, fact_id)', async () => {
    wire([DK_KN])
    await getKarakas()
    const { sql } = mainCall()
    expect(sql).toMatch(/ORDER BY fact_category, ayanamsha_id, fact_key, fact_subject, CASE [\s\S]+ END, formula_id, fact_id\s+LIMIT/)
    expect(sql).toContain("WHEN fact_category = 'karaka_chara_position' AND formula_id = 'kn_rao_rahu_included' THEN 0")
  })

  it('both schools\' rows are still served (never collapsed)', async () => {
    wire([DK_KN, DK_PA, SK_KN])
    const rows = (await getKarakas({ categories: ['karaka_chara_position'] })).content['rows'] as Row[]
    expect(rows.map(x => x['fact_value_text'])).toEqual(['Jupiter', 'Mercury', 'Mercury'])
  })
})

describe('get_sensitive_points — total canonical-first ORDER BY', () => {
  it('SQL: ORDER BY is total — adds fact_subject, the canonical-first rank and fact_id around formula_id', async () => {
    wire([YOGI_BPHS])
    await getSensitivePoints({ categories: ['esoteric_point_yogi'] })
    const { sql } = mainCall()
    expect(sql).toMatch(/ORDER BY fact_category, ayanamsha_id, fact_key, fact_subject, CASE [\s\S]+ END, formula_id, fact_id LIMIT \$3 OFFSET \$4/)
    expect(sql).toContain("WHEN fact_category = 'esoteric_point_yogi' AND formula_id = 'bphs_93_20' THEN 0")
  })

  it('both formulas are still served (never collapsed)', async () => {
    wire([YOGI_BPHS, YOGI_ALT])
    const rows = (await getSensitivePoints({ categories: ['esoteric_point_yogi'] })).content['rows'] as Row[]
    expect(rows.map(x => x['fact_id'])).toEqual(['1ab369a4dca61235', '8ed0713d195cc400'])
  })
})
