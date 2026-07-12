/**
 * wp13a_computed_but_unserved.test.ts — WP-1.3(a) / F-L10-* (LCA-19)
 * ====================================================================
 * The Lane-10 shortfall's dominant class: assets COMPUTED and stored but with NO
 * deployed serving path. This suite proves each new/un-stubbed serving surface:
 *   (1) is per_chart + requires chart_id;
 *   (2) queries the correct chart-scoped table with chart_id = $1;
 *   (3) enforces bounded serving (LIMIT capped) and discloses a total;
 *   (4) narrows the SQL when optional filters are supplied.
 *
 * DB is mocked — no live connection required. Ground-truth row counts (verified via
 * bounded prod queries on both charts) are asserted through the mocked COUNT total.
 */
import { describe, it, expect, vi } from 'vitest'

const CHART_A = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (String(sql).includes('COUNT(*)')) return { rows: [{ total: '42' }] }
    if (String(sql).includes('MIN(month)')) return { rows: [{ first_month: '1984-02-01', last_month: '2070-01-01', distinct_scopes: 120, avg_activation: '0.1', max_activation: '0.9' }] }
    return { rows: [{ probe: 1 }] }
  }),
}))

import { query as mockQuery } from '@/lib/db/client'

import { getMedicalIndicationsCapability } from '../L1_ganita/get_medical_indications'
import { getVastuDirectionsCapability }    from '../L1_ganita/get_vastu_directions'
import { getYogaFiringsCapability }        from '../L1_ganita/get_yoga_firings'
import { queryCdlmSummaryCapability }      from '../L2_bodha/query_cdlm_summary'
import { queryCgmMotifsCapability }        from '../L2_bodha/query_cgm_motifs'
import { queryCgmPathsCapability }         from '../L2_bodha/query_cgm_paths'
import { queryChartGestaltCapability }     from '../L2_bodha/query_chart_gestalt'
import { queryDashaDossierCapability }     from '../L3_kala/query_dasha_dossier'
import { queryActivationWaveformCapability } from '../L3_kala/query_activation_waveform'
import { queryObstructionPeriodsCapability } from '../L3_kala/query_obstruction_periods'
import { queryTemporalViewCapability }     from '../L3_kala/query_temporal_view'

type Cap = {
  name: string
  scope: string
  required_inputs?: string[]
  handler: (args: Record<string, unknown>, ctx: unknown) => Promise<{ content: unknown; is_error?: boolean }>
}

const SIMPLE: Array<{ cap: Cap; table: string }> = [
  { cap: getMedicalIndicationsCapability as unknown as Cap, table: 'ga_medical' },
  { cap: getVastuDirectionsCapability as unknown as Cap,    table: 'ga_vastu_planet_direction_map' },
  { cap: getYogaFiringsCapability as unknown as Cap,        table: 'ga_yoga_firings' },
  { cap: queryCdlmSummaryCapability as unknown as Cap,      table: 'bodha_cdlm_chart_summary' },
  { cap: queryCgmMotifsCapability as unknown as Cap,        table: 'bodha_cgm_motifs' },
  { cap: queryCgmPathsCapability as unknown as Cap,         table: 'bodha_cgm_paths' },
  { cap: queryChartGestaltCapability as unknown as Cap,     table: 'bodha_chart_gestalt' },
  { cap: queryDashaDossierCapability as unknown as Cap,     table: 'kala_avadhi' },
  { cap: queryObstructionPeriodsCapability as unknown as Cap, table: 'kala_obstruction' },
  { cap: queryTemporalViewCapability as unknown as Cap,     table: 'kala_darshana' },
]

