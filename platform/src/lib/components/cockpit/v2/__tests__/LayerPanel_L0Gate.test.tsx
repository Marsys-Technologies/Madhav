import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LayerPanel } from '../LayerPanel'

// Mock useUserRole so we can control isSuperAdmin in tests
vi.mock('@/hooks/useUserRole', () => ({
  useUserRole: vi.fn(),
}))

import { useUserRole } from '@/hooks/useUserRole'
import type { AssetStats } from '@/app/api/cockpit/stats/route'
const mockUseUserRole = useUserRole as ReturnType<typeof vi.fn>

const ASSET_BASE = {
  asset_id: 'bg_ephemeris',
  layer: 'brahmagyan',
  sort_order: 1,
  sanskrit_name: 'Sūryasiddhānta',
  english_name: 'Solar ephemeris',
  english_description: '',
  storage_type: 'table',
  target_table: 'ephemeris_daily',
  count_sql: null,
  size_sql: null,
  target_floor: null,
  expected_volume_formula: null,
  expected_volume_inputs: null,
  volume_explanation: null,
  depends_on: [],
  scope: 'global',
  is_active: true,
  estimated_seconds: null,
  created_at: '2026-01-01T00:00:00Z',
  // Migration 202+ service-support fields
  asset_type: 'data' as const,
  layer_name: 'Brahma Jñāna',
  layer_index: 'L0',
  provides_apis: null,
  health_probe: null,
  catalog_status: 'CURRENT' as const,
  // Migration 242 service/artifact kind fields
  asset_kind: 'data' as const,
  service_health: null,
  last_invoked_at: null,
  last_selftest_at: null,
  selftest_detail: null,
}

function stat(assetId: string, state: AssetStats['state'], actualRows: number): AssetStats {
  return {
    asset_id: assetId,
    actual_rows: actualRows,
    volume: actualRows,
    size_bytes: null,
    last_updated: '2026-09-12T00:00:00.000Z',
    error: null,
    state,
    last_built_at: state === 'lit' ? '2026-09-12T00:00:00.000Z' : null,
    build_state_stale: false,
    service_health: null,
    last_invoked_at: null,
  }
}

describe('LayerPanel — L0 BuildActionButton gate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('hides BuildActionButton for brahmagyan layer when not super_admin', () => {
    mockUseUserRole.mockReturnValue({ role: 'guest', isSuperAdmin: false, loading: false })
    render(
      <LayerPanel
        layer="brahmagyan"
        assets={[ASSET_BASE]}
        stats={new Map()}
        chartId="chart-1"
        activeRun={null}
        onRunStarted={() => {}}
      />
    )
    // BuildActionButton renders a button with text 'Build' or 'Rebuild' — should not be present
    expect(screen.queryByText(/^(Build|Rebuild)$/)).toBeNull()
  })

  it('shows BuildActionButton for brahmagyan layer when super_admin', () => {
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
    render(
      <LayerPanel
        layer="brahmagyan"
        assets={[ASSET_BASE]}
        stats={new Map()}
        chartId="chart-1"
        activeRun={null}
        onRunStarted={() => {}}
      />
    )
    expect(screen.getByText(/^(Build|Rebuild)$/)).toBeTruthy()
  })

  it('shows BuildActionButton for non-brahmagyan layer regardless of role', () => {
    mockUseUserRole.mockReturnValue({ role: 'guest', isSuperAdmin: false, loading: false })
    render(
      <LayerPanel
        layer="ganita"
        assets={[{ ...ASSET_BASE, asset_id: 'ga_positions', layer: 'ganita', scope: 'per_chart' }]}
        stats={new Map()}
        chartId="chart-1"
        activeRun={null}
        onRunStarted={() => {}}
      />
    )
    expect(screen.getByText(/^(Build|Rebuild)$/)).toBeTruthy()
  })
})

