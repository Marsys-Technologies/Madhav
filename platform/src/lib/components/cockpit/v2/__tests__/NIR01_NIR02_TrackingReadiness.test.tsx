import { act, cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { AssetRow as RegistryAssetRow } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import type { ActiveRun, ActiveRunAsset } from '@/hooks/useActiveRun'
import { AssetRow } from '../AssetRow'
import { LayerPanel } from '../LayerPanel'
import { PreparationReadiness } from '../PreparationReadiness'
import { deriveBuildStage } from '../buildStage'
import { DataAssetsView } from '../DataAssetsView'
import { CockpitShell } from '../CockpitShell'
import { ChartReadinessBand } from '@/components/profile/ChartReadinessBand'
import { deriveChartReadiness } from '@/lib/build/readiness/model'

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }) }))
vi.mock('@/hooks/useBuildToast', () => ({ useBuildToast: vi.fn() }))
vi.mock('@/lib/components/cockpit/v2/WorkflowView', () => ({ WorkflowView: () => null }))
vi.mock('@/lib/components/cockpit/v2/PlanModal', () => ({ PlanModal: () => null }))
vi.mock('@/lib/components/cockpit/v2/TelemetryStrip', () => ({ TelemetryStrip: () => null }))
vi.mock('@/lib/components/cockpit/v2/ClearConfirmModal', () => ({ ClearConfirmModal: () => null }))
vi.mock('@/components/profile/LayerPreviewModal', () => ({ LayerPreviewModal: () => null }))

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string }) => (
    <a href={href} {...props}>{children}</a>
  ),
}))

const { mockRegistry, mockStats, mockUseActiveRun } = vi.hoisted(() => ({
  mockRegistry: vi.fn(),
  mockStats: vi.fn(),
  mockUseActiveRun: vi.fn(),
}))

vi.mock('@/hooks/useAssetRegistry', () => ({ useAssetRegistry: mockRegistry }))
vi.mock('@/hooks/useAssetStats', () => ({ useAssetStats: mockStats }))
vi.mock('@/hooks/useActiveRun', () => ({ useActiveRun: mockUseActiveRun }))
vi.mock('@/hooks/useUserRole', () => ({ useUserRole: () => ({ isSuperAdmin: false }) }))
vi.mock('@/hooks/useClearEligibility', () => ({
  useClearEligibility: () => ({ eligibility: null, refresh: vi.fn() }),
}))
vi.mock('next/dynamic', () => ({
  default: () => function MockGraph() {
    return null
  },
}))

class FakeEventSource extends EventTarget {
  static instances: FakeEventSource[] = []
  onerror: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  close = vi.fn()
  constructor(readonly url: string) {
    super()
    FakeEventSource.instances.push(this)
  }
  emit(type: string, data: object) {
    this.dispatchEvent(new MessageEvent(type, { data: JSON.stringify(data) }))
  }
}

function makeAsset(overrides: Partial<RegistryAssetRow> & { asset_id: string; layer: string }): RegistryAssetRow {
  return {
    sort_order: 1,
    sanskrit_name: overrides.asset_id,
    english_name: overrides.english_name ?? overrides.asset_id,
    english_description: '',
    storage_type: 'table',
    target_table: null,
    count_sql: null,
    size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: null,
    depends_on: [],
    scope: 'per_chart',
    is_active: true,
    estimated_seconds: 10,
    created_at: '2026-11-15T00:00:00Z',
    asset_type: 'data',
    layer_name: overrides.layer,
    layer_index: 'L1',
    provides_apis: null,
    health_probe: null,
    catalog_status: 'CURRENT',
    asset_kind: 'data',
    service_health: null,
    last_invoked_at: null,
    last_selftest_at: null,
    selftest_detail: null,
    ...overrides,
  }
}

function makeStat(assetId: string, state: AssetStats['state'], actualRows: number | null = 10): AssetStats {
  return {
    asset_id: assetId,
    state,
    actual_rows: actualRows,
    volume: actualRows,
    size_bytes: null,
    last_updated: '2026-11-20T00:00:00Z',
    error: state === 'error' ? 'boom' : null,
    last_built_at: state === 'lit' ? '2026-11-20T00:00:00Z' : null,
    build_state_stale: false,
    service_health: null,
    last_invoked_at: null,
  }
}