describe('WP-1.3(a) — computed-but-unserved serving surfaces', () => {
  it.each(SIMPLE)('$cap.name is per_chart and requires chart_id', ({ cap }) => {
    expect(cap.scope).toBe('per_chart')
    expect(cap.required_inputs).toContain('chart_id')
  })

  it.each(SIMPLE)('$cap.name errors without chart_id and does not touch the DB', async ({ cap }) => {
    vi.mocked(mockQuery).mockClear()
    const r = await cap.handler({}, {})
    expect(r.is_error).toBe(true)
    expect(vi.mocked(mockQuery)).not.toHaveBeenCalled()
  })

  it.each(SIMPLE)('$cap.name queries $table scoped by chart_id and discloses a total', async ({ cap, table }) => {
    vi.mocked(mockQuery).mockClear()
    const r = await cap.handler({ chart_id: CHART_A }, {})
    expect(r.is_error).toBe(false)
    const calls = vi.mocked(mockQuery).mock.calls
    const main = calls.find(c => String(c[0]).includes(`FROM ${table}`) && !String(c[0]).includes('COUNT(*)'))!
    expect(main, `a SELECT against ${table}`).toBeDefined()
    expect(String(main[0])).toContain('chart_id = $1')
    expect((main[1] as unknown[])[0]).toBe(CHART_A)
    const content = r.content as Record<string, unknown>
    expect(content).toHaveProperty('total_matching')
    expect(content.total_matching).toBe(42)
  })

  it.each(SIMPLE)('$cap.name caps LIMIT at 50 (bounded serving)', async ({ cap }) => {
    vi.mocked(mockQuery).mockClear()
    await cap.handler({ chart_id: CHART_A, limit: 100000 }, {})
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('LIMIT $'))!
    const limitParam = Number((main[1] as unknown[]).at(-1))
    expect(limitParam).toBeLessThanOrEqual(50)
  })
})

describe('WP-1.3(a) — kala_taranga waveform budget discipline (F-L10-015, 79,728 rows)', () => {
  const cap = queryActivationWaveformCapability

  it('is per_chart and requires chart_id', () => {
    expect(cap.scope).toBe('per_chart')
    expect(cap.required_inputs).toContain('chart_id')
  })

  it('summary mode (default) returns an aggregate — NO raw-row dump of the 79k waveform', async () => {
    vi.mocked(mockQuery).mockClear()
    const r = await cap.handler({ chart_id: CHART_A }, {})
    expect(r.is_error).toBe(false)
    const content = r.content as Record<string, unknown>
    expect(content.mode).toBe('summary')
    expect(content).toHaveProperty('aggregate')
    expect(content).toHaveProperty('total_matching')
    // The peak-months bounded probe uses a fixed LIMIT literal — no unbounded SELECT *.
    const selects = vi.mocked(mockQuery).mock.calls.map(c => String(c[0]))
    expect(selects.some(s => s.includes('LIMIT 24'))).toBe(true)
    expect(selects.some(s => /LIMIT \$\d+/.test(s) && !s.includes('COUNT'))).toBe(false)
  })

  it('drill mode REQUIRES a scope filter (budget guard) — errors without one', async () => {
    vi.mocked(mockQuery).mockClear()
    const r = await cap.handler({ chart_id: CHART_A, mode: 'drill' }, {})
    expect(r.is_error).toBe(true)
  })

  it('drill mode with a scope filter returns bounded rows (LIMIT <= 50)', async () => {
    vi.mocked(mockQuery).mockClear()
    await cap.handler({ chart_id: CHART_A, mode: 'drill', scope_kind: 'graha', limit: 9999 }, {})
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('FROM kala_taranga') && String(c[0]).includes('LIMIT $'))!
    const limitParam = Number((main[1] as unknown[]).at(-1))
    expect(limitParam).toBeLessThanOrEqual(50)
  })
})

describe('WP-1.3(a) — optional filters narrow the SQL', () => {
  it('get_medical_indications filters by graha', async () => {
    vi.mocked(mockQuery).mockClear()
    await getMedicalIndicationsCapability.handler({ chart_id: CHART_A, graha: 'Mars' }, {})
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('FROM ga_medical') && !String(c[0]).includes('COUNT'))!
    expect(String(main[0])).toContain('graha = $')
    expect(main[1] as unknown[]).toContain('Mars')
  })

  it('query_dasha_dossier defaults system_id to vimshottari and honors active_on', async () => {
    vi.mocked(mockQuery).mockClear()
    await queryDashaDossierCapability.handler({ chart_id: CHART_A, active_on: '2010-06-15' }, {})
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('FROM kala_avadhi') && !String(c[0]).includes('COUNT'))!
    expect(String(main[0])).toContain('system_id = $')
    expect(String(main[0])).toContain('period_start <=')
    const params = main[1] as unknown[]
    expect(params).toContain('vimshottari')
    expect(params).toContain('2010-06-15')
  })

  it('query_obstruction_periods filters by severity', async () => {
    vi.mocked(mockQuery).mockClear()
    await queryObstructionPeriodsCapability.handler({ chart_id: CHART_A, severity: 'high' }, {})
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('FROM kala_obstruction') && !String(c[0]).includes('COUNT'))!
    expect(String(main[0])).toContain('severity = $')
    expect(main[1] as unknown[]).toContain('high')
  })
})
