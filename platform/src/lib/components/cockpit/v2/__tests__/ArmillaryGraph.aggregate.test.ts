import { describe, it, expect } from 'vitest'
import { aggregate } from '../ArmillaryGraph'
import type { AssetWithState } from '../LiveDependencyGraph'

// Minimal AssetWithState stub — only fields aggregate() reads.
function makeAsset(overrides: Partial<AssetWithState>): AssetWithState {
  return {
    asset_id: 'test_asset',
    layer: 'bodha',
    sort_order: 1,
    sanskrit_name: 'Test',
    english_name: 'Test',
    english_description: '',
    storage_type: 'table',
    target_table: null,
    count_sql: null,
    size_sql: null,
    target_floor: null,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    scope: 'per_chart',
    asset_type: 'data',
    catalog_status: 'CURRENT',
    depends_on: [],
    is_active: true,
    health_probe: null,
    state: 'lit',
    last_built_at: null,
    actual_rows: null,
    build_state_stale: false,
    ...overrides,
  } as AssetWithState
}

describe('aggregate()', () => {
  it('counts lit assets as built and closes ring', () => {
    const assets = [
      makeAsset({ asset_id: 'a', state: 'lit' }),
      makeAsset({ asset_id: 'b', state: 'lit' }),
    ]
    const { builtFrac, state } = aggregate(assets)
    expect(builtFrac).toBe(1.0)
    expect(state).toBe('lit')
  })

  it('counts service_ok assets as built — ring closes when services are present', () => {
    const assets = [
      makeAsset({ asset_id: 'svc', state: 'service_ok', asset_type: 'service' }),
      makeAsset({ asset_id: 'data', state: 'lit' }),
    ]
    const { builtFrac } = aggregate(assets)
    expect(builtFrac).toBe(1.0)
  })

  it('counts build_state_stale assets as built — ring closes when rows present but ledger stale', () => {
    const assets = [
      makeAsset({ asset_id: 'a', state: 'lit', build_state_stale: false }),
      makeAsset({ asset_id: 'b', state: 'lit', build_state_stale: true }),
      makeAsset({ asset_id: 'c', state: 'lit', build_state_stale: true }),
    ]
    const { builtFrac } = aggregate(assets)
    expect(builtFrac).toBe(1.0)
  })

  it('all assets rows-present (mix of lit and stale ledger) → CLOSED ring', () => {
    // This is the documented regression test: even if some assets have build_state_stale,
    // the ring must close when all data is present.
    const assets = [
      makeAsset({ asset_id: 'bo_laksana',     state: 'lit' }),
      makeAsset({ asset_id: 'bo_bimba',       state: 'lit' }),
      makeAsset({ asset_id: 'bo_karanajala',  state: 'lit' }),
      makeAsset({ asset_id: 'bo_sangati',     state: 'lit' }),
      makeAsset({ asset_id: 'bo_samvada',     state: 'lit' }),
      makeAsset({ asset_id: 'bo_samskara',    state: 'lit' }),
      makeAsset({ asset_id: 'bo_upaya',       state: 'lit' }),
      makeAsset({ asset_id: 'bo_pramana_mapa', state: 'lit' }),
      makeAsset({ asset_id: 'bo_drishti',     state: 'lit', build_state_stale: true }),
      makeAsset({ asset_id: 'bo_anveshana',   state: 'lit', build_state_stale: true }),
    ]
    const { builtFrac, state } = aggregate(assets)
    expect(builtFrac).toBe(1.0)
    expect(state).toBe('stale') // stale badge but ring closed — soft warning, not absent
  })

  it('dormant when zero assets built', () => {
    const assets = [makeAsset({ state: 'dormant' })]
    const { builtFrac, state } = aggregate(assets)
    expect(builtFrac).toBe(0)
    expect(state).toBe('dormant')
  })

  it('building takes priority over all other states', () => {
    const assets = [
      makeAsset({ asset_id: 'a', state: 'building' }),
      makeAsset({ asset_id: 'b', state: 'lit' }),
    ]
    const { state } = aggregate(assets)
    expect(state).toBe('building')
  })
})
