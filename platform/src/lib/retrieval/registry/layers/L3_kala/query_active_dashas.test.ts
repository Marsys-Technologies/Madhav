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

  it('groups the active chain per system and reports across all present systems', async () => {
    // 8 systems built — narayana absent, per get_dashas ground truth.
    routeQueries(
      ['ashtottari', 'chara_karaka', 'kalachakra', 'mudda', 'naisargika', 'vimshottari', 'vimshottari_kp', 'yogini'],
      [
        { system_id: 'vimshottari', level_n: 1, lord_graha: 'Mercury', lord_sign: 'Capricorn', start_date: '2026-01-01', end_date: '2043-01-01', start_iso: null, end_iso: null },
        { system_id: 'vimshottari', level_n: 2, lord_graha: 'Venus', lord_sign: 'Aquarius', start_date: '2026-06-01', end_date: '2029-06-01', start_iso: null, end_iso: null },
        { system_id: 'vimshottari', level_n: 3, lord_graha: 'Sun', lord_sign: 'Capricorn', start_date: '2026-07-01', end_date: '2026-09-01', start_iso: null, end_iso: null },
        { system_id: 'yogini', level_n: 1, lord_graha: 'Jupiter', lord_sign: 'Pisces', start_date: '2020-01-01', end_date: '2030-01-01', start_iso: null, end_iso: null },
      ],
    )

    const res = await handler({ chart_id: NATIVE, date: '2026-07-25' })
    expect(res.is_error).toBeFalsy()
    const c = res.content

    // grouped by system
    expect(c['system_count']).toBe(2)
    const systems = c['systems'] as Array<{ system_id: string; active_chain: unknown[]; levels_present: number[] }>
    const vim = systems.find(s => s.system_id === 'vimshottari')!
    expect(vim.active_chain).toHaveLength(3)
    expect(vim.levels_present).toEqual([1, 2, 3])
    const chain = vim.active_chain as Array<{ level_name: string; lord_graha: string }>
    expect(chain[0].level_name).toBe('Mahadasha')
    expect(chain[0].lord_graha).toBe('Mercury')
    expect(chain[1].level_name).toBe('Antardasha')
    expect(chain[2].level_name).toBe('Pratyantardasha')

    // honest coverage: 8 present, narayana disclosed absent (never fabricated)
    const cov = c['coverage'] as Record<string, unknown>
    expect(cov['systems_present_for_chart']).toHaveLength(8)
    expect(cov['expected_absent']).toEqual(['narayana'])
    expect(String(cov['expected_absent_note'])).toMatch(/narayana/)
    // yogini present but only L1 active row — chara_karaka etc. present-but-no-active-row disclosed
    expect(cov['present_but_no_active_row_on_date']).toEqual(
      expect.arrayContaining(['ashtottari', 'chara_karaka', 'kalachakra', 'mudda', 'naisargika', 'vimshottari_kp']),
    )
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
