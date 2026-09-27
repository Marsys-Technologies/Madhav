import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getChartWorkspaceSummary } from '../workspaceSummary'

const CHART = 'c0000000-0000-4000-8000-00000000000a'

function route(handlers: { positions?: unknown[]; dashas?: unknown[]; yogas?: unknown[]; fail?: RegExp }) {
  mockQuery.mockImplementation(async (sql?: string) => {
    if (typeof sql !== 'string') return { rows: [] }
    if (handlers.fail?.test(sql)) throw new Error('relation missing')
    if (sql.includes('chart_facts')) return { rows: handlers.positions ?? [] }
    if (sql.includes('chart_dashas')) return { rows: handlers.dashas ?? [] }
    if (sql.includes('ga_yoga_firings')) return { rows: handlers.yogas ?? [] }
    return { rows: [] }
  })
}

const pos = (fact_subject: string, fact_key: string, text: string | null, num: string | null = null) => ({
  fact_subject,
  fact_key,
  fact_value_text: text,
  fact_value_num: num,
})

describe('getChartWorkspaceSummary', () => {
  beforeEach(() => mockQuery.mockReset())

  it('builds D1 from this chart’s own L1 graha positions — never a canonical fallback', async () => {
    route({
      positions: [
        pos('LAGNA', 'sign', 'Leo'),
        pos('LAGNA', 'longitude_sidereal', null, '130.5'),
        pos('SUN', 'sign', 'Leo'),
        pos('MOON', 'sign', 'Aries'),
        pos('SATURN', 'sign', 'Libra'),
      ],
    })
    const s = await getChartWorkspaceSummary(CHART)
    expect(s.d1.isEmpty).toBe(false)
    expect(s.d1.chartId).toBe(CHART)
    expect(s.d1.lagnaSign).toBe('Leo')
    expect(s.d1.lagnaDegreeDms).toBe('10°30′00″')
    expect(s.d1.houses[0]).toEqual({ house: 1, sign: 'Leo', planets: ['Sun'] })
    expect(s.d1.houses[8]).toEqual({ house: 9, sign: 'Aries', planets: ['Moon'] })
    expect(s.d1.houses[2]).toEqual({ house: 3, sign: 'Libra', planets: ['Saturn'] })
    expect(s.d1.topYogas).toEqual([])
    expect(s.flags).toEqual([])
  })

  it('pins fact_key and uses a total, latest-build ordering for positions', async () => {
    route({})
    await getChartWorkspaceSummary(CHART)
    const sql = mockQuery.mock.calls.map(([s]) => s).find((s) => typeof s === 'string' && s.includes('chart_facts')) as string
    expect(sql).toMatch(/fact_category\s*=\s*'graha_position'/)
    expect(sql).toMatch(/fact_key\s+IN\s*\('sign',\s*'longitude_sidereal'\)/)
    expect(sql).toMatch(/DISTINCT ON \(fact_subject, fact_key\)/)
    expect(sql).toMatch(/ORDER BY fact_subject, fact_key, computed_at DESC, build_id DESC/)
  })

  it('returns an honest empty D1 and no daśā or yogas for a chart with no computed facts', async () => {
    route({})
    const s = await getChartWorkspaceSummary(CHART)
    expect(s.d1.isEmpty).toBe(true)
    expect(s.d1.lagnaSign).toBe('')
    expect(s.d1.houses.every((h) => h.planets.length === 0)).toBe(true)
    expect(s.currentDasha).toBeNull()
    expect(s.confirmedYogas).toEqual([])
    expect(JSON.stringify(s)).not.toMatch(/Kalpadruma|Mercury|Capricorn/)
  })

  it('reads the current Vimśottarī mahā/antar daśā containing today', async () => {
    route({
      positions: [pos('LAGNA', 'sign', 'Aries')],
      dashas: [
        { level_n: 1, lord_graha: 'VENUS', end_date: '2031-01-01' },
        { level_n: 2, lord_graha: 'MOON', end_date: '2027-03-04' },
      ],
    })
    const s = await getChartWorkspaceSummary(CHART)
    expect(s.currentDasha).toEqual({ md: 'Venus', ad: 'Moon', adEnd: '2027-03-04' })
    expect(s.d1.currentDasha).toEqual(s.currentDasha)
  })

  it('lists only fired, whole, un-cancelled yoga firings as confirmed', async () => {
    route({
      positions: [pos('LAGNA', 'sign', 'Aries')],
      yogas: [{ yoga_canonical_id: 'gajakesari', name: 'Gajakesari Yoga' }],
    })
    const s = await getChartWorkspaceSummary(CHART)
    expect(s.confirmedYogas).toEqual([{ id: 'gajakesari', name: 'Gajakesari Yoga' }])
    const sql = mockQuery.mock.calls.map(([q]) => q).find((q) => typeof q === 'string' && q.includes('ga_yoga_firings')) as string
    expect(sql).toMatch(/f\.fired\s*=\s*true/)
    expect(sql).toMatch(/NOT f\.is_partial/)
    expect(sql).toMatch(/NOT f\.bhanga_active/)
  })

  it('fails loud, not silent: a read failure yields empty values plus a flag', async () => {
    route({ fail: /ga_yoga_firings/, positions: [pos('LAGNA', 'sign', 'Aries')] })
    const s = await getChartWorkspaceSummary(CHART)
    expect(s.d1.isEmpty).toBe(false)
    expect(s.confirmedYogas).toEqual([])
    expect(s.flags).toContain('yogas_unresolved')
  })
})
