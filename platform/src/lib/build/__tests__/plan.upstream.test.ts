import { describe, it, expect } from 'vitest'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry } from '../plan'

function reg(asset_id: string, layer: string, depends_on: string[]): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: null }
}

function tp(asset_id: string, state: ThroughputEntry['state']): [string, ThroughputEntry] {
  return [asset_id, { asset_id, state }]
}

// Cross-layer registry: L2 asset depends on L1 which depends on L0
const CROSS_LAYER = [
  reg('bg_data', 'brahmagyan', []),
  reg('ga_data', 'ganita', ['bg_data']),
  reg('bo_analysis', 'bodha', ['ga_data']),
  reg('ph_result', 'phala', ['bo_analysis']),
]

describe('resolveBuildPlan — pre-flight gate (blocks stale cross-layer deps)', () => {
  it('asset-scope build is blocked when direct dep is stale', () => {
    // bo_analysis is stale — building ph_result on stale data must be blocked
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'lit'), tp('bo_analysis', 'stale'),
    ])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('blocked')
    expect(result.plan_waves).toEqual([])
    expect(result.blockers.length).toBeGreaterThan(0)
    expect(result.blockers[0].dep_asset_id).toBe('bo_analysis')
    expect(result.blockers[0].required_by).toContain('ph_result')
  })

  it('asset-scope build succeeds when all upstream deps are lit', () => {
    // Everything is lit except ph_result
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'lit'), tp('bo_analysis', 'lit'),
    ])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toEqual(['ph_result'])
    // upstream deps must NOT be in plan (they're already lit)
    expect(result.plan_waves.flat()).not.toContain('bg_data')
    expect(result.plan_waves.flat()).not.toContain('ga_data')
    expect(result.plan_waves.flat()).not.toContain('bo_analysis')
  })

  it('layer-scope build is blocked when cross-layer dep is stale', () => {
    // bo_analysis (bodha) is stale; building phala layer on stale data is blocked
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'lit'), tp('bo_analysis', 'stale'),
    ])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'phala', action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('blocked')
    expect(result.plan_waves).toEqual([])
    expect(result.blockers.length).toBeGreaterThan(0)
  })

  it('layer-scope build succeeds when cross-layer upstream is lit', () => {
    // bo_analysis is lit, ph_result is dormant
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'lit'), tp('bo_analysis', 'lit'),
    ])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'phala', action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toContain('ph_result')
    expect(result.plan_waves.flat()).not.toContain('ga_data')
    expect(result.plan_waves.flat()).not.toContain('bo_analysis')
  })

  it('rebuild of single asset returns ONLY that asset (no auto-pull upstream)', () => {
    // All upstream is lit; only ph_result is being rebuilt
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'lit'), tp('bo_analysis', 'lit'), tp('ph_result', 'lit'),
    ])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'rebuild',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('ok')
    // rebuild of asset = only the target, no transitive downstream, no upstream pull
    expect(result.plan_waves).toEqual([['ph_result']])
    expect(result.plan_waves.flat()).not.toContain('bg_data')
    expect(result.plan_waves.flat()).not.toContain('ga_data')
    expect(result.plan_waves.flat()).not.toContain('bo_analysis')
  })

  it('rebuild of single asset is blocked when direct dep is stale', () => {
    // bo_analysis is stale — ph_result rebuild on stale data should be blocked
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'lit'), tp('bo_analysis', 'stale'), tp('ph_result', 'lit'),
    ])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'rebuild',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('blocked')
    expect(result.plan_waves).toEqual([])
    expect(result.blockers[0].dep_asset_id).toBe('bo_analysis')
  })

  it('layer rebuild is blocked when cross-layer dep is stale', () => {
    // Rebuilding bodha layer; ga_data (ganita) is stale — pre-flight blocks
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'stale'), tp('ph_result', 'lit'),
    ])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'bodha', action: 'rebuild',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('blocked')
    expect(result.plan_waves).toEqual([])
    expect(result.blockers.length).toBeGreaterThan(0)
    expect(result.blockers[0].dep_asset_id).toBe('ga_data')
  })

  it('layer rebuild succeeds when cross-layer upstream is lit', () => {
    // ga_data lit; rebuilding bodha layer
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'lit'), tp('ph_result', 'lit'),
    ])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'bodha', action: 'rebuild',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toContain('bo_analysis')
    expect(result.plan_waves.flat()).not.toContain('bg_data')
    expect(result.plan_waves.flat()).not.toContain('ga_data')
    // lit downstream ph_result not included in layer rebuild
    expect(result.plan_waves.flat()).not.toContain('ph_result')
  })

  it('empty depends_on root asset is still included (regression guard)', () => {
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'bg_data', action: 'build',
      registry: CROSS_LAYER, throughput: new Map(),
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toEqual(['bg_data'])
  })

  it('global build is not gated by pre-flight (all in scope)', () => {
    const throughput = new Map([tp('bg_data', 'lit')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    // Global scope: pre-flight does not apply; dormant non-L0 assets build normally
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).not.toContain('bg_data')
    expect(result.plan_waves.flat()).toContain('ga_data')
    expect(result.plan_waves.flat()).toContain('bo_analysis')
    expect(result.plan_waves.flat()).toContain('ph_result')
  })
})

