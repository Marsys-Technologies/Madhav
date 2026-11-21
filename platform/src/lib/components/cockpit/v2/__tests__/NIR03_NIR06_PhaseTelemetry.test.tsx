import { act, cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { AssetRow as RegistryAssetRow } from '@/app/api/cockpit/registry/route'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
import type { ActiveRun, ActiveRunAsset } from '@/hooks/useActiveRun'
import { AssetRow } from '../AssetRow'
import { CockpitShell } from '../CockpitShell'
import { DataAssetsView } from '../DataAssetsView'
import { PlanModal } from '../PlanModal'
import { deriveBuildStage, formatPhaseBreakdown, formatPhaseMs, stageFill } from '../buildStage'

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }) }))
vi.mock('@/hooks/useBuildToast', () => ({ useBuildToast: vi.fn() }))
vi.mock('@/lib/components/cockpit/v2/WorkflowView', () => ({ WorkflowView: () => null }))
vi.mock('@/lib/components/cockpit/v2/TelemetryStrip', () => ({ TelemetryStrip: () => null }))
vi.mock('@/lib/components/cockpit/v2/ClearConfirmModal', () => ({ ClearConfirmModal: () => null }))

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
    last_updated: '2026-11-21T00:00:00Z',
    error: null,
    last_built_at: null,
    build_state_stale: false,
    service_health: null,
    last_invoked_at: null,
  }
}

