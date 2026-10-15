import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AssetRow } from '../AssetRow'
import type { AssetStats } from '@/app/api/cockpit/stats/route'

// FIX2: a chart page must never offer to clear a GLOBAL asset (shared by every chart).
vi.mock('@/hooks/useUserRole', () => ({ useUserRole: vi.fn() }))
import { useUserRole } from '@/hooks/useUserRole'

const BASE = {
  asset_id: 'ga_positions', layer: 'ganita', sort_order: 1, sanskrit_name: 's', english_name: 'Positions',
  english_description: '', storage_type: 'table', target_table: 't', count_sql: 'SELECT 1', size_sql: null,
  target_floor: null, expected_volume_formula: null, expected_volume_inputs: null, volume_explanation: null,
  depends_on: [], scope: 'per_chart', is_active: true, estimated_seconds: null, created_at: '2026-01-01T00:00:00Z',
  asset_type: 'data' as const, layer_name: 'x', layer_index: 'L1', provides_apis: null, health_probe: null,
  catalog_status: 'CURRENT' as const, asset_kind: 'data' as const, service_health: null,
  last_invoked_at: null, last_selftest_at: null, selftest_detail: null,
}
const STAT: AssetStats = {
  asset_id: 'x', actual_rows: 3, volume: 3, size_bytes: null, last_updated: '2026-01-01T00:00:00Z', error: null,
  state: 'lit', last_built_at: '2026-01-01T00:00:00Z', build_state_stale: false, service_health: null, last_invoked_at: null,
}

function renderRow(asset: typeof BASE) {
  return render(
    <AssetRow asset={asset} stat={STAT} chartId="c1" activeRunId={null} activeRunPaused={false} onRunStarted={() => {}} />,
  )
}

describe('AssetRow clear button', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(useUserRole as ReturnType<typeof vi.fn>).mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  it('is shown for a per-chart asset', () => {
    renderRow(BASE)
    expect(screen.getByTitle(/clear/i)).toBeTruthy()
  })

  it('is hidden for a global asset, even for super_admin', () => {
    renderRow({ ...BASE, asset_id: 'mi_kula', layer: 'mimamsa', scope: 'global' })
    expect(screen.queryByTitle(/clear/i)).toBeNull()
  })
})
