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

function run(state: string, last_error: string | null = null, extra: Partial<{ id: string; action: string; scope: string }> = {}) {
  return {
    id: extra.id ?? 'run-1',
    chart_id: CHART,
    state,
    scope: extra.scope ?? 'asset',
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
const NONE = { assets: 0, dispatchFailed: false }
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
    ['stopped run whose assets still hold data falls through to data state', [row('ga_positions')], run('stopped'), 'partially-built', pct(2)],
  ] as const)('%s', (_label, throughput, latestRun, expectedState, expectedPercent) => {
    const actual = deriveChartReadiness({ throughput: [...throughput], latestRun, unresolvedFailure: NONE })
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

  it('treats a lit zero-row asset as data present', () => {
    const r = deriveChartReadiness({ throughput: [row('ga_prashna', 'lit', 0)], latestRun: null })
    const byLayer = Object.fromEntries(r.layerPips.map((p) => [p.layer, p.state]))
    expect(byLayer.ganita).toBe('lit')
    expect(byLayer.kala).toBe('dim')
  })

  describe('stale assets are not valid current data', () => {
    it('a stale required asset keeps an otherwise complete chart out of Ready', () => {
      const r = deriveChartReadiness({
        throughput: [...ALL_LAYERS, row('bo_bimba', 'stale', 12)],
        latestRun: run('completed'),
        unresolvedFailure: NONE,
      })
      expect(r.state).not.toBe('ready')
      expect(isDerivedChartReady(r)).toBe(false)
      expect(r.state).toBe('partially-built')
    })

    it('marks the layer holding a stale asset as needing attention, not built', () => {
      const r = deriveChartReadiness({
        throughput: [...ALL_LAYERS, row('bo_bimba', 'stale', 12)],
        latestRun: run('completed'),
        unresolvedFailure: NONE,
      })
      const byLayer = Object.fromEntries(r.layerPips.map((p) => [p.layer, p.state]))
      expect(byLayer.bodha).toBe('amber')
    })

    it('a layer whose only data is stale does not count as built', () => {
      const r = deriveChartReadiness({ throughput: [row('bo_laksana', 'stale', 12)], latestRun: null, unresolvedFailure: NONE })
      expect(r.state).toBe('not-built')
      expect(r.percent).toBe(0)
    })
  })

  describe('serving impact of active runs', () => {
    const recal = (state = 'running') =>
      ({ ...run(state, null, { id: 'recal-1', scope: 'asset_set', action: 'rebuild' }), planned_assets: ['mi_jivanaghatana', 'mi_pramana', 'ph_rectification', 'ph_pramana'] })

    it('an LEL recalibration run leaves a Ready chart Ready (it does not invalidate served data)', () => {
      const r = deriveChartReadiness({ throughput: ALL_LAYERS, latestRun: recal(), unresolvedFailure: NONE })
      expect(r.state).toBe('ready')
      expect(r.activeRunId).toBe('recal-1')
      expect(r.activeRunBlocksReadings).toBe(false)
    })

    it('its own assets building do not block readings', () => {
      const r = deriveChartReadiness({
        throughput: [...ALL_LAYERS, row('mi_pramana', 'building', 4)],
        latestRun: recal(),
        unresolvedFailure: NONE,
      })
      expect(r.state).toBe('ready')
    })

    it.each([
      ['a global rebuild', { scope: 'global', action: 'rebuild' }, ['ga_positions']],
      ['a global build', { scope: 'global', action: 'build' }, []],
      ['a layer rebuild', { scope: 'layer', action: 'rebuild' }, ['bo_laksana']],
      ['an asset rebuild outside the recalibration set', { scope: 'asset', action: 'rebuild' }, ['ga_positions']],
      ['an asset set mixing recalibration and serving assets', { scope: 'asset_set', action: 'rebuild' }, ['mi_pramana', 'bo_laksana']],
      ['a run whose planned assets are unknown', { scope: 'asset_set', action: 'rebuild' }, null],
      ['a run with no planned assets', { scope: 'asset_set', action: 'rebuild' }, []],
    ] as const)('%s blocks readings (fails safe until classified)', (_label, extra, planned) => {
      const r = deriveChartReadiness({
        throughput: ALL_LAYERS,
        latestRun: { ...run('running', null, { ...extra, id: 'r-9' }), planned_assets: planned === null ? null : [...planned] },
        unresolvedFailure: NONE,
      })
      expect(r.state).toBe('building')
      expect(r.activeRunBlocksReadings).toBe(true)
    })

    it('a building asset outside the non-blocking run still blocks', () => {
      const r = deriveChartReadiness({
        throughput: [...ALL_LAYERS, row('ga_positions', 'building', 3)],
        latestRun: recal(),
        unresolvedFailure: NONE,
      })
      expect(r.state).toBe('building')
    })
  })

  it('dormant rows with no data do not count as built', () => {
    const r = deriveChartReadiness({ throughput: [row('ga_positions', 'dormant', null, null)], latestRun: null })
    expect(r.state).toBe('not-built')
    expect(r.percent).toBe(0)
  })

  it('a failed small refresh that left its data intact stays Ready with a non-blocking warning', () => {
    const r = deriveChartReadiness({ throughput: ALL_LAYERS, latestRun: run('failed', 'writer crashed'), unresolvedFailure: NONE })
    expect(r.state).toBe('ready')
    expect(isDerivedChartReady(r)).toBe(true)
    expect(r.latestError).toBe('writer crashed')
    expect(r.refreshWarning).toMatch(/latest refresh did not finish/i)
  })

  it.each(['failed', 'stopped'])('a %s small refresh that cleared or broke any of its assets is not Ready', (state) => {
    const r = deriveChartReadiness({ throughput: ALL_LAYERS, latestRun: run(state, 'x'), unresolvedFailure: { assets: 2, dispatchFailed: false } })
    expect(r.state).toBe('failed')
    expect(isDerivedChartReady(r)).toBe(false)
  })

  it('a completed small refresh carries no warning', () => {
    const r = deriveChartReadiness({ throughput: ALL_LAYERS, latestRun: run('completed'), unresolvedFailure: NONE })
    expect(r.state).toBe('ready')
    expect(r.refreshWarning ?? null).toBeNull()
  })

  it('a failed chart correction is never masked by a later successful small run', () => {
    const r = deriveChartReadiness({
      throughput: ALL_LAYERS,
      latestRun: run('completed', null, { id: 'run-small' }),
      unresolvedFailure: { assets: 3, dispatchFailed: false },
    })
    expect(r.state).toBe('failed')
    expect(isDerivedChartReady(r)).toBe(false)
  })

  it('an earlier failed small run whose assets are still broken is not masked by a later completed run', () => {
    const r = deriveChartReadiness({
      throughput: ALL_LAYERS,
      latestRun: run('completed', null, { id: 'run-later', scope: 'asset' }),
      unresolvedFailure: { assets: 1, dispatchFailed: false },
    })
    expect(r.state).toBe('failed')
  })

  it('an unknown failure picture after a failed or stopped latest run fails closed', () => {
    expect(deriveChartReadiness({ throughput: ALL_LAYERS, latestRun: run('failed', 'x') }).state).toBe('failed')
  })

  it('a correction whose dispatch failed stays Needs rebuild until its whole plan is rebuilt', () => {
    const r = deriveChartReadiness({
      throughput: ALL_LAYERS,
      latestRun: run('completed', null, { id: 'run-small' }),
      unresolvedFailure: { assets: 5, dispatchFailed: true },
    })
    expect(r.state).toBe('needs-rebuild')
  })

  it('a failed full rebuild whose every planned asset was rebuilt afterwards no longer blocks', () => {
    const r = deriveChartReadiness({
      throughput: ALL_LAYERS,
      latestRun: run('completed', null, { id: 'run-small' }),
      unresolvedFailure: NONE,
    })
    expect(r.state).toBe('ready')
  })

  it.each(['failed', 'stopped'])(
    'a %s global rebuild is never Ready, even when every layer shows some data (partial correction rebuild)',
    (state) => {
      const full = run(state, state === 'failed' ? 'writer crashed' : null, { scope: 'global', action: 'rebuild' })
      const r = deriveChartReadiness({ throughput: ALL_LAYERS, latestRun: full, unresolvedFailure: { assets: 4, dispatchFailed: false } })
      expect(r.state).toBe('failed')
      expect(isDerivedChartReady(r)).toBe(false)
    },
  )

  it('a completed global rebuild with every layer lit is Ready', () => {
    expect(deriveChartReadiness({ throughput: ALL_LAYERS, latestRun: run('completed', null, { scope: 'global' }) }).state).toBe('ready')
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

  it('issues exactly three batched queries and never touches pyramid_layers', async () => {
    const other = 'c0000000-0000-4000-8000-000000000002'
    mockQuery.mockImplementation(async (sql?: string) => {
      if (sql?.includes('GROUP BY')) return { rows: [] }
      if (sql?.includes('build_runs')) return { rows: [{ ...run('running'), chart_id: other }] }
      if (sql?.includes('asset_throughput')) return { rows: [row('ga_positions')] }
      return { rows: [] }
    })
    const map = await getChartReadinessMap([CHART, other])
    const calls = mockQuery.mock.calls.filter(([sql]) => typeof sql === 'string')
    expect(calls).toHaveLength(3)
    for (const [sql, params] of calls) {
      expect(sql).not.toMatch(/pyramid_layers/)
      expect(params).toEqual([[CHART, other]])
    }
    const runSql = calls.map(([s]) => s as string).find((s) => s.includes('build_runs') && !s.includes('GROUP BY'))!
    // Latest run regardless of its state — a failed dispatch must be visible — and
    // no per-row correlated subquery (cost must not grow with run history).
    expect(runSql).toMatch(/DISTINCT ON \(r\.chart_id\)/)
    expect(runSql).toMatch(/last_error/)
    expect(runSql).toMatch(/\bscope\b/)
    expect(runSql).not.toMatch(/r\.state IN/)
    expect(runSql).not.toMatch(/SELECT COUNT/)
    const failureSql = calls.map(([s]) => s as string).find((s) => s.includes('GROUP BY'))!
    // Every failed/stopped run of any age still owning broken per-chart assets;
    // a full rebuild's assets must be rebuilt after it started.
    expect(failureSql).toMatch(/r\.state IN \('failed', 'stopped'\)/)
    expect(failureSql).toMatch(/ar\.scope = 'per_chart'/)
    expect(failureSql).toMatch(/at\.last_built_at >= r\.created_at/)
    expect(failureSql).toMatch(/COUNT\(DISTINCT bra\.asset_id\)/)
    expect(failureSql).toMatch(/JOB_DISPATCH_FAILED/)
    // Only a lit asset holds valid current data; a stale one does not resolve a failure.
    expect(failureSql).toMatch(/at\.state = 'lit'/)
    expect(failureSql).not.toMatch(/'stale'/)
    // The latest run carries its planned assets (for serving-impact classification),
    // read once per chart, never per historical run.
    expect(runSql).toMatch(/planned_assets/)
    expect(runSql).toMatch(/build_run_assets/)
    const throughputSql = calls.map(([s]) => s as string).find((s) => s.includes('asset_throughput'))!
    expect(throughputSql).toMatch(/is_active\s*=\s*true/)
    expect(map.get(CHART)?.state).toBe('partially-built')
    expect(map.get(other)?.state).toBe('building')
  })
})