// ── L0 guard tests (pre-flight: L0 stale/error → blocked) ────────────────────
describe('resolveBuildPlan — L0 blocking via pre-flight gate (stale/error states)', () => {
  const REGISTRY_WITH_L0 = [
    reg('bg_ephemeris', 'brahmagyan', []),
    reg('ga_chart', 'ganita', ['bg_ephemeris']),
    reg('ga_other', 'ganita', []),
    reg('bo_analysis', 'bodha', ['ga_chart']),
  ]

  it('asset-scope build of L1 asset with stale L0 dep → blocked with L0 guidance', () => {
    // bg_ephemeris is stale; ga_chart directly depends on it
    const throughput = new Map([tp('bg_ephemeris', 'stale')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_chart', action: 'build',
      registry: REGISTRY_WITH_L0, throughput,
    })
    expect(result.status).toBe('blocked')
    expect(result.plan_waves).toEqual([])
    expect(result.blockers.length).toBeGreaterThan(0)
    expect(result.blockers[0].dep_asset_id).toBe('bg_ephemeris')
    expect(result.blockers[0].required_by).toContain('ga_chart')
    expect(result.blockers[0].guidance).toMatch(/Brahmagyan/)
  })

  it('layer-scope build with stale L0 dep blocks (pre-flight traverses transitively)', () => {
    // ga_chart depends on stale bg_ephemeris; pre-flight traverses transitively for layer scope
    const throughput = new Map([tp('bg_ephemeris', 'stale')])
    const result = resolveBuildPlan({
      scope: 'layer', scope_target: 'ganita', action: 'build',
      registry: REGISTRY_WITH_L0, throughput,
    })
    expect(result.status).toBe('blocked')
    expect(result.plan_waves).toEqual([])
    expect(result.blockers.some((b) => b.dep_asset_id === 'bg_ephemeris')).toBe(true)
  })

  it('when L0 dep is lit, pre-flight passes and asset builds normally', () => {
    // bg_ephemeris is lit; ga_chart can build normally
    const throughput = new Map([tp('bg_ephemeris', 'lit')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_chart', action: 'build',
      registry: REGISTRY_WITH_L0, throughput,
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toContain('ga_chart')
    expect(result.plan_waves.flat()).not.toContain('bg_ephemeris')
    expect(result.blockers).toHaveLength(0)
  })

  it('blocker entry carries dep_state, required_by, and L0 guidance', () => {
    const throughput = new Map([tp('bg_ephemeris', 'error')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_chart', action: 'build',
      registry: REGISTRY_WITH_L0, throughput,
    })
    expect(result.status).toBe('blocked')
    const blocker = result.blockers[0]
    expect(blocker.dep_asset_id).toBe('bg_ephemeris')
    expect(blocker.dep_state).toBe('error')
    expect(blocker.required_by).toContain('ga_chart')
    expect(blocker.guidance).toBeTruthy()
  })

  it('asset with no cross-layer dep is not blocked even when other L0 assets are stale', () => {
    // ga_other has no deps -> no blockers, even though bg_ephemeris is stale
    const throughput = new Map([tp('bg_ephemeris', 'stale')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_other', action: 'build',
      registry: REGISTRY_WITH_L0, throughput,
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toContain('ga_other')
  })
})