describe('NIR-01 & NIR-02 tracking and readiness regressions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    FakeEventSource.instances = []
    vi.stubGlobal('EventSource', FakeEventSource)
    vi.stubGlobal('matchMedia', vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })))
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('distinguishes an active light writer (no substeps) from a genuinely queued asset', () => {
    expect(deriveBuildStage({ polledState: 'building', isQueued: false })).toBe('running')
    expect(deriveBuildStage({ polledState: 'queued', isQueued: true })).toBe('queued')

    const gaPositions = makeAsset({ asset_id: 'ga_positions', layer: 'ganita', english_name: 'Planet positions' })
    const gaStrength = makeAsset({ asset_id: 'ga_strength', layer: 'ganita', english_name: 'Strength', depends_on: ['ga_positions'] })

    const activeRunAssetBuilding: ActiveRunAsset = {
      asset_id: 'ga_positions',
      state: 'building',
      position: 0,
      disposition: null,
      error: null,
      blocked_by_asset_id: null,
      started_at: '2026-11-20T00:00:01Z',
      ended_at: null,
    }
    const activeRunAssetQueued: ActiveRunAsset = {
      asset_id: 'ga_strength',
      state: 'queued',
      position: 1,
      disposition: null,
      error: null,
      blocked_by_asset_id: null,
      started_at: null,
      ended_at: null,
    }

    const { rerender } = render(
      <AssetRow
        asset={gaPositions}
        stat={makeStat('ga_positions', 'building', null)}
        chartId="chart-1"
        activeRunId="run-1"
        activeRunPaused={false}
        activeRunAsset={activeRunAssetBuilding}
        isActiveAsset
        substep={null}
        onRunStarted={vi.fn()}
        preparation
      />,
    )
    expect(screen.getByText('Building')).toBeInTheDocument()
    expect(screen.queryByText('Queued')).toBeNull()

    rerender(
      <AssetRow
        asset={gaStrength}
        stat={makeStat('ga_strength', 'dormant', 0)}
        chartId="chart-1"
        activeRunId="run-1"
        activeRunPaused={false}
        activeRunAsset={activeRunAssetQueued}
        isActiveAsset={false}
        substep={null}
        onRunStarted={vi.fn()}
        preparation
      />,
    )
    expect(screen.getByText('Queued')).toBeInTheDocument()
  })

  it('resets SSE overlays when activeRun.id changes between runs', () => {
    const gaPositions = makeAsset({ asset_id: 'ga_positions', layer: 'ganita', english_name: 'Planet positions' })
    mockRegistry.mockReturnValue({ assets: [gaPositions], isLoading: false, error: null, refetch: vi.fn() })
    mockStats.mockReturnValue({
      stats: new Map([['ga_positions', makeStat('ga_positions', 'dormant', 0)]]),
      lastFetched: new Date('2026-11-20T00:00:00Z'),
      error: null,
      refetch: vi.fn(),
      refetchLive: vi.fn(),
    })

    const run1: ActiveRun = {
      id: 'run-1',
      scope: 'layer',
      scope_target: 'ganita',
      action: 'build',
      state: 'running',
      plan: ['ga_positions'],
      current_asset_id: 'ga_positions',
      created_at: '2026-11-20T00:00:00Z',
      started_at: '2026-11-20T00:00:01Z',
      pause_requested_at: null,
      stop_requested_at: null,
    }
    const run2: ActiveRun = { ...run1, id: 'run-2', current_asset_id: null }
    const onAssetsReady = vi.fn()

    const { rerender } = render(
      <DataAssetsView
        chartId="chart-1"
        activeRun={run1}
        activeRunAssets={[{ asset_id: 'ga_positions', state: 'building', position: 0, disposition: null, error: null, blocked_by_asset_id: null, started_at: '2026-11-20T00:00:01Z', ended_at: null }]}
        refreshRun={vi.fn()}
        onAssetsReady={onAssetsReady}
      />,
    )

    expect(FakeEventSource.instances).toHaveLength(1)
    act(() => {
      FakeEventSource.instances[0].emit('asset.substep', {
        type: 'asset.substep',
        chart_id: 'chart-1',
        asset_id: 'ga_positions',
        substep_key: 'step1',
        substep_label: 'Ayanamsha 1',
        index: 1,
        total: 5,
        rows_written: 120,
      })
    })
    expect(screen.getByText('1 / 5')).toBeInTheDocument()

    rerender(
      <DataAssetsView
        chartId="chart-1"
        activeRun={run2}
        activeRunAssets={[{ asset_id: 'ga_positions', state: 'queued', position: 0, disposition: null, error: null, blocked_by_asset_id: null, started_at: null, ended_at: null }]}
        refreshRun={vi.fn()}
        onAssetsReady={onAssetsReady}
      />,
    )
    expect(screen.queryByText('1 / 5')).toBeNull()
    expect(screen.getByText('Queued')).toBeInTheDocument()
  })

  it('uses activeRun.plan so Gaṇita stays Prepared and unlocked when Resume schedules only Bodha', () => {
    const gaPositions = makeAsset({ asset_id: 'ga_positions', layer: 'ganita', english_name: 'Planet positions' })
    const boLaksana = makeAsset({ asset_id: 'bo_laksana', layer: 'bodha', english_name: 'House themes', depends_on: ['ga_positions'] })
    const allAssets = [gaPositions, boLaksana]
    const stats = new Map([
      ['ga_positions', makeStat('ga_positions', 'lit', 100)],
      ['bo_laksana', makeStat('bo_laksana', 'dormant', 0)],
    ])
    const resumeRun: ActiveRun = {
      id: 'run-resume',
      scope: 'asset_set',
      // Resume passes all prep assets in scope_target even though plan only targets Bodha.
      scope_target: 'ga_positions,bo_laksana',
      action: 'rebuild',
      state: 'running',
      plan: ['bo_laksana'],
      current_asset_id: 'bo_laksana',
      created_at: '2026-11-20T00:00:00Z',
      started_at: '2026-11-20T00:00:01Z',
      pause_requested_at: null,
      stop_requested_at: null,
    }
    const runAssets: ActiveRunAsset[] = [
      { asset_id: 'ga_positions', state: 'complete', position: 0, disposition: 'skip_no_delta', error: null, blocked_by_asset_id: null, started_at: '2026-11-20T00:00:01Z', ended_at: '2026-11-20T00:00:02Z' },
      { asset_id: 'bo_laksana', state: 'building', position: 1, disposition: null, error: null, blocked_by_asset_id: null, started_at: '2026-11-20T00:00:02Z', ended_at: null },
    ]

    render(
      <>
        <LayerPanel
          layer="ganita"
          assets={[gaPositions]}
          allAssets={allAssets}
          stats={stats}
          chartId="chart-1"
          activeRun={resumeRun}
          activeRunAssets={runAssets}
          defaultExpanded
          onRunStarted={vi.fn()}
          preparation
        />
        <LayerPanel
          layer="bodha"
          assets={[boLaksana]}
          allAssets={allAssets}
          stats={stats}
          chartId="chart-1"
          activeRun={resumeRun}
          activeRunAssets={runAssets}
          defaultExpanded
          onRunStarted={vi.fn()}
          preparation
        />
        <PreparationReadiness
          assets={allAssets}
          stats={stats}
          unavailable={false}
          chartId="chart-1"
          activeRun={resumeRun}
          activeRunAssets={runAssets}
        />
      </>,
    )

    // Gaṇita is unlocked (has Rebuild/Clear, no Stop) while Bodha owns the active building asset and surfaces Stop.
    const buttons = screen.getAllByRole('button')
    expect(buttons.filter(b => (b.getAttribute('aria-label') ?? b.textContent ?? '').includes('Stop'))).toHaveLength(2) // Layer + AssetRow for bo_laksana only (not ga_positions)
    expect(screen.getByRole('button', { name: 'Rebuild Planet positions' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Rebuild Gaṇita' })).toBeInTheDocument()

    const readiness = screen.getByRole('complementary', { name: 'What you can ask now' })
    expect(within(readiness).getByText('Gaṇita · Prepared')).toBeInTheDocument()
    expect(within(readiness).getByText('Bodha · Preparation in progress')).toBeInTheDocument()
  })

  it('renders retry and refresh callouts on ChartReadinessBand for amber/retry layers', () => {
    const chartId = 'c0000000-0000-4000-8000-000000000099'
    const readiness = deriveChartReadiness({
      throughput: [
        { asset_id: 'ga_positions', state: 'lit', rows_written: 10, last_built_at: '2026-11-20T00:00:00Z' },
        { asset_id: 'bo_laksana', state: 'stale', rows_written: 10, last_built_at: '2026-11-20T00:00:00Z' },
      ],
      latestRun: null,
    })
    const { rerender } = render(<ChartReadinessBand chartId={chartId} readiness={readiness} canBuild />)
    expect(screen.getByText(/Bodha needs refresh/i)).toBeInTheDocument()

    const retryReadiness = deriveChartReadiness({
      throughput: [
        { asset_id: 'ga_positions', state: 'lit', rows_written: 10, last_built_at: '2026-11-20T00:00:00Z' },
        { asset_id: 'bo_laksana', state: 'error', rows_written: 0, last_built_at: null },
      ],
      latestRun: null,
      unresolvedFailure: { assets: 1, dispatchFailed: false, preparationRetryAssets: ['bo_laksana'] },
    })
    rerender(<ChartReadinessBand chartId={chartId} readiness={retryReadiness} canBuild />)
    expect(screen.getByText(/Preparation needs a retry \(Bodha\)/i)).toBeInTheDocument()
  })

  it('excludes completed assets in activeRunAssets from Preparation in progress even when stats poll lags', () => {
    const gaPositions = makeAsset({ asset_id: 'ga_positions', layer: 'ganita' })
    const boLaksana = makeAsset({ asset_id: 'bo_laksana', layer: 'bodha', depends_on: ['ga_positions'] })
    const stats = new Map([
      // Polled stats still show dormant/stale for ga_positions right after completion
      ['ga_positions', makeStat('ga_positions', 'dormant', 0)],
      ['bo_laksana', makeStat('bo_laksana', 'dormant', 0)],
    ])
    const fullRun: ActiveRun = {
      id: 'run-full',
      scope: 'asset_set',
      scope_target: 'ga_positions,bo_laksana',
      action: 'build',
      state: 'running',
      plan: ['ga_positions', 'bo_laksana'],
      current_asset_id: 'bo_laksana',
      created_at: '2026-11-20T00:00:00Z',
      started_at: '2026-11-20T00:00:01Z',
      pause_requested_at: null,
      stop_requested_at: null,
    }
    const runAssets: ActiveRunAsset[] = [
      { asset_id: 'ga_positions', state: 'complete', position: 0, disposition: null, error: null, blocked_by_asset_id: null, started_at: '2026-11-20T00:00:01Z', ended_at: '2026-11-20T00:00:02Z' },
      { asset_id: 'bo_laksana', state: 'building', position: 1, disposition: null, error: null, blocked_by_asset_id: null, started_at: '2026-11-20T00:00:02Z', ended_at: null },
    ]

    render(
      <PreparationReadiness
        assets={[gaPositions, boLaksana]}
        stats={stats}
        unavailable={false}
        chartId="chart-1"
        activeRun={fullRun}
        activeRunAssets={runAssets}
      />,
    )

    expect(screen.getByText('Gaṇita · Prepared')).toBeInTheDocument()
    expect(screen.getByText('Bodha · Preparation in progress')).toBeInTheDocument()
  })

  it('displays wave-parallel building assets simultaneously in CockpitShell preparation banner', () => {
    const gaStrength = makeAsset({ asset_id: 'ga_strength', layer: 'ganita', english_name: 'Planetary strength' })
    const gaDashas = makeAsset({ asset_id: 'ga_dashas', layer: 'ganita', english_name: 'Dashas Timeline' })
    mockRegistry.mockReturnValue({ assets: [gaStrength, gaDashas], isLoading: false, error: null, refetch: vi.fn() })
    mockStats.mockReturnValue({
      stats: new Map([
        ['ga_strength', makeStat('ga_strength', 'building', null)],
        ['ga_dashas', makeStat('ga_dashas', 'building', null)],
      ]),
      lastFetched: new Date('2026-11-20T00:00:00Z'),
      error: null,
      refetch: vi.fn(),
      refetchLive: vi.fn(),
    })
    const parallelRun: ActiveRun = {
      id: 'run-parallel',
      scope: 'layer',
      scope_target: 'ganita',
      action: 'build',
      state: 'running',
      plan: ['ga_strength', 'ga_dashas'],
      current_asset_id: 'ga_strength',
      created_at: '2026-11-20T00:00:00Z',
      started_at: '2026-11-20T00:00:01Z',
      pause_requested_at: null,
      stop_requested_at: null,
    }
    const parallelAssets: ActiveRunAsset[] = [
      { asset_id: 'ga_strength', state: 'building', position: 0, disposition: null, error: null, blocked_by_asset_id: null, started_at: '2026-11-20T00:00:01Z', ended_at: null },
      { asset_id: 'ga_dashas', state: 'building', position: 1, disposition: null, error: null, blocked_by_asset_id: null, started_at: '2026-11-20T00:00:01Z', ended_at: null },
    ]
    mockUseActiveRun.mockReturnValue({
      run: parallelRun,
      assets: parallelAssets,
      preparationIncomplete: false,
      preparationRetryAssets: [],
      refresh: vi.fn(),
    })

    render(<CockpitShell chartId="chart-1" variant="preparation" />)
    expect(screen.getByText(/0 of 2 assets complete · Planetary strength, Dashas Timeline/)).toBeInTheDocument()
  })
})
