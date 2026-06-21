import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LayerPanel } from '../LayerPanel'

// Mock useUserRole so we can control isSuperAdmin in tests
vi.mock('@/hooks/useUserRole', () => ({
  useUserRole: vi.fn(),
}))

import { useUserRole } from '@/hooks/useUserRole'
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
