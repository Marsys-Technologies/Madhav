/**
 * formula_pins_tool_text_chart_facts_query.test.ts — SERVED-TEXT additions to chart_facts_query (a `tool-text:`
 * commit): the multi-formula variants made visible and labelled. The row-reduction BEHAVIOUR
 * (canonical headline, Mrityu null, total ORDER BY) is pinned in formula_pins_readers.test.ts.
 *
 * Source: INVESTIGATION_L1_DUPLICATE_KEYS_v1_0.md + SS decision 2026-10-01 ("EVERY served surface
 * for these categories shows the canonical row FIRST and the variants labelled with their
 * formula_id"). Fixture values are production values (formula_pins_fixtures.ts).
 */
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { DK_KN, DK_PA, MR_BPHS, MR_SAR, MR_TAJ, PLAIN, SK_KN, YOGI_ALT, YOGI_BPHS, type Row } from './formula_pins_fixtures'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const AYA = 'lahiri_chitrapaksha'

beforeAll(async () => {
  await import('../../catalog')
}, 120_000)

beforeEach(() => {
  mockQuery.mockReset()
})

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


describe('chart_facts_query — pivoted rows disclose EVERY variant, canonical first, labelled with formula_id', () => {
  for (const [label, order] of [
    ['variant arrives first', [YOGI_ALT, YOGI_BPHS]],
    ['canonical arrives first', [YOGI_BPHS, YOGI_ALT]],
  ] as const) {
    it(`Yogi: formula_variants lists bphs_93_20 (canonical) then alt_96_40 (variant) (${label})`, async () => {
      wire([...order])
      const row = ((await chartFactsQuery({ category: 'esoteric_point_yogi' })).content['facts'] as Row[])[0]!
      const variants = (row['formula_variants'] as Record<string, Array<Row>>)['longitude_sidereal']!
      expect(variants.map(v => [v['formula_id'], v['role'], v['value']])).toEqual([
        ['bphs_93_20', 'canonical', 352.351180718121],
        ['alt_96_40', 'variant', 355.68451411812],
      ])
      expect(row['formula_null_reasons']).toBeUndefined()
    })
  }

  it('chara karaka: parashari (Mercury) is disclosed and labelled next to the canonical kn_rao Jupiter', async () => {
    wire([DK_PA, DK_KN])
    const row = ((await chartFactsQuery({ category: 'karaka_chara_position' })).content['facts'] as Row[])[0]!
    const v = (row['formula_variants'] as Record<string, Array<Row>>)['assigned_graha']!
    expect(v.map(x => [x['formula_id'], x['value']])).toEqual([['kn_rao_rahu_included', 'Jupiter'], ['parashari_rahu_excluded', 'Mercury']])
  })

  it('Mrityu: null headline carries reason no_canonical_formula; all three disclosed with formula_id', async () => {
    wire([MR_TAJ, MR_BPHS, MR_SAR])
    const row = ((await chartFactsQuery({ category: 'esoteric_point_mrityu' })).content['facts'] as Row[])[0]!
    expect((row['formula_null_reasons'] as Row)['longitude_sidereal']).toBe('no_canonical_formula')
    const v = (row['formula_variants'] as Record<string, Array<Row>>)['longitude_sidereal']!
    expect(v.map(x => x['formula_id'])).toEqual(['bphs_ch39', 'saravali', 'tajik_aapamrityu'])
    expect(v.map(x => x['value'])).toEqual([96.4418410650319, 8.00640374694672, 247.80790552491])
  })

  it('a single-formula row is labelled canonical', async () => {
    wire([SK_KN])
    const row = ((await chartFactsQuery({ category: 'karaka_chara_position' })).content['facts'] as Row[])[0]!
    expect(((row['formula_variants'] as Record<string, Array<Row>>)['assigned_graha']!)[0]).toMatchObject({ formula_id: 'kn_rao_rahu_included', role: 'canonical' })
  })

  it('ordinary rows (NULL formula_id) gain no formula fields at all', async () => {
    wire([PLAIN])
    const row = ((await chartFactsQuery({ category: 'graha_position' })).content['facts'] as Row[])[0]!
    expect(row['formula_variants']).toBeUndefined()
    expect(row['formula_null_reasons']).toBeUndefined()
  })
})

describe('chart_facts_query — shape=rows labels each row; NULL formula_id is not added to ordinary rows', () => {
  it('rows carry formula_id + formula_role for declared categories', async () => {
    wire([YOGI_BPHS, YOGI_ALT, PLAIN])
    const rows = (await chartFactsQuery({ shape: 'rows', category: 'esoteric_point_yogi' })).content['rows'] as Row[]
    expect(rows.map(x => [x['formula_id'], x['formula_role']])).toEqual([
      ['bphs_93_20', 'canonical'], ['alt_96_40', 'variant'], [undefined, undefined],
    ])
    expect('formula_id' in rows[2]!).toBe(false)
  })

  it('Mrityu rows are labelled no_canonical_formula, never canonical', async () => {
    wire([MR_BPHS, MR_SAR, MR_TAJ])
    const rows = (await chartFactsQuery({ shape: 'rows', category: 'esoteric_point_mrityu' })).content['rows'] as Row[]
    expect(rows.map(x => x['formula_role'])).toEqual(['no_canonical_formula', 'no_canonical_formula', 'no_canonical_formula'])
  })
})

