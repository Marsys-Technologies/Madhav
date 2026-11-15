import { act, cleanup, render } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { AssetRow } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import type { AssetWithState } from '../LiveDependencyGraph'
import type { SubstepOverlay } from '../DataAssetsView'
import { DataAssetsView } from '../DataAssetsView'

const { mockRegistry, mockStats, mockGraph, mockLayer, refetchStats, refetchLive } = vi.hoisted(() => ({
  mockRegistry: vi.fn(), mockStats: vi.fn(), mockGraph: vi.fn(), mockLayer: vi.fn(),
  refetchStats: vi.fn(), refetchLive: vi.fn(),
}))
vi.mock('@/hooks/useAssetRegistry', () => ({ useAssetRegistry: mockRegistry }))
vi.mock('@/hooks/useAssetStats', () => ({ useAssetStats: mockStats }))
// Capture the real DataAssetsView's outgoing graph/ledger props. Connection
// ownership and reconnect callbacks still run through the real useCockpitSSE.
vi.mock('next/dynamic', () => ({ default: () => function Instrument(props: { assets: AssetWithState[] }) {
  mockGraph(props)
  return null
} }))
vi.mock('../LayerPanel', () => ({ LayerPanel: (props: {
  stats: Map<string, AssetStats>; substepOverlay: Map<string, SubstepOverlay>
}) => { mockLayer(props); return null } }))

class Source extends EventTarget {
  static instances: Source[] = []
  onerror: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  close = vi.fn()
  constructor(readonly url: string) { super(); Source.instances.push(this) }
  send(type: string, data: object = {}) {
    this.dispatchEvent(new MessageEvent(type, { data: JSON.stringify(data) }))
  }
}

const ASSET: AssetRow = {
  asset_id: 'ga_positions', layer: 'ganita', sort_order: 1,
  sanskrit_name: 'Positions', english_name: 'Positions', english_description: '',
  storage_type: 'table', target_table: null, count_sql: null, size_sql: null,
  target_floor: null, expected_volume_formula: null, expected_volume_inputs: null,
  volume_explanation: null, depends_on: [], scope: 'per_chart', is_active: true,
  estimated_seconds: null, created_at: '2026-11-15T00:00:00Z', asset_type: 'data',
  layer_name: 'Gaṇita', layer_index: 'L1', provides_apis: null, health_probe: null,
  catalog_status: 'CURRENT', asset_kind: 'data', service_health: null,
  last_invoked_at: null, last_selftest_at: null, selftest_detail: null,
}

function polled(state: AssetStats['state']) {
  const rows = state === 'dormant' ? 0 : 100
  const stat: AssetStats = {
    asset_id: ASSET.asset_id, state, actual_rows: rows, volume: rows,
    size_bytes: null, last_updated: '2026-11-15T00:00:00Z',
    error: state === 'error' ? 'writer failed' : null, last_built_at: null,
    build_state_stale: false, service_health: null, last_invoked_at: null,
  }
  return { stats: new Map([[ASSET.asset_id, stat]]), lastFetched: new Date('2026-11-15T00:00:00Z'),
    error: null, refetch: refetchStats, refetchLive }
}

function graphAsset(): AssetWithState { return mockGraph.mock.lastCall![0].assets[0] }
function ledger() { return mockLayer.mock.lastCall![0] as {
  stats: Map<string, AssetStats>; substepOverlay: Map<string, SubstepOverlay>
} }

function receiveBuildingOverlay() {
  const source = Source.instances[0]
  act(() => {
    source.send('asset.state_change', { type: 'asset.state_change', asset_id: ASSET.asset_id,
      from_state: 'dormant', to_state: 'building' })
    source.send('asset.progress', { type: 'asset.progress', asset_id: ASSET.asset_id,
      rows_written: 42, expected_rows: null })
    source.send('asset.substep', { type: 'asset.substep', chart_id: 'chart', asset_id: ASSET.asset_id,
      substep_key: 'positions', substep_label: 'Positions', index: 1, total: 3, rows_written: 42 })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-11-15T00:00:00Z'))
  Source.instances = []
  vi.stubGlobal('EventSource', Source)
  vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }))
  mockRegistry.mockReturnValue({ assets: [ASSET], isLoading: false, error: null, refetch: vi.fn() })
  mockStats.mockReturnValue(polled('dormant'))
})
afterEach(() => { cleanup(); vi.clearAllTimers(); vi.useRealTimers(); vi.unstubAllGlobals() })

describe('DataAssetsView reconnect reconciliation', () => {
  it.each(['lit', 'error', 'incomplete'] as const)('reconciles missed terminal %s stats with graph/header and clears obsolete substep progress on a genuine reconnect', (terminal) => {
    const onAssetsReady = vi.fn(), refreshRun = vi.fn()
    const view = () => <DataAssetsView chartId="chart" activeRun={null} refreshRun={refreshRun} onAssetsReady={onAssetsReady} />
    const { rerender } = render(view())
    const first = Source.instances[0]
    act(() => first.send('hello'))
    expect(refetchStats).not.toHaveBeenCalled()
    expect(refetchLive).not.toHaveBeenCalled()
    expect(refreshRun).not.toHaveBeenCalled()
    receiveBuildingOverlay()
    expect(graphAsset()).toMatchObject({ state: 'building', actual_rows: 42 })
    expect(ledger().substepOverlay.get(ASSET.asset_id)).toMatchObject({ substep_index: 1, substep_total: 3 })

    // The normal poll has committed terminal truth; the terminal SSE was missed.
    mockStats.mockReturnValue(polled(terminal))
    rerender(view())
    expect(ledger().stats.get(ASSET.asset_id)?.state).toBe(terminal)
    expect(graphAsset()).toMatchObject({ state: 'building', actual_rows: 42 })
    expect(onAssetsReady.mock.lastCall![0][0].state).toBe('building')

    act(() => { first.onerror?.(); vi.advanceTimersByTime(1_000) })
    const next = Source.instances[1]
    act(() => next.send('hello'))
    expect(graphAsset()).toMatchObject({ state: terminal, actual_rows: 100 })
    expect(onAssetsReady.mock.lastCall![0][0]).toMatchObject({ state: terminal, actual_rows: 100 })
    expect(ledger().substepOverlay.size).toBe(0)
    expect(refetchStats).toHaveBeenCalledTimes(1)
    expect(refreshRun).toHaveBeenCalledTimes(1)
    expect(refetchLive).not.toHaveBeenCalled()
  })

  it('retains the existing live-count refresh when a terminal run event is actually received', () => {
    const refreshRun = vi.fn()
    const { rerender } = render(<DataAssetsView chartId="chart" activeRun={null} refreshRun={refreshRun} />)
    act(() => Source.instances[0].send('hello'))
    receiveBuildingOverlay()
    mockStats.mockReturnValue(polled('lit'))
    rerender(<DataAssetsView chartId="chart" activeRun={null} refreshRun={refreshRun} />)
    act(() => Source.instances[0].send('run.state_change', { type: 'run.state_change', run_id: 'run', state: 'completed' }))

    expect(graphAsset()).toMatchObject({ state: 'lit', actual_rows: 100 })
    expect(ledger().substepOverlay.size).toBe(0)
    expect(refreshRun).toHaveBeenCalledTimes(1)
    expect(refetchLive).toHaveBeenCalledTimes(1)
    expect(refetchStats).not.toHaveBeenCalled()
  })
})