describe('NIR-03 & NIR-06 durable phase telemetry and duration breakdowns', () => {
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

  it('derives build stages and formatting helpers for all durable phases', () => {
    expect(deriveBuildStage({ polledState: 'building', phase: 'computing' })).toBe('computing')
    expect(deriveBuildStage({ polledState: 'building', phase: 'writing' })).toBe('writing')
    expect(deriveBuildStage({ polledState: 'building', phase: 'writing', substepIndex: 5, substepTotal: 5 })).toBe('substeps')
    expect(deriveBuildStage({ polledState: 'building', phase: 'verifying', substepIndex: 5, substepTotal: 5 })).toBe('verifying')
    expect(deriveBuildStage({ polledState: 'building', phase: 'publishing', substepIndex: 5, substepTotal: 5 })).toBe('publishing')
    expect(stageFill('computing')).toBe(8)
    expect(stageFill('verifying')).toBe(90)
    expect(stageFill('publishing')).toBe(96)

    expect(formatPhaseMs(450)).toBe('450ms')
    expect(formatPhaseMs(3200)).toBe('3.2s')
    expect(formatPhaseMs(125000)).toBe('2m 5s')
    expect(formatPhaseBreakdown({ compute_ms: 120, write_ms: 4200, verify_ms: 310, publish_ms: 45 })).toBe(
      'Compute 120ms · Write 4.2s · Verify 310ms · Publish 45ms',
    )
  })

  it('renders durable mid-build phase and substep progress immediately on reload without waiting for SSE', () => {
    const gaDashas = makeAsset({ asset_id: 'ga_dashas', layer: 'ganita', english_name: 'Dashas Timeline' })
    const reloadRunAsset: ActiveRunAsset = {
      asset_id: 'ga_dashas',
      position: 0,
      state: 'building',
      started_at: '2026-11-21T00:00:01Z',
      ended_at: null,
      error: null,
      disposition: null,
      blocked_by_asset_id: null,
      phase: 'writing',
      substep_index: 14,
      substep_total: 35,
      substep_label: 'Yogini · Lahiri',
      compute_ms: 95,
      write_ms: null,
      verify_ms: null,
      publish_ms: null,
    }

    const { rerender } = render(
      <AssetRow
        asset={gaDashas}
        stat={makeStat('ga_dashas', 'building', null)}
        chartId="chart-1"
        activeRunId="run-1"
        activeRunPaused={false}
        activeRunAsset={reloadRunAsset}
        isActiveAsset
        substep={null}
        onRunStarted={vi.fn()}
        preparation
      />,
    )

    expect(screen.getByText('Writing')).toBeInTheDocument()
    expect(screen.getByText('14 / 35')).toBeInTheDocument()
    expect(screen.getByText('Compute 95ms')).toBeInTheDocument()

    rerender(
      <AssetRow
        asset={gaDashas}
        stat={makeStat('ga_dashas', 'building', 2100)}
        chartId="chart-1"
        activeRunId="run-1"
        activeRunPaused={false}
        activeRunAsset={{ ...reloadRunAsset, phase: 'verifying', write_ms: 18400 }}
        isActiveAsset
        substep={null}
        onRunStarted={vi.fn()}
        preparation
      />,
    )
    expect(screen.getByText('Verifying')).toBeInTheDocument()
    expect(screen.getByText('2,100 rows')).toBeInTheDocument()
    expect(screen.getByText('Compute 95ms · Write 18s')).toBeInTheDocument()

    rerender(
      <AssetRow
        asset={gaDashas}
        stat={makeStat('ga_dashas', 'lit', 2100)}
        chartId="chart-1"
        activeRunId="run-1"
        activeRunPaused={false}
        activeRunAsset={{
          ...reloadRunAsset,
          state: 'complete',
          phase: 'complete',
          write_ms: 18400,
          verify_ms: 420,
          publish_ms: 60,
        }}
        isActiveAsset={false}
        substep={null}
        onRunStarted={vi.fn()}
        preparation
      />,
    )
    expect(screen.getByText('Compute 95ms · Write 18s · Verify 420ms · Publish 60ms')).toBeInTheDocument()
  })

  it('updates phase labels live from asset.phase SSE events in DataAssetsView and CockpitShell banner', () => {
    const gaPositions = makeAsset({ asset_id: 'ga_positions', layer: 'ganita', english_name: 'Planet positions' })
    mockRegistry.mockReturnValue({ assets: [gaPositions], isLoading: false, error: null, refetch: vi.fn() })
    mockStats.mockReturnValue({
      stats: new Map([['ga_positions', makeStat('ga_positions', 'building', null)]]),
      lastFetched: new Date('2026-11-21T00:00:00Z'),
      error: null,
      refetch: vi.fn(),
      refetchLive: vi.fn(),
    })

    const run: ActiveRun = {
      id: 'run-live',
      scope: 'layer',
      scope_target: 'ganita',
      action: 'build',
      state: 'running',
      plan: ['ga_positions'],
      current_asset_id: 'ga_positions',
      created_at: '2026-11-21T00:00:00Z',
      started_at: '2026-11-21T00:00:01Z',
      pause_requested_at: null,
      stop_requested_at: null,
    }
    const assets: ActiveRunAsset[] = [
      {
        asset_id: 'ga_positions',
        position: 0,
        state: 'building',
        started_at: '2026-11-21T00:00:01Z',
        ended_at: null,
        error: null,
        disposition: null,
        blocked_by_asset_id: null,
        phase: 'computing',
      },
    ]

    mockUseActiveRun.mockReturnValue({
      run,
      assets,
      preparationIncomplete: false,
      preparationRetryAssets: [],
      refresh: vi.fn(),
    })

    render(<CockpitShell chartId="chart-1" variant="preparation" />)
    expect(screen.getByText(/0 of 1 assets complete · Planet positions \(Computing\)/)).toBeInTheDocument()
    expect(screen.getByText('Computing')).toBeInTheDocument()

    act(() => {
      FakeEventSource.instances[0].emit('asset.phase', {
        type: 'asset.phase',
        chart_id: 'chart-1',
        asset_id: 'ga_positions',
        run_id: 'run-live',
        phase: 'verifying',
        compute_ms: 80,
        write_ms: 2100,
      })
    })
    expect(screen.getByText('Verifying')).toBeInTheDocument()
    expect(screen.getByText('Compute 80ms · Write 2.1s')).toBeInTheDocument()

    act(() => {
      FakeEventSource.instances[0].emit('asset.phase', {
        type: 'asset.phase',
        chart_id: 'chart-1',
        asset_id: 'ga_positions',
        run_id: 'run-live',
        phase: 'publishing',
        compute_ms: 80,
        write_ms: 2100,
        verify_ms: 350,
      })
    })
    expect(screen.getByText('Publishing')).toBeInTheDocument()
    expect(screen.getByText('Compute 80ms · Write 2.1s · Verify 350ms')).toBeInTheDocument()
  })

  it('surfaces per-phase duration breakdown in PlanModal when duration_history.phase_breakdown is present', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          data: {
            status: 'ok',
            blockers: [],
            plan_waves: [['ga_positions', 'bo_laksana']],
            estimated_seconds: 120,
            duration_history: {
              sample_count: 3,
              last_seconds: 120,
              lower_seconds: 110,
              upper_seconds: 135,
              phase_breakdown: {
                compute_ms: 400,
                write_ms: 112000,
                verify_ms: 3500,
                publish_ms: 1200,
                total_ms: 117100,
                sample_runs: 3,
              },
            },
          },
        }),
        { status: 200 },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    render(
      <PlanModal
        chartId="00000000-0000-4000-8000-000000000001"
        scope="layer"
        scopeTarget="bodha"
        action="rebuild"
        label="Rebuild Bodha"
        preparation
        onClose={vi.fn()}
        onRunStarted={vi.fn()}
      />,
    )

    await waitFor(() =>
      expect(screen.getByTestId('plan-phase-breakdown')).toHaveTextContent(
        'Phase breakdown (3 runs): Compute 400ms · Write 1m 52s · Verify 3.5s · Publish 1.2s',
      ),
    )
  })
})