describe('LayerPanel — L0 ClearIconButton gate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('hides ClearIconButton for brahmagyan layer when not super_admin', () => {
    mockUseUserRole.mockReturnValue({ role: 'guest', isSuperAdmin: false, loading: false })
    render(
      <LayerPanel
        layer="brahmagyan"
        assets={[ASSET_BASE]}
        stats={new Map()}
        chartId="chart-1"
        activeRun={null}
        onRunStarted={() => {}}
      />
    )
    // The clear button has title containing "Clear" — should not be present
    expect(screen.queryByTitle(/clear/i)).toBeNull()
  })

  it('shows ClearIconButton for brahmagyan layer when super_admin', () => {
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
    render(
      <LayerPanel
        layer="brahmagyan"
        assets={[ASSET_BASE]}
        stats={new Map()}
        chartId="chart-1"
        activeRun={null}
        onRunStarted={() => {}}
      />
    )
    // ClearIconButton renders a button with title containing "Clear"
    expect(screen.getByTitle(/clear/i)).toBeTruthy()
  })

  it('shows ClearIconButton for non-brahmagyan layer regardless of role', () => {
    mockUseUserRole.mockReturnValue({ role: 'guest', isSuperAdmin: false, loading: false })
    render(
      <LayerPanel
        layer="ganita"
        assets={[{ ...ASSET_BASE, asset_id: 'ga_positions', layer: 'ganita', scope: 'per_chart' }]}
        stats={new Map()}
        chartId="chart-1"
        activeRun={null}
        onRunStarted={() => {}}
      />
    )
    expect(screen.getByTitle(/clear/i)).toBeTruthy()
  })
})

describe('LayerPanel — singleton asset_set ownership', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  it('holds the selected service row and its layer while a singleton asset_set run is active', () => {
    render(
      <LayerPanel
        layer="brahmagyan"
        assets={[{ ...ASSET_BASE, asset_id: 'bg_ephemeris_engine', asset_type: 'service' as const, asset_kind: 'service' as const, health_probe: { type: 'ephemeris' } }]}
        stats={new Map()}
        defaultExpanded
        chartId="chart-1"
        activeRun={{
          id: 'run-ephemeris',
          scope: 'asset_set',
          scope_target: 'bg_ephemeris_engine',
          action: 'rebuild',
          state: 'running',
          plan: ['bg_ephemeris_engine'],
          current_asset_id: 'bg_ephemeris_engine',
          created_at: '2026-08-27T00:00:00Z',
          started_at: '2026-08-27T00:00:01Z',
          pause_requested_at: null,
          stop_requested_at: null,
        }}
        onRunStarted={() => {}}
      />
    )

    expect(screen.queryByText(/^(Build|Rebuild)$/)).toBeNull()
    expect(screen.queryByTitle('Rebuild')).toBeNull()
    expect(screen.getAllByTitle('Stop build')).toHaveLength(2)
  })
})

describe('LayerPanel — D-NATIVE-11 supporting-writer operational readiness', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  const l2Assets = [
    { ...ASSET_BASE, asset_id: 'bo_laksana', layer: 'bodha', scope: 'per_chart' },
    {
      ...ASSET_BASE,
      asset_id: 'bo_grounding',
      layer: 'bodha',
      scope: 'per_chart',
      target_floor: 0,
    },
  ]

  it('keeps a dormant supporting writer in the operational denominator', () => {
    render(
      <LayerPanel
        layer="bodha"
        assets={l2Assets}
        stats={new Map([
          ['bo_laksana', stat('bo_laksana', 'lit', 12)],
          ['bo_grounding', stat('bo_grounding', 'dormant', 0)],
        ])}
        chartId="chart-1"
        activeRun={null}
        onRunStarted={() => {}}
      />
    )

    expect(screen.getByTitle('1 / 2 lit')).toBeTruthy()
    expect(screen.getByText('1')).toBeTruthy()
    expect(screen.getByText('/ 2')).toBeTruthy()
  })

  it('accepts a successfully completed zero-row supporting writer as operationally ready', () => {
    render(
      <LayerPanel
        layer="bodha"
        assets={l2Assets}
        stats={new Map([
          ['bo_laksana', stat('bo_laksana', 'lit', 12)],
          ['bo_grounding', stat('bo_grounding', 'lit', 0)],
        ])}
        chartId="chart-1"
        activeRun={null}
        onRunStarted={() => {}}
      />
    )

    expect(screen.getByTitle('All assets lit')).toBeTruthy()
    expect(screen.getByText('2')).toBeTruthy()
    expect(screen.getByText('/ 2')).toBeTruthy()
  })
})
