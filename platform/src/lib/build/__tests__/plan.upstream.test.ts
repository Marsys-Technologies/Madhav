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

describe('resolveBuildPlan — pre-flight gate (replaces upstream-pull)', () => {
  it('asset-scope build of downstream with explicit dormant cross-layer dep → blocked', () => {
    // ph_result depends on bo_analysis (explicitly dormant) — preflight catches it
    const throughput = new Map([tp('bg_data', 'lit'), tp('bo_analysis', 'dormant')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('blocked')
    expect(result.plan_waves.flat()).toHaveLength(0)
    expect(result.blockers.length).toBeGreaterThan(0)
    const blockerIds = result.blockers.map(b => b.dep_asset_id)
    expect(blockerIds).toContain('bo_analysis')
  })

  it('preflight treats absent throughput entries as ready (unknown deps do not block)', () => {
    // bo_analysis has no throughput entry — treated as ready by preflight
    const throughput = new Map([tp('bg_data', 'lit')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('ok')
  })

  it('build does NOT pull in already-lit upstream (skip-if-lit)', () => {
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
  })

  it('rebuild of asset-scope returns only the target (no transitive downstream expansion)', () => {
    // All upstream is lit; only ph_result is being rebuilt
    const throughput = new Map([
      tp('bg_data', 'lit'), tp('ga_data', 'lit'), tp('bo_analysis', 'lit'), tp('ph_result', 'lit'),
    ])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ph_result', action: 'rebuild',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('ok')
    const plan = result.plan_waves.flat()
    expect(plan).toContain('ph_result')
    expect(plan).not.toContain('bg_data')
    expect(plan).not.toContain('ga_data')
    expect(plan).not.toContain('bo_analysis')
  })

  it('empty depends_on root asset is still included (regression guard)', () => {
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'bg_data', action: 'build',
      registry: CROSS_LAYER, throughput: new Map(),
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toEqual(['bg_data'])
  })

  it('global build is scoped to dormant assets only', () => {
    const throughput = new Map([tp('bg_data', 'lit')])
    const result = resolveBuildPlan({
      scope: 'global', scope_target: null, action: 'build',
      registry: CROSS_LAYER, throughput,
    })
    expect(result.status).toBe('ok')
    const plan = result.plan_waves.flat()
    expect(plan).not.toContain('bg_data')
    expect(plan).toContain('ga_data')
    expect(plan).toContain('bo_analysis')
    expect(plan).toContain('ph_result')
  })
})

// ── L0 guard tests (native ruling 2026-06-26: bg_* never auto-pulled) ──────────
describe('resolveBuildPlan — L0 exclusion guard (pre-flight)', () => {
  const REGISTRY_WITH_DORMANT_L0 = [
    reg('bg_ephemeris', 'brahmagyan', []),
    reg('ga_chart', 'ganita', ['bg_ephemeris']),
    reg('ga_other', 'ganita', []),
    reg('bo_analysis', 'bodha', ['ga_chart']),
  ]

  it('asset-scope build of L1 asset with explicit dormant L0 dep → blocked', () => {
    // bg_ephemeris is explicitly dormant; ga_chart directly depends on it
    const throughput = new Map([tp('bg_ephemeris', 'dormant')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_chart', action: 'build',
      registry: REGISTRY_WITH_DORMANT_L0, throughput,
    })
    expect(result.status).toBe('blocked')
    expect(result.plan_waves.flat()).not.toContain('ga_chart')
    expect(result.plan_waves.flat()).not.toContain('bg_ephemeris')
    const blockerIds = result.blockers.map(b => b.dep_asset_id)
    expect(blockerIds).toContain('bg_ephemeris')
    const l0Blocker = result.blockers.find(b => b.dep_asset_id === 'bg_ephemeris')
    expect(l0Blocker?.guidance).toMatch(/Brahmagyan/)
  })

  it('asset-scope build of asset with no cross-layer deps passes', () => {
    // ga_other has no cross-layer deps → pre-flight passes → ok
    const throughput = new Map([tp('bg_ephemeris', 'dormant')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_other', action: 'build',
      registry: REGISTRY_WITH_DORMANT_L0, throughput,
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toContain('ga_other')
  })

  it('when L0 dep is lit, no blocking occurs and L0 is not pulled into plan', () => {
    // bg_ephemeris is lit; ga_chart can build normally
    const throughput = new Map([tp('bg_ephemeris', 'lit')])
    const result = resolveBuildPlan({
      scope: 'asset', scope_target: 'ga_chart', action: 'build',
      registry: REGISTRY_WITH_DORMANT_L0, throughput,
    })
    expect(result.status).toBe('ok')
    expect(result.plan_waves.flat()).toContain('ga_chart')
    expect(result.plan_waves.flat()).not.toContain('bg_ephemeris')
    expect(result.blockers).toHaveLength(0)
  })
})
