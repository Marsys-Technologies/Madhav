import { describe, expect, it } from 'vitest'
import { deriveChartReadiness } from '../model'
import type { ReadinessRunRow, ReadinessThroughputRow } from '../types'

function tRow(asset_id: string, state: string, rows_written: number | null = 10): ReadinessThroughputRow {
  return { asset_id, state, rows_written, last_built_at: '2026-11-20T00:00:00Z' }
}

function rRow(overrides: Partial<ReadinessRunRow> = {}): ReadinessRunRow {
  return {
    id: 'run-1',
    state: 'running',
    scope: 'layer',
    action: 'rebuild',
    last_error: null,
    created_at: '2026-11-20T00:00:00Z',
    started_at: '2026-11-20T00:00:01Z',
    ended_at: null,
    ...overrides,
  }
}

describe('NIR-02 readiness model precedence', () => {
  it('marks a layer building even when some assets in it are lit or stale', () => {
    const r = deriveChartReadiness({
      throughput: [
        tRow('ga_positions', 'lit'),
        tRow('ga_strength', 'stale'),
        tRow('ga_tajaka', 'building', null),
        tRow('bo_laksana', 'lit'),
      ],
      latestRun: rRow({ scope: 'layer', planned_assets: ['ga_tajaka'] }),
    })
    const byLayer = Object.fromEntries(r.layerPips.map((p) => [p.layer, p.state]))
    expect(byLayer.ganita).toBe('building')
    expect(byLayer.bodha).toBe('lit')
    expect(r.preparationDataUnavailable).toBe(true)
  })

  it('keeps a layer amber rather than lit when any asset is dormant, stale, or needs retry', () => {
    const partial = deriveChartReadiness({
      throughput: [tRow('ga_positions', 'lit'), tRow('ga_tajaka', 'dormant', 0)],
      latestRun: null,
    })
    expect(Object.fromEntries(partial.layerPips.map((p) => [p.layer, p.state])).ganita).toBe('amber')

    const retry = deriveChartReadiness({
      throughput: [tRow('ga_positions', 'lit'), tRow('bo_laksana', 'lit')],
      latestRun: null,
      unresolvedFailure: { assets: 1, dispatchFailed: false, preparationRetryAssets: ['bo_laksana'] },
    })
    expect(Object.fromEntries(retry.layerPips.map((p) => [p.layer, p.state])).bodha).toBe('amber')
    expect(retry.preparationDataUnavailable).toBe(true)
    expect(retry.preparationRetryAssets).toEqual(['bo_laksana'])
  })

  it('keeps a non-blocking active run layer pip as building rather than collapsing to dim', () => {
    const r = deriveChartReadiness({
      throughput: [tRow('ka_windows', 'building', null)],
      latestRun: rRow({ scope: 'layer', action: 'rebuild', planned_assets: ['ka_windows'] }),
    })
    expect(Object.fromEntries(r.layerPips.map((p) => [p.layer, p.state])).kala).toBe('building')
  })
})
