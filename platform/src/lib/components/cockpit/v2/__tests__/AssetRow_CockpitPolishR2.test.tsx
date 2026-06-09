import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AssetRow } from '../AssetRow'
import { LayerPanel } from '../LayerPanel'
import type { AssetStats } from '@/app/api/cockpit/stats/route'

// Cockpit Polish R2 — service rendering + visual fixes.
// Covers brief issues 1 (service health), 5 (status dot), 7 (name size).

vi.mock('@/hooks/useUserRole', () => ({
  useUserRole: vi.fn(),
}))

import { useUserRole } from '@/hooks/useUserRole'
const mockUseUserRole = useUserRole as ReturnType<typeof vi.fn>

const DATA_ASSET = {
  asset_id: 'ga_positions',
  layer: 'ganita',
  sort_order: 1,
  sanskrit_name: 'Graha-sphuṭa',
  english_name: 'Planet positions',
  english_description: '',
  storage_type: 'table',
  target_table: 'ganita_positions',
  count_sql: 'SELECT count(*) FROM ganita_positions',
  size_sql: null,
  target_floor: 9,
  expected_volume_formula: null,
  expected_volume_inputs: null,
  volume_explanation: null,
  depends_on: [],
  scope: 'per_chart',
  is_active: true,
  estimated_seconds: null,
  created_at: '2026-01-01T00:00:00Z',
  asset_type: 'data' as const,
  layer_name: 'Gaṇita',
  layer_index: 'L1',
  provides_apis: null,
  health_probe: null,
  catalog_status: 'CURRENT' as const,
}

const SERVICE_ASSET = {
  ...DATA_ASSET,
  asset_id: 'bg_panchanga',
  layer: 'brahmagyan',
  sanskrit_name: 'Pañcāṅga Gaṇanā',
  english_name: 'Panchanga Engine',
  storage_type: 'service',
  target_table: null,
  count_sql: null,
  target_floor: null,
  scope: 'global',
  asset_type: 'service' as const,
  layer_name: 'Brahma Jñāna',
  layer_index: 'L0',
}

function statOf(partial: Partial<AssetStats>): AssetStats {
  return {
    asset_id: 'x',
    actual_rows: null,
    volume: null,
    size_bytes: null,
    last_updated: '2026-01-01T00:00:00Z',
    error: null,
    state: 'dormant',
    last_built_at: null,
    ...partial,
  }
}

describe('Cockpit Polish R2 — AssetRow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  it('mounts a service row green with no missing_table / degraded text (issue 1)', () => {
    render(
      <AssetRow
        asset={SERVICE_ASSET}
        stat={statOf({ asset_id: 'bg_panchanga', state: 'service_ok', error: null })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    expect(screen.getByText('● GREEN')).toBeTruthy()
    expect(screen.queryByText(/missing_table/)).toBeNull()
    expect(screen.queryByText(/degraded/)).toBeNull()
  })

  it('renders a status dot instead of a literal CURRENT text chip (issue 5)', () => {
    const { container } = render(
      <AssetRow
        asset={DATA_ASSET}
        stat={statOf({ asset_id: 'ga_positions', state: 'lit', actual_rows: 9 })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    // No "CURRENT" rendered as visible text anywhere in the row
    expect(screen.queryByText('CURRENT')).toBeNull()
    // A status dot carries the words in its title tooltip
    expect(container.querySelector('[title="CURRENT · healthy"]')).toBeTruthy()
  })

  it('renders the sanskrit name at the bumped 18px medium weight (issue 7)', () => {
    render(
      <AssetRow
        asset={DATA_ASSET}
        stat={statOf({ asset_id: 'ga_positions', state: 'lit', actual_rows: 9 })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    const name = screen.getByText('Graha-sphuṭa')
    expect(name.className).toContain('text-[18px]')
    expect(name.className).toContain('font-medium')
  })
})

describe('Cockpit Polish R2 — parent context (LayerPanel renders a service row green)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  it('mounts a brahmagyan service inside LayerPanel without degraded state', () => {
    render(
      <LayerPanel
        layer="brahmagyan"
        assets={[SERVICE_ASSET]}
        stats={new Map([['bg_panchanga', statOf({ asset_id: 'bg_panchanga', state: 'service_ok' })]])}
        defaultExpanded
        chartId="chart-1"
        activeRun={null}
        onRunStarted={() => {}}
      />
    )
    expect(screen.getByText('● GREEN')).toBeTruthy()
    expect(screen.queryByText(/degraded/)).toBeNull()
  })
})
