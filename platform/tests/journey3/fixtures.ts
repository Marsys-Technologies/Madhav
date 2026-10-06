import type { AssetStats } from '@/app/api/cockpit/stats/route'
export const DATA_ASSET = {
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
  // Migration 242 service/artifact kind fields
  asset_kind: 'data' as const,
  service_health: null,
  last_invoked_at: null,
  last_selftest_at: null,
  selftest_detail: null,
}


export function statOf(partial: Partial<AssetStats>): AssetStats {
  return {
    asset_id: 'x',
    actual_rows: null,
    volume: null,
    size_bytes: null,
    last_updated: '2026-01-01T00:00:00Z',
    error: null,
    state: 'dormant',
    last_built_at: null,
    build_state_stale: false,
    service_health: null,
    last_invoked_at: null,
    ...partial,
  }
}


const preparationFixtures = { DATA_ASSET, statOf }
export default preparationFixtures
