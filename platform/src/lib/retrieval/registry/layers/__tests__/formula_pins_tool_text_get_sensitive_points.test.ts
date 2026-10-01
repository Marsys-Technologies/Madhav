/**
 * formula_pins_tool_text_get_sensitive_points.test.ts — SERVED-TEXT additions to get_sensitive_points (a `tool-text:`
 * commit): the multi-formula variants made visible and labelled. The row-reduction BEHAVIOUR
 * (canonical headline, Mrityu null, total ORDER BY) is pinned in formula_pins_readers.test.ts.
 *
 * Source: INVESTIGATION_L1_DUPLICATE_KEYS_v1_0.md + SS decision 2026-10-01 ("EVERY served surface
 * for these categories shows the canonical row FIRST and the variants labelled with their
 * formula_id"). Fixture values are production values (formula_pins_fixtures.ts).
 */
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { MR_BPHS, MR_SAR, MR_TAJ, YOGI_ALT, YOGI_BPHS, type Row } from './formula_pins_fixtures'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

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
async function getSensitivePoints(args: Row = {}) {
  const { getSensitivePointsCapability } = await import('../L1_ganita/get_sensitive_points')
  return (getSensitivePointsCapability.handler as (a: Row, c?: unknown) => Promise<{ content: Row; is_error?: boolean }>)({ chart_id: CHART_ID, ...args })
}


describe('get_sensitive_points — canonical-first disclosure; Mrityu has no headline', () => {
  it('Yogi: multi_formula lists canonical first with role and canonical_formula_id', async () => {
    wire([YOGI_BPHS, YOGI_ALT])
    const res = await getSensitivePoints({ categories: ['esoteric_point_yogi'] })
    const mf = (res.content['multi_formula'] as Row[])[0]!
    expect(mf['canonical_formula_id']).toBe('bphs_93_20')
    expect(mf['headline_reason']).toBeUndefined()
    expect((mf['formulas'] as Row[]).map(f => [f['formula_id'], f['role']])).toEqual([['bphs_93_20', 'canonical'], ['alt_96_40', 'variant']])
    expect((res.content['rows'] as Row[]).map(x => x['formula_role'])).toEqual(['canonical', 'variant'])
  })

  it('Mrityu: canonical_formula_id null + headline_reason no_canonical_formula; all three served', async () => {
    wire([MR_BPHS, MR_SAR, MR_TAJ])
    const res = await getSensitivePoints({ categories: ['esoteric_point_mrityu'] })
    const mf = (res.content['multi_formula'] as Row[])[0]!
    expect(mf['canonical_formula_id']).toBeNull()
    expect(mf['headline_reason']).toBe('no_canonical_formula')
    expect((mf['formulas'] as Row[]).map(f => f['formula_id'])).toEqual(['bphs_ch39', 'saravali', 'tajik_aapamrityu'])
    expect(res.content['formula_policy']).toMatchObject({ categories: { esoteric_point_mrityu: { canonical_formula_id: null, no_canonical_reason: 'no_canonical_formula' } } })
  })
})

describe('get_sensitive_points — list order is declared order, not a ranking (covers Mrityu, not only Avayogi)', () => {
  it('multi_formula_note says so and names Mrityu; formula_policy carries the same order_note', async () => {
    wire([MR_BPHS, MR_SAR, MR_TAJ])
    const res = await getSensitivePoints({ categories: ['esoteric_point_mrityu'] })
    const note = String(res.content['multi_formula_note'])
    expect(note).toContain('not a ranking')
    expect(note).toContain('esoteric_point_mrityu')
    expect(note).toContain('NO canonical formula')
    expect((res.content['formula_policy'] as Row)['order_note']).toContain('not a ranking')
  })
})
