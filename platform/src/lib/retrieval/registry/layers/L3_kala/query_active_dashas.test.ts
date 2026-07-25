/**
 * query_active_dashas.test.ts — EL-33 (Elevation v2.1, γ.F) active-dasha convenience face.
 *
 * Unit-level: mocks @/lib/db/client to prove the multi-system grouping + honest coverage
 * accounting (the real intelligence) without a live DB. An INTEGRATION-gated block runs the
 * same handler against the real chart_dashas table when INTEGRATION=true.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── mock the db client ──────────────────────────────────────────────────────────
const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (sql: string, params: unknown[]) => queryMock(sql, params) }))

import { queryActiveDashasCapability } from './query_active_dashas'

type Handler = (a: Record<string, unknown>, c?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
const handler = queryActiveDashasCapability.handler as Handler

const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
const ABHINANDAN = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'  // second chart — narayana absent

describe('EL-33 query_active_dashas — descriptor', () => {
  it('is a per-chart temporal L3 tool grounded to L1 facts', () => {
    expect(queryActiveDashasCapability.name).toBe('query_active_dashas')
    expect(queryActiveDashasCapability.scope).toBe('per_chart')
    expect(queryActiveDashasCapability.required_inputs).toContain('chart_id')
    expect(queryActiveDashasCapability.grounds_to).toEqual({ l1_fact_ids: true })
  })
})

// Route by SQL text so call order/count never matters.
function routeQueries(present: string[], chainRows: Record<string, unknown>[]) {
  queryMock.mockImplementation((sql: string) => {
    if (/DISTINCT system_id/.test(sql)) return Promise.resolve({ rows: present.map(system_id => ({ system_id })) })
    return Promise.resolve({ rows: chainRows })
  })
}

describe('EL-33 query_active_dashas — multi-system grouping + honest coverage', () => {
  beforeEach(() => queryMock.mockClear())

  it('native 482012f1: all 9 systems present (incl. narayana) → no expected_absent', async () => {
    // Ground truth (Verifier-confirmed live): the native chart carries ALL 9 systems including
    // narayana (266 rows under lahiri). Coverage is per-chart — this is the native's reality.
    routeQueries(
      ['ashtottari', 'chara_karaka', 'kalachakra', 'mudda', 'naisargika', 'narayana', 'vimshottari', 'vimshottari_kp', 'yogini'],
      [
        { system_id: 'vimshottari', level_n: 1, lord_graha: 'Mercury', lord_sign: 'Capricorn', start_date: '2026-01-01', end_date: '2043-01-01', start_iso: null, end_iso: null },
        { system_id: 'vimshottari', level_n: 2, lord_graha: 'Venus', lord_sign: 'Aquarius', start_date: '2026-06-01', end_date: '2029-06-01', start_iso: null, end_iso: null },
        { system_id: 'vimshottari', level_n: 3, lord_graha: 'Sun', lord_sign: 'Capricorn', start_date: '2026-07-01', end_date: '2026-09-01', start_iso: null, end_iso: null },
        { system_id: 'narayana', level_n: 1, lord_graha: 'Mars', lord_sign: 'Aries', start_date: '2020-01-01', end_date: '2032-01-01', start_iso: null, end_iso: null },
        { system_id: 'yogini', level_n: 1, lord_graha: 'Jupiter', lord_sign: 'Pisces', start_date: '2020-01-01', end_date: '2030-01-01', start_iso: null, end_iso: null },
      ],
    )

    const res = await handler({ chart_id: NATIVE, date: '2026-07-25' })
    expect(res.is_error).toBeFalsy()
    const c = res.content

    // grouped by system: vimshottari (3 levels), narayana + yogini (1 level each)
    expect(c['system_count']).toBe(3)
    const systems = c['systems'] as Array<{ system_id: string; active_chain: unknown[]; levels_present: number[] }>
    const vim = systems.find(s => s.system_id === 'vimshottari')!
    expect(vim.active_chain).toHaveLength(3)
    expect(vim.levels_present).toEqual([1, 2, 3])
    const chain = vim.active_chain as Array<{ level_name: string; lord_graha: string }>
    expect(chain[0].level_name).toBe('Mahadasha')
    expect(chain[0].lord_graha).toBe('Mercury')
    expect(chain[1].level_name).toBe('Antardasha')
    expect(chain[2].level_name).toBe('Pratyantardasha')
    expect(systems.find(s => s.system_id === 'narayana')).toBeDefined()

    // honest coverage: all 9 present for the native, nothing absent
    const cov = c['coverage'] as Record<string, unknown>
    expect(cov['systems_present_for_chart']).toHaveLength(9)
    expect(cov['expected_absent']).toEqual([])
    expect(String(cov['expected_absent_note'])).toMatch(/all 9 expected systems present/)
    // chara_karaka etc. present-but-no-active-row-on-date disclosed
    expect(cov['present_but_no_active_row_on_date']).toEqual(
      expect.arrayContaining(['ashtottari', 'chara_karaka', 'kalachakra', 'mudda', 'naisargika', 'vimshottari_kp']),
    )
  })

  it('Abhinandan 1c826d5a: 8 systems, narayana absent → disclosed as a per-chart coverage gap', async () => {
    // Ground truth: the second chart lacks narayana (per-chart coverage differs). The honest-
    // disclosure path surfaces this without fabricating a lord for the absent system.
    routeQueries(
      ['ashtottari', 'chara_karaka', 'kalachakra', 'mudda', 'naisargika', 'vimshottari', 'vimshottari_kp', 'yogini'],
      [
        { system_id: 'vimshottari', level_n: 1, lord_graha: 'Saturn', lord_sign: 'Libra', start_date: '2020-01-01', end_date: '2039-01-01', start_iso: null, end_iso: null },
      ],
    )

    const res = await handler({ chart_id: ABHINANDAN, date: '2026-07-25' })
    expect(res.is_error).toBeFalsy()
    const cov = res.content['coverage'] as Record<string, unknown>
    expect(cov['systems_present_for_chart']).toHaveLength(8)
    expect(cov['expected_absent']).toEqual(['narayana'])
    expect(String(cov['expected_absent_note'])).toMatch(/narayana/)
  })

  it('the date filter is a single-instant containment (bounded — not the heavy tree)', async () => {
    routeQueries(['vimshottari'], [])
    await handler({ chart_id: NATIVE, date: '2026-07-25', ayanamsha_id: 'lahiri_chitrapaksha' })
    const chainSql = String(queryMock.mock.calls.find(c => !/DISTINCT/.test(String(c[0])))![0])
    expect(chainSql).toMatch(/start_date <= \$3::date AND end_date >= \$3::date/)
    expect(chainSql).toMatch(/level_n <= \$4/)
  })
})

// NOTE: no colocated INTEGRATION block here — a `vi.unmock` is hoisted file-wide by vitest and
// would cancel the mock above. Live-DB verification against real chart_dashas is done via the
// standard INTEGRATION harness (mirrors temporal_activation_wp13e.integration.test.ts) in a
// separate file so the unit mock and the live path never collide.
