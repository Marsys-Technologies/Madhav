/**
 * formula_pins_tool_text_get_karakas.test.ts — SERVED-TEXT additions to get_karakas (a `tool-text:`
 * commit): the multi-formula variants made visible and labelled. The row-reduction BEHAVIOUR
 * (canonical headline, Mrityu null, total ORDER BY) is pinned in formula_pins_readers.test.ts.
 *
 * Source: INVESTIGATION_L1_DUPLICATE_KEYS_v1_0.md + SS decision 2026-10-01 ("EVERY served surface
 * for these categories shows the canonical row FIRST and the variants labelled with their
 * formula_id"). Fixture values are production values (formula_pins_fixtures.ts).
 */
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { DK_KN, DK_PA, SK_KN, type Row } from './formula_pins_fixtures'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

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
async function getKarakas(args: Row = {}) {
  const { getKarakasCapability } = await import('../L1_ganita/get_karakas')
  return (getKarakasCapability.handler as (a: Row, c?: unknown) => Promise<{ content: Row; is_error?: boolean }>)({ chart_id: CHART_ID, ...args })
}


describe('get_karakas — stops hiding formula_id', () => {
  it('projects fact_subject + formula_id and labels each karaka row with its formula_role', async () => {
    wire([DK_KN, DK_PA, SK_KN])
    const rows = (await getKarakas({ categories: ['karaka_chara_position'] })).content['rows'] as Row[]
    expect(rows.map(x => [x['fact_subject'], x['formula_id'], x['formula_role']])).toEqual([
      ['DARAKARAKA', 'kn_rao_rahu_included', 'canonical'],
      ['DARAKARAKA', 'parashari_rahu_excluded', 'variant'],
      ['STRIKARAKA', 'kn_rao_rahu_included', 'canonical'],
    ])
  })

  it('serves the formula policy (canonical, variants, provisional status) for the declared category', async () => {
    wire([DK_KN])
    const res = await getKarakas({ categories: ['karaka_chara_position'] })
    expect(res.content['formula_policy']).toEqual({
      status: 'provisional_until_J1',
      categories: { karaka_chara_position: { canonical_formula_id: 'kn_rao_rahu_included', variants: ['parashari_rahu_excluded'] } },
    })
  })

  it('no formula_policy when no declared category is requested', async () => {
    wire([])
    expect((await getKarakas({ categories: ['arudha_pada'] })).content['formula_policy']).toBeUndefined()
  })

  it('SQL: selects fact_subject and formula_id', async () => {
    wire([DK_KN])
    await getKarakas()
    expect(mainCall().sql).toMatch(/SELECT[\s\S]*\bfact_subject\b[\s\S]*\bformula_id\b[\s\S]*FROM chart_facts/)
  })
})

