import { describe, expect, it, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import {
  deriveChartReadiness,
  emptyChartReadiness,
  getChartReadinessMap,
  isDerivedChartReady,
} from '../readiness'
import { BRAHMA_LAYER_ORDER } from '@/lib/brahma/lexicon'

const CHART = 'c0000000-0000-4000-8000-000000000001'

function row(asset_id: string, state = 'lit', rows_written: number | null = 5, last_built_at: string | null = '2026-09-01T00:00:00Z') {
  return { chart_id: CHART, asset_id, state, rows_written, last_built_at }
}

function run(state: string, last_error: string | null = null, extra: Partial<{ id: string; action: string }> = {}) {
  return {
    id: extra.id ?? 'run-1',
    chart_id: CHART,
    state,
    action: extra.action ?? 'rebuild',
    last_error,
    created_at: '2026-09-02T00:00:00Z',
    started_at: null,
    ended_at: null,
  }
}

const ALL_LAYERS = [row('ga_positions'), row('bo_laksana'), row('ka_windows'), row('ph_outlook'), row('mi_seva')]

// Brahmagyan is global infrastructure and is always lit once any per-chart
// layer holds data; percent is lit public layers over the six-layer order.
const pct = (lit: number) => Math.round((lit / BRAHMA_LAYER_ORDER.length) * 100)

describe('deriveChartReadiness', () => {
  it.each([
    ['empty chart', [], null, 'not-built', 0],
    ['active run on empty chart', [], run('running'), 'building', 0],
    ['planned run', [], run('planned'), 'building', 0],
    ['paused run', [], run('paused'), 'building', 0],
    ['building throughput without a run row', [row('ga_positions', 'building', null)], null, 'building', 0],
    ['partial layers', [row('ga_positions')], null, 'partially-built', pct(2)],
    ['every public layer lit', ALL_LAYERS, run('completed'), 'ready', 100],
    ['dispatch failure after correction', [], run('failed', 'JOB_DISPATCH_FAILED: local spawn failed'), 'needs-rebuild', 0],
    ['ordinary failed run on a partial chart', [row('ga_positions')], run('failed', 'writer crashed'), 'failed', pct(2)],
    ['stopped run falls through to data state', [row('ga_positions')], run('stopped'), 'partially-built', pct(2)],
  ] as const)('%s', (_label, throughput, latestRun, expectedState, expectedPercent) => {
    const actual = deriveChartReadiness({ throughput: [...throughput], latestRun })
    expect(actual.state).toBe(expectedState)
    expect(actual.percent).toBe(expectedPercent)
  })

  it('is ready only when Brahmagyan and all five per-chart layers are lit', () => {
    for (let drop = 0; drop < ALL_LAYERS.length; drop += 1) {
      const partial = ALL_LAYERS.filter((_, i) => i !== drop)
      expect(deriveChartReadiness({ throughput: partial, latestRun: null }).state).toBe('partially-built')
    }
    const full = deriveChartReadiness({ throughput: ALL_LAYERS, latestRun: null })
    expect(full.state).toBe('ready')
    expect(full.layerPips.map((p) => p.layer)).toEqual([...BRAHMA_LAYER_ORDER])
    expect(full.layerPips.every((p) => p.state === 'lit')).toBe(true)
  })

  it('treats lit zero-row and stale-with-rows assets as data present', () => {
    const r = deriveChartReadiness({
      throughput: [row('ga_prashna', 'lit', 0), row('bo_laksana', 'stale', 12)],
      latestRun: null,
    })
    const byLayer = Object.fromEntries(r.layerPips.map((p) => [p.layer, p.state]))
    expect(byLayer.ganita).toBe('lit')
    expect(byLayer.bodha).toBe('lit')
    expect(byLayer.kala).toBe('dim')
  })

  it('dormant rows with no data do not count as built', () => {
    const r = deriveChartReadiness({ throughput: [row('ga_positions', 'dormant', null, null)], latestRun: null })
    expect(r.state).toBe('not-built')
    expect(r.percent).toBe(0)
  })

  it('a failed scoped run on a fully lit chart stays ready but keeps the error visible', () => {
    const r = deriveChartReadiness({ throughput: ALL_LAYERS, latestRun: run('failed', 'writer crashed') })
    expect(r.state).toBe('ready')
    expect(r.latestError).toBe('writer crashed')
  })

  it('a dispatch failure is never masked by leftover data', () => {
    const r = deriveChartReadiness({
      throughput: ALL_LAYERS,
      latestRun: run('failed', 'JOB_DISPATCH_FAILED: spawn ENOENT'),
    })
    expect(r.state).toBe('needs-rebuild')
    expect(isDerivedChartReady(r)).toBe(false)
  })

  it('reports active and latest run ids, last activity, and a human label', () => {
    const r = deriveChartReadiness({
      throughput: [row('ga_positions', 'lit', 3, '2026-09-01T00:00:00Z'), row('bo_laksana', 'lit', 3, '2026-09-05T00:00:00Z')],
      latestRun: run('running', null, { id: 'run-active' }),
    })
    expect(r.activeRunId).toBe('run-active')
    expect(r.latestRunId).toBe('run-active')
    expect(r.lastActivity).toBe('2026-09-05T00:00:00Z')
    expect(r.label).toBe('Building')
  })

  it.each([
    ['not-built', 'Not built'],
    ['building', 'Building'],
    ['partially-built', 'Partially built'],
    ['ready', 'Ready'],
    ['failed', 'Failed'],
    ['needs-rebuild', 'Needs rebuild'],
  ] as const)('labels %s as "%s"', (state, label) => {
    const fixtures: Record<string, Parameters<typeof deriveChartReadiness>[0]> = {
      'not-built': { throughput: [], latestRun: null },
      building: { throughput: [], latestRun: run('running') },
      'partially-built': { throughput: [row('ga_positions')], latestRun: null },
      ready: { throughput: ALL_LAYERS, latestRun: null },
      failed: { throughput: [], latestRun: run('failed', 'boom') },
      'needs-rebuild': { throughput: [], latestRun: run('failed', 'JOB_DISPATCH_FAILED: x') },
    }
    const r = deriveChartReadiness(fixtures[state])
    expect(r.state).toBe(state)
    expect(r.label).toBe(label)
  })

  it('emptyChartReadiness is the not-built value', () => {
    expect(emptyChartReadiness()).toMatchObject({ state: 'not-built', percent: 0, activeRunId: null })
  })
})

describe('getChartReadinessMap', () => {
  beforeEach(() => mockQuery.mockReset())

  it('returns an empty map without querying when no chart ids are given', async () => {
    expect((await getChartReadinessMap([])).size).toBe(0)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('issues exactly two batched queries and never touches pyramid_layers', async () => {
    const other = 'c0000000-0000-4000-8000-000000000002'
    mockQuery.mockImplementation(async (sql?: string) => {
      if (sql?.includes('asset_throughput')) return { rows: [row('ga_positions')] }
      if (sql?.includes('build_runs')) return { rows: [{ ...run('running'), chart_id: other }] }
      return { rows: [] }
    })
    const map = await getChartReadinessMap([CHART, other])
    const calls = mockQuery.mock.calls.filter(([sql]) => typeof sql === 'string')
    expect(calls).toHaveLength(2)
    for (const [sql, params] of calls) {
      expect(sql).not.toMatch(/pyramid_layers/)
      expect(params).toEqual([[CHART, other]])
    }
    const runSql = calls.map(([s]) => s as string).find((s) => s.includes('build_runs'))!
    expect(runSql).toMatch(/DISTINCT ON \(chart_id\)/)
    expect(runSql).toMatch(/last_error/)
    expect(runSql).not.toMatch(/state IN/)
    const throughputSql = calls.map(([s]) => s as string).find((s) => s.includes('asset_throughput'))!
    expect(throughputSql).toMatch(/is_active\s*=\s*true/)
    expect(map.get(CHART)?.state).toBe('partially-built')
    expect(map.get(other)?.state).toBe('building')
  })
})
